---
title: "Unsupervised Learning: Clustering"
description: "Learn how to choose, fit, and evaluate clustering methods when there are no labels. This module focuses on scaling discipline, algorithm assumptions, and honest validation."
slug: ai-ml-engineering/machine-learning/module-1.8-unsupervised-learning-clustering
sidebar:
  order: 8
---

> Track: AI/ML Engineering | Complexity: Intermediate | Time: 75-90 minutes
> Prerequisites: [Module 1.1: Scikit-learn API & Pipelines](../module-1.1-scikit-learn-api-and-pipelines/), [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/), [Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/), and [Module 1.7: Naive Bayes, k-NN & SVMs](../module-1.7-naive-bayes-knn-and-svms/).

## Learning Outcomes

1. **Choose** the appropriate clustering algorithm (k-means/MiniBatchKMeans, DBSCAN/HDBSCAN, AgglomerativeClustering, GaussianMixture) given the suspected cluster shape, dataset size, and whether noise points are meaningful, citing the assumption each algorithm makes.

2. **Diagnose** silent clustering failures (unscaled distance-based features, k-means on non-spherical data, DBSCAN with poorly tuned `eps`, single-linkage chaining) by inspecting the data shape, the scaling pipeline, and the algorithm's internal score.

3. **Evaluate** clusterings without ground-truth labels using `silhouette_score`, `calinski_harabasz_score`, and `davies_bouldin_score`, and **explain** why agreement among internal metrics does not imply the partition is correct.

4. **Decide** the number of clusters using elbow analysis, silhouette analysis, BIC for `GaussianMixture`, and stability under re-fitting, while justifying why each criterion can mislead in isolation.

5. **Justify** when clustering is the wrong tool — naming the supervised alternative from [Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/), [Module 1.5: Decision Trees & Random Forests](../module-1.5-decision-trees-and-random-forests/), or [Module 1.6: XGBoost & Gradient Boosting](../module-1.6-xgboost-gradient-boosting/) when labels exist, or pointing to [Module 1.9: Anomaly Detection & Novelty Detection](../module-1.9-anomaly-detection-and-novelty-detection/) or [Module 1.10: Dimensionality Reduction](../module-1.10-dimensionality-reduction/) when those are the actual question.

## Why This Module Matters

Your team already has a disciplined supervised workflow. After
[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/)
and [Module 1.7: Naive Bayes, k-NN & SVMs](../module-1.7-naive-bayes-knn-and-svms/),
you know how to separate training from evaluation, how to scale distance-based
models, and how to explain why a metric went up or down.

Then product asks for something different: "Find the natural customer
segments in this behavioral feature table." There is no label, no target, and
no obvious success metric that behaves like supervised accuracy. The request
sounds familiar because it still involves features and a model, but the
discipline changes immediately.

The scikit-learn clustering user guide,
https://scikit-learn.org/stable/modules/clustering.html, is the right tone
setter here because it treats clustering as a family of assumptions about data
shape rather than a button you press to reveal truth. That is the core
mindset shift for this module.

In supervised learning, you can usually say what "good" means before you fit
the model. In clustering, you often cannot. A partition can look neat, score
well on internal metrics, and still fail the actual business question because
it grouped points by a numerical artifact rather than by a meaningful pattern.

This is why clustering projects disappoint so often. The algorithm always
returns something, even when the data do not support the story you want to
tell. If the team mistakes "the model produced clusters" for "we discovered
real structure," it ships a story instead of evidence.

The right goal is more modest and more rigorous. You want to determine whether
the data show structure that survives scaling choices, algorithm choice,
re-fitting, and domain inspection. If the answer is no, the honest outcome is
not failure. The honest outcome is that clustering was not the right tool for
the question.

That honesty matters in production settings. Clustering often sits upstream of
campaign design, operations handoffs, analyst dashboards, or later supervised
labeling work. A weak clustering choice can quietly distort all of those
downstream decisions even though nothing "crashes."

This module teaches the practical habits that reduce that risk. You will match
algorithm assumptions to data shape, treat internal metrics as sanity checks
rather than truth, and defend your choices in terms that make sense to both
engineers and domain owners.

## Section 1: Why Clustering Projects Disappoint

Clustering is attractive because it promises discovery without labels. That
promise is real in some settings, but it is easy to overread. The model can
only partition the feature space you provide, using the similarity notion that
your preprocessing and algorithm encode.

That sounds abstract until you see how many choices are hiding inside it. Are
you measuring Euclidean distance, local density, or probabilistic component
membership? Are large-magnitude numeric columns dominating the geometry? Are
you asking for flat segments when the data might have a hierarchy instead?

A team with a strong supervised pipeline sometimes carries over the wrong
expectations. They expect a held-out test score, a single best model, and a
clear answer to "what is the right number of groups?" Clustering rarely gives
you any of those in the same clean way.

Instead, clustering gives you candidates. Those candidates can be useful if
they line up with stable structure in the data and if domain experts can make
sense of them. They become dangerous when teams confuse compactness with
correctness.

This is why "natural customer segments" is a risky phrase. It sounds as if the
segments are already present in a clean, objective form, waiting to be
extracted. In practice, the result depends on feature design, scaling, the
algorithm family, and what kinds of variation you want the model to ignore.

A useful first question is not "which clustering method is best?" It is "what
kind of structure do we suspect?" If the answer is compact spherical groups,
k-means can be sensible. If the answer is curved shapes with noise points,
density-based methods may be a better fit.

A second useful question is "what would make the result actionable?" If no one
can explain how a cluster would change messaging, triage, or later modeling,
the partition may be visually interesting but operationally empty. That is not
a modeling failure. It is a problem-framing failure.

A third useful question is "what would falsify the result?" If the clusters
change dramatically when you refit on bootstrap subsamples, or disappear after
proper scaling, or map only to a single high-range feature, the clustering is
not stable enough to trust. This is the unsupervised analog of the discipline
you built earlier in
[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/).

The important shift is to treat clustering as structured exploration. That
does not make it soft or vague. It means the standards are different: match
assumptions to geometry, validate with stability and domain review, and be
ready to say that no useful segmentation emerged.

## Section 2: k-means and k-means++

k-means is often the first clustering algorithm people learn because the basic
loop is simple. Assign each point to the nearest centroid, recompute each
centroid as the mean of the points assigned to it, and repeat until the
solution stops improving. This is the classic Lloyd-style pattern.

That simplicity is useful, but it hides strong assumptions. The algorithm
works in a Euclidean geometry and summarizes each cluster by a mean. That
immediately suggests what kinds of patterns it likes: compact groups that can
be represented well by central points.

Initialization matters because a poor starting point can send the optimization
toward a weak local minimum. That is why `k-means++` became the default
initialization strategy. Instead of picking centroids carelessly, it chooses
initial centers in a way that spreads them out and usually leads to better
starts.

You also need to understand the current `n_init` behavior. With
`n_init="auto"`, scikit-learn runs once when `init="k-means++"` and ten times
when `init="random"`. The default `init` is `"k-means++"`, which is usually
what you want unless you have a specific reason to experiment.

The most common silent failure is not initialization. It is scaling. k-means
uses Euclidean distance, so a feature with a larger numeric range can dominate
the partition even if it is not the most meaningful signal. The scaling
discipline from
[Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/)
and the distance-model warning from
[Module 1.7: Naive Bayes, k-NN & SVMs](../module-1.7-naive-bayes-knn-and-svms/)
apply here directly.

If you remember why unscaled inputs break k-NN or SVMs, you already understand
why unscaled inputs break k-means. The same family of footgun is back. The
difference is that in clustering you do not have labels to warn you with an
obviously collapsed downstream score.

The user guide states the shape assumption in plain language:
"Inertia makes the assumption that clusters are convex and isotropic, which is
not always the case. It responds poorly to elongated clusters, or manifolds
with irregular shapes." That sentence should stay in your head whenever
someone treats a low inertia as proof that the partition is meaningful.

Inertia is useful, but only as a local diagnostic. It is the within-cluster
sum of squared distances to centroids, so it always decreases as `k`
increases. That means inertia alone cannot tell you the right number of
clusters, because the metric rewards adding more centroids.

Another frequent mistake is to call `KMeans.score(X)` a performance score or
even "accuracy." It is not. For k-means, `score` is tied to the objective and
is not a supervised notion of predictive quality. Use `.fit_predict()` to
obtain labels, inspect `.inertia_` for the fitted model, and evaluate with
internal metrics only as sanity checks.

> **Pause and predict** — If one feature is measured on a much larger numeric
> range than the others, what do you expect k-means to do before you read the
> example below? Commit to an answer in words, not just "it gets worse."

The safest way to use k-means in practice is inside a pipeline that makes the
scaling step explicit. That protects you from accidental inconsistencies and
keeps the geometry you are relying on visible to reviewers. The runnable
example below shows a proper pipeline and then contrasts it with an unscaled
variant.

```python
import matplotlib.pyplot as plt
import numpy as np
from sklearn.cluster import KMeans
from sklearn.datasets import make_blobs
from sklearn.metrics import silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

X, _ = make_blobs(centers=4, random_state=0)

scaled_pipeline = Pipeline(
    steps=[
        ("scale", StandardScaler()),
        ("cluster", KMeans(n_clusters=4, n_init="auto", random_state=0)),
    ]
)

scaled_labels = scaled_pipeline.fit_predict(X)
scaled_inertia = scaled_pipeline.named_steps["cluster"].inertia_
scaled_silhouette = silhouette_score(
    scaled_pipeline.named_steps["scale"].transform(X),
    scaled_labels,
)

X_unscaled = X.copy()
X_unscaled[:, 0] = X_unscaled[:, 0] * 100

unscaled_model = KMeans(n_clusters=4, n_init="auto", random_state=0)
unscaled_labels = unscaled_model.fit_predict(X_unscaled)
unscaled_inertia = unscaled_model.inertia_
unscaled_silhouette = silhouette_score(X_unscaled, unscaled_labels)

print("Scaled inertia:", scaled_inertia)
print("Scaled silhouette:", scaled_silhouette)
print("Unscaled inertia:", unscaled_inertia)
print("Unscaled silhouette:", unscaled_silhouette)

fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
axes[0].scatter(X[:, 0], X[:, 1], c=scaled_labels, cmap="tab10")
axes[0].set_title("Scaled Pipeline")
axes[1].scatter(X_unscaled[:, 0], X_unscaled[:, 1], c=unscaled_labels, cmap="tab10")
axes[1].set_title("Unscaled Feature Dominates")
plt.tight_layout()
plt.show()
```

The important point is not the exact values that print. The important point is
that the unscaled setup changes the geometry the algorithm sees. Once one
column is stretched far more than the others, centroid assignment begins to
reflect that distortion rather than the structure you intended to discover.

This is also why k-means discussions need data-shape language, not just metric
language. A model can produce a clean partition of the wrong geometry. If your
groups are curved, nested, or elongated, the centroids can look stable while
the assignment boundary is conceptually wrong.

That is not a reason to avoid k-means. It is a reason to use it where it fits.
If you suspect roughly spherical, similarly sized groups and you want a fast,
simple baseline, k-means remains a strong place to start. If you need more
than that, change the algorithm rather than forcing the data into the wrong
story.

## Section 3: MiniBatchKMeans for Scale

Full-batch k-means repeatedly touches the entire dataset. When `N` becomes
very large, that is expensive in both time and memory movement. You may still
want a centroid-based segmentation, but you need a cheaper update rule.

`MiniBatchKMeans` addresses that by updating centroids from small random
batches instead of the full dataset at each pass. The result is usually much
faster and slightly noisier. That tradeoff is often appropriate for a first
segmentation pass, especially when the business question is exploratory.

The default `batch_size` is `1024`, and that change matters because it reflects
how the estimator is intended to behave in modern scikit-learn usage. Smaller
batches can make updates noisier. Larger batches can look more like full-batch
behavior but give back some of the speed advantage.

You should not mentally classify MiniBatchKMeans as a different family of
model. It inherits the same geometric assumptions as k-means. It still wants
distance-aware preprocessing, and it still does not solve the "right `k`"
problem for you.

If you are working with sparse, high-dimensional data, the user guide
recommends multiple `n_init` runs. That is a practical reminder that faster
optimization does not remove sensitivity to initialization and data geometry.
It only changes how the centroids get updated.

The API shape is intentionally close to `KMeans`, so swapping it into a
pipeline is straightforward. That makes it a good operational choice when the
dataset scale grows faster than the need for perfect centroid refinement.

```python
from sklearn.cluster import MiniBatchKMeans
from sklearn.datasets import make_blobs
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

X, _ = make_blobs(centers=4, random_state=0)

pipeline = Pipeline(
    steps=[
        ("scale", StandardScaler()),
        (
            "cluster",
            MiniBatchKMeans(
                n_clusters=4,
                n_init="auto",
                random_state=0,
                batch_size=1024,
            ),
        ),
    ]
)

labels = pipeline.fit_predict(X)
model = pipeline.named_steps["cluster"]

print("Cluster centers shape:", model.cluster_centers_.shape)
print("First ten labels:", labels[:10])
```

The decision to use MiniBatchKMeans should be framed as a cost-quality choice,
not as a conceptual change in what clustering means. If your reviewers ask why
you chose it, the answer is about scale and latency, not about handling
non-convex structure or noise points better. It does neither.

That distinction matters because teams sometimes escalate to larger data and
quietly downgrade their validation standards. Faster fitting is useful. Faster
fitting of the wrong geometry is still wrong. Keep the same scrutiny around
scaling, shape assumptions, and downstream meaning.

## Section 4: Choosing k — and Why No Single Criterion Is Enough

Choosing the number of clusters is where many clustering discussions become
overconfident. People want a clean answer because supervised workflows train
them to expect one. Clustering usually offers several imperfect signals rather
than a single authoritative criterion.

The elbow method looks at inertia as `k` increases. Because inertia always
decreases, you are looking for a knee where additional clusters stop buying
much improvement. This can be useful when the bend is visually sharp, but on
messier real data the curve is often smooth and ambiguous.

Silhouette analysis adds another lens. The score ranges from `-1` to `+1`,
with higher values indicating that points are, on average, closer to their own
cluster than to neighboring clusters. That sounds ideal until you remember
what it rewards: compact, well-separated partitions.

This is why internal metrics do **not** tell you the right `k`. They tell you
that the partition is compact at that `k`. Those are not the same statement.
The distinction is essential, and it becomes obvious in the silhouette gallery
example:
https://scikit-learn.org/stable/auto_examples/cluster/plot_kmeans_silhouette_analysis.html

That example is valuable because it shows a situation where a two-cluster
partition can look better to silhouette than a four-cluster partition on data
generated from four blobs. Why? Because merging nearby true groups can produce
a more compact, simpler partition even though it erases meaningful structure.
Compactness won the metric contest, not the semantic one.

Calinski-Harabasz and Davies-Bouldin add more internal signals. Higher
Calinski-Harabasz is better. Lower Davies-Bouldin is better, with zero as the
theoretical minimum. Both can be informative, but both reward variations of
separation and compactness.

That shared preference means agreement among internal metrics is weaker
evidence than it first appears. If they all reward similar geometry, they can
all be fooled by the same mismatch between algorithm and data shape. Agreement
is a sanity check, not independent confirmation.

Gap statistic is sometimes discussed as another option. It compares observed
clustering structure to what would be expected under a null reference. It is a
reasonable idea, but in practice many teams still need the same judgment calls
about preprocessing, stability, and domain meaning afterward.

If you want a disciplined workflow, use internal metrics to narrow the field,
not to finish the argument. Then ask whether the candidate partition is stable
under re-fitting, whether it survives feature changes, and whether domain
owners can explain the groups in terms that matter outside the notebook.

The code below evaluates several values of `k` using inertia, silhouette,
Calinski-Harabasz, and Davies-Bouldin. It does not claim to discover the truth.
It creates a structured comparison that you can combine with plotting and later
domain review.

```python
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.datasets import make_blobs
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

X, _ = make_blobs(centers=4, random_state=0)

ks = range(2, 9)
inertias = []
silhouettes = []
calinski_scores = []
davies_scores = []

for k in ks:
    pipeline = Pipeline(
        steps=[
            ("scale", StandardScaler()),
            ("cluster", KMeans(n_clusters=k, n_init="auto", random_state=0)),
        ]
    )
    labels = pipeline.fit_predict(X)
    X_scaled = pipeline.named_steps["scale"].transform(X)

    inertias.append(pipeline.named_steps["cluster"].inertia_)
    silhouettes.append(silhouette_score(X_scaled, labels))
    calinski_scores.append(calinski_harabasz_score(X_scaled, labels))
    davies_scores.append(davies_bouldin_score(X_scaled, labels))

fig, axes = plt.subplots(2, 2, figsize=(10, 8))
axes[0, 0].plot(list(ks), inertias, marker="o")
axes[0, 0].set_title("Inertia")
axes[0, 1].plot(list(ks), silhouettes, marker="o")
axes[0, 1].set_title("Silhouette")
axes[1, 0].plot(list(ks), calinski_scores, marker="o")
axes[1, 0].set_title("Calinski-Harabasz")
axes[1, 1].plot(list(ks), davies_scores, marker="o")
axes[1, 1].set_title("Davies-Bouldin")

for ax in axes.ravel():
    ax.set_xlabel("k")

plt.tight_layout()
plt.show()
```

If all four plots point toward the same `k`, that is useful. It means the
partition is internally coherent by several related standards. It still does
not mean you found the one correct segmentation of the real-world phenomenon
behind the data.

This is why the right phrasing in a design review is careful. Say that the
chosen `k` is the most defensible among the candidates you tested, given the
current feature set, scaling pipeline, internal diagnostics, and domain review.
Do not say that the model proved there are exactly that many segments.

> **Pause and reflect** — Suppose your inertia curve has no clear elbow, your
> silhouette prefers a smaller `k`, and domain experts care about a slightly
> larger segmentation that is still stable. Which signal should dominate, and
> why is that answer different from a supervised model-selection argument?

A strong answer usually puts downstream usefulness and stability above raw
internal compactness. If the larger segmentation remains interpretable,
stable, and operationally distinct, it may be the better choice. If the
difference survives only inside one metric plot, it is probably too fragile.

## Section 5: DBSCAN and Density-Based Clustering

DBSCAN starts from a different picture of what a cluster is. Instead of asking
for centroids, it asks whether points live in dense regions separated by
sparser neighborhoods. That change in assumption makes the method useful for
data shapes that k-means handles poorly.

The model distinguishes among core points, border points, and noise points. A
core point has enough neighbors within a radius to support a dense region. A
border point is attached to a dense region but does not itself have the same
neighbor count. A noise point is assigned label `-1`.

That noise label matters because it turns clustering into a partial bridge
toward
[Module 1.9: Anomaly Detection & Novelty Detection](../module-1.9-anomaly-detection-and-novelty-detection/).
DBSCAN is not a dedicated anomaly detector, but it is explicitly willing to
say that some points do not belong to any dense cluster.

The two main knobs are `eps` and `min_samples`. `eps` defines the neighborhood
radius. `min_samples` defines how much local support is needed before a point
acts like the seed of a dense region. The defaults are not universal truths.
They are starting values.

This is where a lot of misuse happens. Teams drop `DBSCAN()` onto data of
unknown scale and interpret the output as structure. That is not disciplined.
If the feature scales are inconsistent, the radius has no coherent meaning, so
the neighborhood test is already broken before the algorithm begins.

The k-distance plot is a common heuristic for choosing `eps`. You sort each
point's distance to its `k`th nearest neighbor and look for a bend. Even then,
you are still using a heuristic, not a proof. The result needs the same
stability and domain scrutiny as every other clustering choice.

DBSCAN is powerful when you expect non-convex shapes. It can recover curved or
arbitrary structures because it does not force each group to orbit a centroid.
It also decides the cluster count from the data rather than requiring you to
set `k` in advance.

Its main weakness appears when clusters have very different densities. A
single global `eps` can be too small for one region and too large for another.
That limitation is one of the reasons HDBSCAN exists, and it is why you should
avoid treating DBSCAN as a universal replacement for k-means.

The example below uses `make_moons`, a classic shape where centroid methods are
a poor fit but density methods make intuitive sense. The code prints the number
of detected clusters and the count of points labeled as noise.

```python
import matplotlib.pyplot as plt
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.datasets import make_moons
from sklearn.preprocessing import StandardScaler

X, _ = make_moons(random_state=0)

X_scaled = StandardScaler().fit_transform(X)

model = DBSCAN(eps=0.3, min_samples=10)
labels = model.fit_predict(X_scaled)

n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
n_noise = np.sum(labels == -1)

print("Clusters found:", n_clusters)
print("Noise points:", n_noise)

plt.scatter(X_scaled[:, 0], X_scaled[:, 1], c=labels, cmap="tab10")
plt.title("DBSCAN on Scaled Two-Moons Data")
plt.show()
```

The output is easy to summarize in words even before you stare at the plot.
DBSCAN is free to return both clusters and noise. That is often exactly what
you want in messy behavioral data where not every point deserves assignment to
a tidy segment.

The scaling step still matters here because distance is still part of the
story. The lesson from
[Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/)
does not disappear just because the algorithm is density-based. What changes is
the shape assumption, not the importance of coherent geometry.

A good design-review defense of DBSCAN sounds like this: the domain suggests
non-convex structure, a fixed `k` is hard to justify, and noise points are
themselves meaningful. A weak defense sounds like this: "k-means looked odd, so
we tried DBSCAN and liked the picture."

## Section 6: HDBSCAN and Hierarchical Clustering

HDBSCAN extends the density-based idea by avoiding commitment to a single
global `eps`. Instead of choosing one density threshold and living with it, it
examines clustering behavior across a range of density levels and extracts the
most stable parts of the hierarchy. In scikit-learn, this estimator is
available as `HDBSCAN`, with `min_cluster_size` as a key control.

That makes HDBSCAN useful when different regions of the data support different
densities. Where DBSCAN can split one real group or merge another because the
global radius is wrong, HDBSCAN can sometimes preserve the stable parts of both
structures. The practical value is not magic accuracy. It is less brittleness.

The tradeoff is interpretability and tuning complexity. You no longer explain
the fit in terms of a single neighborhood radius. You explain it in terms of
stable density structure across a hierarchy. That is often a better story for
the data, but it is a more complex story for stakeholders.

Hierarchical clustering is a broader family, and
`AgglomerativeClustering` is the standard bottom-up form. It starts with each
point as its own cluster and repeatedly merges the closest available pair
until the requested stopping condition is reached. That process naturally
supports a hierarchy rather than only a flat partition.

The linkage choice controls what "closest" means. `ward`, the default linkage,
merges in a way that minimizes within-cluster variance and is only valid with
Euclidean distance. `complete` uses the maximum pairwise distance between two
candidate clusters. `average` uses the mean pairwise distance. `single` uses
the minimum pairwise distance.

These choices are not cosmetic. They produce different failure modes. Single
linkage is especially prone to chaining, where a thin bridge of nearby points
causes two visibly separate groups to collapse into one extended cluster. That
can be disastrous when the domain cares about distinct segments rather than
mere connectivity.

Ward linkage is often a reasonable baseline when you still want compact groups.
Complete linkage is a defensible alternative when you want tighter control over
cluster diameter. Average linkage can be a middle ground. Single linkage should
be used only when its connectivity bias is actually the point of the analysis.

Dendrograms are helpful when the business question is inherently hierarchical.
A flat segmentation might be too blunt if the team wants to know whether groups
split into subgroups and how those subgroups relate. In that case, the
hierarchy itself is information, not just a path to a single chosen cut.

The cost is scale. Agglomerative methods have computational behavior that is
roughly `O(n^2 log n)`, so they do not scale to millions of points in the way
that centroid methods can. That does not make them impractical. It means you
need to reserve them for datasets and questions where their richer structure is
worth the cost.

A small runnable example helps make the linkage behavior concrete. The code
below fits both Ward and single linkage on the same scaled moons data so you
can compare the resulting assignments visually.

```python
import matplotlib.pyplot as plt
from sklearn.cluster import AgglomerativeClustering
from sklearn.datasets import make_moons
from sklearn.preprocessing import StandardScaler

X, _ = make_moons(random_state=0)
X_scaled = StandardScaler().fit_transform(X)

ward_labels = AgglomerativeClustering(n_clusters=2, linkage="ward").fit_predict(X_scaled)
single_labels = AgglomerativeClustering(n_clusters=2, linkage="single").fit_predict(X_scaled)

fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
axes[0].scatter(X_scaled[:, 0], X_scaled[:, 1], c=ward_labels, cmap="tab10")
axes[0].set_title("Agglomerative: ward")
axes[1].scatter(X_scaled[:, 0], X_scaled[:, 1], c=single_labels, cmap="tab10")
axes[1].set_title("Agglomerative: single")
plt.tight_layout()
plt.show()
```

In practice, HDBSCAN and agglomerative clustering answer different kinds of
questions. HDBSCAN is still fundamentally about density and stable extraction.
Agglomerative clustering is about how groups merge under a chosen notion of
inter-cluster distance. The fact that both can produce a hierarchy does not
make them interchangeable.

This is also where problem framing matters again. If the team asks for a
single operational segmentation for downstream targeting, a full hierarchy may
be more detail than they need. If they ask how usage patterns nest or split
across an organization, the hierarchy may be the whole point.

## Section 7: Gaussian Mixture Models

Gaussian Mixture Models change the clustering story again. Instead of saying
each point belongs to exactly one cluster, a GMM says each point has a
probability of belonging to each component. That makes it a soft clustering
method rather than a hard assignment rule.

This is useful when membership is genuinely uncertain. In many real datasets,
some points sit between groups or express mixed behavior. Forcing them into one
cluster can hide useful ambiguity. A GMM lets you surface that ambiguity rather
than pretending it does not exist.

The fitting procedure is based on the EM algorithm. In the E-step, the model
computes responsibilities, which are the current probabilities that each point
belongs to each component. In the M-step, it updates the component parameters
to better match those responsibilities. The loop continues until the log
likelihood stops improving meaningfully.

A GMM is not just "k-means with probabilities." The covariance structure makes
a major difference. With `covariance_type="full"`, each component can learn its
own full covariance matrix. Other choices include `tied`, `diag`, and
`spherical`, each imposing a different bias-variance tradeoff.

That flexibility is why GMMs are often a better fit for ellipsoidal structure
than k-means. If the groups are stretched or oriented differently, a mean plus
full covariance can capture that geometry better than a centroid plus Voronoi
assignment. If the data really look spherical, k-means may be simpler and
sufficient.

Model selection is also more principled here. `GaussianMixture` provides
`.bic()` and `.aic()` methods, and the user guide recommends BIC for choosing
the number of components. BIC penalizes model complexity more aggressively,
which is useful when flexible covariance structures could otherwise overfit.

You still need judgment. A lower BIC does not prove that the components are
meaningful business segments. It proves that, among the tested models, one
offers a better tradeoff between fit and complexity under the GMM assumption.
That is a narrower claim, and it is the right one.

The example below builds a simple elongated dataset, fits GMMs with different
component counts, and compares their BIC values. It also shows how to inspect
soft membership through `predict_proba`.

```python
import matplotlib.pyplot as plt
import numpy as np
from sklearn.datasets import make_blobs
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

X, _ = make_blobs(centers=3, random_state=0)
transform = np.array([[0.6, -0.6], [-0.4, 0.8]])
X = X @ transform
X = StandardScaler().fit_transform(X)

components = range(1, 7)
bics = []

for n_components in components:
    gmm = GaussianMixture(
        n_components=n_components,
        covariance_type="full",
        random_state=0,
    )
    gmm.fit(X)
    bics.append(gmm.bic(X))

best_n = list(components)[int(np.argmin(bics))]
best_gmm = GaussianMixture(
    n_components=best_n,
    covariance_type="full",
    random_state=0,
)
best_gmm.fit(X)

labels = best_gmm.predict(X)
probs = best_gmm.predict_proba(X)

print("Best component count by BIC:", best_n)
print("First five soft assignments:")
print(probs[:5])

plt.scatter(X[:, 0], X[:, 1], c=labels, cmap="tab10")
plt.title("GaussianMixture Clustering")
plt.show()
```

When should you choose a GMM over k-means? Choose it when the cluster shape is
better described as ellipsoidal than spherical, when soft membership matters,
or when BIC-based component selection gives you a cleaner model-selection story
than inertia and silhouette alone. Choose k-means when you need a fast, simple
hard partition and the geometry supports it.

There is also a practical caution. `covariance_type="full"` can become too
parameter-heavy on a tiny dataset. If the sample is small relative to the
feature space, simpler covariance structures like `diag` or `spherical` can be
more stable and easier to justify. Flexibility is only an advantage when the
data can support it.

> **Pause and predict** — If the business wants to tag some users as "mostly in
> segment A but partially in segment B," which part of the GMM output should
> matter more than the hard labels, and why would k-means be awkward here?

A strong answer points to component probabilities, not just the final predicted
component. That is the whole reason to prefer a mixture model in the first
place. If you reduce the output back to hard labels immediately, you may be
discarding the most valuable part of the model.

## Section 8: Evaluation Without Labels

This is the section that keeps clustering honest. In supervised learning, you
usually know how to separate fitting from evaluation, and you can often ground
the discussion in a held-out metric. In clustering, evaluation without labels
is fundamentally different.

Internal metrics are about geometry. `silhouette_score`,
`calinski_harabasz_score`, and `davies_bouldin_score` all reward partitions
that are compact and well separated in feature space. That can be useful, but
it does not answer whether the grouping is meaningful in the domain.

This distinction cannot be treated as a footnote. If two candidate
segmentations differ in a way that matters operationally, internal metrics may
still prefer the more compact one that collapses useful nuance. Geometry and
meaning are related, but they are not identical.

External metrics exist when labels are available for comparison. The common
choices are Adjusted Rand Index through `adjusted_rand_score`, normalized
mutual information through `normalized_mutual_info_score`, and V-measure
through `v_measure_score`. These are useful when you have ground-truth classes
or some trusted reference partition.

But when you truly do not have labels, internal metrics must be paired with
stability checks. Refit the model on bootstrap subsamples or perturbed
versions of the data and see whether the partition structure survives. If the
clusters change dramatically under small shifts, they are not robust enough to
carry much meaning.

This is the clustering analog of leakage and over-interpretation from
[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/).
If you `fit_predict` on the full dataset and report `silhouette_score` on that
same dataset as if it were out-of-sample evidence, you are overstating what you
learned. The score is descriptive of that fit, not a generalization guarantee.

A minimal stability workflow can be built with repeated resampling and a
partition-agreement measure. The code below uses bootstrap subsamples and ARI
between overlapping predictions as a simple check. The goal is not to produce
a single magic stability number. The goal is to force the model to survive
re-fitting.

```python
import numpy as np
from sklearn.cluster import KMeans
from sklearn.datasets import make_blobs
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

X, _ = make_blobs(centers=4, random_state=0)

base_pipeline = Pipeline(
    steps=[
        ("scale", StandardScaler()),
        ("cluster", KMeans(n_clusters=4, n_init="auto", random_state=0)),
    ]
)
base_labels = base_pipeline.fit_predict(X)
base_score = silhouette_score(
    base_pipeline.named_steps["scale"].transform(X),
    base_labels,
)

rng = np.random.default_rng(0)
stability_scores = []

for _ in range(5):
    sample_idx = rng.integers(0, len(X), len(X))
    unique_idx = np.unique(sample_idx)

    X_sample = X[unique_idx]
    pipeline = Pipeline(
        steps=[
            ("scale", StandardScaler()),
            ("cluster", KMeans(n_clusters=4, n_init="auto", random_state=0)),
        ]
    )
    sample_labels = pipeline.fit_predict(X_sample)

    overlap_score = adjusted_rand_score(
        base_labels[unique_idx],
        sample_labels,
    )
    stability_scores.append(overlap_score)

print("In-sample silhouette:", base_score)
print("Bootstrap agreement scores:", stability_scores)
```

Even that simple pattern teaches the right lesson. A respectable internal score
on the original fit does not guarantee stability under re-fitting. If the
partition is unstable, the right response is not to hide that fact. The right
response is to revisit feature design, algorithm choice, or the framing of the
problem.

Domain validation matters even more than stability. Once you have a few
candidate partitions, the people who know the data need to inspect them. Do
the clusters correspond to recognizable behaviors, workflows, or failure modes?
Can someone propose a different action for each cluster that is not merely
cosmetic?

This is often where good clustering projects separate themselves from bad ones.
The good ones treat domain review as part of model evaluation. The bad ones use
domain review only after they have already decided that the clustering "worked"
because the internal plots looked convincing.

A practical review checklist helps. Ask whether the clustering survives proper
scaling, whether the preferred `k` remains plausible across internal metrics,
whether the partition is stable under re-fitting, whether cluster sizes are
operationally sane, and whether humans can articulate how the groups differ.

If the answer fails on any of those fronts, the right conclusion may be to stop
clustering entirely. That conclusion is often more valuable than shipping a
fragile segmentation. Unsupervised learning is not weaker when it admits
uncertainty. It is stronger because it refuses to pretend.

## Section 9: Decision Frame — When to Reach for Each

By this point you should be thinking in terms of assumptions, not brand names.
The question is not "which clustering API do I remember?" It is "what geometry,
scale, and operational output does this problem require?"

k-means and MiniBatchKMeans are the right starting point when you want a fast
centroid baseline on data that look roughly compact and when scaling discipline
is easy to enforce. They are poor choices for curved manifolds, density
variation, and tasks where noise points are themselves meaningful.

DBSCAN and HDBSCAN are the right tools when cluster shape is likely non-convex
and when a fixed cluster count is hard to justify. They are especially useful
when the model should be allowed to leave some points unassigned. Their main
risk is sensitivity to density assumptions and scale choices.

Agglomerative clustering is attractive when hierarchy matters or when you want
to inspect how groups merge under different linkage rules. It is less attractive
when the dataset is extremely large or when reviewers only need a fast, flat,
operational segmentation. Its main strength is structural insight, not scale.

GMMs are useful when cluster membership is soft, when ellipsoidal structure is
more plausible than spherical structure, or when BIC gives you a more honest
component-selection story. They are less attractive when you need a simple,
hard partition or when the data are too small to support flexible covariance.

The table below is a compact decision frame you can use in reviews.

| Method | Primary regime | Scaling required | Complexity scales like | Handles noise | Handles non-convex shapes | Common alternatives |
| --- | --- | --- | --- | --- | --- | --- |
| `KMeans` / `MiniBatchKMeans` | Compact centroid-style segments, large tabular baselines | Yes for distance-based features; see [Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/) and [Module 1.7: Naive Bayes, k-NN & SVMs](../module-1.7-naive-bayes-knn-and-svms/) | Iterative centroid updates; MiniBatch is cheaper on very large `N` | No | No | `GaussianMixture`, `DBSCAN`, `HDBSCAN` |
| `DBSCAN` / `HDBSCAN` | Density-separated groups with possible outliers | Usually yes, because neighborhood distances still depend on scale | Neighborhood search and density extraction | Yes, explicit `-1` noise for DBSCAN | Yes | `AgglomerativeClustering`, [Module 1.9: Anomaly Detection & Novelty Detection](../module-1.9-anomaly-detection-and-novelty-detection/) |
| `AgglomerativeClustering` | Hierarchical structure or flat cuts from a hierarchy | Often yes for Euclidean interpretations | Roughly `O(n^2 log n)` | Not explicitly | Sometimes, depends on linkage and geometry | `HDBSCAN`, `KMeans` |
| `GaussianMixture` | Ellipsoidal groups and soft membership | Usually yes for stable geometry | EM over component parameters | Not explicitly | Limited by Gaussian component assumptions | `KMeans`, [Module 1.11: Hyperparameter Optimization](../module-1.11-hyperparameter-optimization/) for tuning broader search spaces |

That last column matters because clustering is rarely the only option. If you
actually have labels, you should usually leave clustering and go back to
supervised models from
[Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/),
[Module 1.5: Decision Trees & Random Forests](../module-1.5-decision-trees-and-random-forests/),
or [Module 1.6: XGBoost & Gradient Boosting](../module-1.6-xgboost-gradient-boosting/).

If the real objective is outlier finding, clustering may be a detour. Move
forward to
[Module 1.9: Anomaly Detection & Novelty Detection](../module-1.9-anomaly-detection-and-novelty-detection/).
If the real objective is high-dimensional compression or visualization before
any grouping, then
[Module 1.10: Dimensionality Reduction](../module-1.10-dimensionality-reduction/)
is probably the next place to focus.

## Section 10: Where Clustering Is the Wrong Tool

The clearest case is the easiest to forget: if you have labels, use them.
Clustering should not replace supervised learning when the task already has a
target. In that situation, the right comparison set lives in
[Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/),
[Module 1.5: Decision Trees & Random Forests](../module-1.5-decision-trees-and-random-forests/),
and [Module 1.6: XGBoost & Gradient Boosting](../module-1.6-xgboost-gradient-boosting/).

A subtler case is when the business already has a segmentation framework that
matters operationally. If teams, contracts, or reporting structures already
define groups, rediscovering alternative behavioral clusters may add confusion
rather than clarity. The model may be interesting, but the organization may
not need a new segmentation axis.

Clustering is also the wrong tool when the real question is anomaly detection.
If the team says they need to identify unusual transactions, suspicious
sessions, or rare failure patterns, a partitioning algorithm may be answering
the wrong question. That is where
[Module 1.9: Anomaly Detection & Novelty Detection](../module-1.9-anomaly-detection-and-novelty-detection/)
belongs in the conversation.

Likewise, if the actual goal is visualization or denoising, clustering can be
an awkward first move. High-dimensional structure is often easier to inspect
after projection or compression. That is the bridge to
[Module 1.10: Dimensionality Reduction](../module-1.10-dimensionality-reduction/).

Another bad fit appears when stakeholders ask for certainty that the data do
not support. If they expect a single objective proof of the correct number of
segments, no clustering algorithm will rescue that expectation. Your job is to
reset the frame, not to force a precise answer out of a vague structure.

The mature stance is simple: use clustering when the question is genuinely
about unlabeled structure and when you can validate the result with stability
and domain review. Do not use clustering to manufacture labels, justify a
prewritten story, or avoid doing the supervised or anomaly-focused work that
the problem actually requires.

## Did You Know?

- The clustering user guide explicitly warns that k-means inertia assumes convex, isotropic clusters and responds poorly to elongated or irregularly shaped manifolds. Source: https://scikit-learn.org/stable/modules/clustering.html
- `MiniBatchKMeans` changed its default `batch_size` from `100` to `1024` in scikit-learn `v1.0`, reflecting its intended use on larger workloads. Source: https://scikit-learn.org/stable/modules/generated/sklearn.cluster.MiniBatchKMeans.html
- `DBSCAN` uses label `-1` for noisy samples, while non-negative integers indicate cluster membership. Source: https://scikit-learn.org/stable/modules/generated/sklearn.cluster.DBSCAN.html
- `GaussianMixture.bic()` returns the Bayesian Information Criterion for the fitted model on `X`, and lower values are preferred. Source: https://scikit-learn.org/stable/modules/generated/sklearn.mixture.GaussianMixture.html

## Common Mistakes

| Mistake | Why it's wrong | Safer pattern |
| --- | --- | --- |
| Running k-means without `StandardScaler` in the pipeline | Euclidean distance gets dominated by high-range features, so the partition reflects scale rather than structure | Put scaling in the same pipeline and review the geometry as in [Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/) and the distance-model warning in [Module 1.7: Naive Bayes, k-NN & SVMs](../module-1.7-naive-bayes-knn-and-svms/) |
| Using k-means on non-convex or elongated clusters | The algorithm prefers centroid-friendly geometry, so compact-looking outputs can still be conceptually wrong | Test density-based methods like `DBSCAN` or `HDBSCAN`, or use `GaussianMixture` if ellipsoidal structure is plausible |
| Treating silhouette, Calinski-Harabasz, or Davies-Bouldin as the answer to "what is the right k?" | Internal metrics report compactness and separation, not semantic correctness | Use them as sanity checks, then require stability and domain validation before choosing `k` |
| Applying DBSCAN with default `eps=0.5` on data of unknown scale | The neighborhood radius becomes arbitrary if feature scales are inconsistent | Scale first when appropriate and tune `eps` with a k-distance heuristic rather than trusting the default |
| Using `AgglomerativeClustering(linkage="single")` without checking for chaining | Single linkage can connect distinct groups through thin bridges of nearby points | Prefer `ward` or `complete` unless connectivity itself is the objective |
| Choosing `GaussianMixture(covariance_type="full")` on a tiny dataset | Full covariance can explode parameter count relative to available evidence | Consider `diag` or `spherical`, then compare with `bic()` and review whether the added flexibility is justified |
| Reporting `fit_predict` plus `silhouette_score` on the same data as if it were out-of-sample evaluation | That is a descriptive fit diagnostic, not a generalization claim | Add stability checks and apply the evaluation discipline from [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/) |
| Calling `KMeans.score(X)` "accuracy" | Clustering does not have a supervised accuracy meaning here, and `score` is tied to the optimization objective | Talk about `.fit_predict()`, `.inertia_`, or internal metrics explicitly, and keep them distinct from supervised performance language |

## Quiz

### 1. A team's k-means silhouette is highest at `k=2`, but domain owners insist there are three meaningful segments. What is the most likely explanation, and what should the team do next?

<details><summary>Answer</summary>

The most likely explanation is that the two-cluster partition is more compact,
so silhouette prefers it even though it merges structure that domain owners
care about. That is exactly why internal metrics do not answer "what is the
right `k`" by themselves. The next step is to compare the `k=2` and `k=3`
solutions for stability, interpretability, and downstream actionability, using
the evaluation discipline from
[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/)
rather than treating compactness as correctness.

</details>

### 2. A k-means pipeline that looked sensible starts producing nonsensical clusters after a new monetary feature is added without scaling. What is the most likely cause, and which module covers the fix?

<details><summary>Answer</summary>

The new feature likely dominates Euclidean distance because its numeric range
is much larger than the rest of the feature table. That means k-means is now
grouping mostly by the added scale rather than by the intended multi-feature
structure. The fix is to put scaling back into the pipeline as taught in
[Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/),
with the same distance-model caution emphasized in
[Module 1.7: Naive Bayes, k-NN & SVMs](../module-1.7-naive-bayes-knn-and-svms/).

</details>

### 3. A teammate proposes `DBSCAN()` with default settings on a tabular dataset of mixed feature scales. What should change before fitting, and why?

<details><summary>Answer</summary>

The team should first make the feature geometry coherent, which usually means
scaling distance-sensitive columns before tuning `eps`. A default radius does
not have a stable meaning if one column is effectively much larger than the
others. This is the same preprocessing discipline from
[Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/),
applied to density-based neighborhoods instead of centroid assignment.

</details>

### 4. A clustering output looks beautiful in a low-dimensional projection, but the partition changes substantially when the model is refit on bootstrap subsamples. What does that imply?

<details><summary>Answer</summary>

It implies the clustering may be visually appealing but not stable enough to
trust. The model is not surviving re-fitting, so the partition may be more
sensitive to sample variation than the projection suggests. The right response
is to revisit the evaluation discipline from
[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/)
and, if the problem is mainly about projection rather than segmentation,
consider whether
[Module 1.10: Dimensionality Reduction](../module-1.10-dimensionality-reduction/)
is the better framing.

</details>

### 5. A team needs probabilistic membership such as "mostly segment A, partly segment B" rather than hard labels. Which algorithm fits, and how should component count be selected?

<details><summary>Answer</summary>

`GaussianMixture` is the better fit because it provides soft component
probabilities through `predict_proba`, which directly represents uncertain or
mixed membership. Component count should be compared with `bic()` and reviewed
for interpretability, rather than chosen by inertia. If the team later wants a
broader tuning sweep, that search discipline connects naturally to
[Module 1.11: Hyperparameter Optimization](../module-1.11-hyperparameter-optimization/).

</details>

### 6. A one-billion-row behavioral dataset needs a fast first segmentation pass. Which clustering algorithm is the most appropriate starting point, and what tradeoff does it accept?

<details><summary>Answer</summary>

`MiniBatchKMeans` is a sensible starting point because it keeps the familiar
centroid-style workflow while reducing the cost of full-batch updates. The
tradeoff is speed versus some extra noise in the centroid estimates. It still
inherits the same scaling requirements described in
[Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/)
and the same geometric limitations as k-means.

</details>

### 7. `AgglomerativeClustering(linkage="single")` collapses two visibly distinct groups into one long chain. What is this failure mode called, and what should the team try next?

<details><summary>Answer</summary>

This is the chaining failure mode of single linkage. The team should usually
switch to `ward` or `complete`, depending on whether they want variance-based
compactness or tighter cluster diameter control. If the real issue is that the
data are curved or density-driven rather than hierarchical, they should also
compare against `DBSCAN` or `HDBSCAN` instead of forcing the answer through one
linkage rule.

</details>

### 8. A team frames the task as "find anomalies in transaction data" and reaches for k-means because it is familiar. What is the likely better direction?

<details><summary>Answer</summary>

The likely better direction is anomaly-focused tooling rather than partitioning
the full dataset into centroid-based segments. That means moving forward to
[Module 1.9: Anomaly Detection & Novelty Detection](../module-1.9-anomaly-detection-and-novelty-detection/)
instead of forcing a clustering answer onto a question that is really about
rare or suspicious points. If the team does use clustering at all, it should
be only as a supporting exploratory step, not the main detection method.

</details>

## Hands-On Exercise: Defend a Clustering Choice for an Unlabeled Feature Table

### Setup

- [ ] Create a fresh notebook or script for the exercise.
- [ ] Import `matplotlib.pyplot`, `numpy`, and the needed scikit-learn classes with normal import statements.
- [ ] Generate a blobs dataset for the centroid baseline and a moons dataset for the density baseline.
- [ ] Write a short note at the top of the file describing the business question: "Find a defensible exploratory segmentation, then explain why it should or should not ship."

### Step 1: Build a scaled k-means baseline

- [ ] Create a blobs dataset and ignore any synthetic labels during fitting.
- [ ] Build a pipeline with `StandardScaler` and `KMeans`.
- [ ] Fit the model for `k` values from `2` to `8`.
- [ ] Record inertia for each `k`.
- [ ] Record `silhouette_score` for each `k`.
- [ ] Plot both curves on separate axes.
- [ ] Write a short paragraph defending one `k` as your current baseline, while explicitly stating why inertia alone is not enough.
- [ ] Add one sentence connecting the scaling step back to [Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/).

### Step 2: Stress-test the k-means conclusion

- [ ] Refit your preferred k-means configuration on bootstrap subsamples.
- [ ] Compare the resulting partitions with a stability measure such as `adjusted_rand_score` on overlapping points.
- [ ] Note whether the segmentation is stable enough to survive re-fitting.
- [ ] Write two sentences explaining why this is the clustering analog of the evaluation discipline from [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/).
- [ ] State clearly whether a strong in-sample silhouette would be enough on its own. It should not be.

### Step 3: Compare DBSCAN on non-convex structure

- [ ] Generate `make_moons` data and apply scaling before fitting.
- [ ] Fit `DBSCAN(eps=0.3, min_samples=10)`.
- [ ] Count how many non-noise clusters were found.
- [ ] Count how many points were assigned label `-1`.
- [ ] Plot the DBSCAN assignment.
- [ ] Fit a scaled k-means baseline on the same moons dataset.
- [ ] Plot the k-means assignment beside the DBSCAN result.
- [ ] Write a short comparison explaining which algorithm better matches the data shape and why the answer is about assumptions, not just metrics.
- [ ] Add one sentence connecting DBSCAN noise points to [Module 1.9: Anomaly Detection & Novelty Detection](../module-1.9-anomaly-detection-and-novelty-detection/).

### Step 4: Fit a Gaussian Mixture baseline

- [ ] Reuse either the blobs dataset or a transformed version with elongated structure.
- [ ] Scale the features before fitting.
- [ ] Fit `GaussianMixture` models over a reasonable range of component counts.
- [ ] Compute `bic()` for each candidate model.
- [ ] Plot BIC against component count.
- [ ] Choose the preferred model by BIC and inspect `predict_proba` for several points.
- [ ] Write a short note explaining when soft membership is more useful than hard clustering.
- [ ] State whether a GMM is a better story than k-means for this dataset and why.

### Step 5: Write the shipping memo

- [ ] Write a short memo titled `Clustering Recommendation`.
- [ ] In the memo, choose one of the tested methods as the most defensible exploratory segmentation for a hypothetical customer-behavior use case.
- [ ] State the feature preprocessing assumptions that must remain true for your recommendation to hold.
- [ ] State what internal metrics supported the choice and why those metrics were not treated as proof.
- [ ] State what stability evidence supported the choice.
- [ ] State what domain validation would still be required before any operational rollout.
- [ ] Include one sentence describing what finding would invalidate the clustering and force you to reconsider the whole approach.
- [ ] Include one sentence on when you would abandon clustering and return to a supervised method from [Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/), [Module 1.5: Decision Trees & Random Forests](../module-1.5-decision-trees-and-random-forests/), or [Module 1.6: XGBoost & Gradient Boosting](../module-1.6-xgboost-gradient-boosting/).

### Completion Check

- [ ] I used a scaled pipeline for k-means rather than fitting on raw features.
- [ ] I explained why internal metrics only measure compactness and separation, not semantic correctness.
- [ ] I showed at least one case where data shape influenced the algorithm choice more than a single metric.
- [ ] I computed and interpreted a DBSCAN noise count.
- [ ] I used `bic()` to compare `GaussianMixture` models.
- [ ] I included a stability check rather than reporting only in-sample clustering diagnostics.
- [ ] I wrote a short shipping memo that names both supporting evidence and invalidation conditions.

## Sources

- User guide:
  - https://scikit-learn.org/stable/modules/clustering.html
  - https://scikit-learn.org/stable/modules/mixture.html

- API reference:
  - https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html
  - https://scikit-learn.org/stable/modules/generated/sklearn.cluster.MiniBatchKMeans.html
  - https://scikit-learn.org/stable/modules/generated/sklearn.cluster.DBSCAN.html
  - https://scikit-learn.org/stable/modules/generated/sklearn.cluster.HDBSCAN.html
  - https://scikit-learn.org/stable/modules/generated/sklearn.cluster.AgglomerativeClustering.html
  - https://scikit-learn.org/stable/modules/generated/sklearn.mixture.GaussianMixture.html
  - https://scikit-learn.org/stable/modules/generated/sklearn.metrics.silhouette_score.html
  - https://scikit-learn.org/stable/modules/generated/sklearn.metrics.calinski_harabasz_score.html
  - https://scikit-learn.org/stable/modules/generated/sklearn.metrics.davies_bouldin_score.html

- Gallery example:
  - https://scikit-learn.org/stable/auto_examples/cluster/plot_cluster_comparison.html
  - https://scikit-learn.org/stable/auto_examples/cluster/plot_kmeans_silhouette_analysis.html
  - https://scikit-learn.org/stable/auto_examples/cluster/plot_dbscan.html

## Next Module

Continue to [Module 1.9: Anomaly Detection & Novelty Detection](../module-1.9-anomaly-detection-and-novelty-detection/).
