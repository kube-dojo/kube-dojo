---
title: "What's New"
template: splash
sidebar:
  order: 2
  label: "What's New"
---

## May 1, 2026 — Machine Learning Module 1.9: Anomaly Detection & Novelty Detection

[Module 1.9](/ai-ml-engineering/machine-learning/module-1.9-anomaly-detection-and-novelty-detection/) continues Phase 1b of the ML expansion in [issue #677](https://github.com/kube-dojo/kube-dojo.github.io/issues/677). It teaches anomaly detection as a decision discipline rather than a four-API tour: the foundational anomaly-vs-novelty distinction (training data already contaminated and you flag rows in the same sample, versus clean training and you score new unseen data — different fitting semantics, different deployment patterns, different `.predict()` availability for `LocalOutlierFactor` whose `novelty=True` swap removes `fit_predict` and warns that calling `predict` on training data gives wrong results), `IsolationForest` as the tree-based first-baseline that does not need feature scaling (mirroring the 1.5 trees-don't-need-scaling contrast) with its `n_estimators=100`/`max_samples='auto'` (= `min(256, n_samples)`)/`contamination='auto'`/`max_features=1.0`/`bootstrap=False` defaults and the no-`partial_fit` reality, `LocalOutlierFactor` as the local-density detector that MUST be scaled (mirroring the 1.7 distance-based contrast) with `n_neighbors=20`/`contamination='auto'` (changed in 0.22 from `0.1`), `OneClassSVM` with the dual-meaning `nu` parameter (upper bound on training-error fraction AND lower bound on support-vector fraction — most practitioners only learn the first half) and the kernel-SVM scaling cost from 1.7, `EllipticEnvelope` as the cheap Gaussian-shape baseline with the explicit `n_samples > n_features ** 2` warning, the `contamination` parameter as its own teaching unit (default `0.1` is a 10% claim most practitioners don't realize they're making, `'auto'` is estimator-specific not statistical truth, `score_samples` ranking should be calibrated against partial labels and review capacity rather than blindly inheriting tutorial values), honest evaluation without labels (rank stability, score-distribution shape, agreement across detector families, precision@k with selection-bias caveats), a regime-keyed decision table across the four detectors, the DBSCAN-noise-points bridge from 1.8 as a free anomaly signal, and a "where anomaly detection is the wrong tool" close that points to supervised classification (1.6/1.7), clustering (1.8), time-series (1.12), and drift monitoring (mlops/1.10). Every claim ties to the official scikit-learn user guide.

## May 1, 2026 — Machine Learning Module 1.8: Unsupervised Learning: Clustering

[Module 1.8](/ai-ml-engineering/machine-learning/module-1.8-unsupervised-learning-clustering/) continues Phase 1b of the ML expansion in [issue #677](https://github.com/kube-dojo/kube-dojo.github.io/issues/677). It teaches clustering as a decision-aware tool-choice exercise rather than a five-API tour: the algorithm-to-data-shape match (k-means and k-means++ assume convex isotropic clusters per the user-guide quote on inertia and respond poorly to elongated or curved manifolds, DBSCAN handles arbitrary shape via density and surfaces noise points with label `-1` as the bridge to anomaly detection in 1.9, HDBSCAN handles density variation that breaks DBSCAN, AgglomerativeClustering offers ward/complete/average/single linkage with an explicit single-linkage chaining warning, GaussianMixture provides soft probabilistic membership across full/tied/diag/spherical covariance types with `bic()` and `aic()` for principled component-count selection), the canonical scaling footgun (k-means MUST be scaled with `StandardScaler` mirroring 1.7's k-NN/SVM discipline, cross-linked back to 1.4), MiniBatchKMeans for the large-N regime with the `batch_size=1024` default change in v1.0, the `n_init="auto"` change in v1.4, the honest framing of how to choose `k` (elbow plus silhouette plus Calinski-Harabasz plus Davies-Bouldin plus stability under bootstrap re-fitting plus domain validation, with an explicit "internal metrics tell you the partition is compact at this k, not that it is correct" callout backed by the silhouette-analysis gallery example), the clustering analog of leakage (`fit_predict` plus `silhouette_score` on the full dataset is not out-of-sample, cross-linked to 1.3), a regime-keyed decision table, and a "where clustering is the wrong tool" close that points back to supervised modules 1.2/1.5/1.6 when labels exist and forward to 1.9/1.10 when the question is anomaly detection or dimensionality reduction. Every claim ties to the official scikit-learn user guide.

## May 1, 2026 — Machine Learning Module 1.7: Naive Bayes, k-NN & SVMs

[Module 1.7](/ai-ml-engineering/machine-learning/module-1.7-naive-bayes-knn-and-svms/) continues Phase 1b of the ML expansion in [issue #677](https://github.com/kube-dojo/kube-dojo.github.io/issues/677). It teaches three "small, simple, surprisingly competitive" classical learners as a decision-aware tool-choice exercise: the four Naive Bayes variants (`GaussianNB`, `MultinomialNB`, `BernoulliNB`, `ComplementNB`) with the explicit user-guide warning that NB is "a decent classifier but a bad estimator" and that `predict_proba` is not calibrated, k-Nearest Neighbors with the canonical scaling footgun (distance-based learners DO need `StandardScaler`, mirroring 1.5's "trees do not need scaling" contrast), the kd-tree/ball-tree/brute-force `algorithm="auto"` switch points (D > 15, sparse, k >= N/2), the curse of dimensionality forward link to 1.10, and Support Vector Machines with the inverse-regularization `C` semantics that mirror LogisticRegression in 1.2 (and reverse Ridge/Lasso `alpha`), the O(n_features × n_samples²)–O(n_features × n_samples³) libsvm cost reality, the `probability=True` Platt-scaling cross-validation cost, and `class_weight="balanced"` for imbalanced data. The module ends with a regime-keyed decision table (NB / k-NN / SVC-rbf / LinearSVC) that ties back to the regularized-linear baseline in 1.2 and the gradient-boosted alternative in 1.6, plus a hands-on exercise that builds all three baselines and writes a model-selection memo. Every claim ties to the official scikit-learn user guide.

## May 1, 2026 — Machine Learning Module 1.5: Decision Trees & Random Forests

[Module 1.5](/ai-ml-engineering/machine-learning/module-1.5-decision-trees-and-random-forests/) continues Phase 1b of the ML expansion in [issue #677](https://github.com/kube-dojo/kube-dojo.github.io/issues/677). It teaches when a tree-based model is the right tool over a linear baseline, the anatomy of a single CART tree (gini/entropy/log_loss for classification; squared_error/friedman_mse/absolute_error/poisson for regression), the full regularization knob set (`max_depth`, `min_samples_split`, `min_samples_leaf`, `min_impurity_decrease`, `max_leaf_nodes`, `ccp_alpha`), bagging and Random Forests with the explicit "trees do not need feature scaling" callout that complements module 1.4's preprocessing contract, OOB error with the `oob_score=True` requires `bootstrap=True` footgun, the two-method feature-importance story (impurity-based bias toward high-cardinality features versus permutation importance and its own correlated-features failure mode), an RF tuning playbook for `n_estimators`/`max_depth`/`min_samples_leaf`/`max_features`, and a closing section on where trees are the wrong tool (high-dimensional sparse text, strong global linear structure, problems that need smooth probability outputs). Every claim ties to the official scikit-learn user guide.

## May 1, 2026 — Machine Learning Module 1.2: Linear & Logistic Regression with Regularization

[Module 1.2](/ai-ml-engineering/machine-learning/module-1.2-linear-and-logistic-regression-with-regularization/) continues Phase 1a of the ML expansion in [issue #677](https://github.com/kube-dojo/kube-dojo.github.io/issues/677). It teaches the regularized-linear-model family as a reasoning exercise rather than an API tour: why linear models still earn their place in 2026 (interpretability for audits, calibrated probabilities, sub-millisecond inference, low-data regimes, log-odds outputs for downstream rule engines), the geometry of OLS and where multicollinearity makes it unstable, Ridge as dense L2 shrinkage, Lasso as L1 sparsity with the corner-of-the-ball intuition and its instability on correlated features, ElasticNet as the mixed-penalty stabilizer, and `LogisticRegression` with the `C = 1 / alpha` inverse-regularization-strength trap stated explicitly along with the sklearn 1.8 `penalty` deprecation in favor of `l1_ratio`. The module also covers the scikit-learn GLM family (`PoissonRegressor`, `GammaRegressor`, `TweedieRegressor`) for count and strictly-positive targets where plain least squares uses the wrong link function. Every claim ties to the official scikit-learn user guide.

## May 1, 2026 — Machine Learning Module 1.4: Feature Engineering & Preprocessing

[Module 1.4](/ai-ml-engineering/machine-learning/module-1.4-feature-engineering-and-preprocessing/) closes Phase 1a of the ML expansion in [issue #677](https://github.com/kube-dojo/kube-dojo.github.io/issues/677). It teaches a systematic preprocessing workflow rather than feature creativity: a categorical-encoding decision frame keyed on cardinality (one-hot, ordinal, target encoding with internal cross-fitting, hashing/embeddings for high cardinality), a five-way scaler comparison (`StandardScaler`/`RobustScaler`/`MinMaxScaler`/`PowerTransformer`/`QuantileTransformer`) tied to learner family, an imputation track (`SimpleImputer`/`IterativeImputer`/`KNNImputer` plus `MissingIndicator` when missingness itself is signal), a brief outlier-handling section that cross-links to the future anomaly-detection module 1.9, a feature-selection three-family comparison (filter, wrapper, embedded) with a candid take on when feature selection is worth running, and a `ColumnTransformer` end-to-end synthesis on a mixed-types DataFrame. Every claim ties to the official scikit-learn user guide.

## May 1, 2026 — Machine Learning Module 1.3: Evaluation, Validation, Leakage & Calibration

[Module 1.3](/ai-ml-engineering/machine-learning/module-1.3-model-evaluation-validation-leakage-and-calibration/) is the first Phase 1a module of the ML expansion in [issue #677](https://github.com/kube-dojo/kube-dojo.github.io/issues/677). It teaches an evaluation discipline rather than a metric reference: a three-way train/validation/test split where the test set is touched once, a decision table for cross-validation splitters (KFold vs StratifiedKFold vs GroupKFold vs StratifiedGroupKFold vs TimeSeriesSplit), a taxonomy of leakage failure modes (preprocessing, target, oversampling, group, temporal, threshold, train-as-generalization), classification and regression metric trade-offs, and a calibration workflow with Platt scaling versus isotonic regression via `CalibratedClassifierCV`, reliability diagrams, ECE, and the Brier decomposition. Every claim ties to the official scikit-learn user guide.

## May 1, 2026 — Machine Learning Track Restructured (Phase 0)

The AI/ML Engineering track's `classical-ml/` section has been restructured and renamed to [Machine Learning](/ai-ml-engineering/machine-learning/), and a new peer section [Reinforcement Learning](/ai-ml-engineering/reinforcement-learning/) has been scaffolded. Old URLs redirect to their new homes; nothing existing 404s.

This is Phase 0 of the ML curriculum expansion tracked in [issue #677](https://github.com/kube-dojo/kube-dojo.github.io/issues/677). Phase 1 onward will fill the new section with Tier-1 modules on regression, evaluation, feature engineering, trees, k-NN/SVM, clustering, anomaly detection, dimensionality reduction, and hyperparameter optimization, plus a Tier-1 reinforcement-learning practitioner foundation.

Phase 0 ships:

- The Tier-1 spine (twelve slots in `machine-learning/`, two slots in `reinforcement-learning/`) with the existing XGBoost and Time Series Forecasting modules renumbered to 1.6 and 1.12 to make room.
- A from-scratch rewrite of [Module 1.1 — Scikit-learn API & Pipelines](/ai-ml-engineering/machine-learning/module-1.1-scikit-learn-api-and-pipelines/), refocused away from the broad algorithm survey and onto the workflow contract that makes every later module honest: estimator API, leakage-safe `Pipeline` and `ColumnTransformer`, cross-validation splitter discipline, custom transformers via `BaseEstimator`, and the hyperparameter-search interface.
- Two new quality gates under `scripts/quality/`: a citation HTTP verifier (every URL in a module's Sources section must resolve to a 200 on the same host) and a python-block syntax checker. Every Phase 1+ module passes both before merge.

## April 29, 2026 — AI History Book: Part 1 Released

The first nine chapters of the [AI History book](/ai-history/) are ready to read. Part 1 covers AI's mathematical foundations, 1840s–1950s: Boole, Turing, Shannon, Markov, McCulloch–Pitts, the cybernetics movement, Walter's electronic tortoises, von Neumann's stored program, and magnetic-core memory.

Every chapter opens with a one-paragraph summary, a cast of characters, a timeline, and a glossary; closes with a "Why this still matters today" note; and exposes its named scenes in the right-side navigation. Math-heavy chapters get a foldout sidebar with the equations laid out.

[Start with Chapter 1 →](/ai-history/ch-01-the-laws-of-thought/)

---

## April 26, 2026 — Quality Rewrite + Route Design

### Module quality rewrite underway
Roughly 130 modules have been rewritten to a stricter pedagogical bar, with more in progress. Each module is reviewed against the published quality rubric before going live.

### Hub pages rewritten as route guides
- **Platform Engineering** opens with three persona routes: SRE, DevEx Builder, Platform Architect.
- **Kubernetes Certifications** opens with three personas: Operator, Developer, Security Specialist — replacing the alphabetical default that pointed most learners at the wrong starting point.
- **Bridge pages** added for moving between tracks: K8s ↔ On-Premises, K8s ↔ Platform Engineering, AI/ML ↔ AI Platform Engineering.
- **Section health** is now visible on each section's index — see which sections are actively improving and which are stable.

### AI History Book scoped
The AI History book is scoped at 72 chapters covering the math, hardware, funding, and people behind each era of AI. First drafts are landing chapter by chapter.

---

## April 17, 2026 — New AI Track

A new top-level **AI** track for AI literacy and practical working habits — a beginner-friendly entry point separate from the existing **AI/ML Engineering** advanced builder path.

Initial sections: AI Foundations, AI-Native Work. Modules cover what AI is, what LLMs are, prompting, verification, privacy, and using AI for learning, writing, research, and coding.

---

## April 16, 2026 — ZTT, AI/ML Path, Certification Prep

### Zero to Terminal hardened
Theory and early labs tightened. Ukrainian translation kept in sync.

### AI/ML local-first path
Ten new modules so a learner with one home GPU can build a working RAG system or fine-tune a model without renting a cluster:

- Home AI Workstation Fundamentals
- Reproducible Python, CUDA, and ROCm Environments
- Notebooks, Scripts, and Project Layouts
- Home-Scale RAG Systems
- Notebooks to Production for ML/LLMs
- Small-Team Private AI Platform
- Single-GPU Local Fine-Tuning
- Multi-GPU Home-Lab Fine-Tuning
- Local Inference Stack for Learners
- Home AI Operations and Cost Model

### Certification prep gaps closed
New exam-prep modules for LFCS, CNPE, CNPA, and CGOA.

### Hub pages refreshed
Homepage, Kubernetes certifications, Cloud, Platform Engineering, On-Premises, and AI/ML Engineering hubs rewritten for clearer cross-track navigation.

---

## March 28, 2026 — Theme Overhaul + New Modules

### New design
Custom homepage, K-themed topbar, smart sidebar that follows your current track, breadcrumbs on every module, complexity/time chips, dark/light mode. Mark-Complete button with an exportable progress dashboard.

### Linux Deep Dive promoted to its own track
37 modules, moved out from under Fundamentals into a top-level Linux track.

### Networking discipline — 5 new modules
CNI Architecture & Selection, Network Policy Design, Service Mesh Strategy, Ingress & Gateway API, Multi-Cluster Networking.

### Platform Leadership discipline — 5 new modules
Building Platform Teams, Developer Experience Strategy, Platform as Product, Adoption & Migration, Scaling Platform Organizations.

### Supply Chain Defense Guide — 4 new sections
Transitive dependency auditing, registry quarantine, AI/LLM gateway security, credential rotation verification.

### All 12 certification learning paths in the sidebar
PCA, ICA, CCA, CGOA, CBA, OTCA, KCA, CAPA, CNPE, CNPA, LFCS, FinOps.

---

## March 26, 2026 — Site Migration + On-Premises Kubernetes

### Faster, cleaner site
Site migrated to Starlight (Astro). Build is now seconds for the whole site instead of minutes; broken links cleaned up across the move.

### On-Premises Kubernetes — 30 new modules
Complete bare-metal K8s track:

- **Planning & Economics** (4) — server sizing, NUMA, cluster topology, TCO
- **Bare Metal Provisioning** (4) — PXE, Talos/Flatcar, Sidero/Metal3
- **Networking** (4) — spine-leaf, BGP, MetalLB/kube-vip, DNS/certs
- **Storage** (3) — Ceph/Rook, local storage
- **Multi-Cluster** (3) — private cloud, shared control planes, CAPI
- **Security** (4) — air-gapped, HSM/TPM, AD/LDAP/OIDC, compliance
- **Operations** (5) — upgrades, firmware, auto-remediation, observability
- **Resilience** (3) — multi-site DR, hybrid connectivity, cloud repatriation

---

## March 2026 — Ecosystem Update

- **Zero to Terminal** — 10 modules for absolute beginners
- **Ukrainian translation** — 115 pages (Prerequisites, CKA, CKAD)
- **KCNA update** — AI/ML, WebAssembly, Green Computing modules
- **21 certification tracks** — every CNCF certification covered
- **Kubernetes 1.35** — all content aligned
- **Platform Engineering Toolkit** — 15 new modules (FinOps, Kyverno, Chaos Engineering, Operators, CAPI, vCluster, Rook/Ceph, GPU Scheduling)

---

## December 2025 — Initial Release

KubeDojo launched with 311 modules covering CKA, CKAD, CKS, KCNA, KCSA, Platform Engineering, Linux, and IaC.

---

### By the Numbers

| Metric | Count |
|--------|-------|
| Total modules | 700+ |
| Tracks | 7 (Fundamentals, Linux, Cloud, Certifications, Platform, On-Premises, AI/ML) |
| Certification paths | 18+ |
| Ukrainian translations | 300+ pages |
