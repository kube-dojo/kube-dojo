---
citations_verified: true
title: "Module 5.9: ML Repository Hygiene"
slug: platform/disciplines/data-ai/mlops/module-5.9-ml-repository-hygiene
sidebar:
  order: 10
---

> **Discipline Track** | Complexity: `[COMPLEX]` | Time: 45-55 min

## Prerequisites

Before starting this module:
- [Module 5.7: Data Versioning with DVC](../module-5.7-dvc-data-versioning/)
- [Module 5.8: Great Expectations Data Quality](../module-5.8-great-expectations-data-quality/)
- [Module 5.3: Model Training & Experimentation](../module-5.3-model-training/)
- Git workflow, including branches, hooks, and pre-commit
- Python tooling, including virtual environments, `pyproject.toml`, and lock files

## Learning Outcomes

After completing this module, you will be able to:
- **Diagnose** ML repository rot by separating source code, data payloads, model artifacts, notebook outputs, environment files, and experiment logs.
- **Design** a maintainable `src/`-layout ML repository that works for local development, CI, DVC, notebooks, Kubernetes manifests, and Terraform.
- **Implement** `.gitignore`, `.dvcignore`, and pre-commit hooks that block large files, stripped notebook drift, private keys, and common ML artifact leaks.
- **Manage** dependency lockfiles with `uv sync --locked`, pip-tools, Poetry, or pixi, and split fast pre-commit checks from thorough CI jobs.
- **Refactor** notebook-centered work into importable Python modules and **estimate** when DVC remote storage beats Git LFS for model weights and repository bloat.

## Why This Module Matters

**Hypothetical scenario:** An application repository usually rots slowly, but an ML repository can rot in a quarter. The reason is not that ML teams are careless. ML work simply produces more kinds of files than ordinary application work.

Source code and small configuration belong in Git. Large datasets, trained model weights, and notebook cell outputs usually do not. Scratch feature exports, filesystem MLflow runs, and Weights & Biases local run folders do not either. Temporary CUDA logs and private `.env` files definitely do not.

The repository is the meeting point for all of those artifacts. Without explicit hygiene, Git becomes the bucket where everything lands, and that bucket quickly becomes expensive. Picture a team with a churn model, a recommender model, and a weekly retraining pipeline. The team starts with a clean repository. One notebook is committed with output cells. A checkpoint directory appears. A sample CSV lands in the root so a review can reproduce a chart.

An old model weight file is added because a serving bug needs rollback testing. Then `mlruns/` is committed because a teammate wants to share experiment metadata. A `.env` file appears in a branch and is removed later, but the secret stays in Git history.

After a year, `main` has grown to 8 GB, and fresh clone time is 12 minutes on a normal runner. CI checkout takes 4 minutes per job before tests even start. Each PR runs four checkout-heavy jobs.

At 20 PRs per day, the team burns 320 runner-minutes per day just waiting for Git to move bytes. That is more than five runner-hours per day spent on repository drag. The slow clone is the visible symptom; the hidden symptoms are worse.

New hires assume the slow clone is normal. CI flakes because checkout and cache restore compete for time. Security review has to inspect old secrets in history, and data scientists stop branching because switching workspaces is painful. Platform engineers hesitate to add useful validation because every job is already slow. The team eventually asks someone to clean Git history, and that is the wrong moment to start hygiene. History surgery is disruptive. It breaks forks, invalidates old commit hashes, and creates coordination work for every developer and every automation token.

The better fix is hygiene from day one. This module connects the repository discipline from [Module 5.3](../module-5.3-model-training/) with the artifact lineage from [Module 5.7](../module-5.7-dvc-data-versioning/) and the data-quality gates from [Module 5.8](../module-5.8-great-expectations-data-quality/). DVC keeps data and model payloads out of Git while preserving reviewable metadata. Great Expectations keeps data assumptions explicit. Repository hygiene keeps the whole project small, reproducible, and reviewable.

You will build a clean ML repository from scratch. You will deliberately break it with a dirty notebook, a large binary file, and a fake private key. Then you will fix the failures in the same way a real team should fix them before opening a PR.
## 1. What Hygiene Means for an ML Repository

Repository hygiene is the operating discipline that keeps Git as the source of truth for reviewable source material, not a landfill for every artifact produced near the project. In a web service, repository hygiene usually means ignoring build outputs, keeping secrets out of commits, and using a lock file. In ML, the same idea has more surface area. The repository holds code, data pointers, notebooks, experiment configuration, metrics, generated reports, training logs, models, deployment manifests, and possibly infrastructure code. It may also hold interactive exploration that is valuable today and misleading tomorrow.

That mixture is why ML repositories rot faster than app repositories. Data files are often large and change frequently. Notebook outputs are often small at first, but they become large when a cell renders a plot, a table preview, or embedded HTML.

Model artifacts are binary, opaque, and frequently copied between branches. Lock files change whenever dependency constraints change or a resolver updates a transitive package. Ephemeral logs look useful during debugging but become noise after the run is done. The default Git mental model is too permissive for this environment. The question cannot be "does this file help me right now?" The question must be "does this file belong in the durable review history?" That distinction is the center of hygiene.

Git should hold source code, small human-reviewed configuration, DVC pointer metadata, validation suites, schema files, test fixtures, documentation, and deployment manifests. Git should not hold raw training snapshots, generated feature matrices, local experiment runs, private environment files, notebook cell outputs, cache directories, or mutable model aliases.

The failure case from the introduction is common because every leak feels harmless in isolation. A `.ipynb_checkpoints/` directory is tiny. A rendered notebook diff is annoying but reviewable once. A 20 MB sample CSV seems acceptable when a reviewer needs to reproduce a bug.

A 300 MB model file feels urgent during rollback work. A local `mlruns/` folder looks like useful experiment evidence. The problem is compounding: Git stores history. Removing the file from the current tree does not remove it from the repository history.

Every future clone still pays for objects already committed. That is why bisection later is the wrong primary strategy. You can rewrite history when there is no alternative, but it is the expensive repair path. Hygiene is a gate, not a cleanup sprint.

Use `.gitignore` to prevent common accidents. Use `.dvcignore` to keep DVC from hashing irrelevant noise. Use pre-commit to fail before a bad commit exists. Use CI to repeat the checks in a neutral environment, and use review policy to treat repository shape as part of production quality.

The practical test is onboarding. A clean ML repository should have a short onboarding sequence: clone the repository, run `uv sync`, run `dvc pull`, run `pre-commit install`, then run the documented task. If onboarding requires searching a shared drive, copying a private `.env`, downloading model weights from a chat thread, or asking which notebook is canonical, hygiene has failed. The same test applies to incident response.

When a model regresses, the repository should show the code commit, dependency lock, DVC data and model hashes, validation contracts, and deployment manifest that produced the artifact. If the answer is "try the latest notebook," the repository is not an operational system. It is a collection of memories.

The cost lens makes this less abstract. An 8 GB repository multiplied by 20 PRs per day and four checkout-heavy jobs per PR creates 80 heavy checkouts per day. At four minutes per checkout, the team spends 320 runner-minutes per day before tests start.

At 20 working days per month, that is 6400 runner-minutes of checkout drag. Those minutes also delay feedback. Delayed feedback increases batch size, and larger batches hide defects. The hygiene problem becomes an engineering throughput problem and a platform cost problem.

Git LFS can be useful for a few large binary assets that must travel with Git workflows. DVC remotes are usually cheaper and more expressive for datasets and model artifacts tied to ML lineage. Container images add another cost surface.

Unpinned ML dependencies can pull different wheels, CUDA builds, and transitive libraries over time. Images grow, cold starts slow down, and registry bandwidth rises. The solution is not one magic tool. The solution is a set of boring gates that run every time. That is what repository hygiene means.
```
repo bloat over time

month 0     source + configs only
            ####

month 3     notebooks with outputs + checkpoints
            ###########

month 6     sample datasets + local run logs
            ########################

month 9     old model weights + scratch exports
            ########################################

month 12    8 GB main, 12 minute clone, slow CI checkout
            ########################################################
```

> **Active learning prompt:** Your team has a PR that adds `notebooks/churn_analysis.ipynb`, `data/sample.csv`, `models/model.pkl`, `dvc.lock`, and `reports/model_card.md`. Which files should be reviewed in Git, which should be moved behind DVC, and which should be regenerated or stripped before commit?

## 2. Repository Layout for an ML Project

The layout of an ML repository should make the ownership of each artifact obvious. If the layout does not tell people where a file belongs, they will put it wherever the current shell happens to be. That is how `train.ipynb`, `main.py`, `data.csv`, `model.pkl`, and `notes.txt` end up in the root.

A flat layout is attractive during the first day of exploration. It becomes painful as soon as tests, CI, DVC, notebooks, and deployment manifests all need to agree on paths. The canonical modern layout starts with importable Python code under `src/`.

Tests import the installed package. Notebooks import the installed package. Training commands and CI import the installed package too. This removes the accidental behavior where a script works only because the current working directory happens to be the project root. The common production layout looks like this:
```text
clean-ml-repo/
|-- pyproject.toml
|-- uv.lock
|-- README.md
|-- .python-version
|-- .gitignore
|-- .dvcignore
|-- .pre-commit-config.yaml
|-- dvc.yaml
|-- dvc.lock
|-- data/
|   |-- raw/              # DVC-tracked, ignored by Git
|   |-- interim/          # DVC-tracked when materialized
|   `-- processed/        # DVC-tracked training inputs
|-- models/               # DVC-tracked model artifacts
|-- notebooks/            # committed without outputs
|-- src/
|   `-- myproject/
|       |-- __init__.py
|       |-- features.py
|       |-- train.py
|       `-- validate.py
|-- pipelines/
|   |-- dvc.yaml fragments or stage docs
|   `-- argo-workflow.yaml
|-- tests/
|   |-- test_features.py
|   `-- test_train_contract.py
|-- infra/
|   |-- k8s/
|   `-- terraform/
|-- experiments/
|   `-- README.md         # tracker notes, not local run payloads
`-- docs/
    `-- model-card.md
```

The important property is not the exact folder names. The important property is boundary clarity. `data/` contains data payloads and should normally be ignored by Git. DVC tracks the selected data snapshots through pointer files, `dvc.yaml`, and `dvc.lock`. `models/` contains model payloads and should also be ignored by Git. DVC or a model registry owns the binary payloads. `notebooks/` contains exploration, EDA, and reports; notebook outputs are stripped before commit.

`src/<package_name>/` contains importable code. Anything used by CI, training, serving, or repeated analysis should move here. `pipelines/` contains stage definitions, orchestrator manifests, and workflow templates. The DVC stage graph may live at the root, but pipeline supporting files should not be scattered through notebooks.

`tests/` contains unit tests, contract tests, and small fixtures. Test fixtures must be deliberately small; large fixtures belong in DVC or a test artifact store. `infra/` contains Kubernetes manifests, Terraform modules, and platform-owned deployment configuration.

If a manifest deploys to Kubernetes, it must use Kubernetes 1.35+ compatible APIs. `experiments/` is not a place to dump local run payloads. It is a place for lightweight tracker notes, query templates, or reviewed experiment manifests.

Local MLflow filesystem runs belong in `mlruns/`, which should be ignored. Weights & Biases local runs belong in `wandb/`, which should be ignored. The historical reference point is Cookiecutter Data Science.

It popularized a standardized project structure for data science work, including separated data, notebooks, models, reports, and source code. That shape remains useful, and modern ML repositories differ in a few ways.

They lean harder on `pyproject.toml` and usually include a lock file such as `uv.lock`, `poetry.lock`, or compiled requirements. They use DVC or an artifact store for data and model payloads. They keep Kubernetes and Terraform near the model system when deployment is part of the lifecycle.

They enforce notebook output stripping in pre-commit rather than relying on habit. They treat CI as part of the repository layout, not as an afterthought. Here is the bad layout the team should reject:
```text
bad-flat-ml-repo/
|-- main.py
|-- train.ipynb
|-- train-final-copy.ipynb
|-- data.csv
|-- data-old.csv
|-- model.pkl
|-- model-latest.pkl
|-- notes.sql
|-- .env
|-- mlruns/
`-- README.md
```

It is hard to test, hard to package, and hard to review. It encourages relative imports. It hides which data is a source, which data is an output, and which data is scratch. It tempts people to commit secrets and artifacts. The refactor is mostly moving files into explicit ownership zones:
```diff
- main.py
- train.ipynb
- data.csv
- model.pkl
- notes.sql
- mlruns/
+ src/myproject/train.py
+ notebooks/train.ipynb
+ data/raw/customer_churn.csv.dvc
+ models/churn_model.pkl.dvc
+ pipelines/dvc.yaml
+ experiments/README.md
+ tests/test_train_contract.py
+ .gitignore
+ .dvcignore
+ .pre-commit-config.yaml
```

The diff is not just cosmetic. It changes how the repository behaves. A test can install the package and import `myproject.train`. A notebook can call `from myproject.features import build_features`.

DVC can tell reviewers which data object changed. The model payload leaves Git. The experiment log leaves Git. The SQL moves to a named pipeline or a reviewed query file instead of root scratch.
### Worked Example: Refactor a Flat Training Script

Suppose the repository starts with this root script:
```python
import pandas as pd
from sklearn.linear_model import LogisticRegression

df = pd.read_csv("data.csv")
X = df[["age", "tenure", "monthly_spend"]]
y = df["churned"]

model = LogisticRegression(max_iter=1000)
model.fit(X, y)
```

That script works only when run from the repository root. It hard-codes a data path. It mixes data loading, feature selection, and model training, and it cannot be imported cleanly from tests. A hygienic first refactor moves logic into `src/myproject/train.py`:
```python
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression

FEATURE_COLUMNS = ["age", "tenure", "monthly_spend"]

def load_training_frame(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)

def fit_churn_model(frame: pd.DataFrame) -> LogisticRegression:
    X = frame[FEATURE_COLUMNS]
    y = frame["churned"]
    model = LogisticRegression(max_iter=1000)
    model.fit(X, y)
    return model
```

Now a notebook can import the functions. CI can test the feature contract with a tiny fixture. DVC can define the real training snapshot as a stage dependency.

The model can still be trained locally, but the reusable logic is no longer trapped inside a root script or notebook cell. You will apply the same pattern in the hands-on exercise.
```
src layout vs flat layout

flat layout                         src layout
-----------                         ----------
repo/                               repo/
|-- main.py                         |-- src/myproject/train.py
|-- train.ipynb                     |-- notebooks/train.ipynb
|-- data.csv                        |-- data/raw.csv.dvc
|-- model.pkl                       |-- models/model.pkl.dvc
`-- mlruns/                         |-- tests/test_train.py
                                    `-- pyproject.toml

tests import by accident            tests import installed package
artifacts leak into root            artifacts have owners
notebook is source of truth         package is source of truth
```

## 3. `.gitignore` and `.dvcignore` Discipline

Ignore files are policy, not cosmetic. They encode what the repository refuses to remember. An ML `.gitignore` has to cover normal Python artifacts and ML-specific outputs. Normal Python ignore patterns include virtual environments, bytecode, build outputs, coverage files, and test caches. ML-specific ignore patterns include notebook checkpoints, local tracker runs, DVC cache objects, model outputs, data payloads, and framework logs.

The important rule is that Git ignores payload locations while DVC tracks selected payloads through metadata. Do not ignore the DVC metadata itself. Commit `.dvc/config`, `.dvcignore`, `dvc.yaml`, `dvc.lock`, and `.dvc` pointer files.

Ignore `.dvc/cache/`, and ignore `data/` and `models/` payloads. Let DVC add pointer files or stage metadata that Git can review. The `.dvcignore` file has a different purpose.

It tells DVC what to skip when DVC traverses the repository for status, hashing, and pipeline operations. The official DVC docs describe `.dvcignore` as similar to `.gitignore`, but for DVC traversal. That matters in ML repositories because a DVC status check can become slow if it walks through thousands of irrelevant logs, notebook checkpoints, local tracker directories, or build outputs. Use `.dvcignore` to keep DVC focused on meaningful dependencies.

Do not use `.dvcignore` to hide files that a DVC stage actually reads. If a training stage reads `schemas/customer.yml`, that schema must be visible to DVC and declared as a dependency. The practical split is:
- `.gitignore` protects Git history.
- `.dvcignore` protects DVC traversal and hashing.
- pre-commit protects the moment a developer tries to commit.
- CI repeats the checks in a clean environment.

A common mistake is assuming `.gitignore` is enough. It is not. Ignored files can still be committed if they were already tracked. Git can also be forced to add ignored files.

Notebook output can live inside an otherwise allowed `.ipynb` file. A private key can be placed inside a file with an allowed name. That is why pre-commit is part of hygiene. The hooks should fail before the bad commit exists.

For ML work, the minimum useful set is:
- `ruff` and `ruff-format` for Python linting and formatting.
- `mypy` for typed `src/` package code.
- `nbstripout` for notebook output stripping.
- `check-added-large-files` with `--maxkb=5000` to block files larger than 5 MB.
- `check-yaml` for YAML syntax.
- `detect-private-key` for deterministic private-key blocking.
- `detect-secrets` or an equivalent secret scanner with a reviewed baseline for broader token detection.

The large-file threshold is intentionally small. It catches accidents before they become habits. If a file larger than 5 MB truly belongs in Git, the PR should explain why. That exception should be rare in ML repositories.

Notebook stripping deserves special attention. `nbstripout` can run as a Git filter or as a pre-commit hook. The pre-commit path is easier to audit because the failure appears during commit and CI can repeat it.

There is a real gotcha with notebooks that are open in an editor while hooks run. The hook may strip output, then the editor may save the old output back to disk. The result looks like a broken nbstripout race.

The fix is operational, not magical. Close or refresh the notebook, run the strip command, re-add the notebook, and rerun the hook. Also remember that pre-commit operates on staged content.

When a hook modifies a file, the first commit should fail. That is expected. Inspect the diff, `git add` the cleaned file, and commit again. This is the desired failing-commit experience:
```text
$ git add .
$ git commit -m "start churn project"

nbstripout........................................................Failed
- hook id: nbstripout
- files were modified by this hook

check for added large files........................................Failed
- hook id: check-added-large-files
- data/data.bin (51200 KB) exceeds 5000 KB

detect private key.................................................Failed
- hook id: detect-private-key
- Private key found: .env

detect secrets.....................................................Failed
- hook id: detect-secrets
- Secret-like value found in .env
```

That output is not friction. It is the repository protecting its future clone time and security posture. The fix is not `git commit --no-verify`.

The fix is to move the large file behind DVC, strip the notebook, remove `.env`, and store secrets in a secret manager or local environment. The cost lens is direct.

Every large file blocked locally avoids future CI checkout cost. Every stripped notebook avoids diff noise and repeated review time. Every blocked secret avoids rotation work, audit work, and incident response. The local hook costs seconds; the late repair costs hours or days.
## 4. Dependency Management for ML

ML dependency management has three layers. Layer one is the declaration file. For modern Python projects, that is `pyproject.toml`. It declares project metadata, Python version constraints, dependencies, optional dependencies, build system, and tool configuration.

The dependency ranges in `pyproject.toml` describe what the project accepts. They do not fully define what the project ran today. Layer two is the lock file. For uv, that is `uv.lock`. For Poetry, that is `poetry.lock`. For pip-tools, that is a compiled `requirements.txt` generated from an input file. For pixi, that is `pixi.lock`. The lock file pins exact versions and transitive dependency resolution. That is the file CI should trust.

Layer three is the container image. The image pins the lock file plus operating-system packages, CUDA libraries, cuDNN, compiler stack, and runtime environment. This layer matters because ML packages often ship different wheels for CPU, CUDA, platform, and Python version combinations.

The Python lock alone does not pin the GPU driver on the node. It does not pin the base image, system libraries, or the container registry artifact. That is why a production ML environment needs all three layers. Pip alone is not enough for a repository that claims reproducibility. The `pip install -r requirements.txt` pattern can be acceptable if `requirements.txt` is fully pinned and generated by a resolver. The weak pattern is hand-editing unpinned requirements and installing them directly. That leaves too much to the resolver at install time. It also makes extras isolation messy.

ML projects often need separate groups for notebooks, training, serving, development, and GPU-specific dependencies. Installing everything everywhere makes environments larger and slower. It also increases the chance that a notebook-only package changes a production serving image.

uv gives a practical default for small and mid-size ML projects. It can create a packaged project with a `src/` layout, record a lock file, and sync the environment from the lock. It supports dependency groups and can run commands inside the project environment.

The important CI flag is `--locked`. The uv docs explain that uv can automatically lock and sync, and that `--locked` fails if the lock file is not up to date. That failure is exactly what CI should do. Otherwise, a CI command can update the lock file during validation. That is uv lock drift. The PR appears to pass, but the lock file in the branch does not represent the environment that CI used.

Use this rule: developers may update the lock file intentionally, and CI may verify the lock file. CI should not silently rewrite it. A clean uv workflow looks like this:
```bash
uv init --package myproject --python 3.12
cd myproject
uv add pandas scikit-learn dvc
uv add --dev pre-commit nbstripout ruff mypy
uv lock
uv sync --locked
uv run ruff check src tests
```

The resulting repository has a `pyproject.toml`, `.python-version`, `uv.lock`, and `src/myproject/`. The package code is installed into the virtual environment. Tests do not rely on root-relative imports. The lock file becomes reviewable evidence.

There are reasonable alternatives. pip-tools is conservative and simple. It works well when a team wants explicit input files and compiled output files, but it is less integrated as a project manager.

Poetry provides a full project workflow and lock file. Some teams prefer its packaging and publishing model. pixi is strong when Python dependencies are only part of the environment and system packages matter.

It is especially useful for teams that want conda-forge-style environment resolution with lock files. Conda is still relevant at the CUDA edge.

If a project depends on a precise mix of CUDA libraries, GPU-enabled frameworks, and native packages, conda or pixi may simplify environment construction. Do not use conda as an excuse to avoid a lock file. The repository still needs a reproducible environment contract.

Container images are where lock drift becomes expensive. If ML dependencies are unpinned, each rebuild may pull different wheels. The image may grow by hundreds of MB. Cold starts slow down, and nodes pull more data from the registry.

Caching becomes less effective, and security scanning produces moving results. The cost is both bandwidth and debugging time. A lock-first-build-second policy prevents that.

The CI or image build starts from a committed lock file. The image build installs from that lock file. A dependency bump is a PR that changes both `pyproject.toml` and the lock. Reviewers can inspect the diff. That is repository hygiene applied to dependencies.
> **Active learning prompt:** A PR changes `pyproject.toml` to allow a wider `torch` range but does not change the lock file. CI uses `uv run` without `--locked` and passes. What should the reviewer request, and what failure mode is being prevented?

## 5. Code Quality and Pre-Commit for ML

Pre-commit should be fast, and CI should be thorough. That split is the difference between a useful local gate and a gate that developers bypass. ML repositories often fail here because teams put too much into pre-commit. They add full test suites, data pulls, notebook execution, GPU checks, and Terraform plan. Then commits take minutes. Developers reach for `--no-verify`, and the policy becomes theater.

The right pre-commit scope is checks that are local, deterministic, fast, and tied to the staged diff. Formatting belongs in pre-commit. Static linting belongs in pre-commit. Notebook output stripping belongs in pre-commit.

Large-file blocking belongs in pre-commit. YAML syntax belongs in pre-commit. Private-key detection belongs in pre-commit. Type checking can belong in pre-commit if scoped to `src/` and fast enough.

SQL formatting can belong there when SQL files are part of the repository. Terraform formatting can run locally, but teams often place `terraform fmt -check` in CI to avoid making every ML commit depend on Terraform availability.

Full pytest usually does not belong in pre-commit. It belongs in CI. A small smoke test can be local if it runs in seconds, but the full suite should not block every commit on a workstation.

GPU-running steps do not belong in pre-commit. They belong in CI on a GPU runner, in a scheduled validation job, or in an orchestrated training pipeline. DVC remote pulls usually do not belong in pre-commit. They can require credentials, network, and large downloads. They belong in CI jobs that need data validation or reproduction.

Great Expectations checks may belong in CI when they validate reviewed sample fixtures. Large production data validation belongs in a pipeline or Kubernetes Job, not in a local hook. The split looks like this:
```text
developer commit
      |
      v
+-------------------------+
| fast pre-commit         |
| - ruff                  |
| - ruff-format           |
| - mypy on src/          |
| - nbstripout            |
| - YAML syntax           |
| - large file block      |
| - private key scan      |
+-------------------------+
      |
      v
pull request
      |
      v
+-------------------------+
| thorough CI             |
| - uv sync --locked      |
| - pytest                |
| - DVC pull as needed    |
| - GX checkpoint sample  |
| - terraform fmt -check  |
| - container build       |
| - optional GPU job      |
+-------------------------+
```

The local hook protects the repository from obvious damage. CI proves the project still works in a neutral environment. The code-quality rules should focus on production paths first. The `src/` package should be linted, formatted, typed, and tested. Notebooks should be stripped and may be smoke-executed in CI only when they are reports that must stay runnable.

Scratch notebooks should not be required to pass production CI. That is another reason to move repeated logic into modules. The more code lives in `src/`, the less the team depends on notebook execution for confidence.

SQL deserves the same treatment. If feature generation uses reviewed SQL, put it under a named folder such as `pipelines/sql/` and lint it with sqlfluff. If the SQL is scratch analysis, do not leave it in the repository root.

Infrastructure files deserve syntax and formatting checks. Kubernetes manifests can be validated with tools appropriate to the platform. Terraform files should be formatted.

But expensive provider initialization, remote state access, and plan generation should not happen in pre-commit. Those steps belong in CI with credentials and policy controls. The cost lens is straightforward.

A 10-second pre-commit hook that blocks a leaked model file is cheap. A 3-minute pre-commit hook that runs the full suite on every commit becomes a bypass magnet. A 6-minute CI job that catches integration breakage before merge is usually worth it. A 90-minute GPU job on every PR may not be. Use tiers: run fast checks on every commit, run standard tests on every PR, and run expensive reproduction or GPU checks on labeled PRs, scheduled jobs, or release candidates.

The repository should make that tiering visible. Put pre-commit configuration at the root. Put CI workflow definitions in one place. Document which checks are local and which are CI-only. Do not bury the policy in a chat message.
## 6. Notebook Discipline

Notebooks are useful, and they are also dangerous as a source of truth. Use notebooks for exploration, EDA, visual reports, and narrative analysis. Use Python modules for anything that gets run more than three times. Use Python modules for anything CI depends on, anything that ships to production, and anything that another notebook imports. The reason is not that notebooks are unprofessional. Notebooks optimize for interactive thinking; production systems optimize for repeatable execution. Those are different modes.

A notebook captures exploration order, intermediate outputs, rich display objects, hidden state, and manual decisions. That is useful during discovery. It is fragile when the notebook becomes the canonical training pipeline.

The common anti-pattern is notebooks as the source of truth. The team has `train_final.ipynb`, then `train_final_clean.ipynb`, then `train_final_clean_v2.ipynb`, then a serving script copied from a cell. Then a CI job runs a different script, and no one knows which artifact produced the promoted model.

The fix is to invert the relationship. The module is the source of truth. The notebook imports the module. The notebook can still explore, visualize, and explain. The repeated behavior lives in testable Python. Papermill is useful when a notebook is a parameterized report or a controlled batch artifact. The pattern is:
1. Keep reusable logic in `src/`.
2. Keep the notebook as a thin report.
3. Define parameters in the first tagged cell.
4. Execute the notebook with explicit parameters.
5. Store the rendered output as a CI artifact, report artifact, or object-store artifact.
6. Commit the notebook source without output cells.

The committed notebook remains reviewable. The rendered report remains available, and Git history stays small. The report can be reproduced. This also helps with data-quality work from [Module 5.8](../module-5.8-great-expectations-data-quality/). A notebook can inspect a Great Expectations validation result, but it should not be the only place where the checkpoint runs.

The checkpoint belongs in Python, DVC, CI, or orchestration. The notebook explains the result. DVC from [Module 5.7](../module-5.7-dvc-data-versioning/) gives the notebook a stable data boundary. The notebook should read a DVC-tracked snapshot or a documented sample fixture. It should not silently read whichever CSV is in the root today.

Strip outputs before commit, and treat this as non-negotiable. Notebook outputs create noisy diffs. They can leak data, embed images, embed HTML, and preserve exception traces with paths or secrets.

They can inflate the repository even when the notebook source is small. The safest default is no outputs in Git. There are exceptions for reviewed teaching material or deliberately committed reports, but those exceptions should be rare and explicit.

For most ML repositories, outputs belong in artifact storage, documentation builds, or tracker systems. The broken nbstripout race usually appears when a developer has a notebook open during commit.

The hook strips the output, and the notebook editor saves the old output again. The commit fails or the next diff looks dirty. The fix is to close or refresh the notebook, run `uv run nbstripout notebooks/example.ipynb`, stage the stripped file, and rerun the hook.

Do not weaken the hook. Do not accept notebook output because "it is only one PR." That exception becomes policy by imitation. Notebook hygiene also affects code review. Reviewers cannot meaningfully review thousands of JSON lines of cell output. They can review a small source diff, a DVC pointer diff, or a report artifact linked from CI. The repository should make the review path easy.
> **Active learning prompt:** A notebook contains a useful EDA chart, feature-selection code used by training, and a cell that manually patches missing labels. Which pieces should stay in the notebook, which should move into `src/`, and which should become a reviewed data-quality or data-prep stage?

## 7. Patterns and Anti-Patterns

The best ML repository hygiene patterns are boring. They make the right path easy and the wrong path noisy. Pattern: `src/` layout over flat layout. The package is installed into the environment. Tests and notebooks import the installed package. CI catches packaging mistakes early, and relative imports stop being the hidden foundation of the project. Pattern: lock first, build second. The lock file is reviewed before CI or image builds trust it. CI uses `uv sync --locked` or an equivalent lock-verification command. Container images install from the lock, and dependency bumps are deliberate PRs.

Pattern: DVC for data and model payloads. Git stores DVC metadata. DVC remote storage stores payloads. Reviewers inspect pointer and lock diffs. Training and validation jobs can pull exact artifacts by Git ref.

Pattern: Great Expectations for data contracts. The validation suite is source material. The DVC data hash identifies the dataset. The checkpoint result proves whether the dataset satisfied the contract. That pairing prevents the quiet baseline drift covered in [Module 5.8](../module-5.8-great-expectations-data-quality/).

Pattern: nbstripout as pre-commit. Notebook source stays small, and rendered outputs stay in artifacts. Review diffs stay human. Pattern: `.envrc` plus direnv for project-scoped environment variables. The repository can provide `.envrc.example`. Developers can opt in locally with direnv. Secrets stay outside Git, and environment setup becomes repeatable without sharing `.env`.

Pattern: small reviewed fixtures. Tests can include tiny synthetic fixtures. Those fixtures should be small enough for Git review. Real data snapshots belong behind DVC. Pattern: clear experiment retention. Local `mlruns/` and `wandb/` folders are ignored. The production tracking server has retention policy, and promotion evidence is exported or linked deliberately.

Now the anti-patterns. Anti-pattern: committing `mlruns/` to Git. Filesystem MLflow runs include metrics, params, artifacts, and metadata meant for a tracker or artifact store. In Git they become noisy, large, and hard to review. They also encourage people to treat local experiments as durable production evidence.

Anti-pattern: sharing `.env` files through the repository. Even fake-looking secrets train people to use the wrong channel. Real secrets in history require rotation. Use a secret manager, CI secrets, workload identity, or local untracked files.

Anti-pattern: mutable `latest` model symlinks in version control. A Git commit should identify an artifact deterministically. A `latest` symlink points to whatever someone updated last. Use content-addressed DVC metadata, registry versions, or explicit model tags.

Anti-pattern: scratch SQL in the repository root. Root scratch grows invisible dependency paths. If SQL is part of the feature contract, place it under `pipelines/sql/`, test it, and lint it. If it is exploration, keep it outside the durable repository or move it into a named notebook.

Anti-pattern: never-cleared experiment tracking server. Experiment trackers are not infinite memory. Without retention, old artifacts consume storage and make search useless. Define retention by run type. Keep promoted runs and audit evidence, and expire scratch runs.

Anti-pattern: using `git commit --no-verify` as a normal workflow. Bypassing hooks should be exceptional and reviewed. If hooks are too slow, fix the hook design. Do not normalize bypassing the repository gate.

Anti-pattern: letting CI mutate the lock file. If CI updates `uv.lock`, the branch did not test the submitted lock. Use `--locked` or the equivalent for the package manager. Anti-pattern: putting GPU training in the local hook. It will be bypassed. Put GPU validation on the appropriate CI runner or orchestration path.
## Did You Know?

- **`.dvcignore` mirrors `.gitignore` for DVC traversal** — patterns listed in `.dvcignore` are excluded when DVC scans the workspace, which keeps local caches, virtual environments, and scratch exports out of DVC operations even when they sit beside tracked data.
- **`nbstripout` can run as a Git clean/smudge filter or a pre-commit hook** — the project strips Jupyter notebook outputs before commits land, so reviewers see logic changes instead of megabytes of JSON and embedded plot data.
- **Lockfiles such as `uv.lock` pin transitive dependencies** — CI commands like `uv sync --locked` install exactly the resolved graph that reviewers approved, instead of silently upgrading packages during the pipeline run.
- **The `pre-commit` framework runs hooks only on staged files by default** — that design keeps local feedback fast while still blocking large binaries, private keys, and secret-like strings before they enter Git history.

## Common Mistakes

| Mistake | Why it happens | How to fix it |
|---|---|---|
| Committing raw datasets or model binaries to Git | Teams want a quick share path and skip DVC setup | Ignore payload directories, track snapshots with DVC pointers, and pull from the DVC remote in CI |
| Committing notebook cell outputs | Explorers save charts for convenience and forget to strip outputs | Add `nbstripout` to pre-commit and publish rendered notebooks or charts as CI artifacts |
| Using CI without `--locked` installs | Pipelines stay green while the lock file drifts from `pyproject.toml` | Regenerate the lock in the PR, commit it, and run `uv sync --locked` (or the equivalent) in CI |
| Checking in local `mlruns/` or W&B folders | Teammates want experiment diffs inside the repository | Ignore tracker directories locally and store promotion evidence as model cards, metrics exports, or registry links |
| Sharing secrets through `.env` in Git | Shortcuts during debugging bypass secret managers | Keep `.env.example` in Git, load real secrets from a manager or CI secret store, and scan with `detect-secrets` |
| Pointing `models/latest` at a moving target | Mutable aliases feel convenient during local iteration | Version models with DVC hashes, registry tags, or immutable release names tied to training commits |
| Putting GPU training or cluster dry runs in pre-commit | Every change feels important enough to validate fully | Keep hooks fast (format, lint, strip, size checks) and run expensive validation on dedicated CI runners |
| Ignoring `.dvcignore` until pulls are slow | DVC walks every file under the project root by default | Add `.dvcignore` early for `.venv/`, caches, and scratch paths so DVC stays focused on real artifacts |

## Knowledge Check

Use these scenarios to test whether you can apply the module.
<details>
<summary>1. A PR adds `models/churn.pkl`, `models/churn.pkl.dvc`, and `dvc.lock`. The author says the `.dvc` file proves DVC is being used. What should the reviewer request?</summary>

The reviewer should request that the raw model payload be removed from Git history before merge, leaving only the DVC pointer or stage metadata plus `dvc.lock`.

Committing both the payload and pointer defeats the purpose of DVC.

The reviewer should also ask for proof that the model object was pushed to the DVC remote if CI or teammates need to pull it.
</details>

<details>
<summary>2. CI starts failing because `uv sync --locked` says the lock file is outdated after a dependency range changed in `pyproject.toml`. A teammate proposes removing `--locked`. What is the correct fix?</summary>

Keep `--locked`.

The failure is useful because the branch changed dependency policy without committing the resolved lock.

The correct fix is to run `uv lock`, review the lock diff, commit it with the `pyproject.toml` change, and rerun CI.

Removing `--locked` would let CI validate a rewritten environment that is not represented by the PR.
</details>

<details>
<summary>3. A notebook PR shows 9000 changed lines, mostly JSON output and base64 image content. The author says the chart is important evidence. How should the team preserve the evidence without accepting the diff?</summary>

Strip notebook outputs before commit and publish the rendered chart or executed notebook as a CI artifact, report artifact, or documentation artifact.

If the chart depends on data, record the DVC data hash and code commit that generated it.

The source notebook can stay reviewable while the evidence remains accessible outside Git history.
</details>

<details>
<summary>4. A team commits `mlruns/` so reviewers can compare experiments. Months later clone time has doubled and the tracker folders are hard to search. What repository policy should replace this?</summary>

Ignore local `mlruns/` folders and use a real experiment tracker or artifact store for run payloads.

Commit only lightweight promotion evidence, such as a model card, metric summary, DVC hash, run URL, or reviewed export.

Define retention for scratch runs separately from promoted runs.
</details>

<details>
<summary>5. A Kubernetes batch scoring manifest and a Terraform module are added to an ML repository. A developer wants every commit to run Terraform initialization and a cluster dry run locally. Why is that a poor pre-commit design?</summary>

Those checks may need provider plugins, credentials, remote state, network access, or a cluster context.

That makes the local hook slow and environment-sensitive.

Keep pre-commit focused on fast syntax and formatting gates, then run `terraform fmt -check`, validation, and deployment policy checks in CI with controlled credentials.
</details>

<details>
<summary>6. A team uses a version-controlled `models/latest` symlink that points to the current model file. Rollback fails because two branches changed the link differently. What is the better artifact identity pattern?</summary>

Use immutable artifact identity: a DVC hash, an explicit model registry version, or a release tag that maps to a content-addressed object.

A Git commit should identify the exact model artifact used by training, validation, and serving.

A mutable `latest` link is convenient for local browsing but weak for review and rollback.
</details>

<details>
<summary>7. A data scientist keeps copying feature-selection code from a notebook into `train.py`, and the two versions drift. What repository change would reduce this risk?</summary>

Move the feature-selection logic into `src/myproject/features.py`, write tests for it, and import it from both the notebook and training command.

The notebook can remain the exploration surface.

The package module becomes the reusable source of truth.

That keeps CI, notebooks, and training aligned.
</details>

<details>
<summary>8. A large Git LFS bill appears after the team starts storing weekly model weights there. The models are tied to DVC data snapshots and metrics. When is DVC remote storage likely the better fit?</summary>

DVC is usually better when model weights are part of an ML lineage graph with data hashes, metrics, parameters, and reproducible stages.

Git LFS can fit a small number of large files that should behave like Git-managed assets.

For recurring datasets and model artifacts, a DVC remote with lifecycle policy and promotion rules is often cheaper and more operationally expressive.
</details>

## Hands-On Exercise: Build a Clean ML Repository
In this exercise you will create a clean ML repository from scratch using uv, DVC, and pre-commit. You will also create three deliberate failures, and the failures are the point. The repository should reject a dirty notebook, a large binary file, and a fake private key before a commit lands. Use a disposable directory, and do not run these commands inside an existing production repository. Bind any local service you add later to `127.0.0.1` only, and this lab does not require a long-running server.

### Step 1: Initialize a Packaged uv Project
Create a packaged project with a `src/` layout, and the packaged uv template creates `src/myproject/` and configures a build backend. That matters because tests and notebooks should import the installed package, not a root-relative script. Install ML and development dependencies, and create the expected repository folders, and initialize Git and DVC.

```bash
uv init --package myproject --python 3.12
cd myproject
```

```bash
uv add pandas scikit-learn dvc
uv add --dev pre-commit nbstripout ruff mypy detect-secrets pytest
uv lock
uv sync --locked
```

```bash
mkdir -p data/raw data/processed models notebooks pipelines tests infra/k8s infra/terraform experiments docs
touch experiments/README.md docs/model-card.md
```

```bash
git init
dvc init -q
```

### Step 2: Write the ML-Specific `.gitignore`
Create `.gitignore` with this full content. This file ignores payloads, but it does not ignore DVC metadata, and after `dvc add data/raw/example.csv`, Git should see the pointer file, not the payload.

```text
# Python bytecode and caches
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/

# Virtual environments
.venv/
venv/
env/

# Build and packaging outputs
build/
dist/
*.egg-info/

# Local editor and OS files
.DS_Store
.idea/
.vscode/
*.swp

# Secrets and local environment
.env
.env.*
!.env.example
.direnv/

# Jupyter notebooks
.ipynb_checkpoints/

# ML experiment trackers and logs
mlruns/
wandb/
lightning_logs/
tensorboard/
runs/

# Data and model payloads
data/**
!data/**/
!data/**/*.dvc
!data/**/.gitignore
models/**
!models/**/
!models/**/*.dvc
!models/**/.gitignore
*.pkl
*.joblib
*.pt
*.pth
*.onnx
*.safetensors

# DVC local cache and temp files
.dvc/cache/
.dvc/tmp/

# Local reports and generated artifacts
reports/generated/
*.html
*.parquet
*.feather
*.arrow

# Terraform local state and plans
infra/**/.terraform/
infra/**/*.tfstate
infra/**/*.tfstate.*
infra/**/*.tfplan
```

### Step 3: Write `.dvcignore`
Create `.dvcignore`. This file should not hide real DVC dependencies, and if a stage reads a file, do not place that file behind `.dvcignore`.

```text
# Keep DVC traversal away from local noise.
.git/
.venv/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.ipynb_checkpoints/
mlruns/
wandb/
lightning_logs/
tensorboard/
runs/
reports/generated/
infra/**/.terraform/
```

### Step 4: Write `pyproject.toml`
Replace or adjust `pyproject.toml` so it has an explicit package, Python pin, and tool configuration. The exact dependency versions will be resolved in `uv.lock`, and the ranges in `pyproject.toml` describe allowed versions. The lock file records the selected versions.

```toml
[project]
name = "myproject"
version = "0.1.0"
description = "Clean ML repository hygiene lab"
readme = "README.md"
requires-python = ">=3.12,<3.13"
dependencies = [
  "dvc>=3.60",
  "pandas>=2.2",
  "scikit-learn>=1.6",
]

[dependency-groups]
dev = [
  "detect-secrets>=1.5",
  "mypy>=1.15",
  "nbstripout>=0.8",
  "pre-commit>=4.0",
  "pytest>=8.3",
  "ruff>=0.9",
]

[build-system]
requires = ["hatchling>=1.27"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/myproject"]

[tool.ruff]
line-length = 100
target-version = "py312"
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.mypy]
python_version = "3.12"
strict = true
mypy_path = "src"
packages = ["myproject"]
```

### Step 5: Write `.pre-commit-config.yaml`
Create `.pre-commit-config.yaml`, and create an initial secrets baseline after confirming no real secrets are present. Install the hooks, and run them once. The first run may modify files, and review the diff, stage the changes, and rerun.

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.10
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: check-added-large-files
        args: [--maxkb=5000]
      - id: check-yaml
      - id: detect-private-key

  - repo: https://github.com/kynan/nbstripout
    rev: 0.8.1
    hooks:
      - id: nbstripout

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: [--baseline, .secrets.baseline]
        exclude: uv.lock

  - repo: local
    hooks:
      - id: mypy-src
        name: mypy on src package
        entry: uv run mypy src
        language: system
        pass_filenames: false
        files: ^src/
```

```bash
uv run detect-secrets scan > .secrets.baseline
```

```bash
uv run pre-commit install
```

```bash
uv run pre-commit run --all-files
```

### Step 6: Add Minimal Package Code
Replace `src/myproject/__init__.py`, and create `src/myproject/features.py`, and create a tiny test, and save that test as `tests/test_features.py`.

```python
from myproject.features import FEATURE_COLUMNS, select_features

__all__ = ["FEATURE_COLUMNS", "select_features"]
```

```python
from __future__ import annotations

import pandas as pd

FEATURE_COLUMNS = ["age", "tenure_months", "monthly_spend"]

def select_features(frame: pd.DataFrame) -> pd.DataFrame:
    missing = sorted(set(FEATURE_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"missing required feature columns: {missing}")
    return frame.loc[:, FEATURE_COLUMNS]
```

```python
import pandas as pd

from myproject.features import select_features

def test_select_features_keeps_contract_order() -> None:
    frame = pd.DataFrame(
        {
            "monthly_spend": [120.0],
            "age": [36],
            "tenure_months": [18],
            "ignored": ["x"],
        }
    )

    selected = select_features(frame)

    assert list(selected.columns) == ["age", "tenure_months", "monthly_spend"]
```

### Step 7: Create the Deliberate Failures
Create a notebook with output cells, and create a large fake data file. Create a fake private key in `.env`. Now attempt the commit, and the `.env` file is ignored, so `git add .` should not stage it. For this lab, force-add it to prove the secret hooks catch a bypass or already-tracked leak. Expected failures: The notebook fails because output cells are present, and the binary fails because it is larger than 5 MB. The `.env` file fails because it contains a private-key shape and secret-like content.

```bash
cat > notebooks/dirty_eda.ipynb <<'JSON'
{
  "cells": [
    {
      "cell_type": "code",
      "execution_count": 1,
      "metadata": {},
      "outputs": [
        {
          "name": "stdout",
          "output_type": "stream",
          "text": ["leaky notebook output\\n"]
        }
      ],
      "source": ["print('leaky notebook output')"]
    }
  ],
  "metadata": {
    "kernelspec": {
      "display_name": "Python 3",
      "language": "python",
      "name": "python3"
    },
    "language_info": {
      "name": "python",
      "version": "3.12"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 5
}
JSON
```

```bash
dd if=/dev/zero of=data.bin bs=1m count=50
```

```bash
cat > .env <<'EOF'
PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
fake-training-key-do-not-use
-----END PRIVATE KEY-----"
EOF
```

```bash
git add .
git add -f .env
git commit -m "start clean ml repository"
```

```text
nbstripout........................................................Failed
check for added large files........................................Failed
detect private key.................................................Failed
detect secrets.....................................................Failed
```

### Step 8: Fix the Failures Correctly
Strip the notebook, and move the large file behind DVC, and remove the secret-bearing `.env` from the index and create a safe template. Rerun the hooks, and if `nbstripout` modifies the notebook again, stage it again. Commit the cleaned state.

```bash
uv run nbstripout notebooks/dirty_eda.ipynb
git add notebooks/dirty_eda.ipynb
```

```bash
mkdir -p data/raw
mv data.bin data/raw/data.bin
dvc add data/raw/data.bin
git add data/raw/data.bin.dvc data/raw/.gitignore
```

```bash
git rm --cached .env
rm -f .env
cat > .env.example <<'EOF'
MYPROJECT_PROFILE=dev
DVC_REMOTE_NAME=local
EOF
git add .env.example .gitignore .secrets.baseline
```

```bash
uv run pre-commit run --all-files
```

```bash
git add notebooks/dirty_eda.ipynb
uv run pre-commit run --all-files
```

```bash
git add pyproject.toml uv.lock .pre-commit-config.yaml .dvcignore .dvc .gitignore
git add src tests notebooks pipelines infra experiments docs
git commit -m "start clean ml repository"
```

### Step 9: Add DVC Pipeline Metadata
Create a tiny DVC stage that records a deterministic data-prep command, and create `dvc.yaml`. Run the stage, and the payload stays out of Git, and the metadata stays in Git. That is the DVC contract from [Module 5.7](../module-5.7-dvc-data-versioning/).

```bash
cat > pipelines/prepare.py <<'PY'
from pathlib import Path

raw = Path("data/raw/data.bin")
processed = Path("data/processed/summary.txt")
processed.parent.mkdir(parents=True, exist_ok=True)
processed.write_text(f"bytes={raw.stat().st_size}\n", encoding="utf-8")
PY
```

```yaml
stages:
  prepare:
    cmd: uv run python pipelines/prepare.py
    deps:
      - pipelines/prepare.py
      - data/raw/data.bin
    outs:
      - data/processed/summary.txt
```

```bash
dvc repro
git add dvc.yaml dvc.lock pipelines/prepare.py data/processed/.gitignore
git commit -m "add DVC prepare stage"
```

### Step 10: Add Kubernetes and Terraform Files
Create `infra/k8s/batch-score-job.yaml`, and this manifest uses stable Kubernetes `batch/v1`, which is appropriate for Kubernetes 1.35+. Create `infra/terraform/main.tf`. Do not put `terraform fmt -check` in pre-commit for this lab, and run it in CI, where Terraform is installed deliberately. Create `.github/workflows/ml-hygiene-ci.yaml`, and the CI split is intentional, and python checks use the lock file. Repository hygiene repeats pre-commit in a clean checkout, and terraform formatting runs in CI, not in the local hook. Long GPU jobs would be another CI job with an explicit runner label, not a pre-commit hook.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: churn-batch-score
  labels:
    app.kubernetes.io/name: churn-batch-score
    app.kubernetes.io/part-of: myproject
spec:
  backoffLimit: 1
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: score
          image: python:3.12-slim
          command: ["/bin/sh", "-c"]
          args:
            - |
              python -c "import pathlib; p=pathlib.Path('models/churn.pkl.dvc'); print('batch-score hygiene:', 'dvc-pointer-present' if p.exists() else 'missing-dvc-pointer')"
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "256Mi"
```

```hcl
terraform {
  required_version = ">= 1.8"

  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.36"
    }
  }
}

variable "namespace" {
  type        = string
  description = "Namespace for ML hygiene lab resources."
  default     = "ml-hygiene"
}
```

```yaml
name: ml-hygiene-ci

on:
  pull_request:

jobs:
  python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: astral-sh/setup-uv@v6
      - run: uv sync --locked
      - run: uv run ruff check src tests
      - run: uv run ruff format --check src tests
      - run: uv run mypy src
      - run: uv run pytest

  repository-hygiene:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: astral-sh/setup-uv@v6
      - run: uv sync --locked
      - run: uv run pre-commit run --all-files

  infra-format:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: hashicorp/setup-terraform@v3
      - run: terraform -chdir=infra/terraform fmt -check -recursive
```

### Step 11: End-State Onboarding Demo

A new contributor should need only this sequence:

```bash
git clone <repo-url>
cd myproject
uv sync --locked
dvc pull
uv run pre-commit install
```

That sequence proves the repository is small, reproducible, and explicit. Git brings source material, uv brings the Python environment from the lock, and DVC brings data and model payloads. pre-commit brings local gates, and nothing requires a shared drive, copying `.env`, or guessing which notebook is canonical.

### Lab Success Criteria
You have completed the lab when you can verify all of the following:

- [ ] `pyproject.toml` declares a packaged `src/` layout.

- [ ] `uv.lock` exists and CI uses `uv sync --locked`.

- [ ] DVC is initialized and data payloads are not committed directly.

- [ ] `.gitignore` excludes ML payloads, local tracker folders, notebook checkpoints, secrets, and caches.

- [ ] `.dvcignore` keeps DVC traversal away from local noise.

- [ ] pre-commit blocks notebook outputs, large files, private keys, and secret-like values.

- [ ] `mypy` runs on the `src/` package, not on every scratch notebook.

- [ ] Terraform format checking runs in CI, not in pre-commit.

- [ ] The Kubernetes manifest uses stable APIs suitable for Kubernetes 1.35+.

- [ ] A clean checkout can run `uv sync --locked`, `dvc pull`, and `uv run pre-commit install`.


## Next Module

Continue to [Module 5.10: Production Model-Serving Traffic Patterns](../module-5.10-model-serving-traffic-patterns/).

## Sources

- [uv documentation](https://docs.astral.sh/uv/) - Official overview of uv as a Python package and project manager with lockfile support.
- [uv creating projects](https://docs.astral.sh/uv/concepts/projects/init/) - Official reference for `uv init --package`, `src/` layout, Python pins, and build backends.
- [uv locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/) - Official reference for lock files, syncing, `--locked`, and `--frozen`.
- [DVC `.dvcignore` files](https://dvc.org/doc/user-guide/project-structure/dvcignore-files) - Official reference for excluding files from DVC traversal.
- [DVC command reference: `init`](https://dvc.org/doc/command-reference/init) - Official behavior for initializing DVC metadata in a Git repository.
- [DVC command reference: `add`](https://dvc.org/doc/command-reference/add) - Official behavior for tracking data and model payloads through DVC pointer metadata.
- [pre-commit documentation](https://pre-commit.com/) - Official documentation for hook configuration, supported Git hooks, staged-file behavior, and installation.
- [pre-commit-hooks repository](https://github.com/pre-commit/pre-commit-hooks) - Official hook collection containing `check-added-large-files`, `check-yaml`, and `detect-private-key`.
- [nbstripout repository](https://github.com/kynan/nbstripout) - Official project documentation for stripping notebook outputs as a Git filter or pre-commit hook.
- [Yelp detect-secrets repository](https://github.com/Yelp/detect-secrets) - Official project documentation for detecting secrets with baseline support.
- [Cookiecutter Data Science repository](https://github.com/drivendataorg/cookiecutter-data-science) - Official project layout reference for standardized data science repositories.
- [GitHub Docs: About Git Large File Storage](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage) - Official explanation of Git LFS pointer behavior and file-size limits.
- [Ruff documentation](https://docs.astral.sh/ruff/) - Official documentation for Ruff linting and formatting.
- [mypy documentation](https://mypy.readthedocs.io/en/stable/) - Official documentation for Python static type checking.
- [Terraform `fmt` command reference](https://developer.hashicorp.com/terraform/cli/commands/fmt) - Official reference for checking Terraform formatting.
- [Kubernetes Jobs documentation](https://kubernetes.io/docs/concepts/workloads/controllers/job/) - Official reference for `batch/v1` Job behavior.
- [direnv documentation](https://direnv.net/) - Official documentation for directory-scoped environment loading.
