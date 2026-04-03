---
title: "Module 5.5: Model Monitoring & Observability"
slug: platform/disciplines/data-ai/mlops/module-5.5-model-monitoring
sidebar:
  order: 6
---
> **Discipline Track** | Complexity: `[COMPLEX]` | Time: 40-45 min

## Prerequisites

Before starting this module:
- [Module 5.4: Model Serving & Inference](../module-5.4-model-serving/)
- [Observability Theory Track](../../../foundations/observability-theory/) (recommended)
- Understanding of statistical distributions
- Basic Prometheus/Grafana knowledge

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Implement model monitoring systems that detect data drift, prediction drift, and performance degradation**
- **Design alerting policies that trigger model retraining when prediction quality drops below thresholds**
- **Build monitoring dashboards that track model accuracy, latency, and feature distribution over time**
- **Evaluate monitoring approaches — statistical tests, reference windows, population stability — for your models**

## Why This Module Matters

ML models fail silently. A web server crashes—you get an alert. A model returns wrong predictions—nothing happens. The model is "up," returning 200 OK, while making decisions that cost you money, customers, or worse.

Traditional monitoring (latency, uptime, errors) is necessary but insufficient. You need to know: Is the model still accurate? Has the data changed? Are predictions still relevant?

Companies like Uber, Airbnb, and Stripe invest heavily in model monitoring because they've learned the cost of undetected model degradation.

## Did You Know?

- **Model accuracy degrades 2-10% per year** on average without retraining, according to research by Google and Microsoft—faster in volatile domains
- **90% of ML models in production have no performance monitoring**—teams only discover failures through user complaints or revenue drops
- **Uber's ML platform detects data drift** before it impacts predictions, enabling proactive retraining instead of reactive firefighting
- **The time to detect model failure** averages 3-6 months without proper monitoring—by then, significant damage has occurred

## What to Monitor

```
┌─────────────────────────────────────────────────────────────────┐
│                 ML MONITORING LAYERS                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  LAYER 1: INFRASTRUCTURE (Traditional)                          │
│  ├── Latency, throughput, error rates                           │
│  ├── CPU, memory, GPU utilization                               │
│  └── Service availability                                       │
│                                                                  │
│  LAYER 2: DATA QUALITY                                          │
│  ├── Schema validation                                          │
│  ├── Missing value rates                                        │
│  ├── Value range violations                                     │
│  └── Feature distributions                                      │
│                                                                  │
│  LAYER 3: MODEL PERFORMANCE                                     │
│  ├── Prediction distribution                                    │
│  ├── Model metrics (if labels available)                        │
│  ├── Feature importance stability                               │
│  └── Calibration                                                │
│                                                                  │
│  LAYER 4: BUSINESS IMPACT                                       │
│  ├── Conversion rates                                           │
│  ├── Revenue attribution                                        │
│  └── User satisfaction                                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### The Four Questions

| Question | Monitoring Layer |
|----------|------------------|
| "Is the service healthy?" | Infrastructure |
| "Is the data valid?" | Data Quality |
| "Is the model accurate?" | Model Performance |
| "Is it working for the business?" | Business Impact |

Most teams only answer question 1. You need all four.

## Understanding Drift

### Types of Drift

```
TYPES OF DRIFT
─────────────────────────────────────────────────────────────────

DATA DRIFT (Feature distribution changes)
Training:   ████████████████████░░░░░░░░░░░░
Production: ░░░░░░░████████████████████░░░░░
            ↑
            Distribution shifted right

Example: Income feature trained on pre-pandemic data,
         now serving post-pandemic data with higher unemployment


CONCEPT DRIFT (Relationship changes)
Training:   Feature X → Outcome Y (strong relationship)
Production: Feature X → Outcome Y (weak/different relationship)

Example: Fraud patterns change. Same features,
         different fraud behaviors.


PREDICTION DRIFT (Output distribution changes)
Training:   Fraud predictions: 2% positive
Production: Fraud predictions: 15% positive
            ↑
            Something changed (data or concept drift upstream)


LABEL DRIFT (Target distribution changes)
Training:   Class balance: 50/50
Production: Class balance: 80/20

Example: Seasonal change in purchase behavior
```

### War Story: The Slow Decline

A financial model predicted loan defaults. Initial accuracy: 94%. Twelve months later: 71%. The decline was gradual—no single day showed a dramatic drop.

The problem? Economic conditions changed slowly. Features that predicted defaults in 2019 didn't work in 2020. Without drift monitoring, the team only discovered the problem during quarterly reviews.

A drift detector would have flagged the issue within weeks, not months.

## Drift Detection Methods

### Statistical Tests

```
DRIFT DETECTION METHODS
─────────────────────────────────────────────────────────────────

KOLMOGOROV-SMIRNOV TEST (Numerical features)
├── Compares cumulative distributions
├── H0: Distributions are the same
├── p < 0.05 → Drift detected
└── Works well for continuous features

CHI-SQUARE TEST (Categorical features)
├── Compares frequency distributions
├── H0: Distributions are the same
├── p < 0.05 → Drift detected
└── Works for discrete/categorical

POPULATION STABILITY INDEX (PSI)
├── Measures distribution shift
├── PSI < 0.1 → No significant change
├── 0.1 ≤ PSI < 0.25 → Moderate shift
├── PSI ≥ 0.25 → Significant shift
└── Industry standard for credit scoring

JENSEN-SHANNON DIVERGENCE
├── Symmetric version of KL divergence
├── Bounded [0, 1]
├── Compares probability distributions
└── Works for both numerical and categorical
```

### PSI Calculation

```
PSI = Σ (Actual% - Expected%) × ln(Actual% / Expected%)

Example:
Bucket    Training    Production    Contribution
─────────────────────────────────────────────────
0-20%     20%         15%           0.015
20-40%    20%         18%           0.002
40-60%    20%         22%           0.002
60-80%    20%         25%           0.013
80-100%   20%         20%           0.000
─────────────────────────────────────────────────
PSI = 0.032 → No significant drift
```

## Evidently for Drift Detection

Evidently is the leading open-source tool for ML monitoring:

```
┌─────────────────────────────────────────────────────────────────┐
│                        EVIDENTLY                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CAPABILITIES                                                    │
│  ├── Data drift detection                                       │
│  ├── Target drift detection                                     │
│  ├── Model performance reports                                  │
│  ├── Data quality monitoring                                    │
│  └── Regression/classification metrics                          │
│                                                                  │
│  OUTPUT FORMATS                                                  │
│  ├── Interactive HTML reports                                   │
│  ├── JSON for dashboards                                        │
│  ├── Prometheus metrics                                         │
│  └── Python objects for automation                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Evidently Reports

```python
from evidently import ColumnMapping
from evidently.report import Report
from evidently.metric_preset import (
    DataDriftPreset,
    DataQualityPreset,
    TargetDriftPreset,
)

# Column mapping
column_mapping = ColumnMapping(
    target='target',
    prediction='prediction',
    numerical_features=['feature1', 'feature2', 'feature3'],
    categorical_features=['category1', 'category2'],
)

# Create report
report = Report(metrics=[
    DataDriftPreset(),
    DataQualityPreset(),
    TargetDriftPreset(),
])

# Generate report
report.run(
    reference_data=training_data,
    current_data=production_data,
    column_mapping=column_mapping,
)

# Save HTML report
report.save_html("drift_report.html")

# Get results as dict
results = report.as_dict()
drift_detected = results['metrics'][0]['result']['dataset_drift']
```

### Evidently Tests (CI/CD)

```python
from evidently.test_suite import TestSuite
from evidently.tests import (
    TestShareOfDriftedColumns,
    TestNumberOfMissingValues,
    TestValueRange,
)

# Define tests
test_suite = TestSuite(tests=[
    TestShareOfDriftedColumns(lt=0.3),  # Less than 30% columns drifted
    TestNumberOfMissingValues(eq=0),     # No missing values
    TestValueRange(column_name='age', left=0, right=120),
])

# Run tests
test_suite.run(
    reference_data=training_data,
    current_data=production_data,
)

# Check results
if not test_suite.as_dict()['summary']['all_passed']:
    print("Tests failed! Block deployment.")
```

## Monitoring Pipeline

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│               ML MONITORING PIPELINE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  INFERENCE SERVICE                                               │
│  ┌────────────────┐                                             │
│  │ Request ──▶    │     ┌─────────────────┐                     │
│  │     Model      │────▶│   Log Store     │                     │
│  │ ──▶ Prediction │     │ (inputs,outputs)│                     │
│  └────────────────┘     └────────┬────────┘                     │
│                                  │                               │
│                                  ▼                               │
│                         ┌─────────────────┐                     │
│                         │  Drift Detector │                     │
│                         │   (Evidently)   │                     │
│                         └────────┬────────┘                     │
│                                  │                               │
│           ┌──────────────────────┼──────────────────────┐       │
│           │                      │                      │        │
│           ▼                      ▼                      ▼        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Prometheus    │  │     Grafana     │  │    Alerting     │  │
│  │   (metrics)     │  │  (dashboards)   │  │  (PagerDuty)    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                  │
│                              │                                   │
│                              ▼                                   │
│                    ┌─────────────────┐                          │
│                    │    Retrain      │                          │
│                    │   Trigger       │                          │
│                    └─────────────────┘                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Define metrics
PREDICTION_COUNT = Counter(
    'model_predictions_total',
    'Total predictions',
    ['model_version', 'prediction_class']
)

PREDICTION_LATENCY = Histogram(
    'model_prediction_latency_seconds',
    'Prediction latency',
    ['model_version'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0]
)

FEATURE_VALUE = Gauge(
    'model_feature_value',
    'Feature values',
    ['feature_name']
)

DRIFT_SCORE = Gauge(
    'model_drift_score',
    'Drift score by feature',
    ['feature_name']
)

# Instrument predictions
def predict_with_monitoring(features):
    with PREDICTION_LATENCY.labels(model_version='v1').time():
        prediction = model.predict(features)

    PREDICTION_COUNT.labels(
        model_version='v1',
        prediction_class=str(prediction)
    ).inc()

    # Log feature values
    for name, value in features.items():
        FEATURE_VALUE.labels(feature_name=name).set(value)

    return prediction

# Start metrics server
start_http_server(8000)
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "ML Model Monitoring",
    "panels": [
      {
        "title": "Prediction Volume",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(model_predictions_total[5m])",
            "legendFormat": "{{model_version}}"
          }
        ]
      },
      {
        "title": "Prediction Latency (p99)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.99, rate(model_prediction_latency_seconds_bucket[5m]))",
            "legendFormat": "p99"
          }
        ]
      },
      {
        "title": "Drift Score by Feature",
        "type": "gauge",
        "targets": [
          {
            "expr": "model_drift_score",
            "legendFormat": "{{feature_name}}"
          }
        ]
      },
      {
        "title": "Prediction Distribution",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum(model_predictions_total) by (prediction_class)",
            "legendFormat": "{{prediction_class}}"
          }
        ]
      }
    ]
  }
}
```

## Alerting Strategy

### What to Alert On

| Condition | Severity | Action |
|-----------|----------|--------|
| Service down | Critical | Page on-call |
| Latency > SLO | High | Investigate immediately |
| Error rate > 1% | High | Investigate immediately |
| Drift detected (single feature) | Medium | Review within 24h |
| Drift detected (multiple features) | High | Review immediately |
| Accuracy drop > 5% | Critical | Retrain or rollback |
| Prediction distribution shift | Medium | Investigate cause |

### Alert Examples

```yaml
# Prometheus alerting rules
groups:
  - name: ml-model-alerts
    rules:
      - alert: ModelLatencyHigh
        expr: histogram_quantile(0.99, rate(model_prediction_latency_seconds_bucket[5m])) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Model latency is high"
          description: "P99 latency is {{ $value }}s (threshold: 0.5s)"

      - alert: ModelDriftDetected
        expr: model_drift_score > 0.25
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Data drift detected"
          description: "Feature {{ $labels.feature_name }} has drift score {{ $value }}"

      - alert: PredictionDistributionShift
        expr: |
          abs(
            (sum(rate(model_predictions_total{prediction_class="1"}[1h])) /
             sum(rate(model_predictions_total[1h])))
            -
            0.02  # Expected positive rate
          ) > 0.01
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Prediction distribution has shifted"
```

## Performance Monitoring Without Labels

### The Delayed Label Problem

```
DELAYED LABEL PROBLEM
─────────────────────────────────────────────────────────────────

Prediction Time                           Label Available
      │                                        │
      ▼                                        ▼
Day 0: Predict fraud                    Day 30: Know if actually fraud
      │◀─────────── 30 day delay ──────────▶│

Problem: By the time you know accuracy dropped,
         you've served bad predictions for 30 days!

Solution: Monitor proxies for performance
├── Prediction distribution (drift)
├── Feature distributions
├── Confidence scores
└── Business metrics (immediate feedback)
```

### Proxy Metrics

When you can't measure accuracy directly:

| Proxy Metric | What It Indicates |
|--------------|-------------------|
| Prediction confidence | Model uncertainty |
| Prediction distribution | Overall behavior change |
| Feature drift | Input distribution shift |
| Business metrics | Real-world impact |
| User behavior | Implicit feedback |

### NannyML for Performance Estimation

```python
import nannyml as nml

# Estimate performance without labels
estimator = nml.CBPE(
    y_pred_proba='prediction_probability',
    y_pred='prediction',
    y_true='target',  # Only needed for reference
    metrics=['roc_auc', 'f1'],
    chunk_size=5000,
)

# Fit on reference data (with labels)
estimator.fit(reference_data)

# Estimate on production data (without labels)
estimates = estimator.estimate(production_data)

# Plot
figure = estimates.plot()
```

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Only monitoring infrastructure | Model fails silently | Add data and model metrics |
| No reference baseline | Can't detect drift | Store training data statistics |
| Alerting on every drift | Alert fatigue | Set meaningful thresholds |
| No automated response | Manual intervention required | Auto-retrain or auto-rollback |
| Ignoring business metrics | Technical success, business failure | Track conversion, revenue |
| No root cause analysis | Fix symptoms, not causes | Investigate why drift occurred |

## Quiz

Test your understanding:

<details>
<summary>1. What's the difference between data drift and concept drift?</summary>

**Answer**:
- **Data drift**: Input feature distributions change (e.g., more high-income users)
- **Concept drift**: Relationship between features and target changes (e.g., what predicts fraud changes)

Data drift can often be detected without labels. Concept drift usually requires labels to detect because you need to compare predictions against actual outcomes.
</details>

<details>
<summary>2. Why is PSI commonly used in financial services?</summary>

**Answer**: PSI (Population Stability Index) is:
- Industry standard with regulatory acceptance
- Simple to explain to non-technical stakeholders
- Provides clear thresholds (< 0.1, 0.1-0.25, > 0.25)
- Works for both numerical and categorical features
- Can be calculated without labels

Financial regulators often require documented drift monitoring, and PSI provides auditable, interpretable results.
</details>

<details>
<summary>3. How do you monitor model performance when labels are delayed?</summary>

**Answer**: Use proxy metrics:
1. **Prediction distribution**: Shifts indicate something changed
2. **Confidence scores**: Low confidence may indicate out-of-distribution data
3. **Feature drift**: Data drift often precedes concept drift
4. **Business metrics**: Immediate feedback (conversions, clicks)
5. **Performance estimation**: Tools like NannyML estimate accuracy without labels

These proxies don't replace actual accuracy measurement but provide early warnings.
</details>

<details>
<summary>4. What should trigger a model retrain?</summary>

**Answer**: Retrain triggers:
- **Accuracy drop**: Below acceptable threshold
- **Significant drift**: Multiple features or high PSI
- **Business metric decline**: Revenue, conversion drops
- **Scheduled interval**: Regular retraining (weekly, monthly)
- **New data available**: Significant volume of new labeled data

Automated retraining should include validation gates—don't deploy a worse model.
</details>

## Hands-On Exercise: Build a Monitoring Pipeline

Set up drift detection and alerting:

### Setup

```bash
mkdir ml-monitoring && cd ml-monitoring
python -m venv venv
source venv/bin/activate
pip install evidently pandas scikit-learn prometheus-client
```

### Step 1: Generate Data with Drift

```python
# generate_data.py
import pandas as pd
import numpy as np
from sklearn.datasets import make_classification

np.random.seed(42)

def generate_dataset(n_samples, drift_factor=0.0):
    """Generate classification dataset with optional drift."""
    X, y = make_classification(
        n_samples=n_samples,
        n_features=5,
        n_informative=3,
        n_redundant=1,
        random_state=42
    )

    df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(5)])
    df['target'] = y

    # Add drift to feature_0 and feature_1
    df['feature_0'] = df['feature_0'] + drift_factor
    df['feature_1'] = df['feature_1'] * (1 + drift_factor * 0.5)

    return df

# Generate reference (training) data
reference = generate_dataset(1000, drift_factor=0.0)
reference.to_parquet('reference_data.parquet')
print("Reference data:")
print(reference.describe())

# Generate production data with drift
production = generate_dataset(1000, drift_factor=0.5)
production.to_parquet('production_data.parquet')
print("\nProduction data (with drift):")
print(production.describe())
```

### Step 2: Create Drift Detection Report

```python
# detect_drift.py
import pandas as pd
from evidently import ColumnMapping
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, DataQualityPreset

# Load data
reference = pd.read_parquet('reference_data.parquet')
production = pd.read_parquet('production_data.parquet')

# Column mapping
column_mapping = ColumnMapping(
    target='target',
    numerical_features=['feature_0', 'feature_1', 'feature_2', 'feature_3', 'feature_4'],
)

# Create report
report = Report(metrics=[
    DataDriftPreset(),
    DataQualityPreset(),
])

# Run report
report.run(
    reference_data=reference,
    current_data=production,
    column_mapping=column_mapping,
)

# Save HTML report
report.save_html('drift_report.html')
print("Drift report saved to drift_report.html")

# Extract drift results
results = report.as_dict()
drift_info = results['metrics'][0]['result']

print(f"\nDataset drift detected: {drift_info['dataset_drift']}")
print(f"Drifted features: {drift_info['number_of_drifted_columns']}/{drift_info['number_of_columns']}")

for col_name, col_data in drift_info['drift_by_columns'].items():
    if col_data['drift_detected']:
        print(f"  - {col_name}: drift_score={col_data['drift_score']:.4f}")
```

### Step 3: Create Automated Tests

```python
# test_data.py
import pandas as pd
from evidently import ColumnMapping
from evidently.test_suite import TestSuite
from evidently.tests import (
    TestShareOfDriftedColumns,
    TestColumnDrift,
    TestNumberOfMissingValues,
    TestShareOfOutRangeValues,
)

# Load data
reference = pd.read_parquet('reference_data.parquet')
production = pd.read_parquet('production_data.parquet')

# Column mapping
column_mapping = ColumnMapping(
    target='target',
    numerical_features=['feature_0', 'feature_1', 'feature_2', 'feature_3', 'feature_4'],
)

# Define test suite
test_suite = TestSuite(tests=[
    # No more than 30% of columns should drift
    TestShareOfDriftedColumns(lt=0.3),

    # Specific column tests
    TestColumnDrift(column_name='feature_0'),
    TestColumnDrift(column_name='feature_1'),

    # Data quality
    TestNumberOfMissingValues(eq=0),
])

# Run tests
test_suite.run(
    reference_data=reference,
    current_data=production,
    column_mapping=column_mapping,
)

# Check results
results = test_suite.as_dict()

print("Test Results:")
print(f"All passed: {results['summary']['all_passed']}")
print(f"Success: {results['summary']['success_tests']}")
print(f"Failed: {results['summary']['failed_tests']}")

for test in results['tests']:
    status = "✓" if test['status'] == 'SUCCESS' else "✗"
    print(f"  {status} {test['name']}: {test['status']}")

# Exit with error if tests fail
if not results['summary']['all_passed']:
    print("\nTests failed! Would block deployment.")
    exit(1)
```

### Step 4: Add Prometheus Metrics

```python
# monitoring_service.py
from prometheus_client import start_http_server, Gauge
import pandas as pd
import time
from evidently import ColumnMapping
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset

# Prometheus metrics
DRIFT_SCORE = Gauge('model_drift_score', 'Drift score by feature', ['feature'])
DATASET_DRIFT = Gauge('model_dataset_drift', 'Overall dataset drift detected')

def calculate_drift():
    """Calculate drift and update metrics."""
    reference = pd.read_parquet('reference_data.parquet')
    production = pd.read_parquet('production_data.parquet')

    column_mapping = ColumnMapping(
        target='target',
        numerical_features=['feature_0', 'feature_1', 'feature_2', 'feature_3', 'feature_4'],
    )

    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=reference, current_data=production, column_mapping=column_mapping)

    results = report.as_dict()
    drift_info = results['metrics'][0]['result']

    # Update metrics
    DATASET_DRIFT.set(1 if drift_info['dataset_drift'] else 0)

    for col_name, col_data in drift_info['drift_by_columns'].items():
        DRIFT_SCORE.labels(feature=col_name).set(col_data['drift_score'])

    print(f"Drift metrics updated. Dataset drift: {drift_info['dataset_drift']}")

# Start metrics server
start_http_server(8000)
print("Metrics server started on :8000")

# Update metrics periodically
while True:
    calculate_drift()
    time.sleep(60)  # Update every minute
```

### Step 5: View Results

```bash
# Generate data
python generate_data.py

# Run drift detection
python detect_drift.py
# Open drift_report.html in browser

# Run tests
python test_data.py

# Start metrics server
python monitoring_service.py

# In another terminal, view metrics
curl localhost:8000/metrics | grep model_
```

### Success Criteria

You've completed this exercise when you can:
- [ ] Generate reference and production data with drift
- [ ] Create HTML drift report
- [ ] Run automated drift tests
- [ ] Export drift metrics to Prometheus format
- [ ] Identify which features drifted

## Key Takeaways

1. **ML needs additional monitoring**: Infrastructure monitoring isn't enough
2. **Drift detection catches problems early**: Before accuracy degrades
3. **Labels are often delayed**: Use proxy metrics for immediate feedback
4. **Automate responses**: Alert, then retrain or rollback
5. **Business metrics matter most**: Technical success ≠ business success

## Further Reading

- [Evidently Documentation](https://docs.evidentlyai.com/) — ML monitoring library
- [NannyML Documentation](https://nannyml.readthedocs.io/) — Performance estimation
- [Monitoring ML Models in Production](https://christophergs.com/machine%20learning/2020/03/14/how-to-monitor-machine-learning-models/) — Comprehensive guide
- [Google's ML Test Score](https://research.google/pubs/pub46555/) — ML testing best practices

## Summary

Model monitoring goes beyond infrastructure observability. You need to track data quality, drift detection, and business impact. Statistical tests (KS, PSI, chi-square) detect distribution changes. Evidently provides comprehensive reports and automated tests. When labels are delayed, use proxy metrics. The goal is catching problems before users do—proactive retraining instead of reactive firefighting.

---

## Next Module

Continue to [Module 5.6: ML Pipelines & Automation](../module-5.6-ml-pipelines/) to learn how to automate the entire ML lifecycle.
