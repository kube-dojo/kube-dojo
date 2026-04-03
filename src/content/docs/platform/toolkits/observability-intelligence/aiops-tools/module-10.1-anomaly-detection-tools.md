---
title: "Module 10.1: Anomaly Detection Tools"
slug: platform/toolkits/observability-intelligence/aiops-tools/module-10.1-anomaly-detection-tools
sidebar:
  order: 2
---
> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: 40-45 min

## Prerequisites

Before starting this module:
- [Module 6.2: Anomaly Detection](../../../disciplines/data-ai/aiops/module-6.2-anomaly-detection/) — Conceptual foundation
- Python proficiency
- Basic understanding of time series data
- pip/conda for package installation

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy anomaly detection systems that identify unusual patterns in Kubernetes metrics and logs**
- **Configure machine learning models for time-series anomaly detection on Prometheus metrics**
- **Implement alert correlation to reduce noise and surface actionable anomaly clusters**
- **Evaluate anomaly detection approaches (statistical, ML, deep learning) for different observability data types**


## Why This Module Matters

You understand anomaly detection concepts—now it's time to implement them. This module covers the practical tools: Prophet for time series forecasting, Luminaire for streaming detection, and PyOD for multi-dimensional anomalies. By the end, you'll know which tool to use for each scenario and how to implement them.

## Did You Know?

- **Facebook's Prophet** was born from their need to forecast capacity for billions of users. They open-sourced it in 2017, and it's now used by companies like Uber, Netflix, and Spotify for everything from demand forecasting to anomaly detection.

- **Zillow's Luminaire** was created specifically to detect anomalies in real estate metrics that exhibit frequent "structural breaks"—sudden baseline changes when new listings hit the market or seasonal patterns shift.

- **Isolation Forest** works by randomly isolating observations. Anomalies are isolated faster because they're "few and different"—requiring fewer random cuts to separate from the rest. This elegant idea won the 2012 SIGKDD Best Paper Award.

- **PyOD** includes over 40 anomaly detection algorithms in a unified API, making it the largest Python library for outlier detection. It was created by a PhD student at Carnegie Mellon who was frustrated with implementing the same algorithms repeatedly.

## War Story: The Black Friday Anomaly Disaster

A retail company trained their Prophet model on a full year of traffic data—including Black Friday. When the next Black Friday arrived, their anomaly detection system considered the massive spike "normal" because it had learned the pattern. Meanwhile, an actual database issue during the sale went undetected because the error rates were "within expected Black Friday chaos."

**The lesson**: Be careful what you train on. Sometimes you want to exclude known anomalous periods from training, or use separate models for special events. The team solved this by maintaining two models: one for normal operations and one specifically for high-traffic events with tighter thresholds.

## Tool Overview

```
ANOMALY DETECTION TOOLS
─────────────────────────────────────────────────────────────────

USE CASE                              TOOL
─────────────────────────────────────────────────────────────────

Time series with seasonality    ───▶  Prophet
  • Daily/weekly patterns
  • Holiday effects
  • Trend + forecast

Real-time streaming             ───▶  Luminaire
  • Low latency
  • Auto-configuration
  • Structural breaks

High-dimensional data           ───▶  PyOD
  • Multiple features
  • Multiple algorithms
  • Ensemble methods

Simple/fast detection           ───▶  Isolation Forest (sklearn)
  • Quick to implement
  • Good baseline
  • Production-ready
```

## Prophet: Time Series Forecasting

### Overview

Facebook's Prophet excels at time series with strong seasonal patterns. It automatically handles:
- Multiple seasonalities (daily, weekly, yearly)
- Holiday effects
- Trend changes
- Missing data

### Installation

```bash
pip install prophet
```

### Basic Usage

```python
from prophet import Prophet
import pandas as pd
from datetime import datetime, timedelta

# Prepare data (Prophet requires 'ds' and 'y' columns)
# Generate sample traffic with daily seasonality
import numpy as np
n_points = 168 * 4  # 4 weeks of hourly data
base_traffic = 1000
daily_pattern = 500 * np.sin(np.arange(n_points) * 2 * np.pi / 24)
noise = np.random.normal(0, 50, n_points)

df = pd.DataFrame({
    'ds': pd.date_range('2024-01-01', periods=n_points, freq='H'),
    'y': base_traffic + daily_pattern + noise
})

# Create and fit model
model = Prophet(
    daily_seasonality=True,
    weekly_seasonality=True,
    interval_width=0.95  # 95% confidence interval
)
model.fit(df)

# Forecast
future = model.make_future_dataframe(periods=24, freq='H')
forecast = model.predict(future)

# Detect anomalies (points outside confidence interval)
df_merged = df.merge(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']], on='ds')
df_merged['anomaly'] = (
    (df_merged['y'] < df_merged['yhat_lower']) |
    (df_merged['y'] > df_merged['yhat_upper'])
)

anomalies = df_merged[df_merged['anomaly']]
print(f"Found {len(anomalies)} anomalies")
```

### Production Pattern

```python
class ProphetAnomalyDetector:
    """
    Production-ready Prophet-based anomaly detector.
    """
    def __init__(self, sensitivity=0.95, retrain_hours=24):
        self.sensitivity = sensitivity
        self.retrain_hours = retrain_hours
        self.model = None
        self.last_train_time = None
        self.forecast_cache = {}

    def train(self, df):
        """
        Train Prophet model on historical data.

        df: DataFrame with 'ds' (timestamp) and 'y' (value) columns
        """
        self.model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=len(df) > 365 * 24,  # Only if > 1 year data
            interval_width=self.sensitivity,
            changepoint_prior_scale=0.05  # Flexibility to trend changes
        )
        self.model.fit(df)
        self.last_train_time = datetime.now()

        # Pre-compute forecast for next 24 hours
        future = self.model.make_future_dataframe(periods=24, freq='H')
        forecast = self.model.predict(future)

        # Cache forecast
        for _, row in forecast.iterrows():
            self.forecast_cache[row['ds']] = {
                'yhat': row['yhat'],
                'lower': row['yhat_lower'],
                'upper': row['yhat_upper']
            }

    def is_anomaly(self, timestamp, value):
        """
        Check if a value is anomalous for given timestamp.
        """
        # Check if retrain needed
        if self._should_retrain():
            return None, "Retrain required"

        # Get cached forecast (or nearest hour)
        ts_hour = timestamp.replace(minute=0, second=0, microsecond=0)
        if ts_hour not in self.forecast_cache:
            # Find nearest cached timestamp
            ts_hour = min(
                self.forecast_cache.keys(),
                key=lambda x: abs((x - ts_hour).total_seconds())
            )

        expected = self.forecast_cache[ts_hour]

        is_anomaly = value < expected['lower'] or value > expected['upper']

        return is_anomaly, {
            'value': value,
            'expected': expected['yhat'],
            'lower_bound': expected['lower'],
            'upper_bound': expected['upper'],
            'deviation': abs(value - expected['yhat'])
        }

    def _should_retrain(self):
        """Check if model needs retraining."""
        if self.model is None:
            return True
        if self.last_train_time is None:
            return True
        hours_since_train = (datetime.now() - self.last_train_time).total_seconds() / 3600
        return hours_since_train > self.retrain_hours
```

### When to Use Prophet

| Use Case | Prophet Fit |
|----------|-------------|
| Metrics with daily patterns | Excellent |
| Weekly business cycles | Excellent |
| Holiday-affected metrics | Excellent |
| Real-time (sub-second) | Poor (batch oriented) |
| High-dimensional data | Poor (univariate) |
| Non-seasonal data | Okay (use simpler methods) |

## Luminaire: Streaming Anomaly Detection

### Overview

Zillow's Luminaire is designed for real-time anomaly detection with minimal configuration. It automatically handles:
- Structural breaks (sudden baseline changes)
- Missing data
- Trend detection
- Streaming updates

### Installation

```bash
pip install luminaire
```

> **Compatibility Note**: Luminaire requires Python 3.7-3.9 and may have dependency conflicts with newer NumPy/pandas versions. If you encounter issues, create a dedicated virtual environment: `python3.9 -m venv luminaire-env`. For Python 3.10+, consider using Prophet or PyOD instead.

### Basic Usage

```python
from luminaire.model import LADStructuralModel
from luminaire.exploration.data_exploration import DataExploration
import pandas as pd

# Prepare data
df = pd.DataFrame({
    'timestamp': pd.date_range('2024-01-01', periods=720, freq='H'),
    'value': your_metric_data
})
df.set_index('timestamp', inplace=True)

# Data exploration (optional but recommended)
de = DataExploration(df)
de.profile()

# Configure and train model
model = LADStructuralModel(
    freq='H',                    # Hourly data
    max_scoring_length=24 * 7,   # Score last week
    detection_threshold=0.01     # Sensitivity
)

# Train
model.train(df)

# Score new data
new_data = pd.DataFrame({
    'timestamp': [datetime.now()],
    'value': [current_metric_value]
}).set_index('timestamp')

result = model.score(new_data)

print(f"Anomaly detected: {result['is_anomaly']}")
print(f"Score: {result['score']}")
```

### Production Pattern

```python
from luminaire.model import LADStructuralModel
from luminaire.optimization.hyperparameter_optimization import HyperparameterOptimization
import pandas as pd
from datetime import datetime

class LuminaireDetector:
    """
    Production-ready Luminaire detector with auto-optimization.
    """
    def __init__(self, freq='H', sensitivity=0.01):
        self.freq = freq
        self.sensitivity = sensitivity
        self.model = None
        self.config = None

    def optimize_and_train(self, df):
        """
        Auto-optimize hyperparameters and train.
        """
        # Hyperparameter optimization
        hpo = HyperparameterOptimization(df)
        self.config = hpo.run(
            freq=self.freq,
            detection_threshold=self.sensitivity
        )

        # Train with optimized config
        self.model = LADStructuralModel(**self.config)
        self.model.train(df)

    def train(self, df):
        """
        Train with default configuration.
        """
        self.model = LADStructuralModel(
            freq=self.freq,
            max_scoring_length=24 * 7,
            detection_threshold=self.sensitivity
        )
        self.model.train(df)

    def detect(self, timestamp, value):
        """
        Detect if single point is anomalous.
        """
        if self.model is None:
            raise ValueError("Model not trained")

        # Create single-point DataFrame
        df = pd.DataFrame({
            'timestamp': [timestamp],
            'value': [value]
        }).set_index('timestamp')

        result = self.model.score(df)

        return {
            'is_anomaly': result['is_anomaly'],
            'score': result['score'],
            'timestamp': timestamp,
            'value': value
        }

    def detect_batch(self, df):
        """
        Detect anomalies in batch.
        """
        if self.model is None:
            raise ValueError("Model not trained")

        result = self.model.score(df)

        return result
```

### When to Use Luminaire

| Use Case | Luminaire Fit |
|----------|---------------|
| Streaming data | Excellent |
| Auto-configuration needed | Excellent |
| Structural breaks (level shifts) | Excellent |
| Sub-second latency | Good |
| Multi-dimensional | Poor (univariate) |
| Complex seasonality | Okay (Prophet better) |

## PyOD: Multi-Dimensional Anomaly Detection

### Overview

PyOD provides 40+ anomaly detection algorithms in a unified API. Key algorithms:
- Isolation Forest (fast, scalable)
- LOF (Local Outlier Factor)
- AutoEncoder (neural network)
- COPOD (fast, no hyperparameters)

### Installation

```bash
pip install pyod
```

### Basic Usage

```python
from pyod.models.iforest import IForest
from pyod.models.copod import COPOD
from pyod.models.lof import LOF
import numpy as np

# Multi-dimensional data (e.g., latency + error_rate + cpu)
X = np.column_stack([
    latencies,
    error_rates,
    cpu_usage
])

# Isolation Forest
clf = IForest(contamination=0.01)  # Expect 1% anomalies
clf.fit(X)

# Predict
labels = clf.predict(X)  # 0 = normal, 1 = anomaly
scores = clf.decision_function(X)  # Higher = more anomalous

# Find anomalies
anomaly_indices = np.where(labels == 1)[0]
print(f"Found {len(anomaly_indices)} anomalies")
```

### Algorithm Comparison

```python
from pyod.models.iforest import IForest
from pyod.models.copod import COPOD
from pyod.models.lof import LOF
from pyod.models.auto_encoder import AutoEncoder
import numpy as np

def compare_algorithms(X_train, X_test, contamination=0.01):
    """
    Compare multiple anomaly detection algorithms.
    """
    algorithms = {
        'IsolationForest': IForest(contamination=contamination),
        'COPOD': COPOD(contamination=contamination),
        'LOF': LOF(contamination=contamination, n_neighbors=20),
    }

    results = {}
    for name, clf in algorithms.items():
        clf.fit(X_train)

        train_pred = clf.predict(X_train)
        test_pred = clf.predict(X_test)
        test_scores = clf.decision_function(X_test)

        results[name] = {
            'train_anomalies': np.sum(train_pred),
            'test_anomalies': np.sum(test_pred),
            'scores': test_scores
        }

    return results

# Usage
results = compare_algorithms(X_train, X_test)
for name, result in results.items():
    print(f"{name}: {result['test_anomalies']} anomalies detected")
```

### Ensemble Detection

```python
from pyod.models.combination import average, maximization
import numpy as np

class EnsembleAnomalyDetector:
    """
    Ensemble multiple algorithms for robust detection.
    """
    def __init__(self, contamination=0.01):
        from pyod.models.iforest import IForest
        from pyod.models.copod import COPOD
        from pyod.models.lof import LOF

        self.models = [
            IForest(contamination=contamination),
            COPOD(contamination=contamination),
            LOF(contamination=contamination, n_neighbors=20)
        ]
        self.contamination = contamination

    def fit(self, X):
        """Train all models."""
        for model in self.models:
            model.fit(X)

    def predict(self, X):
        """
        Ensemble prediction using score averaging.
        """
        # Get scores from each model
        all_scores = np.array([
            model.decision_function(X)
            for model in self.models
        ])

        # Average scores
        ensemble_scores = np.mean(all_scores, axis=0)

        # Convert to labels using contamination threshold
        threshold = np.percentile(ensemble_scores, 100 * (1 - self.contamination))
        labels = (ensemble_scores > threshold).astype(int)

        return labels, ensemble_scores
```

### When to Use PyOD

| Use Case | PyOD Fit |
|----------|----------|
| Multi-dimensional data | Excellent |
| Multiple algorithms needed | Excellent |
| Comparing approaches | Excellent |
| Streaming (real-time) | Okay (batch oriented) |
| Time series patterns | Poor (use Prophet) |
| Simple requirements | Overkill (use sklearn) |

## Practical Comparison

### Side-by-Side Test

```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Generate test data with known anomalies
def generate_test_data(n_points=720, anomaly_rate=0.02):
    """Generate data with injected anomalies."""
    np.random.seed(42)

    timestamps = pd.date_range('2024-01-01', periods=n_points, freq='H')

    # Base signal with seasonality
    base = 100
    daily = 30 * np.sin(np.arange(n_points) * 2 * np.pi / 24)
    weekly = 20 * np.sin(np.arange(n_points) * 2 * np.pi / 168)
    noise = np.random.normal(0, 5, n_points)

    values = base + daily + weekly + noise

    # Inject anomalies
    n_anomalies = int(n_points * anomaly_rate)
    anomaly_indices = np.random.choice(n_points, n_anomalies, replace=False)
    anomaly_labels = np.zeros(n_points)

    for idx in anomaly_indices:
        values[idx] += np.random.choice([-1, 1]) * np.random.uniform(50, 100)
        anomaly_labels[idx] = 1

    return pd.DataFrame({
        'timestamp': timestamps,
        'value': values,
        'is_anomaly': anomaly_labels
    })

# Compare tools
def evaluate_tool(detector, df, name):
    """Evaluate detector performance."""
    # Get predictions (implement for each tool)
    predictions = detector.predict(df)

    # Calculate metrics
    actual = df['is_anomaly'].values
    predicted = predictions

    tp = np.sum((actual == 1) & (predicted == 1))
    fp = np.sum((actual == 0) & (predicted == 1))
    fn = np.sum((actual == 1) & (predicted == 0))

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    print(f"\n{name}:")
    print(f"  Precision: {precision:.2%}")
    print(f"  Recall: {recall:.2%}")
    print(f"  F1 Score: {f1:.2%}")

    return {'precision': precision, 'recall': recall, 'f1': f1}
```

### Tool Selection Matrix

```
TOOL SELECTION MATRIX
─────────────────────────────────────────────────────────────────

                    Prophet    Luminaire    PyOD/IForest
─────────────────────────────────────────────────────────────────
Seasonality            ★★★        ★★           ★
Real-time             ★           ★★★          ★★
Multi-dimensional     ★           ★            ★★★
Auto-config           ★★          ★★★          ★★
Interpretability      ★★★        ★★           ★
Setup complexity      ★★          ★            ★★★
Memory usage          ★★          ★★★          ★★
─────────────────────────────────────────────────────────────────

★ = Basic  ★★ = Good  ★★★ = Excellent

RECOMMENDATION BY USE CASE:
─────────────────────────────────────────────────────────────────

Traffic/Request metrics → Prophet
  (Strong seasonality, need forecasting)

Log volume/Error rates → Luminaire
  (Streaming, structural changes)

Multi-metric correlation → PyOD/IForest
  (Latency + errors + CPU together)

Simple/Quick baseline → IForest (sklearn)
  (Fastest to implement)
```

## Hands-On Exercise: Build Multi-Tool Detector

Build a detector that uses the right tool for each metric type:

### Setup

```bash
mkdir anomaly-tools && cd anomaly-tools
python -m venv venv
source venv/bin/activate
pip install prophet pandas numpy scikit-learn
# pip install luminaire  # Optional - may have compatibility issues
pip install pyod
```

### Implementation

```python
# multi_detector.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from prophet import Prophet
from pyod.models.iforest import IForest

class MultiToolDetector:
    """
    Uses different tools for different metric types.

    - Time series with seasonality: Prophet
    - Multi-dimensional: IsolationForest (PyOD)
    - Simple streaming: Z-score fallback
    """
    def __init__(self):
        self.prophet_models = {}  # metric_name -> Prophet model
        self.iforest_model = None
        self.z_stats = {}  # metric_name -> (mean, std)

    def train_prophet(self, metric_name, df):
        """
        Train Prophet for time series metric.

        df: DataFrame with 'ds' and 'y' columns
        """
        model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            interval_width=0.95
        )
        model.fit(df)
        self.prophet_models[metric_name] = model
        print(f"Trained Prophet for {metric_name}")

    def train_iforest(self, X, feature_names):
        """
        Train IsolationForest for multi-dimensional data.

        X: numpy array of shape (n_samples, n_features)
        """
        self.iforest_model = IForest(
            contamination=0.01,
            n_estimators=100
        )
        self.iforest_model.fit(X)
        self.feature_names = feature_names
        print(f"Trained IsolationForest for features: {feature_names}")

    def train_zscore(self, metric_name, values):
        """
        Calculate Z-score statistics for simple metrics.
        """
        self.z_stats[metric_name] = {
            'mean': np.mean(values),
            'std': np.std(values)
        }
        print(f"Calculated Z-score stats for {metric_name}")

    def detect_timeseries(self, metric_name, timestamp, value):
        """
        Detect anomaly in time series metric using Prophet.
        """
        if metric_name not in self.prophet_models:
            raise ValueError(f"No Prophet model for {metric_name}")

        model = self.prophet_models[metric_name]

        # Get forecast for this timestamp
        future = pd.DataFrame({'ds': [timestamp]})
        forecast = model.predict(future)

        expected = forecast['yhat'].iloc[0]
        lower = forecast['yhat_lower'].iloc[0]
        upper = forecast['yhat_upper'].iloc[0]

        is_anomaly = value < lower or value > upper

        return {
            'is_anomaly': is_anomaly,
            'value': value,
            'expected': expected,
            'lower': lower,
            'upper': upper,
            'method': 'prophet'
        }

    def detect_multidim(self, features):
        """
        Detect anomaly in multi-dimensional data using IsolationForest.

        features: dict of feature_name -> value
        """
        if self.iforest_model is None:
            raise ValueError("IsolationForest not trained")

        # Create feature vector
        X = np.array([[features[f] for f in self.feature_names]])

        prediction = self.iforest_model.predict(X)[0]
        score = self.iforest_model.decision_function(X)[0]

        return {
            'is_anomaly': prediction == 1,
            'score': score,
            'features': features,
            'method': 'iforest'
        }

    def detect_simple(self, metric_name, value, threshold=3):
        """
        Simple Z-score detection for basic metrics.
        """
        if metric_name not in self.z_stats:
            raise ValueError(f"No Z-score stats for {metric_name}")

        stats = self.z_stats[metric_name]
        z_score = (value - stats['mean']) / stats['std'] if stats['std'] > 0 else 0

        return {
            'is_anomaly': abs(z_score) > threshold,
            'z_score': z_score,
            'value': value,
            'mean': stats['mean'],
            'method': 'zscore'
        }


# Test the detector
if __name__ == '__main__':
    # Generate test data
    np.random.seed(42)
    n = 720  # 30 days of hourly data

    # Traffic metric (time series with seasonality)
    timestamps = pd.date_range('2024-01-01', periods=n, freq='H')
    traffic = 1000 + 500 * np.sin(np.arange(n) * 2 * np.pi / 24) + np.random.normal(0, 50, n)

    # Multi-dimensional metrics
    latency = np.random.normal(100, 10, n)
    error_rate = np.random.normal(1, 0.5, n)
    cpu = np.random.normal(50, 10, n)

    # Inject anomalies
    anomaly_idx = [100, 200, 300, 400, 500]
    traffic[anomaly_idx] += 2000
    latency[anomaly_idx] += 100
    error_rate[anomaly_idx] += 10

    # Create and train detector
    detector = MultiToolDetector()

    # Train Prophet for traffic
    traffic_df = pd.DataFrame({
        'ds': timestamps,
        'y': traffic
    })
    detector.train_prophet('traffic', traffic_df)

    # Train IsolationForest for multi-dim
    X = np.column_stack([latency, error_rate, cpu])
    detector.train_iforest(X, ['latency', 'error_rate', 'cpu'])

    # Train Z-score for simple metric
    detector.train_zscore('memory', np.random.normal(60, 5, n))

    # Test detection
    print("\n=== Testing Detection ===")

    # Test Prophet (time series)
    result = detector.detect_timeseries(
        'traffic',
        timestamps[100],  # Known anomaly
        traffic[100]
    )
    print(f"\nProphet detection at idx 100:")
    print(f"  Is anomaly: {result['is_anomaly']}")
    print(f"  Value: {result['value']:.0f}, Expected: {result['expected']:.0f}")

    # Test IsolationForest (multi-dim)
    result = detector.detect_multidim({
        'latency': latency[100],
        'error_rate': error_rate[100],
        'cpu': cpu[100]
    })
    print(f"\nIsolationForest detection at idx 100:")
    print(f"  Is anomaly: {result['is_anomaly']}")
    print(f"  Score: {result['score']:.2f}")

    # Test Z-score (simple)
    result = detector.detect_simple('memory', 90)  # High value
    print(f"\nZ-score detection for memory=90:")
    print(f"  Is anomaly: {result['is_anomaly']}")
    print(f"  Z-score: {result['z_score']:.2f}")
```

### Success Criteria

You've completed this exercise when:
- [ ] Trained Prophet for seasonal time series
- [ ] Trained IsolationForest for multi-dimensional data
- [ ] Implemented Z-score fallback for simple metrics
- [ ] Detected injected anomalies successfully
- [ ] Understand which tool to use for each metric type

## Key Takeaways

1. **No single tool fits all**: Match the tool to the data characteristics
2. **Prophet for seasonality**: Best for metrics with clear patterns
3. **Luminaire for streaming**: Real-time detection with auto-config
4. **PyOD for multi-dimensional**: When correlating multiple metrics
5. **Ensemble improves robustness**: Combine multiple approaches
6. **Start simple**: Z-score or IsolationForest before complex tools

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Using Prophet for real-time | Prophet is batch-oriented, not designed for sub-second | Use Luminaire or Z-score for streaming |
| Training on anomalous data | Model learns anomalies as "normal" | Clean training data or use robust methods |
| Same contamination everywhere | 1% contamination wrong for most datasets | Tune per-metric based on actual anomaly rate |
| Ignoring seasonality type | Daily model misses weekly patterns | Check data for multiple seasonality periods |
| Over-engineering first attempt | Complex ensemble before baseline | Start with Z-score or IsolationForest |
| Not retraining models | Baseline drift causes false positives | Schedule regular retraining (daily/weekly) |

## Quiz

<details>
<summary>1. When should you choose Prophet over Luminaire for anomaly detection?</summary>

**Answer**: Choose Prophet when:
- Your data has strong daily, weekly, or yearly seasonality patterns
- You need to forecast future values, not just detect current anomalies
- You can tolerate batch processing (not real-time)
- Holiday effects significantly impact your metrics

Choose Luminaire when:
- You need real-time, streaming detection
- Your data has frequent structural breaks (sudden baseline changes)
- You want minimal configuration
- Low-latency detection is critical
</details>

<details>
<summary>2. What is the purpose of the `contamination` parameter in PyOD algorithms?</summary>

**Answer**: The `contamination` parameter specifies the expected proportion of anomalies in your dataset (e.g., 0.01 = 1% anomalies). It affects:
- The decision threshold for classifying points as anomalies
- Model sensitivity (lower = more conservative, higher = more sensitive)
- Should be tuned based on actual domain knowledge about anomaly rates

Common mistake: Using the default value without considering your actual data characteristics.
</details>

<details>
<summary>3. Why would you use an ensemble approach (combining multiple algorithms) for anomaly detection?</summary>

**Answer**: Ensemble approaches provide:
1. **Robustness**: Different algorithms catch different types of anomalies
2. **Reduced false positives**: Consensus reduces individual algorithm weaknesses
3. **Handling unknown patterns**: When you're unsure which algorithm fits best
4. **Production reliability**: Single algorithm failures don't break detection

The trade-off is increased complexity and compute cost.
</details>

<details>
<summary>4. How does Isolation Forest detect anomalies differently from Z-score?</summary>

**Answer**:
- **Z-score**: Measures distance from mean in standard deviations. Works well for univariate data with roughly normal distribution. Fails when anomalies aren't "far" from the mean or when distribution is non-Gaussian.

- **Isolation Forest**: Randomly partitions data using decision trees. Anomalies require fewer splits to isolate because they're "few and different." Works well for high-dimensional data and doesn't assume any distribution.

Key differences:
- Z-score: Univariate, assumes distribution, interpretable threshold
- Isolation Forest: Multi-dimensional, distribution-free, learns from data structure
</details>

## Further Reading

- [Prophet Documentation](https://facebook.github.io/prophet/)
- [Luminaire GitHub](https://github.com/zillow/luminaire)
- [PyOD Documentation](https://pyod.readthedocs.io/)
- [Isolation Forest Paper](https://cs.nju.edu.cn/zhouzh/zhouzh.files/publication/icdm08b.pdf)

## Summary

Anomaly detection tools each have strengths: Prophet for seasonal time series, Luminaire for streaming with structural breaks, and PyOD for multi-dimensional data. The key is matching the tool to your data's characteristics—and combining them for robust detection.

---

## Next Module

Continue to [Module 10.2: Event Correlation Platforms](../module-10.2-event-correlation-platforms/) to learn about enterprise platforms like BigPanda and Moogsoft.
