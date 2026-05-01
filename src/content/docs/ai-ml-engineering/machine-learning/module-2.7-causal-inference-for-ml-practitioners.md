---
title: "Causal Inference for ML Practitioners"
description: "Treat causal inference as a different question from prediction: estimate the effect of an intervention rather than the value of a feature, accept that counterfactuals are unobservable, work the identification step before reaching for an estimator, distinguish the potential-outcomes, DAG, and instrumental-variable frameworks, and run DoWhy's model-identify-estimate-refute loop with EconML for heterogeneous effects rather than treating SHAP, partial dependence, or feature importance as causal evidence."
slug: ai-ml-engineering/machine-learning/module-2.7-causal-inference-for-ml-practitioners
sidebar:
  order: 27
---

> Track: AI/ML Engineering | Complexity: Intermediate | Time: 95-115 minutes
> Prerequisites: [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/), [Module 2.2: Interpretability and Failure Slicing](../module-2.2-interpretability-and-failure-slicing/), and [Module 2.6: Fairness & Bias Auditing](../module-2.6-fairness-and-bias-auditing/). This is the last Tier-2 module of the Machine Learning track. The next conceptual move is Reinforcement Learning Module 2.1, Offline RL & Imitation Learning, which is forthcoming under issue #677. The forward reference is plain text rather than a link because the destination module has not landed yet.

The on-call message arrives in the form of a question that sounds reasonable. A stakeholder reads the SHAP report from [Module 2.2](../module-2.2-interpretability-and-failure-slicing/), notices that `last_month_revenue` is the top driver of churn predictions, and asks the obvious follow-up. If the team intervenes by giving discounts that lower `last_month_revenue`, will customer churn drop in the same proportion that the SHAP value suggests? The honest answer is that the SHAP plot cannot answer that question. SHAP describes how the trained model uses the feature it was given. It does not establish that changing the feature in the world would change the outcome in the world. The question on the table is causal, not predictive, and the predictive model was never asked to answer it.

The second incident arrives a week later, dressed up as an A/B-test follow-up. A growth team reports that customers who received the retention email churned at a much lower rate than customers who did not, and they want to ship the email to everyone. A reviewer points out that the email was sent to users who logged in last week, while users who did not log in were silently excluded. The "control" group is not a control. It is a different population. The naive group difference is not the causal effect of sending the email. It is a mixture of the email's effect and the selection that decided who got it. This module is the corrective. Causal inference is the discipline of estimating what would change if the team intervened, given that the data alone almost never settles the question.

## Learning Outcomes
By the end of this module, a practitioner will be able to:

1. **Diagnose** when a problem is causal because the stakeholder is asking about an intervention or counterfactual rather than about a prediction, and reject cases where causal inference is a misnamed request for a better predictive model.
2. **Explain** the potential-outcomes notation, the fundamental problem of causal inference, the identification step, and why the no-unobserved-confounders assumption cannot be tested from the observed data alone.
3. **Implement** DoWhy's four-step workflow on a synthetic confounded dataset, including at least two refutation methods, and re-estimate the same effect with EconML's `LinearDML` to compare assumption sets.
4. **Compare** propensity weighting, doubly-robust estimation, causal forests, and meta-learners by what they assume, what they relax, and what they cannot rescue from a wrong identification.
5. **Decide** whether the right next move is a randomized experiment, observational adjustment with sensitivity analysis, an instrumental variable, or rejecting the framing because the problem is purely predictive.

## Why This Module Matters
Causal inference is the discipline that earns the right to use the word "because" in production. Predictive ML is excellent at saying that two variables move together in the training distribution. It is silent on whether moving one of them would move the other. That silence is not a temporary limitation that better feature engineering will fix. It is structural, and a large fraction of failed ML projects fail because a causal question was answered with a predictive method.

The two libraries this module leans on are PyWhy's DoWhy and EconML. The DoWhy documentation describes a clean workflow that turns a vague causal claim into an artifact a reviewer can audit. The user guide, which lives at `https://www.pywhy.org/dowhy/main/user_guide/`, organizes the workflow around four causal tasks (effect estimation, attribution, counterfactual estimation, and prediction under intervention) and treats refutation as a first-class step rather than a footnote. EconML, at `https://www.pywhy.org/EconML/`, is the heterogeneous-effect counterpart. It estimates how the effect of a treatment varies across covariates using machine-learning-based estimators with the sklearn fit/predict idiom that practitioners already know. EconML moved from `microsoft/EconML` to `py-why/EconML` in 2023 and the GitHub redirect still proves it. The two libraries together cover most production needs short of a bespoke econometric model.

The module also has to be more rigorous than a tour of methods. Causal inference is an identification problem first and an estimation problem second. The data alone never tells the team whether the no-unobserved-confounders assumption holds, whether the instrument satisfies the exclusion restriction, or whether the parallel-trends premise of difference-in-differences is plausible for the chosen pre and post windows. That assumption work is where mature teams spend most of their effort, because a fancy estimator under the wrong identification is worse than a simple estimator under the right one. The DoWhy refutation suite is useful precisely because it gives the team principled ways to challenge its own answer rather than waiting for a reviewer to do it.

## Section 1: What Causal Inference Is and Isn't
Causal inference is the discipline of estimating the effect of an intervention. The defining question is counterfactual. If the team had set treatment `T` to a different value for the same units, how would outcome `Y` have differed? Predictive ML asks a related but different question. Given values of features `X` already drawn from the deployment distribution, what should the team predict for `Y`? The two questions can use overlapping data and overlapping methods, but they answer different things, and confusing them is the canonical source of expensive mistakes.

This module is the wrong tool when the deployment is satisfied with prediction. A churn-risk score that triggers a retention workflow does not need to be causal. It needs to rank customers usefully so the workflow operates on the right cohort. Asking "what is `P(churn | features)`?" is a prediction question, and a predictive model with [Module 1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/) calibration is the appropriate instrument. Asking "if we send a discount, how many of the cohort who would have churned will now stay?" is a causal question. The same churn data does not automatically support both questions. The causal version often requires either a randomized experiment or a careful observational design with named assumptions.

The shortest test is the intervention test. Could the team, in principle, run an experiment in which it changed the variable of interest while holding everything else constant? If yes, the question is causal and the methods in this module apply. If the variable of interest is not under the team's control and the team only wants to predict the next state of the world, prediction is the right framing. The intervention test is also the most common diagnostic when stakeholders ask for "why" questions in product reviews. Sometimes "why" means "explain this prediction" and the answer lives in [Module 2.2](../module-2.2-interpretability-and-failure-slicing/). Sometimes "why" means "if we changed it, what would happen?" and the answer requires this module.

There are three ideas teams confuse constantly. The first is correlation. Two variables move together in the training distribution. The second is prediction. A model can use one to forecast the other. The third is causation. An intervention on one would change the distribution of the other. Predictive ML treats correlation as if it were causation by default, because that is the assumption that maximizes likelihood on observational data. SHAP, partial dependence, ICE plots, permutation importance, and feature attribution methods all describe the model's response to its inputs, not the world's response to interventions. That is not a flaw of the methods. It is a property of what they were designed to do. When the question turns causal, the predictive toolkit is silent, and the right move is to switch frameworks rather than reinterpret the predictive output.

## Section 2: The Fundamental Problem of Causal Inference
Holland's 1986 framing remains the cleanest statement of why causal inference is hard. For each unit `i`, let `Y_i(1)` be the outcome the unit would experience under treatment and `Y_i(0)` be the outcome the same unit would experience under control. The individual treatment effect is `Y_i(1) - Y_i(0)`. The fundamental problem is that for any given unit, the team observes either `Y_i(1)` or `Y_i(0)`, never both. The other one is a counterfactual that is, by construction, unavailable. This is not a sampling problem that more data will fix. It is structural, and every causal inference method is, in some sense, a way of estimating the missing potential outcome under stated assumptions.

The notation matters because it forces the team to be explicit about the estimand. The average treatment effect is `ATE = E[Y(1) - Y(0)]`, taken over the population. The average treatment effect on the treated is `ATT = E[Y(1) - Y(0) | T = 1]`, taken only over units that actually received treatment. The conditional average treatment effect is `CATE(x) = E[Y(1) - Y(0) | X = x]`, which lets the effect vary across covariates and is the dominant target of EconML and causal forests. The local average treatment effect, `LATE`, is the effect on compliers in an instrumental-variable design. These are different quantities, and a clean causal pipeline names which one it is estimating before it runs any code.

Predictive ML escapes the fundamental problem by sidestepping it. A churn model never claims to know what would have happened to a particular customer under different policy. It claims to estimate `P(churn | X)` from the joint distribution of `(X, churn)` in the training data. The fundamental problem only bites when the team interprets that prediction as a counterfactual, and the SHAP report on a predictive model invites exactly that misinterpretation. The cross-link from [Module 2.2](../module-2.2-interpretability-and-failure-slicing/) is direct. SHAP describes the model's behavior. The claim that changing a feature would change the outcome by the SHAP value is a counterfactual claim, and the predictive workflow has no defense for it.

The honest consequence is that any causal answer relies on assumptions that imitate what a randomized experiment would have given the team for free. Randomization makes treatment statistically independent of the potential outcomes by design. Observational adjustment tries to recover that independence after the fact, which is why the next two sections spend most of their words on identification rather than estimation. The data does not contain the missing counterfactuals. The framework decides how to fill them in.

## Section 3: Three Frameworks — Potential Outcomes, DAGs, and Instrumental Variables
Causal inference is taught through three frameworks that mature work uses interchangeably depending on the problem. They are not interchangeable in their assumptions, in their notation, or in the audiences that find them natural, and confusing them is a common practitioner failure. A team that draws a DAG and then writes potential-outcomes notation without checking that the two agree is one identification step away from a confident wrong answer.

The Rubin and Neyman potential-outcomes framework is the dominant language in epidemiology, biostatistics, and applied econometrics. It writes the estimand as `E[Y(1) - Y(0)]` directly, defines the assignment mechanism, and reduces causal identification to questions about whether the treated and control distributions can be brought into balance under stated assumptions. The most common identifying assumption is the no-unobserved-confounders assumption, also called ignorability or conditional independence. It says that, conditional on the observed covariates `X`, the treatment assignment `T` is independent of the potential outcomes `(Y(0), Y(1))`. That is the assumption that propensity-score weighting, matching, and outcome regression all rely on, even when the code does not say so out loud.

The Pearl structural-causal-model framework is the dominant language in computer science. It writes the model as a directed acyclic graph in which an edge from `X` to `Y` is a structural commitment that intervening on `X` would shift `Y`'s distribution along that path. The DoWhy documentation states this constraint plainly: the causal graph must be a directed acyclic graph in which an edge `X → Y` implies that `X` causes `Y`. Identification is done graphically, using the backdoor criterion, the front-door criterion, and the do-calculus. The strength of the framework is that it separates substantive assumptions, encoded in the edges, from statistical machinery. The weakness is that the graph itself is a domain-knowledge artifact, and a confidently drawn but wrong DAG produces confidently wrong identifications.

The instrumental-variable framework is the dominant language in econometrics. When neither the no-unobserved-confounders assumption nor a defensible DAG is available, an instrument `Z` that affects `T` but does not affect `Y` except through `T` can identify a local average treatment effect on the compliers. The exclusion restriction, that `Z` has no direct path to `Y` other than through `T`, is the load-bearing assumption and cannot be tested from the data. Strong instruments are rare. Most practitioner uses of the IV framework are hospital randomization in clinical trials, judge or examiner assignment in administrative data, or rare natural experiments such as Mendelian randomization. The framework is powerful when the conditions hold and dangerous when they do not.

Mature work picks the framing that fits the problem rather than insisting on one of them. Some questions translate cleanly into potential-outcomes language but resist a defensible DAG, because the team cannot agree on the structural edges. Some questions translate cleanly into a DAG but resist potential-outcomes notation because the relevant counterfactual is over a vector of interventions, not a scalar. Some questions resist both and only an instrument can rescue the analysis. The cost of mixing them up is high because a backdoor adjustment in DAG language presumes the same structural commitments that the potential-outcomes adjustment would write as ignorability. The two are often equivalent, but the equivalence has to be checked, not assumed.

## Section 4: Identification Before Estimation
The single most important sentence in this module is that identification dominates estimation. A causal estimand is identified, under stated assumptions, when the data the team can observe contains enough information to recover the estimand without any further unobserved quantity. That step is conceptual, not computational. It happens before any model is fit. Once identification is in hand, the estimation step picks among methods that estimate the same identified expression with different efficiency, robustness, and computational cost. If the identification is wrong, no estimator will save the analysis. If the identification is right, even a simple estimator gives a defensible answer, and a flexible estimator gives a more efficient one.

In potential-outcomes language, identification is usually established by the conjunction of three conditions. The first is conditional ignorability: conditional on observed covariates `X`, the treatment is independent of the potential outcomes. The second is positivity, also called overlap: every covariate cell with positive density in the population has both treated and control units, so the estimator is asked to compare like with like. The third is the stable-unit-treatment-value assumption (SUTVA), which says that one unit's treatment does not affect another unit's potential outcomes and that there are no hidden versions of the treatment. Each of these is an assumption, not a measurement. Each of them constrains how far the analysis can travel.

In DAG language, identification is established by the backdoor criterion. The team finds a set of variables `Z` that blocks every backdoor path between `T` and `Y` while opening no collider paths, and adjusts for `Z`. DoWhy's `identify_effect` step automates the search over the supplied graph for valid adjustment sets. The output is a closed-form expression, called the identified estimand, that maps the observable joint distribution to the causal target. Different graphs can yield different identified estimands, and a graph that omits a confounder will yield an identified expression that does not match the truth even though the search procedure ran without error.

In IV language, identification rests on three exclusion-style conditions. The instrument must be relevant, meaning it actually affects treatment. It must satisfy the exclusion restriction, meaning it has no direct effect on the outcome other than through treatment. And it must satisfy independence, meaning it is unrelated to the unmeasured confounders. The first is testable from the data via a first-stage regression. The other two are not testable in the same way and have to be defended by domain knowledge. That is why instrument hunts in industry tend to fail. The available variables that look instrument-shaped usually fail one of the untestable conditions in ways that are hard to expose without a randomized experiment.

> **Pause and predict** — A team is auditing its propensity-score model and proudly reports that the propensity model has an `R^2` of `0.92` on the treatment indicator, almost perfectly predicting who got treated. Is this a sign of strength or a warning?

It is a warning. A propensity model that nearly perfectly predicts treatment means there is little overlap between treated and control units in covariate space, which is a positivity violation. The reweighting estimator divides by the propensity, so cells with very low or very high propensities blow up the variance and produce unstable estimates. The honest reading is that the data does not support a population-level causal estimand for these regions and the team should either trim, redefine the estimand to overlapping support, or accept a much narrower target population.

Sensitivity analysis is the final move that turns identification into a defensible artifact. The Cinelli and Hazlett robustness-value approach, partial-`R^2`-based confounding bounds, and the Rosenbaum bounds family ask how strong an unobserved confounder would have to be to overturn the qualitative conclusion. DoWhy exposes simulation-based, partial-`R^2`-based, and Reisz-estimator-based sensitivity analyses through the same refutation interface used for placebo tests. The output is not a yes-or-no on whether the assumption holds. It is a number that says the analysis is robust to confounders up to some strength, beyond which it would flip. Stakeholders who refuse to accept any uncertainty about identification are usually asking the wrong question. Sensitivity analysis turns the identification gap from a hidden assumption into a quantified one.

## Section 5: Randomization Is the Gold Standard
Randomization is what makes causal inference easy, and any observational method is, in some sense, an attempt to recover what randomization would have given for free. In a randomized controlled trial, treatment assignment is independent of potential outcomes by design, not by assumption. The simple difference in means between treated and control groups is an unbiased estimate of the average treatment effect, the standard error follows from elementary statistics, and identification has a one-line proof.

A randomized experiment is also nearly the only causal-inference setup where the team gets to skip the assumption work. The DAG, the propensity model, the sensitivity analysis, the IV exclusion restriction, all of it can be replaced by the act of flipping a coin at assignment. That is a remarkable concession that any organization with a working A/B-testing platform should not give up casually. When a randomized experiment is feasible, the answer to "should we run an RCT or an observational study?" is almost always to run the RCT.

The qualifier is that randomization solves identification but not deployment. RCTs have edge cases that need their own care. Compliance can break down when participants do not take the treatment they were assigned, in which case the as-treated comparison reintroduces the selection problem and the intent-to-treat estimator answers a slightly different question. Attrition can break the analysis when the units who drop out are not a random subset, which is structurally similar to selection bias and benefits from the same toolkit. External validity is a separate concern: an effect estimated in the experimental population may not transport to the operational population, and the team has to think about what counts as a representative cohort.

The hierarchy in practice is RCT first, observational with named adjustment second, observational with no adjustment never. An RCT, even a small one, beats a much larger observational study in identification because it neutralizes confounders the team did not measure or did not think to measure. The observational study, by contrast, is exposed to every confounder the team forgot. When stakeholders refuse to fund an RCT because "we already have the data," the right answer is that "having the data" and "having an answer" are not the same thing, and the assumption work that observational analysis requires is not free either.

## Section 6: Common Observational Methods
When an RCT is impossible and the question is still causal, the team picks among observational methods that all rely on stronger assumptions in exchange for using only data already in hand. The methods differ in which assumption they lean on hardest, which is the right axis to read this section by.

Propensity-score matching and weighting, in the lineage of Rosenbaum and Rubin's 1983 paper, lean on the no-unobserved-confounders assumption. The propensity score is `e(X) = P(T = 1 | X)`. Matching pairs a treated unit with a control unit at the same propensity. Inverse-propensity weighting reweights the sample so that the treated and control distributions of `X` look the same. Both are valid under conditional ignorability and overlap. Both fail when the propensity model is misspecified, when there are positivity violations, or when an important confounder is unobserved. Modern practice always inspects covariate balance after matching or weighting, because the propensity-score adjustment is supposed to make the two groups comparable on `X` and a residual imbalance is direct evidence the adjustment did not work.

Doubly-robust estimators combine an outcome model and a propensity model into an estimator that is consistent if either of the two is correctly specified. The augmented inverse-propensity-weighted estimator is the canonical example. The robustness is not magic; it does not say one of the models can be arbitrarily wrong. It says that a small mistake in one is partially absorbed if the other is right, which is operationally useful when the team is uncertain which model class is closer to the truth. EconML's `DRLearner` is the production-friendly version of this idea, and it pairs nicely with the cross-fitting machinery from the double-machine-learning literature.

Difference-in-differences is the right tool when the team observes an outcome before and after a policy change in a treated group and a comparable untreated group. The identifying assumption is parallel trends, which says the two groups would have moved in parallel in the absence of treatment. That assumption is untestable from the post-period alone, but pre-period parallelism is a useful diagnostic and the modern literature has generalized the estimator to staggered adoption and event studies. DiD is widely abused in industry when teams treat any pre-post comparison as causal. The parallel-trends premise has to be defended explicitly.

Regression discontinuity exploits sharp threshold-based assignment, where units above a cutoff receive treatment and units below it do not. Just above and just below the cutoff, the units are similar in everything except treatment, and the local effect is identified under a smoothness assumption. This is a beautiful design when it applies, which is mainly in policy evaluation, education research, and rule-based eligibility programs. It does not generalize to settings without a sharp threshold.

Synthetic controls construct a weighted average of untreated units that matches the pre-treatment trajectory of a single treated unit, then attribute the post-treatment difference to the intervention. They are most useful at the geographic or unit level when there are too few treated units for matching to work but the panel is long enough for the synthetic match to be credible. The Abadie line of work formalized the method and its inferential machinery; production teams use it for state-level, region-level, or large-account-level interventions where a true RCT is not feasible.

Each of these methods has an identifying assumption that the team has to defend, not just a hyperparameter. The assumption is the load-bearing piece of the analysis, and the choice of method is largely the choice of which assumption the team is willing to argue for in front of a reviewer.

## Section 7: ML-Flavored Causal Methods
The next family is the one that sits closest to the rest of this track. Modern causal methods use machine learning to estimate nuisance components, propensities, or heterogeneous effects with the flexibility of a gradient-boosted ensemble or a deep network while preserving the identification step. The crucial reminder is that these methods give better estimation, not better identification. A causal forest trained on confounded observational data with no adjustment for the relevant confounders will return a confidently wrong heterogeneous effect, just as a doubly-robust meta-learner will. The flexibility relaxes parametric assumptions about the outcome surface; it does not relax the identification assumption.

Wager and Athey's 2015 paper at `arxiv.org/abs/1510.04342` introduced causal forests as a way to estimate heterogeneous treatment effects with random-forest-based machinery and asymptotically valid confidence intervals. Athey, Tibshirani, and Wager generalized the framework in their 2016 paper at `arxiv.org/abs/1610.01271` under the name generalized random forests, which extends the same honest-tree machinery to a wider class of estimands than treatment effects alone. EconML's `CausalForestDML` is the production implementation that practitioners reach for when the deployment cares about the conditional average treatment effect rather than only the population average.

Chernozhukov and coauthors' 2016 paper at `arxiv.org/abs/1608.00060` introduced double or debiased machine learning. The setup acknowledges that flexible ML estimators of nuisance functions are biased, in the regularization sense, and that naive plug-in estimators inherit that bias. The fix is a Neyman-orthogonal moment combined with cross-fitting: the data is split, nuisance functions are estimated on one fold, the orthogonal residuals are computed on the held-out fold, and the final causal parameter is fit on the orthogonalized residuals. The method delivers root-`n` consistent and asymptotically normal estimates of the parameter of interest even with high-dimensional nuisance models. EconML's `LinearDML` and `NonParamDML` are the practitioner-facing implementations.

Künzel, Sekhon, Bickel, and Yu's 2017 paper at `arxiv.org/abs/1706.03461` introduced the meta-learner family as a way to convert any standard ML regressor into a heterogeneous-effect estimator. The S-learner fits a single model on the joint feature plus treatment, computes the predicted contrast at `T = 1` versus `T = 0`, and reports it. The T-learner fits two separate models, one per treatment arm, and computes the contrast in their predictions. The X-learner is a clever two-stage estimator that handles imbalanced treatment groups by first imputing pseudo-outcomes from the wrong arm and then fitting a CATE model on those pseudo-outcomes. EconML and CausalML both implement these meta-learners with sklearn-compatible APIs, and the choice between them is mostly a function of arm imbalance and the team's tolerance for hyperparameter complexity.

The hard callout for this section is the same callout as for Section 4. Flexible CATE estimators do not remove the identification assumption. They estimate the identified expression more flexibly. If conditional ignorability fails on a high-dimensional set of confounders, a causal forest fit on those covariates will produce a CATE estimate that recovers something, but that something is not the causal effect. The cross-link to [Module 2.2](../module-2.2-interpretability-and-failure-slicing/) is sharp here. SHAPs of a causal-forest estimate describe the model that estimated the CATE, not the causal mechanism, and reading them as causal explanations of the heterogeneity reintroduces the same confusion this module set out to dissolve.

## Section 8: DoWhy and the Four-Step Framework
DoWhy is a Python library for causal inference, currently at version 0.14, that organizes the workflow around four steps. The team first builds a `CausalModel` that names the treatment, outcome, observed covariates, and either a graph or a list of common causes. It then identifies a causal estimand, which yields a closed-form expression in terms of observable quantities. It then estimates that expression with one or more methods. Finally, it refutes the estimate with placebo tests, random-common-cause tests, data-subset tests, and sensitivity analyses. The four-step structure is what makes DoWhy distinctive among causal-inference libraries, and the refutation step is the most operationally important one because most other libraries treat it as the user's homework.

The minimal worked example below builds a synthetic confounded dataset where the true average treatment effect is known to be `1.0`. A confounder `W` affects both treatment `T` and outcome `Y`. Treatment is binary. The naive group difference, ignoring `W`, will overstate the effect because confounder structure makes treated units look better than control units even before treatment is applied.

```python
import numpy as np
import pandas as pd
from dowhy import CausalModel

rng = np.random.default_rng(7)
n = 4000
W = rng.normal(size=n)
T = (rng.uniform(size=n) < (1 / (1 + np.exp(-0.8 * W)))).astype(int)
Y = 1.0 * T + 1.5 * W + rng.normal(scale=1.0, size=n)

df = pd.DataFrame({"W": W, "T": T, "Y": Y})

model = CausalModel(
    data=df,
    treatment="T",
    outcome="Y",
    common_causes=["W"],
)

identified_estimand = model.identify_effect()
print(identified_estimand)
```

The `identify_effect` step prints an identified estimand using the backdoor criterion on the supplied common cause, which says, in plain text, that the average causal effect is the expected value of `Y` given `T` and `W` averaged over the marginal distribution of `W`. That is the closed-form expression every estimator in the next step will try to estimate. A different graph or a missing common cause would give a different identified estimand, and the difference is the entire identification step in code.

The estimation step asks the model to plug a method into the identified expression. Two reasonable choices on this dataset are propensity weighting and outcome regression. Propensity weighting estimates `P(T = 1 | W)`, builds inverse-propensity weights, and computes the weighted mean difference. Linear regression with `T` and `W` as covariates gives an outcome-regression estimate of the same quantity under linearity assumptions.

```python
estimate_psw = model.estimate_effect(
    identified_estimand,
    method_name="backdoor.propensity_score_weighting",
    target_units="ate",
)
print("propensity_score_weighting", round(estimate_psw.value, 3))

estimate_lr = model.estimate_effect(
    identified_estimand,
    method_name="backdoor.linear_regression",
)
print("linear_regression", round(estimate_lr.value, 3))
```

A DoWhy estimate without a refutation is not a finished analysis. The refutation step asks the model whether its answer survives plausible challenges. The placebo refuter replaces the real treatment with a randomly permuted placebo and re-runs the estimator. If the method is not reading noise as effect, the placebo estimate should be close to zero. The random-common-cause refuter adds an irrelevant simulated common cause to the dataset and re-runs the estimator. A robust method's estimate should not change much. The data-subset refuter re-estimates on a random subsample, which checks for unstable behavior driven by a small number of influential points. The unobserved-common-cause refuter introduces a hypothetical confounder of varying strength and reports how strong it would need to be to overturn the conclusion, which is the sensitivity-analysis step in operational form.

```python
refute_placebo = model.refute_estimate(
    identified_estimand,
    estimate_lr,
    method_name="placebo_treatment_refuter",
    placebo_type="permute",
)
print(refute_placebo)

refute_rcc = model.refute_estimate(
    identified_estimand,
    estimate_lr,
    method_name="random_common_cause",
)
print(refute_rcc)

refute_subset = model.refute_estimate(
    identified_estimand,
    estimate_lr,
    method_name="data_subset_refuter",
    subset_fraction=0.8,
)
print(refute_subset)
```

The DoWhy refutation user guide at `https://www.pywhy.org/dowhy/main/user_guide/refuting_causal_estimates/` states the discipline clearly. An analysis that fails any one of these refutations is incorrect and needs to be fixed. The methods are not graded on a curve. A placebo refuter that returns a number close to the original estimate is direct evidence that the estimator is reading structure that is not really there.

> **Pause and decide** — Your DoWhy estimate of the treatment effect on the original data is `0.18`. The placebo-treatment refuter, which randomly permutes the treatment column and re-runs the same estimator, returns `0.16`. What does that result tell you, and what is the appropriate next step?

The result is a near-failure of the placebo test. A correctly behaving estimator on a randomly permuted treatment should return an estimate close to zero, because the permuted treatment has no real relationship to the outcome. Returning `0.16` means the estimator is finding something in the structure of the data that has nothing to do with the original treatment. The honest reading is that the original `0.18` is suspect. The next step is not to publish the `0.18` with a footnote. It is to revisit the identification, consider unmeasured confounding, try a different estimator and confirm or contradict the result, and run an unobserved-common-cause sensitivity analysis to characterize how much hidden confounding the conclusion can absorb.

## Section 9: EconML for Heterogeneous Effects
DoWhy is the right starting point when the question is the average treatment effect with refutation. EconML, currently at version 0.16.0, is the right tool when the question is heterogeneity. EconML's spec at `https://www.pywhy.org/EconML/spec/spec.html` is built around a small number of estimator families. The double-machine-learning family, with `LinearDML`, `SparseLinearDML`, `NonParamDML`, and `CausalForestDML`, fits the orthogonal-moment estimators from the Chernozhukov line of work. The doubly-robust family, with `DRLearner` and its variants, combines outcome and propensity models with the AIPW efficient-influence-function machinery. The meta-learner family, with `TLearner`, `SLearner`, and `XLearner`, wraps any sklearn estimator into a CATE estimator. The orthogonal-random-forest and instrumental-variable families round out the spec for cases where the team needs forest-based heterogeneity or has a credible instrument.

A minimal heterogeneous-effect example reuses the synthetic dataset from Section 8 but adds a feature that makes the effect depend on a covariate. The true effect of treatment on outcome is `0.5 + 1.0 * Z`, so units with high `Z` benefit from treatment and units with low `Z` do not. EconML's `LinearDML` is the simplest orthogonal estimator that recovers this kind of linear heterogeneity, and `CausalForestDML` is the flexible version that does not need the linearity assumption.

```python
import numpy as np
import pandas as pd
from econml.dml import CausalForestDML, LinearDML
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LogisticRegression

rng = np.random.default_rng(13)
n = 6000
Z = rng.normal(size=n)
W = rng.normal(size=n)
T = (rng.uniform(size=n) < (1 / (1 + np.exp(-0.6 * W)))).astype(int)
Y = (0.5 + 1.0 * Z) * T + 1.5 * W + rng.normal(scale=1.0, size=n)

X = Z.reshape(-1, 1)
W_arr = W.reshape(-1, 1)

linear_dml = LinearDML(
    model_y=RandomForestRegressor(n_estimators=300, max_depth=5, random_state=0),
    model_t=LogisticRegression(max_iter=2000),
    discrete_treatment=True,
    random_state=0,
)
linear_dml.fit(Y=Y, T=T, X=X, W=W_arr)
print("LinearDML coef on Z", round(float(linear_dml.coef_[0]), 3))

forest_dml = CausalForestDML(
    model_y=RandomForestRegressor(n_estimators=300, max_depth=5, random_state=0),
    model_t=LogisticRegression(max_iter=2000),
    discrete_treatment=True,
    random_state=0,
)
forest_dml.fit(Y=Y, T=T, X=X, W=W_arr)
cate_at_z = forest_dml.effect(np.array([[-2.0], [0.0], [2.0]]))
print("CausalForestDML effects at Z=-2,0,2", np.round(cate_at_z, 3))
```

The pattern is sklearn-shaped. The team picks a model class for the outcome regression (`model_y`) and a model class for the treatment regression (`model_t`), both fit with cross-fitting under the hood to give the orthogonal moment its statistical guarantees. The fit signature distinguishes the variables whose effect the team wants to estimate (`X`, the covariates over which heterogeneity is reported) from the controls used only as confounder adjustments (`W`). That distinction matters because the spec's identification arguments rely on adjusting for `W`, while the `X` slot is the heterogeneity grid the team will eventually plot or summarize.

EconML pairs naturally with DoWhy. The `CausalModel` in DoWhy can call EconML estimators by passing the full module path as the `method_name` argument to `estimate_effect`, which means the four-step DoWhy pipeline still applies. The team gets the identification step and the refutation step from DoWhy and the heterogeneity-aware estimation from EconML, which is a reasonable production default when the question is "for which subpopulation does this intervention work?".

## Section 10: Uplift Modeling — The Marketing and Recsys Cousin
Uplift modeling is the marketing- and recommender-system-flavored sibling of causal inference. The defining question is which units would respond differently to a treatment than they would to no treatment, which is exactly the conditional treatment effect dressed up in a different vocabulary. The classic operational example is a retention email. The team does not want to send the email to users who would have stayed anyway, because that wastes budget and may even annoy them. The team also does not want to send it to users who will leave regardless of the email, because that wastes budget and does not save them. The valuable cohort is the persuadables, units whose decision to stay is changed by the email. Uplift modeling tries to identify them.

The Uber-maintained CausalML library at `https://causalml.readthedocs.io/` and the EconML meta-learner family both support this workflow. CausalML adds explicit uplift-tree implementations, including the Rzepakowski-Jaroszewicz divergence-based uplift tree, that are designed to split on the criterion that maximizes the difference between treated and control conditional outcomes rather than the more common purity-of-class objective. Practitioner code looks like a meta-learner pattern with an uplift twist:

```python
from causalml.inference.meta import BaseTLearner
from sklearn.ensemble import GradientBoostingRegressor

t_learner = BaseTLearner(
    learner=GradientBoostingRegressor(n_estimators=200, max_depth=3, random_state=0),
)
t_learner.fit(X=X, treatment=T, y=Y)
uplift_scores = t_learner.predict(X=X)
```

The pitfall is the one this module has been repeating. Uplift modeling is causal modeling, and it inherits the same identification responsibility. If the historical "treated" cohort was selected by a non-random process, the uplift estimator picks up that selection along with the true uplift. The cleanest uplift workflows are built on top of randomized historical campaigns, so the assignment mechanism is known. Observational uplift is possible but requires the same identification work as any other observational causal study, and skipping it because the engineering looks like sklearn is a common production failure.

The cross-link to [Module 2.4](../module-2.4-recommender-systems/) is direct. A recommender system that is asked "which item, if shown, would change the user's decision the most?" is asking an uplift question. A recommender that is asked "which item is the user most likely to click given their history?" is asking a prediction question. The two have different optimal models, different data needs, and different evaluation procedures. The offline NDCG winner from a click-through prediction model is not necessarily the uplift winner, because click-through prediction does not separate the persuadables from the would-have-clicked-anyway cohort.

## Section 11: Causal Fairness
Fairness work and causal inference share a foundational instinct. Both ask whether an intervention or alternate world would change the outcome the system produces. [Module 2.6](../module-2.6-fairness-and-bias-auditing/) covered group fairness as the dominant operational frame. Causal fairness, in the lineage of Kusner, Loftus, Russell, and Silva's 2017 paper on counterfactual fairness at `arxiv.org/abs/1703.06856`, sharpens the framing. A decision is counterfactually fair if it would be the same in a counterfactual world where the protected attribute had been different, holding everything else relevant the same. The definition turns fairness into a counterfactual claim, which is exactly the kind of claim this module's machinery is built to evaluate.

Counterfactual fairness has hard advantages. It rules out fairness-through-unawareness, because a model that uses proxies for the protected attribute will produce a different counterfactual prediction even when the protected attribute itself is removed. It surfaces path-specific concerns explicitly. Some causal paths from the protected attribute to the outcome are deemed unfair, such as direct discrimination, while others may be deemed acceptable, such as differences in observed qualifications that the team has chosen to treat as legitimate. The framework forces the team to encode that judgment in the graph rather than leaving it to the metric.

The hard disadvantages are the same disadvantages that face any causal analysis. The DAG has to be drawn, the structural commitments about which paths are unfair have to be defended, and the identification has to hold. In contested deployments, the team often cannot agree on which paths are legitimate and which are not. That is not a flaw of counterfactual fairness. It is a feature: the framework forces normative disagreement to surface in a place where it can be argued explicitly, rather than hiding it in a metric that will quietly encode the disagreement under whichever choice happened to ship.

The cross-link to [Module 2.6](../module-2.6-fairness-and-bias-auditing/) is operational. The group-fairness audit there gives the team a measurement of disparate harm in the world the team observed. The counterfactual-fairness audit here asks whether the model's behavior would change in a counterfactual world where the protected attribute had differed. Both are valid lenses. Mature deployments use the group audit as the primary instrument, because it is measurable from the data, and the counterfactual lens as a structural check, because it forces the team to be explicit about which paths it considers fair.

## Section 12: When Causal Inference Is the Wrong Tool
The discipline of this module's closing sections has been to name when its tool is not the right one. Causal inference is the wrong tool when the deployment question is purely predictive. A churn-risk score, a fraud-detection score, a recommender ranking, an anomaly score, all are predictive deployments where the system does not need to know what would have happened under intervention. The team should ship a calibrated predictive model from [Module 1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/) and stop there.

Causal inference is the wrong tool when the data does not support identification. If there is no defensible DAG, no instrument satisfies the exclusion restriction, no pre-period parallelism is plausible for a difference-in-differences design, and the unmeasured confounders are clearly large, the honest answer is that the data does not contain the answer and no method will conjure it. The temptation to publish an estimate anyway, with a hedging paragraph in the appendix, is exactly how observational analyses end up overruling later randomized experiments. Saying "we cannot identify the effect from this data" is a finished analysis, not a failed one.

Causal inference is the wrong tool when the stakeholders refuse to engage with assumptions. The audit artifact for a causal analysis includes the identification strategy, the named assumptions, the sensitivity-analysis bounds, and the refutation results. If the deployment culture wants only a single point estimate to plug into a slide, the right move is to either rebuild the culture around assumption-aware reasoning or decline the work. A point estimate without an assumption set is a number masquerading as a conclusion.

Causal inference is the wrong tool when randomization is feasible and the team is using observational machinery to avoid the engineering cost of an A/B test. An RCT, even a small one, beats an observational analysis on every identification axis. Teams reach for observational causal machinery in those cases for political reasons rather than methodological ones, and the right answer is to reroute the budget toward an RCT and pay the engineering cost up front rather than the assumption cost at audit time.

## Section 13: The Practitioner Playbook
The mature workflow looks the same whether the deployment is healthcare, finance, marketing, or platform reliability. The first move is to specify the question as a causal one. The team writes the estimand in plain language and confirms that it is an intervention or counterfactual question rather than a predictive one. If the question is predictive, the team stops here and uses the rest of the track.

The second move is to draw the DAG, name the confounders, name the mediators, name the colliders, and check the structural commitments with a domain expert. Mature teams treat the DAG as a contract among engineers, scientists, and domain owners rather than as a private artifact of the modeling code. The graph encodes the substantive assumptions, and the analysis is only as defensible as the graph it stands on.

The third move is to pick the framework that fits the problem. A randomized experiment if randomization is feasible. A potential-outcomes adjustment if the no-unobserved-confounders assumption is defensible on the available covariates. A DAG-based identification if the structure is rich enough to use the backdoor or front-door criterion. An instrumental-variable analysis if a credible instrument is available. The framework decides which assumptions the team is on the hook for, and the choice is explicit rather than implicit.

The fourth move is the DoWhy four-step workflow. Build the `CausalModel`. Run `identify_effect` and read the resulting expression aloud. Estimate with at least two methods so the team can see whether the answer depends heavily on the estimator. Refute with placebo, random common cause, data subset, and unobserved-common-cause sensitivity analysis. The output is not just a point estimate; it is the estimate plus the refutation evidence.

The fifth move is to communicate the assumption set, not just the point estimate. The audit artifact for a causal analysis lists the estimand in plain language, the framework, the identifying assumptions, the chosen estimators, the refutation results, the sensitivity-analysis bound, and the limits of generalization. Stakeholders who only read the headline number will misuse it; the assumption set is what allows future reviewers to recognize when the analysis stops applying.

This playbook is intentionally repetitive. Causal inference is rarely a clever-trick discipline. Most of the work is sequence discipline under stakeholder pressure to skip steps, and the steps that get skipped first are also the steps that decide whether the answer is right.

## Did You Know?
- DoWhy organizes its causal-inference workflow around four causal tasks (effect estimation, attribution, counterfactual estimation, and outcome prediction under intervention) and exposes refutation as a first-class part of the same API as estimation. Source: https://www.pywhy.org/dowhy/main/user_guide/causal_tasks/index.html

- EconML moved from `microsoft/EconML` to `py-why/EconML` in 2023, and the original Microsoft GitHub URL still 301-redirects to the PyWhy organization, which is why citations to the older Microsoft URL still resolve correctly even though the canonical home has changed. Source: https://github.com/py-why/EconML

- DoWhy's refutation user guide tells the practitioner outright that an analysis failing any one of the placebo, random-common-cause, data-subset, dummy-outcome, graph, or sensitivity refutations is incorrect and needs to be fixed, which makes refutation a gate rather than a footnote. Source: https://www.pywhy.org/dowhy/main/user_guide/refuting_causal_estimates/

- The DoWhy library was introduced as an end-to-end Python causal-inference library in the 2020 paper of the same name, and the four-step structure of model-identify-estimate-refute is part of the design rather than a later addition. Source: https://arxiv.org/abs/2011.04216

## Common Mistakes
| Mistake | Why it bites | What to do instead |
| --- | --- | --- |
| Treating SHAP top features as causal drivers | SHAP describes the model, not the world; the predictive method has no machinery for interventions | Restate the question as causal, draw the DAG, and run a DoWhy or EconML analysis on the appropriate target |
| Skipping the DAG or identification step and going straight to estimation | A flexible estimator under the wrong identification produces a confidently wrong number that looks rigorous | Treat identification as the load-bearing step and only reach for an estimator after the identified expression is written down |
| Using propensity matching without checking covariate balance afterward | Matching is supposed to make groups comparable on `X`; residual imbalance is direct evidence the adjustment did not work | Inspect standardized mean differences across groups after matching and re-match or reweight if balance is poor |
| Confusing CATE estimation flexibility with identification rigor | Causal forests and meta-learners give better estimates of the identified expression, not better identifications | State the identification assumptions explicitly and recognize that flexible CATE methods inherit them rather than relax them |
| Citing physics paper `arxiv 1610.04018` as the causal-forests paper | The correct identifier is `arxiv 1510.04342` (Wager and Athey); `1610.04018` is a paper about colloidal joints | Use `1510.04342` for causal forests and `1610.01271` for the generalized-random-forests extension |
| Running DoWhy's `estimate_effect` and stopping before `refute_estimate` | An estimate that has not faced the placebo, random-common-cause, and sensitivity refuters is not a finished analysis | Make refutation a non-skippable phase of the pipeline, and treat any near-failure of a refuter as a reason to revisit the identification |
| Reporting an observational point estimate without naming the assumption set | Stakeholders treat the headline number as a fact and use it to overrule later randomized evidence | Ship the estimate with the framework, the identifying assumptions, the sensitivity bound, and the refutation results as a single artifact |
| Picking a framework by personal preference rather than by what the problem permits | A potential-outcomes adjustment without a defensible ignorability is no better than a DAG without defensible edges | Pick the framework whose assumptions the team is willing and able to argue for in front of a reviewer |

## Quiz
1. A product manager points at a SHAP report from a churn model and asks whether reducing `last_month_revenue` by ten percent will reduce churn by the SHAP value. What is the right response?

<details><summary>Answer</summary>
SHAP describes how the trained model uses the feature it was given; it does not establish that an intervention on the feature in the world would change the outcome by the SHAP value. The question being asked is causal. The honest move is to either run a randomized experiment that varies `last_month_revenue`-related policy or to build an observational causal analysis with named confounders, identification, estimation, and refutation. The SHAP plot cannot answer the question, no matter how rich it looks.
</details>

2. A team's propensity model achieves an `R^2` of `0.92` on the treatment indicator. Is this good news for downstream IPW estimation?

<details><summary>Answer</summary>
It is bad news. A propensity model that nearly perfectly predicts treatment means there is little overlap between treated and control units, which is a positivity violation. IPW divides by the propensity, so very high or very low propensities create units with extreme weights and unstable estimates. The honest options are to trim the sample to overlapping support, redefine the estimand to a narrower population where overlap exists, or accept that the data does not support a clean ATE estimate.
</details>

3. You estimate a treatment effect of `0.18` with DoWhy's linear-regression backdoor estimator. The placebo-treatment refuter, run on a permuted treatment column, returns `0.16`. What does that imply, and what should the team do?

<details><summary>Answer</summary>
A correctly behaving estimator on a permuted treatment should return a number close to zero, because the permuted treatment carries no real signal. A placebo result of `0.16`, close to the original `0.18`, means the estimator is reading structure in the data that has nothing to do with the actual treatment. The original estimate is suspect. The next step is to revisit identification, consider unmeasured confounding, try a different estimator and compare, and run an unobserved-common-cause sensitivity analysis to characterize how robust the conclusion is.
</details>

4. A team finds an instrument that strongly predicts treatment in the first stage. Is the instrument therefore valid?

<details><summary>Answer</summary>
No. Relevance, the first-stage condition, is testable from the data and is necessary but not sufficient. The other two IV conditions, the exclusion restriction and independence from unmeasured confounders, are not testable in the same way and have to be defended by domain knowledge. A relevant instrument that violates exclusion gives a confidently wrong answer just as surely as no instrument at all. The team has to argue the untestable conditions as carefully as it tests the relevance condition.
</details>

5. Your CATE estimates from `CausalForestDML` look smooth and interpretable, but a critic says the model could be wrong. What is the strongest version of that critique, and how do you respond?

<details><summary>Answer</summary>
The strongest version of the critique is that flexible CATE estimators do not relax the identification assumption. They estimate the identified expression more flexibly. If the team did not adjust for an important confounder, the causal forest will produce a smooth heterogeneous-effect surface that looks principled and is wrong in a structured way. The response is to state the identification assumption explicitly, name the adjustment set, run sensitivity analysis for unmeasured confounders, and demonstrate that the qualitative conclusion survives the refutation suite.
</details>

6. A growth team observes that customers who received a retention email had a much lower churn rate than customers who did not. They want to ship the email to everyone. What identifying assumption are they implicitly relying on, and is it likely to hold?

<details><summary>Answer</summary>
They are implicitly relying on the no-unobserved-confounders assumption: that the difference in churn between recipients and non-recipients is attributable to the email, conditional on observed covariates. It is unlikely to hold here. The email was probably sent to engaged users, while non-recipients include disengaged users who were already at higher churn risk regardless of any email. The naive group difference confounds the email's effect with the assignment mechanism. The right next step is either a randomized experiment for the next campaign or a careful observational adjustment with a defensible set of confounders and a refutation suite.
</details>

7. When does counterfactual fairness give the team something that a group-fairness audit does not, and when does it not?

<details><summary>Answer</summary>
Counterfactual fairness asks whether the model's prediction would change in a counterfactual world where the protected attribute had been different, which forces the team to make path-specific structural commitments about which causal paths are considered fair and which are not. It rules out fairness-through-unawareness because proxy variables still drive different counterfactual predictions even when the protected attribute is removed. It does not give the team something a group audit does not when the structural commitments cannot be defended, which is the common production case. In that case the framework still surfaces the disagreement explicitly, but it does not resolve it. Mature deployments use the group audit as the primary instrument and the counterfactual lens as a structural check.
</details>

8. Under what conditions should the team decline to estimate a causal effect at all?

<details><summary>Answer</summary>
Three conditions justify declining. First, the data does not support identification: there is no defensible DAG, no usable instrument, no parallel-trends story, and the unmeasured confounders are large. Second, the stakeholders refuse to engage with the assumption set, treating the analysis as a one-number request that bypasses identification. Third, randomization is feasible and the team is using observational machinery to avoid the engineering cost. In all three cases the responsible answer is that the data does not contain the answer (case one), the deployment culture is not ready to use the answer (case two), or the answer should come from an RCT (case three).
</details>

## Hands-On Exercise
- [ ] Step 0: Import the standard numerical stack, scikit-learn, and the DoWhy and EconML pieces used in this module. The CausalML import is optional and only needed for Step 6.

```python
import numpy as np
import pandas as pd
from dowhy import CausalModel
from econml.dml import CausalForestDML, LinearDML
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LogisticRegression
```

- [ ] Step 1: Build a synthetic confounded dataset where the true average treatment effect is known. The confounder `W` affects both treatment and outcome. The treatment effect is constant at `1.0` for the ATE part, with an extra `1.0 * Z` heterogeneity term so the CATE varies by covariate `Z`.

```python
rng = np.random.default_rng(11)
n = 5000
W = rng.normal(size=n)
Z = rng.normal(size=n)
T = (rng.uniform(size=n) < (1 / (1 + np.exp(-0.7 * W)))).astype(int)
Y = (1.0 + 1.0 * Z) * T + 1.5 * W + rng.normal(scale=1.0, size=n)

df = pd.DataFrame({"W": W, "Z": Z, "T": T, "Y": Y})

print("naive group difference (biased)", round(df.groupby("T")["Y"].mean().diff().iloc[-1], 3))
```

- [ ] Step 2: Build a `CausalModel`, run `identify_effect`, and read the identified estimand aloud. The common cause is `W`; `Z` enters as part of the heterogeneity grid in later steps but the simplest backdoor adjustment uses `W` as the confounder.

```python
model = CausalModel(
    data=df,
    treatment="T",
    outcome="Y",
    common_causes=["W"],
)
identified_estimand = model.identify_effect()
print(identified_estimand)
```

- [ ] Step 3: Estimate the ATE with two methods so you can see whether the answer depends heavily on the estimator. Use propensity-score weighting and linear regression for the backdoor adjustment.

```python
estimate_psw = model.estimate_effect(
    identified_estimand,
    method_name="backdoor.propensity_score_weighting",
    target_units="ate",
)
estimate_lr = model.estimate_effect(
    identified_estimand,
    method_name="backdoor.linear_regression",
)
print("psw", round(estimate_psw.value, 3))
print("lr", round(estimate_lr.value, 3))
```

- [ ] Step 4: Refute the linear-regression estimate with at least two refuters. The placebo refuter should return a number close to zero. The random-common-cause refuter should leave the estimate roughly unchanged.

```python
refute_placebo = model.refute_estimate(
    identified_estimand,
    estimate_lr,
    method_name="placebo_treatment_refuter",
    placebo_type="permute",
)
refute_rcc = model.refute_estimate(
    identified_estimand,
    estimate_lr,
    method_name="random_common_cause",
)
print(refute_placebo)
print(refute_rcc)
```

- [ ] Step 5: Switch to EconML to estimate the conditional average treatment effect over `Z`. `LinearDML` recovers the linear coefficient on `Z` (true value is `1.0`). `CausalForestDML` recovers the heterogeneity nonparametrically and you can sample CATE values at chosen `Z` points.

```python
X_grid = Z.reshape(-1, 1)
W_arr = W.reshape(-1, 1)

linear_dml = LinearDML(
    model_y=RandomForestRegressor(n_estimators=300, max_depth=5, random_state=0),
    model_t=LogisticRegression(max_iter=2000),
    discrete_treatment=True,
    random_state=0,
)
linear_dml.fit(Y=df["Y"].values, T=df["T"].values, X=X_grid, W=W_arr)
print("LinearDML coef on Z", round(float(linear_dml.coef_[0]), 3))

forest_dml = CausalForestDML(
    model_y=RandomForestRegressor(n_estimators=300, max_depth=5, random_state=0),
    model_t=LogisticRegression(max_iter=2000),
    discrete_treatment=True,
    random_state=0,
)
forest_dml.fit(Y=df["Y"].values, T=df["T"].values, X=X_grid, W=W_arr)
print(
    "CausalForestDML CATE at Z=-2,0,2",
    np.round(forest_dml.effect(np.array([[-2.0], [0.0], [2.0]])), 3),
)
```

- [ ] Step 6 (optional): Reframe the problem as an uplift question and use a meta-learner to score units by their estimated incremental effect of treatment. This step uses CausalML's `BaseTLearner` and is the bridge to [Module 2.4](../module-2.4-recommender-systems/) when the recommender question is "which item changes the user's decision the most?" rather than "which item is the user most likely to click?".

```python
from causalml.inference.meta import BaseTLearner
from sklearn.ensemble import GradientBoostingRegressor

t_learner = BaseTLearner(
    learner=GradientBoostingRegressor(n_estimators=200, max_depth=3, random_state=0),
)
t_learner.fit(X=X_grid, treatment=df["T"].values, y=df["Y"].values)
uplift_scores = t_learner.predict(X=X_grid)
print("uplift score quantiles", np.round(np.quantile(uplift_scores, [0.1, 0.5, 0.9]), 3))
```

- [ ] Step 7: Write a short paragraph naming the estimand, the identification assumption, the chosen estimator, the refutation results, and the limits of the analysis. Compare the naive group difference from Step 1 to the DoWhy ATE estimate from Step 3 and explain why they differ. State whether you would publish the result, request more data, or fall back to an RCT.

### Completion Check
- [ ] I named the estimand in plain language before running any estimator.
- [ ] I ran `identify_effect` and read the identified expression rather than relying on the estimator output alone.
- [ ] I estimated the same effect with at least two methods and compared them.
- [ ] I refuted the estimate with at least two refuters, including the placebo-treatment refuter, and acted on the result if a refutation failed.
- [ ] I separated the average-treatment-effect question from the heterogeneous-effect question and used DoWhy for the first and EconML for the second.
- [ ] I wrote down the assumption set as part of the analysis artifact, not just the point estimate.

## Sources
- https://www.pywhy.org/dowhy/main/
- https://www.pywhy.org/dowhy/main/user_guide/
- https://www.pywhy.org/dowhy/main/user_guide/modeling_causal_relations/index.html
- https://www.pywhy.org/dowhy/main/user_guide/causal_tasks/index.html
- https://www.pywhy.org/dowhy/main/user_guide/causal_tasks/estimating_causal_effects/index.html
- https://www.pywhy.org/dowhy/main/user_guide/refuting_causal_estimates/index.html
- https://www.pywhy.org/dowhy/main/example_notebooks/dowhy_simple_example.html
- https://www.pywhy.org/dowhy/main/example_notebooks/sensitivity_analysis_testing.html
- https://github.com/py-why/dowhy
- https://www.pywhy.org/EconML/
- https://www.pywhy.org/EconML/spec/spec.html
- https://www.pywhy.org/EconML/spec/api.html
- https://www.pywhy.org/EconML/spec/causal_intro.html
- https://www.pywhy.org/EconML/spec/estimation/dml.html
- https://www.pywhy.org/EconML/spec/estimation/forest.html
- https://www.pywhy.org/EconML/spec/estimation/metalearners.html
- https://github.com/py-why/EconML
- https://causal-learn.readthedocs.io/
- https://github.com/py-why/causal-learn
- https://causalml.readthedocs.io/en/latest/about.html
- https://causalml.readthedocs.io/en/latest/methodology.html
- https://github.com/uber/causalml
- https://arxiv.org/abs/1510.04342
- https://arxiv.org/abs/1610.01271
- https://arxiv.org/abs/1608.00060
- https://arxiv.org/abs/1706.03461
- https://arxiv.org/abs/1703.06856
- https://arxiv.org/abs/2011.04216

## Next Module
This module closes the Tier-2 sequence of the Machine Learning track. The next conceptual move belongs to the Reinforcement Learning track, where Module 2.1, Offline RL and Imitation Learning, takes the same separation between observational and interventional data into the sequential-decision setting and asks how to learn a policy from logged interactions when running new experiments is unsafe or impossible. That module is forthcoming under issue #677, which closes once Module 2.7 here and the RL Tier-2 module both land. The forward reference is plain text rather than a markdown link because the destination module has not shipped yet, and the surrounding modules in this track already point to causal inference as the discipline that picks up where SHAP, conformal coverage, and group-fairness audits leave off.
