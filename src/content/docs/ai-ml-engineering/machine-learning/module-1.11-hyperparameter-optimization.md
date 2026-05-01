---
title: "Hyperparameter Optimization"
description: "Choose and run hyperparameter search under an honest evaluation protocol so the score you celebrate is the score your deployment can actually keep."
slug: ai-ml-engineering/machine-learning/module-1.11-hyperparameter-optimization
sidebar:
  order: 11
---

> Track: AI/ML Engineering | Complexity: Intermediate | Time: 75-90 minutes
> Prerequisites: [Module 1.1: Scikit-learn API & Pipelines](../module-1.1-scikit-learn-api-and-pipelines/), [Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/), [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/), [Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/), [Module 1.5: Decision Trees & Random Forests](../module-1.5-decision-trees-and-random-forests/), [Module 1.6: XGBoost & Gradient Boosting](../module-1.6-xgboost-gradient-boosting/), and [Module 1.10: Dimensionality Reduction](../module-1.10-dimensionality-reduction/).

Most teams arrive at hyperparameter optimization with a goal that sounds
precise and is actually vague.
They want the best score.

That phrase hides nearly everything that matters.
Best on which split.
Best on which metric.
Best after how many retries.
Best before or after someone peeked at the test set.

The mistake is not ambition.
The mistake is acting as though search algorithms come first.
They do not.
Honest goal-setting comes first.

A team that cannot clearly say what the score means is not doing model
selection.
It is doing organized wishful thinking with compute attached.

This module is therefore not a catalog of knobs.
It is a discipline for making tuning honest enough that the result can
survive contact with retraining, deployment, and review.

You already have the ingredients for that discipline.
[Module 1.1: Scikit-learn API & Pipelines](../module-1.1-scikit-learn-api-and-pipelines/)
gave you estimator shape and pipeline boundaries.
[Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/)
showed that some models expose a clean regularization path instead of an
open-ended search party.
[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/)
made leakage a first-class engineering concern rather than a footnote.

Hyperparameter optimization sits on top of all of that.
It is less about clever search and more about refusing to lie to
yourself.

## Learning Outcomes

- Design a tuning protocol that separates model selection, inner-loop
  hyperparameter search, and final generalization estimation under a
  leakage-safe evaluation plan.
- Evaluate when `GridSearchCV`, `RandomizedSearchCV`, successive
  halving, Optuna, or Ray Tune matches the shape of the search space and
  the compute budget you actually have.
- Debug optimistic tuning results by tracing how fold reuse, metric
  mismatch, and accidental test-set contact bias the reported score.
- Justify a stopping rule for search based on diminishing returns,
  variance across folds, and deployment cost rather than on the emotional
  pull of a slightly larger validation number.
- Choose and defend a scoring strategy that matches ranking,
  calibration, imbalance, or business utility requirements for the real
  decision the model will support.

## Why This Module Matters

The scikit-learn grid-search guide is careful about what search APIs
actually promise.
They compare candidates under a cross-validation protocol and can refit
the selected candidate on the full training set, but they do not erase
the need for correct evaluation design:
[https://scikit-learn.org/stable/modules/grid_search.html](https://scikit-learn.org/stable/modules/grid_search.html)

Optuna is equally direct in its own way.
It gives you a study, a sampler, pruning support, and a strong
optimization interface, but it does not magically define what "good"
means for your application:
[https://optuna.readthedocs.io/en/stable/](https://optuna.readthedocs.io/en/stable/)

That distinction becomes painful on a retraining deadline.
A model is being refreshed for the next reporting cycle.
For months the team has treated one number as the gold metric:
"tuned-model AUC."

Only late in the process does someone ask the question that should have
been asked on day one.
Was that score estimated on a split that stayed blind to tuning.

The answer is no.
The team tuned across the same five-fold split that it later quoted in
slides and status updates.
Hyperparameters were chosen because they looked good on those folds, and
then the mean score on those same folds was reported as if it were an
unbiased estimate of generalization.

Nothing in that workflow feels obviously dishonest when you are close to
it.
`GridSearchCV` produces a clean table.
Optuna produces an elegant optimization history.
The code runs.
The number improves.

But the reported number is optimistic.
Not because the models are bad.
Because the protocol reused the same evidence both to choose and to
judge.

That is why hyperparameter optimization matters.
It is the meeting point between statistics and engineering process.
You are deciding how much compute to spend, which risks to accept, and
what evidence is strong enough to justify shipping a model.

## Section 1: What "tuning" actually is

Hyperparameters are settings you choose before or around fitting.
Learned parameters are what the estimator discovers from data while it
fits.

For ridge regression, `alpha` is a hyperparameter.
The coefficient vector is learned.
For a random forest, `max_depth`, `max_features`, and
`min_samples_leaf` are hyperparameters.
The split thresholds inside each tree are learned.

That distinction is easy to recite and surprisingly easy to blur in
practice.
Teams talk about "training the best model" when what they really mean is
alternating between fitting and selecting across a family of training
runs.

Hyperparameter optimization serves at least three different jobs.
The first job is model selection across classes.
Should this problem be handled by logistic regression, random forest, or
gradient boosting at all.

The second job is tuning within a chosen class.
Given that gradient boosting is competitive here, which learning rate,
depth, and regularization pattern is stable under the scoring rule you
care about.

The third job is risk-aware deployment selection.
Two candidates may have almost identical mean validation scores, but one
is simpler, cheaper, or more stable across folds.
The right deployment choice may therefore be the one that is slightly
less exciting on a single leaderboard column and much easier to trust.

This is why "find the highest CV score" is not the right definition of
the task.
A search run can always find a number to celebrate if you ask it the
wrong question long enough.

The central claim of this module is stricter.
The goal of hyperparameter optimization is to find a
generalization-stable setting under an honest evaluation protocol.

The phrase "generalization-stable" matters.
A candidate that wins because it loves one fold partition and collapses
when the split changes is not a winner in any operational sense.

The phrase "honest evaluation protocol" matters even more.
If the protocol leaks, overfits selection noise, or uses the wrong
metric, then the search method becomes a faster way to become confident
in the wrong model.

Put differently, search algorithms do not create truth.
They only spend your budget exploring a truth criterion you chose in
advance.

## Section 2: The leakage spine — why naive tuning lies

If you remember only one section from this module, remember this one.
Naive tuning lies most often through evidence reuse.

The loudest form of misuse is tuning on the test set.
That is plain leakage.
If the test set influences hyperparameter choice, it is no longer a test
set.

The quieter form is more common in real teams.
A team runs a search procedure with five-fold cross-validation, then
quotes the best candidate's mean fold score as if it were the final
performance estimate for the tuned process.

That number is useful for ranking candidates inside the search.
It is not an unbiased estimate of the full tuning procedure's future
generalization.
The folds helped decide which hyperparameters looked best.
Selection pressure was applied to that same evidence.

This is the same logic you saw in
[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/).
The details of the algorithm changed.
The leakage principle did not.

Scikit-learn's cross-validation documentation shows the nested
cross-validation pattern directly:
[https://scikit-learn.org/stable/modules/cross_validation.html](https://scikit-learn.org/stable/modules/cross_validation.html)
An outer loop estimates generalization.
An inner loop tunes.
The outer test folds stay blind to the tuning decisions that happen
inside the corresponding outer training folds.

Nested CV is the gold standard when you need a robust estimate of how
the whole tuning workflow will generalize.
It is expensive because every outer split launches an inner search.
But it cleanly separates choosing from judging.

If nested CV is too expensive, the fallback is not to pretend the bias
went away.
The fallback is to keep a tuning-blind holdout test set that you touch
once after search is complete.

That holdout does not need to be mystical.
It just needs discipline.
No threshold adjustment.
No retry because "the score looks weird."
No sneaking one more search after seeing the result.

This is where many practitioner dashboards go wrong.
They track a single "best validation score" number for weeks, and the
team forgets whether that number is for candidate ranking or for final
reporting.
Those are not the same job.

When you hear someone say that their tuned CV AUC "stayed at 0.82 for
three rounds of tuning," do not hear comfort automatically.
Hear a protocol question.
Which folds.
Which search spaces.
Which data boundary stayed blind.

> **Pause and predict** — A team reports that its tuned-model CV AUC
> "stayed at 0.82 across three rounds of tuning," all on the same
> five-fold partition. Is that reassuring because the number is stable,
> or suspicious because the evidence source never changed? Explain what
> extra result you would ask for before treating the score as
> decision-grade.

The right follow-up is usually an outer-loop estimate, a truly blind
holdout result, or at least a rerun with different split seeds.
Without one of those, the team knows the search procedure found a good
candidate for that evidence source.
It does not yet know how the tuned process generalizes.

This is why leakage is the spine of the entire topic.
Every tool in the rest of this module is secondary to this boundary.
A better optimizer cannot rescue a bad protocol.

## Section 3: GridSearchCV — when it is OK and when it is not

`GridSearchCV` is the cleanest search API in the scikit-learn family.
You declare a finite cartesian product of hyperparameter values.
The search evaluates every combination under cross-validation.

That makes it ideal for small, deliberate spaces.
If you have one or two hyperparameters with a short, defensible list of
values, exhaustive enumeration is not naive.
It is transparent.

The trouble begins when teams confuse transparency with scalability.
A grid grows multiplicatively.
Five hyperparameters with six candidate values each means 7,776
combinations before you even multiply by the number of CV folds.

That explosion is not merely a runtime problem.
It also encourages thoughtless search-space design.
People start choosing evenly spaced values on a linear axis for
quantities that live naturally on a log scale, simply because grids want
tables.

There is another hidden cost.
A grid spends equal attention everywhere, even where you already know
the space is implausible.
If `alpha` might matter over orders of magnitude, then evaluating
`0.1`, `0.2`, and `0.3` while skipping `0.001` and `100` is not
systematic.
It is arbitrary but tidy-looking.

That said, `GridSearchCV` has two features that make it a dependable
teaching and production tool for small spaces.
`refit=True` means that once the best hyperparameters are selected, the
estimator is refit on the full training set using those settings.
And `cv_results_` gives you the entire score table rather than only the
winner.

That table is valuable.
It lets you inspect rank, mean score, variance across folds, fit time,
and how flat the top of the search surface really is.
Senior practitioners often learn more from the top ten rows than from
the single winner.

Here is a case where exhaustive search is reasonable.
Ridge regression has a simple structure, the search space is tiny, and
every value has a clear interpretation.

```python
import numpy as np

from sklearn.datasets import load_diabetes
from sklearn.linear_model import Ridge
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

X, y = load_diabetes(return_X_y=True)

pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("model", Ridge()),
])

param_grid = {
    "model__alpha": [0.01, 0.1, 1.0, 10.0, 100.0],
    "model__solver": ["auto", "svd", "cholesky"],
}

search = GridSearchCV(
    pipe,
    param_grid=param_grid,
    scoring="neg_root_mean_squared_error",
    cv=5,
    refit=True,
)

search.fit(X, y)
print(search.best_params_)
print(search.best_score_)
print(search.cv_results_["mean_test_score"][:5])
```

There are only fifteen combinations here.
That is a search space you can reason about.
You can explain every value to a teammate.

Notice what makes this safe.
Scaling lives inside the pipeline.
The scoring rule is explicit.
The grid is small enough that exhaustive search means something other
than brute-force panic.

Where does `GridSearchCV` become the wrong tool.
Usually when the space is wide, mixed-type, or naturally continuous.
It is also the wrong tool when you do not actually believe the midpoint
values in your grid deserve equal attention.

In those cases the question shifts from "enumerate everything" to
"spend budget where coverage matters most."
That is the door to random search.

## Section 4: RandomizedSearchCV and the Bergstra & Bengio result

Random search looks less structured than grid search and is often more
intelligent for real spaces.
That is one of the most useful mindset corrections in applied ML.

Bergstra and Bengio's paper on random search made the argument
memorable:
[https://www.jmlr.org/papers/v13/bergstra12a.html](https://www.jmlr.org/papers/v13/bergstra12a.html)
When only a few hyperparameters matter strongly for a given problem,
randomly sampling the search space often outperforms a grid with the
same evaluation budget.

The reason is geometric rather than mystical.
A grid spends many trials revisiting the same values along weak axes.
Random sampling produces more distinct values along each important axis
over the same number of trials.

This is especially true when parameters live on log scales.
Regularization strengths, kernel widths, and learning rates are almost
never quantities you should explore with equal linear spacing.
Sampling from a log-uniform distribution usually reflects the real
uncertainty much better.

`RandomizedSearchCV` makes budget explicit through `n_iter`.
That is good engineering.
Instead of pretending the space is exhaustible, you decide how many
candidate draws the problem deserves.

You still keep the same scikit-learn conveniences.
Pipelines work the same way.
`refit` works the same way.
`cv_results_` still records what happened.

A practical default for an RBF SVM is to sample `C` and `gamma` from
log-uniform ranges.
The exact bounds depend on feature scale and the problem family, but the
distribution shape matters more than making a pretty grid.

```python
import scipy.stats

from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

X, y = load_breast_cancer(return_X_y=True)

pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("svc", SVC(kernel="rbf")),
])

param_distributions = {
    "svc__C": scipy.stats.loguniform(1e-4, 1e2),
    "svc__gamma": scipy.stats.loguniform(1e-4, 1e0),
}

search = RandomizedSearchCV(
    pipe,
    param_distributions=param_distributions,
    n_iter=24,
    scoring="roc_auc",
    cv=5,
    random_state=0,
    n_jobs=-1,
    refit=True,
)

search.fit(X, y)
print(search.best_params_)
print(search.best_score_)
```

This search does not promise coverage.
It promises a controlled budget with sensible sampling.
That is usually the more honest contract.

Random search also teaches you about scale.
If the top scores cluster tightly across a wide range of sampled values,
the model may simply not be very sensitive within that region.
That is a valuable operational finding.

The danger is using random search as an excuse not to think.
A bad distribution is just as harmful as a bad grid.
If the range is absurdly wide, if the data is unscaled, or if the metric
does not match deployment, stochastic search will simply explore the
wrong world faster.

Still, for medium-size classical ML problems, `RandomizedSearchCV` is a
very strong baseline.
It is simple, budget-aware, and usually gives you more value per trial
than a large exhaustive grid.

## Section 5: Successive halving — sklearn's HalvingGridSearchCV / HalvingRandomSearchCV

Sometimes the real bottleneck is not the count of candidates but the
cost of evaluating each candidate at full resource.
That is where successive halving becomes attractive.

The idea is intuitive.
Start many candidates cheaply.
Measure them with limited resource.
Drop the obvious losers.
Spend more resource only on survivors.

Scikit-learn exposes this idea through
`HalvingGridSearchCV` and `HalvingRandomSearchCV`:
[https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.HalvingGridSearchCV.html](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.HalvingGridSearchCV.html)
[https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.HalvingRandomSearchCV.html](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.HalvingRandomSearchCV.html)
The broader user-guide discussion sits in the same model-selection
chapter as the other search tools:
[https://scikit-learn.org/stable/modules/grid_search.html](https://scikit-learn.org/stable/modules/grid_search.html)

By default, the resource is `n_samples`.
That means early rounds compare candidates using smaller subsets of the
training data.
For some estimators you can instead use a fitting parameter such as
`n_estimators` or `max_iter`.

This is powerful because many bad candidates reveal themselves early.
Why fully train a hundred models if most of them are clearly weak after
a cheap partial evaluation.

The tradeoff is ranking bias.
Early-stage performance is not always a faithful preview of final-stage
performance.
A candidate that learns slowly may look poor with small resource and
become strong later.

That is the core engineering judgment.
Successive halving buys wall-clock savings by betting that cheap early
signals are informative enough.
Sometimes that bet is excellent.
Sometimes it kills the right answer before it has enough room to
mature.

A random forest is a natural example for resource-based halving because
`n_estimators` is both meaningful and incremental.

```python
from sklearn.experimental import enable_halving_search_cv
import scipy.stats

from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import HalvingRandomSearchCV

X, y = load_breast_cancer(return_X_y=True)

param_distributions = {
    "max_depth": [None, 3, 5, 8],
    "max_features": ["sqrt", "log2", 0.5],
    "min_samples_leaf": [1, 2, 4],
}

search = HalvingRandomSearchCV(
    RandomForestClassifier(random_state=0, n_jobs=-1),
    param_distributions=param_distributions,
    factor=3,
    resource="n_estimators",
    min_resources=30,
    max_resources=300,
    scoring="roc_auc",
    cv=5,
    random_state=0,
)

search.fit(X, y)
print(search.best_params_)
print(search.best_score_)
```

Notice what this code says operationally.
We are comfortable using small forests as a screening stage.
We are willing to accept that some candidates may be underrated early in
exchange for cheaper exploration.

That is often a good bargain for tree ensembles and iterative models.
It is less appealing when early learning curves are noisy or when small
resource rankings are known to be unstable.

> **Pause and decide** — You have two jobs.
> In the first, each candidate is a random forest whose early ranking is
> usually visible after a modest number of trees.
> In the second, each candidate is a model that learns slowly and
> irregularly, with some strong settings looking mediocre until late.
> Which job is a good fit for halving, and which job risks pruning away
> the eventual winner.

The answer is not "halving is good" or "halving is bad."
The answer is about whether cheap resource is predictive enough for this
family and this dataset.

That principle scales beyond sklearn.
Once you understand successive halving conceptually, pruners and
schedulers in other frameworks become much easier to reason about.

## Section 6: Optuna — TPE, study, trial, pruners

Optuna is a strong modern default for classical ML tuning because it
separates the search loop from the objective function cleanly while
keeping the API small.
The landing page and tutorial are the right entry points:
[https://optuna.readthedocs.io/en/stable/tutorial/index.html](https://optuna.readthedocs.io/en/stable/tutorial/index.html)
[https://optuna.readthedocs.io/en/stable/](https://optuna.readthedocs.io/en/stable/)

The basic nouns matter.
A `study` owns an optimization run.
A `trial` represents one sampled candidate.
The objective function builds a model, evaluates it, and returns the
number the study should optimize.

One important practitioner correction belongs here because many people
get it wrong from memory.
Optuna's default sampler is TPE, the Tree-structured Parzen Estimator,
not random.
The sampler reference is explicit about the available choices:
[https://optuna.readthedocs.io/en/stable/reference/samplers/index.html](https://optuna.readthedocs.io/en/stable/reference/samplers/index.html)

That matters because it changes how you think about default behavior.
If you call `optuna.create_study()` without overriding the sampler,
Optuna is already doing model-based search rather than simple random
draws.

The core suggest API is intentionally plain.
`trial.suggest_float(..., log=True)` handles log-scale continuous ranges.
`trial.suggest_int` handles integer ranges.
`trial.suggest_categorical` handles discrete choices.

The simplest honest Optuna objective for sklearn keeps CV inside the
objective and returns the mean score.

```python
import optuna

from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

X, y = load_breast_cancer(return_X_y=True)

def objective(trial):
    c_value = trial.suggest_float("C", 1e-4, 1e2, log=True)
    gamma_value = trial.suggest_float("gamma", 1e-4, 1e0, log=True)

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("svc", SVC(kernel="rbf", C=c_value, gamma=gamma_value)),
    ])

    scores = cross_val_score(pipe, X, y, cv=5, scoring="roc_auc")
    return scores.mean()

study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=30)

print(study.best_params)
print(study.best_value)
```

This snippet is compact because Optuna is letting sklearn do what
sklearn is good at.
The objective is not a new training framework.
It is a disciplined wrapper around candidate construction and
evaluation.

`study.best_params` tells you the best sampled setting.
`study.best_value` tells you the objective value of that trial.
And if you want diagnostics, Optuna's visualization helpers such as
`optuna.visualization.plot_optimization_history` can show whether the
search improved steadily, plateaued early, or jumped only occasionally.

The more advanced Optuna feature is pruning.
Pruning is Optuna's version of "stop wasting time on candidates that
look unpromising."
The pruner reference includes `MedianPruner`,
`SuccessiveHalvingPruner`, and `HyperbandPruner`:
[https://optuna.readthedocs.io/en/stable/reference/pruners.html](https://optuna.readthedocs.io/en/stable/reference/pruners.html)

To prune honestly, the objective must report intermediate values.
That means your training process needs meaningful checkpoints.
Iterative models and staged ensembles are a natural fit.

Here is a simple staged boosting-style pattern using
`GradientBoostingClassifier` with `warm_start=True`.

```python
import optuna

from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

X, y = load_breast_cancer(return_X_y=True)
X_train, X_valid, y_train, y_valid = train_test_split(
    X,
    y,
    test_size=0.2,
    stratify=y,
    random_state=0,
)

def pruning_objective(trial):
    learning_rate = trial.suggest_float("learning_rate", 1e-3, 3e-1, log=True)
    max_depth = trial.suggest_int("max_depth", 1, 3)

    model = GradientBoostingClassifier(
        learning_rate=learning_rate,
        max_depth=max_depth,
        n_estimators=1,
        warm_start=True,
        random_state=0,
    )

    score = 0.0
    for step, n_estimators in enumerate([20, 40, 80, 120, 160], start=1):
        model.set_params(n_estimators=n_estimators)
        model.fit(X_train, y_train)
        score = roc_auc_score(y_valid, model.predict_proba(X_valid)[:, 1])
        trial.report(score, step)

        if trial.should_prune():
            raise optuna.TrialPruned()

    return score

study = optuna.create_study(
    direction="maximize",
    pruner=optuna.pruners.MedianPruner(),
)
study.optimize(pruning_objective, n_trials=20)
```

This pattern is valuable because it changes the cost structure of search.
Instead of paying full price for every candidate, you pay enough to find
out whether the candidate deserves more time.

The danger is the same one you saw with halving.
If the early reported values are noisy or unrepresentative, pruning can
be too aggressive.
Median pruning is not wisdom.
It is a policy.

Still, for one-machine tuning on real projects, Optuna often feels like
the point where search becomes ergonomic rather than ceremonial.
You get flexible spaces, good defaults, storage options, pruners, and a
small amount of framework surface area to learn.

## Section 7: Hyperopt, briefly

Hyperopt matters historically because it popularized practical
model-based hyperparameter optimization for many ML users before newer
frameworks became the default choice:
[https://hyperopt.github.io/hyperopt/](https://hyperopt.github.io/hyperopt/)

Its TPE-based search ideas remain familiar in the literature and in old
codebases, and you will still encounter it in internal notebooks,
benchmark scripts, and older service stacks.

Most modern teams reach for Optuna first instead.
The reason is not that Hyperopt became wrong.
The reason is that Optuna usually gives a cleaner study abstraction,
better pruning ergonomics, easier persistence, and more convenient
diagnostic tooling for day-to-day practitioner work.

The useful mental model is that Hyperopt is the older sibling whose core
ideas still matter.
If you inherit it, you should understand it.
If you are choosing fresh tooling for sklearn-centric work today, you
will usually reach for Optuna unless there is a local platform reason
not to.

## Section 8: Ray Tune — when one machine is not enough

There is a point where the question is no longer "which sampler should I
use on my laptop."
The question becomes "how do I coordinate large numbers of expensive
trials across many CPUs or GPUs without writing a distributed
orchestrator by hand."

That is Ray Tune's domain:
[https://docs.ray.io/en/latest/tune/index.html](https://docs.ray.io/en/latest/tune/index.html)

Ray Tune is not just another search-space syntax.
It is a distributed tuning system.
It assumes that trials may run in parallel across machines, that
schedulers may stop weak trials early, and that search algorithms may be
swapped independently from execution policy.

The scheduler catalog includes tools such as `ASHAScheduler`,
`HyperBandScheduler`, `PopulationBasedTraining`, and
`MedianStoppingRule`:
[https://docs.ray.io/en/latest/tune/api/schedulers.html](https://docs.ray.io/en/latest/tune/api/schedulers.html)

The search-algorithm side includes the simple
`BasicVariantGenerator`, more specialized search integrations, and
wrappers such as `OptunaSearch`:
[https://docs.ray.io/en/latest/tune/api/suggestion.html](https://docs.ray.io/en/latest/tune/api/suggestion.html)

Two papers anchor the intuition behind the common early-stopping
policies.
Hyperband formalized the allocate-and-drop strategy for budgeted search:
[https://arxiv.org/abs/1603.06560](https://arxiv.org/abs/1603.06560)
And the ASHA paper showed how that idea can be adapted efficiently for
massively parallel settings:
[https://arxiv.org/abs/1810.05934](https://arxiv.org/abs/1810.05934)

When should you actually use Ray Tune.
Usually when trials are expensive, spaces are large, and parallel
hardware is available.
If your entire experiment fits comfortably in `RandomizedSearchCV` or
Optuna on one machine, distributed orchestration may be unnecessary
complexity.

Here is the minimal shape of a Tune run with ASHA.

```python
from ray import tune
from ray.tune.schedulers import ASHAScheduler

from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import cross_val_score

X, y = load_breast_cancer(return_X_y=True)

def trainable(config):
    model = GradientBoostingClassifier(
        learning_rate=config["learning_rate"],
        max_depth=config["max_depth"],
        n_estimators=config["n_estimators"],
        random_state=0,
    )
    score = cross_val_score(model, X, y, cv=5, scoring="roc_auc").mean()
    tune.report(auc=score)

scheduler = ASHAScheduler(
    metric="auc",
    mode="max",
    max_t=20,
    grace_period=3,
    reduction_factor=3,
)

analysis = tune.run(
    trainable,
    config={
        "learning_rate": tune.loguniform(1e-4, 1e-1),
        "max_depth": tune.randint(2, 8),
        "n_estimators": tune.choice([50, 100, 200]),
    },
    num_samples=20,
    scheduler=scheduler,
    metric="auc",
    mode="max",
)
```

This snippet hides a lot of power behind a small surface.
The search space is declarative.
The scheduler controls early stopping.
And the same conceptual split you learned from Optuna still applies:
the trainable defines how a candidate is evaluated, while the tuning
system decides which candidates deserve compute.

Ray Tune becomes compelling when the experiment volume justifies the
extra operational overhead.
If you are tuning deep models, large gradient-boosting jobs, or many GPU
trials at once, it can save enormous engineering effort.
If you are searching a modest tabular model on one dataset, it is often
too much machinery.

Distributed tuning is not a badge of seriousness.
It is an infrastructure choice.
Make it only when the resource profile requires it.

## Section 9: The right scoring metric

The search algorithm cannot rescue a bad scoring rule.
If `scoring=` does not match the deployment decision, then the entire
optimization effort is pointed at the wrong hill.

This is where
[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/)
has to stay close at hand.
A metric is not just a reporting preference.
It encodes what type of mistake you are rewarding or punishing during
selection.

ROC-AUC is useful when ranking quality matters across thresholds.
Average precision is often more honest for highly imbalanced positive
classes because it focuses on performance where the positives actually
live.
`neg_log_loss` matters when calibrated probabilities are part of the
decision rather than only class ordering.

If the business utility is custom, build a custom scorer.
`make_scorer` exists for a reason.
The default metrics are not sacred.

Multi-metric search is one of the most underused features in sklearn.
You can ask the search object to record several metrics for every
candidate and still choose one metric for final refitting.

```python
import scipy.stats

from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

X, y = load_breast_cancer(return_X_y=True)

pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("svc", SVC(kernel="rbf", probability=True)),
])

search = RandomizedSearchCV(
    pipe,
    param_distributions={
        "svc__C": scipy.stats.loguniform(1e-4, 1e2),
        "svc__gamma": scipy.stats.loguniform(1e-4, 1e0),
    },
    n_iter=20,
    scoring={"auc": "roc_auc", "ap": "average_precision"},
    refit="auc",
    cv=5,
    random_state=0,
)

search.fit(X, y)
print(search.cv_results_["mean_test_auc"][:3])
print(search.cv_results_["mean_test_ap"][:3])
```

This table becomes extremely useful when you have multiple constraints.
Maybe several candidates tie on AUC but differ on average precision.
Maybe the top-ranked model by AUC has much worse fit time.
Maybe you care about calibration enough to inspect log loss before
shipping.

That is how grown-up model selection usually feels.
There is one refit metric because the API needs a winner, but the final
deployment decision often uses several columns from `cv_results_`.

> **Pause and predict** — You are tuning a fraud detector where the
> positive class is rare and the ranking quality among the top reviewed
> cases matters more than broad threshold-free separability across the
> full class distribution. Which scoring choice is likely to mislead you:
> plain accuracy, ROC-AUC, or average precision, and why.

The point is not that ROC-AUC is bad.
The point is that metric choice is problem-shape choice.
A beautiful optimizer attached to an irrelevant score is still a
beautiful failure.

## Section 10: When tuning is not worth it

Hyperparameter optimization has a strong aura around it because it looks
like serious engineering.
Sometimes the serious thing to do is to skip it.

Small datasets are the first warning sign.
If fold-to-fold variance is large, then the tuning signal may be weaker
than the noise created by the split itself.
Long search runs in that regime often produce confidence without much
real lift.

Well-regularized linear models are another case.
As you saw in
[Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/),
the regularization path is already a structured search problem.
`RidgeCV` and `LogisticRegressionCV` are often enough.
You do not always need a separate general-purpose optimizer around them.

Default sklearn baselines also deserve more respect than many teams give
them.
A random forest with sensible defaults is often close enough to useful
that a huge search budget buys less than better features or a clearer
metric definition.
The detailed tree-specific tuning playbook belongs back in
[Module 1.5: Decision Trees & Random Forests](../module-1.5-decision-trees-and-random-forests/).

Feature engineering often dominates tuning.
If the current representation is weak, no optimizer will search you into
a better feature space.
That is why
[Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/)
stays upstream of this module both conceptually and operationally.

There is also a sequencing issue.
When you are still framing the problem, getting a baseline from
[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/)
matters more than polishing the baseline's hyperparameters.
A weakly framed problem plus heroic tuning is still a weakly framed
problem.

Tuning is worth it when the candidate family is already plausible, the
metric is meaningful, and the budget has a reasonable chance of
improving a deployment decision.
Otherwise it is often a distraction with a graph attached.

## Section 11: How much tuning is enough

One of the hardest operational questions is not how to start search.
It is how to stop.

The emotionally dangerous answer is "when the score stops improving."
That sounds rigorous and becomes endless in practice because a long
enough search often discovers a tiny improvement somewhere.

A better answer is based on diminishing returns.
On many simple tabular problems, the first modest batch of trials
captures most of the available lift.
Later trials mostly reshuffle a tight cluster of near-equivalent
candidates.

That is why experienced practitioners often examine the running best
curve rather than only the final winner.
If the curve flattened early and the top candidates are tightly grouped,
continuing search may be a compute decision rather than a modeling
decision.

This is also why tuning order matters.
First decide which model class deserves attention.
Then tune within that class.
Do not spend a large budget polishing a class that never had a real
chance.

The model-class playbooks already live elsewhere in the track.
[Module 1.5: Decision Trees & Random Forests](../module-1.5-decision-trees-and-random-forests/)
explains the random-forest-specific order of attack.
[Module 1.6: XGBoost & Gradient Boosting](../module-1.6-xgboost-gradient-boosting/)
does the same for boosting.
This module is teaching the search-protocol shape that wraps those
playbooks.

What does "enough" look like in practice.
It often looks like the top of `cv_results_` being flat.
It looks like repeated trials finding the same region rather than new
regimes.
It looks like the blind holdout no longer moving in meaningful ways.

Enough also depends on cost.
A modest metric gain may be worth it for a high-value decision system.
The same gain may be absurdly expensive for a batch model whose output
only weakly influences operations.

Stopping is therefore an engineering judgment, not a moral weakness.
Your job is not to prove that no better setting exists anywhere.
Your job is to stop when more search is unlikely to change the shipping
decision.

## Section 12: Where HPO is the wrong tool

Hyperparameter optimization is the wrong tool when the real problem is
data or representation.
If your features are weak, missing important business structure, or
leaking target information, better search only helps you discover the
wrongness more efficiently.

It is the wrong tool when the metric is wrong.
This is another direct return to
[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/).
If the deployment cares about calibration or rare-positive precision and
you optimize for something else, you are tuning the wrong objective.

It is the wrong tool when the search space is wrong.
No optimizer can tune its way out of the wrong model class.
A linear model with a poor representation does not become a
state-of-the-art non-linear learner because you searched `C` more
carefully.

It is also the wrong tool when deployment cost dominates.
A tiny validation gain is not automatically valuable if it multiplies
training cost, latency, or operational complexity.
This is especially relevant when moving from simpler models to large
boosting pipelines or distributed search infrastructure.

That is where cross-links matter.
If the fix is cleaner features, go back to
[Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/).
If the question is whether boosting is the right class at all, go back
to [Module 1.6: XGBoost & Gradient Boosting](../module-1.6-xgboost-gradient-boosting/).
If the problem naturally wants learned representations, the deeper
answer may live in the deep-learning track rather than here.

Search is powerful.
It is not foundational.
It sits downstream of problem framing, data construction, and evaluation
design.

## Section 13: Connecting back

[Module 1.1: Scikit-learn API & Pipelines](../module-1.1-scikit-learn-api-and-pipelines/)
is where the operational shape of this entire module begins.
Search objects are estimators wrapped around other estimators.
Pipelines are what keep preprocessing, feature transforms, and model
fitting inside the same fold-safe boundary.
If you do not feel the pipeline boundary clearly, tuning will leak.

[Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/)
should stay in your head whenever a tuning problem starts to look larger
than it really is.
Sometimes the regularization path is the tuning story.
Sometimes a disciplined linear baseline with `CV` helpers is the answer,
not a giant generic optimizer.

[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/)
is the anchor for every honest claim in this module.
Nested CV, blind holdouts, leakage-safe pipelines, and scoring alignment
all come directly from that foundation.
If you are uncertain about whether a tuning result is trustworthy, that
module is the first place to revisit.

[Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/)
explains why search cannot compensate for a weak representation.
It also explains why scaling, encoding, and imputation belong inside the
pipeline that the search object evaluates, not in a precomputed step on
the full dataset.

[Module 1.5: Decision Trees & Random Forests](../module-1.5-decision-trees-and-random-forests/)
contains the model-specific meaning behind many common random-forest
hyperparameters.
This module tells you how to search them honestly.
That module tells you which ones are worth your time and in what order.

[Module 1.6: XGBoost & Gradient Boosting](../module-1.6-xgboost-gradient-boosting/)
does the same for boosting families.
Learning rate, depth, sampling, and tree count all have their own local
interactions.
The current module's job is to make sure the search protocol around
those interactions is not statistically self-deceiving.

[Module 1.10: Dimensionality Reduction](../module-1.10-dimensionality-reduction/)
matters because representation choices themselves can become tunable
objects.
If you are choosing `n_components`, perplexity-like controls, or other
transforms, the same leakage and fold-boundary rules still apply.
The transform must live inside the evaluation pipeline.

The forward link is
[Module 1.12: Time Series Forecasting](../module-1.12-time-series-forecasting/).
Time series makes all of this stricter, not looser.
Search must respect temporal splits, delayed feedback, and operational
costs that often dwarf small leaderboard gains.

## Did You Know?

- Optuna's default sampler is TPE, not random, so an untouched
  `create_study()` call is already doing model-based search:
  https://optuna.readthedocs.io/en/stable/reference/samplers/index.html
- Scikit-learn's `HalvingRandomSearchCV` uses an iterative halving
  schedule whose default resource is `n_samples`, which is why early
  rounds can screen candidates using smaller subsets first:
  https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.HalvingRandomSearchCV.html
- Bergstra and Bengio argued that random search can beat grid search in
  high-dimensional spaces when only a few hyperparameters matter
  strongly:
  https://www.jmlr.org/papers/v13/bergstra12a.html
- `GridSearchCV.cv_results_` is a dictionary of arrays indexed by
  candidate, which means you can inspect fold-level behavior and not
  merely the winning mean score:
  https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GridSearchCV.html

## Common Mistakes

| Mistake | Why it bites | Fix |
| --- | --- | --- |
| Reporting the best inner-CV score as the final generalization estimate | The same folds helped select the hyperparameters, so the reported number is biased upward for the tuned procedure | Use nested CV for estimation or keep a tuning-blind holdout that is touched once at the end |
| Searching outside a pipeline | Scaling, encoding, imputation, or dimensionality reduction can leak fold information when fit before CV | Put every data-dependent transform inside the same `Pipeline` the search object evaluates |
| Using a linear grid for log-scale parameters | The search over-samples arbitrary midpoints and under-samples the orders of magnitude that actually matter | Use `loguniform` or `suggest_float(..., log=True)` for quantities such as `C`, `gamma`, and learning rate |
| Pruning or halving too aggressively | Early rankings can disagree with full-resource rankings, so promising slow starters get eliminated | Use conservative early-stopping settings when learning curves are noisy and verify that cheap-resource ranking is informative |
| Optimizing the wrong metric | The selected winner may be excellent at a number nobody deploys against | Match `scoring=` to ranking, imbalance, calibration, or business utility requirements before you search |
| Spending a huge budget before choosing a model class | You polish one family deeply without learning whether another family was stronger to begin with | Compare a small number of strong classes first, then tune within the best contenders |
| Treating tiny score gains as automatic wins | The improvement may be within fold variance or not worth the added compute and complexity | Inspect variance, blind-holdout movement, and deployment cost before declaring the search worth it |

## Quiz

1. A team uses `RandomizedSearchCV` with five-fold CV on the training
   set, finds a great configuration for gradient boosting, and then
   reports `best_score_` as the final model performance in a quarterly
   review.
   What is wrong with that reporting choice, and what result would make
   the claim more trustworthy.

<details><summary>Answer</summary>
`best_score_` is valid for ranking candidates inside that search, but it
is not an unbiased estimate of the full tuning procedure's future
generalization because the same folds were used for selection and
reporting.
The safest fix is nested cross-validation, where the outer loop measures
the tuned process on untouched outer test folds.
If nested CV is too expensive, a tuning-blind holdout test set touched
once after search is complete is the next-best choice.
</details>

2. A practitioner defines a five-dimensional grid with six values along
   each axis because they want to be "systematic."
   They only have budget for a modest number of evaluations and suspect
   that only one or two hyperparameters matter strongly.
   Why is the grid a poor fit here, and what alternative matches the
   problem better.

<details><summary>Answer</summary>
The grid creates 7,776 candidate combinations before the CV multiplier,
which is a poor use of budget when only a few axes likely matter.
Most trials will revisit the same values along weak dimensions while
failing to sample enough distinct values on the truly important axes.
`RandomizedSearchCV` with sensible distributions, especially log-uniform
ranges for scale-sensitive parameters, is usually the better choice.
</details>

3. A random-forest tuning job takes too long, so someone proposes
   switching to `HalvingRandomSearchCV` with `resource='n_estimators'`.
   Under what conditions is that a smart move, and what specific risk
   should the team keep in mind.

<details><summary>Answer</summary>
It is a smart move when small forests are good early indicators of which
hyperparameter settings deserve more attention, because halving can drop
obvious losers cheaply and spend more trees only on survivors.
The risk is that early-stage rankings may disagree with full-resource
rankings, especially if some promising settings learn slowly or have
noisy partial results.
The team should therefore treat aggressive halving as a cost-saving
policy, not as a guarantee of identical winners.
</details>

4. A teammate says, "Optuna is basically random search unless you wire
   in something fancy."
   How would you correct that statement, and why does the correction
   matter when interpreting results.

<details><summary>Answer</summary>
Optuna's default sampler is TPE, not random, so a plain
`optuna.create_study()` call is already using a model-based search
strategy.
That matters because it changes the baseline expectation for how trials
are chosen and how quickly the search may concentrate around promising
regions.
It also means that if you want truly random sampling for comparison, you
must request it explicitly instead of assuming the default does that.
</details>

5. A search over an imbalanced fraud dataset is optimized for plain
   accuracy because it is the easiest metric to explain.
   The final model looks excellent on paper and disappoints badly once
   analysts start reviewing flagged cases.
   What went wrong at the tuning stage.

<details><summary>Answer</summary>
The search optimized a metric that largely ignores the decision shape
the deployment actually cares about.
With a rare positive class, plain accuracy can stay high while the model
does a poor job ranking the cases analysts most need to review.
A better search would usually track average precision or another metric
that reflects rare-positive retrieval quality, possibly alongside AUC
for broader ranking context.
</details>

6. A team has only a single machine, modest tabular data, and no need
   for GPUs or cluster scheduling.
   One engineer wants Ray Tune anyway because "serious projects use
   distributed tools."
   How would you respond.

<details><summary>Answer</summary>
Ray Tune is valuable when trials are expensive, spaces are large, and
parallel hardware makes distributed scheduling worthwhile.
If the search fits comfortably on one machine, the extra orchestration
may add complexity without changing the decision.
In that setting, `RandomizedSearchCV` or Optuna usually gives the team a
faster and cleaner path to the answer.
</details>

7. An Optuna study shows clear early improvement and then a long flat
   plateau where many top trials have nearly identical CV scores.
   The team is considering running far more trials overnight.
   What evidence would you inspect before approving that budget.

<details><summary>Answer</summary>
I would inspect the running-best curve, the spread of the top candidate
scores, and whether a blind holdout or outer-CV estimate has moved in a
meaningful way as search progressed.
If the leading region is flat and the differences are within ordinary
fold variance, more trials may not change the shipping decision.
I would also compare the expected compute cost against the operational
value of the tiny improvement the team hopes to capture.
</details>

## Hands-On Exercise

- [ ] Step 0: Start a fresh notebook or script and import `time`,
  `numpy as np`, `scipy.stats`, `optuna`, `load_breast_cancer`,
  `LogisticRegression`, `GradientBoostingClassifier`,
  `GridSearchCV`, `RandomizedSearchCV`, `cross_val_score`,
  `StratifiedKFold`, `Pipeline`, and `StandardScaler`.
  Also import `enable_halving_search_cv` from
  `sklearn.experimental` and then `HalvingRandomSearchCV` from
  `sklearn.model_selection`.
  Load `X, y = load_breast_cancer(return_X_y=True)` and stand up a base
  pipeline with `StandardScaler()` followed by
  `LogisticRegression(max_iter=3000, solver="saga")`.

- [ ] Step 1: Run `GridSearchCV` over a small logistic-regression space
  such as `C` crossed with `penalty` values that are actually compatible
  with the chosen solver.
  Keep the total combination count small enough that exhaustive search
  is still a reasoned choice.
  Record `best_params_`, `best_score_`, and one sentence on why the
  space was small enough to justify a grid.

- [ ] Step 2: Re-run the same model with `RandomizedSearchCV`, using
  `scipy.stats.loguniform` for `C`.
  Time the search with `time.perf_counter()` and compare the wall-clock
  cost and final `best_score_` against Step 1.
  Write two sentences on whether random search gave you similar quality
  for fewer evaluations.

- [ ] Step 3: Switch to `HalvingRandomSearchCV` using the same base
  classifier and `resource="n_samples"`.
  Compare its runtime and `best_score_` with the earlier searches.
  Note whether the cheaper early rounds seemed to preserve competitive
  candidates or whether the result looked unstable.

- [ ] Step 4: Build an Optuna study over essentially the same logistic
  regression space.
  Use the default sampler so you are explicitly relying on TPE.
  Inside the objective, keep scaling inside the pipeline and use
  `cross_val_score(..., scoring="roc_auc")`.
  Report `study.best_params` and `study.best_value`.

- [ ] Step 5: Add pruning with `MedianPruner` to an iterative
  classifier example.
  One workable pattern is a `GradientBoostingClassifier` with
  `warm_start=True`, increasing `n_estimators` across a short schedule,
  calling `trial.report(value, step)` after each stage, and stopping
  when `trial.should_prune()` returns `True`.
  Write a short note on which trials were pruned and whether the pruning
  rule looked too aggressive or appropriately conservative.

- [ ] Step 6: Demonstrate multi-metric scoring by re-running
  `RandomizedSearchCV` with
  `scoring={"auc": "roc_auc", "ap": "average_precision"}` and
  `refit="auc"`.
  Print both `mean_test_auc` and `mean_test_ap` from `cv_results_` for
  several top candidates.
  Write one sentence on whether the candidate that wins on AUC also
  looks best on average precision.

- [ ] Step 7: Run a deliberate leakage demonstration.
  First, tune `RandomizedSearchCV` on the full dataset and record
  `best_score_`.
  Then estimate the tuned procedure honestly with nested CV by defining
  an outer `StratifiedKFold` and calling
  `cross_val_score(search, X, y, cv=outer, scoring="roc_auc")`.
  Record the outer-CV mean beside the earlier `best_score_`.
  Write a short paragraph naming the bias explicitly:
  `best_score_` is optimistic because the same inner folds both selected
  the hyperparameters and produced the reported score.
  Tie the explanation back to
  [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/).

- [ ] Step 8: Run a stop-condition check with Optuna by comparing
  `n_trials=5` against `n_trials=50` on the same search space.
  Plot the running best if you want, or print the running best after
  each trial.
  Observe whether the later trials discover meaningfully new territory
  or mostly confirm the same top region.

- [ ] Completion check: confirm that scaling lived inside every
  `Pipeline`, not in a single precomputed transform outside CV.

- [ ] Completion check: confirm that the deliberate-leakage step reports
  the nested outer-CV mean alongside `best_score_`, not instead of it.

- [ ] Completion check: write one final shipping recommendation sentence
  stating which method you would default to on a small to medium sklearn
  tabular problem and why.

## Sources

- https://scikit-learn.org/stable/modules/grid_search.html
- https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GridSearchCV.html
- https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.RandomizedSearchCV.html
- https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.HalvingGridSearchCV.html
- https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.HalvingRandomSearchCV.html
- https://scikit-learn.org/stable/modules/cross_validation.html
- https://optuna.readthedocs.io/en/stable/
- https://optuna.readthedocs.io/en/stable/tutorial/index.html
- https://optuna.readthedocs.io/en/stable/reference/pruners.html
- https://optuna.readthedocs.io/en/stable/reference/samplers/index.html
- https://docs.ray.io/en/latest/tune/index.html
- https://docs.ray.io/en/latest/tune/api/schedulers.html
- https://docs.ray.io/en/latest/tune/api/suggestion.html
- https://hyperopt.github.io/hyperopt/
- https://www.jmlr.org/papers/v13/bergstra12a.html
- https://arxiv.org/abs/1603.06560
- https://arxiv.org/abs/1810.05934

## Next Module

Continue to [Module 1.12: Time Series Forecasting](../module-1.12-time-series-forecasting/).
