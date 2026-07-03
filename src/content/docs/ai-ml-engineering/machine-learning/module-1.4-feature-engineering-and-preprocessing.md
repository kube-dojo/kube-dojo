---
title: "Feature Engineering & Preprocessing"
description: "Design a leakage-safe preprocessing pipeline for mixed-types tabular data: choose categorical encoders by cardinality, scalers by distribution and learner family, imputers by missingness mechanism, and feature selection methods by their cost-benefit profile, then assemble everything inside a ColumnTransformer."
slug: ai-ml-engineering/machine-learning/module-1.4-feature-engineering-and-preprocessing
sidebar:
  order: 4
---

> **AI/ML Engineering Track** | Complexity: `[MEDIUM]` | Time: 5-6 hours
> **Prerequisites**: [Module 1.1](../module-1.1-scikit-learn-api-and-pipelines/) (Pipeline, ColumnTransformer, custom transformers) and [Module 1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/) (CV-aware fitting, leakage taxonomy). Comfortable NumPy and pandas.

## Learning Outcomes

By the end of this module, a practitioner will be able to:

1. **Design** a leakage-safe preprocessing chain for a mixed-types DataFrame using `ColumnTransformer` and `make_column_selector`, routing the right scaler, encoder, and imputer to the right dtype.
2. **Choose** a categorical encoding strategy - one-hot, ordinal, target with internal cross-fitting, or a high-cardinality fallback - given column cardinality, label availability, and the chosen learner family.
3. **Compare** numerical scalers (`StandardScaler`, `RobustScaler`, `MinMaxScaler`, `PowerTransformer`, `QuantileTransformer`) and decide which is appropriate from feature-distribution shape and learner sensitivity.
4. **Implement** a non-leaking imputation strategy with `SimpleImputer`, `IterativeImputer`, or `KNNImputer`, and add `MissingIndicator` (or `add_indicator=True`) when missingness itself is signal.
5. **Evaluate** filter, wrapper, and embedded feature-selection methods (variance, chi2/ANOVA, RFE/RFECV, `SelectFromModel`) and explain when feature selection is worth the cost versus when regularization or tree models already do the job.

These outcomes extend Module 1.1 and Module 1.3. Module 1.1 taught the workflow contract. Module 1.3 taught the evaluation contract. This module teaches the *preprocessing* contract that fits inside both. The contract is not a feature-creativity exercise. It is a small, deliberately boring catalog of decisions - encode, scale, impute, select - made systematically so that the remaining variance in your model performance comes from the algorithm and the data, not from accidental leaks in the preprocessing layer.

## Why This Module Matters

A team ships a classifier whose cross-validated ROC AUC looked solid and watches production AUC drift consistently below the held-out estimate over the first weeks of live traffic. The on-call engineer reads the training notebook, finds `StandardScaler.fit_transform(X)` on the full dataset before the train/test split, and learns that the held-out score had been quietly using statistics that included its own rows. The model is fine. The data is fine. The preprocessing layer leaked, and the leakage was invisible to every offline metric the team had.

The scikit-learn common pitfalls guide identifies that exact failure mode and two close cousins. A `OneHotEncoder` fit on training data only and shipped without `handle_unknown="ignore"` will raise `ValueError` the first time production sends a category that was always rare during training - a cleaner crash than silent degradation, but a Tuesday-night incident either way. A `SimpleImputer` whose median was computed across both training and test rows smuggles target-correlated information through the imputation statistic; cross-validation reads contaminated medians and production reads honest ones, and the gap between them is exactly the gap an evaluator cannot see. All three patterns share a structural cause and the same structural fix: every preprocessing decision must come from training-only statistics, and `Pipeline` is the mechanism that enforces this automatically.

The compose guide adds the structural counterpart: in real datasets, columns of different dtypes need different preprocessing, and the composition tool is `ColumnTransformer`. The preprocessing user guide then catalogs the actual transformer choices - many algorithms either require or behave better when input features are on similar scales, free of missing values, and encoded in a form the algorithm can consume.

Together, these three guides describe one thing - a preprocessing layer that is correct by construction. The reason a module exists for that is that the catalog is wider than it looks. Encoding has at least four legitimate strategies, each fitting a different cardinality regime. Scaling has at least five, each protecting against a different distributional pathology. Imputation has at least three, with a separate question of whether missingness should also be encoded as a feature. Feature selection has three families with very different cost-benefit tradeoffs. None of these decisions is the "default", and getting them wrong does not raise an exception - it just shifts the error budget into a place the evaluation cannot see. This module gives you a decision frame for each one and a single end-to-end pipeline that ties them together so a reviewer can read it in one pass.

## Section 1: Categorical Encoding by Cardinality

A learner cannot consume the string `"DE"` as input. Encoding turns categories into numbers in a way that does not lie about the relationships between them. The right encoder depends on three things: the cardinality of the column, whether a true ordering exists among the categories, and whether the downstream learner is sensitive to spurious linear or distance relationships in the encoded values.

### One-Hot Encoding for Low Cardinality

`OneHotEncoder` is the workhorse for low-cardinality nominal columns. It maps each level to a binary indicator column. There is no implied ordering and no implied distance between levels. The trade-off is dimensionality: a column with `k` levels expands into `k` columns (or `k-1` with `drop="first"`).

```python
import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder

df = pd.DataFrame({"country": ["US", "DE", "FR", "DE", "US"]})
enc = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
encoded = enc.fit_transform(df[["country"]])
print(enc.get_feature_names_out())
print(encoded)
```

`handle_unknown="ignore"` is non-negotiable for production. Without it, the first unseen category at serving time raises `ValueError` and inference breaks. With it, an unseen category is encoded as all zeros and the model continues. Module 1.1 covers this in detail; the takeaway here is that any production-bound `OneHotEncoder` should set this argument.

The "dummy variable trap" is the question of whether to keep all `k` indicator columns or drop one with `drop="first"`. For unregularized linear models, the full one-hot encoding is exactly collinear with the intercept, and the design matrix is singular. For regularized linear models (Ridge, Lasso, ElasticNet) and for tree-based models, this collinearity is harmless, and `drop=None` is fine. The sklearn guide is explicit that `drop` is a modeling choice, not a correctness requirement.

### Ordinal Encoding Only When Order Is Real

`OrdinalEncoder` maps each category to an integer. That integer is interpreted as a number by every downstream learner. This is the right tool when the categories carry a real ordering - "Bronze < Silver < Gold", "S < M < L < XL" - and a wrong tool everywhere else.

```python
import numpy as np
import pandas as pd
from sklearn.preprocessing import OrdinalEncoder

df = pd.DataFrame({"tier": ["Silver", "Gold", "Bronze", "Gold", "Silver"]})
enc = OrdinalEncoder(categories=[["Bronze", "Silver", "Gold"]])
print(enc.fit_transform(df[["tier"]]))
```

Passing `categories=` explicitly is what locks the meaningful ordering. Without it, the encoder uses the order of first appearance, which is arbitrary. The anti-pattern this encoder enables, if used carelessly, is ordinal-encoding a nominal column for a linear model: the learner sees `country=2` and `country=4` and concludes that `country=4` is "twice as much" of something. For a tree-based learner, ordinal encoding is more forgiving because trees split on thresholds rather than projecting onto a linear axis - but the encoding still imposes an arbitrary split order, which can hurt when there is no natural ordering to recover.

### Target Encoding for Medium Cardinality

For columns with a few hundred to a few thousand levels, one-hot encoding becomes painful: the design matrix grows wide and sparse, distance metrics (k-NN, kernel SVMs) lose discrimination, and many of the indicator columns carry almost no signal. `TargetEncoder` (introduced in sklearn 1.3 for binary and regression targets, with multiclass support added in sklearn 1.4) replaces a category with a shrunk estimate of the target's conditional mean for that category - the per-class conditional probability for binary classification, regressed toward the global mean to keep low-count categories from dominating, and one output column per class for multiclass classification.

The catch is that target encoding reads `y`. Module 1.3's leakage taxonomy names the failure: if a row's own label contributes to that row's encoded feature, the validation score is no longer testing unseen behavior. The sklearn `TargetEncoder` documentation is explicit that the encoder uses an internal cross-fitting scheme during `fit_transform` so that, for each training row, the encoded value is computed from a fold that excludes that row.

```python
import numpy as np
from sklearn.preprocessing import TargetEncoder

X = np.array([
    ["A"], ["A"], ["A"], ["B"], ["B"], ["B"],
    ["C"], ["C"], ["C"], ["D"], ["D"], ["D"],
])
y = np.array([1, 0, 1, 0, 0, 0, 1, 1, 1, 0, 1, 0])

enc = TargetEncoder(target_type="binary", random_state=0)
X_train_encoded = enc.fit_transform(X, y)
print("training (cross-fitted):")
print(X_train_encoded.ravel())

# At transform-time on unseen data, the encoder uses the full mapping
# learned on the original X, y, NOT the cross-fitted one.
X_new = np.array([["A"], ["B"], ["E"]])  # "E" is unseen
print("transform on unseen rows:")
print(enc.transform(X_new).ravel())
```

The first call (`fit_transform`) returns cross-fitted values for downstream learners. A subsequent `transform` uses a single mapping learned over all of `X, y`, which is the right behavior for inference. This split is what makes `TargetEncoder` safe inside a `Pipeline` driven by `cross_validate`: the encoder's `fit` only sees the training fold, and the cross-fitting happens fold-internally.

The naive failure mode - `df.groupby("category")[target].mean()` over the full dataset before splitting - is exactly the target-leakage example from Module 1.3, and `TargetEncoder` exists to make it unnecessary. If you reach for `pandas.groupby().mean()` to encode a category, you owe yourself a justification for why `TargetEncoder` is not the right tool.

### High Cardinality: Hashing or Embeddings

For columns with thousands to millions of levels - user IDs, ZIP codes, raw URLs - both one-hot and target encoding become awkward. One-hot blows the dimensionality up. Target encoding is statistically thin for any category seen only a handful of times, even with smoothing. Two pragmatic patterns survive at this scale.

The first is *feature hashing*: map each category to a fixed-width sparse feature vector by hashing the raw string into `m` buckets, with each row producing a one-hot (or signed) entry in the bucket the hash selects. Collisions are accepted as a regularization cost - the model treats categories that happen to land in the same bucket as the same feature, and useful signal usually survives because most categories collide with low-information ones. This is the pattern behind `HashingVectorizer` for text and is implementable for arbitrary categorical columns by hashing the raw string. It is fast, requires no fit, and tolerates unseen categories gracefully because a never-seen category simply hashes into the same fixed feature space as everything else. The crucial property is that the output is a *fixed-width feature vector*, not a single integer bucket id - encoding categories as a raw integer bucket index would reintroduce the spurious-ordering problem that motivated leaving `OrdinalEncoder` for explicitly ordered columns.

The second is *learned embeddings* - mapping each category to a dense low-dimensional vector trained jointly with the model. This is the dominant pattern in deep tabular models and is delegated to a deep-learning framework rather than to sklearn. The deep-learning track covers this in its tabular module.

For high-cardinality categoricals where neither hashing nor embeddings is appropriate, the sklearn-contrib package `category_encoders` ships smoothed target encoders, leave-one-out encoders, James-Stein encoders, and several others. They follow the sklearn estimator contract and drop into a `Pipeline` cleanly.

### Cardinality Decision Table

| Cardinality | Typical example | First-choice encoder | Why |
|---|---|---|---|
| Low (≤10 levels) | country, payment method, weekday | `OneHotEncoder` | No artificial ordering, dimensionality is manageable |
| Medium (10-1000) | product SKU group, ZIP-3, occupation | `TargetEncoder` for linear/distance learners; one-hot still fine for trees | Target encoding compresses without imposing order; trees handle wide one-hot fine |
| High (>1000) | user_id, raw ZIP, raw URL | Feature hashing or learned embeddings | One-hot is too wide; per-category statistics are too thin |
| Ordered (any cardinality) | tier, education level, T-shirt size | `OrdinalEncoder(categories=[...])` | The order is real and the learner should see it |

> **Pause and predict** - You are encoding a `merchant_id` column with about 4,000 distinct values for a fraud-classification logistic regression. One-hot would explode the design matrix. What does `TargetEncoder` give you that `pd.Series.map(df.groupby("merchant_id")["fraud"].mean())` does not? (Answer: `TargetEncoder` cross-fits during `fit_transform`, so the per-row training value does not include that row's own label, and it learns a single inference mapping that survives `transform` on unseen rows. The naive groupby uses every row's label to compute its own encoded value - target leakage by Module 1.3's taxonomy.)

## Section 2: Numerical Scaling and Distributional Transforms

Whether scaling matters depends on what the learner does with feature magnitudes. Distance-based learners (k-NN, k-means, kernel SVMs with RBF or polynomial kernels) compute distances directly, so a feature with a 1000x larger range dominates the distance. Gradient-based learners (logistic regression, linear regression with gradient solvers, neural networks) converge faster and more reliably with comparable feature scales. Tree-based learners (decision trees, random forests, gradient-boosted trees) split on thresholds and are invariant to monotonic rescaling - scaling them is a no-op that adds latency. The decision tree and random forest module (1.5) discusses this; for now, the rule is: scale for distance-based and gradient-based learners, do not bother for tree ensembles.

The sklearn preprocessing guide describes five scaler families with different distributional assumptions. None is universally best.

### Scaler Decision Table

| Scaler | What it does | Best when | Trap |
|---|---|---|---|
| `StandardScaler` | Subtracts mean, divides by std | Roughly Gaussian features, no extreme outliers | A single 1000σ outlier can squash 99% of mass into a tiny range |
| `RobustScaler` | Subtracts median, divides by IQR | Outliers are plausible and you want them to remain outliers but not dominate the scale | The output is no longer unit-variance, so do not assume σ=1 downstream |
| `MinMaxScaler` | Maps to a fixed range (default `[0, 1]`) | The learner expects a bounded input range (e.g., neural network image intensities) | A new outlier at inference time falls outside the trained range |
| `PowerTransformer` (`yeo-johnson` default; `box-cox` for strictly positive data) | Monotonic power transform that stabilizes variance and makes the distribution more Gaussian-like | Strongly skewed numeric features feeding a learner that benefits from near-normal inputs | Non-linear transformation; interpretation of coefficients in the original units is lost |
| `QuantileTransformer` | Maps to uniform or normal via the empirical CDF | Heavy-tailed or multimodal features; you want robustness to outliers above all | Most aggressive transformation; can crush real signal into the bulk of the distribution |

### Worked Example: Five Scalers, One Skewed Feature

```python
import numpy as np
from sklearn.preprocessing import (
    MinMaxScaler,
    PowerTransformer,
    QuantileTransformer,
    RobustScaler,
    StandardScaler,
)

rng = np.random.default_rng(0)
# Income-like distribution: log-normal with a few extreme outliers
x = np.concatenate([
    rng.lognormal(mean=10.0, sigma=0.6, size=995),
    np.array([1e7, 2e7, 5e7, 8e7, 1e8]),
]).reshape(-1, 1)

scalers = {
    "StandardScaler": StandardScaler(),
    "RobustScaler": RobustScaler(),
    "MinMaxScaler": MinMaxScaler(),
    "PowerTransformer": PowerTransformer(method="yeo-johnson"),
    "QuantileTransformer": QuantileTransformer(
        output_distribution="normal", n_quantiles=200, random_state=0
    ),
}

for name, scaler in scalers.items():
    z = scaler.fit_transform(x).ravel()
    print(
        f"{name:22s} median={np.median(z):+.2f}  iqr={np.subtract(*np.percentile(z, [75, 25])):.2f}  "
        f"min={z.min():+.2f}  max={z.max():+.2f}"
    )
```

The output makes the trade-offs concrete. `StandardScaler` produces a tiny IQR because the few extreme outliers inflate the standard deviation; the bulk of the data is squashed near zero. `RobustScaler` keeps the IQR on the order of one because the median and IQR are unaffected by the outliers, but the maximum value is still large. `MinMaxScaler` puts everything in `[0, 1]`, with the outliers pinning the maximum and the bulk of the data near the bottom. `PowerTransformer` and `QuantileTransformer` reshape the distribution; `QuantileTransformer` with `output_distribution="normal"` produces a near-Gaussian shape regardless of the input.

The right choice is rarely "whichever has the prettiest histogram". For logistic regression with L2 regularization on income data, `RobustScaler` or `PowerTransformer` is usually right - the model is sensitive to scale but can tolerate residual non-normality. For k-NN, `RobustScaler` plus possibly `QuantileTransformer` is defensible because distances should not be dominated by tail values. For a gradient-boosted tree, none of these scalers is necessary at all.

> **Pause and predict** - You are training a kernel SVM with an RBF kernel on a tabular dataset where one numeric column ranges from 0 to 1 and another ranges from 0 to 1,000,000. Which scaler is the first one you reach for, and why is `StandardScaler` a defensible second choice but a worse first choice if you suspect outliers? (Answer: `RobustScaler` first - distances need to be on a comparable scale, but you do not want a few extreme rows to set the unit. `StandardScaler` is defensible if outliers are absent, but a single 100σ row will collapse most of the data into a tiny range. The kernel SVM cannot recover from that.)

## Section 3: Missing Values

Missing data is a preprocessing problem with two layers: how to fill the value (imputation) and whether the missingness itself carries information (indicators).

### The Leakage Trap

Imputation statistics fitted on the full dataset are the canonical preprocessing leak from Module 1.3. The mean of the `income` column over training plus validation is not the same as the mean over training alone, and once that statistic has been used to fill validation rows, the validation set is no longer a held-out evaluation. The fix is the same one Module 1.1 and Module 1.3 both recommend: put every imputer inside a `Pipeline` so each fold's imputer fits only on that fold's training rows.

### `SimpleImputer`

`SimpleImputer` covers most of the everyday cases.

```python
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer

df = pd.DataFrame({
    "age": [34.0, np.nan, 51.0, 22.0, np.nan, 45.5, 30.0],
    "city": ["Berlin", "Lyon", None, "Berlin", "Madrid", None, "Lyon"],
})

num_imputer = SimpleImputer(strategy="median")
cat_imputer = SimpleImputer(strategy="most_frequent")

print(num_imputer.fit_transform(df[["age"]]).ravel())
print(cat_imputer.fit_transform(df[["city"]]).ravel())
```

The four strategies have different default failure modes:

- `mean`: appropriate for symmetric numeric distributions with light tails. Sensitive to outliers.
- `median`: appropriate for skewed or heavy-tailed numeric distributions. The default safe choice for raw numeric features.
- `most_frequent`: the only valid default for categorical columns; for numeric columns it implies a discrete distribution, which is rare.
- `constant`: explicit fill value via `fill_value`. Useful for "out-of-band" markers (e.g., `-1` or `"unknown"`) when combined with a `MissingIndicator` so the learner can pick up the signal.

### Missingness as a Feature

Whether a value is missing is sometimes more informative than the value itself. A patient with no recorded blood-pressure reading might be a patient who never came to the clinic, not a patient with median blood pressure. Encoding the missingness pattern explicitly as an additional feature lets the model learn that signal directly.

```python
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer

df = pd.DataFrame({
    "lab_value": [12.0, np.nan, 9.5, np.nan, 11.2, np.nan, 14.1],
})

imputer = SimpleImputer(strategy="median", add_indicator=True)
out = imputer.fit_transform(df[["lab_value"]])
print(out)
```

The output has two columns: the imputed `lab_value` and a binary missing indicator. `add_indicator=True` is the lightweight form; the standalone `MissingIndicator` transformer exposes more configuration (which columns to track, how to handle features that have no missing values in training but might have missing values in production).

### `IterativeImputer` and `KNNImputer`

When the missingness is structured - one column tends to be missing when another column has certain values - smarter imputation can recover signal that a column-wise median throws away.

`IterativeImputer` is still an experimental sklearn API and requires an explicit opt-in import:

```python
import numpy as np
import pandas as pd
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from sklearn.linear_model import BayesianRidge

df = pd.DataFrame({
    "x1": [1.0, 2.0, np.nan, 4.0, 5.0, np.nan, 7.0],
    "x2": [2.1, 4.2, 6.1, np.nan, 10.0, 12.1, np.nan],
    "x3": [10.0, np.nan, 30.0, 40.0, np.nan, 60.0, 70.0],
})

imputer = IterativeImputer(estimator=BayesianRidge(), max_iter=10, random_state=0)
print(imputer.fit_transform(df))
```

`IterativeImputer` regresses each column with missing values on the other columns in a round-robin schedule until estimates stabilize. It is appropriate when the data is missing at random with structure, when columns are correlated, and when you can afford the extra fit cost.

`KNNImputer` fills each missing entry with a weighted average of the `k` nearest complete rows in feature space.

```python
import numpy as np
import pandas as pd
from sklearn.impute import KNNImputer

df = pd.DataFrame({
    "x1": [1.0, 2.0, np.nan, 4.0, 5.0, np.nan, 7.0],
    "x2": [2.1, 4.2, 6.1, 8.0, 10.0, 12.1, 14.0],
})

imputer = KNNImputer(n_neighbors=3, weights="distance")
print(imputer.fit_transform(df))
```

`KNNImputer` is appropriate when local similarity is meaningful and the dataset is small enough to afford the distance computation. Two caveats: distances are scale-sensitive (so usually `StandardScaler` or `RobustScaler` should run before `KNNImputer`), and mixed-type data needs categorical encoding before imputation - `KNNImputer` works on numeric arrays.

### Imputation Decision Table

| Imputer | Cost | When to use | When to avoid |
|---|---|---|---|
| `SimpleImputer(strategy="median")` | Cheap | First-pass numeric imputation; skewed distributions | When missingness is structured and other columns predict it |
| `SimpleImputer(strategy="most_frequent")` | Cheap | Categorical columns | Numeric columns with continuous distributions |
| `SimpleImputer(strategy="constant", fill_value=...)` | Cheap | When you want an out-of-band marker, paired with `add_indicator=True` | When the marker accidentally falls inside the data range |
| `IterativeImputer` | Moderate to high | Correlated numeric columns, structured missingness | Tiny datasets, time-pressured iteration |
| `KNNImputer` | Moderate | Local similarity is meaningful, dataset is small to medium, features already on similar scales | Very high dimensions or mixed dtypes |

## Section 4: Outlier Handling (Brief - Anomaly Detection Lives in Module 1.9)

Outlier handling at the preprocessing layer is a narrow question: what do I do with rows whose feature values are extreme enough to distort fitting? The deep treatment of anomaly and novelty detection - what counts as an outlier in the first place, how to detect them, and when an outlier is a meaningful rare event rather than a data-quality artifact - is Module 1.9. Three pragmatic levers belong here.

The first lever is *robust statistics*. `RobustScaler` (Section 2) was already this. By using the median and IQR rather than the mean and standard deviation, it prevents a small number of extreme rows from dominating the scale. The outliers stay outliers; they just stop dictating where everyone else lives.

The second lever is *winsorization*: clipping each feature to per-column quantiles learned from the training data. Module 1.1 ships a `WinsorizeTransformer` example with exactly this design. It is a small, leakage-safe transformer that fits low and high quantiles on training data and clips at transform time. Winsorization is appropriate when you have a positive prior that the extreme values are recording errors or rare regime shifts you are not modeling.

The third lever is *outlier detection as a preprocessing filter*. `IsolationForest` is sklearn's standard tool here: it fits an ensemble of random trees that isolate anomalous points by short paths. As a preprocessing step, you fit it on training data, predict `+1` for inliers and `-1` for outliers, and either drop the outlier rows from training or carry the score as an additional feature.

```python
import numpy as np
from sklearn.ensemble import IsolationForest

rng = np.random.default_rng(0)
X_inliers = rng.normal(size=(200, 2))
X_outliers = rng.uniform(low=-6, high=6, size=(20, 2))
X = np.vstack([X_inliers, X_outliers])

detector = IsolationForest(contamination=0.1, random_state=0)
detector.fit(X)
labels = detector.predict(X)  # +1 inlier, -1 outlier
print("inliers:", int((labels == 1).sum()), "outliers:", int((labels == -1).sum()))
```

Two caveats keep this section short. First, dropping rows the model considers "outliers" is a decision with real downstream consequences - you are deciding the model never has to learn from rare events, which is sometimes correct (sensor glitches) and sometimes catastrophic (fraud, equipment failure, rare diseases). Second, contamination is a hyperparameter that should be tuned on the development data, not set to a comfortable-looking default. Module 1.9 walks through both questions in depth.

## Section 5: Feature Selection - When It Is Worth the Cost

Feature selection is often the first thing junior practitioners reach for and one of the last things experienced ones do. The reason is simple: most modern learners already incorporate selection. Lasso shrinks irrelevant coefficients to zero. Ridge tolerates correlated features. Gradient-boosted trees expose `feature_importances_` and ignore features with no predictive value. For datasets with a few hundred features and a learner with built-in regularization, an explicit feature-selection step rarely improves predictive performance and often introduces variance: the set of "selected" features differs across folds, which is a stability problem the model itself does not have.

That said, four situations make feature selection genuinely worth running.

1. **Interpretability**. A regulated environment may require a model with a small, fixed feature list, even at the cost of accuracy.
2. **Inference latency**. Each feature carries a serving cost - a database read, a featurization step, a network round-trip. Cutting half the features may matter for a tail-latency budget even when accuracy is unchanged.
3. **Near-constant features**. Columns with a single value or near-zero variance contribute nothing and waste compute. `VarianceThreshold` is the right cleanup tool.
4. **Severe small-`n` regime**. When you have far more candidate features than rows, an explicit selection step (filter or embedded) can stabilize a learner that would otherwise overfit aggressively.

Selection methods come in three families.

### Filter Methods

Filter methods rank features by a univariate statistic computed against the target, ignoring the learner. They are fast and learner-agnostic, but they are blind to interactions: two features that are individually weak but jointly strong will both be discarded.

- `VarianceThreshold` drops columns whose variance falls below a cutoff. Set the threshold low (e.g., `0.0`) to remove constant columns; set it higher to remove near-constant ones.
- `SelectKBest` keeps the top `k` features by a scoring function. The standard choices are `chi2` for non-negative features against a classification target, `f_classif` for ANOVA F-test against a classification target, and `f_regression` for regression.

```python
import numpy as np
from sklearn.datasets import make_classification
from sklearn.feature_selection import SelectKBest, VarianceThreshold, f_classif

X, y = make_classification(
    n_samples=400,
    n_features=30,
    n_informative=8,
    n_redundant=10,
    random_state=0,
)

variance = VarianceThreshold(threshold=0.01)
X_var = variance.fit_transform(X)

selector = SelectKBest(score_func=f_classif, k=10)
X_top = selector.fit_transform(X_var, y)

print("variance-pruned shape:", X_var.shape)
print("top-10 shape:", X_top.shape)
print("kept indices (in pruned matrix):", np.flatnonzero(selector.get_support()))
```

### Wrapper Methods

Wrapper methods evaluate subsets of features by retraining the underlying learner. They are slow but learner-aware and can capture interactions a filter misses.

- `RFE` recursively fits the learner, ranks features by the learner's own coefficients or importances, drops the weakest, and repeats until a target feature count remains.
- `RFECV` runs `RFE` inside cross-validation and chooses the feature count that maximizes the cross-validated score, so you do not have to specify the target count up front.

```python
import numpy as np
from sklearn.datasets import make_classification
from sklearn.feature_selection import RFECV
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold

X, y = make_classification(
    n_samples=400,
    n_features=30,
    n_informative=8,
    n_redundant=10,
    random_state=0,
)

estimator = LogisticRegression(max_iter=1000)
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
selector = RFECV(estimator=estimator, cv=cv, scoring="roc_auc", min_features_to_select=3)
selector.fit(X, y)

print("optimal number of features:", selector.n_features_)
print("selected indices:", np.flatnonzero(selector.support_))
```

`RFECV` is the most rigorous wrapper option, but it is expensive: each fold refits the learner once per candidate feature count, so the total fit count grows with both the fold count and the feature count.

### Embedded Methods

Embedded methods piggyback on a learner that already produces a feature ranking - L1-regularized linear models (Lasso) or tree ensembles with `feature_importances_`. `SelectFromModel` is the standard wrapper.

```python
import numpy as np
from sklearn.datasets import make_classification
from sklearn.feature_selection import SelectFromModel
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

X, y = make_classification(
    n_samples=400,
    n_features=30,
    n_informative=8,
    n_redundant=10,
    random_state=0,
)

selector_pipeline = Pipeline([
    ("scale", StandardScaler()),
    ("lasso_select", SelectFromModel(
        LogisticRegression(penalty="l1", solver="liblinear", C=0.5, max_iter=1000),
        threshold="median",
    )),
])

X_sel = selector_pipeline.fit_transform(X, y)
print("selected shape:", X_sel.shape)
```

Embedded selection is usually the best cost-benefit choice when the underlying model already exposes coefficients or importances: selection happens as a side effect of fitting, with no extra optimization loop.

### Selection Decision Table

| Family | Speed | Learner-aware | Interaction-aware | Stability across folds | Best when |
|---|---|---|---|---|---|
| Filter (`VarianceThreshold`, `SelectKBest`) | Fast | No | No | Moderate | Cleanup of constant/near-constant columns; very wide datasets where wrappers are infeasible |
| Wrapper (`RFE`, `RFECV`) | Slow | Yes | Yes (via the learner) | Moderate; `RFECV` is more stable than `RFE` | Modest feature count, willing to spend compute, want a learner-aware ranking |
| Embedded (`SelectFromModel` over Lasso, RF, GBM) | Fast (selection is free) | Yes | Yes | Higher | Whenever the underlying learner already produces importances or sparse coefficients |

### The Selection Leakage Pitfall

A subtle leak: running feature selection once on the full training set and then running cross-validation on the selected columns leaks information from each validation fold into the selection decision. The fix is the one Module 1.3 reused for every preprocessing step - put the selector inside the `Pipeline`, so each fold runs its own selection on its own training rows.

```python
import numpy as np
from sklearn.datasets import make_classification
from sklearn.feature_selection import SelectFromModel
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

X, y = make_classification(
    n_samples=400,
    n_features=30,
    n_informative=8,
    n_redundant=10,
    random_state=0,
)

pipeline = Pipeline([
    ("scale", StandardScaler()),
    ("select", SelectFromModel(
        LogisticRegression(penalty="l1", solver="liblinear", C=0.5, max_iter=1000),
    )),
    ("clf", LogisticRegression(max_iter=1000)),
])

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
scores = cross_validate(pipeline, X, y, cv=cv, scoring="roc_auc")
print("cv roc_auc:", scores["test_score"].mean(), "+/-", scores["test_score"].std())
```

The pipeline above fits the L1 selector independently on each fold's training set, so the selected feature set respects the fold boundary. Outside the pipeline, the selection would have peeked at the validation rows.

## Section 6: ColumnTransformer End-to-End

The previous five sections are tools. This section is the assembly. The point of `ColumnTransformer` is that a real tabular dataset has columns of different dtypes that need different preprocessing, and you want all of it inside one fittable, cloneable, picklable object that participates in cross-validation correctly. The compose user guide and the canonical mixed-types example walk through exactly this shape.

### A Mixed-Types Pipeline

```python
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer, make_column_selector
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.feature_selection import SelectFromModel
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    OneHotEncoder,
    OrdinalEncoder,
    RobustScaler,
    TargetEncoder,
)


def make_synthetic_frame(n_rows: int = 2000, random_state: int = 0) -> tuple[pd.DataFrame, np.ndarray]:
    rng = np.random.default_rng(random_state)
    df = pd.DataFrame({
        "age": rng.integers(low=18, high=80, size=n_rows).astype(float),
        "income": rng.lognormal(mean=10.0, sigma=0.6, size=n_rows),
        "tenure_months": rng.integers(low=0, high=120, size=n_rows).astype(float),
        "country": rng.choice(["US", "DE", "FR", "BR", "IN"], size=n_rows, p=[0.4, 0.2, 0.15, 0.15, 0.1]),
        "tier": rng.choice(["Bronze", "Silver", "Gold"], size=n_rows, p=[0.6, 0.3, 0.1]),
        "merchant_id": rng.integers(low=0, high=300, size=n_rows).astype(str),
    })
    # Inject realistic missingness on income and tenure
    income_missing = rng.random(size=n_rows) < 0.10
    tenure_missing = rng.random(size=n_rows) < 0.05
    df.loc[income_missing, "income"] = np.nan
    df.loc[tenure_missing, "tenure_months"] = np.nan
    # A target with mild dependence on a handful of columns
    logits = (
        0.02 * (df["age"] - 40)
        + 0.0000005 * df["income"].fillna(df["income"].median())
        + (df["tier"] == "Gold").astype(float)
        - (df["country"] == "BR").astype(float) * 0.5
    )
    proba = 1.0 / (1.0 + np.exp(-logits))
    y = (rng.random(size=n_rows) < proba).astype(int)
    return df, y


df, y = make_synthetic_frame()

# Per-dtype routing.
numeric_pipe = Pipeline([
    ("impute", SimpleImputer(strategy="median", add_indicator=True)),
    ("scale", RobustScaler()),
])

low_card_categorical_pipe = Pipeline([
    ("impute", SimpleImputer(strategy="most_frequent")),
    ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
])

ordinal_pipe = Pipeline([
    ("impute", SimpleImputer(strategy="most_frequent")),
    ("ordinal", OrdinalEncoder(categories=[["Bronze", "Silver", "Gold"]])),
])

high_card_categorical_pipe = Pipeline([
    ("impute", SimpleImputer(strategy="most_frequent")),
    ("target", TargetEncoder(target_type="binary", random_state=0)),
])

preprocess = ColumnTransformer(
    transformers=[
        ("num", numeric_pipe, make_column_selector(dtype_include=np.number)),
        ("low_card", low_card_categorical_pipe, ["country"]),
        ("ordinal", ordinal_pipe, ["tier"]),
        ("high_card", high_card_categorical_pipe, ["merchant_id"]),
    ],
    remainder="drop",
)

model = Pipeline([
    ("preprocess", preprocess),
    ("select", SelectFromModel(
        LogisticRegression(penalty="l1", solver="liblinear", C=0.5, max_iter=1000),
    )),
    ("clf", LogisticRegression(max_iter=1000)),
])

X_dev, X_test, y_dev, y_test = train_test_split(
    df, y, test_size=0.2, stratify=y, random_state=0,
)

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
scores = cross_validate(
    model, X_dev, y_dev,
    cv=cv,
    scoring=["roc_auc", "average_precision"],
    return_train_score=True,
)
print("cv roc_auc:", scores["test_roc_auc"].mean(), "+/-", scores["test_roc_auc"].std())

model.fit(X_dev, y_dev)
y_proba = model.predict_proba(X_test)[:, 1]
print("final test roc_auc:", roc_auc_score(y_test, y_proba))
print("final test avg_precision:", average_precision_score(y_test, y_proba))
```

Read the structure rather than the result. Numeric columns are routed by dtype to a median-imputer-with-indicator and a `RobustScaler`. Low-cardinality categoricals (`country`) get one-hot encoding. Ordered categoricals (`tier`) get explicit `OrdinalEncoder` with the order locked by `categories=`. High-cardinality categoricals (`merchant_id`) get cross-fitted target encoding. Feature selection runs as an embedded step over an L1-regularized logistic regression. The final classifier sees the selected feature set. The whole graph fits in one call and runs inside cross-validation correctly because every learned statistic - imputation medians, scaling IQRs, one-hot vocabularies, target-encoder mappings, L1 coefficients used for selection - lives inside the pipeline and is refit per fold.

### What This Bought You

The graph above is roughly forty lines of declarative configuration. Without `ColumnTransformer` and `Pipeline`, the same workflow is dozens of lines of imperative code that has to be repeated inside every cross-validation fold and every grid-search iteration, with new opportunities for off-by-one fold leaks each time. The compose user guide phrases this directly: composition is what makes leakage-safety automatic instead of accidental.

A reviewer reading this code can audit the preprocessing layer in one pass: which columns go where, what each transformer is, whether `handle_unknown` is set, whether the leakage-prone steps (`TargetEncoder`, imputation) are inside the pipeline. If the graph reads cleanly, the model can be reviewed; if it does not, no metric on top of it is trustworthy. That is the punchline of every preprocessing decision in the previous five sections: the audit surface is the pipeline graph.

## Did You Know?

1. The scikit-learn user guide on preprocessing notes that many learning algorithms behave better when their input features are on similar scales and free of missing values, and that the right transformer depends on the distribution of the feature and the algorithm consuming it: https://scikit-learn.org/stable/modules/preprocessing.html
2. `TargetEncoder` (sklearn 1.3+) uses an internal cross-fitting scheme during `fit_transform` to avoid the target-leakage failure mode that hand-rolled `groupby().mean()` encoders fall into: https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.TargetEncoder.html
3. `IterativeImputer` is still labeled experimental in the sklearn imputation guide and requires the explicit opt-in `from sklearn.experimental import enable_iterative_imputer` before use: https://scikit-learn.org/stable/modules/impute.html
4. The compose user guide describes `ColumnTransformer` and `make_column_selector` as the canonical pattern for routing different preprocessing to different columns of a heterogeneous DataFrame, with a worked end-to-end example for mixed numeric and categorical types: https://scikit-learn.org/stable/auto_examples/compose/plot_column_transformer_mixed_types.html

## Common Mistakes

| Mistake | Contaminated statistic or wrong assumption | Why it fails | Safer pattern |
|---|---|---|---|
| Calling `OneHotEncoder.fit` on the full dataset before splitting | Vocabulary of categories | Validation-only categories shape the encoder; production unseen categories raise | Put `OneHotEncoder(handle_unknown="ignore")` inside `Pipeline` |
| Hand-rolling `df.groupby("cat")[target].mean()` for target encoding | Per-category mean | Each row's own label contributes to its encoded value (target leakage by Module 1.3) | Use `TargetEncoder` inside `Pipeline`; it cross-fits during `fit_transform` |
| Using `OrdinalEncoder` on a nominal column for a linear model | Encoded integer | The learner sees a fictitious linear ordering | Use `OneHotEncoder` for nominal categories, or pass an explicit `categories=` only when an ordering is real |
| `StandardScaler` on heavy-tailed columns with a few extreme outliers | Mean and std | Outliers inflate std, squashing the bulk of the data near zero | `RobustScaler` or `PowerTransformer`; consider `QuantileTransformer` for very heavy tails |
| Calling `SimpleImputer.fit_transform(X)` before splitting | Imputation statistic | Validation rows shape the median; same shape as preprocessing leakage in Module 1.3 | Put the imputer inside `Pipeline`; each fold refits its own |
| `KNNImputer` on raw mixed-type, unscaled data | Distances | Categorical strings break the distance computation; unscaled numeric features dominate | Encode categoricals first, scale numerics, then run `KNNImputer` |
| Running feature selection once on the full training set then cross-validating on the selected columns | Selected feature set | Each validation fold contributed to the selection decision | Put the selector inside `Pipeline` so each fold selects on its own training rows |
| Wrapping a tree ensemble in `StandardScaler` | None - the scaler is just dead weight | Trees split on thresholds and ignore monotonic rescaling; latency without benefit | Skip scaling for tree ensembles; it is a no-op the inference path still has to evaluate |

## Quiz

### 1. A teammate hand-rolls a target encoder for a `merchant_id` column with 4,000 levels by computing `df.groupby("merchant_id")["fraud"].mean()` over the full training set, then maps each row to that value before splitting.

What is the leak, and what is the minimal fix?

<details>
<summary>Answer</summary>

The contaminated statistic is the per-category target mean. Every training row's encoded feature includes that row's own label in the mean it is mapped to, so the validation score in cross-validation is no longer testing unseen behavior. Module 1.3 names this target leakage. The minimal fix is `TargetEncoder` inside a `Pipeline`: it cross-fits during `fit_transform` so each row's training value is computed from a fold that excludes that row, and it learns a single inference mapping at the same time.

</details>

### 2. A k-NN classifier is trained on a frame with one feature ranging from 0 to 1 and another from 0 to 1,000,000.

Which scaler family is the first one you reach for, and why is `MinMaxScaler` a fragile choice in production?

<details>
<summary>Answer</summary>

Reach for `RobustScaler` first. k-NN computes distances and the larger-range feature would otherwise dominate every nearest-neighbor decision. `MinMaxScaler` is fragile because it pins the output range to the training-set minimum and maximum; an inference-time row outside that range falls outside `[0, 1]` and the learner has no calibrated behavior for that case. `RobustScaler` uses median and IQR, so a new outlier at inference time does not violate any range invariant.

</details>

### 3. A medical model imputes missing lab values with the column mean, but the missingness pattern is itself diagnostic - patients without certain readings tend to have very different outcomes than patients with them.

What feature is the model unable to learn, and what is the smallest change that lets it learn that feature?

<details>
<summary>Answer</summary>

The model cannot learn the missingness pattern itself, because mean imputation overwrites that signal. The smallest change is `SimpleImputer(strategy="median", add_indicator=True)`, or equivalently using `MissingIndicator` alongside the imputer. The indicator column is binary per imputed feature and exposes the missingness pattern directly to the learner.

</details>

### 4. A pipeline that worked locally for months breaks the first time a teammate runs it on a fresh checkout. The traceback ends with `ImportError: cannot import name 'IterativeImputer' from 'sklearn.impute'`. Both environments have the same sklearn version pinned.

What does the traceback tell you about how `IterativeImputer` differs from the other imputers in this section, and how do you fix the local environment without changing the sklearn version?

<details>
<summary>Answer</summary>

Imports that fail with a name-not-found error from a real submodule, despite a matching package version, signal that the symbol is gated rather than absent. `IterativeImputer` is still classified experimental in sklearn, so importing it requires an explicit opt-in: `from sklearn.experimental import enable_iterative_imputer` (a side-effecting import) before `from sklearn.impute import IterativeImputer`. Your environment has likely cached a partially imported `sklearn.impute` module without the experimental opt-in. Add the opt-in line above the imputer import in the pipeline file, restart any long-running Python processes, and the symbol resolves.

</details>

### 5. A team runs `SelectKBest(k=20)` once on the full training set, then evaluates the resulting model with `cross_validate` on the 20 selected columns. The held-out scores look excellent.

Why is this evaluation overconfident, and what is the fix?

<details>
<summary>Answer</summary>

The selection ran once on data that includes every cross-validation fold's validation rows. Those rows influenced which 20 features survived, so each "held-out" fold is no longer held out from the selection decision. The fix is to put `SelectKBest(k=20)` inside the `Pipeline`. Each fold then refits the selector on its own training rows, and the validation score reflects selection plus modeling on truly unseen data.

</details>

### 6. A linear model is trained on a column ordinally encoded as `Bronze=0, Silver=1, Gold=2`. The same column is then used in a random-forest classifier on the same dataset.

Why is the encoding choice acceptable for one model and questionable for the other?

<details>
<summary>Answer</summary>

For the linear model, an ordinal encoding asserts a linear relationship: a one-unit jump from Bronze to Silver is worth as much as a one-unit jump from Silver to Gold. If the underlying tier is genuinely ordered and roughly linear in the target, that is fine. For the random forest, ordinal encoding imposes a particular split order: the tree can only place thresholds along the ordinal axis. If the underlying tier ordering is real, the forest still works, but if Silver behaves more like Bronze than Gold for the target, a one-hot encoding would let the tree express that more naturally. Choose ordinal only when the ordering is real and roughly monotone in the signal.

</details>

### 7. A `RobustScaler` is followed by a `PowerTransformer(method="yeo-johnson")`. The pipeline runs without error, and validation metrics are not noticeably better than `StandardScaler` alone.

What is the redundancy here, and when would you keep the chain anyway?

<details>
<summary>Answer</summary>

`PowerTransformer` already produces an output with stabilized variance and a roughly Gaussian shape; running `RobustScaler` first does not hurt but rarely helps, because the power transform itself dampens the influence of extreme values. The redundancy is that two transformers are doing overlapping work. Keep the chain only when you want explicit control over the centering and scale of the output (for example, a downstream regularization-sensitive learner that has been tuned around unit-variance inputs); otherwise either transformer alone is usually sufficient.

</details>

### 8. A `ColumnTransformer` routes numeric columns by `make_column_selector(dtype_include=np.number)` and categorical columns by hard-coded names. In production, an upstream service starts sending the columns in a different order and adds a new numeric column.

Which routing breaks, and which one survives?

<details>
<summary>Answer</summary>

Routing by `make_column_selector(dtype_include=np.number)` survives, because it picks columns by dtype on a DataFrame and is order-independent; the new numeric column is captured automatically. Routing by hard-coded names also survives if the named columns still exist with the same names, regardless of order. The combination breaks only if the upstream change drops a named categorical column or renames it; the dtype selector is robust to both reordering and additions of new numeric columns.

</details>

## Hands-On Exercise: Build a Mixed-Types Pipeline End to End

You will assemble a full preprocessing pipeline on a synthetic mixed-types DataFrame, evaluate it inside cross-validation, and verify each leakage-safe property by deliberately breaking it and observing the bias.

### Setup

Use `sklearn.datasets.make_classification` plus a hand-built DataFrame to create at least 1,500 rows, with at least four columns: one numeric column with realistic missingness, one low-cardinality categorical (3-6 levels), one ordered categorical (3-5 ordered levels), and one medium-cardinality categorical (50-300 levels).

### Step 1: Reserve a final test set

- [ ] Split off 20% of the data as a final test set with `train_test_split` and `stratify=y`.
- [ ] Confirm the positive-class rate in the development and test splits is similar.
- [ ] Do not look at the final test metrics until the workflow is frozen.

### Step 2: Build per-dtype pipelines

- [ ] Numeric pipe: `SimpleImputer(strategy="median", add_indicator=True)` then `RobustScaler`.
- [ ] Low-cardinality categorical pipe: `SimpleImputer(strategy="most_frequent")` then `OneHotEncoder(handle_unknown="ignore")`.
- [ ] Ordered categorical pipe: `SimpleImputer(strategy="most_frequent")` then `OrdinalEncoder(categories=[<your order>])`.
- [ ] Medium-cardinality categorical pipe: `SimpleImputer(strategy="most_frequent")` then `TargetEncoder(target_type="binary", random_state=0)`.

### Step 3: Assemble a `ColumnTransformer`

- [ ] Route numeric columns with `make_column_selector(dtype_include=np.number)`.
- [ ] Route the categorical columns by name.
- [ ] Set `remainder="drop"` and confirm the resulting matrix has the column count you expect.

### Step 4: Add a feature-selection stage

- [ ] Add a `SelectFromModel` step using L1-regularized `LogisticRegression`.
- [ ] Confirm the selector is the second-to-last step in the outer `Pipeline`, with the final classifier last.

### Step 5: Evaluate inside cross-validation

- [ ] Run `cross_validate` with `StratifiedKFold(n_splits=5, shuffle=True, random_state=0)`.
- [ ] Score on `roc_auc` and `average_precision`.
- [ ] Set `return_train_score=True` to surface overfitting; if train-test gap is wide, document it as a diagnostic, not as deployment evidence.

### Step 6: Deliberately break leakage and observe the bias

- [ ] Outside the pipeline, run `TargetEncoder.fit_transform` on the full training set's medium-cardinality column, then feed the leaked column into a `cross_validate` call.
- [ ] Compare the leaked CV score to the non-leaked CV score from Step 5.
- [ ] Restore the pipeline-correct version. Note the score difference in a comment in your script.

### Step 7: Final test pass

- [ ] Refit the pipeline on the full development set.
- [ ] Score once on the final test set.
- [ ] Compare to the cross-validation mean. If they disagree by more than the cross-validation standard deviation, write a sentence about what might explain the gap (distribution shift, fold-to-fold variance, lucky split).

### Completion Check

- [ ] No transformer is fit outside the pipeline anywhere in the script.
- [ ] Every encoder, imputer, scaler, and selector lives inside the pipeline graph.
- [ ] `handle_unknown="ignore"` on the production-bound `OneHotEncoder`.
- [ ] `TargetEncoder` is the only encoder that reads `y`, and it lives inside the pipeline.
- [ ] The pipeline graph fits in one screen and a reviewer can read the column routing in one pass.

## Sources

- [Preprocessing data](https://scikit-learn.org/stable/modules/preprocessing.html)
- [Imputation of missing values](https://scikit-learn.org/stable/modules/impute.html)
- [Feature selection](https://scikit-learn.org/stable/modules/feature_selection.html)
- [Pipelines and composite estimators (`ColumnTransformer`, `make_column_selector`)](https://scikit-learn.org/stable/modules/compose.html)
- [Common pitfalls and recommended practices](https://scikit-learn.org/stable/common_pitfalls.html)
- [Column Transformer with Mixed Types (worked example)](https://scikit-learn.org/stable/auto_examples/compose/plot_column_transformer_mixed_types.html)
- [`OneHotEncoder`](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.OneHotEncoder.html)
- [`OrdinalEncoder`](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.OrdinalEncoder.html)
- [`TargetEncoder`](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.TargetEncoder.html)
- [`StandardScaler`](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html)
- [`RobustScaler`](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.RobustScaler.html)
- [`MinMaxScaler`](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.MinMaxScaler.html)
- [`PowerTransformer`](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.PowerTransformer.html)
- [`QuantileTransformer`](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.QuantileTransformer.html)
- [`SimpleImputer`](https://scikit-learn.org/stable/modules/generated/sklearn.impute.SimpleImputer.html)
- [`IterativeImputer`](https://scikit-learn.org/stable/modules/generated/sklearn.impute.IterativeImputer.html)
- [`KNNImputer`](https://scikit-learn.org/stable/modules/generated/sklearn.impute.KNNImputer.html)
- [`MissingIndicator`](https://scikit-learn.org/stable/modules/generated/sklearn.impute.MissingIndicator.html)
- [`VarianceThreshold`](https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.VarianceThreshold.html)
- [`SelectKBest`](https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.SelectKBest.html)
- [`RFE`](https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.RFE.html)
- [`RFECV`](https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.RFECV.html)
- [`SelectFromModel`](https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.SelectFromModel.html)
- [`ColumnTransformer`](https://scikit-learn.org/stable/modules/generated/sklearn.compose.ColumnTransformer.html)
- [`make_column_selector`](https://scikit-learn.org/stable/modules/generated/sklearn.compose.make_column_selector.html)
- [`IsolationForest`](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html)
- [`category_encoders` (sklearn-contrib)](https://contrib.scikit-learn.org/category_encoders/)

## Next Module

Continue to [Module 1.5: Decision Trees & Random Forests](module-1.5-decision-trees-and-random-forests/).
