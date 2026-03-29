---
title: "Module 10.5: Multi-Cloud Fleet Management (Azure Arc / GKE Fleet)"
slug: cloud/enterprise-hybrid/module-10.5-fleet-management
sidebar:
  order: 6
---
**Complexity**: [COMPLEX] | **Time to Complete**: 2.5h | **Prerequisites**: Hybrid Cloud Architecture (Module 10.4), Kubernetes Multi-Cluster Basics

## Why This Module Matters

In late 2023, a global retail company operated 73 Kubernetes clusters across three cloud providers and two data centers. Each cluster had its own deployment pipeline, its own monitoring stack, its own policy engine, and its own team responsible for upgrades. When a critical CVE in the Kubernetes API server (CVE-2023-5528) was announced, their security team needed to assess and patch every cluster. It took them 11 days to determine which clusters were affected, 6 weeks to patch all of them, and during that window they discovered that 9 clusters were running Kubernetes versions so old they were no longer receiving security patches at all. Nobody had noticed because nobody had a fleet-wide view.

The incident report identified a fundamental organizational failure: they had clusters but not a fleet. Each cluster was a pet, individually configured and managed. The company had no centralized inventory, no way to push configuration changes to all clusters simultaneously, and no unified view of compliance or health. Their CTO described it as "running 73 separate Kubernetes islands with bridges made of Slack messages and wiki pages."

Fleet management tools solve this by treating your entire collection of Kubernetes clusters as a single manageable unit. Azure Arc, Google Fleet (GKE Enterprise), and open-source alternatives like Rancher Fleet provide centralized inventory, policy distribution, configuration management, and observability across clusters regardless of where they run. In this module, you will learn the reality of multi-cloud fleet management, how Azure Arc and Google Fleet work, how to centralize telemetry and policy, and how to implement multi-cloud GitOps at scale.

---

## The Multi-Cloud Reality Check

Before diving into tools, you need an honest assessment of why enterprises end up multi-cloud and what it actually costs.

### Why Enterprises Go Multi-Cloud

Most enterprises do not choose multi-cloud strategically. They end up there through:

1. **Acquisitions**: Company A uses AWS, acquires Company B which uses Azure. Consolidation is estimated at 3 years but never happens.
2. **Best-of-breed selection**: ML team chose GCP for Vertex AI, main platform team chose AWS for EKS, data team chose Azure for Synapse.
3. **Regulatory requirements**: EU data must stay in a specific region that only one provider supports well.
4. **Vendor negotiation leverage**: "We use AWS but we could switch to Azure" is only credible if you actually have Azure workloads.
5. **Shadow IT**: A team started using a second cloud on a corporate credit card. By the time IT found out, there were production workloads running.

### The Real Cost of Multi-Cloud

```text
┌──────────────────────────────────────────────────────────────┐
│  MULTI-CLOUD COST MULTIPLIERS                                 │
│                                                                │
│  Category              Single Cloud    Multi-Cloud (3 CSPs)   │
│  ──────────────        ────────────    ────────────────────   │
│  Platform team size    5-8 engineers   12-20 engineers         │
│  Training budget       $15K/year       $45-60K/year           │
│  Tooling licenses      $50K/year       $100-200K/year         │
│  Data transfer costs   Internal only   $50-200K/year          │
│  Compliance audits     1 scope         3 scopes               │
│  Incident complexity   Low             High (finger-pointing) │
│  Negotiation leverage  Low             Medium                  │
│                                                                │
│  Net effect: 2-3x operational cost for marginal benefit       │
│  Exception: If you genuinely use best-of-breed per provider   │
└──────────────────────────────────────────────────────────────┘
```

This does not mean multi-cloud is wrong. It means you should be deliberate about it and invest in fleet management tooling proportional to your fleet size.

---

## Azure Arc for Kubernetes

Azure Arc extends Azure's management plane to any Kubernetes cluster, regardless of where it runs. You can connect an EKS cluster, a GKE cluster, an on-premises kubeadm cluster, or even a Raspberry Pi cluster to Azure Arc and manage them all through the Azure portal and APIs.

### How Azure Arc Works

```text
┌──────────────────────────────────────────────────────────────┐
│                    AZURE ARC ARCHITECTURE                      │
│                                                                │
│  ┌──────────────────────────────────────────┐                 │
│  │           Azure Control Plane             │                 │
│  │                                            │                 │
│  │  Azure Resource Manager ◄──── Azure Portal│                 │
│  │  Azure Policy Engine                       │                 │
│  │  Azure Monitor                             │                 │
│  │  Microsoft Defender                        │                 │
│  └───────────────┬──────────────────────────┘                 │
│                   │ HTTPS (outbound only)                       │
│                   │                                             │
│  ┌────────────────▼─────────────────────────┐                 │
│  │  Arc Agent (runs IN your cluster)         │                 │
│  │                                            │                 │
│  │  ┌─────────────────┐  ┌────────────────┐ │                 │
│  │  │ cluster-connect  │  │ config-agent   │ │                 │
│  │  │ (reverse proxy)  │  │ (GitOps/Flux)  │ │                 │
│  │  └─────────────────┘  └────────────────┘ │                 │
│  │  ┌─────────────────┐  ┌────────────────┐ │                 │
│  │  │ azure-policy     │  │ monitoring     │ │                 │
│  │  │ (Gatekeeper)     │  │ (omsagent)     │ │                 │
│  │  └─────────────────┘  └────────────────┘ │                 │
│  └──────────────────────────────────────────┘                 │
│                                                                │
│  KEY: All communication is OUTBOUND from your cluster.        │
│  No inbound ports needed. No VPN required.                    │
└──────────────────────────────────────────────────────────────┘
```

### Connecting a Cluster to Azure Arc

```bash
# Prerequisites: Azure CLI with connectedk8s extension
az extension add --name connectedk8s
az extension add --name k8s-configuration

# Connect an EKS cluster to Azure Arc
# First, ensure your kubeconfig points to the target cluster
export KUBECONFIG=~/.kube/eks-production-config

az connectedk8s connect \
  --name eks-prod-us-east-1 \
  --resource-group rg-arc-fleet \
  --location eastus \
  --tags "provider=aws" "environment=production" "team=platform" \
  --distribution eks \
  --infrastructure aws

# Verify the connection
az connectedk8s show \
  --name eks-prod-us-east-1 \
  --resource-group rg-arc-fleet \
  --query '{Name:name, Status:connectivityStatus, Distribution:distribution, Infrastructure:infrastructure}'

# List all Arc-connected clusters
az connectedk8s list \
  --resource-group rg-arc-fleet \
  --query '[].{Name:name, Status:connectivityStatus, Provider:infrastructure, K8sVersion:kubernetesVersion}' \
  --output table
```

### Azure Policy for Arc-Connected Clusters

Once connected, you can push Azure Policies to any cluster in your fleet:

```bash
# Assign a policy to enforce no privileged containers across ALL Arc clusters
az policy assignment create \
  --name deny-privileged-containers \
  --display-name "Deny privileged containers on all Arc clusters" \
  --policy "/providers/Microsoft.Authorization/policyDefinitions/95edb821-ddaf-4404-9732-666045e056b4" \
  --scope "/subscriptions/$SUB_ID/resourceGroups/rg-arc-fleet" \
  --params '{"effect": {"value": "deny"}}'

# This installs OPA Gatekeeper on every Arc-connected cluster
# and deploys the constraint automatically

# Check compliance across the fleet
az policy state list \
  --resource-group rg-arc-fleet \
  --filter "policyDefinitionName eq '95edb821-ddaf-4404-9732-666045e056b4'" \
  --query '[].{Resource:resourceId, Compliance:complianceState}' \
  --output table
```

### GitOps with Arc (Flux)

```bash
# Deploy a GitOps configuration to all Arc clusters with a specific tag
az k8s-configuration flux create \
  --name platform-baseline \
  --cluster-name eks-prod-us-east-1 \
  --resource-group rg-arc-fleet \
  --cluster-type connectedClusters \
  --namespace flux-system \
  --scope cluster \
  --url https://github.com/company/fleet-config.git \
  --branch main \
  --kustomization name=platform path=./platform/base prune=true \
  --kustomization name=monitoring path=./monitoring/overlays/production prune=true \
  --kustomization name=policies path=./policies/production prune=true
```

---

## Google Fleet (GKE Enterprise)

Google's approach to fleet management is built around the concept of a "fleet" -- a logical grouping of GKE and non-GKE clusters that share configuration and policies.

### GKE Fleet Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                 GOOGLE FLEET ARCHITECTURE                      │
│                                                                │
│  ┌──────────────────────────────────────────┐                 │
│  │           GCP Fleet Host Project          │                 │
│  │                                            │                 │
│  │  Fleet API ◄──── GCP Console              │                 │
│  │  Config Sync (GitOps)                      │                 │
│  │  Policy Controller (OPA)                   │                 │
│  │  Service Mesh (Istio/ASM)                  │                 │
│  │  Binary Authorization                      │                 │
│  └───────────────┬──────────────────────────┘                 │
│                   │                                             │
│  ┌────────────────┼─────────────────────────────────┐         │
│  │                │                                   │         │
│  │  ┌─────────────▼──┐  ┌──────────────┐  ┌────────▼────┐   │
│  │  │ GKE Cluster    │  │ EKS Cluster  │  │ On-Prem     │   │
│  │  │ (native fleet  │  │ (attached    │  │ K8s         │   │
│  │  │  member)       │  │  via agent)  │  │ (attached)  │   │
│  │  │                │  │              │  │             │   │
│  │  │ Config Sync    │  │ Config Sync  │  │ Config Sync │   │
│  │  │ Policy Ctrl    │  │ Policy Ctrl  │  │ Policy Ctrl │   │
│  │  └────────────────┘  └──────────────┘  └─────────────┘   │
│  │                                                   │         │
│  │  Fleet Features: applied uniformly across all     │         │
│  │  members regardless of where they run             │         │
│  └───────────────────────────────────────────────────┘         │
└──────────────────────────────────────────────────────────────┘
```

### Registering Clusters in a Fleet

```bash
# Register a GKE cluster (automatic for GKE clusters in the fleet project)
gcloud container fleet memberships register gke-prod-us \
  --gke-cluster us-central1/gke-prod-us \
  --enable-workload-identity

# Register an external cluster (EKS, AKS, on-prem)
# First, generate a registration manifest
gcloud container fleet memberships register eks-prod-east \
  --context=arn:aws:eks:us-east-1:123456789012:cluster/eks-prod \
  --kubeconfig=/path/to/eks-kubeconfig \
  --enable-workload-identity \
  --public-issuer-url=https://oidc.eks.us-east-1.amazonaws.com/id/ABC123

# List fleet members
gcloud container fleet memberships list \
  --format="table(name, uniqueId, authority.workloadIdentityPool, state.code)"
```

### Fleet-Wide Configuration with Config Sync

Config Sync is Google's GitOps engine, similar to Flux or ArgoCD but tightly integrated with Fleet:

```yaml
# config-sync-config.yaml
# Applied once, syncs to all fleet members
apiVersion: configmanagement.gke.io/v1
kind: ConfigManagement
metadata:
  name: config-management
spec:
  sourceFormat: unstructured
  git:
    syncRepo: https://github.com/company/fleet-config.git
    syncBranch: main
    secretType: token
    policyDir: fleet-policies
  policyController:
    enabled: true
    templateLibraryInstalled: true
    referentialRulesEnabled: true
    logDeniesEnabled: true
    mutationEnabled: true
```

```bash
# Enable Config Sync for the entire fleet
gcloud beta container fleet config-management enable

# Apply configuration to all fleet members
gcloud beta container fleet config-management apply \
  --membership=gke-prod-us \
  --config=config-sync-config.yaml

# Check sync status across the fleet
gcloud beta container fleet config-management status \
  --format="table(Name, Status, Last_Synced_Token, Sync_Errors)"
```

### Fleet-Wide Policy with Policy Controller

```yaml
# fleet-policies/constraint-templates/require-labels.yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequiredlabels
spec:
  crd:
    spec:
      names:
        kind: K8sRequiredLabels
      validation:
        openAPIV3Schema:
          type: object
          properties:
            labels:
              type: array
              items:
                type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequiredlabels
        violation[{"msg": msg}] {
          provided := {l | input.review.object.metadata.labels[l]}
          required := {l | l := input.parameters.labels[_]}
          missing := required - provided
          count(missing) > 0
          msg := sprintf("Missing required labels: %v", [missing])
        }

---
# fleet-policies/constraints/require-team-label.yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredLabels
metadata:
  name: require-team-label
spec:
  enforcementAction: deny
  match:
    kinds:
      - apiGroups: ["apps"]
        kinds: ["Deployment", "StatefulSet"]
  parameters:
    labels:
      - "team"
      - "cost-center"
```

---

## Centralized Telemetry for Multi-Cloud Fleets

A fleet without centralized observability is a fleet in name only. You need a single place to see the health, performance, and compliance of every cluster.

### Telemetry Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│              CENTRALIZED FLEET TELEMETRY                       │
│                                                                │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ AWS     │  │ Azure   │  │ GCP     │  │ On-Prem │        │
│  │ Cluster │  │ Cluster │  │ Cluster │  │ Cluster │        │
│  │         │  │         │  │         │  │         │        │
│  │ OTel    │  │ OTel    │  │ OTel    │  │ OTel    │        │
│  │ Collector│  │ Collector│  │ Collector│  │ Collector│        │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘        │
│       │            │            │            │               │
│       └────────────┼────────────┼────────────┘               │
│                    │            │                             │
│              ┌─────▼────────────▼─────┐                      │
│              │  CENTRAL TELEMETRY HUB  │                      │
│              │                          │                      │
│              │  Metrics: Thanos/Cortex │                      │
│              │  Logs: Loki/Elasticsearch│                      │
│              │  Traces: Tempo/Jaeger   │                      │
│              │  Dashboards: Grafana    │                      │
│              └──────────────────────────┘                      │
└──────────────────────────────────────────────────────────────┘
```

### OpenTelemetry Collector for Fleet Telemetry

```yaml
# otel-collector-fleet.yaml
# Deploy on each cluster with cluster-specific labels
apiVersion: v1
kind: ConfigMap
metadata:
  name: otel-collector-config
  namespace: monitoring
data:
  config.yaml: |
    receivers:
      prometheus:
        config:
          scrape_configs:
            - job_name: kubernetes-pods
              kubernetes_sd_configs:
                - role: pod
              relabel_configs:
                - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
                  action: keep
                  regex: true
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317

    processors:
      resource:
        attributes:
          - key: cluster.name
            value: "${CLUSTER_NAME}"
            action: upsert
          - key: cluster.provider
            value: "${CLOUD_PROVIDER}"
            action: upsert
          - key: cluster.region
            value: "${CLUSTER_REGION}"
            action: upsert
          - key: cluster.environment
            value: "${ENVIRONMENT}"
            action: upsert
      batch:
        timeout: 30s
        send_batch_size: 1024

    exporters:
      otlphttp/metrics:
        endpoint: https://telemetry-hub.company.com/api/v1/push
        headers:
          Authorization: "Bearer ${TELEMETRY_TOKEN}"
      otlphttp/traces:
        endpoint: https://telemetry-hub.company.com/api/v1/traces
        headers:
          Authorization: "Bearer ${TELEMETRY_TOKEN}"

    service:
      pipelines:
        metrics:
          receivers: [prometheus]
          processors: [resource, batch]
          exporters: [otlphttp/metrics]
        traces:
          receivers: [otlp]
          processors: [resource, batch]
          exporters: [otlphttp/traces]
```

### Fleet Health Dashboard Query Examples

```promql
# Cluster count by provider and status
count by (cluster_provider, cluster_environment) (
  up{job="kubernetes-apiservers"}
)

# API server latency P99 across the fleet
histogram_quantile(0.99,
  sum by (cluster_name, le) (
    rate(apiserver_request_duration_seconds_bucket{verb!="WATCH"}[5m])
  )
)

# Node readiness across the fleet
sum by (cluster_name) (kube_node_status_condition{condition="Ready", status="true"})
/
sum by (cluster_name) (kube_node_info)

# Pod restart rate by cluster (anomaly detection)
sum by (cluster_name) (
  increase(kube_pod_container_status_restarts_total[1h])
) > 50
```

---

## Multi-Cloud GitOps at Scale

GitOps for a fleet of clusters requires more than a single ArgoCD instance. You need patterns that scale to dozens or hundreds of clusters.

### ArgoCD ApplicationSet for Fleet-Wide Deployment

```yaml
# fleet-gitops/applicationset-platform.yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: fleet-platform-services
  namespace: argocd
spec:
  generators:
    # Generate an Application for every cluster registered in ArgoCD
    - clusters:
        selector:
          matchExpressions:
            - key: environment
              operator: In
              values:
                - production
                - staging
  template:
    metadata:
      name: 'platform-{{name}}'
      labels:
        fleet-component: platform
    spec:
      project: fleet-platform
      source:
        repoURL: https://github.com/company/fleet-platform.git
        targetRevision: main
        path: 'clusters/{{metadata.labels.provider}}/{{metadata.labels.environment}}'
      destination:
        server: '{{server}}'
        namespace: platform-system
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        retry:
          limit: 5
          backoff:
            duration: 5s
            factor: 2
            maxDuration: 3m
        syncOptions:
          - CreateNamespace=true
          - ServerSideApply=true
```

### Fleet Git Repository Structure

```text
fleet-platform/
├── base/                          # Shared across all clusters
│   ├── monitoring/
│   │   ├── prometheus.yaml
│   │   ├── otel-collector.yaml
│   │   └── kustomization.yaml
│   ├── policy/
│   │   ├── kyverno-policies.yaml
│   │   └── kustomization.yaml
│   └── security/
│       ├── falco.yaml
│       └── kustomization.yaml
│
├── clusters/
│   ├── aws/
│   │   ├── production/
│   │   │   ├── kustomization.yaml    # patches for AWS prod
│   │   │   └── values-override.yaml
│   │   └── staging/
│   │       └── kustomization.yaml
│   ├── azure/
│   │   ├── production/
│   │   │   └── kustomization.yaml    # patches for Azure prod
│   │   └── staging/
│   │       └── kustomization.yaml
│   └── onprem/
│       └── production/
│           └── kustomization.yaml    # patches for on-prem
│
└── fleet-sync.yaml                   # ApplicationSet definition
```

```yaml
# clusters/aws/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../../base/monitoring
  - ../../../base/policy
  - ../../../base/security
patches:
  - target:
      kind: ConfigMap
      name: otel-collector-config
    patch: |-
      - op: replace
        path: /data/config.yaml
        value: |
          # AWS-specific: export to CloudWatch as well
          exporters:
            awscloudwatchlogs:
              log_group_name: /eks/fleet-telemetry
              log_stream_name: ${CLUSTER_NAME}
  - target:
      kind: ClusterPolicy
      name: require-image-registry
    patch: |-
      - op: replace
        path: /spec/rules/0/validate/pattern/spec/containers/0/image
        value: "123456789012.dkr.ecr.*.amazonaws.com/*"
```

---

## Did You Know?

1. Azure Arc has connected over 26,000 Kubernetes clusters as of early 2025, including clusters running on AWS, GCP, and edge devices. Microsoft does not charge for the basic Arc connection -- the revenue comes from extensions (Azure Policy, Monitoring, Defender) that cost $6-15 per vCPU/month. A 100-node cluster with 4 vCPUs per node running all extensions can cost $2,400-6,000/month in Arc extension fees alone.

2. Google renamed "Anthos" to "GKE Enterprise" in 2023 partly because customers could not pronounce it consistently. The name "Anthos" came from the Greek word for "flower," symbolizing growth and adaptation. Despite the rebrand, the underlying technology has been remarkably stable -- Config Sync, Policy Controller, and Service Mesh (based on Istio) have remained the core pillars since the original Anthos launch in 2019.

3. The average enterprise fleet grows by 35% per year in cluster count, according to a 2024 Datadog survey. Organizations with fleet management tooling grow faster (42%/year) than those without (21%/year) because the management overhead per cluster is lower, removing the friction that previously limited cluster creation. This suggests that fleet management tools do not just manage existing complexity -- they enable more of it.

4. Rancher, originally created by Rancher Labs and now owned by SUSE after a $600 million acquisition in 2020, manages over 180,000 clusters worldwide. Unlike Arc and Fleet which are tied to specific clouds, Rancher is fully vendor-neutral and self-hosted. Its "Fleet" component (confusingly sharing a name concept with Google's Fleet) handles GitOps-based multi-cluster management and scales to thousands of clusters per management server.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| **Connecting clusters to Arc/Fleet without a strategy** | "Let us just connect everything and see what happens." Clusters flood in without naming conventions, tags, or ownership. | Define a fleet taxonomy first: naming conventions, required tags (provider, environment, team, region), grouping strategy. Then connect clusters. |
| **Using fleet management as the sole management layer** | "Arc/Fleet replaces our need for per-cluster tools." But fleet tools provide a subset of cluster management features. | Fleet tools handle cross-cluster concerns (policy, config sync, observability). Per-cluster concerns (node management, storage, networking) still need per-cluster tools. |
| **Same configuration for all clusters** | "One size fits all -- push the same policies and monitoring everywhere." But dev clusters do not need production-grade monitoring, and on-prem clusters have different storage classes. | Use the base/overlay pattern: shared base configurations with per-environment and per-provider patches. Kustomize overlays are ideal for this. |
| **Ignoring fleet telemetry costs** | Centralized monitoring of 50 clusters generates enormous data volumes. Teams are surprised by a $30K/month observability bill. | Set retention policies, use sampling for traces, aggregate metrics at the cluster level before shipping. Calculate telemetry costs per cluster before enabling fleet-wide collection. |
| **No cluster lifecycle management** | Fleet management connects existing clusters but nobody plans for cluster creation, upgrades, or decommissioning at fleet scale. | Combine fleet management with Cluster API or Crossplane for lifecycle. Fleet tools manage what runs in clusters; lifecycle tools manage the clusters themselves. |
| **Multi-cloud GitOps without abstractions** | Git repo contains provider-specific configs scattered everywhere. Changing a policy means editing 3 different files for 3 providers. | Use the base/overlay pattern shown in this module. Provider-specific differences go in overlay patches, not in the base configuration. |

---

## Quiz

<details>
<summary>Question 1: What is the fundamental architectural difference between Azure Arc and Google Fleet (GKE Enterprise) for managing non-native clusters?</summary>

**Azure Arc** uses an agent installed inside the target cluster that maintains an outbound HTTPS connection to Azure. All communication is initiated by the agent (outbound only), so no inbound firewall rules are needed. The agent makes the cluster appear as an Azure resource in ARM (Azure Resource Manager), which means all Azure management tools (Policy, Monitor, Defender) work on it.

**Google Fleet** also uses an agent for non-GKE clusters, but Fleet has a stronger concept of "fleet features" -- capabilities like Config Sync, Policy Controller, and Service Mesh that are enabled at the fleet level and automatically distributed to all members. Google's approach is more opinionated: if you enable a feature on the fleet, every member gets it. Arc is more a-la-carte: you choose which extensions to install on each cluster.

The practical difference is that Fleet is better for homogeneous fleets (where you want identical configuration everywhere), while Arc is more flexible for heterogeneous fleets (where different clusters need different extensions).
</details>

<details>
<summary>Question 2: Your company has 40 clusters: 25 on AWS, 10 on Azure, and 5 on-premises. You need to choose between Azure Arc and Google Fleet. What factors should drive the decision?</summary>

Key factors: (1) **Existing cloud investment**: If the company already uses Azure AD for identity, Azure Monitor for observability, and Azure DevOps for CI/CD, Arc integrates seamlessly with these tools. If using GCP services, Fleet is more natural. (2) **Team expertise**: Arc requires Azure knowledge, Fleet requires GCP knowledge. Pick the one your team already knows. (3) **Feature requirements**: If you need built-in service mesh (Istio), Fleet has tighter integration. If you need integration with Windows containers or Azure SQL, Arc is stronger. (4) **Cost**: Arc charges per-vCPU for extensions. Fleet charges per-vCPU for GKE Enterprise. Compare total cost for your fleet size. (5) **Vendor neutrality**: Both create dependency on a cloud provider for your management plane. If this is a concern, consider Rancher (self-hosted, vendor-neutral). Given 25/40 clusters are on AWS, you might also evaluate EKS Connector + ArgoCD as a lighter-weight option that does not introduce a third cloud dependency.
</details>

<details>
<summary>Question 3: How does the base/overlay pattern in GitOps solve the multi-cloud configuration problem?</summary>

The base/overlay pattern separates **what** you want to deploy (base) from **how** it differs per environment (overlay). The base directory contains configurations that are identical across all clusters: monitoring stack, policy definitions, security tools. Overlay directories contain patches specific to each cloud provider or environment: AWS clusters use ECR image registries, Azure clusters use ACR, on-prem uses Harbor. A Kustomization file in each overlay references the base and applies patches. When you change a policy in the base, it propagates to all clusters automatically. When you need a provider-specific adjustment, you only change the relevant overlay. Without this pattern, you end up with N copies of every configuration file (one per cluster), and keeping them in sync becomes impossible at scale.
</details>

<details>
<summary>Question 4: A fleet-wide policy update is pushed via GitOps. It works on 39 out of 40 clusters. The 40th cluster (an on-premises kubeadm cluster running Kubernetes 1.28) rejects the policy. What happened and how do you handle it?</summary>

The most likely cause is a **Kubernetes version incompatibility**. If the policy uses an API version or feature available in 1.30+ (like a newer Gatekeeper constraint template), the 1.28 cluster will reject it. This is a common fleet management challenge: version skew across clusters. Solutions: (1) Include **version gates** in your GitOps configuration -- only sync policies that match the cluster's Kubernetes version. ArgoCD ApplicationSets can filter by cluster labels including version. (2) **Upgrade the outlier** -- if one cluster is significantly behind the fleet, it creates ongoing friction. (3) **Use conditional patches** in Kustomize overlays that adjust policies for older clusters. (4) **Add automated pre-flight checks** in the GitOps pipeline that validate each configuration against the target cluster's capabilities before syncing.
</details>

<details>
<summary>Question 5: What are the telemetry cost implications of centralizing monitoring for a 50-cluster fleet?</summary>

A single Kubernetes cluster with 20 nodes and 200 pods generates approximately 50,000-100,000 active metric time series. At 50 clusters, that is 2.5-5 million time series. Managed services like Grafana Cloud charge $8/1000 active series/month, making the metrics bill $20,000-40,000/month. Logs are even more expensive: 50 clusters can generate 500GB-2TB of logs per day. At $0.50/GB ingestion, that is $250-1,000/day for logs alone. **Mitigation strategies**: (1) Filter metrics at the source -- only ship golden signals (latency, traffic, errors, saturation) to the central hub. (2) Aggregate before shipping -- pre-aggregate per-pod metrics into per-deployment metrics. (3) Sample traces -- 1-5% sampling for normal traffic, 100% for errors. (4) Set retention tiers -- 7 days hot storage, 30 days warm, 365 days cold (S3/GCS). (5) Use open-source central stores (Thanos, Loki, Tempo) instead of managed services if the team has capacity to operate them.
</details>

<details>
<summary>Question 6: Why is fleet management not a replacement for per-cluster management tools? Give two specific examples.</summary>

Fleet management tools handle **cross-cluster concerns** but cannot handle **cluster-internal operations** that require deep provider-specific knowledge. Example 1: **Node autoscaling**. Azure Arc can push policies to an EKS cluster, but it cannot configure Karpenter provisioners or EKS managed node group scaling parameters. Those are AWS-specific operations that require EKS-specific tools (eksctl, Terraform with AWS provider, or AWS console). Example 2: **Storage management**. Fleet tools can deploy a StorageClass manifest, but configuring the underlying storage (EBS CSI driver, Azure Disk CSI driver, or on-prem Ceph) requires provider-specific knowledge and tools. The fleet tool cannot resize an EBS volume or configure a Ceph pool. Fleet management is best understood as a coordination layer on top of per-cluster management, not a replacement for it.
</details>

---

## Hands-On Exercise: Build a Multi-Cluster Fleet with GitOps

In this exercise, you will create a fleet of three kind clusters simulating different environments, implement centralized GitOps, and build a fleet inventory and health dashboard.

**What you will build:**

```text
┌──────────────────────────────────────────────────────┐
│  Fleet Management Lab                                  │
│                                                        │
│  Management Cluster (ArgoCD)                           │
│  ├── fleet-aws-prod (kind, simulates AWS)             │
│  ├── fleet-azure-staging (kind, simulates Azure)      │
│  └── fleet-onprem-prod (kind, simulates on-prem)      │
│                                                        │
│  GitOps: ArgoCD ApplicationSets deploy platform        │
│  services to all fleet members                         │
└──────────────────────────────────────────────────────┘
```

### Task 1: Create the Fleet Clusters

<details>
<summary>Solution</summary>

```bash
# Create three clusters
for CLUSTER in fleet-mgmt fleet-aws-prod fleet-azure-staging; do
  kind create cluster --name $CLUSTER
done

# Verify all clusters are running
for CLUSTER in fleet-mgmt fleet-aws-prod fleet-azure-staging; do
  echo "=== $CLUSTER ==="
  kubectl --context kind-$CLUSTER get nodes
done
```

</details>

### Task 2: Install ArgoCD on the Management Cluster

<details>
<summary>Solution</summary>

```bash
# Install ArgoCD on management cluster
kubectl --context kind-fleet-mgmt create namespace argocd
kubectl --context kind-fleet-mgmt apply -n argocd \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
kubectl --context kind-fleet-mgmt wait --for=condition=available \
  deployment/argocd-server -n argocd --timeout=120s

# Get the admin password
ARGOCD_PW=$(kubectl --context kind-fleet-mgmt -n argocd \
  get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d)
echo "ArgoCD admin password: $ARGOCD_PW"
```

</details>

### Task 3: Register Fleet Clusters in ArgoCD

<details>
<summary>Solution</summary>

```bash
# Get the API server URLs for each fleet cluster
AWS_SERVER=$(kubectl --context kind-fleet-aws-prod config view --minify -o jsonpath='{.clusters[0].cluster.server}')
AZURE_SERVER=$(kubectl --context kind-fleet-azure-staging config view --minify -o jsonpath='{.clusters[0].cluster.server}')

# Add fleet clusters to ArgoCD via CLI or Secrets
# Using the Secret method (no argocd CLI needed)
for CLUSTER_INFO in "fleet-aws-prod:aws:production:kind-fleet-aws-prod" "fleet-azure-staging:azure:staging:kind-fleet-azure-staging"; do
  NAME=$(echo $CLUSTER_INFO | cut -d: -f1)
  PROVIDER=$(echo $CLUSTER_INFO | cut -d: -f2)
  ENV=$(echo $CLUSTER_INFO | cut -d: -f3)
  CTX=$(echo $CLUSTER_INFO | cut -d: -f4)

  SERVER=$(kubectl --context $CTX config view --minify -o jsonpath='{.clusters[0].cluster.server}')
  CA_DATA=$(kubectl --context $CTX config view --minify --raw -o jsonpath='{.clusters[0].cluster.certificate-authority-data}')
  TOKEN=$(kubectl --context $CTX -n kube-system get secret \
    $(kubectl --context $CTX -n kube-system get sa default -o jsonpath='{.secrets[0].name}' 2>/dev/null || echo "none") \
    -o jsonpath='{.data.token}' 2>/dev/null | base64 -d || echo "")

  # Create a ServiceAccount for ArgoCD in the target cluster
  kubectl --context $CTX create serviceaccount argocd-manager -n kube-system 2>/dev/null || true
  kubectl --context $CTX create clusterrolebinding argocd-manager \
    --clusterrole=cluster-admin --serviceaccount=kube-system:argocd-manager 2>/dev/null || true

  cat <<EOF | kubectl --context kind-fleet-mgmt apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: cluster-$NAME
  namespace: argocd
  labels:
    argocd.argoproj.io/secret-type: cluster
    provider: $PROVIDER
    environment: $ENV
type: Opaque
stringData:
  name: $NAME
  server: $SERVER
  config: |
    {
      "tlsClientConfig": {
        "insecure": true
      }
    }
EOF

  echo "Registered cluster: $NAME (provider=$PROVIDER, env=$ENV)"
done

# Verify clusters are registered
kubectl --context kind-fleet-mgmt get secrets -n argocd -l argocd.argoproj.io/secret-type=cluster
```

</details>

### Task 4: Deploy Platform Services Across the Fleet

<details>
<summary>Solution</summary>

```bash
# Create platform baseline configmaps on each cluster via ArgoCD Applications
# Since we don't have a Git repo, we'll use a direct approach to demonstrate the pattern

for CTX in kind-fleet-aws-prod kind-fleet-azure-staging; do
  CLUSTER_NAME=$(echo $CTX | sed 's/kind-//')

  # Create platform namespace
  kubectl --context $CTX create namespace platform-system 2>/dev/null || true

  # Deploy fleet-standard configuration
  cat <<EOF | kubectl --context $CTX apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: fleet-identity
  namespace: platform-system
  labels:
    managed-by: fleet-management
data:
  cluster-name: "$CLUSTER_NAME"
  fleet-version: "1.0.0"
  managed-by: "fleet-mgmt-cluster"
  registered-at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: fleet-monitoring-config
  namespace: platform-system
  labels:
    managed-by: fleet-management
data:
  scrape-interval: "30s"
  retention: "7d"
  external-labels: |
    cluster=$CLUSTER_NAME
    fleet=enterprise
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: fleet-default-deny
  namespace: platform-system
  labels:
    managed-by: fleet-management
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
  egress:
    - to: []
      ports:
        - protocol: TCP
          port: 443
        - protocol: TCP
          port: 53
        - protocol: UDP
          port: 53
EOF

  echo "Platform services deployed to $CLUSTER_NAME"
done
```

</details>

### Task 5: Build a Fleet Inventory and Health Report

<details>
<summary>Solution</summary>

```bash
cat <<'SCRIPT' > /tmp/fleet-report.sh
#!/bin/bash
echo "============================================="
echo "  FLEET INVENTORY & HEALTH REPORT"
echo "  $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "============================================="

TOTAL_NODES=0
TOTAL_PODS=0
TOTAL_CLUSTERS=0
HEALTHY=0

for CTX in kind-fleet-aws-prod kind-fleet-azure-staging; do
  CLUSTER=$(echo $CTX | sed 's/kind-//')
  TOTAL_CLUSTERS=$((TOTAL_CLUSTERS + 1))

  echo ""
  echo "--- Cluster: $CLUSTER ---"

  # Get cluster info
  FLEET_ID=$(kubectl --context $CTX get configmap fleet-identity -n platform-system -o jsonpath='{.data.cluster-name}' 2>/dev/null || echo "NOT REGISTERED")
  echo "  Fleet ID: $FLEET_ID"

  # Node health
  NODES=$(kubectl --context $CTX get nodes --no-headers 2>/dev/null | wc -l | tr -d ' ')
  READY_NODES=$(kubectl --context $CTX get nodes --no-headers 2>/dev/null | grep " Ready" | wc -l | tr -d ' ')
  echo "  Nodes: $READY_NODES/$NODES ready"
  TOTAL_NODES=$((TOTAL_NODES + NODES))

  # Pod count
  PODS=$(kubectl --context $CTX get pods -A --no-headers --field-selector=status.phase=Running 2>/dev/null | wc -l | tr -d ' ')
  echo "  Running Pods: $PODS"
  TOTAL_PODS=$((TOTAL_PODS + PODS))

  # K8s version
  VERSION=$(kubectl --context $CTX version --short 2>/dev/null | grep Server | awk '{print $3}' || kubectl --context $CTX get nodes -o jsonpath='{.items[0].status.nodeInfo.kubeletVersion}' 2>/dev/null)
  echo "  Kubernetes Version: $VERSION"

  # Fleet services check
  FLEET_CONFIGS=$(kubectl --context $CTX get configmap -n platform-system -l managed-by=fleet-management --no-headers 2>/dev/null | wc -l | tr -d ' ')
  NETPOLS=$(kubectl --context $CTX get networkpolicy -n platform-system -l managed-by=fleet-management --no-headers 2>/dev/null | wc -l | tr -d ' ')

  if [ "$FLEET_CONFIGS" -ge 2 ] && [ "$NETPOLS" -ge 1 ]; then
    echo "  Fleet Services: HEALTHY ($FLEET_CONFIGS configs, $NETPOLS netpols)"
    HEALTHY=$((HEALTHY + 1))
  else
    echo "  Fleet Services: DEGRADED (configs=$FLEET_CONFIGS, netpols=$NETPOLS)"
  fi
done

echo ""
echo "============================================="
echo "  FLEET SUMMARY"
echo "============================================="
echo "  Total Clusters: $TOTAL_CLUSTERS"
echo "  Healthy Clusters: $HEALTHY/$TOTAL_CLUSTERS"
echo "  Total Nodes: $TOTAL_NODES"
echo "  Total Running Pods: $TOTAL_PODS"
echo "  Fleet Health: $(( (HEALTHY * 100) / TOTAL_CLUSTERS ))%"
echo "============================================="
SCRIPT

chmod +x /tmp/fleet-report.sh
bash /tmp/fleet-report.sh
```

</details>

### Clean Up

```bash
kind delete cluster --name fleet-mgmt
kind delete cluster --name fleet-aws-prod
kind delete cluster --name fleet-azure-staging
docker network rm hybrid-net 2>/dev/null || true
rm /tmp/fleet-report.sh
```

### Success Criteria

- [ ] I created three kind clusters simulating a multi-cloud fleet
- [ ] I installed ArgoCD on the management cluster
- [ ] I registered fleet clusters in ArgoCD with provider and environment labels
- [ ] I deployed standardized platform services across all fleet members
- [ ] I built a fleet inventory and health report
- [ ] I can explain the architectural differences between Azure Arc and Google Fleet
- [ ] I can describe the base/overlay pattern for multi-cloud GitOps

---

## Next Module

Now that you can manage a fleet of clusters, it is time to learn how to provision them declaratively. Head to [Module 10.6: Multi-Cloud Provisioning with Cluster API](../module-10.6-cluster-api/) to learn how CAPI and its providers (CAPA, CAPZ, CAPG) let you create, upgrade, and scale Kubernetes clusters across any infrastructure using Kubernetes-native APIs.
