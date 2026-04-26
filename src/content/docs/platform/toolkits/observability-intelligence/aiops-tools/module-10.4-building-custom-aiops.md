---
title: "Module 10.4: Building Custom AIOps"
slug: platform/toolkits/observability-intelligence/aiops-tools/module-10.4-building-custom-aiops
sidebar:
  order: 5
---

# Module 10.4: Building Custom AIOps

> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 60-75 minutes

## Prerequisites

Before starting this module, you should be comfortable reading PromQL queries, interpreting Kubernetes workload health, and writing small Python services that process structured data. You do not need to be a machine learning specialist, but you should understand the difference between a training baseline, a prediction, and a false positive.

You should complete these first:

- [AIOps Discipline](/platform/disciplines/data-ai/aiops/) — Conceptual foundation for automation, signal quality, and operational decision support
- [Module 10.1: Anomaly Detection Tools](../module-10.1-anomaly-detection-tools/) — Detection approaches and algorithm trade-offs
- [Module 10.2: Event Correlation Platforms](../module-10.2-event-correlation-platforms/) — Correlation, grouping, and incident reduction patterns
- [Module 10.3: Observability AI Features](../module-10.3-observability-ai-features/) — Commercial platform capabilities and their limits
- Python basics, including virtual environments, dictionaries, lists, and reading JSON files
- Kubernetes basics, including Deployments, Services, ConfigMaps, Secrets, and container health probes
- Kafka or another event-streaming platform at a conceptual level

## Learning Outcomes

After completing this module, you will be able to:

- **Design** a custom AIOps pipeline that separates ingestion, feature engineering, anomaly detection, correlation, and action stages.
- **Implement** a runnable Python baseline detector that turns metric samples into anomaly events with enough context for later correlation.
- **Evaluate** whether a team should build custom AIOps or buy a platform feature based on data volume, domain specificity, operational risk, and staffing.
- **Debug** common failure modes in custom AIOps systems, including noisy models, broken ordering, missing topology, and unsafe remediation.
- **Compare** deployment patterns for stateless detectors, stateful correlators, feedback loops, and Kubernetes runtime controls.

## Why This Module Matters

At 02:13, a checkout team sees latency rise, payment retries spike, and inventory reservations drift upward. The commercial observability platform opens three alerts, the log tool highlights two suspicious deploys, and the tracing dashboard shows pressure across half the request path. No individual signal is wrong, but none of them explains the incident quickly enough for the incident commander to choose the first fix.

This is the moment where custom AIOps becomes tempting. The team already owns rich domain knowledge: payment authorization is allowed to slow down during bank maintenance windows, inventory errors are more dangerous during flash sales, and a cache miss surge is only critical when it aligns with a specific checkout funnel. A general-purpose tool can detect abnormal behavior, but it may not know which abnormal behavior matters to this business at this hour.

Custom AIOps is not a badge of maturity by itself. It is a product you build for your own operations, and it inherits the same obligations as any production service: reliability, versioning, observability, rollback, security, and user feedback. The goal is not to sprinkle machine learning over alerts; the goal is to turn operational data into faster, safer decisions that engineers trust under pressure.

A senior platform engineer treats custom AIOps as a socio-technical system. The pipeline must handle data quality, model quality, human review, incident workflow, and failure isolation. If any one of those layers is ignored, the model can become a high-speed noise generator that looks sophisticated while making on-call life worse.

## 1. Decide Whether Custom AIOps Is Worth Building

Most teams should not start by building custom AIOps. Commercial platforms, open-source detectors, and simpler alert hygiene usually solve the first wave of operational intelligence problems at lower cost. Building custom becomes reasonable only when the team can name the specific decision that existing tools cannot support, and when that decision is valuable enough to justify owning a new production system.

The first design question is therefore not "Which model should we use?" The first question is "What operational decision will this system improve?" A useful answer sounds concrete: "When checkout latency rises, identify whether the likely root cause is payment provider latency, inventory write contention, or a recent deployment within two minutes." A weak answer sounds vague: "Use AI to improve incident response."

A custom AIOps system usually earns its keep in one of four situations. The first is domain-specific behavior, where the important signal depends on business context that a generic tool does not know. The second is data sovereignty, where raw telemetry cannot leave controlled infrastructure. The third is scale economics, where platform pricing or query limits make deep analysis expensive. The fourth is workflow integration, where the output must drive internal runbooks, approval gates, or remediation systems that commercial tools cannot safely control.

```text
BUILD-VERSUS-BUY DECISION PATH

┌────────────────────────────────────────────────────────────────────┐
│ Start with the operational decision, not the model.                 │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│ Can an existing platform detect the condition with acceptable       │
│ latency, context, precision, and cost?                              │
└────────────────────────────────────────────────────────────────────┘
              │ Yes                                      │ No
              ▼                                          ▼
┌──────────────────────────────┐          ┌───────────────────────────┐
│ Buy, configure, and improve   │          │ Is the missing context     │
│ alert hygiene first.          │          │ specific to your domain?   │
└──────────────────────────────┘          └───────────────────────────┘
                                                        │
                                                        ▼
                                      ┌────────────────────────────────┐
                                      │ Do you have owners for data,    │
                                      │ models, runtime, and feedback?  │
                                      └────────────────────────────────┘
                                               │ Yes          │ No
                                               ▼              ▼
                              ┌────────────────────────┐  ┌────────────────────┐
                              │ Build a narrow custom  │  │ Fix ownership and  │
                              │ pipeline with rollback │  │ data maturity first│
                              │ and human review.      │  │ before building.   │
                              └────────────────────────┘  └────────────────────┘
```

> **Stop and think:** Your organization has a noisy CPU alert that pages too often. Is that evidence that you need custom AIOps, or is it evidence that the alert policy and service ownership model need repair first? Write down the decision the system would improve before choosing a tool.

A practical rule is to start with a narrow use case where false positives and false negatives can be reviewed by humans. Do not begin with automatic remediation across the whole cluster. Begin with one service family, one high-value symptom, one correlation path, and one clear feedback workflow. This keeps the first version understandable enough that engineers can inspect it during an incident.

The build decision also has a staffing side. A custom AIOps platform needs people who can maintain streaming infrastructure, Kubernetes workloads, Python services, data contracts, model evaluation, and incident integrations. If the team cannot commit to those responsibilities, a commercial feature with weaker customization may still be the safer engineering choice.

## 2. Design the Pipeline Around Data Contracts

A custom AIOps pipeline is easier to reason about when each stage has one job and a clear contract. Ingestion collects signals, feature engineering reshapes them, detection scores unusual behavior, correlation groups related events, incident management chooses human or automated action, and feedback records whether the system helped. This separation lets you scale and debug stages independently.

The architecture below is intentionally ordinary. Kafka is not magic; it is a durable buffer and replay mechanism between services that should not fail together. Python is not magic either; it is a convenient runtime for feature engineering and model libraries. Kubernetes provides deployment, restart, configuration, and resource controls. The value comes from the contracts between these pieces, not from any single tool.

```text
CUSTOM AIOPS ARCHITECTURE ON KUBERNETES

DATA SOURCES                         INGESTION AND CONTRACTS
┌──────────────────┐                 ┌───────────────────────────────┐
│ Prometheus       │ metrics query   │ topic: raw.metrics             │
│ Loki             │ log events      │ topic: raw.logs                │
│ Tempo            │ trace spans     │ topic: raw.traces              │
│ Kubernetes API   │ object events   │ topic: raw.k8s_events          │
└────────┬─────────┘                 └──────────────┬────────────────┘
         │                                          │
         ▼                                          ▼
┌────────────────────────────────────────────────────────────────────┐
│ FEATURE ENGINEERING                                                 │
│ Normalize timestamps, attach service ownership, calculate rates,    │
│ join deployment metadata, suppress invalid samples, emit features.  │
│ topic: features.service_health                                      │
└───────────────────────────────┬────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│ DETECTION                                                           │
│ Score feature windows with statistical rules, seasonal models,      │
│ or trained detectors. Emit anomaly candidates with evidence.        │
│ topic: aiops.anomalies                                             │
└───────────────────────────────┬────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│ CORRELATION AND ROOT-CAUSE HYPOTHESIS                               │
│ Group candidates by time, topology, ownership, deploy history,      │
│ and dependency direction. Emit incidents with confidence scores.    │
│ topic: aiops.incidents                                             │
└───────────────────────────────┬────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│ ACTION AND FEEDBACK                                                 │
│ Notify humans, attach runbooks, gate remediation, collect review,   │
│ and feed labels back into future evaluation.                        │
└────────────────────────────────────────────────────────────────────┘
```

The most important design artifact is the event schema. If every stage invents its own fields, correlation becomes guesswork and feedback becomes almost impossible. At minimum, anomaly events need a timestamp, service identity, metric name, observed value, expected range or baseline, detector name, score, window, and labels that connect the event to ownership and topology.

A schema does not need to be complicated at the beginning. The following JSON example is small enough to read during an incident but structured enough for later automation. Notice that it carries both the score and the evidence behind the score. A responder should be able to tell whether the model reacted to a latency spike, a drop in traffic, a deployment, or a missing sample.

```json
{
  "schema_version": "1.0",
  "event_type": "anomaly",
  "timestamp": "2026-04-26T01:20:30Z",
  "service": "checkout-api",
  "namespace": "commerce",
  "metric_name": "http_request_duration_p99",
  "window_seconds": 300,
  "value": 1.83,
  "expected": 0.42,
  "lower_bound": 0.18,
  "upper_bound": 0.91,
  "anomaly_score": 0.88,
  "detector": "seasonal_baseline",
  "labels": {
    "team": "checkout",
    "region": "us-east",
    "tier": "critical"
  },
  "evidence": {
    "sample_count": 300,
    "baseline_days": 14,
    "recent_deploy": "checkout-api-2026.04.26-1",
    "missing_samples": 0
  }
}
```

A senior implementation treats this schema as a contract. Producers validate it before publishing, consumers reject invalid messages safely, and version changes are rolled out deliberately. Without that discipline, the model may work in a notebook while the production pipeline silently drops context that correlation depends on.

> **Stop and think:** If the `service` field is missing from an anomaly event, which later stages become unreliable? Consider correlation, routing, runbook selection, ownership, and feedback before reading on.

Missing service identity breaks more than routing. The correlator cannot attach topology, the incident manager cannot choose the right on-call policy, the feedback loop cannot learn which detector performs poorly for which team, and dashboards cannot explain whether one service is noisy or many services are affected. AIOps quality often fails because of weak metadata, not weak math.

## 3. Build a Minimal Detector Before Adding Machine Learning

The safest first detector is usually not a complex model. A rolling baseline with explicit evidence is easier to validate, easier to explain, and easier to compare against future approaches. When a simple detector fails, the team learns what feature is missing; when a complex model fails, the team may only learn that nobody trusts it.

The worked example below reads metric samples from a JSON Lines file, calculates a rolling mean and standard deviation per service and metric, and emits anomaly events when a value moves far outside the recent baseline. It is intentionally local and runnable so you can study the mechanics without needing Kafka, Prometheus, or Kubernetes. This is the "I do" step before the exercise asks you to build a small pipeline yourself.

Create a file named `samples.jsonl`:

```json
{"timestamp":"2026-04-26T01:00:00Z","service":"checkout-api","namespace":"commerce","metric_name":"latency_p99","value":0.41}
{"timestamp":"2026-04-26T01:01:00Z","service":"checkout-api","namespace":"commerce","metric_name":"latency_p99","value":0.43}
{"timestamp":"2026-04-26T01:02:00Z","service":"checkout-api","namespace":"commerce","metric_name":"latency_p99","value":0.39}
{"timestamp":"2026-04-26T01:03:00Z","service":"checkout-api","namespace":"commerce","metric_name":"latency_p99","value":0.45}
{"timestamp":"2026-04-26T01:04:00Z","service":"checkout-api","namespace":"commerce","metric_name":"latency_p99","value":0.40}
{"timestamp":"2026-04-26T01:05:00Z","service":"checkout-api","namespace":"commerce","metric_name":"latency_p99","value":0.44}
{"timestamp":"2026-04-26T01:06:00Z","service":"checkout-api","namespace":"commerce","metric_name":"latency_p99","value":0.42}
{"timestamp":"2026-04-26T01:07:00Z","service":"checkout-api","namespace":"commerce","metric_name":"latency_p99","value":0.46}
{"timestamp":"2026-04-26T01:08:00Z","service":"checkout-api","namespace":"commerce","metric_name":"latency_p99","value":0.43}
{"timestamp":"2026-04-26T01:09:00Z","service":"checkout-api","namespace":"commerce","metric_name":"latency_p99","value":1.86}
{"timestamp":"2026-04-26T01:10:00Z","service":"catalog-api","namespace":"commerce","metric_name":"latency_p99","value":0.28}
{"timestamp":"2026-04-26T01:11:00Z","service":"catalog-api","namespace":"commerce","metric_name":"latency_p99","value":0.31}
{"timestamp":"2026-04-26T01:12:00Z","service":"catalog-api","namespace":"commerce","metric_name":"latency_p99","value":0.29}
{"timestamp":"2026-04-26T01:13:00Z","service":"catalog-api","namespace":"commerce","metric_name":"latency_p99","value":0.30}
{"timestamp":"2026-04-26T01:14:00Z","service":"catalog-api","namespace":"commerce","metric_name":"latency_p99","value":0.32}
{"timestamp":"2026-04-26T01:15:00Z","service":"catalog-api","namespace":"commerce","metric_name":"latency_p99","value":0.81}
```

Create a file named `rolling_detector.py`:

```python
#!/usr/bin/env python3
import argparse
import json
import statistics
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque


@dataclass(frozen=True)
class MetricSample:
    timestamp: str
    service: str
    namespace: str
    metric_name: str
    value: float

    @classmethod
    def from_json(cls, line: str) -> "MetricSample":
        data = json.loads(line)
        return cls(
            timestamp=data["timestamp"],
            service=data["service"],
            namespace=data["namespace"],
            metric_name=data["metric_name"],
            value=float(data["value"]),
        )


class RollingBaselineDetector:
    def __init__(self, window_size: int, min_points: int, z_threshold: float) -> None:
        self.window_size = window_size
        self.min_points = min_points
        self.z_threshold = z_threshold
        self.history: dict[str, Deque[float]] = defaultdict(lambda: deque(maxlen=window_size))

    def key_for(self, sample: MetricSample) -> str:
        return f"{sample.namespace}/{sample.service}/{sample.metric_name}"

    def score(self, sample: MetricSample) -> dict | None:
        key = self.key_for(sample)
        previous_values = list(self.history[key])
        self.history[key].append(sample.value)

        if len(previous_values) < self.min_points:
            return None

        mean = statistics.fmean(previous_values)
        stdev = statistics.pstdev(previous_values)
        z_score = 0.0 if stdev == 0 else abs(sample.value - mean) / stdev

        if z_score < self.z_threshold:
            return None

        direction = "high" if sample.value > mean else "low"
        return {
            "schema_version": "1.0",
            "event_type": "anomaly",
            "timestamp": sample.timestamp,
            "service": sample.service,
            "namespace": sample.namespace,
            "metric_name": sample.metric_name,
            "value": sample.value,
            "expected": round(mean, 4),
            "lower_bound": round(mean - (self.z_threshold * stdev), 4),
            "upper_bound": round(mean + (self.z_threshold * stdev), 4),
            "anomaly_score": round(min(z_score / self.z_threshold, 1.0), 4),
            "detector": "rolling_z_score",
            "evidence": {
                "window_size": self.window_size,
                "baseline_points": len(previous_values),
                "z_score": round(z_score, 4),
                "direction": direction,
            },
        }


def run(input_path: str, window_size: int, min_points: int, z_threshold: float) -> None:
    detector = RollingBaselineDetector(
        window_size=window_size,
        min_points=min_points,
        z_threshold=z_threshold,
    )

    with open(input_path, "r", encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            sample = MetricSample.from_json(line)
            anomaly = detector.score(sample)
            if anomaly is not None:
                print(json.dumps(anomaly, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Detect anomalies with a rolling baseline.")
    parser.add_argument("input_path", help="Path to a JSON Lines metric sample file.")
    parser.add_argument("--window-size", type=int, default=20)
    parser.add_argument("--min-points", type=int, default=5)
    parser.add_argument("--z-threshold", type=float, default=3.0)
    args = parser.parse_args()

    run(
        input_path=args.input_path,
        window_size=args.window_size,
        min_points=args.min_points,
        z_threshold=args.z_threshold,
    )
```

Run it from the directory that contains both files:

```bash
.venv/bin/python rolling_detector.py samples.jsonl --min-points 5 --z-threshold 3.0
```

You should see anomaly JSON for the checkout latency spike and the catalog latency spike. The exact score depends on the prior values in each service-specific baseline. That separation matters because a value that is normal for one service may be abnormal for another service with a different latency profile.

The detector has obvious limitations, and that is useful. It assumes recent history is representative, it handles each metric independently, and it does not understand seasonality, deployments, traffic shape, or topology. Those gaps are not failures of the example; they are the design backlog for the next layer. You now have a baseline that produces explainable events, which means you can test whether fancier approaches actually improve operational outcomes.

> **Prediction prompt:** Before changing the threshold from `3.0` to `2.0`, predict what will happen to false positives and false negatives. Then run the command again and compare the number of emitted anomaly events. The point is not to memorize a magic threshold; the point is to feel the precision and recall trade-off.

Feature engineering is the next step because raw metrics rarely contain enough context. A detector that sees only `latency_p99=1.86` cannot know whether that value occurred during a canary, a traffic surge, a dependency outage, or a scheduled load test. A feature pipeline enriches the sample before detection so the model can make a better judgment.

```text
FEATURE ENGINEERING RESPONSIBILITIES

┌────────────────────┐       ┌────────────────────────────┐       ┌─────────────────────┐
│ Raw metric sample  │──────▶│ Feature engineering stage   │──────▶│ Feature event       │
└────────────────────┘       └────────────────────────────┘       └─────────────────────┘
        │                                  │                                │
        │                                  │                                │
        │ timestamp                        │ service owner                  │ rate over window
        │ labels                           │ deployment version             │ error budget burn
        │ value                            │ topology neighbors             │ traffic percentile
        │ scrape metadata                  │ maintenance calendar           │ recent deploy flag
```

The senior habit is to version features as carefully as application APIs. A model trained with `recent_deploy` and `team` should not suddenly receive events where those fields are renamed or absent. Feature drift can be just as damaging as model drift because it changes what the detector thinks it knows about the world.

## 4. Choose Detection Models by Signal Shape

Different signals fail in different ways, so one detector rarely fits the whole platform. Request latency often has daily and weekly seasonality. Error rate may be sparse until a dependency breaks. CPU usage may gradually climb because of a leak. Queue depth may jump after a downstream outage. A mature custom AIOps system maps detector choice to signal behavior instead of applying one algorithm everywhere.

The simplest useful detector families are statistical thresholds, seasonal baselines, isolation-based outlier detection, and supervised classifiers trained on labeled incidents. Statistical thresholds are explainable and cheap, but they miss subtle patterns. Seasonal baselines handle repeated cycles, but they need enough history. Isolation methods can catch strange combinations of features, but they are harder to explain. Supervised models can be powerful, but only when labels are reliable and representative.

| Signal Pattern | Better Starting Detector | Why It Fits | Main Risk |
|---|---|---|---|
| Stable service latency with occasional spikes | Rolling z-score or robust median absolute deviation | Easy to explain and validate with local history | Noisy during deploys or traffic shifts |
| Strong daily or weekly cycle | Seasonal baseline or Prophet-style forecast | Learns expected recurring shape over time | Needs enough clean historical data |
| Many features interacting together | Isolation Forest or similar outlier method | Finds unusual combinations without labels | Can be hard to explain during incidents |
| Known incident classes with reviewed labels | Supervised classifier | Learns from past responder decisions | Labels may encode old bias or stale topology |
| Rare but high-impact domain events | Rule plus model hybrid | Keeps business invariants explicit | Rules can become unmaintained policy code |

A good detector emits uncertainty, not just a verdict. The event should say which baseline it used, how much data supported the score, and why the score crossed the threshold. This evidence lets responders decide whether to trust the signal during a messy incident. It also gives model owners enough information to improve the pipeline after the incident review.

The feedback loop is where custom AIOps becomes operationally useful. Every incident should allow responders to label whether the anomaly was useful, noisy, late, duplicated, or dangerous. Those labels become evaluation data. Without feedback, the team is tuning by opinion and anecdote; with feedback, the team can measure whether changes reduce noise without hiding real incidents.

```text
FEEDBACK LOOP FOR CONTINUOUS IMPROVEMENT

┌──────────────────┐
│ Anomaly emitted  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐      responder labels      ┌──────────────────────┐
│ Incident review  │───────────────────────────▶│ Feedback store        │
└──────────────────┘                            └──────────┬───────────┘
                                                            │
                                                            ▼
┌──────────────────┐      evaluation report      ┌──────────────────────┐
│ Model registry   │◀───────────────────────────│ Offline evaluation    │
└────────┬─────────┘                            └──────────────────────┘
         │
         ▼
┌──────────────────┐
│ Controlled rollout│
└──────────────────┘
```

Feedback must be designed for tired humans. A five-field form that appears after every incident may get filled out; a twenty-field form will be ignored or filled with low-quality data. The first version can ask whether the alert was useful, whether the root-cause hypothesis was correct, whether the severity was right, and which service actually caused the issue. These few labels already support meaningful evaluation.

A senior team also keeps a champion-challenger path. The current detector remains the champion that controls production behavior, while a challenger detector scores the same stream in shadow mode. The challenger does not page anyone. It produces evaluation reports that compare precision, recall, timeliness, and duplication against the current approach. This avoids replacing a trusted imperfect system with an unproven impressive one.

## 5. Correlate Events Before Paging Humans

Anomaly detection answers "Is this signal unusual?" Correlation answers "Are these unusual signals part of the same operational story?" That second question is where many AIOps projects become valuable, because responders do not need a separate page for every metric. They need a grouped incident with evidence, likely blast radius, and a starting hypothesis.

Correlation uses several weak signals together. Time proximity says events happened near each other. Topology says one service depends on another. Ownership says two services belong to the same team or platform. Deployment history says a recent change may be related. Text similarity says log messages or event reasons share language. No single signal proves root cause, but the combination can rank useful hypotheses.

```text
CORRELATION INPUTS

┌──────────────────┐       ┌─────────────────────┐
│ Anomaly events   │──────▶│ Correlation engine  │
└──────────────────┘       └──────────┬──────────┘
                                      │
┌──────────────────┐                  │
│ Service topology │──────────────────┤
└──────────────────┘                  │
                                      ▼
┌──────────────────┐       ┌─────────────────────┐
│ Deploy history   │──────▶│ Incident candidate  │
└──────────────────┘       └─────────────────────┘
                                      ▲
┌──────────────────┐                  │
│ Ownership data   │──────────────────┘
└──────────────────┘
```

The following runnable correlator groups anomaly events by service neighborhood and time bucket. It is deliberately simple, but it shows the shape of the problem: a detector emits isolated events, while a correlator keeps enough state to group them into an incident. In production, you would likely use Kafka partitions, Redis, a stream processor, or a database-backed state store instead of a local dictionary.

Create `correlate_anomalies.py`:

```python
#!/usr/bin/env python3
import argparse
import datetime as dt
import json
from collections import defaultdict


TOPOLOGY = {
    "checkout-api": {"payment-api", "inventory-api", "cart-api"},
    "payment-api": {"checkout-api"},
    "inventory-api": {"checkout-api", "warehouse-api"},
    "catalog-api": {"search-api"},
}


def parse_timestamp(value: str) -> dt.datetime:
    normalized = value.replace("Z", "+00:00")
    return dt.datetime.fromisoformat(normalized)


def bucket_for(timestamp: str, bucket_seconds: int) -> int:
    parsed = parse_timestamp(timestamp)
    return int(parsed.timestamp()) // bucket_seconds


def neighborhood(service: str) -> set[str]:
    related = set(TOPOLOGY.get(service, set()))
    related.add(service)
    return related


def group_key(event: dict, bucket_seconds: int) -> str:
    service = event["service"]
    bucket = bucket_for(event["timestamp"], bucket_seconds)
    members = sorted(neighborhood(service))
    return f"{bucket}:{','.join(members)}"


def severity_from_score(score: float) -> str:
    if score >= 0.85:
        return "critical"
    if score >= 0.65:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


def correlate(input_path: str, bucket_seconds: int) -> list[dict]:
    groups: dict[str, list[dict]] = defaultdict(list)

    with open(input_path, "r", encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            event = json.loads(line)
            groups[group_key(event, bucket_seconds)].append(event)

    incidents = []
    for index, events in enumerate(groups.values(), start=1):
        events.sort(key=lambda item: item["timestamp"])
        max_score = max(float(event["anomaly_score"]) for event in events)
        services = sorted({event["service"] for event in events})
        first_event = events[0]

        incidents.append(
            {
                "incident_id": f"INC-{index:05d}",
                "created_at": first_event["timestamp"],
                "severity": severity_from_score(max_score),
                "services": services,
                "event_count": len(events),
                "hypothesis": {
                    "probable_starting_service": first_event["service"],
                    "reason": "earliest anomaly in topology-aware time bucket",
                    "confidence": 0.6 if len(events) > 1 else 0.3,
                },
                "events": events,
            }
        )

    return incidents


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Group anomaly events into incident candidates.")
    parser.add_argument("input_path", help="Path to JSON Lines anomaly events.")
    parser.add_argument("--bucket-seconds", type=int, default=300)
    args = parser.parse_args()

    for incident in correlate(args.input_path, args.bucket_seconds):
        print(json.dumps(incident, sort_keys=True))
```

You can connect this to the detector by redirecting output:

```bash
.venv/bin/python rolling_detector.py samples.jsonl --min-points 5 > anomalies.jsonl
.venv/bin/python correlate_anomalies.py anomalies.jsonl --bucket-seconds 300
```

The output is not a final truth; it is an incident candidate. That distinction matters. AIOps should make the responder faster, not pretend to be omniscient. The incident should say "probable starting service" and "confidence" rather than "root cause" unless the evidence is strong enough to justify that claim.

Correlation state is the reason many examples run the correlator as one replica. If two replicas see different parts of the same incident without shared state, they may create duplicate incidents. Scaling options exist, but each one has a cost. You can partition by service ownership, store active incidents in Redis, use a stream processor with keyed state, or accept duplicate candidates and merge them later. The right answer depends on incident volume and blast-radius boundaries.

## 6. Deploy With Kubernetes Controls and Operational Guardrails

A custom AIOps service is part of the production control plane for humans. If it fails, it can hide incidents, spam responders, or execute unsafe remediation. Kubernetes deployment choices must therefore reflect the risk profile of each stage. Stateless detectors can usually scale horizontally. Correlators need careful state handling. Incident managers should be conservative and idempotent. Remediation should be gated until the organization has evidence that it is safe.

The Kubernetes manifests below show the shape of a minimal deployment. They are not a complete production platform, but they demonstrate the controls that matter: explicit resources, health probes, configuration through ConfigMaps, credentials through Secrets, and different replica counts for stateless and stateful stages. Use `kubectl` for commands; if your shell defines `k` as an alias for `kubectl`, the shorter alias is fine after you have verified it points to the same binary.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: aiops
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: aiops-config
  namespace: aiops
data:
  ANOMALY_THRESHOLD: "3.0"
  CORRELATION_WINDOW_SECONDS: "300"
  AUTO_REMEDIATION_ENABLED: "false"
  INCIDENT_TOPIC: "aiops.incidents"
---
apiVersion: v1
kind: Secret
metadata:
  name: aiops-secrets
  namespace: aiops
type: Opaque
stringData:
  PAGERDUTY_ROUTING_KEY: "replace-with-real-routing-key"
  SLACK_WEBHOOK_URL: "https://hooks.slack.com/services/replace/me"
```

```yaml
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
          image: registry.example.com/aiops/anomaly-detector:1.0.0
          imagePullPolicy: IfNotPresent
          envFrom:
            - configMapRef:
                name: aiops-config
          env:
            - name: KAFKA_BOOTSTRAP_SERVERS
              value: "kafka.aiops.svc.cluster.local:9092"
          ports:
            - name: http
              containerPort: 8080
          resources:
            requests:
              cpu: "250m"
              memory: "512Mi"
            limits:
              cpu: "750m"
              memory: "1Gi"
          readinessProbe:
            httpGet:
              path: /ready
              port: http
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /healthz
              port: http
            initialDelaySeconds: 20
            periodSeconds: 20
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: event-correlator
  namespace: aiops
  labels:
    app: event-correlator
spec:
  replicas: 1
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
          image: registry.example.com/aiops/event-correlator:1.0.0
          imagePullPolicy: IfNotPresent
          envFrom:
            - configMapRef:
                name: aiops-config
          env:
            - name: KAFKA_BOOTSTRAP_SERVERS
              value: "kafka.aiops.svc.cluster.local:9092"
            - name: STATE_BACKEND
              value: "local"
          ports:
            - name: http
              containerPort: 8080
          resources:
            requests:
              cpu: "200m"
              memory: "384Mi"
            limits:
              cpu: "500m"
              memory: "768Mi"
          readinessProbe:
            httpGet:
              path: /ready
              port: http
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /healthz
              port: http
            initialDelaySeconds: 20
            periodSeconds: 20
```

```yaml
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
          image: registry.example.com/aiops/incident-manager:1.0.0
          imagePullPolicy: IfNotPresent
          envFrom:
            - configMapRef:
                name: aiops-config
            - secretRef:
                name: aiops-secrets
          ports:
            - name: http
              containerPort: 8080
          resources:
            requests:
              cpu: "100m"
              memory: "256Mi"
            limits:
              cpu: "300m"
              memory: "512Mi"
          readinessProbe:
            httpGet:
              path: /ready
              port: http
            initialDelaySeconds: 5
            periodSeconds: 10
```

The `AUTO_REMEDIATION_ENABLED` default is `false` for a reason. Remediation is an actuator, and actuators deserve stronger controls than dashboards. Start with recommendations, then move to human-approved actions, then narrow automatic actions only after measuring safety. The first automatic action should be reversible, scoped, rate-limited, and tied to a runbook that humans already trust.

The platform should also monitor the AIOps system itself. Track input lag, invalid event count, detector latency, anomaly volume, incident deduplication rate, action failures, and responder feedback. If anomaly volume doubles after a deploy, the AIOps team should know before on-call responders lose trust. Monitor your monitoring, but more specifically, monitor the decision pipeline that influences responders.

```text
AIOPS SERVICE HEALTH SIGNALS

┌────────────────────────┐    ┌───────────────────────────────────────┐
│ Pipeline Stage         │    │ Health Signals                         │
├────────────────────────┤    ├───────────────────────────────────────┤
│ Ingestion              │    │ Kafka lag, invalid events, sample gaps │
│ Feature engineering    │    │ enrichment misses, schema rejects      │
│ Detection              │    │ score latency, anomaly rate, errors    │
│ Correlation            │    │ duplicate incidents, open state size   │
│ Incident management    │    │ notification failures, action retries  │
│ Feedback               │    │ label coverage, reviewer disagreement  │
└────────────────────────┘    └───────────────────────────────────────┘
```

Production maturity is not reached when the first model runs. It is reached when the team can deploy a new detector in shadow mode, compare it against historical incidents, roll it out to one service group, explain its output during an incident, and roll it back without losing the event stream. That is a platform engineering standard, not a data science luxury.

## Did You Know?

- **Netflix built several internal and open-source anomaly detection components because streaming behavior has service-specific patterns that generic monitoring could not fully capture.** The important lesson is not that every company should copy Netflix; it is that detection quality improves when the model understands the operating domain.

- **LinkedIn's ThirdEye grew from the need to detect business and service anomalies across high-volume metric streams.** Its existence illustrates a common custom-AIOps driver: when metric volume, organizational context, and decision latency become tightly coupled, platform teams need more control over the pipeline.

- **Many AIOps failures are data-contract failures rather than model failures.** Missing ownership labels, inconsistent service names, and unversioned feature changes can break correlation even when the detector's statistical method is reasonable.

- **Shadow evaluation is one of the safest ways to improve operational intelligence.** A challenger detector can score the same events as production without paging humans, which lets the team compare usefulness before changing incident behavior.

## Common Mistakes

| Mistake | Impact | Better Approach |
|---|---|---|
| Building custom AIOps before naming the decision it improves | The project becomes a model demo that does not reduce incident pain | Define the operational decision, target services, success metric, and human workflow before choosing tools |
| Training or tuning against too little representative data | False positives rise during normal cycles, deploys, or traffic shifts | Collect enough baseline history, separate service profiles, and start with advisory output |
| Treating anomaly detection as the whole product | Responders receive isolated signals without root-cause context or action guidance | Add topology, ownership, deployment history, correlation, and feedback from the beginning |
| Scaling correlators without shared state or partition design | Related anomalies become duplicate incidents or inconsistent hypotheses | Partition by correlation domain or use a state backend with explicit merge behavior |
| Hiding model evidence behind a single score | Engineers cannot judge whether an alert is trustworthy during an incident | Emit expected range, sample count, detector name, window, and supporting metadata |
| Enabling remediation before proving alert quality | The system can restart, scale, or change workloads for the wrong reason | Begin with recommendations, require human approval, and automate only narrow reversible actions |
| Ignoring drift in features, labels, and topology | Model quality decays even though code and thresholds appear unchanged | Version schemas, monitor enrichment misses, and review detector performance over time |
| Failing to observe the AIOps pipeline itself | Broken ingestion or noisy models are discovered by annoyed responders | Track lag, invalid events, anomaly volume, duplicate incidents, action failures, and feedback coverage |

## Quiz

### Question 1

Your team wants to build custom AIOps because the CPU alert for a critical service pages too often. During review, you discover the alert fires on every short-lived deployment spike, but incidents are only caused when error rate and queue depth rise together. What should you recommend as the first change, and why?

<details>
<summary>Show Answer</summary>

Start by improving the decision logic rather than building a broad custom platform. The immediate problem is not that CPU needs a sophisticated model; the problem is that the alert does not match the incident condition. A better first step is to correlate CPU with error rate, queue depth, deployment windows, and service impact, then page only when the combined condition predicts user risk. This aligns the signal with the operational decision and may avoid unnecessary custom infrastructure.
</details>

### Question 2

A detector emits anomaly events with `timestamp`, `metric_name`, `value`, and `anomaly_score`, but it does not include `service`, `namespace`, or ownership labels. The model scores look accurate in offline tests. What will likely fail when you connect this detector to incident workflow?

<details>
<summary>Show Answer</summary>

Correlation and routing will fail even if the model scores are accurate. Without service and namespace identity, the system cannot attach topology, group related events, choose the correct on-call team, select a runbook, or gather service-specific feedback. Offline model accuracy is not enough for AIOps; the event contract must carry the context needed by downstream operational decisions.
</details>

### Question 3

A platform team deploys three correlator replicas behind one Kafka consumer group. Afterward, responders see duplicate incidents for the same checkout outage, and each incident contains only part of the evidence. What design issue caused this, and what are two reasonable fixes?

<details>
<summary>Show Answer</summary>

The correlator has stateful grouping behavior, but the deployment scaled it like a stateless service. Related anomaly events were split across replicas without a shared correlation state or partitioning strategy. Two reasonable fixes are to partition events by a stable correlation key such as service group or ownership domain, or to store active incident state in a shared backend such as Redis or a stream processor with keyed state. Running a single correlator can also be acceptable while volume is low.
</details>

### Question 4

Your challenger detector finds more anomalies than the current production detector during shadow evaluation. Product leadership wants to promote it immediately because it catches two past incidents earlier. What additional evidence should you ask for before rollout?

<details>
<summary>Show Answer</summary>

Ask for precision, duplicate rate, false positive review, timeliness, and responder usefulness across a representative period. Catching two incidents earlier is valuable, but the detector may also create enough noise to reduce trust. A safe rollout compares the challenger against production in shadow mode, reviews false positives with service owners, and then enables it for a narrow service group before broader paging behavior changes.
</details>

### Question 5

An AIOps pipeline starts producing many critical incidents every Monday morning. The affected services are healthy, but traffic patterns are different from weekends. Which part of the design should you inspect first, and what change might reduce the noise?

<details>
<summary>Show Answer</summary>

Inspect the baseline and feature engineering design first. The detector may be comparing Monday traffic to weekend history without understanding weekly seasonality or business-hour patterns. A better approach is to use a seasonal baseline, include day-of-week and traffic context as features, or maintain separate baselines for comparable time windows. This addresses the signal shape rather than simply raising thresholds.
</details>

### Question 6

A team wants to enable automatic remediation for every incident where the anomaly score exceeds `0.90`. The proposed action restarts the affected Deployment. What risks should you raise, and how would you redesign the rollout?

<details>
<summary>Show Answer</summary>

Anomaly score alone does not prove root cause or prove that restart is safe. Restarting every high-score workload can worsen incidents, hide evidence, or create cascading failures. Redesign the rollout as advisory first, then human-approved remediation for a narrow known failure mode, then automatic action only when the runbook is reversible, rate-limited, scoped, and supported by feedback showing high correctness. The action should depend on root-cause evidence, not just anomaly severity.
</details>

### Question 7

Your detector performed well for two months, but recently it misses incidents after a service migration. The code did not change. What non-code causes should you investigate, and how would you prevent a repeat?

<details>
<summary>Show Answer</summary>

Investigate feature drift, label changes, topology changes, service renames, missing ownership metadata, altered traffic shape, and deployment process changes. The model may receive different inputs even though detector code is unchanged. Prevention requires schema validation, feature versioning, enrichment-miss metrics, topology freshness checks, and regular feedback-based evaluation. AIOps quality depends on the data contract staying true to the operating environment.
</details>

## Hands-On Exercise

### Objective

Build a minimal local AIOps pipeline that turns metric samples into anomaly events, groups those events into incident candidates, and evaluates whether the pipeline output would be useful to a responder. This exercise uses local files so you can focus on the concepts before adding Kafka or Kubernetes.

### Scenario

The commerce platform team owns `checkout-api`, `payment-api`, `inventory-api`, and `catalog-api`. During a load event, responders receive scattered telemetry from several services. Your task is to build the first version of a custom AIOps pipeline that detects unusual latency, correlates related anomalies, and produces an incident candidate with evidence.

### Step 1: Create the workspace

```bash
mkdir custom-aiops-local
cd custom-aiops-local
touch samples.jsonl rolling_detector.py correlate_anomalies.py review_incidents.py
```

### Step 2: Add the sample data

Copy the `samples.jsonl` content from the worked example into your local file. Add at least six more samples for `payment-api` where latency rises shortly after the `checkout-api` spike. Keep the timestamps within the same five-minute bucket so the correlator has a chance to group them.

### Step 3: Add the detector

Copy `rolling_detector.py` from the worked example into your local file. Run the detector and store its output:

```bash
.venv/bin/python rolling_detector.py samples.jsonl --min-points 5 --z-threshold 3.0 > anomalies.jsonl
```

If the output is empty, lower the threshold to `2.5` and run it again. Do not treat threshold tuning as a trick; write down why the lower threshold changes the trade-off between missed incidents and alert noise.

### Step 4: Add the correlator

Copy `correlate_anomalies.py` from the correlation section into your local file. Run it against the detector output:

```bash
.venv/bin/python correlate_anomalies.py anomalies.jsonl --bucket-seconds 300 > incidents.jsonl
```

Open `incidents.jsonl` and inspect whether checkout and payment anomalies were grouped. If they were not grouped, inspect the topology map and timestamps before changing detector logic.

### Step 5: Add a small review script

Create `review_incidents.py` to summarize incident candidates for a responder:

```python
#!/usr/bin/env python3
import json
import sys


def summarize(path: str) -> None:
    with open(path, "r", encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            incident = json.loads(line)
            services = ", ".join(incident["services"])
            hypothesis = incident["hypothesis"]
            print(f"Incident: {incident['incident_id']}")
            print(f"Severity: {incident['severity']}")
            print(f"Services: {services}")
            print(f"Events: {incident['event_count']}")
            print(f"Starting hypothesis: {hypothesis['probable_starting_service']}")
            print(f"Reason: {hypothesis['reason']}")
            print(f"Confidence: {hypothesis['confidence']}")
            print("---")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: review_incidents.py incidents.jsonl")
    summarize(sys.argv[1])
```

Run the review script:

```bash
.venv/bin/python review_incidents.py incidents.jsonl
```

### Step 6: Evaluate the design

Write a short design note in your own words. Explain whether the output would help an incident commander, what context is missing, and what you would add before paging humans. Include at least one improvement to the event schema, one improvement to correlation, and one safety control for remediation.

### Success Criteria

- [ ] You generated anomaly events from local metric samples using `.venv/bin/python`.
- [ ] Each anomaly event includes service identity, metric name, value, score, detector name, and evidence.
- [ ] You grouped anomaly events into at least one incident candidate.
- [ ] You inspected whether topology and time windows changed the grouping behavior.
- [ ] You explained the threshold trade-off instead of treating the detector as automatically correct.
- [ ] You identified missing context that would matter during a real incident.
- [ ] You proposed a safe next step before any automatic remediation is enabled.

## Next Module

Continue with the broader reliability practice that consumes AIOps output: [SRE Discipline](/platform/disciplines/core-platform/sre/). There you will connect detection, correlation, and incident automation to service-level objectives, error budgets, escalation policy, and operational review.
