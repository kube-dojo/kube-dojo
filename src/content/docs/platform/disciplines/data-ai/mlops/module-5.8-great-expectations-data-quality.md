---
citations_verified: true
title: "Module 5.8: Great Expectations Data Quality"
slug: platform/disciplines/data-ai/mlops/module-5.8-great-expectations-data-quality
sidebar:
  order: 9
---

> **Discipline Track** | Complexity: `[COMPLEX]` | Time: 50-60 min

## Prerequisites

Before starting this module, confirm you have completed the earlier MLOps prerequisites and the baseline technical skills listed below:

- [Module 5.2: Feature Engineering & Stores](../module-5.2-feature-stores/)
- [Module 5.7: Data Versioning with DVC](../module-5.7-dvc-data-versioning/)
- Python familiarity, including functions, virtual environments, and decorators
- YAML and JSON Schema basics
- Comfort reading Kubernetes Job, CronJob, and ConfigMap manifests

## Learning Outcomes

After completing this module, you will be able to apply the following capabilities in real CSV-backed MLOps workflows:

- **Diagnose** silent model regressions caused by schema drift, null-rate drift, and distribution shifts before blaming model code.
- **Design** Great Expectations suites that separate essential production contracts from noisy profiling output.
- **Implement** GX Core `1.16.1` Data Sources, Expectation Suites, Validation Definitions, Checkpoints, and Data Docs for CSV-backed MLOps workflows.
- **Integrate** Great Expectations with DVC so a tracked dataset snapshot becomes a reviewed baseline, not an auto-accepted drift target.
- **Operate** inline, orchestrated, and Kubernetes-native data-quality gates with cost controls for Data Docs retention, large-table validation, sampling, and cross-region storage access, evaluating latency, observability, and failure behavior across runtime postures.

## Why This Module Matters

**Hypothetical scenario:** A fraud-detection model degrades over a weekend. No deployment failed. No exception reached the pager. The training image is the same.

The inference service is healthy. The dashboard shows lower precision on Monday morning, but the pipeline logs are green. The root cause is not a neural network mystery. A vendor changed a CSV header from `currency_code` to `CURR_CD`. The pipeline's permissive CSV reader accepted the file.

The feature engineering code silently produced missing currency features. The model still returned predictions, just worse ones. That is the dangerous shape of ML failure. Traditional software usually fails loudly when a required function, field, or dependency disappears. ML systems often fail softly.

The data shape changes, the code keeps running, and the model becomes less trustworthy. You cannot debug what you do not validate. You cannot roll back confidently if you do not know which data contract was broken. You cannot treat data quality as a cleanup task after the model is already trained. Great Expectations, now branded in the docs as GX Core, gives you a way to turn data assumptions into runnable tests.

The analogy is imperfect but useful: `pytest` is to code as Great Expectations is to data. `pytest` asks whether your code still satisfies its behavioral contract. Great Expectations asks whether a dataset still satisfies its shape, completeness, range, uniqueness, and semantic contracts. The difference is that data contracts usually have business meaning.

A column being non-null is not just a technical preference. It may decide whether a credit model excludes a region, whether a fraud rule misses a currency, or whether a serving feature vector becomes sparse in a way the model never saw during training. This module treats data quality as a production gate, not as a "best practice" checkbox. You will learn the GX mental model. You will author expectations from a baseline dataset and then trim them down to the few contracts that actually matter.

You will run checkpoints in Python, CI, orchestration systems, Kubernetes Jobs, and Argo Workflows. You will connect the baseline to the DVC workflow from [Module 5.7](../module-5.7-dvc-data-versioning/) so changing data requires review instead of quiet suite mutation. You will also see where Great Expectations is not enough, because a static validation report is not a substitute for drift monitoring, slice analysis, or time-series observability.

## 1. Why Data Quality Is a Production Gate

The first mental shift is simple: Data validation belongs on the critical path. It is not a dashboard someone checks when time allows. It is not a weekly report. It is not a notebook cell that runs during a demo and then disappears.

It is a gate. If the data violates the contract, the downstream build, training job, or serving update must stop. That sounds strict until you compare the alternatives. A failed data gate is a loud failure. A silent data drift is a quiet failure.

Loud failures interrupt the pipeline while the cause is still close to the change. Quiet failures create bad models, confusing metrics, and investigation debt. The weekend fraud example has the classic pattern. The vendor shipped a field rename. The ingestion code did not crash.

The feature pipeline did not crash. The model training job did not crash. The model regressed because the input semantics changed. When teams investigate these incidents, they often start in the wrong layer. They compare model versions.

They inspect hyperparameters. They ask whether the training container changed. Those checks are reasonable, but they miss the fact that most ML artifacts are functions of data first and code second. Code tells the model how to learn. Data tells the model what world it is learning from.

When the world changes without being named, a model can be "correctly" trained on the wrong reality. That is why data validation must run before training, before batch scoring, and before promoting a model. It must also run near the source of truth when possible. Validating only at the ML boundary is late. By then, a bad export may already have polluted a feature store, a warehouse table, a training snapshot, and a model registry run.

Shift-left validation catches problems closer to the producer. It also gives the producer a clear contract to honor. The useful comparison with unit testing is not that data and code are the same. They are not. Code has deterministic behavior under controlled inputs.

Data has statistical properties, messy edge cases, and legitimate evolution. The comparison is that both need executable contracts. Without tests, code review becomes guesswork. Without expectations, data review becomes vibes. Great Expectations gives you named assertions such as:

- `transaction_id` must be unique.
- `currency_code` must exist.
- `currency_code` values must be in a controlled set.
- `amount` must be non-negative.
- `email` must be present for most customer-facing transactions.
- The table must have the expected ordered columns.

Each assertion is small. Together, they draw a boundary around the data your model is allowed to consume. The boundary should be strict where the business contract is strict. It should be tolerant where normal variation is expected. That distinction matters.

If you demand that every numeric mean match last week's exact value, your pipeline will fail constantly. If you accept every newly observed value because a profiler saw it once, your pipeline will accept drift as truth. Data validation engineering sits between those extremes. You are not trying to freeze reality. You are trying to detect when reality changed in a way that demands engineering review.

That is the same discipline you practiced in [Module 5.6](../module-5.6-ml-pipelines/), where pipeline gates turned ML work into an auditable release process. The difference here is that the gate is about data contracts. The gate answers a production question: "Is this dataset safe enough to train, score, or promote with?" When the answer is no, the pipeline must stop.

The alert should point to the failing expectation, the affected column, the observed value, and the dataset version. The on-call person should not have to reverse-engineer the contract from a notebook. That is why the expectation suite lives in Git. That is why checkpoint output is stored. That is why Data Docs are generated.

And that is why failed checkpoints must not be advisory. Advisory validation is a suggestion. Production validation is a control. The distinction is visible in behavior. If the checkpoint fails and the training step still runs, the system has learned to ignore its own evidence. If the checkpoint fails and a CI job fails, the system has turned evidence into a release decision. That difference is the heart of this module.

> **Active learning prompt:** The fraud model's precision drops after `currency_code` becomes `CURR_CD`. Before looking at any model metrics, which two data contracts would you want to fail, and what would each failure prove?

## 2. The GX Mental Model: Expectations, Suites, Checkpoints, and Data Sources

Great Expectations has many objects, but four nouns carry the daily workflow: Data Source. Expectation. Expectation Suite. Checkpoint.

GX Core `1.16.1` also uses Data Assets, Batch Definitions, Validation Definitions, and Data Docs. Those nouns are not extra bureaucracy. They separate "where the data lives", "which slice of data is being validated", "what is expected", and "how validation is run". Start with the simplified graph:

```text
┌──────────────────────┐
│ Source of data        │
│ CSV, SQL, DataFrame   │
└──────────┬───────────┘
           │
           v
┌──────────────────────┐
│ GX Data Source        │
│ connection + type     │
└──────────┬───────────┘
           │
           v
┌──────────────────────┐
│ Data Asset + Batch    │
│ table, files, slice   │
└──────────┬───────────┘
           │
           v
┌──────────────────────┐       ┌──────────────────────┐
│ Expectation Suite     │<------│ Expectations          │
│ reviewed data contract│       │ individual assertions │
└──────────┬───────────┘       └──────────────────────┘
           │
           v
┌──────────────────────┐
│ Validation Definition │
│ batch + suite binding │
└──────────┬───────────┘
           │
           v
┌──────────────────────┐
│ Checkpoint            │
│ runnable validation   │
└──────────┬───────────┘
           │
           v
┌──────────────────────┐
│ Data Docs + actions   │
│ HTML, JSON, alerts    │
└──────────────────────┘
```

An **Expectation** is one assertion. For example, `expect_column_values_to_be_unique` asserts that a column has no duplicates. It is comparable to one unit test. It should be small enough that a failure points to a specific problem. An **Expectation Suite** is a collection of expectations over a dataset or logical table.

It is comparable to a test file or test class. For a `transactions` table, the suite may assert required columns, primary-key uniqueness, allowed currency values, timestamp parseability, and amount ranges. A suite is not a place to dump every fact a profiler can infer. It is a reviewed contract. A **Data Source** tells GX where and how data is read.

In GX Core `1.16.1`, the Python API exposes factories such as `context.data_sources.add_pandas_filesystem(...)`. A filesystem Data Source can point at a directory of CSV files. A SQL Data Source can point at a database. A Spark Data Source can validate distributed data. The Data Source is not the expectation.

It is the connection boundary. A **Data Asset** is a logical collection inside the source. For a filesystem source, a CSV asset may represent matching CSV files. For a SQL source, an asset may represent a table or query. A **Batch Definition** chooses the specific batch to validate.

In the lab, the same CSV asset has one batch definition for `transactions.csv` and another for `transactions_drift.csv`. That lets one suite validate two files with the same expected contract. A **Validation Definition** binds a Batch Definition to an Expectation Suite. This object is easy to skip mentally, but it matters in GX Core `1.x`. It is the named "validate this data with that suite" object.

A **Checkpoint** is the runnable job. It can run one or more validation definitions. It returns success or failure. It can trigger actions such as updating Data Docs or writing validation results. In production, the checkpoint's return value should decide whether the next step runs.

That is the job of a gate. The file layout is also worth understanding. Older tutorials often say `expectation_suite.json`. With a file-backed GX Core `1.16.1` context, a suite named `transactions.critical` is stored under a path like:

```text
gx/
├── great_expectations.yml
├── expectations/
│   └── transactions/
│       └── critical.json
├── checkpoints/
│   └── transactions_checkpoint.json
└── validation_definitions/
    └── transactions_drift_validation.json
```

The suite file is still the JSON representation of an expectation suite. The exact filename is derived from the suite name. That detail matters when you review diffs. If a suite changes, you should see a Git diff in `gx/expectations/...`. If a checkpoint changes, you should see a Git diff in `gx/checkpoints/...`.

If only runtime validation results changed, those should usually live under `gx/uncommitted/` or an external artifact store, not in a code PR. GX's API history is a real practitioner trap. The docs for GX Core `1.16.1` use the current object model. Many search results still point to older `0.18.x` pages, legacy V3 API examples, and `great_expectations init` CLI workflows. The older examples may use `DataContext`, YAML datasource blocks, `RuntimeBatchRequest`, or `context.add_or_update_checkpoint(...)`.

The current API more often uses factories on `context.data_sources`, `context.suites`, `context.validation_definitions`, and `context.checkpoints`. The word "Fluent" appears because the datasource classes grew from the Fluent API introduced before GX Core `1.0`. For new GX Core `1.x` work, use the current `context.data_sources.add_*` and `add_or_update_*` methods. Do not mix legacy V3 snippets into a new suite unless you have a migration reason and a test proving the behavior. The `add_or_update` naming is another source of confusion.

It is convenient in local authoring because rerunning a bootstrap script updates the stored object. It is risky in production if it updates a suite as a side effect of observing new data. Creating or updating a Data Source is operational configuration. Creating or updating an Expectation Suite is a contract change. Those two actions deserve different levels of review.

The API method name does not decide your governance model. Your pipeline does. This is why suite files belong in Git. It is also why validation results do not automatically rewrite suite files. If a batch introduces `BTC` as a new currency, the checkpoint should fail.

If the business accepts `BTC`, a human should update the suite in a reviewed pull request. That is a production contract workflow. It is slower than accepting every observed value. It is also the point.

## 3. Authoring Expectations Without Creating Noise

Expectation authoring has three useful modes. The first mode is profiling from a baseline dataset. The second mode is manual authoring with explicit `expect_column_*` classes or methods. The third mode is configuration-as-data, often YAML validated by JSON Schema before it becomes a suite. Each mode solves a different problem.

Profiling is good for discovery. Manual authoring is good for intent. Schema-validated configuration is good for review and repeatability. The mistake is treating profiling output as a finished production contract. A profiler can observe facts.

It cannot know which facts matter. If a baseline file has exactly six rows, a profiler may infer that row count should be six. That is rarely a production contract. If a baseline file has only `USD` and `EUR`, a profiler may infer that those are the only allowed currencies. That may or may not be true.

If a baseline file has no null email values, a profiler may infer that email must never be null. That may be too strict for business-to-business accounts, test accounts, or privacy-suppressed records. Profiling gives you candidate expectations. Engineering review turns candidates into a suite. Here is a baseline file used in the lab:

```csv
transaction_id,account_id,amount,currency_code,email,event_ts
TXN-1001,ACC-100,12.25,USD,ava@example.test,2026-05-18T08:10:00Z
TXN-1002,ACC-101,90.00,EUR,ben@example.test,2026-05-18T08:11:00Z
TXN-1003,ACC-102,44.80,GBP,cy@example.test,2026-05-18T08:12:00Z
TXN-1004,ACC-103,18.30,USD,dia@example.test,2026-05-18T08:13:00Z
TXN-1005,ACC-104,205.20,EUR,eli@example.test,2026-05-18T08:14:00Z
TXN-1006,ACC-105,31.10,USD,fay@example.test,2026-05-18T08:15:00Z
```

A simple baseline profiler may produce eight candidate expectations, which you should treat as discovery output rather than a finished contract:

```yaml
suite_name: transactions.profiled
expectations:
  - type: expect_table_columns_to_match_ordered_list
    column_list: [transaction_id, account_id, amount, currency_code, email, event_ts]
  - type: expect_table_row_count_to_be_between
    min_value: 6
    max_value: 6
  - type: expect_column_values_to_not_be_null
    column: transaction_id
  - type: expect_column_values_to_be_unique
    column: transaction_id
  - type: expect_column_values_to_not_be_null
    column: email
  - type: expect_column_values_to_be_in_set
    column: currency_code
    value_set: [USD, EUR, GBP]
  - type: expect_column_values_to_be_between
    column: amount
    min_value: 12.25
    max_value: 205.20
  - type: expect_column_values_to_match_regex
    column: transaction_id
    regex: "^TXN-[0-9]+$"
```

That output is useful. It is not finished. The row count expectation is too brittle. The exact amount range is too narrow. The email non-null rule may be too strict if a tiny percentage of transactions can arrive before customer enrichment. The transaction ID regex may be useful, but it may belong in an upstream ingestion contract rather than the ML training gate. After review, the worked-example production suite might keep four expectations:

```yaml
suite_name: transactions.critical
expectations:
  - type: expect_table_columns_to_match_ordered_list
    column_list: [transaction_id, account_id, amount, currency_code, email, event_ts]
  - type: expect_column_values_to_be_unique
    column: transaction_id
  - type: expect_column_values_to_be_in_set
    column: currency_code
    value_set: [USD, EUR, GBP]
  - type: expect_column_values_to_be_between
    column: amount
    min_value: 0
    max_value: 500
```

The diff teaches the "less is more" principle by showing which profiler noise was removed and which contracts survived review:

```diff
 suite_name: transactions.critical
 expectations:
   - type: expect_table_columns_to_match_ordered_list
     column_list: [transaction_id, account_id, amount, currency_code, email, event_ts]
-  - type: expect_table_row_count_to_be_between
-    min_value: 6
-    max_value: 6
-  - type: expect_column_values_to_not_be_null
-    column: transaction_id
   - type: expect_column_values_to_be_unique
     column: transaction_id
-  - type: expect_column_values_to_not_be_null
-    column: email
   - type: expect_column_values_to_be_in_set
     column: currency_code
     value_set: [USD, EUR, GBP]
   - type: expect_column_values_to_be_between
     column: amount
-    min_value: 12.25
-    max_value: 205.20
-  - type: expect_column_values_to_match_regex
-    column: transaction_id
-    regex: "^TXN-[0-9]+$"
+    min_value: 0
+    max_value: 500
```

The final suite is smaller. It is also stronger. It focuses on contracts that would produce a real production problem. The ordered column expectation catches the `currency_code` to `CURR_CD` header drift. The uniqueness expectation protects joins, deduplication, and feature aggregation.

The currency set expectation catches semantic expansion that may require feature engineering review. The amount range expectation catches unit changes, decimal movement, and accidental multiplier bugs. The lab keeps a fifth not-null identity expectation as an extra guard, because hands-on practice benefits from seeing identity completeness and identity uniqueness as separate checks. The hand-authored suite tells future reviewers why the gate exists. That is much more valuable than a giant suite where every failure looks equally important.

Configuration-as-data makes this review easier. Instead of embedding every expectation directly in Python, you can store a curated YAML policy and validate it with JSON Schema. The schema below is intentionally small. It proves that each expectation has a `type`, and it constrains common fields enough to catch typos before GX runs:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["suite_name", "expectations"],
  "properties": {
    "suite_name": { "type": "string", "minLength": 3 },
    "expectations": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["type"],
        "properties": {
          "type": { "type": "string" },
          "column": { "type": "string" },
          "column_list": {
            "type": "array",
            "items": { "type": "string" }
          },
          "value_set": {
            "type": "array",
            "items": { "type": "string" }
          },
          "min_value": { "type": "number" },
          "max_value": { "type": "number" },
          "mostly": { "type": "number", "minimum": 0, "maximum": 1 }
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false
}
```

JSON Schema does not replace Great Expectations. It validates the suite configuration before your Python code turns it into GX objects. It catches mistakes like `value_sets` instead of `value_set`. It also makes suite review clearer because reviewers can focus on business intent rather than Python boilerplate. Manual GX authoring still matters.

Some teams prefer method-style calls such as `expect_column_values_to_be_between` when working inside validators. The lab uses the explicit expectation classes because they serialize cleanly from YAML and make the mapping from reviewed configuration to GX objects visible. For advanced expectations, custom metrics, or Spark-specific behavior, direct Python is often clearer. The key is to keep intent visible. If a suite is generated, say so. If a suite is curated, review it. If a suite is updated because the business contract changed, connect the update to the data and model evidence.

> **Active learning prompt:** The profiler suggests keeping an exact row-count expectation because the baseline has six rows. Would you keep it for a daily training export? Defend your answer by naming the failure you want to catch and the false alarm you want to avoid.

## 4. Running Checkpoints in Production

A suite is only useful when it runs. In GX Core `1.x`, the Checkpoint is the runnable validation job. It decides whether the data passed the suite. It may update Data Docs. It may write validation results.

It may trigger actions. Your platform decides what happens next. There are three common runtime postures. The first is inline validation in a Python ELT pipeline. The second is a dedicated task in an orchestrator such as Airflow, Argo Workflows, or Kubeflow Pipelines.

The third is a Kubernetes Job, init container, or sidecar around a data-processing workload. Each posture has a different blast radius. Inline validation is the lowest ceremony. The same Python process reads data, runs the checkpoint, and exits non-zero on failure. It is a good fit for smaller CSV, Parquet, or pandas-backed jobs.

It is also useful in CI because it has few moving parts. The tradeoff is that validation shares resources with the pipeline step. If validation is slow, the whole step is slow. If the process crashes, you need logs that distinguish data failure from code failure. Orchestrated validation separates the gate into its own task.

An Airflow DAG can put `validate_transactions` before `train_model`. An Argo Workflow can put `gx-checkpoint` before a training template. Kubeflow Pipelines can make validation an upstream component whose output controls downstream execution. This posture is easier to observe. It also gives platform teams a clean place to attach retry policy, logs, artifacts, and alerts.

The tradeoff is orchestration overhead. The suite, data credentials, and validation image must be promoted like any other production component. Kubernetes-native validation is useful when the data job already runs in a cluster. An init container can validate mounted input before the main container starts. A sidecar can publish validation artifacts beside the main job.

A standalone Job or CronJob can run on a schedule and fail independently. This posture makes failure visible in Kubernetes primitives. A failed Job has failed Pods. A CronJob has failed history. ArgoCD can surface unhealthy workloads.

The tradeoff is that Kubernetes only knows exit codes and container state. You still need GX output stored somewhere humans can inspect. Compare the three postures:

| Runtime posture | Typical latency | Failure mode | Observability surface | Good fit |
|---|---:|---|---|---|
| Inline Python ELT | Seconds to minutes | Process exits non-zero | Step logs, CI job, Python exception | Small to medium datasets, local CI, simple batch jobs |
| Airflow, Argo, or Kubeflow task | Minutes, depends on scheduler | Validation task fails and downstream tasks do not start | DAG UI, task artifacts, alerts | Shared ML platforms and audited pipelines |
| Kubernetes Job, init container, or sidecar | Seconds to cluster-scheduled minutes | Pod exits non-zero, Job fails | Kubernetes events, Pod logs, CronJob history, ArgoCD health | Cluster-native data jobs and scheduled checks |

The hard rule is the same in every posture: A failed Checkpoint must fail the build, fail the task, fail the Job, or trigger an alert tied to an explicit operational response. It must not be advisory. Here is the pipeline shape you want:

```text
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│ Extract CSV │---->│ GX Checkpoint     │---->│ Train model │
└─────────────┘     │ required gate     │     └─────────────┘
                    └────────┬─────────┘
                             │
                    failure  │  success
                             v
                    ┌──────────────────┐
                    │ Stop pipeline     │
                    │ alert + docs link │
                    └──────────────────┘
```

This is the anti-silent-failure architecture. The checkpoint is not a report attached to a successful build. It is a condition for continuing. A minimal GitHub Actions gate looks like this:

```yaml
name: gx-data-quality

on:
  pull_request:
    paths:
      - "gx/**"
      - "data/transactions*.csv"
      - "scripts/gx_validate.py"

jobs:
  validate-transactions:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv venv --seed --python 3.13 .venv
      - run: .venv/bin/python -m pip install great_expectations==1.16.1 pandas pyyaml jsonschema
      - run: .venv/bin/python scripts/gx_validate.py
```

A minimal GitLab CI gate has the same operational meaning as the GitHub Actions example because both fail the pipeline when validation fails:

```yaml
stages:
  - validate
  - train

gx_data_quality:
  stage: validate
  image: ghcr.io/astral-sh/uv:bookworm-slim
  script:
    - uv venv --seed --python 3.13 .venv
    - .venv/bin/python -m pip install great_expectations==1.16.1 pandas pyyaml jsonschema
    - .venv/bin/python scripts/gx_validate.py

train_model:
  stage: train
  needs: ["gx_data_quality"]
  script:
    - .venv/bin/python scripts/train_model.py
```

In both examples, the checkpoint script must raise a non-zero exit code when `result.success` is false. Do not catch the failure and print a warning. Do not write "known issue" into the logs and continue. Do not update the suite to make the failure disappear. The job should fail because the data contract failed.

If the failure is expected, change the contract in review. This strictness also applies to timeouts. On large tables, a checkpoint can take longer than the build budget. That is not a reason to disable validation. It is a reason to design a faster validation posture.

You may validate a stratified sample in PR checks and run a full validation in the nightly pipeline. You may split a large suite into cheap schema expectations and expensive distribution expectations. You may run schema checks before materializing a training table and distribution checks after compaction. You may put the heaviest checks in a cluster job with a clear timeout and alert. The production rule is still failure-by-default.

If the gate cannot run, the release system should treat that as a failed gate unless a reviewed exception exists. The exception should be visible. The exception should expire. The exception should not become the normal path.

## 5. GE and DVC: Baselines Are Reviewed Snapshots

[Module 5.7](../module-5.7-dvc-data-versioning/) taught that DVC gives Git a stable pointer to data artifacts. Great Expectations gives that data pointer a contract. Together, they answer a stronger question: "Did this exact dataset version satisfy the reviewed expectations?" That is more useful than either tool alone.

DVC can tell you which `transactions.csv` was used. Great Expectations can tell you whether that file satisfied the data contract. DVC does not decide whether `currency_code` may become `CURR_CD`. Great Expectations does not decide which large object hash is the approved baseline. The integration pattern is:

1. Track a baseline dataset with DVC.
2. Profile or inspect that baseline to propose expectations.
3. Curate the suite by hand.
4. Commit the suite and the DVC metadata together.
5. Run checkpoints against future datasets.
6. Treat `dvc.lock` changes and suite changes as reviewable signals.

This is the important rule: When `dvc.lock` changes, the suite may need review, but it should not auto-update. Auto-updating the suite from the new data accepts the new data as normal. That is how silent drift becomes the new baseline. Imagine this pull request:

```diff
diff --git a/dvc.lock b/dvc.lock
@@
-      md5: 6d1c8a...
+      md5: a95bd2...
       path: data/transactions.csv

diff --git a/gx/expectations/transactions/critical.json b/gx/expectations/transactions/critical.json
@@
-            "value_set": ["USD", "EUR", "GBP"]
+            "value_set": ["USD", "EUR", "GBP", "BTC"]
```

That diff is not automatically wrong. It is also not routine. It says the data snapshot changed and the semantic contract changed. A reviewer should ask why. Is `BTC` now a supported currency?

Was a vendor export polluted with test data? Did a new market launch? Did feature engineering learn how to encode the new value? Did the training-serving feature contract change? Do old models still behave correctly when the new value appears?

The DVC pointer gives you the dataset identity. The suite diff gives you the contract change. The review connects both to model behavior. The anti-pattern is a script named something like `profile_and_accept_latest.py`. It reads the new data.

It infers the new observed ranges. It overwrites the suite. It commits the suite. It makes the checkpoint green. That is not validation.

That is paperwork around drift. Profiling should propose. Review should accept. Checkpoint runs should enforce. This distinction matters most for features.

In [Module 5.2](../module-5.2-feature-stores/), the training-serving skew problem came from features being computed differently in different places. GE cannot solve skew by itself. It can enforce that the training data and serving input data share critical constraints. For example, you can share a suite that validates:

- Required feature columns exist.
- Feature IDs are unique or grouped as expected.
- Enumerated values match the encoding contract.
- Timestamps are parseable and within a valid window.
- Numeric features are within operational ranges.

The same suite can run before training and before batch serving. That does not mean every expectation is identical in every environment. Serving may have smaller batches. Training may have historical ranges. But the core schema and semantic contracts should be shared when the model expects the same features.

This is suite-as-code. It treats data contracts like source code. They have owners. They have diffs. They have reviews. They have tests. They move with the rest of the MLOps release evidence.

> **Active learning prompt:** A pull request updates `dvc.lock` for `data/transactions.csv` and also widens the `amount` max from `500` to `5000`. What evidence would you require before approving that suite change?

## 6. Data Docs and Incident Response

Data Docs are the human-readable side of Great Expectations. They turn validation results and suite definitions into static HTML. That matters during incidents. When a checkpoint fails at 02:10 UTC, the on-call person should not need to decode raw JSON from a Pod log. They should be able to open a report that says which suite ran, which expectations failed, and what values were observed.

Data Docs can show expectation descriptions. They can show validation history and column-level status across runs. They can show failed expectations. They can show observed values and sample unexpected records when result format captures them. They can show which checkpoint and batch were involved. That makes them useful for handoff between platform, data, and ML teams. The simplest local preview is a static HTTP server bound to loopback:

```bash
.venv/bin/python -m http.server 8008 --bind 127.0.0.1 --directory gx/uncommitted/data_docs/local_site
```

Then open `http://127.0.0.1:8008/`. Binding to `127.0.0.1` is deliberate. The lab preview is for your machine, not for the whole network. In production, Data Docs can be published as static files. A common pattern is to upload them to object storage behind private access.

Another pattern is to attach the generated HTML directory as a pipeline artifact. For model-centric workflows, a checkpoint can write validation output beside an MLflow run so the model artifact and the data-quality evidence travel together. The key is traceability. A model registry entry should let you answer:

- Which dataset snapshot was validated?
- Which expectation suite version ran?
- Which checkpoint result passed?
- Where is the Data Docs report?
- Which suite diff, if any, was reviewed for this run?

Data Docs are not a monitoring system. They are evidence. They are excellent for explaining a failed gate. They are less effective for high-cardinality, long-running drift questions. For example, a daily `merchant_id` distribution with hundreds of thousands of values does not fit neatly into a static report.

A time-series quantile shift may be invisible if your suite only checks a broad min and max. A slow change in missingness by region may pass a global `mostly` threshold while hurting one market. Those problems need monitoring, slice analysis, and drift tooling. Great Expectations can participate by validating known contracts and writing evidence. It should not be the only way you understand data behavior over time.

Cost also shows up here. Data Docs are static HTML plus stored validation JSON. That sounds cheap, and it often is. It can still grow quickly when every hourly run stores full unexpected row samples for many suites. Set retention deliberately.

Keep enough history for incident response and audits. Prune low-value historical runs. Use object storage lifecycle policies for old Data Docs. Do not keep large validation payloads forever just because the default directory is easy to ignore. Compute cost is the other side.

Validating a multi-GB dataset with many column-level expectations can be expensive. The cost is not just CPU. It can include cluster runtime, warehouse query cost, object storage reads, and network egress. Sampling is a legitimate tactic when it is explicit. A PR check may validate schema, nullability, and a stratified sample.

A nightly job may validate the full table. A release gate may validate the full training snapshot and block promotion. Older Checkpoint examples may use `runtime_configuration` and `expectation_suite_kwargs` to pass sampling-related options at runtime. In new GX Core `1.x` projects, prefer making the sampling boundary explicit in your wrapper script, Batch Definition, SQL query, or orchestration task so reviewers can see exactly which rows were validated. The wrong tactic is accidental sampling.

If a local pandas job only reads the first chunk because memory is low, the validation result may be misleading. Name the sampling strategy. Write it into the checkpoint configuration or wrapper script. Record it in the Data Docs or pipeline artifact. Cross-region storage can surprise teams.

If a Kubernetes cluster in one region validates data stored in another region, each run may read large objects across region boundaries. That cost is easy to miss because the checkpoint is "just validation". Place validation near the data when possible. Cache immutable DVC snapshots near the compute cluster when appropriate. Avoid pulling multi-GB tables across regions for a gate that could run beside the storage system. Incident response is where these choices pay off. A failed checkpoint should produce a small, durable packet of evidence:

- the failing expectation suite version,
- the checkpoint name,
- the data batch identity,
- the DVC data hash when available,
- the Data Docs URL or artifact path,
- the pipeline run ID,
- the owner to page or notify.

That packet turns "the model got worse" into "the training data violated the reviewed contract before training started." That is the difference between debugging and guessing.

## 7. Patterns and Anti-Patterns

Great Expectations succeeds when it becomes part of the platform contract. It fails when it becomes a notebook habit. The difference is not the number of expectations. The difference is how the expectations are owned, reviewed, run, and acted on. Use these patterns as defaults.

| Pattern | Why it works | Scaling consideration |
|---|---|---|
| Shift-left validation | Validates near the source of truth before bad data spreads into feature stores, training snapshots, and model registries. | Put cheap schema checks upstream and heavier distribution checks where compute is available. |
| Suite-as-code | Keeps data contracts in Git with diffs, ownership, and code review. | Treat suite changes like API changes when downstream models depend on them. |
| Failure-by-default | Makes a failed checkpoint stop the build, task, or Job instead of becoming ignored noise. | Add explicit exception workflows with owners and expiry dates for true emergencies. |
| Shared suite for training and serving | Reduces training-serving skew by enforcing common feature contracts at both boundaries. | Split environment-specific thresholds into small overlays rather than duplicating entire suites. |
| Baseline snapshot with DVC | Connects an expectation suite to a reproducible data version. | Review `dvc.lock` and suite diffs together when contracts change. |
| Data Docs as incident evidence | Gives humans a readable report during failures. | Store only useful history and prune old validation artifacts. |

These patterns sound simple. They require discipline because data changes more often than code. There will be pressure to "just update the suite" when a checkpoint blocks a deadline. Sometimes the suite should change. But that change should be reviewed with evidence. The anti-patterns are the habits that remove that review:

| Anti-pattern | What goes wrong | Better alternative |
|---|---|---|
| Profiling production after the fact | The suite explains yesterday's data instead of preventing today's bad data from moving forward. | Profile baselines for discovery, then enforce curated suites before downstream work. |
| Validating only the columns you remembered | Important drift hides in untested columns, especially join keys and feature columns added later. | Use schema expectations plus review checklists when dataset columns change. |
| Auto-accepting profiler output | The suite grows noisy and accepts silent drift as the new baseline. | Trim suites to production contracts and require review for semantic changes. |
| Never reviewing suites when schemas legitimately change | Teams either bypass validation or normalize constant failures. | Pair schema migrations with suite PRs, model-impact notes, and DVC evidence. |
| Treating GE as a one-time setup | The first suite becomes stale as producers, models, and features evolve. | Assign ownership and revisit suites during data-source, feature, and model changes. |
| Running checkpoints but ignoring failure | Validation becomes theater and engineers stop trusting the gate. | Fail the build, fail the task, or page the owner with a Data Docs link. |
| Keeping every Data Docs artifact forever | Storage and report indexes grow without operational value. | Apply retention by environment, suite criticality, and audit needs. |
| Mixing legacy V3 examples with GX Core `1.x` code | Bootstraps become brittle because object names, factories, and checkpoint APIs differ. | Pin GX Core version, use current docs, and test bootstrap scripts in CI. |

These patterns also imply ownership. A data-quality suite without an owner is a stale contract waiting to happen. The owner may be the data-producing team, the feature-platform team, or the ML platform team. The right owner depends on where the expectation gets its meaning. If the expectation says `currency_code` must be one of three values, the producer and product owner need to approve changes.

If the expectation says a feature vector must contain the model's required columns, the model or feature-platform owner needs to approve changes. If the expectation says the validation Job must publish Data Docs and exit non-zero, the platform owner needs to approve changes. Separate technical ownership from semantic ownership. The person who maintains the runner may not be the person who can decide that a new currency is legitimate. That distinction prevents two bad outcomes.

First, platform engineers are not forced to approve business meaning they do not own. Second, domain owners cannot bypass operational controls by treating them as implementation details. Versioning is the next ownership layer. Pin the GX version in the lab, CI image, and production image. The API changed enough across legacy V3, GX Core `1.0`, and later `1.x` releases that "latest" is not a deployment strategy.

Pinning does not mean never upgrading. It means upgrading intentionally. An upgrade PR should run the checkpoint scripts, compare generated suite files, and confirm that Data Docs still build. That upgrade PR is the right place to handle `add_or_update` behavior changes, factory-name changes, and output-shape changes. Do not discover those changes during an incident.

Suite size deserves the same discipline. Large suites feel reassuring because they contain many checks. They can also hide signal. If a single checkpoint emits dozens of low-value failures, responders may miss the one failure that matters. Group expectations by operational purpose.

Cheap schema and identity expectations can run everywhere. Business-semantic expectations should block data releases. Heavier distribution expectations may run in scheduled gates with richer compute. That grouping keeps validation fast enough to be trusted. It also makes failure routing clearer.

A missing column pages a different owner than a slow distribution drift. A DVC baseline change with no suite diff may be routine. A suite diff with no data change may be a contract cleanup. A data diff and suite diff together is a design review. Treat those combinations differently.

That is how you keep Great Expectations from becoming a pile of JSON files no one wants to touch. The final operating pattern is to write the failure message for the person who has to act. The checkpoint output should not just say "validation failed." It should identify the suite, batch, expectation, column, observed value, and Data Docs location. If you send alerts, include those fields.

If you attach artifacts to a pipeline run, name them consistently. If you publish Data Docs, include the run ID in the path or metadata. The goal is a short path from failure to decision. Should the producer fix the export? Should the suite change?

Should the model retraining wait? Should a temporary exception be granted? Patterns and anti-patterns are useful only when they make those decisions easier. The strongest pattern is the combination of failure-by-default and suite-as-code. One without the other is incomplete.

Failure-by-default without review creates brittle pipelines that everyone wants to bypass. Suite-as-code without failure behavior creates beautiful contracts no one obeys. Together, they make data contracts operational.

## Decision Framework

Use this framework when adding Great Expectations to an MLOps workflow so you place validation near the right owner and gate:

```text
Start
  |
  v
Is the dataset a source-of-truth export?
  |-- yes --> Validate schema and required fields near the producer.
  |            Store suite as code with producer ownership.
  |
  |-- no --> Is it a training or scoring snapshot?
              |-- yes --> Bind suite to DVC or snapshot identity.
              |            Fail the training or scoring gate on checkpoint failure.
              |
              |-- no --> Is it an exploratory notebook dataset?
                          |-- yes --> Profile for discovery, but do not treat the
                          |            generated suite as production without review.
                          |
                          |-- no --> Define the owner and contract before writing
                                      expectations.
```

For runtime placement, use this matrix to choose inline Python, orchestrator tasks, or Kubernetes Jobs and CronJobs:

| Decision question | Choose inline Python | Choose orchestrator task | Choose Kubernetes Job or CronJob |
|---|---|---|---|
| Dataset size | Small or moderate | Moderate or large | Moderate or large, cluster-local |
| Ownership | One pipeline team | Platform-managed DAG | Platform or data platform team |
| Failure visibility | CI status and logs are enough | DAG status is the main interface | Kubernetes status and ArgoCD health matter |
| Data location | Local files or mounted object sync | Warehouse, lake, or shared storage | PVC, object-store mount, or in-cluster processing |
| Cost control | Keep suite small, sample explicitly | Schedule and resource pools | Requests, limits, node pools, and retention |
| Best use | Fast PR gate | Production ML pipeline | Scheduled validation and cluster-native gates |

For expectation scope, use this rule: Validate what would change a downstream decision. Do not validate trivia. Do validate primary keys, required columns, join keys, enumerations, units, timestamp ranges, feature ranges, and completeness assumptions. Do not validate every observed mean, every exact row count, or every string length unless those facts are real contracts.

For suite updates, use this rule: If the data changed and the suite changed, require a human explanation. That explanation should say whether the change is a producer bug, a legitimate product expansion, a feature-engineering change, or a model-risk exception. For incidents, use this rule: If a checkpoint fails, the first response is not "make it green". The first response is "identify which contract failed and whether the data or the contract is wrong." That keeps the gate honest.

## Did You Know?

1. GX Core `1.16.1` is the current public documentation version verified for this module, and its Python package requires Python `3.10` through `3.13`; a Python `3.14` environment will not install it cleanly.
2. A file-backed GX context stores suite and checkpoint definitions under `gx/`, while validation results and local Data Docs default under `gx/uncommitted/`, which is a useful boundary between reviewed contracts and runtime artifacts.
3. Data Docs are static HTML, so they can be served by a simple loopback HTTP server during a lab or uploaded to private object storage in production.
4. GX result formats such as `BASIC`, `SUMMARY`, and `COMPLETE` change how much validation detail is stored; detailed unexpected-row capture is useful during debugging but can become expensive on large datasets.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| Treating a profiler suite as production-ready | Profilers infer observed facts, not business intent. | Trim the suite to reviewed contracts and document why each expectation exists. |
| Updating suites whenever data changes | Teams want green pipelines and mistake drift for evolution. | Review suite changes with DVC diffs, model-impact notes, and owner approval. |
| Validating only after training | The pipeline already spent compute and may have produced bad artifacts. | Put checkpoints before training, scoring, and promotion gates. |
| Ignoring GX version drift | Search results mix legacy V3 and current GX Core APIs. | Pin `great_expectations==1.16.1` for the lab and cite current docs in implementation notes. |
| Letting checkpoint failures be advisory | No one wants a data-quality gate to block work at first. | Make failure behavior explicit: non-zero exit, failed task, failed Job, or alert with owner. |
| Capturing too much Data Docs detail forever | Full unexpected samples are helpful once and costly forever. | Tune result format and apply retention to old validation artifacts. |
| Running large suites in the wrong region | Validation reads data across storage-region boundaries. | Run validation near the data or replicate immutable snapshots deliberately. |
| Sharing no suite between training and serving | Each boundary drifts independently and skew hides until model metrics degrade. | Share core schema and semantic expectations, then add environment-specific overlays. |

## Quiz

<details>
<summary>Your fraud model's code and container image did not change, but precision dropped after a vendor CSV delivery. The pipeline accepted the file and trained successfully. What should you check first, and why?</summary>

Start with the data contract, not the model code.
Check whether required columns changed, whether key columns became null, whether enumerated values changed, and whether numeric ranges shifted.
The important clue is that the pipeline accepted the file, which means the failure may be silent schema or semantic drift.
A Great Expectations checkpoint should have failed before training if the suite covered the affected contract.
</details>

<details>
<summary>A profiler generated an expectation that yesterday's export must have exactly six rows. Your daily export usually has thousands of rows. Should this expectation stay in the production suite?</summary>

No, not as written.
The profiler observed a fact about one small baseline, but the production contract is not "exactly six rows."
If row count matters, replace it with a realistic lower bound, upper bound, or freshness check tied to business volume.
Keeping the exact count would create false alarms and teach the team to distrust the suite.
</details>

<details>
<summary>A pull request updates `dvc.lock` and also adds `BTC` to the accepted `currency_code` set. What review questions should block approval until answered?</summary>

Ask whether `BTC` is a legitimate product change or contaminated input.
Ask whether feature engineering and serving code can encode the new value consistently.
Ask whether historical training data, model evaluation, and monitoring slices were updated to account for it.
The suite change may be correct, but it is a semantic contract change and should not be hidden inside a data refresh.
</details>

<details>
<summary>Your team runs a checkpoint in CI, but the script catches failure, prints a warning, and exits successfully so training can continue. What is the operational problem?</summary>

The checkpoint is advisory, not a gate.
The system has converted a failed data contract into log noise, which is exactly how silent drift reaches model artifacts.
The fix is to return a non-zero exit when `result.success` is false, then attach Data Docs so the failure is easy to investigate.
If the gate must be bypassed, require an explicit exception with owner and expiry.
</details>

<details>
<summary>A checkpoint against a multi-GB table is too slow for pull-request validation. What design would preserve safety without making every PR wait for a full scan?</summary>

Split validation by cost and risk.
Run cheap schema, nullability, and configuration checks in PR, possibly against a deterministic stratified sample.
Run full-table distribution checks in a nightly or release gate near the data.
Document the sampling strategy so a sampled pass is not mistaken for full-table evidence.
</details>

<details>
<summary>Data Docs show that global email completeness is acceptable, but a regional model is still failing. What limitation are you seeing?</summary>

A global expectation can hide slice-specific failures.
If one region has a much higher null rate, the overall `mostly` threshold may still pass.
Data Docs are useful evidence for the expectations you ran, but they are not a substitute for high-cardinality slice monitoring or time-series drift analysis.
Add region-aware validation or monitoring where that slice matters.
</details>

<details>
<summary>A bootstrap script copied from an old tutorial uses `RuntimeBatchRequest` and `context.add_or_update_checkpoint`, while the rest of the project uses GX Core `1.16.1`. What is the risk?</summary>

The project is mixing legacy V3-era examples with the current GX Core object model.
That can create brittle configuration, confusing file layout, and APIs that do not match the installed package.
Pin the GX version, use current docs, and rewrite the bootstrap around `context.data_sources`, `context.suites`, `context.validation_definitions`, and `context.checkpoints`.
Then run the script in CI so API drift is caught early.
</details>

## Hands-On Exercise: Great Expectations Gate on kind

In this lab, you will build a working GX Core `1.16.1` setup for a transaction dataset. You will profile a baseline CSV, curate the suite, run a checkpoint against drifted data, generate Data Docs, and package the checkpoint as a Kubernetes Job. The Kubernetes examples assume kind or minikube with Kubernetes `1.35+`. The local Python examples pin Python `3.13` because GX Core `1.16.1` does not install on Python `3.14`. The current GX Core package installed from PyPI does not provide a `great_expectations` CLI entry point in this environment. Older workflows may tell you to run `great_expectations init`. For GX Core `1.16.1`, the supported equivalent in this lab is `gx.get_context(mode="file")`, which creates the same file-backed `gx/` project structure.

### Task 1: Create the project and baseline data

```bash
mkdir gx-transactions-quality
cd gx-transactions-quality

uv venv --seed --python 3.13 .venv
.venv/bin/python -m pip install great_expectations==1.16.1 pandas pyyaml jsonschema

mkdir -p data scripts schemas suites
cat > data/transactions.csv <<'CSV'
transaction_id,account_id,amount,currency_code,email,event_ts
TXN-1001,ACC-100,12.25,USD,ava@example.test,2026-05-18T08:10:00Z
TXN-1002,ACC-101,90.00,EUR,ben@example.test,2026-05-18T08:11:00Z
TXN-1003,ACC-102,44.80,GBP,cy@example.test,2026-05-18T08:12:00Z
TXN-1004,ACC-103,18.30,USD,dia@example.test,2026-05-18T08:13:00Z
TXN-1005,ACC-104,205.20,EUR,eli@example.test,2026-05-18T08:14:00Z
TXN-1006,ACC-105,31.10,USD,fay@example.test,2026-05-18T08:15:00Z
CSV

cat > data/transactions_drift.csv <<'CSV'
transaction_id,account_id,amount,CURR_CD,email,event_ts
TXN-2001,ACC-200,1225.00,USD,,2026-05-19T08:10:00Z
TXN-2002,ACC-201,9000.00,BTC,han@example.test,2026-05-19T08:11:00Z
TXN-2003,ACC-202,4480.00,EUR,,2026-05-19T08:12:00Z
TXN-2004,ACC-203,1830.00,USD,ivy@example.test,2026-05-19T08:13:00Z
CSV
```

If your platform image still exposes a legacy CLI, the optional command below may scaffold a project before you create the file-backed context manually:

```bash
command -v great_expectations >/dev/null 2>&1 && great_expectations init || true
```

For the pinned GX Core version used here, create the file context with the supported Python API and register the baseline and drift CSV batch definitions:

```bash
cat > scripts/bootstrap_gx.py <<'PY'
import great_expectations as gx

context = gx.get_context(mode="file")
data_source = context.data_sources.add_or_update_pandas_filesystem(
    name="transactions_fs",
    base_directory="data",
)
asset = data_source.add_csv_asset(name="transactions_csv")
asset.add_batch_definition_path(name="baseline", path="transactions.csv")
asset.add_batch_definition_path(name="drift", path="transactions_drift.csv")
print(f"GX project root: {context.root_directory}")
PY

.venv/bin/python scripts/bootstrap_gx.py
```

Confirm Task 1 succeeded using the following success criteria before you move on to profiling and suite curation:

- [ ] `gx/great_expectations.yml` exists.
- [ ] `gx/expectations/` exists.
- [ ] `data/transactions.csv` and `data/transactions_drift.csv` exist.
- [ ] The bootstrap command prints the GX project root.

<details>
<summary>Solution notes</summary>

The important step is the file-backed context.
It creates a durable `gx/` directory that can be committed, reviewed, and reused by CI.
The Data Source points at the local `data/` directory, while the Data Asset and Batch Definitions distinguish the baseline file from the drifted file.
</details>

### Task 2: Profile the baseline and curate the suite

Create a small profiler script that proposes expectations from the baseline CSV and writes the candidate suite to YAML for review:

```bash
cat > scripts/profile_transactions.py <<'PY'
from pathlib import Path

import pandas as pd
import yaml

baseline = pd.read_csv("data/transactions.csv")

profile = {
    "suite_name": "transactions.profiled",
    "expectations": [
        {
            "type": "expect_table_columns_to_match_ordered_list",
            "column_list": list(baseline.columns),
        },
        {
            "type": "expect_table_row_count_to_be_between",
            "min_value": int(len(baseline)),
            "max_value": int(len(baseline)),
        },
        {"type": "expect_column_values_to_not_be_null", "column": "transaction_id"},
        {"type": "expect_column_values_to_be_unique", "column": "transaction_id"},
        {"type": "expect_column_values_to_not_be_null", "column": "email"},
        {
            "type": "expect_column_values_to_be_in_set",
            "column": "currency_code",
            "value_set": sorted(baseline["currency_code"].unique().tolist()),
        },
        {
            "type": "expect_column_values_to_be_between",
            "column": "amount",
            "min_value": float(baseline["amount"].min()),
            "max_value": float(baseline["amount"].max()),
        },
        {
            "type": "expect_column_values_to_match_regex",
            "column": "transaction_id",
            "regex": "^TXN-[0-9]+$",
        },
    ],
}

Path("suites").mkdir(exist_ok=True)
Path("suites/transactions_profiled.yml").write_text(
    yaml.safe_dump(profile, sort_keys=False),
)
print("wrote suites/transactions_profiled.yml")
PY

.venv/bin/python scripts/profile_transactions.py
```

Now curate the final production suite down to five reviewed expectations that catch real contract failures instead of profiler noise:

```bash
cat > suites/transactions_critical.yml <<'YAML'
suite_name: transactions.critical
expectations:
  - type: expect_table_columns_to_match_ordered_list
    column_list: [transaction_id, account_id, amount, currency_code, email, event_ts]
  - type: expect_column_values_to_not_be_null
    column: transaction_id
  - type: expect_column_values_to_be_unique
    column: transaction_id
  - type: expect_column_values_to_be_in_set
    column: currency_code
    value_set: [USD, EUR, GBP]
  - type: expect_column_values_to_be_between
    column: amount
    min_value: 0
    max_value: 500
YAML
```

Add the JSON Schema guard so suite YAML typos fail in CI before Great Expectations runs the checkpoint:

```bash
cat > schemas/suite-policy.schema.json <<'JSON'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["suite_name", "expectations"],
  "properties": {
    "suite_name": { "type": "string", "minLength": 3 },
    "expectations": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["type"],
        "properties": {
          "type": { "type": "string" },
          "column": { "type": "string" },
          "column_list": {
            "type": "array",
            "items": { "type": "string" }
          },
          "value_set": {
            "type": "array",
            "items": { "type": "string" }
          },
          "min_value": { "type": "number" },
          "max_value": { "type": "number" },
          "mostly": { "type": "number", "minimum": 0, "maximum": 1 }
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false
}
JSON
```

Confirm Task 2 succeeded using the following success criteria so the curated suite is ready for checkpoint execution:

- [ ] `suites/transactions_profiled.yml` contains eight candidate expectations.
- [ ] `suites/transactions_critical.yml` contains five reviewed expectations.
- [ ] The final suite catches schema, identity, enumeration, and amount-range failures.

<details>
<summary>Solution notes</summary>

The row-count expectation was removed because the daily export should grow.
The exact observed amount range was widened because production amounts can vary.
The email expectation was removed from the critical suite in this lab so the drift file demonstrates schema and amount failures cleanly.
In a real platform, you may add a separate email completeness expectation with a realistic `mostly` threshold.
</details>

### Task 3: Build and run the checkpoint

Create a checkpoint runner script that converts the curated YAML into Great Expectations objects and fails with a non-zero exit code on drift:

```bash
cat > scripts/gx_validate.py <<'PY'
from pathlib import Path

import great_expectations as gx
from great_expectations import expectations as gxe
from jsonschema import validate
import yaml


def load_policy() -> dict:
    policy = yaml.safe_load(Path("suites/transactions_critical.yml").read_text())
    schema = yaml.safe_load(Path("schemas/suite-policy.schema.json").read_text())
    validate(policy, schema)
    return policy


def to_expectation(config: dict):
    expectation_type = config["type"]
    if expectation_type == "expect_table_columns_to_match_ordered_list":
        return gxe.ExpectTableColumnsToMatchOrderedList(
            column_list=config["column_list"],
        )
    if expectation_type == "expect_column_values_to_not_be_null":
        return gxe.ExpectColumnValuesToNotBeNull(column=config["column"])
    if expectation_type == "expect_column_values_to_be_unique":
        return gxe.ExpectColumnValuesToBeUnique(column=config["column"])
    if expectation_type == "expect_column_values_to_be_in_set":
        return gxe.ExpectColumnValuesToBeInSet(
            column=config["column"],
            value_set=config["value_set"],
        )
    if expectation_type == "expect_column_values_to_be_between":
        return gxe.ExpectColumnValuesToBeBetween(
            column=config["column"],
            min_value=config["min_value"],
            max_value=config["max_value"],
        )
    raise ValueError(f"Unsupported expectation type: {expectation_type}")


def main() -> None:
    context = gx.get_context(mode="file")
    data_source = context.data_sources.add_or_update_pandas_filesystem(
        name="transactions_fs",
        base_directory="data",
    )
    try:
        asset = data_source.add_csv_asset(name="transactions_csv")
    except Exception:
        asset = data_source.get_asset("transactions_csv")
    try:
        drift_batch = asset.add_batch_definition_path(
            name="drift",
            path="transactions_drift.csv",
        )
    except Exception:
        drift_batch = asset.get_batch_definition("drift")

    policy = load_policy()
    suite = gx.ExpectationSuite(name=policy["suite_name"])
    for item in policy["expectations"]:
        suite.add_expectation(to_expectation(item))
    suite = context.suites.add_or_update(suite)

    validation_definition = gx.ValidationDefinition(
        name="transactions_drift_validation",
        data=drift_batch,
        suite=suite,
    )
    validation_definition = context.validation_definitions.add_or_update(
        validation_definition,
    )

    checkpoint = gx.Checkpoint(
        name="transactions_checkpoint",
        validation_definitions=[validation_definition],
        result_format={"result_format": "SUMMARY"},
    )
    checkpoint = context.checkpoints.add_or_update(checkpoint)
    result = checkpoint.run()
    context.build_data_docs(site_names="local_site")

    print(yaml.safe_dump(result.describe_dict(), sort_keys=False))
    if not result.success:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
PY

.venv/bin/python scripts/gx_validate.py
```

The command should fail. That is correct. The drift file changed the header, introduced a new currency code, left some email values blank, and shifted amounts upward by ten times. This curated suite is expected to catch the header drift and amount shift. The missing email values are visible in the drift file, but the final suite does not gate on email in this lab. That is intentional so you can see that untested assumptions do not magically fail. Confirm Task 3 succeeded using the following success criteria before you inspect Data Docs:

- [ ] The checkpoint exits non-zero.
- [ ] The output shows `success: false`.
- [ ] The ordered column expectation reports `CURR_CD` where `currency_code` was expected.
- [ ] The amount expectation fails because values exceed `500`.
- [ ] You can explain which drift was not caught and why.

<details>
<summary>Solution notes</summary>

The failure is the point of the lab.
If the command exits successfully, check that `transactions_drift.csv` still has `CURR_CD` and high amounts.
If the script cannot find the Data Source, rerun `scripts/bootstrap_gx.py`.
If JSON Schema validation fails, inspect the curated YAML for a typo such as `value_sets`.
</details>

### Task 4: Generate and preview Data Docs

The checkpoint runner already calls `context.build_data_docs(...)`. Preview the generated static site:

```bash
.venv/bin/python -m http.server 8008 --bind 127.0.0.1 --directory gx/uncommitted/data_docs/local_site
```

Open `http://127.0.0.1:8008/` and look for the failed `transactions_checkpoint` run. Confirm Task 4 succeeded using the following success criteria before you containerize the checkpoint:

- [ ] The Data Docs index loads on `127.0.0.1`.
- [ ] The failed suite is visible.
- [ ] You can identify the failing expectations without reading raw Pod logs.

<details>
<summary>Solution notes</summary>

Data Docs are static files, so a loopback-only HTTP server is enough for local inspection.
In production, publish them to a private static host, upload them as CI artifacts, or attach them to model registry evidence.
Do not publish raw validation artifacts publicly if they can contain customer rows or sensitive columns.
</details>

### Task 5: Containerize the checkpoint as a Kubernetes Job

Create a minimal container image that packages the checkpoint runner and its Python dependencies for Kubernetes execution:

```bash
cat > requirements.txt <<'REQ'
great_expectations==1.16.1
pandas
pyyaml
jsonschema
REQ

cat > Dockerfile <<'DOCKER'
FROM ghcr.io/astral-sh/uv:bookworm-slim
WORKDIR /workspace
COPY requirements.txt .
RUN uv venv --seed --python 3.13 .venv
RUN .venv/bin/python -m pip install --no-cache-dir -r requirements.txt
COPY scripts/gx_validate.py scripts/gx_validate.py
ENTRYPOINT [".venv/bin/python", "scripts/gx_validate.py"]
DOCKER

docker build -t kubedojo/gx-checkpoint:1.16.1-lab .
kind load docker-image kubedojo/gx-checkpoint:1.16.1-lab
```

Create a namespace, ConfigMap, PVC, and data-loader Job so the drift CSV is available on a cluster volume before validation runs:

```bash
kubectl create namespace gx-lab --dry-run=client -o yaml | kubectl apply -f -

kubectl -n gx-lab create configmap gx-suite \
  --from-file=suites/transactions_critical.yml \
  --from-file=schemas/suite-policy.schema.json \
  --dry-run=client -o yaml | kubectl apply -f -

cat > k8s-pvc.yml <<'YAML'
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: transactions-data
  namespace: gx-lab
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
YAML

kubectl apply -f k8s-pvc.yml

cat > k8s-load-data.yml <<'YAML'
apiVersion: batch/v1
kind: Job
metadata:
  name: load-transactions-drift
  namespace: gx-lab
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: load
          image: busybox:1.36
          command:
            - /bin/sh
            - -c
            - |
              mkdir -p /workspace/data
              cat > /workspace/data/transactions_drift.csv <<'CSV'
              transaction_id,account_id,amount,CURR_CD,email,event_ts
              TXN-2001,ACC-200,1225.00,USD,,2026-05-19T08:10:00Z
              TXN-2002,ACC-201,9000.00,BTC,han@example.test,2026-05-19T08:11:00Z
              TXN-2003,ACC-202,4480.00,EUR,,2026-05-19T08:12:00Z
              TXN-2004,ACC-203,1830.00,USD,ivy@example.test,2026-05-19T08:13:00Z
              CSV
          volumeMounts:
            - name: data
              mountPath: /workspace/data
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: transactions-data
YAML

kubectl apply -f k8s-load-data.yml
kubectl -n gx-lab wait --for=condition=complete job/load-transactions-drift --timeout=120s
```

Now run the checkpoint Job and confirm Kubernetes surfaces the expected non-zero failure instead of hiding it behind restarts:

```bash
cat > k8s-gx-job.yml <<'YAML'
apiVersion: batch/v1
kind: Job
metadata:
  name: gx-transactions-checkpoint
  namespace: gx-lab
spec:
  backoffLimit: 0
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: gx
          image: kubedojo/gx-checkpoint:1.16.1-lab
          imagePullPolicy: IfNotPresent
          workingDir: /workspace
          volumeMounts:
            - name: suite
              mountPath: /workspace/suites
            - name: suite
              mountPath: /workspace/schemas
            - name: data
              mountPath: /workspace/data
      volumes:
        - name: suite
          configMap:
            name: gx-suite
        - name: data
          persistentVolumeClaim:
            claimName: transactions-data
YAML

kubectl apply -f k8s-gx-job.yml
kubectl -n gx-lab wait --for=condition=failed job/gx-transactions-checkpoint --timeout=120s
kubectl -n gx-lab logs job/gx-transactions-checkpoint
```

The Job should fail because the checkpoint exits non-zero. `restartPolicy: Never` prevents the Pod from hiding the failure behind restarts. A CronJob built from the same template would mark the scheduled run failed and keep failed history according to its history limits. The absolute mount paths above are container paths required by Kubernetes, not host-machine paths. Confirm Task 5 succeeded using the following success criteria before you wire the Argo Workflow gate:

- [ ] The image builds and loads into kind.
- [ ] The data-loader Job completes.
- [ ] The GX Job fails.
- [ ] The Pod logs contain the failed checkpoint result.

<details>
<summary>Solution notes</summary>

If the Job succeeds, inspect the drift CSV mounted in the PVC and confirm it contains `CURR_CD`.
The script bootstraps the filesystem Data Source at runtime, so the ConfigMap only needs the reviewed suite and the JSON Schema guard.
For a production image, you can instead mount a reviewed `gx/` directory when the Data Source, Checkpoint, and site settings are owned as configuration.
</details>

### Task 6: Halt an Argo Workflow on validation failure

The Argo pattern is to make data validation an upstream template. If the GX container exits non-zero, Argo does not run the training task.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: gx-ml-gate-
  namespace: gx-lab
spec:
  entrypoint: gated-training
  templates:
    - name: gated-training
      dag:
        tasks:
          - name: validate-data
            template: gx-checkpoint
          - name: train-model
            dependencies: [validate-data]
            template: train

    - name: gx-checkpoint
      container:
        image: kubedojo/gx-checkpoint:1.16.1-lab
        imagePullPolicy: IfNotPresent
        workingDir: /workspace
        volumeMounts:
          - name: suite
            mountPath: /workspace/suites
          - name: suite
            mountPath: /workspace/schemas
          - name: data
            mountPath: /workspace/data

    - name: train
      container:
        image: ghcr.io/astral-sh/uv:bookworm-slim
        command: ["/bin/sh", "-c"]
        args:
          - |
            echo "training would start only after validation succeeds"

  volumes:
    - name: suite
      configMap:
        name: gx-suite
    - name: data
      persistentVolumeClaim:
        claimName: transactions-data
```

Notice what is missing. There is no `continueOn` override. There is no wrapper that turns failure into success. The DAG edge from `validate-data` to `train-model` means training depends on validation success. Confirm Task 6 succeeded using the following success criteria before you leave the lab:

- [ ] You can explain why `train-model` does not run after a failed checkpoint.
- [ ] You can point to the non-zero checkpoint exit as the control signal.
- [ ] You can describe where Data Docs or validation artifacts would be attached in your platform.

<details>
<summary>Solution notes</summary>

In a production Argo installation, publish Data Docs or checkpoint JSON as workflow artifacts.
Also add resource requests, timeouts, and owner labels.
The key learning goal is that the validation template is a required upstream task, not a side report.
</details>

## Sources

- [GX Core overview](https://docs.greatexpectations.io/docs/core/introduction/gx_overview/) — mental model for Expectations, Checkpoints, and Data Docs in GX Core `1.x`.
- [Filesystem data connections](https://docs.greatexpectations.io/docs/core/connect_to_data/filesystem_data/) — how to register CSV and Parquet assets for batch validation.
- [SQL data connections](https://docs.greatexpectations.io/docs/core/connect_to_data/sql_data/) — validating warehouse tables without copying full exports locally.
- [Create an Expectation](https://docs.greatexpectations.io/docs/core/define_expectations/create_an_expectation/) — authoring individual assertions that become suite contracts.
- [Run a Checkpoint](https://docs.greatexpectations.io/docs/core/trigger_actions_based_on_results/run_a_checkpoint/) — executable validation jobs that gate downstream pipeline steps.
- [Configure Data Docs](https://docs.greatexpectations.io/docs/core/configure_project_settings/configure_data_docs/) — generating static HTML evidence for failed gates and incident response.
- [Expectations API reference](https://docs.greatexpectations.io/docs/reference/api/expectations/) — canonical expectation class names and parameters for GX Core `1.16.1`.
- [DataContext API reference](https://docs.greatexpectations.io/docs/reference/api/data_context/) — file-backed project layout, suites, checkpoints, and validation definitions.
- [DVC data versioning](https://dvc.org/doc/start/data-management/data-versioning) — tracking dataset snapshots that expectation suites should bind to as reviewed baselines.
- [Pandera documentation](https://pandera.readthedocs.io/en/stable/) — schema-first DataFrame validation that complements expectation suites in Python pipelines.
- [Evidently documentation](https://docs.evidentlyai.com/) — drift reports and monitoring views that extend static checkpoint evidence over time.
- [Soda documentation](https://docs.soda.io/) — alternative SQL-first data-quality checks useful when teams already standardize on warehouse-native contracts.
- [Data Validation for Machine Learning (Breck et al., 2019)](https://arxiv.org/abs/1903.05134) — research framing for treating data contracts as first-class ML release controls.

## Next Module

Next: [Module 5.9: ML Repository Hygiene](../module-5.9-ml-repository-hygiene/) will connect data-quality gates, DVC metadata, model artifacts, and CI policy into a maintainable ML repository layout.
