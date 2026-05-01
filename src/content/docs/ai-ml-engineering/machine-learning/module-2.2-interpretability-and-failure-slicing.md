---
title: "ML Interpretability + Failure Slicing"
description: "Pick the right interpretability tool for the question being asked — permutation importance, PDP/ICE, SHAP, LIME, counterfactuals, or failure slicing — and avoid the canonical traps: SHAP explains the model not reality, permutation importance lies under correlated features, PDP assumes feature independence, and per-row attribution is rarely the operational tool."
slug: ai-ml-engineering/machine-learning/module-2.2-interpretability-and-failure-slicing
sidebar:
  order: 22
---

> Track: AI/ML Engineering | Complexity: Intermediate | Time: 90-110 minutes
> Prerequisites: [Module 1.1: Scikit-learn API & Pipelines](../module-1.1-scikit-learn-api-and-pipelines/), [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/), [Module 1.5: Decision Trees & Random Forests](../module-1.5-decision-trees-and-random-forests/), and [Module 1.6: XGBoost & Gradient Boosting](../module-1.6-xgboost-gradient-boosting/).

The on-call interpretability incident usually begins with a well-intentioned report. A team ships a SHAP appendix to compliance, the appendix lists top drivers for denied applications, and the next meeting treats those SHAP values as if they were causal statements about the world. They are not. SHAP describes what the model did with the features it was given; it does not prove that changing a feature would change the real outcome in the same way. The second version of the same incident is operational instead of legal: a team spends a week reading per-row SHAP plots for 50,000 denials, when the real failure is concentrated in one cohort that a slice table would have surfaced in ten minutes. This module is the corrective. The interpretability tool has to match the question. SHAP describes the model, not reality, and per-row attribution is rarely the right operational tool when the defect lives at the cohort level.

## Learning Outcomes

By the end of this module, a practitioner will be able to:

1. **Diagnose** whether a model explanation request is global, local,
   functional, counterfactual, causal, fairness-related, or operational, and
   reject tools that answer a different question.
2. **Defend** the descriptive-versus-causal boundary clearly enough that a
   stakeholder does not mistake SHAP, LIME, PDP, or permutation importance for a
   claim about what would happen in the real world under intervention.
3. **Implement** permutation importance, PDP/ICE, TreeSHAP, KernelSHAP, LIME,
   counterfactual generation, and failure slicing with leakage-safe held-out
   data and standard Python libraries.
4. **Compare** the canonical failure modes of the major tools: correlated
   features for permutation importance, independence violations for PDP/ICE,
   background sensitivity for SHAP, instability for LIME, and feasibility gaps
   for counterfactuals.
5. **Build** an operational interpretation report that starts with cheap global
   diagnostics, escalates only when needed, prioritizes failure slices over
   one-row storytelling, and documents the limits of every explanation it uses.

These outcomes extend the evaluation contract from [Module 1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/), the fitted-pipeline contract from [Module 1.1](../module-1.1-scikit-learn-api-and-pipelines/), the tree-model intuition from [Module 1.5](../module-1.5-decision-trees-and-random-forests/), and the boosted-tree context from [Module 1.6](../module-1.6-xgboost-gradient-boosting/). The new habit is not "always explain the row." The habit is "name the question first, then pick the cheapest faithful tool that answers it."

## Why This Module Matters

Interpretability is expensive when it is used as a performance ritual and cheap when it is used as a debugging discipline. The right order of moves is: permutation importance, then PDP/ICE, then SHAP, then LIME or counterfactuals for local questions, then failure slicing for operational defects. That order is deliberate. It begins with tools that are simple to compute and easy to falsify, then escalates toward methods that require more assumptions, more background choices, and more narrative discipline.

The documentation spine for this module is small. The SHAP documentation frames SHAP as "a game theoretic approach to explain the output of any machine learning model":
https://shap.readthedocs.io/en/latest/
The scikit-learn permutation importance guide defines the cheap global baseline:
https://scikit-learn.org/stable/modules/permutation_importance.html
The
scikit-learn PDP/ICE guide defines the functional-shape tools:
https://scikit-learn.org/stable/modules/partial_dependence.html
Those three
documents are enough to anchor the practice. Everything else in this module is about choosing the right tool for the question and refusing to overclaim.

The order also protects you from a common production failure. If a model starts missing a subgroup, a per-row explanation can make every miss look unique. A slice table can show that the misses share the same cohort, geography, product line, language, plan type, device class, or data-source path. The same lesson from [Module 2.1](../module-2.1-class-imbalance-and-cost-sensitive-learning/) applies
here: the metric you celebrate has to match the deployment. A beautiful local explanation is a bad operational artifact when the deployment needs a cohort-level remedy.

## Section 1: What Interpretability Is and Is Not

Interpretability is a set of techniques for making model behavior legible enough that humans can debug, govern, and operate the system. It is not a magic conversion layer that turns a black-box prediction into truth about the world. The distinction sounds philosophical until a compliance report, a customer notice, or an on-call escalation depends on it.

There are three practical reasons to explain a model.

First, interpretability supports compliance. A regulated workflow often needs a clear account of what features were available, what the model used, and whether the resulting decision can be described in a way a reviewer can evaluate. Permutation importance, SHAP summaries, sparse linear models, and counterfactual explanations can all contribute to that account.

Second, interpretability supports debugging. A feature that dominates global importance may be a leakage feature. A PDP that spikes in an implausible region may expose a feature-engineering bug. A failure slice with poor PR-AUC may show that a data source is missing for one cohort. This is the mode where interpretability earns its keep most often.

Third, interpretability supports trust, but only in the engineering sense of the word. It helps a team understand when the model is behaving consistently with the data and the task. It should not be used to manufacture stakeholder comfort when the evaluation, calibration, monitoring, or fairness evidence is weak.

There are also three things interpretability is not.

It is not a causal claim. A SHAP value for `income` does not prove that changing income would change the real-world outcome. It says the model's output moved when the model saw that feature value relative to its background expectation. Causal claims require causal design, intervention reasoning, and confounder discipline. That is why Module 2.7, Causal Inference for ML Practitioners, is a separate forthcoming module rather than a footnote inside SHAP.

It is not a fairness audit. A sensitive attribute can have low SHAP importance while the model still produces disparate impact through correlated proxies. A fairness audit asks group-level harm, parity, calibration, and allocation questions. SHAP can help investigate a suspected mechanism, but it cannot replace the audit. Module 2.6, Fairness & Bias Auditing, is the right home for that workflow.

It is not a replacement for evaluation. A model with coherent explanations can still have poor PR-AUC, bad calibration, leakage, or brittle generalization. The evaluation contract from [Module 1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/) comes first. Interpretability explains behavior after the behavior has been measured honestly.

The descriptive/causal boundary is the spine of this module. Most interpretability methods answer "what did this model do?" They do not answer "what would happen if the world changed?" Treating those as the same question is how teams write confident documents that collapse under review.

## Section 2: Global vs Local Interpretability

The first fork is global versus local. Global explanations summarize model behavior over a dataset. Local explanations describe one prediction or one small region around a prediction. Many bad interpretability reports fail before the first chart because they use a local tool to answer a global question, or a global tool to justify one individual decision.

| Question | Best first tool | Scope | What it answers |
| --- | --- | --- | --- |
| Which features matter most on held-out data? | Permutation importance | Global | Which feature shuffles hurt the score most |
| What shape did the model learn for one feature? | PDP/ICE | Global/regional | How predictions move across a feature grid |
| Why did this tree model predict high risk for this row? | TreeSHAP | Local | How feature values add up to the model output |
| Why did this arbitrary black-box model predict this row? | LIME or KernelSHAP | Local | Which local surrogate features approximate the prediction |
| What would need to change for a different decision? | Counterfactuals | Local/actionable | Feasible changes that cross the decision boundary |
| Where is the model failing in production? | Failure slicing | Cohort/operational | Which cohorts have poor metrics |
| Is this model fair? | Fairness audit | Group/system | Whether outcomes differ harmfully across protected groups |
| Would changing this feature change the real outcome? | Causal inference | Causal/system | Effects under intervention |

The table is intentionally asymmetric. It names fairness audits and causal inference as different workflows because they are often mislabeled as interpretability. If a stakeholder asks, "Why was this applicant denied?", SHAP or LIME may be useful. If the stakeholder asks, "Would approving more applicants from this group improve repayment outcomes?", interpretability is the wrong frame. That is a causal policy question.

Global tools are usually the right starting point because most model failures are not one-row mysteries. A model overuses a leakage feature. A missingness indicator dominates. A monotonic relationship runs in the wrong direction. A cohort has worse calibration. These are global or slice-level problems. Local tools become useful after the global picture has narrowed the question.

Local tools are still valuable. They help explain a representative true positive, a false positive, a false negative, or a borderline row. They help write adverse-action notices when the deployment requires row-level reasoning. They help compare two models on the same case. But local explanations become noise when a team treats a row-by-row gallery as a substitute for a cohort metric table.

## Section 3: Permutation Importance — the Cheap-and-Honest Baseline

Permutation importance is the first global diagnostic because it asks a blunt question on held-out data: if I break this feature, how much does the model's score degrade? The scikit-learn guide defines the method as "randomly shuffling the values of a single feature and observing the resulting degradation of the model's score":
https://scikit-learn.org/stable/modules/permutation_importance.html
That definition is both the strength and the
weakness. It is simple, model agnostic, and tied to the evaluation metric. It is also vulnerable to correlated features because the model may recover the shuffled information through a partner feature.

The procedure is straightforward.

Train the model on the training set.

Score the fitted model on held-out validation data.

For one feature, randomly permute that feature's values in the held-out data.

Score the model again on the corrupted held-out data.

Record the score drop.

Repeat the shuffle several times and average the score drop.

Move to the next feature.

The `n_repeats` parameter matters because a single shuffle can be lucky or unlucky. Five repeats is often enough for a quick screen; ten to thirty repeats is better when the ranking will drive a decision. The scikit-learn function is `sklearn.inspection.permutation_importance`, documented here:
https://scikit-learn.org/stable/modules/generated/sklearn.inspection.permutation_importance.html
Use it on a fitted estimator or fitted pipeline, and pass held-out data, not the training set. Permutation importance on training data answers "what did the model memorize?" Held-out permutation importance answers "what does the model need to score well on data it did not fit?"

```python
import numpy as np
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

X, y = make_classification(
    n_samples=4000,
    n_features=8,
    n_informative=4,
    n_redundant=0,
    random_state=0,
)

feature_names = np.array([f"x{i}" for i in range(X.shape[1])])
X_train, X_valid, y_train, y_valid = train_test_split(
    X,
    y,
    test_size=0.25,
    stratify=y,
    random_state=0,
)

pipe = Pipeline([
    ("scale", StandardScaler()),
    ("model", RandomForestClassifier(n_estimators=300, random_state=0)),
])
pipe.fit(X_train, y_train)

result = permutation_importance(
    pipe,
    X_valid,
    y_valid,
    scoring="average_precision",
    n_repeats=10,
    random_state=0,
)

order = result.importances_mean.argsort()[::-1]
for idx in order:
    print(
        feature_names[idx],
        round(result.importances_mean[idx], 4),
        "+/-",
        round(result.importances_std[idx], 4),
    )
```

Notice the scoring choice. In an imbalanced workflow, use the metric that matches the deployment, as in [Module 2.1](../module-2.1-class-imbalance-and-cost-sensitive-learning/). If the model is selected by PR-AUC, compute permutation importance with `scoring="average_precision"`. If the model is selected by log-loss or calibration, use the corresponding scoring function. A feature is important only relative to the score you care about.

The canonical pitfall is correlated features. The scikit-learn multicollinearity example says it directly: "When two features are correlated and one of the features is permuted, the model still has access to the latter through its correlated feature. This results in a lower reported importance value for both features, though they might actually be important."
https://scikit-learn.org/stable/auto_examples/inspection/plot_permutation_importance_multicollinear.html
This is the same model-family intuition you already saw in [Module 1.5](../module-1.5-decision-trees-and-random-forests/): a tree ensemble can split on either member of a correlated pair. If feature A and feature B carry nearly the same signal, shuffling A leaves B available, and shuffling B leaves A available. The individual importances look small even when the pair is crucial.

> **Pause and predict** — A random forest gets strong validation PR-AUC from two
> almost-duplicate features, `debt_ratio_raw` and `debt_ratio_normalized`.
> Permutation importance says both are unimportant. Is the model ignoring them?
> (Answer: not necessarily. Each feature may act as backup for the other. When
> one is shuffled, the other still carries the same information, so the score
> barely drops. The right check is groupwise or cluster-aware permutation, not a
> conclusion that both features are useless.)

The remedy is to cluster correlated features, keep one representative from each cluster, or permute clusters as groups. The scikit-learn example demonstrates a cluster-correlated-features approach: compute feature correlations, cluster the features, select representatives, and rerun permutation importance after removing redundant partners. In production, the version you choose depends on the task. For feature selection, selecting one representative per cluster is reasonable. For explanation, groupwise importance is often more honest: "this correlated feature family matters" is the correct statement.

```python
import numpy as np
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import average_precision_score
from sklearn.model_selection import train_test_split

rng = np.random.default_rng(0)
X_base, y = make_classification(
    n_samples=5000,
    n_features=5,
    n_informative=2,
    n_redundant=0,
    weights=[0.85, 0.15],
    random_state=0,
)

# Add a strongly correlated partner for x0.
partner = X_base[:, [0]] + rng.normal(scale=0.02, size=(X_base.shape[0], 1))
X_corr = np.hstack([X_base, partner])
names = np.array(["x0", "x1", "x2", "x3", "x4", "x0_partner"])

X_train, X_valid, y_train, y_valid = train_test_split(
    X_corr,
    y,
    test_size=0.25,
    stratify=y,
    random_state=0,
)

model = RandomForestClassifier(n_estimators=300, random_state=0)
model.fit(X_train, y_train)

base_score = average_precision_score(y_valid, model.predict_proba(X_valid)[:, 1])
plain = permutation_importance(
    model,
    X_valid,
    y_valid,
    scoring="average_precision",
    n_repeats=10,
    random_state=0,
)

print("plain feature importances")
for idx in plain.importances_mean.argsort()[::-1]:
    print(names[idx], round(plain.importances_mean[idx], 4))

# Cluster-aware demonstration: permute x0 and its partner together.
X_grouped = X_valid.copy()
perm = rng.permutation(X_grouped.shape[0])
group = [0, 5]
X_grouped[:, group] = X_grouped[perm][:, group]
group_score = average_precision_score(y_valid, model.predict_proba(X_grouped)[:, 1])

print("base score:", round(base_score, 4))
print("score after permuting correlated pair:", round(group_score, 4))
print("group importance:", round(base_score - group_score, 4))
```

This code does not implement hierarchical clustering because the pedagogical point is the failure mode. In a real report, you would compute a correlation matrix, cluster features above a threshold, and either pick one representative or permute the cluster as a unit. The multicollinearity example in scikit-learn is the reference pattern for that
remedy:
https://scikit-learn.org/stable/auto_examples/inspection/plot_permutation_importance_multicollinear.html

## Section 4: PDP and ICE — Functional Shape

Permutation importance says which features matter for a score. PDP and ICE ask a different question: what shape did the model learn as a feature changes? Scikit-learn defines partial dependence as the dependence between the target response and a set of input features of interest, marginalizing over the other
features: https://scikit-learn.org/stable/modules/partial_dependence.html
ICE
curves show the same relationship per row rather than as an average. The API entry point is `PartialDependenceDisplay.from_estimator`, documented here:
https://scikit-learn.org/stable/modules/generated/sklearn.inspection.PartialDependenceDisplay.html

A PDP is the average prediction over a grid. Pick a feature value, replace that feature with the grid value for every row, ask the model for predictions, and average the predictions. Repeat across the grid. The curve says how the model's average prediction moves as that feature is set to each value.

An ICE plot keeps each row's curve separate. Instead of averaging immediately, it shows one curve per validation row. ICE is useful when the average hides heterogeneity. A PDP might be flat because half the rows slope upward and half the rows slope downward. ICE exposes that pattern. Centered ICE subtracts each row's starting point so differences in slope are easier to see.

The scikit-learn API makes the comparison direct with `kind="both"` and `centered=True`.

```python
from sklearn.datasets import make_classification
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import PartialDependenceDisplay
from sklearn.model_selection import train_test_split

X, y = make_classification(
    n_samples=3000,
    n_features=6,
    n_informative=4,
    random_state=0,
)

X_train, X_valid, y_train, y_valid = train_test_split(
    X,
    y,
    test_size=0.25,
    stratify=y,
    random_state=0,
)

clf = HistGradientBoostingClassifier(random_state=0)
clf.fit(X_train, y_train)

display = PartialDependenceDisplay.from_estimator(
    clf,
    X_valid,
    features=[0, 1],
    kind="both",
    centered=True,
    subsample=200,
    random_state=0,
)
```

The canonical pitfall is the independence assumption. The scikit-learn guide states the problem exactly: "Both PDPs and ICEs assume that the input features of interest are independent from the complement features, and this assumption is often violated in practice. Thus, in the case of correlated features, we will create absurd data points to compute the PDP/ICE."
https://scikit-learn.org/stable/modules/partial_dependence.html

That sentence should slow you down. If `age` and `years_employed` are strongly correlated, a PDP for `years_employed` may evaluate combinations that cannot exist. If `loan_amount` and `monthly_payment` are tied by a product formula, a PDP that changes one without the other creates impossible rows. The model will still produce predictions for those rows because most tabular models accept any numeric matrix of the right shape. The plot may therefore average predictions over regions where the data distribution has no support.

The operational consequence is simple: PDP is safe when the feature is roughly independent from the rest of the features or when the grid stays in a dense region of the data. PDP is risky when the feature is tightly coupled to other features. ICE helps by showing whether individual rows behave differently, but ICE does not remove the independence assumption. It only makes some of the damage visible.

```python
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import PartialDependenceDisplay
from sklearn.model_selection import train_test_split

rng = np.random.default_rng(0)
n = 2000
age = rng.normal(45, 10, size=n)
years_employed = np.clip(age - 22 + rng.normal(0, 3, size=n), 0, None)
noise = rng.normal(size=n)

X = np.column_stack([age, years_employed, noise])
y = 0.2 * age + 0.8 * years_employed + rng.normal(0, 2, size=n)

X_train, X_valid, y_train, y_valid = train_test_split(
    X,
    y,
    test_size=0.25,
    random_state=0,
)

rf = RandomForestRegressor(n_estimators=300, random_state=0)
rf.fit(X_train, y_train)

display = PartialDependenceDisplay.from_estimator(
    rf,
    X_valid,
    features=[0, 1],
    kind="both",
    centered=True,
    subsample=100,
    random_state=0,
)
```

In this example, `age` and `years_employed` are deliberately coupled. A PDP that sets a young row to very high `years_employed` creates an absurd row. The model still predicts. The plot still renders. The practitioner has to know the data well enough not to overread the curve. This is why PDP/ICE belong after permutation importance in the
playbook: they are more informative about shape, but they require more domain sanity checking.

There is a brief connection to deep learning here. Gradient-based saliency in computer vision, introduced in the context covered in [Deep Learning Module 1.4](../../deep-learning/module-1.4-cnns-computer-vision/), also tries to answer "which inputs changed the output?" Attention weights in transformer architectures are sometimes read as explanations as well, but attention is not automatically a faithful explanation. The same caution applies: a visualization is an interpretability artifact only after you know what question it answers and what assumptions it made.

## Section 5: SHAP — the Workhorse for Tabular

SHAP is the workhorse interpretability method for tabular ML because it gives a consistent additive explanation vocabulary across local and global views. The SHAP documentation describes the library as "a game theoretic approach to explain the output of any machine learning model":
https://shap.readthedocs.io/en/latest/
The underlying idea comes from Shapley
values in cooperative game theory, and the modern ML formulation was presented by Lundberg and Lee in 2017:
https://arxiv.org/abs/1705.07874

The game-theoretic story is compact. Imagine the prediction as a payout and the features as players in a cooperative game. A Shapley value assigns each feature its fair contribution to the difference between a baseline output and the prediction for a row. "Fair" has a formal meaning. The values satisfy efficiency, symmetry, dummy, and additivity.

Efficiency means the feature contributions add up to the model output relative to the baseline. Symmetry means two features that contribute identically receive the same value. Dummy means a feature that contributes nothing receives zero. Additivity means explanations compose across sums of games. You do not need the proof to use SHAP responsibly, but you do need the discipline: the values are model-output attributions under a chosen background distribution. They are not facts about the world.

There are several SHAP families.

TreeSHAP exploits tree structure and computes exact Shapley values in polynomial time for tree ensembles. This is the high-value regime for random forests, gradient boosting, XGBoost-style models, and other tree ensembles. The SHAP API reference is the entry point for those explainers:
https://shap.readthedocs.io/en/latest/api.html
The connection to
[Module 1.6](../module-1.6-xgboost-gradient-boosting/) is direct: boosted trees are often the best tabular baseline, and TreeSHAP is the explanation method that earned its popularity on that model family.

KernelSHAP is model agnostic. It approximates Shapley values by sampling feature coalitions and fitting a weighted local model. That flexibility is useful, but it is slower, noisier, and more sensitive to the background dataset. Do not use KernelSHAP on a tree ensemble when TreeSHAP is available. That is paying more to get a less exact answer.

Linear SHAP has closed-form structure for linear models. In many ordinary linear or logistic settings, the model coefficients already carry most of the explanation burden, especially when the features are standardized and the regularization path is understood. That is why [Module 1.2](../module-1.2-linear-and-logistic-regression-with-regularization/)
matters: an inherently interpretable model often beats a black box plus a
post-hoc explanation.

SHAP supports both local and global views. A waterfall plot explains one row by starting at the expected value and adding feature contributions until it reaches the row's prediction. A global bar chart of `mean(abs(SHAP))` ranks features by average attribution magnitude. A beeswarm plot shows both magnitude and direction across many rows. The global views are often more useful than the local view because they reveal systematic behavior rather than one-case stories.

**Hard boundary:** SHAP describes the model, not reality. If a SHAP value says that `missed_payment_count` increased the predicted default risk for a row, it does not prove that reducing the count would reduce the real default risk by the same amount. It says the fitted model used that feature value in that way relative to the selected background. For intervention claims, wait for Module 2.7, Causal Inference for ML Practitioners.

```python
import shap
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

X, y = make_classification(
    n_samples=3000,
    n_features=10,
    n_informative=5,
    weights=[0.8, 0.2],
    random_state=0,
)

feature_names = [f"x{i}" for i in range(X.shape[1])]
X_train, X_valid, y_train, y_valid = train_test_split(
    X,
    y,
    test_size=0.25,
    stratify=y,
    random_state=0,
)

rf = RandomForestClassifier(n_estimators=300, random_state=0)
rf.fit(X_train, y_train)

# Modern SHAP API: Explainer auto-routes to an appropriate tree explainer.
explainer = shap.Explainer(rf, X_train, feature_names=feature_names)
values = explainer(X_valid[:200])

# Local explanation for one validation row.
shap.plots.waterfall(values[0, :, 1])

# Global summaries over the validation sample.
shap.plots.bar(values[:, :, 1])
shap.plots.beeswarm(values[:, :, 1])
```

The exact indexing for classifier outputs can vary with SHAP versions and model types, so inspect the returned object in a notebook before writing a report. The principle is stable: explain the fitted model on a representative held-out sample, use a background dataset that matches the data distribution you want to explain, and state whether the plotted output is log-odds, probability, or raw model margin.

KernelSHAP is the fallback when the model is not tree-structured and the model itself does not have a clean explanation. For logistic regression, you would usually prefer coefficients or Linear SHAP. The example below uses KernelSHAP to show the pattern because it is the model-agnostic interface practitioners often need for arbitrary predictors.

```python
import shap
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

X, y = make_classification(
    n_samples=2500,
    n_features=8,
    n_informative=4,
    random_state=0,
)

feature_names = [f"x{i}" for i in range(X.shape[1])]
X_train, X_valid, y_train, y_valid = train_test_split(
    X,
    y,
    test_size=0.25,
    stratify=y,
    random_state=0,
)

pipe = Pipeline([
    ("scale", StandardScaler()),
    ("model", LogisticRegression(max_iter=2000)),
])
pipe.fit(X_train, y_train)

background = shap.sample(X_train, 100, random_state=0)
predict_positive = lambda rows: pipe.predict_proba(rows)[:, 1]

explainer = shap.KernelExplainer(predict_positive, background)
shap_values = explainer.shap_values(X_valid[:25], nsamples=100)

shap.summary_plot(shap_values, X_valid[:25], feature_names=feature_names)
```

The operational warning is that KernelSHAP can be slow and sensitive. The background sample, the number of sampled coalitions, and the output scale all matter. If the report depends on KernelSHAP, rerun the explanation with a few background samples and confirm the ranking is stable enough for the decision being made. If it is not stable, the correct report is "this explanation is not stable enough to support the requested claim."

## Section 6: LIME — Local Linear Surrogate

LIME, introduced by Ribeiro, Singh, and Guestrin in 2016 (https://arxiv.org/abs/1602.04938), answers a local question with a local surrogate model. The GitHub repository is here:
https://github.com/marcotcr/lime
The mechanism is simple. Perturb the row locally, ask the black-box model for predictions on those perturbations, weight the perturbations by proximity to the
original row, and fit a sparse linear model to approximate the black-box model near that row. The coefficients of the local surrogate become the explanation.

LIME is useful because it is model agnostic and intuitive. A stakeholder can understand a sparse local linear explanation more easily than a game-theoretic attribution method. It also works when the model is hard to introspect, as long as you can call `predict_proba`.

LIME is also fragile. The explanation can change across random seeds. The kernel bandwidth controls what "local" means. The perturbation distribution may create unrealistic samples. The sparse surrogate may fit the local predictions poorly even though it still returns a neat list of feature weights. This is the faithfulness gap: the local linear model is an explanation artifact, not the original model.

Use LIME when the task is genuinely local, the model is arbitrary, the stakeholder needs a sparse explanation, and the explanation can be sanity checked across seeds. Prefer SHAP when you need additive consistency across many rows, a global ranking from local attributions, or exact tree explanations.

```python
import numpy as np
from lime.lime_tabular import LimeTabularExplainer
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

X, y = make_classification(
    n_samples=3000,
    n_features=8,
    n_informative=4,
    random_state=0,
)
feature_names = [f"x{i}" for i in range(X.shape[1])]
class_names = ["negative", "positive"]

X_train, X_valid, y_train, y_valid = train_test_split(
    X,
    y,
    test_size=0.25,
    stratify=y,
    random_state=0,
)

model = RandomForestClassifier(n_estimators=300, random_state=0)
model.fit(X_train, y_train)

explainer = LimeTabularExplainer(
    training_data=X_train,
    feature_names=feature_names,
    class_names=class_names,
    mode="classification",
    discretize_continuous=True,
    random_state=0,
)

row_id = 0
explanation = explainer.explain_instance(
    X_valid[row_id],
    model.predict_proba,
    num_features=5,
)

print(explanation.as_list())
```

Do not ship a single LIME explanation as if it were a stable property of the model. Run it several times with fixed and varied seeds. Compare it against a nearby row. Check whether the local surrogate score is acceptable. If those checks fail, the explanation is not strong enough for a compliance claim.

## Section 7: Counterfactual Explanations — The Actionable Cousin

Counterfactual explanations ask a different question: what would have to change for the model to make a different decision? That is not the same as "which features contributed most?" A SHAP waterfall may say a row was denied because several features pushed the score down. A counterfactual says, "under this model, a nearby row with these feature changes would have crossed the decision threshold."

The DiCE paper by Mothilal, Sharma, and Tan frames counterfactual explanations around diversity and feasibility:
https://arxiv.org/abs/1905.07697
The DiCE repository is here: https://github.com/interpretml/DiCE
The practical value
is recourse. Counterfactuals are useful for adverse-action notices, debugging threshold behavior, and understanding whether the model's decision boundary can be crossed through plausible changes.

The constraints matter more than the generator. Feasibility means some features cannot change. Age cannot become lower. A historical missed-payment count cannot be rewritten. A country code may not be actionable for the user. Proximity means the counterfactual should be close enough to the original row to be meaningful. Diversity means the generator should return different possible routes rather than three trivial variants of the same route. Plausibility means the counterfactual should live near the training distribution instead of an absurd combination of feature values.

Alibi is another library with counterfactual explanation support, but this module does not depend on it. The standard dependency here is DiCE.

```python
import dice_ml
from sklearn.ensemble import RandomForestClassifier

# `train_frame` is the tabular training frame produced by your preprocessing
# workflow. DiCE's sklearn backend expects the same column names at prediction.
feature_names = ["income", "debt_ratio", "tenure", "missed_payments"]
outcome_name = "approved"

model = RandomForestClassifier(n_estimators=300, random_state=0)
model.fit(train_frame[feature_names], train_frame[outcome_name])

data = dice_ml.Data(
    dataframe=train_frame,
    continuous_features=feature_names,
    outcome_name=outcome_name,
)
wrapped_model = dice_ml.Model(model=model, backend="sklearn")
explainer = dice_ml.Dice(data, wrapped_model, method="random")

# Ask for three different nearby ways to cross the model's decision boundary.
query = validation_frame[feature_names].iloc[[0]]
counterfactuals = explainer.generate_counterfactuals(
    query,
    total_CFs=3,
    desired_class="opposite",
    features_to_vary=["income", "debt_ratio", "tenure"],
)

counterfactuals.visualize_as_dataframe(show_only_changes=True)
```

The code is deliberately modest. A production counterfactual report needs a feature policy before it needs a better optimizer. Which features are mutable? Which changes are legally and ethically appropriate to suggest? Which combinations are plausible? Without that policy, counterfactuals become a machine for producing technically valid but operationally useless advice.

## Section 8: Failure Slicing — The Operational Tool

This is the pivot. Per-row SHAP rarely improves a model. Finding the failing cohort almost always does. A row-level explanation can tell you why one denial looked risky to the model. A slice table can tell you that the model fails on a specific region, plan type, device source, language, data vendor, time window, or acquisition channel. The slice table gives you an engineering action: fix a feature pipeline, collect more examples, add a segment-specific model, change a threshold, or reduce the model's scope.

Failure slicing is just evaluation discipline applied across cohorts. Take the held-out validation set. Add the operational categories you care about. Compute the same metric by cohort that you use for the overall model. Sort by the worst metric, but always keep support counts visible. The cross-links are the same ones you already know: [Module 1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/) for metric discipline and [Module 2.1](../module-2.1-class-imbalance-and-cost-sensitive-learning/) for imbalanced metrics and cost-aware interpretation.

Automated slice-discovery tools, often described under names like SliceFinder, search for combinations of feature predicates where performance is unusually bad. They can be useful, but they are not magic production maturity in a box. The risk is multiple comparisons: if you search enough slices, some will look bad by chance. The production move is to use automated discovery as a candidate generator, then validate candidate slices on fresh data or a later time window.

```python
import numpy as np
from sklearn.datasets import make_classification
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score
from sklearn.model_selection import train_test_split

rng = np.random.default_rng(0)
X, y = make_classification(
    n_samples=6000,
    n_features=8,
    n_informative=4,
    weights=[0.9, 0.1],
    random_state=0,
)

segment = rng.choice(
    ["consumer", "small_business", "enterprise"],
    size=X.shape[0],
    p=[0.65, 0.25, 0.10],
)

# Deliberately make one cohort harder by adding label noise.
hard = segment == "small_business"
flip = hard & (rng.random(X.shape[0]) < 0.15)
y_noisy = y.copy()
y_noisy[flip] = 1 - y_noisy[flip]

X_train, X_valid, y_train, y_valid, seg_train, seg_valid = train_test_split(
    X,
    y_noisy,
    segment,
    test_size=0.25,
    stratify=y_noisy,
    random_state=0,
)

model = HistGradientBoostingClassifier(random_state=0)
model.fit(X_train, y_train)
proba = model.predict_proba(X_valid)[:, 1]

rows = []
for value in np.unique(seg_valid):
    mask = seg_valid == value
    if y_valid[mask].sum() == 0:
        continue
    rows.append({
        "segment": value,
        "n": int(mask.sum()),
        "positives": int(y_valid[mask].sum()),
        "pr_auc": average_precision_score(y_valid[mask], proba[mask]),
    })

for row in sorted(rows, key=lambda item: item["pr_auc"]):
    print(
        row["segment"],
        "n=", row["n"],
        "positives=", row["positives"],
        "pr_auc=", round(row["pr_auc"], 3),
    )
print("overall pr_auc:", average_precision_score(y_valid, proba))
```

The report is intentionally boring. That is the point. When a model is failing in production, the first artifact you want is often a table with `slice`, `n`, `positives`, and the metric that matters. If the worst slice has low support, you mark it as unstable and collect more data. If the worst slice has enough support and is consistently bad across time windows, you have found an operational defect.

> **Pause and decide** — You have 50,000 denied applications, a SHAP waterfall
> for each row, and a complaint that one customer segment sees unusually many
> denials. Do you start by sampling more SHAP plots or by slicing validation
> metrics by segment? (Answer: slice first. The complaint is cohort-shaped, so
> the evidence should be cohort-shaped. Per-row SHAP can help after the failing
> slice is identified, but it is the wrong first artifact for a group-level
> operational defect.)

Failure slicing also protects against the most seductive SHAP anti-pattern: reading rows until a story emerges. Humans are good at finding stories in individual explanations. They are less good at noticing denominator problems, support imbalance, and metric instability unless the table forces those quantities into view. Slice first, then explain representative rows inside the slice if you need to debug mechanism.

## Section 9: Faithfulness — The Explanations Might Lie

Every post-hoc method produces some explanation. That does not mean the explanation faithfully reflects what the model actually computes. A saliency map can look plausible for a randomly initialized neural network. A LIME explanation can be sparse and readable even when the local surrogate fits the black-box predictions poorly. A SHAP summary can be stable under one background sample and unstable under another. A PDP can show a clean curve in a region the data never occupies.

The first sanity check is model randomization. If the explanation barely changes when the model is randomly initialized or the labels are shuffled, the explanation is probably describing the data distribution, the input image, or the explanation method's bias more than the fitted model. This check is easiest in deep learning, but the spirit applies
everywhere: explanations should depend on the trained model.

The second sanity check is perturbation stability. Small changes to the row, background sample, random seed, or validation subsample should not completely rewrite the explanation unless the model itself is unstable in that region. If a single row has a LIME explanation that changes dramatically across seeds, do not ship it as a decisive account of the model.

The third sanity check is metric alignment. If a feature ranks high under permutation importance for accuracy but low for PR-AUC, and the deployment cares about PR-AUC, the accuracy explanation is not the explanation you need. The explanation must be tied to the deployment metric.

Faithfulness matters most in regulatory and safety-critical settings. If an explanation will be used to justify a decision to a customer, a regulator, a clinical reviewer, or a safety board, the bar is higher than "the plot looks reasonable." You need stability checks, background sensitivity checks, and a clear statement of what the explanation can and cannot claim.

The escape hatch is an inherently interpretable model. A sparse logistic regression can be the explanation, not just a model that needs one; cross-link [Module 1.2](../module-1.2-linear-and-logistic-regression-with-regularization/). A bounded-depth tree can be enumerated; cross-link [Module 1.5](../module-1.5-decision-trees-and-random-forests/). These models may leave accuracy on the table, but in regulated workflows the interpretability requirement can be part of the objective function. A black box plus SHAP clears requirements by argument. An interpretable model clears many requirements directly.

The EU AI Act framing is useful even when you are not doing legal analysis. A high-risk system needs evidence, documentation, risk management, and human oversight. An inherently interpretable model makes some of that evidence easier to inspect. A black-box model can still be acceptable, but the explanation stack has to be treated as an argument with assumptions, not as a guarantee.

## Section 10: The Right Tool for the Right Job

The practical decision table is short enough to memorize.

| Job | Use | Avoid |
| --- | --- | --- |
| First global feature screen | Permutation importance on held-out data | Built-in impurity importance as the only evidence |
| Correlated feature family | Cluster-aware or groupwise permutation | Individual permutation ranks interpreted literally |
| Feature-response shape | PDP plus ICE | PDP alone on strongly correlated features |
| Tree ensemble row explanation | TreeSHAP | KernelSHAP on the same tree ensemble |
| Arbitrary black-box local explanation | LIME or KernelSHAP | Treating one local result as globally true |
| Actionable recourse | Counterfactuals with feasibility constraints | Suggesting changes to immutable or implausible features |
| Production failure diagnosis | Failure slicing | Reading hundreds of per-row attributions first |
| Regulatory simplicity | Interpretable model | Black-box model plus fragile post-hoc explanation |

The anti-patterns follow directly from the table. SHAP for everything is a smell. Permutation importance under correlated features is under-reported unless you cluster or group. PDP under correlated features can average absurd rows. KernelSHAP on a tree ensemble wastes the structure TreeSHAP gives you. A single-shot LIME explanation is too unstable for serious claims. Per-row SHAP for a cohort failure is the wrong level of analysis.

This is also where tool order matters. Start with the cheapest global diagnostic. If the global diagnostic says the model depends on a suspicious feature, investigate that feature. If the global diagnostic is clean but a metric is bad, slice failures. If a slice is bad, explain representative rows inside that slice. If a row-level decision needs an action notice, generate counterfactuals with feasibility constraints. Interpretability is a workflow, not a chart type.

## Section 11: When Interpretability Is the Wrong Tool

Interpretability is the wrong tool for causal claims. If the question is "what would happen if we changed this feature?", use causal inference, experiments, natural experiments, or a carefully argued observational design. Module 2.7, Causal Inference for ML Practitioners, exists because model attribution cannot carry that burden.

Interpretability is the wrong tool for fairness audits. SHAP can show that a sensitive attribute has low direct attribution while the model still produces disparate impact through correlated proxies. A zip code, school, device, income proxy, or employment pattern can carry group information even when the protected attribute is absent or low-attribution. Module 2.6, Fairness & Bias Auditing, is where the group metric, parity, calibration, threshold, and mitigation questions belong.

Interpretability is the wrong substitute for shipping safer models. If a bounded-depth tree, monotonic model, sparse linear model, or constrained feature set meets the performance requirement, that may be a better engineering choice than a black-box model explained after the fact. The evaluation discipline from [Module 1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/) and the feature-engineering discipline from [Module 1.4](../module-1.4-feature-engineering-and-preprocessing/) matter more than a fancy explanation library.

Interpretability is also not a model-improvement loop by itself. A SHAP report can tell you which features the model used. It does not automatically tell you which new feature to build, which labels to collect, or which objective to optimize. To predict better, you still need the foundations from earlier machine-learning modules: feature engineering, model selection, validation, regularization, and threshold discipline.

## Section 12: Practitioner Playbook

The playbook is cost-asymmetric. Cheap, robust, global checks come first. Expensive, fragile, local tools come later.

Start with held-out permutation importance using the metric that matches the deployment. If correlated features are present, cluster them, select representatives, or permute groups. Document the metric and the validation set.

Use PDP/ICE for the top few features where shape matters. Check correlation before trusting the curve. Use ICE when you suspect heterogeneity. Treat strange curves as debugging leads, not as truth.

Use SHAP for representative rows and global attribution summaries when the model family earns it, especially tree ensembles. For tree models, prefer TreeSHAP. For arbitrary models, use KernelSHAP only when the cost and approximation limits are acceptable. State the background data and output scale.

Use LIME when the stakeholder needs a sparse local surrogate for an arbitrary model, and rerun it across seeds. Do not promote a single LIME output into a global claim.

Use counterfactuals when the question is actionable recourse. Decide which features are mutable before generating examples. Reject counterfactuals that are close numerically but impossible operationally.

Use failure slicing whenever the complaint or metric is cohort-shaped. Slice by the categories the system actually operates on, compute support and the real deployment metric, and validate any discovered slice on another time window.

Decide the remedy only after the diagnosis. The remedy may be feature engineering, more data for the failing cohort, a separate model, a cohort threshold, a monitoring alert, or scope reduction. Sometimes the right answer is to refuse model automation for a segment until the data is good enough.

Document the final explanation in plain language. Name the data split, metric, model version, explanation method, background data, important assumptions, and known limitations. The explanation is an engineering artifact, not a screenshot.

## Did You Know?

- TreeSHAP computes exact Shapley values in polynomial time for tree ensembles,
  which is why tree models occupy the sweet spot for practical SHAP workflows:
  https://arxiv.org/abs/1705.07874 and https://shap.readthedocs.io/en/latest/api.html
- The scikit-learn PDP guide warns that PDP and ICE assume independence and can
  create "absurd data points" when correlated features are varied independently:
  https://scikit-learn.org/stable/modules/partial_dependence.html
- The scikit-learn permutation-importance example warns that correlated
  features can under-report each other because the model still has access to the
  signal through the partner feature:
  https://scikit-learn.org/stable/modules/permutation_importance.html
- DiCE is designed to generate diverse counterfactual explanations while
  balancing proximity, diversity, and feasibility constraints:
  https://arxiv.org/abs/1905.07697 and https://github.com/interpretml/DiCE

## Common Mistakes

| Mistake | Why it bites | Fix |
| --- | --- | --- |
| Treating SHAP as causal | SHAP attributes model output; it does not prove intervention effects in the real world | State that SHAP explains the model and route causal claims to Module 2.7 |
| Running permutation importance under correlation and trusting individual ranks | Correlated partners back each other up, so each feature's shuffle can look harmless | Cluster correlated features or permute feature groups |
| Reading PDP literally under correlated features | PDP/ICE may evaluate impossible feature combinations and average predictions over absurd rows | Check correlations, use ICE, and restrict interpretation to supported regions |
| Using KernelSHAP on a tree ensemble | It is slower and approximate when TreeSHAP can exploit tree structure directly | Use `shap.Explainer` or a tree explainer for tree models |
| Shipping a single LIME explanation | LIME can vary with random seed, kernel bandwidth, and perturbation distribution | Run stability checks and report local surrogate quality |
| Reading per-row SHAP for a cohort failure | The failure is group-shaped, so row stories delay the metric table that would identify the defect | Slice validation or production metrics by cohort first |
| Treating SHAP as a fairness audit | A sensitive feature can have low attribution while proxies create disparate impact | Run a fairness audit with group metrics and proxy analysis |
| Computing permutation importance on training data | The result can reward memorized training behavior rather than held-out utility | Compute on validation or test data reserved for explanation |

## Quiz

1. A compliance reviewer reads a SHAP report and writes, "Increasing income
causes the model's default-risk estimate to fall, so applicants can improve their outcome by increasing income." What is wrong with the sentence?

<details><summary>Answer</summary>
The sentence turns a model attribution into a causal claim. SHAP can say that the model output was lower for rows with higher income relative to the chosen background. It cannot prove that intervening on income would change the real default outcome, or even that the model would respond the same way under a feasible intervention. The corrected sentence is descriptive: "For this fitted model and background data, higher income contributed downward to the predicted risk." Causal recourse belongs in a causal-inference workflow, not a SHAP plot.
</details>

2. A random forest uses two strongly correlated features. Permutation
importance reports both as low importance, but dropping both together hurts PR-AUC. Which explanation is most likely?

<details><summary>Answer</summary>
The features are backing each other up. When one feature is permuted, the model can still recover the signal from the correlated partner, so the individual score drop is small. Dropping or permuting both together removes the shared signal and exposes the true importance of the feature family. The fix is cluster-aware or groupwise permutation importance, not a literal reading of the individual ranks.
</details>

3. A PDP for `loan_amount` shows that predicted risk falls as loan amount rises.
The team knows loan amount is tightly coupled to product type and underwriting channel. What should they check before trusting the curve?

<details><summary>Answer</summary>
They should check whether the PDP is creating unsupported combinations of `loan_amount`, product type, and underwriting channel. PDP varies one feature while holding the others as observed, which assumes the feature of interest is independent of the complement features. When that assumption fails, the plot can average predictions over impossible rows. ICE curves, correlation checks, and slice-specific PDPs can help, but the core answer is to restrict interpretation to regions supported by the data.
</details>

4. A team has a gradient-boosted tree model and wants row-level explanations for
hundreds of validation examples. One engineer proposes KernelSHAP because it is model agnostic. What is the better first choice?

<details><summary>Answer</summary>
Use TreeSHAP through SHAP's tree-aware explainer path. KernelSHAP is useful when the model is arbitrary and no structured explainer is available, but for tree ensembles it is slower and approximate compared with the tree-specific method. The better first choice is `shap.Explainer(model, background)` or an explicit tree explainer, then waterfall plots for representative rows and global summaries such as mean absolute SHAP or beeswarm plots.
</details>

5. A LIME explanation for one rejected application changes substantially across
three random seeds. What should the report say?

<details><summary>Answer</summary>
The report should say the local explanation is unstable and should not be used as decisive evidence for that row. LIME fits a local surrogate from sampled perturbations, and changes across seeds indicate the sparse surrogate is not stable in that region. The team can try more samples, tune the kernel width, or use another local method, but the honest conclusion is that this LIME output is not strong enough for a compliance claim without additional evidence.
</details>

6. A support team complains that model denials appear concentrated in one
customer segment. The ML team has a dashboard of per-row SHAP plots. What is the first analysis they should run?

<details><summary>Answer</summary>
They should run failure slicing by customer segment on held-out or production data, reporting support, positive count, and the deployment metric for each segment. The complaint is cohort-shaped, so the evidence should be cohort-shaped. SHAP can help explain representative rows inside the failing segment after the slice is confirmed, but it is not the first diagnostic.
</details>

7. A sensitive attribute has low SHAP importance, so a team claims the model is
fair. Why is that claim invalid?

<details><summary>Answer</summary>
Low SHAP importance for the sensitive attribute does not rule out disparate impact. The model may use correlated proxies that carry group information, and fairness is a group-level outcome question rather than a direct-attribution question. A fairness audit must measure outcomes, errors, calibration, and threshold effects across groups. SHAP can help investigate mechanisms, but it cannot certify fairness by itself.
</details>

8. A counterfactual generator suggests that an applicant would be approved if
their age were lower and their historical missed-payment count were changed. What is wrong with the counterfactual?

<details><summary>Answer</summary>
It violates feasibility. Age cannot become lower, and historical missed-payment count cannot be rewritten as an action available to the applicant. A useful counterfactual must respect mutable-feature constraints, proximity, diversity, and plausibility. The generator should be configured to vary only features that can legitimately change, and the report should reject impossible recourse even if it crosses the model's decision boundary.
</details>

## Hands-On Exercise

- [ ] Step 0: Start a notebook or script and import `numpy as np`,
  `make_classification`, `train_test_split`, `RandomForestClassifier`,
  `HistGradientBoostingClassifier`, `LogisticRegression`, `Pipeline`, `StandardScaler`,
  `permutation_importance`, `PartialDependenceDisplay`,
  `average_precision_score`, `roc_auc_score`, `shap`,
  `LimeTabularExplainer`, and `dice_ml`. Keep the package set to numpy,
  sklearn, shap, lime, and dice_ml.

- [ ] Step 1: Generate a binary dataset with `make_classification` using at
  least 5,000 rows, 10 features, four informative features, and moderate class
  imbalance. Add one strongly correlated partner feature by copying one
  informative feature and adding small Gaussian noise.

- [ ] Step 2: Split into train, validation, and test using stratified splits.
  Fit a random forest or histogram gradient boosting model on the training
  split. Record validation ROC-AUC and PR-AUC, and state which metric matches
  the operational goal you choose.

- [ ] Step 3: Compute permutation importance on validation data with
  `scoring="average_precision"` and `n_repeats=10`. Identify the ranks of the
  correlated pair and write one sentence explaining whether individual
  permutation under-reported them.

- [ ] Step 4: Run a groupwise permutation check by shuffling the correlated pair
  together. Compare the grouped score drop with the individual score drops and
  write the conclusion as a feature-family statement.

- [ ] Step 5: Use `PartialDependenceDisplay.from_estimator` with `kind="both"`
  and `centered=True` for two important features. For each plot, write whether
  the feature appears independent enough for a PDP to be trusted.

- [ ] Step 6: Run TreeSHAP with `shap.Explainer(model, X_train_sample)` on a
  representative validation sample. Produce one local waterfall and one global
  bar or beeswarm summary. State explicitly that the explanation describes the
  model, not reality.

- [ ] Step 7: Fit a logistic regression pipeline with `StandardScaler` and run a
  small KernelSHAP example on 10 to 25 validation rows. Compare the cost and
  stability of this explanation with TreeSHAP on the tree model.

- [ ] Step 8: Run LIME for one false positive and one false negative. Repeat at
  least one explanation with a different random seed and record whether the
  feature list is stable enough to trust.

- [ ] Step 9: Build a DiCE counterfactual example for one row. Request three
  diverse counterfactuals and configure at least one feature as not allowed to
  vary. Reject any returned counterfactual that is operationally impossible.

- [ ] Step 10: Add a categorical cohort column to the validation set. Compute
  PR-AUC by cohort with support counts and identify the worst stable slice.
  Explain why this table is often more actionable than reading many per-row SHAP
  plots.

- [ ] Step 11: Write a one-page interpretation report in this order:
  permutation importance, correlated-feature caveat, PDP/ICE shape findings,
  SHAP summary, two local examples, counterfactual feasibility note, failure
  slice table, and recommended remedy.

- [ ] Completion check: confirm that every explanation used held-out validation
  or test rows for reporting, not training rows reused as evidence.

- [ ] Completion check: confirm that the report contains at least one explicit
  "model, not reality" sentence for SHAP or LIME.

- [ ] Completion check: confirm that the final recommendation names an
  engineering remedy: feature engineering, more data, a separate model, a
  threshold change, monitoring, or scope reduction.

## Sources

- https://shap.readthedocs.io/en/latest/
- https://shap.readthedocs.io/en/latest/api.html
- https://scikit-learn.org/stable/modules/permutation_importance.html
- https://scikit-learn.org/stable/modules/partial_dependence.html
- https://scikit-learn.org/stable/modules/generated/sklearn.inspection.permutation_importance.html
- https://scikit-learn.org/stable/modules/generated/sklearn.inspection.PartialDependenceDisplay.html
- https://scikit-learn.org/stable/auto_examples/inspection/plot_permutation_importance_multicollinear.html
- https://github.com/marcotcr/lime
- https://github.com/interpretml/DiCE
- https://arxiv.org/abs/1705.07874
- https://arxiv.org/abs/1602.04938
- https://arxiv.org/abs/1905.07697

## Next Module

The next module in this Tier-2 sequence is **Module 2.3: Probabilistic & Bayesian ML with PyMC**, covering uncertainty-aware modeling, priors, posterior inference, Bayesian regression, and when probability distributions are the model rather than an afterthought. It ships next in Phase 3 of [issue #677](https://github.com/kube-dojo/kube-dojo.github.io/issues/677); the link in this section will go live when that PR lands.
