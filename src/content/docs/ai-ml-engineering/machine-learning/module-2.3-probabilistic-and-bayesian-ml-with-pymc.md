---
title: "Probabilistic & Bayesian ML with PyMC"
description: "Use PyMC to model uncertainty instead of worshipping point estimates, read posterior diagnostics before trusting summaries, and recognize where Bayesian linear and hierarchical models earn their extra compute."
slug: ai-ml-engineering/machine-learning/module-2.3-probabilistic-and-bayesian-ml-with-pymc
sidebar:
  order: 23
---

> Track: AI/ML Engineering | Complexity: `[MEDIUM]` | Time: 90-110 minutes
> Prerequisites: [Module 1.2: Linear and Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/), [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/), and [Module 1.12: Time Series Forecasting](../module-1.12-time-series-forecasting/). This module also sets up a plain-text forward reference to Module 2.5, conformal prediction and uncertainty quantification.

The on-call story for Bayesian ML rarely starts with a philosophical argument
about priors. It starts with a team that has already shipped competent
frequentist models, has read a few excited posts about PyMC, and decides that
probabilistic programming must mean better predictions. A week later the team
has a posterior for every coefficient, a trace plot screenshot in a slide deck,
and a product manager asking whether a ninety-percent credible interval means
the model is ninety percent accurate. The predictions are not clearly better,
the compute bill is much worse, and nobody can explain what the interval is
for.

The second hook is harsher because it is entirely self-inflicted. Another team
fits a PyMC model, copies the posterior means into a report, and only later
notices that several parameters have `r_hat` above the accepted threshold and
that the sampler reported divergences. They read posterior numbers without
checking diagnostics first. That mistake is more serious than choosing the
wrong prior, because it means the model summary was never trustworthy enough to
interpret in the first place.

This module is the correction. It teaches Bayesian ML as a practical choice
about uncertainty, pooling, diagnostics, and communication. It does not ask you
to become a statistical purist. It asks you to know when PyMC earns its cost,
when it does not, and how to keep the resulting workflow honest in the same
way that [Module 2.1: Class Imbalance & Cost-Sensitive Learning](../module-2.1-class-imbalance-and-cost-sensitive-learning/)
kept metrics honest and [Module 2.2: ML Interpretability + Failure Slicing](../module-2.2-interpretability-and-failure-slicing/)
kept explanations honest.

## Learning Outcomes

By the end of this module, a practitioner will be able to:

1. **Diagnose** whether a modeling problem actually needs Bayesian uncertainty,
   hierarchical pooling, or principled small-data behavior rather than simply a
   regularized frequentist baseline from [Module 1.2: Linear and Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/).
2. **Explain** the Bayesian frame well enough to distinguish priors,
   likelihoods, posteriors, posterior predictive distributions, and the
   difference between credible intervals and confidence intervals from
   [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/).
3. **Implement** Bayesian linear and hierarchical models in PyMC v5, sample
   them with NUTS, and read `az.summary` outputs for `r_hat`,
   `ess_bulk`, `ess_tail`, and divergence counts before discussing results.
4. **Compare** MCMC and ADVI responsibly, including the canonical warning that
   variational inference tends to underestimate posterior spread even when point
   locations look acceptable.
5. **Decide** when Bayesian modeling is the wrong tool because point prediction
   is enough, compute is constrained, or a faster frequentist uncertainty method
   such as Module 2.5's conformal prediction would serve the deployment better.

## Why This Module Matters

The PyMC overview describes the library as "an open source probabilistic
programming framework" that uses automatic differentiation through PyTensor:
https://www.pymc.io/projects/docs/en/stable/learn/core_notebooks/pymc_overview.html
That sentence is useful because it says what PyMC actually is. It is a
framework for writing probability models and computing with them. It is not a
guarantee of better leaderboard numbers. That distinction is the spine of this
module.

The canonical pitfall list is short and worth naming directly. **Bayesian ML is
for uncertainty, not always for better point predictions.** Prior choice
matters most in small-data or weakly identified settings, not in every mature
dataset. **R-hat / ESS / divergences are non-negotiable diagnostics**, which
means `r_hat <= 1.01`, effective sample size of at least `400` per chain, and
zero divergences before you trust a summary table. **Hierarchical models are the
canonical Bayesian win.** **Bayesian costs 10-100x compute, pay only when
uncertainty matters.** **ADVI / VI underestimates posterior variance, so use VI
for prototyping, MCMC for production.** And if the real need is prediction
intervals under a strict compute budget, Module 2.5's conformal prediction is a
frequentist alternative rather than a philosophical rival.

Most production confusion around Bayesian ML is not caused by Bayes' rule
itself. It comes from teams using Bayesian tooling to answer the wrong
question. If the operational question is "which model gives the lowest point
MSE under a fixed latency budget," a Ridge regression from
[Module 1.2: Linear and Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/)
is often the more disciplined answer. If the operational question is "how much
uncertainty should we assign to this coefficient, this group effect, or this
forecast path," then PyMC becomes a serious engineering tool rather than an
academic ornament.

## Section 1: Why Bayesian ML in 2026

Bayesian ML sits in an awkward place in modern practice because its public
reputation is split between two stories. One story says Bayesian methods are
intellectually cleaner because every unknown quantity becomes a distribution.
The other story says Bayesian methods are impractical because they are slow,
hard to debug, and difficult to explain to non-specialists. Both stories are
partly true, and neither is useful by itself.

The practical reason teams still adopt Bayesian modeling in 2026 is not that
they have forgotten how to train good point estimators. It is that some
decisions are brittle when reduced to a single number. A fraud model may need a
credible interval for the fraud rate in a thin cohort. A pricing model may need
uncertainty around elasticity estimates before a policy change. A healthcare
workflow may need principled pooling across hospitals where some sites have far
less data than others. A forecasting problem may need uncertainty bands around
future trajectories, which is where the ideas in
[Module 1.12: Time Series Forecasting](../module-1.12-time-series-forecasting/)
meet Bayesian inference naturally.

The wrong reason to adopt Bayesian modeling is a vague hope that it will reveal
hidden predictive power that regularized frequentist models somehow left on the
table. Sometimes the posterior mean of a Bayesian linear model is extremely
close to the coefficient estimate you would get from a regularized linear model
in sklearn. That is not a failure of Bayes. It is evidence that the data is
informative enough that the extra benefit is not point accuracy but quantified
uncertainty.

This is why the thesis needs to be stated plainly: **Bayesian ML is for
uncertainty, not always for better point predictions**. If you remember one
sentence from this module, make it that one. It protects you from the most
common overclaim and also from the opposite mistake of dismissing Bayesian
modeling because it did not magically improve mean squared error.

The second reason Bayesian ML remains relevant is that partial pooling solves a
class of problems that frequentist workflows often handle awkwardly. If you
estimate a separate effect for every store, hospital, product family, or region,
small groups become unstable. If you pool all groups into one effect, you erase
real heterogeneity. The middle ground is a hierarchical model that lets groups
share information without pretending they are identical. That is not a niche
benefit. It is one of the most reliable places where the extra machinery pays
rent.

Bayesian modeling also remains easy to misuse. Stakeholders often hear a
credible interval as if it were a guarantee of decision correctness. The right
posture is selective use: pay the computational and interpretive cost only when
the uncertainty information changes a real decision.

## Section 2: The Bayesian Frame, Briefly

The compact version of the Bayesian frame is the formula every practitioner has
seen and too many treat as a slogan:

`Posterior ∝ Likelihood × Prior`

That formula matters because it tells you what the model is doing at a high
level. The prior expresses what parameter values were plausible before seeing
the current data. The likelihood expresses how probable the observed data is
under different parameter settings. The posterior combines the two into an
updated distribution over unknown quantities after the data has been observed.

This does not mean the prior always dominates the answer. In many practical
settings with moderate or large data and weakly informative priors, the data
pulls the posterior strongly enough that the prior mostly acts as regularization
and boundary control. The prior is still present. It is simply not the dramatic
villain or hero that bayesian debates often make it out to be.

The posterior is not even the final operational object in many workflows. The
posterior predictive distribution is. That distribution answers a more applied
question: given what we have learned about the parameters, what data would we
expect to observe next? This is the distribution you use for predictive
intervals, scenario checks, and posterior predictive diagnostics. It is the
closest Bayesian analogue to the calibration and prediction-discipline concerns
from [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/).

The credible-versus-confidence distinction is worth being precise about because
it is one of the first things stakeholders ask.

| Interval | Operational reading | Common misuse |
| --- | --- | --- |
| Credible interval | Given the model and data, the parameter plausibly lies in this range with stated posterior probability | Treating the model assumptions as irrelevant |
| Confidence interval | Over repeated samples, intervals built this way contain the true parameter at the stated frequency | Reading a single interval as a direct parameter probability statement |

This table is not a scorecard. It is a translation aid. Bayesian intervals are
often easier for stakeholders to read because the language lines up with how
people naturally talk about uncertainty. The danger is that they become easier
to over-trust. A beautifully interpretable credible interval is still only as
good as the model, the prior, and the sampler diagnostics.

In a sklearn workflow the model often feels like a function that emits a point
prediction. In a PyMC workflow the model is a joint probability structure over
parameters and observations, and the point estimate is only one summary of it.

## Section 3: Priors Without Ritual

The cultural reputation of priors is worse than the practical reality. Teams
that are new to Bayesian modeling often treat the prior as a dangerous place
where subjectivity seeps into an otherwise objective pipeline. Teams that are
too comfortable with Bayesian language sometimes act as if clever priors can
rescue weak data. Both instincts are unhelpful.

In everyday applied work, the prior is usually serving one of three roles. It
can encode genuine domain knowledge. It can weakly regularize the model away
from absurd values. Or it can stabilize a weakly identified problem that would
otherwise wander into pathological parameter regions. Those are all legitimate.
What is not legitimate is hand-tuning priors until the posterior tells a story
you wanted in advance.

Weakly informative priors are the normal default for practical PyMC work. A
`Normal(0, 1.5)` prior on standardized regression coefficients is not claiming
that coefficients must be tiny. It is saying that wildly large coefficients are
unlikely absent strong evidence. A `HalfNormal(1.0)` prior on a residual scale
parameter is not a metaphysical statement about noise. It is a guardrail that
keeps the model in a numerically sensible range while still allowing the data to
move it.

Where priors matter most is exactly where you would expect disciplined
regularization to matter in frequentist workflows: small data, high collinearity,
hierarchical variance components, separation problems, and models where the
likelihood does not by itself identify the parameters clearly. In these
regimes, priors do not merely decorate the analysis. They determine whether the
posterior is sensible.

> **Pause and predict** — You have twelve observations, three correlated
> predictors, and a weak signal. Will the posterior be mostly data-driven or
> mostly shaped by your weakly informative priors? (Answer: mostly shaped by the
> combination of both, with the priors mattering much more than they would in a
> large dataset. With such thin data and collinearity, the likelihood is not
> sharp enough to dominate. This is where prior choice is consequential and why
> "the data swamps the prior" is not a universal slogan.)

The phrase "the data swamps the prior" is best treated as a conditional claim.
It is often true with enough clean data and well-scaled predictors. It is often
false precisely where practitioners most want uncertainty estimates: sparse
groups, partial pooling, rare events, and edge-case forecasting segments.

Improperly broad priors are not neutral. A giant uniform prior over an absurd
range can make sampling harder, hide scaling issues, and create a false sense of
objectivity. The operational question is not "did I eliminate subjectivity?" It
is "did I choose a prior that is weakly informative, computationally stable, and
defensible for the scale of this problem?"

The prior conversation also becomes easier when you standardize features. In
[Module 1.2: Linear and Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/)
you learned that scaling makes coefficient regularization interpretable. The
same idea helps here. A coefficient prior on standardized predictors has a
cleaner meaning and is easier to communicate than the same prior on wildly
different raw scales.

Priors deserve documentation, not drama. Name the family, explain whether it is
domain-driven or weakly informative, and say where it matters most. That level
of clarity is almost always enough for an internal engineering report.

## Section 4: PyMC the Library

PyMC matters in this module not as a brand but as a workflow. The core PyMC
overview page frames it as a Python probabilistic programming framework with a
PyTensor computational backend:
https://www.pymc.io/projects/docs/en/stable/learn/core_notebooks/pymc_overview.html
That description explains why the library feels different from sklearn. You are
not just calling a trainer on an estimator object. You are declaring a
probabilistic graph and then asking the library to perform inference over it.

The basic structure is always the same. You open a `with pm.Model() as model:`
context. Inside it you define stochastic variables such as priors and latent
effects, deterministic relationships such as a linear predictor, and observed
variables that tie the model to data. The model context becomes a container for
all these named random variables and their computational relationships.

PyMC's distribution API is the grammar of that declaration:
https://www.pymc.io/projects/docs/en/stable/api/distributions.html
`pm.Normal`, `pm.HalfNormal`, `pm.Bernoulli`, `pm.Poisson`, and their relatives
play the same role that distributional assumptions played implicitly in earlier
modules. Here they are written directly in code.

`pm.Data` and `pm.MutableData` are important because they separate model
structure from specific arrays. A common pattern is to define a model with data
containers and later swap those inputs to generate posterior predictive samples
for new points. This makes the model reusable in a way that feels more like a
true modeling object and less like a one-shot fitting routine.

The sampling API is equally central:
https://www.pymc.io/projects/docs/en/stable/api/generated/pymc.sample.html
The default mental model should be that `pm.sample` with multiple chains and
tuning iterations is the serious inference path, not a decorative extra after a
point estimate. PyMC's samplers documentation also makes it clear that NUTS is
the default workhorse for continuous models:
https://www.pymc.io/projects/docs/en/stable/api/samplers.html

ArviZ is the other half of the working stack:
https://python.arviz.org/en/stable/
PyMC gives you the model and inference engine. ArviZ gives you the summary
tables, trace plots, posterior plots, and a standard data structure for
inspection. If a team says it is "doing Bayesian modeling" but never opens
`az.summary` or `az.plot_trace`, it is probably doing posterior theater rather
than Bayesian workflow.

One of the cleanest habits you can build early is to think in named variables
and diagnostics rather than in magical fitting calls. Clear names make the
posterior reviewable by other engineers.

## Section 5: Bayesian Linear Regression

Bayesian linear regression is the right first example because it exposes the
tradeoff honestly. It is conceptually familiar if you already know regression
from [Module 1.2: Linear and Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/),
yet it immediately shows the Bayesian difference: coefficients, residual scale,
and predictions are all distributions rather than single fitted values.

The wrong way to pitch Bayesian linear regression is as a superior replacement
for Ridge regression. On many tabular problems the posterior mean predictions of
the two models will be very similar. The right pitch is that the Bayesian model
also tells you how uncertain those coefficients and predictions are, assuming
your model and inference are sound.

```python
import numpy as np
import pymc as pm
import arviz as az
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split

rng = np.random.default_rng(9)
X = rng.normal(size=(240, 2))
beta_true = np.array([1.4, -2.1])
y = 0.6 + X @ beta_true + rng.normal(scale=0.7, size=240)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=9
)

ridge = Ridge(alpha=1.0)
ridge.fit(X_train, y_train)
print("ridge test mse:", round(mean_squared_error(y_test, ridge.predict(X_test)), 3))

with pm.Model() as linear_model:
    X_data = pm.Data("X_data", X_train)
    y_data = pm.Data("y_data", y_train)

    alpha = pm.Normal("alpha", mu=0.0, sigma=2.0)
    beta = pm.Normal("beta", mu=0.0, sigma=1.5, shape=X_train.shape[1])
    sigma = pm.HalfNormal("sigma", sigma=1.0)

    mu = alpha + pm.math.dot(X_data, beta)
    pm.Normal("obs", mu=mu, sigma=sigma, observed=y_data)

    idata = pm.sample(
        draws=2000,
        tune=2000,
        chains=4,
        target_accept=0.95,
        random_seed=9,
    )

summary = az.summary(idata, var_names=["alpha", "beta", "sigma"])
print(summary[["mean", "sd", "hdi_3%", "hdi_97%", "ess_bulk", "r_hat"]])
```

The point of this block is not that the Bayesian model beats Ridge on test MSE.
It often will not. The point is that the PyMC model gives you posterior
intervals for `alpha`, `beta`, and `sigma`, and `az.summary` gives you the
diagnostics needed before those intervals deserve any trust. If `r_hat` is above
`1.01` or effective sample sizes are thin, the posterior table is not ready for
presentation no matter how elegant the model looks.

This is also where the canonical tradeoff becomes concrete. The Ridge baseline
fits almost instantly. The PyMC model may take far longer because it is
producing samples from a posterior rather than a single optimum. That slower
path is justified only if the uncertainty information changes an actual
downstream decision.

Bayesian linear regression is therefore best treated as a controlled comparison.
If no one will use the intervals, you likely did extra compute for little
benefit.

## Section 6: Hierarchical Models Are the Canonical Bayesian Win

If Bayesian linear regression is the familiar entry point, hierarchical modeling
is the section where the whole approach starts to earn its reputation. **This is
the canonical Bayesian win.** The reason is partial pooling. Separate each group
fully and small groups become noisy. Pool everything and real group differences
vanish. A hierarchical model lets group estimates borrow strength from one
another while still varying.

This matters anywhere groups have uneven sample sizes. Think hospitals,
districts, stores, languages, products, or customer segments. The groups with
little data should not be allowed to swing wildly on noise, but they also should
not be flattened into the global mean as if the group identity carries no real
signal.

| Pooling strategy | What it assumes | Typical failure |
| --- | --- | --- |
| Complete pooling | All groups share the same effect | Misses real heterogeneity |
| No pooling | Each group stands alone | Small groups become unstable |
| Partial pooling | Groups differ but are related | Requires a real hierarchical model |

The logic also connects naturally to [Module 1.12: Time Series Forecasting](../module-1.12-time-series-forecasting/).
Many forecasting problems are grouped time series in disguise. You may want
store-level or region-level effects that share strength over time without
pretending each series is independent or identical. Hierarchical Bayesian models
make that structure explicit.

```python
import numpy as np
import pymc as pm
import arviz as az

rng = np.random.default_rng(21)
G = 8
group_sizes = np.array([10, 14, 18, 22, 30, 36, 42, 54])
group_idx = np.repeat(np.arange(G), group_sizes)
x = rng.normal(size=group_idx.size)

true_group_intercepts = np.array([-1.2, -0.8, -0.1, 0.2, 0.5, 0.9, 1.3, 1.6])
y = (
    true_group_intercepts[group_idx]
    + 0.7 * x
    + rng.normal(scale=0.6, size=group_idx.size)
)

raw_group_means = np.array([y[group_idx == g].mean() for g in range(G)])
print("no-pooling means:", np.round(raw_group_means, 2))

with pm.Model() as hierarchical_model:
    x_data = pm.Data("x_data", x)
    g_data = pm.Data("g_data", group_idx)

    mu_a = pm.Normal("mu_a", mu=0.0, sigma=1.5)
    sigma_a = pm.HalfNormal("sigma_a", sigma=1.0)
    a_offset = pm.Normal("a_offset", mu=0.0, sigma=1.0, shape=G)
    a = pm.Deterministic("a", mu_a + a_offset * sigma_a)

    beta = pm.Normal("beta", mu=0.0, sigma=1.0)
    sigma = pm.HalfNormal("sigma", sigma=1.0)
    mu = a[g_data] + beta * x_data

    pm.Normal("obs", mu=mu, sigma=sigma, observed=y)

    idata_h = pm.sample(
        draws=2000,
        tune=2000,
        chains=4,
        target_accept=0.95,
        random_seed=21,
    )

group_summary = az.summary(idata_h, var_names=["a"])
print(group_summary[["mean", "hdi_3%", "hdi_97%", "ess_bulk", "r_hat"]])
```

The important comparison is between the raw group means and the posterior means
for `a`. Small groups get pulled toward the shared population mean because the
model has learned that group intercepts come from a common distribution. Large
groups resist that shrinkage because they have enough local evidence. That is
partial pooling in operational form.

This is why "hierarchical models are the canonical Bayesian win" is more than a
slogan. They solve a real estimation problem in a way that is elegant,
defensible, and often superior to ad hoc smoothing rules. When a team asks where
Bayesian modeling most clearly earns its complexity, this is usually the first
answer.

## Section 7: MCMC, NUTS, and Diagnostics

The main reason Bayesian tooling feels expensive is that inference is expensive.
A deterministic optimizer can give you a point estimate quickly. A posterior
sampler has to explore a distribution. That makes the inference algorithm a
first-class engineering concern rather than an invisible implementation detail.

For continuous models in PyMC, NUTS is the default workhorse. The samplers page
and the underlying Hoffman and Gelman paper are the canonical references:
https://www.pymc.io/projects/docs/en/stable/api/samplers.html and
https://arxiv.org/abs/1111.4246
NUTS is a variant of Hamiltonian Monte Carlo that adapts trajectory length so
the sampler can move efficiently without the user hand-picking path lengths. In
practical terms, it is why PyMC can fit rich continuous models without falling
back to naive random walks.

The workflow still requires discipline. Multiple chains matter because a single
chain cannot tell you whether it got stuck in one region. Tuning iterations
matter because the sampler needs time to adapt step sizes and mass matrices
before the kept draws are considered usable. `target_accept` matters because
increasing it can reduce divergences at the cost of slower exploration.

Most importantly, **R-hat / ESS / divergences are non-negotiable diagnostics**.
That phrase should be read literally. The working defaults for this module are
`r_hat <= 1.01`, `ESS >= 400` per chain, and divergences equal to zero. If any
of those fail, the posterior summary is provisional at best.

`az.summary` is the normal first checkpoint because it reports `r_hat`,
`ess_bulk`, `ess_tail`, and MCSE information through the ArviZ summary API:
https://python.arviz.org/projects/stats/en/latest/api/generated/arviz_stats.summary.html
`az.plot_trace` is the normal second checkpoint because it shows whether chains
are mixing and whether the sampler is wandering cleanly instead of sticking in
problematic regions:
https://python.arviz.org/projects/plots/en/latest/api/generated/arviz_plots.plot_trace.html

> **Pause and decide** — Your posterior table looks substantively plausible, but
> one coefficient has `r_hat = 1.03`, `ess_bulk = 260`, and the run reported
> three divergences. Do you keep the estimate because the mean is stable enough,
> or do you treat the result as not yet trustworthy? (Answer: not yet
> trustworthy. The diagnostics fail the basic contract. A stable-looking mean is
> not permission to ignore non-convergence and geometry problems. Increase
> `target_accept`, inspect parameterization, and rerun before you discuss the
> coefficient as if it were settled.)

Divergences deserve special emphasis because practitioners often misread them as
mere warnings. A divergence is evidence that the sampler had trouble exploring
the posterior geometry faithfully. It can signal funnel-shaped geometry, poor
parameterization, or a prior-likelihood combination that creates pathological
regions. You do not get to declare victory because the number of divergences was
small relative to the total number of draws.

Bayesian modeling demands more than casual patience because you are paying to
validate that inference actually reached the distribution you think it reached.
**Bayesian costs 10-100x compute, pay only when uncertainty matters.**

## Section 8: Variational Inference and ADVI

Variational inference exists because MCMC is not always affordable. Instead of
sampling directly from the posterior, variational methods choose a simpler
family of distributions and optimize that family to approximate the posterior.
PyMC exposes this through `pm.fit`, including the standard `method="advi"` path:
https://www.pymc.io/projects/docs/en/stable/api/vi.html and the original ADVI
paper at https://arxiv.org/abs/1603.00788

The engineering attraction is obvious. VI is usually much faster than full MCMC.
It can be good enough for model prototyping, for checking whether the model
structure is sensible, or for iterating on priors and parameterization before
paying the full sampling cost.

The canonical warning is equally important: **ADVI / VI underestimates posterior
variance. Use VI for prototyping, MCMC for production.** This happens because
the approximation family, especially mean-field ADVI, often cannot capture the
full posterior dependence structure. The posterior center may look fine while
the posterior width is too narrow. That is dangerous if the whole reason you
went Bayesian was to quantify uncertainty honestly.

```python
import numpy as np
import pymc as pm
import arviz as az

rng = np.random.default_rng(33)
X = rng.normal(size=(220, 2))
y = 1.1 + X @ np.array([0.9, -1.7]) + rng.normal(scale=0.8, size=220)

with pm.Model() as advi_model:
    X_data = pm.Data("X_data", X)
    alpha = pm.Normal("alpha", mu=0.0, sigma=2.0)
    beta = pm.Normal("beta", mu=0.0, sigma=1.5, shape=2)
    sigma = pm.HalfNormal("sigma", sigma=1.0)

    mu = alpha + pm.math.dot(X_data, beta)
    pm.Normal("obs", mu=mu, sigma=sigma, observed=y)

    approx = pm.fit(n=25000, method="advi")
    idata_vi = approx.sample(2000)

print(az.summary(idata_vi, var_names=["alpha", "beta", "sigma"])[["mean", "sd"]])
az.plot_posterior(idata_vi, var_names=["alpha", "beta", "sigma"])
```

The right way to read this example is as a speed-quality tradeoff. It gets you
posterior-like samples quickly, which is often enough to check whether the model
is grossly mis-scaled or whether coefficient directions make sense. It is not
the result you should put in front of a stakeholder when interval width is the
decision variable.

If the model is still exploratory, VI is useful. If you are about to publish
credible intervals or use them to trigger policy, move to MCMC.

## Section 9: Posterior Predictive Checks

Posterior predictive checks are the most underused diagnostic in many Bayesian
workflows because teams get hypnotized by the posterior over parameters. But the
actual question in most applied settings is not "what is the posterior mean of
beta?" It is "does this model generate data that resembles the world we are
trying to explain or predict?"

That is what posterior predictive sampling tests. Draw parameter values from the
posterior, simulate new observations under those values, and compare those
simulated observations with the real observed data. PyMC's posterior predictive
notebook is the working reference:
https://www.pymc.io/projects/docs/en/stable/learn/core_notebooks/posterior_predictive.html

If the simulated data systematically misses the observed means, spreads, tails,
or category frequencies, the problem may not be the sampler at all. It may be
the model structure. In other words, you can have a beautifully converged
posterior for a badly specified model.

```python
import numpy as np
import pymc as pm
import arviz as az

rng = np.random.default_rng(18)
X = rng.normal(size=(180, 1))
y = 0.4 + 2.3 * X[:, 0] + rng.normal(scale=0.9, size=180)

with pm.Model() as ppc_model:
    X_data = pm.Data("X_data", X[:, 0])
    alpha = pm.Normal("alpha", mu=0.0, sigma=2.0)
    beta = pm.Normal("beta", mu=0.0, sigma=1.5)
    sigma = pm.HalfNormal("sigma", sigma=1.0)

    mu = alpha + beta * X_data
    pm.Normal("obs", mu=mu, sigma=sigma, observed=y)

    idata_ppc = pm.sample(
        draws=2000,
        tune=2000,
        chains=4,
        target_accept=0.95,
        random_seed=18,
    )
    ppc = pm.sample_posterior_predictive(
        idata_ppc,
        var_names=["obs"],
        random_seed=18,
    )

simulated = ppc.posterior_predictive["obs"].values
sim_means = simulated.mean(axis=2).reshape(-1)
sim_stds = simulated.std(axis=2).reshape(-1)

print("observed mean:", round(float(y.mean()), 3))
print("median simulated mean:", round(float(np.median(sim_means)), 3))
print("observed std:", round(float(y.std()), 3))
print("median simulated std:", round(float(np.median(sim_stds)), 3))

az.plot_posterior(idata_ppc, var_names=["alpha", "beta", "sigma"])
```

This block is intentionally simple because the lesson is conceptual. You do not
need a fancy discrepancy statistic to learn something useful. Start with obvious
comparisons: mean, spread, tail behavior, and whether the simulated outcomes are
living in the same world as the observed outcomes. If they are not, the model is
missing structure.

Posterior predictive checks are the Bayesian cousin of the calibration mindset
from [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/).
Both are asking whether the probabilistic story your model tells is aligned with
observed reality. The tooling is different. The discipline is the same.

## Section 10: When Bayesian Is the Wrong Tool

This section matters because teams rarely overuse Bayesian modeling out of
malice. They overuse it because the language of uncertainty sounds sophisticated
and therefore hard to reject. The practical correction is to name the regimes
where Bayes is the wrong tool, even if the team could in principle make it work.

If point predictions suffice, Bayesian modeling is usually the wrong tool. A
regularized regression or tree model can often match predictive performance at a
fraction of the compute. If the stakeholder only wants a ranking or a point
forecast and will never use interval width, the posterior is solving the wrong
problem.

If compute is tight, Bayesian modeling is often the wrong tool. This is not a
moral judgment. It is an engineering one. MCMC requires multiple chains,
tuning, diagnostic review, and often repeated model revision. When the latency
or iteration budget is tight, a faster method may create more value simply by
letting the team iterate honestly.

If the stakeholders will misread credible intervals, Bayesian modeling can also
be the wrong tool in practice. A sophisticated uncertainty estimate that will be
misinterpreted as a guarantee may be more dangerous than a simpler method whose
limitations are easier to explain.

This is where a forward reference matters. **Conformal prediction (Module 2.5)
is a frequentist alternative** for uncertainty quantification. It does not
replace Bayesian reasoning in every regime, but it is often a better
engineering answer when you need predictive intervals or set-valued predictions
with less modeling overhead. Treat the two approaches as tools with different
guarantees, not as ideological camps.

Module 2.7, causal inference for ML practitioners, is another important
boundary. Bayesian models can appear in causal workflows, but a posterior over a
predictive model is not automatically a causal effect estimate. If the question
is intervention rather than prediction, the workflow has changed.

The anti-hype rule for this section is simple. Do not ship a Bayesian model
because it sounds more principled. Ship it because the uncertainty, pooling, or
small-data behavior will alter a real decision enough to justify the cost.

## Section 11: Practitioner Playbook

The practical playbook starts with refusal. Do not begin from "we want a
Bayesian model." Begin from the decision that depends on interval width,
cohort shrinkage, or a direct posterior probability statement. If that answer is
vague, fit the frequentist baseline first. A regularized model from
[Module 1.2: Linear and Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/)
sets the point-prediction floor cheaply and forces the team to justify the extra
Bayesian path.

Once the value case is clear, standardize predictors where appropriate and pick
weakly informative priors that are easy to defend. Write the PyMC model in named
components so that another engineer can inspect `alpha`, `beta`, `sigma`, or
group-level parameters without reverse engineering the whole graph.

Start with an MCMC path when the final output will be shown to stakeholders.
Use four chains, enough tuning, and an explicit `target_accept` when geometry is
likely to be awkward. Check `az.summary`. Check trace plots. Treat diagnostics as
gates, not decorations.

If the model is still in exploratory mode, use ADVI as a sketching tool. Learn
from its speed, but do not let it define the final interval widths. The phrase
to remember is still the same: use VI for prototyping, MCMC for production.

Run posterior predictive checks before you congratulate yourself on pretty
coefficient plots. A converged posterior over a misspecified model is still a
misspecified model. The posterior predictive distribution is the model talking
back about whether it understands the data-generating process.

Reach for hierarchical models early when grouped structure is real and group
sample sizes differ meaningfully. That is where Bayesian modeling most often
pays back the added complexity with something a simpler workflow would not have
handled as gracefully.

Finally, write the conclusion in plain language. State whether the Bayesian
model materially changed a decision compared with the frequentist baseline.
State which diagnostics passed. State whether the credible intervals were the
reason to keep the model. If you cannot say those things clearly, the model is
probably not ready.

## Did You Know?

- PyMC's default continuous-model workhorse is NUTS, which adapts Hamiltonian Monte Carlo trajectories rather than requiring manual path-length tuning. Source: https://www.pymc.io/projects/docs/en/stable/api/samplers.html and https://arxiv.org/abs/1111.4246
- The PyMC overview explicitly describes PyMC as a Python probabilistic programming framework that uses PyTensor for automatic differentiation. Source: https://www.pymc.io/projects/docs/en/stable/learn/core_notebooks/pymc_overview.html
- ArviZ's summary tooling reports `r_hat`, `ess_bulk`, `ess_tail`, and related diagnostics, which is why responsible Bayesian workflow in Python is a PyMC plus ArviZ stack rather than PyMC alone. Source: https://python.arviz.org/en/stable/api.html and https://python.arviz.org/projects/stats/en/latest/api/generated/arviz_stats.summary.html
- ADVI is built into PyMC through the variational API, but it is an approximation strategy rather than an exact posterior sampler. Source: https://www.pymc.io/projects/docs/en/stable/api/vi.html and https://arxiv.org/abs/1603.00788

## Common Mistakes

| Mistake | Why it bites | Fix |
| --- | --- | --- |
| Using Bayesian methods because "Bayesian means better" | The point predictions may be no better than a regularized frequentist baseline | State the uncertainty or pooling decision that justifies the extra cost |
| Reading posterior summaries before diagnostics | Non-converged chains can produce polished-looking nonsense | Check `r_hat`, ESS, divergences, and trace plots first |
| Treating weakly informative priors as optional detail | Poorly scaled or absurd priors can destabilize the model | Standardize predictors and choose defensible priors on that scale |
| Trusting ADVI interval width as if it were MCMC | Mean-field approximations often shrink posterior variance | Use ADVI to prototype and MCMC to report production intervals |
| Running one chain for speed | `r_hat` becomes far less informative and local sticking is easy to miss | Run four chains unless you have an unusually strong reason not to |
| Skipping posterior predictive checks | A converged sampler can still fit a structurally wrong model | Simulate from the posterior predictive and compare to observed data |
| Building separate group models when data is sparse | Small groups overfit and large groups dominate attention | Use hierarchical partial pooling |
| Choosing Bayesian tooling under a strict compute budget without need | The team pays 10-100x more compute for little decision value | Compare against simpler baselines and use conformal prediction when appropriate |

## Quiz

1. A team fits Bayesian linear regression and gets almost the same test MSE as a
Ridge baseline, but now they also have credible intervals for coefficients and
predictions. Was the extra work justified?

<details><summary>Answer</summary>
It depends on whether those credible intervals change a real decision. If the
deployment only uses point predictions, the extra computation likely bought very
little. If the intervals affect policy, risk tolerance, or whether a coefficient
is treated as uncertain versus directional, then the Bayesian model may have
earned its cost even without better MSE.
</details>

2. A posterior summary shows `r_hat = 1.05` on three parameters and
`ess_bulk = 200` on one of them. The posterior means look stable. Is the result
good enough to report?

<details><summary>Answer</summary>
No. The diagnostics fail the minimum contract. A stable-looking mean is not
evidence of convergence. The right move is to revisit parameterization, raise
`target_accept` if appropriate, inspect trace plots, and rerun until the
diagnostic thresholds are met or the model's limitations are stated explicitly.
</details>

3. ADVI reports a narrow posterior around a coefficient, while an MCMC run puts
the same center with much wider credible intervals. Which should you report to a
stakeholder, and why?

<details><summary>Answer</summary>
Report the MCMC result if interval width matters. ADVI can be valuable for
prototyping, but its approximation often underestimates posterior variance. When
the stakeholder is using the interval as a decision input, the more faithful
MCMC posterior is the defensible result.
</details>

4. A hospital network has eight sites with modest patient counts per site and
wants site-specific baseline effects. Should the team fit pooled, no-pooled, or
partially pooled models first?

<details><summary>Answer</summary>
Partially pooled. This is the textbook hierarchical setting: each site is real
enough to deserve its own effect, but the smaller sites should borrow strength
from the larger structure rather than standing entirely alone. No pooling will
be noisy; complete pooling will erase real differences.
</details>

5. A stakeholder asks, "What is the probability this coefficient is positive?"
Which interval framework answers that most directly?

<details><summary>Answer</summary>
A Bayesian posterior answers that most directly, because it lets you compute the
posterior probability that the coefficient exceeds zero under the model. A
confidence interval from a frequentist workflow is not read as a direct
probability statement about the specific parameter value in the same way.
</details>

6. A PyMC run finishes with six divergences after sampling. The summary table
otherwise looks acceptable. Ignore, increase `target_accept`, or reparameterize?

<details><summary>Answer</summary>
Do not ignore the divergences. The first steps are usually to inspect the model,
consider raising `target_accept`, and examine whether a non-centered or other
reparameterization is needed. Divergences are evidence of problematic posterior
geometry, not cosmetic warnings.
</details>

7. A team wants prediction intervals for a production system but has a tight
compute budget and cannot afford repeated MCMC diagnostics. What alternative
should they at least consider?

<details><summary>Answer</summary>
They should at least consider conformal prediction in Module 2.5. It is a
frequentist alternative for uncertainty quantification that often provides a
better engineering tradeoff when the need is interval-like output rather than a
full posterior over model parameters.
</details>

8. Posterior predictive samples repeatedly fail to match the observed spread of
the data even though `r_hat` looks fine. What does that signal?

<details><summary>Answer</summary>
It signals a model-specification problem rather than a convergence problem. The
sampler may have explored the posterior of the specified model successfully, but
the specified model is not generating data that resembles the world. The fix is
to revisit likelihood, predictors, structure, or hierarchy rather than to
celebrate the tidy diagnostics.
</details>

## Hands-On Exercise

- [ ] Step 0: Start a notebook or script and import `numpy as np`,
  `pymc as pm`, `arviz as az`, `Ridge`, `mean_squared_error`,
  `train_test_split`, and any small sklearn utilities you need for a baseline.

- [ ] Step 1: Generate synthetic regression data with known coefficients and a
  clearly chosen noise scale. Keep the data simple enough that you can reason
  about what the posterior should learn.

- [ ] Step 2: Fit a `Ridge` baseline and record its test MSE. Write one sentence
  explaining why that baseline matters before any Bayesian claim is made.

- [ ] Step 3: Build a Bayesian linear regression in PyMC with weakly informative
  priors on the intercept, coefficients, and residual scale.

- [ ] Step 4: Sample with NUTS using `draws=2000`, `tune=2000`, `chains=4`, and
  `target_accept=0.95`.

- [ ] Step 5: Run `az.summary` and reject the run if any key parameter has
  `r_hat > 1.01`, effective sample size below `400` per chain, or any
  divergences.

- [ ] Step 6: Use `az.plot_posterior` or `az.plot_trace` to inspect the fitted
  model, then write a short note comparing the coefficient uncertainty with the
  point-estimate-only view from Ridge.

- [ ] Step 7: Run `pm.sample_posterior_predictive` and compare simulated means
  and spreads against the observed data. State whether the model appears to
  reproduce the data-generating pattern adequately.

- [ ] Step 8: Refit the same model with `pm.fit(method="advi")`, draw posterior
  samples from the approximation, and compare its posterior widths to the MCMC
  widths.

- [ ] Step 9: Create a grouped synthetic dataset and fit a hierarchical varying
  intercept model with `G = 8` groups. Compare the partial-pooling estimates to
  raw group means or a no-pooling analogue.

- [ ] Step 10: Write a one-paragraph report stating where the Bayesian model
  justified action because uncertainty mattered and where it would have been
  wasted effort if the only objective were point prediction.

- [ ] Completion check: confirm that diagnostics passed with `r_hat <= 1.01`,
  ESS at or above `400` per chain, and divergences equal to zero.

- [ ] Completion check: confirm that posterior predictive samples cover the
  observed behavior well enough that the model is not obviously misspecified.

- [ ] Completion check: confirm that the ADVI versus MCMC width comparison is
  documented explicitly, not implied.

## Sources

- https://www.pymc.io/projects/docs/en/stable/learn/core_notebooks/pymc_overview.html
- https://www.pymc.io/projects/docs/en/stable/api.html
- https://www.pymc.io/projects/docs/en/stable/api/distributions.html
- https://www.pymc.io/projects/docs/en/stable/api/samplers.html
- https://www.pymc.io/projects/docs/en/stable/api/generated/pymc.sample.html
- https://www.pymc.io/projects/docs/en/stable/api/vi.html
- https://www.pymc.io/projects/docs/en/stable/learn/core_notebooks/GLM_linear.html
- https://www.pymc.io/projects/docs/en/stable/learn/core_notebooks/posterior_predictive.html
- https://www.pymc.io/projects/examples/en/latest/generalized_linear_models/multilevel_modeling.html
- https://python.arviz.org/en/stable/
- https://python.arviz.org/en/stable/api.html
- https://python.arviz.org/projects/stats/en/latest/api/generated/arviz_stats.summary.html
- https://python.arviz.org/projects/plots/en/latest/api/generated/arviz_plots.plot_trace.html
- https://arxiv.org/abs/1111.4246
- https://arxiv.org/abs/1603.00788

## Next Module

The next module in this Tier-2 sequence is **Module 2.4: Recommender Systems**, covering collaborative filtering, content-based scoring, learning-to-rank, and the production-MLOps caveats that turn a research-prototype recommender into a system that survives the cold-start problem and the feedback loop. It ships next in Phase 3 of [issue #677](https://github.com/kube-dojo/kube-dojo.github.io/issues/677); the link in this section will go live when that PR lands.
