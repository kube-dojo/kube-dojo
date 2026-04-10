---
title: "Data Pipelines"
slug: ai-ml-engineering/mlops/module-10.7-data-pipelines
sidebar:
  order: 1108
---
> **AI/ML Engineering Track** | Complexity: `[COMPLEX]` | Time: 5-6
> **Migrated from neural-dojo** — pending pipeline polish

## The $50 Million Bug: When "train_FINAL_v2.csv" Destroyed a Product Launch

**Seattle. March 12, 2021. 9:47 AM.**

Jennifer Chen, lead ML engineer at a major retail company, was about to have the worst day of her career. In two hours, their new personalized pricing model would go live—a system that had taken 18 months and a team of 12 engineers to build.

The model had performed beautifully in testing. A/B tests showed a 23% increase in conversion rates. Leadership was ecstatic. The CEO had already announced the launch to investors.

Then Jennifer got a Slack message from a junior engineer: "Hey, quick question—which training data should I use for the final model? train_v3.csv or train_v3_FINAL.csv?"

Her stomach dropped.

She opened the data folder and found chaos:

```
data/
├── train.csv
├── train_v2.csv
├── train_v2_clean.csv
├── train_v3.csv
├── train_v3_FINAL.csv
├── train_v3_FINAL_REAL.csv
├── train_FINAL_USE_THIS.csv
└── train_march_update.csv
```

"Which one did we use for the production model?" she typed back, dreading the answer.

Silence. Then: "I... I'm not sure. I think Dave used one of them but he's on vacation."

Over the next 48 hours, the team discovered a horrifying truth: the production model had been trained on `train_v3.csv`—a dataset that was two months out of date and missing critical features. The model they'd tested had used `train_v3_FINAL_REAL.csv`. They were completely different datasets.

The launch was delayed by three weeks. The company lost an estimated $50 million in the holiday season. Three engineers were fired. And Jennifer spent the next six months implementing what should have been there from the start: **data versioning**.

> "We version our code religiously. But our data was stored like photos on my grandmother's computer—folders named 'vacation pics' and 'vacation pics (2)'. That inconsistency cost us everything."
> — Jennifer Chen, speaking at MLOps World 2022

This module teaches you how to avoid Jennifer's nightmare. You'll learn to version data like code, manage features across teams, and validate data quality automatically. These aren't nice-to-haves—they're the foundation of production ML that actually works.

The stakes are higher than you might think. In ML, your model is only as good as your data—and your data is only as valuable as your ability to track, version, and validate it. A model trained on corrupted data doesn't throw errors. It doesn't crash. It quietly makes terrible predictions that destroy trust, revenue, and sometimes careers.

By the end of this module, you'll have the tools and practices to ensure that never happens to you.

---

## What You'll Be Able to Do

By the end of this module, you will:
- Master DVC for dataset and model versioning—the industry standard for tracking datasets like code
- Understand feature stores and implement Feast—the solution to feature engineering chaos
- Implement data validation with Great Expectations—unit tests for your data
- Build reproducible ML pipelines with versioned data—because "it worked on my machine" isn't acceptable
- Understand data lineage and governance—tracing data from source to model for debugging and compliance

---

##  Theory

### The Data Management Problem

Data is the foundation of ML, but it's often treated as an afterthought. We obsess over model architectures while our data sits in chaotic folder structures with names like "final_v2_REAL.csv". This is like building a house on sand—no matter how beautiful the structure, it will collapse.

The data management problem has three layers, each more insidious than the last:

**Layer 1: Version Chaos.** Without versioning, you can't answer basic questions: "What data trained model v2.3?" "Has the training data changed since last week?" "Can we reproduce last month's results?" In software engineering, these questions are trivially answered with Git. In ML, they often produce shrugs and guesses.

**Layer 2: Feature Inconsistency.** Different teams compute the same features differently. Your data science team calculates "user_age" one way in Python. Your backend team calculates it another way in SQL. Your mobile team calculates it a third way in Swift. Same concept, three implementations, three bugs waiting to happen.

**Layer 3: Silent Quality Degradation.** Data drifts silently. Your training data had 2% missing values. New production data has 15% missing. Your model doesn't fail—it just makes increasingly worse predictions. By the time someone notices, the damage is done.

Think of data versioning like a time machine for your datasets. Git lets you travel back in time through your code history. DVC lets you do the same with your data. You can answer questions like "What dataset did model v2.3 use?" and "What changed between training runs?" Instead of guessing, you can know.

```
THE DATA CHAOS PROBLEM
======================

Without Versioning:
───────────────────
"Which version of the dataset was model v2.3 trained on?"
"Did someone update the preprocessing script?"
"Why do we get different results on the same code?"

    data/
    ├── train.csv
    ├── train_v2.csv
    ├── train_final.csv
    ├── train_FINAL_real.csv
    └── train_USE_THIS_ONE.csv

With DVC:
─────────
    data/
    └── train.csv.dvc  ← Tracked in Git, points to versioned data

    git log:
    - commit abc123: "Add train data v3.2 (50K samples)"
    - commit def456: "Update train data v3.1 (45K samples)"
    - commit ghi789: "Initial train data v3.0 (40K samples)"
```

### Did You Know? The 85% Failure Rate

A 2022 survey by Gartner found that **85% of AI projects fail**, with "data quality issues" cited as the #1 reason. Google's ML team reported that data-related issues cause **60% of production ML failures**. This led to the "Data-Centric AI" movement championed by **Andrew Ng**, shifting focus from model architecture to data quality and versioning.

The Data-Centric AI movement represents a philosophical shift in how we think about ML. For years, the ML community focused on model architecture—new layers, new attention mechanisms, new training techniques. Kaggle competitions rewarded clever model ensembles. Research papers emphasized architectural innovations.

Andrew Ng challenged this orthodoxy. In his now-famous "Landing AI" presentation, he showed that systematic data improvement often beats sophisticated modeling. A company using a simple model on carefully curated data consistently outperformed competitors using state-of-the-art architectures on messy data.

The key insight: models are commoditizing, but data remains differentiating. Anyone can download the same open-source model. Not everyone has clean, well-versioned, high-quality data. The competitive advantage has shifted from "who has the best model" to "who has the best data."

Andrew Ng put it bluntly in a 2021 keynote:

> "In AI, data is food. You can have the most sophisticated kitchen in the world, but if your ingredients are rotten, your meal will be terrible. We've been obsessing over the kitchen while ignoring the pantry."

---

## 1. DVC: Data Version Control

### What is DVC?

DVC (Data Version Control) is Git for data and ML models. Think of it like a librarian for your datasets—it keeps track of every version, knows where everything is stored, and can retrieve any historical version on demand.

To understand why DVC matters, imagine trying to manage a library without a catalog system. Every book is somewhere on the shelves, but nobody knows where. Readers wander the stacks hoping to stumble across what they need. When someone asks "do we have the 1985 edition of this textbook?" the librarian can only shrug.

That's what data management looks like without DVC. Datasets exist somewhere on S3 or Google Cloud Storage. Someone downloaded a version last month. Someone else modified it. The original might still exist. Or maybe it was overwritten. Nobody knows for certain.

DVC creates that missing catalog. Every dataset gets a unique identifier. Every version is tracked. Every change is logged. When someone asks "what data trained model v2.3?" the answer is one command away.

The core insight is elegant: Git is terrible at tracking large files, but great at tracking small text files. So DVC creates small "pointer" files (`.dvc` files) that Git tracks, while the actual data lives in external storage (S3, GCS, Azure, or local disk). It's like keeping a library card catalog in Git while the actual books sit on warehouse shelves.

```
DVC ARCHITECTURE
================

┌─────────────────────────────────────────────────────────────────────┐
│                           DVC                                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │   Data Files    │  │    Pipelines    │  │    Metrics      │    │
│  │                 │  │                 │  │                 │    │
│  │ • .dvc files    │  │ • dvc.yaml      │  │ • dvc metrics   │    │
│  │ • Remote storage│  │ • Reproducible  │  │ • Experiments   │    │
│  │ • Cache         │  │ • Dependencies  │  │ • Comparisons   │    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Remote Storage                            │   │
│  │  S3 | GCS | Azure Blob | SSH | Local | HTTP | HDFS          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Basic DVC Workflow

The DVC workflow mirrors Git so closely that if you know Git, you already know 80% of DVC. This wasn't accidental—Dmitry Petrov deliberately designed DVC to feel familiar. When you've been using Git for a decade, the last thing you want is to learn a completely new paradigm for data.

The mental model is simple: DVC handles big files the same way Git handles small files. `git add` becomes `dvc add`. `git push` becomes `dvc push`. `git pull` becomes `dvc pull`. The commands feel natural because they are natural—just extended to work with data.

The key commands map directly:

```bash
# Initialize DVC in a Git repo
cd my-ml-project
git init
dvc init

# Add data to DVC tracking (like git add, but for big files)
dvc add data/train.csv
# Creates: data/train.csv.dvc (small text file, tracked by Git)
# Actual data stored in .dvc/cache/

# Commit the .dvc file (the pointer, not the data)
git add data/train.csv.dvc data/.gitignore
git commit -m "Add training data v1.0"

# Push data to remote storage (like git push, but for data)
dvc remote add -d myremote s3://my-bucket/dvc-cache
dvc push

# Later: pull data on another machine (like git pull)
git clone <repo>
dvc pull
```

The magic happens in that `.dvc` file—a small YAML file that Git happily tracks:

```yaml
# data/train.csv.dvc
outs:
  - md5: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
    size: 1048576
    path: train.csv
```

This file is like a receipt. It says "the file `train.csv` has this specific hash and this size." When you `dvc pull`, DVC uses this receipt to fetch the exact right version from storage.

### DVC Pipelines: Reproducibility Built In

DVC doesn't just version data—it versions entire ML pipelines. You define your pipeline in `dvc.yaml`, and DVC tracks dependencies, parameters, and outputs. It's like a Makefile for ML that actually understands data dependencies.

This is where DVC becomes truly powerful. Data versioning alone is useful, but pipeline versioning is transformative. Consider the typical ML workflow: you preprocess data, train a model, evaluate it, and maybe do some post-processing. Each step depends on the outputs of previous steps. Change your preprocessing, and everything downstream needs to re-run. Change a hyperparameter, and only training and evaluation need to re-run.

Without DVC, you track these dependencies manually—or more likely, you don't track them at all. You run the entire pipeline every time, wasting hours on unchanged steps. Or you run only part of the pipeline and wonder why your results don't match last week's.

DVC pipelines make dependencies explicit. You declare what each step needs and what it produces. DVC builds a dependency graph and intelligently re-runs only what changed. It's like having a smart assistant who knows exactly which steps need to run based on what you modified.

```yaml
# dvc.yaml - Your ML pipeline as code
stages:
  preprocess:
    cmd: python src/preprocess.py
    deps:
      - src/preprocess.py
      - data/raw/
    params:
      - preprocess.split_ratio
    outs:
      - data/processed/

  train:
    cmd: python src/train.py
    deps:
      - src/train.py
      - data/processed/
    params:
      - train.learning_rate
      - train.epochs
    outs:
      - models/model.pkl
    metrics:
      - metrics.json:
          cache: false

  evaluate:
    cmd: python src/evaluate.py
    deps:
      - src/evaluate.py
      - models/model.pkl
      - data/processed/test.csv
    metrics:
      - evaluation.json:
          cache: false
```

DVC automatically builds a dependency graph and only re-runs stages when their inputs change. Changed the preprocessing script? Only preprocessing and downstream stages re-run. Changed a hyperparameter? Only training and evaluation re-run. It's incremental builds for ML.

```
DVC PIPELINE DAG
================

     ┌────────────────┐
     │   data/raw/    │
     └───────┬────────┘
             │
             ▼
     ┌────────────────┐
     │  preprocess    │
     │                │
     │  deps:         │
     │  - raw data    │
     │  - script      │
     └───────┬────────┘
             │
             ▼
     ┌────────────────┐
     │    train       │
     │                │
     │  deps:         │
     │  - processed   │
     │  - params      │
     └───────┬────────┘
             │
             ▼
     ┌────────────────┐
     │   evaluate     │
     │                │
     │  outputs:      │
     │  - metrics     │
     └────────────────┘
```

### Did You Know? The Origin of DVC

DVC was created by **Dmitry Petrov**, a former Microsoft data scientist, in 2017. The name is a play on "CSV" (Comma-Separated Values), which is ironic since DVC handles any file type. Dmitry founded **Iterative.ai**, the company behind DVC, which raised $20M in funding.

The project started from Dmitry's frustration at Microsoft:

> "I kept seeing the same pattern. Teams would build amazing models, then spend weeks trying to reproduce them because nobody knew which data version they'd used. Git solved this for code 20 years ago. Why were we still living in the dark ages for data?"
> — Dmitry Petrov, DVC creator

Today, DVC is used by companies like Intel, Microsoft, and Hugging Face. It has over 12,000 GitHub stars and a vibrant community.

The success of DVC highlights an important lesson: ML tools succeed when they meet practitioners where they are. DVC didn't ask data scientists to learn a completely new paradigm. It built on Git, which most developers already know. The learning curve is gentle because the concepts are familiar—just applied to a new domain.

This is why DVC won against more ambitious alternatives like Pachyderm (which required Kubernetes and a complete infrastructure overhaul). DVC is a scalpel where others offered chainsaws. You can add it to an existing project in five minutes and see immediate benefits. That simplicity drove adoption, and adoption drove community, and community drove features.

### DVC Experiments

DVC also tracks experiments, letting you run multiple training configurations and compare results:

```bash
# Run experiment with parameter changes
dvc exp run -S train.learning_rate=0.001 -S train.epochs=20

# List experiments
dvc exp show

# Compare experiments
dvc exp diff exp-abc123 exp-def456

# Apply best experiment to your branch
dvc exp apply exp-abc123
git commit -m "Apply best experiment"
```

This is like git branches for hyperparameters. You can try dozens of configurations, compare their metrics, and promote the best one—all without manually tracking spreadsheets.

---

## 2. Feature Stores: Solving the Feature Engineering Problem

### The Feature Engineering Chaos

Feature engineering is where data science meets software engineering—and usually crashes. The problem isn't computing features; it's managing them across teams, environments, and time.

Here's a scenario that happens at virtually every company using ML. Your recommendation team builds a user embeddings feature. It works great. Your fraud team hears about it and wants to use it too. But they can't just import it—they're using different languages, different databases, different deployment infrastructure. So they reimplement it. Three months later, a third team reimplements it again.

Now you have three implementations of the "same" feature:
- Team A: Python, computes on-demand, uses birthdate field
- Team B: SQL, batch computed nightly, uses signup_year minus birth_year
- Team C: Java, cached in Redis, uses age_bucket categories

Same concept. Three implementations. Three sources of bugs. When Team A discovers an edge case and fixes it, Teams B and C continue using buggy versions. When the underlying data schema changes, each team scrambles independently to fix their code.

This is feature engineering chaos, and it's shockingly common. A 2020 Tecton survey found that **87% of ML practitioners had experienced feature engineering bugs** in production. Feature stores exist to solve this problem.

Think of it like a restaurant kitchen without recipes. Every chef makes their own version of "garlic sauce"—some add cream, some don't, some roast the garlic first. Customers get inconsistent dishes, and when a chef leaves, their recipes leave with them.

```
FEATURE ENGINEERING CHAOS
=========================

Without Feature Store:
──────────────────────
Team A: "We compute user_age from birthdate"
Team B: "We compute age from signup_year - birth_year"
Team C: "We use age_bucket categorical feature"

Result: Same feature, 3 different implementations!

Training vs Serving Skew:
────────────────────────
Training: Features computed in batch (Spark, 1 hour lag)
Serving:  Features computed in real-time (different code)
Result:   Model works in training, fails in production!

With Feature Store:
──────────────────
┌─────────────────────────────────────────────────────────────────┐
│                     FEATURE STORE                               │
├─────────────────────────────────────────────────────────────────┤
│  Single source of truth for all features                        │
│  Same features for training AND serving                         │
│  Versioning, lineage, discovery                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Training-Serving Skew: The Silent Killer

The most insidious problem in production ML is **training-serving skew**. Your model trains on features computed one way (say, a Spark job running overnight) but serves predictions using features computed another way (say, real-time Python code). Even tiny differences can cause dramatic accuracy drops.

It's like training a translator on formal English, then deploying them in a room full of teenagers using slang. The "language" is different enough that the skills don't transfer.

Here's a concrete example of how this happens. Your training pipeline computes "days_since_last_purchase" using this logic:

```python
# Training: Spark job running on historical data
days_since = (snapshot_date - last_purchase_date).days
```

Your serving pipeline computes it using this logic:

```python
# Serving: Python running in real-time
days_since = (datetime.now() - last_purchase_date).days
```

Spot the difference? Training uses `snapshot_date` (the date when the training data was created). Serving uses `datetime.now()` (the current moment). If your training data is two weeks old, every serving prediction has a 14-day bias. Your model learned that "20 days since last purchase" means one thing. In production, it means something different.

This bug doesn't crash your system. It doesn't throw exceptions. It just makes your model subtly wrong—and wrong in a way that's almost impossible to debug without understanding the training-serving gap.

Feature stores solve this by ensuring the exact same code computes features for training and serving. One definition, one implementation, consistent results.

### Feast: Open-Source Feature Store

Feast (Feature Store) is the leading open-source solution. Think of it as a database specifically designed for ML features—with time-travel capabilities, online/offline stores, and first-class support for ML workflows.

The name "Feast" is a playful acronym for "Feature Store." It was created at Gojek (the Indonesian super-app) by Willem Pienaar, who previously worked on Uber's Michelangelo platform—arguably the first production feature store at scale. When Pienaar joined Gojek, he brought those hard-won lessons and built Feast from scratch as an open-source project.

What makes Feast powerful is its dual-store architecture. Most databases optimize for one thing: either fast writes and complex queries (OLAP) or fast reads with simple lookups (OLTP). ML needs both. You need complex queries for training (joining features with historical labels) and fast lookups for serving (get user X's features immediately). Feast provides both through its offline and online stores.

```
FEAST ARCHITECTURE
==================

┌─────────────────────────────────────────────────────────────────────┐
│                           FEAST                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │ Feature Repo    │  │  Offline Store  │  │  Online Store   │    │
│  │                 │  │                 │  │                 │    │
│  │ • Definitions   │  │ • Historical    │  │ • Low latency   │    │
│  │ • Transformations│ │ • Batch queries │  │ • Real-time     │    │
│  │ • Metadata      │  │ • Training data │  │ • Serving       │    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
│                              │                     │               │
│                              ▼                     ▼               │
│                       ┌───────────┐         ┌───────────┐         │
│                       │ BigQuery  │         │   Redis   │         │
│                       │ Snowflake │         │ DynamoDB  │         │
│                       │ Redshift  │         │ Postgres  │         │
│                       └───────────┘         └───────────┘         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

The architecture has two key components:
- **Offline Store**: For historical data and training. Think "data warehouse for features."
- **Online Store**: For low-latency serving. Think "Redis with ML superpowers."

### Feast Feature Definitions

Feast uses Python to define features—like schemas for your ML data. This is a deliberate design choice: Python is the lingua franca of data science, so feature definitions live in Python rather than YAML or a proprietary format.

The mental model is similar to database schemas. Just as a database schema defines what columns a table has and what types they contain, a Feast feature view defines what features exist and how to compute them. The difference is that Feast adds ML-specific concepts: entities (what you're predicting about), timestamps (for point-in-time correctness), and TTL (how long features remain valid).

Let's walk through a complete example:

```python
# feature_repo/features.py
from datetime import timedelta
from feast import Entity, Feature, FeatureView, FileSource, ValueType

# Define entity (the thing we're making predictions about)
# Like a primary key in a database
user = Entity(
    name="user_id",
    value_type=ValueType.INT64,
    description="User identifier"
)

# Define data source (where features come from)
user_features_source = FileSource(
    path="data/user_features.parquet",
    event_timestamp_column="event_timestamp",
    created_timestamp_column="created_timestamp"
)

# Define feature view (collection of related features)
# Like a table in a database
user_features = FeatureView(
    name="user_features",
    entities=["user_id"],
    ttl=timedelta(days=365),  # How long features are valid
    features=[
        Feature(name="age", dtype=ValueType.INT64),
        Feature(name="total_purchases", dtype=ValueType.INT64),
        Feature(name="avg_order_value", dtype=ValueType.FLOAT),
        Feature(name="days_since_last_purchase", dtype=ValueType.INT64),
        Feature(name="favorite_category", dtype=ValueType.STRING),
    ],
    online=True,  # Available for real-time serving
    source=user_features_source
)
```

### Using Feast in Practice

With features defined, you can retrieve them for training and serving. This is where Feast really shines: the same API works for both historical data (training) and real-time data (serving), ensuring consistency.

The key concept is "point-in-time correct" feature retrieval. When training a model, you don't want to use features from the future—that would be data leakage. If you're predicting whether a user churned on January 15th, you should only use features available before January 15th. Feast handles this automatically through its `get_historical_features` API.

```python
from feast import FeatureStore
import pandas as pd

# Initialize feature store
store = FeatureStore(repo_path="feature_repo/")

# Get training data (historical features)
# "Point-in-time correct" - features as they existed at each timestamp
entity_df = pd.DataFrame({
    "user_id": [1, 2, 3, 4, 5],
    "event_timestamp": pd.to_datetime(["2024-01-01"] * 5)
})

training_df = store.get_historical_features(
    entity_df=entity_df,
    features=[
        "user_features:age",
        "user_features:total_purchases",
        "user_features:avg_order_value",
    ]
).to_df()

# Get online features (real-time serving)
# Low-latency lookup for production inference
online_features = store.get_online_features(
    features=[
        "user_features:age",
        "user_features:total_purchases",
        "user_features:avg_order_value",
    ],
    entity_rows=[{"user_id": 123}]
).to_dict()
```

### Did You Know? The Origin of Feature Stores

Feature stores emerged from **Uber's Michelangelo platform** in 2017. Uber's ML team discovered that **60% of their ML bugs came from feature engineering inconsistencies**—teams computing the same feature differently, training-serving skew, and stale features.

Their solution, Michelangelo's feature store, became the template for an industry. **Willem Pienaar**, who worked on Michelangelo, later created Feast at Gojek and donated it to the Linux Foundation AI & Data.

Today, every major cloud provider has their own feature store:
- AWS SageMaker Feature Store
- GCP Vertex AI Feature Store
- Azure Machine Learning Feature Store

The open-source Feast remains the most flexible option, supporting multiple backends and deployment patterns.

---

## 3. Data Validation with Great Expectations

### Why This Module Matters

Data validation is like quality control in manufacturing. You wouldn't ship products without inspection, so why train models on uninspected data?

The problem is that data fails silently. Your pipeline runs successfully, your model trains successfully, your deployment succeeds—and then your model makes terrible predictions because the input data was garbage.

Consider a real scenario. Your e-commerce model predicts customer churn. It's trained on customer data: age, purchase history, days since last login, etc. One day, your upstream data team changes the age calculation. Instead of computing age from birthdate, they now use a self-reported age field. This field has:
- Missing values for 20% of users (who didn't fill it out)
- Outliers like "999" (from users trying to skip the field)
- String values like "twenty-five" (from users who didn't follow instructions)

Your pipeline doesn't break. It happily converts "999" to an integer and treats "twenty-five" as missing. Your model trains on this garbage and starts making garbage predictions. Customer support tickets spike. Revenue drops. And you spend a week debugging before discovering the upstream change.

Data validation prevents this. You define what "good data" looks like upfront. Before training, you check that the data meets those expectations. If it doesn't, you fail fast—before corruption spreads downstream.

```
DATA QUALITY ISSUES
===================

Common Problems:
────────────────
• Missing values increased from 1% to 15%
• Categorical column has new unexpected values
• Numerical column has outliers (negative ages)
• Data distribution shifted (concept drift)
• Schema changed (new columns, renamed fields)

Without Validation:
───────────────────
Data pipeline runs successfully...
Model trains successfully...
Model deployed successfully...
 Model makes terrible predictions!
"Why is the model predicting -$500 orders?"

With Great Expectations:
───────────────────────
 Data validated before training
 Expectations documented
 Failed validations alert immediately
 Data quality is part of CI/CD
```

Think of Great Expectations like unit tests for your data. You define what "good data" looks like (your expectations), and the system validates every dataset against those expectations.

### Great Expectations Architecture

```
GREAT EXPECTATIONS ARCHITECTURE
===============================

┌─────────────────────────────────────────────────────────────────────┐
│                    GREAT EXPECTATIONS                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │  Expectations   │  │   Datasources   │  │   Checkpoints   │    │
│  │                 │  │                 │  │                 │    │
│  │ • Rules         │  │ • Pandas        │  │ • Validation    │    │
│  │ • Tests         │  │ • Spark         │  │   runs          │    │
│  │ • Documentation │  │ • SQL           │  │ • Actions       │    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Data Docs                                 │   │
│  │  Auto-generated HTML documentation of expectations          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Common Expectations

Great Expectations provides hundreds of built-in expectations—pre-built validation rules you can apply to your data. The name "expectations" is intentional: these are assertions about what your data should look like. Think of them as unit tests for data.

The genius of Great Expectations is its expressiveness. Instead of writing custom Python code to check "does this column exist?" you call `expect_column_to_exist("user_id")`. Instead of writing validation logic for "are all values between 0 and 100?", you call `expect_column_values_to_be_between("age", 0, 100)`. The code reads like English documentation of your data contract.

Here are the essential expectations every data scientist should know:

```python
import great_expectations as gx

# Create context and validator
context = gx.get_context()
validator = context.get_validator(...)

# Column existence - does the data have the columns we expect?
validator.expect_column_to_exist("user_id")
validator.expect_column_to_exist("age")
validator.expect_column_to_exist("email")

# Data types - are values the right type?
validator.expect_column_values_to_be_of_type("user_id", "int64")
validator.expect_column_values_to_be_of_type("age", "int64")
validator.expect_column_values_to_be_of_type("email", "str")

# Null checks - are required fields populated?
validator.expect_column_values_to_not_be_null("user_id")
validator.expect_column_values_to_not_be_null("email")

# Value ranges - are values within reasonable bounds?
validator.expect_column_values_to_be_between("age", min_value=0, max_value=120)
validator.expect_column_values_to_be_between("purchase_amount", min_value=0)

# Uniqueness - are IDs actually unique?
validator.expect_column_values_to_be_unique("user_id")
validator.expect_column_values_to_be_unique("email")

# Patterns - do strings match expected formats?
validator.expect_column_values_to_match_regex(
    "email",
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)

# Categorical values - are categories from expected set?
validator.expect_column_values_to_be_in_set(
    "country",
    ["US", "UK", "CA", "DE", "FR"]
)

# Distribution checks - has the data distribution shifted?
validator.expect_column_mean_to_be_between("age", min_value=25, max_value=45)
validator.expect_column_stdev_to_be_between("purchase_amount", min_value=10, max_value=100)

# Row count - do we have expected data volume?
validator.expect_table_row_count_to_be_between(min_value=1000, max_value=1000000)

# Column count - has the schema changed?
validator.expect_table_column_count_to_equal(15)
```

### Automated Validation in Pipelines

The real power of Great Expectations emerges when you embed it in your pipelines. Instead of manually running validation, you configure "checkpoints" that run automatically before critical operations—before training, before deployment, before any step that assumes data quality.

This is the difference between reactive and proactive data quality. Reactive means discovering bad data after it's caused problems. Proactive means catching bad data before it enters your pipeline. The latter is always cheaper.

Here's how to set up automated validation:

```python
# Create checkpoint for automated validation
checkpoint = context.add_checkpoint(
    name="user_data_checkpoint",
    validations=[
        {
            "batch_request": {
                "datasource_name": "my_datasource",
                "data_asset_name": "user_data",
            },
            "expectation_suite_name": "user_data_suite",
        }
    ]
)

# Run checkpoint (e.g., in CI/CD or before training)
results = checkpoint.run()

# Check if validation passed
if not results.success:
    print(" Data validation failed!")
    for result in results.run_results.values():
        for validation_result in result.validation_result.results:
            if not validation_result.success:
                print(f"   {validation_result.expectation_config.expectation_type}")
    raise ValueError("Cannot proceed with invalid data")
else:
    print(" Data validation passed!")
```

### Did You Know? The Great Expectations Origin

Great Expectations was created by **Abe Gong** and **James Campbell** in 2017 at Superconductive, a data reliability startup. The name comes from the Charles Dickens novel, symbolizing the "expectations" we have for our data—and the drama when those expectations are violated.

The founders had a memorable pitch:

> "We realized that data teams spent 80% of their time on data quality issues, but had zero tools to catch problems before they became disasters. It's like doing surgery without X-rays—you don't see the problem until you're already cutting."
> — Abe Gong, Great Expectations co-founder

The project now has over 8,000 GitHub stars and is used by companies like GitHub, Shopify, and Heineken. It's become the de facto standard for data validation in ML pipelines.

---

## 4. Data Lineage & Governance

### What is Data Lineage?

Data lineage tracks where data comes from and where it goes—like a family tree for your datasets. When something goes wrong, lineage lets you trace the problem back to its source.

Think of it like supply chain tracking. When a product is recalled, manufacturers can trace every component back to its source. Data lineage provides the same capability for ML: when a model fails, you can trace exactly which data, transformations, and code were involved.

Here's why lineage matters in practice. Your fraud detection model suddenly starts flagging 50% more legitimate transactions as fraudulent. Users are angry. Revenue is dropping. You need to figure out what changed.

Without lineage, you're blind. Did the model change? Did the features change? Did the training data change? Did some upstream ETL job modify the data schema? You have no way to know without manually checking dozens of systems.

With lineage, you can trace the problem systematically. You look at the model's lineage and see it was retrained yesterday. The lineage shows it used features from the `fraud_features_v3` table. You trace `fraud_features_v3` and find it depends on a transformation that was updated two days ago. You examine that transformation and find a bug—someone changed a timezone calculation that shifted all timestamps by 8 hours. Bug found in minutes, not days.

Lineage isn't just about debugging—it's about confidence. When a regulator asks "what data was used to make this decision about this customer?" you can answer precisely. When GDPR requires you to trace a user's data through your system, you have a map. When an audit asks about model decisions, you have receipts.

```
DATA LINEAGE
============

Lineage tracks where data comes from and where it goes:

┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Raw Data   │────►│ Transformed │────►│   Model     │
│  (S3)       │     │   (Spark)   │     │  Features   │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐     ┌─────────────┐
                    │  Training   │────►│   Model     │
                    │   Data      │     │  v2.3.1     │
                    └─────────────┘     └─────────────┘

Questions Lineage Answers:
─────────────────────────
• What data was used to train model v2.3.1?
• Which models will be affected if table X changes?
• Who created this feature and when?
• What transformations were applied to this data?
```

### Data Governance Best Practices

Governance is the set of policies and practices that ensure data is managed responsibly. It's like corporate governance for data—defining who can access what, how changes are tracked, and how compliance is maintained.

In traditional software, governance often means "red tape that slows us down." In ML, governance means "guardrails that prevent expensive disasters." The difference is that ML failures are often invisible, gradual, and expensive. A governance failure in traditional software usually causes an obvious crash. A governance failure in ML causes models to slowly drift into wrongness.

Effective data governance answers six key questions:

**1. Where did this data come from?** (Provenance)
Every dataset should have a birth certificate. Where was it collected? Who processed it? What transformations were applied? This matters when you discover a bug—you need to trace it back to the source.

**2. Who is allowed to access this data?** (Access Control)
Not all data should be available to all teams. PII requires special handling. Financial data has compliance requirements. Healthcare data has HIPAA restrictions. Governance defines who can see what.

**3. How is this data being used?** (Usage Tracking)
Knowing that 47 models depend on a particular table changes how carefully you modify it. Usage tracking reveals these dependencies before you accidentally break downstream consumers.

**4. How long should we keep this data?** (Retention)
Data storage isn't free. More importantly, old data creates liability. GDPR's "right to be forgotten" means you must be able to delete user data on request. Retention policies define when data should be archived or deleted.

**5. How do we handle data quality issues?** (Incident Response)
When someone discovers bad data, what happens? Who gets notified? How quickly must it be fixed? Governance defines the playbook for data incidents.

**6. How do we prove compliance?** (Audit Trail)
Regulators and auditors ask hard questions. "Show me the data that trained this model that denied this customer a loan." Without governance, you can't answer. With governance, it's a query.

```
DATA GOVERNANCE CHECKLIST
=========================

 Version Control
   • All data versioned (DVC)
   • All code versioned (Git)
   • All configs versioned

 Data Quality
   • Expectations defined (Great Expectations)
   • Automated validation in pipelines
   • Alerting on failures

 Documentation
   • Data dictionaries
   • Feature definitions
   • Schema documentation

 Access Control
   • Role-based access
   • Audit logging
   • PII handling

 Lineage
   • End-to-end tracking
   • Impact analysis
   • Reproducibility
```

---

## 5. Tool Comparison: Building Your Data Management Stack

### The MLOps Tool Explosion

If you've spent any time researching data management tools, you've likely been overwhelmed by choices. DVC, Feast, Great Expectations, MLflow, Weights & Biases, Kubeflow, Pachyderm, Delta Lake, LakeFS, dbt, Airflow, Prefect, Dagster... the list goes on.

This explosion of tools reflects the maturity of ML as a discipline. When ML was new, everyone built custom solutions. Now that patterns have emerged, tools have crystallized around common needs. But the sheer number of tools creates its own problem: analysis paralysis.

Here's the key insight: **you don't need all these tools, and you definitely don't need them all at once.** Start with the basics, add complexity when pain emerges, and always prioritize solving real problems over having a "complete" stack.

### When to Use What

Different tools solve different problems. Here's a decision matrix:

```
TOOL SELECTION MATRIX
=====================

┌────────────────────┬─────────────────────────────────────────────────┐
│     Problem        │              Solution                           │
├────────────────────┼─────────────────────────────────────────────────┤
│ Version large      │ DVC                                             │
│ datasets           │ • Git-like workflow for data                    │
│                    │ • Remote storage integration                    │
├────────────────────┼─────────────────────────────────────────────────┤
│ Share features     │ Feast / Feature Store                           │
│ across teams       │ • Centralized definitions                       │
│                    │ • Same features train & serve                   │
├────────────────────┼─────────────────────────────────────────────────┤
│ Validate data      │ Great Expectations                              │
│ quality            │ • Schema validation                             │
│                    │ • Distribution checks                           │
├────────────────────┼─────────────────────────────────────────────────┤
│ Track data         │ OpenLineage / DataHub                           │
│ lineage            │ • End-to-end tracking                           │
│                    │ • Impact analysis                               │
├────────────────────┼─────────────────────────────────────────────────┤
│ All-in-one         │ DVC + Great Expectations + Feast                │
│ data platform      │ • Full data lifecycle                           │
│                    │ • Can be overwhelming for small teams           │
└────────────────────┴─────────────────────────────────────────────────┘
```

### Complexity vs Value

Start simple and add complexity as needed:

```
TOOL COMPLEXITY VS VALUE
========================

High │                              ┌─────────────┐
     │                     ┌────────│ Full Data   │
     │              ┌──────│        │ Platform    │
     │       ┌──────│Feast │        └─────────────┘
V    │       │      │      │
A    │       │      └──────┘
L    │       │ Great
U    │       │ Expectations
E    │       └──────┘
     │ ┌──────┐
     │ │ DVC  │
     │ └──────┘
     │
Low  └─────────────────────────────────────────────────►
                     COMPLEXITY
```

**Recommendation**: Start with DVC for data versioning. Add Great Expectations when data quality issues hurt. Add Feast when multiple teams share features or training-serving skew becomes a problem.

### The 80/20 Rule of Data Management

For most teams, especially those early in their ML journey, here's the pragmatic approach:

**Start with DVC + Git.** This solves 80% of data management pain:
- You can track datasets and models
- You can reproduce experiments
- You can share data across your team
- You can roll back to previous versions

**Add Great Expectations when...** you've been burned by data quality issues:
- A model failed because of unexpected nulls
- A schema change broke your pipeline
- You spent days debugging a data drift issue

**Add Feast when...** multiple teams share features OR you're building real-time ML:
- Two teams computed the same feature differently
- Training-serving skew caused production issues
- You need sub-second feature lookups for inference

**Add a full data platform when...** you have 50+ data scientists and need enterprise features:
- Multiple teams need self-service access to features
- Compliance requirements mandate comprehensive lineage
- Cost of data quality issues justifies the investment

Don't let tool FOMO drive your decisions. Every tool you add is a tool you need to maintain, monitor, and train people on. Start simple and add complexity only when it solves real problems.

---

##  Hands-On Exercises

### Exercise 1: Set Up DVC

```bash
# Initialize
pip install dvc dvc-s3
git init
dvc init

# Add data
dvc add data/train.csv
git add data/train.csv.dvc
git commit -m "Add training data"

# Set up remote
dvc remote add -d myremote s3://bucket/path
dvc push
```

### Exercise 2: Create a DVC Pipeline

```yaml
# dvc.yaml
stages:
  preprocess:
    cmd: python src/preprocess.py
    deps:
      - src/preprocess.py
      - data/raw/
    outs:
      - data/processed/
```

### Exercise 3: Define Feast Features

```python
from feast import Entity, Feature, FeatureView, ValueType

# Define entity
user = Entity(name="user_id", value_type=ValueType.INT64)

# Define feature view
# ... complete the implementation
```

### Exercise 4: Create Great Expectations Suite

```python
import great_expectations as gx

context = gx.get_context()
suite = context.add_expectation_suite("my_suite")

# Add at least 10 expectations covering:
# - Column existence
# - Data types
# - Value ranges
# - Null checks
# - Distribution properties
```

---

## Key Takeaways

If you remember nothing else from this module, remember these eight principles that separate professional ML from hobbyist ML:

1. **Data versioning is non-negotiable.** DVC gives you Git-like control over datasets. Every model should be traceable to the exact data it was trained on.

2. **Feature stores prevent training-serving skew.** When the same code computes features for training and serving, a whole class of bugs disappears.

3. **Data validation catches problems early.** Great Expectations acts like unit tests for data—catching quality issues before they corrupt your models.

4. **Lineage enables debugging.** When a model fails in production, lineage lets you trace back to the root cause—whether it's bad data, broken code, or shifted distributions.

5. **Start simple, add complexity as needed.** DVC alone solves 80% of data management pain. Add Feast and Great Expectations when their specific problems become acute.

6. **Data quality > model complexity.** Andrew Ng's Data-Centric AI movement has it right: a simple model on good data beats a complex model on messy data.

7. **Reproducibility requires versioning everything.** Data, code, configs, parameters—if it affects your results, it needs to be versioned.

8. **Automation is key.** Manual data validation doesn't scale. Embed Great Expectations checkpoints into your CI/CD pipelines.

The journey from "data chaos" to "data maturity" doesn't happen overnight. It's an iterative process of identifying pain points, implementing solutions, and building habits. The tools in this module—DVC, Feast, Great Expectations—are battle-tested solutions to problems that have cost real companies real money.

Start with DVC. When that's second nature, add Great Expectations. When feature consistency becomes a problem, consider Feast. Each tool earns its place by solving a real problem you've experienced. That's the path to a data infrastructure you can trust.

---

##  Further Reading

### Documentation
- [DVC Documentation](https://dvc.org/doc)
- [Feast Documentation](https://docs.feast.dev/)
- [Great Expectations](https://docs.greatexpectations.io/)

### Papers & Articles
- "Hidden Technical Debt in Machine Learning Systems" (Google, 2015)
- "Data Management Challenges in Production ML" (Polyzotis et al., 2018)
- "Feast: Feature Store for Machine Learning" (Gojek, 2020)

---

## Interview Preparation

**Q: Why can't you just use Git for machine learning data?**

Git stores complete file copies for every version. A 10GB dataset with 100 versions would need 1TB of storage. Git also has no concept of cloud storage backends or large file handling. DVC solves this by storing pointers in Git while keeping actual data in S3, GCS, or Azure Blob Storage. It's designed from the ground up for large binary files common in ML.

**Q: How would you handle training-serving skew in production?**

Training-serving skew occurs when features computed during training differ from production. The solution is a feature store like Feast that provides a single source of truth. Features are computed once, stored centrally, and served consistently to both training pipelines and online serving. This eliminates the "recompute features differently" anti-pattern.

**Q: What's your approach to data validation in ML pipelines?**

Use Great Expectations to define explicit contracts about your data. Run validation at every pipeline stage: after ingestion, after transformation, and before model training. Critical validations include: no null values in required columns, values within expected ranges, distributions matching historical data, and schema matching expectations. Integrate these as gates in CI/CD — failing validation stops the pipeline.

---

##  Knowledge Check

1. **What problem does DVC solve that Git doesn't?**

2. **What is training-serving skew and how do feature stores prevent it?**

3. **Name 5 common Great Expectations validators.**

4. **When would you choose Feast over just using DVC?**

5. **What is data lineage and why is it important?**

---

## ⏭️ Next Steps

You now understand data versioning and feature stores! These are critical for reproducible ML.

**Up Next**: Module 50 - ML Pipeline & Workflow Orchestration

---

_Module 49 Complete! You now understand DVC, Feast, and Great Expectations!_
_"Bad data = bad models. Version your data like you version your code."_
_Remember Jennifer Chen's $50 million bug—don't let it happen to you._
