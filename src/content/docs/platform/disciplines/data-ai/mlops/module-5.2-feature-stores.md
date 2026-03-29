---
title: "Module 5.2: Feature Engineering & Stores"
slug: platform/disciplines/data-ai/mlops/module-5.2-feature-stores
sidebar:
  order: 3
---
> **Discipline Track** | Complexity: `[COMPLEX]` | Time: 40-45 min

## Prerequisites

Before starting this module:
- [Module 5.1: MLOps Fundamentals](../module-5.1-mlops-fundamentals/)
- Basic understanding of data transformations
- Familiarity with pandas DataFrames
- Understanding of training vs. inference

## Why This Module Matters

The number one cause of ML production failures isn't bad models—it's **training/serving skew**. Your model trains on features computed one way, then serves predictions using features computed differently. Same feature name, different values, wrong predictions.

Feature stores solve this by providing a single source of truth for features. Compute once, use everywhere. Netflix, Uber, and Airbnb all built feature stores after learning this lesson the hard way.

If you're doing ML at scale without a feature store, you're building technical debt.

## Did You Know?

- **Uber built Michelangelo** (their ML platform) primarily to solve the feature consistency problem—they found 30% of ML debugging time was spent on feature issues
- **Feature computation often takes 80% of ML pipeline time**—yet gets 20% of the attention. Feature stores flip this ratio by making feature engineering reusable
- **The term "feature store" was coined by Uber in 2017**, but the concept existed earlier as "feature engineering platforms" at Google and Facebook
- **Point-in-time correctness** (avoiding data leakage) is the hardest feature store problem to solve—get it wrong and your backtesting lies to you

## What is a Feature Store?

A feature store is a centralized repository for storing, sharing, and serving ML features. Think of it as a "data warehouse for ML features."

```
┌─────────────────────────────────────────────────────────────────┐
│                 WITHOUT FEATURE STORE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TRAINING PIPELINE           SERVING PIPELINE                    │
│  ┌──────────────────┐        ┌──────────────────┐               │
│  │ SQL Query A      │        │ SQL Query B      │ ← Different!  │
│  │ (batch, complex) │        │ (realtime, fast) │               │
│  └────────┬─────────┘        └────────┬─────────┘               │
│           │                           │                          │
│  ┌────────▼─────────┐        ┌────────▼─────────┐               │
│  │ Python Transform │        │ Java Transform   │ ← Different!  │
│  │ (pandas)         │        │ (custom code)    │               │
│  └────────┬─────────┘        └────────┬─────────┘               │
│           │                           │                          │
│           ▼                           ▼                          │
│      Training Data              Serving Data                     │
│      (features: X)              (features: X') ← SKEW!          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                  WITH FEATURE STORE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                    ┌──────────────────┐                         │
│                    │  FEATURE STORE   │                         │
│                    │  ┌────────────┐  │                         │
│                    │  │ Feature    │  │                         │
│                    │  │ Definition │  │ ← Single source of truth│
│                    │  └──────┬─────┘  │                         │
│                    │         │        │                         │
│           ┌────────┴─────────┴────────┴─────────┐               │
│           │                                      │               │
│  ┌────────▼─────────┐                ┌──────────▼───────┐       │
│  │  OFFLINE STORE   │                │  ONLINE STORE    │       │
│  │  (training)      │                │  (serving)       │       │
│  │  - Data Lake     │                │  - Redis/DynamoDB│       │
│  │  - Batch queries │                │  - Low latency   │       │
│  └────────┬─────────┘                └──────────┬───────┘       │
│           │                                      │               │
│           ▼                                      ▼               │
│      Training Data                         Serving Data          │
│      (features: X)                         (features: X) ← SAME! │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### The Training/Serving Skew Problem

```python
# TRAINING: pandas on full dataset
df['avg_purchase_30d'] = df.groupby('user_id')['amount'].transform(
    lambda x: x.rolling(30).mean()
)

# SERVING: custom SQL for single user
SELECT AVG(amount)
FROM purchases
WHERE user_id = ?
  AND date > NOW() - INTERVAL 30 DAY  # Bug: different window!
```

Small differences cause big problems:
- Different date ranges
- NULL handling differences
- Timezone mismatches
- Rounding errors

### War Story: The $10M Feature Bug

A financial services company deployed a credit risk model. The training pipeline computed "average balance over 90 days" correctly. The serving pipeline had a bug—it computed 30-day average instead.

The model underestimated risk. They approved loans they shouldn't have. Six months later: $10M in defaults traced to one feature computation bug.

A feature store would have prevented this entirely.

## Feature Store Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                   FEATURE STORE ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    FEATURE REGISTRY                         │ │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐             │ │
│  │  │ user_      │ │ product_   │ │ transaction│             │ │
│  │  │ features   │ │ features   │ │ _features  │             │ │
│  │  │ ─────────  │ │ ─────────  │ │ ──────────│             │ │
│  │  │ age        │ │ price      │ │ amount     │             │ │
│  │  │ tenure     │ │ category   │ │ is_fraud   │             │ │
│  │  │ avg_spend  │ │ popularity │ │ hour_of_day│             │ │
│  │  └────────────┘ └────────────┘ └────────────┘             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│              ┌───────────────┴───────────────┐                  │
│              │                               │                   │
│  ┌───────────▼───────────┐     ┌────────────▼────────────┐     │
│  │     OFFLINE STORE     │     │      ONLINE STORE       │     │
│  │   ┌───────────────┐   │     │   ┌───────────────┐    │     │
│  │   │  Data Lake    │   │     │   │ Redis/DynamoDB│    │     │
│  │   │  (Parquet)    │   │     │   │ (Key-Value)   │    │     │
│  │   └───────────────┘   │     │   └───────────────┘    │     │
│  │                       │     │                         │     │
│  │  • Historical data    │     │  • Latest values only  │     │
│  │  • Point-in-time      │     │  • Millisecond latency │     │
│  │  • Training datasets  │     │  • Online inference    │     │
│  └───────────────────────┘     └─────────────────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Offline vs. Online Stores

| Aspect | Offline Store | Online Store |
|--------|---------------|--------------|
| **Purpose** | Training data | Real-time inference |
| **Latency** | Seconds to minutes | Milliseconds |
| **Data** | Full history | Latest values |
| **Storage** | Data lake (S3, GCS) | Key-value (Redis, DynamoDB) |
| **Query** | Batch, point-in-time | Key lookup |
| **Cost** | Storage optimized | Compute optimized |

## Feature Engineering Best Practices

### Feature Types

```
FEATURE CATEGORIES
─────────────────────────────────────────────────────────────────

IDENTITY FEATURES (Entity attributes)
├── user_id, product_id
├── Static or slowly changing
└── Usually joined, not computed

NUMERICAL FEATURES (Quantitative)
├── Raw: age, price, quantity
├── Transformed: log(price), sqrt(amount)
└── Normalized: z-score, min-max scaling

CATEGORICAL FEATURES (Qualitative)
├── One-hot: category_electronics, category_books
├── Ordinal: size_small=1, size_medium=2, size_large=3
└── Embeddings: learned representations

TEMPORAL FEATURES (Time-based)
├── Extracted: hour, day_of_week, month
├── Cyclical: sin(hour), cos(hour)
└── Lagged: value_yesterday, value_last_week

AGGREGATE FEATURES (Windowed computations)
├── Rolling: avg_purchases_7d, max_amount_30d
├── Cumulative: total_lifetime_purchases
└── Relative: purchases_vs_avg_user
```

### Transformation Code

```python
# Good feature engineering patterns
import pandas as pd
import numpy as np

def create_user_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create user-level features."""
    features = pd.DataFrame()
    features['user_id'] = df['user_id']

    # Numerical: log transform for skewed data
    features['log_total_spend'] = np.log1p(df['total_spend'])

    # Temporal: cyclical encoding for hour
    features['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
    features['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)

    # Aggregate: rolling windows
    features['avg_purchase_7d'] = df.groupby('user_id')['amount'].transform(
        lambda x: x.rolling(7, min_periods=1).mean()
    )

    # Ratio features (often powerful)
    features['purchase_frequency'] = df['num_purchases'] / df['days_active']

    return features
```

## Point-in-Time Correctness

The most critical feature store capability is **point-in-time correctness**—ensuring you only use data that was available at prediction time.

```
POINT-IN-TIME JOIN (Correct)
─────────────────────────────────────────────────────────────────

Training Example: Predict if user will purchase on 2024-01-15

Timeline:
Jan 1    Jan 5    Jan 10   Jan 15   Jan 20
  │        │        │        │        │
  ▼        ▼        ▼        ▼        ▼
Purchase Purchase Purchase  PREDICT  Purchase
  $50      $30      $100      │        $80
                              │
                              └── At prediction time, we knew:
                                  - 3 purchases
                                  - $180 total
                                  - $60 average

                                  NOT $260 total (includes future!)


WITHOUT POINT-IN-TIME (Data Leakage)
─────────────────────────────────────────────────────────────────

If you compute features using ALL data:
- avg_purchase = $65 (includes Jan 20!)
- This is FUTURE INFORMATION
- Model learns from data it won't have in production
- Backtests look amazing, production fails
```

### Implementing Point-in-Time Joins

```python
# Feast handles this automatically
from feast import FeatureStore

store = FeatureStore(repo_path=".")

# Entity DataFrame with timestamps
entity_df = pd.DataFrame({
    "user_id": [1, 2, 3],
    "event_timestamp": [
        datetime(2024, 1, 15),  # Use features available on Jan 15
        datetime(2024, 1, 16),
        datetime(2024, 1, 17),
    ]
})

# Get features as of each timestamp
training_df = store.get_historical_features(
    entity_df=entity_df,
    features=[
        "user_features:avg_purchase_7d",
        "user_features:total_purchases",
    ],
).to_df()
```

## Feature Store Tools

### Feast (Open Source)

```
┌─────────────────────────────────────────────────────────────────┐
│                         FEAST                                    │
│              "Feature Store for Machine Learning"                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PROS                          CONS                              │
│  ├── Open source, free         ├── Less polished UI              │
│  ├── Cloud agnostic            ├── Smaller community             │
│  ├── Kubernetes native         ├── Limited streaming             │
│  ├── Point-in-time joins       └── Manual schema management      │
│  └── Growing ecosystem                                           │
│                                                                  │
│  BEST FOR: Teams wanting control, K8s environments               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Feature Store Comparison

| Feature Store | Type | Strengths | Best For |
|--------------|------|-----------|----------|
| **Feast** | Open source | Flexible, K8s native | Self-hosted, multi-cloud |
| **Tecton** | Commercial | Streaming, enterprise | Real-time ML at scale |
| **Hopsworks** | Open core | ML platform integration | End-to-end ML |
| **Databricks** | Commercial | Spark integration | Databricks users |
| **SageMaker** | AWS | AWS integration | AWS-native teams |
| **Vertex AI** | GCP | GCP integration | GCP-native teams |

## Feast Deep Dive

### Project Structure

```
feast-project/
├── feature_repo/
│   ├── feature_store.yaml    # Configuration
│   ├── entities.py           # Entity definitions
│   ├── features.py           # Feature views
│   └── data_sources.py       # Data source definitions
├── data/
│   └── user_features.parquet
└── requirements.txt
```

### Configuration

```yaml
# feature_store.yaml
project: my_project
registry: data/registry.db
provider: local
online_store:
  type: sqlite
  path: data/online_store.db
offline_store:
  type: file
entity_key_serialization_version: 2
```

### Defining Features

```python
# entities.py
from feast import Entity

user = Entity(
    name="user_id",
    description="Unique user identifier",
)

product = Entity(
    name="product_id",
    description="Unique product identifier",
)
```

```python
# data_sources.py
from feast import FileSource

user_stats_source = FileSource(
    name="user_stats",
    path="data/user_stats.parquet",
    timestamp_field="event_timestamp",
)
```

```python
# features.py
from feast import FeatureView, Field
from feast.types import Float32, Int64
from datetime import timedelta

from entities import user
from data_sources import user_stats_source

user_features = FeatureView(
    name="user_features",
    entities=[user],
    ttl=timedelta(days=1),
    schema=[
        Field(name="total_purchases", dtype=Int64),
        Field(name="avg_purchase_amount", dtype=Float32),
        Field(name="days_since_last_purchase", dtype=Int64),
    ],
    source=user_stats_source,
)
```

### Using Feast

```python
from feast import FeatureStore
import pandas as pd
from datetime import datetime

# Initialize
store = FeatureStore(repo_path="feature_repo/")

# Apply feature definitions
# Run: feast apply

# Materialize features to online store
# Run: feast materialize 2024-01-01 2024-01-31

# Get training data (offline)
entity_df = pd.DataFrame({
    "user_id": [1, 2, 3],
    "event_timestamp": [datetime.now()] * 3,
})

training_df = store.get_historical_features(
    entity_df=entity_df,
    features=["user_features:total_purchases", "user_features:avg_purchase_amount"],
).to_df()

# Get online features (serving)
online_features = store.get_online_features(
    features=["user_features:total_purchases", "user_features:avg_purchase_amount"],
    entity_rows=[{"user_id": 1}],
).to_dict()

print(online_features)
# {'user_id': [1], 'total_purchases': [42], 'avg_purchase_amount': [29.99]}
```

## Feature Engineering Patterns

### Pattern 1: Lag Features

```python
# For time series: what happened N periods ago
def create_lag_features(df, column, lags=[1, 7, 30]):
    for lag in lags:
        df[f'{column}_lag_{lag}d'] = df.groupby('user_id')[column].shift(lag)
    return df

# Result: value_lag_1d, value_lag_7d, value_lag_30d
```

### Pattern 2: Rolling Aggregates

```python
# Windowed statistics
def create_rolling_features(df, column, windows=[7, 30, 90]):
    for window in windows:
        df[f'{column}_mean_{window}d'] = df.groupby('user_id')[column].transform(
            lambda x: x.rolling(window, min_periods=1).mean()
        )
        df[f'{column}_std_{window}d'] = df.groupby('user_id')[column].transform(
            lambda x: x.rolling(window, min_periods=1).std()
        )
    return df
```

### Pattern 3: Ratio Features

```python
# Comparative features
def create_ratio_features(df):
    # User vs. average user
    global_avg = df['purchase_amount'].mean()
    df['purchase_vs_avg'] = df['purchase_amount'] / global_avg

    # Recent vs. historical
    df['recent_vs_historical'] = df['avg_7d'] / df['avg_90d']

    return df
```

### Pattern 4: Interaction Features

```python
# Combine features for non-linear relationships
def create_interaction_features(df):
    df['price_x_quantity'] = df['price'] * df['quantity']
    df['age_x_tenure'] = df['user_age'] * df['account_tenure']
    return df
```

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No point-in-time joins | Data leakage, false confidence | Use feature store with timestamps |
| Feature computed twice | Training/serving skew | Single definition, feature store |
| Missing feature versioning | Can't reproduce models | Version features with models |
| Too many features | Overfitting, slow inference | Feature selection, importance analysis |
| No feature documentation | Team can't understand/reuse | Document every feature |
| Ignoring feature freshness | Stale predictions | TTL and monitoring |

## Quiz

Test your understanding:

<details>
<summary>1. What is training/serving skew and why is it dangerous?</summary>

**Answer**: Training/serving skew occurs when features are computed differently during training vs. inference. Even small differences (date ranges, NULL handling, timezone) cause the model to receive different inputs than it was trained on, leading to degraded predictions. It's dangerous because:
1. Silent failure—no errors, just wrong predictions
2. Hard to debug—model "works" but performs poorly
3. Can be very subtle—off-by-one errors, timezone issues
</details>

<details>
<summary>2. Why do feature stores have both offline and online stores?</summary>

**Answer**: Different use cases require different tradeoffs:
- **Offline store**: For training. Needs full history, point-in-time queries, can tolerate latency. Optimized for storage cost and batch queries (data lake).
- **Online store**: For serving. Needs low latency (milliseconds), only latest values. Optimized for fast lookups (Redis, DynamoDB).

Both stores are populated from the same feature definitions, ensuring consistency.
</details>

<details>
<summary>3. What is point-in-time correctness and what happens without it?</summary>

**Answer**: Point-in-time correctness ensures training data only includes features that were available at prediction time. Without it:
- **Data leakage**: Future information leaks into training
- **Overly optimistic backtests**: Model appears better than it is
- **Production failure**: Model underperforms because it doesn't have "future" data in production

Example: Training a purchase prediction model with user's "total lifetime purchases" that includes purchases AFTER the prediction date.
</details>

<details>
<summary>4. When should you NOT use a feature store?</summary>

**Answer**: Feature stores add complexity. Skip them when:
- **Simple models**: Few features, single model
- **No serving component**: Analytics/reporting only
- **Small team**: Overhead exceeds benefit
- **Early exploration**: Still validating ML value

Consider a feature store when:
- Multiple models share features
- Training/serving skew is causing issues
- Feature computation is slow/expensive
- Team is growing and needs collaboration
</details>

## Hands-On Exercise: Build a Feature Store

Let's build a complete feature store with Feast:

### Setup

```bash
# Create project directory
mkdir feast-demo && cd feast-demo

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install Feast
pip install feast pandas pyarrow
```

### Step 1: Initialize Feast Project

```bash
feast init feature_repo
cd feature_repo
```

### Step 2: Create Sample Data

```python
# create_data.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Generate user feature data
np.random.seed(42)
n_users = 100
n_days = 30

data = []
for user_id in range(1, n_users + 1):
    for day in range(n_days):
        timestamp = datetime(2024, 1, 1) + timedelta(days=day)
        data.append({
            "user_id": user_id,
            "event_timestamp": timestamp,
            "total_purchases": np.random.randint(0, 100),
            "avg_purchase_amount": round(np.random.uniform(10, 200), 2),
            "days_since_last_purchase": np.random.randint(0, 30),
        })

df = pd.DataFrame(data)
df.to_parquet("data/user_features.parquet")
print(f"Created {len(df)} records")
print(df.head())
```

```bash
mkdir -p data
python create_data.py
```

### Step 3: Define Features

```python
# feature_repo/features.py
from datetime import timedelta
from feast import Entity, FeatureView, Field, FileSource
from feast.types import Float32, Int64

# Entity
user = Entity(
    name="user_id",
    join_keys=["user_id"],
    description="User identifier",
)

# Data source
user_features_source = FileSource(
    name="user_features_source",
    path="data/user_features.parquet",
    timestamp_field="event_timestamp",
)

# Feature view
user_features = FeatureView(
    name="user_features",
    entities=[user],
    ttl=timedelta(days=1),
    schema=[
        Field(name="total_purchases", dtype=Int64),
        Field(name="avg_purchase_amount", dtype=Float32),
        Field(name="days_since_last_purchase", dtype=Int64),
    ],
    source=user_features_source,
    online=True,
)
```

### Step 4: Apply and Materialize

```bash
# Apply feature definitions
feast apply

# Materialize to online store
feast materialize 2024-01-01 2024-02-01
```

### Step 5: Use Features

```python
# use_features.py
from feast import FeatureStore
import pandas as pd
from datetime import datetime

store = FeatureStore(repo_path=".")

# Training: Get historical features
entity_df = pd.DataFrame({
    "user_id": [1, 2, 3, 4, 5],
    "event_timestamp": [datetime(2024, 1, 15)] * 5,  # Point-in-time
})

training_df = store.get_historical_features(
    entity_df=entity_df,
    features=[
        "user_features:total_purchases",
        "user_features:avg_purchase_amount",
        "user_features:days_since_last_purchase",
    ],
).to_df()

print("Training data (point-in-time as of Jan 15):")
print(training_df)

# Serving: Get online features
online_features = store.get_online_features(
    features=[
        "user_features:total_purchases",
        "user_features:avg_purchase_amount",
    ],
    entity_rows=[
        {"user_id": 1},
        {"user_id": 2},
    ],
).to_dict()

print("\nOnline features (latest):")
for key, values in online_features.items():
    print(f"  {key}: {values}")
```

### Success Criteria

You've completed this exercise when you can:
- [ ] Create sample feature data
- [ ] Define entities and feature views in Feast
- [ ] Apply feature definitions
- [ ] Materialize features to online store
- [ ] Retrieve historical features for training (point-in-time)
- [ ] Retrieve online features for serving (latest values)

## Key Takeaways

1. **Feature stores solve training/serving skew**: Single source of truth for features
2. **Offline and online stores serve different needs**: Training vs. real-time inference
3. **Point-in-time correctness prevents data leakage**: Only use data available at prediction time
4. **Feature engineering is reusable**: Compute once, use across models
5. **Start simple**: Feast provides core functionality without vendor lock-in

## Further Reading

- [Feast Documentation](https://docs.feast.dev/) — Open source feature store
- [Feature Store for ML](https://www.featurestore.org/) — Community resources
- [Uber Michelangelo](https://eng.uber.com/michelangelo-machine-learning-platform/) — Uber's ML platform
- [Building Feature Stores](https://www.tecton.ai/blog/) — Tecton's blog

## Summary

Feature stores are the backbone of production ML. They ensure consistency between training and serving, prevent data leakage through point-in-time correctness, and enable feature reuse across teams. While they add complexity, the alternative—debugging training/serving skew in production—is far more expensive.

---

## Next Module

Continue to [Module 5.3: Model Training & Experimentation](../module-5.3-model-training/) to learn how to build reproducible training pipelines with experiment tracking.
