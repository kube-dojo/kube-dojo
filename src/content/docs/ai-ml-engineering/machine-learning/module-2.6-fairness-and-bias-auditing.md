---
title: "Fairness & Bias Auditing"
description: "Audit ML systems for systematic disparate harm across protected groups, pick the fairness metric matching the harm structure, navigate the mutually-exclusive impossibility result, and apply pre-, in-, and post-processing mitigations with Fairlearn rather than treating fairness as a technical fix for a normative question."
slug: ai-ml-engineering/machine-learning/module-2.6-fairness-and-bias-auditing
sidebar:
  order: 26
---

> Track: AI/ML Engineering | Complexity: `[MEDIUM]` | Time: 90-110 minutes
> Prerequisites: [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/), [Module 2.2: Interpretability and Failure Slicing](../module-2.2-interpretability-and-failure-slicing/), and [Module 2.5: Conformal Prediction and Uncertainty Quantification](../module-2.5-conformal-prediction-and-uncertainty-quantification/). This module also sets up a plain-text forward reference to Module 2.7, causal inference for ML practitioners.

The on-call incident starts with a chart that nobody expected to matter. The model is live. The overall accuracy is acceptable. The calibration plot from [Module
1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/) looks ordinary. Then a reviewer slices decisions by a protected group and sees that approvals are
not merely uneven; they are uneven in a way that maps to a real harm. One group is cleared far less often even when the task is one where allocation decisions matter. The
question arriving in chat is not "is the model good?" The question is "which fairness failure are we actually looking at, and which metric would prove or disprove it?"

The second incident is the one practitioners confess after the first meeting. Someone already removed the sensitive attribute at training time. The column is gone. The
team expected that deletion to settle the issue. It did not. The gap remains because the model learned through correlated features, historical patterns, and proxy
structure. This is the core correction for the module. Fairness auditing is not the act of hiding a column and hoping the harm goes away. It is the disciplined work of
naming the relevant groups, choosing the fairness metric that matches the harm, measuring disparity directly, and then deciding whether mitigation, redesign, or
non-deployment is the honest answer.

## Learning Outcomes
By the end of this module, a practitioner will be able to:

1. **Diagnose** when a model needs a fairness audit because real allocation or quality-of-service harms can fall unevenly across named groups, and reject cases where
   "fairness" is just a confused request for better global accuracy.
2. **Explain** the operational meaning of demographic parity, equal opportunity, equalized odds, calibration within group, and individual fairness, including the
   impossibility result that prevents several of these criteria from holding simultaneously when base rates differ.
3. **Implement** group-level fairness assessment with Fairlearn's `MetricFrame`, disparity metrics, post-processing with `ThresholdOptimizer`, and in-processing with
   reductions such as `ExponentiatedGradient`.
4. **Compare** pre-processing, in-processing, and post-processing mitigations in terms of what they change, what assumptions they make, what operational costs they
   impose, and which legal or product constraints can rule them out.
5. **Decide** whether to mitigate, document and accept, redesign the system, or stop calling the problem a fairness issue because the real defect is data quality,
   leakage, misspecification, or an unresolved normative dispute.

## Why This Module Matters
Fairness is not an optional appendix to model evaluation. It is the part of the evaluation story that asks whether system errors, approvals, refusals, or service quality
are falling in systematically different ways across groups that matter in the legal or social context of deployment. Most production teams do not fail because they lack a
metric name. They fail because they pick a metric before naming the harm, or because they assume one global performance number answers a group-level question.

The Fairlearn user guide is the documentation spine for this module because it starts from the right frame. It says unfairness should be defined "in terms of its impact
on people" (https://fairlearn.org/main/user_guide/fairness_in_machine_learning.html). That sentence is short, but it does most of the conceptual work. It moves the
discussion away from intent, public relations, or abstract purity and toward measurable harms. If the system allocates opportunities, resources, attention, or burden,
then fairness work asks how those outcomes differ across groups and whether the chosen difference is acceptable.

This is also why the module has to be more rigorous than a checklist of metric definitions. Fairness is a normative choice, not a technical fix. The technical work still
matters, because once a team decides which harms count and which groups require protection, the engineering system has to measure those harms correctly, expose the gap
honestly, and implement the least misleading mitigation available. A vague moral commitment without measurement is hand-waving. A metric without a harm model is just
arithmetic.

Fairlearn is useful precisely because it supports both sides of the engineering workflow. Its assessment tools let you compute disparities cleanly. Its mitigation tools
let you try pre-processing, in-processing, and post-processing responses without pretending they are interchangeable. The goal of the module is to make that workflow
operational: define the harm, choose the metric, measure the disparity, decide the mitigation timing, then remeasure and document the tradeoff.

## Section 1: What Fairness/Bias Auditing Is and Isn't
Fairness and bias auditing is the discipline of testing whether a predictor creates systematic disparate harm across protected or otherwise sensitive groups. The word
systematic matters. A single bad prediction can be tragic, but fairness auditing is usually about patterns rather than anecdotes. The unit of analysis is not "did the
model ever make a mistake?" It is "does the model allocate opportunity, error, or service quality in meaningfully different ways across groups that the deployment has
reason to treat carefully?"

This immediately narrows the class of problems where fairness work belongs. If no groups are at stake, if the model output has no real-world consequence, or if the
request for fairness is secretly a request for higher overall accuracy, then this module is the wrong instrument. A ranking model for song ordering in an internal toy
demo does not trigger the same audit burden as a classifier that screens people for credit, hiring, insurance, housing, benefits, moderation, fraud review, or medical
prioritization. The structure of harm decides whether fairness work is relevant.

There are three ideas that teams conflate constantly. The first is statistical bias in the ordinary estimation sense. A model can be biased because it has systematic
residual structure, poor sampling, label noise, or misspecification. The second is fairness, which is a claim about how harms are distributed across people and groups.
The third is accuracy, which is a claim about technical prediction quality on some evaluation set. These ideas overlap, but they are not the same question asked three
times.

The distinction matters because a model can be accurate and unfair. If the population is imbalanced and the minority cohort is small, a model can reach a good overall
score while still harming that cohort consistently. A model can also be inaccurate and not especially unfair if its errors are evenly bad across groups. Neither state is
acceptable in a high-stakes system, but the remedy is different. One calls for general model improvement. The other calls for a fairness audit and possibly group-targeted
mitigation.

Fairness work also does not replace product governance. If the organization has not decided which groups matter, which harms matter, which thresholds matter, and which
performance losses are acceptable, no library can rescue the project. That is why fairness modules in mature teams are coupled to model cards, decision logs, and legal
review. The audit artifact is not only a notebook. It is a record of what was measured, why it was measured, and what was done when a gap appeared.

This makes fairness auditing closer to reliability work than many people first expect. The team is not trying to prove moral innocence. The team is trying to surface a
failure mode before the deployment normalizes it. The audit asks which group sees fewer approvals, more false positives, more false negatives, less coverage, worse
calibration, or poorer service, and then it asks whether that pattern is compatible with the stated purpose of the system.

## Section 2: Group Fairness Metrics and the Impossibility Result
Group fairness is the dominant operational frame because it starts from a simple question: which groups are at risk of harm, and what aspect of model behavior should be
comparable across those groups? Fairlearn follows this group fairness approach explicitly. The most important consequence is that you cannot choose a metric by
popularity. You choose it by the harm structure of the deployment.

Demographic parity, also called independence or statistical parity, asks whether the positive prediction rate is the same across groups. In notation, it asks for `P(Y_hat
= 1 | A = a)` to be equal across values of the sensitive attribute `A`. If the system is about allocating opportunity, demographic parity often enters the conversation
first because it measures who receives the positive decision. In a hiring-screen or lending prefilter, that quantity is immediately meaningful. It is also blunt. Equal
selection rates can still hide very different error structures.

Equal opportunity, defined by Hardt, Price, and Srebro in https://arxiv.org/abs/1610.02413, focuses on the true positive rate. It asks whether qualified people have the
same chance of receiving the positive outcome across groups. That is often the right metric when the main harm is denying deserving cases. If the system routes patients
to scarce follow-up care or flags fraud cases for manual review, missing truly positive cases can be the dominant harm. Equal opportunity says that harm should not fall
unevenly by group.

Equalized odds is stricter. It asks for equal true positive rate and equal false positive rate across groups. In effect, it wants both kinds of classification error to
line up. This is attractive when both missed positives and wrongful positives matter. It is also more expensive to satisfy because it constrains the classifier more
heavily. If the operating harm is asymmetric, equalized odds can be more than you need. If both errors are consequential, it may be the honest target.

Calibration within group asks a different question. For each predicted score `p`, it wants `P(Y = 1 | Y_hat = p, A = a) ≈ p` for each group `a`. This is not about equal
decision rates or equal error rates. It is about whether the score means the same thing within each group. If a model assigns a score of `0.8`, calibration within group
asks whether that score corresponds to roughly the same empirical event rate in each group. This matters in risk-scoring systems where the score itself, not only a hard
decision threshold, drives downstream policy.

The trap is assuming these metrics are just different dashboard panes that can all be green simultaneously. They cannot. Multiple fairness criteria are mutually exclusive
when base rates differ. The impossibility result associated with Chouldechova and Kleinberg, with canonical references at https://arxiv.org/abs/1610.07524 and
https://arxiv.org/abs/1609.05807, states the hard boundary clearly. When outcome prevalences differ across groups, you cannot in general satisfy calibration within group
together with equalized odds and other parity conditions, except in special cases such as perfect prediction or equal base rates.

That sentence has to be said without softening. Stakeholders often ask for "fairness" as though it were one dial. In reality it is a family of objectives that can
conflict. If a team demands demographic parity, equalized odds, and calibration within group simultaneously on a problem with different base rates, the honest answer is
not "we will optimize harder." The honest answer is that the request is mathematically incoherent unless the data-generating conditions have unusual structure.

> **Pause and predict** - A stakeholder demands demographic parity AND equalized odds AND calibration within group, simultaneously, on a problem where the base rates
> differ across groups. What should you tell them?

You should tell them the request is not generally satisfiable. The next step is not to hide behind theory but to return to harms. If the main failure is that qualified
members of one group are being denied too often, equal opportunity may be the right target. If the score itself is used downstream and must mean the same thing within
each group, calibration within group may be central. The metric is chosen by the harm you are trying to prevent, not by the hope that all desirable criteria can be
maximized at once.

This is the engineering content of fairness. A fairness audit does not end with "there is a gap." It continues with "which metric encodes the deployment's harm model,
which equally plausible metric would disagree, and why did we choose this one?" Teams that cannot answer that question are not auditing. They are collecting vocabulary.

## Section 3: Individual Fairness
Individual fairness, associated with Dwork et al. at https://arxiv.org/abs/1104.3913, uses a different intuition. Similar individuals should receive similar predictions.
This sounds more natural than group fairness when you first hear it, because it seems to align with an ordinary sense of equal treatment. If two applicants are similar in
relevant ways, then a fair system should treat them similarly.

The difficulty is hidden in the word similar. Individual fairness requires a distance metric over people or cases. That metric has to decide which differences matter, how
much they matter, and which differences are irrelevant even if they are predictive. In many real systems that judgment is not given by the data. It is a domain decision.
The metric for similarity in a medical triage system is not the metric for similarity in a hiring-screen system, and neither one falls automatically out of `fit()`.

This subjectivity is why group fairness dominates in practice. Group metrics are imperfect, but they are easier to measure, audit, regulate, and communicate. You can show
selection rate by group. You can show false positive rate by group. You can document the gap. You can attempt mitigation and remeasure. Individual fairness often needs a
debate about the similarity metric before any audit can even begin.

Individual and group fairness can also pull against each other. If a mitigation changes thresholds or selection behavior at the group level, then two otherwise similar
individuals from different groups may be treated differently. From a group-fairness perspective that may be justified because it closes a systemic harm gap. From a strict
individual-fairness perspective the differential treatment can look suspect. Neither perspective is fake. They are optimizing different fairness ideals.

The practical takeaway is not that individual fairness is useless. It is that its elegance hides a modeling burden that many production teams cannot defend. When a
regulator, auditor, or user asks for evidence, a distance metric that lives only in an engineer's head is not enough. Group fairness wins operational priority because it
yields measurable artifacts tied to named groups and named harms.

Still, individual fairness is worth remembering because it prevents a common failure of group thinking. A system can equalize a group metric while behaving wildly
inconsistently within each group. If a model handles near-identical cases very differently for arbitrary reasons, group parity alone may not expose that problem. The
mature view is that individual fairness is a useful conceptual check even when group fairness provides the main audit framework.

## Section 4: The Proxy Variable Problem — "Fairness Through Unawareness Is Mostly Mythology"
The most common practitioner misconception in fairness work is also the easiest to state. Dropping the sensitive attribute from the training matrix does not make the
model fair. If the data contains proxies, the model can recover group information through other columns: location, language patterns, name structure, education history,
browsing device, profile fields, or downstream variables that encode the same social pattern indirectly. Fairness through unawareness is mostly mythology.

This matters because teams often believe they have solved the governance issue the moment they remove the protected column. In reality they have only blinded themselves.
They may have made the system harder to audit while leaving the harm structure intact. The deployment then looks cleaner on paper while behaving the same way in
production. That is not mitigation. It is record-keeping theater.

The reason is statistical, not mystical. Correlated features carry information. If one group's examples tend to differ in address patterns, school types, historical
access to resources, or user-interface behavior, then a sufficiently flexible model can pick up that structure. The protected attribute does not need to be present
explicitly for group membership to affect predictions. Removing the column can even prevent you from seeing how much of the disparity remains.

Auditing therefore requires access to the sensitive attribute in the assessment data even when the model excludes it from the feature set. That sentence should feel
uncomfortable, because it creates a real privacy and governance tension. You may need sensitive labels precisely to test whether the system treats groups differently.
Without them, you often cannot compute the disparity metrics. With them, you introduce collection, storage, consent, and legal questions. Fairness work is full of these
tensions. They are not reasons to stop measuring. They are reasons to design the measurement process carefully.

> **Pause and decide** - An auditor asks whether your model is fair because you dropped the `gender` column at training time. What is the right honest answer?

The honest answer is no. Dropping the column does not establish fairness because proxy variables can still transmit the same group information, and fairness is an outcome
property, not a feature-list property. The model must be audited on group outcomes directly, which means the assessment dataset usually needs the sensitive attribute even
if the training feature matrix does not.

This is also where fairness work becomes more mature than generic failure slicing. In [Module 2.2](../module-2.2-interpretability-and-failure-slicing/), slicing told you
where performance degraded. Fairness auditing uses a similar computational move but adds legal, ethical, and policy weight because the slices are named groups with
protection or sensitivity in the deployment context. The same code can compute the table. The meaning of the table is heavier.

The proxy problem is why teams should be suspicious of claims like "we never used race," "we hid gender," or "the model cannot discriminate because that column is
absent." Those sentences are about inputs. Fairness auditing is about outputs and harms. A model can ignore the sensitive column directly and still reproduce the
historical structure that made the column sensitive in the first place.

## Section 5: Marginal vs Conditional vs Cohort Coverage
This section exists because fairness questions often arrive from teams that just finished a good uncertainty project. [Module 2.5: Conformal Prediction and Uncertainty
Quantification](../module-2.5-conformal-prediction-and-uncertainty-quantification/) made an important distinction between marginal coverage and subgroup behavior.
Conformal prediction gives a global coverage contract under exchangeability. It does not automatically guarantee equal coverage for every named cohort. That subgroup
miscoverage is one manifestation of unfairness.

The connection matters because practitioners can be lulled by a global average. If a conformal wrapper is valid marginally but one protected group receives much lower
empirical coverage, wider intervals, or noisier prediction sets, then the system can still be unfair even while honoring its overall statistical contract. The fairness
question is not "did conformal fail?" The question is "which cohort receives the weaker form of uncertainty protection, and does that matter for the deployment harm
model?"

Conditional coverage is stronger than marginal coverage because it asks for the guarantee to hold at finer granularity, often conditioned on features or subgroups.
Ordinary conformal methods do not give that guarantee for free. That limitation is not a small caveat. It is the reason fairness audits cannot stop at one global number.
When the protected group is the meaningful unit of harm, the audit must name the cohort and measure it directly.

This is where [Module 2.2: Interpretability and Failure Slicing](../module-2.2-interpretability-and-failure-slicing/) becomes the descriptive cousin of fairness work.
Failure slicing tells you which cohorts are performing worse. Fairness auditing is failure slicing on regulated, named groups plus a principled decision about which
disparity metric encodes the harm. The computational workflow looks familiar. The governance consequence is much more serious.

A useful mental model is this. Calibration, coverage, and fairness are related but not interchangeable contracts. A model can have good marginal coverage and still
under-cover one group. A model can be calibrated within group and still violate equalized odds. A model can have excellent overall accuracy and still produce disparate
false positive rates. Global success metrics are necessary but not sufficient for group-level safety.

The practical habit to build is simple. Every time a model's global metric looks good, ask which named cohorts could still be receiving a worse version of the system.
That question belongs right next to the validation and calibration questions from [Module 1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/). It is
not an optional ethics afterthought.

## Section 6: Fairlearn for Assessment
Fairlearn's assessment workflow is built around one core object: `MetricFrame`. That is a useful design choice because it forces teams to think in terms of metrics by
group rather than in terms of a single global score. A fairness audit usually begins with a small set of metrics that match the harm: selection rate if allocation is the
issue, true positive rate if missed deserved cases are the issue, false positive rate if wrongful burden is the issue, and accuracy only as background context rather than
as the fairness metric itself.

The exact import paths matter because fairness code is often copied from slides or old notebooks. Use the current Fairlearn metrics API directly:

```python
from fairlearn.metrics import (
    MetricFrame,
    selection_rate,
    demographic_parity_difference,
    equalized_odds_difference,
    equal_opportunity_difference,
)
```

In practice you will usually also want groupwise error-rate helpers such as `false_positive_rate`, plus an ordinary performance metric from scikit-learn for context. The
point is not to flood the dashboard. The point is to compute the smallest set of metrics that matches the harm model cleanly.

The following example uses a synthetic binary-classification problem with two groups. The model is trained without the sensitive attribute as an input. The attribute is
kept for assessment, because that is the only way to see whether outcomes differ by group.

```python
import numpy as np
import pandas as pd
from fairlearn.metrics import (
    MetricFrame,
    demographic_parity_difference,
    equal_opportunity_difference,
    equalized_odds_difference,
    false_positive_rate,
    selection_rate,
)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

rng = np.random.default_rng(23)
n_samples = 1600
a = rng.integers(0, 2, size=n_samples)

x1 = rng.normal(loc=np.where(a == 0, 0.4, -0.3), scale=1.0, size=n_samples)
x2 = rng.normal(loc=np.where(a == 0, 0.2, -0.2), scale=1.1, size=n_samples)
x3 = rng.normal(loc=0.0, scale=1.0, size=n_samples)

logit = 1.2 * x1 + 0.8 * x2 + 0.4 * x3 - 0.7 * (a == 1)
logit = logit + rng.normal(scale=0.9, size=n_samples)
y = (logit > 0.35).astype(int)

X = pd.DataFrame({"x1": x1, "x2": x2, "x3": x3})
X_train, X_test, y_train, y_test, a_train, a_test = train_test_split(
    X,
    y,
    a,
    test_size=0.3,
    stratify=y,
    random_state=23,
)

model = LogisticRegression(max_iter=2000)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

frame = MetricFrame(
    metrics={
        "selection_rate": selection_rate,
        "accuracy": accuracy_score,
        "false_positive_rate": false_positive_rate,
    },
    y_true=y_test,
    y_pred=y_pred,
    sensitive_features=a_test,
)

dp_diff = demographic_parity_difference(
    y_true=y_test,
    y_pred=y_pred,
    sensitive_features=a_test,
)
eo_diff = equalized_odds_difference(
    y_true=y_test,
    y_pred=y_pred,
    sensitive_features=a_test,
)
eopp_diff = equal_opportunity_difference(
    y_true=y_test,
    y_pred=y_pred,
    sensitive_features=a_test,
)

print("overall")
print(frame.overall)
print()
print("by_group")
print(frame.by_group)
print()
print("difference")
print(frame.difference())
print()
print("ratio")
print(frame.ratio())
print()
print("demographic_parity_difference", round(dp_diff, 3))
print("equalized_odds_difference", round(eo_diff, 3))
print("equal_opportunity_difference", round(eopp_diff, 3))
```

This example shows the main `MetricFrame` API surface that matters in practice: `.overall`, `.by_group`, `.difference()`, and `.ratio()`. The overall metric is the
familiar deployment average. The by-group view is the actual audit table. The difference and ratio views summarize disparity compactly, which is useful for dashboards and
compliance notes.

The temptation after seeing a large demographic parity difference is to declare the model unfair immediately. Sometimes that is correct. Sometimes it is too fast. A lower
selection rate may be the right alarm if the harm is about access to opportunity. It may be the wrong alarm if the task is one where different base rates exist and missed
qualified cases are the dominant concern. In that case equal opportunity may be the better focal metric. The library computes the numbers. Judgment selects the number
that matters.

A healthy assessment workflow therefore has three layers. First compute the group table. Then decide which disparity encodes the actual harm. Then document why that
metric, rather than a nearby alternative, is the governance anchor for the deployment. Fairlearn helps with the first layer. Engineers still have to do the next two.

## Section 7: Pre-processing Mitigations
Pre-processing mitigations intervene before model fitting. Their appeal is easy to understand. If the training data itself carries the structure that leads to disparity,
perhaps the cleanest move is to change the data distribution or the feature representation before the learner sees it. This family includes reweighting, resampling, and
feature transformation approaches.

Reweighting and resampling are model-agnostic. They do not require a special fairness-aware estimator. Instead they alter which examples count more heavily or how the
observed sample is balanced. The strength of this approach is that it can work with ordinary models and pipelines. The weakness is that it can only change the learner
indirectly. If the harm is driven by deeper representation issues or target-definition problems, balancing the sample may not be enough.

Fairlearn includes `CorrelationRemover` as a pre-processing tool. The idea is not magical fairness extraction. It is more limited and more honest. It filters out
components of features that are linearly correlated with the sensitive attribute, reducing the model's ability to recover that attribute directly from the transformed
features.

```python
import numpy as np
from fairlearn.preprocessing import CorrelationRemover

X_with_group = np.array(
    [
        [0.0, 1.0, 0.2],
        [0.0, 0.8, 0.1],
        [1.0, -0.3, 0.4],
        [1.0, -0.5, 0.3],
    ]
)

remover = CorrelationRemover(sensitive_feature_ids=[0], alpha=1.0)
X_transformed = remover.fit_transform(X_with_group)
print(X_transformed.shape)
```

The pros of pre-processing are practical. It is model-agnostic. It can slot into ordinary training code. It is often easier to explain than complex constrained
optimization. It can be appropriate when a representation-level repair is what the system needs. The cons are equally real. Reweighting can distort the data distribution
the model sees. Resampling can amplify noise. Correlation removal can strip predictive signal together with proxy signal, and linear decorrelation is not the same as
removing all downstream proxy structure.

Pre-processing is also the easiest family to misuse politically. Teams like it because it sounds clean: "we fixed the data." But if the model keeps creating a harmful gap
after training, the preprocessing step has not solved the real problem. It has only changed one input to the workflow. The audit must still be rerun after the model is
fit.

In other words, pre-processing is best understood as one timing option in a sequence, not as a moral guarantee. It acts before the learner. That can be the right place to
intervene. It does not remove the need for group-level measurement afterward.

## Section 8: In-processing Mitigations
In-processing mitigations change the learning algorithm itself. Instead of hoping a cleaned dataset will produce a fair model automatically, they optimize with fairness
constraints or fairness-aware objectives during fitting. This is often the most direct way to say, in code, that the system is willing to trade a bit of raw predictive
performance to reduce a named disparity.

Fairlearn's canonical reductions approach is `ExponentiatedGradient`. It wraps a base estimator and solves a constrained optimization problem over a collection of
classifiers, targeting criteria such as demographic parity or equalized odds. The key value is conceptual clarity. You specify the fairness constraint, the base learner,
and the sensitive features. The mitigation then searches for a classifier mixture that tries to respect the constraint while keeping predictive utility as high as it can.

```python
from fairlearn.reductions import DemographicParity, ExponentiatedGradient
from sklearn.linear_model import LogisticRegression

mitigator = ExponentiatedGradient(
    estimator=LogisticRegression(max_iter=2000),
    constraints=DemographicParity(),
)

mitigator.fit(X_train, y_train, sensitive_features=a_train)
y_pred_mitigated = mitigator.predict(X_test)
```

`GridSearch` is the simpler reductions alternative. It explores a grid of fairness-utility tradeoff points rather than using the exponentiated-gradient strategy. In
practice that can be easier to reason about when you want a more transparent scan over constraint settings, or when the problem is small enough that the simpler search
cost is acceptable.

The adversarial family takes a different route. `AdversarialFairnessClassifier` and `AdversarialFairnessRegressor` attempt to learn predictors whose outputs retain task
signal while making it harder for an auxiliary adversary to recover the sensitive attribute. This can be powerful in representation-heavy settings, especially when
nonlinear proxy structure matters. It is also operationally heavier. Adversarial training is more complex to debug, more sensitive to optimization choices, and harder to
explain to non-specialists than reductions.

The pros of in-processing are strong when the fairness requirement is central. You are optimizing the actual learning problem rather than patching around it after the
fact. You can often achieve cleaner fairness-utility tradeoff control than with simple data balancing. The cons are just as real. You need a fairness-aware training loop,
more implementation discipline, and acceptance that the model class may become harder to inspect or reproduce.

In-processing is usually the right family when fairness is not an audit afterthought but a first-class training requirement. If the system cannot be deployed without
meeting a specific disparity target, constrained learning is often more honest than hoping post-hoc threshold changes will rescue an unconstrained model. The price is
engineering complexity, plus the performance-fairness tradeoff that this module keeps insisting on rather than hiding.

## Section 9: Post-processing Mitigations
Post-processing mitigations leave the base model mostly alone and change the decision rule afterward. This is attractive when the model is already trained, hard to
retrain, owned by another team, or part of a legacy pipeline. If the model outputs scores, a post-processing step can turn those scores into group-aware thresholds
intended to close a disparity gap.

Fairlearn's main post-processing tool is `ThresholdOptimizer`. It learns thresholding behavior subject to a fairness constraint such as demographic parity or equalized
odds. The crucial operational fact is that it works on a trained predictor. That makes it a pragmatic option when retraining is expensive or institutionally blocked.

```python
from fairlearn.postprocessing import ThresholdOptimizer
from sklearn.linear_model import LogisticRegression

post_model = ThresholdOptimizer(
    estimator=LogisticRegression(max_iter=2000),
    constraints="demographic_parity",
    predict_method="predict_proba",
)

post_model.fit(X_train, y_train, sensitive_features=a_train)
y_pred_post = post_model.predict(X_test, sensitive_features=a_test)
```

The strongest pro is obvious. It works on any pre-trained model that can provide an appropriate prediction method. You do not have to rebuild the training stack. You can
often evaluate several fairness constraints quickly. For teams with a frozen model artifact, this can be the only practical mitigation that ships in a reasonable time.

The strongest cons are equally obvious once you say them aloud. First, post-processing usually requires the sensitive attribute at inference time, because the threshold
rule depends on group membership. That can be legally, ethically, or operationally impossible. Second, per-group thresholding can be controversial in jurisdictions where
differential treatment by group raises serious legal concerns even if the intent is to reduce disparity. Third, it can feel like a patch if the upstream representation or
labeling problem remains untouched.

This is why post-processing is best understood as the final timing option, not as the universally safest one. It is powerful because it is downstream of model training.
It is risky because it makes the group-conditioned nature of the decision rule explicit at prediction time. That explicitness can be both the point and the obstacle.

A disciplined team will therefore ask three questions before defaulting to `ThresholdOptimizer`. Can we legally and operationally use the sensitive attribute at
inference? Do we trust the score ranking enough that threshold adjustment is a meaningful intervention? And if we close the gap this way, are we comfortable documenting
that the fairness policy lives in the thresholding layer rather than in the learned representation itself?

## Section 10: The Performance-Fairness Tradeoff
Every fairness module that avoids this section is being dishonest. Closing a fairness gap usually costs something on a global performance metric. Sometimes that cost is
small. Sometimes it is substantial. Sometimes it appears in accuracy, sometimes in calibration, sometimes in ranking quality, sometimes in operational complexity rather
than a single scalar score. The tradeoff is real.

This is not a failure of fairness methods. It is the predictable result of optimizing more than one objective. If an unconstrained model has learned a decision rule that
exploits historical structure correlated with group membership, then constraining or correcting that rule can reduce whatever metric benefited from that structure. A
fairness mitigation is not discovering free utility hidden in the codebase. It is changing what the system optimizes.

The performance-fairness tradeoff is therefore not embarrassing fine print. It is the engineering content of the module. Teams need to know how much global accuracy, how
much false positive burden, how much threshold complexity, or how much retraining cost they are accepting in order to reduce a group disparity. That is the real design
decision. The metric table before mitigation and the metric table after mitigation are the evidence.

The wrong reaction is to treat any performance loss as proof that fairness work is misguided. The right reaction is to ask whether the lost performance was paying for a
harmful disparity. If it was, then some loss may be the price of stopping the system from externalizing cost onto one group. The equally wrong reaction is to ignore the
loss and pretend the mitigation is free. Mature teams document both sides.

This is also why mitigation choice matters. A pre-processing change may spread performance pain differently than a reductions-based in-processing constraint. A
post-processing threshold change may preserve ranking quality while changing hard decision rates. The audit record should therefore show not only that a gap closed, but
also how the cost appeared and why that cost was acceptable under the deployment's governance rules.

## Section 11: The Compliance Map
Fairness work does not happen in a legal vacuum. In Europe, the EU AI Act creates high-risk categories where systems used in contexts such as employment or access to
essential services face significant obligations. The reference site at https://artificialintelligenceact.eu/ describes the Act as assigning applications to risk
categories, with high-risk systems subject to specific requirements. A fairness audit is not the whole compliance story, but in high-risk categories it becomes part of
the evidence that the system's harms were looked for deliberately rather than accidentally discovered later.

GDPR Article 22 adds another relevant frame for automated individual decision-making. The text at https://gdpr-info.eu/art-22-gdpr/ states that a data subject has a right
not to be subject to a decision based solely on automated processing, including profiling, when that decision produces legal or similarly significant effects, subject to
specific exceptions and safeguards. This matters because many fairness-sensitive systems are also profiling systems. Technical mitigation choices cannot be separated
cleanly from rights around human review, contestability, and documentation.

In the United States, sector-specific regulations matter heavily. Credit contexts raise Equal Credit Opportunity Act concerns. Employment contexts raise Title VII
concerns. Housing contexts raise Fair Housing Act concerns. The point is not that one library somehow satisfies all of these. The point is that the technical work has to
map to the legal context, not the other way around. You do not start with a favorite metric and then ask which law it might impress. You start with the decision domain,
the protected groups, the relevant harms, and the review obligations, then choose the technical audit accordingly.

This mapping has a hard operational consequence. Auditing often requires labeled group membership. But collecting and storing group labels can itself be a legal, privacy,
ethical, and governance issue. Sometimes the organization has the data lawfully. Sometimes it does not. Sometimes it may use it for auditing but not for inference.
Sometimes the data quality for the sensitive attribute is poor or self-reported in ways that complicate interpretation. The fairness workflow must document these limits
rather than pretending group labels are frictionless.

Compliance work therefore needs a triangle, not a single axis. One corner is the technical metric. Another is the legal regime. The third is the data-governance process
that determines how sensitive attributes are collected, retained, and used. A team that optimizes only the first corner can still fail the deployment.

## Section 12: What Fairness Is NOT
Fairness is not interpretability. A transparent model can still be unfair. A simple scorecard with perfectly visible coefficients can deny one group far more often than
another or produce a higher false positive rate for that group. The fact that you can explain the coefficients does not sanitize the outcome. That is why [Module 2.2:
Interpretability and Failure Slicing](../module-2.2-interpretability-and-failure-slicing/) is adjacent to this one rather than a replacement for it.

The converse also matters. A black-box model can pass a chosen fairness audit criterion in a specific deployment even if it is harder to interpret. Suppose a nonlinear
ensemble is calibrated within group, or meets an equalized-odds target under the chosen threshold policy, while a transparent baseline fails badly on the same audit. That
does not settle the governance debate, but it shows why "interpretable" and "fair" are different axes. One is about legibility. The other is about disparate harm.

Fairness is not accuracy. Higher accuracy can reduce some disparities if the errors were broadly due to underfitting, but it can also leave disparities untouched or even
worsen them if the model gets better at exploiting structure that correlates with group membership. A model selection process that celebrates one more point of global
accuracy without inspecting who benefits from that gain is not doing fairness work.

Fairness is not calibration. A model can be well calibrated within each group and still violate equalized odds. That was part of the impossibility result earlier. The
calibration discipline from [Module 1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/) is crucial, but it is answering a different question: do
probabilities mean what they claim to mean? Fairness asks how harms are distributed when those probabilities become actions.

Fairness is also not subgroup conformal coverage, though the two can connect. [Module 2.5](../module-2.5-conformal-prediction-and-uncertainty-quantification/) taught that
marginal coverage can hide subgroup miscoverage. If one protected group systematically receives under-coverage, that is a fairness problem because the system's
uncertainty protection is worse for that cohort. Related does not mean identical. Fairness auditing is broader than coverage, but subgroup miscoverage is one concrete
manifestation of unfairness.

This section is deliberately negative because teams often approach fairness by mislabeling a nearby success. The model is interpretable, therefore fair. The model is
accurate, therefore fair. The model is calibrated, therefore fair. The model has marginal coverage, therefore fair. None of those inferences is valid. Fairness has to be
measured as fairness.

## Section 13: The Audit Playbook
A fairness audit becomes much easier once it is written as a sequence of moves. First identify the protected or sensitive attributes that matter in the legal and ethical
context of the deployment. This is a governance step before it is a coding step. The answer differs between domains, and sometimes the organization will need legal review
before even collecting the labels needed for audit.

Second pick the fairness metric that matches the harm structure. If the main harm is unequal access to opportunity, demographic parity may be the right starting point. If
the main harm is missing deserving positives, equal opportunity may be better. If both false positives and false negatives matter, equalized odds may be the correct
target. If a risk score drives downstream policy directly, calibration within group may be central. State the choice in plain language.

Third compute the metric per group with `MetricFrame` and companion disparity functions. Do not stop at the global score. Save the by-group table. Save the difference or
ratio summary. Save the sample counts. An audit artifact without support counts is fragile because a dramatic disparity on a tiny subgroup may be real, noisy, or both.
The record needs enough information to support judgment.

Fourth decide what to do with the gap. Mitigation is only one option. Sometimes the right answer is to mitigate with pre-processing, in-processing, or post-processing.
Sometimes the right answer is to document and accept because a different metric was deemed more aligned with the harm model. Sometimes the gap reveals a deeper defect in
labels, features, or deployment scope, and the correct answer is redesign or non-deployment.

Fifth re-evaluate after mitigation and expect performance cost. This step exists because fairness work that never remeasures is public relations. The post-mitigation
table should show the chosen disparity metric, the ordinary performance metrics, and a short explanation of how the tradeoff changed. If the gap closed only because the
system became unusably weak overall, the mitigation has not obviously succeeded.

Sixth document everything for compliance and future maintenance. Which groups did you audit? Which metric did you choose? Which criteria did you reject and why? What
mitigation timing did you choose? What was the cost? What assumptions about group labels, proxies, and inference-time availability shaped the design? The fairness audit
should be auditable itself.

This playbook is intentionally boring. That is a strength. Good fairness work is usually not a clever trick. It is careful sequence discipline under social and legal
pressure.

## Section 14: When Fairness Work Is the Wrong Tool
Fairness work is the wrong tool when the underlying problem is data quality. If labels are inconsistent, missing, stale, or operationally misdefined, the best fairness
metric in the world cannot rescue the audit. That is a [Module 1.4: Feature Engineering and Preprocessing](../module-1.4-feature-engineering-and-preprocessing/) problem
first. Poor data quality can masquerade as unfairness, but the right remedy may be better measurement, better labeling, or tighter preprocessing contracts.

Fairness work is also the wrong first tool when the problem is leakage. If the model is using future information, target proxies, or split contamination, apparent
disparities can be artifacts of a broken evaluation pipeline. [Module 1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/) comes first because a
fairness audit built on leaked evaluation is not a fairness audit. It is a story about corrupted evidence.

Sometimes the real issue is model misspecification. A linear model may be too rigid, or a tree-based model may be a better fit, or the threshold policy may be the wrong
deployment abstraction entirely. Those are model-choice questions from [Module 1.2: Linear and Logistic Regression with
Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/) and [Module 1.5: Decision Trees and Random
Forests](../module-1.5-decision-trees-and-random-forests/). Fairness metrics can surface the harm, but they are not substitutes for a model that understands the task.

Another failure mode is organizational rather than technical. Sometimes the stakeholders do not actually want fairness. They want the appearance of fairness without
accepting any tradeoff, any label collection burden, any legal review, or any change to the decision policy. That is not a tool-selection issue. It is a value conflict.
The correct response is to say that no fairness library can turn an unresolved normative disagreement into a solved engineering problem.

The mature ending to the module is therefore narrow and precise. Fairness auditing is a sharp tool for a sharp class of problems: systematic disparate harm across named
groups in consequential systems. When that is the problem, fairness work is indispensable. When the problem is dirty data, leakage, wrong model family, or a stakeholder
unwilling to make a normative choice, the tool is being asked to do a different job than the one it was built for.

## Did You Know?
- Fairlearn organizes mitigation work into distinct timing families rather than treating all fairness interventions as one technique, which is why the user guide
  separates assessment, preprocessing, reductions, postprocessing, and adversarial mitigation. Source: https://fairlearn.org/main/user_guide/mitigation/index.html

- Equal opportunity and equalized odds are not generic slogans; they were formalized as concrete error-rate criteria in the Hardt, Price, and Srebro paper that made
  threshold-based fairness tradeoffs operational for supervised learning. Source: https://arxiv.org/abs/1610.02413

- The impossibility discussion that dominates modern fairness debates is not a vague warning. It is a mathematical result showing that multiple desirable fairness
  criteria can conflict when groups have different base rates. Source: https://arxiv.org/abs/1609.05807

- Individual fairness entered the field through the idea that similar individuals should be treated similarly, but the hidden challenge is defining a defensible
  similarity metric for the real deployment. Source: https://arxiv.org/abs/1104.3913

## Common Mistakes
| Mistake | Why it bites | What to do instead |
| --- | --- | --- |
| Dropping the sensitive attribute and declaring victory | Proxies can still reconstruct group information, and the outcome disparity can remain unchanged | Keep the attribute for audit data, measure group outcomes directly, and document the proxy risk |
| Picking demographic parity because it sounds intuitive | The main harm may actually be false negatives or false positives rather than raw selection rate | Choose the metric that matches the deployment harm structure and justify the choice |
| Demanding every fairness criterion at once | Base-rate differences make several criteria incompatible | Explain the impossibility result and force a governance choice about priority |
| Treating `MetricFrame.overall` as the audit | The global score hides the group gap you were supposed to inspect | Save and review `.by_group`, `.difference()`, `.ratio()`, and support counts |
| Using post-processing without checking inference-time group access | `ThresholdOptimizer` usually needs sensitive features at prediction time | Confirm legal and operational feasibility before choosing post-processing |
| Calling fairness an interpretability problem | A transparent model can still impose disparate harm | Audit group outcomes directly and use interpretability only as a supporting diagnostic |
| Ignoring the performance cost after mitigation | A closed fairness gap can come with unusable predictive behavior | Remeasure global performance and record the tradeoff explicitly |
| Auditing without a legal map | The same metric can be irrelevant or insufficient depending on the domain | Tie the technical audit to the sector, rights, and compliance context |

## Quiz
1. A credit-scoring team finds that one group's approval rate is much lower than another's, but the true positive rates are nearly identical. Which question should the
   team ask before declaring the system unfair under its chosen metric?

<details><summary>Answer</summary>
They should ask which harm matters operationally. If the main concern is unequal access to opportunity, the lower approval rate may make demographic parity the relevant
audit lens. If the concern is missing qualified cases, then equal opportunity may be more important, and the near-equal true positive rates would matter more. The right
move is not to declare victory or failure from one chart. It is to tie the metric to the harm model first.
</details>

2. A model excludes the protected attribute from training, yet the audit still shows a large false positive rate gap across groups. What is the most likely explanation,
   and what should the team do next?

<details><summary>Answer</summary>
The most likely explanation is proxy structure. Other features carried enough group information for the model to reproduce the disparity. The next step is to keep the
sensitive attribute in the assessment pipeline, inspect the relevant group metrics with `MetricFrame`, and decide whether preprocessing, in-processing, post-processing,
or deeper redesign is warranted.
</details>

3. A stakeholder insists on demographic parity, equalized odds, and calibration within group for a deployment where observed event rates differ by group. What is the
   correct engineering response?

<details><summary>Answer</summary>
The correct response is that the request is not generally satisfiable under different base rates. The team must return to the harm model, explain the impossibility
result, and choose which criterion has governance priority for the deployment rather than pretending all three can be optimized simultaneously.
</details>

4. Your team can only access the sensitive attribute offline for audit, not at inference time. Which mitigation family becomes less attractive, and why?

<details><summary>Answer</summary>
Post-processing becomes less attractive because methods such as `ThresholdOptimizer` generally need the sensitive attribute at prediction time to apply group-conditioned
thresholds. If inference-time access is unavailable or unacceptable, pre-processing or in-processing methods may be more feasible.
</details>

5. A fairness mitigation closes a demographic parity gap but drops overall utility enough that the operations team can no longer rely on the model for automated
   approvals. What is the right conclusion?

<details><summary>Answer</summary>
The right conclusion is not that fairness work failed or succeeded in isolation. It is that the chosen mitigation produced a tradeoff the deployment may not accept. The
team must document the reduced disparity, the lost utility, and then decide whether to try a different mitigation family, redesign the task, narrow the automation scope,
or keep human review in the loop.
</details>

6. A team reports that its model is fair because it is a sparse logistic regression with fully visible coefficients. What is missing from that claim?

<details><summary>Answer</summary>
Interpretability evidence is missing the fairness evidence. A transparent model can still deny one group more often, produce uneven false positive rates, or under-serve a
named cohort. The team still needs a group-level audit on the appropriate fairness metrics, plus documentation of why those metrics match the harm structure.
</details>

7. A conformal classification system has valid marginal coverage overall, but one protected group receives noticeably lower empirical coverage than another. Why does that
   belong in a fairness module rather than only an uncertainty module?

<details><summary>Answer</summary>
Because one cohort is receiving a worse form of uncertainty protection. The global conformal contract can still hold while a protected group is under-covered. That
subgroup miscoverage is a group-level harm question, so the team must audit it as fairness rather than dismissing it as an acceptable side effect of the overall average.
</details>

## Hands-On Exercise
- [ ] Step 0: Import the standard numerical stack, an ordinary classifier, and the Fairlearn assessment and mitigation tools used in this module.

```python
import numpy as np
import pandas as pd
from fairlearn.metrics import (
    MetricFrame,
    count,
    demographic_parity_difference,
    demographic_parity_ratio,
    equal_opportunity_difference,
    equalized_odds_difference,
    equalized_odds_ratio,
    false_positive_rate,
    selection_rate,
    true_positive_rate,
)
from fairlearn.postprocessing import ThresholdOptimizer
from fairlearn.reductions import DemographicParity, ExponentiatedGradient
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
```

- [ ] Step 1: Build a synthetic binary-classification dataset with two groups. Make one group's base rate lower, and make the feature distribution slightly different
      across groups so that proxy structure is plausible rather than artificial.

```python
rng = np.random.default_rng(31)
n_samples = 2200
a = rng.integers(0, 2, size=n_samples)

x1 = rng.normal(loc=np.where(a == 0, 0.5, -0.4), scale=1.0, size=n_samples)
x2 = rng.normal(loc=np.where(a == 0, 0.3, -0.2), scale=1.1, size=n_samples)
x3 = rng.normal(loc=np.where(a == 0, 0.0, 0.2), scale=1.0, size=n_samples)

logit = 1.1 * x1 + 0.8 * x2 + 0.5 * x3 - 0.8 * (a == 1)
logit = logit + rng.normal(scale=1.0, size=n_samples)
y = (logit > 0.45).astype(int)

X = pd.DataFrame({"x1": x1, "x2": x2, "x3": x3})
print("group base rates")
print(pd.Series(y).groupby(a).mean())
```

- [ ] Step 2: Train a baseline `LogisticRegression`. Keep the sensitive attribute out of the feature matrix, but keep it in the train and test split outputs for audit.

```python
X_train, X_test, y_train, y_test, a_train, a_test = train_test_split(
    X,
    y,
    a,
    test_size=0.3,
    stratify=y,
    random_state=31,
)

baseline = LogisticRegression(max_iter=2000)
baseline.fit(X_train, y_train)
y_pred_baseline = baseline.predict(X_test)
```

- [ ] Step 3: Create a `MetricFrame` using `selection_rate`, `accuracy_score`, and `false_positive_rate`. Also compute `demographic_parity_difference` and
      `equalized_odds_difference`. Write one paragraph stating which metric best matches the harm you care about in this synthetic task.

```python
frame_baseline = MetricFrame(
    metrics={
        "count": count,
        "selection_rate": selection_rate,
        "accuracy": accuracy_score,
        "false_positive_rate": false_positive_rate,
        "true_positive_rate": true_positive_rate,
    },
    y_true=y_test,
    y_pred=y_pred_baseline,
    sensitive_features=a_test,
)

dp_diff_baseline = demographic_parity_difference(
    y_true=y_test,
    y_pred=y_pred_baseline,
    sensitive_features=a_test,
)
dp_ratio_baseline = demographic_parity_ratio(
    y_true=y_test,
    y_pred=y_pred_baseline,
    sensitive_features=a_test,
)
eo_diff_baseline = equalized_odds_difference(
    y_true=y_test,
    y_pred=y_pred_baseline,
    sensitive_features=a_test,
)
eo_ratio_baseline = equalized_odds_ratio(
    y_true=y_test,
    y_pred=y_pred_baseline,
    sensitive_features=a_test,
)
eopp_diff_baseline = equal_opportunity_difference(
    y_true=y_test,
    y_pred=y_pred_baseline,
    sensitive_features=a_test,
)

print(frame_baseline.by_group)
print("dp_diff", round(dp_diff_baseline, 3))
print("dp_ratio", round(dp_ratio_baseline, 3))
print("eo_diff", round(eo_diff_baseline, 3))
print("eo_ratio", round(eo_ratio_baseline, 3))
print("eopp_diff", round(eopp_diff_baseline, 3))
```

- [ ] Step 4: Apply post-processing mitigation with `ThresholdOptimizer(constraints="demographic_parity")`. Recompute the same metrics and compare them to the baseline.

```python
post = ThresholdOptimizer(
    estimator=LogisticRegression(max_iter=2000),
    constraints="demographic_parity",
    predict_method="predict_proba",
)
post.fit(X_train, y_train, sensitive_features=a_train)
y_pred_post = post.predict(X_test, sensitive_features=a_test)

frame_post = MetricFrame(
    metrics={
        "selection_rate": selection_rate,
        "accuracy": accuracy_score,
        "false_positive_rate": false_positive_rate,
        "true_positive_rate": true_positive_rate,
    },
    y_true=y_test,
    y_pred=y_pred_post,
    sensitive_features=a_test,
)

print(frame_post.by_group)
print(
    "dp_diff_post",
    round(
        demographic_parity_difference(
            y_true=y_test,
            y_pred=y_pred_post,
            sensitive_features=a_test,
        ),
        3,
    ),
)
print(
    "eo_diff_post",
    round(
        equalized_odds_difference(
            y_true=y_test,
            y_pred=y_pred_post,
            sensitive_features=a_test,
        ),
        3,
    ),
)
```

- [ ] Step 5: Apply in-processing mitigation with `ExponentiatedGradient` and a `DemographicParity` constraint. Remeasure the same metrics and compare the disparity
      pattern against the post-processing result.

```python
inproc = ExponentiatedGradient(
    estimator=LogisticRegression(max_iter=2000),
    constraints=DemographicParity(),
)
inproc.fit(X_train, y_train, sensitive_features=a_train)
y_pred_inproc = inproc.predict(X_test)

frame_inproc = MetricFrame(
    metrics={
        "selection_rate": selection_rate,
        "accuracy": accuracy_score,
        "false_positive_rate": false_positive_rate,
        "true_positive_rate": true_positive_rate,
    },
    y_true=y_test,
    y_pred=y_pred_inproc,
    sensitive_features=a_test,
)

print(frame_inproc.by_group)
print(
    "dp_diff_inproc",
    round(
        demographic_parity_difference(
            y_true=y_test,
            y_pred=y_pred_inproc,
            sensitive_features=a_test,
        ),
        3,
    ),
)
print(
    "eo_diff_inproc",
    round(
        equalized_odds_difference(
            y_true=y_test,
            y_pred=y_pred_inproc,
            sensitive_features=a_test,
        ),
        3,
    ),
)
```

- [ ] Step 6: Write a short paragraph naming the harm-matching metric, the mitigation you would choose, the performance cost you observed, and the record you would hand
      to compliance. The paragraph should name the protected group field, the pre-mitigation disparity, the post-mitigation disparity, the ordinary performance change,
      and any limitation such as the need for sensitive features at inference time.

### Completion Check
- [ ] I measured fairness by named group rather than relying on the global accuracy score.
- [ ] I stated which fairness metric matched the harm structure and why.
- [ ] I reran the audit after both post-processing and in-processing mitigation.
- [ ] I recorded the performance cost instead of pretending the mitigation was free.
- [ ] I wrote down whether the chosen mitigation requires the sensitive attribute at inference time.

## Sources
- https://fairlearn.org/main/
- https://fairlearn.org/main/user_guide/index.html
- https://fairlearn.org/main/user_guide/fairness_in_machine_learning.html
- https://fairlearn.org/main/user_guide/assessment/index.html
- https://fairlearn.org/main/user_guide/mitigation/index.html
- https://fairlearn.org/main/api_reference/index.html
- https://fairlearn.org/main/auto_examples/
- https://github.com/fairlearn/fairlearn
- https://aif360.readthedocs.io/en/stable/
- https://arxiv.org/abs/1610.02413
- https://arxiv.org/abs/1609.05807
- https://arxiv.org/abs/1610.07524
- https://arxiv.org/abs/1104.3913
- https://artificialintelligenceact.eu/
- https://gdpr-info.eu/art-22-gdpr/

## Next Module
The next module in this Tier-2 sequence is Module 2.7, causal inference for ML practitioners. This module deliberately ended at the point where a team has to say which
harms it cares about and which fairness metric it is willing to use. The next step asks a different question: not whether predictions distribute harm evenly, but whether
an intervention would change the world in the way the team thinks it would. That is why the forward reference is plain text rather than a link. It is the next conceptual
move, but it is a different one.
