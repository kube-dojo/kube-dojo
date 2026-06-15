---
title: "Module 1.5: Automating Chaos & Game Days"
slug: platform/disciplines/reliability-security/chaos-engineering/module-1.5-automating-chaos
sidebar:
  order: 6
revision_pending: false
---
> **Discipline Module** | Complexity: `[MEDIUM]` | Time: 2 hours

## Prerequisites

Before starting this module:
- **Required**: [Module 1.3: Network & Application Fault Injection](../module-1.3-network-fault-injection/) — Familiarity with multiple chaos experiment types
- **Required**: CI/CD fundamentals — GitHub Actions, GitLab CI, or equivalent pipeline experience
- **Recommended**: [SRE Module 1.2: SLOs](/platform/disciplines/core-platform/sre/module-1.2-slos/) — Understanding SLOs and error budgets
- **Recommended**: Prometheus and Grafana basics

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Design automated chaos engineering pipelines that run experiments on schedule and in CI/CD**
- **Implement GameDay exercises that combine multiple chaos experiments into realistic failure scenarios**
- **Build chaos experiment result tracking that measures resilience improvements over time**
- **Configure automated abort conditions that halt experiments when unexpected blast radius is detected**

## Why This Module Matters

The real value of chaos engineering is not in running a single experiment — it is in making resilience verification a routine, automated practice that catches regressions before they reach production. When chaos experiments are manual, one-off events, they compete with every other engineering priority for attention. Engineers intend to run them quarterly but skip a round when a launch deadline approaches, and the discipline atrophies.

In October 2021, a backbone router misconfiguration took Facebook, Instagram, and WhatsApp offline for six hours — and the engineers trying to fix it lost access to their own internal recovery tooling because it ran on the same downed infrastructure. <!-- incident-xref: facebook-2021-bgp --> For the full case study, see [Route 53 & DNS](../../../../cloud/aws-essentials/module-1.5-route53/).

The answer: Facebook's internal tools (including the ones engineers needed to fix the problem) ran on the same infrastructure that was down. Engineers lost access to important internal recovery tooling and faced unusually difficult network and physical access during the outage. The recovery tools were victims of the same failure they were supposed to fix.

The outage illustrates why teams should drill recovery-path dependencies and validate risky network changes before deployment. But the deeper lesson is about automation: if Facebook had been running automated chaos experiments that specifically tested network path failure and recovery tooling availability, the vulnerability might have been surfaced before the configuration change that triggered it — during a controlled experiment, not a six-hour global outage.

This module teaches you to move chaos engineering from manual experiments into automated pipelines and structured Game Days. The goal is to make resilience verification as routine as running unit tests — something that happens on every deployment, not something an engineer remembers to do once a quarter.

### Hypothetical scenario:

A platform team runs manual chaos experiments quarterly. For three quarters straight, the pod-kill experiment passes — the application recovers cleanly within 80 seconds. The team feels confident. What they do not know is that last quarter's database migration added a connection-pool dependency that makes pod restarts take 4x longer when the pool is saturated. The quarterly experiment happened during low traffic at 10 PM. If that same experiment had run during a Tuesday 2 PM peak — or in a CI/CD pipeline on every deployment — the regression would have been caught immediately. Instead, it surfaced during a real pod eviction six weeks later, causing a 9-minute outage during business hours. By automating the experiment and varying the timing, the team would have discovered the vulnerability in a controlled setting rather than in production.

---

## The Chaos Maturity Ladder

Chaos engineering programs progress through distinct stages of automation. Understanding where your organization sits on this ladder helps you plan the next increment — the capabilities, safety mechanisms, and cultural readiness required at each rung.

### Stage 1: Ad-Hoc Manual Experiments

An engineer reads about chaos engineering, installs Chaos Mesh on a staging cluster, and manually applies a pod-kill experiment. They watch Grafana dashboards, observe the recovery, and document findings in a shared document. This is where nearly every team starts, and it produces genuine value — the first experiment almost always finds something surprising.

The limitation of ad-hoc experiments is coverage: they happen when someone remembers, they test whatever scenario that person thinks of, and the blast radius selection is driven by comfort rather than risk. A cluster running 60 microservices may only ever see experiments against the three services the chaos-curious engineer works on. The other 57 services remain untested. Worse, the experiments are not reproducible — the exact configuration, the baseline metrics at the time, and the detailed observations live in an engineer's terminal history.

### Stage 2: Scheduled GameDays

A team commits to a quarterly GameDay. Experiments are documented in advance, roles are assigned (Game Master, Scribe, Observers), and hypotheses are written down. The structured format means experiments are reproducible, and the formal debrief produces tracked action items.

The jump from ad-hoc to scheduled is largely a cultural one — it requires an engineering manager who prioritizes the exercise even when the roadmap is full. The technical tooling at this stage is still mostly manual, but the organizational commitment means experiments happen consistently. A quarterly GameDay testing five hypotheses produces twenty documented findings per year. Those findings feed into the reliability backlog with the same priority as production incidents.

### Stage 3: Automated Pipeline Experiments

The team encodes chaos experiments as part of the CI/CD pipeline. A deployment to staging triggers a steady-state verification, followed by a suite of chaos experiments, followed by automated SLO validation. If the experiments pass, the deployment proceeds. If they fail, the pipeline blocks the deployment and notifies the team.

The key enabler at this stage is the **automated abort controller** — a safety mechanism that watches SLOs during unattended experiments and deletes chaos resources if error rates or latency breach thresholds. Without automated abort, unattended chaos is reckless. With it, the pipeline can run experiments on every PR merge, every nightly build, and every pre-release candidate.

### Stage 4: Continuous Production Chaos

The highest maturity level: chaos experiments run continuously in production, with tightly scoped blast radii and fully automated abort-and-rollback mechanisms. The goal is not to break production but to verify, minute by minute, that resilience mechanisms are functional. If a circuit breaker stops working because of a configuration change, continuous chaos detects it within the experiment interval — not during the next quarter's GameDay. The experiment interval might be 30 minutes for critical paths and 2 hours for less critical services, creating a detection window that is orders of magnitude tighter than quarterly manual testing.

Continuous production chaos requires mature observability, automated canarying, and a culture that treats a failed chaos experiment exactly like a failed test in CI — an expected, valuable signal rather than a cause for alarm. Very few organizations operate at this level, and most should not attempt it without first mastering stages 1–3. The progression is cumulative: each stage builds the safety infrastructure and organizational trust required for the next. The jump from Stage 3 (automated pipeline) to Stage 4 (continuous production) is primarily a cultural one — the technical building blocks are the same abort controllers, CRDs, and Prometheus rules. What changes is the organizational confidence that the guardrails hold and that a failed experiment at 3 AM on a Sunday will be automatically contained before any customer notices.

Each rung on the ladder increases the surface area of resilience verification — more services, more failure modes, more frequent testing. But each rung also demands more sophisticated safety automation. The ladder is not a race; organizations that skip rungs inevitably experience an uncontrolled incident that sets the program back by eroding trust. Progress deliberately: master manual experiments before you schedule them, master scheduled experiments before you automate them, and master automated experiments before you run them continuously in production.

---

## Automating the Experiment Loop

Manual chaos experiments follow a mental checklist: open a terminal, apply a chaos CRD, watch Grafana, decide if things look okay, delete the CRD, write notes. When you automate this loop, you encode every step — the hypothesis, the steady-state check, the experiment application, the SLO validation, and the cleanup — as machine-executable definitions that run without human judgment in the loop.

### Encoding Experiments as CRDs

Chaos Mesh provides two CRDs that are central to automation: `Schedule` and `Workflow`. A `Schedule` object defines a recurring chaos experiment, analogous to a Kubernetes CronJob. You specify the experiment type (pod-kill, network-delay, stress-chaos), the target selector, the duration, and a cron expression for the recurrence. The Chaos Mesh controller manager handles the scheduling — it creates the actual chaos CRD objects at the specified intervals and cleans them up when the duration expires.

A `Workflow` object orchestrates multiple experiments in sequence or in parallel, with conditional branching based on outcomes. This is the building block for a GameDay encoded as code: a workflow that runs a steady-state verification step, then a pod-kill experiment, then a network-partition experiment, then a comprehensive SLO validation step, and finally a cleanup step. If any experiment fails, the workflow can branch to an abort path or notify the team.

Encoding experiments as CRDs means they live in version control alongside application code. The chaos experiment that validates circuit-breaker resilience can be reviewed in the same PR that modifies the circuit-breaker configuration. The experiment becomes documentation of expected behaviour — a living specification that says "this service should survive a 200ms network delay between the API gateway and the backend, with P99 latency remaining under 2 seconds."

### Automating Steady-State Verification

The steady-state verification step is what distinguishes a chaos experiment from a controlled outage. Before injecting any fault, the automation must confirm that the system is healthy — error rates are within expected bounds, latency is within SLOs, all pods are Ready, and load-generation traffic is flowing. If the steady-state is already violated, injecting chaos makes the situation worse and produces meaningless results (because you cannot attribute the failure to the experiment versus the pre-existing condition).

In a pipeline context, steady-state verification is a gate: if the baseline is unhealthy, the chaos stage is skipped entirely and the pipeline reports "baseline failure — cannot proceed." This prevents the most common chaos-automation failure mode, where a broken staging environment goes undetected for hours because the chaos experiments ran against an already-broken system and nobody noticed.

### Automated Abort: The Critical Safety Net

When chaos experiments run unattended, the most important component is not the experiment itself — it is the mechanism that stops the experiment when things go wrong. Chaos Mesh's `duration` field is a time-based limit, not a condition-based one. If the experiment is configured to run for 180 seconds but the system starts failing catastrophically at second 15, the experiment continues for another 165 seconds, compounding the damage. The duration field answers "how long should this fault last in ideal conditions?" — it cannot answer "should this fault still be running given current system health?"

The automated abort controller solves this by watching real-time SLO metrics and deleting chaos resources the moment a threshold is breached. In practice, this means Prometheus alerting rules wired to a webhook that calls `kubectl delete` on all active chaos experiments in the affected namespace. The controller operates independently of the chaos pipeline — it is a separate process that watches metrics regardless of which experiment is running or who started it. This separation is essential: if the abort mechanism were part of the same pipeline that started the experiment, a pipeline failure (runner crash, network partition) would disable the safety mechanism at the exact moment it is needed most.

Designing the abort thresholds requires judgment. Set them too tight, and every experiment triggers an abort — the pipeline never completes, and the team stops trusting the signal. Set them too loose, and the abort controller never fires — the system degrades for the full experiment duration, and the team wonders why they built it. A practical starting point: set the abort threshold at 2–3x the SLO threshold. If the SLO allows 1% error rate, abort when the error rate reaches 2–3% during an experiment. This gives the system room to recover autonomously while preventing unbounded degradation.

---

## Integrating Chaos into CI/CD

The step from manual chaos to CI/CD-integrated chaos is the single highest-leverage transition in a chaos engineering program. It transforms resilience verification from a scheduled event that competes for calendar time into a continuous signal that fires on every deployment. The core insight is that a chaos experiment has the same structure as a test: a setup step (deploy), a precondition check (steady state), an action (inject fault), an assertion (validate SLOs), and a teardown (cleanup). Once you see chaos experiments as tests, integrating them into a pipeline becomes a matter of engineering, not a conceptual leap.

### The Chaos Pipeline Pattern

The fundamental pattern is: **deploy → verify steady state → inject chaos → validate SLOs → clean up**. This sequence ensures that chaos experiments test the deployment's resilience, not its startup behaviour, and that every step has a clear pass/fail outcome that gates the next step.

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

The timing matters. Chaos must run **after** deployment stabilization, not during it. A typical deployment involves pods starting, health checks initializing, connection pools warming up, and caches populating. Running chaos during this window conflates deployment reliability with resilience — you cannot distinguish whether a failure came from a broken deployment or a fragile recovery mechanism. A 60–120 second stabilization delay between deployment and steady-state verification gives the system time to reach its operating baseline.

### Chaos as a Deployment Gate

A chaos experiment in CI/CD is a test with a binary outcome: the system maintained SLOs during the experiment (pass) or it did not (fail). When you gate deployments on chaos-test results, you treat a failed experiment identically to a failed unit test — the deployment is blocked, the team is notified, and the system is rolled back to the last known-good state. This is a profound shift in how organizations think about resilience: it is no longer a property you hope the system has but a property you verify on every change.

The practical trade-off is time. A chaos suite that takes 15 minutes to run adds 15 minutes to every deployment pipeline. For teams deploying multiple times per day, this overhead is non-trivial. The solution is tiered chaos: light experiments on every PR merge (pod-kill, 2–5 minutes), medium experiments on nightly builds (network delay + resource stress, 10–15 minutes), and comprehensive experiments on pre-release candidates (multi-fault workflows, 30–60 minutes). This tiering preserves deployment velocity while progressively increasing confidence as a change approaches production. A PR merge that passes pod-kill chaos is unlikely to break catastrophically on deployment. A release candidate that passes the full suite has been tested against every failure mode the team knows how to simulate.

### Chaos in Progressive Delivery

When combined with progressive delivery strategies like canary deployments or Argo Rollouts, chaos experiments become part of the analysis step that determines whether a canary is healthy enough to promote. Instead of only checking latency and error rate, the analysis also injects controlled faults and verifies that the canary's resilience matches the stable version. This integration closes a dangerous gap: a deployment can pass standard health checks — pods are running, endpoints are reachable, error rates are normal — while carrying a resilience regression that would only surface under stress.

This is where chaos engineering and deployment strategy converge. A canary that passes standard health checks but fails a pod-kill experiment should not be promoted — its resilience has regressed relative to the stable version. The analysis step in Argo Rollouts supports custom metric queries, which means you can plug Prometheus queries for chaos experiment results directly into the canary promotion criteria. A canary analysis template that includes both standard metrics (latency, error rate) and chaos experiment results creates a defense-in-depth gate: the canary must be both healthy and resilient before it receives production traffic.

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

## Guardrails for Unattended Chaos

Running chaos experiments without human oversight introduces risks that manual experiments avoid by having an engineer watching dashboards. The solution is not to avoid unattended chaos but to build guardrails that replicate the vigilance of a human operator — automatically, consistently, and faster than any human could react.

### Blast-Radius Limits

Every automated experiment must declare its blast radius explicitly, and that declaration must be enforceable. This means using namespace-scoped chaos CRDs with RBAC that prevents chaos controllers from operating outside designated namespaces. Chaos Mesh supports namespace-level configuration that restricts which namespaces can host chaos experiments — a staging chaos controller should never be able to inject faults into production namespaces.

The blast radius should also be scoped by selector specificity. A `mode: all` selector targeting the label `app: backend` in staging is reasonable. The same selector with `mode: all` and no namespace restriction is a production incident waiting to happen. Automating chaos means automating the discipline of selector scoping.

### Business-Hours Windows and Blackout Periods

Some experiments are safe to run unattended at 2 AM on a Wednesday but would be disruptive during a Monday morning production deployment window. Chaos Mesh `Schedule` objects support cron expressions, which means you can express time-window constraints directly in the schedule definition. A nightly chaos suite that runs between 2 AM and 4 AM on weekdays — and never on weekends when the on-call rotation has reduced staffing — is a deliberate safety choice.

More sophisticated guardrails involve integration with deployment calendars and change-freeze windows. If your organization has a policy of no non-essential changes during the last week of a quarter, your chaos scheduler should honour that policy. The simplest implementation is a separate job in the pipeline that checks a shared calendar before applying chaos experiments.

### Kill Switches and Exclude-Lists

Every automated chaos infrastructure needs a kill switch — a mechanism that immediately and irrevocably stops all chaos experiments across all environments, regardless of who started them or what stage they are in. In Chaos Mesh, this can be implemented as a Kubernetes validating admission webhook that blocks the creation of new chaos CRDs, combined with a cluster-level job that deletes all existing chaos resources.

The kill switch should be triggerable from a single command, by any member of the on-call rotation, without requiring Kubernetes expertise. A Slack bot command (`!chaos-abort`), a PagerDuty incident action, or a big red button in the chaos dashboard all serve this purpose. The kill switch is the circuit breaker for the chaos program itself — when tripped, it stops all experiments until a post-incident review determines it is safe to resume.

Exclude-lists complement kill switches by preventing specific services or namespaces from ever being targeted. A payment-processing service with a 99.999% uptime requirement should be on the exclude-list for all automated experiments — it can still be tested in carefully supervised GameDays, but never by an unattended pipeline.

### Observability and Attribution

When chaos experiments run unattended, every anomaly in the monitoring system needs to be attributable. Is the spike in error rate caused by a chaos experiment, a real incident, or a deployment regression? Without clear attribution, chaos experiments create noise that erodes trust in monitoring and wastes on-call engineer time. Teams that fail to solve attribution invariably abandon automated chaos after their first false alarm — an on-call engineer spends 90 minutes investigating a "production incident" that turns out to be a scheduled pod-kill experiment in staging that bled into a shared metrics namespace.

Attribution requires two things: labels on chaos CRDs that identify the experiment source (pipeline run ID, experiment name, triggering event), and annotations on Prometheus metrics or Grafana dashboards that overlay experiment timelines on top of system metrics. When an on-call engineer sees a latency spike at 3:17 AM, they should be able to determine within seconds whether a chaos experiment was active at that time and, if so, which one.

Chaos Mesh experiments are Kubernetes resources, which means they carry standard labels and annotations. A convention of labeling every experiment with `chaos-source: ci-cd` or `chaos-source: scheduled` and including the pipeline run ID or schedule name makes attribution queries straightforward. The convention should be enforced by a validating admission webhook that rejects chaos CRDs without the required labels — if an experiment cannot be attributed, it should not be created.

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
          image: bitnamilegacy/kubectl:latest
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

A Game Day is not "let's break stuff and see what happens." It's a structured exercise with clear objectives, roles, and learning outcomes. The purpose is to test socio-technical resilience — how your systems, your people, your runbooks, your monitoring, and your communication channels behave together under stress.

Game Days complement automated chaos experiments. Automated experiments verify known resilience mechanisms against known failure modes — circuit breakers open, retries work, failover completes. Game Days explore the unknown: what happens when multiple failures cascade in ways you did not anticipate, when the runbook is wrong, when the on-call engineer who knows the obscure recovery procedure is on vacation.

The distinction matters because you make different investments for each. Automated experiments justify investment in SLO instrumentation, abort controllers, and pipeline infrastructure. Game Days justify investment in runbook quality, cross-team communication protocols, and organizational learning processes. Both are necessary; neither replaces the other.

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

## Measuring and Improving the Program

A chaos engineering program, once automated, generates data. The question is whether you measure the right things — and whether you use those measurements to improve the program itself.

### Metrics Worth Tracking

The primary purpose of chaos engineering is to find weaknesses before they cause incidents. Therefore the most honest metric is **findings per experiment** — how many previously unknown resilience gaps does each experiment surface? A healthy chaos program should produce a steady stream of findings, especially after expanding to new services or introducing new experiment types.

**Mean time to detect (MTTD)** during experiments measures how fast your monitoring catches a fault. If a pod-kill experiment takes 26 seconds for the pod to recover but 90 seconds for an alert to fire, your detection gap is 64 seconds — time during which the on-call engineer has no signal.

**Mean time to recovery (MTTR)** during experiments measures the actual recovery time, not the theoretical time. If your runbook says failover takes 5 seconds but experiments consistently show 30 seconds, the runbook is wrong.

**Error budget consumed per experiment** measures the blast radius in SLO terms. If each experiment consumes 5% of the monthly error budget, you cannot run experiments frequently without exhausting the budget. This metric forces a conversation about SLO thresholds — if the SLO is set so tightly that even a controlled experiment violates it, either the SLO is unrealistic or the experiment's blast radius is too large.

**Experiments that passed without findings for 4+ consecutive weeks** is a leading indicator that your experiment suite has stagnated. If you are running the same pod-kill and network-delay experiments every night and they pass every night, you are not learning anything new. Rotate experiment types, increase blast radius, or target new services. A mature chaos program treats a passing experiment without a finding not as a success to celebrate but as a signal to ask: "what should we test next?"

### Avoiding Vanity Metrics

The most seductive trap in measuring a chaos program is to optimize for metrics that look good but measure nothing useful. "Number of experiments run" is a vanity metric — running 1000 experiments that all pass tells you the experiments are too weak. "Experiments passed" is even worse — it creates an incentive to lower SLO thresholds and reduce blast radii so the dashboard stays green. If you find yourself tweaking SLO thresholds to make experiments pass more often, you are optimizing the wrong variable.

Goodhart's law applies directly here: when a metric becomes a target, it ceases to be a good metric. If your team's quarterly goal is "run 48 chaos experiments," they will run 48 experiments — but they will choose the fastest, safest, least-informative ones. Instead, set goals on outcomes: "surface and fix six resilience gaps this quarter," or "reduce the gap between detected and recovered MTTR by 50%." The distinction between activity metrics and outcome metrics is the difference between looking busy and actually improving resilience.

### Analyzing Chaos Results

Collecting data from automated experiments is necessary but insufficient. The data must be visible, interpretable, and actionable — not buried in CI/CD logs that nobody reads. A chaos results dashboard serves three audiences: the platform team running the experiments (who need real-time experiment status and SLO overlays), the engineering manager tracking the program (who needs trends in findings and fixes over time), and the on-call engineer investigating an anomaly (who needs rapid experiment attribution).

Every experiment that runs should produce a durable record: a timestamp, the experiment type and target, the pre-experiment steady-state metrics, the SLO metrics during the experiment, and the pass/fail outcome. This record enables two critical analyses. First, correlation: if error rates spiked at 3:17 AM and a chaos experiment was active at that time, the experiment is the likely cause — but only if the record exists. Second, trend analysis: plotting findings per experiment over quarters shows whether the program is maturing (declining findings as weaknesses are fixed) or stagnating (flat findings, suggesting the experiment suite needs rotation).

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

## Patterns and Anti-Patterns

### Patterns

**Steady-state-first pipeline design**: Always verify the baseline before injecting chaos. If the system is already unhealthy, skip the experiment and fail the pipeline with a clear "baseline failure" message. This prevents the most common misdiagnosis — attributing a pre-existing failure to the chaos experiment. When a pipeline reports "chaos experiment failed," the team investigates the experiment. When it reports "baseline failure — cannot proceed," the team investigates the deployment. The distinction keeps chaos from being blamed for pre-existing issues and preserves trust in the pipeline's signal.

**Tiered experiment suites**: Run fast, safe experiments on every deployment and progressively more aggressive experiments on less frequent cadences. Pod-kill on every PR merge. Network delay on nightly builds. Multi-fault workflows on pre-release candidates. This balances deployment velocity with confidence — the 2-minute pod-kill experiment gates every deployment, while the 60-minute comprehensive suite gates only release candidates. A deployment that passes the light suite but fails the heavy suite tells you exactly where the resilience boundary lies.

**Abort-as-a-service**: Deploy the abort controller as an independent service with its own service account, RBAC, and monitoring. It must not share fate with the chaos controller or the CI/CD pipeline. If the pipeline crashes, the abort controller must still be able to delete experiments. The abort controller is the circuit breaker for your chaos program — when it trips, everything stops. A well-designed abort controller logs every action (which experiment, which SLO threshold, which timestamp) so every abort decision is auditable and explainable.

**Label-driven attribution**: Every chaos CRD carries labels that identify its source (pipeline run ID, schedule name, experiment type). Grafana dashboards overlay experiment timelines on top of system metrics. An on-call engineer should never have to wonder whether a latency spike is caused by chaos. The convention `chaos-source: ci-cd` or `chaos-source: scheduled`, combined with a run identifier, makes attribution a single-label query. Without this discipline, chaos experiments create noise in monitoring that erodes trust and wastes on-call investigation time.

**Findings-to-backlog pipeline**: GameDay findings are treated as production incidents — same priority, same SLA, same postmortem expectations. If findings linger in a backlog for two quarters, the program loses credibility and participants disengage. The feedback loop is the program's engine: find a weakness, fix it, verify the fix with the same experiment, and record the outcome. When this loop turns quickly, the program visibly improves resilience. When it stalls, the program becomes expensive theatre.

### Anti-Patterns

**Running chaos without abort**: The chaos equivalent of deploying without monitoring. An unattended experiment that degrades staging for hours before anyone notices erodes trust in the entire program. Automated abort is not optional — it is the minimum viable safety mechanism for unattended chaos. If your pipeline cannot respond to an SLO breach within 30 seconds, do not run unattended chaos. The abort controller is not an optimization to add later; it is a prerequisite for removing the human from the observation loop.

**Repetitive experiment suites**: Running the same pod-kill experiment every night and passing every night is not resilience verification — it is a cron job that generates green checkmarks. Rotate experiment types, increase blast radii, and target new services regularly. A useful heuristic: if an experiment has passed 10 consecutive times without a finding, retire it and replace it with something new. The purpose of chaos engineering is to find unknown weaknesses, not to repeatedly confirm known strengths.

**Skipping cleanup on failure**: If a CI job fails mid-experiment and the cleanup step is gated on success, the chaos CRDs remain active indefinitely. Every cleanup step must use `if: always()` or equivalent unconditional execution. Better yet, set short durations on every chaos CRD (120s–180s) so even if cleanup fails completely, the experiment terminates on its own. A defense-in-depth approach layers CRD duration limits, unconditional cleanup steps, and a separate cron job that deletes experiments older than a threshold.

**Treating findings as suggestions**: If GameDay findings are filed as P4 backlog tickets, the program generates documentation but no action. Critical findings must carry the same urgency as production incidents. The social contract of GameDays is "we will find problems, and we will fix them." When findings go unfixed, the next GameDay becomes harder to staff — nobody volunteers to find problems that will be ignored.

**Measuring activity instead of outcomes**: Counting experiments run is easy; measuring weaknesses found and fixed is harder. The easy metric becomes the target, and the program optimizes for volume over impact. Define outcome-oriented goals from the start: "fix six resilience gaps this quarter," not "run 48 experiments this quarter." When a metric becomes a target, it ceases to be a good metric — this is Goodhart's law applied directly to chaos engineering program management.

---

## Did You Know?

- **Chaos Mesh Schedule CRDs use standard cron syntax.** Automated chaos testing can run continuously to verify failover, scaling, and protection mechanisms and to surface resilience regressions earlier than occasional manual exercises. A `Schedule` object is to a chaos experiment what a CronJob is to a batch job — recurring, predictable, and configured declaratively.

- **Coverage matters more than frequency.** Frequent chaos testing in delivery pipelines can surface resilience regressions sooner than infrequent manual exercises, but the exact incident reduction depends on how teams measure and run the program. The key variable is not frequency alone but coverage — a weekly experiment against 3 services catches fewer regressions than a daily experiment against 30, because most regressions occur in services you are not testing.

- **Game Days come from military wargaming.** The term originated in structured training exercises with defined rules, roles, and debriefs — not entertainment. Early large-scale reliability drills tested technology, people, and process together rather than infrastructure alone. The rigor of that tradition carries directly into the modern Game Day structure: hypothesis, execution, observation, debrief, and action items tracked to closure.

- **At scale, chaos becomes continuous.** Large organizations sometimes run recurring disaster-recovery exercises to expose hidden dependencies before real emergencies. Some run thousands of chaos experiments per month across production environments, with automated abort mechanisms that stop experiments within seconds of SLO violation. At that scale, chaos engineering is no longer a periodic exercise — it is a continuous operational practice that verifies resilience minute by minute.

---

## Decision Framework: When to Automate vs. When to Keep Manual

Not every experiment belongs in a CI/CD pipeline. The decision to automate should be based on the experiment's predictability, blast radius, and safety surface — not on whether it is technically possible to encode it as a CRD. The framework below helps you make that decision systematically. If you answer "No" to any of the automation prerequisites, keep the experiment manual until the prerequisite is met.

| Question | If Yes... | If No... |
|----------|-----------|----------|
| Does the experiment have a well-defined steady state and SLO thresholds that can be queried programmatically? | Automate — the pass/fail decision can be made by metrics queries | Keep manual — a human needs to interpret ambiguous signals |
| Is the blast radius contained within a single namespace with no production dependencies? | Automate — the safety surface is bounded | Keep manual or use extreme caution — unattended experiments with broad blast radii are dangerous |
| Has the experiment been run manually at least 3 times with consistent, understood results? | Automate — the expected behaviour is known | Run manually first — automating an experiment you do not understand produces uninterpretable results |
| Is there an abort controller deployed that can terminate experiments within 30 seconds of SLO violation? | Automate — the safety mechanism is in place | Do NOT automate — unattended chaos without automated abort is reckless |
| Does the experiment test a single, well-understood failure mode (pod-kill, network delay, resource stress)? | Automate — these are the ideal candidates for CI/CD | Keep manual — complex, multi-variable scenarios benefit from human observation |

---

## Common Mistakes

| Mistake | Why It's a Problem | Better Approach |
|---------|-------------------|-----------------|
| Running chaos in CI/CD without automated abort | A failed experiment in an unattended pipeline can degrade staging for hours before anyone notices | Always wire Prometheus alerts to an abort controller; never run unattended chaos without automated safety |
| Making Game Days mandatory attendance | Forced participation breeds resentment; people attend physically but don't engage mentally | Make Game Days engaging and voluntary; share exciting findings afterward to build FOMO |
| Skipping the steady-state verification step in CI | If the system is already unhealthy when chaos starts, you can't distinguish chaos impact from pre-existing issues | Always verify steady state BEFORE injecting chaos; fail the pipeline if the baseline is already violated |
| Running the same experiments every time | After the third identical pod-kill experiment, you're not learning anything new — you're just confirming what you already know | Maintain an experiment backlog; rotate experiments; increase blast radius over time; target new services |
| Not cleaning up experiments on pipeline failure | If the CI job fails mid-experiment (runner dies, timeout), the chaos CRDs remain active indefinitely | Use `if: always()` cleanup steps; set short durations on chaos CRDs; have a cron job that deletes old experiments |
| Treating Game Day findings as "nice to haves" | If findings are filed as low-priority tickets that often go unfixed, the program loses credibility and participants stop engaging | Treat critical Game Day findings like production incidents — they get the same priority and SLA as a real outage |
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

A healthy chaos program should produce new findings often enough to stay useful, without causing frequent uncontrolled disruption.

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

Avoid gating production deployments on production chaos experiments — the blast radius of a failed experiment affecting a just-deployed canary is often too unpredictable.

</details>

### Question 7: Your team is running weekly chaos experiments in a staging environment. The abort controller is deployed, but it has never triggered. Your manager asks whether the abort controller is even necessary. How do you respond?

<details>
<summary>Show Answer</summary>

The abort controller is like a fire extinguisher — its value is not measured by how often it is used but by what happens when it is needed. The fact that it has never triggered could mean the experiments are well-scoped and the system is resilient, or it could mean the abort thresholds are set too high to ever fire.

The abort controller provides defense-in-depth: if an experiment interacts with an unrelated change in an unexpected way — a new deployment introduces a memory leak, a configuration change breaks circuit breakers, a network policy blocks recovery traffic — the abort controller is the last line of defense that prevents a contained experiment from becoming a widespread outage.

Without it, the team is one unexpected interaction away from a chaos experiment that runs for its full duration against a system that is actively failing, damaging staging for the full experiment window. The cost of maintaining the abort controller — a small deployment and a few Prometheus rules — is negligible compared to the cost of a single uncontrolled experiment degrading a shared staging environment for hours.

</details>

### Question 8: Your organization runs four Game Days per year and has a growing backlog of findings. The same findings appear in multiple Game Days. What is the underlying problem and how do you fix it?

<details>
<summary>Show Answer</summary>

The underlying problem is a broken feedback loop between Game Day findings and engineering action. Findings are being documented but not prioritized, so the same weaknesses persist across quarters. This erodes trust in the program: if participants see that findings from the last Game Day are still not fixed, they disengage from the current one.

The fix requires organizational commitment: treat Game Day findings with the same urgency as production incidents. Critical findings get a P1 ticket, an owner, and a deadline — just like a sev-1 outage would. The Game Day debrief is not the end of the process; it is the start of the remediation cycle.

Additionally, track closure rate as a program metric. If 50% of findings from Q1 are still open when Q2's Game Day arrives, the program has a prioritization problem, not a detection problem. At that point, reduce the cadence of Game Days until the backlog is cleared — running more experiments without fixing the findings from previous ones is expensive theatre.

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

The progression is deliberate and cumulative. You do not go from zero to continuous production chaos in one step — you build the safety infrastructure at each rung before climbing to the next. Manual experiments teach you what to test. Scheduled GameDays teach you how to test as a team. Automated pipelines teach you how to test without human oversight. Continuous production chaos, when you are ready for it, teaches you that resilience can be a property you measure continuously rather than a checkbox you tick quarterly.

Key takeaways:
- **Automate the routine** — pod-kill and network delay experiments should run in CI/CD
- **Keep humans for the complex** — Game Days test multi-service, cross-team scenarios
- **Abort automatically** — Prometheus alerts triggering experiment deletion is non-negotiable for unattended chaos
- **Analyze and share** — findings without action items and executive summaries provide no organizational value
- **Build culture gradually** — skepticism → acceptance → adoption → integration → culture
- **Measure outcomes, not activity** — findings fixed per quarter matters more than experiments run
- **Guardrails are the enabler** — you cannot automate chaos without automated safety; the abort controller is the minimum viable safety mechanism

---

## Next Module

Return to the [Chaos Engineering README]() to review the complete discipline, explore further reading, and find links to related platform engineering tracks.

## Sources

- [Understanding the October 2021 Facebook Outage](https://blog.cloudflare.com/october-2021-facebook-outage) <!-- incident-xref: facebook-2021-bgp --> — Incident analysis for the module's opening example and its network-configuration root cause. For the canonical treatment, see [Route 53 & DNS](../../../../cloud/aws-essentials/module-1.5-route53/).
- [Chaos Mesh Documentation](https://chaos-mesh.org/docs/) — Primary documentation for CRDs, Schedule, Workflow, and experiment types referenced throughout the module.
- [Chaos Mesh Workflow Orchestration](https://chaos-mesh.org/docs/create-chaos-mesh-workflow/) — Documentation for orchestrating multiple chaos experiments in sequence or parallel.
- [Principles of Chaos Engineering](https://principlesofchaos.org/) — Foundational principles including "build a hypothesis around steady-state behaviour" and "minimize blast radius."
- [LitmusChaos](https://docs.litmuschaos.io/) — Alternative open-source chaos engineering platform with GitOps-native ChaosEngine CRD and ChaosHub experiment marketplace.
- [LitmusChaos GitHub](https://github.com/litmuschaos/litmus) — Source repository for LitmusChaos; CNCF incubating project.
- [AWS Fault Injection Service — Experiment Templates](https://docs.aws.amazon.com/fis/latest/userguide/experiment-templates.html) — AWS-native chaos engineering service with stop conditions, actions, and target resource selection.
- [Google SRE Workbook — Canarying Releases](https://sre.google/workbook/canarying-releases/) — Chapter on canarying and progressive delivery, including how analysis steps can incorporate resilience verification.
- [Argo Rollouts — Analysis and Progressive Delivery](https://argo-rollouts.readthedocs.io/en/stable/features/analysis/) — How Argo Rollouts analysis templates can run Prometheus queries to gate canary promotion, relevant to chaos-as-analysis integration.
- [Chaos Engineering (book)](https://www.oreilly.com/library/view/chaos-engineering/9781492043850/) — O'Reilly book by Casey Rosenthal and Nora Jones; the chapter on automation covers CI/CD integration and continuous verification.
- [Chaos Engineering (Wikipedia)](https://en.wikipedia.org/wiki/Chaos_engineering) — Overview of the discipline, its history, and Netflix's Chaos Monkey<!-- incident-xref: netflix-chaos-monkey --> origins.
- [Chaos Mesh GitHub](https://github.com/chaos-mesh/chaos-mesh) — Source repository for Chaos Mesh; CNCF incubating project.
