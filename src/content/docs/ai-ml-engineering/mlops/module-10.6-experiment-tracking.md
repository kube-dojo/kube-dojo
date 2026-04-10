---
title: "Experiment Tracking"
slug: ai-ml-engineering/mlops/module-10.6-experiment-tracking
sidebar:
  order: 1107
---
> **AI/ML Engineering Track** | Complexity: `[MEDIUM]` | Time: 5-6
> **Migrated from neural-dojo** — pending pipeline polish

## The Model That Vanished: A Cautionary Tale

**San Francisco. March 2021. 9:47 PM.**

Sarah Chen stared at her laptop in disbelief. The production sentiment classifier—the one powering their customer support automation—had been returning random predictions for the past two hours. The model that had achieved 94.2% accuracy in testing was now performing worse than a coin flip.

The investigation took three days. The model in production had been deployed from a Google Drive folder called "final_models_v3_USE_THIS_ONE." There were seventeen similar folders. The model file was called `sentiment_model_FINAL_real_this_one.pkl`. It had been uploaded by someone who had left the company six months ago.

But which training run produced this model? Nobody knew. The training script existed in four different versions across three team members' laptops. The dataset could have been any of twelve different versions—the file was just called `training_data.csv` with no version information. The hyperparameters? Lost in a Jupyter notebook that had been overwritten countless times.

After three days, Sarah's team gave up trying to reproduce the model. They started from scratch, retraining on what they hoped was the right dataset with what they thought were reasonable hyperparameters. They achieved 91.8% accuracy—worse than the original, but at least they could explain where it came from.

**Matei Zaharia**, creator of Apache Spark and later MLflow, saw this pattern repeated across hundreds of companies he consulted for: *"Every ML team hits the same wall. They build amazing models, but they can't reproduce them six months later. They can't explain to their CEO which dataset trained the production model. They can't answer why this week's model is worse than last month's. It's like building software without version control—but somehow, ML teams accepted this chaos as normal."*

In 2018, Zaharia's team at Databricks released MLflow, an open-source platform designed to solve exactly this problem. Within two years, it had become the most popular MLOps tool in the world.

This module teaches you how to prevent Sarah's nightmare. You'll learn MLflow and Weights & Biases—the two dominant experiment tracking platforms—and understand how to build systems where every model's lineage is tracked, every experiment is reproducible, and no model ever mysteriously vanishes.

---

## What You'll Be Able to Do

By the end of this module, you will:
- Master MLflow for experiment tracking, model versioning, and registry
- Learn Weights & Biases (W&B) for real-time experiment visualization and team collaboration
- Implement systematic experiment organization and tagging strategies
- Understand the MLOps maturity model and where your organization stands
- Deploy production-grade tracking infrastructure

---

##  The Experiment Tracking Problem

### Why Experiment Tracking Matters

Machine learning development is fundamentally different from traditional software development. In traditional software, you write code, test it, and deploy it. The code IS the product. In ML, you train models—and the model is the product. The code is just a recipe.

This creates a unique problem. Traditional version control (Git) tracks code changes beautifully. But it's terrible at tracking:
- Which dataset version was used for training
- What hyperparameters produced the best model
- Which preprocessing steps were applied
- The random seed that made results reproducible
- The actual model weights (which can be gigabytes)

Think of it like a kitchen. Git can track your recipe (the code), but it can't track which specific tomatoes you used, what temperature your oven actually was (not what you set it to), or the skill of the chef on that particular day. In ML, all of these "environmental" factors matter—sometimes more than the recipe itself.

Without proper tracking, ML development degrades into chaos. Teams create folder structures that look like archaeological sites: `model_final.pt`, `model_final_v2.pt`, `model_final_ACTUALLY_FINAL.pt`, `model_best_USE_THIS.pt`. When the inevitable question comes—"Can we reproduce the model we shipped six months ago?"—the answer is usually a panicked silence.

**Did You Know?** A landmark 2019 study by **Joelle Pineau** at McGill University (now co-managing director of Meta AI) found that only 15% of ML papers could be reproduced from their published descriptions. The problem wasn't fraud—it was missing details. Hyperparameters weren't reported. Dataset preprocessing wasn't documented. Random seeds weren't recorded. Pineau's team proposed the "ML Reproducibility Checklist," now required by major ML conferences. *"Reproducibility isn't a nice-to-have,"* she wrote. *"It's the foundation of science. If we can't reproduce it, we can't build on it."*

### The Hidden Cost of Poor Tracking

Google's internal research revealed something startling: ML teams spend 40% of their time on what they call "ML debt"—debugging, versioning, and reproducing experiments. That's nearly half of an ML engineer's time spent not on building models, but on archaeology—digging through old experiments to figure out what was done before.

This cost compounds. Every time a team member leaves, institutional knowledge walks out the door. Every time a model needs updating, engineers must reconstruct the original training environment. Every time a stakeholder asks "why is this model behaving this way?", the answer requires hours of forensic investigation.

The solution is experiment tracking: systematically recording everything about every experiment, so any model can be reproduced, explained, and improved upon.

---

## 1. MLflow: The Open-Source Standard

### The Vision Behind MLflow

**Matei Zaharia** didn't set out to build an experiment tracking tool. He was trying to understand why ML teams at Databricks's customers were struggling to get models into production. The pattern was consistent: brilliant data scientists would build amazing models in notebooks, but those models would die in the handoff to production.

*"We realized the problem wasn't deployment,"* Zaharia explained in a 2019 interview. *"The problem was that nobody knew what they were deploying. The data scientist couldn't tell the ML engineer exactly which preprocessing steps were needed. The ML engineer couldn't tell operations which model version was in production. Everyone was guessing."*

MLflow was designed to solve this by treating experiment metadata with the same rigor that databases treat data: structured, queryable, and persistent.

The name "MLflow" comes from the concept of "workflow"—but specifically, the flow of machine learning experiments from conception to production. It's not just about tracking; it's about enabling the entire ML lifecycle.

### MLflow's Four Components

MLflow is actually four tools in one, each solving a different part of the ML lifecycle:

**MLflow Tracking** records experiments: parameters, metrics, artifacts, and source code. Every time you train a model, Tracking creates a "run" that captures everything about that training session. You can think of it as a flight recorder for your ML experiments—it captures everything so you can reconstruct what happened later.

**MLflow Projects** packages code in a reproducible format. Instead of sending a colleague a Python script and hoping it works on their machine, you package the code with its dependencies and entry points. Anyone can run the same experiment by pointing MLflow at the project.

**MLflow Models** provides a standard format for saving models. Different frameworks (PyTorch, TensorFlow, scikit-learn) save models differently. MLflow Models provides a unified format that any deployment tool can understand. It's like PDF for ML models—a universal format that works everywhere.

**MLflow Model Registry** provides versioning and lifecycle management for production models. It's the bridge between experimentation and deployment, letting you stage models, approve them for production, and roll back when things go wrong.

### Basic Experiment Tracking

Let's see MLflow in action. The following example trains a simple classifier and logs everything to MLflow:

```python
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score

# Set the experiment name
# All runs will be grouped under this experiment
mlflow.set_experiment("sentiment-classifier")

# Start a run - this creates a new experiment record
with mlflow.start_run(run_name="random-forest-baseline"):
    # Log parameters - the knobs you can turn
    mlflow.log_param("n_estimators", 100)
    mlflow.log_param("max_depth", 10)
    mlflow.log_param("dataset_version", "v3.2")
    mlflow.log_param("random_seed", 42)

    # Train the model
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42
    )
    model.fit(X_train, y_train)

    # Evaluate and log metrics - the outcomes you measure
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    f1 = f1_score(y_test, predictions, average='weighted')

    mlflow.log_metric("accuracy", accuracy)
    mlflow.log_metric("f1_score", f1)
    mlflow.log_metric("train_samples", len(X_train))
    mlflow.log_metric("test_samples", len(X_test))

    # Log the model itself - so we can reload it later
    mlflow.sklearn.log_model(model, "model")

    # Log any artifacts - plots, data samples, reports
    mlflow.log_artifact("confusion_matrix.png")
    mlflow.log_artifact("feature_importance.json")

    # Get the run ID for reference
    run_id = mlflow.active_run().info.run_id
    print(f"Run ID: {run_id}")
    print(f"Accuracy: {accuracy:.4f}")
```

Every `log_param`, `log_metric`, and `log_artifact` call writes to MLflow's storage. After the experiment finishes, you can browse to the MLflow UI, search for runs with specific parameters, compare metrics across runs, and download the exact model that achieved the best results.

The power becomes apparent when you've run hundreds of experiments. Instead of sifting through folders and notebooks, you query: "Show me all runs with learning_rate < 0.01 and accuracy > 0.9, sorted by F1 score." MLflow returns the exact runs, with everything you need to reproduce them.

### Autologging: Tracking Without Code Changes

Manually logging every parameter is tedious. MLflow's autologging feature automatically captures parameters and metrics for supported frameworks:

```python
import mlflow

# Enable autologging for PyTorch
mlflow.pytorch.autolog()

# Now training automatically logs:
# - Model architecture
# - Optimizer settings (lr, momentum, weight_decay)
# - Loss curves (step by step)
# - Validation metrics
# - Model checkpoints
# - Training time

# Your training code remains unchanged
trainer = Trainer(model, train_loader, val_loader)
trainer.train(epochs=10)
```

Autologging works with all major frameworks: scikit-learn, PyTorch, TensorFlow, XGBoost, LightGBM, Hugging Face Transformers, and FastAI. It's a one-line addition that captures 90% of what you'd want to track.

Think of autologging like a security camera that automatically records. You don't have to remember to press "record"—it's always on, capturing everything important. You only add manual logging for custom metrics or domain-specific parameters that the framework doesn't know about.

**Did You Know?** MLflow was released as open source on the same day it was announced, in June 2018. This was intentional. **Matei Zaharia** had learned from Spark's success that open-source-first builds community trust. Within two years, MLflow had over 10,000 GitHub stars and contributions from Facebook, Microsoft, and hundreds of other organizations. Today, it's governed by the Linux Foundation and used at scale by companies like Uber, Microsoft, and Facebook.

### The Model Registry: From Experiment to Production

Training a good model is only half the battle. Getting that model safely into production—and managing it once it's there—requires a different set of tools. That's what the Model Registry provides.

```python
import mlflow
from mlflow.tracking import MlflowClient

client = MlflowClient()

# After a successful training run, register the model
model_uri = f"runs:/{run_id}/model"
registered_model = mlflow.register_model(
    model_uri,
    "SentimentClassifier"  # The model's name in the registry
)

# Add documentation - your future self will thank you
client.update_model_version(
    name="SentimentClassifier",
    version=registered_model.version,
    description="""
    BERT-based sentiment classifier trained on v3.2 dataset.
    Achieves 94.2% accuracy on test set.
    Uses 6-layer DistilBERT for efficiency.
    Trained by ML Team, reviewed by Alice.
    """
)

# Transition through lifecycle stages
# Stage 1: None → Staging (for testing)
client.transition_model_version_stage(
    name="SentimentClassifier",
    version=registered_model.version,
    stage="Staging"
)

# After testing passes...
# Stage 2: Staging → Production (live serving)
client.transition_model_version_stage(
    name="SentimentClassifier",
    version=registered_model.version,
    stage="Production"
)
```

The Registry provides four stages: None (just registered), Staging (under testing), Production (serving live traffic), and Archived (retired). Models flow through these stages as they're validated and deployed.

This might seem like bureaucracy, but it prevents disasters. When Sarah's team had the model in a "USE_THIS_ONE" folder, there was no process, no audit trail, no way to know what was actually in production. With the Registry, there's exactly one "Production" version of each model, and you can see exactly when it was promoted and by whom.

### Loading Models from the Registry

Once models are in the Registry, loading them is simple:

```python
import mlflow.pyfunc

# Load the current production model
model = mlflow.pyfunc.load_model(
    model_uri="models:/SentimentClassifier/Production"
)

# Or load a specific version for comparison
model_v2 = mlflow.pyfunc.load_model(
    model_uri="models:/SentimentClassifier/2"
)

# Inference works the same regardless of which framework trained it
predictions = model.predict(input_data)
```

The `models:/` URI scheme is powerful. You can reference by stage ("Production", "Staging") or by version number. Your serving infrastructure can always point at "Production," and the Registry handles which specific version that means.

---

## 2. Weights & Biases: Visualization and Collaboration

### A Different Philosophy

Weights & Biases (W&B) takes a different approach than MLflow. While MLflow emphasizes self-hosting and lifecycle management, W&B emphasizes real-time visualization and team collaboration.

**Lukas Biewald**, W&B's founder, came to ML from a different angle. He had previously founded CrowdFlower (now Figure Eight), a data labeling platform. He saw firsthand how data quality affects model quality. When he started W&B in 2017, his vision was a platform where teams could see their experiments in real-time, collaborate on interpreting results, and share insights instantly.

*"The problem with most tracking tools is that they're write-only,"* Biewald explained. *"You log metrics, but then you need custom scripts to actually look at them. We wanted something where you log and immediately see beautiful, interactive charts. The visualization should be instant, not an afterthought."*

The name "Weights & Biases" comes from the fundamental parameters in neural networks—but it's also a nod to the scientific process: we all have biases, and tracking helps us account for them.

**Did You Know?** W&B raised $200 million in Series C funding in 2022 at a $1 billion valuation. Their customer list includes OpenAI (who uses W&B extensively for GPT training), NVIDIA, Toyota Research, and Samsung. The company bet early on building the best visualization and collaboration features, and it paid off: many researchers use W&B specifically for its interactive charts and easy sharing.

### Basic W&B Logging

W&B's API is deliberately simple. You initialize a run, log what you want, and W&B handles the rest:

```python
import wandb
import torch
import torch.nn as nn

# Initialize a run - this creates a new experiment record
wandb.init(
    project="sentiment-classifier",
    config={
        "learning_rate": 0.001,
        "epochs": 10,
        "batch_size": 32,
        "architecture": "BERT-base",
        "dataset": "sentiment-v3.2",
        "optimizer": "AdamW"
    },
    notes="Testing BERT-base with lower learning rate",
    tags=["bert", "experiment", "v3.2-dataset"]
)

# Training loop with real-time logging
for epoch in range(wandb.config.epochs):
    for batch_idx, (data, target) in enumerate(train_loader):
        # Forward pass
        output = model(data)
        loss = criterion(output, target)

        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        # Log metrics - they appear in the dashboard in real-time
        wandb.log({
            "train_loss": loss.item(),
            "epoch": epoch,
            "batch": batch_idx,
            "learning_rate": get_lr(optimizer)
        })

    # Validation at end of each epoch
    val_loss, val_acc = evaluate(model, val_loader)
    wandb.log({
        "val_loss": val_loss,
        "val_accuracy": val_acc,
        "epoch": epoch
    })

# Save the trained model as an artifact
artifact = wandb.Artifact("sentiment-model", type="model")
artifact.add_file("model.pt")
wandb.log_artifact(artifact)

wandb.finish()
```

The moment you call `wandb.log()`, the metric appears in the W&B dashboard. If you're training on a remote server, you can watch the training curves update in real-time from your laptop. Multiple team members can watch the same run, discuss it in the built-in commenting system, and compare it to previous runs.

### W&B Sweeps: Hyperparameter Optimization

One of W&B's most popular features is Sweeps—built-in hyperparameter optimization. Instead of manually trying different configurations, you define a search space and let W&B explore it:

```python
import wandb

# Define the search space
sweep_config = {
    "method": "bayes",  # Options: bayes, random, grid
    "metric": {
        "name": "val_accuracy",
        "goal": "maximize"
    },
    "parameters": {
        "learning_rate": {
            "min": 0.0001,
            "max": 0.1,
            "distribution": "log_uniform_values"
        },
        "batch_size": {
            "values": [16, 32, 64, 128]
        },
        "hidden_size": {
            "min": 64,
            "max": 512,
            "distribution": "int_uniform"
        },
        "dropout": {
            "min": 0.1,
            "max": 0.5
        }
    },
    "early_terminate": {
        "type": "hyperband",
        "min_iter": 3
    }
}

# Create the sweep
sweep_id = wandb.sweep(sweep_config, project="sentiment-classifier")

# Define the training function
def train():
    wandb.init()

    # Config comes from the sweep
    model = build_model(
        hidden_size=wandb.config.hidden_size,
        dropout=wandb.config.dropout
    )

    for epoch in range(10):
        train_epoch(model, wandb.config.learning_rate, wandb.config.batch_size)
        val_acc = evaluate(model)
        wandb.log({"val_accuracy": val_acc, "epoch": epoch})

# Launch sweep agents - these run the experiments
# count=50 means try 50 different configurations
wandb.agent(sweep_id, train, count=50)
```

The Bayesian optimization in Sweeps is particularly smart. It builds a model of the objective function based on completed runs and uses it to pick the next hyperparameters to try. Instead of randomly sampling (which wastes time on obviously bad configurations), it focuses on promising regions of the search space.

The early termination feature (using Hyperband) makes sweeps even more efficient. If a configuration is performing terribly after 3 epochs, why run it for 100? Hyperband automatically kills unpromising runs and redirects resources to better ones.

### W&B Tables: Data and Prediction Visualization

W&B Tables let you log and visualize structured data—predictions, datasets, and anything else that fits in a table:

```python
import wandb

# Create a table for model predictions
table = wandb.Table(columns=["text", "true_label", "predicted", "confidence"])

for text, true, pred, conf in predictions:
    table.add_data(text, true, pred, conf)

# Log the table - it becomes interactive in the dashboard
wandb.log({"predictions": table})

# Log confusion matrix with a single line
wandb.log({
    "confusion_matrix": wandb.plot.confusion_matrix(
        y_true=y_true,
        preds=y_pred,
        class_names=["negative", "positive"]
    )
})

# Log precision-recall curve
wandb.log({
    "pr_curve": wandb.plot.pr_curve(
        y_true=y_true,
        y_probas=y_probas,
        labels=["negative", "positive"]
    )
})
```

Tables in the W&B dashboard are interactive. You can sort by confidence to find high-confidence errors, filter by label to analyze specific classes, and even build custom queries. For debugging model behavior, this is invaluable—you can see exactly which examples the model gets wrong and why.

---

## 3. MLflow vs W&B: Choosing Your Platform

### The Trade-offs

Both MLflow and W&B are excellent tools, but they emphasize different things:

**MLflow** is open-source, self-hostable, and emphasizes the full ML lifecycle. It's the right choice when:
- You need to self-host for security or compliance reasons
- Model serving and deployment are important
- You want full control over your infrastructure
- Cost is a constraint (MLflow is free forever)

**W&B** is SaaS-first with superior visualization and collaboration. It's the right choice when:
- You want best-in-class experiment visualization
- Team collaboration is a priority
- You need built-in hyperparameter sweeps
- You prefer a managed service over self-hosting

Many teams use both: W&B for experiment visualization during research, MLflow for model registry and deployment in production. The tools aren't mutually exclusive—they solve overlapping but different problems.

Think of it like the difference between GitHub (collaboration, visualization) and your CI/CD system (deployment, operations). GitHub is great for code review and collaboration; CI/CD is great for automated deployment. Similarly, W&B excels at experiment collaboration, while MLflow excels at model lifecycle management.

**Did You Know?** The MLflow vs W&B debate is reminiscent of the MySQL vs PostgreSQL debates of the 2000s. Both are good, both have passionate advocates, and the "right" choice depends on your specific needs. What matters most is that you use SOMETHING—the worst experiment tracking platform is the one you don't use at all.

---

## 4. Experiment Organization Best Practices

### Naming Conventions That Scale

As your experiments grow from tens to thousands, organization becomes critical. Here's a structure that scales:

```
Project: sentiment-classifier
├── Experiment: baseline-models
│   ├── Run: logistic-regression-v1
│   ├── Run: random-forest-v1
│   └── Run: naive-bayes-v1
│
├── Experiment: transformer-experiments
│   ├── Run: bert-base-lr001
│   ├── Run: bert-base-lr0001
│   ├── Run: bert-large-frozen
│   └── Run: distilbert-finetuned
│
├── Experiment: hyperparameter-sweep-2024-01
│   ├── Run: sweep-001 through sweep-100
│   └── (100 runs with different configs)
│
└── Experiment: production-candidates
    ├── Run: candidate-v1.0-validated
    ├── Run: candidate-v1.1-validated
    └── Run: candidate-v1.2-A/B-testing
```

The key is consistency. Every team member should use the same naming conventions, the same experiment groupings, and the same tagging strategy.

### Strategic Tagging

Tags are the secret weapon of experiment organization. A good tagging strategy makes it easy to find any experiment months later:

```python
mlflow.set_tags({
    # Experiment classification
    "experiment_type": "hyperparameter_search",
    "team": "nlp",
    "owner": "alice@company.com",

    # Data provenance
    "dataset_version": "v3.2",
    "dataset_source": "production_logs",
    "data_split": "stratified_5_fold",
    "train_samples": "50000",
    "test_samples": "10000",

    # Model architecture
    "model_family": "transformer",
    "model_base": "bert-base-uncased",
    "model_size_mb": "400",
    "trainable_params": "110M",

    # Training environment
    "gpu": "A100-40GB",
    "framework": "pytorch-2.0",
    "cuda_version": "11.8",

    # Business context
    "project": "customer-sentiment",
    "use_case": "support-automation",
    "priority": "high",

    # Status
    "validated": "true",
    "production_candidate": "true"
})
```

With this tagging, you can query: "Show me all production candidates from the NLP team that were trained on dataset v3.2 using A100 GPUs." The answer comes back instantly.

### Metric Logging Strategy

Not all metrics are equal. Some should be logged at every step; others only once. Here's a framework:

```python
# Step-level metrics: logged frequently during training
for step, batch in enumerate(train_loader):
    loss = train_step(batch)

    # Log every N steps to avoid overwhelming storage
    if step % 10 == 0:
        mlflow.log_metric("train_loss", loss, step=step)
        mlflow.log_metric("learning_rate", get_lr(optimizer), step=step)

# Epoch-level metrics: logged once per epoch
for epoch in range(num_epochs):
    train_metrics = train_epoch()
    val_metrics = evaluate()

    mlflow.log_metrics({
        "epoch_train_loss": train_metrics["loss"],
        "epoch_train_accuracy": train_metrics["accuracy"],
        "epoch_val_loss": val_metrics["loss"],
        "epoch_val_accuracy": val_metrics["accuracy"],
    }, step=epoch)

# Final metrics: logged once at the end
mlflow.log_metrics({
    "best_val_accuracy": best_accuracy,
    "final_test_accuracy": test_accuracy,
    "total_training_time_hours": training_time / 3600,
    "final_model_size_mb": get_model_size(model),
    "total_epochs_trained": actual_epochs,
    "early_stopped": was_early_stopped
})
```

The step-level metrics let you diagnose training dynamics. The epoch-level metrics are for comparing runs. The final metrics are for quick filtering and model selection.

---

## 5. The MLOps Maturity Model

### Understanding Where You Are

**Google's MLOps team**, led by **Fei-Fei Li** and **Cassie Kozyrkov**, published an influential maturity model in 2021. It describes five levels of ML infrastructure sophistication:

**Level 0: No MLOps** - This is Sarah's team from our opening story. Models live in notebooks. Deployment is manual. There's no version control for models, no experiment tracking, no reproducibility. Surprisingly, a 2021 survey found that 60% of organizations were still at this level.

**Level 1: DevOps but not MLOps** - Teams have version control for code and basic CI/CD. But ML-specific concerns—experiment tracking, model versioning, dataset versioning—are still manual. The model is deployed like any other application, with no ML-specific monitoring.

**Level 2: Automated Training** - This is where MLflow and W&B come in. Experiments are tracked. Models are versioned. There are automated training pipelines. But deployment is still manual—someone has to look at the metrics and decide to deploy.

**Level 3: Automated Deployment** - CI/CD for models. Automated testing for both data and models. A/B testing and canary deployments for safe rollouts. But monitoring is still reactive—you don't know the model is degrading until someone complains.

**Level 4: Full MLOps** - The holy grail. Continuous training triggered by data drift. Automated retraining when performance degrades. Model monitoring with automatic alerts. Feature stores for consistent feature engineering. The system is self-maintaining.

Most organizations should aim for Level 2 as a first milestone. It's achievable with a small team, provides massive benefits, and creates the foundation for higher levels.

**Did You Know?** Google estimated that only 5% of organizations have achieved Level 3 or higher. The journey from Level 0 to Level 4 typically takes 2-4 years for a well-funded team. But even reaching Level 2—automated tracking and reproducibility—transforms ML from an art into an engineering discipline.

---

## 6. Production Experiment Tracking Setup

### MLflow Production Architecture

For production use, MLflow needs proper infrastructure: a database for metadata, object storage for artifacts, and authentication for security.

```yaml
# docker-compose.yml for production MLflow
version: '3.8'

services:
  mlflow:
    image: ghcr.io/mlflow/mlflow:v2.8.0
    ports:
      - "5000:5000"
    environment:
      - MLFLOW_BACKEND_STORE_URI=postgresql://user:pass@postgres:5432/mlflow
      - MLFLOW_ARTIFACT_ROOT=s3://mlflow-artifacts/
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
    command: >
      mlflow server
      --host 0.0.0.0
      --port 5000
      --backend-store-uri postgresql://user:pass@postgres:5432/mlflow
      --default-artifact-root s3://mlflow-artifacts/

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=mlflow
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

The PostgreSQL backend gives you proper ACID guarantees for experiment metadata. S3 (or compatible storage like MinIO) gives you scalable artifact storage. In production, you'd also add authentication (MLflow supports OIDC) and run behind a load balancer.

### Configuring Clients

Once the server is running, configure clients to use it:

```python
import mlflow
import os

# Point to the tracking server
mlflow.set_tracking_uri("http://mlflow-server.internal:5000")

# Or via environment variables
os.environ["MLFLOW_TRACKING_URI"] = "http://mlflow-server.internal:5000"
os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://minio:9000"  # If using MinIO

# Now all logging goes to the server, not local files
with mlflow.start_run():
    mlflow.log_param("model", "bert-base")
    mlflow.log_metric("accuracy", 0.95)
    mlflow.sklearn.log_model(model, "model")
```

Every team member, every training server, and every notebook can point to the same tracking server. Experiments from all sources appear in the same UI, making collaboration seamless.

---

##  Hands-On Exercises

### Exercise 1: Set Up Local MLflow Tracking

Start with local tracking to understand the concepts:

```bash
# Install MLflow
pip install mlflow

# Start local tracking server
mlflow server --host 0.0.0.0 --port 5000

# In another terminal, run an experiment
python -c "
import mlflow
mlflow.set_tracking_uri('http://localhost:5000')
mlflow.set_experiment('my-first-experiment')
with mlflow.start_run():
    mlflow.log_param('learning_rate', 0.001)
    mlflow.log_metric('accuracy', 0.95)
    print('Run logged successfully!')
"
```

Then browse to http://localhost:5000 to see your experiment.

### Exercise 2: Create a W&B Experiment

Set up W&B and log a training run:

```bash
# Install and login
pip install wandb
wandb login  # Follow the prompts to get your API key

# Run a simple experiment
python -c "
import wandb
import random

wandb.init(project='my-first-project')
for step in range(100):
    wandb.log({'loss': random.random(), 'step': step})
wandb.finish()
"
```

The URL printed at the end takes you to your interactive dashboard.

### Exercise 3: Implement a Full Model Registry Workflow

Practice the complete lifecycle:

```python
import mlflow
from mlflow.tracking import MlflowClient

# Train and log a model (assuming you have X_train, y_train, etc.)
from sklearn.ensemble import RandomForestClassifier

mlflow.set_experiment("model-registry-demo")

with mlflow.start_run() as run:
    model = RandomForestClassifier(n_estimators=100)
    model.fit(X_train, y_train)
    accuracy = model.score(X_test, y_test)

    mlflow.log_param("n_estimators", 100)
    mlflow.log_metric("accuracy", accuracy)
    mlflow.sklearn.log_model(model, "model")

    run_id = run.info.run_id

# Register the model
model_uri = f"runs:/{run_id}/model"
mlflow.register_model(model_uri, "DemoClassifier")

# Transition through stages
client = MlflowClient()
client.transition_model_version_stage("DemoClassifier", 1, "Staging")
# After testing...
client.transition_model_version_stage("DemoClassifier", 1, "Production")

# Load the production model
production_model = mlflow.pyfunc.load_model("models:/DemoClassifier/Production")
```

---

##  Further Reading

### Documentation
- [MLflow Documentation](https://mlflow.org/docs/latest/) - Comprehensive API reference
- [Weights & Biases Docs](https://docs.wandb.ai/) - Guides and tutorials
- [MLflow Model Registry Guide](https://mlflow.org/docs/latest/model-registry.html) - Deep dive on versioning

### Research Papers
- "Hidden Technical Debt in Machine Learning Systems" (Google, 2015) - **D. Sculley** et al.
- "MLOps: Continuous Delivery and Automation Pipelines in Machine Learning" (Google, 2021)
- "Challenges in Deploying Machine Learning" (Paleyes et al., 2022)
- "A Reproducibility Checklist for ML Research" (Pineau et al., 2021)

---

##  Key Takeaways

1. **Experiment tracking is not optional** - Without it, ML development degrades into chaos. Every serious ML team uses some form of tracking. The question is whether you use a proper system or a folder called "final_models_USE_THIS_v3."

2. **MLflow is the open-source standard** - Four components (Tracking, Projects, Models, Registry) covering the full ML lifecycle. Self-hostable and free. Used by Microsoft, Facebook, and thousands of companies.

3. **W&B excels at visualization and collaboration** - Real-time dashboards, interactive tables, built-in hyperparameter sweeps. The best experience for teams who want to see their experiments instantly.

4. **The Model Registry bridges experimentation and production** - Staging, Production, Archived—clear lifecycle stages with audit trails. No more "which model.pkl is actually in production?"

5. **Organization scales with discipline** - Consistent naming, strategic tagging, and thoughtful metric logging make the difference between 50 experiments and 5000.

6. **Start at Level 2** - Most organizations are at Level 0 (no MLOps). Getting to Level 2 (automated tracking and reproducibility) is achievable and transformative. Then build toward Level 3 and 4.

---

##  Did You Know?

**The Hidden Tax of Poor Reproducibility**: A 2020 study by **Pete Warden** (former Google TensorFlow team) estimated that poor reproducibility costs the average ML team 20% of their engineering time. Over a year, for a 10-person team, that's equivalent to losing 2 full-time engineers to "archaeology"—digging through old experiments trying to figure out what was done.

**The Experiment Explosion**: Modern ML research generates experiments at an unprecedented rate. DeepMind's AlphaFold project ran over 100,000 experiments. OpenAI's GPT-3 involved thousands of ablation studies. Without tracking, this scale of experimentation would be impossible to manage.

**Why "Weights & Biases"?**: Beyond the neural network terminology, the name reflects a philosophy. "Biases" in ML have a specific meaning (the b in y = Wx + b), but they also refer to cognitive biases in researchers. The platform helps you see your data objectively, revealing biases you might not notice otherwise.

---

## ⏭️ Next Steps

You now understand experiment tracking and model registry—the foundation of reproducible ML!

**Up Next**: Module 49 - Data Versioning & Feature Stores (DVC, Feast)

---

*Module 48 Complete! You now understand MLflow and Weights & Biases—the tools that transform ML from art to engineering.*

*Remember Sarah's vanishing model: without tracking, you're just one departure away from losing everything you've built. With tracking, every model tells its own story.*

*"What gets measured gets managed. What gets tracked gets reproduced. What gets reproduced gets improved."* — The MLOps Manifesto
