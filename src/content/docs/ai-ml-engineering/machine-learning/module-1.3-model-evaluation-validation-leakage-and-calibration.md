---
title: "Model Evaluation, Validation, Leakage & Calibration"
description: "Design honest evaluation pipelines: CV splitter selection, a taxonomy of leakage, classification and regression metric trade-offs, and probability calibration with Platt scaling and isotonic regression."
slug: ai-ml-engineering/machine-learning/module-1.3-model-evaluation-validation-leakage-and-calibration
sidebar:
  order: 3
---

> **AI/ML Engineering Track** | Complexity: `[MEDIUM]` | Time: 5-6 hours
> **Prerequisites**: Module 1.1, `Pipeline`, `ColumnTransformer`, `cross_validate`, `train_test_split`, and comfortable NumPy/pandas.

## Learning Outcomes

By the end of this module, a practitioner will be able to:

1. **Design** a cross-validation strategy for tabular, grouped, and time-series data without leakage by selecting the right `model_selection` splitter and arranging it correctly inside a `Pipeline`.
2. **Detect** five or more taxonomic leakage failure modes - preprocessing, target, group, temporal, and threshold/metric leakage - by reading existing pipelines and naming the contaminated statistic.
3. **Evaluate** a candidate metric for a problem given class balance, business cost, and threshold sensitivity, and explain why ROC-AUC, PR-AUC, log-loss, and Brier can rank the same models differently.
4. **Compare** Platt scaling versus isotonic regression for a miscalibrated classifier and choose between them based on dataset size, monotonicity assumptions, and the shape of the empirical reliability curve.
5. **Implement** an end-to-end calibration workflow using `CalibratedClassifierCV` and verify it with a reliability diagram and Brier/log-loss diagnostics.

These outcomes extend Module 1.1. Module 1.1 taught the sklearn estimator contract. This module teaches the evaluation contract around it. The difference matters. A model can obey the API perfectly and still report a score that is not honest. That happens when the split is wrong, the metric asks the wrong question, or the probabilities mean something different from what the downstream system assumes.

## Why This Module Matters

The scikit-learn common pitfalls guide defines data leakage as using information during model building that would not be available at prediction time. It also states the practical consequence: performance estimates become overly optimistic, and the model performs worse on genuinely novel data. The official recommendation is direct: split first, fit preprocessing only on training data, and use `Pipeline` so cross-validation and hyperparameter tuning apply the correct `fit` and `transform` calls
to the correct rows. That is the starting point, not the finish line. Leakage is not only `StandardScaler.fit_transform(X)` before a split. It is also a target encoder that computes category means from validation labels. It is an oversampler that duplicates minority-class examples before folds are created. It is a patient identifier appearing in both train and validation folds. It is a random shuffle on a forecasting problem where future rows explain past rows. It is tuning a classification
threshold on the test set and then reporting that same test score as final evidence. It is selecting the calibration set only after seeing which split makes a model look good. The shape is always the same. Some statistic learned from data outside the permitted training scope influences either the fitted model, the selected model, the selected threshold, or the reported metric. This module gives you names for those failures. Names make reviews sharper. Instead of saying "this feels suspicious",
you can say "the validation fold contaminates the scaling mean" or "the group boundary is broken". That is the difference between general caution and an evaluation discipline.

## Section 1: The Test Set Is Touched Once

The simplest honest split has three functions. Training data fits model parameters. Validation data chooses model settings. Test data estimates final generalization after the choice has already been made.

```
All labeled data
│
├── train       fit weights, trees, coefficients, scaler means
├── validation  choose hyperparameters, threshold, calibration method
└── test        final estimate, read once at the end
```

The test set is not a debugging surface. It is not a leaderboard. It is not where thresholds are tuned. It is not where feature choices are compared. Every time the test score changes your decision, test information becomes part of model selection. That is leakage through human iteration rather than through code. The scikit-learn cross-validation guide makes the same point when it warns that tuning estimator settings against the test set leaks knowledge about that test set into the
model-selection process.

### A Three-Way Split in Code

The following example uses generated toy data and keeps the functions separate. The first split creates a final test set. The second split divides the remaining development data into train and validation.

```python
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    log_loss,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

X, y = make_classification(
    n_samples=1200,
    n_features=12,
    n_informative=6,
    weights=[0.9, 0.1],
    random_state=0,
)

X_dev, X_test, y_dev, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    stratify=y,
    random_state=0,
)

X_train, X_valid, y_train, y_valid = train_test_split(
    X_dev,
    y_dev,
    test_size=0.25,
    stratify=y_dev,
    random_state=1,
)

model = Pipeline([
    ("scale", StandardScaler()),
    ("clf", LogisticRegression(max_iter=1000)),
])

model.fit(X_train, y_train)
valid_proba = model.predict_proba(X_valid)[:, 1]

print("validation roc_auc:", roc_auc_score(y_valid, valid_proba))
print("validation pr_auc :", average_precision_score(y_valid, valid_proba))
print("validation logloss:", log_loss(y_valid, valid_proba))

# Only after the workflow is frozen:
test_proba = model.predict_proba(X_test)[:, 1]
print("final test roc_auc:", roc_auc_score(y_test, test_proba))
```

The validation numbers are allowed to influence design. The final test number is evidence, not a steering wheel. If it surprises you, you do not keep tuning against it. You write down the surprise, return to the development protocol, and reserve a new final evaluation only when the experimental question has changed enough to justify new held-out evidence.

### When Cross-Validation Replaces a Separate Validation Set

A fixed validation set is easy to reason about. It is also sample-inefficient. The cross-validation guide explains the usual tradeoff: a separate validation split reduces the amount of data available for learning, and results can depend on one random partition. Cross-validation solves this inside the development data. The test set still remains outside the loop.

```
Outer holdout:

development data                                  final test
┌──────────────────────────────────────────────┐  ┌─────────┐
│ CV fold 1: train train train train validate  │  │ untouched│
│ CV fold 2: train train train validate train  │  │ once     │
│ CV fold 3: train train validate train train  │  │ at end   │
│ CV fold 4: train validate train train train  │  │         │
│ CV fold 5: validate train train train train  │  │         │
└──────────────────────────────────────────────┘  └─────────┘
```

Use cross-validation when you need reliable model selection and the data is not large enough to afford a single validation split. Use a fixed validation set when the evaluation unit is naturally temporal, grouped, or operationally fixed. Use nested cross-validation when the project needs an unbiased estimate of a full model-selection procedure and a single final test set is not available. For most applied pipelines, the practical pattern
is:

1. Split off a final test set once.
2. Run CV on the development data for model and hyperparameter selection.
3. Refit the selected workflow on the full development data.
4. Evaluate once on the final test set.

The key word is workflow. If preprocessing, feature selection, resampling, threshold tuning, or calibration are part of selection, they belong inside the selection protocol.

## Section 2: When KFold Lies to You

`KFold` is honest only when rows are exchangeable enough for the problem. That assumption is stronger than it sounds. The cross-validation guide states the usual iid assumption and then warns that practical data often has time dependence or group structure. If rows are generated by patients, users, sessions, stores, devices, or time windows, a random fold can look statistically tidy while violating the way the model will be used.

### Splitter Decision Table

| Splitter | Use when | What it preserves | What goes wrong if misused |
|---|---|---|---|
| `KFold` | Regression or balanced classification with independent rows | Each row appears in one validation fold | Class imbalance or grouped repetition can make folds unrepresentative |
| `StratifiedKFold` | Classification, especially imbalanced classes | Approximate class proportions per fold | It does not prevent the same group from appearing in train and validation |
| `GroupKFold` | Multiple rows share an entity that must stay together | Group disjointness | Class proportions can be skewed when groups carry different label rates |
| `StratifiedGroupKFold` | Classification with both group boundaries and imbalance | Group disjointness plus approximate class balance | It may still struggle when group sizes or label distributions are extreme |
| `TimeSeriesSplit` | Ordered observations where future data must not train past predictions | Forward-only training windows | Randomized CV trains on future rows and validates on past rows |

### KFold Timeline

```
KFold on iid rows:

row order:  0  1  2  3  4  5  6  7  8  9
fold A:    [V][V][T][T][T][T][T][T][T][T]
fold B:    [T][T][V][V][T][T][T][T][T][T]
fold C:    [T][T][T][T][V][V][T][T][T][T]
fold D:    [T][T][T][T][T][T][V][V][T][T]
fold E:    [T][T][T][T][T][T][T][T][V][V]

T = training row, V = validation row
```

That is fine when row order carries no meaning. It is wrong when row order is time. It is also wrong when adjacent rows are duplicate measurements from the same entity.

### GroupKFold Keeps Entities Apart

```
Rows:       r0 r1 r2 r3 r4 r5 r6 r7 r8 r9
Group ID:   A  A  B  B  C  C  D  D  E  E

fold 1:    [V][V][T][T][T][T][T][T][T][T]  validation groups: A
fold 2:    [T][T][V][V][T][T][T][T][T][T]  validation groups: B
fold 3:    [T][T][T][T][V][V][T][T][T][T]  validation groups: C
```

The important invariant is not equal row counts. The invariant is entity separation. If the same patient, user, session, device, or household appears in both train and validation, the validation fold may test recognition instead of generalization. For imbalanced classification with groups, prefer `StratifiedGroupKFold` when feasible. It tries to preserve class proportions while keeping groups intact, which is exactly the double constraint described in the sklearn cross-validation guide.

### TimeSeriesSplit Moves Forward Only

```
TimeSeriesSplit:

time:      t0 t1 t2 t3 t4 t5 t6 t7 t8 t9
fold 1:   [T][T][T][V][.][.][.][.][.][.]
fold 2:   [T][T][T][T][V][.][.][.][.][.]
fold 3:   [T][T][T][T][T][V][.][.][.][.]
fold 4:   [T][T][T][T][T][T][V][.][.][.]

T = past used for training
V = next future block used for validation
. = not used in that fold
```

The guide describes `TimeSeriesSplit` as a variation where successive training sets are supersets of earlier ones. That matches many forecasting and monitoring workflows. It does not magically fix features that themselves peek into the future. A rolling mean computed with future rows is still temporal leakage, even if the splitter is correct.

### Worked Example: Choosing a Splitter

```python
import numpy as np
from sklearn.model_selection import (
    GroupKFold,
    KFold,
    StratifiedGroupKFold,
    StratifiedKFold,
    TimeSeriesSplit,
)

X = np.arange(20).reshape(10, 2)
y = np.array([0, 0, 1, 1, 0, 0, 1, 1, 0, 1])
groups = np.array(["u1", "u1", "u2", "u2", "u3", "u3", "u4", "u4", "u5", "u5"])

splitters = {
    "iid_regression_or_balanced": KFold(n_splits=5),
    "imbalanced_classification": StratifiedKFold(n_splits=5, shuffle=True, random_state=0),
    "grouped": GroupKFold(n_splits=5),
    "grouped_and_imbalanced": StratifiedGroupKFold(n_splits=5),
    "time_ordered": TimeSeriesSplit(n_splits=3),
}

for name, splitter in splitters.items():
    if name in {"grouped", "grouped_and_imbalanced"}:
        first_train, first_valid = next(splitter.split(X, y, groups=groups))
    else:
        first_train, first_valid = next(splitter.split(X, y))
    print(name, "train:", first_train, "valid:", first_valid)
```

> **Pause and predict** - You have clickstream rows where each user can contribute hundreds of events, and the label is whether that user later churned. Which splitter is the first one you should consider? (Answer: a group-aware splitter such as `GroupKFold`, or `StratifiedGroupKFold` if class balance is also a concern, because the same user must not span train and validation.)

The pause question is not about syntax. It is about identifying the evaluation unit. Rows are not always the unit that must generalize. Sometimes the unit is a user. Sometimes it is a future week. Sometimes it is a manufacturing lot. When the unit changes, the splitter changes.

## Section 3: A Taxonomy of Leakage

Leakage is easier to detect when you name the contaminated statistic. Ask one question: what information is this line learning, and would that information be available at prediction time? If the answer is no, you have a leak.

### Preprocessing Leakage

Preprocessing leakage occurs when a transformation learns statistics from validation or test rows. The common pitfalls guide uses preprocessing and feature selection as the canonical examples. The same rule applies to scaling, imputation, PCA, feature selection, discretization, and any learned transformer.

```python
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

X, y = make_classification(n_samples=500, n_features=8, random_state=0)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)  # leaked: mean_ and scale_ used all rows

X_train, X_test, y_train, y_test = train_test_split(
    X_scaled,
    y,
    test_size=0.2,
    stratify=y,
    random_state=0,
)

model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)
print(model.score(X_test, y_test))
```

The contaminated statistics are `StandardScaler.mean_` and `StandardScaler.scale_`. The fix is the Module 1.1 pattern: put the scaler inside a `Pipeline`.

```python
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

X, y = make_classification(n_samples=500, n_features=8, random_state=0)
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    stratify=y,
    random_state=0,
)

model = Pipeline([
    ("scale", StandardScaler()),
    ("clf", LogisticRegression(max_iter=1000)),
])

model.fit(X_train, y_train)
print(model.score(X_test, y_test))
```

Inside cross-validation, the same construction fits the scaler separately for each training fold. That is why `Pipeline` is not style. It is a boundary enforcement mechanism.

### Target Leakage

Target leakage occurs when the feature construction uses labels, outcomes, or post-outcome information unavailable at prediction time. A target encoder is the classic legitimate-but-dangerous example. It replaces a category with a statistic derived from `y`. That can be useful only if the statistic is learned inside the training fold.

```python
import pandas as pd

df = pd.DataFrame({
    "city": ["A", "A", "B", "B", "C", "C", "D", "D"],
    "clicked": [1, 1, 0, 0, 1, 0, 0, 1],
})

city_rate = df.groupby("city")["clicked"].mean()
df["city_encoded"] = df["city"].map(city_rate)

print(df)
```

The contaminated statistic is `city_rate`. It was computed from every label before any split. If a validation row's own label contributes to its encoded feature, the validation score is no longer testing unseen behavior. In Module 1.4, you will treat target encoding as a feature-engineering method. Here the rule is simpler: any transformer that reads `y` must be cross-validation-aware and must be fitted only on the training portion of each fold.

### Oversampling Leakage

Oversampling before the split is leakage because duplicated or synthetic minority examples can cross fold boundaries. Even without an external imbalanced-learning library, the shape is visible.

```python
import numpy as np

X = np.array([
    [0.0, 0.0],
    [0.1, 0.0],
    [1.0, 1.0],
    [1.1, 1.0],
    [1.2, 1.1],
])
y = np.array([1, 1, 0, 0, 0])

minority_idx = np.flatnonzero(y == 1)
X_oversampled = np.concatenate([X, X[minority_idx]], axis=0)
y_oversampled = np.concatenate([y, y[minority_idx]], axis=0)

print(X_oversampled)
print(y_oversampled)
```

If you split after this operation, a copied minority example can be in training while its duplicate is in validation. The contaminated statistic is the sampling distribution, and sometimes the duplicated row itself. The correct pattern is to place resampling inside the fold-specific training workflow. With plain sklearn, that usually means class weights, threshold choice, or a model that can handle imbalance. With external resampling libraries, it means their pipeline object must participate
inside CV rather than being run once on the full dataset.

### Group Leakage

Group leakage happens when related rows cross fold boundaries. The model may learn a fingerprint rather than a generalizable rule.

```python
import numpy as np
from sklearn.model_selection import GroupKFold, KFold

X = np.arange(12).reshape(6, 2)
y = np.array([0, 0, 1, 1, 0, 1])
groups = np.array(["p1", "p1", "p2", "p2", "p3", "p3"])

kfold = KFold(n_splits=3)
bad_train, bad_valid = next(kfold.split(X, y))
print("KFold validation groups:", groups[bad_valid])

group_cv = GroupKFold(n_splits=3)
good_train, good_valid = next(group_cv.split(X, y, groups=groups))
print("GroupKFold validation groups:", groups[good_valid])
print("train groups:", groups[good_train])
```

The contaminated statistic is entity identity. The fix is to pass `groups` to a group-aware splitter and use that splitter consistently in `cross_validate`, `GridSearchCV`, and calibration workflows.

### Temporal Leakage

Temporal leakage occurs when training uses information from the future. Random shuffling is the obvious cause. Feature construction can be just as dangerous.

```python
import pandas as pd

df = pd.DataFrame({
    "day": [1, 2, 3, 4, 5, 6],
    "sales": [10, 12, 11, 15, 16, 14],
})

df["bad_centered_mean"] = df["sales"].rolling(window=3, center=True).mean()
df["good_past_mean"] = df["sales"].shift(1).rolling(window=3).mean()

print(df)
```

The contaminated statistic is the centered rolling mean. For day 3, it can include day 4. That feature is not available when predicting day 3. `TimeSeriesSplit` handles the fold order; it does not inspect your feature logic.

### Threshold and Metric Leakage

Classification models often output scores or probabilities. Business decisions often require a threshold. Choosing the threshold on the test set leaks test labels into the final decision.

```python
import numpy as np
from sklearn.metrics import f1_score

y_test = np.array([0, 0, 0, 1, 1, 1])
p_test = np.array([0.05, 0.20, 0.45, 0.35, 0.70, 0.95])

for threshold in [0.25, 0.50, 0.75]:
    pred = (p_test >= threshold).astype(int)
    print(threshold, f1_score(y_test, pred))
```

This code is fine for a classroom demonstration. It is not fine as a final evaluation protocol. The contaminated statistic is the selected threshold. Tune thresholds on validation data or inside cross-validation. Then read the test metric once using the frozen threshold.

### Reporting Train Metrics as Generalization

Training metrics answer "did the estimator fit the data it saw?" They do not answer "will the estimator generalize?" `cross_validate(return_train_score=True)` is useful because it shows the gap. It is not permission to report train scores as deployment evidence.

```python
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_validate

X, y = make_classification(n_samples=600, n_features=20, random_state=0)
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
model = RandomForestClassifier(random_state=0)

scores = cross_validate(
    model,
    X,
    y,
    cv=cv,
    scoring="roc_auc",
    return_train_score=True,
)

print("train:", scores["train_score"].mean())
print("valid:", scores["test_score"].mean())
```

The contaminated claim is the report, not the model. A train score can diagnose overfitting. It cannot certify generalization.

## Section 4: Metrics Ask Different Questions

Metrics are not interchangeable labels for "model quality". They encode different claims. Some require a hard class prediction. Some evaluate ranking. Some evaluate probabilities. Some are sensitive to class prevalence. Some ignore calibration entirely.

### Classification Metric Decision Table

| Metric | Input | Threshold-dependent? | Best use | Main trap |
|---|---|---:|---|---|
| Accuracy | class labels | Yes | Balanced classes with symmetric mistake costs | Imbalanced data can look strong at the no-skill rate |
| Precision | class labels | Yes | False positives are expensive | Can be improved by predicting fewer positives |
| Recall | class labels | Yes | False negatives are expensive | Can be improved by predicting more positives |
| F1 | class labels | Yes | Need a single precision/recall compromise | Ignores true negatives and hides threshold choice |
| MCC | class labels | Yes | Imbalanced binary or multiclass classification | Still depends on the chosen threshold |
| ROC-AUC | scores | No | Ranking positives above negatives across thresholds | Can look strong when early precision is poor |
| PR-AUC / AP | scores | No | Rare positives where positive-class retrieval matters | Baseline changes with positive prevalence |
| Log-loss | probabilities | No fixed threshold | Probabilistic prediction with harsh penalty for confident errors | A ranking-good model can lose if probabilities are overconfident |
| Brier | probabilities | No fixed threshold | Squared probability error and calibration diagnostics | Lower Brier is not purely "better calibration" unless decomposed |

Accuracy is the most intuitive metric and the easiest to misuse. If the positive class rate is 5%, a classifier that always predicts negative has 95% accuracy. That no-skill rate must be the first comparison, not an afterthought. The sklearn model-evaluation guide includes a large metrics catalog because no single metric answers every operational question.

### Worked Example: Same Labels, Different Story

```python
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
)

y_true = np.array([0, 0, 0, 0, 0, 0, 0, 0, 1, 1])
y_pred = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1])

print("accuracy :", accuracy_score(y_true, y_pred))
print("precision:", precision_score(y_true, y_pred))
print("recall   :", recall_score(y_true, y_pred))
print("f1       :", f1_score(y_true, y_pred))
print("mcc      :", matthews_corrcoef(y_true, y_pred))
```

The model gets most rows right. It also misses half the positives. Whether that is acceptable is not a metric question. It is a problem-definition question.

### ROC-AUC and PR-AUC Can Disagree

ROC-AUC asks how well positives are ranked above negatives across thresholds. Average precision summarizes precision-recall behavior and is especially sensitive to the quality of the top-ranked positive predictions. The sklearn guide notes that average precision with random predictions equals the fraction of positive samples. That makes PR-AUC much more prevalence-aware than ROC-AUC. Here is a small example where two score vectors answer the ranking question differently from the early-retrieval
question.

```python
import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

y_true = np.array([1, 1, 0, 0, 0, 0, 0, 0])

model_a = np.array([0.90, 0.55, 0.80, 0.70, 0.60, 0.40, 0.30, 0.20])
model_b = np.array([0.70, 0.69, 0.68, 0.67, 0.66, 0.65, 0.10, 0.09])

for name, scores in {"A": model_a, "B": model_b}.items():
    print(
        name,
        "roc_auc=",
        round(roc_auc_score(y_true, scores), 3),
        "average_precision=",
        round(average_precision_score(y_true, scores), 3),
    )
```

One model can rank the positive class acceptably in pairwise terms while placing too many negatives near the top of the list. Another can do better at early retrieval for the positives that matter most. That is why rare-event triage often starts with PR-AUC and precision/recall at an operating threshold rather than accuracy.

> **Pause and predict** - A classifier for a 2% positive class reports 98% accuracy and no other metrics. What is the first diagnostic question? (Answer: compare it to the no-skill classifier that always predicts the majority class, then inspect recall, precision, PR-AUC, and the confusion matrix at the chosen threshold.)

### Log-Loss and Brier Care About Probability Quality

ROC-AUC does not care whether a positive row receives 0.51 or 0.99 if the ranking is unchanged. Log-loss and Brier do. Log-loss penalizes confident wrong probabilities sharply. Brier is the mean squared error between predicted probabilities and outcomes in binary classification. The sklearn calibration guide warns that proper scoring rules such as log-loss and Brier combine reliability, resolution, and uncertainty. So a lower Brier score is useful, but it is not a calibration proof by itself
unless you decompose or inspect the reliability curve.

```python
import numpy as np
from sklearn.metrics import brier_score_loss, log_loss

y_true = np.array([0, 0, 1, 1])
calm = np.array([0.20, 0.30, 0.70, 0.80])
overconfident = np.array([0.01, 0.99, 0.99, 0.99])

for name, proba in {"calm": calm, "overconfident": overconfident}.items():
    print(name, "log_loss:", round(log_loss(y_true, proba), 3))
    print(name, "brier   :", round(brier_score_loss(y_true, proba), 3))
```

The overconfident model is punished hard for the confident wrong second row. That is the behavior you want when probabilities drive downstream risk.

## Section 5: Regression Metrics Penalize Different Errors

Regression evaluation has the same problem in quieter clothing. MAE, RMSE, MAPE, and R2 are not synonyms. They encode different error preferences.

| Metric | What it measures | Penalizes | Good when | Trap |
|---|---|---|---|---|
| MAE | Mean absolute error | Linear error size | You want errors in target units and robustness to outliers | Does not punish rare large misses as strongly as RMSE |
| RMSE | Square root of mean squared error | Large errors strongly | Large misses are disproportionately costly | Can be dominated by outliers |
| MAPE | Relative absolute error | Error relative to target magnitude | Stakeholders reason in relative terms | Breaks or explodes near zero; sklearn returns relative values, not 0-100 percentages |
| R2 | Variance explained relative to a constant baseline | Poor explanatory fit | You need a baseline-relative score | Can be negative when the model is worse than the constant mean predictor |

The sklearn guide describes R2 as the proportion of target variance explained by the independent variables. It also notes that the best value is 1.0 and lower is worse. A negative R2 is not a formatting bug. It means the model is worse than the baseline implied by predicting the target mean on the evaluated data.

### Worked Example: Same Predictions, Different Penalties

```python
import numpy as np
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    r2_score,
)

y_true = np.array([100.0, 110.0, 120.0, 130.0])
model_a = np.array([100.0, 111.0, 119.0, 180.0])
model_b = np.array([112.0, 112.0, 112.0, 112.0])

for name, pred in {"A": model_a, "B": model_b}.items():
    print(name, "mae :", round(mean_absolute_error(y_true, pred), 3))
    print(name, "rmse:", round(mean_squared_error(y_true, pred) ** 0.5, 3))
    print(name, "mape:", round(mean_absolute_percentage_error(y_true, pred), 3))
    print(name, "r2  :", round(r2_score(y_true, pred), 3))
```

Model A is almost perfect on most rows and badly wrong on one. Model B is mediocre everywhere. MAE and RMSE will not rank those patterns the same in every dataset. That is not a problem with the functions. It is the point of having different functions.

### When MAPE Breaks

MAPE divides by the true target magnitude, with an epsilon guard in sklearn to avoid undefined division. That makes it scale-relative. It also makes it unstable when target values are zero or near zero.

```python
from sklearn.metrics import mean_absolute_percentage_error

y_true = [0.0, 1.0, 10.0]
y_pred = [0.1, 1.2, 12.0]

print(mean_absolute_percentage_error(y_true, y_pred))
```

The output is finite because sklearn guards the denominator. The interpretation is still usually poor. When zeros are meaningful, consider MAE, RMSE, pinball loss for quantiles, or a transformed target that matches the operational question.

## Section 6: Calibration Is Not Ranking

Calibration asks a probability question. Among samples where the model says 0.8, do about 80% actually belong to the positive class? That is different from ranking. A model can have strong ROC-AUC and still produce probabilities that are too extreme or too timid. The sklearn calibration guide defines a well-calibrated classifier in exactly this confidence-frequency sense. It also explains reliability diagrams: bin predicted probabilities on the x-axis and plot the fraction of positives in each
bin on the y-axis.

```
Reliability diagram:

fraction
positive  1.0 |                         perfect calibration
              |                       /
          0.8 |                    x /
              |                  x  /
          0.6 |               x    /
              |             x     /
          0.4 |          x       /
              |       x         /
          0.2 |    x           /
              | x             /
          0.0 +----------------------------
              0.0   0.2   0.4   0.6   0.8   1.0
                    mean predicted probability
```

Points below the diagonal are overconfident for the positive class. Points above the diagonal are underconfident. The histogram under many reliability plots matters because a smooth-looking line based on empty bins is not evidence.

### Platt Scaling Versus Isotonic Regression

`CalibratedClassifierCV` supports `method="sigmoid"` and `method="isotonic"`. Sigmoid calibration is often called Platt scaling. It fits a logistic mapping from raw classifier scores to probabilities. It is low-capacity and tends to be safer with smaller calibration sets. Isotonic regression fits a non-parametric monotone step function. It can correct more general monotonic distortions. The sklearn calibration guide warns that isotonic is more prone to overfitting, especially on small datasets,
and states that isotonic tends to perform as well as or better than sigmoid when there is enough data, roughly more than 1000 samples.

| Method | sklearn value | Shape assumption | Strength | Risk |
|---|---|---|---|---|
| Platt scaling | `method="sigmoid"` | S-shaped correction | Lower variance, preserves ranking as a strictly monotonic transform | Cannot fix arbitrary calibration curve shapes |
| Isotonic regression | `method="isotonic"` | Monotone non-decreasing correction | More flexible; can fix broader monotonic distortions | Higher overfitting risk, introduces ties that can affect AUC |

Use sigmoid when the calibration set is small, the reliability curve looks roughly S-shaped, or you need to preserve ranking metrics as much as possible. Use isotonic when you have enough calibration data and the empirical reliability curve shows a monotonic but non-sigmoid distortion. Do not choose the method after reading the final test set. That is calibration-set leakage.

### CalibratedClassifierCV Without Prefit Leakage

`CalibratedClassifierCV` uses cross-validation to obtain unbiased predictions for fitting calibrators. With `ensemble=True`, it trains a clone of the base estimator on each training fold, predicts on that fold's held-out data, and fits a calibrator to those predictions. With `ensemble=False`, it uses cross-validated predictions to train one calibrator, then fits the base estimator on all data. The documentation also describes calibrating an already fitted estimator with `FrozenEstimator`, while
placing responsibility on the user to keep model-fitting data disjoint from calibration data. The safest beginner workflow is to let `CalibratedClassifierCV` own the internal CV.

```python
import numpy as np
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.datasets import make_classification
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold, train_test_split

X, y = make_classification(
    n_samples=2000,
    n_features=20,
    n_informative=8,
    weights=[0.85, 0.15],
    random_state=0,
)

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    stratify=y,
    random_state=0,
)

base = HistGradientBoostingClassifier(random_state=0)
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)

calibrated = CalibratedClassifierCV(
    estimator=base,
    method="sigmoid",
    cv=cv,
    ensemble=True,
)

calibrated.fit(X_train, y_train)
proba = calibrated.predict_proba(X_test)[:, 1]

fraction_positive, mean_predicted = calibration_curve(
    y_test,
    proba,
    n_bins=10,
    strategy="uniform",
)

print("roc_auc:", round(roc_auc_score(y_test, proba), 3))
print("brier  :", round(brier_score_loss(y_test, proba), 3))
print("logloss:", round(log_loss(y_test, proba), 3))
print("reliability points:")
for x_value, y_value in zip(mean_predicted, fraction_positive):
    print(round(x_value, 3), round(y_value, 3))
```

This code prints reliability-curve coordinates. In a notebook, plot `mean_predicted` on the x-axis and `fraction_positive` on the y-axis with the diagonal `y=x`. The diagram matters more than a single scalar when the task is calibration diagnosis.

### Expected Calibration Error

Expected Calibration Error, often abbreviated ECE, summarizes the average gap between predicted confidence and observed frequency across bins. It is not a core sklearn metric function, but it is easy to compute from bin assignments. Use it as a diagnostic, not as the only truth. Different binning strategies can produce different values.

```python
import numpy as np


def expected_calibration_error(y_true, y_proba, n_bins=10):
    y_true = np.asarray(y_true)
    y_proba = np.asarray(y_proba)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0

    for left, right in zip(edges[:-1], edges[1:]):
        if right == 1.0:
            in_bin = (y_proba >= left) & (y_proba <= right)
        else:
            in_bin = (y_proba >= left) & (y_proba < right)
        if not np.any(in_bin):
            continue
        bin_weight = in_bin.mean()
        confidence = y_proba[in_bin].mean()
        accuracy = y_true[in_bin].mean()
        ece += bin_weight * abs(confidence - accuracy)

    return ece

y_true = np.array([0, 0, 1, 1, 1, 0])
y_proba = np.array([0.05, 0.20, 0.55, 0.80, 0.90, 0.60])
print(round(expected_calibration_error(y_true, y_proba, n_bins=3), 3))
```

ECE compresses a curve into one number. Compression is useful for dashboards. It can hide whether miscalibration happens at low, middle, or high probabilities. Keep the reliability diagram.

### Brier Decomposition in Plain Language

The calibration guide notes that Brier and log-loss are strictly proper scoring rules but mix several effects. For Brier, the classic decomposition
separates:

| Term | Plain meaning | Interpretation |
|---|---|---|
| Reliability | Are predicted probabilities close to observed frequencies? | Calibration error |
| Resolution | Do different bins have meaningfully different event rates? | Discrimination/refinement |
| Uncertainty | How inherently variable is the outcome? | Dataset base-rate difficulty |

This is why a model can have a lower Brier score without being better calibrated. It may have better resolution. It may separate easy positives and negatives so well that the total score improves despite local calibration defects. For calibration work, report Brier and log-loss, but inspect the reliability curve and the binned gaps.

### Calibration Workflow Checklist

1. Split off final test data before model selection.
2. Choose the model family and metric on development data.
3. Choose the calibration method using training or validation evidence, not final test results.
4. Fit `CalibratedClassifierCV` with a splitter that matches the data structure.
5. Evaluate probability metrics and reliability curves on held-out data.
6. Freeze the threshold only after probabilities are calibrated, unless the downstream system consumes probabilities directly.

> **Pause and predict** - A model has ROC-AUC 0.92, but in the 0.8 probability bin only about half the examples are positive. Is the model "good"? (Answer: it may rank examples well, but it is overconfident and poorly calibrated in that probability region. Calibration is a different property from ranking.)

## Did You Know?

1. The scikit-learn cross-validation guide explicitly warns that tuning hyperparameters on the test set lets knowledge about that test set leak into the model-selection process: https://scikit-learn.org/stable/modules/cross_validation.html
2. The common pitfalls guide recommends `Pipeline` because it ensures the appropriate method is performed on the correct data subset during fitting and prediction: https://scikit-learn.org/stable/common_pitfalls.html
3. `CalibratedClassifierCV` can fit sigmoid or isotonic calibrators, and its cross-validation procedure is designed so calibrators are trained from unbiased predictions: https://scikit-learn.org/stable/modules/calibration.html
4. The calibration example in the sklearn gallery compares classifiers with reliability curves and probability histograms, which is why calibration review should include both curve shape and bin support: https://scikit-learn.org/stable/auto_examples/calibration/plot_calibration_curve.html

## Common Mistakes

| Mistake | Contaminated statistic | Why it fails | Safer pattern |
|---|---|---|---|
| Calling `StandardScaler.fit_transform(X)` before splitting | Feature means and scales | Validation/test rows influence preprocessing | Put `StandardScaler` inside `Pipeline` |
| Fitting target encoding before CV | Category target means | A row's label can influence its own validation feature | Fit encoders inside a CV-aware pipeline |
| Oversampling before train/test split | Sampling distribution and duplicated examples | Copies or synthetic neighbors can cross split boundaries | Resample inside training folds or use class weights |
| Using `KFold` when the same entity appears many times | Entity identity | Model recognizes groups instead of generalizing | Use `GroupKFold` or `StratifiedGroupKFold` |
| Randomly shuffling time-series rows | Future observations | Model trains on future information | Use `TimeSeriesSplit` and past-only features |
| Tuning threshold on the final test set | Selected threshold | Test labels become part of model selection | Tune threshold on validation/CV data |
| Reporting train metrics as deployment evidence | Evaluation claim | The model is scored on rows it already saw | Report held-out or CV metrics, with train scores only as diagnostics |
| Selecting a calibration set after seeing test results | Calibration split choice | Test results influence probability correction | Reserve calibration data before final testing |

## Quiz

### 1. A pipeline scores well with random `KFold`, but each customer appears in many rows.

What do you check first?

<details>
<summary>Answer</summary>

Check whether the same customer ID appears in both training and validation folds. If it does, this is group leakage. Switch to `GroupKFold` or `StratifiedGroupKFold` and pass the customer ID as `groups`. The earlier score may have measured customer recognition rather than generalization to unseen customers.

</details>

### 2. A model for a rare event reports 96% accuracy and no confusion matrix.

What is the first metric critique?

<details>
<summary>Answer</summary>

Compare the score to the no-skill majority-class baseline. If the positive class is rare, high accuracy may mean the model predicts almost everything negative. Ask for precision, recall, F1 or MCC at the chosen threshold, plus PR-AUC or average precision from scores.

</details>

### 3. A teammate scales the full matrix, then calls `cross_validate`.

Why does CV not save the evaluation?

<details>
<summary>Answer</summary>

The fold splitter runs after the scaling statistic has already been learned from all rows. Each validation fold influenced `mean_` and `scale_`. The scaler must be inside a `Pipeline` so each fold fits preprocessing only on that fold's training rows.

</details>

### 4. A time-series model uses `TimeSeriesSplit`, but a feature is a centered rolling average.

Is the evaluation safe?

<details>
<summary>Answer</summary>

No. The splitter is forward-only, but the feature itself can include future observations. Temporal safety requires both a temporal splitter and feature logic that only uses information available at prediction time.

</details>

### 5. Two classifiers have the same ROC-AUC, but one has much worse log-loss.

What does that suggest?

<details>
<summary>Answer</summary>

Their ranking ability may be similar, but their probability estimates differ. The worse log-loss model may be overconfident on wrong examples or generally miscalibrated. Inspect Brier score, reliability curves, and the probability distribution.

</details>

### 6. Isotonic calibration improves validation Brier score on a tiny calibration set.

What risk should you name?

<details>
<summary>Answer</summary>

Isotonic regression is flexible and can overfit small calibration sets. Compare it against sigmoid calibration, inspect the reliability curve, and avoid selecting the method using the final test set.

</details>

### 7. A regression model has negative R2 but acceptable MAE.

How can both be true?

<details>
<summary>Answer</summary>

MAE reports average absolute error in target units. R2 compares the model against a constant baseline on variance explained. A model can have errors that look tolerable in units but still perform worse than predicting the evaluation-set mean.

</details>

### 8. A team calibrates a fitted model using data that was also used to train the base estimator.

What is the leakage?

<details>
<summary>Answer</summary>

The calibrator sees predictions from a model evaluated on rows it was trained on. Those predictions are biased toward the training data. Use `CalibratedClassifierCV` with internal CV, or ensure the fitted base estimator and calibration set are disjoint when using a frozen fitted estimator.

</details>

## Hands-On Exercise: Build an Honest Calibrated Classifier

You will build a complete evaluation workflow on generated toy data. The point is not to maximize a score. The point is to prove that every learned statistic belongs to the correct split.

### Setup

Use `sklearn.datasets.make_classification` to create an imbalanced binary dataset. Create at least 2000 rows, at least 15 features, and a positive class that is clearly the minority. Keep the code in one notebook or one Python file so you can rerun it from scratch.

### Step 1: Reserve the final test set

- [ ] Split once into development and final test sets with `train_test_split`.
- [ ] Use `stratify=y`.
- [ ] Do not inspect final test metrics until the workflow is frozen.
- [ ] Write down the positive-class rate in both splits and compare it to the overall rate.

### Step 2: Choose and justify the splitter

- [ ] Start with `StratifiedKFold` for ordinary imbalanced tabular data.
- [ ] Replace it with `GroupKFold` or `StratifiedGroupKFold` if you add a synthetic group ID.
- [ ] Replace it with `TimeSeriesSplit` if you reorder the toy data into a temporal simulation.
- [ ] In one paragraph, name what your splitter preserves.

### Step 3: Build the uncalibrated pipeline

- [ ] Put `StandardScaler` inside a `Pipeline`.
- [ ] Use a real sklearn classifier with `predict_proba`, such as `LogisticRegression` or `HistGradientBoostingClassifier`.
- [ ] Evaluate with `cross_validate` using at least ROC-AUC, average precision, and negative log-loss.
- [ ] If you request train scores, label them as diagnostics rather than generalization evidence.

### Step 4: Calibrate without touching the final test set

- [ ] Wrap the base classifier with `CalibratedClassifierCV`.
- [ ] Run `method="sigmoid"` first.
- [ ] Try `method="isotonic"` only as a comparison, and decide based on development evidence.
- [ ] Keep the `cv` strategy aligned with your data structure.

### Step 5: Draw the reliability diagram

- [ ] Use `calibration_curve` to compute `fraction_positive` and `mean_predicted`.
- [ ] Plot the diagonal reference line.
- [ ] Add a histogram or count table for predicted-probability bins.
- [ ] Explain where the model is overconfident or underconfident.

### Step 6: Report probability metrics

- [ ] Compute `brier_score_loss` on held-out data.
- [ ] Compute `log_loss` on held-out data.
- [ ] Compare these to ROC-AUC and average precision.
- [ ] Explain whether ranking quality and probability quality tell the same story.

### Step 7: Freeze a threshold

- [ ] Pick a threshold using validation or CV evidence.
- [ ] Report precision, recall, F1, MCC, and a confusion matrix at that threshold.
- [ ] Evaluate the frozen threshold once on the final test set.
- [ ] State the no-skill accuracy baseline beside the final accuracy.

### Completion Check

- [ ] No preprocessing is fitted outside a pipeline.
- [ ] No threshold is selected on the final test set.
- [ ] No calibration method is selected after reading final test metrics.
- [ ] The final report separates ranking metrics, threshold metrics, and probability metrics.
- [ ] The reliability diagram is interpreted in words, not just displayed.

## Sources

- [Cross-validation: evaluating estimator performance](https://scikit-learn.org/stable/modules/cross_validation.html)
- [Metrics and scoring: quantifying the quality of predictions](https://scikit-learn.org/stable/modules/model_evaluation.html)
- [Probability calibration](https://scikit-learn.org/stable/modules/calibration.html)
- [Common pitfalls and recommended practices](https://scikit-learn.org/stable/common_pitfalls.html)
- [Probability Calibration curves](https://scikit-learn.org/stable/auto_examples/calibration/plot_calibration_curve.html)
- [Custom refit strategy of a grid search with cross-validation](https://scikit-learn.org/stable/auto_examples/model_selection/plot_grid_search_digits.html)
- [`StratifiedKFold`](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedKFold.html)
- [`GroupKFold`](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html)
- [`StratifiedGroupKFold`](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html)
- [`TimeSeriesSplit`](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html)
- [`log_loss`](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.log_loss.html)
- [`brier_score_loss`](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html)
- [`matthews_corrcoef`](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.matthews_corrcoef.html)
- [`calibration_curve`](https://scikit-learn.org/stable/modules/generated/sklearn.calibration.calibration_curve.html)
- [`CalibratedClassifierCV`](https://scikit-learn.org/stable/modules/generated/sklearn.calibration.CalibratedClassifierCV.html)
- [On Calibration of Modern Neural Networks](https://arxiv.org/abs/1706.04599)

## Next Module

Continue to [Module 1.4: Feature Engineering & Preprocessing](module-1.4-feature-engineering-and-preprocessing/).
