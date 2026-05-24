---
citations_verified: true
title: "Module 5.10: Production Model-Serving Traffic Patterns"
slug: platform/disciplines/data-ai/mlops/module-5.10-model-serving-traffic-patterns
sidebar:
  order: 11
---

> **Discipline Track** | Complexity: `[COMPLEX]` | Time: 55-65 min

## Prerequisites

Before starting this module:

- [Module 5.4: Model Serving & Inference](../module-5.4-model-serving/)
- [Module 5.5: Model Monitoring & Observability](../module-5.5-model-monitoring/)
- [Service Mesh Strategy](../../reliability-security/networking/module-1.3-service-mesh-strategy/) and [Ingress and Gateway](../../reliability-security/networking/module-1.4-ingress-gateway/) basics
- KServe `InferenceService` basics, including predictors, storage URIs, and ServingRuntimes
- Comfort reading Kubernetes manifests, Istio `VirtualService` rules, and Prometheus-style rollout metrics

## Learning Outcomes

After completing this module, you will be able to:

- **Analyze** whether a model promotion should use canary, blue/green, A/B, shadow, mirroring, or a bandit allocation.
- **Design** a production traffic plan that names cohorts, assignment rules, rollback controls, metric gates, and cost limits before traffic moves.
- **Implement** a KServe canary rollout with `canaryTrafficPercent`, staged promotion, status inspection, rollback, and model-output telemetry.
- **Build** Istio `VirtualService` routes for weighted, header-based, sticky-cohort, and mirrored model-serving traffic.
- **Evaluate** when shadow validation gives stronger evidence than A/B testing, especially for safety, cold-start, and compute-heavy serving paths.
- **Compare** Thompson sampling, epsilon-greedy, and upper-confidence-band allocation for online model serving.
- **Diagnose** rollout anti-patterns such as unbounded experiments, quality-blind promotion, mixed cohorts, stale shadows, and rollback logic owned by the model being rolled back.
- **Estimate** the cost of canary duplication, shadow serving, cohort stores, mesh sidecars, GPU warm capacity, and cross-zone traffic.

## Why This Module Matters

Offline model evaluation is necessary.

It is not permission to replace production.

A model can pass validation notebooks, beat the previous model on held-out data, satisfy a data-quality gate from [Module 5.8](../module-5.8-great-expectations-data-quality/), and still make the business worse once real traffic reaches it.

The reason is not mystical.

Offline evaluation is a compressed simulation of the world.

Production traffic is the world, including latency, retries, stale features, user adaptation, bot behavior, premium cohorts, fraud pressure, and product surfaces the notebook did not model.

Serving traffic patterns are the discipline that turns "deploy the new model" into "measure the new model under bounded risk."

They are the release-control layer between [Module 5.4](../module-5.4-model-serving/) and [Module 5.5](../module-5.5-model-monitoring/).

In this module, promotion is not a redeploy.

Promotion is a controlled experiment with rollback.

Picture a recommendations team that trains a new ranking model.

The model improves offline precision on a held-out click dataset.

The team deploys it straight to production at full traffic.

For two days, infrastructure metrics look healthy.

The p99 latency is stable.

The HTTP error rate is unchanged.

The autoscaler behaves.

Everyone relaxes.

At the end of the first week, product analytics shows that a holdout cohort lost 12 percent click-through compared with the previous model.

The offline win did not survive the online system.

Maybe the new model overfit to historical heavy users.

Maybe it explored less aggressively and made the home page feel stale.

Maybe it ranked a profitable category lower because the training set underrepresented it.

Maybe it created a feedback loop where lower exposure made the model even less confident.

The technical rollback is now messy.

The old model was no longer receiving live traffic.

Its caches are cold.

Its autoscaling profile is stale.

Its feature assumptions may have drifted.

The release notes say "model v2 deployed," but they do not say which cohorts saw the drop first.

The business question is worse than the Kubernetes question.

How much revenue was lost?

Which users were affected?

Was the effect concentrated in a regulated segment?

Did the model change outcomes for a protected class?

Did the team keep enough logs to compare v1 and v2 predictions on the same requests?

Could a separate control plane force traffic back to v1 if the model-serving stack itself was unhealthy?

Traffic patterns answer those questions before the incident.

They define who sees the new model.

They define how long the experiment runs.

They define what is measured.

They define who can halt.

They define how the old path stays alive.

They define whether the candidate sees live requests without serving live answers.

They define the cost of duplicated inference.

The KServe docs describe canary rollouts as routing a percentage of traffic to a new `InferenceService` revision using `canaryTrafficPercent`.

The Istio docs describe routing by headers, weights, and mirroring at the service-mesh layer.

The Seldon Core docs describe routers, including multi-armed bandit routers that use feedback to adapt routing decisions.

Those APIs are useful, but the API is not the strategy.

The strategy is deciding which evidence you need before promotion.

Use canary when you primarily need progressive operational exposure.

Use A/B when you need statistically interpretable product or quality comparison.

Use shadow when you fear offline-online divergence but cannot risk serving the candidate response.

Use mirroring when you need a copy of production requests for load and behavior validation.

Use a bandit when cumulative reward during the experiment matters more than a clean fixed-horizon comparison.

Use blue/green when you need fast cutover and fast rollback between complete stacks.

The rest of this module gives you the decision framework and the concrete manifests.

You will see where the patterns overlap.

You will also see where they are often confused.

The common production failure is not "we did not know canaries existed."

The common production failure is "we called it a canary, but we never defined the quality metric that would stop it."

## 1. Why Traffic Patterns Matter

The safest way to think about model-serving traffic is to separate deployment from exposure.

Deployment puts a candidate model artifact, runtime, transformer, or prompt template into the serving environment.

Exposure decides which requests can use it.

Traditional application deployments often blur those steps because the code path is the product behavior.

Model serving cannot afford that shortcut.

A model can be deployed, warm, observable, and ready without being trusted for user-facing answers.

That distinction lets you prepare a candidate without betting the whole product on it.

It also lets platform teams hold two truths at once.

The platform may say the service is healthy.

The data science team may say the model is not ready to promote.

Both statements can be true.

The "deploy and pray" anti-pattern ignores that split.

It treats offline model validation as a release gate for full exposure.

It usually starts with understandable pressure.

The old model is stale.

The new model's offline metrics look better.

The product team wants the improvement live.

The infrastructure path supports rolling updates.

Someone says the deployment has readiness probes and rollback.

Then the model replaces production at full traffic.

The deployment succeeds.

The model-serving stack is stable.

The user-facing metric degrades anyway.

The rollback is not clean because the old model is not receiving traffic anymore.

Its caches are cold.

Its warmed GPU memory is gone.

Its feature-store reads may hit different cache paths.

Its request logs no longer line up with the candidate's outputs.

The team can move traffic back, but it cannot reconstruct the experiment that should have happened.

In the recommendations incident motif from the introduction, the 12 percent click-through drop after a week is the obvious outcome.

The hidden issue is the missing comparison.

The team did not know whether the drop was uniform or concentrated.

It did not know whether premium users behaved differently from free users.

It did not know whether new users were more affected than returning users.

It did not know whether the new model was worse for cold-start requests but better for mature profiles.

It did not know whether latency changed the product experience even though p99 stayed inside the SLO.

It did not know whether the old model would have degraded during the same week because the market changed.

The incident is not just a bad model.

It is bad experimental control.

Production model serving is especially vulnerable because model quality is not the same as service health.

HTTP success means the server returned a payload.

It does not mean the payload was good.

Low p99 latency means the service was fast.

It does not mean the ranking was useful.

Stable CPU means the pod was not overloaded.

It does not mean the class distribution stayed sane.

No exception means the code path executed.

It does not mean the feature vector had the semantics the model expected.

That is why the promotion plan must include both infrastructure telemetry and model-output telemetry.

Infrastructure telemetry asks whether the service is surviving.

Model-output telemetry asks whether the model is behaving.

Product telemetry asks whether users or business processes are better off.

Compliance telemetry asks whether the exposure respected audit, privacy, and fairness constraints.

A canary that watches only error rate is a deployment canary, not a model canary.

A model canary needs distribution checks.

It needs slice metrics.

It needs delayed outcome tracking.

It needs a request budget so the candidate sees enough examples without overexposing users.

It needs a rollback gate that lives outside the candidate model.

Traffic patterns also keep teams honest about time.

Some evidence appears immediately.

Startup failures, import errors, and model-file permission problems appear quickly.

Latency regressions usually appear during load.

Prediction-distribution drift can appear in minutes if the sampled cohort is representative.

Business outcomes may need hours, days, or a full product cycle.

Label-based metrics may need even longer.

You cannot promote a fraud model on five minutes of HTTP success if chargeback labels arrive later.

You cannot promote a recommender on one hour of clicks if retention is the real metric.

You cannot promote a safety classifier because it did not crash.

The exposure pattern must match the metric delay.

That is the first design question.

What evidence do we need, and how long does that evidence take to become reliable?

The second design question is who bears risk.

If an SRE is responsible for service availability, canary traffic gives a small operational blast radius.

If a data scientist is responsible for model quality, shadow traffic gives side-by-side outputs on real requests without serving the candidate.

If a product manager is responsible for conversion, A/B testing gives a fixed comparison between cohorts.

If the business cares about maximizing reward during the test, a bandit reduces the time spent on worse arms but weakens the simplicity of fixed-cohort inference.

If compliance requires deterministic review, blue/green may be easier to audit than adaptive allocation.

The third design question is whether the old model stays warm.

Rollback is only fast if the rollback target remains viable.

A green deployment that scales to zero is not a useful emergency path.

A previous KServe revision with no capacity may still be routable, but the first requests after rollback may pay cold-start latency.

A GPU-backed model may take long enough to load that "rollback" becomes "wait while angry users keep retrying."

For high-risk paths, keeping the previous model warm is part of the rollout budget.

The fourth design question is whether the candidate changes only the model weights.

KServe canary is very good when the InferenceService revision changes a model artifact, runtime image, transformer, or explainer inside one serving abstraction.

It is less expressive when the experiment changes an upstream feature pipeline, a prompt-template service, a retrieval stack, or a product cohort assignment.

In those cases, the service mesh, feature-flag system, or application gateway may need to own routing.

The fifth design question is who can stop the rollout.

Do not make a bad model responsible for disabling itself.

The kill switch should live in a separate control plane, such as ArgoCD, a feature-flag service, a platform API, or a guarded `kubectl patch` runbook.

The model server can emit metrics.

It should not be the only authority that can halt exposure.

> **Active learning prompt:** A fraud model candidate has lower false positives offline, but true fraud labels arrive two days later. Which traffic pattern would you choose for the first production exposure, and which metric would you refuse to use as the promotion gate?

The practical lesson is simple.

A deployment pipeline answers "can this artifact run?"

A traffic pattern answers "should this artifact receive more real traffic?"

Those are different questions.

Treating them as one question is how a successful deployment becomes a failed model release.

## 2. The Canon: Canary, Blue/Green, A/B, Shadow, Bandit, and Mirroring

The names are often used loosely.

That looseness creates production bugs.

Canary, blue/green, A/B, shadow, bandit, and mirroring are not synonyms for "gradual rollout."

They answer different questions.

They protect different people.

They produce different evidence.

They have different statistical and operational costs.

Start with this comparison grid.

```text
+--------------------+-------------------------+--------------------------+--------------------------+-------------------------+
| Pattern            | Primary question        | Who benefits most        | Typical duration         | Main risk               |
+--------------------+-------------------------+--------------------------+--------------------------+-------------------------+
| Canary             | Is the candidate safe   | SRE, platform engineer   | Minutes to days          | Promoting on health     |
|                    | under bounded traffic?  |                          |                          | instead of quality      |
+--------------------+-------------------------+--------------------------+--------------------------+-------------------------+
| Blue/green         | Can we switch whole     | SRE, release manager     | Minutes to hours         | Hidden data or cache    |
|                    | stacks and roll back?   |                          |                          | mismatch                |
+--------------------+-------------------------+--------------------------+--------------------------+-------------------------+
| A/B test           | Which variant wins on   | Product manager, data    | Days to weeks            | Weak cohort assignment  |
|                    | a declared metric?      | scientist                |                          | or no fixed end         |
+--------------------+-------------------------+--------------------------+--------------------------+-------------------------+
| Shadow             | How would the candidate | Data scientist, risk     | Hours to weeks           | Cost and stale shadows  |
|                    | behave on live inputs?  | owner                    |                          |                         |
+--------------------+-------------------------+--------------------------+--------------------------+-------------------------+
| Traffic mirroring  | Can a duplicate request | SRE, platform engineer   | Minutes to days          | Side effects if writes  |
|                    | path survive load?      |                          |                          | are not blocked         |
+--------------------+-------------------------+--------------------------+--------------------------+-------------------------+
| Bandit             | Which arm should get    | Product owner, ranking   | Continuous or bounded    | Routing and estimation  |
|                    | more traffic now?       | scientist                |                          | are coupled             |
+--------------------+-------------------------+--------------------------+--------------------------+-------------------------+
```

A canary moves a small share of live traffic to a candidate.

The candidate returns the user-facing answer for those requests.

It measures operational safety first.

It can measure model quality if the canary cohort is tracked and outcomes are captured.

It benefits SREs because blast radius is bounded.

It benefits data scientists because output distributions can be compared before full promotion.

It benefits product teams only if the canary is large and long enough to measure product impact.

A canary is usually fast.

It can start at one percent traffic and move through 10 percent, half traffic, and full promotion.

The exact steps should be driven by request volume and risk, not by tradition.

One percent of a high-volume recommender may be enough to see latency and output-shape issues quickly.

One percent of a low-volume fraud review tool may be statistically meaningless.

Blue/green keeps two complete serving stacks.

Blue is current production.

Green is the candidate.

The switch can happen through DNS, a load balancer, an ingress route, a service selector, or a mesh route.

The pattern measures whether a full stack can take production load and whether rollback is fast.

It benefits release managers and SREs because the rollback target is explicit.

It is not automatically an experiment.

If every user moves from blue to green at the same moment, you have cut over, not compared.

Blue/green is useful when the candidate changes many components together.

A new feature pipeline, a new runtime, a new model store, and a new transformer may be easier to reason about as a complete green stack.

A/B testing assigns users, sessions, accounts, requests, or entities to cohorts.

The assignment should be stable for the duration of the experiment unless the design explicitly says otherwise.

A/B measures a declared outcome.

That outcome might be click-through, revenue, fraud loss, manual-review time, support escalation, or a calibrated quality score.

It benefits product managers because the result maps to a decision.

It benefits data scientists because it tests online behavior rather than offline replay alone.

It benefits compliance teams when cohort assignment and metric definitions are auditable.

A/B usually takes longer than canary.

It must wait for enough samples and enough outcome delay.

For a recommender, clicks may arrive quickly but retention may not.

For fraud, labels may lag by days.

For support automation, satisfaction scores may arrive only after the interaction closes.

The common mistake is to start a half-and-half split with no fixed end date.

That is not an experiment.

That is an ungoverned permanent fork.

Shadow mode sends live requests to the candidate but does not serve the candidate response.

The current model remains authoritative.

The candidate prediction is logged, compared, or scored later.

Shadow measures offline-online divergence under real inputs.

It benefits data scientists because it creates paired predictions on the same request.

It benefits risk owners because users do not receive candidate outputs.

It benefits SREs because it reveals load, memory, and startup behavior without user-facing response changes.

Shadow is valuable when A/B is unsafe or impossible.

A safety classifier can be shadowed before it is allowed to block user actions.

A cold-start recommender can be shadowed on new users before it is allowed to rank production content.

A medical triage model can be shadowed for audit without changing clinician workflow.

Shadow is not free.

The candidate runs on real traffic.

If the candidate is an LLM endpoint or a GPU-bound model, doubling inference may be too expensive.

Traffic mirroring is the infrastructure mechanism often used to implement shadow.

Istio's `mirror` and `mirrors` fields send a duplicate request to another destination in addition to the primary route, and the mirrored response does not delay the primary response according to the Istio reference.

Mirroring can validate load paths, request parsing, and non-serving output logging.

It is dangerous if the mirrored service performs side effects.

Mirrored prediction services must not write user-visible state, trigger payments, send emails, update feature stores as if they were authoritative, or commit decisions.

A multi-armed bandit adapts traffic allocation based on observed reward.

It is not simply "A/B with automation."

In a fixed A/B test, the allocation is usually held steady so the analysis is simpler.

In a bandit, the allocation changes because the system is trying to maximize cumulative reward while learning.

That makes bandits attractive for recommendations, ranking, and content selection where sending too much traffic to a weak arm has real cost.

It also makes them harder to audit.

The routing logic and quality-estimation logic are coupled.

If the reward metric is delayed, biased, or attacked, the router can move traffic in the wrong direction.

If a model failure correlates across arms, the bandit may confidently exploit the wrong option.

If a premium cohort has different behavior, the global reward estimate may hide harm to that cohort.

This decision tree is the first pass.

```text
Start
  |
  +-- Is it unsafe to serve candidate outputs yet?
  |       |
  |       +-- yes --> Use shadow or traffic mirroring first.
  |       |
  |       +-- no
  |
  +-- Is the main fear offline-online divergence?
  |       |
  |       +-- yes --> Shadow, then canary with paired-output checks.
  |       |
  |       +-- no
  |
  +-- Is there a clear win metric and can you wait for it?
  |       |
  |       +-- yes --> A/B test with persistent cohort assignment.
  |       |
  |       +-- no
  |
  +-- Is cumulative reward during the test more important than simple analysis?
  |       |
  |       +-- yes --> Bandit, with guardrails and independent metrics.
  |       |
  |       +-- no
  |
  +-- Is the candidate mostly a model or runtime revision inside one InferenceService?
          |
          +-- yes --> KServe canary.
          |
          +-- no --> Blue/green or service-mesh routing across stacks.
```

The tree is not a replacement for judgment.

It prevents category errors.

If your concern is that the model will crash under load, A/B is too slow as the first signal.

If your concern is that users will stop clicking after a week, a five-minute canary is too shallow.

If your concern is that the candidate will reveal private data, shadowing to logs may make the risk worse unless logging is governed.

If your concern is that the old and new feature pipelines cannot run side by side, KServe canary alone is not enough.

The pattern must match the failure mode.

The owner also matters.

An SRE can halt a canary on p99 and error budget burn.

A data scientist can halt on output distribution, calibration, or slice regression.

A product manager can halt on declared business metrics.

A compliance reviewer can halt on exposure policy, cohort imbalance, or missing audit logs.

The promotion plan should name all of those gates.

When teams argue about "which pattern is best," they are often arguing about which risk they care about.

Make the risk explicit, and the pattern usually becomes obvious.

## 3. Canary on KServe

KServe canary rollouts are the most direct pattern for a model artifact or serving revision inside one `InferenceService`.

The current KServe canary docs describe `canaryTrafficPercent` as the field that splits traffic between the candidate revision and the last good revision in serverless deployment mode.

That serverless-mode caveat matters.

If your KServe installation uses raw deployment mode, read the current API and operator behavior before assuming the same revision-based canary semantics.

The canary object is still an `InferenceService`.

You are not creating two separate Services and hand-writing a mesh split.

You are updating the serving spec.

KServe creates a new revision.

KServe tracks the last revision that was fully rolled out.

KServe routes the configured percentage to the latest ready revision and the remainder to the previous rolled-out revision.

The KServe canary example shows the operational shape: the first model receives all traffic, adding `canaryTrafficPercent: 10` routes a small share to the new revision, removing the field after a healthy rollout promotes the new model, and setting the value to zero pins traffic back to the previous model.

That is the happy path.

Production canaries need more than the happy path.

First, decide what changed.

If only `storageUri` changes from model v1 to model v2, the blast radius is mostly model behavior.

If the ServingRuntime image changes, the blast radius includes server behavior, dependency behavior, and request parsing.

If a transformer changes, the blast radius includes feature normalization, prompt construction, token truncation, schema mapping, and post-processing.

If an explainer changes, user-facing predictions may be stable while explanation endpoints regress.

KServe's API reference shows `predictor`, `transformer`, and `explainer` as separate top-level components under `InferenceServiceSpec`.

It also shows rollout-related component fields such as `minReplicas`, autoscaling settings, `timeout`, `logger`, and `canaryTrafficPercent`.

That means a complete rollout plan must say which component is being canaried and which endpoints are included in the evidence.

For a predictor-only canary, compare predictions, latency, error rate, and resource usage.

For a transformer canary, compare input normalization and output shape before you blame the model.

For an explainer canary, compare explanation availability, explanation latency, and whether explanation payloads still reference valid feature names.

Second, budget requests.

A canary percentage is not enough.

A candidate that receives one percent of traffic on a quiet service may not see enough requests to prove anything.

A candidate that receives one percent of traffic on a high-volume endpoint may receive enough traffic to cause real harm.

Write the budget in requests as well as percent.

For example, "hold at one percent until at least 5,000 candidate requests arrive and p99 stays inside the SLO for two consecutive windows" is stronger than "hold at one percent for ten minutes."

The right number depends on traffic volume, metric delay, and risk.

Third, keep the previous model warm if rollback time matters.

KServe can route back to a previous rolled-out revision, but warm capacity is a separate concern.

If the old revision scales down, rollback may still wait for pods, model download, image pull, or GPU memory allocation.

For high-stakes endpoints, set `minReplicas` deliberately during the rollout window.

That increases cost.

It also turns rollback from an aspiration into an operation.

Fourth, understand autoscaling during traffic shift.

Autoscalers respond to traffic after it arrives.

When you move from one percent to ten percent, the candidate may suddenly need more pods.

If the model has slow startup, the first window after the shift can show latency that is really cold-start pressure.

That latency still matters to users.

Do not promote through a cold-start spike and then declare the model healthy because it recovered.

Either pre-warm capacity or make the shift slow enough that the autoscaler catches up.

Fifth, separate health from quality.

A canary should halt on infrastructure signals such as elevated p99, request errors, restarts, memory pressure, queue depth, and autoscaler saturation.

It should also halt on model signals such as output-distribution shift, invalid output rate, calibration drift, feature-missing rate, explanation failures, and slice-level degradation.

The halt criteria should be named before the rollout.

The kill switch should be a patch, GitOps change, feature flag, or platform API outside the model process.

This diagram shows the KServe canary architecture.

```text
Client requests
     |
     v
KServe / Knative route for one InferenceService
     |
     +--------------------+--------------------+
     |                                         |
     v                                         v
Previous rolled-out revision              Latest ready revision
model-v1 predictor                         model-v2 predictor
optional transformer-v1                    optional transformer-v2
optional explainer-v1                      optional explainer-v2
     |                                         |
     +--------------------+--------------------+
                          |
                          v
Telemetry: p99, error rate, candidate share,
output distribution, slice metrics, rollback gate
```

Here is an end-to-end manifest for the predictor path.

The lab later uses a smaller version of this, but this annotated version shows the production knobs.

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: churn-risk
  namespace: ml-serving
  annotations:
    serving.kserve.io/enable-tag-routing: "true"
spec:
  predictor:
    minReplicas: 1
    maxReplicas: 5
    timeout: 10
    canaryTrafficPercent: 10
    logger:
      mode: all
      url: http://prediction-logger.ml-serving.svc.cluster.local
    model:
      modelFormat:
        name: sklearn
      runtime: kserve-sklearnserver
      storageUri: pvc://sklearn-models/churn-risk-v2/
      resources:
        requests:
          cpu: "250m"
          memory: "512Mi"
        limits:
          cpu: "1"
          memory: "1Gi"
```

The field `canaryTrafficPercent: 10` does not say "this model is good."

It says "route a bounded share to the candidate revision."

The model-quality decision still belongs to your gates.

For a staged rollout, use a sequence like this:

```text
0 percent   Candidate deployed, directly tested by tag or internal request.
1 percent   Smoke traffic, startup behavior, basic output sanity.
10 percent  Real cohort diversity, first quality comparisons, autoscaler response.
50 percent  Broad exposure after early gates pass.
100 percent Full promotion after declared gates pass.
```

The zero-percent step is important.

The KServe canary example documents pinning traffic back to the previous model by setting `canaryTrafficPercent` to zero.

The same idea is useful before exposure.

Deploy the candidate and explicitly test the latest revision by tag when tag routing is enabled.

Do not make the first live user request discover that the model file is missing.

The one-percent step is not about statistical proof.

It is about blast radius.

Check that the candidate starts, loads the artifact, accepts real payloads, emits telemetry, and does not poison downstream systems.

The ten-percent step is where output comparisons become more meaningful.

Compare the candidate's prediction distribution with the primary's historical distribution.

Compare feature-missing rates.

Compare invalid output rates.

Compare top categories, class balance, score quantiles, and explanation success.

Use cohorts.

A global distribution can hide a premium-user regression.

The half-traffic step is where capacity and product impact become more visible.

Watch autoscaler behavior.

Watch cold starts.

Watch queueing.

Watch p99 and p99.9 separately if the path is user-facing.

Watch the metrics from [Module 5.5](../module-5.5-model-monitoring/), not only Kubernetes metrics.

The full-promotion step should remove ambiguity.

Once v2 is promoted, remove the canary field or pin it to the intended final state according to your GitOps convention.

Keep v1 rollback artifacts available for the rollback window.

Do not delete the old model artifact immediately just because the traffic split says full promotion.

When should you halt?

Halt if p99 exceeds the rollout SLO for the candidate cohort.

Halt if error rate rises above the rollout budget.

Halt if the candidate's invalid output rate is higher than the primary.

Halt if the candidate's score distribution shifts beyond the agreed bound and there is no expected reason.

Halt if a protected or high-value cohort regresses even when the global metric is neutral.

Halt if autoscaling cannot keep up after a traffic step.

Halt if logs, traces, or request IDs are missing, because a rollout you cannot observe is not a controlled rollout.

Halt if the transformer and predictor versions are not compatible.

That last point is a common KServe gotcha.

The transformer is often where feature schemas, prompt templates, and response shaping live.

If the predictor changes but the transformer is still producing the old feature shape, the candidate may be unfairly judged or silently broken.

If the transformer changes but the predictor does not, the primary model may receive inputs it was never trained on.

Roll out transformer and predictor changes deliberately.

Either version them together, or test compatibility explicitly before live exposure.

The explainer has a similar issue.

If explanations are part of a regulated workflow, an explainer failure can block promotion even when predictions are accurate.

KServe supports explainer components, and the KServe Alibi explainer docs show an `explainer` component container calling the predictor.

That means explanation latency and predictor latency can interact.

Canary the explanation endpoint too if it is user-facing or audit-facing.

> **Active learning prompt:** You move a KServe canary from one percent to ten percent, p99 jumps for five minutes, then recovers. The candidate output distribution also shifts toward one class. Which signal would you attribute to autoscaling, which signal would you attribute to model behavior, and what would you do before moving to half traffic?

KServe canary is a powerful default when the serving abstraction is stable.

It is not a substitute for experiment design.

Write the gates first.

Then write the manifest.

## 4. A/B Testing with Istio VirtualService Weights

KServe canary is not always enough.

It works best when the old and new serving paths fit inside one `InferenceService` revision history.

Many model experiments do not fit that shape.

The candidate may use a different model architecture.

It may need a different feature pipeline.

It may use a different prompt template.

It may call a retrieval service.

It may require a different transformer image.

It may use a different batching policy.

It may need a different GPU class.

It may be a model plus a rules engine.

At that point, service-mesh routing becomes the cleaner control surface.

Istio's `VirtualService` lets you match requests and route them to destinations by header, URI, gateway, and weighted destination.

The Istio reference explicitly frames service versions as subsets and says the chosen version can be decided by criteria such as headers, URLs, or weights.

That is exactly what an A/B model experiment needs.

The platform route should not know whether v2 is "better."

It should know which cohort gets which serving path.

The experiment system should know why.

A simple weighted split looks like this.

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: churn-weighted
  namespace: ml-serving
spec:
  hosts:
    - churn-model.ml-serving.svc.cluster.local
  http:
    - name: weighted-ab
      route:
        - destination:
            host: churn-model-v1.ml-serving.svc.cluster.local
            port:
              number: 80
          weight: 50
        - destination:
            host: churn-model-v2.ml-serving.svc.cluster.local
            port:
              number: 80
          weight: 50
```

That is a traffic split.

It is not yet a good A/B test.

For an A/B test, assignment stability matters.

If each request is randomly assigned, the same user may see v1 in one session and v2 in the next.

That can be acceptable for stateless scoring, but it is often invalid for user-experience experiments.

A recommender changes what users see.

Users react to that history.

The next request is not independent of the previous recommendation.

If assignment flips randomly, the experiment contaminates itself.

Header-based routing is a common way to make assignment explicit.

An upstream experiment service, gateway, edge worker, or application middleware assigns the cohort.

The mesh enforces the serving destination.

The model server receives a normal request.

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: churn-cohorts
  namespace: ml-serving
spec:
  hosts:
    - churn-model.example.internal
  gateways:
    - mesh
  http:
    - name: treatment
      match:
        - headers:
            x-user-cohort:
              exact: treatment
      route:
        - destination:
            host: churn-model-v2.ml-serving.svc.cluster.local
            port:
              number: 80
    - name: control
      match:
        - headers:
            x-user-cohort:
              exact: control
      route:
        - destination:
            host: churn-model-v1.ml-serving.svc.cluster.local
            port:
              number: 80
    - name: default-control
      route:
        - destination:
            host: churn-model-v1.ml-serving.svc.cluster.local
            port:
              number: 80
```

The default route is intentional.

Requests without an experiment assignment should not silently fall into treatment.

They should go to the safe default or be rejected by the gateway, depending on the policy.

Stratified cohorts make the design stronger.

If premium users, free users, new users, returning users, mobile users, desktop users, and suspected bot traffic are mixed randomly, the global result may hide slice effects.

Stratified assignment ensures each important segment has control and treatment representation.

The routing header can encode both assignment and stratum, or the assignment service can store the stratum in analytics metadata.

Do not make the model server infer the experiment group from the request after the route has already been chosen.

The assignment must be durable and auditable.

Cookie-based sticky sessions are useful for browser-facing products.

The first request assigns the user to control or treatment.

The browser stores the assignment.

Later requests carry the same assignment.

This preserves experience consistency.

It also creates edge cases.

Users clear cookies.

Users switch devices.

Shared devices mix identities.

Anonymous users may later sign in.

Cookie assignment is good when the product experience is session-oriented and the risk of cross-device inconsistency is acceptable.

Server-side assignment is stronger when identity matters.

Store assignment by account, user ID, tenant ID, merchant ID, device ID, or another stable key.

Redis is a common low-latency store.

A relational table is easier to audit.

A feature-flag platform can manage assignment, rollout rules, and kill switches.

The cost is persistence, lookup latency, storage, and governance.

The benefit is experiment validity.

Random request assignment is useful when each inference is independent.

Batch scoring a stream of unrelated transactions can use random assignment if the outcome of one request does not influence the next.

Even then, be careful.

Fraud systems, recommender systems, moderation systems, and support systems often create feedback loops.

The model's answer changes the future distribution of requests.

That is why a neat half-and-half split can still be a bad experiment.

The duration should be fixed before the experiment starts.

The sample-size target should be fixed before the experiment starts.

The primary metric should be fixed before the experiment starts.

Guardrail metrics should be fixed before the experiment starts.

The decision rule should be fixed before the experiment starts.

If the team checks every morning and stops when the graph looks favorable, the false-positive rate is not what the dashboard claims.

That is not a Kubernetes problem.

It is an experiment-design problem.

Model-serving A/B also needs operational gates.

Treatment can win on click-through and still be too expensive.

Treatment can win globally and harm a regulated cohort.

Treatment can have the same average latency and worse tail latency.

Treatment can produce better short-term engagement and worse retention.

Treatment can increase downstream manual review load.

Do not define "winner" as a single metric without guardrails.

For CI/CD, GitHub Actions, GitLab CI, and ArgoCD should validate manifests, apply route changes, and record approvals.

Do not let an analyst manually edit mesh weights in production with no review.

The route is part of the experiment.

It deserves code review.

It deserves rollback.

It deserves audit history.

The strongest pattern is decoupled assignment, routing, and analysis.

The assignment service decides the cohort.

The mesh enforces the route.

The model server predicts.

The metrics pipeline computes outcomes independently.

That separation prevents a bad model-serving path from also controlling the metric that promotes it.

It also makes file-backed review possible.

The reviewer can read the `VirtualService`, the assignment config, the metric query, and the rollback runbook separately.

That is how an A/B test becomes an engineering system instead of a dashboard ritual.

## 5. Shadow Mode and Traffic Mirroring

Shadow mode is the validation pattern for models that should see real production inputs before they are trusted to serve real production outputs.

The current production model remains authoritative.

The candidate receives a copy of the request.

The candidate response is logged, compared, scored later, or discarded.

The user never sees it.

That makes shadowing especially valuable when the cost of a bad answer is high.

It is also valuable when offline evaluation is suspected to be weak.

A fraud model may have training labels that lag production behavior.

A moderation model may face adversarial prompts that do not exist in the evaluation set.

A recommender may receive cold-start requests whose features are sparse.

A support classifier may see messy text that a cleaned training set hid.

A retrieval-augmented generation system may receive prompts with production-only tenant vocabulary.

Shadowing lets the candidate encounter those requests without controlling the answer.

The shadow pattern is easy to explain and easy to misuse.

Here is the dataflow.

```text
                         +-------------------------------+
                         | production response to user    |
                         +---------------^---------------+
                                         |
Client request --> Router / mesh --> Primary model v2
                         |
                         | mirrored copy
                         v
                   Shadow model v3
                         |
                         v
             prediction log, diff job, drift store
```

The shadow service must be side-effect safe.

It can log predictions.

It can emit metrics.

It can write to an isolated comparison table.

It must not update user-visible state.

It must not trigger notifications.

It must not train online from mirrored traffic unless the training path is explicitly isolated.

It must not write authoritative features.

It must not call payment, fulfillment, ticket-routing, or policy-enforcement systems as if the prediction were live.

Traffic mirroring at the mesh layer duplicates HTTP requests.

Istio's mirroring task calls the pattern "shadowing" and explains that mirrored traffic is outside the critical request path.

The Istio `VirtualService` reference also states that the gateway or sidecar does not wait for the mirrored destination before returning the primary response.

That is good for user latency.

It is not a guarantee that the mirror has no cost.

The duplicate request still consumes network, CPU, memory, model-loading capacity, and downstream dependencies called by the shadow model.

For large LLM serving, shadow can be financially painful.

If the primary request costs meaningful GPU time, mirroring all traffic can roughly double inference cost.

If the candidate has a larger context window, calls a vector database, or uses a heavier reranker, the shadow path can cost more than the primary.

That is why the cost lens must be explicit.

Shadow cost is often about two times baseline when the candidate has similar cost.

For larger candidates, it can be worse.

For small tabular models, it may be cheap enough to run for longer.

For a GPU-bound LLM, shadowing every request may be unjustifiable.

Sampled shadowing is often better.

Mirror a fixed percentage.

Mirror specific cohorts.

Mirror high-risk slices.

Mirror synthetic replay instead of live traffic when privacy rules forbid logging live payloads.

Mirror only after PII redaction if the candidate does not need raw fields.

Mirror only requests with consent or policy clearance when the domain requires it.

Shadow answers need a comparison plan.

Logging predictions is not enough.

Decide how the log pairs primary and shadow outputs.

Use a request ID that is generated before the router.

Record model version, artifact hash, input schema version, feature-store timestamp, transformer version, and prompt template version.

Record whether the primary served the user successfully.

Record the shadow status even if it failed.

Record latency separately for primary and shadow.

Record whether the candidate output would have violated a policy.

If labels arrive later, join them to both predictions.

This is paired evidence.

Paired evidence is stronger than comparing two different days.

The candidate and the primary saw the same request distribution.

That is the main reason to shadow.

Shadowing validates things that A/B cannot validate safely.

It can validate that a cold-start model produces plausible outputs for new users without exposing those users.

It can validate that a larger model can survive production traffic before the team pays the business risk of serving it.

It can validate that a safety model catches violations without blocking users yet.

It can validate that a new feature pipeline populates values on real production requests.

It can validate that an explanation endpoint is available for real inputs before auditors depend on it.

It can validate model-output distribution before delayed labels arrive.

Shadowing does not answer every question.

It cannot measure user reaction to the candidate because users did not see the candidate.

It cannot measure feedback loops created by the candidate.

It cannot measure downstream behavior that would happen only if the candidate response were served.

It can tell you how the model would have answered.

It cannot tell you how the world would have changed after that answer.

That is why shadow often comes before canary or A/B.

For a safety-critical model, use shadow before canary.

For a recommender, use shadow to check offline-online divergence, then A/B to measure user behavior.

For a large model, use sampled shadow to measure compute and output quality, then a small canary with budget caps.

For a compliance-sensitive model, use shadow logs as evidence, then require human review before live exposure.

Seldon Core has first-class language around shadow deployments in its routing documentation.

It describes a shadow deployment as a parallel deployment that receives duplicate requests while its response is discarded.

That is the same conceptual pattern whether the implementation is Seldon, Istio, BentoML custom middleware, an API gateway, or a model-server sidecar.

The implementation choice should be driven by where side effects can be controlled.

If the model server itself owns preprocessing and logging, server-side shadow may be simpler.

If the platform must duplicate traffic across separate stacks, mesh mirroring is cleaner.

If the candidate needs a sanitized payload, route through a transformer first.

If the candidate should receive only a subset, use header, path, or percentage matching.

Do not shadow forever.

Shadow is a validation step.

Permanent shadowing doubles operational surface area.

It creates a second production path that nobody trusts enough to serve and nobody wants to delete.

It can leak sensitive data into logs.

It can mask candidate failures because no user is complaining.

It can waste GPU capacity that should be used for serving, training, or batch evaluation.

Every shadow should have an exit condition.

Examples are "collect 20,000 paired requests," "observe no policy regressions for three business days," "finish delayed-label analysis for the sampled cohort," or "halt because candidate cost exceeds the budget."

The exit can be promotion, canary, redesign, or deletion.

Leaving the shadow running is not an exit.

## 6. Multi-Armed Bandit Serving

A/B testing asks a fixed-horizon comparison question.

A bandit asks a sequential allocation question.

In A/B, the team usually holds the split steady so the analysis can estimate which variant performed better.

In a bandit, the router adapts the split while the experiment is running.

It explores candidates to learn.

It exploits candidates that appear better.

That matters when traffic itself is valuable.

If a weak recommender arm receives half of all users for two weeks, the experiment has an opportunity cost.

A bandit tries to reduce that cost by allocating more traffic to arms that look promising.

That is useful for ranking, content selection, recommendation slots, pricing suggestions, notification timing, and other repeated decisions where reward can be observed.

It is less useful when the reward is delayed, sparse, biased, or hard to attribute.

A bandit is not a free upgrade from A/B.

It changes the evidence.

It changes the risk.

It changes the operational boundary between routing and model-quality estimation.

The simplest bandit algorithms are easy to describe.

Epsilon-greedy chooses the currently best arm most of the time and explores a random arm some of the time.

If epsilon is 0.10, then about one in ten decisions explores.

The strength is simplicity.

The weakness is crude exploration.

It may keep exploring weak arms longer than necessary, and it may under-explore arms whose uncertainty is high.

Thompson sampling maintains a probability distribution over each arm's reward and samples from those distributions to choose an arm.

Arms with strong evidence of high reward tend to win.

Arms with uncertainty still get chances.

The strength is a natural exploration-exploitation balance.

The weakness is that the posterior model must match the reward shape well enough to be useful.

Upper confidence bound chooses arms using an optimistic estimate.

An arm gets credit for observed reward and for uncertainty.

If an arm has not been tried much, its uncertainty term can pull traffic toward it.

The strength is explicit uncertainty-driven exploration.

The weakness is sensitivity to assumptions and tuning.

In serving systems, the math is only half the problem.

The reward pipeline is the hard part.

A click may arrive immediately.

A purchase may arrive later.

A refund may arrive much later.

A fraud label may arrive after investigation.

A support satisfaction score may arrive after case closure.

The bandit needs feedback.

If feedback is delayed, the router is learning from stale evidence.

If feedback is biased, the router is optimizing the bias.

If feedback can be manipulated, the router becomes an attack surface.

Seldon Core's routing docs describe routers as predictive units that can route to children and optionally receive feedback rewards.

The same docs list epsilon-greedy and Thompson sampling as reference multi-armed bandit router implementations.

That is a useful Kubernetes-native pattern because the router is part of the inference graph.

It is also a warning.

Once the router learns from feedback, deployment, metrics, and online learning are coupled.

A bad feedback path can make a healthy router harmful.

Alibi Explain is in the Seldon ecosystem, but be precise about what it provides.

Alibi's Anchor explanations use bandit ideas internally to search for high-precision anchors.

That does not make Alibi Explain an online production traffic router.

For serving allocation on Kubernetes, look to Seldon Core routers, custom mesh-integrated routers, feature-flag systems, or application-level decision services.

Cloud-managed platforms also need precise language.

Vertex AI endpoints support traffic split percentages across deployed models according to Google Cloud's deployment docs.

Vertex AI Vizier is a managed black-box optimization service.

Those are useful capabilities, but they are not the same as saying every Vertex AI endpoint is a managed online bandit router.

If a vendor or internal platform advertises "Vertex AI bandit" or another cloud-managed bandit, require the exact product surface, feedback API, audit model, and rollback behavior before designing around it.

For production bandits, start with guardrails.

Set minimum and maximum traffic per arm.

Set a global kill switch.

Set per-cohort safety limits.

Set a fallback arm.

Set a no-learning mode.

Set reward sanity checks.

Set metric freshness checks.

Set logging requirements for assignment, context, arm, reward, and model version.

Set privacy rules for context features.

Set analysis rules for delayed outcomes.

The context vector matters.

A non-contextual bandit treats each arm as if it has one global reward distribution.

That may be good enough for a banner choice.

It is rarely enough for model serving across heterogeneous users.

A contextual bandit uses request or user features to choose an arm.

That can improve reward.

It also raises the stakes.

Context features can encode sensitive attributes or proxies.

Context drift can make the policy stale.

Context logging can become a privacy issue.

The router can learn harmful shortcuts.

Bandits also complicate fairness and compliance.

If the algorithm allocates more traffic to the arm that wins globally, a smaller cohort may receive worse outcomes for longer.

If rewards are sparse for a cohort, the algorithm may under-learn that cohort.

If the business metric is revenue, the bandit may optimize away from low-revenue users in ways the organization does not want.

Guardrail metrics must be independent of the bandit.

That is the decoupled-metrics-gate pattern again.

The router can choose traffic.

It should not be the only system that decides the rollout is acceptable.

Correlated failures are the hidden operational bite.

Suppose two arms share the same feature store.

The feature store drifts.

Both arms degrade, but one degrades less.

The bandit may move more traffic to the less-bad arm and declare progress.

The correct action may be to halt serving and fix the feature pipeline.

Suppose all arms share a transformer that truncates a prompt incorrectly.

The bandit cannot discover a good arm because the shared preprocessing is broken.

Suppose the reward service drops events for mobile traffic.

The bandit may learn that mobile users have lower reward and route them differently.

Those are system failures, not model-ranking discoveries.

Bandit serving belongs late in maturity.

Use it after you have reliable request IDs, cohort assignment, metric freshness, rollback, delayed-label joins, slice monitoring, and cost controls.

Use it when you can explain the policy to a reviewer.

Use it when the cost of sending traffic to a weak arm during a fixed A/B test is material.

Do not use it to avoid defining a success metric.

A bandit without a trustworthy reward is just automated drift.

## 7. Patterns, Anti-Patterns, and Cost Control

The best traffic pattern is usually a composition.

Production teams rarely use exactly one idea.

They shadow before canary.

They canary before broad A/B.

They use blue/green for stack cutover and A/B for product evidence.

They use a bandit after fixed experiments identify safe arms.

They keep a kill switch outside the model.

They compute metrics outside the router.

The pattern is less important than the control loop.

A good control loop has a candidate, a bounded exposure rule, independent telemetry, a promotion rule, a rollback rule, and a cost budget.

Progressive rollout with a kill switch is the first pattern.

The rollout advances only when gates pass.

The kill switch can move traffic back without requiring the candidate to cooperate.

In GitOps environments, that may be an ArgoCD-controlled manifest change.

In platform environments, it may be a rollout API.

In emergency response, it may be a guarded `kubectl patch` command with audit logging.

The important point is separation.

If the candidate model server is crashing, it should not be the only component that can undo the rollout.

Decoupled metrics gate is the second pattern.

Traffic-routing logic should not be the only source of truth for model quality.

The router can emit events.

The model can emit predictions.

The gateway can emit request IDs.

The metrics pipeline should independently join assignments, predictions, outcomes, costs, and slices.

That pipeline should compute whether the rollout is allowed to advance.

This protects the team from self-promoting models.

It also makes PR review stronger because metric queries and routing manifests can be reviewed separately.

Shadow-before-canary is the third pattern for safety-critical models.

If a bad output can deny service, approve credit, block a user, recommend medical action, or trigger costly human work, do not let the first production exposure be user-facing.

Shadow the candidate.

Compare paired predictions.

Inspect slice behavior.

Run delayed-label analysis.

Only then canary a small, governed cohort.

The shadow result does not prove user impact, but it reduces unknowns before user impact is possible.

Separate-control-plane rollback is the fourth pattern.

For a model served through KServe, the rollback can be a patch to `canaryTrafficPercent`, a Git revert, or a promotion manifest that restores the previous `storageUri`.

For Istio, it can be a `VirtualService` weight or header rule change.

For a feature-flag assignment service, it can be a flag kill.

For a bandit, it can be freezing allocation to the fallback arm.

The rollback actor should have permission, audit, and practice.

A runbook nobody has run is a wish.

Cost budgeting is the fifth pattern.

Serving experiments spend money in non-obvious places.

The user-specified canary cost lens in this module assumes a comparison canary where the primary serves the answer and the candidate is also evaluated for the sampled request.

In that posture, canary cost is approximately `(1 + canary_pct) x baseline inference cost`.

For a ten-percent comparison canary, the primary still handles baseline serving and the candidate adds about one tenth of baseline inference compute.

If your canary is a pure traffic split where each request goes to exactly one model, compute cost is not duplicated per request, but warm replicas, model memory, image pulls, caches, and GPU reservations still create incremental cost.

Write which posture you are using.

Shadow cost is simpler and often harsher.

If every request is mirrored to a similar model, expect about `2 x baseline` inference cost.

If the shadow is a larger LLM, a GPU-heavy reranker, or a model that calls retrieval and tools, cost can exceed that.

Shadowing every request is often not worth it for large LLM serving.

Sample the shadow.

Limit duration.

Use cheaper offline replay when possible.

Use strict log retention.

Cohort experiments have persistence cost.

Cookie assignment costs little infrastructure but has validity issues.

Redis assignment adds a low-latency dependency.

Relational assignment adds stronger audit and slower writes.

Feature-flag platforms add governance, UI, approvals, and usually vendor cost.

None of those costs are accidental.

They buy experiment validity.

Mesh-based experiments have network cost.

Sidecars add CPU and memory overhead.

Cross-zone or cross-region traffic can create egress charges and latency.

If a canary sends traffic from a gateway in one zone to a candidate in another zone, the mesh can amplify both cost and tail latency.

Keep primary and candidate topology comparable during experiments.

Otherwise you may measure placement instead of model quality.

The anti-patterns are familiar.

A half-and-half A/B test with no fixed end date becomes permanent split-brain product behavior.

Promoting on "no error-rate change" ignores silent model degradation.

Canarying across traffic types mixes premium, free, internal, bot, and synthetic traffic until no cohort signal is trustworthy.

Shadowing forever turns validation into an expensive second production path.

Letting the model choose its own rollback path creates a control-plane dependency on the thing being evaluated.

Changing assignment rules mid-experiment invalidates comparison unless the analysis accounts for it.

Deleting the previous model artifact immediately after promotion makes rollback slower and less certain.

Using global metrics only lets harm hide inside slices.

The remedy is boring in the best way.

Name the pattern.

Name the cohort.

Name the metric.

Name the duration.

Name the request budget.

Name the rollback.

Name the cost.

Name the owner.

Then move traffic.

## Worked Example: Choosing a Pattern for a Ranking Model

A marketplace team has a new ranking model for search results.

Offline evaluation shows better normalized discounted cumulative gain on held-out historical sessions.

The team also changed the feature pipeline to include merchant response time.

The model is larger and costs more per request.

Click labels arrive quickly.

Purchase and refund outcomes lag.

Premium sellers are a sensitive cohort because search placement affects revenue.

The team proposes a ten-percent canary for one hour and promotion if error rate is unchanged.

That plan is weak.

The serving change is not only model weights.

The feature pipeline changed.

The business metric is not error rate.

Premium sellers need slice protection.

Refund outcomes lag.

The larger model changes cost.

A better plan is:

1. Shadow the candidate for a fixed request budget across search traffic.
2. Compare paired primary and candidate rankings by request, category, query type, seller tier, and cold-start status.
3. Halt if the candidate has missing features, invalid scores, extreme distribution shifts, or unacceptable cost per mirrored request.
4. Canary one percent of non-premium traffic after shadow gates pass.
5. Move to a stratified A/B test with stable cohort assignment across user and seller strata.
6. Use click-through as an early metric, purchase as the primary metric, refund and premium-seller exposure as guardrails.
7. Keep the old model warm until delayed metrics are reviewed.

This plan is slower than "deploy v2."

It is faster than explaining a revenue regression without paired evidence.

It also gives each owner a defensible gate.

The SRE watches latency and errors.

The data scientist watches distribution and ranking quality.

The product manager watches conversion.

The compliance reviewer watches protected slices and audit logs.

The platform owner watches cost and rollback readiness.

## Hands-On Lab: Canary, Shadow, and Cohort Routing on kind

In this lab, you will build a local KServe canary on kind and then add Istio routes for shadow and cohort traffic.

The lab uses tiny scikit-learn classifiers so that response values reveal which model handled a request.

Model v1 always predicts class `0`.

Model v2 always predicts class `1`.

Model v3 always predicts class `2` and is used as the shadow candidate.

You will bind ingress to `127.0.0.1` with a port-forward.

The YAML blocks below are complete manifests.

### Lab Safety Notes

Use a disposable kind cluster.

Do not point this lab at a shared cluster.

KServe canary rollout is serverless-mode behavior in the current KServe docs, so install KServe in Knative mode.

The lab uses PVC model storage because the KServe PVC provider is documented and works well for local artifacts on kind.

If your workstation cannot run the full KServe stack, you can still syntax-check the manifests and read the status commands.

### Step 1: Create a Kubernetes 1.35+ kind Cluster

Create a kind config that binds the Kubernetes API server to loopback.

```yaml
apiVersion: kind.x-k8s.io/v1alpha4
kind: Cluster
name: kserve-traffic
networking:
  apiServerAddress: "127.0.0.1"
nodes:
  - role: control-plane
```

Save it as `kind-traffic.yaml`, then create the cluster.

```bash
kind create cluster --config kind-traffic.yaml --image kindest/node:v1.35.0
kubectl cluster-info
```

### Step 2: Install KServe in Knative Mode

Use the current KServe quickstart script for Knative mode.

```bash
curl -fsSL "https://raw.githubusercontent.com/kserve/kserve/refs/tags/v0.17.0/hack/setup/quick-install/kserve-knative-mode-full-install-with-manifests.sh" | bash
kubectl wait --for=condition=Available deployment/kserve-controller-manager -n kserve --timeout=300s
kubectl wait --for=condition=Ready pod -l app=istio-ingressgateway -n istio-system --timeout=300s
```

In a second terminal, bind the ingress service to loopback.

```bash
kubectl port-forward -n istio-system svc/istio-ingressgateway 8080:80 --address 127.0.0.1
```

In the first terminal, export the ingress values.

```bash
export INGRESS_HOST=127.0.0.1
export INGRESS_PORT=8080
```

### Step 3: Build Three Tiny scikit-learn Model Artifacts

Create a local virtual environment by your normal project method, then use `.venv/bin/python` for the lab commands.

Install the small dependency set.

```bash
.venv/bin/python -m pip install scikit-learn==1.6.1 joblib==1.4.2
```

Create `train_models.py`.

```python
from pathlib import Path

from joblib import dump
from sklearn.datasets import make_classification
from sklearn.dummy import DummyClassifier


def main() -> None:
    model_root = Path("models")
    features, labels = make_classification(
        n_samples=60,
        n_features=4,
        n_informative=3,
        n_redundant=0,
        n_classes=3,
        random_state=13,
    )
    constants = {
        "model-v1": 0,
        "model-v2": 1,
        "model-v3": 2,
    }
    for name, constant in constants.items():
        classifier = DummyClassifier(strategy="constant", constant=constant)
        classifier.fit(features, labels)
        target = model_root / name
        target.mkdir(parents=True, exist_ok=True)
        dump(classifier, target / "model.joblib")


if __name__ == "__main__":
    main()
```

Run it.

```bash
.venv/bin/python train_models.py
find models -name model.joblib -print
```

### Step 4: Create the Namespace, PVC, and Copy Pod

Create storage for the model artifacts.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ml-serving
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: sklearn-models
  namespace: ml-serving
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: model-store
  namespace: ml-serving
spec:
  restartPolicy: Never
  containers:
    - name: model-store
      image: busybox:1.37.0
      command:
        - /bin/sh
        - -c
        - mkdir -p /models/model-v1 /models/model-v2 /models/model-v3 && sleep 3600
      volumeMounts:
        - name: model-data
          mountPath: /models
      resources:
        requests:
          cpu: "50m"
          memory: "64Mi"
        limits:
          cpu: "100m"
          memory: "128Mi"
  volumes:
    - name: model-data
      persistentVolumeClaim:
        claimName: sklearn-models
```

Save it as `model-storage.yaml`, then copy the artifacts.

```bash
kubectl apply -f model-storage.yaml
kubectl wait --for=condition=Ready pod/model-store -n ml-serving --timeout=120s
kubectl cp models/model-v1/model.joblib ml-serving/model-store:/models/model-v1/model.joblib -c model-store
kubectl cp models/model-v2/model.joblib ml-serving/model-store:/models/model-v2/model.joblib -c model-store
kubectl cp models/model-v3/model.joblib ml-serving/model-store:/models/model-v3/model.joblib -c model-store
```

### Step 5: Deploy Model v1 Through KServe

Create the baseline `InferenceService`.

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: churn-router
  namespace: ml-serving
  annotations:
    serving.kserve.io/enable-tag-routing: "true"
spec:
  predictor:
    minReplicas: 1
    model:
      modelFormat:
        name: sklearn
      runtime: kserve-sklearnserver
      storageUri: pvc://sklearn-models/model-v1/
      resources:
        requests:
          cpu: "100m"
          memory: "256Mi"
        limits:
          cpu: "500m"
          memory: "512Mi"
```

Save it as `isvc-v1.yaml`, then wait for readiness.

```bash
kubectl apply -f isvc-v1.yaml
kubectl wait --for=condition=Ready inferenceservice/churn-router -n ml-serving --timeout=300s
export SERVICE_HOSTNAME=$(kubectl get inferenceservice churn-router -n ml-serving -o jsonpath='{.status.url}' | cut -d "/" -f 3)
```

Create a request body.

```bash
cat > input.json <<'EOF'
{"instances":[[0.1,0.2,0.3,0.4]]}
EOF
```

Send a baseline request.

```bash
curl -sS \
  -H "Host: ${SERVICE_HOSTNAME}" \
  -H "Content-Type: application/json" \
  "http://${INGRESS_HOST}:${INGRESS_PORT}/v1/models/churn-router:predict" \
  -d @input.json
```

Expected response:

```json
{"predictions":[0]}
```

### Step 6: Deploy Model v2 as a 10 Percent Canary

Change only the model artifact path and add `canaryTrafficPercent`.

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: churn-router
  namespace: ml-serving
  annotations:
    serving.kserve.io/enable-tag-routing: "true"
spec:
  predictor:
    minReplicas: 1
    canaryTrafficPercent: 10
    model:
      modelFormat:
        name: sklearn
      runtime: kserve-sklearnserver
      storageUri: pvc://sklearn-models/model-v2/
      resources:
        requests:
          cpu: "100m"
          memory: "256Mi"
        limits:
          cpu: "500m"
          memory: "512Mi"
```

Save it as `isvc-v2-canary.yaml`, then apply it.

```bash
kubectl apply -f isvc-v2-canary.yaml
kubectl wait --for=condition=Ready inferenceservice/churn-router -n ml-serving --timeout=300s
kubectl get inferenceservice churn-router -n ml-serving
```

Send 1000 requests and count predictions.

```bash
for request in $(seq 1 1000); do
  curl -sS \
    -H "Host: ${SERVICE_HOSTNAME}" \
    -H "Content-Type: application/json" \
    "http://${INGRESS_HOST}:${INGRESS_PORT}/v1/models/churn-router:predict" \
    -d @input.json | jq -r '.predictions[0]'
done | sort | uniq -c
```

You should see roughly 900 predictions from v1 and roughly 100 predictions from v2.

The exact count will vary because routing is probabilistic.

If all predictions are `0`, inspect the `InferenceService` status and candidate pod logs.

If all predictions are `1`, confirm that the previous revision is still listed in the KServe status traffic section.

### Step 7: Promote to Half Traffic, Full Traffic, Then v2 Only

Move to half traffic.

```bash
kubectl patch inferenceservice churn-router -n ml-serving --type merge -p '{"spec":{"predictor":{"canaryTrafficPercent":50}}}'
kubectl wait --for=condition=Ready inferenceservice/churn-router -n ml-serving --timeout=300s
```

Move to full candidate traffic.

```bash
kubectl patch inferenceservice churn-router -n ml-serving --type merge -p '{"spec":{"predictor":{"canaryTrafficPercent":100}}}'
kubectl wait --for=condition=Ready inferenceservice/churn-router -n ml-serving --timeout=300s
```

Promote v2 as the ordinary spec by removing the canary field.

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: churn-router
  namespace: ml-serving
  annotations:
    serving.kserve.io/enable-tag-routing: "true"
spec:
  predictor:
    minReplicas: 1
    model:
      modelFormat:
        name: sklearn
      runtime: kserve-sklearnserver
      storageUri: pvc://sklearn-models/model-v2/
      resources:
        requests:
          cpu: "100m"
          memory: "256Mi"
        limits:
          cpu: "500m"
          memory: "512Mi"
```

Save it as `isvc-v2-promoted.yaml`, then apply it.

```bash
kubectl apply -f isvc-v2-promoted.yaml
kubectl wait --for=condition=Ready inferenceservice/churn-router -n ml-serving --timeout=300s
kubectl get pods -n ml-serving
```

The previous revision should eventually scale down according to Knative and KServe policy.

Do not delete the v1 model artifact until the rollback window is closed.

### Step 8: Add Model v3 as a Shadow Destination

Deploy v3 as a separate `InferenceService`.

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: churn-shadow-v3
  namespace: ml-serving
spec:
  predictor:
    minReplicas: 1
    logger:
      mode: all
      url: http://prediction-logger.ml-serving.svc.cluster.local
    model:
      modelFormat:
        name: sklearn
      runtime: kserve-sklearnserver
      storageUri: pvc://sklearn-models/model-v3/
      resources:
        requests:
          cpu: "100m"
          memory: "256Mi"
        limits:
          cpu: "500m"
          memory: "512Mi"
```

Save it as `isvc-v3-shadow.yaml`, then apply it.

```bash
kubectl apply -f isvc-v3-shadow.yaml
kubectl wait --for=condition=Ready inferenceservice/churn-shadow-v3 -n ml-serving --timeout=300s
```

Create a tiny prediction logger so the shadow leg has a visible sink.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prediction-logger
  namespace: ml-serving
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prediction-logger
  template:
    metadata:
      labels:
        app: prediction-logger
    spec:
      containers:
        - name: logger
          image: hashicorp/http-echo:1.0
          args:
            - "-text=shadow-log"
          ports:
            - containerPort: 5678
          resources:
            requests:
              cpu: "50m"
              memory: "64Mi"
            limits:
              cpu: "100m"
              memory: "128Mi"
---
apiVersion: v1
kind: Service
metadata:
  name: prediction-logger
  namespace: ml-serving
spec:
  selector:
    app: prediction-logger
  ports:
    - name: http
      port: 80
      targetPort: 5678
```

Save it as `prediction-logger.yaml`, then apply it.

```bash
kubectl apply -f prediction-logger.yaml
kubectl rollout status deployment/prediction-logger -n ml-serving --timeout=120s
```

Create an Istio mirror route that keeps v2 authoritative and mirrors to v3.

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: churn-shadow
  namespace: ml-serving
spec:
  hosts:
    - churn-shadow.example.internal
  gateways:
    - knative-serving/knative-ingress-gateway
  http:
    - name: primary-v2-shadow-v3
      route:
        - destination:
            host: churn-router-predictor-default.ml-serving.svc.cluster.local
            port:
              number: 80
          weight: 100
      mirror:
        host: churn-shadow-v3-predictor-default.ml-serving.svc.cluster.local
        port:
          number: 80
      mirrorPercentage:
        value: 100
```

Save it as `virtualservice-shadow.yaml`, then apply it.

```bash
kubectl apply -f virtualservice-shadow.yaml
```

Send 100 requests through the shadow host.

```bash
for request in $(seq 1 100); do
  curl -sS \
    -H "Host: churn-shadow.example.internal" \
    -H "Content-Type: application/json" \
    "http://${INGRESS_HOST}:${INGRESS_PORT}/v1/models/churn-router:predict" \
    -d @input.json >/dev/null
done
kubectl logs -n ml-serving -l serving.kserve.io/inferenceservice=churn-shadow-v3 --tail=100
```

The user-facing response comes from v2.

The v3 logs show that mirrored requests reached the shadow path.

If v3 returns a model-name mismatch, add a transformer in front of the shadow model to rewrite the inference path, or deploy v3 with a runtime argument that accepts the shared public model name.

That is a realistic production issue, not a lab failure.

Mirrors copy requests; they do not automatically adapt model-server naming contracts.

### Step 9: Add Header-Based Cohort Routing

Create direct v1 and v2 services for a clean cohort split.

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: churn-control-v1
  namespace: ml-serving
spec:
  predictor:
    minReplicas: 1
    model:
      modelFormat:
        name: sklearn
      runtime: kserve-sklearnserver
      storageUri: pvc://sklearn-models/model-v1/
      resources:
        requests:
          cpu: "100m"
          memory: "256Mi"
        limits:
          cpu: "500m"
          memory: "512Mi"
---
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: churn-treatment-v2
  namespace: ml-serving
spec:
  predictor:
    minReplicas: 1
    model:
      modelFormat:
        name: sklearn
      runtime: kserve-sklearnserver
      storageUri: pvc://sklearn-models/model-v2/
      resources:
        requests:
          cpu: "100m"
          memory: "256Mi"
        limits:
          cpu: "500m"
          memory: "512Mi"
```

Save it as `isvc-ab-direct.yaml`, then apply it.

```bash
kubectl apply -f isvc-ab-direct.yaml
kubectl wait --for=condition=Ready inferenceservice/churn-control-v1 -n ml-serving --timeout=300s
kubectl wait --for=condition=Ready inferenceservice/churn-treatment-v2 -n ml-serving --timeout=300s
```

Create a `VirtualService` that routes by `x-user-cohort`.

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: churn-ab-cohorts
  namespace: ml-serving
spec:
  hosts:
    - churn-ab.example.internal
  gateways:
    - knative-serving/knative-ingress-gateway
  http:
    - name: treatment
      match:
        - headers:
            x-user-cohort:
              exact: treatment
      rewrite:
        uri: /v1/models/churn-treatment-v2:predict
      route:
        - destination:
            host: churn-treatment-v2-predictor-default.ml-serving.svc.cluster.local
            port:
              number: 80
    - name: control
      match:
        - headers:
            x-user-cohort:
              exact: control
      rewrite:
        uri: /v1/models/churn-control-v1:predict
      route:
        - destination:
            host: churn-control-v1-predictor-default.ml-serving.svc.cluster.local
            port:
              number: 80
    - name: default-control
      rewrite:
        uri: /v1/models/churn-control-v1:predict
      route:
        - destination:
            host: churn-control-v1-predictor-default.ml-serving.svc.cluster.local
            port:
              number: 80
```

Save it as `virtualservice-ab.yaml`, then apply it.

```bash
kubectl apply -f virtualservice-ab.yaml
```

Send 200 control requests.

```bash
for request in $(seq 1 200); do
  curl -sS \
    -H "Host: churn-ab.example.internal" \
    -H "x-user-cohort: control" \
    -H "Content-Type: application/json" \
    "http://${INGRESS_HOST}:${INGRESS_PORT}/v1/models/churn-public:predict" \
    -d @input.json | jq -r '.predictions[0]'
done | sort | uniq -c
```

Send 200 treatment requests.

```bash
for request in $(seq 1 200); do
  curl -sS \
    -H "Host: churn-ab.example.internal" \
    -H "x-user-cohort: treatment" \
    -H "Content-Type: application/json" \
    "http://${INGRESS_HOST}:${INGRESS_PORT}/v1/models/churn-public:predict" \
    -d @input.json | jq -r '.predictions[0]'
done | sort | uniq -c
```

The control count should be all `0`.

The treatment count should be all `1`.

If a request without `x-user-cohort` returns `0`, the default-control route is working.

### Lab Reflection

You used KServe canary for progressive revision exposure.

You used Istio mirroring for shadow validation.

You used Istio header matching for cohort assignment.

Those are three different control loops.

In production, you would also add Prometheus queries, a metric gate, an ArgoCD rollback commit, and a written experiment end date.

The manifests are only the routing surface.

The release discipline is the system around them.

## Common Mistakes

| Mistake | Why it fails | Better practice |
|---|---|---|
| Promoting because HTTP error rate is unchanged | The new model may be fast, stable, and wrong | Gate on output quality, slice metrics, and delayed outcomes as well as service health |
| Running a half-and-half A/B split with no fixed end | The experiment becomes permanent forked behavior | Define duration, sample size, primary metric, guardrails, and decision rule before launch |
| Canarying across mixed traffic types | Premium, free, bot, internal, and synthetic traffic hide each other | Stratify cohorts and analyze slices independently |
| Shadowing every request for a large LLM | The duplicate path can double or exceed baseline cost | Sample shadow traffic and set an exit condition |
| Letting the candidate model own rollback | A failing model may not be able to disable itself | Keep rollback in ArgoCD, a platform API, a feature flag, or a guarded operator action |
| Changing cohort assignment mid-test | The comparison no longer means what the dashboard says | Version assignment rules and treat changes as a new experiment |
| Deleting v1 immediately after v2 promotion | Rollback becomes a cold deployment instead of a traffic move | Keep previous artifacts, runtime image, and warm capacity for the rollback window |
| Using bandits without reward freshness checks | The router learns from stale or biased feedback | Block allocation changes when reward lag, missing events, or slice imbalance exceed limits |

## Scenario Quiz

<details>
<summary>1. A new fraud model has better offline precision, but confirmed fraud labels arrive two days later. The team wants to canary for one hour and promote if p99 and error rate are stable. What is wrong with this plan?</summary>

The plan measures serving health, not fraud quality.
Because labels arrive later, a one-hour canary cannot prove the primary business outcome.
A stronger plan shadows the model first, checks output distribution and slice behavior, then uses a small governed canary with delayed-label review before broad promotion.
</details>

<details>
<summary>2. A recommender candidate is safe enough to serve, but product needs a clean read on retention impact. Should the team use random per-request routing or persistent cohort assignment?</summary>

Use persistent cohort assignment.
Recommendations change what users see, and that history affects future behavior.
Random per-request routing contaminates the user experience and weakens the retention read.
Cookie assignment may work for anonymous sessions, but account-level or server-side assignment is stronger when identity matters.
</details>

<details>
<summary>3. A canary from one percent to ten percent shows a short p99 spike, then recovery. The candidate also shifts the positive class rate far above the primary. Which signal blocks promotion?</summary>

The output shift blocks promotion until explained.
The short p99 spike may be autoscaler or cold-start behavior, though it still deserves capacity tuning.
The class-rate shift is model behavior and can indicate feature skew, threshold mismatch, or a real distribution change.
Do not advance to half traffic until the model-output gate is understood.
</details>

<details>
<summary>4. A shadow model writes predictions to the same feature store table used by the primary model. Why is this dangerous?</summary>

Shadow responses must not create authoritative side effects.
Writing to the same feature store can contaminate future primary predictions and training data.
The shadow path should write only to isolated comparison storage with request IDs, model versions, and retention controls.
</details>

<details>
<summary>5. A product owner asks for a bandit because "it will automatically find the best model." What must you verify before agreeing?</summary>

Verify the reward definition, reward freshness, cohort guardrails, fallback arm, logging, privacy rules, cost caps, and independent metrics gate.
A bandit optimizes what it observes.
If the reward is delayed, biased, or missing for a cohort, the router can confidently allocate traffic in a harmful direction.
</details>

<details>
<summary>6. A KServe canary changes both the predictor model artifact and a transformer image. The model performs worse than v1. What should you inspect before blaming the model?</summary>

Inspect transformer compatibility.
The transformer may be producing old feature names, new feature order, truncated prompts, missing fields, or changed post-processing.
Rollout evidence should separate predictor behavior from transformer behavior when both changed.
</details>

<details>
<summary>7. An A/B test shows treatment wins globally, but premium users regress. The global metric is statistically strong. Should the team promote?</summary>

Not without resolving the premium-user regression.
Global wins can hide unacceptable slice harm.
The experiment plan should define premium users as a guardrail cohort before launch, and guardrail failure should block promotion or require an explicit business and compliance decision.
</details>

<details>
<summary>8. A team keeps a shadow deployment running for months because it is "useful data." What is the operational problem?</summary>

Shadow is a validation step, not a permanent state.
Long-lived shadows add cost, logging risk, unserved failure paths, and operational noise.
Every shadow should have an exit condition such as a paired-request budget, delayed-label analysis window, promotion decision, redesign, or deletion.
</details>

## Next Module

Next, continue to Module 5.11: Drift-Triggered Auto-Retraining Loop, where production monitoring signals become retraining decisions.

Traffic patterns decide how a candidate model earns exposure.

Drift and retraining decide when a new candidate is needed.

## Sources

- [KServe Canary Rollout Strategy](https://kserve.github.io/website/docs/model-serving/predictive-inference/rollout-strategies/canary) - Official KServe documentation for `canaryTrafficPercent`, previous and latest revisions, rollback, and serverless-mode canary behavior.
- [KServe Canary Rollout Example](https://kserve.github.io/website/docs/model-serving/predictive-inference/rollout-strategies/canary-example) - Official example showing canary traffic, promotion by removing the canary field, rollback by setting the field to zero, and tag routing.
- [KServe Control Plane API Reference](https://kserve.github.io/website/docs/reference/crd-api) - Official API reference for `InferenceService`, component specs, `canaryTrafficPercent`, component status, and rollout-related fields.
- [KServe Quickstart Guide](https://kserve.github.io/website/docs/getting-started/quickstart-guide) - Official current quickstart for KServe installation modes, kind support, and Knative-mode install commands.
- [KServe Scikit-learn Runtime Documentation](https://kserve.github.io/website/docs/model-serving/predictive-inference/frameworks/sklearn) - Official SKLearn ServingRuntime documentation for `modelFormat: sklearn`, `runtime: kserve-sklearnserver`, storage URIs, and prediction requests.
- [KServe PVC Storage Provider](https://kserve.github.io/website/docs/model-serving/storage/providers/pvc) - Official guide for storing model artifacts on PVCs and serving them with `pvc://` storage URIs.
- [KServe Alibi Tabular Explainer](https://kserve.github.io/website/docs/model-serving/predictive-inference/explainers/alibi/tabular-explainer) - Official example of an `InferenceService` with predictor and explainer components.
- [Istio VirtualService Reference](https://istio.io/latest/docs/reference/config/networking/virtual-service/) - Official reference for weighted routes, header matching, route destinations, and mirror policy fields.
- [Istio Traffic Mirroring Task](https://istio.io/latest/docs/tasks/traffic-management/mirroring/) - Official task describing mirroring, shadowing, and duplicate request behavior outside the primary response path.
- [Seldon Core Routers Including Multi-Armed Bandits](https://docs.seldon.ai/seldon-core-1/configuration/routing/routers) - Official Seldon Core documentation for routers, feedback, epsilon-greedy, and Thompson sampling reference implementations.
- [Seldon Core Routing and Shadow Deployments](https://docs.seldon.ai/seldon-core-1/configuration/routing/ambassador) - Official Seldon Core routing documentation describing canary, shadow, and header-based routing concepts.
- [Alibi Explain Introduction](https://docs.seldon.ai/alibi-explain) - Official Alibi Explain documentation for the scope of Seldon's explanation library and its use of bandit ideas inside explanation methods.
- [Vertex AI Deploy Model API](https://cloud.google.com/vertex-ai/docs/predictions/deploy-model-api) - Official Google Cloud documentation for Vertex AI endpoint deployment and static traffic split behavior.
- [Vertex AI Vizier Overview](https://cloud.google.com/vertex-ai/docs/vizier/overview) - Official Google Cloud documentation for managed black-box optimization, useful context when evaluating cloud-managed bandit claims.
