---
title: "Module 1.5: Automating Chaos & Game Days"
slug: platform/disciplines/reliability-security/chaos-engineering/module-1.5-automating-chaos
sidebar:
  order: 6
---
> **Discipline Module** | Complexity: `[MEDIUM]` | Time: 2 hours

## Prerequisites

Before starting this module:
- **Required**: [Module 1.3: Network & Application Fault Injection](../module-1.3-network-fault-injection/) — Familiarity with multiple chaos experiment types
- **Required**: CI/CD fundamentals — GitHub Actions, GitLab CI, or equivalent pipeline experience
- **Recommended**: [SRE Module 1.2: SLOs](../../core-platform/sre/module-1.2-slos/) — Understanding SLOs and error budgets
- **Recommended**: Prometheus and Grafana basics

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Design automated chaos engineering pipelines that run experiments on schedule and in CI/CD**
- **Implement GameDay exercises that combine multiple chaos experiments into realistic failure scenarios**
- **Build chaos experiment result tracking that measures resilience improvements over time**
- **Configure automated abort conditions that halt experiments when unexpected blast radius is detected**

## Why This Module Matters

On October 4, 2021, Facebook experienced a 6-hour global outage that affected 3.5 billion users and cost the company an estimated $65 million in revenue. The root cause was a configuration change to their backbone routers that disconnected Facebook's data centers from each other. But the real question isn't why it happened — network misconfigurations happen. The question is why it lasted 6 hours.

The answer: Facebook's internal tools (including the ones engineers needed to fix the problem) ran on the same infrastructure that was down. Engineers couldn't access the admin panels, couldn't SSH into servers, couldn't even get into the buildings because the badge readers depended on Facebook's internal network. The recovery tools were victims of the same failure they were supposed to fix.

A single Game Day testing the scenario "what if our internal tools are inaccessible during an outage" would have revealed this dependency. An automated chaos pipeline testing backbone connectivity would have caught the configuration issue before it went live. Neither existed.

This module teaches you to move chaos engineering from manual experiments into automated pipelines and structured Game Days. The goal is to make resilience verification as routine as running unit tests — something that happens on every deployment, not something an engineer remembers to do once a quarter.

---

## Did You Know?

> **Netflix runs over 2,000 automated chaos experiments per week** across their production infrastructure. These experiments run continuously, verifying that auto-scaling, failover, and circuit breakers work correctly. When an experiment reveals a regression (something that used to be resilient is no longer), it creates an automated ticket for the owning team. This continuous verification has reduced Netflix's unplanned outage rate by 78% since they started the program.

> **Gremlin (a commercial chaos engineering platform) reported** that organizations running chaos experiments in CI/CD pipelines experience 60% fewer severity-1 incidents than those running chaos only during manual Game Days. The key difference is frequency — automated chaos catches regressions within hours, while quarterly Game Days leave months of blind spots.

> **The concept of "Game Days" originated at Amazon in 2004** when Jesse Robbins (now known as the "Master of Disaster") started running failure simulations that tested not just technology but people and processes. The first Game Day revealed that 40% of runbooks were outdated and that three critical services had no runbooks at all. Robbins later said: "The Game Day didn't break anything — it revealed things that were already broken."

> **Google's DiRT (Disaster Recovery Testing) program** runs annual company-wide exercises where entire regions are simulated as failed. In 2019, a DiRT exercise revealed that 11 internal services had undocumented dependencies on a specific metadata service. Fixing those dependencies before a real regional failure prevented what would have been a multi-hour cascading outage.

---

## Integrating Chaos into CI/CD

### The Chaos Pipeline Pattern

The fundamental pattern is: **deploy → verify steady state → inject chaos → validate SLOs → clean up**

```
┌─────────────┐   ┌──────────────┐   ┌───────────────┐
│   Deploy     │──→│  Verify       │──→│  Inject        │
│   to staging │   │  steady state │   │  chaos         │
└─────────────┘   └──────────────┘   └───────┬───────┘
                                              │
                                     ┌────────▼────────┐
                                     │  SLO validation  │
                                     │  (Prometheus)    │
                                     └────────┬────────┘
                                              │
                                    ┌─────────▼─────────┐
                                    │    Pass/Fail?       │
                                    └─────┬───────┬──────┘
                                          │       │
                                   Pass   │       │  Fail
                                    ┌─────▼──┐  ┌─▼──────────┐
                                    │ Clean   │  │ Abort chaos │
                                    │ up +    │  │ + rollback  │
                                    │ proceed │  │ deployment  │
                                    └─────────┘  └─────────────┘
```

### When to Run Chaos in CI/CD

| Trigger | Chaos Level | Duration | Example |
|---------|-------------|----------|---------|
| Every PR merge to main | Light (pod-kill single pod) | 2-5 minutes | Verify deployment survives basic pod restart |
| Nightly build | Medium (network delay + pod-kill) | 10-15 minutes | Verify service mesh and circuit breakers |
| Weekly scheduled | Heavy (multi-fault workflow) | 30-60 minutes | Comprehensive resilience regression suite |
| Pre-release | Full Game Day (manual + automated) | 2-4 hours | Release readiness verification |

### GitHub Actions: Complete Chaos Pipeline

```yaml
# .github/workflows/chaos-pipeline.yaml
name: Chaos Engineering Pipeline

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 2 * * 1-5'     # 2 AM weekdays for nightly chaos

env:
  CLUSTER_NAME: chaos-staging
  CHAOS_NAMESPACE: chaos-tests

jobs:
  deploy:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure kubectl
        uses: azure/setup-kubectl@v3

      - name: Set up kubeconfig
        run: |
          echo "${{ secrets.KUBECONFIG }}" | base64 -d > $HOME/.kube/config

      - name: Deploy application
        run: |
          kubectl apply -f k8s/staging/ --namespace=staging
          kubectl rollout status deployment/frontend -n staging --timeout=120s
          kubectl rollout status deployment/backend -n staging --timeout=120s
          kubectl rollout status deployment/api-gateway -n staging --timeout=120s

      - name: Wait for stabilization
        run: |
          echo "Waiting 60s for deployment to stabilize..."
          sleep 60

  verify-steady-state:
    name: Verify Steady State
    needs: deploy
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up kubeconfig
        run: echo "${{ secrets.KUBECONFIG }}" | base64 -d > $HOME/.kube/config

      - name: Check all pods healthy
        run: |
          UNHEALTHY=$(kubectl get pods -n staging --field-selector=status.phase!=Running -o name | wc -l)
          if [ "$UNHEALTHY" -gt 0 ]; then
            echo "ERROR: $UNHEALTHY unhealthy pods found"
            kubectl get pods -n staging --field-selector=status.phase!=Running
            exit 1
          fi
          echo "All pods healthy"

      - name: Verify SLO baseline
        run: |
          # Query Prometheus for current error rate
          ERROR_RATE=$(curl -s "http://prometheus.monitoring:9090/api/v1/query" \
            --data-urlencode 'query=sum(rate(http_requests_total{namespace="staging",code=~"5.."}[5m])) / sum(rate(http_requests_total{namespace="staging"}[5m])) * 100' \
            | jq -r 'if .data.result | length > 0 then .data.result[0].value[1] else "0" end')

          echo "Current error rate: ${ERROR_RATE}%"

          # Fail if error rate already above 0.5%
          if (( $(echo "$ERROR_RATE > 0.5" | bc -l) )); then
            echo "ERROR: Steady state already violated. Error rate: ${ERROR_RATE}%"
            exit 1
          fi

      - name: Verify latency baseline
        run: |
          P99=$(curl -s "http://prometheus.monitoring:9090/api/v1/query" \
            --data-urlencode 'query=histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{namespace="staging"}[5m])) by (le))' \
            | jq -r 'if .data.result | length > 0 then .data.result[0].value[1] else "0" end')

          echo "Current p99 latency: ${P99}s"

          if (( $(echo "$P99 > 0.5" | bc -l) )); then
            echo "ERROR: Steady state already violated. P99 latency: ${P99}s"
            exit 1
          fi

  chaos-pod-kill:
    name: Chaos — Pod Kill
    needs: verify-steady-state
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up kubeconfig
        run: echo "${{ secrets.KUBECONFIG }}" | base64 -d > $HOME/.kube/config

      - name: Apply pod-kill experiment
        run: |
          cat <<'YAML' | kubectl apply -f -
          apiVersion: chaos-mesh.org/v1alpha1
          kind: PodChaos
          metadata:
            name: ci-pod-kill
            namespace: staging
          spec:
            action: pod-kill
            mode: one
            selector:
              namespaces:
                - staging
              labelSelectors:
                app: backend
            gracePeriod: 0
            duration: "120s"
          YAML

          echo "Pod-kill experiment applied at $(date -u)"

      - name: Wait for experiment duration
        run: sleep 130

      - name: Validate SLOs during experiment
        id: slo-check
        run: |
          # Check error rate over the last 3 minutes
          ERROR_RATE=$(curl -s "http://prometheus.monitoring:9090/api/v1/query" \
            --data-urlencode 'query=sum(rate(http_requests_total{namespace="staging",code=~"5.."}[3m])) / sum(rate(http_requests_total{namespace="staging"}[3m])) * 100' \
            | jq -r 'if .data.result | length > 0 then .data.result[0].value[1] else "0" end')

          P99=$(curl -s "http://prometheus.monitoring:9090/api/v1/query" \
            --data-urlencode 'query=histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{namespace="staging"}[3m])) by (le))' \
            | jq -r 'if .data.result | length > 0 then .data.result[0].value[1] else "0" end')

          echo "Error rate during chaos: ${ERROR_RATE}%"
          echo "P99 latency during chaos: ${P99}s"

          PASS=true
          if (( $(echo "$ERROR_RATE > 1.0" | bc -l) )); then
            echo "FAIL: Error rate SLO violated (${ERROR_RATE}% > 1.0%)"
            PASS=false
          fi
          if (( $(echo "$P99 > 2.0" | bc -l) )); then
            echo "FAIL: Latency SLO violated (${P99}s > 2.0s)"
            PASS=false
          fi

          if [ "$PASS" = true ]; then
            echo "PASS: All SLOs maintained during pod-kill"
          else
            echo "slo_passed=false" >> $GITHUB_OUTPUT
            exit 1
          fi

      - name: Clean up experiment
        if: always()
        run: |
          kubectl delete podchaos ci-pod-kill -n staging --ignore-not-found
          echo "Experiment cleaned up"

  chaos-network-delay:
    name: Chaos — Network Delay
    needs: chaos-pod-kill
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up kubeconfig
        run: echo "${{ secrets.KUBECONFIG }}" | base64 -d > $HOME/.kube/config

      - name: Apply network delay experiment
        run: |
          cat <<'YAML' | kubectl apply -f -
          apiVersion: chaos-mesh.org/v1alpha1
          kind: NetworkChaos
          metadata:
            name: ci-network-delay
            namespace: staging
          spec:
            action: delay
            mode: all
            selector:
              namespaces:
                - staging
              labelSelectors:
                app: backend
            delay:
              latency: "200ms"
              jitter: "50ms"
              correlation: "75"
            direction: to
            target:
              selector:
                namespaces:
                  - staging
                labelSelectors:
                  app: api-gateway
              mode: all
            duration: "180s"
          YAML

          echo "Network delay experiment applied at $(date -u)"

      - name: Wait and validate
        run: |
          sleep 190

          P99=$(curl -s "http://prometheus.monitoring:9090/api/v1/query" \
            --data-urlencode 'query=histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{namespace="staging"}[3m])) by (le))' \
            | jq -r 'if .data.result | length > 0 then .data.result[0].value[1] else "0" end')

          echo "P99 latency during network delay: ${P99}s"

          if (( $(echo "$P99 > 3.0" | bc -l) )); then
            echo "FAIL: P99 latency exceeded 3s during 200ms injected delay"
            exit 1
          fi

          echo "PASS: System handled 200ms network delay within SLO"

      - name: Clean up experiment
        if: always()
        run: kubectl delete networkchaos ci-network-delay -n staging --ignore-not-found

  report:
    name: Chaos Report
    needs: [chaos-pod-kill, chaos-network-delay]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Generate report
        run: |
          echo "## Chaos Engineering Report" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "**Date**: $(date -u)" >> $GITHUB_STEP_SUMMARY
          echo "**Trigger**: ${{ github.event_name }}" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "| Experiment | Result |" >> $GITHUB_STEP_SUMMARY
          echo "|------------|--------|" >> $GITHUB_STEP_SUMMARY
          echo "| Pod Kill | ${{ needs.chaos-pod-kill.result }} |" >> $GITHUB_STEP_SUMMARY
          echo "| Network Delay | ${{ needs.chaos-network-delay.result }} |" >> $GITHUB_STEP_SUMMARY

      - name: Notify on failure
        if: failure()
        run: |
          curl -X POST "${{ secrets.SLACK_WEBHOOK }}" \
            -H 'Content-type: application/json' \
            -d '{
              "text": "Chaos Pipeline FAILED: Resilience regression detected in staging. See: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
            }'
```

---

## Automated Abort on Prometheus Alerts

### The Abort Controller Pattern

The most critical safety mechanism for automated chaos is the ability to abort experiments automatically when SLOs are violated. Here's how to build it:

```
┌──────────────┐    fires alert    ┌────────────────┐
│  Prometheus   │─────────────────→│ Alertmanager    │
│  (SLO rules)  │                   │                 │
└──────────────┘                   └────────┬────────┘
                                            │ webhook
                                   ┌────────▼────────┐
                                   │  Chaos Abort     │
                                   │  Controller      │
                                   │  (custom app)    │
                                   └────────┬────────┘
                                            │ kubectl delete
                                   ┌────────▼────────┐
                                   │  Chaos Mesh      │
                                   │  Experiments      │
                                   │  (deleted/paused) │
                                   └──────────────────┘
```

### Prometheus Alert Rules for Chaos Abort

```yaml
# chaos-abort-rules.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: chaos-abort-rules
  namespace: monitoring
spec:
  groups:
    - name: chaos-safety
      rules:
        - alert: ChaosAbort_ErrorRateCritical
          expr: |
            sum(rate(http_requests_total{namespace="staging", code=~"5.."}[2m]))
            /
            sum(rate(http_requests_total{namespace="staging"}[2m]))
            > 0.05
          for: 30s
          labels:
            severity: chaos-abort
            action: delete-all-chaos
          annotations:
            summary: "Error rate exceeded 5% — aborting all chaos experiments"
            runbook: "This alert auto-deletes all Chaos Mesh experiments in staging"

        - alert: ChaosAbort_LatencyCritical
          expr: |
            histogram_quantile(0.99,
              sum(rate(http_request_duration_seconds_bucket{namespace="staging"}[2m])) by (le)
            ) > 5
          for: 30s
          labels:
            severity: chaos-abort
          annotations:
            summary: "P99 latency exceeded 5s — aborting all chaos experiments"

        - alert: ChaosAbort_PodCrashLoop
          expr: |
            increase(kube_pod_container_status_restarts_total{namespace="staging"}[5m]) > 3
          for: 1m
          labels:
            severity: chaos-abort
          annotations:
            summary: "Pod crash-looping detected — aborting all chaos experiments"
```

### Alertmanager Webhook for Auto-Abort

```yaml
# alertmanager-config.yaml
apiVersion: v1
kind: Secret
metadata:
  name: alertmanager-config
  namespace: monitoring
stringData:
  alertmanager.yaml: |
    global:
      resolve_timeout: 1m

    route:
      receiver: 'default'
      routes:
        - match:
            severity: chaos-abort
          receiver: 'chaos-abort-webhook'
          repeat_interval: 1m

    receivers:
      - name: 'default'
        slack_configs:
          - api_url: '<slack-webhook-url>'
            channel: '#alerts'

      - name: 'chaos-abort-webhook'
        webhook_configs:
          - url: 'http://chaos-abort-controller.chaos-mesh:8080/abort'
            send_resolved: true
        slack_configs:
          - api_url: '<slack-webhook-url>'
            channel: '#chaos-engineering'
            title: 'CHAOS ABORT TRIGGERED'
            text: '{{ .CommonAnnotations.summary }}'
```

### Simple Chaos Abort Controller

```yaml
# chaos-abort-controller.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chaos-abort-controller
  namespace: chaos-mesh
spec:
  replicas: 1
  selector:
    matchLabels:
      app: chaos-abort-controller
  template:
    metadata:
      labels:
        app: chaos-abort-controller
    spec:
      serviceAccountName: chaos-abort-sa
      containers:
        - name: controller
          image: bitnami/kubectl:latest
          command:
            - /bin/bash
            - -c
            - |
              # Simple HTTP server that deletes all chaos experiments when called
              while true; do
                echo -e "HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK" | \
                nc -l -p 8080 -q 1

                echo "$(date -u) ABORT TRIGGERED — deleting all chaos experiments"

                # Delete all chaos experiments across all namespaces
                for TYPE in podchaos networkchaos stresschaos iochaos timechaos dnschaos httpchaos; do
                  kubectl delete $TYPE --all -A --ignore-not-found 2>/dev/null
                  echo "  Deleted all $TYPE"
                done

                echo "$(date -u) All chaos experiments deleted"

                # Post to Slack
                curl -s -X POST "$SLACK_WEBHOOK" \
                  -d '{"text":"All chaos experiments aborted by safety controller"}' || true
              done
          ports:
            - containerPort: 8080
          env:
            - name: SLACK_WEBHOOK
              valueFrom:
                secretKeyRef:
                  name: slack-webhook
                  key: url
---
apiVersion: v1
kind: Service
metadata:
  name: chaos-abort-controller
  namespace: chaos-mesh
spec:
  selector:
    app: chaos-abort-controller
  ports:
    - port: 8080
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: chaos-abort-sa
  namespace: chaos-mesh
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: chaos-abort-role
rules:
  - apiGroups: ["chaos-mesh.org"]
    resources: ["*"]
    verbs: ["get", "list", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: chaos-abort-binding
subjects:
  - kind: ServiceAccount
    name: chaos-abort-sa
    namespace: chaos-mesh
roleRef:
  kind: ClusterRole
  name: chaos-abort-role
  apiGroup: rbac.authorization.k8s.io
```

---

## Structuring Game Days

### The Game Day Playbook

A Game Day is not "let's break stuff and see what happens." It's a structured exercise with clear objectives, roles, and learning outcomes.

### Pre-Game Day (1-2 Weeks Before)

```markdown
## Game Day Planning Checklist

### Objectives
- [ ] Define 3-5 specific hypotheses to test
- [ ] Identify which services/teams are in scope
- [ ] Set success criteria for each experiment

### Logistics
- [ ] Schedule 3-4 hour block (avoid Mondays and Fridays)
- [ ] Book war room (physical or virtual)
- [ ] Ensure on-call engineer is NOT a participant (safety net)
- [ ] Notify customer support team about the exercise
- [ ] Prepare rollback procedures for each experiment

### Technical
- [ ] Verify monitoring dashboards are working
- [ ] Confirm alerting is functional
- [ ] Pre-create chaos experiment YAMLs
- [ ] Test abort mechanisms
- [ ] Prepare load generation (to simulate real traffic)

### Communication
- [ ] Send calendar invite with agenda
- [ ] Share experiment documents for review
- [ ] Create dedicated Slack channel: #gameday-YYYY-MM-DD
- [ ] Assign roles (see table below)
```

### Game Day Roles

| Role | Person | Responsibilities |
|------|--------|-----------------|
| **Game Master** | Senior SRE | Runs the schedule, makes abort decisions, keeps time |
| **Experimenter** | SRE/Platform Eng | Applies chaos CRDs, monitors experiments |
| **Red Team Observer** | Dev Team Lead | Watches application metrics, identifies customer impact |
| **Scribe** | Any team member | Documents everything: times, observations, decisions, surprises |
| **Safety Officer** | On-call engineer (not participating) | Monitors production for spillover, has authority to halt |
| **Stakeholder** | Engineering Manager | Observes, asks questions, sees the value (builds buy-in) |

### Game Day Agenda Template

```
09:00 - 09:30  KICKOFF
  - Review objectives and hypotheses
  - Confirm roles and communication channels
  - Verify monitoring dashboards on shared screen
  - Confirm safety officer is in place

09:30 - 09:45  STEADY STATE VERIFICATION
  - All experiments' baseline metrics recorded
  - Dashboards screenshotted for comparison
  - Load generator started (simulating normal traffic)

09:45 - 10:30  EXPERIMENT 1: Pod Failure
  - 09:45 - Apply chaos
  - 09:50 - Observe (all eyes on dashboards)
  - 10:00 - Record observations
  - 10:05 - Clean up chaos
  - 10:10 - Verify recovery
  - 10:15 - DEBRIEF: What happened? Hypothesis confirmed/refuted?
             What surprised us? Actions?

10:30 - 10:45  BREAK (mandatory — Game Days are mentally intense)

10:45 - 11:30  EXPERIMENT 2: Network Partition
  - Same structure as Experiment 1

11:30 - 12:15  EXPERIMENT 3: Database Failover
  - Same structure as Experiment 1

12:15 - 12:30  BREAK

12:30 - 13:30  WRAP-UP SESSION
  - Review all findings
  - Prioritize action items (fix critical, track others)
  - Rate the Game Day (what worked, what to improve)
  - Schedule next Game Day
  - CELEBRATE — you found weaknesses BEFORE customers did
```

### The Debrief Framework

After each experiment, use the OODA debrief:

1. **Observe**: What happened? (Just facts — metrics, events, timestamps)
2. **Orient**: Why did it happen? (Root cause analysis)
3. **Decide**: What should we do about it? (Action items)
4. **Act**: Who does what by when? (Assignments with deadlines)

```markdown
## Experiment 1 Debrief

### Observation
- Pod killed at 09:46:12
- Service endpoint updated at 09:46:15 (3s)
- 4 HTTP 503 errors between 09:46:12 and 09:46:18
- New pod ready at 09:46:38 (26s total)
- Error rate peaked at 2.1% at 09:46:14

### Orientation
- The 3-second gap between pod kill and endpoint update caused 4 errors
- Readiness probe has a 5s initial delay — could be reduced
- No retry logic in the API gateway for this path

### Decision
- Reduce readiness probe initialDelaySeconds to 2s
- Add retry-on-503 to the API gateway configuration
- Consider pod disruption budget to prevent all replicas being killed simultaneously

### Action
- @alice: Update readiness probe — due by Friday
- @bob: Add retry configuration to API gateway — due by next Tuesday
- @carol: Create PDB for backend service — due by Friday
```

---

## Analyzing Chaos Results

### Building a Chaos Results Dashboard

```yaml
# grafana-dashboard-config.yaml (key panels)
# Panel 1: Experiment Timeline
# Shows when experiments start/stop overlaid with error rate

# Prometheus queries for chaos experiment tracking:
# Active experiments count:
# count(chaos_mesh_experiments{phase="Running"})

# Panel 2: SLO Burn Rate During Chaos
# Shows how fast error budget is consumed during experiments

# Error budget burn rate:
# sum(rate(http_requests_total{code=~"5.."}[5m]))
# /
# sum(rate(http_requests_total[5m]))
# /
# (1 - 0.999)  # SLO target

# Panel 3: Recovery Time
# Time from experiment end to steady state restoration
```

### Metrics to Track Across Experiments

| Metric | How to Calculate | Target |
|--------|-----------------|--------|
| **Mean Time to Detect (MTTD)** | Time from fault injection to first alert firing | < 2 minutes |
| **Mean Time to Recovery (MTTR)** | Time from experiment end to steady state | < 5 minutes |
| **Error Budget Consumed** | (errors during chaos / total requests) vs SLO | < 10% of monthly budget per experiment |
| **Blast Radius Accuracy** | Affected services vs predicted affected services | 100% match |
| **False Positive Rate** | Alerts that fired but weren't related to the experiment | < 5% |
| **Findings per Experiment** | Improvements identified per chaos run | >= 1 |

### Tracking Resilience Over Time

```markdown
## Chaos Engineering Quarterly Report — Q1 2026

### Experiment Summary
| Month | Experiments Run | Findings | Critical Fixes | SLO Violations |
|-------|----------------|----------|----------------|----------------|
| Jan   | 12             | 8        | 2              | 0              |
| Feb   | 18             | 5        | 1              | 1 (expected)   |
| Mar   | 24             | 3        | 0              | 0              |

### Resilience Trend
- Findings per experiment decreased from 0.67 to 0.13 (80% improvement)
- All critical findings from Q4 verified as fixed
- 3 new services onboarded to continuous chaos

### Key Findings
1. Cart service circuit breaker timeout was 30s (should be 5s)
2. Payment retry logic doubled charges during network partition
3. Search cache TTL was infinite — never refreshed on backend recovery
```

---

## Building a Resilience Culture

### The Maturity Journey

```
Stage 1: SKEPTICISM
  "Why would we deliberately break our systems?"
  → Action: Run a low-risk Game Day, show the findings, demonstrate value

Stage 2: ACCEPTANCE
  "Okay, that Game Day found real bugs. Let's do another one."
  → Action: Make Game Days quarterly, involve more teams

Stage 3: ADOPTION
  "Can we automate some of these experiments in CI/CD?"
  → Action: Build the chaos pipeline, start with staging

Stage 4: INTEGRATION
  "Every deployment should pass chaos tests before reaching production."
  → Action: Gate deployments on chaos validation, run continuous chaos

Stage 5: CULTURE
  "I want to run a chaos experiment on my service before the launch."
  → Action: Provide self-service chaos tools, celebrate findings
```

### Selling Chaos to Leadership

Engineers usually understand the value of Chaos Engineering. Leadership often needs convincing. Here's a framework:

**The Cost Argument:**
- Average cost of a severity-1 incident at your company: $X per hour
- Number of sev-1 incidents per year: Y
- Total annual cost: $X * Y * average_duration_hours
- Cost of Chaos Engineering program: 1 engineer's time + tooling
- Expected incident reduction (industry average): 40-60%
- ROI: ($X * Y * avg_hours * 0.5) - program_cost

**The Compliance Argument:**
- SOC 2 Type II requires demonstrating operational resilience
- PCI DSS 4.0 requires testing security controls
- FedRAMP requires disaster recovery testing
- Game Days and chaos experiments provide audit evidence for all of these

**The Talent Argument:**
- Top engineers want to work at organizations with mature engineering practices
- A chaos engineering program signals engineering maturity
- It reduces on-call burnout (fewer surprises = less firefighting)

---

## Common Mistakes

| Mistake | Why It's a Problem | Better Approach |
|---------|-------------------|-----------------|
| Running chaos in CI/CD without automated abort | A failed experiment in an unattended pipeline can degrade staging for hours before anyone notices | Always wire Prometheus alerts to an abort controller; never run unattended chaos without automated safety |
| Making Game Days mandatory attendance | Forced participation breeds resentment; people attend physically but don't engage mentally | Make Game Days engaging and voluntary; share exciting findings afterward to build FOMO |
| Skipping the steady-state verification step in CI | If the system is already unhealthy when chaos starts, you can't distinguish chaos impact from pre-existing issues | Always verify steady state BEFORE injecting chaos; fail the pipeline if the baseline is already violated |
| Running the same experiments every time | After the third identical pod-kill experiment, you're not learning anything new — you're just confirming what you already know | Maintain an experiment backlog; rotate experiments; increase blast radius over time; target new services |
| Not cleaning up experiments on pipeline failure | If the CI job fails mid-experiment (runner dies, timeout), the chaos CRDs remain active indefinitely | Use `if: always()` cleanup steps; set short durations on chaos CRDs; have a cron job that deletes old experiments |
| Treating Game Day findings as "nice to haves" | If findings are filed as low-priority tickets that never get fixed, the program loses credibility and participants stop engaging | Treat critical Game Day findings like production incidents — they get the same priority and SLA as a real outage |
| No executive summary after Game Days | Technical details in a Confluence page that nobody reads provides no organizational learning | Write a 1-page executive summary with findings, business risk, and cost of not fixing; present at the next all-hands |

---

## Quiz

### Question 1: Why should chaos experiments in CI/CD run AFTER deployment stabilization, not immediately after deploy?

<details>
<summary>Show Answer</summary>

Immediately after deployment, pods may still be starting, health checks may be initializing, caches are cold, and connection pools are being established. Running chaos during this period tests the deployment's startup behavior, not its steady-state resilience.

If you inject a pod-kill during rolling deployment, you're testing a combination of "can it deploy" and "can it survive chaos" simultaneously. You can't distinguish which one caused a failure. By waiting for stabilization (60-120 seconds after all pods are Ready), you ensure the deployment is complete and steady state is established before measuring the impact of chaos.

</details>

### Question 2: What is the purpose of the abort controller, and why can't Chaos Mesh's built-in duration be the only safety mechanism?

<details>
<summary>Show Answer</summary>

The abort controller provides **external safety** that can stop experiments immediately when SLOs are violated, regardless of the experiment's configured duration.

Chaos Mesh's `duration` field only controls how long the fault is injected — it cannot react to real-time conditions. If you set `duration: 300s` but the system starts failing catastrophically at second 15, the experiment continues for another 285 seconds, causing unnecessary damage.

The abort controller watches Prometheus metrics and can delete chaos experiments the moment an SLO threshold is crossed, typically within 30-60 seconds. This provides:
1. **Faster response** than waiting for the duration to expire
2. **Business-metric-aware** safety (error rate, transaction volume) vs. time-based only
3. **Cross-experiment** safety — if multiple experiments are running and their combined impact exceeds thresholds, all are aborted

</details>

### Question 3: Why is the Scribe role important during a Game Day?

<details>
<summary>Show Answer</summary>

The Scribe captures real-time observations, decisions, and timestamps that would otherwise be lost. During a Game Day, everyone is focused on dashboards and their own responsibilities. Without a dedicated Scribe:

1. **Timestamps are lost**: "I think the alert fired around 10:15" is useless; "Alert `HighErrorRate` fired at 10:14:32 UTC" is actionable data
2. **Decisions aren't recorded**: Why did the team decide to continue instead of abort? That context matters for the debrief
3. **Observations aren't captured**: An engineer notices a brief CPU spike at 10:16 but doesn't mention it because they're focused on the next experiment. The Scribe catches these peripheral observations
4. **Action items are forgotten**: Verbal agreements during the heat of the moment evaporate unless written down immediately
5. **The report is harder to write**: Without real-time notes, the post-Game Day report becomes a reconstruction from memory, which is unreliable

The Scribe's notes become the primary source for the debrief, the executive summary, and the action items.

</details>

### Question 4: You run chaos experiments in CI/CD every night. For the past 3 weeks, all experiments have passed. Is this good news?

<details>
<summary>Show Answer</summary>

It depends, and potentially **no** — it might mean your experiments are too weak or too repetitive.

Three weeks of passing experiments could mean:
1. **Good**: Your system is genuinely resilient to the tested failure modes
2. **Bad**: Your experiments aren't challenging enough (small blast radius, short duration, fault types the system easily handles)
3. **Bad**: You're running the same experiments every night without variation, confirming known resilience without testing new scenarios
4. **Bad**: Your SLO thresholds for pass/fail are too lenient (5% error rate threshold when real users notice at 1%)

To evaluate, ask:
- When was the last time an experiment **failed**? If never, the experiments may not be rigorous enough
- Are you rotating experiment types and targets?
- Have you increased blast radius since the initial setup?
- Are the SLO thresholds aligned with real user expectations?

A healthy chaos program should have an experiment failure rate of 10-20% — frequent enough to provide new insights, infrequent enough that the system is generally resilient.

</details>

### Question 5: How do you handle the situation where a Game Day experiment reveals a critical vulnerability in production?

<details>
<summary>Show Answer</summary>

Treat the finding exactly like a production incident discovery:

1. **Immediately**: Assess the real risk. Is this vulnerability actively exploitable in production right now? If yes, it becomes a P1 incident regardless of the Game Day.

2. **During the Game Day**: Document the finding thoroughly. Do NOT attempt to fix it during the Game Day — fixes require proper code review and testing, not rushed patches.

3. **After the Game Day**: Create a P1/S1 ticket with the finding. Include the exact reproduction steps (the chaos experiment configuration), the observed impact, and the potential production risk.

4. **Mitigation**: If the vulnerability can be mitigated immediately (e.g., adding a circuit breaker configuration change), do that as a temporary fix while a permanent fix is developed.

5. **Communication**: Include the finding in the Game Day executive summary and highlight it as a critical discovery that prevented a potential production incident. This is the strongest possible evidence of the Game Day's value.

6. **Verification**: After the fix is deployed, re-run the exact same chaos experiment to verify the fix. Add this experiment to the CI/CD chaos suite to prevent regression.

</details>

### Question 6: What is the difference between gating deployments on chaos tests and running chaos as a post-deployment check?

<details>
<summary>Show Answer</summary>

**Gating (pre-deployment)**: The chaos experiments run against the new version in a staging/canary environment, and the deployment to production is blocked if any experiment fails. This prevents known-fragile code from reaching production. The tradeoff is that it adds 15-30 minutes to every deployment pipeline.

**Post-deployment check**: The new version is deployed to production first, then chaos experiments run to verify resilience. If experiments fail, an alert is raised and the team decides whether to rollback. This is faster but riskier — the fragile code is already in production.

The recommended progression:
1. Start with **post-deployment checks** in staging
2. Move to **gating** in staging (block production deploy on staging chaos failure)
3. Eventually, run **post-deployment checks** in production with automated canary rollback

Never gate production deployments on production chaos experiments — the blast radius of a failed experiment affecting a just-deployed canary is too unpredictable.

</details>

---

## Hands-On Exercise: GitHub Actions Chaos Pipeline

### Objective

Create a complete GitHub Actions workflow that deploys an application, verifies steady state, injects a Chaos Mesh pod-kill experiment, validates that SLOs were maintained, and cleans up — all automatically.

### What You'll Build

```
GitHub Actions Workflow:
  Job 1: Deploy    → Apply K8s manifests, wait for ready
  Job 2: Verify    → Check error rate < 0.5%, p99 < 500ms
  Job 3: Chaos     → Pod-kill 1 backend pod for 120s
  Job 4: Validate  → Check error rate < 1%, p99 < 2s during chaos
  Job 5: Cleanup   → Delete chaos CRDs, report results
```

### Step 1: Create the Workflow File

Create `.github/workflows/chaos-pipeline.yaml` using the complete pipeline template from earlier in this module. Adapt it for your cluster by:

1. Replacing `${{ secrets.KUBECONFIG }}` with your cluster's kubeconfig
2. Replacing the Prometheus URL with your monitoring endpoint
3. Adjusting namespace names to match your environment
4. Adjusting SLO thresholds to match your application

### Step 2: Create the Chaos Experiment Templates

```bash
# Create a directory for chaos experiment templates
mkdir -p chaos-experiments/

# Create pod-kill template
cat > chaos-experiments/pod-kill.yaml << 'EOF'
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: ci-pod-kill-${GITHUB_RUN_ID}
  namespace: staging
  labels:
    chaos-source: ci-cd
    run-id: "${GITHUB_RUN_ID}"
spec:
  action: pod-kill
  mode: one
  selector:
    namespaces:
      - staging
    labelSelectors:
      app: backend
  gracePeriod: 0
  duration: "120s"
EOF

# Create network delay template
cat > chaos-experiments/network-delay.yaml << 'EOF'
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: ci-network-delay-${GITHUB_RUN_ID}
  namespace: staging
  labels:
    chaos-source: ci-cd
    run-id: "${GITHUB_RUN_ID}"
spec:
  action: delay
  mode: all
  selector:
    namespaces:
      - staging
    labelSelectors:
      app: backend
  delay:
    latency: "200ms"
    jitter: "50ms"
    correlation: "75"
  direction: to
  target:
    selector:
      namespaces:
        - staging
      labelSelectors:
        app: api-gateway
    mode: all
  duration: "180s"
EOF
```

### Step 3: Create the SLO Validation Script

```bash
# Create a reusable SLO validation script
cat > chaos-experiments/validate-slos.sh << 'SCRIPT'
#!/bin/bash
set -euo pipefail

PROMETHEUS_URL="${PROMETHEUS_URL:-http://prometheus.monitoring:9090}"
NAMESPACE="${NAMESPACE:-staging}"
ERROR_RATE_THRESHOLD="${ERROR_RATE_THRESHOLD:-1.0}"
LATENCY_THRESHOLD="${LATENCY_THRESHOLD:-2.0}"
LOOKBACK="${LOOKBACK:-3m}"

echo "=== SLO Validation ==="
echo "Prometheus: $PROMETHEUS_URL"
echo "Namespace: $NAMESPACE"
echo "Error Rate Threshold: ${ERROR_RATE_THRESHOLD}%"
echo "P99 Latency Threshold: ${LATENCY_THRESHOLD}s"
echo "Lookback Window: $LOOKBACK"

# Query error rate
ERROR_RATE=$(curl -sf "$PROMETHEUS_URL/api/v1/query" \
  --data-urlencode "query=sum(rate(http_requests_total{namespace=\"$NAMESPACE\",code=~\"5..\"}[${LOOKBACK}])) / sum(rate(http_requests_total{namespace=\"$NAMESPACE\"}[${LOOKBACK}])) * 100" \
  | jq -r '.data.result[0].value[1] // "0"')

echo "Error Rate: ${ERROR_RATE}%"

# Query p99 latency
P99=$(curl -sf "$PROMETHEUS_URL/api/v1/query" \
  --data-urlencode "query=histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{namespace=\"$NAMESPACE\"}[${LOOKBACK}])) by (le))" \
  | jq -r '.data.result[0].value[1] // "0"')

echo "P99 Latency: ${P99}s"

# Evaluate
PASS=true

if (( $(echo "$ERROR_RATE > $ERROR_RATE_THRESHOLD" | bc -l) )); then
  echo "FAIL: Error rate ${ERROR_RATE}% exceeds threshold ${ERROR_RATE_THRESHOLD}%"
  PASS=false
fi

if (( $(echo "$P99 > $LATENCY_THRESHOLD" | bc -l) )); then
  echo "FAIL: P99 latency ${P99}s exceeds threshold ${LATENCY_THRESHOLD}s"
  PASS=false
fi

if [ "$PASS" = true ]; then
  echo "PASS: All SLOs maintained"
  exit 0
else
  echo "FAIL: SLO violations detected"
  exit 1
fi
SCRIPT

chmod +x chaos-experiments/validate-slos.sh
```

### Step 4: Create the Cleanup Script

```bash
# Create a cleanup script that removes all CI-created chaos experiments
cat > chaos-experiments/cleanup.sh << 'SCRIPT'
#!/bin/bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-staging}"

echo "=== Chaos Cleanup ==="
echo "Removing all chaos experiments with label chaos-source=ci-cd"

for TYPE in podchaos networkchaos stresschaos iochaos timechaos dnschaos httpchaos; do
  COUNT=$(kubectl get $TYPE -n $NAMESPACE -l chaos-source=ci-cd --no-headers 2>/dev/null | wc -l)
  if [ "$COUNT" -gt 0 ]; then
    kubectl delete $TYPE -n $NAMESPACE -l chaos-source=ci-cd
    echo "Deleted $COUNT $TYPE resources"
  fi
done

echo "=== Cleanup Complete ==="

# Verify no experiments remain
REMAINING=$(kubectl get podchaos,networkchaos,stresschaos -n $NAMESPACE --no-headers 2>/dev/null | wc -l)
echo "Remaining experiments: $REMAINING"

if [ "$REMAINING" -gt 0 ]; then
  echo "WARNING: Some experiments still active:"
  kubectl get podchaos,networkchaos,stresschaos -n $NAMESPACE
fi
SCRIPT

chmod +x chaos-experiments/cleanup.sh
```

### Step 5: Test Locally (Without GitHub Actions)

If you don't have GitHub Actions runners connected to your cluster, test the pipeline locally:

```bash
# 1. Deploy the application
kubectl apply -f k8s/staging/
kubectl rollout status deployment/backend -n staging --timeout=120s

# 2. Wait for stabilization
sleep 60

# 3. Verify steady state
./chaos-experiments/validate-slos.sh

# 4. Apply chaos experiment
kubectl apply -f chaos-experiments/pod-kill.yaml

# 5. Wait for experiment
sleep 130

# 6. Validate SLOs
ERROR_RATE_THRESHOLD=1.0 LATENCY_THRESHOLD=2.0 ./chaos-experiments/validate-slos.sh

# 7. Clean up
./chaos-experiments/cleanup.sh
```

### Success Criteria

- [ ] Workflow file created with all 5 jobs (deploy, verify, chaos, validate, cleanup)
- [ ] Cleanup runs even when previous jobs fail (`if: always()`)
- [ ] SLO validation checks both error rate AND latency
- [ ] Chaos experiment CRDs are labeled for easy cleanup (`chaos-source: ci-cd`)
- [ ] The workflow can run on schedule (nightly) and on push
- [ ] Slack notification fires on failure
- [ ] You can explain what each job does and why the ordering matters
- [ ] Experiment duration is shorter than the validation wait time (no checking stale metrics)

### Bonus Challenge

Extend the pipeline to include:
1. A network delay experiment that runs after the pod-kill experiment
2. A Grafana annotation API call that marks experiment start/end times on dashboards
3. A job that commits the chaos results to a `chaos-reports/` directory in the repo

---

## Summary

Automating chaos transforms resilience verification from a quarterly event into a continuous practice. CI/CD integration catches resilience regressions on every deployment. Prometheus-based abort controllers provide automated safety nets for unattended experiments. Structured Game Days combine the depth of manual investigation with the rigor of predefined hypotheses and debriefs. Together, they build a culture where resilience is verified, not assumed.

Key takeaways:
- **Automate the routine** — pod-kill and network delay experiments should run in CI/CD
- **Keep humans for the complex** — Game Days test multi-service, cross-team scenarios
- **Abort automatically** — Prometheus alerts triggering experiment deletion is non-negotiable for unattended chaos
- **Analyze and share** — findings without action items and executive summaries provide no organizational value
- **Build culture gradually** — skepticism → acceptance → adoption → integration → culture

---

## Next Module

Return to the [Chaos Engineering README]() to review the complete discipline, explore further reading, and find links to related platform engineering tracks.
