---
title: "Module 10.4: Building Custom AIOps"
slug: platform/toolkits/observability-intelligence/aiops-tools/module-10.4-building-custom-aiops
sidebar:
  order: 5
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 50-60 minutes

## Prerequisites

Before starting this module:
- [AIOps Discipline](../../../disciplines/data-ai/aiops/) — Complete conceptual foundation
- [Module 10.1: Anomaly Detection Tools](module-10.1-anomaly-detection-tools/) — Detection libraries
- Python proficiency (pandas, scikit-learn basics)
- Kubernetes basics (Deployments, Services, ConfigMaps)
- Basic understanding of Kafka or similar streaming platforms

## Why This Module Matters

Platform AI (Datadog Watchdog, Dynatrace Davis) covers 80% of use cases. But sometimes you need **custom AIOps** because:

1. **Domain-specific detection** — Your anomalies are unique to your business
2. **Data sovereignty** — Data cannot leave your infrastructure
3. **Cost optimization** — Platform AI pricing doesn't scale for you
4. **Integration requirements** — Need to integrate with proprietary systems
5. **Competitive advantage** — AIOps as a differentiator

Building custom AIOps is a significant investment. This module shows you how to do it right.

## Did You Know?

- **Netflix's anomaly detection system** processes **billions of time series** with custom algorithms. They open-sourced many components (Surus, Argus) but the full system remains proprietary because it's tightly integrated with their streaming architecture.

- **Uber built Argos** for real-time anomaly detection across their microservices. At peak, it processes 500+ million metrics per minute with sub-second detection latency—impossible with off-the-shelf tools at their scale.

- **LinkedIn's ThirdEye** is open-sourced from their internal AIOps platform. It was built after they realized commercial tools couldn't handle their 10,000+ services generating 30+ million metrics.

- **Pinterest's Anomaly Detection** system uses isolation forest ensembles trained on 2 years of historical data. They found that domain-specific training data improved accuracy by 40% compared to generic models—the key insight that drove them to build custom.

## War Story: The $8M Custom AIOps That Saved $50M

A major e-commerce company was losing $2M per hour during peak shopping periods when their systems had issues. Their off-the-shelf monitoring tools detected problems, but the correlation was too slow—by the time they figured out the root cause, an hour had passed.

**The challenge:**
- 4,000+ microservices
- 2 million metrics per minute
- Complex dependencies (payment → inventory → shipping → notifications)
- Platform AI tools took 5-15 minutes to correlate events

**The decision to build custom:**

After a $12M incident during a flash sale (6 hours of degraded checkout), they decided commercial tools weren't cutting it. They spent $8M over 18 months building a custom AIOps platform.

**Architecture decisions:**
1. **Kafka backbone** — Every metric, log, and trace flowed through Kafka topics
2. **Pre-computed topology** — Service dependencies updated every 5 minutes, cached in Redis
3. **Domain-specific detectors** — Different ML models for checkout flow vs. browse flow
4. **Human feedback loop** — Engineers rated every alert, continuously improving models

**The breakthrough:**

Their custom system achieved 45-second detection-to-root-cause time. The key innovation wasn't fancier ML—it was **pre-computed correlation**. Instead of correlating events in real-time, they maintained a constantly-updated dependency graph that instantly showed blast radius.

**Results after 2 years:**
- MTTR dropped from 45 minutes to 6 minutes
- Incident frequency dropped 60% (predictive alerting caught issues before impact)
- Engineering hours on incidents dropped from 400/month to 80/month
- ROI: $50M saved annually vs. $8M investment

**The lesson**: Custom AIOps makes sense at scale. The break-even point for this company was around 1,000 services. Below that, commercial tools win on cost. Above that, custom wins on accuracy and speed.

---

## Custom AIOps Architecture

```
CUSTOM AIOPS ARCHITECTURE ON KUBERNETES
────────────────────────────────────────────────────────────────

DATA SOURCES                    INGESTION
┌─────────┐                    ┌─────────────────┐
│Prometheus│───────────────────▶│                 │
├─────────┤                    │     Kafka       │
│  Loki   │───────────────────▶│    (Ingest)     │
├─────────┤                    │                 │
│  Tempo  │───────────────────▶│  Topics:        │
├─────────┤                    │  - metrics      │
│ Events  │───────────────────▶│  - logs         │
└─────────┘                    │  - traces       │
                               │  - events       │
                               └────────┬────────┘
                                        │
PROCESSING                              ▼
┌─────────────────────────────────────────────────────────┐
│                    AIOPS PIPELINE                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  Anomaly    │  │   Event     │  │    Root     │     │
│  │  Detection  │──│ Correlation │──│   Cause     │     │
│  │  (Python)   │  │  (Python)   │  │  Analysis   │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│         │                                  │            │
│         └──────────────┬───────────────────┘            │
│                        ▼                                │
│               ┌─────────────┐                          │
│               │  Incident   │                          │
│               │  Manager    │                          │
│               └─────────────┘                          │
└────────────────────────┬────────────────────────────────┘
                         │
ACTIONS                  ▼
              ┌─────────────────┐
              │  - PagerDuty    │
              │  - Slack        │
              │  - Auto-Remediate
              │  - Runbooks     │
              └─────────────────┘
```

---

## Project Structure

```
custom-aiops/
├── docker-compose.yml          # Local development
├── k8s/                        # Kubernetes manifests
│   ├── namespace.yaml
│   ├── kafka/
│   │   ├── kafka-deployment.yaml
│   │   └── zookeeper-deployment.yaml
│   ├── aiops/
│   │   ├── detector-deployment.yaml
│   │   ├── correlator-deployment.yaml
│   │   └── configmap.yaml
│   └── monitoring/
│       └── prometheus-servicemonitor.yaml
├── src/
│   ├── detector/               # Anomaly detection service
│   │   ├── main.py
│   │   ├── detectors/
│   │   │   ├── prophet_detector.py
│   │   │   ├── isolation_forest.py
│   │   │   └── luminaire_detector.py
│   │   └── config.py
│   ├── correlator/             # Event correlation service
│   │   ├── main.py
│   │   ├── correlators/
│   │   │   ├── time_based.py
│   │   │   ├── topology_based.py
│   │   │   └── text_based.py
│   │   └── config.py
│   ├── incident_manager/       # Incident management
│   │   ├── main.py
│   │   ├── actions/
│   │   │   ├── pagerduty.py
│   │   │   ├── slack.py
│   │   │   └── remediation.py
│   │   └── config.py
│   └── common/
│       ├── kafka_utils.py
│       ├── prometheus_client.py
│       └── models.py
├── tests/
├── requirements.txt
└── README.md
```

---

## Step 1: Data Ingestion Layer

### Kafka Setup on Kubernetes

```yaml
# k8s/kafka/kafka-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kafka
  namespace: aiops
spec:
  replicas: 1  # Use 3 for production
  selector:
    matchLabels:
      app: kafka
  template:
    metadata:
      labels:
        app: kafka
    spec:
      containers:
      - name: kafka
        image: confluentinc/cp-kafka:7.5.0
        ports:
        - containerPort: 9092
        env:
        - name: KAFKA_BROKER_ID
          value: "1"
        - name: KAFKA_ZOOKEEPER_CONNECT
          value: "zookeeper:2181"
        - name: KAFKA_ADVERTISED_LISTENERS
          value: "PLAINTEXT://kafka:9092"
        - name: KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR
          value: "1"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: kafka
  namespace: aiops
spec:
  ports:
  - port: 9092
  selector:
    app: kafka
```

### Prometheus Metrics Exporter

```python
# src/common/prometheus_client.py
"""
Export Prometheus metrics to Kafka for AIOps processing.
"""
import json
import time
from datetime import datetime
from kafka import KafkaProducer
from prometheus_api_client import PrometheusConnect

class PrometheusExporter:
    """Export Prometheus metrics to Kafka."""

    def __init__(
        self,
        prometheus_url: str,
        kafka_bootstrap: str,
        topic: str = "metrics"
    ):
        self.prom = PrometheusConnect(url=prometheus_url)
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_bootstrap,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        self.topic = topic

    def export_metrics(self, queries: list[dict]):
        """
        Export metrics to Kafka.

        Args:
            queries: List of {"name": str, "query": str} dicts
        """
        timestamp = datetime.utcnow().isoformat()

        for query_def in queries:
            try:
                result = self.prom.custom_query(query_def["query"])

                for metric in result:
                    message = {
                        "timestamp": timestamp,
                        "name": query_def["name"],
                        "labels": metric["metric"],
                        "value": float(metric["value"][1])
                    }
                    self.producer.send(self.topic, message)

            except Exception as e:
                print(f"Error exporting {query_def['name']}: {e}")

        self.producer.flush()

    def run_continuous(self, queries: list[dict], interval: int = 60):
        """Run continuous export."""
        while True:
            self.export_metrics(queries)
            time.sleep(interval)


# Configuration
METRICS_TO_EXPORT = [
    {
        "name": "http_request_duration_p99",
        "query": "histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))"
    },
    {
        "name": "http_request_rate",
        "query": "sum(rate(http_requests_total[5m])) by (service)"
    },
    {
        "name": "error_rate",
        "query": "sum(rate(http_requests_total{status=~'5..'}[5m])) by (service) / sum(rate(http_requests_total[5m])) by (service)"
    },
    {
        "name": "cpu_usage",
        "query": "avg(rate(container_cpu_usage_seconds_total[5m])) by (pod)"
    },
    {
        "name": "memory_usage",
        "query": "avg(container_memory_usage_bytes) by (pod)"
    }
]

if __name__ == "__main__":
    exporter = PrometheusExporter(
        prometheus_url="http://prometheus:9090",
        kafka_bootstrap="kafka:9092"
    )
    exporter.run_continuous(METRICS_TO_EXPORT, interval=60)
```

---

## Step 2: Anomaly Detection Service

### Main Detection Service

```python
# src/detector/main.py
"""
Anomaly Detection Service

Consumes metrics from Kafka, detects anomalies, publishes to anomalies topic.
"""
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
from kafka import KafkaConsumer, KafkaProducer
from .detectors.prophet_detector import ProphetDetector
from .detectors.isolation_forest import IsolationForestDetector
from .detectors.luminaire_detector import LuminaireDetector
from .config import Config

class AnomalyDetectionService:
    """Main anomaly detection service."""

    def __init__(self, config: Config):
        self.config = config

        # Kafka setup
        self.consumer = KafkaConsumer(
            config.metrics_topic,
            bootstrap_servers=config.kafka_bootstrap,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id="anomaly-detector",
            auto_offset_reset="latest"
        )

        self.producer = KafkaProducer(
            bootstrap_servers=config.kafka_bootstrap,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

        # Detectors
        self.detectors = {
            "prophet": ProphetDetector(),
            "isolation_forest": IsolationForestDetector(),
            "luminaire": LuminaireDetector()
        }

        # Metric history for batch detection
        self.metric_history: dict[str, list] = defaultdict(list)
        self.history_window = timedelta(hours=24)

    def get_metric_key(self, metric: dict) -> str:
        """Generate unique key for metric series."""
        labels = metric.get("labels", {})
        sorted_labels = sorted(labels.items())
        return f"{metric['name']}:{sorted_labels}"

    def add_to_history(self, metric: dict):
        """Add metric to history buffer."""
        key = self.get_metric_key(metric)
        self.metric_history[key].append({
            "timestamp": metric["timestamp"],
            "value": metric["value"]
        })

        # Trim old data
        cutoff = datetime.utcnow() - self.history_window
        self.metric_history[key] = [
            m for m in self.metric_history[key]
            if datetime.fromisoformat(m["timestamp"]) > cutoff
        ]

    def detect_anomaly(self, metric: dict) -> dict | None:
        """
        Run anomaly detection on metric.

        Returns anomaly dict if detected, None otherwise.
        """
        key = self.get_metric_key(metric)
        history = self.metric_history[key]

        if len(history) < self.config.min_history_points:
            return None

        # Choose detector based on metric type
        detector_name = self.config.metric_detector_map.get(
            metric["name"],
            "isolation_forest"  # default
        )
        detector = self.detectors[detector_name]

        # Run detection
        is_anomaly, score, details = detector.detect(
            history,
            metric["value"]
        )

        if is_anomaly:
            return {
                "timestamp": metric["timestamp"],
                "metric_name": metric["name"],
                "metric_labels": metric.get("labels", {}),
                "value": metric["value"],
                "anomaly_score": score,
                "detector": detector_name,
                "details": details
            }

        return None

    def run(self):
        """Main processing loop."""
        print("Starting Anomaly Detection Service...")

        for message in self.consumer:
            metric = message.value

            # Add to history
            self.add_to_history(metric)

            # Detect anomalies
            anomaly = self.detect_anomaly(metric)

            if anomaly:
                print(f"Anomaly detected: {anomaly['metric_name']}")
                self.producer.send(
                    self.config.anomalies_topic,
                    anomaly
                )
                self.producer.flush()


if __name__ == "__main__":
    config = Config.from_env()
    service = AnomalyDetectionService(config)
    service.run()
```

### Prophet Detector Implementation

```python
# src/detector/detectors/prophet_detector.py
"""
Prophet-based anomaly detector for metrics with seasonality.
"""
import pandas as pd
from prophet import Prophet

class ProphetDetector:
    """Anomaly detection using Facebook Prophet."""

    def __init__(
        self,
        seasonality_mode: str = "multiplicative",
        interval_width: float = 0.95
    ):
        self.seasonality_mode = seasonality_mode
        self.interval_width = interval_width
        self.models: dict = {}

    def detect(
        self,
        history: list[dict],
        current_value: float
    ) -> tuple[bool, float, dict]:
        """
        Detect if current value is anomalous.

        Returns:
            (is_anomaly, score, details)
        """
        if len(history) < 100:
            return False, 0.0, {"reason": "insufficient_data"}

        # Prepare data for Prophet
        df = pd.DataFrame(history)
        df.columns = ["ds", "y"]
        df["ds"] = pd.to_datetime(df["ds"])

        # Train Prophet model
        model = Prophet(
            seasonality_mode=self.seasonality_mode,
            interval_width=self.interval_width,
            daily_seasonality=True,
            weekly_seasonality=True
        )
        model.fit(df)

        # Get forecast for current point
        future = model.make_future_dataframe(periods=1, freq="min")
        forecast = model.predict(future)
        last_row = forecast.iloc[-1]

        # Check if current value is outside confidence interval
        lower = last_row["yhat_lower"]
        upper = last_row["yhat_upper"]
        expected = last_row["yhat"]

        is_anomaly = current_value < lower or current_value > upper

        # Calculate anomaly score (how far outside the interval)
        if is_anomaly:
            if current_value < lower:
                score = (lower - current_value) / (upper - lower)
            else:
                score = (current_value - upper) / (upper - lower)
        else:
            score = 0.0

        details = {
            "expected": expected,
            "lower_bound": lower,
            "upper_bound": upper,
            "deviation": current_value - expected
        }

        return is_anomaly, min(score, 1.0), details
```

### Isolation Forest Detector

```python
# src/detector/detectors/isolation_forest.py
"""
Isolation Forest anomaly detector for high-dimensional data.
"""
import numpy as np
from sklearn.ensemble import IsolationForest

class IsolationForestDetector:
    """Anomaly detection using Isolation Forest."""

    def __init__(
        self,
        contamination: float = 0.01,
        n_estimators: int = 100
    ):
        self.contamination = contamination
        self.n_estimators = n_estimators

    def detect(
        self,
        history: list[dict],
        current_value: float
    ) -> tuple[bool, float, dict]:
        """
        Detect if current value is anomalous.

        Returns:
            (is_anomaly, score, details)
        """
        if len(history) < 50:
            return False, 0.0, {"reason": "insufficient_data"}

        # Extract values
        values = np.array([h["value"] for h in history]).reshape(-1, 1)
        current = np.array([[current_value]])

        # Train Isolation Forest
        model = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            random_state=42
        )
        model.fit(values)

        # Predict
        prediction = model.predict(current)[0]
        score = -model.decision_function(current)[0]  # Higher = more anomalous

        is_anomaly = prediction == -1

        # Calculate statistics for context
        mean = np.mean(values)
        std = np.std(values)
        z_score = (current_value - mean) / std if std > 0 else 0

        details = {
            "mean": float(mean),
            "std": float(std),
            "z_score": float(z_score),
            "isolation_score": float(score)
        }

        return is_anomaly, min(abs(score), 1.0), details
```

---

## Step 3: Event Correlation Service

```python
# src/correlator/main.py
"""
Event Correlation Service

Consumes anomalies from Kafka, correlates related events, creates incidents.
"""
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
from kafka import KafkaConsumer, KafkaProducer
from .correlators.time_based import TimeBasedCorrelator
from .correlators.topology_based import TopologyBasedCorrelator
from .correlators.text_based import TextBasedCorrelator
from .config import Config

class EventCorrelationService:
    """Main event correlation service."""

    def __init__(self, config: Config):
        self.config = config

        # Kafka setup
        self.consumer = KafkaConsumer(
            config.anomalies_topic,
            bootstrap_servers=config.kafka_bootstrap,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id="event-correlator",
            auto_offset_reset="latest"
        )

        self.producer = KafkaProducer(
            bootstrap_servers=config.kafka_bootstrap,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

        # Correlators
        self.time_correlator = TimeBasedCorrelator(
            window_seconds=config.correlation_window
        )
        self.topology_correlator = TopologyBasedCorrelator(
            topology_file=config.topology_file
        )
        self.text_correlator = TextBasedCorrelator()

        # Active incidents
        self.active_incidents: dict = {}
        self.incident_counter = 0

    def correlate_event(self, anomaly: dict) -> str | None:
        """
        Try to correlate anomaly with existing incident.

        Returns incident_id if correlated, None otherwise.
        """
        for incident_id, incident in self.active_incidents.items():
            # Time correlation
            if self.time_correlator.correlates(anomaly, incident["events"]):
                return incident_id

            # Topology correlation
            if self.topology_correlator.correlates(anomaly, incident["events"]):
                return incident_id

            # Text similarity
            if self.text_correlator.correlates(anomaly, incident["events"]):
                return incident_id

        return None

    def create_incident(self, anomaly: dict) -> str:
        """Create new incident from anomaly."""
        self.incident_counter += 1
        incident_id = f"INC-{self.incident_counter:06d}"

        self.active_incidents[incident_id] = {
            "id": incident_id,
            "created_at": anomaly["timestamp"],
            "updated_at": anomaly["timestamp"],
            "status": "open",
            "severity": self.calculate_severity(anomaly),
            "events": [anomaly],
            "root_cause": None
        }

        return incident_id

    def add_to_incident(self, incident_id: str, anomaly: dict):
        """Add anomaly to existing incident."""
        incident = self.active_incidents[incident_id]
        incident["events"].append(anomaly)
        incident["updated_at"] = anomaly["timestamp"]

        # Recalculate severity
        incident["severity"] = max(
            incident["severity"],
            self.calculate_severity(anomaly)
        )

        # Try to identify root cause
        if len(incident["events"]) >= 3:
            incident["root_cause"] = self.identify_root_cause(
                incident["events"]
            )

    def calculate_severity(self, anomaly: dict) -> int:
        """Calculate severity (1-5) based on anomaly."""
        score = anomaly.get("anomaly_score", 0)

        if score > 0.9:
            return 5  # Critical
        elif score > 0.7:
            return 4  # High
        elif score > 0.5:
            return 3  # Medium
        elif score > 0.3:
            return 2  # Low
        else:
            return 1  # Info

    def identify_root_cause(self, events: list[dict]) -> dict | None:
        """
        Identify probable root cause from correlated events.
        """
        if not events:
            return None

        # Sort by timestamp
        sorted_events = sorted(events, key=lambda e: e["timestamp"])

        # First event is often the root cause
        first_event = sorted_events[0]

        # Look for infrastructure-level events
        infra_events = [
            e for e in sorted_events
            if any(k in e.get("metric_name", "").lower()
                   for k in ["cpu", "memory", "disk", "network"])
        ]

        if infra_events:
            root_event = infra_events[0]
        else:
            root_event = first_event

        return {
            "event": root_event,
            "confidence": 0.7,  # Would use ML in production
            "reasoning": "First occurring event in correlation window"
        }

    def publish_incident(self, incident_id: str):
        """Publish incident to Kafka."""
        incident = self.active_incidents[incident_id]
        self.producer.send(self.config.incidents_topic, incident)
        self.producer.flush()

    def cleanup_old_incidents(self):
        """Close incidents that haven't had events recently."""
        cutoff = datetime.utcnow() - timedelta(
            minutes=self.config.incident_timeout_minutes
        )

        for incident_id, incident in list(self.active_incidents.items()):
            last_update = datetime.fromisoformat(incident["updated_at"])
            if last_update < cutoff:
                incident["status"] = "resolved"
                self.publish_incident(incident_id)
                del self.active_incidents[incident_id]

    def run(self):
        """Main processing loop."""
        print("Starting Event Correlation Service...")

        for message in self.consumer:
            anomaly = message.value

            # Try to correlate with existing incident
            incident_id = self.correlate_event(anomaly)

            if incident_id:
                self.add_to_incident(incident_id, anomaly)
                print(f"Added to incident: {incident_id}")
            else:
                incident_id = self.create_incident(anomaly)
                print(f"Created incident: {incident_id}")

            # Publish updated incident
            self.publish_incident(incident_id)

            # Periodic cleanup
            self.cleanup_old_incidents()


if __name__ == "__main__":
    config = Config.from_env()
    service = EventCorrelationService(config)
    service.run()
```

---

## Step 4: Incident Manager Service

```python
# src/incident_manager/main.py
"""
Incident Manager Service

Consumes incidents from Kafka, takes actions (alert, remediate).
"""
import json
import os
from kafka import KafkaConsumer
from .actions.pagerduty import PagerDutyAction
from .actions.slack import SlackAction
from .actions.remediation import RemediationAction
from .config import Config

class IncidentManagerService:
    """Main incident management service."""

    def __init__(self, config: Config):
        self.config = config

        # Kafka setup
        self.consumer = KafkaConsumer(
            config.incidents_topic,
            bootstrap_servers=config.kafka_bootstrap,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id="incident-manager",
            auto_offset_reset="latest"
        )

        # Actions
        self.pagerduty = PagerDutyAction(config.pagerduty_key)
        self.slack = SlackAction(config.slack_webhook)
        self.remediation = RemediationAction(config.runbook_dir)

        # Track notified incidents
        self.notified_incidents: set = set()

    def should_alert(self, incident: dict) -> bool:
        """Determine if incident should trigger alert."""
        # Only alert on new or escalated incidents
        if incident["id"] in self.notified_incidents:
            # Check for escalation
            return incident["severity"] >= 4

        return incident["severity"] >= 3

    def should_remediate(self, incident: dict) -> bool:
        """Determine if auto-remediation should run."""
        if not self.config.auto_remediation_enabled:
            return False

        # Only auto-remediate known issues
        if not incident.get("root_cause"):
            return False

        # Check if runbook exists
        root_cause_type = self.get_root_cause_type(incident)
        return self.remediation.has_runbook(root_cause_type)

    def get_root_cause_type(self, incident: dict) -> str:
        """Extract root cause type for runbook matching."""
        root_cause = incident.get("root_cause", {})
        event = root_cause.get("event", {})
        return event.get("metric_name", "unknown")

    def handle_incident(self, incident: dict):
        """Process incident and take appropriate actions."""

        # Always notify Slack for visibility
        self.slack.send(incident)

        # Alert on-call if severity warrants
        if self.should_alert(incident):
            self.pagerduty.create_incident(incident)
            self.notified_incidents.add(incident["id"])

        # Auto-remediate if possible
        if self.should_remediate(incident):
            root_cause_type = self.get_root_cause_type(incident)
            result = self.remediation.execute(root_cause_type, incident)

            # Notify about remediation
            self.slack.send_remediation_result(incident, result)

    def run(self):
        """Main processing loop."""
        print("Starting Incident Manager Service...")

        for message in self.consumer:
            incident = message.value

            print(f"Processing incident: {incident['id']}")
            self.handle_incident(incident)


if __name__ == "__main__":
    config = Config.from_env()
    service = IncidentManagerService(config)
    service.run()
```

### Slack Action

```python
# src/incident_manager/actions/slack.py
"""
Slack notification action.
"""
import requests

class SlackAction:
    """Send notifications to Slack."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send(self, incident: dict):
        """Send incident notification to Slack."""
        severity_emoji = {
            1: "ℹ️",
            2: "⚠️",
            3: "🟠",
            4: "🔴",
            5: "🚨"
        }

        emoji = severity_emoji.get(incident["severity"], "❓")
        event_count = len(incident["events"])

        # Build message
        message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} Incident: {incident['id']}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Severity:* {incident['severity']}/5"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Events:* {event_count}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Status:* {incident['status']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Created:* {incident['created_at']}"
                        }
                    ]
                }
            ]
        }

        # Add root cause if identified
        if incident.get("root_cause"):
            rc = incident["root_cause"]
            message["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Probable Root Cause:* {rc['event']['metric_name']}\n"
                            f"Confidence: {rc['confidence']*100:.0f}%"
                }
            })

        requests.post(self.webhook_url, json=message)

    def send_remediation_result(self, incident: dict, result: dict):
        """Send remediation result to Slack."""
        status = "✅ Success" if result["success"] else "❌ Failed"

        message = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Auto-Remediation {status}*\n"
                                f"Incident: {incident['id']}\n"
                                f"Action: {result['action']}\n"
                                f"Output: ```{result.get('output', 'N/A')}```"
                    }
                }
            ]
        }

        requests.post(self.webhook_url, json=message)
```

---

## Step 5: Kubernetes Deployment

```yaml
# k8s/aiops/detector-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: anomaly-detector
  namespace: aiops
  labels:
    app: anomaly-detector
spec:
  replicas: 2
  selector:
    matchLabels:
      app: anomaly-detector
  template:
    metadata:
      labels:
        app: anomaly-detector
    spec:
      containers:
      - name: detector
        image: your-registry/anomaly-detector:latest
        env:
        - name: KAFKA_BOOTSTRAP
          value: "kafka:9092"
        - name: METRICS_TOPIC
          value: "metrics"
        - name: ANOMALIES_TOPIC
          value: "anomalies"
        - name: MIN_HISTORY_POINTS
          value: "100"
        envFrom:
        - configMapRef:
            name: aiops-config
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: event-correlator
  namespace: aiops
  labels:
    app: event-correlator
spec:
  replicas: 1  # Single instance for correlation consistency
  selector:
    matchLabels:
      app: event-correlator
  template:
    metadata:
      labels:
        app: event-correlator
    spec:
      containers:
      - name: correlator
        image: your-registry/event-correlator:latest
        env:
        - name: KAFKA_BOOTSTRAP
          value: "kafka:9092"
        - name: ANOMALIES_TOPIC
          value: "anomalies"
        - name: INCIDENTS_TOPIC
          value: "incidents"
        - name: CORRELATION_WINDOW
          value: "300"
        envFrom:
        - configMapRef:
            name: aiops-config
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "250m"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: incident-manager
  namespace: aiops
  labels:
    app: incident-manager
spec:
  replicas: 1
  selector:
    matchLabels:
      app: incident-manager
  template:
    metadata:
      labels:
        app: incident-manager
    spec:
      containers:
      - name: manager
        image: your-registry/incident-manager:latest
        env:
        - name: KAFKA_BOOTSTRAP
          value: "kafka:9092"
        - name: INCIDENTS_TOPIC
          value: "incidents"
        envFrom:
        - secretRef:
            name: aiops-secrets
        - configMapRef:
            name: aiops-config
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "250m"
```

### ConfigMap and Secrets

```yaml
# k8s/aiops/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: aiops-config
  namespace: aiops
data:
  AUTO_REMEDIATION_ENABLED: "true"
  INCIDENT_TIMEOUT_MINUTES: "30"
  RUNBOOK_DIR: "/etc/runbooks"

---
# k8s/aiops/secrets.yaml (use sealed-secrets or external-secrets in production)
apiVersion: v1
kind: Secret
metadata:
  name: aiops-secrets
  namespace: aiops
type: Opaque
stringData:
  PAGERDUTY_KEY: "your-pagerduty-integration-key"
  SLACK_WEBHOOK: "https://hooks.slack.com/services/xxx/xxx/xxx"
```

---

## Common Mistakes

| Mistake | Impact | Solution |
|---------|--------|----------|
| Training on too little data | High false positive rate | Wait for 2+ weeks of data before alerting |
| Not handling concept drift | Degraded accuracy over time | Retrain models regularly or use online learning |
| Single point of failure | Complete AIOps outage | Deploy with replicas, handle Kafka partitions |
| Ignoring seasonality | Weekend/holiday false positives | Use Prophet or similar for seasonal metrics |
| Alert on every anomaly | Alert fatigue | Require correlation before alerting |
| No observability for AIOps | Blind to AIOps issues | Monitor your monitoring |

---

## Quiz

Test your understanding of building custom AIOps:

### Question 1
Why use Kafka between pipeline stages?

<details>
<summary>Show Answer</summary>

Kafka provides:
1. **Decoupling** — Services can scale independently
2. **Durability** — Messages persist if consumers are down
3. **Replay** — Can reprocess historical data
4. **Backpressure** — Handles traffic spikes gracefully
5. **Multiple consumers** — Same data feeds multiple services
</details>

### Question 2
Why does the correlator run as a single replica?

<details>
<summary>Show Answer</summary>

Event correlation requires **global state** to group related events. With multiple replicas, different anomalies might go to different instances, breaking correlation.

Solutions for scaling:
- Partition by service/region to isolate correlation domains
- Use distributed state (Redis) for shared correlation state
- Accept eventual consistency with cross-instance sync
</details>

### Question 3
What's the minimum data needed before anomaly detection works?

<details>
<summary>Show Answer</summary>

It depends on the algorithm:
- **Prophet**: 100+ data points covering at least one full seasonal cycle (1 week minimum for weekly patterns)
- **Isolation Forest**: 50+ data points for reasonable baseline
- **Luminaire**: 50+ points for structural break detection

Best practice: Wait 2+ weeks before enabling alerting to avoid false positives during the learning period.
</details>

---

## Hands-On Exercise

### Objective
Build a minimal custom AIOps pipeline using Python and Docker.

### Exercise: Local AIOps Pipeline

**Step 1: Create Project Structure**

```bash
mkdir custom-aiops && cd custom-aiops
mkdir -p src/detector src/correlator
touch docker-compose.yml
touch src/detector/main.py src/correlator/main.py
touch requirements.txt
```

**Step 2: Create docker-compose.yml**

```yaml
version: '3.8'
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1

  detector:
    build:
      context: .
      dockerfile: Dockerfile.detector
    depends_on:
      - kafka
    environment:
      KAFKA_BOOTSTRAP: kafka:29092

  correlator:
    build:
      context: .
      dockerfile: Dockerfile.correlator
    depends_on:
      - kafka
    environment:
      KAFKA_BOOTSTRAP: kafka:29092
```

**Step 3: Create Minimal Detector**

```python
# src/detector/main.py
import json
import random
import time
from kafka import KafkaProducer, KafkaConsumer
import numpy as np

def create_detector():
    producer = KafkaProducer(
        bootstrap_servers='kafka:29092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    # Simulate metrics and detect anomalies
    baseline = 100
    history = []

    while True:
        # Generate metric (occasionally anomalous)
        if random.random() < 0.05:  # 5% anomaly rate
            value = baseline * random.uniform(2, 5)
            is_anomaly = True
        else:
            value = baseline + random.gauss(0, 10)
            is_anomaly = False

        history.append(value)
        if len(history) > 100:
            history.pop(0)

        # Simple z-score detection
        if len(history) >= 20:
            mean = np.mean(history)
            std = np.std(history)
            z_score = abs(value - mean) / std if std > 0 else 0

            if z_score > 3:
                anomaly = {
                    "timestamp": time.time(),
                    "metric": "cpu_usage",
                    "value": value,
                    "z_score": z_score
                }
                producer.send('anomalies', anomaly)
                print(f"Anomaly detected: {anomaly}")

        time.sleep(1)

if __name__ == "__main__":
    time.sleep(10)  # Wait for Kafka
    create_detector()
```

**Step 4: Run the Pipeline**

```bash
docker-compose up --build
```

### Success Criteria
- [ ] Kafka cluster running
- [ ] Detector producing anomalies to Kafka
- [ ] Can consume anomalies from Kafka topic
- [ ] Understand the data flow

---

## Key Takeaways

1. **Start with platforms** — Build custom only when platform AI doesn't fit
2. **Kafka is the backbone** — Decouples services, provides durability
3. **Correlation is hard** — Single-instance or distributed state required
4. **Models need data** — Wait 2+ weeks before alerting
5. **Monitor your monitoring** — AIOps needs observability too

---

## Further Reading

### Open Source AIOps Projects
- [LinkedIn ThirdEye](https://github.com/linkedin/thirdeye) — Open-source anomaly detection
- [Netflix Surus](https://github.com/Netflix/Surus) — Collection of anomaly detection tools
- [Apache Flink](https://flink.apache.org/) — Stream processing for real-time ML

### Building ML Systems
- [Designing Machine Learning Systems](https://www.oreilly.com/library/view/designing-machine-learning/9781098107956/) — Chip Huyen
- [Machine Learning Engineering](http://www.mlebook.com/) — Andriy Burkov
- [Reliable Machine Learning](https://www.oreilly.com/library/view/reliable-machine-learning/9781098106218/) — O'Reilly

### Kafka and Streaming
- [Kafka: The Definitive Guide](https://www.confluent.io/resources/kafka-the-definitive-guide-v2/) — Confluent
- [Streaming Systems](https://www.oreilly.com/library/view/streaming-systems/9781491983867/) — O'Reilly

---

## Summary

Building custom AIOps is a significant investment requiring Kafka for data flow, Python ML libraries for detection, and Kubernetes for deployment. The architecture follows a pipeline pattern: ingest → detect → correlate → act. Start with platform AI and build custom only when you have unique requirements that justify the engineering effort. When you do build custom, ensure you have sufficient data, handle concept drift, and monitor your monitoring.

---

## Toolkit Complete

Congratulations! You've completed the AIOps Tools Toolkit. You now understand:

- **Anomaly Detection Tools** — Prophet, Luminaire, PyOD
- **Event Correlation Platforms** — BigPanda, Moogsoft, PagerDuty
- **Observability AI Features** — Datadog Watchdog, Dynatrace Davis
- **Building Custom AIOps** — Python + Kafka + Kubernetes pipelines

Continue your learning:
- [AIOps Discipline](../../../disciplines/data-ai/aiops/) — Deepen conceptual understanding
- [Observability Toolkit](../observability/) — The data collection layer
- [SRE Discipline](../../../disciplines/core-platform/sre/) — Apply AIOps to reliability
