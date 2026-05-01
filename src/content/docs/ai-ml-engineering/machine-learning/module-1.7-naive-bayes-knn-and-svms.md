---
title: "Naive Bayes, k-NN & SVMs"
description: "Learn when three compact classical models are the right fit, what assumptions they make, and how to avoid their most common operational mistakes."
slug: ai-ml-engineering/machine-learning/module-1.7-naive-bayes-knn-and-svms
sidebar:
  order: 7
---

> Track: AI/ML Engineering | Complexity: Intermediate | Time: 75-90 minutes
> Prerequisites: [Module 1.1: Scikit-learn API & Pipelines](../module-1.1-scikit-learn-api-and-pipelines/), [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/), and [Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/).

## Learning Outcomes

1. Choose the appropriate Naive Bayes variant
   (`GaussianNB`, `MultinomialNB`, `BernoulliNB`,
   `ComplementNB`) given the feature type and class balance, and
   explain why predicted probabilities should not be used as calibrated
   estimates.

2. Diagnose distance-based learner failures by inspecting whether
   features were scaled, whether dimensionality is too high for the
   kd-tree or ball-tree path, and whether the chosen distance metric
   matches the feature type.

3. Decide between a kernel SVM (`SVC` with `rbf` or `poly`) and a
   linear SVM (`LinearSVC` or `LinearSVR`) for a given dataset by
   reasoning about size, sparsity, and margin structure.

4. Compare the regularization semantics of SVM `C` to
   `LogisticRegression` `C` from
   [Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/)
   and to Ridge or Lasso `alpha`, using only scikit-learn defaults and
   one cross-validation pass.

5. Justify when each of Naive Bayes, k-NN, and SVM is the wrong tool,
   naming the alternative, usually
   [Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/)
   or [Module 1.6: XGBoost & Gradient Boosting](../module-1.6-xgboost-gradient-boosting/),
   and the reason behind the choice.

## Why This Module Matters

A team already has a working tabular pipeline, a reviewable train-test
split, and a clean deployment checklist. That is the good news. The bad
news is that three different product requests land in the same week, and
each request points to a different model family.

Before lunch, they need a fast text-spam baseline that is simple enough
to explain and quick enough to ship into a triage loop. Later that same
day, they need a similarity fallback for cold-start recommendations,
where "show me things like this" matters more than a long training job.
Then a separate owner asks for a small-data structured classifier where
the team suspects boosting would work, but the cost of tuning and
explaining it feels like overkill.

This is exactly why these three models belong together. Naive Bayes is
often the right short-path baseline for text and count features, as the
scikit-learn user guide makes clear in
https://scikit-learn.org/stable/modules/naive_bayes.html. Nearest
neighbors are the obvious mental model when the operational question is
similarity, retrieval, or local geometry, which is the territory of
https://scikit-learn.org/stable/modules/neighbors.html. SVMs remain
useful when the data is small or medium, the boundary is not obviously
linear, and a maximum-margin view is still a better fit than a bigger
ensemble, as discussed in
https://scikit-learn.org/stable/modules/svm.html.

The point of this module is not that one of these models secretly beats
everything else. The point is that each one is strong inside a narrow
regime and misleading outside it. A disciplined practitioner should be
able to say, in plain language, why a quick Naive Bayes baseline is
enough for one task, why k-NN silently breaks when scaling is ignored,
and why an SVM is still reasonable on the right kind of small-data
problem.

That ability matters during on-call work because design mistakes here
usually look respectable at first. A Naive Bayes classifier can post a
perfectly serviceable accuracy number while giving you badly calibrated
probabilities. A k-NN model can appear to train instantly and still fail
because one unscaled feature dominates the distance calculation. An SVM
can look elegant in a notebook and become a time sink when someone
casually enables `probability=True` or aims a kernel SVM at too many
rows.

These are not abstract classroom errors. They are the kinds of mistakes
that produce slow retraining, unstable thresholds, brittle cold-start
logic, and models that are hard to defend in review. The fastest way to
avoid them is not to memorize formulae. It is to understand the regime
where each model is helping, the regime where it is lying to you, and
the simpler alternative when it stops fitting the job.

That is also why this module leans on earlier work instead of repeating
it. We will not re-teach leakage-safe pipelines from
[Module 1.1: Scikit-learn API & Pipelines](../module-1.1-scikit-learn-api-and-pipelines/),
calibration from
[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/),
or scaling practice from
[Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/).
Those foundations are assumed. What changes here is model choice under
pressure.

If you remember one framing device from this opener, let it be this:
Naive Bayes is a fast directional baseline, k-NN is a local geometry
machine, and SVM is a margin machine. Each view is useful. Each view
fails for different reasons. Your job is to choose the one whose blind
spot you can afford.

## Section 2: Naive Bayes

Naive Bayes is one of the most honest examples of a model that works
well even when its assumptions are plainly false. Its central
assumption, conditional independence of features within a class, is
rarely true in real datasets. Words in documents are correlated,
engineered features are correlated, and sensor measurements are
correlated.

Yet the model still performs well often enough to remain important. The
reason is practical rather than magical. In many classification
problems, especially text, the model does not need a perfect joint
distribution to place a decision boundary in roughly the right
direction.

That distinction matters. If you ask Naive Bayes to tell you the
relative odds of a class label in a coarse ranking sense, it is often
useful. If you ask it to tell you whether a predicted probability is a
trustworthy estimate of real-world frequency, you are asking for more
than it reliably gives.

This is why the scikit-learn user guide describes Naive Bayes as "a
decent classifier, but a bad estimator." That short warning should stay
in your head any time you see `predict_proba` coming out of a Naive
Bayes pipeline. The output is often good enough for ordering examples,
but it is not something you should operationally threshold as if it were
well calibrated. For calibration workflows and when to repair this, go
back to
[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/).

There is also more than one Naive Bayes model in practice, and the
variant is not cosmetic. The variant is the choice. Each one encodes a
different expectation about the feature representation, and choosing the
wrong one is a clean way to sabotage a baseline before you have even
started comparing alternatives.

`GaussianNB` assumes continuous features and models each feature with a
per-class Gaussian distribution. This makes sense when you have dense,
real-valued inputs and you want a very cheap baseline. The
`var_smoothing=1e-9` parameter exists for numerical stability, which is
a reminder that simple models still have numerical edge cases.

`MultinomialNB` is the canonical text baseline for count-like features.
Raw term counts fit naturally, and TF-IDF often works well in practice
too. The default `alpha=1.0` is Laplace smoothing, which prevents unseen
feature counts from collapsing the posterior to zero.

`BernoulliNB` is for binary features, where presence versus absence
matters more than count magnitude. Its default `binarize=0.0` means
values are thresholded at zero unless you provide already-binary inputs.
This becomes useful when a feature's meaning is "did the event happen"
rather than "how many times did it happen."

`ComplementNB` is the version to remember for imbalanced text problems.
The scikit-learn documentation describes it as "particularly suited for
imbalanced data sets." That phrase is short, but the practical lesson is
larger: the right Naive Bayes variant is not just about data type, it is
also about where the class distribution creates instability for the
simplest baseline.

Smoothing deserves direct attention because it is one of the few Naive
Bayes knobs people do reach for. The idea is straightforward. When the
model sees a token, category, or pattern in one class but not another,
it should not assign an impossible zero probability to that unseen event
without caution.

`alpha=1.0` is Laplace smoothing. It adds a full count of prior mass in
a simple way and is deliberately conservative. When `alpha` is smaller
than `1`, you are in Lidstone smoothing territory, which still avoids
zeros but makes a lighter correction.

Do not over-romanticize that parameter. Smoothing can stabilize the
counts, but it does not fix the deeper modeling simplification. If your
features are highly correlated, if your probability estimates need to
support downstream threshold policies, or if your team is actually
optimizing for calibrated risk, smoothing will not rescue you from the
core limitation. That is where
[Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/)
or calibration techniques from
[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/)
become the right next move.

The independence assumption is still worth understanding at a more
practical level. In text classification, many tokens co-occur
systematically. Some phrases nearly define one another. If your mental
model says "then Naive Bayes should collapse," that is too literal.

What often matters more is whether the aggregate signal points in a
useful direction. A document with a pile of class-associated words can
still be ranked toward the right class even if the probability magnitude
is overconfident. That is why Naive Bayes remains a strong first pass in
latency-bound text triage, lightweight moderation pipelines, and
baseline experiments where speed matters more than perfect posterior
estimation.

It is also one of the easiest ways to create a baseline that is faster
than the debate around it. A disciplined team can assemble a
leakage-safe `Pipeline` with text vectorization and `MultinomialNB`,
split the data properly, and get a reasonable answer before a more
complex model is even done tuning. That answer may not be the model you
ship forever. It may still be the answer that tells you whether the
problem is linearly separable, whether the label quality is usable, and
whether more expensive modeling is worth it.

> **Pause and predict** — If a Naive Bayes text classifier shows strong
> accuracy on held-out data but its probability calibration plot looks
> poor, should you celebrate the probabilities, ignore the problem, or
> separate the classification success from the probability-quality
> problem before deciding what to ship?

The right instinct is the third one. Separate the question "does it
classify well enough?" from the question "are its probabilities good
enough for thresholding, ranking under uncertainty, or downstream
decision support?" Naive Bayes can answer the first more often than it
answers the second.

Another operational detail is that Naive Bayes usually pairs naturally
with encoding steps that do not require feature scaling. This is a nice
contrast with the distance-based and margin-based models later in the
module. If you are using count features for `MultinomialNB` or binary
presence features for `BernoulliNB`, you are mainly making
representation choices, not trying to equalize Euclidean geometry.

That does not mean preprocessing disappears. It means the relevant
preprocessing changes. Tokenization choices, stop-word handling,
lowercasing, and whether you keep raw counts or TF-IDF now matter more
than a `StandardScaler`. Keep the pipeline discipline from
[Module 1.1: Scikit-learn API & Pipelines](../module-1.1-scikit-learn-api-and-pipelines/),
but do not cargo-cult the scaling step into places where it is not the
main risk.

When is Naive Bayes still the right tool today? It is right when you
need a fast baseline, when your features are sparse counts or indicators
that align with one of the supported variants, when latency or
simplicity matters, and when probability quality is not the main
deliverable. It is also right when the fastest useful answer is more
valuable than a slower marginal improvement.

When is it the wrong tool? It is wrong when calibrated probabilities are
part of the product contract, when correlated features are severe enough
to destabilize interpretation, or when the task has a clear global
linear structure that a regularized linear model from
[Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/)
will likely fit more transparently.

Here is a small runnable example of a text baseline with
`CountVectorizer` and `MultinomialNB`. The point of this example is not
to create a production spam detector. The point is to show a leakage-safe
pipeline and to make the calibration warning concrete.

```python
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

texts = [
    "claim your free prize now",
    "limited time offer claim bonus",
    "meeting moved to tomorrow morning",
    "please review the design document",
    "win a free ticket now",
    "project update and next steps",
    "exclusive offer just for you",
    "schedule the incident review",
    "bonus cash prize claim today",
    "can you send the latest report",
    "free entry limited time",
    "let us discuss the bug backlog",
]

labels = [1, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0]

X_train, X_test, y_train, y_test = train_test_split(
    texts,
    labels,
    test_size=0.33,
    random_state=42,
    stratify=labels,
)

model = Pipeline(
    steps=[
        ("vectorizer", CountVectorizer()),
        ("classifier", MultinomialNB(alpha=1.0)),
    ]
)

model.fit(X_train, y_train)

predictions = model.predict(X_test)
probabilities = model.predict_proba(X_test)

print("Accuracy:", accuracy_score(y_test, predictions))
print("Predictions:", predictions.tolist())
print("Probabilities:")
for text, probs in zip(X_test, probabilities):
    print(f"{text!r} -> ham={probs[0]:.3f}, spam={probs[1]:.3f}")
```

Read the output carefully. The printed probabilities will look neat and
decisive. That is exactly why this warning matters. Those values are
usable as model outputs, but they are not evidence that the probabilities
are calibrated enough for a threshold like "send to a human only when
spam probability exceeds this number."

If your operational policy depends on trustworthy uncertainty, you
should not stop at `predict_proba`. You should either move to a model
family that gives you a better path to probability quality, such as
`LogisticRegression` from
[Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/),
or explicitly use calibration tools discussed in
[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/).

There is a subtler decision-review argument here too. Naive Bayes is
often easier to justify as a baseline than as a final answer. "We needed
a fast, sparse-text baseline, and it gave us directional signal quickly"
is a strong argument. "We used it because the probabilities looked
confident" is not.

That is the mindset you want to carry forward into k-NN and SVM. Each of
these model families has a regime where it is surprisingly effective.
Each also has a specific output that looks more trustworthy than it
really is if you forget what the model is assuming.

## Section 3: k-Nearest Neighbors

k-Nearest Neighbors is almost the opposite of Naive Bayes in where the
work happens. Naive Bayes does a small amount of fitting up front and
then makes cheap predictions. k-NN is a lazy learner: there is almost no
real training phase, and most of the cost appears when you ask for a
prediction.

That laziness is not a defect by itself. It is a design choice. If your
task is fundamentally about local similarity, k-NN is one of the most
direct models you can build because it refuses to invent a global
equation for the data when a local neighborhood may be enough.

The basic idea is familiar. For a query point, find the `k` closest
training examples under some distance metric, then classify or regress
from those neighbors. In classification, the simplest version takes a
majority vote. In regression, it averages the target values.

What matters in practice is not that description. What matters is how
many hidden assumptions sit inside words like "closest" and "neighbors."
The model only makes sense if the feature space and the distance metric
actually encode a meaningful notion of similarity.

The default metric for many scikit-learn nearest-neighbor estimators is
Euclidean distance, which is Minkowski distance with `p=2`. That is
reasonable for many dense numeric problems, but it is only one choice.
If you care about axis-aligned movement more than straight-line
distance, Manhattan distance with `p=1` may be a better fit.

For binary features, Hamming-style thinking is often more natural
because the question is how many bit positions disagree. For text or
embedding-like representations, cosine similarity may be closer to the
real notion of semantic closeness than Euclidean distance, although in
scikit-learn that often means being deliberate about how you define the
metric and whether the estimator path supports it efficiently.

This is the first place where k-NN can fail silently. If you use a
distance metric that does not match the feature type, the model will
still run. It just will not be answering the question you think you
asked. That is why metric choice is not an afterthought in nearest
neighbors. It is part of the model definition.

Weighting is the next lever. With `weights="uniform"`, all selected
neighbors vote equally. With `weights="distance"`, closer neighbors get
more influence. The second option often makes intuitive sense, but it is
not always automatically better. If your distances are already noisy or
distorted by poor scaling, distance weighting can amplify the problem.

The training-time simplicity of k-NN also tempts people to ignore its
inference-time cost. Every prediction needs neighbor lookup. On tiny
datasets, that is fine. On large datasets, the cost becomes part of the
system design, not just part of the model choice.

This is why scikit-learn offers multiple neighbor-search back ends:
brute force, kd-tree, and ball-tree. The `algorithm="auto"` option is
an adaptive compromise rather than a magic trick. The user guide notes
that it falls back to brute force when input data is sparse, when the
dimensionality `D` is greater than `15`, when `k >= N/2`, or when the
chosen metric is not supported by the tree methods.

That set of rules tells you something important about real-world k-NN.
The efficient-tree story is not universal. As dimensionality grows, the
tree methods lose their advantage. Sparse inputs also often force the
brute-force path. If you imagined k-NN as "cheap because trees make it
fast," the user guide is already warning you to be more careful.

The deeper issue is the curse of dimensionality. As the number of
features grows, distances tend to become less discriminative. Points
start to look similarly far away from one another, which weakens the
idea that the nearest few neighbors are genuinely special. This is one
reason why nearest-neighbor methods often degrade as you move from a
compact feature space into a much larger one.

That is also why
[Module 1.10: Dimensionality Reduction](../module-1.10-dimensionality-reduction/)
is the right forward link here. If the data geometry becomes mushy in
high dimension, you do not fix that by hoping for a better `k` alone.
You often need a representation that restores useful structure or a
model family that relies less directly on raw distance concentration.

There is an even more common k-NN mistake, though, and it happens long
before dimensionality gets extreme. k-NN must be scaled. This is not
optional and not a style preference. Distance-based learners depend on
feature geometry, so an unscaled feature with a larger numeric range can
dominate the distance computation.

This is the mirror image of a point you saw in
[Module 1.5: Decision Trees & Random Forests](../module-1.5-decision-trees-and-random-forests/).
Tree-based models do not need scaling because they split by thresholds
on individual features. k-NN absolutely does need scaling because it
measures distance across features at once.

If one feature is measured in dollars and another in a small bounded
range, the dollars feature can overwhelm the rest of the geometry. The
model will still give predictions. They will simply reflect the wrong
notion of closeness. That is why the safest default pattern is a
pipeline that includes `StandardScaler` before `KNeighborsClassifier` or
`KNeighborsRegressor`, exactly as reinforced in
[Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/).

k-NN still wins in several modern regimes despite these caveats. It is
useful on very small datasets where complex parametric fitting is
unnecessary. It is useful as a conceptual bridge to anomaly detection
via neighbor distance. It is useful for cold-start similarity and
retrieval tasks, especially when you already believe the embedding space
carries the semantics you care about.

What k-NN does not do well is extrapolate. If a query lands far from the
training support, the algorithm still returns neighbors because it must.
Those neighbors may not be representative in any meaningful sense. This
is a local interpolation method, not a robust extrapolation engine.

> **Pause and reflect** — Imagine a k-NN classifier that performed
> acceptably yesterday, then regressed after a new numeric feature was
> added. Before trying more neighbors, what is the first structural
> thing you should inspect in the pipeline, and why?

The answer is scaling. If the new feature entered with a much larger
range, it probably distorted the geometry long before the value of `k`
became the main problem. This is exactly the kind of failure that looks
mysterious if you treat feature engineering and model choice as
separate.

Here is a runnable example that makes the scaling issue visible on a
deliberately mixed-scale classification problem. Notice that both models
use the same `k`. The only difference is whether the pipeline scales the
features.

```python
from sklearn.datasets import make_classification
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

X, y = make_classification(
    n_samples=600,
    n_features=6,
    n_informative=4,
    n_redundant=0,
    random_state=42,
)

X[:, 0] = X[:, 0] * 1000.0

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.3,
    random_state=42,
    stratify=y,
)

knn_no_scale = Pipeline(
    steps=[
        ("knn", KNeighborsClassifier(n_neighbors=9, weights="distance")),
    ]
)

knn_scaled = Pipeline(
    steps=[
        ("scale", StandardScaler()),
        ("knn", KNeighborsClassifier(n_neighbors=9, weights="distance")),
    ]
)

knn_no_scale.fit(X_train, y_train)
knn_scaled.fit(X_train, y_train)

pred_no_scale = knn_no_scale.predict(X_test)
pred_scaled = knn_scaled.predict(X_test)

print("Accuracy without scaling:", accuracy_score(y_test, pred_no_scale))
print("Accuracy with scaling:", accuracy_score(y_test, pred_scaled))
print("Pipeline.score without scaling:", knn_no_scale.score(X_test, y_test))
print("Pipeline.score with scaling:", knn_scaled.score(X_test, y_test))
```

The `score` calls here report mean accuracy because this is a
classifier. They do not report AUC. That distinction is easy to forget
when you are moving quickly, which is why the module is explicit about
`model.score()` semantics. For classifiers, `score` means accuracy. For
regressors, it means `R^2`. If you want ROC AUC, compute ROC AUC
directly, and only on outputs that actually support the intended metric.

The example above is also a reminder that scaling belongs inside the
pipeline. Do not fit a scaler on the full dataset first and then split.
That would reintroduce leakage that
[Module 1.1: Scikit-learn API & Pipelines](../module-1.1-scikit-learn-api-and-pipelines/)
and
[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/)
already taught you to avoid.

Another subtle but practical point is that `k` itself interacts with
data density and label noise. Very small `k` can overreact to noisy
points. Very large `k` can wash out meaningful local structure. There is
no globally correct setting. The right value depends on whether the
signal is genuinely local and how sparse your training support is.

Even so, the biggest k-NN errors in production are usually not bad `k`
values. They are structural. Unscaled features, too many dimensions,
mismatched metrics, and unrealistic expectations about inference cost
cause more pain than a slightly imperfect neighborhood size. That is why
the practitioner's first checklist for k-NN should be about geometry,
not about parameter hunting.

If you are deciding whether to use k-NN for a cold-start recommendation
fallback, the questions should sound like this. Do the features or
embeddings define a meaningful space? Is inference latency acceptable for
neighbor lookup? Will queries live near training support often enough to
trust local reasoning? Are you prepared for the method to degrade as the
feature space gets wider?

When those answers are favorable, k-NN can be refreshingly effective.
When they are not, pushing harder usually means you wanted another tool
all along. Sometimes that tool is approximate nearest neighbors or
vector search for large-scale retrieval. Sometimes it is a regularized
linear model from
[Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/)
because the signal is more global than local. Sometimes it is
[Module 1.6: XGBoost & Gradient Boosting](../module-1.6-xgboost-gradient-boosting/)
because the problem is tabular and rich enough that local lazy lookup is
not the right abstraction.

## Section 4: Support Vector Machines

Support Vector Machines start from a geometric idea that is still useful
even if you never derive the optimization problem by hand. If two
classes can be separated, try to separate them with the widest possible
margin. The margin is the distance from the decision boundary to the
closest training points that constrain it.

This framing does two things at once. First, it encourages a boundary
that is not merely correct on the training data but robust to small
perturbations. Second, it creates a clean way to talk about complexity:
some problems are well handled by a linear margin, while others need a
curved one.

A hard-margin SVM insists on perfect separation. That is more of a
conceptual starting point than a realistic default. Real data is noisy,
overlapping, and messy. So in practice we use a soft margin, which
allows violations while penalizing them.

That penalty is controlled by `C`, and the direction of `C` is one of
the most commonly misunderstood points in this module. In SVMs, `C` is
an inverse regularization parameter. Lower `C` means stronger
regularization. Higher `C` means weaker regularization and a stronger
attempt to fit the training data closely.

This direction is the same as `LogisticRegression` `C` from
[Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/).
It is the opposite of Ridge or Lasso `alpha`, where larger values mean
more regularization. If someone reads `C=10.0` and casually says "more
regularized," they have it backward.

That contrast matters in team settings because many practitioners move
between linear models and SVMs without re-checking the hyperparameter
semantics. A config file full of `alpha` values and a config file full
of `C` values do not tell the same story as they get larger. This is
not trivia. It is a source of silent mis-tuning.

SVMs split into two large practical families. `LinearSVC` and
`LinearSVR` are the linear versions, built on a different solver path
than kernel SVMs. They are particularly important for large feature
spaces, sparse text, and regimes where a linear margin is credible and
the sample count is large enough that kernel methods become painful.

The scikit-learn documentation notes that `LinearSVC` scales better to
large numbers of samples. That statement is not marketing language. It
is a direct cue about when not to reach for `SVC(kernel="rbf")` just
because it is the most recognizable class name in the API.

The other family is kernel SVMs through `SVC` and `SVR`, including
`kernel="rbf"`, `kernel="poly"`, and `kernel="sigmoid"`. The core idea
of the kernel trick is that you can act as if you mapped data into a
richer feature space without explicitly constructing all those expanded
features. Conceptually, this lets a linear margin in the transformed
space become a non-linear decision boundary in the original space.

You do not need the derivation to use this responsibly. What you do need
is a sense of when the flexibility is buying something real and when it
is just adding computational cost. An RBF SVM is valuable when the
boundary is genuinely curved and the dataset is still in the size regime
where kernel fitting remains realistic.

The `gamma` parameter shapes how local that curvature becomes. In
`SVC`, the default `gamma="scale"` corresponds to
`1 / (n_features * X.var())`, while `gamma="auto"` corresponds to
`1 / n_features`. The important operational point is not to memorize the
formulae for their own sake, but to understand that `gamma` controls how
far the influence of a training point reaches.

Small `gamma` values make the boundary smoother and broader. Large
`gamma` values make the boundary more local and more capable of fitting
fine-grained variations. Combined with `C`, this gives you the familiar
bias-variance tension in a different language: smoother margins versus
more training-set conformity.

SVM cost is the next hard reality. The scikit-learn user guide warns
that libsvm-based `SVC` and `SVR` scale roughly between
`O(n_features * n_samples^2)` and
`O(n_features * n_samples^3)`. You do not need an exact runtime model to
understand the implication. Kernel SVMs are not the casual default for
very large datasets.

That cost warning is one reason `LinearSVC` matters so much. If the
feature space is large and sparse, such as text or bag-of-words data, a
linear margin often gets you the relevant behavior without asking you to
pay kernel costs. This is also a place where a regularized linear model
from
[Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/)
may be a more transparent baseline than a kernel method.

The second cost warning is about probability outputs. In `SVC`,
setting `probability=True` triggers internal Platt scaling with an
expensive five-fold cross-validation during `fit`. That means the flag
is not a minor convenience switch. It changes training cost
substantially.

Many teams do not need this at all. If what you want is a confidence-like
ordering for ranking or margin inspection, `decision_function` is often
enough. If what you truly need is calibrated probability behavior, then
you should think through the calibration workflow explicitly and connect
back to
[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/)
rather than enabling `probability=True` by reflex.

SVMs also need scaling. The user guide states plainly that support
vector machine algorithms are not scale invariant, so scaling is highly
recommended. This is the same geometric reason you saw in k-NN: if the
units are inconsistent across features, the margin geometry becomes
distorted.

That is why `StandardScaler` belongs in the pipeline before `SVC` or
`LinearSVC`, and why this is another direct cross-link to
[Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/).
Do not re-fight the same bug in two model families. Distance-based and
margin-based learners both depend on meaningful feature scale.

Imbalanced classification introduces another practical tweak:
`class_weight="balanced"`. This tells the estimator to adjust class
weights inversely to class frequencies. It is not a universal cure, but
it is an important first-line configuration change when the minority
class matters and the baseline is otherwise underweighting it.

> **Pause and predict** — A teammate proposes
> `SVC(kernel="rbf", probability=True)` on a large imbalanced dataset
> because "we need good probabilities." Before you accept that plan,
> which two costs or risks should you name immediately?

The first is computational cost: kernel SVMs already scale poorly with
sample count, and `probability=True` adds expensive internal
cross-validation. The second is conceptual: if calibrated probabilities
are a core requirement, you should validate that requirement through the
workflow in
[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/)
instead of assuming the flag solves the whole problem.

Here is a runnable example that compares a scaled RBF `SVC` with a
scaled `LinearSVC` on a non-linear `make_moons` dataset. The point is to
show the curved decision boundary of the kernel model against the
straight-line bias of the linear one.

```python
import matplotlib.pyplot as plt
import numpy as np
from sklearn.datasets import make_moons
from sklearn.inspection import DecisionBoundaryDisplay
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC, SVC

X, y = make_moons(n_samples=400, noise=0.22, random_state=42)

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.3,
    random_state=42,
    stratify=y,
)

rbf_svc = Pipeline(
    steps=[
        ("scale", StandardScaler()),
        ("svc", SVC(C=1.0, kernel="rbf", gamma="scale")),
    ]
)

linear_svc = Pipeline(
    steps=[
        ("scale", StandardScaler()),
        ("svc", LinearSVC(C=1.0, dual="auto", max_iter=10000)),
    ]
)

rbf_svc.fit(X_train, y_train)
linear_svc.fit(X_train, y_train)

print("RBF SVC accuracy:", rbf_svc.score(X_test, y_test))
print("LinearSVC accuracy:", linear_svc.score(X_test, y_test))

fig, axes = plt.subplots(1, 2, figsize=(10, 4))

for ax, model, title in [
    (axes[0], rbf_svc, "RBF SVC"),
    (axes[1], linear_svc, "LinearSVC"),
]:
    DecisionBoundaryDisplay.from_estimator(
        model,
        X,
        response_method="predict",
        cmap=plt.cm.coolwarm,
        alpha=0.35,
        ax=ax,
    )
    ax.scatter(X[:, 0], X[:, 1], c=y, cmap=plt.cm.coolwarm, edgecolor="k", s=25)
    ax.set_title(title)

plt.tight_layout()
plt.show()
```

If you run the plot, the visual comparison is immediate. The RBF SVC can
wrap around the moon-shaped clusters with a curved boundary. The linear
SVM still tries to separate them with a straight margin because that is
all the model family permits.

That does not mean the kernel SVM is always the better choice. It means
the dataset has non-linear structure that the linear margin cannot
capture directly. If you change the problem to a much larger sparse text
matrix, the tradeoff reverses quickly and `LinearSVC` becomes the more
credible operational baseline.

This is the decision point many practitioners miss. They learn "SVMs are
powerful" and then stop. What they need instead is a sharper statement:
kernel SVMs are powerful in the right sample-size regime and geometry,
while linear SVMs are the practical branch for large sparse spaces.

Where do SVMs still shine? They shine on small to medium supervised
problems where the margin view fits the data, where feature scaling is
under control, and where a well-regularized boundary is easier to defend
than a more elaborate ensemble. They are also strong when you need a
competitive classical learner without immediately reaching for boosting.

Where are they the wrong tool? They are the wrong tool for millions of
rows with kernel fitting, for calibration-heavy requirements if you have
not planned for the cost, and for non-tabular structure such as images,
sequences, or graphs where the representational burden points toward the
deep-learning track instead.

## Section 5: Decision Table — When to Reach for Each

By this point, the right comparison is no longer "which one is best?"
The useful comparison is "what regime is each model built for, what
preprocessing discipline does it require, and what kind of failure should
I expect if I use it outside that regime?" A compact table helps force
that question into the open.

| Model | Primary regime | Scaling required | Complexity scales like | Probability quality | Common alternatives |
| --- | --- | --- | --- | --- | --- |
| Naive Bayes | Fast sparse-text or count-feature baseline; simple triage; latency-sensitive classification | Usually no numeric scaling focus; representation choice matters more | Cheap fit and cheap predict for typical sparse setups | Weak calibration; treat `predict_proba` cautiously | [Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/) for calibrated linear classification; [Module 1.6: XGBoost & Gradient Boosting](../module-1.6-xgboost-gradient-boosting/) for richer tabular signal |
| k-NN | Very small datasets; local similarity; cold-start fallback; neighbor search intuition | Yes, strongly | Minimal training cost; prediction cost grows with neighbor lookup and data size | Depends on local vote structure; not a calibrated-probability tool | Approximate nearest neighbors or vector search at scale; [Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/) when signal is global |
| SVM (`SVC`, `rbf`) | Small or medium datasets with non-linear margin structure | Yes, strongly | Kernel cost grows steeply with sample count | `probability=True` is expensive; use with care | [Module 1.6: XGBoost & Gradient Boosting](../module-1.6-xgboost-gradient-boosting/) for medium-to-large tabular problems; deep learning for non-tabular structure |
| `LinearSVC` | Large sparse feature spaces; text; many samples; linear margin plausible | Yes, strongly | Better scaling than kernel SVMs on large sample counts | No native calibrated probability output by default | [Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/) when probability interpretation matters |

The table hides an important theme in plain sight: none of these models
is the universal tabular default. If the data is medium-to-large,
mixed-signal, and fundamentally tabular, your comparison should usually
include
[Module 1.6: XGBoost & Gradient Boosting](../module-1.6-xgboost-gradient-boosting/).
Boosted trees tend to be stronger in that regime because they can absorb
non-linear feature interactions without making k-NN's local-distance
assumption or SVM's kernel-cost tradeoff.

Likewise, if the structure is globally linear and you want a model that
is both strong and relatively interpretable, a regularized linear model
from
[Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/)
often deserves priority over all three models in this module. The
decision is not about fashion. It is about matching the inductive bias
to the problem.

There is also a deeper modeling distinction across the four rows.
Naive Bayes cares about directional evidence under a simple
probabilistic factorization. k-NN cares about local neighborhoods in a
chosen metric space. SVMs care about margins, globally for linear SVM
and with kernelized flexibility for non-linear SVM.

A design review improves immediately when someone can state that
difference clearly. "We used k-NN because nearby examples in embedding
space mean something operationally." "We used Naive Bayes because we
needed a sparse-text baseline before investing in a richer model." "We
used `LinearSVC` because the features were high-dimensional and sparse,
and a linear margin scaled better than a kernel method."

Those are regime-aware explanations. They travel well from notebook to
production because they name both the strength and the risk. A vague
statement like "SVM performed well in my experiment" does not carry the
same weight because it says nothing about cost, preprocessing, or what
would happen when the data changes.

## Section 6: Practitioner Playbook — What They Share

Naive Bayes, k-NN, and SVMs look different on the surface, but they
share one practical lesson: each fails silently in a specific regime.
The model usually keeps returning outputs. The danger is that the output
shape looks normal enough to trust before you inspect the underlying
assumption.

For Naive Bayes, the silent failure is usually probability quality.
Because the model is simple and often accurate enough to be useful,
teams are tempted to overread its posterior probabilities. If the
problem requires threshold tuning, uncertainty communication, or
decision-making that depends on well-calibrated risk, Naive Bayes is
often the wrong tool unless you are explicitly planning a calibration
workflow from
[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/).

Heavily correlated features are a related warning sign. Naive Bayes does
not become illegal when features correlate, but the factorized modeling
story gets more strained. If a feature set is engineered, dense, and
full of redundant signals, a regularized linear model from
[Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/)
often gives you a cleaner baseline.

For k-NN, the silent failure is geometric mismatch. Unscaled features,
too many dimensions, the wrong distance metric, and queries that land
far from training support all produce confident-looking predictions with
weak real meaning. This is why nearest-neighbor debugging starts with
representation and scale before it starts with `k`.

For SVM, the silent failure is usually regime mismatch. A kernel SVM can
look elegant on a small example and become operationally unreasonable on
a larger one. `probability=True` looks like a harmless request for
convenience until training time expands because of internal five-fold
cross-validation. Class imbalance can also pull the boundary in the
wrong direction unless you pay attention to weighting.

The fastest way to use these models well is to keep a short playbook in
mind.

First, ask what structure the model is assuming. Naive Bayes assumes
conditional independence and rewards simple sparse evidence. k-NN
assumes local similarity in the chosen metric. SVM assumes that the
useful structure can be expressed through a large-margin boundary, with
or without a kernel.

Second, ask whether the preprocessing matches the assumption. k-NN and
SVM require scaling because both depend on geometry.
[Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/)
is not optional background here; it is central. Naive Bayes generally
does not need numeric scaling in the same way, but it does need the
right feature representation for the chosen variant.

Third, ask whether the runtime profile fits the system. Naive Bayes is a
good answer when you need a baseline before lunch. k-NN is deceptively
light at fit time but moves the cost to inference. Kernel SVMs may be
perfectly reasonable on one dataset and a bad idea on another simply
because sample count changed.

Fourth, ask what kind of output quality matters. If you need calibrated
probabilities, that requirement should narrow the field immediately.
Naive Bayes is weak on calibration, SVM probabilities can be expensive,
and even when a model exposes `predict_proba`, the right question is not
"does the method exist?" but "does the output match the contract we need
to honor?"

A separate but related discipline is pipeline structure. Put scaling for
k-NN and SVM inside the pipeline so it is fit only on the training fold.
Keep vectorization for Naive Bayes inside the pipeline for the same
reason. The moment you separate preprocessing from cross-validation or
train-test splitting in an ad hoc way, you create leakage risk that can
make all downstream comparisons unreliable.

That pipeline discipline also makes comparisons fairer. If you evaluate
Naive Bayes, k-NN, and SVM under different data-preparation shortcuts,
you are not actually comparing models. You are comparing models plus
different amounts of accidental leakage and different levels of
preprocessing care.

It is helpful to contrast these models one more time with
[Module 1.5: Decision Trees & Random Forests](../module-1.5-decision-trees-and-random-forests/).
Trees usually do not require scaling because splits happen per feature.
That is why a tree model can survive the mixed-unit feature mistake that
breaks k-NN or distorts an SVM margin. The contrast matters because many
teams move between model families while unconsciously carrying the wrong
preprocessing habits with them.

The same kind of discipline matters when you compare against
[Module 1.6: XGBoost & Gradient Boosting](../module-1.6-xgboost-gradient-boosting/).
If boosted trees win on a medium-sized tabular problem, that result is
meaningful only if the baselines were built correctly. A poorly scaled
k-NN baseline or a casually configured SVM is not a fair benchmark. It
is just a weakly constructed straw model.

There is also a communication advantage to this playbook. When someone
asks why a model was chosen, the best answers are short and structural.
"We needed a fast sparse baseline." "We needed local similarity." "We
needed a non-linear margin on a manageable dataset." Those statements
are more useful than long hyperparameter recitations because they expose
the actual reasoning.

> **Pause and reflect** — If you had to explain the difference between
> Naive Bayes, k-NN, and SVM to a teammate in one sentence each, would
> your summaries mention the model's assumption, its main preprocessing
> dependency, and the regime where it fails most quietly?

If not, tighten the summary until they do. That exercise is not just
for teaching. It is a check that you understand what would need to be
monitored after deployment.

### Pipeline Discipline Subsection

For k-NN and SVM, the safe default is a `Pipeline` that starts with a
scaler, then applies the estimator. This preserves train-only fitting of
the scaler and ensures the geometry seen during evaluation matches the
geometry that would be used in production. It also makes cross-validation
and hyperparameter search less error-prone.

For Naive Bayes, the safer pattern is representation inside the
pipeline. Text vectorizers, binarization logic, and the chosen NB
variant should sit together so that fitting the representation never
sees held-out data. The model itself may be simple, but the leakage risk
from outside-pipeline preprocessing is still real.

For tree models from
[Module 1.5: Decision Trees & Random Forests](../module-1.5-decision-trees-and-random-forests/),
the pipeline story is different because scaling is not structurally
required. That is exactly why carrying over the same "always scale
everything" reflex from k-NN or SVM is less important there than it is
here. Model family shapes preprocessing, not the other way around.

## Section 7: Where They're the Wrong Tool

Naive Bayes is the wrong tool when calibrated probabilities are central
to the task. If a review queue, risk threshold, or downstream policy
depends on trustworthy probability estimates, you should reach for
`LogisticRegression` from
[Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/)
or use calibration methods from
[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/).
Naive Bayes may still be a useful baseline, but it should not be your
last word on probability quality.

k-NN is the wrong tool when the dataset is massive and inference-time
neighbor lookup becomes the real bottleneck. If you are effectively
doing similarity search at scale, the more appropriate family is
approximate nearest neighbors or vector-search infrastructure, not a
plain exact k-NN classifier that was never meant to shoulder that system
load alone.

k-NN is also the wrong tool when the dimensionality gets large enough
that distances stop being informative. That is the moment to consider a
representation fix through
[Module 1.10: Dimensionality Reduction](../module-1.10-dimensionality-reduction/)
or to choose a model that relies less directly on raw neighborhood
geometry.

SVM is the wrong tool when someone proposes a kernel method on a dataset
whose sample count already makes the cost hard to justify. It is also a
bad fit when the requirement is deeply tied to images, sequences, or
graph structure, because in those cases the representation burden often
belongs in the deep-learning track rather than in a handcrafted kernel
setup.

Any of the three models in this module can be the wrong tool on
medium-to-large tabular problems with mixed signal and feature
interactions. That is the default territory where
[Module 1.6: XGBoost & Gradient Boosting](../module-1.6-xgboost-gradient-boosting/)
should usually enter the comparison. It is not that Naive Bayes, k-NN,
or SVM become invalid. It is that their inductive biases are no longer
the most natural fit.

There is an important emotional discipline here too. Classical models
often feel appealing because they are easy to name and quick to try. But
shipping the wrong simple model can cost more time than starting with
the right baseline family in the first place. Simplicity is valuable
only when it aligns with the structure of the problem.

If you take one decision rule from this section, use this one: when a
model's failure mode overlaps directly with the thing the product cares
about most, that model is probably the wrong tool. If the product cares
about calibrated uncertainty, do not excuse Naive Bayes because it is
fast. If the product cares about large-scale retrieval latency, do not
excuse exact k-NN because it is conceptually simple. If the product
cares about throughput on many rows, do not excuse kernel SVM because it
looked beautiful on a smaller sample.

## Did You Know?

- The scikit-learn user guide explicitly warns that Naive Bayes is a
  decent classifier but a bad estimator, which is why its
  `predict_proba` outputs should not be treated as calibrated by
  default. Source: https://scikit-learn.org/stable/modules/naive_bayes.html

- In scikit-learn nearest-neighbor classes, `algorithm="auto"` selects
  brute force when the input is sparse, when the dimensionality is above
  `15`, when `k >= N/2`, or when the metric is unsupported by the tree
  methods. Source: https://scikit-learn.org/stable/modules/neighbors.html

- Setting `probability=True` on `SVC` triggers an expensive internal
  five-fold cross-validation step for Platt scaling during fitting.
  Source: https://scikit-learn.org/stable/modules/svm.html

- In SVMs, `C` is an inverse regularization parameter, so decreasing
  `C` means more regularization rather than less. Source:
  https://scikit-learn.org/stable/modules/svm.html

## Common Mistakes

| Mistake | Why it's wrong | Safer pattern |
| --- | --- | --- |
| Treating Naive Bayes `predict_proba` as calibrated probability | Naive Bayes can classify reasonably well while producing poor probability estimates; this breaks thresholding logic | Use Naive Bayes as a baseline, then revisit calibration in [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/) or compare with [Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/) |
| Using `KNeighborsClassifier` without `StandardScaler` | Unscaled features dominate Euclidean or Minkowski distance and distort neighborhood geometry | Put scaling inside a pipeline as reinforced in [Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/) |
| Enabling `SVC(probability=True)` by default | It triggers expensive internal five-fold cross-validation and increases training cost materially | Use `decision_function` when ranking confidence is enough, and only enable probability intentionally with calibration needs from [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/) |
| Defaulting to `SVC(kernel="rbf")` on a very large dataset | Kernel SVM cost scales poorly with sample count and can become operationally unrealistic | Prefer `LinearSVC` for large sparse linear regimes or compare against [Module 1.6: XGBoost & Gradient Boosting](../module-1.6-xgboost-gradient-boosting/) for larger tabular problems |
| Reading SVM `C` as a direct regularization weight | In SVMs, larger `C` means less regularization, not more | Compare its meaning with `LogisticRegression` `C` and Ridge or Lasso `alpha` in [Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/) |
| Confusing `MultinomialNB` and `BernoulliNB` | Count-valued features and binary presence features imply different event models | Match `MultinomialNB` to count-like features and `BernoulliNB` to binary indicators |
| Reporting `model.score(X_test, y_test)` as AUC | For classifiers, `score` is mean accuracy; for regressors, it is `R^2` | Compute ROC AUC explicitly only when the model output and metric support it |
| Mixing cosine thinking with Euclidean training | A retrieval story built around cosine similarity can break if the fitted model still uses Euclidean geometry | Choose a metric that matches the representation and validate it explicitly |

## Quiz

### 1. A spam-filter team needs a baseline today because a manual triage
queue is backing up. They can build either a `MultinomialNB` text model
or spend longer tuning a richer classifier. What is the reasonable move,
and what should they refuse to promise about the model's output?

<details><summary>Answer</summary>

A reasonable move is to ship a leakage-safe `Pipeline` baseline with
`CountVectorizer` and `MultinomialNB` so the team gets directional value
quickly. They should refuse to promise that Naive Bayes probabilities
are calibrated, and they should point reviewers to
[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/)
for the difference between classification quality and probability
quality. If later comparison matters, a regularized linear alternative
from
[Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/)
is the natural next benchmark.

</details>

### 2. A k-NN classifier regresses sharply after a new feature measured
in dollars is added to the dataset. The team has not changed `k`. What
is the most likely cause, and what module should you cite in review?

<details><summary>Answer</summary>

The most likely cause is that the new feature entered with a much larger
numeric range and now dominates Euclidean distance. The fix is to put
scaling inside the pipeline and review the preprocessing discipline from
[Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/).
This is also a good moment to remind the team that the contrast with
trees from
[Module 1.5: Decision Trees & Random Forests](../module-1.5-decision-trees-and-random-forests/)
does not carry over here: k-NN depends on geometry, so scaling is
structural, not optional.

</details>

### 3. A team enables `probability=True` on
`SVC(kernel="rbf")` because a dashboard wants confidence numbers. Fit
time jumps immediately. Explain the most likely reason and the better
review question to ask.

<details><summary>Answer</summary>

The most likely reason is that `probability=True` triggers expensive
internal five-fold cross-validation for Platt scaling during `fit`, on
top of the already costly kernel SVM training path. The better review
question is whether the dashboard truly needs calibrated probabilities or
whether `decision_function` would be enough for ranking and relative
confidence. That decision belongs in the calibration workflow from
[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/),
not as an incidental toggle.

</details>

### 4. A teammate proposes `SVC(kernel="rbf")` on a very large tabular
dataset because "SVMs are strong classical models." What should you
suggest instead, and why?

<details><summary>Answer</summary>

Suggest reconsidering the regime first. For very large sparse or roughly
linear settings, `LinearSVC` is a more plausible SVM branch. For
medium-to-large tabular data with mixed signal, the stronger default
comparison is usually
[Module 1.6: XGBoost & Gradient Boosting](../module-1.6-xgboost-gradient-boosting/).
If probability interpretation matters too, compare with
[Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/).
The core reason is that kernel SVM cost scales poorly with sample count,
so the proposal is mismatched to the dataset regime.

</details>

### 5. A configuration file changes SVM `C` from `1.0` to `10.0`. Is
that more regularization or less, and what comparison helps prevent this
mistake?

<details><summary>Answer</summary>

That is less regularization. In SVMs, `C` is an inverse regularization
parameter, so larger `C` means the model pushes harder to fit the
training data. The comparison that prevents this mistake is to remember
that SVM `C` behaves in the same direction as `LogisticRegression` `C`
from
[Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/),
but in the opposite direction of Ridge or Lasso `alpha`.

</details>

### 6. A Naive Bayes model posts strong held-out accuracy, but its
calibration plot is poor and the product owner wants a probability-based
automation threshold. What is the right next move?

<details><summary>Answer</summary>

Do not mistake the accuracy result for a probability-quality result.
Return to
[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/)
to validate calibration explicitly, and compare against
[Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/)
if you need a stronger baseline for calibrated classification. Naive
Bayes may remain a useful baseline, but it is the wrong final tool if
probability thresholds are part of the product contract.

</details>

### 7. A nearest-neighbor baseline degrades when the feature space grows
from compact engineered features into a much wider representation. The
team has already scaled the data. Why might performance still fall, and
what module is the recovery path?

<details><summary>Answer</summary>

Scaling does not solve the curse of dimensionality. As the number of
features grows, distances become less discriminative, so "nearest" stops
meaning what you hoped it meant. The recovery path is often to revisit
representation and then study
[Module 1.10: Dimensionality Reduction](../module-1.10-dimensionality-reduction/)
for ways to restore useful structure before relying on local geometry
again. Depending on the signal, a different model family from
[Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/)
or
[Module 1.6: XGBoost & Gradient Boosting](../module-1.6-xgboost-gradient-boosting/)
may also be the better answer.

</details>

### 8. An SVM baseline on imbalanced fraud labels mostly predicts the
majority class. What one-line configuration change is a reasonable first
response, and what should still be evaluated afterward?

<details><summary>Answer</summary>

A reasonable first response is to try `class_weight="balanced"` so the
classifier compensates for class frequency imbalance. After that, the
team should still evaluate the model using the measurement discipline
from
[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/)
and compare whether a tabular method from
[Module 1.6: XGBoost & Gradient Boosting](../module-1.6-xgboost-gradient-boosting/)
better fits the data regime. The config change is useful, but it is not
a substitute for regime-aware model selection.

</details>

## Hands-On Exercise: Ship a Fast Baseline Trio Without Lying to Yourself

The exercise goal is not to crown one permanent winner. The goal is to
practice leakage-safe implementation, identify the main failure mode of
each model, and write a short model-selection memo that you could defend
in a review.

### Setup

- [ ] Create a notebook or script where you can run three independent
  experiments: a text baseline for Naive Bayes, a mixed-scale tabular
  baseline for k-NN, and an imbalanced classification baseline for SVM.

- [ ] Re-read the pipeline discipline from
  [Module 1.1: Scikit-learn API & Pipelines](../module-1.1-scikit-learn-api-and-pipelines/)
  so that all preprocessing sits inside the fitted pipeline.

- [ ] Re-read the scaling rules from
  [Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/)
  before you start the k-NN and SVM parts.

- [ ] Decide in advance which evaluation outputs you will report. If you
  use classifier `score`, label it as accuracy, not AUC. If you need
  calibration reasoning, connect it back to
  [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/).

### Step 1: Build a Leakage-Safe `MultinomialNB` Text Baseline

- [ ] Create a small labeled text dataset or use an existing internal
  dataset with simple binary labels such as spam versus not spam, routed
  versus not routed, or urgent versus non-urgent.

- [ ] Split the data with `train_test_split(..., stratify=y)` so the
  class balance is preserved between train and test.

- [ ] Build a pipeline with `CountVectorizer()` followed by
  `MultinomialNB(alpha=1.0)`.

- [ ] Fit the pipeline only on the training split.

- [ ] Report held-out accuracy and print a few `predict_proba` rows.

- [ ] Write one sentence explaining why the probabilities are not safe
  to treat as calibrated estimates, referencing
  [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/).

- [ ] If your text labels are noticeably imbalanced, repeat the baseline
  with `ComplementNB` and note whether it behaves more sensibly for the
  minority class.

### Step 2: Compare k-NN With and Without Scaling

- [ ] Create or load a small tabular classification dataset where at
  least one feature has a much larger numeric range than the others.

- [ ] Build one pipeline with `KNeighborsClassifier(...)` alone and a
  second pipeline with `StandardScaler()` followed by the same
  `KNeighborsClassifier(...)`.

- [ ] Use the same train-test split and the same `k` value for both
  models so the comparison isolates the effect of scaling.

- [ ] Report test accuracy for both pipelines and explicitly label
  `Pipeline.score` as accuracy.

- [ ] Inspect at least one failure case and describe how the unscaled
  feature likely distorted the neighborhood geometry.

- [ ] Write a short note comparing this behavior to
  [Module 1.5: Decision Trees & Random Forests](../module-1.5-decision-trees-and-random-forests/),
  where scaling is usually not the main concern.

### Step 3: Train an Imbalanced `SVC` Baseline Carefully

- [ ] Create an imbalanced binary classification dataset, either from an
  internal problem or with `make_classification` using class imbalance.

- [ ] Build a pipeline with `StandardScaler()` followed by
  `SVC(kernel="rbf", class_weight="balanced")`.

- [ ] Fit the model and report held-out accuracy. If you want confidence
  ranking, inspect `decision_function` rather than immediately enabling
  `probability=True`.

- [ ] Write one paragraph explaining why `probability=True` is
  expensive, and when it would be justified despite the cost.

- [ ] Build a second pipeline with `LinearSVC` on the same dataset and
  compare the result qualitatively. You do not need a winner on every
  metric; you need a reasoned comparison.

- [ ] Explain the meaning of `C` in your own words and compare it to
  `LogisticRegression` `C` from
  [Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/).

### Step 4: Write a Model-Selection Memo

- [ ] Write a short memo with three sections: "What each baseline got
  right," "What each baseline got wrong," and "What I would ship first."

- [ ] In the Naive Bayes section, state clearly whether the problem is a
  fast sparse-text baseline and whether probability calibration matters.

- [ ] In the k-NN section, state whether local similarity is truly the
  product need or whether the model was just convenient to try.

- [ ] In the SVM section, state whether the boundary appears linear or
  curved, and whether the sample size makes the chosen SVM branch
  operationally reasonable.

- [ ] Compare your preferred model against at least one alternative from
  [Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/)
  or
  [Module 1.6: XGBoost & Gradient Boosting](../module-1.6-xgboost-gradient-boosting/),
  depending on whether your data is mostly linear or medium-sized
  tabular.

- [ ] End the memo with a single sentence naming the model you would
  ship first and the main risk you would monitor after deployment.

### Completion Check

- [ ] I kept preprocessing inside pipelines instead of fitting it on the
  full dataset first.

- [ ] I did not describe classifier `score` as AUC.

- [ ] I showed why Naive Bayes probabilities should not be treated as
  calibrated by default.

- [ ] I demonstrated that k-NN changes materially when scaling is added.

- [ ] I used a scaled SVM pipeline and explained the runtime implication
  of `probability=True`.

- [ ] I compared at least one model choice against
  [Module 1.2: Linear & Logistic Regression with Regularization](../module-1.2-linear-and-logistic-regression-with-regularization/)
  or
  [Module 1.6: XGBoost & Gradient Boosting](../module-1.6-xgboost-gradient-boosting/).

- [ ] My final recommendation names both the model I would ship and the
  specific failure mode I would watch.

## Sources

- User guide:
  https://scikit-learn.org/stable/modules/naive_bayes.html
- User guide:
  https://scikit-learn.org/stable/modules/neighbors.html
- User guide:
  https://scikit-learn.org/stable/modules/svm.html

- API reference:
  https://scikit-learn.org/stable/modules/generated/sklearn.naive_bayes.GaussianNB.html
- API reference:
  https://scikit-learn.org/stable/modules/generated/sklearn.naive_bayes.MultinomialNB.html
- API reference:
  https://scikit-learn.org/stable/modules/generated/sklearn.naive_bayes.BernoulliNB.html
- API reference:
  https://scikit-learn.org/stable/modules/generated/sklearn.naive_bayes.ComplementNB.html
- API reference:
  https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.KNeighborsClassifier.html
- API reference:
  https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.KNeighborsRegressor.html
- API reference:
  https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.NearestNeighbors.html
- API reference:
  https://scikit-learn.org/stable/modules/generated/sklearn.svm.SVC.html
- API reference:
  https://scikit-learn.org/stable/modules/generated/sklearn.svm.SVR.html
- API reference:
  https://scikit-learn.org/stable/modules/generated/sklearn.svm.LinearSVC.html
- API reference:
  https://scikit-learn.org/stable/modules/generated/sklearn.svm.LinearSVR.html

- Gallery example:
  https://scikit-learn.org/stable/auto_examples/svm/plot_iris_svc.html
- Gallery example:
  https://scikit-learn.org/stable/auto_examples/neighbors/plot_classification.html

## Next Module

Continue to [Module 1.8: Unsupervised Learning: Clustering](../module-1.8-unsupervised-learning-clustering/).
