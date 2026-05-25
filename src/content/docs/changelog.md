---
title: "What's New"
template: splash
sidebar:
  order: 2
  label: "What's New"
---

## May 2026

- **AI Engineering Foundations prompt-safety module.** [Prompt Safety and Evaluation](/ai/ai-engineering-foundations/module-1.3-prompt-safety-and-evaluation/) adds a prompt-eval harness lesson covering golden-set regression, LLM-as-judge calibration, direct and indirect prompt injection, prompt leakage, jailbreak probes, drift detection, and CI-ready safety gates.

- **Kafka on Kubernetes: MirrorMaker2, partition reassignment, and Cruise Control.** [Module 1.2: Apache Kafka on Kubernetes (Strimzi)](/platform/disciplines/data-ai/data-engineering/module-1.2-kafka/) expanded with three new operator-grade sections covering `KafkaMirrorMaker2` CRD configuration for DR and multi-region topologies (offset translation, heartbeat/checkpoint connectors, active-active vs active-passive patterns), `kafka-reassign-partitions.sh` three-phase workflow (generate/execute/verify with bandwidth throttling), and Cruise Control continuous rebalancing via the `KafkaRebalance` CRD (state machine, goal tiers, self-healing anomaly detection, production tuning). Issue #1324.

- **Operator implementation decision framework.** [Module 7.15: Helm vs Ansible vs Go Operator Decision Framework](/platform/toolkits/infrastructure-networking/iac-tools/module-7.15-helm-ansible-go-operator-decision/) gives platform engineers a 12-axis decision matrix for choosing between Helm, Ansible, and Go operator styles. Covers OperatorHub.io capability levels, three worked examples (AWX Operator + cert-manager + Crossplane), code volume estimates, migration paths, and a hands-on lab that builds all three operator flavors against the same `WebApp` CRD on kind.

- **Platform Toolkits / IaC Tools**: Module 7.13 Advanced watches.yaml Patterns — multi-CRD operators, WATCH_NAMESPACE scoping, cluster-scoped RBAC, watchDependentResources + blacklist filtering, finalizer mapping, selector filters, and performance tuning via ANSIBLE_WORKERS (#1356, T2-13 Wave 2).

- **Platform Toolkits / IaC Tools**: Module 7.17 Testing Ansible Operators with Molecule and Kuttl (#1360, T2-13 arc complete) — Molecule delegated + docker + kind driver scenarios, Kuttl TestStep/TestAssert/errors.yaml E2E tests, operator-sdk scorecard, GitHub Actions matrix pipeline, coverage measurement, 8-row common mistakes table, 6 scenario-based quiz questions, hands-on lab with 4 tasks (~700 content lines).

- **Platform Toolkits / IaC Tools**: Module 7.14 AWX, Tower, and Event-Driven Ansible (EDA) Integration (#1357 — AWX Operator architecture, AAP vs AWX vs standalone decision matrix, EDA rulebooks on Kubernetes via ansible.eda.webhook + informer-forwarder pattern, webhook integration with Alertmanager and GitHub Actions, credential management, k8s_info + add_host inventory pattern, operator-as-AWX-job pattern, production deployment and backup strategy, ~450 lines of prose content).

- **AI Infrastructure inference benchmarking.** [Benchmarking LLM Inference: TTFT, TPOT, and Workload-Aware Load Shaping](/ai-ml-engineering/ai-infrastructure/module-1.8-inference-benchmarking/) teaches TTFT, TPOT, percentile latency, structured vLLM benchmark runs, workload-aware load shaping, serving-parameter tuning, and bandwidth-math validation for production inference stacks.

- **Production LLM inference engine selection.** [Production-Tier LLM Inference Engines: Decision Framework](/ai-ml-engineering/ai-infrastructure/module-1.7-production-inference-engines/) maps ExLlamaV2/V3, vLLM, SGLang, TensorRT-LLM, NVIDIA Dynamo, TGI, LMDeploy, MLC LLM, and OpenVINO to hardware tiers, workload classes, migration paths, and production failure modes.

- **AI Infrastructure bandwidth math.** [GPU Memory Hierarchy and Bandwidth Math for LLM Inference](/ai-ml-engineering/ai-infrastructure/module-1.6-memory-bandwidth-math/) teaches HBM/GDDR/DRAM/NVLink/PCIe tradeoffs, arithmetic intensity, decode tokens-per-second prediction, and benchmark validation before engine or GPU selection.

- **2026-05-19** feat(content): module 3.1 LLM-Native Stack on Kubernetes — first module of synthesis-apps mini-arc (T2-7).

- **Platform Toolkits / IaC Tools**: Module 7.11 HCP Terraform Workflow Operations (#1304 Wave 2, T2-23, ~2091 lines).

- **Platform Toolkits / GitOps & Deployments**: Module 2.5 Dapr + Buildpacks application definition beyond Helm (#1304 Wave 2, T2-20, ~2189 lines).

- **MLOps**: Module 5.12 CML for ML CI — closes MLOps Discipline track (#1304 Wave 2, T2-19, ~2069 lines).

- **MLOps**: Module 5.11 Drift-Triggered Auto-Retraining Loop (#1304 Wave 2, T2-18, ~2001 lines).

- **MLOps model-serving traffic gap filled.** [Production Model-Serving Traffic Patterns](/platform/disciplines/data-ai/mlops/module-5.10-model-serving-traffic-patterns/) now covers KServe canaries, Istio A/B routing, shadow traffic, mirroring, bandits, rollback gates, and cost controls for production model promotion.

- **MLOps repository-hygiene gap filled.** [ML Repository Hygiene](/platform/disciplines/data-ai/mlops/module-5.9-ml-repository-hygiene/) now covers clean `src/` layouts, DVC-aware ignore policy, uv lock discipline, notebook output stripping, pre-commit gates, CI split, and cost controls for ML repository bloat.

- **MLOps data-quality gap filled.** [Great Expectations Data Quality](/platform/disciplines/data-ai/mlops/module-5.8-great-expectations-data-quality/) now covers GX Core 1.x suites, checkpoints, Data Docs, DVC baseline review, cost controls, and Kubernetes/Argo validation gates.

- **MLOps data-versioning gap filled.** [Data Versioning with DVC](/platform/disciplines/data-ai/mlops/module-5.7-dvc-data-versioning/) now covers Git-plus-DVC artifact lineage, DVC pipelines, MinIO remotes on kind, cost controls, and CI/Kubeflow integration boundaries.

- **Azure Essentials application-hosting gap filled.** [Azure App Service — Operator Path](/cloud/azure-essentials/module-3.14-app-service/) now covers App Service Plans and SKUs, deployment slots with slot-swap rollback, Hybrid Connections versus VNet integration versus Private Endpoint, managed identity, autoscale, App Service Environment v3, and the App Service versus Container Apps versus AKS decision.

- **Azure Essentials edge-operations gap filled.** [Azure Application Gateway — Operator Path](/cloud/azure-essentials/module-3.13-application-gateway/) now covers WAF policy tuning, Key Vault-backed TLS, AGIC versus Application Gateway for Containers, autoscaling capacity units, Log Analytics/KQL diagnostics, and v1-to-v2 migration gotchas.

- **Cloud governance gap filled.** [Cloud Custodian -- Policy-as-Code Governance Across Multi-Cloud](/cloud/enterprise-hybrid/module-10.11-cloud-custodian/) now covers declarative multi-cloud remediation, AWS/Azure examples, and production operations.

- **Agent runtime expanded.** DeepSeek V4 Pro and Flash are now integrated as
  production peer agents via ``hermes --provider deepseek`` with a dedicated adapter,
  registry entry, and bridge-mode tool/mode wiring. Pro defaults to
  ``deepseek-v4-pro`` and Flash can be selected through ``AB_DEEPSEEK_MODEL``,
  including dispatch coverage for review, research, and code lanes.

- **On-prem multi-cluster track complete.** Four new modules in [On-Premises Multi-Cluster](/on-premises/multi-cluster/): [Gardener](/on-premises/multi-cluster/module-5.6-gardener/) (open-source Kubernetes-as-a-Service with a three-tier Gardens/Seeds/Shoots architecture), [Karmada + Liqo + kube-vip](/on-premises/multi-cluster/module-5.7-multi-cluster-on-prem/) (federation and virtual-IP advertisement for on-prem clusters), [OpenStack on Kubernetes](/on-premises/multi-cluster/module-5.8-openstack-on-kubernetes/) (running OpenStack's own control plane as Kubernetes workloads), and [VMware Tanzu](/on-premises/multi-cluster/module-5.9-vmware-tanzu/) (the full Tanzu portfolio — TKG, vSphere with Tanzu, TMC, TAP — plus an honest look at enterprise decisions after the Broadcom acquisition).

- **ML model-serving toolkit.** [KServe](/platform/toolkits/data-ai-platforms/ml-platforms/module-9.8-kserve/), [Seldon Core](/platform/toolkits/data-ai-platforms/ml-platforms/module-9.9-seldon-core/), and [BentoML](/platform/toolkits/data-ai-platforms/ml-platforms/module-9.10-bentoml/) now have full modules — covering inference graphs, A/B experiments, and Python-first model packaging. The new [bare-metal MLOps capstone](/platform/toolkits/data-ai-platforms/ml-platforms/module-9.11-bare-metal-mlops/) shows how to wire all three into a complete production stack on your own hardware, from GPU scheduling and storage through to observability.

- **Machine Learning track — Tier-1 layer complete (twelve modules).** The [Machine Learning](/ai-ml-engineering/machine-learning/) section now has a complete twelve-module Tier-1 layer (ten new modules plus two existing modules renumbered into slots 1.6 and 1.12): [scikit-learn API and Pipelines](/ai-ml-engineering/machine-learning/module-1.1-scikit-learn-api-and-pipelines/), [regression with regularization](/ai-ml-engineering/machine-learning/module-1.2-linear-and-logistic-regression-with-regularization/), [evaluation, leakage, and calibration](/ai-ml-engineering/machine-learning/module-1.3-model-evaluation-validation-leakage-and-calibration/), [feature engineering](/ai-ml-engineering/machine-learning/module-1.4-feature-engineering-and-preprocessing/), [decision trees and random forests](/ai-ml-engineering/machine-learning/module-1.5-decision-trees-and-random-forests/), [k-NN, Naive Bayes, and SVMs](/ai-ml-engineering/machine-learning/module-1.7-naive-bayes-knn-and-svms/), [clustering](/ai-ml-engineering/machine-learning/module-1.8-unsupervised-learning-clustering/), [anomaly detection](/ai-ml-engineering/machine-learning/module-1.9-anomaly-detection-and-novelty-detection/), [dimensionality reduction](/ai-ml-engineering/machine-learning/module-1.10-dimensionality-reduction/), and [hyperparameter optimization](/ai-ml-engineering/machine-learning/module-1.11-hyperparameter-optimization/).

- **Machine Learning track — seven advanced modules.** The Tier-2 layer tackles the harder questions you hit in production: [class imbalance and cost-sensitive learning](/ai-ml-engineering/machine-learning/module-2.1-class-imbalance-and-cost-sensitive-learning/), [interpretability and failure slicing](/ai-ml-engineering/machine-learning/module-2.2-interpretability-and-failure-slicing/), [Bayesian ML with PyMC](/ai-ml-engineering/machine-learning/module-2.3-probabilistic-and-bayesian-ml-with-pymc/), [recommender systems](/ai-ml-engineering/machine-learning/module-2.4-recommender-systems/), [conformal prediction and uncertainty quantification](/ai-ml-engineering/machine-learning/module-2.5-conformal-prediction-and-uncertainty-quantification/), [fairness and bias auditing](/ai-ml-engineering/machine-learning/module-2.6-fairness-and-bias-auditing/), and [causal inference for ML practitioners](/ai-ml-engineering/machine-learning/module-2.7-causal-inference-for-ml-practitioners/).

- **Deep Learning and Reinforcement Learning extensions.** Two new deep learning modules: [self-supervised learning](/ai-ml-engineering/deep-learning/module-1.8-self-supervised-learning/) (SimCLR, DINO, MAE — when to use them versus supervised pretraining) and [graph neural networks](/ai-ml-engineering/deep-learning/module-1.9-graph-neural-networks/) (GCN, GraphSAGE, GAT — with an honest look at when a plain MLP still wins). The new [Reinforcement Learning](/ai-ml-engineering/reinforcement-learning/) section opens with [practitioner foundations](/ai-ml-engineering/reinforcement-learning/module-1.1-rl-practitioner-foundations/) and [offline RL and imitation learning](/ai-ml-engineering/reinforcement-learning/module-2.1-offline-rl-and-imitation-learning/).

## April 2026

- **AI History Book — Part 1.** The first nine chapters of the [AI History book](/ai-history/) are live. Part 1 covers AI's mathematical foundations from the 1840s to the 1950s — Boole, Turing, Shannon, McCulloch–Pitts, and the cybernetics movement. Each chapter includes a cast of characters, timeline, glossary, and a "Why this still matters" note. [Start with Chapter 1.](/ai-history/ch-01-the-laws-of-thought/)

- **New AI track.** A beginner-friendly [AI track](/ai/) covers AI literacy and practical working habits — what LLMs are, prompting, verification, privacy, and using AI for learning, writing, research, and coding. A gentler entry point than the advanced AI/ML Engineering path.

- **Local-first AI/ML path.** Ten new modules so you can build a working RAG system or fine-tune a model on a single home GPU, no cloud account required. Covers environment setup (CUDA/ROCm), home-scale RAG, local inference stacks, single-GPU and multi-GPU fine-tuning, and home AI operations. [See the full path.](/ai-ml-engineering/)

- **Hub pages redesigned.** Platform Engineering and Kubernetes Certifications now open with persona routes — SRE, DevEx Builder, Platform Architect; Operator, Developer, Security Specialist — so you find the right starting point immediately. Bridge pages link K8s to On-Premises, K8s to Platform Engineering, and AI/ML to AI Platform Engineering.

- **Certification prep expanded.** New exam-prep modules for LFCS, CNPE, CNPA, and CGOA added to the Certifications track.

## March 2026

- **Site migrated to Starlight.** The build now takes seconds instead of minutes. Broken links from the old site have been cleaned up.

- **New site design.** Custom homepage, a sidebar that follows your current track, breadcrumbs, complexity and time chips, dark/light mode, and a Mark-Complete button with an exportable progress dashboard.

- **Linux Deep Dive** promoted to its own top-level track — 37 modules, no longer buried under Fundamentals.

- **On-Premises Kubernetes — 30 new modules.** A complete bare-metal track: planning and economics, provisioning (PXE, Talos, Flatcar, Sidero, Metal3), networking (spine-leaf, BGP, MetalLB, kube-vip), storage (Ceph/Rook), multi-cluster, security (air-gapped, HSM/TPM, AD/LDAP/OIDC), operations, and resilience (multi-site DR, hybrid connectivity, cloud repatriation). [Start here.](/on-premises/)

- **New Platform Engineering disciplines.** Five new Networking modules (CNI Architecture, Network Policy, Service Mesh, Ingress and Gateway API, Multi-Cluster Networking), five new Platform Leadership modules (Building Platform Teams, Developer Experience Strategy, Platform as Product, Adoption and Migration, Scaling Platform Organizations), and a four-section Supply Chain Defense guide covering transitive dependency auditing, registry quarantine, AI gateway security, and credential rotation.

- **Ecosystem updates.** Zero to Terminal has 10 beginner modules. Ukrainian translation covers 115+ pages across Prerequisites, CKA, and CKAD. All content aligned with Kubernetes 1.35. Platform Engineering Toolkit expanded with FinOps, Kyverno, Chaos Engineering, Operators, CAPI, vCluster, and GPU Scheduling. All 21 CNCF certification learning paths are in the sidebar.
