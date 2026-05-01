---
title: "Machine Learning"
description: "Tier-1 + Tier-2 machine learning practitioner curriculum: scikit-learn API, regression, evaluation, feature engineering, trees, boosting, clustering, anomaly detection, dimensionality reduction, hyperparameter optimization, time series, and Tier-2 topics including imbalance, interpretability, recommenders, conformal prediction, fairness, and causal inference."
slug: ai-ml-engineering/machine-learning
sidebar:
  order: 0
  label: "Machine Learning"
---

> **AI/ML Engineering Track**

## Overview

Machine learning is the engineering discipline behind most production ML systems on tabular and structured data. Despite the deep-learning headlines, the majority of business-critical ML in fraud detection, churn, credit scoring, demand forecasting, and recommendation ranking still runs on the algorithms in this section: linear models with regularization, regularized GBMs, random forests, calibrated classifiers, and time-series methods.

This section is organized as a Tier-1 spine of twelve practitioner-essentials, followed by a Tier-2 set of advanced topics that production teams reach for once the basics are stable. Every module is taught at Bloom Level 3+ — design, evaluate, debug — not "remember the API."

## Tier-1 Modules

| # | Module | Status |
|---|---|---|
| 1.1 | [Scikit-learn API & Pipelines](module-1.1-scikit-learn-api-and-pipelines/) | Available |
| 1.2 | [Linear & Logistic Regression with Regularization](module-1.2-linear-and-logistic-regression-with-regularization/) | Available |
| 1.3 | [Model Evaluation, Validation, Leakage & Calibration](module-1.3-model-evaluation-validation-leakage-and-calibration/) | Available |
| 1.4 | [Feature Engineering & Preprocessing](module-1.4-feature-engineering-and-preprocessing/) | Available |
| 1.5 | Decision Trees & Random Forests | Coming soon (Phase 1b) |
| 1.6 | [XGBoost & Gradient Boosting](module-1.6-xgboost-gradient-boosting/) | Available |
| 1.7 | Naive Bayes, k-NN & SVMs | Coming soon (Phase 1b) |
| 1.8 | Unsupervised Learning: Clustering | Coming soon (Phase 1b) |
| 1.9 | Anomaly Detection & Novelty Detection | Coming soon (Phase 1b) |
| 1.10 | Dimensionality Reduction | Coming soon (Phase 1b) |
| 1.11 | Hyperparameter Optimization | Coming soon (Phase 1b) |
| 1.12 | [Time Series Forecasting](module-1.12-time-series-forecasting/) | Available |

## Tier-2 Modules

| # | Module | Status |
|---|---|---|
| 2.1 | Class Imbalance & Cost-Sensitive Learning | Coming soon (Phase 3) |
| 2.2 | ML Interpretability: SHAP, LIME, PDP/ICE + Failure Slicing | Coming soon (Phase 3) |
| 2.3 | Probabilistic & Bayesian ML with PyMC | Coming soon (Phase 3) |
| 2.4 | Recommender Systems | Coming soon (Phase 3) |
| 2.5 | Conformal Prediction & Uncertainty Quantification | Coming soon (Phase 3) |
| 2.6 | Fairness & Bias Auditing | Coming soon (Phase 3) |
| 2.7 | Causal Inference for ML Practitioners | Coming soon (Phase 3) |

## Recommended Order

For first-time practitioners:

1. Start with 1.1 to internalize the sklearn estimator/transformer/pipeline contract.
2. Move to 1.3 (evaluation, validation, leakage, calibration) before any modeling work — most ML failures in production are evaluation failures, not modeling failures.
3. Build feature engineering muscle in 1.4.
4. Then walk through algorithms 1.2, 1.5, 1.6, 1.7 — each adds to your sense of which model to reach for.
5. Branch into 1.8–1.10 for unsupervised work, 1.11 for systematic tuning, 1.12 for time series.

The Tier-2 set is sequence-independent — pick by problem.

## Cross-Links

- For deep learning architectures (CNNs, transformers, training loops): [Deep Learning Foundations](../deep-learning/)
- For RL: [Reinforcement Learning](../reinforcement-learning/)
- For deploying these models on Kubernetes: [MLOps & LLMOps](../mlops/)
- For drift, monitoring, and observability of these models in production: see [MLOps Module 1.10 — ML Monitoring](../mlops/module-1.10-ml-monitoring/)

See the full expansion plan in [issue #677](https://github.com/kube-dojo/kube-dojo.github.io/issues/677).
