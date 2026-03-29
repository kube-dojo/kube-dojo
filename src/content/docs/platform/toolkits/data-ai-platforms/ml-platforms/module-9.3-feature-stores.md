---
title: "Module 9.3: Feature Stores"
slug: platform/toolkits/data-ai-platforms/ml-platforms/module-9.3-feature-stores
sidebar:
  order: 4
---
> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: 40-45 minutes

## Overview

Feature stores solve the most frustrating problem in ML: feature reuse. Data scientists spend 80% of their time on feature engineering, then those features sit in notebooks, unused by others. Feature stores centralize features, ensure training-serving consistency, and make features discoverable. This module covers Feast, the leading open-source feature store, on Kubernetes.

**What You'll Learn**:
- Feature store concepts and architecture
- Feast installation and configuration
- Defining and managing features
- Online vs offline serving
- Integration with ML pipelines

**Prerequisites**:
- Basic ML concepts
- Python familiarity
- Kubernetes fundamentals
- [MLOps Discipline](../../../disciplines/data-ai/mlops/) recommended

---

## Why This Module Matters

Every ML team eventually builds the same features. User click counts, transaction aggregates, text embeddings—they're reinvented in every project. Without a feature store, you have notebooks full of feature logic that nobody can find. Feature stores make features first-class citizens: versioned, documented, and shared across the organization.

> 💡 **Did You Know?** Uber built Michelangelo (their ML platform) in 2017 and discovered that 60% of engineer time was spent on features. They created a feature store, and that 60% dropped to 15%. Other companies noticed: Airbnb built Zipline, LinkedIn built Feathr, and the pattern became a standard. Feast emerged as the open-source solution that anyone could use.

---

## Feature Store Architecture

```
FEATURE STORE ARCHITECTURE
════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│                      FEAST ARCHITECTURE                          │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Feature    │    │    Feast     │    │   Feature    │      │
│  │ Definitions  │───▶│   Registry   │◀───│   Views      │      │
│  │   (Python)   │    │  (Storage)   │    │   (Queries)  │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                              │                                   │
│         ┌────────────────────┼────────────────────┐             │
│         │                    │                    │             │
│         ▼                    ▼                    ▼             │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐     │
│  │   Offline   │      │   Online    │      │   Feature   │     │
│  │    Store    │      │    Store    │      │   Server    │     │
│  │  (BigQuery, │      │  (Redis,    │      │   (gRPC)    │     │
│  │   Parquet)  │      │   DynamoDB) │      │             │     │
│  └─────────────┘      └─────────────┘      └─────────────┘     │
│         │                    │                    │             │
│         │                    │                    │             │
│         ▼                    ▼                    ▼             │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐     │
│  │  Training   │      │  Real-time  │      │  Batch      │     │
│  │   (Batch)   │      │  Inference  │      │  Inference  │     │
│  └─────────────┘      └─────────────┘      └─────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

DATA FLOW:
─────────────────────────────────────────────────────────────────

Raw Data                 Feature Store                  ML Model
    │                         │                            │
    │  Transform              │                            │
    │ ──────────────▶ Offline Store                       │
    │                         │                            │
    │                         │ Materialize                │
    │                         │ ──────────────▶ Online Store
    │                         │                            │
    │                         │                   ◀────────│
    │                         │                 Get Features
    │                         │                            │
```

### Key Concepts

| Concept | Description | Example |
|---------|-------------|---------|
| **Feature** | Single computed value | `user_total_orders` |
| **Feature View** | Group of related features | `user_features` (orders, spend, tenure) |
| **Entity** | What features describe | `user_id`, `product_id` |
| **Data Source** | Where raw data comes from | BigQuery, Parquet, Kafka |
| **Offline Store** | Historical features for training | Data warehouse |
| **Online Store** | Latest features for inference | Redis, DynamoDB |

> 💡 **Did You Know?** The training-serving skew problem was so common that it got its own name. Models trained on batch-computed features would fail in production where features were computed differently. Feature stores guarantee that the exact same feature computation runs in both places—solving a problem that caused countless production incidents.

---

## Feast Installation

### Local Development

```bash
# Install Feast
pip install feast

# Create new project
feast init my_feature_repo
cd my_feature_repo

# Project structure:
# my_feature_repo/
# ├── feature_repo/
# │   ├── __init__.py
# │   ├── example_repo.py    # Feature definitions
# │   └── feature_store.yaml # Configuration
# └── data/
#     └── driver_stats.parquet
```

### Kubernetes Deployment

```yaml
# feast-feature-server.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: feast-feature-server
  namespace: feast
spec:
  replicas: 3
  selector:
    matchLabels:
      app: feast-server
  template:
    metadata:
      labels:
        app: feast-server
    spec:
      containers:
      - name: feast
        image: feastdev/feature-server:0.35.0
        command:
        - feast
        - serve
        - --host=0.0.0.0
        - --port=6566
        ports:
        - containerPort: 6566
        env:
        - name: FEAST_REGISTRY
          value: "s3://feast-bucket/registry.pb"
        - name: FEAST_ONLINE_STORE_TYPE
          value: "redis"
        - name: FEAST_REDIS_HOST
          value: "redis.feast:6379"
        volumeMounts:
        - name: feast-config
          mountPath: /app/feature_repo
      volumes:
      - name: feast-config
        configMap:
          name: feast-config
---
apiVersion: v1
kind: Service
metadata:
  name: feast-server
  namespace: feast
spec:
  selector:
    app: feast-server
  ports:
  - port: 6566
    targetPort: 6566
```

### Redis Online Store

```yaml
# redis.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: feast
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: 256Mi
          limits:
            memory: 1Gi
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: feast
spec:
  selector:
    app: redis
  ports:
  - port: 6379
```

---

## Defining Features

### Feature Store Configuration

```yaml
# feature_store.yaml
project: my_project
registry: s3://feast-bucket/registry.pb
provider: aws

online_store:
  type: redis
  connection_string: redis.feast:6379

offline_store:
  type: file  # or bigquery, redshift, snowflake

entity_key_serialization_version: 2
```

### Feature Definitions

```python
# features.py
from datetime import timedelta
from feast import Entity, Feature, FeatureView, FileSource, Field
from feast.types import Float32, Int64, String

# Define entities (what features describe)
user = Entity(
    name="user_id",
    description="Unique user identifier",
    join_keys=["user_id"]
)

# Define data source
user_stats_source = FileSource(
    name="user_stats",
    path="s3://data-lake/user_stats.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created_timestamp"
)

# Define feature view
user_features = FeatureView(
    name="user_features",
    entities=[user],
    ttl=timedelta(days=1),  # How long features are valid
    schema=[
        Field(name="total_orders", dtype=Int64),
        Field(name="total_spend", dtype=Float32),
        Field(name="avg_order_value", dtype=Float32),
        Field(name="days_since_last_order", dtype=Int64),
        Field(name="favorite_category", dtype=String),
    ],
    source=user_stats_source,
    online=True,  # Materialize to online store
    tags={"team": "growth", "version": "v1"},
)

# Streaming source example
from feast import KafkaSource

user_activity_source = KafkaSource(
    name="user_activity_stream",
    kafka_bootstrap_servers="kafka.default:9092",
    topic="user-activity",
    timestamp_field="event_timestamp",
    message_format=AvroFormat(schema_json=AVRO_SCHEMA),
)

realtime_user_features = FeatureView(
    name="realtime_user_features",
    entities=[user],
    ttl=timedelta(minutes=5),  # Short TTL for real-time
    schema=[
        Field(name="clicks_last_5min", dtype=Int64),
        Field(name="session_duration", dtype=Float32),
    ],
    source=user_activity_source,
    online=True,
)
```

### Feature Services

```python
# feature_services.py
from feast import FeatureService

# Group features for a specific use case
recommendation_features = FeatureService(
    name="recommendation_features",
    features=[
        user_features[["total_orders", "favorite_category"]],
        realtime_user_features[["clicks_last_5min"]],
    ],
    tags={"model": "recommendation-v2"},
)

fraud_detection_features = FeatureService(
    name="fraud_detection_features",
    features=[
        user_features[["total_spend", "days_since_last_order"]],
        transaction_features,  # Another feature view
    ],
)
```

> 💡 **Did You Know?** Feature Services solved the "which features does my model need?" problem. Before Feature Services, data scientists had to remember which features went with which model. Now they define it once: "This model needs these features." Anyone deploying the model just references the Feature Service, and Feast handles the rest.

---

## Materializing and Serving Features

### Apply Feature Definitions

```bash
# Register features with Feast
feast apply

# Output:
# Created entity user_id
# Created feature view user_features
# Created feature service recommendation_features
```

### Materialize to Online Store

```bash
# Materialize historical data to online store
feast materialize-incremental $(date +%Y-%m-%dT%H:%M:%S)

# Or with specific date range
feast materialize 2024-01-01T00:00:00 2024-01-15T00:00:00

# Scheduled materialization (cron job)
apiVersion: batch/v1
kind: CronJob
metadata:
  name: feast-materialize
  namespace: feast
spec:
  schedule: "0 * * * *"  # Every hour
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: feast
            image: feastdev/feature-server:0.35.0
            command:
            - feast
            - materialize-incremental
            - $(date -Iseconds)
          restartPolicy: OnFailure
```

### Getting Features for Training

```python
from feast import FeatureStore
import pandas as pd

store = FeatureStore(repo_path=".")

# Entity DataFrame (what you want features for)
entity_df = pd.DataFrame({
    "user_id": [1, 2, 3, 4, 5],
    "event_timestamp": pd.to_datetime([
        "2024-01-15 10:00:00",
        "2024-01-15 11:00:00",
        "2024-01-15 12:00:00",
        "2024-01-15 13:00:00",
        "2024-01-15 14:00:00",
    ])
})

# Get historical features (point-in-time correct)
training_df = store.get_historical_features(
    entity_df=entity_df,
    features=[
        "user_features:total_orders",
        "user_features:total_spend",
        "user_features:favorite_category",
    ],
).to_df()

print(training_df)
# user_id | event_timestamp | total_orders | total_spend | favorite_category
# 1       | 2024-01-15 10:00| 42           | 1250.00     | electronics
# ...
```

### Getting Features for Inference

```python
from feast import FeatureStore

store = FeatureStore(repo_path=".")

# Get online features (latest values)
feature_vector = store.get_online_features(
    features=[
        "user_features:total_orders",
        "user_features:total_spend",
        "realtime_user_features:clicks_last_5min",
    ],
    entity_rows=[
        {"user_id": 123},
        {"user_id": 456},
    ],
).to_dict()

print(feature_vector)
# {
#     "user_id": [123, 456],
#     "total_orders": [42, 15],
#     "total_spend": [1250.00, 450.00],
#     "clicks_last_5min": [7, 2],
# }
```

### gRPC Feature Server

```python
# Using gRPC for low-latency inference
from feast import FeatureStore
from feast.protos.feast.serving.ServingService_pb2 import GetOnlineFeaturesRequest
from feast.protos.feast.serving.ServingService_pb2_grpc import ServingServiceStub
import grpc

channel = grpc.insecure_channel("feast-server.feast:6566")
stub = ServingServiceStub(channel)

request = GetOnlineFeaturesRequest(
    feature_service="recommendation_features",
    entities={"user_id": [123, 456]},
)

response = stub.GetOnlineFeatures(request)
```

---

## Feature Store Patterns

### Point-in-Time Joins

```
POINT-IN-TIME CORRECTNESS
════════════════════════════════════════════════════════════════════

Problem: Training data must use features AS THEY WERE at prediction time

Timeline:
─────────────────────────────────────────────────────────────────
Jan 1      Jan 5      Jan 10     Jan 15     Jan 20
  │          │          │          │          │
  ▼          ▼          ▼          ▼          ▼
Feature:   Feature:   Feature:   Feature:   Feature:
total=10   total=12   total=15   total=20   total=25

Training Example:
If user converted on Jan 10, what was their feature value?

WRONG: Use latest value (25)
RIGHT: Use value at Jan 10 (15)

Feast handles this automatically:
─────────────────────────────────────────────────────────────────
entity_df = pd.DataFrame({
    "user_id": [1],
    "event_timestamp": ["2024-01-10"]  # Training timestamp
})

# Returns total_orders=15 (the value AT that time)
store.get_historical_features(entity_df, features)
```

### Feature Transformation

```python
# On-demand features (computed at request time)
from feast import on_demand_feature_view, Field
from feast.types import Float64

@on_demand_feature_view(
    sources=[user_features],
    schema=[Field(name="spend_per_order", dtype=Float64)],
)
def user_derived_features(inputs: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame()
    df["spend_per_order"] = inputs["total_spend"] / inputs["total_orders"]
    return df
```

### Feature Freshness

```
FEATURE FRESHNESS PATTERNS
════════════════════════════════════════════════════════════════════

Pattern          Latency         Use Case
─────────────────────────────────────────────────────────────────
Batch            Hours           Historical aggregates
                                 (total_lifetime_spend)

Streaming        Seconds-Minutes Real-time aggregates
                                 (clicks_last_hour)

On-Demand        Milliseconds    Request-time computation
                                 (distance_to_store)

ARCHITECTURE:
─────────────────────────────────────────────────────────────────

                    ┌─────────────────┐
                    │   ML Model      │
                    │                 │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│    Batch    │      │  Streaming  │      │  On-Demand  │
│  Features   │      │  Features   │      │  Features   │
│ (Nightly)   │      │ (Kafka)     │      │ (Request)   │
└─────────────┘      └─────────────┘      └─────────────┘
```

> 💡 **Did You Know?** On-demand features solved the "I need to compute something at request time" problem. Before Feast 0.20, you had two choices: materialize everything (slow) or compute outside Feast (training-serving skew). On-demand features let you define transformations that run during `get_online_features()`, keeping logic centralized.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No TTL on features | Stale data served | Set appropriate ttl |
| Ignoring point-in-time | Data leakage in training | Always use get_historical_features |
| Too many feature views | Query complexity | Group related features |
| No feature documentation | Features undiscoverable | Use tags and descriptions |
| Skipping materialization | Online store empty | Schedule regular materialization |
| Same features in multiple views | Inconsistency | Create shared feature views |

---

## War Story: The Time-Traveling Feature

*A fraud detection model had 99% accuracy in training but 60% in production. The team couldn't figure out why.*

**What went wrong**:
1. Training data included `is_fraud` label
2. Feature `transactions_after_fraud_report` was computed for all data
3. In training, this used future knowledge (transactions AFTER fraud was reported)
4. In production, this feature was always 0 (no future data)

**The fix**:
```python
# Entity DataFrame with correct timestamps
entity_df = pd.DataFrame({
    "user_id": user_ids,
    "event_timestamp": transaction_timestamps  # Not report timestamps!
})

# Feast returns features AS OF transaction time
# No future leakage possible
training_df = store.get_historical_features(
    entity_df=entity_df,
    features=["transaction_features:amount", "user_features:total_spend"]
).to_df()
```

**Lesson**: Point-in-time correctness isn't optional. If you're not using a feature store for training data, you're probably leaking future information.

---

## Quiz

### Question 1
What's the difference between offline and online stores?

<details>
<summary>Show Answer</summary>

**Offline Store**:
- Stores historical feature values
- Used for training data generation
- High latency (seconds to minutes)
- High throughput for batch queries
- Examples: BigQuery, Parquet, Redshift

**Online Store**:
- Stores latest feature values
- Used for real-time inference
- Low latency (milliseconds)
- Key-value lookups by entity
- Examples: Redis, DynamoDB, Bigtable

Workflow:
1. Compute features → Offline store
2. Materialize → Copy latest values to Online store
3. Training → Query Offline store
4. Inference → Query Online store

</details>

### Question 2
Why is point-in-time correctness important?

<details>
<summary>Show Answer</summary>

Point-in-time correctness prevents **data leakage**:

Without it:
```
Training example: User A, January 15
Feature "total_purchases" = 100 (includes purchases through March!)
Result: Model learns from future data
Production: Only knows purchases up to "now"
Result: Model performs worse than expected
```

With point-in-time:
```
Training example: User A, January 15
Feature "total_purchases" = 42 (only purchases up to January 15)
Result: Model learns from realistic data
Production: Gets features as of prediction time
Result: Model performance matches training
```

Feast's `get_historical_features` handles this automatically using `event_timestamp`.

</details>

### Question 3
When should you use on-demand features vs batch features?

<details>
<summary>Show Answer</summary>

**Batch Features** when:
- Feature computation is expensive
- Values don't change frequently
- Historical aggregates (lifetime totals)
- Can tolerate staleness (hours)

**On-Demand Features** when:
- Depends on request context
- Simple transformations
- Needs to be fresh
- Combines other features

Examples:
```python
# Batch: Compute nightly, materialize
user_lifetime_spend  # Doesn't change fast

# On-demand: Compute per request
@on_demand_feature_view
def request_features(inputs):
    # Uses request-time data
    df["distance_to_store"] = haversine(
        inputs["user_lat"], inputs["user_lon"],
        inputs["store_lat"], inputs["store_lon"]
    )
    return df
```

Rule of thumb: If it needs fresh request data, on-demand. Otherwise, batch and materialize.

</details>

---

## Hands-On Exercise

### Objective
Set up Feast and serve features for an ML model.

### Tasks

1. **Initialize Feast project**:
   ```bash
   pip install feast
   feast init feast_demo
   cd feast_demo
   ```

2. **Create feature definitions** (save as `feature_repo/user_features.py`):
   ```python
   from datetime import timedelta
   from feast import Entity, FeatureView, FileSource, Field
   from feast.types import Float32, Int64

   user = Entity(name="user_id", join_keys=["user_id"])

   user_source = FileSource(
       path="data/user_features.parquet",
       timestamp_field="event_timestamp"
   )

   user_features = FeatureView(
       name="user_features",
       entities=[user],
       ttl=timedelta(days=1),
       schema=[
           Field(name="total_purchases", dtype=Int64),
           Field(name="avg_purchase_amount", dtype=Float32),
       ],
       source=user_source,
       online=True,
   )
   ```

3. **Create sample data** (save as `create_data.py`):
   ```python
   import pandas as pd
   from datetime import datetime

   df = pd.DataFrame({
       "user_id": [1, 2, 3, 1, 2, 3],
       "total_purchases": [10, 5, 20, 12, 7, 22],
       "avg_purchase_amount": [50.0, 100.0, 25.0, 55.0, 95.0, 30.0],
       "event_timestamp": pd.to_datetime([
           "2024-01-01", "2024-01-01", "2024-01-01",
           "2024-01-15", "2024-01-15", "2024-01-15",
       ]),
       "created_timestamp": pd.to_datetime(["2024-01-01"] * 6),
   })

   df.to_parquet("feature_repo/data/user_features.parquet")
   print("Data created!")
   ```

   ```bash
   mkdir -p feature_repo/data
   python create_data.py
   ```

4. **Apply and materialize**:
   ```bash
   cd feature_repo
   feast apply
   feast materialize-incremental $(date +%Y-%m-%dT%H:%M:%S)
   ```

5. **Query features**:
   ```python
   # query_features.py
   from feast import FeatureStore
   import pandas as pd

   store = FeatureStore(repo_path=".")

   # Historical features
   entity_df = pd.DataFrame({
       "user_id": [1, 2],
       "event_timestamp": pd.to_datetime(["2024-01-10", "2024-01-10"])
   })

   training_df = store.get_historical_features(
       entity_df=entity_df,
       features=["user_features:total_purchases", "user_features:avg_purchase_amount"]
   ).to_df()

   print("Training features:")
   print(training_df)

   # Online features
   online_features = store.get_online_features(
       features=["user_features:total_purchases", "user_features:avg_purchase_amount"],
       entity_rows=[{"user_id": 1}, {"user_id": 2}]
   ).to_dict()

   print("\nOnline features:")
   print(online_features)
   ```

   ```bash
   python query_features.py
   ```

6. **Clean up**:
   ```bash
   cd ..
   rm -rf feast_demo
   ```

### Success Criteria
- [ ] Feast project initialized
- [ ] Feature definitions created
- [ ] Sample data generated
- [ ] Features applied to registry
- [ ] Features materialized to online store
- [ ] Can query historical and online features

### Bonus Challenge
Add an on-demand feature that computes `purchases_per_dollar` from the existing features.

---

## Further Reading

- [Feast Documentation](https://docs.feast.dev/)
- [Feast on Kubernetes](https://docs.feast.dev/reference/kubernetes)
- [Feature Store Summit Talks](https://www.featurestoresummit.com/)
- [Building Real-Time ML Features](https://www.tecton.ai/blog/)

---

## Toolkit Complete!

Congratulations on completing the ML Platforms Toolkit! You've learned:
- Kubeflow for ML workflows and pipelines
- MLflow for experiment tracking and model registry
- Feast for feature storage and serving

These tools form the foundation of a modern MLOps platform on Kubernetes.

---

*"Features are the fuel of machine learning. A feature store is the gas station that keeps your models running—consistent, fresh, and available whenever you need them."*
