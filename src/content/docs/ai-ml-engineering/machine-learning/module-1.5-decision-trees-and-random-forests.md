---
title: "Decision Trees & Random Forests"
description: "Learn when single trees outperform linear models, how to regularize them, and how Random Forests reduce variance. You will also learn honest evaluation, out-of-bag estimation, and safer feature-importance analysis."
slug: ai-ml-engineering/machine-learning/module-1.5-decision-trees-and-random-forests
sidebar:
  order: 5
---

> Track: AI/ML Engineering | Complexity: `[MEDIUM]` | Time: 75-90 minutes
> Prerequisites: [Module 1.1: Scikit-learn API & Pipelines](../module-1.1-scikit-learn-api-and-pipelines/), [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/), and [Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/).

## Learning Outcomes

1. **Design**: a decision tree's regularization profile by choosing among `max_depth`,
   `min_samples_split`, `min_samples_leaf`, `min_impurity_decrease`, `max_leaf_nodes`, and
   `ccp_alpha`, given a target bias-variance budget.

2. **Compare**: a single decision tree, a Random Forest, and an Extra-Trees ensemble on variance
   reduction, training cost, prediction smoothness, and the kind of randomization each contributes.

3. **Evaluate**: a Random Forest's generalization both via held-out cross-validation and via the OOB
   estimate, and explain why `oob_score=True` is silently ignored without `bootstrap=True`.

4. **Diagnose**: a misleading `feature_importances_` ranking by re-running with
   `sklearn.inspection.permutation_importance` and explain the impurity-based bias toward
   high-cardinality continuous features.

5. **Decide**: when trees and tree ensembles are the wrong tool for the job, and justify reaching
   for [Module 1.2](../module-1.2-linear-and-logistic-regression-with-regularization/), [Module
   1.6](../module-1.6-xgboost-gradient-boosting/), or the deep-learning track instead.

## Why This Module Matters

A team has a fraud model that already follows the habits from [Module
1.2](../module-1.2-linear-and-logistic-regression-with-regularization/) and [Module
1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/): the split discipline is clean, the
logistic regression is regularized, and the probability outputs are usable. Yet the worst false
negatives keep sharing the same shape. A particular merchant category only becomes risky inside a
certain amount band and during a particular time-of-day window. Nothing is wrong with the linear
model. It is simply using one global surface where the problem contains local interaction pockets.

That is the moment when a tree-based model becomes attractive. A decision tree can carve the feature
space into regions with simple yes-no rules, and a Random Forest can stabilize that idea by
averaging many such trees. The team can keep the leakage-safe evaluation contract from [Module
1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/), and it can keep the preprocessing
contract from [Module 1.4](../module-1.4-feature-engineering-and-preprocessing/), but it does not
need the `StandardScaler` that the logistic regression relied on. Trees do not care about feature
scaling because their split logic depends on order and thresholds, not on distance in a scaled
vector space.

This trade is not free. The scikit-learn tree guide emphasizes both the advantages and the
disadvantages of decision trees: they capture non-linear relationships, interact naturally with
mixed tabular signals after encoding, and are easy to inspect, but they are also unstable and can
grow over-complex trees that do not generalize well. A forest reduces variance, but it still
produces stepwise decision boundaries and a feature-importance story that is easy to misuse if you
treat `feature_importances_` as ground truth instead of as a rough, biased summary ([tree
guide](https://scikit-learn.org/stable/modules/tree.html)).

The practical value of this module is not "trees are better than linear models." The practical value
is knowing when to switch tools, how to regularize that switch, how to evaluate it without leakage,
and how to explain the result without fooling yourself with the wrong importance metric.

## Section 1: Why a Tree When You Already Have a Linear Model

A linear classifier from [Module 1.2](../module-1.2-linear-and-logistic-regression-with-regularization/) learns
one global relationship. If the log-odds of the positive class rise smoothly with a weighted
combination of features, that is excellent news. Linear models are efficient, stable, and often
surprisingly strong. They also behave especially well on high-dimensional sparse text, where each
token feature contributes a small amount to a large global pattern.

A tree solves a different problem. Instead of one global surface, it builds a sequence of local
decisions. "If amount is above this threshold, go left. If merchant type is in this group, go right.
If time falls in this window, split again." That structure means a tree can discover axis-aligned
interactions without hand-built cross terms. You do not need to invent a feature that says "merchant
category times amount band times time bucket." The tree can express the interaction by routing
examples down different branches.

That expressive power is why trees often rescue tabular problems where the useful signal is
conditional. A feature may matter only inside one region of the data. A linear model has to smear
that relationship across the whole sample unless you explicitly add the interaction. A tree can
isolate the region and treat it differently. For many operational datasets, that is the first real
taste of non-linearity without leaving the classical scikit-learn toolbox.

Trees also remove one entire category of preprocessing concern. If you multiply a numeric feature by
a positive constant, the ordering of rows does not change. The candidate split thresholds change
numerically, but the ranked order stays the same. That is why scaling is unnecessary for trees. This
matters in production because the temptation to preserve the exact same preprocessing graph from a
linear baseline can lead to dead weight. If a numeric branch exists only to hold `StandardScaler`
for a tree, it adds latency and configuration surface without adding signal.

Another useful property is robustness to outliers in `X`. A huge value can still matter if it
creates a useful split, but a tree is not fitting a global line that gets pulled by extreme points.
What matters is whether the outlier changes the threshold choices. This is a subtle but important
distinction. In practice, trees often let you spend less energy on monotonic rescaling and more
energy on validating whether the model is isolating sensible regions.

The costs are equally important. A single decision tree is high-variance. The scikit-learn guide
warns that small variations in the data can produce a completely different tree structure. That
means a single tree can look interpretable while actually being brittle. If you retrain on a
slightly different sample, the top split can move, a subtree can disappear, and the narrative you
told yourself about "the model's logic" can collapse.

Tree predictions are also piecewise constant. In classification, that means the estimated class
probabilities change in steps. In regression, that means flat plateaus separated by jumps. If the
problem needs smooth responses or meaningful extrapolation outside the training range, trees are
often the wrong tool. A regressor tree cannot keep extending a trend line beyond what it has seen.
It predicts by region, not by continuation.

Once you understand that trade, the next decision becomes easier. If you need global linear
structure, lean on [Module 1.2](../module-1.2-linear-and-logistic-regression-with-regularization/). If you need
flexible local interactions on tabular data, trees are worth trying. If you need even more
predictive strength on the same style of data, then [Module
1.6](../module-1.6-xgboost-gradient-boosting/) is the forward link, because boosting pushes tree
ensembles in a different direction from bagging.

> **Pause and predict** — If your current logistic regression is
> missing a three-way interaction, would you rather add manual
> cross features or try a shallow tree first? Before reading on,
> decide which choice changes your maintenance burden more over
> time.

One more contrast with linear models matters in practice. Linear models give you coefficients that
can be stable, global, and easy to compare across retrains if the feature space is stable. Decision
trees give you rules that are local, conditional, and sensitive to the training sample. That does
not make trees less useful. It makes the inspection story different. You do not read a tree the way
you read a coefficient table.

For sparse text, the advice flips hard. The tree guide notes that trees can behave poorly on
problems with very many features and limited observations per feature pattern. A bag-of-words or
TF-IDF matrix is exactly that situation. In those problems, the global linear story from [Module
1.2](../module-1.2-linear-and-logistic-regression-with-regularization/) usually wins on both accuracy and
compute. Trees shine on tabular interaction structure, not on every feature matrix that happens to
be numeric.

A useful mental model is this: a linear model asks, "What global direction separates the classes?" A
tree asks, "What sequence of local threshold decisions partitions the examples into purer groups?" A
Random Forest later asks, "What if we average many different answers to that second question?" Those
are related questions, but they are not interchangeable.

## Section 2: Anatomy of a Single CART Tree

A CART tree grows by greedy top-down recursion. At each node, it searches candidate splits and
chooses the one that most improves an impurity criterion. For classification, scikit-learn supports
`gini`, `entropy`, and `log_loss`. In practice, these often lead to similar trees, especially once
you regularize. For regression, the supported criteria include `squared_error`, `friedman_mse`,
`absolute_error`, and `poisson`, which differ in how they evaluate the quality of a split and which
data-generating assumptions they prefer
([DecisionTreeClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeClassifier.html),
[DecisionTreeRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeRegressor.html)).

The algorithm is greedy, not globally optimal. Once a split is chosen near the top of the tree, the
downstream search happens inside the regions that split created. You should picture the tree as
making locally sensible decisions one after another, not as solving one giant optimization problem
over all possible trees. That is why a tree can be both powerful and unstable. A small change in the
sample can change an early split, and that change alters the search space for everything below it.

The scikit-learn user guide is direct about the risk: decision-tree learners can create over-complex
trees that do not generalize the data well. If you let the tree keep splitting until it runs out of
stopping conditions, it can chase idiosyncrasies of the training sample. On a noisy dataset, that
means memorization disguised as interpretability. A leaf that contains one example is easy to
explain and often useless.

To make the mechanics concrete, use a deliberately non-linear toy problem. `make_moons` is small,
noisy, and built to expose where a linear boundary struggles. The code below fits a single
`DecisionTreeClassifier`, reports its test accuracy explicitly, and reads two structural properties
from the learned tree: `max_depth` and `node_count`.

### Worked Example: A Single Tree on a Non-Linear Toy Problem

```python
import numpy as np

from sklearn.datasets import make_moons
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

X, y = make_moons(n_samples=1000, noise=0.25, random_state=0)

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    stratify=y,
    random_state=0,
)

tree = DecisionTreeClassifier(
    criterion="gini",
    max_depth=4,
    min_samples_leaf=10,
    random_state=0,
)

tree.fit(X_train, y_train)

test_accuracy = tree.score(X_test, y_test)
print("test accuracy:", test_accuracy)
print("max depth:", tree.tree_.max_depth)
print("node count:", tree.tree_.node_count)
```

The important line is `tree.score(X_test, y_test)`. For a classifier, `score()` returns mean
accuracy on the provided data. It does not return AUC. It does not return calibration quality. It
does not return "overall performance." The semantics are simple and narrow. If later in the module
you care about ROC AUC, compute ROC AUC explicitly, the same way [Module
1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/) taught you to compute metrics
intentionally rather than by habit.

What does the tree learn here? Conceptually, it is drawing alternating rectangles around regions of
the moon-shaped classes. A shallow tree cannot trace the whole curve smoothly, but it can
approximate the structure with a handful of cuts. That is already enough to demonstrate why local
thresholding can beat a single global line on the right kind of problem.

A tree is easier to understand if you picture the recursive split structure directly:

```text
root
|-- x2 <= 0.18
|   |-- x1 <= -0.62 : class 0
|   |-- x1 >  -0.62
|   |   |-- x2 <= -0.41 : class 1
|   |   |-- x2 >  -0.41 : class 0
|-- x2 >  0.18
    |-- x1 <= 1.12 : class 1
    |-- x1 >  1.12 : class 0
```

That sketch is not the exact learned tree. It is a cartoon of what CART does: it alternates
features, applies thresholds, and routes examples until each leaf has a simpler class distribution
than the parent node had. Once you see it this way, a lot of later tuning advice becomes intuitive.
Every regularization knob is really a way to constrain how eagerly the tree keeps carving the space.

Classification and regression differ only in the target summary at the leaves and in the split
criterion. A classifier leaf stores a class distribution and predicts the majority class or the
class probabilities implied by that leaf. A regressor leaf stores a numeric summary, such as the
mean target under `squared_error`. The partitioning logic is the same. That shared structure is why
a large fraction of the practical advice in this module applies to both settings.

The danger of a single tree is not that it cannot fit a complex pattern. The danger is that it can
fit too much complexity too cheaply. A few extra levels of depth can turn a reasonable rule set into
a tree that memorizes isolated pockets of noise. That is why you should think of an unconstrained
tree as a diagnostic object or a high-variance baseline, not as the final answer on most real
tabular tasks.

If you want to visualize a fitted tree for a tiny example, the scikit-learn example gallery includes
a small iris classifier visualization
([plot_iris_dtc](https://scikit-learn.org/stable/auto_examples/tree/plot_iris_dtc.html)). The lesson
to carry forward is not the exact picture. The lesson is that every additional branch is a variance
choice.

> **Pause and reflect** — Suppose a tree gets one top-level split
> wrong because the training sample is slightly different. Which
> parts of the later structure stay safe, and which parts get
> rebuilt from scratch? If you answered "nearly everything below
> that node is now different," you are already thinking in the
> right variance language.

## Section 3: Tree Regularization Knobs

Tree regularization is about controlling how many regions the model is allowed to create, how small
those regions may become, and how much impurity reduction a split must earn before the tree accepts
it. Unlike linear models, you are not shrinking coefficients toward zero. You are limiting partition
complexity. That means the best knob depends on what kind of overfitting you fear.

The common controls fall into two families. Pre-pruning stops growth early. Post-pruning lets the
tree grow and then cuts back subtrees that do not justify their complexity. Scikit-learn supports
both styles. `max_depth`, `min_samples_split`, `min_samples_leaf`, `min_impurity_decrease`, and
`max_leaf_nodes` are all pre-pruning controls. `ccp_alpha` is the post-pruning control based on
cost-complexity pruning.

Here is a practical decision table you can use when choosing the first knob to touch:

```text
+-------------------------+-------------------------------------------+----------------------------------------------+
| Knob                    | What it directly limits                   | When it is a strong first move               |
+-------------------------+-------------------------------------------+----------------------------------------------+
| max_depth               | Number of sequential decisions            | Tree keeps growing obvious twiggy branches   |
| min_samples_split       | Small parent nodes from splitting         | You want to block late micro-splits          |
| min_samples_leaf        | Tiny leaves                               | Leaves become one-row stories on noisy data  |
| min_impurity_decrease   | Split must earn minimum gain              | You want thresholding in impurity units      |
| max_leaf_nodes          | Total terminal regions                    | You want a hard budget on rule count         |
| ccp_alpha               | Post-prune weak subtrees                  | You want to grow first, simplify after       |
+-------------------------+-------------------------------------------+----------------------------------------------+
```

`max_depth` is the easiest knob to reason about. If a path can only contain a small number of
decisions, the tree cannot keep drilling into narrow pockets. This often works well as an early
guardrail, especially on tabular datasets where you want some interactions but not a combinatorial
explosion of them. The downside is that depth treats all levels equally. It can block useful
refinement in one branch because a different branch already spent the depth budget.

`min_samples_split` works one level earlier. It says a node must contain at least this many examples
before the algorithm is even allowed to consider splitting it. This prevents the tree from wasting
time splitting tiny parents. It is helpful, but it does not guarantee that the resulting leaves are
large, because a split from a sufficiently large parent can still create a tiny child.

`min_samples_leaf` is often the more interpretable safety rail. Every terminal region must contain
at least that many training examples. On noisy data, this is one of the cleanest ways to stop the
tree from giving each oddball pattern its own leaf. If you are used to linear regularization, think
of this as a minimum evidence requirement for each local rule. The model is not forbidden from
creating a region. It is forbidden from creating a region that is supported by almost no data.

> **Pause and predict** — What happens when `min_samples_leaf=1`
> on a noisy dataset with several weak predictors? Before reading
> the answer, say it plainly: the tree is allowed to keep carving
> until a leaf can describe one row at a time.

`min_impurity_decrease` is useful when you want to phrase the rule in terms of earned gain. A split
must reduce impurity by at least the specified amount. This can feel more principled than a raw
depth cap, but it is also more abstract because the meaning of the threshold depends on the
criterion and the data distribution. In a production tuning loop, it is usually not the first knob
people reach for, but it is a good one to know when depth and leaf-size controls still allow too
much fragmentation.

`max_leaf_nodes` gives you a hard budget on how many terminal regions the tree may end up with. That
can be attractive when the goal is bounded interpretability. If an analyst must read the tree or if
you need to cap the number of downstream business rules that people will inspect, leaf count is a
more honest complexity budget than depth alone. Two trees of the same depth can have very different
total rule counts.

Then there is `ccp_alpha`, the post-pruning lever. Cost-complexity pruning grows the tree, computes
candidate pruned subtrees, and then removes branches that do not justify their complexity.
Scikit-learn's tree guide summarizes the stopping condition by stating that the pruning process
stops when the pruned tree's minimal `alpha_eff` is greater than the `ccp_alpha` parameter ([tree
guide](https://scikit-learn.org/stable/modules/tree.html)). The practical reading is simple: larger
`ccp_alpha` means stronger pressure toward a smaller tree.

Post-pruning is useful because greedy growth can be locally right and globally too enthusiastic. By
growing first, you allow the tree to discover candidate structure. By pruning after, you ask whether
the extra branches still earn their keep. This is often cleaner than trying to guess the perfect
`max_depth` in advance. The trade is computational and conceptual: now you are managing a second
stage rather than one direct stopping rule.

A healthy default tuning order for a single tree is: `min_samples_leaf` first, then `max_depth`,
then possibly `ccp_alpha` if you want a more deliberate simplification pass. That order is not a
law. It is a robust starting pattern because tiny leaves are such a common source of tree
overfitting.

You should also distinguish the needs of a standalone tree from the needs of a forest. A single tree
often needs stronger direct regularization because there is no averaging stage waiting later to
reduce variance. In a Random Forest, each individual tree can be deeper than you might tolerate
alone, because the ensemble is going to average across many bootstrap-resampled and
feature-resampled versions of that high-variance learner.

A final practical warning: if you inspect a tree and like its top few decisions, do not assume the
rest of the structure is equally trustworthy. Shallow splits tend to be supported by more examples.
Deep splits often reflect thinner evidence. Regularization is not only about test performance. It is
also about how much of the tree you are willing to interpret as signal rather than as sampling
noise.

## Section 4: Bagging and Random Forests

A single tree is expressive and unstable. Bagging is the classic response to that combination. The
idea is simple: fit many trees on bootstrap-resampled versions of the training set, then aggregate
their predictions. For classification, aggregate by majority vote or by averaging class
probabilities. For regression, average the numeric outputs. Bagging works best when the base learner
has high variance, which is exactly the problem a single tree has.

Random Forests add a second source of randomness beyond the bootstrap sample. At each split, the
algorithm considers only a subset of features rather than the full feature set. This matters because
strong predictors otherwise tend to dominate many trees in the same way. Feature subsampling
decorrelates the trees. Once the trees make more different errors, averaging them reduces variance
more effectively ([ensemble guide](https://scikit-learn.org/stable/modules/ensemble.html)).

Scikit-learn's Random Forest defaults reflect the difference between classification and regression.
For classification, `max_features="sqrt"` is the default. For regression, `max_features=1.0` means
all features are considered at each split unless you change it
([RandomForestClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html),
[RandomForestRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html)).
That default difference already tells you something about the expected bias-variance trade.
Classification forests usually gain a lot from decorrelation through feature subsampling. Regression
forests often tolerate using more features per split.

A forest does not magically make trees smooth. It averages step functions, so the result is still
piecewise. But averaging many different step functions is much less jagged than trusting one tree
that happened to see one sample. This is the heart of the variance-reduction story. Forests let you
keep local interaction structure while reducing the sensitivity of any single branch decision.

Here is a compact comparison that captures the family:

```text
+--------------------+------------------------+-------------------------------+------------------------------+
| Model              | Randomness source      | Main benefit                  | Main cost                    |
+--------------------+------------------------+-------------------------------+------------------------------+
| Decision Tree      | None beyond sample     | Maximum local flexibility     | High variance                |
| BaggingClassifier  | Bootstrap rows         | Variance reduction            | More compute, no decorrelate |
| Random Forest      | Rows + feature subset  | Stronger variance reduction   | More hyperparameters         |
| Extra Trees        | Rows + random split    | Faster, often lower variance  | Higher bias                  |
+--------------------+------------------------+-------------------------------+------------------------------+
```

Extra Trees deserve a brief mention here because the comparison sharpens your intuition. A Random
Forest searches for the best threshold among candidate features. Extra Trees randomize one step
further by choosing random thresholds and keeping the best among those random proposals. That
usually increases bias a bit, often lowers variance, and can reduce training cost. You are not
required to use Extra Trees often. You are required to know what kind of randomness they add.

### Scaling Callout: Trees Do Not Need Feature Scaling

This is the tree equivalent of the `C` or `alpha` callout from the linear-model world. In [Module
1.4](../module-1.4-feature-engineering-and-preprocessing/), the Common Mistakes section already
flagged `StandardScaler` before a tree as a no-op. The reason is structural, not just empirical.
Tree splits depend on order and thresholds. If you rescale a feature monotonically, the rank
ordering of examples is unchanged, so the same partition can be represented by different numeric
threshold values.

That means a `StandardScaler` before a `RandomForestClassifier` is not harmless elegance. It is
needless latency, needless config, and one more artifact for someone to keep consistent between
training and serving. Keep the preprocessing contract from [Module
1.1](../module-1.1-scikit-learn-api-and-pipelines/) and [Module
1.4](../module-1.4-feature-engineering-and-preprocessing/), but drop the scaler unless it exists for
some other branch in a shared model comparison pipeline.

A careful way to say this is: trees still need valid numeric input, and categorical features still
need the encoding strategy from [Module 1.4](../module-1.4-feature-engineering-and-preprocessing/).
What they do not need is scale normalization of numeric columns.

### Worked Example: Single Tree vs Random Forest

```python
from sklearn.datasets import make_moons
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

X, y = make_moons(n_samples=1200, noise=0.30, random_state=0)

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    stratify=y,
    random_state=0,
)

single_tree = DecisionTreeClassifier(
    max_depth=None,
    min_samples_leaf=1,
    random_state=0,
)

forest = RandomForestClassifier(
    n_estimators=200,
    max_features="sqrt",
    random_state=0,
)

single_tree.fit(X_train, y_train)
forest.fit(X_train, y_train)

print("single-tree test accuracy:", single_tree.score(X_test, y_test))
print("forest test accuracy:", forest.score(X_test, y_test))
```

Do not stare at this example for a magic number. Stare at it for a story. The unconstrained tree is
free to chase local quirks of the training sample. The forest averages many trees trained on
slightly different data and slightly different feature subsets. On repeated resamples, the
single-tree result will swing more. The forest will usually be steadier. That steadiness is the real
product you are buying.

Bagging is not always worth it. If the base learner already has low variance, averaging many
versions of it may buy little. That is why bagging a heavily regularized linear model is rarely the
first idea people reach for. The payoff comes when the base learner changes a lot under small data
perturbations. Trees fit that profile almost perfectly.

There is also a compute story. A forest with many trees is more expensive to train and serve than a
single tree, but the work is embarrassingly parallel and the tuning surface is usually simpler than
the one you face with boosted trees. That is one reason Random Forests remain such a strong baseline
for tabular problems: they often deliver robust performance without forcing you into a fragile
optimization setup.

> **Pause and predict** — If two features are both extremely
> strong, what happens if every tree sees all features at every
> split? Now ask the same question if each split only sees a random
> subset. Which setting is more likely to create diverse trees that
> help the ensemble average away variance?

## Section 5: OOB Error and Honest RF Evaluation

Out-of-bag estimation is one of the most practical conveniences of Random Forests. Because each tree
trains on a bootstrap sample, some rows are absent from that tree's training set. A row has
probability `(1 - 1/N)^N` of being left out of one bootstrap sample, which tends toward `1/e` as `N`
grows. That means a row is included in about `63.2%` of trees and is out-of-bag for about `36.8%` of
them. The forest can aggregate predictions for that row using only the trees that did not train on
it ([ensemble guide](https://scikit-learn.org/stable/modules/ensemble.html)).

This is useful because it gives you a built-in validation surface without a separate held-out split
for the OOB calculation itself. But do not over-read the convenience. The scikit-learn ensemble
guide notes that OOB estimates are usually very pessimistic and that cross-validation is preferred
when feasible. That sentence is the one you should remember when someone tries to use OOB as a full
replacement for the disciplined evaluation contract from [Module
1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/).

The API also contains a footgun that is easy to miss. `oob_score=True` requires `bootstrap=True`. If
bootstrap sampling is off, the OOB flag is silently irrelevant because there are no out-of-bag rows
by construction. If you copy an estimator config from somewhere else, always verify that those flags
are paired.

Here is a minimal, explicit evaluation pattern. It fits a forest with OOB enabled, reports
`oob_score_`, then computes held-out test accuracy and held-out ROC AUC directly.

```python
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

X, y = make_classification(
    n_samples=1500,
    n_features=12,
    n_informative=5,
    n_redundant=2,
    random_state=0,
)

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    stratify=y,
    random_state=0,
)

forest = RandomForestClassifier(
    n_estimators=200,
    bootstrap=True,
    oob_score=True,
    random_state=0,
)

forest.fit(X_train, y_train)

test_accuracy = forest.score(X_test, y_test)
test_auc = roc_auc_score(y_test, forest.predict_proba(X_test)[:, 1])

print("oob score:", forest.oob_score_)
print("test accuracy:", test_accuracy)
print("test roc auc:", test_auc)
```

Notice the metric discipline. `forest.score(X_test, y_test)` is test accuracy because this is a
classifier. ROC AUC is computed explicitly with `roc_auc_score(y_test,
forest.predict_proba(X_test)[:, 1])`. That line is not just syntactic detail. It protects you from
the common reporting error where someone writes down one metric name while the code actually
computed another.

OOB is most helpful during model development. It is cheap enough to let you see whether more trees
are still helping, whether a very aggressive `max_features` choice is hurting, or whether the forest
is grossly overfitting. But once you begin comparing model families or reporting final results, go
back to the discipline from [Module 1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/):
frozen train-validation-test roles, no leakage, explicit metrics, and a final untouched test
evaluation.

Another subtle point is that OOB predictions are not based on the same number of trees for every
row. Some rows are OOB for more trees than others. On larger forests this usually washes out well
enough, but it is another reason OOB should feel like an internal development instrument rather than
a universal scoreboard.

When you compare OOB with cross-validation, do not ask whether they match exactly. Ask whether they
tell the same operational story. If OOB says the model improved when you doubled `n_estimators`, and
cross-validation says the same, you have a stable signal. If OOB and cross-validation disagree
sharply, trust the cleaner external evaluation and investigate whether the data, class balance, or
folding pattern is making OOB less representative.

> **Pause and reflect** — If the only evidence for a new forest
> configuration is a slightly better `oob_score_`, is that enough
> to ship? Answer from the discipline of
> [Module 1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/),
> not from the convenience of one extra attribute.

## Section 6: Feature Importance — Two Methods, Two Failure Modes

Feature importance is where tree ensembles often tempt people into overconfidence. The seductive
part is that Random Forests expose `feature_importances_` immediately after fitting. The dangerous
part is that the resulting ranking looks more definitive than it really is. The scikit-learn
ensemble documentation calls out two important weaknesses of impurity-based importances: they are
computed from training-set statistics, and they favor high-cardinality features
([plot_forest_importances](https://scikit-learn.org/stable/auto_examples/ensemble/plot_forest_importances.html),
[ensemble guide](https://scikit-learn.org/stable/modules/ensemble.html)).

Impurity-based importance is cheap because the forest already knows how much each split reduced
impurity during training. Summing those reductions over trees gives you a built-in importance
summary. That makes it useful as a quick model-debugging glance. It does not make it safe for
consequential decisions, such as dropping a column, making a policy argument, or telling
stakeholders that one field is "the reason" the model works.

High-cardinality bias is the classic trap. A continuous feature, or a feature with many unique
values, offers many possible thresholds. That sheer flexibility lets it earn impurity reductions
even when its signal is weak or absent. A unique row identifier is the cartoon version of the
problem. It can create very pure splits simply because it offers almost unlimited partition choices.
The forest can then rank it surprisingly high even though it has no causal or repeatable value.

Permutation importance addresses that flaw differently. Instead of asking, "How much impurity
reduction did this feature help create during training?" it asks, "How much does predictive
performance on a validation set fall if I randomly shuffle this feature?" That approach is far
closer to the question you usually care about when acting on importance. It also decouples the
estimate from the training impurity bookkeeping and therefore avoids the high-cardinality preference
built into impurity importance ([permutation importance
guide](https://scikit-learn.org/stable/modules/permutation_importance.html), [permutation_importance
API](https://scikit-learn.org/stable/modules/generated/sklearn.inspection.permutation_importance.html)).

But permutation importance has its own failure mode. When features are strongly correlated,
permuting one at a time can understate the importance of all of them. The model can often
reconstruct the signal from the correlated partners that were left intact. The scikit-learn
multicollinearity example demonstrates this clearly: a model can perform well while one-at-a-time
permutation importance suggests that no single correlated feature matters very much ([multicollinear
example](https://scikit-learn.org/stable/auto_examples/inspection/plot_permutation_importance_multicollinear.html)).

The correct operational rule is not "always trust permutation importance." The correct rule is:
prefer permutation importance when the ranking will influence a decision, and if correlated features
are present, inspect groups or clusters rather than treating each column as an isolated unit.

### Worked Example: A Signal Feature and a Fake Row Identifier

```python
import numpy as np

from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split

X, y = make_classification(
    n_samples=1200,
    n_features=1,
    n_informative=1,
    n_redundant=0,
    n_repeated=0,
    n_clusters_per_class=1,
    class_sep=1.0,
    random_state=0,
)

row_id = np.arange(X.shape[0]).reshape(-1, 1)
X_augmented = np.hstack([X, row_id])
feature_names = ["signal", "row_id"]

X_train, X_test, y_train, y_test = train_test_split(
    X_augmented,
    y,
    test_size=0.25,
    stratify=y,
    random_state=0,
)

forest = RandomForestClassifier(
    n_estimators=200,
    random_state=0,
)

forest.fit(X_train, y_train)

impurity_importance = forest.feature_importances_
permutation = permutation_importance(
    forest,
    X_test,
    y_test,
    n_repeats=10,
    random_state=0,
)

for name, value in zip(feature_names, impurity_importance):
    print("impurity", name, value)

for name, value in zip(feature_names, permutation.importances_mean):
    print("permutation", name, value)
```

Do not promise exact printed values from this script. The point is the ranking pattern. The
impurity-based score can give the unique identifier too much credit because it creates many
splitting opportunities. The permutation score usually reveals the truth more honestly on held-out
data: shuffling the real signal hurts, while shuffling the row identifier should do little.

This difference matters most when you are about to act. If a team wants to prune fields, reduce
collection burden, or explain model behavior to another function, use permutation importance on a
proper validation or test surface. Treat impurity importance as an internal debugging clue, not as
evidence strong enough to drive policy.

There is a second nuance worth carrying forward. Importance is not the same as usefulness in the
presence of substitutes. A feature can be genuinely informative and still receive low permutation
importance if another feature can stand in for it. That is why domain grouping and correlation
inspection belong beside the importance calculation, not after it as an afterthought.

A simple safety pattern is:

```text
1. Fit the forest inside the leakage-safe pipeline.
2. Check impurity importance only as a rough debugging view.
3. Compute permutation importance on held-out data.
4. If correlated features exist, group or cluster them first.
5. Make decisions only after the grouped picture is clear.
```

That workflow is slower than reading one attribute and moving on. It is also the workflow that keeps
you from being fooled by the forest's most convenient explanation surface.

## Section 7: Hyperparameter Tuning Playbook for Random Forests

Random Forest tuning is usually less fragile than boosted-tree tuning, but that does not mean "turn
on a forest and walk away." A useful playbook focuses on the small set of knobs that actually move
the bias-variance trade in meaningful ways.

Start with `n_estimators`. More trees usually help until the ensemble performance plateaus. Each
added tree reduces variance a bit more by averaging another independent or partially independent
high-variance learner. The gain eventually flattens because the ensemble has already stabilized
around its available signal. This is why "how many trees?" should be answered empirically with OOB
or cross-validation curves, not by cargo-culting the number from an example notebook.

A good development range is often `100` to `300` trees for an initial sweep, with more added only if
the curve is still moving. That is not a universal optimum. It is a sane starting window that
usually reveals whether you are near the plateau. Once the curve flattens, extra trees mostly buy
compute cost.

The next knobs to tune are usually `max_depth` and `min_samples_leaf`. These are your variance
controls. Deeper trees and tiny leaves let each estimator chase more sample-specific structure.
Shallower trees and larger leaves bias the forest more but often create a better bias-variance
balance overall. Because the ensemble already reduces variance by averaging, the best forest often
uses trees that are reasonably expressive but not wildly unconstrained for the data regime.

`max_features` is the most forest-specific tuning knob because it controls split-level feature
subsampling. Smaller values usually increase tree diversity and therefore variance reduction, but
they also increase bias because each split is choosing from a narrower menu. The scikit-learn guide
also notes an important compute trade: smaller `max_features` can significantly decrease runtime.
That means `max_features` affects not just model quality but also how expensive the search will be
([ensemble guide](https://scikit-learn.org/stable/modules/ensemble.html)).

A practical summary looks like this:

```text
+-------------------+-------------------------------+---------------------------------------------+
| Hyperparameter    | Main effect                   | Typical question to ask                     |
+-------------------+-------------------------------+---------------------------------------------+
| n_estimators      | More averaging                | Has the OOB or CV curve plateaued yet?      |
| max_depth         | More or fewer branch levels   | Are trees memorizing local noise pockets?   |
| min_samples_leaf  | Larger or smaller leaves      | Are leaves too thin to trust?               |
| max_features      | More or less decorrelation    | Do I want more diversity or less bias?      |
| criterion         | Split scoring detail          | Is this materially moving RF quality?       |
+-------------------+-------------------------------+---------------------------------------------+
```

Notice what is missing from the center of the playbook: `criterion` is rarely the first or second
thing to tune in a Random Forest. The choice matters less than tree count, feature subsampling, and
the variance controls. If you are spending a lot of search budget on criterion before understanding
the plateau in `n_estimators`, you are probably tuning the wrong lever first.

You can use OOB as a cheap first pass to map the tree-count curve. Then use cross-validation,
following the discipline from [Module 1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/), for
the more consequential comparisons. This gives you a sensible division of labor: OOB for quick
internal direction, CV for robust selection, and the test set for the final untouched estimate.

Extra Trees fit naturally into this playbook as a sibling model family to try once a Random Forest
baseline is stable. If your forest is strong but expensive, or if you suspect more randomization
could help reduce variance further, `ExtraTreesClassifier` is a reasonable comparison point
([ExtraTreesClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.ExtraTreesClassifier.html)).
Do not treat it as a mandatory step. Treat it as a nearby branch in the same family.

If you need a deeper search strategy, move forward to the upcoming Hyperparameter Optimization
module (1.11). This module's job is to teach the shape of the tuning landscape, not to re-teach
systematic HPO. The forest lesson is that a small number of
well-chosen sweeps can already get you most of the way to a trustworthy baseline.

> **Pause and predict** — If you reduce `max_features`, what two
> things change at once? Answer both before continuing: tree
> diversity goes up, and per-tree split quality may go down. That
> is the forest's core bias-variance trade in one line.

One last tuning discipline matters in real teams. If a forest beats a linear baseline by only a
small margin but costs much more to train, explain, and serve, do not automatically prefer the
forest. Model selection is not a beauty contest. It is an engineering decision under deployment
constraints. The best model is the one whose gain survives contact with compute budgets, monitoring,
and stakeholder comprehension.

## Section 8: Where Trees Are the Wrong Tool

Tree enthusiasm becomes expensive when it turns into reflex. There are several problem types where
trees are simply not the first tool you should reach for.

The clearest example is high-dimensional sparse text. Bag-of-words and TF-IDF matrices create huge
feature spaces where each example activates a tiny subset of features. Linear models thrive here
because they pool weak evidence globally across many sparse dimensions. Trees struggle because they
try to partition on local threshold rules in a space that is mostly zeros. If your data looks like
text classification, return to [Module 1.2](../module-1.2-linear-and-logistic-regression-with-regularization/).

Problems with strong global linear structure are another place to resist the tree impulse. If the
signal is well described by a smooth weighted sum, a tree can still fit it, but it will do so by
approximating the line with a stack of local step regions. That is a more complicated representation
of a simpler truth. In such a case, the forest may win a narrow benchmark and still lose the
engineering argument on simplicity, calibration, and interpretive stability.

Smooth probability outputs are a third warning sign. Forests can produce class probabilities, but
they are averages of leaf-based class proportions, which makes them stepwise and sometimes awkward
for downstream ranking or thresholding workflows. If your product needs especially smooth score
behavior, a calibrated linear model from [Module
1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/) or a boosted-tree approach from [Module
1.6](../module-1.6-xgboost-gradient-boosting/) is often a better next step.

Sequence and image problems belong in a different toolbox. Trees do not encode locality, order, or
hierarchical feature extraction the way deep models do. You can always flatten a structured input
into columns and feed it to a forest. The question is whether that representation respects the
problem. Usually it does not. When the signal depends on spatial or temporal structure, move to the
deep-learning track rather than forcing a tabular model to play a different game.

Regression extrapolation is another quiet failure mode worth remembering. A tree regressor cannot
continue a trend beyond the training support in the way a linear model can. It averages target
values within learned regions. If future inputs are expected to move outside the historical range
and that continuation matters, trees are an awkward fit.

The discipline to carry out of this module is not "use trees on tabular data." It is "recognize when
local threshold interactions are the actual problem structure." When that structure is present,
trees and forests are excellent tools. When it is absent, they can turn a simple modeling task into
a more complex one with no real gain.

## Did You Know?

1. The scikit-learn tree user guide warns that decision-tree learners can create biased trees if
   some classes dominate, and it recommends balancing the dataset before fitting when class
   imbalance would otherwise distort the learned structure. Source:
   https://scikit-learn.org/stable/modules/tree.html

2. The probability that a row is left out of a bootstrap sample tends to `(1 - 1/N)^N -> 1/e`, which
   is why each row is out-of-bag for about `36.8%` of trees and can receive a free validation-style
   prediction from the remaining ensemble. Source:
   https://scikit-learn.org/stable/modules/ensemble.html

3. Extra Trees randomize split thresholds one step further than a Random Forest. Instead of
   searching for the best threshold for each candidate feature, they draw random thresholds and then
   keep the best among those random proposals. That usually trades a bit more bias for lower
   variance and faster fitting. Source: https://scikit-learn.org/stable/modules/ensemble.html

4. The scikit-learn ensemble documentation states explicitly that impurity-based importances favor
   high-cardinality features, and the multicollinear permutation-importance example shows that even
   permutation importance can fail when several features carry the same signal unless you treat them
   as a group. Source: https://scikit-learn.org/stable/modules/ensemble.html Source:
   https://scikit-learn.org/stable/auto_examples/inspection/plot_permutation_importance_multicollinear.html

## Common Mistakes

| Mistake | Why it's wrong | Safer pattern |
|---|---|---|
| `StandardScaler` before a tree ensemble | Tree splits depend on ordering and thresholds, so scaling is a no-op that adds latency and pipeline surface area. | Keep encoding from [Module 1.4](../module-1.4-feature-engineering-and-preprocessing/), but remove numeric scaling for the tree branch. |
| `oob_score=True` without `bootstrap=True` | OOB only exists when rows are omitted from bootstrap samples. Without bootstrap, the flag is functionally ignored. | Always pair `oob_score=True` with `bootstrap=True`. |
| Reading `feature_importances_` and acting on it directly | Impurity importance is biased toward high-cardinality features and is computed from training-time impurity reductions. | Use `permutation_importance` on held-out data before making decisions. |
| Trusting permutation importance with correlated features | One-at-a-time shuffling can make all correlated features look weak because the others still carry the signal. | Cluster or group correlated features and permute the group. |
| Reporting `Pipeline.score()` and calling it AUC | For classifiers, `score()` returns mean accuracy. For regressors, it returns `R^2`. | Compute ROC AUC explicitly with `roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])`. |
| Leaving `min_samples_leaf=1` on noisy data | The tree is free to create leaves that describe one row at a time, which is a classic overfitting path. | Raise `min_samples_leaf` or use `ccp_alpha` to prune back weak twigs. |
| Setting `n_estimators=10` because an example used it | Too few trees can leave the ensemble noisy and unstable. Example counts are not tuning guidance. | Start with a wider sweep such as `100` to `300`, monitor OOB or CV, and stop at the plateau. |

## Quiz

### 1. A fraud team's logistic regression is well-regularized, but the worst misses all share the same interaction pattern.

The team can describe the pattern in plain language: a certain merchant type becomes risky only in a
specific amount band and only during a narrow time window. They are debating whether to add manual
interaction features to the logistic regression or to try a tree-based model. What should they think
about before choosing?

<details><summary>Answer</summary>

A tree-based model is a natural candidate because the useful signal is local and interaction-heavy.
A decision tree can represent the pattern directly with conditional thresholds, and a Random Forest
can stabilize that idea by averaging many trees. The team should still keep the evaluation
discipline from [Module 1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/) and the
preprocessing contract from [Module 1.4](../module-1.4-feature-engineering-and-preprocessing/), but
it can drop `StandardScaler` for the tree branch because trees do not need scaling.

That does not mean the tree automatically wins. Manual interaction features preserve the linear
model's global simplicity and often give smoother, more stable probabilities. The right choice
depends on whether the team wants to keep engineering interaction terms by hand or wants the model
family itself to discover local rule structure. The main conceptual test is whether the problem is
really about global linear evidence or about conditional pockets that a global surface cannot
express cleanly.

</details>

### 2. You fit an unconstrained `DecisionTreeClassifier` and the training score is perfect, but the validation score is disappointing.

A teammate says this is good news because the tree has "learned the data exactly." What diagnosis
would you offer, and which knobs would you reach for first?

<details><summary>Answer</summary>

The likely diagnosis is overfitting driven by a high-variance base learner. A tree that is free to
keep splitting can memorize narrow idiosyncrasies of the training sample, especially when
`min_samples_leaf=1` and `max_depth=None`. Perfect training accuracy is not the achievement here. It
is the warning sign that the tree may have grown more complex than the data can support.

The first knobs I would reach for are `min_samples_leaf` and `max_depth`, because they directly
control leaf thinness and branch length. If I wanted a grow-first-simplify-later workflow, I would
also consider `ccp_alpha` for post-pruning. The goal is not to make the tree small for aesthetic
reasons. The goal is to force each local rule to be supported by enough data that it can generalize
to new examples.

</details>

### 3. A Random Forest pipeline still includes the exact same numeric preprocessing branch that was used for logistic regression.

That branch contains `StandardScaler`, and nobody has removed it because "it does not hurt." Should
you leave it there?

<details><summary>Answer</summary>

For a pure tree branch, `StandardScaler` is unnecessary and should be removed. Tree splits depend on
rank order and thresholding, not on Euclidean geometry or coefficient optimization. A monotonic
rescaling of a numeric feature changes the numeric threshold values but does not change which
partition is possible. So the scaler is not contributing predictive value.

Leaving it in does have costs. It adds latency, another fitted artifact, and more configuration that
can drift between training and serving. The safer pattern is to keep the encoding logic that
converts categorical features into usable numeric columns, as in [Module
1.4](../module-1.4-feature-engineering-and-preprocessing/), but remove numeric scaling from the
forest path.

</details>

### 4. An engineer enables `oob_score=True` on a forest configuration but also sets `bootstrap=False`.

The resulting experiment table shows no useful OOB signal. What is the underlying issue?

<details><summary>Answer</summary>

OOB estimation requires bootstrap sampling. Each row must be absent from some trees' training sets
so that those trees can provide out-of-bag predictions for that row. With `bootstrap=False`, every
tree trains on the full training set, so there is no out-of-bag surface to compute. In practical
terms, `oob_score=True` is not meaningful in that configuration.

The fix is simple and explicit: if you want OOB, pair `oob_score=True` with `bootstrap=True`. Even
then, you should treat OOB as a development aid rather than as a full substitute for
cross-validation. The stronger evaluation story still comes from the split discipline in [Module
1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/).

</details>

### 5. A product manager wants to drop several fields because their impurity-based importance values are low.

The model is a Random Forest, and the team has not run any other importance method. Is that enough
evidence to remove the fields?

<details><summary>Answer</summary>

No. `feature_importances_` is a quick internal summary, not a safe decision surface by itself.
Impurity-based importance is biased toward high-cardinality features and is derived from
training-time split reductions. Low impurity importance can also be misleading if features are
correlated or if one feature is only useful in a limited region of the space.

A safer workflow is to compute permutation importance on held-out data and then inspect whether any
low-ranked features are acting as substitutes inside correlated groups. If the team is going to drop
fields, that decision should come from a held-out performance story and a correlation-aware
importance analysis, not from one training attribute that happens to be easy to print.

</details>

### 6. Your permutation-importance plot shows that none of a cluster of similar operational metrics looks important, yet the forest performs well.

A teammate concludes that the entire metric family is irrelevant. What alternative explanation
should you consider?

<details><summary>Answer</summary>

Strong feature correlation is the first alternative explanation. When permutation importance
shuffles one feature at a time, the model may still recover the same signal from the other
correlated features that remain intact. The result is that each feature looks individually
unimportant even though the group is collectively essential.

The right response is to inspect the correlation structure and evaluate grouped or clustered
permutations rather than deleting the whole family. The scikit-learn multicollinearity example makes
this exact point: one-at-a-time permutation can understate importance when features are redundant
substitutes. So the absence of a large single-feature drop is not proof that the signal is absent.

</details>

### 7. A teammate proposes replacing a strong sparse-text logistic baseline with a Random Forest because "forests capture nonlinearities."

The feature matrix is a large TF-IDF representation. How would you respond?

<details><summary>Answer</summary>

I would push back and ask whether the problem structure actually matches what trees are good at.
Sparse text classification is usually one of the best settings for linear models because the signal
is spread across many dimensions and each example activates a tiny subset of them. Trees are not
naturally efficient or stable in that regime. They try to partition locally in a space that is
mostly zeros, which is usually a poor match.

The fact that forests capture nonlinearities is true but not sufficient. You do not pay for
nonlinearity just because it exists in the abstract. You pay for it because the data needs local
interaction partitions. For sparse text, the safer default is to stay with the linear baseline from
[Module 1.2](../module-1.2-linear-and-logistic-regression-with-regularization/) unless a strong validation story
proves otherwise.

</details>

### 8. A forest slightly outperforms your linear baseline on accuracy, but the downstream system cares about stable probability ranking and clean threshold control.

Should the forest win automatically?

<details><summary>Answer</summary>

No. A small accuracy improvement does not automatically outweigh the cost of rougher probability
behavior, heavier serving, and a more fragile explanation surface. Random Forest probabilities are
averages of leaf-level class proportions, so they can be stepwise and less smooth than what a
well-behaved linear model or a later calibrated boosting model can provide.

The right decision depends on the product objective. If threshold setting, ranking stability, or
calibration quality is central, the team should compare those properties explicitly rather than
letting headline accuracy make the decision alone. In many such cases, a calibrated linear model
from [Module 1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/) or a boosting approach from
[Module 1.6](../module-1.6-xgboost-gradient-boosting/) is the more appropriate next step.

</details>

## Hands-On Exercise: Leakage-Safe Random Forest Workflow

The goal of this exercise is to build a clean forest baseline, evaluate it honestly, compare OOB
with cross-validation, audit two importance methods, and verify that scaling is unnecessary for the
tree branch. Keep the process aligned with the contracts from [Module
1.1](../module-1.1-scikit-learn-api-and-pipelines/), [Module
1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/), and [Module
1.4](../module-1.4-feature-engineering-and-preprocessing/).

### Setup

- [ ] Choose a tabular binary-classification dataset that is small enough to iterate on quickly.
- [ ] If your dataset is fully numeric, optionally create one simple categorical feature by binning
  a numeric column so you can reuse the `ColumnTransformer` patterns from [Module
  1.4](../module-1.4-feature-engineering-and-preprocessing/).
- [ ] Reserve a final untouched test split before any model comparison.
- [ ] Decide up front which metric is primary. If you care about ranking quality, make ROC AUC
  explicit rather than assuming `score()` tells the full story.

### Step 1: Build the leakage-safe data split

- [ ] Create `X_train`, `X_test`, `y_train`, and `y_test` with stratification if the target is
  imbalanced.
- [ ] Keep the test set frozen. Do not peek at it during model selection.
- [ ] If you need feature engineering, define it inside a pipeline so the transform is learned only
  from training folds.

### Step 2: Define the preprocessing contract

- [ ] Build a `ColumnTransformer` that encodes categorical columns in the same spirit as [Module
  1.4](../module-1.4-feature-engineering-and-preprocessing/).
- [ ] Do not add `StandardScaler` to the numeric branch for the forest path.
- [ ] Write one sentence in your notebook explaining why scaling is unnecessary for trees.

### Step 3: Fit a single-tree baseline

- [ ] Create a pipeline whose estimator is a `DecisionTreeClassifier`.
- [ ] Start with a modest regularization profile, such as a bounded `max_depth` or a nontrivial
  `min_samples_leaf`.
- [ ] Record validation accuracy or AUC and inspect `tree_.max_depth` and `tree_.node_count` on the
  fitted estimator.
- [ ] Write down whether the tree looks variance-prone relative to the size and noise level of your
  data.

### Step 4: Fit an initial Random Forest

- [ ] Replace the tree with `RandomForestClassifier`.
- [ ] Use `bootstrap=True` and `oob_score=True`.
- [ ] Start with a reasonable tree count rather than a tiny demo count.
- [ ] Record `oob_score_` after fitting and note that it is not the same thing as cross-validated
  AUC.

### Step 5: Evaluate with held-out CV discipline

- [ ] Run cross-validation on the training split only.
- [ ] If ROC AUC is your metric, compute it explicitly rather than relying on `score()`.
- [ ] Compare the OOB story with the CV story. Ask whether both say the forest is promising.
- [ ] Keep any final model-choice decision off the test set.

### Step 6: Demonstrate the no-scaling property

- [ ] Clone the pipeline and add `StandardScaler` to the numeric branch even though the forest does
  not need it.
- [ ] Refit the scaled and unscaled versions under the same CV protocol.
- [ ] Confirm that the predictive difference is negligible while the scaled version is operationally
  more complex.
- [ ] Remove the scaler again and keep the simpler forest pipeline.

### Step 7: Sweep `n_estimators` to find the plateau

- [ ] Evaluate a small ladder of tree counts such as `100`, `200`, and `300`.
- [ ] Track OOB and CV performance for each point.
- [ ] Stop increasing the count when the curve visibly plateaus for your metric and budget.
- [ ] Write down the smallest tree count that sits on the plateau.

### Step 8: Tune the main variance knobs

- [ ] Sweep `min_samples_leaf` across a small set of sensible values.
- [ ] Try one or two `max_depth` settings if the forest still looks too flexible.
- [ ] Adjust `max_features` if you want to trade bias against tree diversity or reduce runtime.
- [ ] Avoid spending most of your search budget on `criterion` unless you have already stabilized
  the more important knobs.

### Step 9: Compare impurity and permutation importance

- [ ] Fit the selected forest on the training split.
- [ ] Record `feature_importances_` as a rough debugging view.
- [ ] Compute `permutation_importance` on a held-out validation surface.
- [ ] Write a short note describing any feature whose importance ranking changes materially between
  the two methods.

### Step 10: Stress-test for correlated features

- [ ] Inspect whether your top features are strongly correlated.
- [ ] If they are, regroup them conceptually before interpreting a low one-at-a-time permutation
  score.
- [ ] If possible, run a grouped permutation experiment or at least a feature-cluster analysis.
- [ ] Document whether correlated substitutes change the story you would tell about the model.

### Step 11: Run the final untouched test pass

- [ ] Freeze the chosen configuration based only on training-time development evidence.
- [ ] Fit that configuration on the full training split.
- [ ] Evaluate exactly once on the untouched test split.
- [ ] Report accuracy and, if relevant, explicit ROC AUC with `roc_auc_score(y_test,
  model.predict_proba(X_test)[:, 1])`.

### Step 12: Write the model-selection memo

- [ ] Summarize why the Random Forest did or did not beat the single-tree and linear baselines.
- [ ] State whether OOB and CV told the same story.
- [ ] Note whether scaling was removed from the tree branch.
- [ ] State which importance method you trust for operational decisions and why.

### Completion Check

- [ ] Your final forest pipeline has no unnecessary scaler in the tree branch.
- [ ] Any OOB experiment uses `bootstrap=True`.
- [ ] You never called classifier `score()` "AUC."
- [ ] The final model was selected without touching the test set during tuning.
- [ ] Feature-importance conclusions were based on held-out permutation analysis, not on impurity
  importance alone.
- [ ] If correlated features existed, you accounted for their effect on permutation importance.
- [ ] Your final write-up can explain why a forest was chosen over a single tree, or why it was
  rejected in favor of a simpler model.

## Sources

- scikit-learn tree user guide: https://scikit-learn.org/stable/modules/tree.html
- scikit-learn ensemble user guide: https://scikit-learn.org/stable/modules/ensemble.html
- scikit-learn permutation importance guide:
  https://scikit-learn.org/stable/modules/permutation_importance.html
- scikit-learn common pitfalls guide: https://scikit-learn.org/stable/common_pitfalls.html
- `DecisionTreeClassifier` API reference:
  https://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeClassifier.html
- `DecisionTreeRegressor` API reference:
  https://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeRegressor.html
- `RandomForestClassifier` API reference:
  https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html
- `RandomForestRegressor` API reference:
  https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html
- `ExtraTreesClassifier` API reference:
  https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.ExtraTreesClassifier.html
- `BaggingClassifier` API reference:
  https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.BaggingClassifier.html
- `permutation_importance` API reference:
  https://scikit-learn.org/stable/modules/generated/sklearn.inspection.permutation_importance.html
- Permutation-importance example:
  https://scikit-learn.org/stable/auto_examples/inspection/plot_permutation_importance.html
- Multicollinear permutation-importance example:
  https://scikit-learn.org/stable/auto_examples/inspection/plot_permutation_importance_multicollinear.html
- Decision-tree visualization example:
  https://scikit-learn.org/stable/auto_examples/tree/plot_iris_dtc.html
- Forest feature-importance example:
  https://scikit-learn.org/stable/auto_examples/ensemble/plot_forest_importances.html

## Next Module

Continue to [Module 1.6: XGBoost & Gradient Boosting](../module-1.6-xgboost-gradient-boosting/).
