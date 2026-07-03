---
title: "Conformal Prediction & Uncertainty Quantification"
description: "Use conformal prediction to wrap any black-box model with a distribution-free coverage guarantee, distinguish marginal from conditional coverage, and choose conformal vs Bayesian vs calibration when uncertainty actually matters."
slug: ai-ml-engineering/machine-learning/module-2.5-conformal-prediction-and-uncertainty-quantification
sidebar:
  order: 25
---

> Track: AI/ML Engineering | Complexity: `[MEDIUM]` | Time: 90-110 minutes
> Prerequisites: [Module 1.2: Linear and Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/), [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/), and [Module 2.3: Probabilistic & Bayesian ML with PyMC](../module-2.3-probabilistic-and-bayesian-ml-with-pymc/). This module also sets up a plain-text forward reference to Module 2.6, fairness and bias auditing.

The on-call story for conformal prediction usually begins with a team that believes it already has uncertainty. A regression or classification model is in production. The dashboard includes a confidence column. The
decision system filters, escalates, or auto-approves based on that value. Then the painful cases surface. The model's "confidence" was really a transformed margin, a distance from a boundary, or a softmax score that
nobody verified against observed outcomes. The system sounded probabilistic while behaving like a point predictor wearing a badge. The failure is not that the model was too simple. The failure is that the deployment
needed a coverage contract and never built one. When the real requirement is "if we say ninety percent, then the truth should land inside the interval at about that rate," conformal prediction is often the simplest
serious fix.

The second story starts from the opposite mistake. A different team has read about Bayesian ML in [Module 2.3: Probabilistic & Bayesian ML with PyMC](../module-2.3-probabilistic-and-bayesian-ml-with-pymc/) and correctly
understands that posterior uncertainty is a principled object. Then they aim that machinery at a giant black-box deployment where priors, likelihood specification, and MCMC compute are badly mismatched to the actual job.
They do not need a posterior over parameters. They need a post-hoc wrapper around an already strong predictor. Conformal prediction gives exactly that: distribution-free marginal coverage around any exchangeable
black-box model, with no priors, no posterior simulation, and no attempt to turn every uncertainty problem into a Bayesian one. That is the core frame for this module. Bayesian and conformal are not better and worse
versions of the same tool. They answer different operational questions.

## Learning Outcomes

By the end of this module, a practitioner will be able to:

1. **Diagnose** whether a deployment actually needs distribution-free coverage guarantees, principled posterior uncertainty ([Module 2.3: Probabilistic & Bayesian ML with
   PyMC](../module-2.3-probabilistic-and-bayesian-ml-with-pymc/)), or just well-calibrated probabilities ([Module 1.3: Model Evaluation, Validation, Leakage &
   Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/)) - and articulate the cost of each choice.
2. **Explain** the conformal contract: marginal coverage under exchangeability, the strict difference between validity and efficiency, and why a wide interval that covers at the stated rate is still a correct conformal
   interval.
3. **Implement** split-conformal regression, cross-conformal (CV+) regression, conformalized quantile regression (CQR), and split-conformal classification using MAPIE v1's `fit()` -> `conformalize()` ->
   `predict_interval()`/`predict_set()` workflow with `confidence_level` (NOT `alpha`).
4. **Compare** conformal prediction against Bayesian uncertainty quantification ([Module 2.3: Probabilistic & Bayesian ML with PyMC](../module-2.3-probabilistic-and-bayesian-ml-with-pymc/)) and against probability
   calibration ([Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/)) on the dimensions of assumptions, computational cost, what the output
   guarantees, and what the output does NOT guarantee.
5. **Decide** when conformal prediction is the wrong tool - point predictions suffice, the deployment needs conditional rather than marginal coverage, distribution shift is severe enough that the exchangeability
   assumption is violated, or interval width swamps decision value.

## Why This Module Matters

Conformal prediction matters because many production teams ask uncertainty questions with the wrong instrument. They want a statement about coverage and reach for a score that was never calibrated. They want a pragmatic
wrapper for an already-trained model and reach for a full probabilistic programming stack. They want subgroup guarantees and stop too early at a global average. The pitfall list is short enough to memorize.

The first pitfall is confusing any model score with usable uncertainty. A raw softmax value, a tree vote fraction, or a distance from a separating boundary can be useful ranking information, but none of those objects
automatically guarantee interval or set coverage. The second pitfall is confusing a valid global statement with a guarantee for every subgroup. Conformal is about marginal not conditional coverage, and that distinction
is not fine print. The third pitfall is thinking that wide intervals are evidence that conformal failed. Sometimes wide intervals are the honest answer. The fourth pitfall is using conformal under severe drift and then
blaming the method when exchangeability was already broken.

The library landscape is much better than it used to be. For practitioners in the scikit-learn ecosystem, MAPIE is the canonical Python library for conformal prediction in ordinary ML workflows. The v1 API matters
because it made the object model explicit. Instead of one overloaded regressor or classifier class with multiple legacy branches, you now choose concrete tools: `SplitConformalRegressor`, `CrossConformalRegressor`,
`ConformalizedQuantileRegressor`, and `SplitConformalClassifier`. That restructuring is not cosmetic. It mirrors the conceptual split you need in practice. Are you calibrating on a held-out set, using CV+ style
out-of-fold residuals, handling heteroskedastic regression with CQR, or building prediction sets for classification rather than intervals for regression?

MAPIE also forces good habits through its method names. Split conformal is not `fit(...).predict(...)` anymore. The workflow is intentionally explicit: `fit()` trains the base estimator, `conformalize()` computes
conformity scores on the calibration split, and `predict_interval()` or `predict_set()` emits the coverage object. Cross conformal collapses the training and conformalization steps into `fit_conformalize()`, because the
out-of-fold residual machinery is the method. That is the right shape for a library because it teaches the right mental model: conformal prediction is a contract layered on top of a base predictor, not a magical model
family with its own loss function and its own data-generating worldview.

If you leave this module with one production instinct, it should be this. First decide what kind of uncertainty the decision actually needs. Then choose the least expensive tool whose guarantees line up with that
decision. Conformal is one of the strongest answers when you need model-agnostic, distribution-free, post-hoc coverage and can live with a marginal guarantee under exchangeability.

## Section 1: What Conformal Prediction Is and Isn't

Conformal prediction is a way to turn ordinary model outputs into prediction intervals for regression or prediction sets for classification with a finite- sample coverage guarantee under exchangeability. That sentence
contains the whole contract. It is distribution-free because it does not require a parametric noise model. It is model-agnostic because it can wrap nearly any predictor with `fit` and `predict` behavior. It is post-hoc
because the base model can already exist before the conformal layer is added.

That is also why conformal prediction is so attractive in production. Teams rarely want to rebuild their serving stack from scratch just to get an uncertainty story. If the base model is a random forest, a
gradient-boosted regressor, a regularized linear model from [Module 1.2: Linear and Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/), or a classifier from
[Module 1.7: Naive Bayes, k-NN & SVMs](../module-1.7-naive-bayes-knn-and-svms/), conformal prediction can usually sit on top of it without changing how the base model learns.

What conformal prediction is not matters just as much. It is not a fix for a bad model. If the base regressor misses major structure, the intervals may be needlessly wide or locally misleading even while global coverage
remains valid. It is not a guarantee of short intervals. Validity is about hitting the stated coverage rate, not about making the interval pretty. It is not a substitute for good evaluation from [Module 1.3: Model
Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/). You still need clean splits, leakage control, and a test set that did not help define the conformal
threshold.

It is also not a Bayesian rival in the simplistic sense. A Bayesian model tries to answer a richer inferential question about posterior beliefs under a chosen prior and likelihood. Conformal prediction answers a narrower
but often more deployable question: can we produce sets or intervals whose long-run coverage is correct at the declared rate? Those are different contracts. A deployment may prefer either one depending on the decision at
stake.

The key idea inside most conformal methods is a conformity or nonconformity score. You take the base model's behavior on calibration data, measure how far truth sits from prediction in a method-specific way, and use the
upper tail of those errors to build future uncertainty sets. For regression that score is often an absolute residual. For classification it may be derived from class probabilities, ranks, or cumulative probability mass.
Once you see that mechanism, conformal stops feeling mysterious. It is a disciplined way to say, "how surprising was the truth on held-out data, and how large a safety margin should we carry forward?"

That is why conformal prediction belongs in an engineering curriculum rather than only in a theory course. It meets practitioners where they already are: black-box models, strong baselines, and a need to make uncertainty
claims that survive contact with operations.

## Section 2: The Exchangeability Assumption

Every serious method has a contract, and conformal's is refreshingly compact: exchangeability is the only assumption. In ordinary practice, people often translate that as "roughly IID," but the real concept is slightly
weaker and more useful. Exchangeability means the joint distribution does not change when you permute the order of the observations. The data need not be generated by a story that is identical in a mechanistic sense for
every sample. What matters is that the calibration examples and future examples can be treated as symmetrically drawn from the same population.

This is why conformal methods work so cleanly on many cross-sectional tabular problems. If you are predicting loan outcomes, defect rates, or demand on a stable population, it is often plausible that train, calibration,
and test examples are exchangeable after careful leakage control. The conformal threshold learned on calibration residuals is then meaningful for future samples because the future is not systematically drawn from a
different world.

The assumption breaks when the future is not like the calibration past. Time series with trend or concept drift are the most obvious case. The residuals from last quarter do not necessarily tell you how surprising next
quarter will be. The assumption also breaks under population shift. If the deployment begins serving a new region, a new customer segment, a new hardware type, or a new policy regime, the calibration set may no longer
represent the served data. At that point conformal can still be run, but its guarantee is not the same because its premise is gone.

This is not unique to conformal prediction. Nearly every ML evaluation method quietly hopes that future data is compatible with past data. What makes conformal different is that the assumption is named so directly. That
direct statement is a strength, not a weakness. It forces the practitioner to say out loud whether the deployment environment is stable enough for a calibration-based coverage guarantee to make sense.

Exchangeability is also where many production misunderstandings begin. Teams sometimes talk as though conformal prediction is "assumption free." It is more accurate to say it is distribution-free but not assumption free.
You do not assume Gaussian residuals, linearity, or a correctly specified posterior. You do assume that the calibration examples and the future examples are exchangeable enough that yesterday's calibration errors can
responsibly price today's uncertainty.

That framing helps you know when to pause. If the base model is updated nightly, traffic sources are changing, and drift alerts are already firing, the question is no longer "can I compute a conformal interval?" The
question is "does the interpretation of that interval survive this environment?" That is the right engineering question.

## Section 3: Marginal vs Conditional Coverage

The single most important sentence in conformal prediction is this: the guarantee is about average coverage over the joint data distribution, not about coverage for every feature vector or every subgroup. In notation,
the contract looks like `P(Y in C(X)) >= 1 - alpha`. That statement is global. It says that across repeated draws from the relevant population, the true outcome lands inside the interval or set at least as often as
promised. It does not say that the same rate holds for any specific age bucket, geography, income group, or rare failure mode.

This distinction is why people say conformal gives marginal coverage rather than conditional coverage. If you ask, "is the ninety percent interval ninety percent accurate for this exact cohort?" plain split conformal
does not promise that. Subgroup miscoverage is not automatically a bug in the implementation. It is a structural consequence of the global guarantee. Some regions of feature space can be over-covered and others
under-covered while the overall rate still looks correct.

That fact can be unsettling the first time you encounter it, because it sounds like conformal is weaker than it was advertised. The better interpretation is that conformal is honest about what it guarantees. It does not
pretend to solve conditional uncertainty everywhere. It solves a specific problem cleanly and leaves a harder fairness and subgroup-audit problem for a later stage. That is exactly where Module 2.6, fairness and bias
auditing, enters the sequence.

When teams skip this distinction, they overclaim. They report a global coverage number and let stakeholders infer more than the method actually says. In regulated, high-stakes, or fairness-sensitive settings, that is not
a harmless oversimplification. It changes how the system is defended. A deployment can be globally valid and still be unsatisfactory for important cohorts.

> **Pause and decide** - An auditor asks whether your model's ninety percent
> interval is ninety percent accurate for women in the dataset. What can you
> say if you only built vanilla split conformal?

You can say that vanilla split conformal targets marginal coverage over the population used for calibration and evaluation. You cannot honestly promise the same rate for that subgroup without measuring subgroup behavior
directly. The next step is not to hand-wave. It is to slice empirical coverage and interval width by cohort, name the gap if there is one, and treat that as an audit task rather than as a footnote. In other words,
conformal gives you a clean global contract, and fairness work asks whether that contract is acceptably shared.

This is also why conformal prediction and interpretability belong near each other in a curriculum. The lesson from [Module 2.2: Interpretability and Failure Slicing](../module-2.2-interpretability-and-failure-slicing/)
was that global averages hide structurally different failure modes. The same discipline applies here. A model can have acceptable overall coverage and still produce narrower, riskier, or less useful intervals in the
places where the deployment most needs caution.

## Section 4: Split Conformal - the Deployable Default

Split conformal regression is the version most practitioners should reach for first. You take your labeled data, hold out a calibration set that the base model does not train on, fit the base model on the training split,
predict on the calibration split, compute residual-based conformity scores, and use an upper quantile of those scores to widen future predictions. The result is a prediction interval with valid marginal coverage under
exchangeability.

The appeal is practical. The training path remains ordinary. Any estimator that already works in your stack can stay in place. The only structural cost is that you must reserve calibration data. That cost is real,
especially on smaller datasets, but the conceptual simplicity is hard to beat. Split conformal is the method that makes teams stop pretending a score is uncertainty and start building a coverage object with a stated
rate.

In MAPIE v1, the method shape makes the workflow explicit. Use `SplitConformalRegressor`, set `confidence_level` at initialization, and choose `prefit=False` if you want MAPIE to fit the base estimator internally. Then
run `fit()` on the training data, `conformalize()` on the calibration data, and `predict_interval()` on a fresh test split or live traffic. The output includes point predictions and a three-dimensional interval array
whose first two slots are lower and upper bounds.

There is an important operational detail hiding inside this elegance. The calibration set is not a bonus validation split that can be reused for endless model tuning. Once you optimize the base model aggressively against
the same examples that define the conformal threshold, you blur the contract. Treat the calibration split as a scarce resource. Tune the base model elsewhere or use a nested workflow that preserves a clean
conformalization stage.

Here is a minimal split-conformal regression example using synthetic data and a random forest base regressor. The code checks empirical coverage on a held-out test set because "theorem says it should work" is not the
same as disciplined evaluation.

```python
import numpy as np
from sklearn.datasets import make_regression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from mapie.regression import SplitConformalRegressor

X, y = make_regression(
    n_samples=1200,
    n_features=10,
    noise=18.0,
    random_state=7,
)

X_trainval, X_test, y_trainval, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=7,
)

X_train, X_calib, y_train, y_calib = train_test_split(
    X_trainval,
    y_trainval,
    test_size=0.25,
    random_state=7,
)

split_cp = SplitConformalRegressor(
    estimator=RandomForestRegressor(
        n_estimators=300,
        random_state=7,
        n_jobs=-1,
    ),
    confidence_level=0.9,
    prefit=False,
).fit(X_train, y_train).conformalize(X_calib, y_calib)

y_pred, y_interval = split_cp.predict_interval(X_test)
lower = y_interval[:, 0, 0]
upper = y_interval[:, 1, 0]

empirical_coverage = np.mean((y_test >= lower) & (y_test <= upper))
mean_width = np.mean(upper - lower)

print(f"Empirical coverage: {empirical_coverage:.3f}")
print(f"Mean interval width: {mean_width:.3f}")
print("First five intervals:")
for pred, lo, hi in zip(y_pred[:5], lower[:5], upper[:5]):
    print(f"prediction={pred:.2f}, lower={lo:.2f}, upper={hi:.2f}")
```

The right way to read that result is not "coverage equals perfection." It is "coverage near the target means the conformal contract is behaving as expected on fresh data." If the intervals are too wide for the decision
to be useful, that is a separate question about efficiency and base-model quality. Split conformal got its part right if it covers at the stated rate.

That is why split conformal is such a useful deployable default. It is simple enough to explain to engineers, specific enough to audit, and honest enough to separate the problem of validity from the problem of whether
the intervals are tight enough to help.

## Section 5: CV+ and Jackknife+

Split conformal spends data on a held-out calibration set. That is often fine, but sometimes the dataset is small enough that losing a large calibration slice hurts the base model materially. CV+ and its relatives are
the answer when you want more sample efficiency. Instead of reserving a single calibration split, you fit models on cross-validation folds, compute conformity scores on the corresponding out-of-fold predictions, and
aggregate them into intervals with the same exchangeability-based coverage logic.

The conceptual win is easy to see. Every observation contributes to conformalization, and most observations also influence training for most fold models. You recover data efficiency without pretending you can calibrate
on the same fitted residuals that trained the model. The statistical machinery is more involved than split conformal, but the practitioner benefit is concrete: stronger use of limited data while retaining a clean
conformity-score story.

The MAPIE v1 tool for this family is `CrossConformalRegressor`. The workflow is different because the method itself is defined by out-of-fold fitting. Instead of separate `fit()` and `conformalize()` calls, you use
`fit_conformalize()`. That name is helpful because it encodes the method. You are not fitting one model and later adding a shell around it. You are fitting a cross-validated ensemble of residual views whose out-of-fold
behavior becomes the basis for the interval.

Jackknife+ belongs in the same conversation because it is one of the central theoretical variants in this space. In practice, many teams can treat CV+ as the more accessible member of the family and know that MAPIE also
exposes `JackknifeAfterBootstrapRegressor` for bootstrap-based variants. The deeper idea is shared: use out-of-sample residual behavior more efficiently than a single held-out calibration split.

Here is a compact CV+ example. Notice that we keep a final test split completely separate so that the empirical coverage check remains honest.

```python
import numpy as np
from sklearn.datasets import make_regression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from mapie.regression import CrossConformalRegressor

X, y = make_regression(
    n_samples=1200,
    n_features=10,
    noise=18.0,
    random_state=11,
)

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=11,
)

cv_plus = CrossConformalRegressor(
    estimator=RandomForestRegressor(
        n_estimators=300,
        random_state=11,
        n_jobs=-1,
    ),
    confidence_level=0.9,
    method="plus",
    cv=5,
    random_state=11,
).fit_conformalize(X_train, y_train)

y_pred, y_interval = cv_plus.predict_interval(X_test)
lower = y_interval[:, 0, 0]
upper = y_interval[:, 1, 0]

empirical_coverage = np.mean((y_test >= lower) & (y_test <= upper))
mean_width = np.mean(upper - lower)

print(f"Train samples used by CV+: {X_train.shape[0]}")
print(f"Empirical coverage: {empirical_coverage:.3f}")
print(f"Mean interval width: {mean_width:.3f}")
```

The operational argument for CV+ is not that it always dominates split conformal. It is that its tradeoff is often better when labeled data is scarce and model quality is sensitive to training set size. The cost is more
fitting work because you train across folds. The benefit is that you do not have to carve away a dedicated calibration block just to get a valid interval.

This is where practitioners should think like engineers rather than like method collectors. If a generous training set already exists, split conformal may be the cleaner deployment choice. If every sample is precious,
CV+ earns its extra compute. Neither choice is universally superior. The right question is which data-compute tradeoff produces the most useful intervals for the system you are actually serving.

## Section 6: Conformalized Quantile Regression

Vanilla split conformal has a limitation that becomes obvious on heteroskedastic data. If the method uses a global absolute-residual quantile, it adds roughly the same correction everywhere. That means the intervals can
end up too wide in easy regions and too narrow-looking, before correction, in hard regions. After calibration, coverage is still valid on average, but the width pattern does not adapt naturally to local difficulty.

Conformalized quantile regression, or CQR, is the standard answer. Instead of starting from a single point predictor and a global residual radius, you train models for lower and upper conditional quantiles and then
conformalize the gap. That lets the base interval shape vary with the input. Where the data is noisier, the learned quantiles can spread apart. Where the data is cleaner, they can pull closer together. The conformal step
then corrects coverage globally without throwing away that heteroskedastic structure.

This is why CQR matters so much in real regression deployments. Many business and scientific systems are not homoskedastic. Error grows with exposure, traffic, size, volatility, or edge-of-support behavior. A
one-radius-fits-all interval is often an unattractive compromise. CQR keeps the marginal coverage guarantee while letting the interval breathe where the problem is genuinely harder.

MAPIE v1 exposes this through `ConformalizedQuantileRegressor`. If you want the library to fit everything internally, you can pass a single estimator that supports quantile loss. If you want explicit control, you can
prefit the lower, upper, and median regressors yourself and pass them as a list with `prefit=True`. The lower and upper models do the conceptual heavy lifting for uncertainty shape; the median model provides point
predictions.

The code below uses gradient boosting quantile regressors for the lower and upper quantiles plus a median model for the point estimate. The important part is not the tree algorithm. It is the pattern: learn asymmetric
structure first, then conformalize.

```python
import numpy as np
from sklearn.datasets import make_regression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from mapie.regression import ConformalizedQuantileRegressor

X, y = make_regression(
    n_samples=1400,
    n_features=6,
    noise=12.0,
    random_state=19,
)

noise_scale = 8.0 + 0.6 * np.abs(X[:, 0])
y = y + np.random.default_rng(19).normal(scale=noise_scale, size=y.shape[0])

X_trainval, X_test, y_trainval, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=19,
)

X_train, X_calib, y_train, y_calib = train_test_split(
    X_trainval,
    y_trainval,
    test_size=0.25,
    random_state=19,
)

lower_q = GradientBoostingRegressor(
    loss="quantile",
    alpha=0.05,
    random_state=19,
)
upper_q = GradientBoostingRegressor(
    loss="quantile",
    alpha=0.95,
    random_state=19,
)
median_q = GradientBoostingRegressor(
    loss="quantile",
    alpha=0.5,
    random_state=19,
)

lower_q.fit(X_train, y_train)
upper_q.fit(X_train, y_train)
median_q.fit(X_train, y_train)

cqr = ConformalizedQuantileRegressor(
    estimator=[lower_q, upper_q, median_q],
    confidence_level=0.9,
    prefit=True,
).conformalize(X_calib, y_calib)

y_pred, y_interval = cqr.predict_interval(X_test)
lower = y_interval[:, 0, 0]
upper = y_interval[:, 1, 0]

empirical_coverage = np.mean((y_test >= lower) & (y_test <= upper))
mean_width = np.mean(upper - lower)

print(f"Empirical coverage: {empirical_coverage:.3f}")
print(f"Mean interval width: {mean_width:.3f}")
print("First five widths:", np.round((upper - lower)[:5], 2))
```

The right success criterion for CQR is not merely that coverage remains near the target. It is that width now tracks local uncertainty more credibly than a global-radius split conformal interval. In hard regions you
should be willing to see wider intervals if that width reflects the data-generating difficulty. Tighter intervals in easy regions and wider intervals in hard regions are not signs of inconsistency. They are the whole
point.

This is also where base-model quality and conformal design interact most constructively. Conformal does not discover heteroskedastic structure on its own. CQR works because the quantile regressors learn something useful
about where uncertainty grows. The conformal layer then protects the global coverage contract around those learned shapes.

## Section 7: Conformal Classification - Set-Valued Prediction

Regression conformal prediction outputs intervals. Classification conformal prediction outputs sets. That alone changes the mental model. The goal is no longer "what single label is most likely?" but "what labels remain
plausible at the chosen coverage level?" In ambiguous examples, the correct answer can contain multiple classes. In easy examples, the set may contain exactly one. Set size becomes a direct operational uncertainty
signal.

This is a much healthier framing than pretending a single class plus a confidence score always tells the whole story. In many classification systems, especially those with overlapping classes or abstention-like
workflows, the useful question is whether the model can narrow possibilities responsibly. A set of size one means the system is confident enough to commit. A set of size three means the system is hedging among three
plausible labels. A set that contains nearly every class means the model has learned little for that sample at the chosen confidence level.

MAPIE supports several conformity-score styles for classification, including LAC, APS, and RAPS. The operational differences matter. LAC often aims for smaller ambiguity sets based on class-score thresholds. APS uses
cumulative probability mass and tends to adapt set size more smoothly to uncertainty. RAPS adds regularization to discourage oversized sets in some settings. You do not need to memorize every theorem to use these
responsibly. You do need to remember that the output is a set, not a disguised probability.

The example below uses `SplitConformalClassifier` with APS-style sets on a multiclass synthetic dataset. After predicting sets, we inspect how many labels each example receives.

```python
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from mapie.classification import SplitConformalClassifier

X, y = make_classification(
    n_samples=1500,
    n_features=12,
    n_informative=8,
    n_redundant=2,
    n_classes=4,
    n_clusters_per_class=1,
    class_sep=1.0,
    random_state=23,
)

X_trainval, X_test, y_trainval, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=23,
    stratify=y,
)

X_train, X_calib, y_train, y_calib = train_test_split(
    X_trainval,
    y_trainval,
    test_size=0.25,
    random_state=23,
    stratify=y_trainval,
)

cp_classifier = SplitConformalClassifier(
    estimator=LogisticRegression(max_iter=2000),
    confidence_level=0.9,
    conformity_score="aps",
    prefit=False,
    random_state=23,
).fit(X_train, y_train).conformalize(X_calib, y_calib)

y_pred, y_sets = cp_classifier.predict_set(X_test)
set_sizes = y_sets[:, :, 0].sum(axis=1)
empirical_coverage = np.mean(y_sets[np.arange(y_test.shape[0]), y_test, 0])

print(f"Empirical set coverage: {empirical_coverage:.3f}")
print("Set-size distribution:")
for size, count in zip(*np.unique(set_sizes, return_counts=True)):
    print(f"size={int(size)} count={int(count)}")

print("First five predicted sets:")
for i in range(5):
    labels_in_set = np.flatnonzero(y_sets[i, :, 0])
    print(
        f"true={y_test[i]}, predicted_label={y_pred[i]}, "
        f"set={labels_in_set.tolist()}"
    )
```

The crucial operational interpretation is this. A larger set is not a bug by itself. It is the method saying, "at this coverage level, multiple labels remain plausible." If the deployment can route such cases to a human
reviewer, request more evidence, or abstain from auto-action, set-valued prediction is often much more honest than forcing one label and pretending the confidence score solves everything.

This is also where conformal classification connects naturally to cost-sensitive thinking from [Module 2.1: Class Imbalance & Cost-Sensitive Learning](../module-2.1-class-imbalance-and-cost-sensitive-learning/). The
right set size depends on downstream cost. If the price of a missed true label is high, a larger but valid set may be preferable. If intervention cost is high, you may accept smaller sets at a different coverage target.
Conformal prediction does not remove business tradeoffs. It makes them explicit.

## Section 8: Validity vs Efficiency

The phrase validity vs efficiency should become second nature when you read conformal results. Validity asks whether the coverage contract is met. Efficiency asks whether the intervals or sets are useful enough to
support the decision. These are related but distinct. A method can be valid and still be so wide, or so large in set size, that it has little operational value.

The easiest way to see this is with an absurd example. An interval that spans the entire real line would contain the true target almost always. It is valid in the most uninteresting sense possible. Likewise, a
classification set that contains every class for every example is hard to miss. Neither output helps a deployer act. The guarantee alone is not the whole objective.

This is where newer practitioners sometimes become frustrated. They hear that conformal provides a finite-sample guarantee and assume the method will somehow compress uncertainty into a tight, elegant package. It cannot
do that by itself. Conformal does not reduce uncertainty. It formalizes it. If the base model is weak, if the features are poor, or if the task is inherently noisy, the valid answer may simply be wide.

The good news is that efficiency is not random. Better models often produce better conformal intervals because their residual behavior is sharper. Better conformity scores can help. CQR can improve efficiency on
heteroskedastic data. Cross conformal can preserve data that would otherwise be lost to a calibration split. But those are improvements within the validity contract, not escapes from it.

> **Pause and predict** - A conformal interval covers at the requested rate on
> the test set, but it is about four times wider than the business can use.
> Did conformal fail?

No. The conformal method may have succeeded perfectly at validity while failing the separate business requirement of efficiency. The fix is not to accuse the coverage guarantee. The fix is to ask whether the base model
can be improved, whether the uncertainty target should be lowered, whether CQR is needed for heteroskedasticity, or whether the deployment simply does not gain enough value from interval output. This is one of the
healthiest lessons in the module: validity and usefulness are not the same question, and confusing them leads teams to misdiagnose the problem.

That distinction also protects you from overoptimizing the wrong metric. A team that chases narrow intervals without checking coverage can quietly destroy the very contract that justified using conformal in the first
place. A team that stops at coverage without checking width can ship something formally correct and practically empty. Good practice requires both views at once.

## Section 9: Conformal vs Bayesian

Conformal prediction and Bayesian uncertainty quantification often get compared as if they were competing brands of the same thing. That is the wrong frame. The better question is what each method is trying to guarantee.
Bayesian methods, as you saw in [Module 2.3: Probabilistic & Bayesian ML with PyMC](../module-2.3-probabilistic-and-bayesian-ml-with-pymc/), produce posterior beliefs conditioned on a prior and a likelihood. If you want
to reason about parameter uncertainty, hierarchical pooling, or full posterior predictive distributions under a model you are willing to specify and defend, Bayesian ML is often the right paradigm.

Conformal prediction asks a different question. It does not try to specify a likelihood or represent your beliefs about parameters. It asks whether a set-valued or interval-valued prediction can achieve a declared
long-run coverage rate under exchangeability. The output is narrower in one sense, because it is "just" a set or interval rather than a full posterior. But it is stronger in another sense, because the guarantee is
distribution-free and does not rely on the correctness of a parametric generative story.

That is why it is important to say explicitly that conformal is not inferior to Bayesian uncertainty. It is answering a different question with a different assumption profile. If the deployment needs coverage around a
black-box model and has no appetite for prior design or MCMC cost, conformal may be the more appropriate and more defensible method. If the deployment needs posterior reasoning, parameter-level beliefs, or hierarchical
structure that changes policy, Bayesian modeling may be indispensable.

The compute story matters too. Post-hoc conformal wrappers are usually cheap relative to full Bayesian inference. Even CV+ often looks modest next to serious MCMC workflows. That difference can decide what is feasible in
production. But cheaper does not mean strictly better. The cheaper method may not answer the question you actually have.

A useful contrast is this. Bayesian methods can tell you things like, "under this model, there is strong posterior support that this coefficient is positive," or "the posterior predictive mass for next week's demand is
spread in this particular way." Conformal methods cannot do that. They can say, "here is an interval or a set that should contain the truth at the declared marginal rate." If that is enough, conformal is elegant. If you
need the richer object, it is the wrong instrument.

The healthiest production attitude is not to force a winner. Sometimes the base predictor itself is Bayesian and the deployment still uses conformalization on top for a coverage layer. Sometimes a Bayesian prototype
teaches you the shape of uncertainty and a conformal wrapper becomes the scalable operational choice. The paradigms can coexist because they are solving adjacent rather than identical problems.

## Section 10: Conformal vs Calibration

Probability calibration and conformal prediction are also easy to confuse, but for a different reason. Both are often described with the language of confidence. That shared vocabulary hides a major distinction.
Calibration is about whether predicted probabilities match observed frequencies. Conformal is about whether prediction sets or intervals contain the truth at the target rate.

The calibration story from [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/) and the scikit-learn calibration guide is about statements
like this: among the examples assigned probability around 0.8, does the positive class occur about eighty percent of the time? That is a conditional frequency statement indexed by predicted probability bins. It is
extremely useful when you need ranking, thresholding, expected-value computation, or downstream decision analysis based on probabilities.

Conformal prediction asks something else. It says: across new examples, does the true label or target land inside the produced set or interval often enough? A classifier can be beautifully calibrated in the probability
sense and still produce poor conformal sets if the conformity score or set-construction choice is weak. A conformal classifier can hit the desired set coverage and still have poorly calibrated raw probabilities. The two
properties can fail independently.

This independence matters operationally. Suppose your deployment needs a probability to optimize expected revenue under different action costs. Then calibration may be central and conformal may be secondary. Suppose the
deployment instead needs a valid abstention or fallback mechanism based on whether the true label is inside a set. Then conformal is central and calibration may be helpful but not sufficient.

The common mistake is to let calibrated probabilities stand in for a coverage guarantee. They are not the same thing. A well-calibrated binary classifier can say "0.9" on some cases and still fail to provide a valid
ninety percent prediction set construction unless you actually build one. Conversely, a conformal set can be valid even if the underlying class probabilities are not beautifully calibrated. That may feel unintuitive
until you remember that the guarantees target different objects.

The simplest way to stay honest is to say the full sentence each time. If you mean calibration, say "probabilities match frequencies." If you mean conformal, say "sets or intervals cover at the declared rate." Collapsing
both into the word confidence is what creates avoidable confusion.

## Section 11: Distribution Shift and Adaptive Conformal

Vanilla conformal methods assume the calibration set and future predictions are exchangeable. Production systems are often not that polite. Traffic changes. Seasonality shifts. User behavior adapts to the model. New
devices appear. A policy change moves the label distribution. In these regimes, a static conformal threshold learned once and frozen forever may drift away from the world it was meant to protect.

This is where adaptive conformal ideas enter. The basic operational intuition is straightforward even if the theory gets deeper. Instead of treating the calibration threshold as fixed, you update it over time in response
to recent miscoverage or recent distribution changes. If the system is starting to miss too often, the threshold can widen. If the environment stabilizes and errors fall, the threshold can tighten. The promise is not
that exchangeability stops matter. The promise is that online updates can make the system more robust to nonstationary behavior than a single frozen calibration pass.

That makes adaptive conformal especially relevant for MLOps practice. Drift monitoring is not separate from uncertainty quantification. If your data monitoring already tells you the served distribution is moving, your
conformal workflow should respond. The wrong posture is to keep serving yesterday's interval width as though the calibration world still exists unchanged.

Adaptive conformal is not a free pass, however. Under severe enough shift, even online threshold updates may not restore the coverage behavior you want. If the feature-label relationship itself changes sharply,
recalibrating the wrapper is not enough. The base model may need retraining, the feature space may need repair, or the deployment may need to step down to a safer fallback mode.

> **Pause and decide** - Your drift monitor has been red for days, and the
> empirical coverage on the latest window is well below target. Should you keep
> using the original split-conformal threshold?

No. The original threshold was justified by a stability assumption that the current system is openly violating. The right response is to treat this as a distribution-shift problem first and a conformal-method problem
second. That usually means recalibrating on a fresh window, considering adaptive conformal updates, checking whether the base model itself has degraded, and making sure any stated coverage claims are tied to the new
operating regime rather than to the old one.

The broader lesson is that conformal prediction is strongest when paired with good operational hygiene. Uncertainty quantification is not a one-time notebook artifact. It is part of a living system whose assumptions
should be monitored the same way you monitor latency, label freshness, and model drift.

## Section 12: Practitioner Playbook

A practitioner playbook for conformal prediction starts before any code is written. First ask whether uncertainty actually matters to the decision. If the system will always take the same action regardless of interval
width, the correct answer may be to ship a point predictor and stop. If the output changes approval thresholds, human-review routing, cost-sensitive abstention, or alerting policy, uncertainty is a real product
requirement rather than a nice slide.

Next, train the best point predictor you can defend. Conformal does not reward sloppy modeling. Stronger base models often buy better efficiency. That is where your ordinary ML discipline from earlier modules still
matters: clean splits, leakage control, feature sanity, baseline comparisons, and failure slicing. A conformal wrapper around a brittle model is still a brittle system, just with a more honest uncertainty story.

Then choose the conformal flavor that matches the constraints. Split conformal is the default when data is ample and deployment simplicity matters. CV+ is the strong option when labeled data is scarce and more fitting
cost is acceptable. CQR is the right move when heteroskedasticity is structurally important. Split conformal classification is the natural choice when the operational output is a set of plausible labels rather than a
scalar probability.

After that, make the data partitioning explicit. If you use split conformal, reserve a calibration set that the base model did not train on. If you use CV+, remember that `fit_conformalize()` is consuming your training
data in a more sample-efficient cross-validated way, but your test set must still be untouched. The empirical coverage check belongs on a fresh test split, not on the training or calibration data used to build the
intervals.

Coverage alone is not enough. Inspect width or set size. Then inspect it again by cohort. That step is where the marginal-versus-conditional distinction stops being abstract. If one region of the data gets much wider
intervals, or if one cohort sees noticeably lower empirical coverage, you have learned something important even if the global average looks fine. That is the forward bridge to Module 2.6 and to real fairness auditing.

Finally, document the contract in plain language. State the confidence level, the exchangeability assumption, the specific conformal method, the size and role of the calibration split, the empirical test coverage, and
the main limitation. If the limitation is drift, say so. If the limitation is interval width, say so. If the limitation is that the guarantee is marginal rather than conditional, say so. A disciplined uncertainty story
is mostly clarity.

## Section 13: When Conformal Is the Wrong Tool

Conformal prediction is powerful precisely because it has a narrow, well-stated contract. That also means there are many cases where it is the wrong tool. The first is trivial but important: point predictions may be
enough. If the system never uses uncertainty for routing, abstention, pricing, or escalation, then a coverage object may add little beyond cognitive overhead.

The second wrong-tool case is when the deployment truly needs conditional coverage rather than a marginal guarantee. If stakeholders need defensible coverage behavior across sensitive cohorts, or if cohort-specific
miscoverage is itself the core risk, vanilla conformal is not the finish line. You need a fairness and subgroup-audit workflow that goes beyond a single global rate.

The third case is severe distribution shift. If exchangeability is badly broken and keeps breaking, a static conformal wrapper will not rescue the system. Adaptive conformal may help, but there are environments where no
simple online threshold update can keep the promise meaningful. At that point you are in retraining, redesign, or fallback territory.

The fourth case is when interval width swamps decision value. A valid interval can still be too wide to act on. That is not a failure of rigor. It is useful evidence that the current model-feature-decision stack cannot
support the level of certainty the business hoped for. Sometimes the honest answer is that the deployment should not automate as much as it planned.

The fifth case is when you genuinely need posterior reasoning. If the decision depends on parameter-level uncertainty, hierarchical shrinkage, or rich distributional inference of the sort covered in [Module 2.3:
Probabilistic & Bayesian ML with PyMC](../module-2.3-probabilistic-and-bayesian-ml-with-pymc/), conformal prediction is not a substitute. It gives valid sets and intervals, not a full posterior worldview.

That is the mature ending to the conformal story. It is not a universal answer. It is a precise answer to a precise class of uncertainty problems. When your problem matches that class, conformal prediction is one of the
cleanest tools in modern ML practice. When it does not, the disciplined move is to say so and choose something else.

## Did You Know?

- MAPIE v1, released in 2025, renamed its public entry points around explicit conformal workflows. `MapieRegressor` is gone; split regression now centers on `SplitConformalRegressor`, with the `fit()` -> `conformalize()`
  -> `predict_interval()` pattern and `confidence_level` replacing `alpha`. Source: https://contrib.scikit-learn.org/MAPIE/stable/getting-started/v1-release-notes/
- A standard introduction to conformal prediction emphasizes that exchangeability, rather than a parametric residual model, is the key premise behind distribution-free coverage around arbitrary black-box estimators.
  Source: https://arxiv.org/abs/2107.07511
- Conformalized quantile regression combines lower and upper quantile models with conformal calibration so interval width can adapt to heteroskedastic structure without giving up marginal coverage. Source:
  https://arxiv.org/abs/1905.03222
- Research on adaptive conformal methods pushes beyond one-shot calibration by updating coverage control online as the environment changes, trading the clean static setting for a more drift-aware operational posture.
  Source: https://arxiv.org/abs/2202.07650

## Common Mistakes

| Mistake | Why it bites | What to do instead |
| --- | --- | --- |
| Calling MAPIE with `alpha=0.1` | v1 deprecated `alpha` for `confidence_level` | Use `confidence_level=0.9` |
| `SplitConformalRegressor.fit(X, y).predict(X_test)` | v1 split conformal needs an explicit `conformalize()` step | `fit()` -> `conformalize()` -> `predict_interval()` |
| Reading marginal coverage as conditional | Subgroup miscoverage is structural, not a bug | Inspect coverage by cohort and carry the audit into Module 2.6 |
| Treating wide intervals as a conformal failure | Width reflects model uncertainty; intervals can remain valid | Improve the base model or use CQR for heteroskedasticity |
| Using vanilla split conformal under known drift | Exchangeability is broken | Recalibrate on a fresh window or use adaptive conformal ideas |
| Confusing calibration with conformal | They guarantee different things | Calibration shapes probability meaning; conformal controls set or interval coverage |
| Skipping the empirical coverage check on a held-out test set | Validity is a population property, not a per-sample feeling | Verify coverage on a fresh test split, ideally per cohort |
| Building CQR with one quantile regressor | CQR needs lower and upper quantiles, plus a point model in MAPIE's prefit workflow | Fit both quantile models and then conformalize |

## Quiz

1. A team reports ninety-two percent empirical coverage for a `SplitConformalRegressor` configured at `confidence_level=0.9`, but they measured it on the same data used to fit and conformalize the model. What is the
   issue?

<details><summary>Answer</summary> They did not validate the coverage contract on a fresh test split. Coverage on training or conformalization data is not the right operational check. The fix is to keep a held-out test
set untouched, call `predict_interval()` there, and measure empirical coverage and width on that separate data. </details>

2. An auditor asks, "Are your ninety percent intervals ninety percent accurate for women in the dataset?" What is the right answer if you only used vanilla split conformal?

<details><summary>Answer</summary> The honest answer is that vanilla split conformal targets marginal coverage on the calibration population, not guaranteed conditional coverage for that subgroup. You should measure
empirical coverage and width for women directly and treat any disparity as part of a subgroup audit rather than claiming the method guarantees it automatically. </details>

3. CQR intervals are about twice as wide as vanilla split-conformal intervals on the same problem, but the marginal coverage is the same. Which is better?

<details><summary>Answer</summary> Neither is automatically better. If the data is heteroskedastic and CQR is wide mainly where the problem is genuinely harder, then the wider intervals may be more useful and more
honest. The correct comparison is about local width behavior and decision value, not just the global coverage number. </details>

4. Production data drifts substantially between calibration and serving. What conformal flavor or workflow should you consider first?

<details><summary>Answer</summary> Do not keep trusting a frozen split-conformal threshold. Recalibrate on a fresh window if possible, monitor empirical coverage over time, and consider adaptive conformal approaches that
update the threshold online. Also verify whether the base model itself needs retraining because drift can break more than the wrapper. </details>

5. A team replaces a Bayesian PyMC pipeline with a conformal one because the compute bill is much lower. What did they trade away?

<details><summary>Answer</summary> They traded away posterior-level reasoning. Conformal prediction can give valid intervals or sets, but it does not provide priors, posterior beliefs about parameters, hierarchical
shrinkage in the Bayesian sense, or full posterior predictive distributions. They gained a cheaper coverage contract and lost a richer inferential object. </details>

6. A conformal classifier outputs set sizes `1, 1, 1, 5` across four examples. What does the size-five output mean operationally?

<details><summary>Answer</summary> It means the model cannot responsibly narrow the plausible labels much for that example at the chosen confidence level. The system should treat that case as high uncertainty: escalate
it, request more evidence, abstain, or apply a more conservative downstream policy instead of pretending the top label is enough. </details>

7. A team built `SplitConformalClassifier` with `confidence_level=0.95` but sees only eighty-eight percent empirical coverage on the test set. Where should they look first?

<details><summary>Answer</summary> They should check all three suspects, but in a disciplined order. First confirm the data split and coverage calculation are correct. Then inspect whether the calibration sample is too
small and noisy. After that, test whether exchangeability is broken by drift or population shift. Base-model quality can hurt efficiency badly, but a major coverage miss usually points first to splitting, sample size, or
assumption mismatch. </details>

## Hands-On Exercise

- [ ] Step 0: Import `numpy`, `make_classification`, `make_regression`, `RandomForestRegressor`, `GradientBoostingRegressor`, `LogisticRegression`, `train_test_split`, `SplitConformalRegressor`,
    `ConformalizedQuantileRegressor`, and `SplitConformalClassifier`.

- [ ] Step 1: Generate synthetic regression data with heteroskedastic noise so the variance grows with `|x|`. Keep one feature easy to inspect so you can slice widths later.

```python
import numpy as np
from sklearn.datasets import make_classification, make_regression
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from mapie.classification import SplitConformalClassifier
from mapie.regression import (
    ConformalizedQuantileRegressor,
    SplitConformalRegressor,
)

X_reg, y_reg = make_regression(
    n_samples=1500,
    n_features=6,
    noise=10.0,
    random_state=31,
)

x_signal = X_reg[:, 0]
hetero_noise = np.random.default_rng(31).normal(
    loc=0.0,
    scale=4.0 + 6.0 * np.abs(x_signal),
    size=X_reg.shape[0],
)
y_reg = y_reg + hetero_noise
```

- [ ] Step 2: Create a `60/20/20` train/calibration/test split for the regression task.

```python
X_train, X_temp, y_train, y_temp = train_test_split(
    X_reg,
    y_reg,
    test_size=0.4,
    random_state=31,
)

X_calib, X_test, y_calib, y_test = train_test_split(
    X_temp,
    y_temp,
    test_size=0.5,
    random_state=31,
)
```

- [ ] Step 3: Fit a `RandomForestRegressor` wrapped in `SplitConformalRegressor(confidence_level=0.9)` and verify empirical coverage on the test split.

```python
split_cp = SplitConformalRegressor(
    estimator=RandomForestRegressor(
        n_estimators=300,
        random_state=31,
        n_jobs=-1,
    ),
    confidence_level=0.9,
    prefit=False,
).fit(X_train, y_train).conformalize(X_calib, y_calib)

y_pred_split, interval_split = split_cp.predict_interval(X_test)
lower_split = interval_split[:, 0, 0]
upper_split = interval_split[:, 1, 0]

coverage_split = np.mean((y_test >= lower_split) & (y_test <= upper_split))
width_split = upper_split - lower_split

print(f"Split-conformal coverage: {coverage_split:.3f}")
print(f"Average width: {width_split.mean():.3f}")
```

- [ ] Step 4: Slice coverage and width by `|x|` quintile and verify that vanilla split conformal tends to produce a roughly constant correction even though the underlying problem is more variable at larger `|x|`.

```python
abs_x_test = np.abs(X_test[:, 0])
quintiles = np.quantile(abs_x_test, [0.2, 0.4, 0.6, 0.8])
bins = np.digitize(abs_x_test, quintiles)

for bucket in range(5):
    mask = bins == bucket
    bucket_coverage = np.mean(
        (y_test[mask] >= lower_split[mask]) & (y_test[mask] <= upper_split[mask])
    )
    bucket_width = np.mean(width_split[mask])
    print(
        f"bucket={bucket} n={mask.sum()} "
        f"coverage={bucket_coverage:.3f} width={bucket_width:.3f}"
    )
```

- [ ] Step 5: Build CQR with two `GradientBoostingRegressor(loss="quantile")` models at `alpha=0.05` and `alpha=0.95`, plus a median point model, then compare width by quintile against Step 4.

```python
lower_q = GradientBoostingRegressor(
    loss="quantile",
    alpha=0.05,
    random_state=31,
)
upper_q = GradientBoostingRegressor(
    loss="quantile",
    alpha=0.95,
    random_state=31,
)
median_q = GradientBoostingRegressor(
    loss="quantile",
    alpha=0.5,
    random_state=31,
)

lower_q.fit(X_train, y_train)
upper_q.fit(X_train, y_train)
median_q.fit(X_train, y_train)

cqr = ConformalizedQuantileRegressor(
    estimator=[lower_q, upper_q, median_q],
    confidence_level=0.9,
    prefit=True,
).conformalize(X_calib, y_calib)

y_pred_cqr, interval_cqr = cqr.predict_interval(X_test)
lower_cqr = interval_cqr[:, 0, 0]
upper_cqr = interval_cqr[:, 1, 0]
width_cqr = upper_cqr - lower_cqr

for bucket in range(5):
    mask = bins == bucket
    print(
        f"bucket={bucket} split_width={width_split[mask].mean():.3f} "
        f"cqr_width={width_cqr[mask].mean():.3f}"
    )
```

- [ ] Step 6: Create a small multiclass classification problem and fit `SplitConformalClassifier(confidence_level=0.9)` on a train/calibration split, then produce prediction sets with `predict_set()`.

```python
X_cls, y_cls = make_classification(
    n_samples=1200,
    n_features=10,
    n_informative=7,
    n_redundant=1,
    n_classes=4,
    n_clusters_per_class=1,
    class_sep=1.0,
    random_state=31,
)

X_train_cls, X_temp_cls, y_train_cls, y_temp_cls = train_test_split(
    X_cls,
    y_cls,
    test_size=0.4,
    random_state=31,
    stratify=y_cls,
)

X_calib_cls, X_test_cls, y_calib_cls, y_test_cls = train_test_split(
    X_temp_cls,
    y_temp_cls,
    test_size=0.5,
    random_state=31,
    stratify=y_temp_cls,
)

cp_classifier = SplitConformalClassifier(
    estimator=LogisticRegression(max_iter=2000),
    confidence_level=0.9,
    conformity_score="aps",
    prefit=False,
    random_state=31,
).fit(X_train_cls, y_train_cls).conformalize(X_calib_cls, y_calib_cls)

y_pred_cls, y_sets_cls = cp_classifier.predict_set(X_test_cls)
coverage_cls = np.mean(y_sets_cls[np.arange(y_test_cls.shape[0]), y_test_cls, 0])
print(f"Classification set coverage: {coverage_cls:.3f}")
```

- [ ] Step 7: Inspect the set-size distribution and write down what a larger set means for downstream routing.

```python
set_sizes = y_sets_cls[:, :, 0].sum(axis=1)
for size, count in zip(*np.unique(set_sizes, return_counts=True)):
    print(f"set_size={int(size)} count={int(count)}")
```

- [ ] Step 8: Write one paragraph explaining where conformal helped, where the base model remained the bottleneck, and whether the deployment would need conditional coverage work that vanilla conformal does not provide.

### Completion Check

- [ ] I verified empirical regression coverage on a fresh test split rather than on training or calibration data.
- [ ] I compared vanilla split-conformal width against CQR width by `|x|` quintile and explained the heteroskedastic pattern.
- [ ] I produced classification prediction sets with `predict_set()` and inspected the set-size distribution explicitly.
- [ ] I stated whether the deployment needs marginal coverage only or a stronger cohort-level audit that vanilla conformal does not guarantee.
- [ ] I documented whether interval or set width was useful enough to change the downstream decision.

## Sources

- https://contrib.scikit-learn.org/MAPIE/stable/
- https://contrib.scikit-learn.org/MAPIE/stable/getting-started/quick-start/
- https://contrib.scikit-learn.org/MAPIE/stable/getting-started/split-cross-conformal/
- https://contrib.scikit-learn.org/MAPIE/stable/getting-started/choosing-algorithm/
- https://contrib.scikit-learn.org/MAPIE/stable/getting-started/v1-release-notes/
- https://contrib.scikit-learn.org/MAPIE/stable/theory/regression/
- https://contrib.scikit-learn.org/MAPIE/stable/theory/classification/
- https://contrib.scikit-learn.org/MAPIE/stable/theory/conformity-scores/
- https://contrib.scikit-learn.org/MAPIE/stable/api/regression/
- https://contrib.scikit-learn.org/MAPIE/stable/api/classification/
- https://contrib.scikit-learn.org/MAPIE/stable/all-examples/
- https://github.com/scikit-learn-contrib/MAPIE
- https://scikit-learn.org/stable/modules/calibration.html
- https://arxiv.org/abs/2107.07511
- https://arxiv.org/abs/1905.03222
- https://arxiv.org/abs/2202.07650

## Next Module

The next module in this Tier-2 sequence is **Module 2.6: Fairness & Bias Auditing**, covering fairness metrics, subgroup miscoverage, the cohort-level audit step that vanilla split conformal does not give you, and the
production controls that turn a marginal-coverage guarantee into a defensible cross-cohort one. It ships next in Phase 3 of [issue #677](https://github.com/kube-dojo/kube-dojo.github.io/issues/677); the link in this
section will go live when that PR lands.
