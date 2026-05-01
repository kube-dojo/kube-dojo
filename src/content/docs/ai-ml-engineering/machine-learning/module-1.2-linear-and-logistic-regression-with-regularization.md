---
title: "Linear & Logistic Regression with Regularization"
description: "After this module, you will be able to choose, tune, and debug linear and logistic regression models with L1, L2, and ElasticNet regularization, interpret their coefficients responsibly, and know when a generalized linear model is the correct replacement for plain least squares."
slug: ai-ml-engineering/machine-learning/module-1.2-linear-and-logistic-regression-with-regularization
sidebar:
  order: 2
---

> **AI/ML Engineering Track** | Complexity: Intermediate | Time: 5-6 hours
> **Prerequisites**: [Module 1.1](../module-1.1-scikit-learn-api-and-pipelines/) — sklearn estimator/transformer/Pipeline contract. Comfortable NumPy and pandas.

## Learning Outcomes

- **Design** regularized regression and classification baselines that stay stable when features are correlated, high-dimensional, or weakly informative.
- **Choose** among `LinearRegression`, `Ridge`, `Lasso`, `ElasticNet`, and `LogisticRegression` based on data regime, interpretability needs, and deployment constraints.
- **Compare** L1, L2, and mixed penalties without confusing `alpha` in regression models with `C` in `LogisticRegression`.
- **Implement** leakage-safe sklearn pipelines that combine scaling and linear models, then evaluate them with task-appropriate metrics.
- **Debug** unstable coefficients, overconfident probabilities, and impossible predictions by tracing them back to scale, solver, or model-family mistakes.

## Why This Module Matters

A common production failure looks boring at first.
A binary classifier is retrained.
The feature set is mostly the same.
The tests pass.
Accuracy on a holdout slice still looks acceptable.

Then downstream behavior changes anyway.

The model starts emitting much more extreme probabilities.
A rules layer that keys off those probabilities becomes brittle.
Analysts inspect the coefficients and find that a few have grown unexpectedly large, while other features that used to matter have effectively disappeared.

Nothing about this failure requires exotic models or broken infrastructure.
It usually comes from a regularization misunderstanding.

One teammate raises `C` in `LogisticRegression` because they think it behaves like `alpha` in `Ridge`.
Another skips scaling before fitting an L1 or L2 penalty.
Someone else compares `Lasso(alpha=1.0)` and `Ridge(alpha=1.0)` as if the same numeric setting meant the same amount of shrinkage.

scikit-learn is consistent once you know its rules.
It is also unforgiving if you project the wrong mental model onto the API.
`Ridge` regularizes harder as `alpha` grows.
`LogisticRegression` regularizes harder as `C` shrinks because `C` is the inverse strength.
L1 penalties can zero coefficients exactly.
L2 penalties usually spread weight across correlated features.
And all of these behaviors depend on feature scale.

This module is about getting that mental model straight.
If you can reason about the geometry, the API stops feeling arbitrary.
If you cannot, linear models become a source of quiet mistakes that look like model drift, data drift, or threshold drift when the real problem is simpler.

## Section 1: Why Linear Models Still Matter

Linear models are not the default winner on most tabular leaderboards in 2026.
If your only objective is maximum predictive accuracy on a medium-to-large tabular problem, gradient-boosted trees usually beat them.

That is not the same as saying linear models are obsolete.

They remain the right first reach when one of a small set of properties matters more than a marginal accuracy gain.

The first property is interpretability for audits.
A coefficient vector is not the whole story of causality or business impact.
It is still a much clearer artifact than a large ensemble when a reviewer asks, "Which inputs increase risk, and by how much, all else equal?"

The second property is probability quality.
A well-regularized logistic regression often produces sensible baseline probabilities with less ceremony than more complex classifiers.
That does not exempt you from checking calibration.
It does mean linear log-odds models are a practical starting point before you move to the diagnostics in [Module 1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/).

The third property is latency.
A trained linear model is a dot product plus an intercept.
For some inference paths, that matters.
If the serving budget is below a millisecond and the feature map is already available, linear models are hard to beat operationally.

The fourth property is the low-data regime.
When you have far fewer observations than you would like, and feature engineering has already encoded much of the structure, a regularized linear model can generalize better than a high-capacity alternative that memorizes noise.

The fifth property is interface simplicity.
Many decision systems consume log-odds, signed scores, or monotone risk contributions.
`LogisticRegression` gives you log-odds geometry directly.
That can matter when the downstream component is a rule engine or a human review workflow rather than another neural layer.

The family to keep in mind in this module is:

- `LinearRegression` for plain least squares.
- `Ridge` for L2-regularized regression.
- `Lasso` for L1-regularized regression.
- `ElasticNet` for a mixture of L1 and L2.
- `LogisticRegression` for linear classification in log-odds space, with regularization built in.
- `SGDRegressor` and `SGDClassifier` when the data volume or update pattern pushes you toward incremental optimization.

The main mistake practitioners make is assuming these models are "simple" and therefore safe to treat casually.

They are simple in form.
They are not trivial in behavior.

A linear model is only as trustworthy as your handling of scale, collinearity, regularization strength, and evaluation protocol.
Those are engineering concerns, not academic decoration.

When linear models work well, they do so because the inductive bias is tight.
You are explicitly saying that a weighted sum of features is the right representation, or at least a good-enough approximation, and that a modest amount of shrinkage is preferable to a more flexible but more fragile hypothesis class.

That bias is useful when:

- the features already carry domain structure,
- the dataset is not huge,
- you need fast and stable training,
- you need a model that can be inspected directly,
- or you need a dependable baseline that tells you whether more complex models are earning their complexity.

They are not a replacement for trees, boosted ensembles, or deep models.
They are a disciplined starting point.
And in some systems, they remain the final production choice for entirely rational reasons.

Two more practical points matter before we get into the math.

First, linear models are often the easiest place to spot a data issue.
If a regularized model still explodes, produces unstable coefficients, or assigns extreme weight to an obviously suspect feature, the problem is often upstream.
That is useful diagnostic pressure.

Second, linear models are composable.
They fit cleanly into sklearn pipelines, cross-validation, and inspection workflows.
You already covered pipeline mechanics in [Module 1.1](../module-1.1-scikit-learn-api-and-pipelines/).
Here, the important point is narrower:
regularization only behaves as intended if the preprocessing inside that pipeline makes coefficient magnitudes comparable.

That is why this module spends more time on shrinkage geometry and parameter meaning than on sklearn plumbing.

## Section 2: OLS and the Geometry of Fit

Start with ordinary least squares.

For a design matrix `X` and target vector `y`, plain linear regression seeks weights `w` that minimize squared error.

In the textbook full-rank setting, the closed-form solution is:

`w = (X^T X)^(-1) X^T y`

This expression is useful because it tells you where instability comes from.

Everything depends on `X^T X`.
If the columns of `X` are nearly linearly dependent, then `X^T X` becomes ill-conditioned or near-singular.
In that case, tiny changes in `y` can produce large swings in `w`.

That is multicollinearity.

The model may still fit the training data well.
Predictions may even remain decent on nearby points.
But the coefficient vector becomes unstable.
Interpretation gets unreliable.
Retraining on a slightly different sample can produce materially different weights.

This is why people sometimes see sign flips between two features that encode similar information.
The model is not discovering new physics.
It is distributing credit across redundant directions in feature space.

You can diagnose collinearity in several ways.
One common diagnostic is the variance-inflation factor, or VIF.
This module will not deep-dive regression diagnostics, but the important intuition is simple:
if one feature can be predicted well by the others, then its coefficient estimate is fragile.

From a geometric perspective, OLS is projecting `y` onto the column space of `X`.
If the space contains nearly overlapping directions, the projection itself may still be clear while the decomposition into coefficients is not.

That distinction matters.

Prediction stability and coefficient stability are related, but they are not identical.
Regularization is often introduced because you want both a predictive model and a coefficient vector that does not move wildly when the sample changes.

In sklearn, `LinearRegression` gives you the plain least-squares baseline.

```python
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

rng = np.random.default_rng(0)

n_samples = 240
x1 = rng.normal(size=n_samples)
x2 = x1 + rng.normal(scale=0.03, size=n_samples)
x3 = rng.normal(size=n_samples)
x4 = 0.5 * x1 - 0.3 * x3 + rng.normal(scale=0.05, size=n_samples)

X = pd.DataFrame(
    {
        "x1": x1,
        "x2": x2,
        "x3": x3,
        "x4": x4,
    }
)

y = 3.0 * x1 - 2.5 * x3 + rng.normal(scale=0.4, size=n_samples)

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=0,
)

model = LinearRegression()
model.fit(X_train, y_train)

print("Coefficients:")
print(pd.Series(model.coef_, index=X.columns).round(3))
print("Intercept:", round(model.intercept_, 3))
print("Test R^2:", round(model.score(X_test, y_test), 3))
```

On a dataset like this, you will often get a respectable `R^2`.
You may also see that the weights on `x1`, `x2`, and `x4` are less stable than you expected.
They are competing to explain overlapping variance.

That does not mean `LinearRegression` is wrong.
It means the problem is under-regularized for the question you are asking.

The core limitation of OLS in practice is not that squared error is fundamentally bad.
It is that the unpenalized solution pays no price for large coefficients.
If the geometry of `X` makes large weights convenient, OLS will use them.

That is why the natural next step is not "abandon linear models."
It is "add a penalty."

Before we do that, there is one edge case you should be able to predict.

> **Pause and predict**
> What happens when `n_features > n_samples` for `LinearRegression`?

`X^T X` becomes singular.
The inverse in the textbook closed form does not exist.
In practice, standard least-squares solvers return one of infinitely many solutions that achieve the same minimum training error.
For the standard `lstsq`-style solver, that is typically the minimum-norm solution.
The problem is still underdetermined.
Regularization makes it well-posed by preferring smaller coefficients.

That point is not theoretical.
High-dimensional small-data settings are common in engineered feature spaces.

A few operational takeaways follow from the OLS baseline.

First, use `LinearRegression` when you want the cleanest unregularized reference.
It tells you what the data wants to do before you constrain it.

Second, treat the coefficients with caution when features are correlated.
A nice training score does not certify stable attribution.

Third, remember that OLS can become a compute issue at scale.
For very large or streaming data, you do not want a full closed-form or batch least-squares workflow.
That is where `SGDRegressor` becomes relevant.
It optimizes incrementally and can train with `partial_fit`, which matters if the design matrix is too large for comfortable in-memory batch optimization.

You should still learn OLS first.
Every regularized linear model in this module is best understood as OLS plus a structured preference against large or unstable weights.

### Why regularization is the natural answer

If collinearity makes many coefficient vectors nearly equivalent in fit quality, you need a tie-breaker.

L2 regularization says:
prefer the smaller overall weight vector.

L1 regularization says:
prefer a small overall weight vector, and if possible, set some coordinates exactly to zero.

ElasticNet says:
do both, because pure sparsity and pure shrinkage each have failure modes.

That is the arc of the rest of this module.

## Section 3: Ridge (L2)

Ridge regression adds an L2 penalty to least squares.

The objective is:

`min_w ||Xw - y||_2^2 + alpha * ||w||_2^2`

The first term wants low residual error.
The second term discourages large coefficients.

The critical parameter is `alpha`.

Higher `alpha` means stronger shrinkage.
At `alpha = 0`, Ridge reduces to the unregularized least-squares problem in spirit.
As `alpha` grows, the solution is pulled toward zero.

The geometric intuition is more useful than the formula alone.

Think of the unregularized loss surface as a bowl in coefficient space.
If the data is well-conditioned, the bowl is roundish.
If the data is collinear, the bowl becomes elongated.
There are directions where the loss changes very slowly and directions where it changes quickly.

Those slow directions are the dangerous ones.
A large movement in coefficient space may barely change training error.
That is exactly where OLS becomes unstable.

Ridge fixes this by adding curvature everywhere.
It shrinks all coefficients toward zero, but not uniformly in a naive sense.
The amount of shrinkage you observe per feature depends on the geometry of the loss in that direction.
Directions with weak identifiability get pulled hardest because the penalty resolves the ambiguity.

That is why Ridge is often the first safe answer to multicollinearity.

It does not try to pick one winner among correlated features.
It tends to spread weight across them.
If your stakeholders care about stable attribution rather than sparse feature selection, that is usually an advantage.

### Worked example: shrinkage on correlated features

The code below creates a synthetic regression problem with correlated features.
Then it fits `Ridge(alpha=1.0)` and `Ridge(alpha=100.0)` and prints coefficient magnitudes.

```python
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split

rng = np.random.default_rng(0)

n_samples = 480

z1 = rng.normal(size=n_samples)
z2 = rng.normal(size=n_samples)
z3 = rng.normal(size=n_samples)

X = pd.DataFrame(
    {
        "f1": z1 + rng.normal(scale=0.05, size=n_samples),
        "f2": z1 + rng.normal(scale=0.05, size=n_samples),
        "f3": z2 + rng.normal(scale=0.05, size=n_samples),
        "f4": z2 + rng.normal(scale=0.05, size=n_samples),
        "f5": z3 + rng.normal(scale=0.05, size=n_samples),
        "f6": z3 + rng.normal(scale=0.05, size=n_samples),
        "f7": rng.normal(size=n_samples),
        "f8": rng.normal(size=n_samples),
    }
)

true_w = np.array([2.8, 0.0, -2.2, 0.0, 1.6, 0.0, 0.0, 0.0])
y = X.to_numpy() @ true_w + rng.normal(scale=0.6, size=n_samples)

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=0,
)

for alpha in [1.0, 100.0]:
    model = Ridge(alpha=alpha)
    model.fit(X_train, y_train)

    coef = pd.Series(model.coef_, index=X.columns)
    print(f"\nalpha={alpha}")
    print("absolute coefficient magnitudes:")
    print(coef.abs().round(3).sort_values(ascending=False))
    print("L2 norm of coef_:", round(np.linalg.norm(model.coef_), 3))
    print("test R^2:", round(model.score(X_test, y_test), 3))
```

What should you expect before you run it?

You should expect the `alpha=100.0` model to have a smaller coefficient norm.
You should also expect the largest magnitudes to be pulled inward.
Depending on noise, test performance may stay similar or even improve slightly if the smaller model reduces variance.

The key verification is not that every individual coefficient shrinks by the same amount.
It is that the overall solution is less aggressive.

### Why scaling matters for Ridge

Ridge regularizes coefficients.
It does not regularize features directly.

That sounds obvious, but it is the source of a major mistake.

Suppose one feature is measured in tiny fractions and another in thousands of units.
A model can represent the same predictive effect with a huge coefficient on the tiny-scale feature or a tiny coefficient on the large-scale feature.
If you penalize coefficients without standardizing features, the large-scale feature is effectively cheaper to use.

That means an unscaled Ridge model can under-penalize large-scale features and over-penalize small-scale features.

This is why the practical pattern is:
scale first, then regularize.

You will cover preprocessing details more formally in [Module 1.4](../module-1.4-feature-engineering-and-preprocessing/).
For this module, keep the rule simple:
if you are using L1 or L2 regularization on numeric features, `StandardScaler` is usually part of the baseline pipeline.

### Choosing `alpha`

`alpha` is not universal.
Its useful range depends on sample size, feature scale, and noise structure.
You should not guess it from intuition alone.

The standard workflow is cross-validation.
`RidgeCV` exists for exactly this reason.

`RidgeCV` is convenient because sklearn also supports generalized cross-validation, or GCV, as a built-in shortcut.
GCV is computationally attractive for some Ridge settings because it approximates leave-one-out behavior without naively retraining a full model for each holdout.

That does not mean you should always treat the chosen `alpha` as gospel.
It means Ridge gives you a disciplined way to search the bias-variance tradeoff rather than pretending the unregularized solution is automatically sensible.

A few practical interpretations help.

If the selected `alpha` is tiny, the data may already be well-conditioned or richly informative.
If the selected `alpha` is large, the model may be telling you that the feature space is noisy, redundant, or simply too flexible for the amount of data available.

In small-data settings, a large `alpha` is often a sign of healthy skepticism rather than underfitting by definition.

### When Ridge is usually the right first answer

Reach for Ridge first when:

- you suspect multicollinearity,
- you care about coefficient stability more than sparsity,
- your feature count is not tiny relative to sample size,
- or you want an auditable baseline that behaves predictably under retraining.

Ridge is conservative.
That is usually an advantage in early model selection.

It says:
keep the linear model, but stop letting it express every fragile direction at full strength.

### Ridge does not do feature selection

One more point matters operationally.

Ridge rarely sets coefficients exactly to zero.
If you need a sparse model for storage, explanation, or manual review reasons, Ridge alone is not the tool.
It shrinks.
It does not select.

That is where Lasso enters.

## Section 4: Lasso (L1)

Lasso replaces the squared L2 norm penalty with an L1 norm penalty.

The objective is:

`min_w (1 / (2 * n_samples)) * ||Xw - y||_2^2 + alpha * ||w||_1`

Two details matter immediately.

First, the penalty is L1 rather than L2.
That changes the geometry completely.

Second, the squared-error term here is normalized by `1 / (2 * n_samples)`.
Ridge in sklearn is typically written without that normalization in the objective statement.
Because the forms differ, the same numeric `alpha` does not mean the same effective penalty between Lasso and Ridge.

Do not compare `Lasso(alpha=1.0)` to `Ridge(alpha=1.0)` as if they were parallel settings.
They are not.

### Why L1 creates sparsity

The geometric explanation is worth learning once and keeping for the rest of your career.

In coefficient space, the L2 constraint region is round.
The L1 constraint region has corners aligned with the axes.

When the loss contours expand outward from the unconstrained optimum, they are more likely to first touch the L1 region at a corner.
A corner means one or more coordinates are exactly zero.

That is the source of sparsity.

In practice, Lasso can perform both shrinkage and variable selection.
It is appealing when you believe many features are noise and you want the model to express that belief directly.

This often makes Lasso more interpretable to non-specialists.
A shorter coefficient list is easier to inspect than a dense one.

The danger is that sparsity can look more authoritative than it really is.

If multiple features are correlated and interchangeable, Lasso may select one and zero the others.
A different resample may select a different representative.
The resulting sparse set can be unstable even when predictive performance is fine.

That is not a bug in sklearn.
It is a consequence of the L1 geometry.

### Worked example: Lasso on informative features plus correlated proxies and noise

The code below builds a regression problem with:

- five informative base features,
- five correlated proxy features that carry overlapping signal but are not the true generating coordinates,
- and ten pure noise features.

Then it fits `Lasso` twice on two independently generated draws from the same process.

```python
import numpy as np
import pandas as pd
from sklearn.linear_model import Lasso

def make_dataset(seed: int):
    rng = np.random.default_rng(seed)
    n_samples = 400

    base = rng.normal(size=(n_samples, 5))
    proxy = base + rng.normal(scale=0.08, size=(n_samples, 5))
    noise = rng.normal(size=(n_samples, 10))

    X = np.hstack([base, proxy, noise])
    columns = [f"x{i}" for i in range(X.shape[1])]

    true_w = np.array([2.5, -2.0, 1.8, 0.0, 1.2] + [0.0] * 15)
    y = X @ true_w + rng.normal(scale=0.5, size=n_samples)

    return pd.DataFrame(X, columns=columns), y

for seed in [0, 1]:
    X, y = make_dataset(seed)
    model = Lasso(alpha=0.1, max_iter=20000)
    model.fit(X, y)

    coef = pd.Series(model.coef_, index=X.columns)
    non_zero = coef[coef != 0.0]

    print(f"\nseed={seed}")
    print("non-zero coefficient count:", int((coef != 0.0).sum()))
    print(non_zero.round(3).sort_values(key=np.abs, ascending=False))
```

What should you expect?

You should expect most of the pure noise coordinates to be zeroed out.
You should also expect that among highly correlated candidates, Lasso may choose different survivors across different samples.

That is valuable and dangerous at the same time.

It is valuable because the model is expressing parsimony.
It is dangerous because the selected set can be treated as a stable truth when it is only one reasonable sparse encoding of the signal.

### Lasso is not a scientific discovery engine

Because Lasso can zero features exactly, people sometimes overread it.

A non-zero coefficient does not prove a feature is truly causal or uniquely important.
A zero coefficient does not prove a feature is globally irrelevant.
It only means that, under the current sample, scale, and penalty, the penalized optimum chose that sparse representation.

This is especially important in domains with correlated measurement channels.
If several features encode similar information, Lasso may pick one almost arbitrarily.

If you need stable groups rather than arbitrary winners, move toward ElasticNet.

### Choosing `alpha` for Lasso

As with Ridge, you should not hard-code `alpha` from intuition.

`LassoCV` is the standard baseline for cross-validated selection.

Because Lasso paths can change structure as `alpha` varies, it is often useful to inspect the regularization path directly.
The path shows which coefficients enter, leave, or remain zero as the penalty changes.

sklearn exposes tooling around that family of ideas, including `lars_path`, and the official coordinate-descent path example is worth studying once you know the basics:
`https://scikit-learn.org/stable/auto_examples/linear_model/plot_lasso_coordinate_descent_path.html`

The point of path inspection is not aesthetic.
It helps you see whether your feature selection is robust or knife-edge.

### Pause and predict

> **Pause and predict**
> Why is comparing `Lasso(alpha=1.0)` to `Ridge(alpha=1.0)` misleading?

Because the objectives are normalized differently and the norms are different.
Lasso uses `(1 / (2 * n_samples)) * ||Xw - y||_2^2 + alpha * ||w||_1`.
Ridge uses a different objective scaling and an L2 penalty.
The same numeric `alpha` does not represent the same effective regularization strength across the two models.
Tune each separately.

### Lasso wants scaling even more than you think

Everything we said about Ridge and feature scale applies here too.

In fact, Lasso can become even more misleading on unscaled data because the selection effect itself depends on the relative cost of coefficients.
An unscaled model may appear to be doing feature selection when it is actually doing unit-selection.

That is not acceptable.

The minimal safe baseline is a pipeline with `StandardScaler` followed by `Lasso`.

Again, do not re-learn pipeline mechanics here.
The only point that matters is conceptual:
if coefficient magnitude is the thing you penalize, you must make coefficient magnitudes comparable.

### Lasso versus feature screening

There is a difference between using Lasso as part of a model and using it as a pre-filter for a later model.

If you fit Lasso on all available data and then carry the selected feature set into a downstream evaluation, you have created a leakage pathway.
The selection step saw the full target.
Feature selection must live inside the cross-validation loop or inside the pipeline used by the CV procedure.

That evaluation protocol belongs in [Module 1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/).
The narrow lesson here is:
L1-based selection is powerful enough to create a convincing but invalid experiment if you place it outside the split boundary.

## Section 5: ElasticNet

ElasticNet mixes L1 and L2 penalties.

The objective is:

`min_w (1 / (2 * n_samples)) * ||Xw - y||_2^2 + alpha * l1_ratio * ||w||_1 + 0.5 * alpha * (1 - l1_ratio) * ||w||_2^2`

It exists because pure Lasso and pure Ridge each have a weakness.

Lasso is good at sparsity.
It is not stable when groups of correlated features all carry similar signal.
It tends to choose one representative and drop the rest.

Ridge is good at stability.
It is not sparse.
It keeps correlated groups together, but it also keeps a lot of weak features alive at small magnitudes.

ElasticNet gives you a compromise.

The L1 component encourages zeros.
The L2 component stabilizes the solution and reduces the arbitrary winner-take-all behavior that pure Lasso shows on correlated groups.

That makes ElasticNet a strong default when your feature space has both of these traits:

- many weak or noisy features,
- and meaningful clusters of correlated predictors.

A practical starting point is `l1_ratio=0.5`.

That is not magic.
It is simply a defensible midpoint that says:
I want both selection pressure and correlation tolerance.

From there, cross-validation should decide whether you want to move closer to Lasso or closer to Ridge.

`ElasticNetCV` exists to tune both `alpha` and `l1_ratio`.

This is one of the few cases where a slightly larger search space is justified even in a first-pass baseline, because the problem structure often genuinely requires both knobs.

### When ElasticNet is better than Lasso

Suppose your dataset has several families of engineered features that all describe the same latent behavior from different angles.

Pure Lasso may pick one member from each family and zero the others.
That is sparse, but it can be brittle.
A small sample change can swap which member survives.

ElasticNet tends to keep small grouped weight across those families while still zeroing truly irrelevant directions.
You trade some sparsity for more stability.

That trade is often worth it.

### The classification analog

The same intuition carries over to logistic regression.

If you want the classification analog of ElasticNet, use `LogisticRegression` with an ElasticNet-style setup in versions and solvers that support it.
The mental model is the same:
`l1_ratio=0.5` is a reasonable starting point when you want partial sparsity without pure L1 instability.

The exact API details vary with sklearn version and solver support, so verify them against the docs for your installed version.
The important conceptual bridge is that regularization geometry does not stop mattering just because the loss changed from squared error to log loss.

### A minimal ElasticNet example

```python
import numpy as np
from sklearn.linear_model import ElasticNet
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

rng = np.random.default_rng(0)
X = rng.normal(size=(320, 12))
X[:, 6:] = X[:, :6] + rng.normal(scale=0.1, size=(320, 6))
y = 2.0 * X[:, 0] - 1.5 * X[:, 2] + 1.2 * X[:, 7] + rng.normal(scale=0.7, size=320)

model = Pipeline(
    [
        ("scale", StandardScaler()),
        ("enet", ElasticNet(alpha=0.1, l1_ratio=0.5, max_iter=20000)),
    ]
)

model.fit(X, y)

coef = model.named_steps["enet"].coef_
print("non-zero coefficients:", int((coef != 0.0).sum()))
print("L2 norm:", round(np.linalg.norm(coef), 3))
```

This code is not meant to prove optimality.
It is meant to reinforce the pattern:
mixed penalties are easy to express in sklearn, and they are often the right answer when neither pure sparsity nor pure shrinkage is enough.

## Section 6: Logistic Regression

Logistic regression is a linear model for log-odds.

Its core equation is:

`log(p / (1 - p)) = w^T x + b`

That equation is worth internalizing because it resolves several recurring misunderstandings.

The model is linear in the transformed response space, not in the probability itself.
The raw score `w^T x + b` is mapped through the logistic function to produce a probability between zero and one.

In sklearn:

- `predict_proba` returns probabilities.
- `predict` returns class labels using a threshold of `0.5` by default in the binary case.

That default threshold is not sacred.
Threshold tuning belongs in [Module 1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/).
For this module, keep the distinction clean:
probability estimation and label thresholding are different operations.

### The defaults you must know

There are a handful of `LogisticRegression` defaults and conventions that trip people repeatedly.

#### Default penalty behavior

Historically, `penalty='l2'` has been the default.
In sklearn `1.8`, that parameter is deprecated and scheduled for removal in `1.10`.
The newer API direction is to express the regime through `l1_ratio`:
`l1_ratio=0` for the default L2 behavior,
`l1_ratio=1` for L1 behavior,
and values between zero and one for ElasticNet-style mixtures.

Most readers still encounter environments at or below `1.8`, so code examples in this module use `penalty="l2"` because it still runs there.
Do not be surprised if a later environment asks you to move to the newer vocabulary.

> **Version callout**
> If a reader on a newer sklearn version gets an error around `penalty`, the underlying lesson is not invalid.
> The conceptual default is still L2 regularization.
> What changed is the way the API wants you to spell it.

#### `C` is the inverse regularization strength

This is the single most frequent logistic-regression mistake in sklearn.

`C=1.0` is the default.

Smaller `C` means stronger regularization.
Larger `C` means weaker regularization.

This is the SVM convention.
It is the opposite of the `alpha` direction used by `Ridge`, `Lasso`, and `ElasticNet`.

The reliable mental conversion is:

`alpha = 1 / C`

Do not push that identity too literally across different losses and scalings.
Do use it as a sign convention.
If someone says "I want stronger regularization" in logistic regression, the first question is:
do you mean a smaller `C`?

#### Solver behavior

`solver='lbfgs'` has been the default since `0.22`.

For multiclass problems, multinomial loss is handled automatically for `n_classes >= 3` with all solvers except `liblinear`.
`liblinear` is binary-only.
If you truly want one-vs-rest behavior around `liblinear`, wrap it with `OneVsRestClassifier`.

The old `multi_class` argument has been removed.
Do not write `multi_class='multinomial'` in current code samples.
That parameter is part of the old mental model, not the current API surface.

### Worked example: coefficient norm versus `C`

The following example trains logistic regression models with three different values of `C` on the same binary classification task.
It prints the L2 norm of the coefficients and computes ROC AUC correctly from `predict_proba`.

```python
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

X, y = make_classification(
    n_samples=800,
    n_features=12,
    n_informative=5,
    n_redundant=4,
    n_repeated=0,
    n_classes=2,
    class_sep=0.8,
    random_state=0,
)

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=0,
    stratify=y,
)

for C in [0.01, 1.0, 100.0]:
    model = Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "logreg",
                LogisticRegression(
                    C=C,
                    penalty="l2",
                    solver="lbfgs",
                    max_iter=2000,
                ),
            ),
        ]
    )

    model.fit(X_train, y_train)

    coef_norm = np.linalg.norm(model.named_steps["logreg"].coef_)
    proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, proba)

    print(f"C={C}")
    print("coefficient norm:", round(coef_norm, 3))
    print("ROC AUC:", round(auc, 3))
    print()
```

There are two things you should verify.

First, as `C` grows, the coefficient norm should usually grow because the penalty weakens.
At very small `C`, the model is strongly shrunk.

Second, ROC AUC is computed from predicted probabilities, not from `model.score`.

That distinction is non-negotiable.

`LogisticRegression.score(X_test, y_test)` returns mean accuracy.
Accuracy may be useful.
It is not ROC AUC.
Reporting it as ROC AUC is a metric honesty failure, not a naming preference.

### Pause and predict

> **Pause and predict**
> What happens to coefficient magnitudes as `C` varies from `0.001` to `1000`?

As `C` grows, regularization weakens and coefficient magnitudes generally increase toward the weakly penalized maximum-likelihood fit, which is the logistic analog of the unregularized linear solution.
As `C` shrinks, regularization strengthens and coefficients shrink toward zero under L2, or can be pushed exactly to zero under L1-compatible setups.

### Logistic regression is often a probability baseline first

A useful practitioner framing is this:
logistic regression is not only a classifier.
It is often your first probability model.

That affects how you inspect it.

Look at:

- probability distributions,
- separation between classes,
- calibration behavior,
- and how coefficient magnitudes change under regularization.

Do not reduce the model to a single accuracy score and move on.

Especially on imbalanced or threshold-sensitive tasks, the value of logistic regression is often that it gives you a transparent probability surface whose errors you can reason about.

### Cross-validating `C`

Just as `RidgeCV`, `LassoCV`, and `ElasticNetCV` help with regression penalties, `LogisticRegressionCV` exists for cross-validated selection of `C`.

Use it when the regularization setting is genuinely part of the modeling question rather than a quick demo choice.

The same caution applies:
do not interpret the chosen `C` out of context.
A tiny `C` may be exactly right if the data is noisy or the feature map is oversized.
A large `C` may be right if the signal is clean and scaling is appropriate.

### L1 and ElasticNet in logistic regression

The conceptual translation from regression is direct.

- L2 logistic regression gives dense shrinkage.
- L1 logistic regression can induce sparsity.
- ElasticNet-style logistic regression balances the two.

The practical constraint is solver support and version-specific API vocabulary.
That is an implementation detail you can check in the docs.
The modeling lesson is the same one you already learned:
if features are correlated and you need stability, pure L1 may be too brittle;
if you want sparsity but not arbitrary winner selection, mixed penalties are often the better starting point.

### Multiclass behavior in current sklearn

You no longer need to force `multi_class='multinomial'` in ordinary modern usage.
For multiclass problems, sklearn handles multinomial behavior automatically for supported solvers.
If you see older code carrying explicit `multi_class` settings, treat that as migration debt unless you have a specific compatibility reason.

The only persistent exception to remember is `liblinear`.
It is binary.
If you need true multiclass support without changing solver, you wrap it in `OneVsRestClassifier`.

### GLMs briefly

There is one more branch of the linear-model family that practitioners should know even if they do not study it deeply at first pass.

Sometimes the problem is not "which penalty should I use?"
The problem is "why am I using plain linear regression for the wrong target type?"

If your target is a count or strictly positive quantity, the link function and variance structure of `LinearRegression` are often wrong.

#### `PoissonRegressor`

Use `PoissonRegressor` for non-negative count targets such as page views, defect counts, or claims frequency.

The reason is not merely that counts are non-negative.
It is that the mean-variance relationship and log link are part of the modeling assumption.
A plain linear regression can predict negative counts and treats the target noise structure as if it were symmetric constant-variance Gaussian noise.
That is the wrong geometry.

If you have been taking `np.log(y)` and then fitting `LinearRegression` just to make a count target behave, that is a sign to check whether the GLM is the cleaner tool.

#### `GammaRegressor`

Use `GammaRegressor` for strictly positive continuous targets with roughly constant coefficient of variation, such as severity-like amounts or duration-like quantities where variance scales with the mean.

Again, the key issue is not only positivity.
It is that the response distribution and link function are better aligned to the target behavior than plain least squares.

#### `TweedieRegressor`

Use `TweedieRegressor` when you need a broader family controlled by a `power` parameter.
It covers Poisson-like behavior at `power=1`, Gamma-like behavior at `power=2`, and the compound-Poisson regime in between, commonly expressed around `power=1.5`.

This is useful when the target mixes a point mass structure and a positive continuous component more naturally than Gaussian regression does.

These are still linear models in the sense that the linear predictor remains central.
They are different in how that predictor maps to the response.

The practical lesson is simple:
if you are fighting the target type with transforms and hoping least squares will cope, you may be using the wrong member of the family.

### Practitioner Playbook

The table below is the short operational version of the module.

| Problem signal | First reach | Why |
|---|---|---|
| I want an auditable baseline for a numeric or binary target | `Ridge` for regression, `LogisticRegression` with L2 for classification | Dense shrinkage is stable, easy to inspect, and usually less brittle than sparse selection on first pass |
| Stakeholders need feature attribution and I care about coefficient stability | `Ridge` | Correlated features tend to share weight rather than forcing arbitrary single-feature winners |
| Stakeholders need a shorter feature list and I suspect many columns are noise | `Lasso` or `ElasticNet` | L1 can zero useless coefficients; ElasticNet is safer if correlated groups matter |
| Half my features are weak, redundant, or correlated proxies | `ElasticNet` | Mixed penalties give selection pressure without pure L1 instability |
| My target is a count and the linear model predicts negatives | `PoissonRegressor` | The link function and mean-variance structure are more appropriate for count data |
| Latency budget is below a millisecond and the feature map is already materialized | Linear model family | Inference is essentially one dot product plus an intercept |
| The dataset is huge or arrives as a stream and full batch fitting is awkward | `SGDClassifier` or `SGDRegressor` with `partial_fit` | Incremental optimization handles large or streaming workloads better than batch solvers |
| I have about a hundred rows and several dozen features | `Ridge` with a relatively strong `alpha` search | High-bias shrinkage is often safer than letting trees or sparse selection overfit small samples |

Calibration note:
`LogisticRegression` with L2 often gives a strong calibrated-probability baseline, but you still need the diagnostics in [Module 1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/) if probability quality matters.

## Did You Know?

1. The sklearn linear-model user guide defines `Ridge` as penalized least squares with `alpha` controlling how strongly coefficients are shrunk toward zero: https://scikit-learn.org/stable/modules/linear_model.html
2. The `LogisticRegression` API documents `C` as the inverse of regularization strength, so smaller values mean stronger regularization: https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html
3. The sklearn linear-model documentation shows that Lasso and ElasticNet use a squared-error term normalized by `1 / (2 * n_samples)`, which is one reason the same `alpha` is not directly comparable to Ridge: https://scikit-learn.org/stable/modules/linear_model.html
4. sklearn ships dedicated generalized linear models such as `PoissonRegressor` for targets where plain least squares uses the wrong link function: https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.PoissonRegressor.html

## Common Mistakes

| Mistake | What goes wrong | Why | Safer pattern |
|---|---|---|---|
| Thinking higher `C` means more regularization in `LogisticRegression` | Coefficients get larger and probabilities can become more extreme when you expected more shrinkage | `C` is the inverse regularization strength | If you want stronger regularization, make `C` smaller |
| Comparing `Ridge(alpha=1)` directly to `Lasso(alpha=1)` | You think one model is harsher or milder for the wrong reason | The objectives use different norms and different loss normalizations | Tune `alpha` separately for each model family |
| Skipping `StandardScaler` before L1 or L2 penalties | Large-scale features become effectively cheaper to use, distorting coefficients and selection | Regularization acts on coefficient magnitude, not raw feature importance | Put scaling inside the pipeline before the linear model |
| Using `LinearRegression` on count or strictly positive targets | You get impossible negative predictions or the wrong noise assumptions | Least squares uses the wrong link function and variance structure | Reach for `PoissonRegressor`, `GammaRegressor`, or `TweedieRegressor` |
| Reporting `model.score(X_test, y_test)` as ROC AUC for `LogisticRegression` | Stakeholders are shown accuracy under the wrong metric label | `.score` returns mean accuracy for classifiers | Compute `roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])` |
| Setting `multi_class='multinomial'` in current sklearn code | You trigger migration noise or version errors | The old argument has been removed; multinomial handling is automatic for supported solvers | Omit `multi_class`; use a current solver such as `lbfgs` |
| Using pure Lasso for selection on strongly correlated features and trusting the exact chosen set across runs | Different samples choose different representatives, which looks like instability or contradiction | L1 prefers sparse corners and may pick one feature from a correlated group arbitrarily | Prefer `ElasticNet` when correlated groups matter |
| Calling `LogisticRegression(penalty='none')` as if it were the current stable spelling | Newer versions may reject or deprecate the configuration | The API vocabulary has shifted toward `l1_ratio` and current documented defaults | For standard L2 behavior, rely on the default direction with `l1_ratio=0`; for effectively unregularized fits, use the documented large-`C` or equivalent pattern for your installed version |

## Quiz

### 1. A teammate sets `LogisticRegression(C=10)` because they want stronger regularization.
What did they actually do?

<details>
<summary>Answer</summary>

They weakened regularization.
In sklearn logistic regression, `C` is the inverse regularization strength.
Larger `C` means less penalty, not more.
The smallest-correction fix is to lower `C`, not raise it.

</details>

### 2. A `Lasso` model selects eight features on one training sample and six on another, with several different survivors across the two fits.
The data has obvious correlated feature groups.
What explains this, and what is the lowest-cost fix?

<details>
<summary>Answer</summary>

This is classic L1 instability under correlation.
Lasso prefers sparse solutions and may pick one representative from a correlated group arbitrarily.
The lowest-cost fix is usually to try `ElasticNet` so the L2 component stabilizes grouped features while preserving some sparsity.

</details>

### 3. A regression model for daily visit counts predicts negative values for some rows.
The team says, "We can just clip them to zero."
What is the better diagnosis?

<details>
<summary>Answer</summary>

The bigger issue is model-family mismatch, not post-processing.
Counts are better handled by a GLM such as `PoissonRegressor`, because the link function and variance assumptions are different from plain least squares.
Clipping negative predictions hides the symptom without fixing the fit geometry.

</details>

### 4. A team runs `LogisticRegression()` on a four-class problem with current sklearn and sees old code that still sets `multi_class='multinomial'`.
What should the modern code do?

<details>
<summary>Answer</summary>

It should usually drop the explicit `multi_class` argument.
Current sklearn handles multinomial multiclass behavior automatically for supported solvers such as `lbfgs`.
Only `liblinear` remains a special case because it is binary-only.

</details>

### 5. A `Ridge` model fit on raw, unscaled features assigns a very small coefficient to a feature measured in millions of units.
A reviewer concludes the feature barely matters.
Why is that conclusion weak?

<details>
<summary>Answer</summary>

Coefficient magnitude is not comparable across features when scales differ.
A tiny coefficient on a huge-scale feature can correspond to a large predictive contribution.
Without scaling, both interpretation and regularization are distorted.
Inspect standardized fits before drawing coefficient-based importance conclusions.

</details>

### 6. A model wrapper uses `LogisticRegression(C=0.0001)` and reports `model.score(X_test, y_test)` of `0.91` to a stakeholder as "ROC AUC."
Later, someone computes ROC AUC correctly and gets a much worse result.
Diagnose both errors.

<details>
<summary>Answer</summary>

The first error is metric misuse:
`model.score` is accuracy, not ROC AUC.
The second error is modeling risk:
`C=0.0001` is extremely strong regularization, so the classifier may be over-shrunk and unable to separate classes well even if accuracy remains superficially acceptable under a particular threshold.
The fix is to report the correct metric from `predict_proba`, then tune `C` with cross-validation.

</details>

### 7. A team chooses ElasticNet over Lasso for strongly correlated feature groups.
What does ElasticNet buy them, and what does it cost?

<details>
<summary>Answer</summary>

ElasticNet buys more stable handling of correlated groups because the L2 component discourages arbitrary single-feature winner selection.
The cost is that the solution is usually less sparse than pure Lasso and introduces an extra hyperparameter, `l1_ratio`, to tune.

</details>

### 8. A small-data project has about one hundred twenty rows and eighty features.
Someone insists on Lasso because "sparsity is always more interpretable."
Why might Ridge be the safer first choice?

<details>
<summary>Answer</summary>

In small-data high-dimensional settings, pure sparsity can become unstable, especially if features correlate or the signal is weak.
Ridge is often safer because it regularizes aggressively without forcing brittle winner-take-all selection.
It usually gives a more stable baseline before you decide whether sparse selection is actually needed.

</details>

## Hands-On Exercise

Build a regression-and-classification notebook that forces you to observe shrinkage, sparsity, inverse-`C`, and GLM behavior directly.

### Step 1

- [ ] Generate a synthetic regression dataset with `n_samples=500`, `n_features=20`, and `n_informative=5`.
- [ ] Introduce high pairwise correlation by creating a handful of latent variables and adding small noise to make duplicate-like features.
- [ ] Split once into development and final test sets, holding out `20%` for the final test set.
- [ ] Keep the final test set untouched until the end.

Suggested scaffold:

```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

rng = np.random.default_rng(0)

n_samples = 500

latent = rng.normal(size=(n_samples, 5))
informative = latent + rng.normal(scale=0.05, size=(n_samples, 5))
correlated_noise = latent + rng.normal(scale=0.08, size=(n_samples, 5))
pure_noise = rng.normal(size=(n_samples, 10))

X = np.hstack([informative, correlated_noise, pure_noise])
columns = [f"x{i}" for i in range(X.shape[1])]
X = pd.DataFrame(X, columns=columns)

true_w = np.array([2.5, -2.0, 1.8, 0.0, 1.2] + [0.0] * 15)
y = X.to_numpy() @ true_w + rng.normal(scale=0.6, size=n_samples)

X_dev, X_test, y_dev, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=0,
)
```

### Step 2

- [ ] Wrap `Ridge(alpha=1.0)` and `Lasso(alpha=0.1)` inside separate pipelines with `StandardScaler`.
- [ ] Use five-fold cross-validation on the development data only.
- [ ] Fit the final chosen instance of each model on the full development split.
- [ ] Compare the number of non-zero coefficients in each fitted model.

Suggested scaffold:

```python
import numpy as np
from sklearn.linear_model import Lasso, Ridge
from sklearn.model_selection import KFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ridge = Pipeline(
    [
        ("scale", StandardScaler()),
        ("ridge", Ridge(alpha=1.0)),
    ]
)

lasso = Pipeline(
    [
        ("scale", StandardScaler()),
        ("lasso", Lasso(alpha=0.1, max_iter=20000)),
    ]
)

cv = KFold(n_splits=5, shuffle=True, random_state=0)

ridge_scores = cross_val_score(ridge, X_dev, y_dev, cv=cv, scoring="r2")
lasso_scores = cross_val_score(lasso, X_dev, y_dev, cv=cv, scoring="r2")

ridge.fit(X_dev, y_dev)
lasso.fit(X_dev, y_dev)

ridge_coef = ridge.named_steps["ridge"].coef_
lasso_coef = lasso.named_steps["lasso"].coef_

print("Ridge CV mean R^2:", round(ridge_scores.mean(), 3))
print("Lasso CV mean R^2:", round(lasso_scores.mean(), 3))
print("Ridge non-zero coefficients:", int((ridge_coef != 0.0).sum()))
print("Lasso non-zero coefficients:", int((lasso_coef != 0.0).sum()))
```

### Step 3

- [ ] Sweep Ridge `alpha` over `[0.01, 0.1, 1, 10, 100]`.
- [ ] Fit each value on the same development split.
- [ ] Print the L2 norm of `coef_` for each model.
- [ ] Verify that the norm shrinks monotonically or near-monotonically as `alpha` grows.

Suggested scaffold:

```python
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

for alpha in [0.01, 0.1, 1, 10, 100]:
    model = Pipeline(
        [
            ("scale", StandardScaler()),
            ("ridge", Ridge(alpha=alpha)),
        ]
    )
    model.fit(X_dev, y_dev)
    coef = model.named_steps["ridge"].coef_
    print(f"alpha={alpha:>5}  coef_l2_norm={np.linalg.norm(coef):.3f}")
```

What should you observe?

As `alpha` grows, the coefficient norm should shrink.
If it does not, inspect whether scaling is inside the pipeline and whether you are reading the right fitted step.

### Step 4

- [ ] Sweep Lasso `alpha` over `[0.01, 0.1, 1, 10, 100]`.
- [ ] Fit each value on the same development split.
- [ ] Print the count of non-zero coefficients for each fit.
- [ ] Verify increasing sparsity as `alpha` grows.

Suggested scaffold:

```python
from sklearn.linear_model import Lasso
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

for alpha in [0.01, 0.1, 1, 10, 100]:
    model = Pipeline(
        [
            ("scale", StandardScaler()),
            ("lasso", Lasso(alpha=alpha, max_iter=20000)),
        ]
    )
    model.fit(X_dev, y_dev)
    coef = model.named_steps["lasso"].coef_
    print(f"alpha={alpha:>5}  non_zero={int((coef != 0.0).sum())}")
```

A useful extension is to inspect which features survive, not only how many.
If the survivors bounce around within correlated groups, that is the behavior this module warned you about.

### Step 5

- [ ] Generate a synthetic binary classification dataset with redundant features.
- [ ] Train `LogisticRegression(C=0.01)`, `LogisticRegression(C=1.0)`, and `LogisticRegression(C=100.0)` in pipelines with `StandardScaler`.
- [ ] Compute `np.linalg.norm(model.named_steps['logreg'].coef_)` for each fit.
- [ ] Compute ROC AUC from `predict_proba`, not from `.score`.
- [ ] Compare coefficient norms and AUC values across the three settings.

Suggested scaffold:

```python
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

X_cls, y_cls = make_classification(
    n_samples=900,
    n_features=16,
    n_informative=6,
    n_redundant=6,
    n_repeated=0,
    n_classes=2,
    random_state=0,
)

Xc_dev, Xc_test, yc_dev, yc_test = train_test_split(
    X_cls,
    y_cls,
    test_size=0.2,
    random_state=0,
    stratify=y_cls,
)

for C in [0.01, 1.0, 100.0]:
    model = Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "logreg",
                LogisticRegression(
                    C=C,
                    penalty="l2",
                    solver="lbfgs",
                    max_iter=2000,
                ),
            ),
        ]
    )
    model.fit(Xc_dev, yc_dev)

    coef_norm = np.linalg.norm(model.named_steps["logreg"].coef_)
    auc = roc_auc_score(yc_test, model.predict_proba(Xc_test)[:, 1])

    print(f"C={C:>6}  coef_l2_norm={coef_norm:.3f}  roc_auc={auc:.3f}")
```

Interpret the results carefully.

If `C=0.01` has the smallest coefficient norm, that is expected.
If its ROC AUC is also worse, that may simply mean the model is over-regularized for this dataset.
Do not confuse "stronger regularization" with "better model."

### Step 6

- [ ] Create a non-negative count target from a Poisson process.
- [ ] Fit `PoissonRegressor` and `LinearRegression` on the same train split.
- [ ] Compare their mean predictions on the test split.
- [ ] Check whether `LinearRegression` produces any negative predictions.
- [ ] Summarize why the difference is about model family, not just clipping.

Suggested scaffold:

```python
import numpy as np
from sklearn.linear_model import LinearRegression, PoissonRegressor
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

rng = np.random.default_rng(0)

X = rng.normal(size=(600, 4))
linear_signal = 0.6 * X[:, 0] - 0.4 * X[:, 1] + 0.3 * X[:, 2]
rate = np.exp(0.8 + linear_signal)
y = rng.poisson(rate)

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=0,
)

lin = Pipeline(
    [
        ("scale", StandardScaler()),
        ("lr", LinearRegression()),
    ]
)

poi = Pipeline(
    [
        ("scale", StandardScaler()),
        ("poisson", PoissonRegressor(alpha=0.0, max_iter=1000)),
    ]
)

lin.fit(X_train, y_train)
poi.fit(X_train, y_train)

lin_pred = lin.predict(X_test)
poi_pred = poi.predict(X_test)

print("LinearRegression mean prediction:", round(lin_pred.mean(), 3))
print("PoissonRegressor mean prediction:", round(poi_pred.mean(), 3))
print("LinearRegression negative predictions:", int((lin_pred < 0).sum()))
print("PoissonRegressor negative predictions:", int((poi_pred < 0).sum()))
```

The goal here is not to claim that `PoissonRegressor` always wins every metric.
The goal is to see that the model family respects the target geometry more naturally.

### Completion Check

Before you consider the exercise finished, verify all of the following:

- [ ] Every regularized linear model is inside a pipeline with `StandardScaler`, rather than scaling the full dataset outside cross-validation.
- [ ] Final test sets stayed untouched during model and hyperparameter exploration.
- [ ] ROC AUC, when reported, was computed from `predict_proba`, not from `.score`.
- [ ] You checked both performance and coefficient behavior, rather than reading a single metric and stopping.
- [ ] You observed that higher `alpha` means more regularization in Ridge and Lasso, while smaller `C` means more regularization in logistic regression.
- [ ] You confirmed that the GLM example is about choosing the correct link function, not about cosmetic clipping of impossible predictions.

## Sources

- https://scikit-learn.org/stable/modules/linear_model.html
- https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html
- https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html
- https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.RidgeCV.html
- https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Lasso.html
- https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LassoCV.html
- https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.ElasticNet.html
- https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.ElasticNetCV.html
- https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html
- https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegressionCV.html
- https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.SGDClassifier.html
- https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.SGDRegressor.html
- https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.PoissonRegressor.html
- https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.GammaRegressor.html
- https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.TweedieRegressor.html
- https://scikit-learn.org/stable/auto_examples/linear_model/plot_logistic_path.html
- https://scikit-learn.org/stable/auto_examples/linear_model/plot_ridge_path.html
- https://scikit-learn.org/stable/auto_examples/linear_model/plot_lasso_coordinate_descent_path.html

## Next Module

Continue to [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](module-1.3-model-evaluation-validation-leakage-and-calibration/).
