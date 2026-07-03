---
title: "Recommender Systems"
description: "Build recommender systems as ranking systems, evaluate them with leakage-aware top-K discipline, and defend production choices against deceptively strong popularity baselines."
slug: ai-ml-engineering/machine-learning/module-2.4-recommender-systems
sidebar:
  order: 24
---

> Track: AI/ML Engineering | Complexity: `[MEDIUM]` | Time: 90-110 minutes
> Prerequisites: [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/), [Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/), [Module 1.7: Naive Bayes, k-NN & SVMs](../module-1.7-naive-bayes-knn-and-svms/), [Module 1.10: Dimensionality Reduction](../module-1.10-dimensionality-reduction/), and [Module 2.1: Class Imbalance & Cost-Sensitive Learning](../module-2.1-class-imbalance-and-cost-sensitive-learning/). This module also sets up a plain-text forward reference to Module 2.5, conformal prediction and uncertainty quantification.

The on-call story for recommender systems starts after the celebration. A team ships a fancy recommender that looked excellent in the notebook. Offline NDCG@10 was high. The dashboard was clean. The model card said the ranking objective matched the product surface. Then the A/B test failed. The first instinct was to blame traffic, seasonality, or a missing feature flag. The deeper review found a plainer problem. The offline split was random, so the same users appeared on both sides. The model was partly memorizing future taste. The popularity baseline was actually beating the new model in production. The offline metric the team celebrated did not match the engagement metric the deployment paid for.

The second hook is quieter but just as damaging. Another team optimizes RMSE on a rating column because ratings look like a supervised learning target. The model becomes good at predicting the middle of the rating distribution. It is safe, calibrated-looking, and wrong for the product. Users never see a single rating prediction. They see a top-5 list. The team never checks NDCG@10. The deployed recommendations are dominated by mediocre middle-of-the-bell-curve items because RMSE rewards the model for being correct on the bulk of ratings, not for getting the top of the list right.

This module is the correction. Recommender systems are not ordinary classification problems wearing a larger catalog. They are ranking systems under missing feedback, temporal leakage, cold-start constraints, and business tradeoffs that do not disappear just because the embedding dimension looks modern. You will learn how to name the problem before choosing the algorithm, build the boring baseline before trusting the clever model, and evaluate with the same discipline that [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/) applied to supervised ML.

## Learning Outcomes

By the end of this module, a practitioner will be able to:

1. **Diagnose** whether a product surface is really a recommendation problem, a search problem, a small-catalog merchandising problem, or a baseline ranking problem that should be handled before modeling.
2. **Compare** explicit-feedback, implicit-feedback, collaborative-filtering, content-based, hybrid, and two-tower recommender designs using the leakage and evaluation posture from [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/).
3. **Implement** an implicit-feedback matrix-factorization workflow with sparse user-item data, popularity baselines, ALS or BPR training, and top-K evaluation.
4. **Decide** when cold-start pressure, feature availability, catalog size, and serving constraints should move you toward content features from [Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/), similarity retrieval from [Module 1.7: Naive Bayes, k-NN & SVMs](../module-1.7-naive-bayes-knn-and-svms/), dimensional embeddings from [Module 1.10: Dimensionality Reduction](../module-1.10-dimensionality-reduction/), or a production two-tower design.
5. **Defend** a recommender-system evaluation plan that includes a named popularity baseline, time-aware splits, top-K metrics, failure slicing from [Module 2.2: Interpretability and Failure Slicing](../module-2.2-interpretability-and-failure-slicing/), and an honest statement about whether the offline result deserves an A/B test.

## Why This Module Matters

The canonical pitfall list is short enough to memorize and serious enough to break launches. Implicit and explicit feedback are different problems.
Top-K ranking metrics matter more than RMSE when users see lists. The popularity baseline is hard to beat. Time-stratified splits are not optional
because recommender systems are leakage-prone. Cold-start is structural, not algorithmic.

The Python ecosystem reflects these distinctions. The `implicit` project is a canonical Python library for implicit-feedback recommendation, with
documentation at https://benfred.github.io/implicit/. TensorFlow Recommenders is canonical production tooling for deep retrieval and ranking
workflows, with documentation at https://www.tensorflow.org/recommenders. Those two links alone tell an important story. One ecosystem helps you
iterate quickly on sparse interaction matrices. The other helps you build deep retrieval and ranking systems that fit modern serving stacks. Neither
relieves you from defining the feedback, split, metric, and baseline.

The reason this module appears after class imbalance, interpretability, and Bayesian ML is deliberate. Recommender systems magnify every modeling
habit you already have. If you celebrate a metric before naming the cost, the baseline, and the deployment target, recommendation work will punish you
faster than ordinary tabular classification. If you treat missing interactions as clean negatives, recommendation work will quietly teach the model
that unknown means disliked. If you split randomly because it is convenient, recommendation work will leak future preferences into the past.

## Section 1: What Recommendations Are and Aren't

A recommender system ranks items from a catalog for a user, session, account, household, device, or other decision context. The output is usually a
top-K list. The query is usually implicit. It is built from interaction history, context, metadata, and product rules rather than from a text box
where the user says exactly what they want.

That framing matters because it separates recommendation from classification. A classifier usually answers one point question at a time. Will this
claim be approved. Is this email spam. Will this customer churn. A recommender answers a list question. Given this user and this moment, which items
should occupy the scarce visible slots.

The ranking surface changes the loss you care about. If the best item is ranked first and the second-best item is ranked third, the system behaves
very differently than if the best item is ranked tenth. Point prediction error hides that distinction. Top-K evaluation exposes it.

Recommendation is also different from search. In search, the user gives an explicit query. The retrieval system can lean heavily on lexical matching,
semantic matching, or both. In recommendation, the query is often a behavioral trace. The user did not type "show me something adjacent to the last
two tutorials I completed but not too similar to the one I abandoned." The model infers that need from history.

That inference is useful only when the product surface actually needs it. Many teams reach for recommender systems because recommendations sound
strategic. Sometimes the catalog is small enough to enumerate. Sometimes the user knows exactly what they want and search is better. Sometimes pure
popularity solves the problem well enough that personalization adds operational risk without enough upside.

The first professional question is therefore not "which algorithm should we use." It is "what decision does the ranking change." If a user sees three
featured items selected by editorial policy, a recommender may be a weak fit. If a marketplace has millions of items and each user only sees a tiny
page, ranking quality becomes product quality.

The catalog size matters because recommendation is partly about scarcity. When every item can be displayed, there is no ranking problem in the strict
sense. When only a few items can be shown, every rank position has opportunity cost. One recommended item displaces another. That displacement is why
a popularity baseline is not a toy. It is the first serious competitor.

Recommendation also has a feedback-loop problem that ordinary one-shot classification may not have. The system influences what users can see. What
users see influences what they click, buy, watch, or ignore. Those interactions become future training data. The model does not merely observe
behavior. It helps create the behavior it later learns from.

This feedback loop makes caution valuable. A model that over-personalizes can narrow a user's experience. A model that over-optimizes short-term
clicks can lower long-term satisfaction. A model that favors already popular items can make the catalog less healthy. The right recommender design is
therefore a product decision as much as a modeling decision.

> **Pause and decide** — A product manager asks for a recommender on a catalog with fewer than twenty items,
> all visible on one screen. What evidence would you need before agreeing that personalization is worth
> building?

The answer should be concrete. You would look for a scarce ranking surface, repeated behavior, meaningful differences across users, and a measurable
business decision that changes when the order changes. Without those conditions, a simpler sort, filter, or editorial rule may be the more honest
system.

## Section 2: Implicit vs Explicit Feedback — the Foundational Split

The first split in recommender systems is not between simple and deep models. It is between explicit feedback and implicit feedback. Explicit feedback
is what a user intentionally provides as a preference label. Ratings, stars, thumbs, and written reviews are explicit. They look supervised because
the target is visible. They also look cleaner than they usually are.

Explicit feedback was the historical default in much of recommender-system education. That is why many older examples start with a rating matrix. The
user gave item A five stars and item B two stars. The model predicts missing ratings. The evaluation computes rating error. This is a coherent problem
when the product really asks users for ratings and uses predicted ratings operationally, but it has become much less common in modern production systems
compared with implicit behavioral signals like clicks, watches, and purchases.

It is less common in production systems now. Many modern surfaces do not ask users for ratings at all. They observe behavior. Clicks, views,
purchases, dwell time, completed plays, saves, shares, add-to-cart events, skips, and repeat visits are implicit signals. They are abundant. They are
also ambiguous.

A click may mean interest. It may mean curiosity. It may mean confusion. A long dwell time may mean engagement. It may mean the user left the tab
open. A purchase is a strong signal, but the absence of a purchase is not a clean negative. The user may never have seen the item. The item may have
been out of stock. The price may have been wrong for that moment.

This is the no-negative-signals trap. In implicit feedback, missing does not mean disliked. Most user-item pairs are unobserved because the catalog is
large. Treating all missing pairs as negative labels teaches the model a false world where every unseen item was actively rejected. That is not what
happened. The model needs a learning objective that understands confidence and sampling.

Different libraries encode this difference. Surprise focuses on explicit rating-prediction and neighborhood- style recommendation workflows, with
documentation at https://surpriselib.com/. The `implicit` library focuses on implicit-feedback models such as ALS and BPR, including the CPU ALS model
documented at https://benfred.github.io/implicit/api/models/cpu/als.html. LightFM combines collaborative and content signals under a hybrid objective.
TensorFlow Recommenders supports deep retrieval and ranking models, including two- tower systems.

The library choice is therefore not merely aesthetic. If you have star ratings and a product that consumes predicted ratings, Surprise may match the
problem. If you have clicks, plays, carts, or purchases, `implicit` is often the faster first serious tool. If you have sparse interactions plus
useful item and user features, LightFM is a pragmatic hybrid option. If you need neural feature encoders and large-scale serving, TensorFlow
Recommenders becomes relevant.

The dangerous move is to pick the library first. The disciplined move is to name the feedback. What is the observed event. What does the event mean.
What does non-observation mean. What top-K list does the user actually see. What would count as a win online.

These questions sound administrative. They are modeling questions. A purchase-only recommender will learn a different preference space from a
view-based recommender. A dwell-time recommender will learn a different preference space from a completion recommender. A thumbs-up recommender can
treat feedback more like explicit preference. The model cannot fix a poorly defined signal.

When teams skip this step, they often produce impressive offline notebooks and confusing product behavior. The matrix has numbers. The factorizer
converges. The nearest neighbors look plausible. The top-K metric moves. Then the launch fails because the numbers never represented the decision the
product was trying to improve.

## Section 3: Collaborative Filtering — User-User and Item-Item k-NN

Collaborative filtering starts from a simple bet. Users who behaved similarly in the past may like similar items in the future. Items consumed by
similar users may be substitutes, complements, or thematic neighbors. You can recommend without knowing much about the item content if you know enough
about interaction patterns.

The older user-user version is easy to explain. Find users similar to the current user. Recommend items those similar users liked and the current user
has not seen. This is the neighborhood logic from k-NN applied to rows of a user-item matrix. The connection to [Module 1.7: Naive Bayes, k-NN &
SVMs](../module-1.7-naive-bayes-knn-and-svms/) is direct. Similarity, distance, sparsity, and the curse of dimensionality all matter.

The item-item version flips the comparison. Find items similar to items the user already liked. Recommend those similar items. In many production
settings item-item methods are more stable than user-user methods because items change less frequently than users. User behavior can shift session by
session. Item neighborhoods often remain useful longer.

The Surprise documentation has a dedicated section for k-NN-inspired algorithms at https://surprise.readthedocs.io/en/stable/knn_inspired.html. That
page is useful because it keeps the neighborhood family separate from matrix factorization. Both can recommend. They make different assumptions and
fail differently.

User-user collaborative filtering struggles when user histories are short. If most users have only a handful of interactions, their nearest neighbors
are unstable. The system can become dominated by popular items because those are the only shared coordinates with enough overlap. It can also be
expensive if the user base is large and neighborhoods need to be updated frequently.

Item-item collaborative filtering struggles with cold items. An item with no interactions has no collaborative neighborhood. Content features may
describe it beautifully, but pure collaborative filtering does not see them. This limitation is not an implementation bug. It follows from the
definition of the method.

The appeal of item-item methods is interpretability. If a user liked an introduction to shell pipelines, recommending a neighboring module on text
processing may be easy to explain. If a user bought one replacement part, recommending compatible parts may be operationally useful. Not every
recommendation surface needs deep embeddings.

The weakness is that neighborhood systems can become local. They recommend items close to what the user already did. That is sometimes desirable. It
is sometimes boring. The difference between relevance and repetition is a product question.

Neighborhood recommenders also force you to confront sparse-matrix mechanics. The user-item matrix is mostly empty. A dense array would waste memory
and compute. The sparse matrix tools in SciPy are therefore part of the practical stack. SciPy documents its sparse array and matrix support at
https://docs.scipy.org/doc/scipy/reference/sparse.html, including CSR matrices at
https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.csr_matrix.html.

CSR format is especially natural for user-item interactions because each row can hold the items associated with one user. That makes it convenient to
slice a user's history. It also makes top-K recommendation code tractable for moderate experiments. The representation is not glamorous, but it is one
of the places where recommender-system engineering becomes real.

## Section 4: Matrix Factorization — Decomposing the User-Item Matrix

Matrix factorization replaces explicit neighborhoods with latent factors. The idea is to approximate a user- item interaction matrix `R` as the
product of two smaller matrices. One matrix contains user embeddings. The other contains item embeddings. In shorthand, `R ≈ U @ V.T`.

Each user becomes a vector in a lower-dimensional space. Each item becomes a vector in the same space. The score for a user-item pair is usually a dot
product. If the user vector points in a similar direction to the item vector, the score is high. If the directions are misaligned, the score is lower.

This is why [Module 1.10: Dimensionality Reduction](../module-1.10-dimensionality-reduction/) is a prerequisite. Matrix factorization is a
recommender-specific version of the same compression instinct. The observed matrix is enormous and sparse. The useful structure is assumed to live in
a lower-dimensional latent space.

The old explicit-feedback story often starts with SVD-style decompositions. You have ratings. You factor the rating matrix. You predict missing
ratings. That can still be useful when ratings are real operational targets. But implicit-feedback systems usually need objectives that handle
confidence, sampling, and ranking.

Alternating least squares, or ALS, is one classic answer. In the implicit-feedback setting, the model treats observed interactions as positive
preference signals with different confidence weights. The common Hu, Koren, and Volinsky formulation uses confidence values like `C_ui = 1 + alpha *
r_ui`, where `r_ui` is an interaction strength. More interactions increase confidence that the positive preference signal is real. Missing
interactions still influence training, but they are not treated like equally confident negative ratings.

The `implicit` ALS implementation documents this model at https://benfred.github.io/implicit/api/models/cpu/als.html. One mapping detail matters in
practice: you do not build the `1 + alpha * r_ui` confidence matrix yourself. You pass `implicit` the raw interaction matrix (the `r_ui` values), and the
library applies the `alpha` scaling internally while treating unobserved entries as the baseline confidence. Pre-multiplying the `+ 1` into the matrix you
hand to the library double-counts that baseline. The library is useful because it
makes the sparse implicit workflow feel like a normal Python workflow. That convenience should not hide the modeling assumption. ALS learns factors
that reconstruct confidence-weighted preference patterns. It does not discover intent by magic.

BPR, or Bayesian Personalized Ranking, takes a different route. It is pairwise. Instead of trying to reconstruct the whole matrix, it trains the model
to score observed items above sampled unobserved items for the same user. In words, it tries to maximize a function like `sigma(score(user, seen_item)
- score(user, random_unseen_item))`. That objective is closer to ranking than to rating prediction.

The `implicit` BPR implementation is documented at https://benfred.github.io/implicit/api/models/cpu/bpr.html. The original BPR paper is available at
https://arxiv.org/abs/1205.2618. For practitioners, the most important distinction is not the word Bayesian in the title. It is the pairwise ranking
posture. The model is trained on comparisons that resemble the top-K problem more closely than RMSE does.

Here is a compact ALS workflow on a synthetic sparse interaction matrix. It is intentionally small enough to run on a laptop. The shape and sparse
representation matter more than the toy data.

```python
import numpy as np
import scipy.sparse as sp
from implicit.als import AlternatingLeastSquares
from implicit.evaluation import ndcg_at_k, precision_at_k, train_test_split

rng = np.random.default_rng(11)
n_users = 200
n_items = 500
n_interactions = 3000

user_ids = rng.integers(0, n_users, size=n_interactions)
item_ids = rng.integers(0, n_items, size=n_interactions)
strengths = rng.integers(1, 5, size=n_interactions).astype(np.float32)

user_items = sp.csr_matrix(
    (strengths, (user_ids, item_ids)),
    shape=(n_users, n_items),
)
user_items.sum_duplicates()

train_user_items, test_user_items = train_test_split(
    user_items,
    train_percentage=0.8,
    random_state=11,
)

model = AlternatingLeastSquares(
    factors=32,
    regularization=0.05,
    iterations=15,
    random_state=11,
)
model.fit(train_user_items)

score_ndcg = ndcg_at_k(model, train_user_items, test_user_items, K=10)
score_precision = precision_at_k(model, train_user_items, test_user_items, K=10)

print(f"NDCG@10: {score_ndcg:.3f}")
print(f"precision@10: {score_precision:.3f}")
```

That code is not a production evaluation plan. It uses the library split helper for a compact exercise. A production evaluation should use a
time-aware split when timestamps exist. The point here is to show the shape of the system. Interactions become a sparse matrix. The model fits latent
factors. The evaluation uses top-K ranking metrics.

> **Pause and predict** — If you optimize RMSE on a five-star rating matrix, why might the resulting top-5
> recommendation list still feel weak to users?

The answer is that RMSE rewards average point accuracy. Top-K surfaces reward putting the most useful items near the top. A model can be numerically
good on common middle ratings and still fail the ranking job. That mismatch is the source of many recommender-system disappointments.

Matrix factorization also has an interpretability tradeoff. The factors are useful but not always semantically clean. One latent dimension may mix
price sensitivity, topic preference, and item age. Another may capture a product-policy artifact. You can inspect nearest items and factor loadings,
but you should not assume the dimensions have stable human meanings.

This is where the interpretability posture from [Module 2.2: Interpretability and Failure
Slicing](../module-2.2-interpretability-and-failure-slicing/) helps. Do not merely ask whether the global NDCG improved. Ask which users improved. Ask
which catalog regions got buried. Ask whether new items, niche items, or minority segments lost visibility. The recommender is a ranking policy, not
just an embedding file.

## Section 5: Content-Based Recommendations

Content-based recommendation uses item attributes directly. The attributes may be text, tags, categories, prices, authors, instructors, brands,
release windows, images, audio features, or learned embeddings. The core idea is to recommend items similar to items the user has already shown
interest in, using item descriptions rather than only collaborative patterns.

This approach is cold-start friendly for new items. A brand-new item has no interactions. Pure collaborative filtering cannot place it well. A
content-based model can still compare its metadata, text, or embedding to items that already have histories. That is why content features matter even
in systems that eventually become collaborative or hybrid.

A simple text-based prototype can be built with TF-IDF item descriptions. That prototype is not the final word. It is a useful sanity check because it
exposes whether item content contains enough signal to group related items. It also helps distinguish "we have no cold-start strategy" from "we have a
reasonable first fallback."

```python
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

descriptions = [
    "kubernetes scheduling pods nodes cluster operations",
    "linux shell pipelines text processing awk sed",
    "container image security scanning vulnerabilities",
    "python feature engineering tabular machine learning",
    "kubernetes networking services ingress dns",
]

vectorizer = TfidfVectorizer(stop_words="english")
item_vectors = vectorizer.fit_transform(descriptions)

query_index = 0
scores = item_vectors[query_index] @ item_vectors.T
ranked = np.asarray(scores.toarray()).ravel().argsort()[::-1]

recommendations = [idx for idx in ranked if idx != query_index][:3]
print(recommendations)
```

The tradeoff is taste nuance. Content similarity can tell you that two items are textually or visually close. It may miss the collaborative fact that
users who start with one category often graduate to another. It may over-recommend near-duplicates. It may be too literal.

Modern content-based systems often use deep embeddings. Text descriptions may be encoded by BERT-like models. Images may be encoded by vision models.
Audio, video, and structured metadata can be embedded as well. Those encoders can produce rich item representations before an item has any interaction
history. They still require evaluation against the product surface.

Content-based recommendation also inherits feature-engineering risk. If category labels are stale, the recommendations will be stale. If item
descriptions are written for search-engine marketing rather than user meaning, the vectors may group items oddly. If image embeddings capture
background style instead of item utility, visual similarity may not equal recommendation relevance.

The practical stance is to treat content as a source of signal, not truth. It is especially valuable for new items and sparse catalogs. It is rarely
enough by itself once there is rich behavioral data.

## Section 6: Hybrid Approaches — the Production Sweet Spot

Hybrid recommenders combine collaborative signals with content or context features. This is often the production sweet spot because the data itself is
hybrid. Users have histories. Items have attributes. Sessions have context. Catalogs have policies. The model should not pretend only one of those
sources exists.

LightFM is a practical example. Its documentation at https://making.lyst.com/lightfm/docs/home.html describes a hybrid recommendation library that can
combine collaborative filtering with user and item features. The model details are documented at https://making.lyst.com/lightfm/docs/lightfm.html.
The appeal is that you can keep a matrix-factorization-like workflow while adding content features that help sparse users or sparse items.

Hybrid systems reduce cold-start pain because item features can stand in before collaborative history accumulates. They also reduce
over-specialization because metadata can connect items that behavior alone has not yet linked. They do not remove the need for careful metrics. A
hybrid system can still over-rank popular items, leak temporal information, or optimize the wrong engagement proxy.

Another influential hybrid idea is Wide & Deep learning. The paper at https://arxiv.org/abs/1606.07792 describes combining memorization through wide
cross-product features with generalization through deep neural features. That framing remains useful even when the exact architecture changes.
Production recommenders often need both memorized rules and learned embeddings.

The wide side can capture known co-occurrences, category crosses, and business features that should not be hidden inside an opaque representation. The
deep side can generalize across sparse combinations. Together they handle a tension that pure collaborative filtering and pure content-based models
often struggle with separately.

Hybrid usually wins in production because production data is not pure. The user who just registered has profile or onboarding features but little
history. The item that just launched has metadata but no interactions. The mature user and mature item have rich collaborative signal. A single system
may need to serve all three cases.

This is also where architecture becomes less about leaderboard elegance and more about routing. New users may receive popularity-with-segment
recommendations. Known users may receive personalized retrieval. New items may be injected through content lookalikes or exploration budgets. Mature
items may compete through collaborative ranking. The "model" is often a system of models, fallbacks, and rerankers.

## Section 7: Two-Tower Architectures (Modern Production)

Two-tower architectures are a modern production pattern for large-scale retrieval. One tower encodes the user or query context. The other tower
encodes the item. At inference time, the system scores candidate items with a dot product or similarity function between the two embeddings.

The architecture is attractive because item embeddings can be pre-computed. If the catalog has millions of items, you do not want to run a heavy
neural network over every item for every request. You compute item vectors ahead of time. You compute the user vector online. Then you retrieve
nearest item vectors using approximate nearest neighbor search.

FAISS and ScaNN are common names in this serving conversation. The important idea is sub-linear retrieval. The system searches an embedding index
instead of scanning the whole catalog. That is what makes two-tower retrieval operationally plausible at large scale.

TensorFlow Recommenders provides canonical examples of this pattern. The basic retrieval tutorial is at
https://www.tensorflow.org/recommenders/examples/basic_retrieval. The efficient serving tutorial is at
https://www.tensorflow.org/recommenders/examples/efficient_serving. The broader API documentation is at
https://www.tensorflow.org/recommenders/api_docs/python/tfrs.

Two-tower systems are often the first stage of a larger recommender pipeline. The retrieval tower finds hundreds or thousands of plausible candidates.
A ranking model then scores those candidates with richer features. A reranker may enforce diversity, freshness, business constraints, or safety rules.
The final list is therefore not merely the raw nearest neighbors.

This staged design matters because no single model can usually do everything well at production scale. Retrieval needs to be fast and broad. Ranking
can be slower and more feature-rich because it sees fewer candidates. Reranking can handle list-level constraints that item-wise scoring misses.

The user tower may include interaction history, recent session events, profile features, device context, or geography. The item tower may include ID
embeddings, category embeddings, text embeddings, image embeddings, price features, and freshness features. Transformer-style attention encoders can
be used for sequence histories or rich text, but that is an architecture choice rather than a license to ignore evaluation.

Two-tower models introduce their own failure modes. If the retrieval objective overfits frequent items, the candidate set becomes too narrow. If item
embeddings are stale, fresh catalog changes lag. If the ANN index is not rebuilt or incrementally updated, serving no longer matches training
assumptions. If the ranking stage never sees candidates from minority catalog regions, it cannot rescue them later.

The main practical lesson is that retrieval quality caps ranking quality. A ranker cannot choose an item it never receives. That makes
candidate-generation metrics and slice analysis important. Top-K evaluation at the final list is necessary but not sufficient when the pipeline has
multiple stages.

> **Pause and decide** — In a two-stage recommender, the final ranker performs well on candidates it
> receives, but niche items rarely enter the candidate set. Which component should you inspect first, and
> why?

The answer is the retrieval stage. Candidate generation controls what the ranker is allowed to consider. If retrieval excludes a catalog region, no
downstream ranker can repair that absence without a separate injection or exploration path.

## Section 8: The Cold-Start Problem

Cold-start is not a bug that disappears with the right algorithm. It is a structural fact. A recommender needs evidence about users and items. When
that evidence is absent, the system must fall back to other information or make a policy choice.

New-user cold-start happens when a user has little or no history. The model does not know their taste. Common mitigations include global popularity,
popularity within a coarse segment, onboarding questions, registration features, inferred context, or signals from a sister domain. Each mitigation
has a cost.

Popularity is robust but not personal. Onboarding can be useful but adds friction. Registration features can be predictive but sensitive.
Sister-domain signals can help if the domains are genuinely related. Context can be valuable but may be unstable. There is no free solution.

New-item cold-start happens when an item has no interaction history. Collaborative filtering cannot infer much from zero interactions. Content
features become the obvious fallback. Tags, descriptions, categories, images, authors, brands, and embeddings can place the item near similar known
items. Exploration policies can then gather real feedback.

The honest framing is that cold-start cannot be solved in the mathematical sense. It can be sidestepped, softened, or managed. You can design better
fallbacks. You can ask for more data. You can use content. You can explore. You cannot infer a specific user's preference for a specific item from no
evidence and no useful features.

Cold-start also changes evaluation. If your test set contains only mature users and mature items, the offline metric will flatter a collaborative
model. If production traffic includes many new users or new items, the launch may underperform. Slice the evaluation by user history length and item
age or item interaction count.

This is a direct application of the failure-slicing discipline from [Module 2.2: Interpretability and Failure
Slicing](../module-2.2-interpretability-and-failure-slicing/). Global NDCG may improve while new users get worse. Global precision may improve while
new items never surface. Those are not side notes. They are product risks.

Cold-start also forces organizational clarity. If a team says "the recommender should recommend new items," ask how new items enter the candidate set.
If the answer is "the model will learn it," ask what data the model will learn from. If the item is new, the collaborative answer is "none." That is
when content, exploration, or merchandising policy enters the design.

## Section 9: Evaluation Discipline — Splits and Metrics

Evaluation is where recommender systems most often lie to their builders. The lies are not usually malicious. They are convenient. A random split is
convenient. RMSE is convenient. A single global metric is convenient. None of those conveniences is enough for a production recommender.

The metric should match the surface. If users see a ranked list, use top-K ranking metrics. NDCG@k rewards relevant items near the top. MAP@k
summarizes precision across ranks. Hit-rate@k asks whether at least one relevant item appears in the list. MRR rewards placing the first relevant item
early. Recall@k asks how much of the held-out relevant set the list recovered. RMSE on ratings is mostly historical unless predicted ratings are the
product.

The `implicit` evaluation API documents ranking metrics including precision, MAP, and NDCG at https://benfred.github.io/implicit/api/evaluation.html.
That documentation is useful because it keeps the workflow close to sparse implicit matrices rather than forcing you through rating-prediction habits.

The split should match time. A production recommender uses the past to rank future opportunities. The offline evaluation should respect that order.
The standard pattern is leave-future-out. For each user, train on earlier interactions and test on later interactions where possible. At minimum,
avoid random splits that allow future taste to inform past recommendations.

User-stratified splits can still leak. They may keep each user on both sides, which sounds fair, but they can train on future interactions and test on
earlier ones. That is not how production works. Random splits definitely leak when the same user's future behavior appears in the training side. The
on-call story at the start of this module is built around that mistake.

This is the recommender-system version of the leakage discipline from [Module 1.3: Model Evaluation, Validation, Leakage &
Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/). The target may not be a single label column, but the principle is
identical. Do not let information from the future, the test surface, or the deployment outcome leak into training.

Offline metrics also correlate weakly with online outcomes. That does not make them useless. It makes them filters. An offline metric can reject bad
ideas cheaply. It can compare candidate systems under controlled assumptions. It can show whether a model clears the popularity baseline. It cannot
prove that users will behave better online. The A/B test is the ground truth for product impact.

Offline evaluation should therefore end with a decision statement. Does the model beat the named baseline on the metric that matches the surface. Does
it avoid obvious slice regressions. Does it preserve enough diversity or novelty for the product goal. Is the expected upside large enough to justify
an online experiment. That statement is more useful than a metric screenshot.

The split and metric also interact with negative sampling. In implicit recommendation, you rarely evaluate against every unobserved item naively. The
unobserved universe is huge and mostly unknown. Some evaluation protocols rank against all items. Some sample candidate negatives. Whatever you
choose, document it. Changing the candidate set can change the metric.

You should also keep training and serving filters aligned. If production filters out unavailable, already- owned, unsafe, or ineligible items, offline
evaluation should respect comparable constraints. Otherwise the model gets credit for recommendations the product could never show.

## Section 10: Beating the Popularity Baseline

The popularity baseline is the most humbling model in recommender systems. It recommends what many users already interact with. It is cheap. It is
stable. It often performs surprisingly well. Many fancy recommenders only look impressive because nobody compared against a serious popularity
baseline.

There are levels to this baseline. Global popularity ranks items by total interactions. Popularity within segment ranks items within region, cohort,
category, language, subscription plan, or other meaningful context. Popularity with novelty discounts items that are already too familiar or too
dominant. The second version often erases naive personalization wins.

This echoes the baseline discipline from [Module 2.1: Class Imbalance & Cost-Sensitive
Learning](../module-2.1-class-imbalance-and-cost-sensitive-learning/). Name the baseline before you celebrate the alternative. In imbalanced
classification, a trivial classifier can look good under the wrong metric. In recommendation, popularity can look unsophisticated while quietly
winning the product.

The baseline should be implemented, evaluated, and shown. Do not describe it abstractly in a meeting. Build it. Measure NDCG@10, precision@10,
recall@10, and any list-level metric that matters for the surface. Slice it by user history length and item maturity. Then compare the model.

If the model does not beat global popularity, it is not ready. If it beats global popularity but not segment popularity, it may not be ready. If it
beats ranking metrics but harms diversity, novelty, or long-term engagement, the decision is not automatic. The baseline is not a bureaucratic gate.
It is a defense against self-deception.

A popularity baseline can also be a production fallback. When user history is missing, use popularity. When the model service is down, use popularity.
When candidate generation returns too few items, backfill with popularity. The baseline is part of system resilience.

The most mature teams do not treat popularity as embarrassing. They treat it as the floor. Personalization has to earn its cost above that floor.

## Section 11: Diversity, Novelty, Serendipity

Relevance is not the only property of a recommendation list. Diversity asks whether the list covers multiple categories, creators, topics, or item
types instead of repeating near-duplicates. Novelty asks whether the items are not already obvious or overexposed to the user. Serendipity asks
whether the list contains useful surprises: items the user might not have found but may genuinely value.

These concepts are related but not identical. A list can be diverse without being novel if it covers several popular categories. A list can be novel
without being relevant if it surfaces obscure but unappealing items. A list can be serendipitous only when surprise and usefulness meet.

Production systems often add these properties through reranking. The model first produces a relevance-ranked candidate list. A reranker adjusts the
list to reduce redundancy, enforce category coverage, or include controlled exploration. Common approaches include maximal marginal relevance,
determinantal point processes, and simpler heuristics.

The tradeoff is real. Increasing diversity can reduce NDCG if the metric only rewards held-out interactions. Increasing novelty can reduce short-term
clicks if familiar items are easier to choose. Adding serendipity can improve long-term satisfaction but make offline measurement harder.

This is why the metric plan must reflect product intent. A learning platform may want a sequence that balances continuity with breadth. A marketplace
may want substitutes, complements, and discovery. A media surface may care about completion, return visits, and catalog health. The same NDCG@10
movement can mean different things in those contexts.

List-level metrics are also where stakeholder vocabulary matters. If the product team asks for "less repetitive" recommendations, translate that into
a measurable diversity or redundancy check. If they ask for "freshness," define whether that means new to the catalog, new to the user, or recently
updated. If they ask for "discovery," decide whether novelty alone is enough.

Recommendation quality is therefore multi-objective. The top-K model supplies relevance. The system may also need diversity, novelty, fairness,
freshness, availability, policy compliance, and latency. Pretending one scalar metric captures everything is a choice. It is usually a bad one.

## Section 12: Practitioner Playbook

Start by choosing the feedback type. For most modern systems, assume implicit feedback by default. Name the event, its strength, and its ambiguity. Do
not call non-observation a negative label unless the product truly exposed the item and the user rejected it.

Build the popularity baseline first. Build global popularity. Build popularity within the most obvious segment. Consider a novelty-aware version if
the surface needs discovery. Keep the code simple enough that anyone on the team can inspect it.

Then try a fast collaborative model. For implicit feedback, ALS and BPR are strong first experiments. The `implicit` project exposes both model
families through a sparse-matrix workflow, with model documentation collected at https://benfred.github.io/implicit/api/models/index.html. Do not jump
to a deep two-tower system until the simpler baselines tell you what problem remains.

If content features are strong or cold-start is important, try a hybrid design. LightFM is a practical option for combining collaborative and content
features. Content-only similarity may also be a useful fallback. The right answer may be a routing system rather than a single model.

For scale or deep feature encoders, consider a two-tower architecture. Use separate user and item encoders. Pre-compute item embeddings. Serve
retrieval through an approximate nearest neighbor index. Add a ranker or reranker when candidate quality is not enough.

Evaluate with time-stratified splits when timestamps exist. Use NDCG@k, precision@k, recall@k, MAP@k, hit- rate@k, or MRR depending on the surface.
Report at least one list-level diversity or novelty check when the product cares about discovery. Slice by user history length, item age, segment, and
catalog region.

A/B test before claiming a product win. Offline improvement is a qualification step. It is not proof of engagement, retention, learning progress,
revenue, or user satisfaction. The launch decision should say what online metric the model is expected to move and what guardrails must hold.

The playbook is simple because the hard part is discipline. Pick the feedback. Build the baseline. Train the first model. Use the right split. Use
top-K metrics. Check diversity. Slice failures. Run the online test. Then decide.

## Section 13: When Recsys Is the Wrong Tool

Recommender systems are powerful, but they are not a universal interface. If the catalog is small enough to enumerate, personalization may add
complexity without improving the user experience. A clear sorted list, filters, or tabs may be better.

If users explicitly know what they want, search usually beats recommendation. A user looking for a specific module, product, policy, or document does
not need taste inference. They need retrieval. Similarity-based retrieval from [Module 1.7: Naive Bayes, k-NN &
SVMs](../module-1.7-naive-bayes-knn-and-svms/) may be the right tool when the query is explicit and the catalog can be matched directly.

If cold-start dominates the product, a recommender may still be useful, but the core problem is data acquisition and feature design. An algorithm
cannot personalize without signal. Onboarding, metadata quality, exploration policy, and content embeddings may matter more than model choice.

If pure popularity solves the surface, accept that result. There is no engineering virtue in replacing a robust baseline with a fragile personalized
model that does not improve the decision. The goal is not to deploy recommendation technology. The goal is to rank the right items for the user and
product.

If the cost of wrong recommendations is high, slow down. Education, healthcare, finance, safety, and regulated domains can make ranking errors
consequential. The system may need constraints, review, uncertainty framing from Module 2.5, or a human-in-the-loop workflow before personalization is
acceptable.

The final test is pragmatic. Can you name the scarce ranking surface. Can you name the feedback. Can you name the baseline. Can you name the top-K
metric. Can you name the cold-start route. Can you name the online decision. If not, you do not yet have a recommender-system plan.

## Did You Know?

- The `implicit` project documents ALS, BPR, nearest-neighbor models, evaluation helpers, and ANN integrations under its canonical documentation at https://benfred.github.io/implicit/
- Surprise is oriented around explicit rating-prediction and neighborhood or matrix-factorization algorithms, with getting-started documentation at https://surprise.readthedocs.io/en/stable/getting_started.html
- TensorFlow Recommenders separates retrieval, ranking, multitask modeling, and efficient serving examples, starting from https://www.tensorflow.org/recommenders/examples/basic_retrieval
- RecBole provides a broader research-oriented recommendation library and benchmark toolkit documented at https://recbole.io/docs/index.html

## Common Mistakes

| Mistake | Why it bites | Fix |
|---|---|---|
| Optimizing RMSE for a top-K surface | The model can predict average ratings well while ranking the best items poorly | Use NDCG@k, MAP@k, recall@k, precision@k, hit-rate@k, or MRR |
| Randomly splitting interactions | Future user behavior leaks into training and inflates offline results | Use time-stratified leave-future-out splits where timestamps exist |
| Treating missing implicit interactions as negatives | Most missing pairs were never exposed, so the label is unknown rather than disliked | Use implicit-feedback objectives, confidence weighting, or sampled comparisons |
| Skipping the popularity baseline | A complex model may only beat a weak strawman | Evaluate global popularity, segment popularity, and novelty-aware popularity |
| Ignoring cold-start slices | Mature-user metrics can hide new-user or new-item failure | Slice by user history length, item age, and interaction count |
| Assuming retrieval quality can be fixed by ranking | The ranker cannot choose candidates it never receives | Measure candidate recall and inspect retrieval-stage coverage |
| Reporting one global metric | Catalog health, diversity, and segment regressions disappear | Add list-level checks and failure slicing |
| Calling offline improvement a launch win | Offline metrics only approximate product behavior | Use offline results to qualify an A/B test, not replace it |

## Quiz

1. A team trains a rating-prediction model and reports excellent RMSE. The product shows users a top-10
   carousel. What is the main evaluation problem?

<details> <summary>Answer</summary>

RMSE measures point prediction error on ratings, not top-K ranking quality. The team should evaluate list metrics such as NDCG@10, MAP@10, recall@10,
or precision@10 against a named baseline.

</details>

2. A random interaction split gives a new ALS model strong NDCG@10. The A/B test fails. What leakage pattern
   should you suspect first?

<details> <summary>Answer</summary>

The same user's future interactions may have appeared in training while earlier or mixed interactions appeared in test. A time-aware leave-future-out
split is more realistic for production.

</details>

3. A catalog has many brand-new items every day and few interactions per item. Pure collaborative filtering
   performs poorly. What kind of signal should you add first?

<details> <summary>Answer</summary>

Add content features such as tags, descriptions, categories, image embeddings, or other item metadata. New items need non-collaborative evidence until
interactions accumulate.

</details>

4. A two-tower retriever has good final-list NDCG for popular items but rarely surfaces niche catalog
   regions. Why might the ranker be unable to fix this?

<details> <summary>Answer</summary>

The ranker only scores candidates it receives. If retrieval never admits niche items into the candidate set, downstream ranking cannot select them.

</details>

5. A stakeholder asks why the recommender is being compared to "just popular items." What should you say?

<details> <summary>Answer</summary>

Popularity is a strong, stable, cheap baseline and often wins in production. Personalization must demonstrate value above global and segment-level
popularity before it earns additional complexity.

</details>

6. A model recommends ten near-duplicate items and has high NDCG@10. Users complain that the list feels
   repetitive. What metric family is missing?

<details> <summary>Answer</summary>

A list-level diversity or redundancy metric is missing. Relevance metrics can reward items that match held-out behavior while still producing a
repetitive list.

</details>

7. A new user has no interaction history. The team says ALS will personalize once the request arrives. What
   is wrong with that claim?

<details> <summary>Answer</summary>

ALS needs interaction evidence to place the user in the latent space. A new user requires a fallback such as popularity, onboarding, profile features,
contextual routing, or sister-domain signals.

</details>

8. A model beats global popularity but loses to popularity within user segment. Should the team claim a
   recommender win?

<details> <summary>Answer</summary>

Not yet. Segment-aware popularity is a stronger and more realistic baseline. The model should beat that baseline or justify why another product
tradeoff, such as diversity or novelty, makes it worth testing.

</details>

## Hands-On Exercise

- [ ] Generate or load a synthetic implicit-feedback user-item interaction matrix as a `scipy.sparse.csr_matrix`.

```python
import numpy as np
import scipy.sparse as sp

rng = np.random.default_rng(21)
n_users = 300
n_items = 800
n_events = 6000

user_ids = rng.integers(0, n_users, size=n_events)
item_ids = rng.integers(0, n_items, size=n_events)
strengths = rng.integers(1, 6, size=n_events).astype(np.float32)

user_items = sp.csr_matrix(
    (strengths, (user_ids, item_ids)),
    shape=(n_users, n_items),
)
user_items.sum_duplicates()
```

- [ ] Build a popularity baseline by counting the globally most-interacted items and keeping the top-K list.

```python
import numpy as np

item_popularity = np.asarray(user_items.sum(axis=0)).ravel()
popular_items = np.argsort(item_popularity)[::-1]

class PopularityRecommender:
    def __init__(self, ranked_items):
        # implicit's Cython evaluation helpers (ndcg_at_k, precision_at_k) expect
        # int32 item IDs. np.argsort returns int64 on 64-bit NumPy, so cast here
        # to avoid a "Buffer dtype mismatch, expected 'int' but got 'long'" crash.
        self.ranked_items = np.asarray(ranked_items, dtype=np.int32)

    def recommend(
        self,
        userid,
        user_items,
        N=10,
        filter_already_liked_items=True,
        items=None,
        recalculate_user=False,
    ):
        user_ids = np.atleast_1d(userid)
        rows = user_items if len(user_ids) > 1 else [user_items]
        all_recs = []
        all_scores = []
        for row in rows:
            seen = set(row.indices) if filter_already_liked_items else set()
            recs = [item for item in self.ranked_items if item not in seen][:N]
            scores = np.linspace(1.0, 0.1, num=len(recs), dtype=np.float32)
            all_recs.append(np.asarray(recs))
            all_scores.append(scores)
        if np.isscalar(userid):
            return all_recs[0], all_scores[0]
        return np.vstack(all_recs), np.vstack(all_scores)

popularity_model = PopularityRecommender(popular_items)
```

- [ ] Create a time-stratified split with leave-future-out per user when timestamps exist, or use `implicit.evaluation.train_test_split` as a clearly labeled fallback for a synthetic matrix.

```python
from implicit.evaluation import train_test_split

train_user_items, test_user_items = train_test_split(
    user_items,
    train_percentage=0.8,
    random_state=21,
)
```

- [ ] Fit `AlternatingLeastSquares` from `implicit` on the training matrix.

```python
from implicit.als import AlternatingLeastSquares

als_model = AlternatingLeastSquares(
    factors=32,
    regularization=0.05,
    iterations=20,
    random_state=21,
)
als_model.fit(train_user_items)
```

- [ ] Evaluate NDCG@10 and precision@10 for both ALS and the popularity baseline with `implicit.evaluation.ndcg_at_k` and related helpers.

```python
from implicit.evaluation import ndcg_at_k, precision_at_k

als_ndcg = ndcg_at_k(als_model, train_user_items, test_user_items, K=10)
pop_ndcg = ndcg_at_k(popularity_model, train_user_items, test_user_items, K=10)

als_precision = precision_at_k(als_model, train_user_items, test_user_items, K=10)
pop_precision = precision_at_k(popularity_model, train_user_items, test_user_items, K=10)

print(f"ALS NDCG@10: {als_ndcg:.3f}")
print(f"Popularity NDCG@10: {pop_ndcg:.3f}")
print(f"ALS precision@10: {als_precision:.3f}")
print(f"Popularity precision@10: {pop_precision:.3f}")
```

- [ ] Add a diversity check, such as counting distinct categories represented in each top-10 slate.

```python
item_categories = np.arange(n_items) % 12

user_id = 0
rec_items, rec_scores = als_model.recommend(
    user_id,
    train_user_items[user_id],
    N=10,
    filter_already_liked_items=True,
)

distinct_categories = len(set(item_categories[rec_items]))
print(f"Distinct categories in top-10: {distinct_categories}")
```

- [ ] Write a short note comparing ALS against popularity and stating whether the result is strong enough to justify an A/B test.

### Completion Check

- [ ] A time-stratified split was used when timestamps existed, or the fallback split was explicitly documented.
- [ ] The popularity baseline was measured before celebrating ALS.
- [ ] ALS beat the popularity baseline on NDCG@10, or the miss was explained honestly.
- [ ] A diversity check was completed for the top-10 list.
- [ ] The conclusion framed offline results as A/B-test qualification, not proof of online impact.

## Sources

- https://benfred.github.io/implicit/
- https://benfred.github.io/implicit/api/models/index.html
- https://benfred.github.io/implicit/api/models/cpu/als.html
- https://benfred.github.io/implicit/api/models/cpu/bpr.html
- https://benfred.github.io/implicit/api/evaluation.html
- https://surpriselib.com/
- https://surprise.readthedocs.io/en/stable/getting_started.html
- https://surprise.readthedocs.io/en/stable/knn_inspired.html
- https://making.lyst.com/lightfm/docs/home.html
- https://making.lyst.com/lightfm/docs/lightfm.html
- https://www.tensorflow.org/recommenders
- https://www.tensorflow.org/recommenders/api_docs/python/tfrs
- https://www.tensorflow.org/recommenders/examples/basic_retrieval
- https://www.tensorflow.org/recommenders/examples/efficient_serving
- https://docs.scipy.org/doc/scipy/reference/sparse.html
- https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.csr_matrix.html
- https://arxiv.org/abs/1606.07792
- https://arxiv.org/abs/1205.2618
- https://recbole.io/docs/index.html

## Next Module

The next module in this Tier-2 sequence is **Module 2.5: Conformal Prediction & Uncertainty Quantification**, covering split conformal prediction,
Mondrian conformal predictors, and the practitioner question of when conformal intervals are the right answer to an uncertainty-quantification ask. It
ships next in Phase 3 of issue #677; the link in this section will go live when that PR lands.
