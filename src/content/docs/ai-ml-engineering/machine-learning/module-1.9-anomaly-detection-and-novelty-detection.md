---
title: "Anomaly Detection & Novelty Detection"
description: "Learn how to choose, fit, and evaluate anomaly and novelty detectors when you have no labels. This module covers IsolationForest, LocalOutlierFactor, OneClassSVM, and EllipticEnvelope, the contamination parameter, the anomaly/novelty distinction, and honest threshold calibration."
slug: ai-ml-engineering/machine-learning/module-1.9-anomaly-detection-and-novelty-detection
revision_pending: false
sidebar:
  order: 9
---

> Track: AI/ML Engineering | Complexity: Intermediate | Time: 75-90 minutes
> Prerequisites: [Module 1.1: Scikit-learn API & Pipelines](../module-1.1-scikit-learn-api-and-pipelines/), [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/), [Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/), [Module 1.7: Naive Bayes, k-NN & SVMs](../module-1.7-naive-bayes-knn-and-svms/), and [Module 1.8: Unsupervised Learning: Clustering](../module-1.8-unsupervised-learning-clustering/).
> Environment note: the worked examples are Python and scikit-learn focused; when this scoring logic is later deployed on Kubernetes 1.35 or newer, this curriculum uses `k` as the kubectl alias after `alias k=kubectl`, but this module does not require cluster access.

Modern ML teams spend a great deal of time dealing with data that is
rare, surprising, malformed, or operationally suspicious, yet only a
small part of that time fits the neat supervised-learning story where
someone already labeled every important case.

An anomaly detector sits in that uncomfortable middle ground.
It is asked to rank, flag, or quarantine observations that seem unlike
what the system considers normal, even when the notion of "normal" is
only partly known and rarely stationary.

That makes this module less about a single algorithm and more about a
decision discipline.
Choosing a detector is inseparable from deciding what training data
means, what score semantics mean, what threshold means, and what kinds
of errors the surrounding workflow can tolerate.

The previous modules already built the foundations needed for this.
[Module 1.1: Scikit-learn API & Pipelines](../module-1.1-scikit-learn-api-and-pipelines/)
covered estimator interfaces and composition.
[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/)
established the habit of asking whether an apparent signal is actually
trustworthy.
[Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/)
made scaling, encoding, and leakage control explicit.
[Module 1.7: Naive Bayes, k-NN & SVMs](../module-1.7-naive-bayes-knn-and-svms/)
showed why distance and kernel methods care deeply about representation.
[Module 1.8: Unsupervised Learning: Clustering](../module-1.8-unsupervised-learning-clustering/)
showed that density, neighborhoods, and cluster structure can be useful
even before labels exist.

This module builds directly on those ideas, but it does not simply
restate them with a new vocabulary.
Anomaly detection introduces a harder epistemic problem:
the detector can always produce a ranking, but the ranking is not the
same thing as verified abnormality.

The goal here is to become technically competent and intellectually
honest at the same time.
By the end, the reader should be able to choose among
`IsolationForest`, `LocalOutlierFactor`, `OneClassSVM`, and
`EllipticEnvelope`, understand why they disagree, and calibrate their
outputs without pretending that unlabeled data somehow evaluates itself.

The subject also has a way of becoming important without much warning.
A detector first appears as a utility score, then gradually becomes part
of operational routing, analyst prioritization, and automated triage.
By the time people realize they depend on it, many threshold and data
assumptions have already hardened into habit.

That is why this module keeps returning to first principles.
What is the model assuming about the data?
What does the output actually mean?
What action will someone take because of that output?
Those questions are more valuable than memorizing any single default.

## Learning Outcomes

- Compare IsolationForest, LOF, OneClassSVM, and EllipticEnvelope tradeoffs for anomaly and novelty workflows.
- Diagnose representation, scaling, threshold, and mode-confusion failures by inspecting `score_samples()`, `predict()` labels, and detector disagreement.
- Design threshold calibration with partial labels, precision at `k`, review budget, and contamination policy instead of default binary labels.
- Implement LOF anomaly versus novelty workflows without misusing training-data prediction or leaking preprocessing across reference and future samples.
- Justify replacing anomaly detection with supervised classification, clustering, time-series forecasting, or monitoring when the operational question demands another tool.

## Why This Module Matters

The scikit-learn user guide on outlier and novelty detection begins the
conversation from an engineering reality rather than a marketing slogan:
[https://scikit-learn.org/stable/modules/outlier_detection.html](https://scikit-learn.org/stable/modules/outlier_detection.html)
separates problems where the training data itself contains outliers from
problems where training data is assumed clean and only future
observations are expected to contain surprising cases.

That distinction sounds small until someone carries an on-call phone.
A model health alert fires after midnight.
A fresh batch of records has been flagged.
An analyst opens a dashboard and sees red markers scattered across a
feature projection.
The question is not "did the library succeed in returning labels?"
It did.
The question is whether those labels correspond to the operational event
the team cares about.

In anomaly mode, the detector is allowed to assume that the training set
already mixes ordinary and abnormal observations.
Its job is to identify unusual points inside that contaminated training
sample.
In novelty mode, the detector is trained on data treated as clean, then
used later to score new observations against the learned notion of
normality.

That sounds like a documentation distinction, but it changes the meaning
of fitting, the meaning of predicting, and the meaning of error.
If the wrong mode is chosen, the resulting system may still look
confident while silently solving the wrong problem.

This is why anomaly detection deserves its own module instead of a short
appendix after clustering.
The algorithm always returns something; the engineering question is
whether what it returned is true.

That sentence is a useful antidote to overconfidence.
An unsupervised score can feel persuasive because it arrives wrapped in
mathematical language and precise decimals.
But a detector can be numerically consistent and still misaligned with
the event a team actually wants to catch.

The expensive part of that misalignment is usually not compute.
It is human attention.
Every false escalation consumes review time, dilutes trust, and makes
future alerts easier to ignore.
That is why thresholding and evaluation are as central as fitting.

Anomaly detection also matters because it appears where labels are
expensive, delayed, politically contested, or impossible to define in
advance.
A fraud queue may receive human review only for the most suspicious
cases.
A predictive-maintenance workflow may have very few confirmed failures.
A data-quality pipeline may know that some records are malformed without
knowing all the forms failure can take next month.

In such settings, the detector is rarely the whole system.
It is a component in a triage loop.
It pushes cases to review, suppression, fallback logic, or additional
models.
That means score ranking, threshold policy, and error handling often
matter more than the seductive visual of separating blue and red points
on a synthetic toy dataset.

This module focuses on the tools scikit-learn provides for that job and
the reasoning needed to use them honestly.
The emphasis is not on memorizing method names.
It is on learning how to align detector assumptions with data geometry,
deployment constraints, and the limits of what unlabeled evidence can
support.

## Section 1: What Anomaly Detection Is, and What It Is Not

The first mistake most teams make is treating anomaly detection as
ordinary classification with one class missing.
That framing feels intuitive because a future dashboard usually shows a
binary outcome:
flagged or not flagged.
But the training problem is fundamentally different.

A supervised classifier learns a boundary between labeled categories.
Even when the classes are imbalanced, it can still anchor its geometry
to known examples of both sides.
An anomaly detector typically learns a description of normality,
local density, or isolation structure, then treats deviation from that
description as suspicious.

This difference matters because "not yet labeled" is not the same as
"negative class omitted."
If the unseen abnormal cases are heterogeneous, sparse, and changing,
then there may be no single stable abnormal region to learn anyway.
What exists instead is a collection of ways normality can fail.

This is one reason anomaly detection often feels messier than ordinary
classification.
The positive concept is not unified.
The model is usually trying to find departures from structure rather
than learn a stable opposing class with consistent support.

That is why anomaly detection should be understood as a structured
ranking problem under uncertainty.
The model does not reveal truth directly.
It provides a score that says, in effect, "under my assumptions,
this point appears less compatible with the reference data than these
other points."

Consider a fraud-review queue.
A payment workflow receives transactions with mixed feature types,
changing behavior patterns, and only partial human follow-up.
Many suspicious transactions are never confirmed either way because
investigators have finite time.
An anomaly detector can prioritize what looks unusual, but it does not
know the legal or business definition of fraud unless such labels are
available and used downstream.

Consider predictive maintenance.
Sensors from a machine stream values that usually remain within ordinary
operating ranges.
Rare fault states may exist, but the system might have recorded only a
few.
An anomaly detector can flag departures from historical behavior even if
it has never seen the exact failure mode before.
That is useful precisely because the problem is not "classify among many
well-sampled fault labels."

Consider data quality.
A tabular ingestion pipeline may receive duplicated records, impossible
combinations, abrupt schema shifts, or strange free-text patterns.
Some defects are rule-based and easy to catch.
Others are merely odd.
An anomaly detector can rank rows for manual inspection or quarantine,
but it cannot replace clear validation rules where those rules exist.

In practice, the healthiest systems use both.
Rules protect invariants that are already known.
Anomaly detectors scan for the failures the rules have not yet learned to
name.
Confusing those roles usually makes both systems worse.

These examples share a pattern.
The detector is most valuable when it acts as a suspiciousness lens,
not when it is forced to impersonate a fully labeled business decision.

Another misconception is that anomaly detection is inherently more
objective because it is "unsupervised."
In practice, unsupervised methods often move human judgment to other
places:
choosing the reference window, selecting features, setting thresholds,
deciding contamination, and interpreting disagreement among detector
families.

That is not a weakness unique to anomaly detection.
It is simply what honest engineering looks like when labels are scarce.
The mistake is pretending those judgment calls disappeared because the
estimator exposes a `.fit()` method.

This is also why raw anomaly scores deserve more respect than hard class
labels.
The score retains ordering information that can be calibrated, compared,
and monitored.
The binary output often hides how arbitrary the threshold decision was.

For many teams, this is the mental shift that makes anomaly detection
practical.
The detector is not primarily a machine for declaring truth.
It is a machine for ordering uncertainty in a way humans and systems can
act on.

By the time a production team discovers that a threshold is too high or
too low, the score distribution often contains the real diagnostic
signal.
The fixed labels alone rarely do.

Anomaly detection is therefore best framed as a disciplined attempt to
surface unexpected observations under explicit assumptions.
It is not a magical shortcut around missing labels, and it is not a
license to stop asking whether the modeled notion of abnormality matches
the operational one.

If that sounds more cautious than glamorous, that is intentional.
The reward for this caution is a detector that survives contact with
real workflows instead of only looking good in static screenshots.

## Section 2: Anomaly vs. Novelty Detection

The most important conceptual split in this module is the one the
scikit-learn guide uses:
outlier or anomaly detection assumes the training set already contains
abnormal points, while novelty detection assumes training data is mostly
or entirely clean and future scoring is applied to new examples.

That wording is easy to skim past, but it decides what fitting means.
In anomaly detection mode, the algorithm is trying to identify unusual
points within the same sample that taught it the data structure.
In novelty detection mode, the model learns the support of normal data,
then evaluates whether later points fall outside that learned support.

Operationally, this changes the contract.
If the training set is contaminated and you act as if it were clean, the
model may absorb abnormal structure into its idea of normality.
If the training set is clean and you force an anomaly-mode tool that is
meant to label points in that same dataset, you may get reasonable
numbers but an incoherent deployment workflow.

A compact memory aid is to ask where abnormal points are allowed to
exist at fit time.
If they are expected inside the fitted sample, think anomaly detection.
If they are expected to arrive later against a cleaner baseline, think
novelty detection.

The user guide also gives a subtle but important geometric warning in
plain language.
For outlier detection, the methods generally assume outliers live in
low-density regions and do not themselves form a dense cluster.
For novelty detection, a group of novel points can form its own dense
cluster, as long as that cluster occupies a low-density region relative
to the training data.

That difference explains why teams sometimes argue past one another.
One person imagines "anomalies" as isolated weird points.
Another imagines a whole new subpopulation appearing after launch.
Both are reasonable scenarios, but they are not the same modeling task.

Suppose a new customer segment enters a system after deployment.
If the training data never contained that segment, a novelty detector
may correctly score many of those points as abnormal even if they are
close to one another.
By contrast, an outlier detector operating inside a contaminated
training sample may be biased toward treating dense clusters as normal
structure and scattered points as the actual anomalies.

This is why the anomaly-versus-novelty distinction should appear in
design reviews, not just in notebook comments.
Teams need to answer concrete questions.
Is the reference dataset supposed to include suspicious examples or
exclude them?
Will the model ever be asked to score the training set itself?
Is the downstream workflow triaging old data, screening incoming data,
or both?

Those questions also influence how data is collected.
If the workflow needs novelty detection, then preserving a trustworthy
reference set becomes a data-governance concern.
If the workflow needs anomaly detection inside a current batch, then the
sampling and batching strategy becomes part of model behavior.

The answers shape API choices as well.
Some estimators in scikit-learn expose different capabilities depending
on which mode is selected.
This is most visible with `LocalOutlierFactor`, where novelty mode
changes which methods are legal and how predictions should be
interpreted.

A reliable habit is to write the mode in plain English before writing
code.
For example:
"Train on a baseline month believed to be mostly clean, then score new
batches for novelty."
Or:
"Fit on the current table and rank suspicious rows within that table for
review."

Those two sentences lead to different validation plans, different
failure modes, and sometimes different estimators.
If that sentence cannot be written clearly, the modeling problem is not
ready.

This is not bureaucratic overhead.
Teams that skip this sentence usually end up debugging behavior that was
already implied by an ambiguous problem statement.

## Section 3: IsolationForest

`IsolationForest` is often the first detector practitioners reach for
because its intuition is simple, its defaults are practical, and its
runtime profile is usually friendly on medium and large tabular data.
Its API reference is here:
[https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html).

The core idea is not to estimate density directly.
Instead, the method builds many random trees and asks how quickly a
point becomes isolated by random splits.
Points that require only a small number of random partition steps to be
separated from the rest are treated as more anomalous.

This makes intuitive sense.
If an observation sits far from dense regions, many random cuts will
peel it away quickly.
If it lives in a crowded ordinary region, random cuts tend to keep it
grouped with many neighbors for longer.

Because the method is tree-based, it inherits one of the practical
virtues discussed in
[Module 1.5: Decision Trees & Random Forests](../module-1.5-decision-trees-and-random-forests/):
it does not rely on Euclidean distance in the same direct way that
neighbor methods or kernel methods do.
That means feature scaling is usually not the first concern.
Representation still matters, but standardization is not mandatory in
the way it is for `LocalOutlierFactor` or `OneClassSVM`.

The default constructor encodes several useful assumptions.
`n_estimators=100` means a moderate forest by default.
`max_samples='auto'` means each base estimator samples
`min(256, n_samples)`.
`contamination='auto'` means thresholding follows estimator-specific
logic rather than a fixed user-declared fraction.
`max_features=1.0` uses all features for each split search,
and `bootstrap=False` means sampling without bootstrap duplication.

Those defaults are sane enough that many first experiments should begin
by leaving them untouched.
A team often learns more by examining score distributions and failure
cases than by rushing to parameter search.

That advice is especially important when the detector is being used for
initial discovery.
If the first reaction to a mediocre result is a long hyperparameter
search, the team may be tuning before it has even confirmed that the
family's notion of suspiciousness matches the problem.

The score semantics also matter.
Across the four estimators in this module, `predict()` returns `+1` for
inliers and `-1` for outliers.
For `IsolationForest`, `decision_function()` uses the thresholded view:
negative values indicate outliers and non-negative values indicate
inliers.
`score_samples()` exposes a continuous score where lower values mean
more abnormal observations.
The scikit-learn documentation notes that this score is the opposite of
the anomaly score used in the original paper, which is why reading the
docstring matters more than relying on memory.

That detail may seem small, but it prevents a class of silent mistakes.
If a team assumes "higher means more anomalous" because of an older
paper or another library, it can invert a ranking, misread a chart, or
apply the wrong threshold direction without any syntax error warning.

The strength of `IsolationForest` is that it often works reasonably well
on mixed-shape tabular problems without expensive distance matrices or
strong Gaussian assumptions.
It also handles larger sample counts better than many kernel methods.
Its weakness is that "easy to isolate" is not identical to
"semantically abnormal."
A small but legitimate subgroup can look suspicious.
A dense cluster of unusual cases can look less suspicious than expected
if the feature representation does not place it in an isolated region.

That last caveat matters more than it first appears.
The model knows nothing about business rarity.
It only knows how quickly random splits can separate a point from the
rest of the sample.
Those two ideas often align, but they are not interchangeable.

It is also important to know what the estimator does not do.
Unlike some online or incremental estimators, `IsolationForest` in
scikit-learn does not expose `partial_fit`.
If the workflow needs ongoing adaptation, the retraining strategy has to
be designed explicitly rather than assumed.
That matters in the same way incremental assumptions mattered when
contrasting boosting workflows in
[Module 1.6: XGBoost & Gradient Boosting](../module-1.6-xgboost-gradient-boosting/):
not every ensemble API implies streaming updates.

The best way to make these semantics concrete is to run a small example.
The following script builds two ordinary clusters, injects uniformly
spread anomalies, fits an `IsolationForest`, and visualizes both the
score distribution and the decision boundary.

> **Pause and predict** - Before reading the plot, decide which points
> will have the lowest `score_samples()` values: the uniform noise, the
> cluster edges, or the cluster centers. Also predict whether the
> histogram will show a clean gap or a messy overlap.

```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_blobs
from sklearn.ensemble import IsolationForest

rng = np.random.RandomState(0)

X_normal, _ = make_blobs(
    n_samples=400,
    centers=[(-2, -2), (2, 2)],
    cluster_std=[0.8, 0.9],
    random_state=0,
)

X_anomaly = rng.uniform(low=-6, high=6, size=(40, 2))
X = np.vstack([X_normal, X_anomaly])
y_true = np.hstack([np.ones(len(X_normal)), -np.ones(len(X_anomaly))])

model = IsolationForest(
    n_estimators=100,
    contamination=0.1,
    random_state=0,
)
model.fit(X)

scores = model.score_samples(X)
labels = model.predict(X)

print("Lowest five scores:", np.sort(scores)[:5])
print("Predicted outliers:", np.sum(labels == -1))

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

axes[0].hist(scores, bins=30, color="steelblue", edgecolor="black")
axes[0].set_title("IsolationForest score_samples")
axes[0].set_xlabel("score_samples (lower = more abnormal)")
axes[0].set_ylabel("count")

xx, yy = np.meshgrid(
    np.linspace(-6.5, 6.5, 300),
    np.linspace(-6.5, 6.5, 300),
)
grid = np.c_[xx.ravel(), yy.ravel()]
zz = model.decision_function(grid).reshape(xx.shape)

axes[1].contourf(xx, yy, zz, levels=20, cmap="RdYlBu")
axes[1].contour(xx, yy, zz, levels=[0], colors="black", linewidths=2)
axes[1].scatter(X[:, 0], X[:, 1], c=labels, cmap="coolwarm", s=18)
axes[1].set_title("Decision boundary and predictions")
axes[1].set_xlabel("x1")
axes[1].set_ylabel("x2")

plt.tight_layout()
plt.show()
```

If the reader predicted "uniform noise gets the lowest scores," that is
usually correct in this toy setup.
But the second half of the prompt is more important:
the histogram rarely shows a magical empty interval separating normal
and abnormal points.
Real data often yields overlap, shoulder regions, and cases that are
ranked as suspicious only relative to the rest of the batch.

That overlap is not a sign that the method failed.
It is a reminder that many anomaly problems are ranking problems long
before they are clean classification problems.
The ambiguous middle is where calibration work begins.

That is why practitioners should inspect scores before hard labels.
A threshold can always be imposed.
Whether that threshold maps to a tolerable review load is a separate
question.

That separation between model fit and review policy is one of the main
habits to carry into production.
Score first.
Then decide what volume, precision, and downstream cost the system can
actually sustain.

In practice, `IsolationForest` is a strong baseline when the dataset is
tabular, reasonably large, and not obviously well-described by a single
elliptical Gaussian cloud.
It is also a good first comparison model when the team wants a detector
that does not depend heavily on scaling choices.

It becomes less persuasive when anomalies are defined by very local
density dips that a neighborhood method can see better, or when the
notion of "normal" is better represented as a smooth boundary in a
scaled feature space.
Even then, it remains useful as a detector-family contrast because
agreement and disagreement across families can reveal whether the signal
is robust or merely an artifact of one geometric assumption.

As a baseline, `IsolationForest` has another practical advantage:
people can usually understand its failure modes quickly.
When it struggles, the team often learns something concrete about
density, subgroup structure, or missing features that guides the next
experiment.

## Section 4: Local Outlier Factor (LOF)

`LocalOutlierFactor` is the detector in this module that most clearly
connects anomaly detection to the density and neighborhood intuitions
developed in
[Module 1.8: Unsupervised Learning: Clustering](../module-1.8-unsupervised-learning-clustering/).
Its API reference is here:
[https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.LocalOutlierFactor.html](https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.LocalOutlierFactor.html).

LOF asks whether a point has substantially lower local density than its
neighbors.
Instead of learning a global shape, it compares how isolated a point is
relative to the neighborhood structure around it.
That makes it especially useful when the data contains regions of
different overall density and a single global threshold would be too
crude.

Because LOF is a nearest-neighbor method, it inherits the scaling
discipline from
[Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/)
and
[Module 1.7: Naive Bayes, k-NN & SVMs](../module-1.7-naive-bayes-knn-and-svms/).
If one feature dominates distance calculations because of unit mismatch,
the anomaly ranking becomes a unit artifact rather than a structure
artifact.
This is not optional cleanup.
It is central to using the estimator correctly.

This is where many disappointing LOF experiments go wrong.
The detector gets blamed for instability when the true issue is that the
feature space never defined a sensible neighborhood relation in the
first place.

The defaults are worth knowing.
`n_neighbors=20` means each point is compared against a local reference
set of size twenty by default.
`contamination='auto'` is now the default, and scikit-learn documents
that this changed from `0.1` in version `0.22`.
`novelty=False` is the standard anomaly-detection setting.

The `novelty` parameter creates a real mode split rather than a cosmetic
toggle.
With the default `novelty=False`, LOF is used to identify outliers in
the training set itself.
In that mode, the common API is `fit_predict(X)`.
With `novelty=True`, the estimator is trained on data considered clean
enough to define normality, then used to score new unseen samples via
`predict`, `score_samples`, and `decision_function`.

This is one of the places where careless API reuse causes incorrect
results.
The scikit-learn documentation warns that `fit_predict` is unavailable
when `novelty=True`, and it also warns that using `predict` on the
training data in novelty mode gives wrong results.
That is not a minor edge case.
It is the direct consequence of how the method computes local density
relations.

The contrast is easiest to see in code.

```python
from sklearn.neighbors import LocalOutlierFactor

# Anomaly detection inside the training set
lof_anomaly = LocalOutlierFactor(n_neighbors=20, novelty=False)
y_train_flags = lof_anomaly.fit_predict(X_train_scaled)

# Novelty detection on future data
lof_novelty = LocalOutlierFactor(n_neighbors=20, novelty=True)
lof_novelty.fit(X_train_scaled)
y_new_flags = lof_novelty.predict(X_new_scaled)
new_scores = lof_novelty.score_samples(X_new_scaled)
```

The scaling reminder in the variable names is deliberate.
If the dataset is not already in a meaningful metric space, the method
should generally live inside a pipeline built as discussed in
[Module 1.1: Scikit-learn API & Pipelines](../module-1.1-scikit-learn-api-and-pipelines/)
rather than being fitted on raw heterogeneous columns.

That pipeline discipline matters even more when LOF is used in novelty
mode.
The future data must pass through the exact same transformation logic as
the reference data, or the learned neighborhood structure ceases to be
comparable.

LOF is attractive when anomalies are local rather than global.
A point may sit in a region that is sparse relative to nearby points
even if, from a global perspective, it does not seem extreme.
This is useful in datasets where multiple ordinary subpopulations have
different densities.

That makes LOF a strong contrast model against more global detectors.
If `IsolationForest` keeps flagging one whole sparse subpopulation and
LOF largely accepts it while isolating thin points inside it, the
disagreement is teaching something useful about the geometry.

Its weaknesses follow from the same logic.
Large datasets can make neighbor search expensive.
High-dimensional spaces can make distance less informative.
The choice of `n_neighbors` changes what "local" means, and that choice
is rarely neutral.
Too small a neighborhood can overreact to noise.
Too large a neighborhood can wash out the very local effect that made
LOF appealing.

In other words, `n_neighbors` quietly defines the scale at which
"ordinary context" is measured.
Changing it can change not only model sensitivity but also the semantic
story the detector is telling about what counts as local normality.

LOF is therefore less of a plug-and-play detector and more of a
geometric statement.
It says:
"I trust local density comparisons more than global isolation or a
single smooth boundary."
When that statement matches the data, LOF can be excellent.
When it does not, the resulting scores can look technical while merely
encoding a poor distance space.

That is not a reason to avoid LOF.
It is a reason to use it deliberately and interpret its output as a
claim about neighborhoods, not as a generic truth oracle.

## Section 5: One-Class SVM

`OneClassSVM` adapts the support vector machine idea to the problem of
describing the normal region of feature space.
Its API reference is here:
[https://scikit-learn.org/stable/modules/generated/sklearn.svm.OneClassSVM.html](https://scikit-learn.org/stable/modules/generated/sklearn.svm.OneClassSVM.html).

Where `IsolationForest` isolates points through random partitions and
LOF compares local densities, `OneClassSVM` tries to learn a boundary
that encloses the ordinary data and separates it from the origin in a
transformed feature space.
With the default `kernel='rbf'`, that boundary can be quite flexible.

The defaults are important because they strongly shape behavior.
Scikit-learn uses `kernel='rbf'`, `gamma='scale'`, and `nu=0.5` by
default.
The first two are often discussed.
The third is frequently misunderstood.

`nu` has a dual meaning that deserves to be called out explicitly.
The documentation states that it is both an upper bound on the fraction
of training errors and a lower bound on the fraction of support vectors.
Most practitioners remember only the first half.
The second half matters because it says something about model
complexity and how much of the training set is actively shaping the
boundary.

Thinking in both roles at once improves tuning judgment.
Changing `nu` is not merely a threshold tweak.
It can materially change how much of the observed geometry the model
treats as structurally defining the frontier.

That dual interpretation is a good example of why anomaly detection
needs more than cargo-cult parameter tuning.
If someone treats `nu` only as "roughly how many outliers I expect,"
they miss that it also constrains the support structure of the learned
boundary.
In effect, it participates in both tolerance and geometry.

This is one reason notebook experiments can be misleading.
A small change in `nu` may appear to simply raise or lower the number of
flagged cases, while in reality the frontier itself may have changed in
meaningful ways.

Because the method depends on kernel distances, scaling is usually
non-negotiable.
The warnings from
[Module 1.7: Naive Bayes, k-NN & SVMs](../module-1.7-naive-bayes-knn-and-svms/)
apply directly here:
unscaled features can make the kernel similarity meaningless, and the
computational cost can become painful as the sample size grows.
For many large tabular datasets, `OneClassSVM` is simply not the first
detector to try.

Where it does shine is on moderate-sized datasets where the normal
region is coherent but not well-approximated by a simple ellipse.
If the data is clean enough for novelty detection and the feature space
has been scaled sensibly, the method can provide a smooth frontier that
captures non-linear support.

In those cases, the appeal is not speed.
It is expressiveness.
The method can represent a normal region that is curved or otherwise
non-linear in the original feature space.

Its main failure modes are familiar.
Poor scaling distorts the kernel.
Poor `gamma` choices make the boundary too rigid or too wiggly.
Large sample sizes produce slow fitting and inference.
And if the training set is not actually clean, the learned support can
wrap around abnormal structure and normalize it.

That last issue is especially painful in novelty workflows.
If contaminated examples are normalized into the support region during
fit, the detector may later treat their close relatives as ordinary,
which is exactly the opposite of what the team intended.

The key practical lesson is not that `OneClassSVM` is fragile.
It is that the method makes stronger geometric commitments than a tree
ensemble baseline.
When those commitments fit the data, the model can be elegant.
When they do not, the model can be deceptively expensive while still
solving the wrong problem.

That is why it is often most useful as a comparison family rather than a
universal starting point.
Agreement between `OneClassSVM` and a very different detector can be
more informative than the raw score of either model alone.

That is why many teams use it less as a universal default and more as a
targeted detector for scaled, moderate-sized, relatively well-behaved
novelty problems.
It is also a good reminder that "SVM" in the name should immediately
trigger the same preprocessing and complexity instincts developed
earlier in the track.

## Section 6: Elliptic Envelope

`EllipticEnvelope` is the most assumption-heavy detector in this module,
but also sometimes the cheapest and most interpretable.
Its API reference is here:
[https://scikit-learn.org/stable/modules/generated/sklearn.covariance.EllipticEnvelope.html](https://scikit-learn.org/stable/modules/generated/sklearn.covariance.EllipticEnvelope.html).

The method fits a robust covariance estimate and then treats points far
from the resulting elliptical support as outliers.
This is essentially a Gaussian-shape story:
normal data is assumed to live in something like a multivariate
elliptical cloud, perhaps with a modest amount of contamination that the
robust estimator can tolerate.

Because that story is so explicit, the method has a useful diagnostic
quality.
If it performs surprisingly well, the data may be simpler than expected.
If it performs badly, the failure often teaches that ordinary structure
is multimodal or non-elliptical.

The default parameters reveal that intended use.
`support_fraction=None` lets the estimator choose the amount of data
used for the support estimate.
`contamination=0.1` sets a concrete default threshold assumption.
`assume_centered=False` means the estimator normally estimates the
location rather than assuming the data is already centered.

Scikit-learn also gives an explicit warning that `n_samples` should be
greater than `n_features ** 2` for stability.
That warning matters because covariance estimation gets unreliable
quickly when dimensionality grows relative to sample size.
This is not a method to reach for casually on wide sparse tables.

When is `EllipticEnvelope` the right choice?
When the feature space is continuous, modest in dimension, roughly
Gaussian after sensible preprocessing, and the team wants a fast,
classical baseline with straightforward geometric interpretation.
In that setting, it can be both cheaper and more transparent than
heavier alternatives.

Transparency matters.
In some operational contexts, a slightly less flexible but easier-to-audit
detector can be preferable to a more expressive model whose decisions are
harder to explain and harder to sanity-check.

For example, if a process is well-understood and normal operating states
occupy one dominant cloud, robust covariance may capture the useful
structure immediately.
The detector then behaves much like a robust Mahalanobis-distance gate.

This can make it appealing in well-instrumented industrial, scientific,
or quality-control contexts where the notion of normal variation really
is centered and continuous rather than highly multimodal.

When is it misleading?
Whenever the true data geometry is multimodal, strongly non-elliptical,
or dominated by categorical encodings and complex interactions.
A bimodal but perfectly ordinary dataset can fool the method into
treating one valid region or the low-density bridge between them as
suspicious because the single-ellipse assumption is too crude.

This is one of the clearest examples in the module of a detector being
"wrong for honest reasons."
The code may run perfectly.
The assumptions may simply not match the data manifold.

That is why `EllipticEnvelope` is best treated as a deliberately chosen
classical baseline, not a universal fallback.
If it works well, that is informative because it tells the team the data
may have a fairly simple normal geometry.
If it fails badly, that failure is diagnostic too:
the normal region probably needs a richer description.

Used this way, the estimator earns its place even when it does not win.
It becomes a probe of whether simple covariance structure is enough to
explain the ordinary data cloud.

## Section 7: The contamination Parameter

The `contamination` parameter deserves its own section because it is one
of the most misused controls in anomaly detection.
It looks small.
It is not.

At a high level, `contamination` tells an estimator how many outliers to
expect when converting continuous scores into binary labels.
If the parameter is set to `0.1`, the user is effectively asserting that
about ten percent of the relevant sample should be treated as outliers
for thresholding purposes.
Many people do not realize they are making that claim.

That matters because the same score ranking can yield very different
operational consequences depending on threshold placement.
A review team that can inspect a few dozen cases per batch needs a very
different cutoff from a quarantine system that auto-blocks events.

Different estimators handle `contamination='auto'` differently because
`auto` is estimator-specific, not a universal statistical truth.
It means "use the library's built-in threshold logic for this
estimator," not "infer the real-world outlier fraction from pure first
principles."
That is good enough for exploration, but usually not enough for
production commitments.

This also means detector comparisons should not stop at the binary
labels.
Two models may disagree mainly because their threshold defaults differ,
not because their underlying rank order of suspicious cases is radically
different.

It is also crucial to separate ranking from thresholding.
`score_samples()` gives the continuous suspiciousness view.
`predict()` gives the thresholded view, returning `+1` or `-1`.
A team that only looks at `predict()` often ends up arguing about the
algorithm when the real problem is an arbitrary cutoff.

> **Pause and predict** - Suppose a deployment hard-codes
> `contamination=0.1`, but in reality only about `0.1%` of events are
> truly worthy of escalation. Before reading on, predict what happens to
> operator workload, trust in the alerts, and the temptation to disable
> the detector entirely.

The likely outcome is alert fatigue.
The system will flag far too many observations relative to the review
capacity and true event rate.
Analysts will learn that being flagged no longer means much.
Soon the metric that matters operationally is not "anomalies found" but
"irrelevant cases generated."

This is why contamination should be discussed in business language as
well as model language.
How many cases can be reviewed?
What is the cost of escalation?
What false-positive burden can the process absorb before users route
around it?

A healthier production pattern is to treat detector training and
threshold calibration as related but separate decisions.
Fit the detector to produce scores.
Then calibrate the operating threshold using partial labels, review
capacity, downstream cost, or a target alert rate that can be defended.
This is directly aligned with the monitoring discipline in
[Module 1.10: ML Monitoring](../../mlops/module-1.10-ml-monitoring/),
where noisy alerting degrades systems even when the underlying score has
some signal.

Another subtle point is that the right contamination setting can change
by context.
A retrospective data-cleaning pass over a historical table may tolerate
a much larger review bucket than an online blocking system.
The ranking signal can remain identical while the acceptable threshold
moves.

The score is the model output.
The threshold is a policy layer on top of it.
Treating those as separate layers creates much cleaner conversations
between model owners and operational stakeholders.

Threshold policy is therefore part of the application contract, not an
eternal property of the estimator.
Store the score, document the threshold, and treat both as reviewable
artifacts.

This is why practitioners should be suspicious of copying contamination
values from tutorials.
A value that made sense for a synthetic demo says almost nothing about
your true anomaly prevalence, your business cost curve, or your team's
capacity to investigate.

In production, a common pattern is to keep the detector's score as a
logged signal, choose an initial threshold using the best available
partial labels, and then revisit that threshold after observing
escalation volume, analyst feedback, and drift in the score
distribution.
That workflow is slower than typing `contamination=0.01`, but it is also
how reliable systems are built.

## Section 8: Evaluating Without Labels

Evaluation without labels does not mean evaluation without discipline.
It means the evidence is weaker, more indirect, and easier to misuse.
That is exactly why the habits from
[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/)
matter even more here.

The first layer is internal evaluation.
Does the ranking remain stable across reasonable perturbations of the
sample, random seed, or feature subset?
If the top suspicious cases reshuffle wildly under small changes, the
detector may be reflecting instability rather than robust structure.

Instability is especially painful when humans are in the loop.
If today's queue looks unrelated to yesterday's after a minor refresh,
analysts quickly lose trust that the system is surfacing anything real.

Score-distribution shape is another internal signal.
A detector whose scores collapse into a narrow band may not be finding
meaningful separation.
A detector with a heavy suspicious tail may be more actionable, though
tail shape alone is never proof.
The point is to inspect whether the model is producing a ranking that
looks structurally informative rather than uniformly uncertain.

It is also helpful to inspect how stable the top-ranked set is under
small data perturbations.
If the exact ordering of the top few cases shifts, that may be fine.
If the membership of the top suspicious slice changes completely, the
system may be too brittle for operational use.

Agreement across detector families is also useful.
If `IsolationForest`, LOF, and `OneClassSVM` all rank a small subset of
cases as highly suspicious despite different geometric assumptions, that
consensus is often more persuasive than any one model in isolation.
If one method alone flags a group, the next question should be whether
that group is a real anomaly cluster or an artifact of the method's
assumptions.

None of these internal signals proves correctness.
They are sanity checks.
They help distinguish "the model is producing a coherent suspiciousness
structure" from "the model is outputting technically valid noise."

The second layer is external partial supervision.
Often a team has some confirmed labels, even if only for a reviewed
subset.
That is enough to evaluate ranking quality with metrics such as
precision at `k`, average precision, or lift over baseline.
These metrics respect the fact that the detector may be used to
prioritize limited review capacity rather than classify every point.

The best metric is usually the one that matches the workflow.
If only the top slice can ever be reviewed, then performance near the
top of the ranking matters far more than global threshold behavior.

Precision at `k` asks a practical question:
among the top `k` flagged cases, how many were truly relevant?
Average precision summarizes ranking quality over thresholds.
Lift asks whether the detector surfaces relevant cases at a rate better
than random selection.
All three are often more operationally meaningful than accuracy in this
setting.

These metrics also force a useful honesty.
They ask what benefit the detector produces at the top of the queue,
which is often the only part of the ranking anyone will ever inspect in
practice.

A common mistake is to evaluate only on the reviewed cases without
acknowledging selection bias.
If human review only ever sees the detector's own top-ranked cases, the
labeled subset is not representative of the whole population.
That does not make evaluation impossible, but it does mean conclusions
must be framed carefully.

Another practical strategy is challenge-set evaluation.
Construct a small set of known odd cases, known ordinary cases, and
ambiguous edge cases.
Then compare how detectors rank them.
This is not the same as a full benchmark, but it surfaces whether the
model's notion of suspiciousness aligns with expert judgment on cases
the team actually cares about.

Challenge sets are also useful for regression testing.
When features or thresholds change, the team can inspect whether the
cases it most cares about moved in the ranking for understandable
reasons.

The central lesson is that anomaly detection does not exempt the team
from evaluation rigor.
It merely forces that rigor to use weaker signals, more caveats, and
clearer statements of uncertainty.

## Section 9: Choosing a Detector

No single detector dominates across all anomaly problems.
Choosing one is mainly about matching assumptions to data geometry,
sample size, preprocessing readiness, and deployment mode.

| Detector | Use when | Avoid when |
| --- | --- | --- |
| IsolationForest | Large or medium tabular data, mixed ordinary structure, need a strong baseline that does not depend heavily on scaling | The anomaly notion is strongly local-density based, or a dense unusual cluster must be separated mainly by neighborhood structure |
| LOF anomaly | Need to flag unusual points within the current dataset, and local density contrasts are more informative than global shape | Features are unscaled, dimensionality is high enough to weaken distance, or the workflow needs clean training plus future scoring |
| LOF novelty | Training data is treated as clean, future samples must be scored against local-density structure, and scaling discipline is in place | The team wants to score the training data itself, or mistakes novelty mode for a generic replacement of the default anomaly API |
| OneClassSVM | Moderate-sized scaled data, novelty framing, and a smooth non-linear support boundary is plausible | Very large datasets, poor scaling, or limited patience for kernel sensitivity and compute cost |
| EllipticEnvelope | Continuous low-to-moderate dimensional data with roughly elliptical Gaussian normal structure, where a cheap classical baseline is useful | Multimodal, strongly non-elliptical, wide, sparse, or mixed-type data where a single robust covariance ellipse is misleading |

This table is not a substitute for experiments.
It is a compact way to prevent category errors.
The fastest route to a bad detector is often not a bad hyperparameter.
It is choosing a family whose assumptions were never plausible.

That is why small comparison studies are so valuable.
Even a short side-by-side score review can reveal whether the problem is
best understood through isolation, local density, smooth support, or a
classical elliptical baseline.

A useful workflow is to start with `IsolationForest` as a baseline,
compare it with one geometry-contrasting method such as LOF or
`OneClassSVM`, and then inspect both score overlap and disagreement.
If a simple classical assumption might hold, add `EllipticEnvelope` as a
cheap probe rather than a default commitment.

## Section 10: Cross-Cutting Connections

Anomaly detection should not live in a conceptual silo.
Several earlier and later modules connect directly to the design choices
in this one.

The first connection is clustering.
In
[Module 1.8: Unsupervised Learning: Clustering](../module-1.8-unsupervised-learning-clustering/),
DBSCAN labeled some points as noise.
Those noise points are not automatically business anomalies, but they
often provide a free first-pass suspiciousness signal.
If DBSCAN marks observations as outside dense regions and a separate
anomaly detector ranks the same cases highly, that convergence is useful
evidence.

The second connection is deep learning.
This module stays within classical scikit-learn estimators, but a common
extension is reconstruction-error anomaly detection with autoencoders.
That belongs more naturally in the
[Deep Learning track](../../deep-learning/),
where representation learning and reconstruction objectives can be
treated in the depth they require.
The important conceptual bridge is that reconstruction error is still a
score needing threshold calibration and evaluation discipline, not a
shortcut around those issues.

That continuity matters.
Changing the model family does not remove the need to decide what
constitutes a useful alert, how partial labels will be used, or how
drift in the score distribution will be monitored.

The third connection is MLOps.
An anomaly detector in production behaves a lot like any other alerting
system.
Thresholds drift.
Input distributions move.
Analyst capacity changes.
The same lessons about healthy alert design and monitoring from
[Module 1.10: ML Monitoring](../../mlops/module-1.10-ml-monitoring/)
apply directly.
Poorly calibrated anomaly detectors do not merely make wrong
predictions.
They consume human attention and erode trust.

For that reason, detector observability should include more than counts
of predicted outliers.
Score histograms, threshold crossings, review outcomes, and detector
agreement over time often reveal degradation earlier than a single
binary alert rate.

A final connection is representation learning more broadly.
The better the features reflect stable structure, the more meaningful
distance, density, or isolation often becomes.
That means anomaly detection quality is frequently limited less by the
detector family than by whether the feature space encodes the right
behavioral distinctions at all.

When every detector family seems confused, the root cause is often not
that all anomaly methods are weak.
It is that the representation has not yet made normal and suspicious
behavior geometrically legible.

## Section 11: When Anomaly Detection Is the Wrong Tool

Anomaly detection is useful, but it is often overused because it sounds
like a sophisticated answer to scarce labels.
In several common situations, it is simply the wrong tool.

If reliable labels exist in sufficient quantity, use supervised
classification first.
A discriminative model from
[Module 1.7: Naive Bayes, k-NN & SVMs](../module-1.7-naive-bayes-knn-and-svms/)
or
[Module 1.6: XGBoost & Gradient Boosting](../module-1.6-xgboost-gradient-boosting/)
can learn the actual decision boundary the business cares about rather
than an indirect proxy for unusualness.

If the supposedly strange cases are really a known sub-population, the
problem may be clustering or segmentation rather than anomaly detection.
That is exactly the kind of distinction explored in
[Module 1.8: Unsupervised Learning: Clustering](../module-1.8-unsupervised-learning-clustering/).
A new dense customer segment is not a point anomaly merely because the
current model never saw it.

If the structure is fundamentally temporal, this module is not enough.
Time-ordered dependence, seasonality, lag behavior, and regime shifts
need dedicated sequence thinking.
That is the domain of
[Module 1.12: Time-Series Forecasting](../module-1.12-time-series-forecasting/),
where deviations are judged relative to temporal expectation rather than
only static feature-space geometry.

A flat tabular detector can still be useful as a supporting signal on
derived summary features, but it should not be mistaken for a substitute
for true temporal modeling when sequence structure is the main source of
meaning.

If the concern is system-wide drift rather than point-level abnormality,
monitoring is the better frame.
A model can be receiving slightly shifted but individually ordinary
events.
That is a distribution-change problem, not necessarily an anomaly-score
problem.
The right response often lives in
[Module 1.10: ML Monitoring](../../mlops/module-1.10-ml-monitoring/).

The distinction matters because the remediation differs.
Point anomalies are often investigated case by case.
Drift is often handled through monitoring, retraining, guardrails, or
upstream system checks.

The more mature a team becomes, the more often it asks this question
before fitting anything:
"Are we trying to detect rare points, identify a new subgroup, model
temporal deviation, or catch distribution drift?"
Those are different jobs.
Anomaly detection handles only some of them.

Asking that question early is usually a sign of technical maturity.
It prevents a detector from being used as a vague substitute for several
distinct modeling and monitoring responsibilities.

## Patterns & Anti-Patterns

The most reliable anomaly-detection pattern is to keep score production separate from operational action. Fit the detector to produce a continuous ranking, store `score_samples()` or an equivalent score with enough feature context to audit later, and then make the escalation threshold a documented policy decision. This pattern works because it preserves information that hard labels discard, allows threshold calibration to evolve as review capacity changes, and makes it possible to compare detector families without confusing ranking quality with alert volume.

A second strong pattern is mode-first design. Before choosing an estimator, write one sentence that says whether abnormal examples are expected inside the fitted sample or only in future data, then let that sentence determine anomaly versus novelty behavior. This is especially important for LOF because the API changes materially between `novelty=False` and `novelty=True`, but the same reasoning applies to every detector in this module. The pattern scales well because it turns an ambiguous modeling discussion into a testable data contract: which dataset defines normality, which dataset is being scored, and which mistakes count as model failures rather than policy disagreements.

A third pattern is detector-family triangulation. Start with a practical baseline such as `IsolationForest`, add one contrasting family such as LOF or `OneClassSVM`, and inspect cases where the models agree or disagree before tuning deeply. Agreement across isolation, density, and kernel views is not proof, but it is useful evidence that the suspiciousness signal is not merely an artifact of one geometry. Disagreement is also valuable because it points the team toward the assumption under pressure: scaling, locality, covariance shape, dense novel clusters, or threshold policy.

The strongest anti-pattern is treating `predict()` as the final truth because it returns neat `+1` and `-1` values. Teams fall into this because binary flags are easy to count, easy to route, and easy to show on dashboards, but those flags hide the threshold decision that often dominates production behavior. The better alternative is to inspect continuous scores first, choose a threshold using partial labels or review budget, and write down the expected false-positive cost before automating any high-impact action.

Another common anti-pattern is using anomaly detection as a dignified name for missing product requirements. If stakeholders cannot say whether they need rare-point detection, new-segment discovery, temporal-deviation detection, or drift monitoring, the model will inherit that confusion and return confident-looking output for a poorly defined job. The fix is not more hyperparameter search. The fix is a short decision review that names the operational action, the evidence available for calibration, and the point at which supervised classification, clustering, forecasting, or monitoring would become the better tool.

The final anti-pattern is allowing preprocessing to drift away from detector semantics. Distance-based and kernel-based detectors need a meaningful metric space, novelty detection needs identical transformations for reference and future samples, and covariance methods need dimensionality discipline before their geometry can be trusted. Teams often skip this because the estimator accepts a NumPy array without complaint, but the absence of an exception is not evidence that the feature space is meaningful. A pipeline that owns scaling, encoding, and score export is boring in the best possible way: it makes the detector's assumptions inspectable.

## Decision Framework

Use this framework as a pre-flight review before committing to a detector. First, decide whether the fitted data contains the suspicious cases you want to rank. If yes, you are doing anomaly detection inside a contaminated sample, so LOF anomaly mode or `IsolationForest` may be sensible first candidates. If no, and you have a clean reference window for future scoring, you are doing novelty detection, so LOF novelty mode, `OneClassSVM`, or another support-learning approach becomes easier to defend. If the team cannot answer this first question, pause the modeling work because the API semantics are not yet defined.

Second, match the detector to the geometry you are willing to believe. Choose `IsolationForest` when the data is tabular, the sample is medium or large, and quick isolation through random partitions is a plausible suspiciousness signal. Choose LOF when local density contrast matters more than global shape and the feature space has been scaled carefully. Choose `OneClassSVM` when the reference data is clean enough for novelty detection, the sample is moderate, and a smooth non-linear support boundary is plausible. Choose `EllipticEnvelope` only when a robust single-ellipse story is honest enough to be useful, because its transparency is valuable only when its assumptions resemble the data.

Third, decide how the score will become an action. For discovery work, a wide review bucket may be acceptable because the goal is learning. For analyst triage, precision near the top of the ranking and review capacity usually matter more than global accuracy. For automated blocking or quarantine, the threshold must be conservative, auditable, and monitored because false positives now cause direct user or system harm. This step is where `contamination` stops being a tutorial parameter and becomes an operational promise.

Finally, define the retirement criteria before the detector ships. A detector should be replaced by supervised classification when reliable labels become plentiful, by clustering when the supposed anomalies are actually new ordinary groups, by time-series methods when sequence context defines abnormality, and by monitoring when the concern is distribution movement rather than point-level suspicion. This exit plan protects the system from becoming an all-purpose alert generator that nobody trusts but everybody is afraid to remove.

## Did You Know?

- Scikit-learn documents that `LocalOutlierFactor` changed its default
  `contamination` from `0.1` to `'auto'` in version `0.22`:
  [https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.LocalOutlierFactor.html](https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.LocalOutlierFactor.html)
- `IsolationForest` resolves `max_samples='auto'` to
  `min(256, n_samples)`:
  [https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html)
- `OneClassSVM` states that `nu` is both an upper bound on the fraction
  of training errors and a lower bound on the fraction of support
  vectors:
  [https://scikit-learn.org/stable/modules/generated/sklearn.svm.OneClassSVM.html](https://scikit-learn.org/stable/modules/generated/sklearn.svm.OneClassSVM.html)
- `EllipticEnvelope` explicitly warns that `n_samples` should exceed
  `n_features ** 2`:
  [https://scikit-learn.org/stable/modules/generated/sklearn.covariance.EllipticEnvelope.html](https://scikit-learn.org/stable/modules/generated/sklearn.covariance.EllipticEnvelope.html)

## Common Mistakes

| Mistake | Why it bites | Fix |
| --- | --- | --- |
| Treating anomaly detection as "classification without the positive class" | The model learns unusualness relative to assumptions, not the true decision boundary the business may care about | Ask first whether labels already support supervised classification |
| Using novelty mode when the task is to flag outliers inside the training sample | The workflow and API semantics no longer match the job | Write the mode in plain English before coding and pick the estimator behavior accordingly |
| Reading `predict()` without inspecting `score_samples()` | Threshold choices can dominate the visible outcome | Plot score distributions and separate ranking quality from threshold policy |
| Leaving distance-based detectors unscaled | LOF and `OneClassSVM` then encode unit mismatch instead of structure | Use the preprocessing discipline from [Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/) |
| Copying a tutorial contamination value into production | The detector may flood operators with false escalations | Calibrate thresholds on partial labels, review capacity, and operating cost |
| Calling LOF `predict` on training data after fitting with `novelty=True` | The documentation warns the result is wrong for that use | Use novelty mode only for unseen data and keep anomaly mode for training-set outlier detection |
| Applying `EllipticEnvelope` to multimodal data | One ellipse cannot represent several ordinary regions well | Use richer detectors or treat the problem as segmentation first |
| Assuming detector disagreement means one model is broken | Different families encode different geometry assumptions | Use disagreement as a diagnostic clue, then inspect cases and features |

## Quiz

1. A team fits `LocalOutlierFactor(novelty=True)` on a carefully cleaned
   baseline dataset, then evaluates model quality by calling `predict`
   on that same training dataset and comparing the flagged points to
   analyst intuition. What is wrong with this procedure?

<details><summary>Answer</summary>
In novelty mode, LOF is meant to score new unseen data against a clean
reference set. The documentation warns that using `predict` on the
training data in this mode gives wrong results. If the goal is to find
outliers within the fitted sample, anomaly mode with `novelty=False` is
the right framing.
</details>

2. A deployment sets `contamination=0.1` because "that is the library
   default in some examples," but the true rate of actionable cases is
   far below one percent and the human review queue is small. What
   failure should the team expect first?

<details><summary>Answer</summary>
The most immediate failure is review overload and alert fatigue. The
model may still rank cases with some signal, but the threshold implied
by ten percent contamination will generate far too many positives for
the true event rate and review capacity. The fix is to separate scoring
from threshold calibration and tune the cutoff on partial labels and
operational constraints.
</details>

3. A practitioner wants to detect anomalous rows inside a static table
   and also wants to score future incoming rows with the same LOF model.
   They ask for one configuration that does both perfectly. What should
   you tell them?

<details><summary>Answer</summary>
LOF has a real split between anomaly detection and novelty detection.
The default anomaly mode is for identifying outliers in the training
data itself. Novelty mode is for fitting on reference data and scoring
new samples. Trying to use one fitted object as if those semantics were
interchangeable is a category error. The team should define which job
matters most or maintain distinct workflows.
</details>

4. A dataset contains a dense cluster of truly unusual observations that
   are far from the training distribution but close to one another. Why
   might `IsolationForest` fail to flag them as strongly as expected?

<details><summary>Answer</summary>
`IsolationForest` works by isolating points through random splits.
Points that are easy to separate in few steps look more anomalous. A
dense unusual cluster can be internally cohesive, so its members may not
be isolated as quickly as scattered outliers. The cases may still be
novel, but the detector family is emphasizing isolation rather than the
specific semantic notion of abnormality.
</details>

5. A team fits `OneClassSVM` directly on raw features where one column
   ranges from fractions and another ranges in the hundreds of
   thousands. The detector behaves erratically. Why is that outcome not
   surprising?

<details><summary>Answer</summary>
`OneClassSVM` is a kernel method, so feature scaling strongly affects
the geometry it sees. On raw features with wildly different units, the
kernel similarity is dominated by large-scale columns and the learned
boundary becomes more about unit magnitude than actual structure. A
pipeline with scaling is usually necessary.
</details>

6. Someone proposes `EllipticEnvelope` for a dataset that consists of
   two ordinary but well-separated modes. They argue that robust
   covariance will take care of the shape. Why should you push back?

<details><summary>Answer</summary>
`EllipticEnvelope` assumes the normal region is well-described by a
single elliptical Gaussian-style cloud. Two well-separated ordinary
modes violate that assumption. The method may mischaracterize one mode
or the region between them because a single ellipse is too crude. This
is a segmentation or richer-geometry problem, not a robust-covariance
shortcut.
</details>

7. You have a table with about one million rows and mostly numeric
   features. You need a first-pass detector that scales reasonably and
   provides a baseline score quickly. Should you start with
   `IsolationForest` or LOF, and why?

<details><summary>Answer</summary>
`IsolationForest` is the better first baseline for that scale in many
cases. It is tree-based, does not depend as directly on distance
calculations, and is usually friendlier on large tabular datasets than a
nearest-neighbor method like LOF. LOF may still be valuable later if
local-density anomalies are central, but it is not the obvious first
pass for a million-row table.
</details>

8. A team already has several thousand verified labels for fraudulent
   and non-fraudulent events, but they still want anomaly detection
   because "rare things are anomalies." What is the more defensible
   modeling path?

<details><summary>Answer</summary>
If the labels are reliable and plentiful enough, supervised
classification is the more direct tool because it learns the actual
target distinction rather than a proxy notion of unusualness. Anomaly
detection can still help as a side signal or discovery tool, but it
should not displace a well-posed labeled classifier without a clear
reason.
</details>

## Hands-On Exercise

- [ ] Create a new notebook or script and import `numpy`,
  `matplotlib.pyplot`, `make_blobs`, `IsolationForest`,
  `LocalOutlierFactor`, `OneClassSVM`, `EllipticEnvelope`,
  `StandardScaler`, `Pipeline`, and one agreement metric such as
  `adjusted_rand_score`.
- [ ] Build a synthetic dataset with a dominant normal structure and a
  smaller injected anomaly component.
  Keep the anomaly-generating logic explicit so it is clear which points
  are only unusual in geometry and which are treated as ground truth for
  partial evaluation.
- [ ] Step 1: Fit `IsolationForest` on the synthetic mixture.
  Plot a histogram of `score_samples()` and a scatter plot colored by
  `predict()`.
  Write two sentences explaining where the suspicious tail begins and
  whether the threshold implied by your chosen contamination looks
  operationally plausible.
- [ ] Step 2: Fit LOF in anomaly mode with `novelty=False` on a scaled
  version of the same data and inspect `fit_predict()` output.
  Then refit LOF with `novelty=True` on a training subset treated as
  clean and score a separate held-out subset.
  Write a short note explaining exactly how the API changed and why
  calling `predict` on the novelty-mode training data would be wrong.
- [ ] Step 3: Fit `OneClassSVM` inside a `Pipeline` with
  `StandardScaler`.
  Then fit a deliberately unscaled version on the same raw data.
  Compare the score distributions or decision regions and explain which
  differences are genuine structure and which are likely scale artifacts.
- [ ] Step 4: Compare partition agreement across detectors.
  Convert each detector's predictions into a binary inlier/outlier
  vector and compute `adjusted_rand_score` or a Jaccard-style agreement
  summary between detector pairs.
  Identify one set of cases where two detectors disagree and inspect
  those rows directly.
- [ ] Step 5: Hold out a small partial-label set and calibrate a
  threshold on `score_samples()` rather than accepting the default
  binary output.
  Measure precision at a review budget of your choice and explain why
  that budget is more realistic than blindly inheriting a contamination
  value.
- [ ] Step 6: Write a short shipping memo.
  State which detector you would deploy first, under what conditions you
  would retire or replace it, and which failure mode you would treat as
  a bug rather than a business-policy disagreement.
- [ ] Completion check: confirm that every distance-based model saw
  scaled inputs, every reported binary flag can be traced back to a
  threshold policy, and every comparison between detectors mentions the
  geometry assumption each family is making.
- [ ] Completion check: confirm that your final recommendation names the
  training mode explicitly as anomaly detection or novelty detection and
  does not treat the two as interchangeable.
- [ ] Completion check: confirm that you inspected continuous scores,
  not only hard labels, and that you used partial labels only in places
  where their selection bias was acknowledged.

## Sources

- https://scikit-learn.org/stable/modules/outlier_detection.html
- https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html
- https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.LocalOutlierFactor.html
- https://scikit-learn.org/stable/modules/generated/sklearn.svm.OneClassSVM.html
- https://scikit-learn.org/stable/modules/generated/sklearn.covariance.EllipticEnvelope.html
- https://scikit-learn.org/stable/auto_examples/miscellaneous/plot_anomaly_comparison.html
- https://scikit-learn.org/stable/auto_examples/applications/plot_outlier_detection_wine.html
- https://scikit-learn.org/stable/auto_examples/neighbors/plot_lof_outlier_detection.html
- https://scikit-learn.org/stable/auto_examples/neighbors/plot_lof_novelty_detection.html
- https://scikit-learn.org/stable/auto_examples/svm/plot_oneclass.html

## Next Module

Continue to [Module 1.10: Dimensionality Reduction](../module-1.10-dimensionality-reduction/).
