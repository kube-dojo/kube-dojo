#!/usr/bin/env bash
#
# On-Premises Phase 2 — write 21 new modules for practitioner-grade expansion (#197)
#
# Modeled on scripts/ai-ml/phase4b-new-modules.sh. Creates stubs, then runs
# the v1 pipeline. Stub scores < 28 trigger REWRITE mode → Gemini writes the
# full module from scratch.
#
# Sequential by design — never parallelize Gemini calls.
# Resumable: completed modules are skipped by the pipeline state machine.
#
# Usage:
#   bash scripts/on-prem/phase2-new-modules.sh            # all 21
#   bash scripts/on-prem/phase2-new-modules.sh 1 2 3      # only the first 3
#
# Prerequisites:
#   - Phase 1 complete: `.venv/bin/python scripts/v1_pipeline.py e2e on-premises`
#     (existing 30 modules re-audited against 8-dimension rubric)
#   - scripts/on-prem/_lib.sh exists (mirror of scripts/ai-ml/_lib.sh)

source "$(dirname "$0")/_lib.sh"

# Module spec arrays — index aligned across all four arrays.
# Ordering follows #197 Phase 2 section order: 1 → 3 → 4 → 5 → 6 → 7 → 9.
SEC=(
  "planning"
  "networking"
  "networking"
  "storage"
  "storage"
  "multi-cluster"
  "multi-cluster"
  "security"
  "security"
  "security"
  "security"
  "operations"
  "operations"
  "operations"
  "operations"
  "ai-ml-infrastructure"
  "ai-ml-infrastructure"
  "ai-ml-infrastructure"
  "ai-ml-infrastructure"
  "ai-ml-infrastructure"
  "ai-ml-infrastructure"
)
NUM=(
  "1.5"
  "3.5"
  "3.6"
  "4.4"
  "4.5"
  "5.4"
  "5.5"
  "6.5"
  "6.6"
  "6.7"
  "6.8"
  "7.6"
  "7.7"
  "7.8"
  "7.9"
  "9.1"
  "9.2"
  "9.3"
  "9.4"
  "9.5"
  "9.6"
)
STEM=(
  "onprem-finops-chargeback"
  "cross-cluster-networking"
  "service-mesh-bare-metal"
  "object-storage-bare-metal"
  "database-operators"
  "fleet-management"
  "active-active-multi-site"
  "workload-identity-spiffe"
  "secrets-management-vault"
  "policy-as-code"
  "zero-trust-architecture"
  "self-hosted-cicd"
  "self-hosted-registry"
  "observability-at-scale"
  "serverless-bare-metal"
  "gpu-nodes-accelerated"
  "private-ai-training"
  "private-llm-serving"
  "private-mlops-platform"
  "private-aiops"
  "high-performance-storage-ai"
)
TITLE=(
  "On-Prem FinOps & Chargeback"
  "Cross-Cluster Networking"
  "Service Mesh on Bare Metal"
  "Object Storage on Bare Metal"
  "Database Operators"
  "Fleet Management"
  "Active-Active Multi-Site"
  "Workload Identity with SPIFFE/SPIRE"
  "Secrets Management on Bare Metal"
  "Policy as Code & Governance"
  "Zero Trust Architecture"
  "Self-Hosted CI/CD"
  "Self-Hosted Container Registry"
  "Observability at Scale"
  "Serverless on Bare Metal"
  "GPU Nodes & Accelerated Computing"
  "Private AI Training Infrastructure"
  "Private LLM Serving"
  "Private MLOps Platform"
  "Private AIOps"
  "High-Performance Storage for AI"
)
TOPIC=(
  "On-Prem FinOps and chargeback models. Kubecost and OpenCost on bare metal, showback/chargeback for internal platform teams, capacity rightsizing lifecycle, depreciation modeling, budget alerting, comparing on-prem TCO to cloud FinOps disciplines."
  "Cross-cluster networking for bare metal K8s. Submariner, Cilium Cluster Mesh, Liqo. East-west traffic across geographically distributed clusters without cloud load balancers. Service discovery, encrypted tunnels, MTU/MSS considerations, dual-stack support."
  "Service mesh on bare metal without cloud load balancers. Istio, Cilium service mesh, Linkerd, Consul. mTLS, traffic shaping, observability integration. Performance considerations vs cloud mesh deployments. Data plane choices: envoy vs eBPF. Kernel tuning for high-throughput mesh traffic."
  "Object storage on bare metal with MinIO. S3-compatible API, distributed deployment modes, tiering policies, erasure coding, encryption at rest, Prometheus metrics. Replication topologies, bucket quotas, multi-tenancy via STS. Lifecycle policies, versioning, legal hold."
  "Database operators on Kubernetes for bare metal. CloudNativePG for PostgreSQL with streaming replication, PITR, pgBouncer. Vitess for MySQL sharding. Self-hosted Redis, Memcached, and Valkey operators. Backup strategies, failover, connection pooling, monitoring."
  "Fleet management for multi-cluster bare metal. Rancher Fleet, Open Cluster Management, ArgoCD ApplicationSets at scale. Cluster registration, placement rules, GitOps rollout strategies, policy distribution, centralized audit logs. Comparing with Karmada and ClusterAPI-based approaches."
  "Active-active multi-site architectures on bare metal. Global load balancing without cloud services, cross-DC data replication, conflict resolution patterns. Eventual consistency vs strong consistency tradeoffs. Split-brain prevention. Database replication (Galera, CockroachDB, YugabyteDB on bare metal)."
  "Workload identity via SPIFFE/SPIRE. Zero-trust workload identity without cloud IAM. X.509 SVIDs, JWT SVIDs, federation across trust domains, workload attestation (k8s, selectors, plugins). Integration with service mesh and secrets managers. Rotation, key management, audit."
  "Secrets management on bare metal K8s. HashiCorp Vault on bare metal (Raft storage, HA), External Secrets Operator, sealed-secrets, Kubernetes Secrets encryption at rest. KMS integration without cloud services. Secret rotation, dynamic secrets for databases, PKI engine usage."
  "Policy as Code and governance on K8s. OPA Gatekeeper and Kyverno for admission control. Runtime policy enforcement with Falco and Tetragon. Policy libraries, violation dashboards, exemption workflows. Comparing OPA vs Kyverno: Rego vs native YAML. Policy CI/CD and testing."
  "Zero Trust Architecture on bare metal K8s. mTLS everywhere via service mesh, network segmentation with NetworkPolicies and Cilium Network Policies, microsegmentation strategies. Identity-based access with SPIFFE, BeyondCorp-style patterns, continuous verification, assume breach posture."
  "Self-hosted CI/CD on K8s. Tekton Pipelines, Gitea with Actions runners, Jenkins on K8s (JCasC, Kubernetes plugin), Woodpecker CI, Drone. Build caching, artifact storage, secret injection, multi-arch builds. Comparing self-hosted options on capability, resource footprint, and operational burden."
  "Self-hosted container registries on bare metal. Harbor (replication, scanning, signing), Quay, Zot, GitLab registry. Distribution architecture, pull-through caches, proxy cache for upstream, vulnerability scanning pipelines (Trivy, Clair). Signing with cosign, policy enforcement, storage backends."
  "Observability at scale on bare metal. Prometheus federation and sharding, Thanos, Cortex, Mimir for long-term storage. OpenTelemetry Collector pipelines. Grafana LGTM stack (Loki, Grafana, Tempo, Mimir). Cardinality management, exemplars, profiling with Pyroscope, alerting fatigue mitigation."
  "Serverless on bare metal K8s. Knative Serving and Eventing for FaaS patterns, KEDA event-driven autoscaling (scale-to-zero), OpenFaaS, Fission. Cold start optimization, autoscaling triggers, comparing serverless runtimes. When to use serverless vs long-running workloads on bare metal."
  "GPU nodes and accelerated computing on K8s. NVIDIA GPU Operator, device plugins, MIG (Multi-Instance GPU), GPU time slicing, node labeling, scheduling strategies. Monitoring GPU utilization (DCGM), driver management, CUDA version compatibility. AMD ROCm and Intel Gaudi alternatives."
  "Private AI training infrastructure. Distributed training on bare metal with PyTorch DDP, FSDP, JAX on K8s. NCCL over InfiniBand/RoCE, RDMA tuning. Job schedulers (Volcano, Kueue, Slurm bridges). Checkpoint storage, fault-tolerant training, topology-aware scheduling for multi-GPU nodes."
  "Private LLM serving on bare metal. vLLM, Text Generation Inference (TGI), Ollama at scale. Model caching, quantization (GPTQ, AWQ), autoscaling inference with KServe/Kubeflow. Token throughput tuning, batch scheduling, continuous batching, multi-model serving, GPU memory optimization."
  "Private MLOps platform on bare metal. Kubeflow, MLflow, model registry, experiment tracking, feature stores (Feast on bare metal). Data versioning (DVC, LakeFS), model deployment pipelines, A/B testing harness, lineage tracking. Self-hosted alternatives to SageMaker and Vertex AI."
  "Private AIOps on bare metal. Anomaly detection for cluster metrics, predictive scaling with ML, self-healing workflows with AI-augmented incident response. Robusta for Prometheus alerts, Kubecost integration, log anomaly detection. Safely letting AI make operational decisions with guardrails."
  "High-performance storage for AI workloads on bare metal. NFS-over-RDMA, parallel file systems (Lustre, BeeGFS, WekaFS), data pipeline optimization. Managing training dataset storage at scale, checkpoint I/O, avoiding GPU idle on data bottlenecks. Storage tiering for hot/warm/cold model data."
)

run_one() {
  local i="$1"
  local sec="${SEC[$i]}" num="${NUM[$i]}" st="${STEM[$i]}"
  local t="${TITLE[$i]}" tp="${TOPIC[$i]}"
  local key="on-premises/${sec}/module-${num}-${st}"

  log "==== Module $((i+1))/21: ${key} ===="
  write_stub "$num" "$sec" "$st" "$t" "$tp"
  run_pipeline "$key"
}

# Pick which to run
if (( $# > 0 )); then
  for n in "$@"; do
    run_one $((n - 1))
  done
else
  for i in "${!STEM[@]}"; do
    run_one "$i"
  done
fi

log "Phase 2 complete. Run 'npm run build' before committing."
