---
title: "Dimensionality Reduction"
description: "Choose, fit, and reason about dimensionality reduction honestly. PCA, TruncatedSVD, IncrementalPCA, KernelPCA, t-SNE, UMAP, and a small note on ICA — with a clear boundary between visualization tools and supervised feature pipelines."
slug: ai-ml-engineering/machine-learning/module-1.10-dimensionality-reduction
sidebar:
  order: 10
---

> Track: AI/ML Engineering | Complexity: `[MEDIUM]` | Time: 75-90 minutes
> Prerequisites: [Module 1.1: Scikit-learn API & Pipelines](../module-1.1-scikit-learn-api-and-pipelines/), [Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/), [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/), [Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/), [Module 1.7: Naive Bayes, k-NN & SVMs](../module-1.7-naive-bayes-knn-and-svms/), [Module 1.8: Unsupervised Learning: Clustering](../module-1.8-unsupervised-learning-clustering/), and [Module 1.9: Anomaly Detection & Novelty Detection](../module-1.9-anomaly-detection-and-novelty-detection/).

Most teams arrive at dimensionality reduction the same way.
A dataset has too many features.
A scatter plot is illegible.
A linear model fits slowly or unstably.
A clustering result looks visually scrambled.
Someone proposes "let's reduce dimensions" and the team begins reaching
for whichever tool was named most recently in conversation.

That instinct is reasonable, but it tends to collapse three different
problems into one tool selection.

The first problem is visualization.
A human wants to see the data on a page, in two dimensions, ideally with
recognizable structure.

The second problem is computational efficiency or numerical stability.
A model is slow, multicollinear, or memory-bound, and a smaller, more
orthogonal feature set would help.

The third problem is supervised feature engineering.
A practitioner believes that fewer features will improve downstream
classification or regression because the original features are noisy,
correlated, or low-signal.

These three problems share vocabulary but disagree about everything that
matters.
They disagree about which tools are safe.
They disagree about whether stochastic embeddings are acceptable.
They disagree about whether the output needs a `transform` method that
generalizes to unseen rows.
They disagree about whether the embedded space needs to be stable across
folds, runs, or seeds.

That is why this module treats the choice of dimensionality-reduction
method as a decision discipline rather than a parameter table.
The wrong tool, picked from the right family, will look successful and
quietly mislead the team for months.

The previous modules already prepared the ground for this kind of
thinking.
[Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/)
made scaling and leakage discipline explicit.
[Module 1.7: Naive Bayes, k-NN & SVMs](../module-1.7-naive-bayes-knn-and-svms/)
showed why distance and kernel methods are exquisitely sensitive to
representation.
[Module 1.8: Unsupervised Learning: Clustering](../module-1.8-unsupervised-learning-clustering/)
introduced the habit of inspecting structure without ground truth.
[Module 1.9: Anomaly Detection & Novelty Detection](../module-1.9-anomaly-detection-and-novelty-detection/)
emphasized the gap between an algorithm returning numbers and a system
producing trustworthy decisions.

Dimensionality reduction sits comfortably alongside those topics, but it
also introduces a new failure mode that does not appear in clustering or
anomaly detection.
The new failure mode is *misuse by mode*: using a visualization-only
tool, such as t-SNE or UMAP, as if it were a supervised preprocessing
step.
That misuse is so common, and so seductive, that the rest of this module
is organized around making the boundary between those two modes
unmistakable.

## Learning Outcomes

- Choose a dimensionality-reduction method by matching the actual job —
  visualization, computational efficiency, or supervised preprocessing —
  to the algorithm's stability, scaling needs, and API surface, building
  on the estimator-contract intuition from
  [Module 1.1: Scikit-learn API & Pipelines](../module-1.1-scikit-learn-api-and-pipelines/).
- Design a PCA-based preprocessing step that is leakage-safe inside a
  cross-validated pipeline and explain why TruncatedSVD or IncrementalPCA
  is sometimes the more appropriate variant, drawing on the preprocessing
  discipline from
  [Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/).
- Diagnose whether disappointing PCA behavior comes from missing
  scaling, from target signal living on a low-variance axis, or from
  rotated features that no longer mean what stakeholders expect, with
  reference to the multicollinearity discussion in
  [Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/).
- Evaluate t-SNE and UMAP as exploratory visualization tools, explain
  why neither is a default supervised feature step, and produce
  perplexity- or n-neighbor-sweep evidence that a visual cluster is
  stable rather than coincidental.
- Justify when dimensionality reduction is the wrong tool by connecting
  alternatives such as feature selection from
  [Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/),
  regularization from
  [Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/),
  and learned representations from the
  [Deep Learning](../../deep-learning/) track.

## Why This Module Matters

The scikit-learn user guide on matrix factorization and decomposition
opens with a careful list of methods rather than a single
recommendation:
[https://scikit-learn.org/stable/modules/decomposition.html](https://scikit-learn.org/stable/modules/decomposition.html)
covers PCA, IncrementalPCA, KernelPCA, TruncatedSVD, ICA, NMF, and more,
and the manifold-learning user guide
[https://scikit-learn.org/stable/modules/manifold.html](https://scikit-learn.org/stable/modules/manifold.html)
adds t-SNE, Isomap, locally linear embedding, MDS, and spectral
embedding to that landscape.

The breadth is not an accident.
Different algorithms encode different geometric assumptions, and those
assumptions matter as soon as the embedding leaves the notebook and
enters a real pipeline.

That distinction sounds tidy until someone is on call.
A model has been quietly using a t-SNE projection as a preprocessing
step for several months.
A new training run is launched.
The downstream classifier degrades.
Investigation reveals that the t-SNE embedding is fit fresh on each
training run, that perplexity was set once long ago and never revisited,
that the embedding has no `transform` method, that the random seed has
drifted across environments, and that nobody is sure whether the latest
embedding even places the same kinds of cases in the same regions.

In that scenario the algorithm is not broken.
It is being asked to do something the manifold-learning guide quietly
warns against: serve as the deterministic, generalizing feature
extractor for a supervised model.

This is also where the tool's marketing pressure shows up.
t-SNE and UMAP plots are visually striking.
A management deck full of well-separated colored blobs is more
persuasive than the same data shown as a PCA scatter, even when the PCA
view is more honest about the geometry.
That visual persuasiveness leaks into design choices.
A manager looks at a t-SNE plot, sees clusters, and asks whether the
classifier could learn directly from those coordinates.
The technically correct answer — "no, that embedding isn't stable, isn't
generalizable, and isn't the same kind of representation a classifier
needs" — is not always the answer that gets heard.

The job of this module is to make the right answer easy to defend.
Once the boundary between visualization tools and supervised
preprocessing tools is clear, the rest of the topic becomes much
quieter.
PCA, TruncatedSVD, and IncrementalPCA do most of the supervised work.
t-SNE and UMAP do the exploratory and stakeholder-communication work.
KernelPCA and ICA fill narrower roles where their assumptions truly
match the data.
That mental map is more durable than any single parameter table.

## Section 1: What Dimensionality Reduction Actually Does

The phrase "dimensionality reduction" suggests a single concept, but at
least three meaningfully different operations live under it.

The first is *projection*.
A projection finds a lower-dimensional subspace and maps every point
into that subspace.
PCA, TruncatedSVD, ICA, and IncrementalPCA are projections.
They produce a deterministic linear map from the original feature space
to a smaller one, and that map can be applied to any new row using the
same coefficients.

The second is *embedding*.
An embedding finds a lower-dimensional layout of points in which some
notion of similarity is preserved, typically a notion based on
neighborhoods rather than a global linear basis.
t-SNE, UMAP, Isomap, locally linear embedding, MDS, and spectral
embedding are embeddings.
Some of them are stochastic.
Some of them have no natural way to place a brand-new row into the
existing layout without recomputing.
Some are dominated by hyperparameters that change the qualitative shape
of the result.

The third is *learned representation*.
A neural network trained for a downstream task carries the original
features through layers that mix, contract, and expand them, and one of
those intermediate layers can be treated as a dense low-dimensional
representation of the input.
Autoencoders, contrastive learners, and self-supervised models live
here.
Those are out of scope for this module and are covered in the deep
learning track, but the contrast is useful.

The reason to hold all three concepts in mind is that practitioners
routinely confuse them.
They reach for an embedding because the visualization is striking, then
treat it as if it were a projection that can be applied to new rows
deterministically.
They reach for a projection because the math is clean, then complain
that the resulting axes "do not make business sense."
They reach for a learned representation because a competing team did,
without acknowledging that learned representations require labeled or
self-supervised training and a stable inference path.

Holding the distinction precisely is the foundation of the rest of the
module.
PCA-family methods are projections.
t-SNE and UMAP are embeddings.
The two are not interchangeable, even when the resulting array shape
looks identical.

## Section 2: PCA in Honest Detail

Principal component analysis is the workhorse linear projection.
Its description is brief and its pitfalls are many, which is the
opposite of how it is often taught.

The mathematical content is short.
PCA finds an orthonormal set of directions in feature space such that
projecting the data onto the first direction maximizes variance,
projecting onto the second direction maximizes variance subject to
orthogonality with the first, and so on.
It is implemented through the singular value decomposition of the
centered data matrix or through the eigendecomposition of the
covariance matrix.
The scikit-learn API at
[https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html)
exposes this as a familiar transformer with `fit`, `transform`,
`fit_transform`, `inverse_transform`, and informative attributes such as
`components_`, `explained_variance_ratio_`, and `singular_values_`.

That is the easy part.

The first nuance is what `n_components` accepts.
It can be an integer, in which case PCA returns exactly that many
components.
It can be a float between zero and one, in which case PCA chooses the
smallest number of components whose cumulative explained-variance ratio
exceeds the requested threshold; this is the friendliest default for
practitioners who want to keep, say, ninety-five percent of the
variance without committing to a fixed integer.
It can be the string `'mle'`, in which case PCA estimates the intrinsic
dimensionality of the data using Minka's maximum-likelihood criterion;
this is convenient for exploratory work but is not the right choice for
strict reproducibility because the estimated dimension can drift as the
data changes.

The second nuance is scaling.
PCA is variance-driven, and variance is units-driven.
A column measured in millions of dollars and a column measured as a
fraction between zero and one will not contribute equally to the
covariance structure.
Without scaling, PCA tends to align its first component with whichever
column has the largest absolute spread, regardless of whether that
column carries the most signal.
This is why PCA almost always belongs in a `Pipeline` with a
`StandardScaler` upstream, and why the same scaling discipline that
[Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/)
demanded for k-nearest neighbors and SVMs applies to PCA in the same
way.

The third nuance is what PCA components actually mean.
A component is a linear combination of original features chosen because
its variance is large.
That is not the same thing as importance.
The largest principal component does not "explain" the target.
It explains variation in the inputs.
If the target signal happens to live on a low-variance axis — for
example, a small but consistent shift in one feature that correlates
with churn — then projecting onto the top components can rotate that
signal away from the eventual classifier and look like dimensionality
reduction has hurt accuracy.
The fact that a component carries fifty percent of the input variance
does not mean it carries any of the target's information.

The fourth nuance is interpretability.
The vectors stored in `components_` give the loadings: how each original
feature contributes to each principal direction.
Loadings are diagnostic, not causal.
A component that loads heavily on three correlated features tells the
practitioner those features move together; it does not tell the
practitioner why.
Pretending otherwise is one of the older sins in applied multivariate
statistics, and it is just as easy to commit in 2026 as it was decades
ago.

The fifth nuance is whitening.
The `whiten` parameter rescales the projected components to unit
variance.
Whitening is sometimes useful before downstream models that assume
isotropic features, but it changes the relative weighting between
components and can amplify noise in low-variance directions.
It is not a default to flip on without thinking.

These nuances combine to produce a useful working stance.
PCA is the right tool for supervised preprocessing when the practitioner
has already standardized features, has a clear reason to suspect
multicollinearity or computational pressure, and is willing to keep
enough components to retain the variance that matters.
It is the wrong tool when the practitioner expects the resulting axes
to mean something to a stakeholder, when the target signal is hidden in
small-variance structure, or when the data is genuinely non-linear and a
manifold approach would do better.

> **Pause and predict** — A teammate runs PCA on a feature matrix where
> one column is "annual revenue in dollars" (range 10⁴–10⁹) and another
> is "customer tenure in years" (range 0–20), without any prior scaling.
> They report that PC1 captures 99.7% of the variance. What does that
> number actually mean about the data, and what would change if the
> features were standardized first? (Answer: PC1 is essentially the
> revenue column rotated slightly. The variance is dominated by units,
> not by signal. After `StandardScaler`, both features contribute
> comparable variance and PC1 reflects whatever covariance actually
> exists between them.)

## Section 3: PCA Inside a Pipeline, Without Leakage

The leakage discipline from
[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/)
applies to PCA in full force.
The mean and the principal directions are statistics of the training
fold and must be re-estimated inside each cross-validation split rather
than precomputed once on the full dataset.
Doing it wrong can look impressively accurate during validation and
collapse on production data, which is the canonical leakage signature.

The right way is to put PCA inside a `Pipeline`.

```python
from sklearn.datasets import load_breast_cancer
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

X, y = load_breast_cancer(return_X_y=True)

pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("pca", PCA(n_components=0.95)),
    ("clf", LogisticRegression(max_iter=2000)),
])

scores = cross_val_score(pipe, X, y, cv=5, scoring="roc_auc")
print(scores.mean(), scores.std())
```

Three things deserve attention in that snippet.

First, scaling sits inside the pipeline.
This means each cross-validation fold computes its own mean and standard
deviation from the training portion of that fold and applies those
statistics to the held-out portion.
Centering the entire dataset before splitting is a textbook leakage
mistake; it gives every fold a tiny but real preview of the held-out
data through the global mean.

Second, `n_components=0.95` lets PCA choose the number of components per
fold.
This makes the pipeline robust to small dataset variations but means the
selected component count can differ across folds.
For most production systems that variance is acceptable; if absolute
reproducibility matters, fix `n_components` to an integer based on a
prior exploration step.

Third, the classifier sits at the end and never sees the raw features
directly.
That is the right place for it.
The PCA stage is a deterministic transformer; it has its own coefficients
once fitted and applies them with `transform` to any new data.
This is the property that makes PCA suitable for supervised use:
exactness, determinism, and a generalizing forward map.

Holding that property in mind makes it easier to see why the embeddings
in the second half of this module are different.

## Section 4: TruncatedSVD for Sparse Data

The standard PCA implementation assumes dense input, because centering a
sparse matrix densifies it and destroys the memory advantage that made
it sparse to begin with.
This is a meaningful problem for text features.
A TF-IDF representation of even a modest corpus easily reaches tens of
thousands of dimensions, almost all of them zero per document.

`TruncatedSVD`, documented at
[https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.TruncatedSVD.html](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.TruncatedSVD.html),
solves this by simply not centering the data.
It performs a truncated singular value decomposition directly on the
matrix as given.
This makes it suitable for sparse input and gives it a second life as
*latent semantic analysis* in classical text retrieval.

The trade-off is that the resulting axes are no longer principal
components in the strict statistical sense; they are top singular
directions of an uncentered matrix.
For sparse, non-negative data such as TF-IDF or count vectors, the
distinction is rarely a problem and the speed and memory benefits are
large.
For dense, mean-shifted continuous data, regular PCA is still the right
choice.

A typical text-classification preprocessing stage looks like this.

```python
from sklearn.datasets import fetch_20newsgroups
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

data = fetch_20newsgroups(subset="train", categories=["sci.med", "sci.space"])

pipe = Pipeline([
    ("tfidf", TfidfVectorizer(max_features=50000)),
    ("svd", TruncatedSVD(n_components=200, random_state=0)),
    ("clf", LogisticRegression(max_iter=2000)),
])

pipe.fit(data.data, data.target)
```

Two practitioner notes are worth attaching.
The first is that the choice of `n_components` for TruncatedSVD is
genuinely arbitrary in a way it is not for dense PCA, because the
explained-variance interpretation is weaker on uncentered sparse data.
A common starting point in retrieval and classification is somewhere in
the low hundreds, but the right number is whatever keeps the downstream
metric stable as the value shifts.
The second is that TruncatedSVD is a real linear projection with a
proper `transform` method, which makes it suitable for supervised
pipelines in the same way as PCA.
This is the contrast that should keep returning to the front of the
mind throughout the module: t-SNE and UMAP do not have that property in
the same way.

## Section 5: IncrementalPCA When Memory Is the Constraint

Sometimes the dataset simply does not fit in memory.
A multi-gigabyte feature matrix on a single machine, or a streaming
training set that arrives in batches, defeats the assumption that PCA
can compute a single SVD on the whole thing.

`IncrementalPCA`, documented at
[https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.IncrementalPCA.html](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.IncrementalPCA.html),
addresses this by exposing a `partial_fit` method.
The estimator maintains a running estimate of the principal components
across batches and refines those estimates as more data arrives.
Memory cost is proportional to the batch size and the number of
features rather than the entire sample count.

The trade-off is a small amount of statistical accuracy.
A batched SVD is not exactly the same as a full SVD; for most
practitioner use cases the gap is small enough to ignore, but it is
worth verifying on a held-out batch that the explained-variance ratio
profile looks similar to a regular PCA on a sample of the data.

A common pattern is to use IncrementalPCA when training data sits in a
memory-mapped file or arrives in chunks from a database cursor.

```python
import numpy as np

from sklearn.decomposition import IncrementalPCA

rng = np.random.default_rng(0)


def stream_of_batches(n_batches=10, batch_size=2000, n_features=100):
    """Stand-in for a real chunked source (memory-mapped file, DB cursor,
    Parquet row groups). It only needs to yield fixed-width arrays."""
    for _ in range(n_batches):
        yield rng.normal(size=(batch_size, n_features))


ipca = IncrementalPCA(n_components=50, batch_size=2000)

for batch in stream_of_batches():
    ipca.partial_fit(batch)

# Once fit, IncrementalPCA behaves like a regular transformer.
X_reduced = np.vstack([ipca.transform(batch) for batch in stream_of_batches()])
```

The `stream_of_batches` generator here is a stand-in: swap it for your real
chunked source (a memory-mapped array, a database cursor, Parquet row groups).
The estimator does not care where the batches come from, only that they
have consistent feature dimensionality and represent the data
distribution well enough that the components stabilize.

IncrementalPCA inherits the same scaling discipline as regular PCA.
A `StandardScaler` with `partial_fit` belongs upstream of it for
streaming use cases, and a fixed pre-computed scaler is acceptable for
batch-mode work as long as the scaler was fit on a representative
sample.

## Section 6: KernelPCA for Non-Linear Structure

Some datasets carry structure that is not linear.
Two interlocking spirals, a curved manifold inside a higher-dimensional
space, or a boundary that bends in the original feature coordinates can
all defeat ordinary PCA.
The first principal component will dutifully maximize variance, but the
geometry of interest sits along a curve, not along a straight axis.

`KernelPCA`, documented at
[https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.KernelPCA.html](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.KernelPCA.html),
applies the kernel trick from
[Module 1.7: Naive Bayes, k-NN & SVMs](../module-1.7-naive-bayes-knn-and-svms/)
to projection.
Conceptually, the data is mapped into a higher-dimensional feature
space implied by a kernel function, PCA is performed in that space, and
the result is projected back.
For appropriate kernels, this lets KernelPCA recover non-linear
structure that ordinary PCA cannot.

The trade-off is severe.
KernelPCA scales roughly with the square of the sample count because it
operates on a kernel matrix whose entries are pairwise similarities.
On twenty thousand samples this becomes uncomfortable.
On hundreds of thousands it becomes infeasible.

KernelPCA also inherits all the kernel selection and scaling concerns
from kernel SVMs.
The RBF kernel needs a sensible `gamma`.
Polynomial kernels are sensitive to degree and to feature scale.
A linear kernel reduces KernelPCA to ordinary PCA with extra overhead,
which is a useful sanity check rather than a useful production setting.

KernelPCA does, importantly, support `transform` on new data.
That makes it more pipeline-friendly than t-SNE for the rare cases where
its assumptions match the data.
The right occasions are usually small-sample, clearly non-linear, and
where the practitioner has invested the effort to validate that the
chosen kernel actually captures the structure.

## Section 7: t-SNE Is for Visualization, Not Pipelines

The single most consequential idea in this module starts here.

t-SNE, the t-distributed stochastic neighbor embedding, is a
*visualization* tool.
The scikit-learn implementation at
[https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html](https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html)
is sklearn-API-shaped — it has a `fit_transform` method — but it is not
a generalizing transformer in the way PCA is.

There are several distinct reasons for this.

The first is that t-SNE has no `transform` method.
Once it has produced an embedding for the rows it was fit on, there is
no straightforward way to place a brand-new row at the right position
in that embedding.
This is not an oversight in the API.
It reflects the fact that t-SNE's objective is defined globally over all
the rows simultaneously and does not factor cleanly into a forward map.
A practitioner who wants t-SNE coordinates for unseen data must refit
the entire embedding, which means the coordinates of previously
embedded points will also shift.

The second is that t-SNE is stochastic.
Different random seeds produce different embeddings.
Different perplexities produce different embeddings.
Different initializations produce different embeddings.
The qualitative shape — clumpiness, separability, cluster boundaries —
is reasonably robust if the structure in the data is robust, but the
exact coordinates are not, and a downstream classifier that depends on
exact coordinates is depending on noise.

The third is that t-SNE preserves local neighborhoods, not global
geometry.
Two points that look close in the embedded space probably are close in
the original space.
But two clusters that look far apart in the embedded space are not
necessarily far apart in the original space.
The size of clusters, the distance between clusters, and the density of
points within clusters in a t-SNE plot are not literal readings of the
data.
The
[t-SNE perplexity example](https://scikit-learn.org/stable/auto_examples/manifold/plot_t_sne_perplexity.html)
makes this dramatically visible: the same data at perplexities of 5, 30,
50, and 100 produces qualitatively different shapes, and only some of
those shapes match the underlying manifold.

The fourth is the perplexity parameter itself.
Perplexity controls the effective number of neighbors that t-SNE
considers around each point.
A small perplexity emphasizes very local structure and can produce
fragmented embeddings.
A large perplexity averages over more neighbors and can blur small
clusters together.
The sklearn default of thirty is a reasonable starting point for medium
datasets, but the user-guide guidance to try several values is not
optional.
The structure that survives across perplexity values is the structure
worth talking about.

The fifth is the modern initialization.
Since version 1.2, sklearn's t-SNE defaults to `init='pca'` and
`learning_rate='auto'`.
Both changes are improvements over the older `init='random'` and the
default learning rate of 200 from earlier versions, because the PCA
initialization gives global structure a head start and the auto learning
rate scales sensibly with sample size.
A practitioner picking up t-SNE in 2026 should accept those defaults
unless they have a specific reason not to.

A typical visualization workflow looks like this.

```python
import matplotlib.pyplot as plt

from sklearn.datasets import load_digits
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler

X, y = load_digits(return_X_y=True)
X_scaled = StandardScaler().fit_transform(X)

fig, axes = plt.subplots(1, 3, figsize=(15, 5))
for ax, perplexity in zip(axes, [10, 30, 50]):
    embedding = TSNE(
        n_components=2,
        perplexity=perplexity,
        init="pca",
        learning_rate="auto",
        random_state=0,
    ).fit_transform(X_scaled)
    ax.scatter(embedding[:, 0], embedding[:, 1], c=y, s=8, cmap="tab10")
    ax.set_title(f"perplexity={perplexity}")
plt.show()
```

Three perplexities, plotted side by side.
If clusters of digits hold together across all three, the practitioner
can speak about them with some confidence.
If a "cluster" appears at perplexity thirty and dissolves at perplexity
ten, the practitioner should be cautious about reading meaning into it.

The practical commitment that follows from all of this is brief.
t-SNE belongs in exploratory notebooks, in stakeholder communication
where the reader understands they are looking at an embedding rather
than a metric space, and in sanity checks for clustering output.
It does not belong as a step inside a `Pipeline` whose final estimator
is a classifier, regressor, or production scorer.
A team that wants the qualitative feel of t-SNE inside a supervised
pipeline almost always wants something else: better feature engineering
upstream, a non-linear classifier such as gradient boosting from
[Module 1.6: XGBoost & Gradient Boosting](../module-1.6-xgboost-gradient-boosting/),
or a learned representation from a neural network.

> **Pause and decide** — A colleague proposes putting `TSNE(n_components=2)`
> as a step inside a `Pipeline` ending in `LogisticRegression`, then
> running 5-fold cross-validation. Even before the leakage argument, name
> the structural reason this pipeline cannot be evaluated fairly. Then,
> separately: would substituting `umap.UMAP` for `TSNE` make the pipeline
> structurally valid, and would it make the choice a good idea? (Answer:
> `TSNE` has no `transform()` method, only `fit_transform`, so a held-out
> fold cannot be embedded in the basis fit on the training fold — the
> per-fold refit cannot project new rows. UMAP does have `transform()`,
> so the pipeline is at least structurally valid; whether it is a good
> idea is a different question, and usually the answer is still no
> because UMAP outputs are stochastic, sensitive to `n_neighbors`, and
> rarely beat a properly-tuned PCA or supervised non-linear model on
> downstream metrics.)

## Section 8: UMAP, Briefly and Honestly

UMAP — uniform manifold approximation and projection — is the most
common modern alternative to t-SNE.
It is documented at
[https://umap-learn.readthedocs.io/en/latest/](https://umap-learn.readthedocs.io/en/latest/)
and lives in the `umap-learn` package, which installs separately from
scikit-learn but follows the sklearn estimator API.

UMAP has three practical advantages over t-SNE for many datasets.
It is often faster on large datasets, though the exact margin depends on
dataset size, dimensionality, and parameter choices, so benchmark on your
own data rather than assuming a fixed speedup.
It tends to preserve more global structure, which means inter-cluster
distances in a UMAP plot are more meaningful than in a t-SNE plot,
though they are still not literal.
And critically, UMAP does support `transform` on new data, which makes
it slightly more amenable to consistent pipelines than t-SNE.

The two parameters that matter most are `n_neighbors`, with a default
of fifteen, and `min_dist`, with a default of 0.1.
The
[UMAP parameters reference](https://umap-learn.readthedocs.io/en/latest/parameters.html)
explains them in more depth.
`n_neighbors` plays a similar role to t-SNE's perplexity: small values
emphasize local structure, large values blur into global structure.
`min_dist` controls how tightly UMAP packs points within clusters; small
values produce dense clusters, larger values produce smoother
distributions.

A typical exploratory snippet looks like this. UMAP is not bundled with
scikit-learn, so install it first with `pip install umap-learn` (the import
name is `umap`, not `umap-learn`).

```python
import umap
from sklearn.datasets import load_digits
from sklearn.preprocessing import StandardScaler

X, y = load_digits(return_X_y=True)
X_scaled = StandardScaler().fit_transform(X)

reducer = umap.UMAP(n_neighbors=15, min_dist=0.1, random_state=0)
embedding = reducer.fit_transform(X_scaled)
```

The fact that UMAP supports `transform` is genuinely useful, but it
should not lead a team to conclude that UMAP coordinates are now safe
as supervised features by default.
UMAP is still stochastic.
Its embeddings still depend on `n_neighbors` and `min_dist`.
Its inter-cluster distances are still not metric distances in the
original space.
The same discipline that t-SNE demands — sweeping the key parameters,
using multiple seeds, treating the result as a visualization rather than
a deterministic feature map — applies to UMAP, slightly relaxed but not
removed.

The honest framing is that UMAP is a better visualization tool than
t-SNE for many datasets, that it is occasionally acceptable as a
preprocessing step when the practitioner has carefully validated
stability and downstream metric quality, and that it is not a
drop-in replacement for PCA inside a supervised pipeline.

## Section 9: ICA in One Paragraph

Independent component analysis is occasionally useful and is included
here for completeness.
Where PCA finds orthogonal directions of maximum variance, ICA finds
directions that are statistically independent.
The use case is *source separation*: a signal recorded as a mixture of
several underlying sources, where the sources are believed to be
independent but the recordings are not.
Audio source separation is the canonical example.
Outside of signal processing and a handful of neuroimaging applications,
ICA is rarely the right tool for general tabular ML.
Sklearn's `FastICA` is documented at
[https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.FastICA.html](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.FastICA.html)
and supports the standard `fit_transform` and `transform` methods.

## Section 10: An Honest Decision Frame

The pile of tools described above can be reduced to a small decision
table without losing too much.

For *visualization or exploration*, the question is whether linear
structure suffices.
PCA into two or three dimensions is fast, deterministic, and always a
useful first look.
If the structure is genuinely non-linear and a manifold-aware view is
worth the effort, t-SNE or UMAP are the right next step.
Both should be run with multiple parameter values and multiple seeds,
and the structure that survives that sweep is the structure that can be
discussed.

For *supervised preprocessing where dimensionality reduction is genuinely
needed*, the answer is almost always PCA on dense data and TruncatedSVD
on sparse data.
IncrementalPCA replaces PCA when memory is the constraint.
KernelPCA replaces PCA when the data is small, clearly non-linear, and
the practitioner has validated the kernel choice.
t-SNE and UMAP do not appear in this list as defaults.
A team that believes they need a t-SNE or UMAP step in a supervised
pipeline should treat that belief as a hypothesis to test, not a
default to ship, and should compare the result against PCA, against
better feature engineering upstream from
[Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/),
and against a flexible non-linear model such as gradient boosting from
[Module 1.6: XGBoost & Gradient Boosting](../module-1.6-xgboost-gradient-boosting/).

For *decorrelation in linear models*, PCA can sometimes help, but
regularization from
[Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/)
is usually a more direct treatment of the same problem.
PCA changes the basis; ridge and lasso shrink coefficients.
The latter keeps the original features and is far easier to explain to
stakeholders.

For *anomaly detection*, the reconstruction error of a PCA model is a
real signal: rows that cannot be reconstructed well from their first few
principal components are unusual relative to the dominant variance
structure.
This is a useful complement to the methods in
[Module 1.9: Anomaly Detection & Novelty Detection](../module-1.9-anomaly-detection-and-novelty-detection/)
when the data is mostly linear and the anomaly geometry is plausibly
captured by deviations from the principal subspace.

For *learned representations*, dimensionality reduction in the classical
sense is the wrong framing.
Autoencoders, variational autoencoders, contrastive learners, and
self-supervised models live in the deep learning track and produce
dense embeddings that are themselves trainable artifacts.
That is a different topic with different rails.

## Section 11: When Dimensionality Reduction Is the Wrong Tool

Several signs suggest that the right answer is not dimensionality
reduction at all.

The first is when feature selection would do.
If a domain expert can name twenty original features that matter and
sixty that do not, dropping the sixty is more interpretable than
rotating all eighty into PCA components.
The original feature names survive, the model output is easier to
debug, and the loss in performance is often negligible.
[Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/)
covered selection methods worth reaching for first.

The second is when stakeholder interpretability matters.
A regulator or product manager can interpret a coefficient on
"customer tenure in months."
They cannot interpret a coefficient on "principal component three."
A pipeline that ends in a regulated decision should think very carefully
before introducing a rotation that obliterates feature names.

The third is when the underlying problem is non-stationary.
A PCA basis fit on last quarter's data and applied to this quarter's
data will quietly drift as the variance structure of the inputs changes.
That drift is harder to monitor than drift in raw features and can show
up as silent degradation in downstream models.

The fourth is when the team is reaching for dimensionality reduction
because a deep learning approach would have been more natural.
For images, audio, raw text, or other domains where representation
learning is mature, an autoencoder or a pretrained encoder typically
produces better embeddings than PCA, and a learned representation is
intentionally a better fit for the downstream task than an unsupervised
projection.
That decision belongs to the deep learning track rather than this
module, but it is worth mentioning here so practitioners do not waste a
week trying to make PCA stand in for an autoencoder.

## Section 12: Practitioner Pitfalls in One Place

Several pitfalls are common enough to call out explicitly.

t-SNE and UMAP are not default supervised feature steps.
Their stochasticity, their parameter sensitivity, and the absence of a
clean transform path in t-SNE's case make them unsuitable as feature
extractors that need to behave the same way across folds, runs, and
deployments.
A team that has ended up with one of them inside a production pipeline
should treat that as a finding to investigate, not a configuration to
preserve.

PCA needs scaling.
Without it, the largest-variance original feature dominates the first
component for trivial reasons.
The pipeline pattern with `StandardScaler` followed by PCA is the
default, and any deviation from it should have a written justification.

PCA components are not the most important factors.
Variance is not importance.
A component that captures forty percent of the input variance has no
necessary relationship to the target, and a small-variance direction can
carry the entire signal of interest.
This is one of the older and more durable mistakes in applied
multivariate statistics.

`n_components` chosen by explained-variance threshold is a sensible
default.
A fixed integer is sensible when reproducibility across folds is more
important than slightly tuning the variance retention.
The `'mle'` option is interesting for exploration but is not the right
choice for stable production pipelines.

t-SNE perplexity is not a single value.
Running with a single perplexity is approximately as informative as
running k-means with a single k.
Sweeping a small range and looking for stable structure is the
practitioner default.

UMAP's `transform` method is real, but UMAP coordinates are still not
metric distances.
A downstream classifier that uses UMAP outputs as features is implicitly
assuming a stability property the algorithm does not guarantee.

## Section 13: Tying Dimensionality Reduction Back to Earlier Modules

Dimensionality reduction sits naturally at the intersection of several
earlier modules, and an honest practitioner uses those connections.

It connects to
[Module 1.1: Scikit-learn API & Pipelines](../module-1.1-scikit-learn-api-and-pipelines/)
because the projection methods slot cleanly into pipelines and the
embedding methods do not.
That structural difference is the heart of the visualization-versus-
preprocessing distinction.

It connects to
[Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/)
because PCA and ridge regression both address multicollinearity, but
they do so by different mechanisms with different interpretability
costs.
A practitioner should know both and pick consciously.

It connects to
[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/)
because dimensionality reduction is one of the easiest places to leak.
Centering and component fitting are statistics of the training fold and
must be re-estimated inside cross-validation.

It connects to
[Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/)
because scaling discipline applies to PCA in full force, and because
feature selection is often a more interpretable alternative to
projection.

It connects to
[Module 1.7: Naive Bayes, k-NN & SVMs](../module-1.7-naive-bayes-knn-and-svms/)
because the kernel trick that makes kernel SVMs work also makes
KernelPCA work, with the same scaling and computational caveats.

It connects to
[Module 1.8: Unsupervised Learning: Clustering](../module-1.8-unsupervised-learning-clustering/)
because clustering and dimensionality reduction are often run together,
and because t-SNE and UMAP plots are frequently used to sanity-check
cluster assignments.

It connects to
[Module 1.9: Anomaly Detection & Novelty Detection](../module-1.9-anomaly-detection-and-novelty-detection/)
because PCA reconstruction error is itself an anomaly signal for data
where the dominant geometry is linear.

The forward link is to
[Module 1.11: Hyperparameter Optimization](../module-1.11-hyperparameter-optimization/),
which will treat the parameter choices in this module — `n_components`,
`perplexity`, `n_neighbors`, `min_dist` — with the same systematic
discipline it applies to model hyperparameters elsewhere.

## Did You Know?

- Scikit-learn's `TSNE` does not provide a `transform` method, only
  `fit_transform`, because the t-SNE objective is defined jointly across
  all input rows and does not factor into a generalizing forward map:
  [https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html](https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html)
- Since version 1.2, the sklearn t-SNE implementation defaults to
  `init='pca'` and `learning_rate='auto'`, which improves global
  stability and scales the optimization step size to dataset size:
  [https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html](https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html)
- Setting `n_components` to a float between zero and one tells PCA to
  keep the smallest number of components whose cumulative explained
  variance reaches that threshold, with `n_components=0.95` being a
  common starting point for retaining ninety-five percent of the
  variance:
  [https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html)
- `TruncatedSVD` does not center the data before factorization, which
  preserves sparsity and makes it the standard choice for TF-IDF
  matrices and other sparse text representations under the name latent
  semantic analysis:
  [https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.TruncatedSVD.html](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.TruncatedSVD.html)

## Common Mistakes

| Mistake | Why it bites | Fix |
| --- | --- | --- |
| Using t-SNE or UMAP as a step inside a supervised pipeline | The embedding is stochastic, parameter-sensitive, and in t-SNE's case has no `transform` method, so the supervised model is built on coordinates that drift across runs and folds | Treat t-SNE and UMAP as visualization tools; for supervised dimensionality reduction use PCA, TruncatedSVD, or IncrementalPCA |
| Running PCA without scaling | The component with the largest absolute spread dominates the first principal direction, even when it carries no signal | Put `StandardScaler` upstream of PCA inside the same `Pipeline` |
| Treating principal components as "the most important factors" | Variance is a property of the inputs, not of the target; the dominant component can be unrelated to the prediction problem | Validate downstream metric quality after dimensionality reduction; do not skip the comparison to a baseline that keeps all features |
| Fitting PCA on the full dataset before cross-validation | The mean and components leak information from validation folds into training folds, giving an optimistic CV score | Put PCA inside the pipeline so each fold fits its own components on its training portion only |
| Running t-SNE with a single perplexity value | A single perplexity can produce qualitatively different shapes from neighboring values; the apparent structure may be a parameter artifact | Sweep perplexity over a small grid such as five, thirty, fifty and trust only the structure that survives |
| Reading inter-cluster distances in a t-SNE plot as literal distances | t-SNE preserves local neighborhoods and distorts global geometry; a wide gap between two visual clusters does not mean the underlying data is far apart | Talk about presence and persistence of clusters across parameter sweeps, not about the distance between them |
| Reaching for KernelPCA on a hundred-thousand-row dataset | KernelPCA scales roughly with the square of the sample count and the kernel matrix becomes infeasible at scale | Use KernelPCA only on small datasets with clear non-linear structure; use PCA, gradient boosting, or learned representations otherwise |
| Using PCA components in a regulated decision pipeline | Stakeholders cannot interpret rotated features, which makes audit and debugging harder than necessary | Prefer feature selection or regularization for interpretable pipelines, and reserve PCA for cases where dimensionality reduction is genuinely necessary |

## Quiz

1. A team adds t-SNE as a preprocessing step inside a `Pipeline` whose
   final estimator is a logistic regression classifier.
   Cross-validated accuracy looks reasonable on the historical data.
   When the pipeline is retrained on a slightly larger dataset for
   production deployment, the classifier's behavior changes
   substantially.
   What is the structural problem with this design?

<details><summary>Answer</summary>
t-SNE is a stochastic embedding method that is fit jointly over all
rows.
It does not have a stable `transform` for new data and its coordinates
depend on perplexity, initialization, and random seed.
Using it as a feature extractor inside a supervised pipeline means the
classifier is being trained on coordinates that change every time the
embedding is refit.
The fix is to remove t-SNE from the pipeline and replace it with PCA or
TruncatedSVD if dimensionality reduction is genuinely needed, or to
abandon dimensionality reduction entirely and rely on better feature
engineering and a more flexible classifier.
</details>

2. A practitioner fits PCA on a dataset with one column representing
   annual revenue in dollars and another representing customer age in
   years, without scaling.
   The first principal component aligns almost perfectly with revenue.
   Is this informative?

<details><summary>Answer</summary>
No.
PCA maximizes variance, and revenue measured in dollars has a far larger
absolute variance than age measured in years for trivial reasons of
units rather than reasons of signal.
The first component is a near-restatement of the revenue column.
The fix is to put `StandardScaler` upstream of PCA so all features
contribute on comparable scales, after which the components reflect
joint structure rather than the largest unit.
</details>

3. A researcher runs t-SNE three times on the same dataset with the
   default parameters and notices that the resulting plots differ in
   the size and position of the clusters, even though the cluster
   memberships look similar.
   How should this affect their interpretation?

<details><summary>Answer</summary>
The qualitative cluster structure is the trustworthy signal because it
survives across runs.
The size and position of clusters in a t-SNE plot are not literal
readings of the data; t-SNE preserves local neighborhoods rather than
global geometry, and inter-cluster distances are not metric distances in
the original feature space.
The researcher should describe the data as having a certain number of
identifiable groups without making claims about how far apart those
groups are.
</details>

4. A team has a TF-IDF feature matrix with thirty thousand columns and
   a few hundred thousand documents.
   They want to apply dimensionality reduction before logistic
   regression.
   Which method is the right default and why?

<details><summary>Answer</summary>
TruncatedSVD is the right default.
It does not center the data, which preserves the sparsity of the
TF-IDF matrix and avoids densifying it into a much larger memory
footprint.
It produces a deterministic linear projection with a proper `transform`
method, so it slots cleanly into a supervised pipeline.
Regular PCA would force the sparse matrix to dense. t-SNE would not be
appropriate either, because it has no out-of-sample `transform` and is a
visualization tool rather than a feature extractor. UMAP does expose a
`transform`, but its stochastic non-linear embedding is better suited to
exploration than to a stable, reproducible production feature pipeline.
</details>

5. A practitioner sets `n_components=0.95` in PCA and is surprised to
   see that the number of components selected differs slightly across
   cross-validation folds.
   Should they worry?

<details><summary>Answer</summary>
Probably not.
A float value for `n_components` tells PCA to keep enough components to
explain ninety-five percent of the variance in the training portion of
each fold, and small differences in the data lead to small differences
in the chosen component count.
For most production work this is acceptable.
If absolute reproducibility across folds is required, fix
`n_components` to a specific integer chosen from a prior exploration on
the full training set.
</details>

6. A small dataset with two interlocking spirals will not separate
   linearly in the original feature space.
   A practitioner wants to use a dimensionality-reduction step that
   preserves the non-linear geometry.
   They are considering KernelPCA, t-SNE, and UMAP.
   What is the difference in role between these three?

<details><summary>Answer</summary>
KernelPCA is a non-linear projection: it produces a deterministic
forward map via the kernel trick and supports `transform` on new data,
which makes it usable as a supervised preprocessing step on small
datasets where the chosen kernel actually captures the structure.
t-SNE and UMAP are visualization-first embeddings: they preserve local
neighborhoods, are stochastic, and depend on parameters such as
perplexity or `n_neighbors` and `min_dist`.
For visualizing the spirals, t-SNE or UMAP will likely produce the most
striking image; for using the reduced representation as a feature in a
supervised pipeline, KernelPCA is the safer choice on a small dataset.
</details>

7. A team observes that running PCA before logistic regression hurts
   their downstream accuracy.
   What is a likely explanation, and what should they try?

<details><summary>Answer</summary>
The most common explanation is that the target signal lives along a
direction that does not have particularly large variance in the inputs.
PCA orders components by variance, so a low-variance but
target-relevant direction can be discarded when the practitioner trims
to a fixed number of components.
The team should compare against a baseline with no dimensionality
reduction, try a higher variance-retention threshold, or move to
regularized logistic regression from
[Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/),
which addresses multicollinearity without rotating the feature space
away from the target.
</details>

8. A team has feature data that arrives in batches over many days and
   does not fit in memory all at once.
   They want a PCA-style dimensionality reduction step.
   Which estimator should they reach for, and what is the trade-off?

<details><summary>Answer</summary>
IncrementalPCA is the natural choice.
It exposes a `partial_fit` method that updates the component estimates
batch by batch, so memory cost is proportional to the batch size and
the number of features rather than the total sample count.
The trade-off is a small loss of statistical accuracy compared to a
full-data SVD; for most practitioner use cases the gap is small enough
to ignore, but it is worth verifying that the explained-variance ratio
profile looks similar to a regular PCA on a representative sample.
</details>

## Hands-On Exercise

- [ ] Create a new notebook or script and import `numpy`,
  `matplotlib.pyplot`, `load_digits`, `StandardScaler`, `Pipeline`,
  `LogisticRegression`, `cross_val_score`, `PCA`, `TruncatedSVD`,
  `IncrementalPCA`, `KernelPCA`, and `TSNE`.
  Optionally install `umap-learn` via `pip install umap-learn` and
  import `umap`.
- [ ] Step 1: Load the digits dataset and stand it up as a feature
  matrix `X` and target vector `y`.
  Apply `StandardScaler` to produce `X_scaled` for the methods that
  need it.
- [ ] Step 2: Build a `Pipeline` of `StandardScaler`, `PCA`, and
  `LogisticRegression`.
  Use `n_components=0.95` for PCA.
  Score it with `cross_val_score` using five folds and a meaningful
  metric for the digits problem such as accuracy or macro F1.
  Compare against a baseline pipeline without PCA and write two
  sentences explaining whether PCA helped, hurt, or was roughly
  neutral, and why that is plausible given the structure of digits
  data.
- [ ] Step 3: Repeat Step 2 with `TruncatedSVD` instead of PCA and a
  fixed integer `n_components`.
  Note that TruncatedSVD does not center the data; verify on the
  digits matrix whether that matters in practice for this dataset.
  Write a short note on when you would prefer TruncatedSVD over PCA in
  production text or recommender pipelines.
- [ ] Step 4: Replace PCA with `IncrementalPCA` in the same pipeline,
  pretending the data is too large for memory by feeding it in chunks
  via `partial_fit`.
  Compare the explained-variance ratio profile against the full-data
  PCA from Step 2 and write one sentence on whether the difference is
  practically meaningful.
- [ ] Step 5: Fit `KernelPCA` with an `rbf` kernel and a small
  `n_components` on a subsample of the digits data.
  Plot the first two kernel components colored by `y`.
  Note the runtime relative to PCA and write one sentence on the
  scaling behavior you observed.
- [ ] Step 6: Run a t-SNE perplexity sweep over values such as five,
  fifteen, thirty, and fifty on `X_scaled`, with `init='pca'` and
  `learning_rate='auto'`, and plot the four embeddings side by side.
  For each plot, identify which structural features are stable across
  perplexities and which appear and disappear.
  Write one sentence per perplexity describing what you would and
  would not be willing to claim about the data based on that plot.
- [ ] Step 7 (optional, if `umap-learn` is installed): Run UMAP with
  the default `n_neighbors=15` and `min_dist=0.1` on the same data.
  Then re-run with `n_neighbors=5` and with `min_dist=0.5`, plotting
  all three side by side.
  Write one sentence on what changed, and one sentence comparing the
  UMAP plots to the t-SNE plots from Step 6.
- [ ] Step 8 (deliberate leakage demonstration): Take the t-SNE
  embedding from Step 6 — fit on the full `X_scaled` once — and naively
  use its two-dimensional output as features for a logistic regression.
  Run `cross_val_score` on `(embedding, y)` and record the score.
  Then attempt the same comparison "honestly" by trying to put t-SNE
  inside a `Pipeline` before logistic regression. Observe that
  `TSNE` does not implement `transform()`, so the pipeline cannot
  refit per-fold and there is no fair way to evaluate it.
  Write a short paragraph naming both failure modes: (a) the naive
  cross-validation score is biased upward because the embedding saw
  every held-out row at fit time — this is a textbook leakage pattern
  per [Module 1.3](../module-1.3-model-evaluation-validation-leakage-and-calibration/),
  and (b) the "fix" of moving t-SNE into the pipeline is structurally
  unavailable, which is the deeper reason t-SNE is not a supervised
  preprocessing tool. For UMAP, repeat the experiment with `umap.UMAP`
  inside a `Pipeline` (UMAP supports `transform()`) and compare its
  fold-safe cross-validation score against the Step 2 PCA baseline.
  Note that "fold-safe" does not mean "good idea" — observe whether
  the score actually improves over PCA.
- [ ] Completion check: confirm that every method that requires scaling
  was scaled inside its pipeline rather than once globally.
- [ ] Completion check: confirm that the t-SNE and UMAP plots were
  used to discuss qualitative structure that survived parameter
  sweeps, not the absolute coordinates or distances.
- [ ] Completion check: confirm that the final shipping recommendation
  separates "tools used for visualization" from "tools used for
  supervised preprocessing" and names a specific defensible default
  for each role on this dataset.

## Sources

- https://scikit-learn.org/stable/modules/decomposition.html
- https://scikit-learn.org/stable/modules/manifold.html
- https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html
- https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.TruncatedSVD.html
- https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.IncrementalPCA.html
- https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.KernelPCA.html
- https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html
- https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.FastICA.html
- https://scikit-learn.org/stable/auto_examples/manifold/plot_t_sne_perplexity.html
- https://scikit-learn.org/stable/auto_examples/decomposition/plot_pca_iris.html
- https://umap-learn.readthedocs.io/en/latest/
- https://umap-learn.readthedocs.io/en/latest/parameters.html

## Next Module

Continue to [Module 1.11: Hyperparameter Optimization](../module-1.11-hyperparameter-optimization/).
