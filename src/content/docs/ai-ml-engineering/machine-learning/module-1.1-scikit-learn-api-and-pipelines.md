---
title: "Scikit-learn API & Pipelines"
description: "Master the scikit-learn estimator/transformer/pipeline contract: fit/predict/transform, ColumnTransformer, model_selection splitters, custom transformers via BaseEstimator, persistence, and search-CV interfaces."
slug: ai-ml-engineering/machine-learning/module-1.1-scikit-learn-api-and-pipelines
sidebar:
  order: 1
---

> **AI/ML Engineering Track** | Complexity: Intermediate | Time: 4-5 hours
> **Prerequisites**: Comfortable Python, NumPy, pandas. No prior ML library experience required.

## Learning Outcomes

By the end of this module, a practitioner will be able to:

1. **Design** a leakage-safe preprocessing-and-modeling workflow using `Pipeline` and `ColumnTransformer` so that no validation-set statistics ever influence training.
2. **Evaluate** a candidate model with the right `model_selection` splitter (`KFold`, `StratifiedKFold`, `GroupKFold`, `TimeSeriesSplit`) for the problem's data structure, and explain why the wrong splitter silently inflates scores.
3. **Debug** a sklearn estimator's behavior by inspecting `get_params`, `set_params`, fitted attributes (the trailing-underscore convention), and the steps inside a `Pipeline`.
4. **Implement** a custom transformer that follows the estimator contract (subclassing `BaseEstimator` and `TransformerMixin`) and drops cleanly into a `Pipeline`.
5. **Compare** `GridSearchCV` versus `RandomizedSearchCV` for hyperparameter search and choose the right one based on parameter-space size and compute budget.

These outcomes are about the *workflow that wraps every algorithm*. The algorithms themselves — linear and logistic regression, decision trees, random forests, gradient boosting, naive Bayes, k-NN, SVMs, clustering, anomaly detection, dimensionality reduction — each get their own dedicated module later in this section.

## Why This Module Matters

The most expensive failure mode in applied machine learning is also the most preventable. A model trains, scores cleanly on a held-out split, and then collapses in production. The cause is rarely the algorithm. More often it is a *leak* — a preprocessing statistic that quietly peeked at test rows, an encoder that learned the target distribution before the split, a hyperparameter search that optimized against the same data used to evaluate it.

The fix is not a smarter algorithm. It is a `Pipeline`.

The scikit-learn user guide treats data leakage as a first-class workflow concern. The [cross-validation guide](https://scikit-learn.org/stable/modules/cross_validation.html) prescribes that every transformer and every estimator funnel through a single object that fits only on training rows, and that cross-validation splitters do the splitting. The [Pipeline and composite estimators guide](https://scikit-learn.org/stable/modules/compose.html) makes the same case from the composition side: a `Pipeline` is the unit of leakage-safety, not a convenience wrapper.

The "API" you are about to learn is the discipline that makes that workflow automatic instead of accidental. The same lesson reappears in subtler forms: target encoding statistics leaking into validation, oversampling applied before splitting, custom feature-engineering scripts that fit statistics on the wrong rows. None of these are algorithm bugs. They are workflow bugs, and the scikit-learn API design exists to prevent them.

The official scikit-learn documentation [user guide](https://scikit-learn.org/stable/user_guide.html) and [developer guide](https://scikit-learn.org/stable/developers/develop.html) codify this discipline as a contract. The rest of this module teaches that contract well enough that you can read any sklearn code and predict its data flow at a glance.

## Section 1: The Estimator Contract

Every learnable object in scikit-learn — every model, every preprocessor — is an **estimator**. Estimators implement a tiny, predictable interface, and once you internalize it the rest of the library becomes mechanical.

### The Five Methods

| Method | Inputs | Output | Who implements it |
|---|---|---|---|
| `fit(X, y=None)` | training data | self (mutates internal state) | every estimator |
| `predict(X)` | new data | array of predictions | predictors (classifiers, regressors) |
| `transform(X)` | data | transformed data | transformers (scalers, encoders, decomposers) |
| `score(X, y)` | data + targets | scalar score | predictors (default metric per estimator type) |
| `partial_fit(X, y=None)` | a chunk of data | self (incremental) | online-capable estimators |

A *classifier* or *regressor* implements `fit` + `predict` + `score`. A *transformer* implements `fit` + `transform`. Some estimators legitimately implement both roles — `KMeans`, for example, exposes `transform` (returning each row's distance to every cluster center) and `predict` (returning the closest cluster index). `PCA`, on the other hand, is purely a transformer; it provides `fit`, `transform`, and `inverse_transform` for reconstruction, but no `predict`. Some estimators add `predict_proba`, `decision_function`, or `inverse_transform`; those are optional and well-documented when present.

The key invariant is that **fitted state lives on the estimator**, in attributes whose names end in a trailing underscore. After calling `fit` on `LinearRegression`, you can read `coef_`, `intercept_`, and `n_features_in_`. Before `fit`, those attributes do not exist. This convention is enforced by the developer guide and is the fastest way to tell at a glance whether you are looking at a hyperparameter (no underscore, set in `__init__`) or a learned parameter (trailing underscore, set in `fit`).

> **Pause and predict** — Suppose you write `model = Ridge(alpha=1.0)` then immediately try to access `model.coef_`. What happens? Why? (Answer: `AttributeError`. `coef_` is set during `fit`. `alpha` is the hyperparameter you passed; `coef_` is the learned parameter that does not yet exist.)

### Worked Example: Reading a Fitted Estimator

```python
import numpy as np
from sklearn.linear_model import Ridge

# Toy data: y = 2 * x_0 + 3 * x_1 + noise
rng = np.random.default_rng(seed=0)
X = rng.normal(size=(200, 2))
y = 2.0 * X[:, 0] + 3.0 * X[:, 1] + rng.normal(scale=0.1, size=200)

model = Ridge(alpha=1.0)             # hyperparameters set here
print(hasattr(model, "coef_"))        # False — not fitted yet

model.fit(X, y)                       # learns from data

# Anything ending in "_" is a fitted attribute
print("coef_      :", model.coef_)        # ~[2.0, 3.0]
print("intercept_ :", model.intercept_)   # ~0.0
print("n_features_in_:", model.n_features_in_)
print("score on training:", model.score(X, y))  # default R^2
```

The trailing-underscore convention is enforced everywhere — `KMeans` exposes `cluster_centers_`, `RandomForestClassifier` exposes `feature_importances_`, `StandardScaler` exposes `mean_` and `scale_`. When you debug a misbehaving sklearn workflow, look at the trailing-underscore attributes first; they tell you what the model actually learned.

### `partial_fit`: When the Dataset Does Not Fit in Memory

A subset of estimators implement `partial_fit`, which accepts data in chunks and updates the model incrementally. This is the right interface for streaming or out-of-core workloads, and the user guide on [scaling computationally](https://scikit-learn.org/stable/user_guide.html) discusses which estimators support it. Notable examples include `SGDClassifier`, `SGDRegressor`, `PassiveAggressiveClassifier`, `MiniBatchKMeans`, and `MultinomialNB`. Calling `fit` would reset the estimator; calling `partial_fit` repeatedly accumulates state. Most batch-trained estimators (`RandomForest`, `SVC`, `LogisticRegression` with default solver) do *not* support `partial_fit` and will raise.

### `get_params` and `set_params`

Every estimator inherits two reflective methods from `BaseEstimator`:

```python
from sklearn.linear_model import LogisticRegression

clf = LogisticRegression(C=0.5, penalty="l2", max_iter=200)

# Inspect every constructor argument
clf.get_params()
# {'C': 0.5, 'penalty': 'l2', 'max_iter': 200, ...}

# Mutate a hyperparameter without reconstructing
clf.set_params(C=2.0)
clf.get_params()["C"]   # 2.0
```

Search-CV objects (`GridSearchCV`, `RandomizedSearchCV`) and pipelines lean on this contract heavily — it is how they programmatically explore a hyperparameter space without knowing anything about the underlying estimator.

## Section 2: Pipelines and the Leakage Problem

A pipeline is an estimator that chains other estimators together. The output of each step's `transform` becomes the input of the next step's `fit` (and `transform`, and `predict`). The last step is typically a final estimator (classifier or regressor); every preceding step must be a transformer.

### Why Pipelines Exist

Consider this innocent-looking code:

```python
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)            # fits on the FULL dataset
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y)

clf = LogisticRegression()
clf.fit(X_train, y_train)
print(clf.score(X_test, y_test))
```

This is a leakage bug. `StandardScaler` learned its mean and standard deviation from the entire dataset, including the rows that are about to become the test set. The test score is biased upward because the scaler has already seen the test distribution. In a small academic dataset this bias is mild; in noisy real-world data it can mask serious overfitting.

The pipeline-correct version:

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y)

pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("clf",    LogisticRegression()),
])

pipe.fit(X_train, y_train)        # scaler.fit on TRAIN only
print(pipe.score(X_test, y_test)) # scaler.transform applied to TEST
```

Now `fit` on the pipeline calls `fit_transform` on every step except the last, and `fit` on the last. `score` and `predict` call `transform` on every step except the last, and the appropriate predictor method on the last. The training statistics never see the test rows.

### Anatomy of a Pipeline

```
                 ┌──────────┐    ┌──────────┐    ┌─────────┐
   X_train ────▶ │ scaler   │ ──▶│ encoder  │ ──▶│ classif │
                 │ fit_trf  │    │ fit_trf  │    │ fit     │
                 └──────────┘    └──────────┘    └─────────┘

                 ┌──────────┐    ┌──────────┐    ┌─────────┐
   X_test  ────▶ │ scaler   │ ──▶│ encoder  │ ──▶│ classif │
                 │ transform│    │ transform│    │ predict │
                 └──────────┘    └──────────┘    └─────────┘
```

The pipeline is itself an estimator: it has `fit`, `predict`, `score`, `get_params`, `set_params`. You can drop it into a cross-validator. You can put it inside `GridSearchCV`. You can pickle it. From the outside it looks like a single model, even though internally it composes several.

### Accessing Steps and Their Parameters

Steps are accessible by name through `named_steps` or by index through `steps`:

```python
pipe.named_steps["scaler"].mean_       # fitted state of the scaler step
pipe.named_steps["clf"].coef_          # fitted state of the classifier step
```

Hyperparameters of inner steps follow the `<step>__<param>` double-underscore convention:

```python
pipe.set_params(clf__C=0.1, scaler__with_mean=False)
```

This naming is what makes `GridSearchCV` over a pipeline ergonomic. You write `param_grid={"clf__C": [0.01, 0.1, 1.0]}` and the search-CV navigates into the right step automatically.

### `make_pipeline`: The Quick Form

For one-off pipelines where step names do not matter, `make_pipeline` auto-names each step after its class (lowercased):

```python
from sklearn.pipeline import make_pipeline

pipe = make_pipeline(StandardScaler(), LogisticRegression())
pipe.named_steps   # {"standardscaler": ..., "logisticregression": ...}
```

Use the explicit `Pipeline([(name, step), ...])` form when you plan to grid-search hyperparameters or read the steps by name; use `make_pipeline` for prototypes.

## Section 3: ColumnTransformer for Heterogeneous Data

`Pipeline` chains transformers vertically. `ColumnTransformer` arranges them horizontally — different columns get different preprocessing in parallel, then the outputs are concatenated.

This is the most common preprocessing pattern in tabular ML, because real datasets mix numerical columns (need scaling), low-cardinality categorical columns (need one-hot encoding), high-cardinality categorical columns (need target or hashing encoding), and text columns (need vectorization).

### The Pattern

```python
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression

numeric_features = ["age", "income", "tenure_months"]
categorical_features = ["country", "subscription_tier"]

numeric_pipe = Pipeline([
    ("impute", SimpleImputer(strategy="median")),
    ("scale",  StandardScaler()),
])

categorical_pipe = Pipeline([
    ("impute", SimpleImputer(strategy="most_frequent")),
    ("onehot", OneHotEncoder(handle_unknown="ignore")),
])

preprocess = ColumnTransformer(
    transformers=[
        ("num", numeric_pipe,     numeric_features),
        ("cat", categorical_pipe, categorical_features),
    ],
    remainder="drop",   # any column not listed is dropped
)

model = Pipeline([
    ("preprocess", preprocess),
    ("clf",        LogisticRegression(max_iter=1000)),
])
```

`model` is now a single object you can `fit`, `predict`, `score`, cross-validate, grid-search, and persist. The official compose guide on [`ColumnTransformer`](https://scikit-learn.org/stable/modules/compose.html) is the canonical reference.

### `remainder` and Column Selection

`remainder="drop"` (the default) discards columns not listed. `remainder="passthrough"` keeps them as-is. `remainder=SomeTransformer()` applies that transformer to the remaining columns.

For projects with dozens of columns, prefer the `make_column_selector` helper:

```python
from sklearn.compose import make_column_selector as selector

preprocess = ColumnTransformer([
    ("num", numeric_pipe,     selector(dtype_include=np.number)),
    ("cat", categorical_pipe, selector(dtype_include=object)),
])
```

This selects columns by dtype rather than by hard-coded name, which makes the pipeline robust to schema drift between train and serving.

### Why `handle_unknown="ignore"` Matters

A common production failure: the training set has values `{"US", "DE", "FR"}` for `country`; production data eventually contains `"BR"`. Without `handle_unknown="ignore"`, `OneHotEncoder.transform` raises and the model serves zero predictions until someone retrains. With `handle_unknown="ignore"`, the unseen category is encoded as all zeros and inference proceeds.

> **Pause and predict** — In the pipeline above, suppose at serving time you call `model.predict(X_new)` where `X_new` has the columns in a different order than training. Does it work? (Answer: yes, because `ColumnTransformer` selects columns by name when given a DataFrame, not by position. This is one of the strongest reasons to keep the input as a DataFrame and not convert to ndarray prematurely.)

## Section 4: model_selection — Splitters and Cross-Validation

Cross-validation is the workhorse of honest model evaluation. The `model_selection` module ([API reference](https://scikit-learn.org/stable/api/sklearn.base.html), [user guide on cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html)) splits the splitter into a small set of strategies and lets you pick the one whose assumption matches your data.

### `train_test_split`: The One-Shot Split

```python
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=0,
    stratify=y,        # preserves class proportions in both splits
)
```

`stratify=y` is the difference between a believable test score and a misleading one for imbalanced classification. When the positive class is 4% of the data, a non-stratified random split can give the test set 6% positives and the training set 3.5%, distorting both training and evaluation.

### Cross-Validation Splitters

The right splitter depends on the data structure.

| Splitter | Use when | What it preserves |
|---|---|---|
| `KFold(n_splits=5)` | Rows are independent. Regression, balanced classification. | Nothing extra. |
| `StratifiedKFold(n_splits=5)` | Classification, especially imbalanced. | Class proportions per fold. |
| `GroupKFold(n_splits=5)` | Rows have a group identifier (patient, customer, session) and the same group must not appear in train and test. | Group disjointness. |
| `StratifiedGroupKFold(n_splits=5)` | Both group constraint and class imbalance. | Group disjointness + class proportions. |
| `TimeSeriesSplit(n_splits=5)` | Time-ordered data; future must not leak into past. | Temporal order. |
| `LeaveOneGroupOut()` | One held-out group per fold. | Group disjointness. |

Picking the wrong splitter is the second-most-common evaluation bug after leakage. `KFold` on time-series data lets the model train on the future and test on the past, producing scores that cannot exist in production. `KFold` on grouped data (multiple rows per patient) lets the model memorize patient-level signal in training and recognize it in test, again producing inflated scores.

### `cross_val_score` and `cross_validate`

`cross_val_score` returns an array of scores, one per fold:

```python
from sklearn.model_selection import StratifiedKFold, cross_val_score

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
scores = cross_val_score(model, X, y, cv=cv, scoring="roc_auc")
print(scores)                # 5 numbers
print(scores.mean(), scores.std())
```

`cross_validate` returns a dict that can include multiple metrics, train scores, and timing:

```python
from sklearn.model_selection import cross_validate

result = cross_validate(
    model, X, y,
    cv=cv,
    scoring=["roc_auc", "average_precision", "f1"],
    return_train_score=True,
    n_jobs=-1,
)
result["test_roc_auc"], result["train_roc_auc"], result["fit_time"]
```

`return_train_score=True` is invaluable for diagnosing overfitting — a healthy model has train and test scores in the same neighborhood; a memorizer has train scores near 1.0 and test scores far lower. Module 1.3 (Evaluation, Validation, Leakage & Calibration) goes deep on metrics; for now the relevant point is that the splitter and the pipeline are independent concerns and `cross_validate` composes them cleanly.

### Why Pipelines Make Cross-Validation Honest

Cross-validation only protects against leakage when the *entire* preprocessing chain is inside the pipeline. If you scale outside the pipeline and then pass the scaled features into `cross_val_score`, every fold uses statistics from rows that are about to become its validation set. The pipeline pattern eliminates that class of bug by construction.

## Section 5: Custom Transformers — `BaseEstimator` and `TransformerMixin`

Real projects always reach a point where built-in transformers do not cover the feature engineering you need. The sklearn [developer guide on rolling your own estimator](https://scikit-learn.org/stable/developers/develop.html) defines the contract.

### The Minimal Transformer

```python
from sklearn.base import BaseEstimator, TransformerMixin
import numpy as np

class WinsorizeTransformer(BaseEstimator, TransformerMixin):
    """Clip each numeric column to per-column [low, high] quantiles
    learned from the training data. Compatible with sklearn's
    Pipeline and ColumnTransformer.
    """

    def __init__(self, low_quantile=0.01, high_quantile=0.99):
        # All __init__ arguments must be assigned to self with the
        # same name and must not be modified. This is what makes
        # get_params / set_params / clone work correctly.
        self.low_quantile = low_quantile
        self.high_quantile = high_quantile

    def fit(self, X, y=None):
        X = np.asarray(X, dtype=float)
        self.low_  = np.quantile(X, self.low_quantile,  axis=0)
        self.high_ = np.quantile(X, self.high_quantile, axis=0)
        self.n_features_in_ = X.shape[1]
        return self

    def transform(self, X):
        X = np.asarray(X, dtype=float)
        return np.clip(X, self.low_, self.high_)
```

The class follows three rules from the developer guide:

1. **`__init__` is a dumb assigner.** It only stores the arguments. No validation, no logging, no derived computation. This guarantees that `clone(estimator)` (used heavily by cross-validation and grid search) produces a fresh, equivalent instance.
2. **`fit` returns `self`.** This is what enables the chaining idiom `MyTransformer().fit(X).transform(X)` and what `Pipeline` relies on internally.
3. **Learned state lives in trailing-underscore attributes.** `low_`, `high_`, and `n_features_in_` only exist after `fit` has run.

`TransformerMixin` gives you `fit_transform` for free (it just calls `fit` then `transform`). `BaseEstimator` gives you `get_params`, `set_params`, and the default `__repr__`.

### Worked Example: A Per-Group Mean Encoder

```python
from sklearn.base import BaseEstimator, TransformerMixin
import pandas as pd
import numpy as np

class GroupMeanEncoder(BaseEstimator, TransformerMixin):
    """Replace a categorical column with the in-group mean of the
    target. Demonstration only — for production target encoding,
    prefer category_encoders.TargetEncoder which adds smoothing.
    """

    def __init__(self, column, default=0.0):
        self.column = column
        self.default = default

    def fit(self, X, y):
        # IMPORTANT: y is required. The encoder leaks if computed
        # without a CV-aware split, which is why this is a teaching
        # example, not a production recipe.
        df = pd.DataFrame({self.column: X[self.column], "_y": y})
        self.mapping_ = df.groupby(self.column)["_y"].mean().to_dict()
        return self

    def transform(self, X):
        X = X.copy()
        X[self.column] = X[self.column].map(self.mapping_).fillna(self.default)
        return X
```

This compiles, runs, and slots into a `Pipeline`. It also illustrates a real concern: target encoders are leakage-prone when fit on the same rows used to evaluate the model. Inside a properly-configured `Pipeline` driven by `cross_val_score`, the encoder's `fit` only sees the training fold, which is the leakage-safe arrangement. Module 1.4 (Feature Engineering & Preprocessing) treats encoders in depth.

> **Pause and predict** — Suppose someone writes `GroupMeanEncoder(column="city", smoothing=10)`. What goes wrong, and what error do you get? (Answer: `__init__` does not accept `smoothing`, so Python raises `TypeError: __init__() got an unexpected keyword argument 'smoothing'`. Adding the parameter requires both an `__init__` argument *and* matching usage in `fit` — not just a decorator on the class.)

### `clone` and the No-Side-Effects Rule

`sklearn.base.clone` produces a copy of an estimator with the same hyperparameters but no fitted state. Cross-validation and grid search call `clone` on every fold so each fold trains a fresh model. `clone` works by reading `get_params` and re-instantiating, which is exactly why `__init__` cannot mutate its arguments — if you stored `np.array(low_quantile)` instead of `low_quantile`, clones would diverge from the original and grid search would behave non-deterministically. The user guide and developer guide both flag this as the most common mistake when authoring custom estimators.

## Section 6: Persistence, Search-CV, and Meta-Estimators

### Saving and Loading Fitted Estimators

The official guidance lives in the [joblib persistence docs](https://joblib.readthedocs.io/en/stable/persistence.html). For typical sklearn workflows:

```python
import joblib

# Save the entire fitted pipeline — preprocess + estimator together
joblib.dump(model, "model.joblib")

# Later, in a serving process
loaded = joblib.load("model.joblib")
predictions = loaded.predict(X_new)
```

A few discipline points:

- **Persist the whole pipeline, not just the final estimator.** If you save only the final classifier, you have lost the preprocessing chain and cannot reproduce inference.
- **Pin library versions.** A pipeline pickled under sklearn 1.5 may not unpickle cleanly under sklearn 1.7 if internal attributes changed. Lock the version in your serving environment.
- **Pickled files are arbitrary code.** Never `joblib.load` a file from an untrusted source. The joblib docs are explicit about this.
- **Inspect what got saved.** `loaded.named_steps`, `loaded.get_params()`, and `loaded.feature_names_in_` (when present) tell you whether the artifact matches what you expect.

For higher-stakes production (cross-version stability, security, smaller artifacts), consider `skops` or ONNX export — both linked from the joblib persistence page.

### `GridSearchCV` and `RandomizedSearchCV`

Both are themselves estimators. They wrap an inner estimator, exhaustively try (or randomly sample) hyperparameter combinations, evaluate each via cross-validation, and then expose the best one through their own `predict` and `score`.

```python
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from scipy.stats import loguniform

# GridSearchCV: try every combination on the grid
grid = GridSearchCV(
    estimator=model,
    param_grid={
        "clf__C":            [0.01, 0.1, 1.0, 10.0],
        "preprocess__num__scale__with_mean": [True, False],
    },
    cv=cv,
    scoring="roc_auc",
    n_jobs=-1,
)
grid.fit(X_train, y_train)
grid.best_params_
grid.best_score_
grid.cv_results_   # full table of every config tried

# RandomizedSearchCV: sample from distributions
rand = RandomizedSearchCV(
    estimator=model,
    param_distributions={
        "clf__C": loguniform(1e-3, 1e2),
    },
    n_iter=50,
    cv=cv,
    scoring="roc_auc",
    n_jobs=-1,
    random_state=0,
)
rand.fit(X_train, y_train)
```

When to use which:

- **Grid** is appropriate when the parameter space is small and discrete (a handful of values, no continuous ranges). It is exhaustive but combinatorial — adding a fourth parameter with five values multiplies runtime by five.
- **Randomized** is the default when any parameter is continuous or the joint space is large. Sampling 50 random points usually covers the important regions of a high-dimensional space far more efficiently than a grid of the same compute budget.

These objects are full-fledged estimators. The fitted `grid` has `predict`, `score`, `best_estimator_`, and survives a `joblib.dump` round-trip just like any other model. Halving search variants (`HalvingGridSearchCV`, `HalvingRandomSearchCV`) and Bayesian alternatives are the topic of module 1.11 (Hyperparameter Optimization); the contract here is the same.

### Meta-Estimators: Pipelines, FeatureUnion, and Friends

A meta-estimator is an estimator built out of other estimators. The ones every practitioner hits early:

- **`Pipeline`** — chain of transformers ending in a final estimator (covered in Section 2).
- **`ColumnTransformer`** — parallel transformers on disjoint column subsets (covered in Section 3).
- **`FeatureUnion`** — parallel transformers on the *same* columns whose outputs are concatenated. Used when you want both a `PCA` projection and the raw scaled features fed into the classifier together.

```python
from sklearn.pipeline import FeatureUnion
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

union = FeatureUnion([
    ("scaled", StandardScaler()),
    ("pca5",   PCA(n_components=5)),
])
# union.transform(X) returns concat([scaled X, PCA-5 X], axis=1)
```

All meta-estimators expose `get_params` / `set_params` with the `step__param` convention, which is what makes them grid-searchable end-to-end. The compose user-guide page is the canonical reference. Other meta-estimators worth knowing exist (`MultiOutputClassifier`, `OneVsRestClassifier`, calibration wrappers, voting and stacking ensembles), but the three above cover the majority of preprocessing patterns and are sufficient for everything in modules 1.2 through 1.12.

## Section 7: Putting the Contract Together

A practitioner-grade workflow ties every concept above into a single object. Read this end-to-end skeleton as a checklist for every future tabular project.

```python
import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin, clone
from sklearn.compose import ColumnTransformer, make_column_selector
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import (
    StratifiedKFold,
    cross_validate,
    RandomizedSearchCV,
    train_test_split,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from scipy.stats import loguniform


class TenureBucket(BaseEstimator, TransformerMixin):
    """Bucket a 'tenure_months' column into [new, growing, established].
    Adds the bucket as a new column without touching the original.
    Hyperparameters are bucket boundaries; learned state is the
    column index after fit."""

    def __init__(self, low=6, high=24, column="tenure_months"):
        self.low = low
        self.high = high
        self.column = column

    def fit(self, X, y=None):
        self.col_loc_ = X.columns.get_loc(self.column)
        return self

    def transform(self, X):
        X = X.copy()
        bins = pd.cut(
            X[self.column],
            bins=[-np.inf, self.low, self.high, np.inf],
            labels=["new", "growing", "established"],
        )
        X["tenure_bucket"] = bins.astype(object)
        return X


def build_pipeline():
    numeric = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale",  StandardScaler()),
    ])
    categorical = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    preprocess = ColumnTransformer([
        ("num", numeric,     make_column_selector(dtype_include=np.number)),
        ("cat", categorical, make_column_selector(dtype_include=object)),
    ])
    return Pipeline([
        ("bucket",     TenureBucket(low=6, high=24)),
        ("preprocess", preprocess),
        ("clf",        LogisticRegression(max_iter=1000)),
    ])


def evaluate_and_tune(X, y):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=0,
    )
    pipe = build_pipeline()

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
    baseline = cross_validate(
        pipe, X_train, y_train,
        cv=cv,
        scoring=["roc_auc", "average_precision"],
        return_train_score=True,
        n_jobs=-1,
    )

    search = RandomizedSearchCV(
        pipe,
        param_distributions={
            "clf__C":         loguniform(1e-3, 1e2),
            "bucket__low":    [3, 6, 12],
            "bucket__high":   [18, 24, 36],
        },
        n_iter=30, cv=cv, scoring="roc_auc",
        n_jobs=-1, random_state=0, refit=True,
    )
    search.fit(X_train, y_train)

    # The held-out set is touched exactly once.
    final_score = search.score(X_test, y_test)

    joblib.dump(search.best_estimator_, "model.joblib")
    return baseline, search, final_score
```

Read what this code is and is not doing. It is not a serious model — `LogisticRegression` on a few engineered columns is a baseline, not a finished system. What it *is* is a complete instance of the contract this module defines:

- Every transformer (custom and built-in) lives inside a `Pipeline`. No one calls `fit_transform` on raw data.
- Column selection is by dtype via `make_column_selector`, so schema drift in production fails loudly at the boundary instead of silently mis-routing columns.
- The custom `TenureBucket` follows the `__init__`-is-dumb-assignment, `fit`-returns-self, trailing-underscore-state rule. It can be cloned, grid-searched (`bucket__low`, `bucket__high`), and pickled.
- Cross-validation uses `StratifiedKFold` because the task is classification and class balance matters; `cross_validate` returns train and test scores so you can see overfitting at a glance.
- Hyperparameter search uses `RandomizedSearchCV` because the parameter space mixes continuous and discrete values; `n_iter=30` is far cheaper than the equivalent grid.
- The held-out test set is touched exactly once, at the very end, after the search has selected its best configuration on training-only cross-validation.
- The persistence step saves `best_estimator_` — the entire fitted pipeline — not just the inner classifier. Inference at serving time reproduces every preprocessing decision.

Every module from 1.2 onward swaps the *algorithm* (the `clf` step) and the *feature engineering* (the bucket transformer and friends), but the surrounding workflow stays exactly this shape.

## Did You Know?

1. **`fit_transform` is not always the same as `fit` then `transform`.** Some transformers (notably text vectorizers and dimensionality reducers) have an optimized fused implementation. Most behave identically; the developer guide notes the exceptions.
2. **`Pipeline` supports memory caching.** Pass `memory="./cache_dir"` and the pipeline will memoize transformer outputs across grid-search folds, which can dramatically speed up cross-validation when the early steps are expensive (text vectorization, image preprocessing) and only the final estimator's hyperparameters are being searched.
3. **The trailing-underscore convention is enforced by `check_estimator`.** Sklearn ships a battery of contract tests in `sklearn.utils.estimator_checks` that any custom estimator can run against itself; the developer guide recommends it as the way to verify your estimator behaves like the rest of the library.
4. **`ColumnTransformer` selects columns by name on DataFrames and by integer index on ndarrays.** The same code can quietly mean different things depending on the input type; keeping inputs as DataFrames end-to-end is the safer convention and is what `make_column_selector(dtype_include=...)` assumes.

## Common Mistakes

| Mistake | Why it bites | The right move |
|---|---|---|
| Calling `fit_transform` on the full dataset before splitting | Test statistics leak into training; offline scores beat production. | Put every transformer inside a `Pipeline`; only `train_test_split` (or a CV splitter) sees raw `X`. |
| Using `KFold` on time-series data | Future leaks into past; reported AUC is unachievable in production. | Use `TimeSeriesSplit`. |
| Using `KFold` on grouped data (multiple rows per patient/user) | The model memorizes group-level features; held-out scores reflect within-group recall, not generalization. | Use `GroupKFold` or `StratifiedGroupKFold`. |
| Mutating constructor args inside `__init__` of a custom estimator | `clone` produces non-equivalent copies; grid search becomes non-deterministic; `get_params` lies. | `__init__` is a dumb assigner only; do all derivations in `fit`. |
| Saving the trained classifier without the preprocessing pipeline | Inference at serving time skips scaling / encoding; predictions are nonsense or crash on unseen categories. | `joblib.dump(pipeline, ...)` — persist the whole composed object. |
| Forgetting `handle_unknown="ignore"` on `OneHotEncoder` for production | First unseen category in production raises; serving outage. | Set `handle_unknown="ignore"` on every production-bound `OneHotEncoder`. |
| Tuning hyperparameters on the test set | The "test" set silently becomes a second validation set; reported numbers are search-overfit. | Use `GridSearchCV` / `RandomizedSearchCV` with `cv=` on the training data; touch `X_test` exactly once at the end. |
| Hard-coding column positions in `ColumnTransformer` | Schema drift in production reorders columns; preprocessing applies to wrong fields. | Select by column name (DataFrame input) or by `make_column_selector(dtype_include=...)`. |

## Quiz

Six scenario-based questions. Click each `<details>` to see the worked answer.

<details>
<summary>1. A teammate ships a churn model with 0.93 AUC on a held-out test split. Production AUC is 0.71. Their preprocessing notebook calls `MinMaxScaler().fit_transform(df)` once at the top, then splits into train and test. What is the most likely cause and what is the minimal fix?</summary>

The scaler peeks at the test set during fit. `min_` and `scale_` are computed over rows that are about to become the held-out test, so the test distribution is normalized using its own statistics. The minimal fix is to put the scaler inside a `Pipeline` so its `fit` runs only on the training fold. After the fix, the offline AUC will drop somewhat — that drop is the leakage being removed, and the new number is an honest estimate of production performance.
</details>

<details>
<summary>2. You have a hospital readmission dataset with multiple admissions per patient. You use `StratifiedKFold(n_splits=5, shuffle=True)` and report a 0.89 AUC. A clinical reviewer calls the result implausible. What did the splitter do wrong?</summary>

`StratifiedKFold` preserves class balance but assumes rows are independent. Multiple admissions per patient violate that assumption: the same patient appears in both training and validation folds, and the model can memorize patient-level signal (chronic conditions, demographics) rather than learning generalizable patterns. The honest splitter is `StratifiedGroupKFold` keyed on `patient_id`, which guarantees no patient appears in both train and validation within a fold.
</details>

<details>
<summary>3. You write a custom transformer `LogPlusOne` and inside `__init__` you do `self.eps_ = max(epsilon, 1e-12)`. Cross-validation with this transformer produces inconsistent scores between runs even with `random_state` fixed. Why?</summary>

`__init__` mutated its argument and stored a derived value (`eps_`, with the trailing underscore that signals fitted state). `clone(estimator)` reads `get_params` (which sees `epsilon`) and re-instantiates — but the cloned object's `eps_` is recomputed from `epsilon`, and any code path that reads `eps_` before `fit` runs sees an inconsistent value. The fix: store only `self.epsilon = epsilon` in `__init__` and compute `self.eps_ = max(self.epsilon, 1e-12)` inside `fit`. Trailing-underscore attributes are fitted state; non-underscore attributes are hyperparameters.
</details>

<details>
<summary>4. You wrap a `RandomForestClassifier` in a `Pipeline` with a `StandardScaler` first. The model trains fine, but a code reviewer asks why the scaler is there. What is the right answer?</summary>

It is unnecessary and worth removing. Tree-based models split on feature values and are invariant to monotonic rescaling, so `StandardScaler` does nothing useful and adds latency at inference time. The pipeline pattern is correct — it just contains a no-op step. Linear models, distance-based models (k-NN, k-means), and neural networks need scaling; tree ensembles do not. Module 1.5 (Trees and Forests) treats this in depth.
</details>

<details>
<summary>5. You run `GridSearchCV` over a four-parameter grid with five values each, on a dataset that takes 90 seconds per fit, with `cv=5`. How long does the search take, and what would you change?</summary>

Five raised to the fourth is six hundred and twenty-five combinations; times five folds is over three thousand fits; times ninety seconds is on the order of three days of single-process compute. Two changes help. First, `n_jobs=-1` parallelizes folds across CPU cores. Second, `RandomizedSearchCV` with `n_iter=60` (or a halving variant) usually finds a near-best configuration far faster, because most parameters do not contribute equally — random sampling concentrates compute on configurations the grid would never reach. Module 1.11 (Hyperparameter Optimization) covers when to escalate to Bayesian or population-based search.
</details>

<details>
<summary>6. A pipeline trained on a DataFrame works in development. In production, the data arrives as a NumPy array because the upstream service was rewritten in Go. The pipeline raises on the first request. What broke and how do you make this robust?</summary>

`ColumnTransformer` referenced columns by name (`["country", "subscription_tier"]`). When the input is an ndarray, those names do not exist; the transformer cannot find the columns and raises. Two robust options: (a) keep the input layer as a DataFrame in production by validating and reconstructing it at the service boundary, with column names locked to a schema; (b) switch to integer indices in `ColumnTransformer`, which then requires you to lock the column order at the schema layer instead. Option (a) is generally safer because it surfaces the schema-drift error at the boundary, not deep inside the model.
</details>

## Hands-On Exercise

You will build, evaluate, and persist a leakage-safe sklearn pipeline on a small tabular classification problem.

**Setup.** Use any binary-classification CSV you have on hand with at least one numeric and one categorical column. If you do not have one, generate a synthetic dataset with `sklearn.datasets.make_classification`.

Success criteria:

- [ ] The whole preprocessing chain (numeric imputation + scaling, categorical imputation + one-hot encoding) lives inside a `ColumnTransformer` inside a `Pipeline` together with a final `LogisticRegression` (or any other classifier of your choice). No call to `fit_transform` outside the pipeline anywhere in your script.
- [ ] You evaluate the pipeline with `cross_validate` on `StratifiedKFold(n_splits=5, shuffle=True, random_state=0)` and report mean and standard deviation of `roc_auc`. Print `train_roc_auc` alongside `test_roc_auc` and explain the gap to yourself in a comment in the script.
- [ ] You write a custom transformer (subclassing `BaseEstimator` and `TransformerMixin`) that adds at least one engineered feature. Test it: instantiate it, call `clone` on it, and verify `clone(t).get_params() == t.get_params()`.
- [ ] You run `RandomizedSearchCV` over at least two hyperparameters (one from the preprocessing chain, one from the classifier) with `n_iter=20`. Print `best_params_`, `best_score_`, and the standard deviation of the best configuration's CV scores.
- [ ] You persist the fitted `RandomizedSearchCV` (or its `best_estimator_`) with `joblib.dump`, then in a fresh interpreter `joblib.load` it and call `predict` on a small held-out slice. Verify the predictions match the in-memory pipeline's predictions on the same rows.
- [ ] You deliberately introduce a leakage bug (call `StandardScaler().fit_transform` on the full dataset before splitting) and observe the inflated test score. Restore the leakage-safe pipeline and document the magnitude of the bias in a comment.

When all six checkboxes are green, you have internalized the contract this module exists to teach. The remaining modules in this section assume it.

## Sources

- [Scikit-learn user guide](https://scikit-learn.org/stable/user_guide.html)
- [Developing scikit-learn estimators (developer guide)](https://scikit-learn.org/stable/developers/develop.html)
- [Pipelines and composite estimators (`Pipeline`, `ColumnTransformer`, `FeatureUnion`)](https://scikit-learn.org/stable/modules/compose.html)
- [Cross-validation: evaluating estimator performance](https://scikit-learn.org/stable/modules/cross_validation.html)
- [Metrics and scoring (overview)](https://scikit-learn.org/stable/modules/model_evaluation.html)
- [`sklearn.base` API reference (`BaseEstimator`, `TransformerMixin`, `clone`)](https://scikit-learn.org/stable/api/sklearn.base.html)
- [Joblib persistence guide](https://joblib.readthedocs.io/en/stable/persistence.html)

## Next Module

[Module 1.2 — Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/) (coming soon, Phase 1b) walks into the algorithm layer with the workflow you just built around it.
