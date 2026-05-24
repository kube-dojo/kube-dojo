---
citations_verified: true
title: "Module 5.7: Data Versioning with DVC"
slug: platform/disciplines/data-ai/mlops/module-5.7-dvc-data-versioning
sidebar:
  order: 8
---

> **Discipline Track** | Complexity: `[COMPLEX]` | Time: 50-60 min

## Prerequisites

Before starting this module:

- [Module 5.2: Feature Engineering & Stores](../module-5.2-feature-stores/)
- [Module 5.3: Model Training & Experimentation](../module-5.3-model-training/)
- [Module 5.6: ML Pipelines & Automation](../module-5.6-ml-pipelines/)
- Basic Git workflow, including branches, commits, remotes, and pull requests
- Familiarity with Git LFS is helpful, but not required
- Comfort reading YAML
- Comfort treating a hash as a content-addressed identifier

## Learning Outcomes

After completing this module, you will be able to:

- **Diagnose** model regressions where the code commit is unchanged but the training data shifted.
- **Implement** DVC tracking for datasets, models, metrics, plots, pipeline stages, and S3-compatible remote storage.
- **Evaluate** DVC against Git LFS, bucket snapshots, feature stores, and Kubeflow Pipelines for real ML platform work.
- **Design** a reproducible data-versioning workflow that separates Git metadata, DVC cache objects, and cloud object storage.
- **Configure** DVC remotes for local, development, production, and CI/CD contexts without committing credentials.
- **Debug** practitioner failure modes such as missing remote objects, checksum drift, cache lock leftovers, and runner permission errors.
- **Estimate** the cost impact of cache growth, cloud egress, lifecycle policies, and long-running CI jobs.

## Why This Module Matters

A model promotion fails on Tuesday.

The deployment team rolls back the service image.

The code diff is empty.

The model artifact is different.

The training notebook claims the same parameters.

The experiment tracker shows the same training script.

The only thing that moved was yesterday's data export.

That is the data-versioning problem.

The problem is not that teams forget to save files.

The problem is that "the data" is usually many objects, from many places, produced by many jobs, with many implicit assumptions.

A production model is not defined by code alone.

It is defined by code, parameters, input data, feature definitions, training environment, model artifact, metrics, validation results, and promotion evidence.

Earlier in this track, [Module 5.2](../module-5.2-feature-stores/) showed why feature values need a stable contract.

[Module 5.3](../module-5.3-model-training/) showed why experiment tracking needs data and parameter evidence, not just loss curves.

[Module 5.6](../module-5.6-ml-pipelines/) showed how ML pipelines turn that evidence into gates.

DVC connects those ideas to Git.

It gives a repository a way to say:

"This commit used this exact dataset object, this exact parameter file, and these exact outputs."

That sentence is the difference between a reproducible ML system and a collection of files that happened to exist at the same time.

The rest of this module treats DVC as an engineering system, not a command reference.

You will learn when it is the right tool.

You will learn when it is the wrong tool.

You will build a small DVC pipeline against MinIO on kind.

You will also practice the operational thinking that matters after the happy-path demo is over.

## Core Content

## 1. The Data-Versioning Problem

Git is excellent at versioning source code.

It is poor at storing large, frequently changing datasets directly.

Large binary files inflate clones, slow down fetches, and make ordinary repository operations painful.

Git LFS improves that by replacing large files with pointer files while the real payload lives in external storage.

That is useful.

It is not the whole MLOps data-versioning problem.

Git LFS tracks file payloads.

DVC tracks file payloads plus ML-oriented pipeline structure, dependency hashes, parameter values, metrics, plots, and remote cache transfer.

The difference matters most when a model regresses and code did not change.

Imagine a churn model with this promotion history:

```text
commit A: code=v1  params=C=0.5  data=customers-2026-05-10  auc=0.89
commit B: code=v1  params=C=0.5  data=customers-2026-05-11  auc=0.78
```

The application team checks the code diff.

There is no code diff.

The model team checks the hyperparameters.

There is no parameter diff.

The data team checks the export job.

The export job succeeded.

The operational question is sharper:

Which exact rows, schema, labels, and feature values changed between the two training runs?

Without data versioning, the answer is often "whatever was in the bucket at the time."

That answer is not auditable.

That answer is not bisectable.

That answer is not enough to roll back confidently.

A model's data version should include every input that can change the learned artifact.

That includes the raw source snapshot.

It includes the cleaned or joined training table if that table is materialized.

It includes labels.

It includes generated feature matrices.

It includes train, validation, and test split boundaries.

It includes any lookup tables used during preprocessing.

It includes files that look small but change semantics, such as vocabulary maps, encoders, and schema contracts.

It does not include every byte in an upstream warehouse.

It does not include every object in a lake.

It includes the exact dependency boundary the training job consumed.

This boundary is a design decision.

If the training job reads a curated Parquet dataset, that Parquet directory is the dependency.

If the training job queries a feature store by event timestamp, the point-in-time retrieval result is the dependency.

If the training job reads a CSV produced by an export job, that CSV is the dependency.

The production contract is not "we can rebuild data from the lake someday."

The production contract is "we can prove which data built this artifact."

Git LFS alone is often too flat for that contract.

It knows a file changed.

It does not know that `train.py` depended on `params.yaml`, produced `model.pkl`, wrote `metrics.json`, and skipped the `load` stage because the raw CSV hash was unchanged.

It does not describe a DAG.

It does not make metrics and plots first-class ML outputs.

It does not decide which stages to re-run after a parameter change.

Bucket snapshots have the opposite weakness.

They can preserve a broad storage state, but they are usually too wide.

A snapshot of an S3 bucket may include unrelated objects, temporary exports, partial writes, old partitions, and outputs from other teams.

It may also miss the Git commit, parameter file, and training script that consumed those objects.

It answers "what did the bucket contain?"

It does not answer "which byte-level inputs produced this model?"

Rollback has the same shape.

If a service rollback points to a previous container image but the retraining job pulls today's data, the rollback is not a true ML rollback.

It is a code rollback with a new data dependency.

A real ML rollback needs a data pointer.

It needs the corresponding model object.

It needs the metric evidence that justified the previous promotion.

It needs the remote cache objects still available.

This is why DVC exists in many small and mid-size ML platforms.

It is lightweight enough to live beside Git.

It is explicit enough to make data and model artifacts part of review.

It does not require every training job to run in a full platform before reproducibility improves.

It gives a path from messy files to reviewable artifacts.

### Worked Example: Bisecting a Data Regression

Suppose three commits exist on `main`.

```text
main~2  code A  params A  data hash aaa111  metric auc=0.88
main~1  code A  params A  data hash bbb222  metric auc=0.86
main    code A  params A  data hash ccc333  metric auc=0.73
```

The code and parameters are stable.

The metrics changed sharply.

With DVC, a responder can check out `main~1`, run `dvc pull`, and reproduce the prior dataset and model state.

Then the responder can check out `main`, run `dvc pull`, and inspect only the changed data dependencies.

The investigation is bounded.

The responder does not need to guess which bucket prefix was current during training.

The responder does not need to ask the export team whether files were overwritten.

The Git history points to DVC metadata, and the DVC metadata points to cache objects.

That is the operational win.

> **Active learning prompt:** A fraud model drops precision after the label export job is refactored. The training code, container image, and parameters are unchanged. What three artifacts would you compare first, and what would each comparison prove?

The best first comparison is usually not the raw file size.

File size can stay almost identical while labels shift.

Compare the DVC dependency hashes first.

That proves whether the byte-level inputs changed.

Compare data-quality summaries next.

That proves whether schema, nulls, label balance, or population changed.

Compare metrics and confusion matrices last.

That proves how the model behavior changed after the data shift.

This order reduces noise.

It also separates root cause from symptom.

The data version is the cause boundary.

The metric is the symptom boundary.

The model artifact is the produced object.

A mature incident report ties all three together.

## 2. DVC Core Model

DVC adds content-addressed artifact storage to a Git repository.

The core idea is simple.

Git stores small metadata files.

DVC stores large artifact content in a local cache.

DVC can also push that cache content to a remote store.

The official DVC `init` command creates a `.dvc/` directory for configuration, cache location, and internal files.

The official DVC `add` command tracks files or directories through lightweight `.dvc` pointer files.

That pointer file is committed to Git.

The large data file is not committed to Git.

The data content is placed in DVC's cache, usually under `.dvc/cache`.

The remote object store is a second copy for team sharing and CI.

Here is the shape:

```text
Git commit
  |
  +-- data/raw.csv.dvc
  |     |
  |     +-- hash: 9a12...        small pointer committed to Git
  |
  +-- dvc.yaml                   pipeline declaration committed to Git
  |
  +-- dvc.lock                   resolved dependency and output hashes committed to Git
  |
  +-- params.yaml                parameter values committed to Git
  |
  +-- .dvc/config                remote names, non-secret settings committed to Git
        |
        +-- .dvc/cache/...       large local content cache, not committed
        |
        +-- s3://bucket/...      shared remote cache, not committed to Git
```

The word "cache" can mislead beginners.

This cache is not disposable in the same way a browser cache is disposable.

The DVC cache is where the local copy of tracked artifact content lives.

If the same content was pushed to a remote, the local cache can be reclaimed and restored.

If the content was never pushed, deleting the only cache copy may delete the only recoverable copy.

That is why `dvc push` is not optional in a team workflow.

Git push shares metadata.

DVC push shares payloads.

You need both.

The official DVC `push` documentation states that pushing data does not affect code, `dvc.yaml`, or `.dvc` files.

Those still need Git.

This split is the first operational rule:

```text
git push  -> publishes DVC metadata, code, params, locks, and reviews
dvc push  -> publishes the large content addressed by that metadata
```

If a teammate receives the Git commit but cannot run `dvc pull`, the commit is incomplete for ML purposes.

This is the most common DVC collaboration failure.

It usually appears as "cache not found" or "failed to pull data from the cloud."

The cause is often that someone pushed Git metadata but forgot to push DVC objects.

The fix is not to change code.

The fix is to push the missing DVC objects from the machine or runner that has them.

DVC can track single files.

DVC can also track directories.

Directory tracking matters because ML datasets are often many small files.

When DVC tracks a directory, it does not create one `.dvc` file per child file.

It creates one top-level pointer file and a directory manifest in the cache.

That keeps Git reviewable while still making individual file content addressable.

This is one place where DVC usually wins over a naive "one archive per dataset version" pattern.

An archive hides internal file changes.

A DVC-tracked directory can preserve structure and deduplicate unchanged files.

Compressed monoliths are often operationally expensive.

They make small changes look like whole-dataset changes.

They reduce cache reuse.

They make partial pulls harder.

DVC's model is closer to Git's object model than to a backup tool.

The artifact content is addressed by hash.

If two branches produce identical file content, DVC can reuse the same cache object.

If only a few files in a directory change, the unchanged file objects can be reused.

This is why "small-and-many" can be a good pattern for DVC datasets when the files represent meaningful independent records or partitions.

There is a balance.

Millions of tiny files can still stress file systems and object storage listing behavior.

One giant ZIP file can destroy deduplication.

Practical teams usually choose partitioned formats such as Parquet directories, image folders, or moderately sized shard files.

### What Goes in Git

Commit these:

- `.dvc/config` when it contains only project-safe settings
- `.dvc/.gitignore`
- `.dvcignore` when used
- `*.dvc` pointer files
- `dvc.yaml`
- `dvc.lock`
- `params.yaml`
- training, loading, and evaluation code
- small schema files, test fixtures, and docs

Do not commit these:

- `.dvc/cache`
- `.dvc/tmp`
- `.dvc/config.local`
- raw training data payloads tracked by DVC
- model binaries tracked by DVC
- credentials
- generated plots and metrics if DVC owns them as outputs

There are exceptions for tiny educational fixtures.

Production model binaries do not belong directly in Git.

If a model artifact is small enough to commit, the habit is still dangerous.

It encourages reviewers to ignore binary diffs.

It bypasses the artifact cache.

It also makes rollback strategy inconsistent across model families.

### DVC vs Git LFS

Git LFS is excellent when a repository has a few large files that should follow normal Git checkout behavior.

Design assets, small model samples, and binary docs can be reasonable LFS candidates.

DVC wins when the artifact has ML lifecycle semantics.

That means data dependencies, pipeline stages, metrics, plots, parameters, cache sharing, and remote object stores.

Use this decision guide:

| Need | Prefer |
|------|--------|
| A few binary files that mostly behave like source assets | Git LFS |
| Training datasets that change by branch or experiment | DVC |
| Model binaries tied to metrics and parameters | DVC |
| Reviewable ML pipeline DAG with reproducible stage outputs | DVC |
| Large docs assets with no ML pipeline dependency | Git LFS |
| Full lakehouse table history, transactions, and concurrent writers | A table format or lake versioning layer, with DVC at the training boundary |

DVC is not a replacement for Delta Lake, Apache Iceberg, lakeFS, or a feature store.

Those tools solve broader data-platform problems.

DVC solves a repository-centered reproducibility problem.

It is strongest at the boundary where a training repo consumes materialized data and produces model evidence.

> **Active learning prompt:** A team has a 90 MB model card PDF, a 6 GB training CSV, a 200 MB tokenizer vocabulary, and a `metrics.json` file. Which should use Git, Git LFS, or DVC, and why?

A reasonable answer is:

The model card PDF can use Git LFS if the repo wants it versioned with docs.

The training CSV should use DVC.

The tokenizer vocabulary should use DVC if it is a training or inference dependency.

The metrics file should be tracked through DVC metrics if it is generated by a pipeline stage.

The key is not only file size.

The key is whether the file is part of the ML reproducibility contract.

## 3. dvc.yaml and params.yaml Pipelines

DVC can track standalone files with `.dvc` pointer files.

That is useful, but it is not enough for a training workflow.

Training is a process.

The process has inputs.

The process has parameters.

The process has outputs.

The process has metrics.

The process has plots.

DVC pipelines declare that process in `dvc.yaml`.

The resolved result is recorded in `dvc.lock`.

The official `dvc.yaml` documentation describes stage dependencies, outputs, metrics, plots, and parameter dependencies.

The official `dvc repro` command regenerates pipeline results by restoring the dependency graph and running only the stages that need to run.

That behavior is the heart of the reproducibility workflow.

It is also the reason DVC is not just "Git LFS for data."

Consider this three-stage pipeline:

```text
               params.yaml
                   |
                   v
+--------+     +---------+     +--------+
|  load  | --> |  train  | --> |  eval  |
+--------+     +---------+     +--------+
    |              |              |
    v              v              v
data/raw.csv   model.pkl      metrics.json
               holdout.csv    plots/cm.png
```

The `load` stage creates a raw CSV.

The `train` stage reads the CSV and parameters, then writes a model and a held-out split.

The `eval` stage reads the model and holdout data, then writes final metrics and plots.

That stage split is intentionally small.

It lets DVC prove that changing a training hyperparameter does not require reloading data.

It lets DVC prove that changing the raw fixture does require retraining and re-evaluation.

It lets a reviewer see where the model evidence came from.

The most important file in this design is not the model.

It is the lock file.

`dvc.lock` is the reproducibility artifact that binds dependency hashes, output hashes, commands, and resolved parameter values.

Do not treat it as generated noise.

Review it like a package lockfile.

Commit it when a pipeline output changes.

Ask why it changed.

If the only change is `train.C`, the lockfile should show the parameter difference and downstream output changes.

If the raw data hash changed unexpectedly, the lockfile is telling you the model is no longer trained on the same input.

That is valuable review evidence.

### Pipeline Example

`params.yaml` might look like this:

```yaml
train:
  C: 0.5
  test_size: 0.25
  seed: 42
  threshold: 0.5
```

`dvc.yaml` might look like this:

```yaml
stages:
  load:
    cmd: .venv/bin/python scripts/load.py
    deps:
      - scripts/load.py
    outs:
      - data/raw.csv

  train:
    cmd: .venv/bin/python scripts/train.py
    deps:
      - data/raw.csv
      - scripts/train.py
    params:
      - train.C
      - train.test_size
      - train.seed
    outs:
      - models/model.pkl
      - data/holdout.csv

  eval:
    cmd: .venv/bin/python scripts/eval.py
    deps:
      - models/model.pkl
      - data/holdout.csv
      - scripts/eval.py
    params:
      - train.threshold
    metrics:
      - metrics.json
    plots:
      - plots/cm.png
```

Notice the deliberate ownership rule.

Only one stage owns a given output path.

A common beginner mistake is to declare `metrics.json` as an output of both `train` and `eval`.

DVC will not let two stages own the same output path because the graph would be ambiguous.

In the lab, the training script writes a quick local `metrics.json` as a transient smoke signal.

The evaluation stage then overwrites it and declares it as the tracked metric.

That teaches the real rule:

DVC can tolerate a later command overwriting a file, but the pipeline declaration should give final ownership to one stage.

If you need both training and evaluation metrics, use distinct files such as `metrics-train.json` and `metrics.json`.

If you need one final metric file, let the final evaluation stage own it.

The same rule applies to plots.

Do not let `train` and `eval` both declare `plots/cm.png`.

One output path, one owning stage.

### Cache Hits and Reruns

Run `dvc repro` once.

DVC computes dependency hashes.

DVC runs `load`, `train`, and `eval`.

DVC records output hashes in `dvc.lock`.

Run `dvc repro` again with no changes.

DVC should report that the pipeline is up to date.

Now change `params.yaml` from `C: 0.5` to `C: 1.5`.

The raw data did not change.

The load script did not change.

The `load` stage should be a cache hit.

The `train` stage should run again because it depends on `train.C`.

The `eval` stage should run again because it depends on the model output from `train`.

This is not magic.

It is dependency tracking.

The graph says exactly what must be invalidated.

That is what makes DVC useful in review.

The reviewer can ask:

"Did this parameter change re-run only the expected stages?"

"Did the data hash stay stable?"

"Did the evaluation output change in a direction we can explain?"

Those are better questions than "did the notebook run?"

### What dvc.lock Proves

`dvc.lock` proves the resolved state of the pipeline.

It does not prove the training environment was identical.

It does not prove the Python libraries were identical.

It does not prove the GPU kernels were deterministic.

It does not prove the upstream source system was correct.

It proves what DVC can see:

the commands, dependencies, parameters, and outputs declared in the DVC graph.

That boundary is important.

If you forget to declare a file as a dependency, DVC cannot detect changes to it.

If `train.py` reads `schema.yaml` but `schema.yaml` is not in `deps`, a schema change may not trigger retraining.

If the script reads an environment variable that changes model behavior, DVC cannot hash that unless you materialize it into a tracked file or parameter.

If the script queries a database directly, the query result must be materialized or the database snapshot must be part of the dependency contract.

DVC rewards explicitness.

It punishes hidden inputs.

That is a feature, not a nuisance.

Hidden inputs are where reproducibility goes to fail.

## 4. Remote Backends, Auth, and Cost Control

DVC remotes are storage locations for tracked data and model content.

The official DVC `remote add` documentation lists cloud providers such as Amazon S3, S3-compatible stores such as MinIO, Azure Blob Storage, Google Cloud Storage, and self-hosted options such as SSH, HDFS, HTTP, and WebDAV.

That breadth matters for platform teams.

The same DVC workflow can run on a laptop with a local remote, on kind with MinIO, in CI against S3, and in production against a locked-down bucket.

The remote is not the source of truth by itself.

The Git commit plus DVC metadata says which objects matter.

The remote stores those objects.

Without the Git metadata, the remote is just a pile of hashes.

Without the remote objects, the Git metadata points to missing content.

Both sides are required.

Basic remote configuration looks like this:

```bash
dvc remote add -d storage s3://ml-platform-dvc-cache
dvc remote modify storage region us-east-1
dvc remote modify --local storage access_key_id "$AWS_ACCESS_KEY_ID"
dvc remote modify --local storage secret_access_key "$AWS_SECRET_ACCESS_KEY"
```

The `--local` flag matters.

Project-safe remote names and bucket URLs can live in `.dvc/config`.

Credentials belong in `.dvc/config.local`, environment variables, IAM roles, workload identity, or the cloud provider's credential chain.

The official DVC configuration documentation states that `.dvc/config` is meant to be tracked by Git and should not contain secrets.

That is a hard line.

If a pull request adds `access_key_id` or `secret_access_key` to `.dvc/config`, stop the review.

The right fix is to move secrets to local config or a CI secret store, rotate exposed credentials, and then continue.

### Auth Patterns

For laptops, use local config or the cloud CLI's normal credentials.

For GitHub Actions, use short-lived credentials through OIDC where possible.

For GitLab CI, use protected variables or cloud workload identity where supported.

For Kubernetes jobs, use a service account mapped to an IAM role or workload identity.

For MinIO in local labs, use a Kubernetes Secret and port-forward only to `127.0.0.1`.

For production buckets, use least privilege.

CI jobs that only pull data need read access.

Training jobs that produce new artifacts need write access to the DVC remote prefix.

Garbage collection jobs need delete access and should be rare, reviewed, and scoped.

The dangerous permission is broad delete.

DVC's `gc --cloud` can remove remote objects.

That is useful for cost control.

It is also a way to break old commits if used without understanding the reference scope.

Run dry runs first.

Keep retention policies aligned with Git branch and tag policies.

Do not let an automated cleanup job delete objects needed by release tags.

### Multi-Environment Remotes

A small team might start with one remote:

```text
origin Git repo
  |
  +-- .dvc/config -> remote "storage" = s3://team-dvc-cache
```

A platform team often needs at least two:

```text
dev remote   -> s3://ml-dev-dvc-cache
prod remote  -> s3://ml-prod-dvc-cache
```

Development remotes allow fast iteration.

Production remotes protect release artifacts.

The promotion boundary should be explicit.

Do not let every feature branch write into the production cache prefix.

Do not let CI jobs for untrusted branches pull privileged datasets.

A practical pattern is:

- feature branches write to a dev remote
- protected release jobs copy or re-push approved DVC objects to a prod remote
- release tags preserve the Git metadata that references approved objects
- production training and rollback jobs read from the prod remote

This gives the platform team separate blast radii.

It also gives security reviewers a clean permission story.

### Cost Lens

DVC cache growth is not theoretical.

Every changed dataset shard, model binary, and generated artifact can add objects.

The local cache grows.

The remote cache grows.

CI caches may grow too.

The first cost control is deduplication-aware data layout.

Avoid one huge archive per version when only a small part changes.

Prefer partitions or shards that align with natural update boundaries.

The second cost control is cache type.

DVC can use `reflink`, `hardlink`, `symlink`, or `copy` link strategies, with `reflink,copy` as a common default.

Hardlinks and symlinks can save disk, but the official configuration docs warn that manually modifying tracked workspace files linked this way could corrupt cache content.

DVC protects those links by making them read-only.

Use `dvc unprotect` when you intentionally need to edit.

Then re-add or repro so DVC records the new content.

The third cost control is garbage collection.

Use `dvc gc --workspace --dry` for a cautious local preview.

Use broader scopes such as all branches or tags when preserving release history matters.

Treat `dvc gc --cloud` as a production operation.

Cloud deletion is not a casual cleanup command.

The fourth cost control is regional alignment.

If a CI runner in one region repeatedly pulls large datasets from a bucket in another region, egress and latency can dominate the pipeline.

Put runners near data.

Use cache warmers for common datasets.

Use self-hosted runners for long jobs when governance and economics justify them.

Use lifecycle policies for temporary remote prefixes, but not for release prefixes that back audit requirements.

The fifth cost control is avoiding accidental full pulls.

Use targeted `dvc pull` when a job only needs a subset.

Use stage targets when a validation job only needs evaluation artifacts.

Do not make every pull request download every historical dataset.

That is a cost bug disguised as simplicity.

### Practitioner Failure Modes

Remote permissions in CI are the most common failure.

The job can clone Git but cannot pull DVC objects.

That means the CI identity has source access but not artifact access.

Fix the IAM role or secret scope.

Do not commit credentials to make CI pass.

Network interruptions can leave partial transfers, stale locks, or temporary index state.

DVC's troubleshooting guide calls out missing cloud data, credential problems, endpoint problems, and leftover lock files after abrupt termination.

If a runner is killed during `dvc push`, retry the push from the source environment.

Then run `dvc status -c` or a targeted pull from a clean environment.

Pointer-vs-cache checksum drift is another real-world problem.

It happens when a workspace file is modified outside DVC's expected flow, especially with unsafe link handling or manual edits.

The pointer says one hash.

The workspace file contains another payload.

Run `dvc status`.

Use `dvc checkout` to restore tracked content from cache.

Use `dvc add` or `dvc commit` only when the changed content is intentional.

The senior move is to ask why drift was possible.

Was the file writable when it should have been protected?

Was a data-prep script writing into a tracked output directory outside a DVC stage?

Was a human editing generated data?

Fix the workflow, not just the immediate hash mismatch.

## 5. DVC and Kubeflow Pipelines

DVC and Kubeflow Pipelines solve different problems.

DVC is a lineage, caching, and repository reproducibility tool.

Kubeflow Pipelines is a distributed execution and orchestration platform.

DVC can run local or CI pipeline stages.

Kubeflow can schedule containers across Kubernetes.

DVC can tell you which data hash trained a model.

Kubeflow can tell you which pod ran which component in a pipeline run.

Those are complementary records.

They are not substitutes.

Trying to make DVC into a scheduler is an anti-pattern.

DVC does not manage a fleet of workers.

DVC does not provide Kubernetes-native retries, pod templates, GPU placement, queue policies, or artifact viewers for distributed runs.

It can run commands.

It can decide whether stages are changed.

That is not the same as orchestrating production-scale training.

Trying to make Kubeflow replace DVC is also awkward.

Kubeflow can record artifacts, but many teams still want repository-level data pointers that survive outside the Kubeflow UI.

They want a Git commit that says exactly which data and model objects matter.

They want a local reproduction path for smaller jobs.

They want code review around data changes.

A practical architecture looks like this:

```text
Git PR
  |
  +-- code, params.yaml, dvc.yaml, dvc.lock
  |
  +-- CI: dvc pull + dvc repro small checks
  |
  +-- merge to main
          |
          v
   Kubeflow Pipeline run
          |
          +-- component pulls DVC data by Git ref
          +-- component trains at cluster scale
          +-- component pushes DVC outputs or model registry artifacts
          +-- promotion gate records Git ref + DVC hashes + metrics
```

This architecture keeps the contracts separate.

DVC owns the reproducibility metadata.

Kubeflow owns distributed execution.

The model registry owns promotion state.

The feature store owns reusable feature serving contracts.

The data-quality tool owns validation suites.

No one tool needs to pretend to be all of MLOps.

### When DVC Alone Fits

DVC alone fits when a pipeline can run on one workstation, one CI runner, or one modest VM.

It fits when the primary need is reproducibility and data sharing.

It fits when model training is short enough for normal review cycles.

It fits when the team wants to bootstrap discipline before adopting a full platform.

It also fits for deterministic preprocessing steps that produce training-ready datasets.

### When Kubeflow Fits

Kubeflow fits when each stage must run in an isolated container.

It fits when stages need different CPU, memory, or GPU requests.

It fits when training is long-running or distributed.

It fits when the organization already standardizes on Kubernetes-native pipelines.

It fits when retries, scheduling, metadata UI, and component reuse matter.

### The Integration Contract

If a Kubeflow component reads DVC data, pin the Git ref.

Do not let a component pull a branch name that moves during execution.

Use a commit SHA or release tag.

Run `dvc pull` inside the component image with credentials provided by Kubernetes, not hard-coded in the repo.

Emit the DVC data hash into the Kubeflow run metadata if your platform supports it.

Also emit it into the model registry.

The incident responder should not need to open three tools and guess which entries match.

The Git commit, DVC hash, Kubeflow run, and registry model version should cross-reference each other.

That is the design target.

> **Design prompt:** You have a nightly GPU training job that takes six hours and a daily data-prep job that takes eight minutes. Which parts should DVC run directly, which parts should Kubeflow run, and where should the data hash be recorded?

A strong design runs the small deterministic prep step through DVC or a lightweight CI path, then lets Kubeflow run the long GPU training job.

The data hash should be recorded in Git through `dvc.lock`, in the Kubeflow run metadata, and in the model registry entry.

This avoids using DVC as a cluster scheduler while still preserving the reproducibility contract.

## 6. DVC and CI/CD

DVC changes CI/CD because the CI runner needs data.

A normal application CI job clones code, installs dependencies, and runs tests.

An ML CI job often needs to pull DVC objects before it can validate or reproduce anything meaningful.

That adds cost, auth, caching, and review design.

CML, Continuous Machine Learning, is the Iterative toolchain commonly paired with DVC in GitHub Actions and GitLab CI.

The CML docs show workflows that install DVC, run `dvc pull`, run `dvc repro`, and publish metrics or plots into pull request reports.

This module only introduces the pattern.

The dedicated CI/CD module appears later as Module 5.12: Continuous Machine Learning with CML.

Do not duplicate the whole CML design here.

Focus on the data-versioning contract.

The CI questions are:

- Can the runner read the Git metadata?
- Can the runner read the DVC remote objects required by this PR?
- Should the runner write new DVC objects, or only validate?
- Is the job pulling too much data for the signal it provides?
- Are metrics and plots surfaced in review?
- Are long jobs routed to the right runner class?

A minimal GitHub Actions shape looks like this:

```yaml
name: dvc-check

on:
  pull_request:
    paths:
      - "dvc.yaml"
      - "dvc.lock"
      - "params.yaml"
      - "scripts/**"
      - "data/**/*.dvc"

jobs:
  repro:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - uses: iterative/setup-dvc@v1

      - name: Install project dependencies
        run: .venv/bin/python -m pip install -r requirements.txt

      - name: Pull DVC inputs
        run: dvc pull --run-cache

      - name: Reproduce pipeline
        run: dvc repro

      - name: Show metrics
        run: dvc metrics show
```

This is a skeleton, not a full production workflow.

Production workflows should use cloud identity rather than static keys where possible.

They should avoid running expensive training on every docs-only change.

They should post metrics and plots for reviewer visibility.

They should separate "validate metadata" from "train a candidate model."

They should make write permissions explicit.

The cost lens is especially important.

GitHub-hosted and GitLab-hosted runners use billed compute minute models for private workloads, with plan-specific allowances and runner cost factors.

Long ML jobs can burn through those allowances quickly.

Self-hosted runners can reduce per-minute platform charges or provide GPUs and warm caches, but they move cost into infrastructure, maintenance, security patching, and queue management.

There is no universal cheaper option.

There is only a cost model you can explain.

Ask these before enabling DVC CI broadly:

- How large is the average `dvc pull`?
- How often do pull requests trigger it?
- Is the DVC remote in the same region as the runner?
- Can the runner reuse a local DVC cache safely?
- Can small checks run without pulling the full dataset?
- Which jobs need write access to the DVC remote?
- Which jobs can use synthetic or sampled data?
- Which jobs deserve self-hosted runners?

The best CI design usually has tiers.

Tier one checks YAML, Python imports, and lightweight metadata.

Tier two pulls a small sample and runs fast reproducibility checks.

Tier three trains or evaluates on a larger dataset after labels, data quality, and resource budgets justify it.

That tiering keeps DVC from becoming a cost amplifier.

It also makes review faster.

## 7. Patterns and Anti-Patterns

DVC succeeds when the workflow is explicit, boring, and reviewable.

It fails when teams treat it as a magic storage layer.

The best pattern is lock-and-rerun.

Change code, data, or params.

Run `dvc repro`.

Review `dvc.lock`.

Push DVC objects.

Push Git metadata.

Make the promotion decision from the exact resulting evidence.

This pattern is deterministic because it makes hidden state visible.

It is also easy to teach.

If the lockfile changed, ask why.

If the lockfile did not change, ask whether the changed file was actually declared as a dependency.

The second pattern is small-and-many, within reason.

Use partitioned datasets, shard files, and directories that let DVC reuse unchanged objects.

Avoid monolithic archives that rewrite the whole content hash for a tiny logical change.

Avoid millions of tiny files unless the storage and file system can handle them.

The goal is not tiny for its own sake.

The goal is content-addressable reuse.

The third pattern is cache-shared-by-team.

A shared remote lets new developers, CI runners, and training jobs pull the exact objects referenced by Git.

A shared local cache can also help on controlled machines, but it needs file permission discipline.

DVC has `cache.shared` and link-type settings for shared-cache patterns.

Use them deliberately.

Do not let many projects mutate one shared cache without ownership rules.

The fourth pattern is branch discipline for data.

Use feature branches for experimental data changes when the data is part of the code review.

Use release branches or tags for blessed data-model combinations.

Do not let every personal experiment become a permanent branch that preserves expensive cache objects forever.

Preserve what matters.

Garbage collect what was never promoted.

The fifth pattern is data-boundary documentation.

Every DVC pipeline should make clear where the training boundary begins.

If the source of truth is a warehouse table, document the query snapshot strategy.

If the source of truth is a feature store, document the point-in-time retrieval.

If the source of truth is a labeled CSV export, document who owns labels and how late-arriving labels are handled.

DVC does not replace those ownership decisions.

It records their materialized result.

### Common Mistakes

| Mistake | Production consequence | Better practice |
|---------|------------------------|-----------------|
| Storing model binaries directly in Git | Reviewers cannot inspect binary diffs, clones grow, rollback policy splits | Track model artifacts with DVC or a model registry |
| Treating DVC as an ETL scheduler | Long jobs lack cluster scheduling, retries, resource isolation, and queue policy | Use DVC for lineage and caching, Kubeflow or Argo for distributed execution |
| Forgetting `dvc push` after `git push` | Teammates and CI receive pointers to missing remote objects | Add release checklists or hooks that verify remote availability |
| Declaring hidden inputs outside `deps` or `params` | `dvc repro` skips stages that should rerun | Materialize hidden inputs or add them to the DVC graph |
| Letting cache grow without policy | Local disks fill, cloud storage grows, old experiments become expensive | Use retention scopes, dry-run garbage collection, and lifecycle policy by prefix |
| Committing `.dvc/config.local` or credentials | Secret exposure and emergency rotation | Keep secrets in local config, CI variables, or workload identity |
| Branching data tightly with every feature branch | Remote cache fills with unreviewed experiment objects | Use dev remotes for experiments and promote only approved objects |
| Editing linked workspace files manually | Pointer and cache content drift, corrupting reproducibility | Use `dvc unprotect`, regenerate through stages, then `dvc repro` or `dvc add` |

### Decision Framework

Ask these questions before adding DVC to a project:

- Is there a concrete reproducibility problem involving data, models, or metrics?
- Are the artifacts too large or too binary for Git review?
- Can the team define the training data boundary clearly?
- Does the pipeline have deterministic stages that benefit from cache reuse?
- Will a shared remote be available to every runner that needs it?
- Can credentials be handled without committing secrets?
- Is there a retention policy for cache growth?
- Does another system already own this problem better?

If most answers are yes, DVC is a good fit.

If the data is a transactional lake table with many concurrent writers, DVC may only belong at the export boundary.

If the job needs distributed scheduling, DVC should feed an orchestrator rather than replace it.

If the artifact is a static design binary unrelated to ML, Git LFS may be simpler.

If the organization already has a registry that stores immutable training datasets, DVC may still help local reproduction, but it should not duplicate governance.

Good DVC architecture starts by respecting the neighboring tools.

## Hands-On Exercise: DVC Pipeline with kind and MinIO

In this lab, you will build a small DVC project.

The project uses kind for a local Kubernetes cluster.

It runs MinIO as an S3-compatible DVC remote inside the cluster.

It binds external access to `127.0.0.1` with `kubectl port-forward`.

It builds a three-stage pipeline:

```text
load -> train -> eval
```

The dataset is an embedded Kaggle-style CSV fixture generated by the load stage.

The model is a tiny scikit-learn `LogisticRegression`.

The first run executes all stages.

The second run changes a parameter and demonstrates that `load` is reused while `train` and `eval` rerun.

### Lab Goal

You are building a reproducibility baseline for an MLOps team.

The team does not yet need distributed training.

It does need data hashes, model hashes, metrics, plots, and remote sharing.

Your task is to create that baseline and prove it works.

### Step 1: Create the kind Cluster

Use Kubernetes v1.35 or newer.

```bash
kind create cluster --name dvc-lab --image kindest/node:v1.35.0
kubectl cluster-info --context kind-dvc-lab
```

If you prefer minikube, use a Kubernetes v1.35+ profile and keep the later namespace, Secret, Deployment, Service, and port-forward commands the same.

### Step 2: Install MinIO

Create a namespace and Secret.

```bash
kubectl create namespace dvc-lab
kubectl -n dvc-lab create secret generic minio-root \
  --from-literal=MINIO_ROOT_USER=minioadmin \
  --from-literal=MINIO_ROOT_PASSWORD=minioadmin123
```

Create `minio.yaml`.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: minio
  namespace: dvc-lab
spec:
  replicas: 1
  selector:
    matchLabels:
      app: minio
  template:
    metadata:
      labels:
        app: minio
    spec:
      containers:
        - name: minio
          image: quay.io/minio/minio:latest
          args:
            - server
            - /data
            - --console-address
            - ":9001"
          envFrom:
            - secretRef:
                name: minio-root
          ports:
            - containerPort: 9000
              name: s3
            - containerPort: 9001
              name: console
          volumeMounts:
            - name: data
              mountPath: /data
      volumes:
        - name: data
          emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: minio
  namespace: dvc-lab
spec:
  type: ClusterIP
  selector:
    app: minio
  ports:
    - name: s3
      port: 9000
      targetPort: 9000
    - name: console
      port: 9001
      targetPort: 9001
```

Apply it.

```bash
kubectl apply -f minio.yaml
kubectl -n dvc-lab rollout status deployment/minio
```

Create `minio-bucket-job.yaml`.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: create-dvc-bucket
  namespace: dvc-lab
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: mc
          image: quay.io/minio/mc:latest
          envFrom:
            - secretRef:
                name: minio-root
          command:
            - /bin/sh
            - -c
            - |
              mc alias set lab http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"
              mc mb --ignore-existing lab/dvc-lab-cache
  backoffLimit: 2
```

Run the bucket job.

```bash
kubectl apply -f minio-bucket-job.yaml
kubectl -n dvc-lab wait --for=condition=complete job/create-dvc-bucket --timeout=120s
```

Forward MinIO to the loopback interface only.

```bash
kubectl -n dvc-lab port-forward --address 127.0.0.1 svc/minio 9000:9000 9001:9001
```

Keep that terminal open.

The S3 API is now reachable at `http://127.0.0.1:9000`.

The console is reachable at `http://127.0.0.1:9001`.

### Step 3: Create the DVC Project

Use another terminal.

```bash
mkdir dvc-versioning-lab
cd dvc-versioning-lab
git init
uv venv .venv
uv pip install --python .venv/bin/python "dvc[s3]" pandas scikit-learn matplotlib joblib pyyaml
.venv/bin/dvc init
```

If your environment does not have `uv`, create a virtual environment with your standard Python tooling, then continue with `.venv/bin/python` for every project command.

Create directories.

```bash
mkdir -p scripts data models plots
```

Create `params.yaml`.

```yaml
train:
  C: 0.5
  test_size: 0.25
  seed: 42
  threshold: 0.5
```

Create `scripts/load.py`.

```python
from pathlib import Path

import pandas as pd
from sklearn.datasets import make_classification


def main() -> None:
    features, labels = make_classification(
        n_samples=160,
        n_features=6,
        n_informative=4,
        n_redundant=0,
        n_clusters_per_class=2,
        class_sep=1.2,
        random_state=42,
    )
    columns = [
        "monthly_spend",
        "support_tickets",
        "usage_minutes",
        "account_age",
        "discount_rate",
        "feature_adoption",
    ]
    frame = pd.DataFrame(features, columns=columns)
    frame["churn"] = labels
    Path("data").mkdir(exist_ok=True)
    frame.to_csv("data/raw.csv", index=False)
    print(f"wrote data/raw.csv with {len(frame)} rows")


if __name__ == "__main__":
    main()
```

Create `scripts/train.py`.

```python
import json
from pathlib import Path

import joblib
import pandas as pd
import yaml
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def main() -> None:
    params = yaml.safe_load(Path("params.yaml").read_text())["train"]
    frame = pd.read_csv("data/raw.csv")
    features = frame.drop(columns=["churn"])
    target = frame["churn"]
    x_train, x_holdout, y_train, y_holdout = train_test_split(
        features,
        target,
        test_size=params["test_size"],
        random_state=params["seed"],
        stratify=target,
    )
    model = Pipeline(
        steps=[
            ("scale", StandardScaler()),
            (
                "logreg",
                LogisticRegression(
                    C=params["C"],
                    max_iter=500,
                    random_state=params["seed"],
                ),
            ),
        ]
    )
    model.fit(x_train, y_train)
    holdout = x_holdout.copy()
    holdout["churn"] = y_holdout.to_numpy()
    Path("models").mkdir(exist_ok=True)
    Path("data").mkdir(exist_ok=True)
    joblib.dump(model, "models/model.pkl")
    holdout.to_csv("data/holdout.csv", index=False)
    probabilities = model.predict_proba(x_train)[:, 1]
    predictions = (probabilities >= params["threshold"]).astype(int)
    smoke_metrics = {
        "train_accuracy": float(accuracy_score(y_train, predictions)),
        "train_auc": float(roc_auc_score(y_train, probabilities)),
    }
    Path("metrics.json").write_text(json.dumps(smoke_metrics, indent=2))
    print("wrote model, holdout split, and transient train metrics")


if __name__ == "__main__":
    main()
```

Create `scripts/eval.py`.

```python
import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
import yaml
from sklearn.metrics import ConfusionMatrixDisplay, accuracy_score, confusion_matrix, roc_auc_score


def main() -> None:
    params = yaml.safe_load(Path("params.yaml").read_text())["train"]
    model = joblib.load("models/model.pkl")
    holdout = pd.read_csv("data/holdout.csv")
    features = holdout.drop(columns=["churn"])
    target = holdout["churn"]
    probabilities = model.predict_proba(features)[:, 1]
    predictions = (probabilities >= params["threshold"]).astype(int)
    metrics = {
        "holdout_accuracy": float(accuracy_score(target, predictions)),
        "holdout_auc": float(roc_auc_score(target, probabilities)),
        "threshold": float(params["threshold"]),
    }
    Path("metrics.json").write_text(json.dumps(metrics, indent=2))
    matrix = confusion_matrix(target, predictions)
    display = ConfusionMatrixDisplay(confusion_matrix=matrix, display_labels=["stay", "churn"])
    display.plot(values_format="d")
    Path("plots").mkdir(exist_ok=True)
    plt.tight_layout()
    plt.savefig("plots/cm.png")
    plt.close()
    print("wrote final metrics and confusion matrix plot")


if __name__ == "__main__":
    main()
```

### Step 4: Declare the DVC Pipeline

Create `dvc.yaml`.

```yaml
stages:
  load:
    cmd: .venv/bin/python scripts/load.py
    deps:
      - scripts/load.py
    outs:
      - data/raw.csv

  train:
    cmd: .venv/bin/python scripts/train.py
    deps:
      - data/raw.csv
      - scripts/train.py
    params:
      - train.C
      - train.test_size
      - train.seed
    outs:
      - models/model.pkl
      - data/holdout.csv

  eval:
    cmd: .venv/bin/python scripts/eval.py
    deps:
      - models/model.pkl
      - data/holdout.csv
      - scripts/eval.py
    params:
      - train.threshold
    metrics:
      - metrics.json
    plots:
      - plots/cm.png
```

Why is `metrics.json` only declared in `eval`?

Because `train` writes a transient file and `eval` overwrites it with final holdout metrics.

DVC should have one owning stage for that output path.

This keeps the graph unambiguous.

Run the pipeline.

```bash
.venv/bin/dvc repro
```

Inspect the graph.

```bash
.venv/bin/dvc dag
```

Expected shape:

```text
+------+      +-------+      +------+
| load | ---> | train | ---> | eval |
+------+      +-------+      +------+
```

Show metrics.

```bash
.venv/bin/dvc metrics show
```

Show plots.

```bash
.venv/bin/dvc plots show --target plots/cm.png
```

Commit the reproducibility state.

```bash
git add .dvc .gitignore data/.gitignore models/.gitignore plots/.gitignore dvc.yaml dvc.lock params.yaml scripts
git commit -m "build DVC data versioning lab"
```

### Step 5: Configure the MinIO Remote

Set credentials for the shell.

```bash
export AWS_ACCESS_KEY_ID=minioadmin
export AWS_SECRET_ACCESS_KEY=minioadmin123
export AWS_DEFAULT_REGION=us-east-1
```

Add the DVC remote.

```bash
.venv/bin/dvc remote add -d minio s3://dvc-lab-cache
.venv/bin/dvc remote modify minio endpointurl http://127.0.0.1:9000
.venv/bin/dvc remote modify --local minio access_key_id "$AWS_ACCESS_KEY_ID"
.venv/bin/dvc remote modify --local minio secret_access_key "$AWS_SECRET_ACCESS_KEY"
```

Commit only the safe config.

```bash
git add .dvc/config
git commit -m "configure DVC MinIO remote"
```

Push DVC objects.

```bash
.venv/bin/dvc push
```

Prove pull works from remote storage.

```bash
rm -rf data models plots metrics.json
.venv/bin/dvc pull
.venv/bin/dvc metrics show
```

The metric should return after the pull because the final metric file was tracked as a DVC metric output.

### Step 6: Change a Parameter and Reproduce

Change regularization from `0.5` to `1.5`.

```bash
perl -0pi -e 's/C: 0\\.5/C: 1.5/' params.yaml
.venv/bin/dvc repro
```

Expected behavior:

- `load` is unchanged and should not rerun.
- `train` reruns because `train.C` changed.
- `eval` reruns because the model output changed.
- `dvc.lock` changes because resolved parameter and output hashes changed.

Show the metrics.

```bash
.venv/bin/dvc metrics show
```

Compare metrics with the previous commit.

```bash
.venv/bin/dvc metrics diff HEAD
```

Generate a plot diff.

```bash
.venv/bin/dvc plots diff --target plots/cm.png HEAD
```

Commit and push the new version.

```bash
git add params.yaml dvc.lock
git commit -m "tune logistic regression regularization"
.venv/bin/dvc push
```

### Step 7: Validate What You Built

Run these checks.

```bash
.venv/bin/dvc status
.venv/bin/dvc status -c
git status --short
```

Interpretation:

- `dvc status` should show that the local pipeline is up to date.
- `dvc status -c` should show whether the cache and remote are in sync.
- `git status --short` should be clean after committing tracked metadata.

If `dvc status -c` reports missing remote objects, run `dvc push`.

If `dvc pull` fails with credentials, check `.dvc/config.local` and environment variables.

If `dvc repro` unexpectedly skips `train`, verify that `params.yaml` is listed under the `params` section.

If `eval` cannot read `metrics.json`, remember that `metrics.json` is a final output, not an input.

If `dvc plots diff` cannot compare the plot, confirm that `plots/cm.png` exists in both the current commit and the revision you compare against.

### Lab Success Criteria

You have completed the lab when you can verify all of the following:

- [ ] MinIO runs inside kind or minikube.
- [ ] External MinIO access is bound to `127.0.0.1`.
- [ ] DVC is initialized in a Git repository.
- [ ] `dvc.yaml` defines `load`, `train`, and `eval`.
- [ ] `dvc repro` creates `data/raw.csv`, `models/model.pkl`, `metrics.json`, and `plots/cm.png`.
- [ ] `dvc dag` shows a three-stage graph.
- [ ] `dvc metrics show` prints holdout metrics.
- [ ] `dvc push` uploads objects to MinIO.
- [ ] `dvc pull` restores deleted local artifacts from MinIO.
- [ ] Changing `train.C` reruns `train` and `eval` but not `load`.
- [ ] You can explain why `metrics.json` is owned by `eval` in `dvc.yaml`.

### Stretch Challenge

Add a data-quality stage before `train`.

Make it fail if `churn` is missing or if the positive class ratio falls below a chosen threshold.

Then compare your design with the next module, Module 5.8: Great Expectations Data Quality.

The transfer lesson is important:

DVC can record the validation artifact and decide what must rerun.

Great Expectations can express richer data-quality contracts.

Use each tool for its strength.

## Knowledge Check

Use these scenarios to test whether you can apply the module.

<details>
<summary>1. A model's production AUC drops after retraining. The Git commit, container image, and `params.yaml` are unchanged. The DVC lockfile changed only for `data/raw.csv` and downstream outputs. What should the incident responder compare first, and why?</summary>

Compare the DVC hash for the raw data dependency, then compare data-quality summaries such as row count, schema, label balance, null rate, and population slices. The lockfile already narrows the cause boundary: code and parameters did not move, but the data did. Metrics show the symptom. Data summaries explain the likely cause. Comparing model binaries first is less useful because the model is expected to change when training data changes.
</details>

<details>
<summary>2. A teammate commits `dvc.yaml` and `dvc.lock`, but CI fails with "cache not found" during `dvc pull`. The teammate says the files are in Git, so CI must be broken. What is the most likely root cause, and what is the fix?</summary>

The most likely root cause is that Git metadata was pushed but the DVC cache objects were not pushed to the remote. Git has the pointers, but the remote object store lacks the payloads. The fix is to run `dvc push` from the environment that still has the cache objects, then rerun CI. If that fails, check remote credentials and endpoint configuration. Committing the raw data directly to Git is the wrong fix.
</details>

<details>
<summary>3. A team wants to run a six-hour GPU training job with DVC because `dvc repro` already defines the DAG. Why is that usually a poor production scheduling design, and how should DVC and Kubeflow be combined instead?</summary>

DVC can run commands and decide whether stages changed, but it is not a cluster scheduler. It does not provide Kubernetes-native pod scheduling, GPU placement, retries, queue policy, or resource isolation. A better design records data and parameter lineage with DVC, pins the Git ref, and runs the long training container through Kubeflow Pipelines. The Kubeflow run should record the Git commit and DVC hashes, while DVC preserves repository-level reproducibility.
</details>

<details>
<summary>4. A pull request changes `schema.yaml`, and the training script reads that schema. `dvc repro` reports everything up to date. What design error caused this, and how do you fix it?</summary>

The schema file is a hidden dependency. DVC can only invalidate stages based on declared dependencies and parameters. Add `schema.yaml` to the relevant stage's `deps`, rerun `dvc repro`, and commit the updated `dvc.lock`. If the schema affects multiple stages, add it to each stage that reads it directly. Do not force reruns as a substitute for fixing the graph.
</details>

<details>
<summary>5. A team stores every experiment in a long-lived branch and never garbage-collects the DVC remote. Storage cost rises quickly. What retention strategy preserves auditability without keeping every scratch run forever?</summary>

Separate experiment, development, and release retention. Use a dev remote or prefix for scratch runs, and apply lifecycle policy there. Preserve release tags and protected branches with a stricter policy. Use `dvc gc` dry runs locally and treat cloud garbage collection as a reviewed operation. Promote only approved DVC objects to the production remote. Auditability comes from preserving released data-model combinations, not every temporary attempt.
</details>

<details>
<summary>6. A CI job can clone the repository and read `.dvc/config`, but `dvc pull` returns an authentication error. A developer proposes adding the access key directly to `.dvc/config`. Why is that wrong, and what should be done instead?</summary>

`.dvc/config` is committed to Git and must not contain secrets. Adding access keys there exposes credentials to anyone with repository access and may require rotation. Use `.dvc/config.local` for local secrets, CI secret variables, OIDC-backed cloud credentials, workload identity, or a scoped service account. Also confirm that the CI identity has only the permissions it needs, such as read access for validation jobs and write access only for trusted artifact-producing jobs.
</details>

<details>
<summary>7. A team tracks a dataset as a single compressed archive. Each daily refresh changes a small fraction of records, but DVC uploads a new huge object each time. What data-layout change would improve cache reuse, and what tradeoff must be watched?</summary>

Split the dataset into meaningful partitions or shard files so unchanged content can be reused across versions. For tabular data, date or domain partitions in Parquet are often better than one ZIP file. The tradeoff is that too many tiny files can stress file systems, object-store listing, and pull performance. The goal is not maximum file count. The goal is stable, reviewable, deduplicated update boundaries.
</details>

## Next Module

*Next module coming soon.*

## Sources

- [DVC command reference: `init`](https://dvc.org/doc/command-reference/init) - Official behavior for initializing a DVC project and creating `.dvc/` configuration and cache structure.
- [DVC command reference: `add`](https://dvc.org/doc/command-reference/add) - Official behavior for `.dvc` pointer files, cache storage, directory tracking, and `.gitignore` updates.
- [DVC user guide: `dvc.yaml` files](https://dvc.org/doc/user-guide/project-structure/dvcyaml-files) - Official reference for stages, dependencies, outputs, metrics, plots, parameters, and lockfile behavior.
- [DVC command reference: `repro`](https://dvc.org/doc/command-reference/repro) - Official behavior for reproducing pipeline stages from the dependency graph.
- [DVC command reference: `push`](https://dvc.org/doc/command-reference/push) - Official behavior for uploading cache objects to remote storage while Git handles code and metadata.
- [DVC command reference: `remote add`](https://dvc.org/doc/command-reference/remote/add) - Official list of supported remote storage backends and default remote configuration behavior.
- [DVC user guide: configuration](https://dvc.org/doc/user-guide/project-structure/configuration) - Official reference for `.dvc/config`, `.dvc/config.local`, `cache.type`, `cache.shared`, and secret-handling guidance.
- [DVC command reference: `gc`](https://dvc.org/doc/command-reference/gc) - Official behavior for local and remote cache garbage collection.
- [DVC user guide: troubleshooting](https://dvc.org/doc/user-guide/troubleshooting) - Official troubleshooting notes for missing remote objects, credentials, endpoints, locks, and cache link issues.
- [DVC command reference: `plots`](https://dvc.org/doc/command-reference/plots) - Official behavior for DVC plot show and diff commands.
- [GitHub Docs: About Git Large File Storage](https://docs.github.com/repositories/working-with-files/managing-large-files/about-git-large-file-storage) - Official GitHub explanation of Git LFS pointer behavior.
- [CML documentation: CML with DVC](https://cml.dev/doc/cml-with-dvc) - Official CML examples for DVC pull, DVC repro, metrics, and plots in GitHub Actions and GitLab CI.
- [GitHub Docs: GitHub Actions billing](https://docs.github.com/en/billing/managing-billing-for-github-actions/about-billing-for-github-actions) - Official source for GitHub-hosted runner minute and storage billing model.
- [GitLab Docs: compute minutes](https://docs.gitlab.com/ci/pipelines/compute_minutes/) - Official source for GitLab hosted runner compute-minute model.
