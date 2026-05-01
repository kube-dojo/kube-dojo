---
title: "Class Imbalance & Cost-Sensitive Learning"
description: "Diagnose when class imbalance is actually the problem, choose between class weights, resampling, threshold tuning, and metric changes, and keep all of it leakage-safe inside imblearn.pipeline.Pipeline so the cross-validation score stays honest."
slug: ai-ml-engineering/machine-learning/module-2.1-class-imbalance-and-cost-sensitive-learning
sidebar:
  order: 21
---

> Track: AI/ML Engineering | Complexity: Intermediate | Time: 90-110 minutes
> Prerequisites: [Module 1.1: Scikit-learn API & Pipelines](../module-1.1-scikit-learn-api-and-pipelines/), [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/), [Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/), [Module 1.7: Naive Bayes, k-NN & SVMs](../module-1.7-naive-bayes-knn-and-svms/), and [Module 1.9: Anomaly Detection & Novelty Detection](../module-1.9-anomaly-detection-and-novelty-detection/).

Class imbalance is one of those topics where the first instinct is almost always wrong. A practitioner sees a 1:50 positive class, reaches for SMOTE, applies it before the train/test split because that is the order the snippet on Stack Overflow uses, and then reports a cross-validated F1 that looks like a small miracle. Production never reproduces it. The model is fine. The data is fine. The evaluation lied, because synthetic minority samples crossed the fold boundary and the held-out metric was scoring on rows that shared neighbors with rows the resampler had used to manufacture training data.

This module is the corrective. It teaches imbalance not as "which oversampler do I pick" but as a sequence of decisions that begins with whether you actually have a problem worth solving and ends with whether the probabilities your model emits still mean what your downstream system thinks they mean. The order of moves is deliberate, the leakage discipline is non-negotiable, and the metric you celebrate has to be the metric your deployment actually pays for.

This is the first Tier-2 module in the Machine Learning track. It assumes you have already internalized the leakage taxonomy from [Module 1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/) and the leakage-safe `Pipeline` discipline from [Module 1.4](../module-1.4-feature-engineering-and-preprocessing/). The new vocabulary here — `imblearn.pipeline.Pipeline`, `class_weight="balanced"`, PR-AUC, MCC, threshold tuning — slots cleanly into both.

## Learning Outcomes

By the end of this module, a practitioner will be able to:

1. **Diagnose** whether a given imbalanced dataset actually requires a cost-sensitive intervention by reasoning about prevalence, business cost asymmetry, the chosen evaluation metric, and whether ROC-AUC alone is hiding a problem PR-AUC would surface.
2. **Design** a leakage-safe resampling workflow using `imblearn.pipeline.Pipeline` so that any `RandomOverSampler`, `SMOTE`, `ADASYN`, or `RandomUnderSampler` step fits only on the training portion of each cross-validation fold.
3. **Choose** between `class_weight="balanced"`, oversampling, undersampling, combined methods, and threshold tuning by mapping each tool to the regime where it actually earns its complexity.
4. **Implement** a threshold-on-validation workflow that optimizes F-beta or expected business cost without ever consulting the test set, and explain why this lever is often more decisive than any resampler.
5. **Defend** the right metric for the problem — PR-AUC, MCC, F-beta, or calibrated log-loss — and explain why optimizing the wrong one can produce a model that scores well on slides and fails on the work analysts actually have to do.

These outcomes extend Module 1.3's evaluation contract and Module 1.4's preprocessing contract. Module 1.3 taught the leakage taxonomy and the calibration workflow. Module 1.4 taught the leakage-safe `Pipeline` discipline. This module teaches what changes when the dataset is also imbalanced, and the answer is rarely "throw a resampler at it."

## Why This Module Matters

The imbalanced-learn user guide is direct about the failure mode this module exists to prevent. Its common-pitfalls page warns that resampling must happen inside the cross-validation loop, never before it, and that the standard `sklearn.pipeline.Pipeline` will not enforce the resampler-fits-only-on-training-folds contract because sklearn's pipeline applies every step's `fit_transform` to the data it receives, including held-out folds during CV. The library ships its own `imblearn.pipeline.Pipeline` precisely because this is the most common way teams report numbers they cannot reproduce in production.

A typical version of the failure looks like this on a Tuesday afternoon. A team is shipping a churn classifier on a roughly 1:30 positive class. The notebook calls `SMOTE().fit_resample(X, y)` once on the full dataset, splits afterwards, and runs five-fold cross-validation that reports an F1 around 0.78. Six weeks after deployment, the on-call engineer sees production F1 around 0.41 on a stable rolling window, opens the training notebook, and finds the synthetic minority samples generated from rows that later appeared in the validation folds. The shape of the failure is exactly the oversampling-leakage entry from Module 1.3's taxonomy, and the fix is exactly the one this module teaches: every resampler lives inside `imblearn.pipeline.Pipeline`, every cross-validation pass triggers a fresh resample on each training fold, and the held-out fold sees only honest prevalence.

The other failure that motivates this module is quieter and more common. A team sees an imbalanced classification problem, jumps straight to a resampler because that is the named technique, and never tries `class_weight="balanced"` first. For most sklearn classifiers this single argument shifts the loss-weighted gradient as if the minority class were proportionally upweighted, costs nothing extra at training time, and is often as good as or better than oversampling. SMOTE earns its complexity in specific regimes. It does not earn its complexity by default.

The third failure is the metric. ROC-AUC is invariant to class prevalence. That sounds like a feature until you understand the consequence: at a 1:1000 positive class, a model that catches none of the rare positives can still post a respectable AUC because the dominant area under the curve is decided by majority-class behavior. PR-AUC and MCC make the same model look as bad as it actually is. The scikit-learn metrics documentation is explicit that average precision corresponds to the area under the precision-recall curve and that Matthews correlation coefficient is robust under class imbalance, and this module is going to use both metrics to refute results that ROC-AUC was happy with.

This module gives you a sequenced playbook. The order is: diagnose, then `class_weight`, then threshold-tune, then resample if needed, then calibrate if probabilities matter. The order is not a personal preference. It is the order in which each move costs the least and risks the least, applied first.

## Section 1: When Imbalance Is a Problem (and When It Isn't)

The first decision is whether you have a problem at all. Imbalance is a property of the data. Whether it is a *problem* depends on three things: the metric you are optimizing, the cost asymmetry of the underlying business decision, and the absolute count of minority examples relative to the model's capacity.

A 1:10 positive rate is barely imbalanced. A 1:100 positive rate is imbalanced enough to warrant care. A 1:1000 positive rate is hard, and a 1:10,000 or 1:1,000,000 positive rate often means you should reframe the problem as anomaly detection rather than classification (cross-link to [Module 1.9](../module-1.9-anomaly-detection-and-novelty-detection/)). The boundaries are not sharp, but the framing differences are real.

The metric matters more than the prevalence ratio. If you genuinely care about ranking quality across the full population — for example, scoring all customers and choosing the top-k for an outreach campaign — ROC-AUC remains a reasonable target and class imbalance is largely a non-issue. If you care about the precision-recall trade-off at a chosen threshold — for example, flagging fraudulent transactions for analyst review under a fixed daily review capacity — PR-AUC and threshold-conditioned metrics become the right target, and class imbalance starts to bite hard.

Cost asymmetry is the third axis. If a missed positive costs a hundred times more than a false alarm, the decision threshold should be aggressive in favor of recall, and `class_weight` or threshold tuning is doing the right work. If a false alarm has roughly the same cost as a missed positive, the threshold should sit near the prevalence, and imbalance handling reduces to picking a metric that respects prevalence.

```python
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    matthews_corrcoef,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score

X, y = make_classification(
    n_samples=10000,
    n_features=20,
    n_informative=8,
    weights=[0.99, 0.01],   # 1:99 imbalance
    random_state=0,
)

print("prevalence:", y.mean())
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)

baseline = LogisticRegression(max_iter=2000)
auc = cross_val_score(baseline, X, y, cv=cv, scoring="roc_auc").mean()
ap = cross_val_score(baseline, X, y, cv=cv, scoring="average_precision").mean()
print("ROC-AUC :", round(auc, 3))
print("PR-AUC  :", round(ap, 3))
```

On this kind of synthetic data, the gap between ROC-AUC and PR-AUC is sharp. ROC-AUC often lands above 0.90 while PR-AUC stays below 0.50, because most of the ROC curve area is dominated by the easy majority side and the precision-recall view is the one that exposes the minority-class struggle. That gap is not a bug in either metric; it is the warning sign that the question you are asking is in the precision-recall regime, not the ranking regime.

> **Pause and predict** — A team reports a fraud classifier at ROC-AUC 0.94 on a 1:200 positive class but the analysts complain the queue is full of noise. PR-AUC turns out to be 0.18. Which metric is telling the truth about whether this model is fit for the analyst-review workflow, and why does ROC-AUC look fine? (Answer: PR-AUC is the honest one for this workflow. The analysts care about precision at a fixed daily review budget, which is a precision-recall question. ROC-AUC remains high because most of the ranking pairs are easy majority-vs-majority comparisons that have nothing to do with the rare-positive retrieval problem the workflow actually solves. ROC-AUC is invariant to prevalence; PR-AUC is not. The right metric for an imbalanced retrieval task is the one that moves when retrieval gets worse.)

### When Imbalance Isn't a Problem

A surprising number of "imbalanced" classification tasks are not actually problems for the classifier. If the metric is ROC-AUC, the cost is symmetric, the minority class still has thousands of examples in absolute terms, and the calibration of probabilities is downstream-irrelevant, then the right move is often to do nothing imbalance-specific and let the classifier learn the natural prevalence. Many production teams reach for SMOTE on a 1:5 task that did not need anything beyond a stratified split, paying complexity for no measurable gain.

The decision rule is short. If ROC-AUC is the metric and the minority class has enough absolute count to learn from, you do not need imbalance handling — pick a stratified splitter (Module 1.3 covers this) and move on. If PR-AUC, recall-at-precision, or business-cost-weighted metrics are the metric, then imbalance handling becomes a real engineering question and the rest of this module applies.

## Section 2: The Leakage Spine — Resampling Inside the CV Loop

This is the section the entire module is organized around. If you remember nothing else from this module, remember that resampling fits only on the training portion of each fold, and `imblearn.pipeline.Pipeline` is the mechanism that enforces it.

The naive failure pattern is this:

```python
# WRONG — leakage
from imblearn.over_sampling import SMOTE
from sklearn.model_selection import cross_val_score
from sklearn.linear_model import LogisticRegression

X_resampled, y_resampled = SMOTE(random_state=0).fit_resample(X, y)
auc = cross_val_score(
    LogisticRegression(max_iter=2000),
    X_resampled,
    y_resampled,
    cv=5,
    scoring="roc_auc",
).mean()
print("optimistic auc:", auc)
```

The contaminated statistic here is the synthetic-minority-sample distribution. SMOTE generated synthetic rows that interpolate between minority neighbors. After the resample, those synthetic rows are mixed into the dataset before cross-validation splits the data. A held-out fold can now contain a synthetic row whose neighbors are training rows, or a duplicated minority row whose original is in training. The fold is no longer held out in any meaningful sense.

The structural fix is to put the resampler inside a pipeline that is itself the unit cross-validated:

```python
# RIGHT — resampler fits on each training fold
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler

pipe = Pipeline([
    ("scale", StandardScaler()),
    ("smote", SMOTE(random_state=0)),
    ("clf", LogisticRegression(max_iter=2000)),
])

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
auc = cross_val_score(pipe, X, y, cv=cv, scoring="roc_auc").mean()
print("honest auc:", auc)
```

The crucial detail is that this is `imblearn.pipeline.Pipeline`, not `sklearn.pipeline.Pipeline`. sklearn's pipeline requires every intermediate step to implement the `fit` + `transform` contract (or `fit_transform`), and a resampler is fundamentally a different abstraction: it returns a new `(X_resampled, y_resampled)` pair, not a transformed `X`. Trying to drop a `SMOTE` instance into `sklearn.pipeline.Pipeline` typically raises an error during `fit` because resamplers do not implement `transform`; sklearn was never designed to host them. The `imblearn.pipeline.Pipeline` is sampler-aware: it knows to run resampler steps only during `fit`, on the training portion of the current fold, and to bypass them entirely at `predict` time so test-time predictions see the original feature distribution. The right way to think about this is not "sklearn would silently leak" but "sklearn's pipeline is the wrong container for resamplers; use the sampler-aware one."

This is the same shape as the oversampling-leakage entry in [Module 1.3's leakage taxonomy](../module-1.3-model-evaluation-validation-leakage-and-calibration/). The taxonomy is not algorithm-specific; the same logic applies whether the resampler is `SMOTE`, `ADASYN`, `RandomOverSampler`, `RandomUnderSampler`, or any of the combined methods covered in Section 6. The rule is unconditional: resamplers fit on training folds only, the imblearn pipeline is the enforcement mechanism, and the held-out fold sees only honest prevalence.

### What "Fold Boundary" Means for SMOTE Specifically

SMOTE creates synthetic minority samples by interpolating between a minority sample and one of its nearest minority neighbors. If SMOTE runs before the split, two failure modes overlap. First, a synthetic sample generated from minority neighbors A and B can land between them, and if A or B is later assigned to the validation fold, the validation fold contains a row that is a near-clone of training data. Second, the same minority row may be selected as a seed for many synthetic neighbors, and its k-nearest neighbors may straddle the train/validation boundary in any later split. Both failures inflate the validation score by amounts that depend on the neighborhood structure, so the optimistic bias is not even constant across runs.

Putting SMOTE inside `imblearn.pipeline.Pipeline` cuts the entire problem off because each fold's training rows are SMOTE'd separately, and the fold's validation rows never participate in any synthesis.

> **Pause and predict** — A practitioner asks whether the leakage from SMOTE-before-split is worse for tree-based learners or for linear learners. Which family should be more affected, and why? (Answer: tree-based learners typically. SMOTE creates synthetic rows close to existing minority points in feature space. A deep tree can carve out small high-purity leaves that essentially memorize the synthetic-row neighborhoods. When those neighborhoods straddle the train/validation boundary, the validation rows fall into leaves that were carved around their training-fold near-neighbors, and the apparent accuracy on validation rises sharply. Linear models with regularization smooth the decision boundary across the entire training set; the synthetic-row contamination still helps, but the smoothing limits how directly the validation rows benefit from training-set near-neighbors. Both leak; the bias is just larger for high-capacity learners.)

## Section 3: `class_weight="balanced"` — the First Move

Most sklearn classifiers accept a `class_weight` parameter. Setting it to `"balanced"` tells the estimator to weight each class inversely proportional to its frequency in the training data, so that the loss function treats the rare class as if it had the same total weight as the common class. The `sklearn.utils.class_weight.compute_class_weight` documentation describes the formula precisely: each class's weight equals `n_samples / (n_classes * n_samples_in_class)`. For a 1:99 prevalence binary problem, the minority class effectively gets a weight close to 50 and the majority class a weight close to 0.5, which is roughly what a 1:99 oversampler would produce in expectation — but without any new rows and without any leakage risk.

This is the first move for almost every imbalanced problem.

```python
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.model_selection import StratifiedKFold, cross_val_score

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)

unweighted = LogisticRegression(max_iter=2000)
ap_unweighted = cross_val_score(unweighted, X, y, cv=cv, scoring="average_precision").mean()

weighted = LogisticRegression(max_iter=2000, class_weight="balanced")
ap_weighted = cross_val_score(weighted, X, y, cv=cv, scoring="average_precision").mean()

print("AP without weights:", round(ap_unweighted, 3))
print("AP with balanced :", round(ap_weighted, 3))
```

`class_weight="balanced"` is supported by `LogisticRegression`, `LinearSVC`, `SVC`, `RandomForestClassifier`, `DecisionTreeClassifier`, `ExtraTreesClassifier`, `RidgeClassifier`, `Perceptron`, `SGDClassifier`, and `PassiveAggressiveClassifier` among others — see the `LogisticRegression` documentation for the canonical description of how the parameter is interpreted. `HistGradientBoostingClassifier` does not take `class_weight` directly but accepts a `sample_weight` argument at fit time, which gives you the same effect when paired with `sklearn.utils.class_weight.compute_class_weight("balanced", classes=np.unique(y_train), y=y_train)` and broadcast back to the rows. The notable exception is `KNeighborsClassifier`, which has no fit-time loss function to weight — its prediction is a vote among neighbors, and any reweighting has to happen at prediction time through the `weights` parameter or by changing the metric.

### Why class weights often beat oversampling

Three reasons. First, class weights touch only the loss function — there are no new rows, no synthetic samples, no neighbor-graph artifacts to leak across folds. Second, class weights cost nothing at training time, while oversampling can multiply the training set size by tens or hundreds and slow CV substantially. Third, class weights compose cleanly with `Pipeline` and `GridSearchCV` because they are just an estimator argument, while resamplers require the imblearn pipeline and a more careful workflow.

The cases where class weights are *not* enough are real but specific: extreme imbalance where the minority class has too few rows to support stable gradient signal even with upweighting; problems where the geometry of the minority class is very specific and SMOTE-style interpolation actually adds useful synthetic structure; problems with strongly clustered minority subgroups where ADASYN's adaptive density helps. Section 4 covers all three. But the discipline is to try `class_weight="balanced"` first, measure the change in PR-AUC and MCC, and only reach for resamplers if the answer is clearly insufficient.

### Custom class weights for explicit cost asymmetry

`class_weight` also accepts a dictionary, which is how you encode an explicit cost ratio when one is known. If a missed positive costs ten times what a false positive costs, then `class_weight={0: 1.0, 1: 10.0}` puts that asymmetry directly into the loss. The asymmetry is no longer about prevalence — it is about cost — and `class_weight="balanced"` is a default that approximates "assume costs are inversely proportional to prevalence", which may or may not match the actual business cost. When the business cost is known, encoding it directly is more honest than adopting the prevalence-inverse default.

### From class weights to a true cost matrix

`class_weight` upweights one class relative to another. A more general framing — and the one that the term *cost-sensitive learning* properly refers to — is a cost matrix `C[true, predicted]` that assigns a different cost to each possible (actual, predicted) pair. For a binary problem the matrix has four entries: cost of a true negative, false positive, false negative, and true positive. True negatives and true positives are usually zero or even negative (a true positive earns money). False positives and false negatives have positive costs whose ratio encodes the business asymmetry.

`class_weight` with a dictionary is a special case of cost-sensitive learning where the cost of misclassifying class 1 is fixed and the cost of misclassifying class 0 is also fixed, regardless of the predicted label. That covers most binary problems but it does not cover situations where, for example, a false positive on a high-value customer is more expensive than a false positive on a low-value customer. For per-row cost weighting, sklearn estimators that accept `sample_weight` at fit time can encode arbitrary per-row costs:

```python
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier

# Suppose `value` is a per-row dollar value associated with each customer
# and missed positives scale with that value
sample_weight = np.where(y_train == 1, value_train * 10.0, 1.0)

clf = HistGradientBoostingClassifier(random_state=0)
clf.fit(X_train, y_train, sample_weight=sample_weight)
```

The cost-sensitive frame also clarifies the threshold question. Once you have a cost matrix, the optimal decision for each row is the one that minimizes expected cost given the predicted probability, and that decision rule is a threshold on the probability that depends on the cost ratio: `threshold = C[FP] / (C[FP] + C[FN])` for the simple binary case. So a 1:10 false-negative-to-false-positive ratio implies a threshold of roughly 0.091, not 0.5. This is the same threshold the F-beta optimization would converge to with appropriate beta, just derived from explicit costs rather than from a metric weighting. When the business cost is genuinely known, the cost-matrix derivation is more direct; when only the relative cost is known, F-beta with a matching beta gets you to a similar place.

## Section 4: The Oversampling Family

Oversampling adds minority-class examples to the training set. The simplest version duplicates existing minority rows. The more sophisticated versions synthesize new minority rows by interpolating between minority neighbors. All of them belong inside `imblearn.pipeline.Pipeline`.

### `RandomOverSampler` — duplication

`RandomOverSampler` copies minority rows until each class has the same number of samples (or a chosen target ratio). It is the simplest oversampler and the one with the fewest assumptions. It introduces no synthetic data, so it cannot interpolate between minority samples in ways that may or may not be sensible, and it does not need to compute neighbor graphs. Its main weakness is that the duplicated rows are exactly identical to the originals, so a tree-based learner with sufficient depth can essentially memorize the duplicates without learning anything new about the minority class.

Use `RandomOverSampler` when the dataset is small and you want a baseline; when you do not trust SMOTE's interpolation assumptions because the features are categorical, ordinal, or otherwise non-interpolable; or when you want to oversample a multiclass problem where the geometry of synthesis is hard to reason about.

### `SMOTE` — synthetic minority oversampling

SMOTE (Synthetic Minority Oversampling Technique), introduced by Chawla, Bowyer, Hall, and Kegelmeyer in 2002, generates synthetic minority samples by picking a minority row, picking one of its k nearest minority neighbors, and creating a new sample at a uniformly random position on the line segment connecting them. The default k is 5. The result is that the minority class fills out the convex hull of the existing minority points without simply duplicating them.

```python
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score

pipe = Pipeline([
    ("smote", SMOTE(random_state=0, k_neighbors=5)),
    ("clf", RandomForestClassifier(n_estimators=200, random_state=0)),
])

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
ap = cross_val_score(pipe, X, y, cv=cv, scoring="average_precision").mean()
print("SMOTE + RF, AP:", round(ap, 3))
```

SMOTE earns its complexity in a specific regime. The features should be continuous or at least sensibly interpolable — interpolating between two rows whose `country` values are `"DE"` and `"FR"` to produce `"DE.5"` is nonsense, and SMOTE on one-hot-encoded categoricals creates synthetic rows with fractional one-hot indicators that no learner has any obvious way to interpret. The minority class should also be reasonably dense in feature space; SMOTE on a minority class consisting of a handful of points scattered across a high-dimensional feature space will interpolate between distant points and create synthetic rows that may not represent any real pattern.

There are SMOTE variants designed for mixed feature types. `SMOTENC` handles datasets with both continuous and categorical features by sampling categorical values from the minority neighbors instead of interpolating. `SMOTEN` is for purely categorical data. The imbalanced-learn over-sampling guide describes both.

### `ADASYN` — adaptive synthetic sampling

ADASYN (Adaptive Synthetic Sampling) generates more synthetic samples for minority points that are *harder to learn* — specifically, minority points whose neighborhood contains many majority points. The intuition is that the decision boundary needs more help where the classes overlap, so synthesis should concentrate there.

In practice, ADASYN often produces results similar to SMOTE on well-separated problems and modestly different results on problems with significant class overlap. The improvement, when present, tends to be small. ADASYN is a defensible choice when you have already tried `class_weight="balanced"` and SMOTE and want to push further; it is not a default-better-than-SMOTE choice.

### `BorderlineSMOTE` — synthesis at the boundary

BorderlineSMOTE focuses synthesis on minority points near the decision boundary, leaving safe-interior minority points alone. The reasoning is similar to ADASYN: the decision boundary is where the classifier struggles most, so synthetic data is most useful there. BorderlineSMOTE comes in two flavors; the documentation describes both. It is another fine-tuning option for problems where plain SMOTE has been tried and the team is looking for a small boost.

### When oversampling helps and when it hurts

Oversampling helps when the minority class is geometrically coherent, the features support sensible interpolation, the imbalance is in the 1:10 to 1:100 range, and `class_weight="balanced"` has already been tried and is not enough. Oversampling hurts — or at least does no good — when the features are high-cardinality categorical, the minority class is very sparse in feature space, the imbalance is so extreme that synthesis is amplifying a handful of points into a dominant fraction of the training set, or the data has substantial label noise that SMOTE will faithfully replicate and amplify.

The honest empirical finding from the broader imbalanced-learning literature is that oversampling often produces modest gains and sometimes hurts. It is not a silver bullet. It is a tool that earns its place in the toolkit when class weights and threshold tuning are not enough.

## Section 5: The Undersampling Family

Undersampling removes majority-class examples to match the minority count. It is the geometric opposite of oversampling: instead of inflating the minority, it deflates the majority.

### `RandomUnderSampler` — random majority removal

`RandomUnderSampler` drops majority rows uniformly at random until a target ratio is reached. It is the simplest undersampler and the one with the lowest computational cost. The risk is information loss: dropping 99% of the majority class on a 1:99 problem means throwing away 99% of the rows that represent normal behavior, and that information is exactly what the classifier uses to learn the negative class. For small datasets, this loss is often unacceptable.

Where `RandomUnderSampler` shines is the opposite regime: very large majority classes where the dominant computational cost is training time. If the majority has ten million rows and the minority has ten thousand, undersampling to a 1:5 ratio reduces training time by orders of magnitude and the discarded majority rows mostly carry redundant information. The decision is a cost-benefit question. How much of the majority class is actually load-bearing for the classifier, and how much of it is repetitive?

```python
from imblearn.under_sampling import RandomUnderSampler
from imblearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score

pipe = Pipeline([
    ("undersample", RandomUnderSampler(sampling_strategy=0.2, random_state=0)),
    ("clf", LogisticRegression(max_iter=2000)),
])

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
ap = cross_val_score(pipe, X, y, cv=cv, scoring="average_precision").mean()
print("RandomUnderSampler, AP:", round(ap, 3))
```

`sampling_strategy=0.2` here means "after undersampling, the minority class should be 20% of the size of the majority class" — that is, a 1:5 ratio. Setting it to `"auto"` makes the classes balanced (1:1). Both have legitimate uses; the right number is whatever leaves enough majority signal for the classifier to learn the negative class while keeping training tractable.

### Smarter undersamplers

Several undersamplers try to keep informative majority rows and drop redundant ones. `TomekLinks` removes pairs of nearest-neighbor points from opposite classes — the intuition is that these pairs are either label noise or boundary points whose removal cleans up the decision surface. `EditedNearestNeighbours` (ENN) removes majority points whose nearest neighbors disagree with the majority label. `NearMiss` selects majority points based on their distance to minority points using one of three rules: NearMiss-1 keeps majority points whose average distance to the *k* closest minority points is smallest, NearMiss-2 keeps majority points whose average distance to the *k* farthest minority points is smallest, and NearMiss-3 keeps a fixed number of majority neighbors per minority point. The three rules optimize for different geometries of the decision boundary, and the imbalanced-learn under-sampling guide describes the trade-offs.

These smarter undersamplers can outperform random undersampling when the majority class has significant structure and you want to preserve the boundary-defining points. They cost more computationally because they require nearest-neighbor graphs over the majority class, which is exactly the class that is large by definition; the cost can be substantial on multi-million-row datasets. They also introduce their own biases — NearMiss-1, NearMiss-2, and NearMiss-3 produce different subsets and the choice is not always obvious — and the cleaned-up training set may no longer represent the production distribution faithfully, which means a model trained on it can be brittle in unexpected ways. For most production problems, the right move is to start with `RandomUnderSampler` and only reach for the smarter variants if information loss appears to be the bottleneck and you have measured that loss against a held-out test set.

### Why undersampling rarely beats class weights

The same logic that made `class_weight="balanced"` the right first move applies to undersampling. Both interventions are trying to make the classifier pay more attention to the minority class. Class weights do it by reweighting the loss without changing the data; undersampling does it by removing data. Removing data has a hard cost — the discarded majority rows often contain real information about what "normal" looks like — and it is hard to recover that information later. Class weights have no such cost.

The case where undersampling actually beats class weights is when the majority class is so large that training time dominates the engineering loop, and the redundancy of the discarded rows is high enough that the loss is small. That is a real regime, especially in industries with massive event streams (ad clicks, network logs, transaction records). In those cases, undersampling buys faster iteration, which compounds across many model revisions. For most tabular problems with majority counts in the millions or fewer, class weights win.

## Section 6: Combined Methods

Combined methods apply both oversampling and undersampling in sequence. The two main implementations in imbalanced-learn are `SMOTEENN` and `SMOTETomek`.

`SMOTEENN` runs SMOTE to oversample the minority class, then runs Edited Nearest Neighbours on the resulting (resampled) dataset to clean up samples whose local neighborhood disagrees with their label. ENN is not limited to synthetic samples: depending on configuration it can remove either original or synthetic rows that look noisy in feature space. The net effect is a resampled dataset that is more conservative both about what SMOTE manufactured and about what it inherited — pruning the boundary region wherever local neighborhoods are mixed enough to make the label call ambiguous.

`SMOTETomek` runs SMOTE then removes Tomek links — pairs of nearest-neighbor points from opposite classes. The net effect is oversampling that cleans up the boundary, removing both noisy synthetic samples and ambiguous original samples.

Both methods are useful when the data is noisy enough that pure SMOTE leaves visible artifacts. The cost is computational: you are paying for both an oversampler and an undersampler, plus a nearest-neighbor graph for the cleaning step. The benefit, when present, is a cleaner training distribution and modestly better generalization. As with ADASYN and BorderlineSMOTE, treat combined methods as fine-tuning options to reach for when plain SMOTE has been measured and you want to try a small additional move, not as the first thing you try.

## Section 7: Threshold Tuning — the Often-Best Lever

Resampling shifts the data distribution. Class weights shift the loss function. Both are upstream of a more direct lever: the threshold the classifier uses to convert probabilities into class labels.

The default `predict()` method on a binary sklearn classifier uses a threshold of 0.5 on `predict_proba(X)[:, 1]`. That default is not a law of nature. It is a convention. If your business cost is asymmetric or your prevalence is far from 50%, the right threshold is somewhere else, and finding it is often the single most decisive move you can make.

```python
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    f1_score,
    fbeta_score,
    precision_recall_curve,
)
from sklearn.model_selection import train_test_split

X_dev, X_test, y_dev, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=0
)
X_train, X_valid, y_train, y_valid = train_test_split(
    X_dev, y_dev, test_size=0.25, stratify=y_dev, random_state=1
)

clf = LogisticRegression(max_iter=2000, class_weight="balanced").fit(X_train, y_train)
proba_valid = clf.predict_proba(X_valid)[:, 1]

precision, recall, thresholds = precision_recall_curve(y_valid, proba_valid)

# F2 emphasizes recall (false negatives are 4x as expensive as false positives)
beta = 2.0
f_beta = (1 + beta**2) * precision * recall / (beta**2 * precision + recall + 1e-12)
best_idx = int(np.argmax(f_beta[:-1]))   # last value has no threshold
best_threshold = thresholds[best_idx]

print("best validation threshold:", round(best_threshold, 3))
print("validation F2 at best    :", round(f_beta[best_idx], 3))

# Apply the frozen threshold ONCE on test
proba_test = clf.predict_proba(X_test)[:, 1]
y_pred_test = (proba_test >= best_threshold).astype(int)
print("test F2:", round(fbeta_score(y_test, y_pred_test, beta=2.0), 3))
```

The key discipline is the same one Module 1.3 introduced under threshold leakage: tune the threshold on validation data, freeze it, then evaluate on test data exactly once. Tuning the threshold on the test set is the most common form of threshold leakage and produces a number that cannot be reproduced in production because the test set is not the deployment distribution.

`fbeta_score` accepts a `beta` argument that controls how much you weight recall relative to precision. `beta=1` is the standard F1, treating them equally. `beta>1` emphasizes recall — `beta=2` is the F2 score, where recall is weighted four times more heavily than precision (the formula uses `beta**2`). `beta<1` emphasizes precision. Choosing the right `beta` is an explicit business-cost decision: if missing a positive costs four times what a false alarm costs, F2 is the right F-beta target. If the costs are reversed, F0.5 is right.

### Threshold tuning vs. resampling

For many problems, threshold tuning on a properly trained classifier — `class_weight="balanced"` plus calibrated probabilities — is enough to handle the imbalance without ever touching a resampler. The classifier learns a probability surface across the full population. The threshold picks where on that surface the decision should sit. You change the threshold without changing the model, you can sweep different operating points for different business contexts (e.g., a fraud team that wants high recall during a campaign and high precision during steady-state review), and you do not introduce any leakage risk because the threshold is just a scalar.

Resampling, by contrast, changes the model. Two separately-resampled training runs may produce two different decision surfaces. Threshold tuning on the resampled model is still valid, but it adds a layer of variance the threshold-tuning-only approach does not have.

### Threshold tuning under a fixed-capacity constraint

The most common production version of threshold tuning is not "maximize F-beta" but "respect a fixed daily review capacity". An analyst team can review 200 cases per day. The classifier produces scores for 50,000 cases per day. The decision is to pick the top 200 by score and ignore the rest, which is equivalent to picking the threshold that selects exactly 200 positives per day on average. The metric of interest is precision at that operating point, sometimes written as *precision@k* or *precision@200*.

```python
import numpy as np

# Daily review capacity
k = 200

# Score every candidate, sort descending, take top-k
proba_valid = clf.predict_proba(X_valid)[:, 1]
order = np.argsort(-proba_valid)
top_k_idx = order[:k]
top_k_threshold = proba_valid[order[k - 1]]

# Precision at k
precision_at_k = y_valid[top_k_idx].mean()
print(f"precision@{k}: {round(precision_at_k, 3)}")
print(f"threshold that selects top {k}: {round(top_k_threshold, 4)}")
```

This is mathematically equivalent to picking the threshold that produces exactly `k` predicted positives on the validation set, and applying that threshold to test exactly once. The reason to think of it as a capacity constraint rather than as F-beta is that the deployment cares about precision at the chosen `k`, not about the precision-recall trade-off across all thresholds. Maximizing F2 over the full curve and maximizing precision at a fixed top-k will generally pick different thresholds, and "what does the deployment actually pay for" is the question that decides which one is right.

A second production-version is "achieve a target precision". Suppose the analyst team will only act on alerts if precision is at least 0.6 — below that, they ignore the queue. The decision is to find the most permissive threshold (highest recall) that still satisfies precision ≥ 0.6 on validation. `precision_recall_curve` gives you the array of thresholds and the corresponding precisions; a single mask-and-argmin finds the right point. This pattern is common in safety-critical and regulatory deployments where false alarms have a fixed reputational cost.

> **Pause and decide** — A team has a sepsis-risk classifier with `class_weight="balanced"` already enabled. PR-AUC is 0.42, which they consider modest but acceptable. The downstream workflow is a clinician-review queue with a fixed daily review capacity of about 200 cases. The team is about to add SMOTE. What should they do first, and why is SMOTE likely to disappoint them in this specific deployment? (Answer: tune the threshold on validation data to maximize the precision-at-200-flags-per-day operating point. The deployment is precision-bound at a fixed review capacity, which is a threshold question, not a model question. SMOTE will change the probability surface but it will not magically improve precision at the chosen operating point — what matters is the rank order of the top 200 scores, and `class_weight="balanced"` already gave the model the right loss signal to learn that ranking. Threshold tuning is the cheaper, more targeted move and it is what the deployment actually needs.)

## Section 8: Metrics for Imbalanced Data

Metric choice is upstream of every other decision in this module. The wrong metric makes good models look bad and bad models look good, and most of the resampling-helped-us-a-lot stories in the wild are stories about a metric that was not capable of distinguishing improvement from noise.

### PR-AUC (`average_precision_score`)

The scikit-learn `average_precision_score` documentation defines it as the area under the precision-recall curve, computed as the weighted mean of precisions at each threshold, with the weight being the increase in recall from the previous threshold. PR-AUC is sensitive to class prevalence in a way ROC-AUC is not. At low prevalence, PR-AUC is bounded by the prevalence itself for a random classifier (a 1% prevalence problem has random-classifier PR-AUC around 0.01), and it rises to 1.0 only when the model can perfectly rank positives above negatives.

The practical advantage is exactly what the formal property suggests: PR-AUC moves when retrieval gets worse, which is the question that matters for imbalanced classification.

### MCC (`matthews_corrcoef`)

The Matthews correlation coefficient is a single-number summary of the confusion matrix that is not biased by class imbalance. Its formula incorporates true positives, true negatives, false positives, and false negatives symmetrically, and it ranges from -1 (perfect disagreement) through 0 (random performance) to +1 (perfect agreement). The scikit-learn `matthews_corrcoef` documentation describes it as a balanced measure that can be used even if the classes are of very different sizes.

```python
from sklearn.metrics import matthews_corrcoef

y_true = [0]*99 + [1]*1
y_pred_dumb = [0]*100   # predicts only the majority
y_pred_real = [0]*98 + [1] + [0]    # one false negative

print("dumb MCC:", matthews_corrcoef(y_true, y_pred_dumb))   # 0.0
print("real MCC:", matthews_corrcoef(y_true, y_pred_real))   # also negative-ish
```

MCC's value is that it goes to zero for the all-majority predictor that would score 0.99 accuracy on a 1:99 problem. Accuracy and ROC-AUC can both be deceived; MCC cannot.

### F-beta (`fbeta_score`)

F-beta scores combine precision and recall into a single number, with `beta` controlling the trade-off. The formula is `(1 + beta**2) * P * R / (beta**2 * P + R)`. F1 (beta=1) treats them equally; F2 weights recall four times more; F0.5 weights precision four times more. The choice of `beta` is the business-cost decision: how many false positives is one missed positive worth?

F-beta is threshold-conditioned. It evaluates the model at one specific operating point, not across the full ranking. That makes it the right metric when you have already decided what the deployment threshold is, and the wrong metric for cross-validation-based hyperparameter search where you want a threshold-independent ranking quality measure (use PR-AUC or MCC for that).

### When ROC-AUC is still the right metric

ROC-AUC is not always wrong on imbalanced data. It is the right metric when the deployment task is to *rank* the full population — for example, to compute every customer's churn risk and order them for an outreach campaign — and there is no fixed operating threshold. ROC-AUC measures the probability that the model ranks a randomly chosen positive above a randomly chosen negative, which is exactly the quantity a ranking deployment cares about.

The metric question is therefore not "use PR-AUC for imbalanced data and ROC-AUC for balanced data". It is "use the metric whose definition matches the decision your deployment actually makes". Imbalanced data shifts the answer toward PR-AUC and MCC for most retrieval-style deployments, but ROC-AUC retains a place when ranking quality across the full population is what matters.

### A worked metric comparison

A small example clarifies why the metric choice matters more than the modeling choice for highly imbalanced data. Two hypothetical models are evaluated on the same 1:99 imbalanced test set:

| Metric | Model A (always predicts 0) | Model B (catches half the positives at high precision) |
| --- | --- | --- |
| Accuracy | 0.99 | 0.985 |
| ROC-AUC | 0.50 (degenerate) | 0.78 |
| PR-AUC | 0.01 (≈ prevalence) | 0.42 |
| F1 | 0.00 | 0.58 |
| Matthews correlation | 0.00 | 0.59 |

Accuracy ranks them as nearly tied — Model A is even slightly better. Every other metric correctly identifies Model B as the useful one. The lesson is not that accuracy is bad in general; it is that accuracy on imbalanced data confuses "predicting the majority" with "useful prediction", and any single metric whose denominator is dominated by the majority class will do the same. PR-AUC, F1, and MCC make the comparison meaningful because their definitions force the rare class to contribute.

The honest reporting practice is to show at least three metrics that respond to imbalance plus one threshold-conditioned metric tied to the deployment's operating point. A typical model card row looks like: *PR-AUC 0.42, ROC-AUC 0.78, MCC 0.59, precision@k=200 = 0.71*. Each number answers a different question, and the reader who knows the deployment can pick the one that matters.

## Section 9: Resampling and Calibration — the Surprise

This is the section that catches most teams off guard. Resampling does not improve probability calibration; it actively makes calibration worse, and the worse calibration is invisible until something downstream depends on the probabilities meaning what they say.

The mechanism is simple. A classifier trained on a 1:99 imbalance and evaluated against the natural prevalence emits probabilities that approximate the conditional class probability `P(y=1|x)`. Resample the training set to 1:1 and the same classifier emits probabilities that approximate `P(y=1|x)` *under the resampled prevalence* — that is, calibrated for a 50/50 world that does not exist outside the training notebook. The classifier still ranks positives above negatives correctly (resampling rarely hurts ranking quality much), but its probability scores are no longer interpretable as the actual probability of class 1 given features.

For deployments that only consume the rank order (e.g., "flag the top 200 cases per day"), this miscalibration is harmless. For deployments that consume the probability values directly — expected-value computations, risk-tier assignment based on probability bands, downstream Bayesian updates, abstention thresholds based on confidence — this miscalibration is invisible to the offline metric and silently wrong in production.

The fix is the calibration workflow from [Module 1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/). If you resampled and probabilities matter, calibrate after training:

```python
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold

resampling_pipe = Pipeline([
    ("smote", SMOTE(random_state=0)),
    ("clf", RandomForestClassifier(n_estimators=200, random_state=0)),
])

calibrated = CalibratedClassifierCV(
    estimator=resampling_pipe,
    method="sigmoid",
    cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=0),
    ensemble=True,
)

calibrated.fit(X, y)
```

The calibrator sits outside the resampling pipeline and is fitted under cross-validation against the *original* class distribution, which restores the probability-as-actual-probability interpretation. Module 1.3 covers `CalibratedClassifierCV` in depth, including the sigmoid-vs-isotonic decision and the reliability-diagram diagnostic.

The cleaner alternative is to skip resampling entirely. `class_weight="balanced"` shifts the loss-function gradient but does not change the training distribution, and the resulting probabilities — while not perfectly calibrated either, since the loss is no longer log-likelihood under the natural distribution — are usually closer to the natural prevalence than a SMOTE-resampled model's probabilities. If probabilities matter and you do not have a strong reason to resample, do not.

## Section 10: Focal Loss — a Cross-Link, Not a Deep Dive

Focal loss, introduced by Lin, Goyal, Girshick, He, and Dollár in 2017 for object detection, is a modified cross-entropy that down-weights easy examples and concentrates the gradient on hard ones. The formula adds a `(1 - p_t)**gamma` factor to the standard cross-entropy term, where `p_t` is the model's predicted probability for the true class. When the model is already confident and correct, `p_t` is close to 1, the focal factor is close to 0, and the example contributes little to the gradient. When the model is wrong or uncertain, the focal factor approaches 1 and the example contributes its full weight. The original paper used `gamma=2.0`.

Focal loss originated in the deep-learning world for dense object detection tasks where the class imbalance is extreme — the foreground-to-background ratio in many object-detection datasets is 1:1000 or worse — and class weights and resampling were both insufficient. The deep-learning track covers it as part of the CNN module: see [Deep Learning Module 1.4: CNNs & Computer Vision](../../deep-learning/module-1.4-cnns-computer-vision/) for the object-detection context where focal loss was introduced.

For tabular sklearn classification, focal loss is rare. It is not implemented in core sklearn, the resampling-or-class-weights toolkit usually solves the imbalance problem at the imbalance ratios tabular work typically faces, and adding a custom loss is usually more engineering than the problem warrants. Mention it in design discussions if your problem is in the 1:1000+ regime and class weights have been tried; otherwise it is the wrong tool for the typical sklearn workflow.

## Section 11: Practitioner Playbook

Here is the recipe in the order the moves should be tried. Each step is cheaper and lower-risk than the next; only escalate when the previous step has been measured and is genuinely insufficient.

1. **Diagnose first.** Compute the actual class prevalence. Pick the metric that matches the deployment decision (PR-AUC, MCC, or F-beta for retrieval-style deployments; ROC-AUC for ranking-style deployments). Decide whether the cost is symmetric or asymmetric. If the asymmetry is known, encode it explicitly rather than approximating with prevalence-inverse defaults.
2. **Try `class_weight="balanced"`.** Or pass an explicit `class_weight` dict if you know the cost asymmetry. Re-measure on the chosen metric. For most problems, this is enough.
3. **Tune the threshold on validation.** Use `precision_recall_curve` and pick the threshold that maximizes the F-beta you care about, or that hits a target precision-at-recall, or that respects a fixed review-capacity constraint. Freeze the threshold and apply it to test data exactly once. This is often the most decisive move.
4. **If still insufficient, add a resampler inside `imblearn.pipeline.Pipeline`.** Start with `RandomOverSampler` for a leakage-free baseline. Then try `SMOTE` if the features support interpolation. Then `ADASYN` or `BorderlineSMOTE` for fine-tuning. Re-measure after each change.
5. **If the imbalance is extreme (1:1000+), reconsider as anomaly detection.** Cross-link to [Module 1.9](../module-1.9-anomaly-detection-and-novelty-detection/). At extreme imbalance, the right framing is often to learn what normal looks like and flag deviations, not to learn a classifier across two classes one of which has thirty examples.
6. **If probabilities matter, calibrate at the end.** Use `CalibratedClassifierCV` from [Module 1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/). Resampling pushes probabilities away from the natural prevalence; calibration restores them.
7. **Document the decisions.** Which step you stopped at, what metric you chose, what threshold you froze, and what cost asymmetry you encoded — these are the documentation that lets the next on-call engineer reproduce your evaluation. Cross-validated F1 with no recorded threshold is not reproducible.

The discipline embedded in this list is that imbalance handling is a sequence of cheaper moves that often suffice before the expensive moves are needed. Most teams that report SMOTE-helped-us-a-lot did not measure step 2 first. Most teams that report SMOTE-did-nothing did not put the resampler inside the imblearn pipeline. Both failures are avoidable with a written-down sequence.

## Section 12: Where Class Imbalance Is the Wrong Frame

Class imbalance is the right frame when the underlying decision is binary or multi-class classification with prevalence skew that breaks the chosen metric or the chosen threshold. It is the wrong frame in several adjacent situations.

**Anomaly detection at extreme imbalance.** When the minority class is below roughly 1:1000 prevalence and especially when its members are heterogeneous — many different kinds of "anomaly" rather than a single coherent positive class — the right framing is often to learn the structure of normal data and flag rows that deviate. [Module 1.9](../module-1.9-anomaly-detection-and-novelty-detection/) covers this in depth: `IsolationForest`, `LocalOutlierFactor`, `OneClassSVM`, and `EllipticEnvelope` each give you a way to score "how unusual is this row" without committing to a binary positive/negative split. The threshold on the anomaly score plays the same role the classification threshold plays here, and the metric question (PR-AUC at top-k) is similar.

**Multi-class with roughly equal classes.** A "10 classes, each at 10%" problem is not imbalanced in the sense this module addresses. The relevant tools there are stratified splits, multi-class metrics (macro-averaged PR-AUC, multi-class log-loss), and care with one-vs-rest decompositions if you need them. Resampling and class weights extend to multi-class but the framing of the problem is different.

**Regression with a skewed target.** A regression problem where the target distribution is heavy-tailed is not a class imbalance problem. The relevant tools are appropriate loss functions (Tweedie / Poisson / Gamma for count and strictly-positive targets — see [Module 1.2](../module-1.2-linear-and-logistic-regression-with-regularization/)), target transformations (log-transform for log-normal targets), and quantile regression when the goal is to predict tail behavior.

**Sequential or streaming imbalance.** When the prevalence shifts over time and the data is non-stationary, a static resampling strategy will be wrong tomorrow even if it is right today. Drift detection and monitoring become first-class concerns; cross-link to MLOps Module 1.10 (ML Monitoring) for the discipline.

The shape across all four is that "imbalance" is one of several diagnoses. Get the diagnosis right before reaching for the imbalance toolkit, or you spend engineering effort on the wrong problem.

## Did You Know?

- `imblearn.pipeline.Pipeline` is a drop-in alternative to `sklearn.pipeline.Pipeline` that adds resampler-aware semantics: resampler steps run during `fit` to transform `(X, y)` for downstream steps, but are bypassed during `predict` so test-time predictions see the original feature distribution. This is the only pipeline implementation that makes resamplers leakage-safe inside cross-validation: https://imbalanced-learn.org/stable/references/generated/imblearn.pipeline.Pipeline.html
- The Matthews correlation coefficient returns 0.0 for an all-majority hard predictor on any imbalanced binary problem, while accuracy on the same prediction approaches the majority-class prevalence — 0.99 at 1:99 imbalance — without conveying any real predictive ability. (ROC-AUC for the same all-majority hard prediction is 0.50, not arbitrarily high; the parallel concern at high imbalance is that a *ranking* model can post a strong ROC-AUC while still being useless at any practical operating threshold, which is why pairing PR-AUC and MCC with ROC-AUC matters.) That property is why `matthews_corrcoef` is the canonical single-number summary that resists accuracy-induced inflation: https://scikit-learn.org/stable/modules/generated/sklearn.metrics.matthews_corrcoef.html
- The original SMOTE paper (Chawla, Bowyer, Hall, and Kegelmeyer, 2002) introduced synthetic minority oversampling as an alternative to simple duplication, with the explicit observation that duplication causes overfitting because the decision region for the minority class becomes very specific to the duplicated points: https://arxiv.org/abs/1106.1813
- Focal loss (Lin et al., 2017) was introduced for dense object detection at extreme foreground-background imbalance ratios common in computer vision, not for tabular classification. The paper's `gamma=2.0` default is a vision-domain choice, and tabular practitioners who reach for focal loss should treat that constant as a hyperparameter to tune rather than a universal default: https://arxiv.org/abs/1708.02002

## Common Mistakes

| Mistake | Why it bites | Fix |
| --- | --- | --- |
| Applying SMOTE before the train/test split | Synthetic minority samples land in the validation fold whose neighbors trained the synthesizer; the cross-validated score is optimistic by an unknown margin | Put the resampler inside `imblearn.pipeline.Pipeline` so each fold's training rows are resampled separately and the held-out fold is never touched |
| Using `sklearn.pipeline.Pipeline` with a resampler | sklearn's pipeline does not understand resamplers as a special step type; it will either error or silently apply the resampler at predict time, which is wrong both ways | Use `imblearn.pipeline.Pipeline` whenever the chain contains a resampler |
| Reaching for SMOTE before trying `class_weight="balanced"` | Class weights are cheaper, leakage-free, and often as good as oversampling — most "SMOTE helped us a lot" reports did not measure the class-weight baseline | Always run the `class_weight` baseline and record its PR-AUC and MCC before adding any resampler |
| Reporting ROC-AUC on a 1:1000 imbalanced retrieval task | ROC-AUC is invariant to prevalence; it can stay high while the model retrieves nothing useful at any practical threshold | Report PR-AUC and MCC; treat ROC-AUC as a secondary signal at high imbalance, not the headline number |
| Tuning the decision threshold on the test set | The threshold becomes a function of test labels, which leaks test information into the deployed model | Tune on validation, freeze the threshold, evaluate on test exactly once |
| Resampling and then using the model's probabilities directly | Resampling shifts the model's calibration toward the resampled prevalence; the probabilities no longer match the natural-prevalence interpretation downstream code expects | Either skip resampling and use `class_weight`, or wrap the resampling pipeline in `CalibratedClassifierCV` with the original distribution |
| Treating extreme imbalance (1:10,000+) as a classification problem | Synthesis and class weights both struggle when the minority has dozens of examples in a high-dimensional feature space; the framing itself is wrong | Reframe as anomaly detection with `IsolationForest`, `LocalOutlierFactor`, or `OneClassSVM` — see Module 1.9 |
| Using `class_weight="balanced"` when you know the cost ratio | The "balanced" default approximates "cost is inversely proportional to prevalence", which is rarely the actual business cost | Pass an explicit `class_weight={0: w0, 1: w1}` dict that encodes the known cost ratio |

## Quiz

1. A team applies SMOTE to the full dataset, then runs `cross_val_score` with `StratifiedKFold(n_splits=5)`, and reports the mean F1 as the model's expected performance. The number is dramatically higher than what they see in production. Where is the leakage, and what is the structural fix?

<details><summary>Answer</summary>
SMOTE generated synthetic minority samples by interpolating between minority neighbors before the cross-validation split. Each fold's validation rows can therefore contain synthetic rows whose neighbors are training rows, or original minority rows whose synthetic descendants are in training. The validation score is no longer an estimate of held-out performance. The fix is to wrap the resampler and classifier in `imblearn.pipeline.Pipeline` and pass that pipeline to `cross_val_score`, so each fold's training rows are SMOTE'd separately and the validation fold sees only honest prevalence. `sklearn.pipeline.Pipeline` will not work for this — it does not understand resampler steps — so the choice of pipeline class is part of the fix.
</details>

2. A practitioner has a 1:200 imbalanced fraud problem and reports that ROC-AUC is 0.93. The analyst team complains that the alert queue is full of noise. PR-AUC turns out to be 0.21. Which metric is telling the truth about the deployment, and why are both numbers consistent with the same model?

<details><summary>Answer</summary>
PR-AUC is the metric that matches the deployment. The analyst team's workflow is precision-bounded at a fixed review capacity, which is a precision-recall question, not a ranking-across-the-population question. ROC-AUC is high because most ranking pairs are easy majority-vs-majority comparisons, and the metric's invariance to prevalence means a model that catches almost no rare positives can still post a respectable AUC. PR-AUC drops sharply because precision at any practical threshold is poor. Both numbers are consistent with the same model because the metrics measure different things: ROC-AUC asks how often the model correctly orders a positive above a negative across the whole population, and PR-AUC asks how clean the top of the ranking is. The deployment cares about the top of the ranking.
</details>

3. A team has a 1:50 imbalanced classifier where `class_weight="balanced"` gave PR-AUC 0.61. They are debating whether to add SMOTE. What single move should they try first, and why is it likely to be more decisive than SMOTE for most precision-bound deployments?

<details><summary>Answer</summary>
Tune the decision threshold on validation data. The classifier already produces a probability surface that ranks positives above negatives reasonably well — `class_weight="balanced"` and a 0.61 PR-AUC suggest the ranking is workable. What the deployment likely needs is the right operating point on that surface for its specific cost ratio or review capacity, which is a threshold question, not a model question. SMOTE will produce a slightly different probability surface but it cannot improve precision at a chosen operating point beyond what the existing rank order supports. Threshold tuning is cheaper, has no leakage risk, and addresses the actual deployment need directly.
</details>

4. A teammate proposes wrapping a SMOTE-plus-RandomForest pipeline in `CalibratedClassifierCV(method="sigmoid")`. Why is this often the right move when the deployment consumes probabilities directly, and what would happen without it?

<details><summary>Answer</summary>
SMOTE shifts the training prevalence away from the natural class distribution. The classifier learns probabilities that are calibrated for the resampled world, not the deployed world. Without calibration, downstream code that interprets the model's probabilities as "actual probability of class 1" — for expected-value computations, risk-tier assignment, or abstention thresholds — will systematically over-predict the minority class because the training distribution made it look more common than it actually is. `CalibratedClassifierCV` fits a calibrator under cross-validation against the original distribution, restoring the probabilities-mean-what-they-say interpretation. Without it, the rank order is fine but the probability values are wrong by an amount proportional to the resampling ratio.
</details>

5. A practitioner has a binary classification problem with 30 minority examples in a feature space of 200 dimensions. They are about to apply SMOTE with `k_neighbors=5`. What is the structural problem with this plan, and what is the better framing?

<details><summary>Answer</summary>
SMOTE with `k_neighbors=5` requires each minority point to have five minority neighbors close enough that interpolation between them produces a sensible synthetic sample. With 30 points in 200 dimensions, the minority class is very sparse — most pairs of minority points are far apart, the nearest neighbors are not necessarily close in any meaningful sense, and synthetic samples on the line segments between distant points may not represent any real pattern. The better framing at this regime is anomaly detection: learn what normal looks like across the (much larger) majority class and flag rows that deviate. Cross-link to Module 1.9. This is the canonical "extreme imbalance is actually an anomaly detection problem" case.
</details>

6. A team is choosing between F1, F2, and F0.5 for a model that flags suspicious transactions for analyst review. The cost of missing a true positive is roughly five times the cost of a false alarm. Which F-beta is appropriate, and what is the role of the `beta` parameter in the formula?

<details><summary>Answer</summary>
F2 is appropriate. The F-beta formula is `(1 + beta**2) * P * R / (beta**2 * P + R)`, and `beta` controls how much weight recall gets relative to precision. `beta=1` weights them equally; `beta=2` weights recall four times more (because the formula uses `beta**2`); `beta=0.5` weights precision four times more. With a five-to-one cost ratio in favor of catching positives, F2 is closer than F1 or F0.5, and an explicit cost dictionary passed via `class_weight={0: 1.0, 1: 5.0}` plus threshold tuning to maximize a recall-conditioned objective is even more direct. The point is that "the right F-beta" is the one whose weighting matches the actual cost asymmetry.
</details>

7. Why does using `class_weight="balanced"` not require any change to the cross-validation protocol, while adding SMOTE does?

<details><summary>Answer</summary>
`class_weight="balanced"` is just an estimator argument. It changes the loss function the classifier optimizes during fitting, but it does not change the training data — there are no new rows, no synthetic samples, no transformations applied to `X` or `y` that need to be confined to a single fold's training portion. A standard `sklearn.pipeline.Pipeline` plus `cross_val_score` is sufficient, and there is no leakage risk. SMOTE, by contrast, generates new rows by interpolating between existing rows, and those new rows must come from training data only — otherwise the validation fold contains rows generated from training rows, and the held-out evaluation is contaminated. Confining SMOTE to each fold's training portion requires the resampler-aware `imblearn.pipeline.Pipeline`. The difference is structural: class weights are an estimator-argument intervention, while resampling is a data-generation intervention.
</details>

8. A team has a 1:5,000 imbalanced sepsis-prediction problem. `class_weight="balanced"` produces a model that is technically correct but the PR-AUC is 0.04. SMOTE produces a model with PR-AUC 0.06 but probabilities calibrated to a 1:1 world. The clinical workflow needs both useful retrieval and probabilities that match clinical priors. What is the right framing change?

<details><summary>Answer</summary>
The framing change is to treat this as an anomaly detection problem rather than a binary classification problem. At 1:5,000 prevalence, the minority class is too sparse for either class weights or SMOTE to give the classifier enough signal — both numbers are essentially "barely better than random". The clinical workflow needs a score that says "how unusual is this patient's pattern relative to baseline", which is exactly what anomaly detection produces. Cross-link to Module 1.9: `IsolationForest` or `LocalOutlierFactor` trained on the majority distribution gives a continuous score that can be thresholded against review capacity. The probability-calibration question dissolves because the score is no longer claiming to be a probability. The threshold-tuning workflow from Section 7 still applies, just on the anomaly score instead of the classifier output.
</details>

## Hands-On Exercise

- [ ] Step 0: Start a fresh notebook or script and import `numpy as np`, `make_classification`, `train_test_split`, `StratifiedKFold`, `cross_val_score`, `LogisticRegression`, `RandomForestClassifier`, `StandardScaler`, `precision_recall_curve`, `fbeta_score`, `matthews_corrcoef`, `average_precision_score`, `roc_auc_score`, `CalibratedClassifierCV`, `Pipeline as ImbPipeline` from `imblearn.pipeline`, `SMOTE`, `RandomOverSampler`, and `RandomUnderSampler`. Generate an imbalanced binary dataset with `make_classification(n_samples=10000, n_features=20, n_informative=8, weights=[0.99, 0.01], random_state=0)` and confirm the prevalence with `y.mean()`.

- [ ] Step 1: Run a baseline `LogisticRegression(max_iter=2000)` (no class weights, no resampling) under five-fold stratified cross-validation. Record both `roc_auc` and `average_precision` from `cross_val_score`. Note in writing how large the gap between the two metrics is and which one matches the imbalanced-retrieval framing of the task.

- [ ] Step 2: Re-run the same model with `class_weight="balanced"` under the same cross-validation. Record the same two metrics. Write one sentence on whether class weights moved PR-AUC meaningfully and whether they moved ROC-AUC.

- [ ] Step 3: Build an `imblearn.pipeline.Pipeline` with `StandardScaler` → `SMOTE(random_state=0)` → `LogisticRegression(max_iter=2000)`. Run it under the same five-fold stratified cross-validation and record both metrics. Compare against Step 2. Note in writing whether SMOTE inside the pipeline beat plain class weights.

- [ ] Step 4: Run a deliberate-leakage demonstration. SMOTE the *full* dataset with `SMOTE(random_state=0).fit_resample(X, y)`, then run cross-validation on the resampled data. Compare the optimistic AUC against the honest AUC from Step 3. Write a short paragraph naming the leakage explicitly: synthetic minority samples crossed the fold boundary, the validation rows contain near-clones of training rows, and the cross-validated score is biased upward by an unknown amount. Tie the explanation back to [Module 1.3's leakage taxonomy](../module-1.3-model-evaluation-validation-leakage-and-calibration/).

- [ ] Step 5: Add `RandomUnderSampler(sampling_strategy=0.2, random_state=0)` to a separate pipeline in front of `LogisticRegression`. Run cross-validation and compare PR-AUC against Steps 2 and 3. Write one sentence on whether undersampling beat SMOTE on this dataset and one sentence on what you would lose if the majority class were small.

- [ ] Step 6: Implement threshold tuning. Split the data into train/validation/test with `train_test_split` twice (the train/validation/test pattern from Module 1.3). Fit `LogisticRegression(class_weight="balanced", max_iter=2000)` on training. Compute `precision_recall_curve` on validation predictions. Pick the threshold that maximizes F2 (`beta=2.0`). Apply the frozen threshold to test predictions exactly once and report the test F2. Write one sentence on why you used F2 and one on why the threshold was chosen on validation, not test.

- [ ] Step 7: Compare metrics for the all-majority predictor. Build `y_pred_dumb = np.zeros_like(y)` and compute `accuracy_score`, `roc_auc_score` (using probabilities from a fitted classifier or the dumb prediction directly — note which), `matthews_corrcoef`, and `fbeta_score(beta=2)`. Note which metric values are inflated by the imbalance and which are not. The MCC of the all-zero predictor should be 0.0 even though accuracy is 0.99.

- [ ] Step 8: Calibrate a SMOTE-resampled model. Wrap the imblearn pipeline from Step 3 in `CalibratedClassifierCV(estimator=pipe, method="sigmoid", cv=5)` and fit on the original (un-resampled) data. Compare the histogram of predicted probabilities from the calibrated model against the un-calibrated SMOTE model. Note in writing how the probability distribution changed and why this matters for any downstream code that consumes the probabilities directly.

- [ ] Completion check: confirm that every resampler in the exercise lived inside an `imblearn.pipeline.Pipeline` except in Step 4's deliberate-leakage demonstration.

- [ ] Completion check: confirm that the threshold from Step 6 was selected on validation and applied to test exactly once, never tuned against test.

- [ ] Completion check: write one final shipping recommendation paragraph stating which combination of moves (class weights, threshold tuning, SMOTE, calibration) you would default to for a precision-bounded deployment at 1:100 imbalance, and why the order of moves matters.

## Sources

- https://imbalanced-learn.org/stable/
- https://imbalanced-learn.org/stable/user_guide.html
- https://imbalanced-learn.org/stable/over_sampling.html
- https://imbalanced-learn.org/stable/under_sampling.html
- https://imbalanced-learn.org/stable/combine.html
- https://imbalanced-learn.org/stable/common_pitfalls.html
- https://imbalanced-learn.org/stable/references/generated/imblearn.pipeline.Pipeline.html
- https://imbalanced-learn.org/stable/references/generated/imblearn.over_sampling.RandomOverSampler.html
- https://imbalanced-learn.org/stable/references/generated/imblearn.over_sampling.SMOTE.html
- https://imbalanced-learn.org/stable/references/generated/imblearn.over_sampling.ADASYN.html
- https://imbalanced-learn.org/stable/references/generated/imblearn.over_sampling.BorderlineSMOTE.html
- https://imbalanced-learn.org/stable/references/generated/imblearn.under_sampling.RandomUnderSampler.html
- https://imbalanced-learn.org/stable/references/generated/imblearn.combine.SMOTEENN.html
- https://imbalanced-learn.org/stable/references/generated/imblearn.combine.SMOTETomek.html
- https://scikit-learn.org/stable/modules/generated/sklearn.metrics.matthews_corrcoef.html
- https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html
- https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_recall_curve.html
- https://scikit-learn.org/stable/modules/generated/sklearn.metrics.fbeta_score.html
- https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html
- https://scikit-learn.org/stable/modules/generated/sklearn.utils.class_weight.compute_class_weight.html
- https://scikit-learn.org/stable/modules/generated/sklearn.calibration.CalibratedClassifierCV.html
- https://arxiv.org/abs/1106.1813
- https://arxiv.org/abs/1708.02002

## Next Module

The next module in this Tier-2 sequence is **Module 2.2: Interpretability and Failure Slicing**, covering SHAP, LIME, PDP/ICE, permutation importance, and failure slicing for diagnosing where a model is wrong. It ships next in Phase 3 of [issue #677](https://github.com/kube-dojo/kube-dojo.github.io/issues/677); the link in this section will go live when that PR lands.
