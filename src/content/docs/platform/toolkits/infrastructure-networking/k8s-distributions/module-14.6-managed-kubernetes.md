---
citations_verified: true
title: "Module 14.6: Managed Kubernetes - EKS vs GKE vs AKS"
slug: platform/toolkits/infrastructure-networking/k8s-distributions/module-14.6-managed-kubernetes
sidebar:
  order: 7
---

## Complexity: [COMPLEX]

## Time to Complete: 55-60 minutes

## Prerequisites

Before starting this module, you should have completed the self-managed Kubernetes modules so the tradeoffs in managed services feel concrete rather than abstract.
You should understand what the control plane does, why etcd failure is serious, and how cloud networking changes cluster behavior.

- [Module 14.4: Talos](../module-14.4-talos/) for immutable self-managed cluster operations and upgrade responsibility.
- [Module 14.5: OpenShift](../module-14.5-openshift/) for enterprise platform packaging and distribution-level opinions.
- Kubernetes fundamentals, including API server, scheduler, controllers, kubelet, Services, Ingress, and storage classes.
- Basic cloud provider knowledge in at least one of AWS, Google Cloud, or Azure, including IAM and virtual networking.
- [Platform Engineering Discipline](/platform/disciplines/core-platform/platform-engineering/) for platform decision framing and internal customer thinking.

---

## Learning Outcomes

After completing this module, you will be able to:

- **Evaluate** EKS, GKE, and AKS against a real workload profile instead of choosing by brand familiarity or a single headline price.
- **Design** a managed Kubernetes baseline that includes private networking, workload identity, node lifecycle policy, upgrade policy, and cost controls.
- **Compare** standard node-pool operations with serverless or autopilot-style modes, then justify which model fits a workload's risk and cost pattern.
- **Debug** common managed-cluster failures by separating provider-managed control plane concerns from customer-owned node, networking, and identity concerns.
- **Create** a decision record that explains why a team should choose one managed Kubernetes provider, one operating mode, and one migration sequence.

---

## Why This Module Matters

A platform team joined an incident bridge at 02:13 after a checkout API stopped accepting writes during a holiday promotion.
The first symptom looked ordinary: application pods were healthy, the Ingress controller was still serving read requests, and CPU graphs were calm.
Then the on-call engineer ran `kubectl get pods` and waited almost a minute for the API server to answer.

The company had built its own Kubernetes control plane because the first version of the platform needed a custom network plugin and a few nonstandard admission controls.
That decision made sense when the platform served two internal teams, but the cluster had quietly become the production substrate for payment processing, order routing, and customer support tools.
The team had automation for node replacement, yet control-plane upgrades, etcd compaction, backup validation, certificate rotation, and API server capacity were still handled by a small group of specialists.

By morning, the outage review found an uncomfortable pattern rather than a single mistake.
The team had optimized for maximum control years earlier, but the business now needed boring availability, repeatable upgrades, audit evidence, and faster cluster creation.
They had been treating Kubernetes as an engineering project when the company needed it to behave like a managed utility.

Managed Kubernetes does not remove platform engineering work; it changes where the work lives.
The provider operates the control plane, but your team still owns workload architecture, identity boundaries, network exposure, node choices, cost guardrails, upgrade timing, and developer experience.
A weak managed Kubernetes decision can still create outages, surprise bills, and security gaps, because the provider cannot guess your traffic pattern or your compliance model.

The hard question is not "which provider is best."
The hard question is "which provider best matches this organization's existing cloud gravity, risk tolerance, workload shape, and operating maturity."
EKS, GKE, and AKS all run Kubernetes, but they encode different assumptions about IAM, networking, upgrades, node management, and integration with the surrounding cloud.

This module teaches the decision as a platform architecture problem, not a product comparison page.
You will first build a mental model of what managed Kubernetes really manages, then compare provider-specific choices, then practice writing a decision record for a realistic workload.
By the end, you should be able to defend a managed Kubernetes recommendation in front of an infrastructure team, an application team, a security team, and a finance team.

---

## Core Section 1: What Managed Kubernetes Actually Moves Off Your Plate

Managed Kubernetes is easiest to understand as a responsibility boundary.
The provider takes ownership of the Kubernetes control plane availability and much of the lifecycle machinery around it, while the customer keeps responsibility for workloads and most blast-radius decisions.
That boundary sounds simple, but real incidents often happen where teams assume the provider owns more than it actually does.

```ascii
MANAGED KUBERNETES RESPONSIBILITY BOUNDARY
────────────────────────────────────────────────────────────────────────────

                 PROVIDER OPERATES                         CUSTOMER OPERATES
┌────────────────────────────────────────────┐   ┌────────────────────────────────────────────┐
│ Kubernetes API server availability          │   │ Namespace, RBAC, and admission policy      │
│ etcd replication, backup, and encryption     │   │ Workload manifests and rollout strategy    │
│ Control plane patching and replacement       │   │ Node pool shape, labels, taints, and cost   │
│ Cluster endpoint certificates                │   │ Network exposure and service boundaries     │
│ Provider integration controllers             │   │ Workload identity and cloud permissions     │
│ Version availability and upgrade channels    │   │ Observability, SLOs, and incident response  │
└────────────────────────────────────────────┘   └────────────────────────────────────────────┘
                         │                                             │
                         └──────────── shared contract ────────────────┘
                                      API compatibility,
                                      upgrade windows,
                                      quotas, regions,
                                      and support policy
```

The provider-managed side is valuable because control-plane work is specialized and unforgiving.
Most application teams do not want to practice etcd restore procedures, rotate API server certificates, or maintain a highly available controller-manager deployment.
Even strong platform teams often prefer to spend their scarce attention on developer workflows, paved roads, policy, and reliability patterns rather than rebuilding a cloud provider's operational muscle.

The customer-owned side remains broad enough that "managed" should never be read as "hands off."
A public cluster endpoint can still be exposed too widely, a node pool can still run in a single zone, a service account can still have excessive cloud permissions, and an autoscaler can still chase a runaway workload.
Managed Kubernetes reduces one category of operational risk while leaving architecture risk firmly in the platform team's hands.

A useful first test is to ask whether a failure would be solved by opening a cloud provider support case or by changing your own configuration.
If the API server is down in every zone for a regional managed cluster, the provider is probably the owner.
If pods cannot pull images because your private registry permissions are wrong, the provider is only supplying the stage where your configuration failed.

> **Stop and think:** Your team says, "We moved to managed Kubernetes, so upgrades are the provider's problem now."
> Which parts of an upgrade are genuinely provider-owned, and which parts still require your team's testing, compatibility checks, and rollout planning?

The answer matters because upgrade ownership is split.
The provider can make a [Kubernetes minor version](https://kubernetes.io/docs/reference/using-api/deprecation-guide/) available, patch the control plane, and sometimes upgrade nodes automatically.
Your team still needs to test deprecated APIs, validate admission controllers, confirm CNI compatibility, coordinate disruption budgets, and update add-ons that are not provider-managed.

| Responsibility Area | Provider Usually Owns | Customer Usually Owns | Platform Team Question |
|---------------------|------------------------|------------------------|------------------------|
| Control plane health | API server, etcd, controllers | API usage patterns and request bursts | Can our clients tolerate API throttling or maintenance windows? |
| Node lifecycle | Managed node replacement primitives | Node pool sizing, images, taints, and disruption | Do workloads have requests, limits, and disruption budgets? |
| Networking | Cloud load balancer integrations | CIDR design, private access, policies, and exposure | Can services reach what they need without broad network trust? |
| Identity | Federation mechanism and token plumbing | Least-privilege roles and service account binding | Can one compromised pod reach unrelated cloud resources? |
| Upgrades | Version channels and control-plane patching | Workload compatibility and add-on testing | Can we prove every critical workload survives the next minor version? |
| Cost | Billing primitives and pricing pages | Traffic shape, autoscaling policy, and waste control | Which workload behavior drives the bill during peak and failure modes? |

The table reveals a core platform lesson: managed Kubernetes changes the operating model from "run every component" to "govern the boundaries."
A senior platform engineer does not memorize every provider checkbox.
They ask where failure can cross a boundary, who has authority to fix it, and what evidence proves the boundary behaves as intended.

That is why provider choice should start from workload and organization context.
A team already deep in AWS databases, queues, and identity may accept EKS control-plane cost because the integration reduces application complexity.
A company standardized on Microsoft identity and Windows workloads may prefer AKS because the enterprise integration removes friction.
A team that wants strong defaults, fast Kubernetes maturity, and minimal node management may choose GKE, especially when Autopilot fits the workload.

```ascii
DECISION CONTEXT BEFORE PROVIDER CONTEXT
────────────────────────────────────────────────────────────────────────────

        Workload shape
             │
             ▼
        Existing cloud gravity
             │
             ▼
        Security and compliance model
             │
             ▼
        Operations maturity
             │
             ▼
        Cost and traffic pattern
             │
             ▼
        Provider and operating mode choice
```

If you reverse that sequence, the decision becomes shallow.
Teams often choose the cloud they personally know, then retrofit the workload to the provider's defaults.
That can work for small systems, but it becomes expensive when identity, egress, upgrade policy, or regulatory constraints show up later as architectural surprises.

This module uses `kubectl` in examples because the Kubernetes API remains the common interface across providers.
After the first provider credentials are configured, many operators set `alias k=kubectl` in their shell for speed; later verification commands use `k` after that convention is introduced.
The alias does not change behavior, and every command can be run by replacing `k` with `kubectl`.

```bash
alias k=kubectl
k version --client
```

A managed cluster decision should always produce a written operating model.
The document does not need to be long, but it should say who upgrades what, who pays for what, who can create clusters, what defaults are enforced, and what exceptions require review.
Without that model, teams inherit provider defaults accidentally and discover the real decision only during an outage or budget review.

---

## Core Section 2: A Decision Model That Starts With Workload Reality

The fastest way to make a weak provider decision is to compare features before describing the workload.
Feature matrices are useful after you know what you are optimizing for, but they are dangerous when they become the starting point.
A platform team should first describe the workload's reliability target, traffic shape, identity needs, data location, and operational constraints.

```ascii
WORKLOAD PROFILE TEMPLATE
────────────────────────────────────────────────────────────────────────────

┌───────────────────────────┐
│ Business criticality       │  Revenue path, internal tool, regulated platform, or experiment
├───────────────────────────┤
│ Runtime pattern            │  Steady, bursty, batch, latency-sensitive, GPU-heavy, or Windows
├───────────────────────────┤
│ Data gravity               │  Primary databases, object stores, analytics systems, and regions
├───────────────────────────┤
│ Identity boundary          │  Cloud services the pods must access and who approves permissions
├───────────────────────────┤
│ Network boundary           │  Public ingress, private services, egress volume, and service mesh
├───────────────────────────┤
│ Operations model           │  Who upgrades nodes, responds to alerts, and supports developers
├───────────────────────────┤
│ Cost driver                │  Compute, egress, storage, load balancers, control plane, or support
└───────────────────────────┘
```

The model is intentionally provider-neutral.
If a team cannot fill it out, they are not ready to compare EKS, GKE, and AKS in a meaningful way.
The missing answers become discovery work, not footnotes.

Here is a worked example before you practice the same reasoning later.
A SaaS company runs a customer API, a background billing worker, and an analytics exporter.
The API reads from a managed PostgreSQL database, the worker publishes to a cloud queue, and the exporter sends large objects to a data warehouse.
Most engineers know AWS, but the security team has standardized workforce identity on Microsoft Entra ID.

The naive answer is "use EKS because the team knows AWS."
That may be correct, but it is not yet justified.
The better process is to score each provider against the actual constraints, then decide whether the advantages are strong enough to justify the operational and migration cost.

| Decision Factor | Workload Evidence | EKS Implication | GKE Implication | AKS Implication |
|-----------------|-------------------|-----------------|-----------------|-----------------|
| Data gravity | PostgreSQL and queue are already in AWS | Strong fit through VPC and IAM integration | Adds cross-cloud data path unless migrated | Adds cross-cloud data path unless migrated |
| Workforce identity | Security uses Microsoft Entra ID | Possible through federation, but extra design | Possible through federation, but extra design | Strong enterprise identity fit |
| Egress pattern | Analytics exporter sends large objects daily | Model NAT, inter-region, and internet egress carefully | May be attractive if analytics moves to Google Cloud | Depends on data destination and ExpressRoute design |
| Team maturity | Team can operate node pools but not control planes | Managed node groups match existing skills | Standard or Autopilot can reduce operations load | Node pools match existing enterprise patterns |
| Compliance | Customer data must stay in two regions | Region availability and AWS controls matter | Region availability and org policy matter | Azure compliance and policy may help |
| Migration cost | Existing Terraform and CI/CD are AWS-oriented | Lowest immediate migration cost | Higher migration effort unless future analytics dominates | Higher migration effort unless identity dominates |

The recommendation from this table would likely be EKS for the first managed cluster, with a deliberate review of analytics traffic and identity federation.
That is not because EKS is universally better.
It is because this particular workload has strong AWS data gravity and an existing AWS delivery path, so moving compute elsewhere would introduce cross-cloud coupling before it creates enough value.

A senior decision record would also name the conditions that could change the answer.
If the analytics exporter becomes the dominant cost and moves to BigQuery, GKE deserves a fresh evaluation.
If Windows workloads and Entra-based governance become central, AKS may become the better platform.
Good architecture decisions include reversal criteria because organizations change faster than provider comparison tables.

> **Pause and predict:** If this SaaS company moves only the public API to another cloud while leaving the database in AWS, what new failure modes appear?
> Think about latency, egress billing, private connectivity, incident ownership, and which team can see packet-level evidence during an outage.

The most important new failure mode is that the user path now crosses cloud boundaries.
A database query may work in normal conditions but become fragile under congestion, routing changes, quota limits, or private-link misconfiguration.
The bill also becomes harder to explain because a traffic spike may increase both compute cost and inter-cloud transfer cost.

```ascii
SINGLE-CLOUD PATH VS CROSS-CLOUD PATH
────────────────────────────────────────────────────────────────────────────

Single-cloud path:

[User] ──▶ [Cloud LB] ──▶ [Kubernetes API Pods] ──▶ [Managed Database]
                         same provider network        same region controls

Cross-cloud path:

[User] ──▶ [Cloud B LB] ──▶ [Kubernetes API Pods] ═══▶ [Cloud A Database]
                         provider B operations       provider A data gravity
                                                   private link, VPN, or public egress
```

This does not mean multi-cloud is wrong.
It means multi-cloud should pay rent by solving a real business problem that is larger than the complexity tax.
Data residency, acquisition integration, customer-specific compliance, and major cost differences can justify it.
"Keeping options open" is usually too vague to justify the operational surface area.

Decision models should include both qualitative and quantitative evidence.
Qualitative evidence explains why a provider reduces friction or risk.
Quantitative evidence estimates control-plane cost, node cost, load balancer cost, storage, egress, support tier, and migration effort.
Both matter because a cheap cluster that slows delivery can be expensive, while an expensive cluster that removes operational toil may be a bargain.

| Cost Category | What To Estimate | Why It Changes The Decision |
|---------------|------------------|-----------------------------|
| Control plane or cluster management fee | Per-cluster hourly charges, paid SLA tiers, or free-tier limits | Many small clusters can make fixed fees visible even when node cost is low |
| Worker compute | VM size, committed use discounts, spot capacity, GPU, and architecture | Steady workloads often benefit from node pools and reservations |
| Serverless pod compute | Requested CPU and memory over time, plus minimums and platform overhead | Bursty workloads may save operations effort while costing more per unit |
| Load balancers | Public and internal load balancers, NAT gateways, and ingress controllers | Platform defaults can create one billable resource per service |
| Network transfer | Cross-zone, cross-region, internet, NAT, and inter-cloud movement | Chatty microservices can make network the real cost center |
| Observability | Logs, metrics, traces, retention, and managed monitoring integrations | Noisy clusters can spend more on telemetry than teams expect |
| Migration effort | Terraform changes, IAM redesign, CI/CD changes, and retraining | A cheaper target provider may not pay back if migration is complex |

The model should also separate cluster choice from operating mode.
[EKS with managed node groups](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html) is a different experience from [EKS with Fargate](https://docs.aws.amazon.com/eks/latest/userguide/fargate-profile.html).
GKE Standard is different from GKE Autopilot.
AKS with user node pools is different from [AKS virtual nodes](https://learn.microsoft.com/en-us/azure/aks/virtual-nodes) or other burst patterns.
Choosing the provider is only half the decision; choosing how much node responsibility you keep is the other half.

---

## Core Section 3: Provider Deep Dives With Scaffolding, Not Just Commands

The following sections compare EKS, GKE, and AKS through the same lens: architecture, creation path, identity model, networking model, node model, and operational habit.
The goal is not to memorize commands.
The goal is to recognize the provider's opinionated shape so you can predict where a design will be easy and where it will push back.

### Amazon EKS: AWS-Native Integration With Explicit Assembly

EKS is often the strongest fit when workloads depend heavily on AWS services such as RDS, DynamoDB, S3, SQS, SNS, MSK, IAM, and VPC networking.
Its philosophy is composable: AWS gives you a managed Kubernetes control plane, but many production capabilities are assembled through add-ons, IAM roles, load balancer controllers, and VPC choices.
That explicit assembly can feel verbose, but it also gives experienced AWS teams familiar control surfaces.

```ascii
EKS ARCHITECTURE
────────────────────────────────────────────────────────────────────────────

                         AWS MANAGED CONTROL PLANE
┌──────────────────────────────────────────────────────────────────────────┐
│ ┌──────────────────┐   ┌──────────────────┐   ┌───────────────────────┐ │
│ │ Kubernetes API    │   │ Encrypted etcd    │   │ Controllers and       │ │
│ │ server endpoint   │   │ managed by AWS    │   │ scheduler             │ │
│ └──────────────────┘   └──────────────────┘   └───────────────────────┘ │
│          │                         │                         │           │
│          └────────────── managed availability boundary ──────┘           │
└──────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                              CUSTOMER AWS VPC
┌──────────────────────────────────────────────────────────────────────────┐
│ ┌──────────────────────┐  ┌──────────────────────┐  ┌─────────────────┐ │
│ │ Managed node group    │  │ Self-managed nodes    │  │ Fargate profile │ │
│ │ EC2 instances         │  │ custom lifecycle      │  │ serverless pods │ │
│ │ VPC CNI pod IPs       │  │ more responsibility   │  │ no node access  │ │
│ └──────────────────────┘  └──────────────────────┘  └─────────────────┘ │
│          │                         │                         │           │
│          └──────────── AWS IAM, security groups, subnets ────┘           │
└──────────────────────────────────────────────────────────────────────────┘
```

[The EKS control plane is managed](https://docs.aws.amazon.com/eks/latest/userguide/what-is-eks.html), but the surrounding AWS resources are still design choices.
Subnets determine where nodes and load balancers land.
Security groups determine which components can talk.
IAM roles determine what controllers and workloads can do.
A production EKS baseline is therefore as much an AWS architecture as a Kubernetes architecture.

The following command creates a small EKS cluster using `eksctl`.
It is runnable in an AWS account with suitable permissions, but it is intentionally framed as a learning cluster rather than a production template.
For production, you would normally codify the same choices in Terraform, CloudFormation, Pulumi, or an internal platform workflow.

```bash
eksctl create cluster \
  --name dojo-eks-managed \
  --region us-west-2 \
  --version 1.35 \
  --nodegroup-name general-workers \
  --node-type m6i.large \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 6 \
  --managed
```

A first-time operator often sees this command as "create Kubernetes."
A platform engineer reads it as several decisions: region, Kubernetes version, instance family, scaling envelope, and node ownership model.
The command works, but the review should ask whether the subnets are private, whether the API endpoint is public, whether add-ons are pinned, and whether the node role has only the permissions it needs.

```bash
aws eks update-kubeconfig \
  --name dojo-eks-managed \
  --region us-west-2

k get nodes -o wide
k get pods -A
```

EKS add-ons are important because the base control plane alone is not the full production story.
[CoreDNS, kube-proxy, the VPC CNI, the EBS CSI driver](https://docs.aws.amazon.com/eks/latest/userguide/eks-add-ons.html), and the AWS Load Balancer Controller each sit on the boundary between Kubernetes and AWS infrastructure.
When these components are unmanaged, stale, or misconfigured, the cluster can fail in ways that look like Kubernetes problems but are actually integration problems.

```bash
eksctl create addon \
  --cluster dojo-eks-managed \
  --name vpc-cni \
  --version latest

eksctl create addon \
  --cluster dojo-eks-managed \
  --name coredns \
  --version latest

eksctl create addon \
  --cluster dojo-eks-managed \
  --name kube-proxy \
  --version latest

eksctl create addon \
  --cluster dojo-eks-managed \
  --name aws-ebs-csi-driver \
  --version latest
```

The most important EKS identity feature is IAM Roles for Service Accounts, commonly called IRSA.
[IRSA lets a Kubernetes service account exchange its projected token for AWS credentials through an IAM trust relationship](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html).
The result is a pod-level permission boundary that avoids static cloud keys inside containers.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: report-reader
  namespace: finance
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/FinanceReportReader
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: report-reader
  namespace: finance
spec:
  replicas: 2
  selector:
    matchLabels:
      app: report-reader
  template:
    metadata:
      labels:
        app: report-reader
    spec:
      serviceAccountName: report-reader
      containers:
        - name: aws-cli
          image: public.ecr.aws/aws-cli/aws-cli:2.17.0
          command:
            - /bin/sh
            - -c
            - aws s3 ls s3://company-finance-reports && sleep 3600
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 256Mi
```

The teaching point is not the annotation syntax; it is the trust boundary.
If the `finance/report-reader` service account is compromised, the attacker should only receive permissions intended for that workload.
If every workload shares a broad node instance role, one compromised pod can often reach far more AWS resources than the application owner expects.

> **Stop and think:** A team migrates to EKS but leaves all workloads using the node instance profile for AWS access.
> Which security benefit did they fail to capture, and how would that affect your incident response after one pod is compromised?

EKS is usually a good answer when AWS integration is the dominant force.
It is less attractive when teams expect a highly opinionated "everything included" experience out of the box.
The platform team must budget time for add-on management, IAM design, subnet planning, and cost visibility around NAT gateways, load balancers, and cross-zone traffic.

### Google GKE: Kubernetes Maturity With Strong Defaults And Autopilot

GKE is shaped by Google's long history with Kubernetes and container orchestration.
It offers a conventional [Standard mode where you manage node pools, plus Autopilot mode](https://cloud.google.com/kubernetes-engine/docs/concepts/choose-cluster-mode) where Google manages most node-level decisions and charges around requested pod resources.
The important decision is whether your team values node-level control more than reduced operational surface.

```ascii
GKE ARCHITECTURE
────────────────────────────────────────────────────────────────────────────

                         GOOGLE MANAGED CONTROL PLANE
┌──────────────────────────────────────────────────────────────────────────┐
│ ┌──────────────────┐   ┌──────────────────┐   ┌───────────────────────┐ │
│ │ Kubernetes API    │   │ Managed etcd      │   │ Controllers,          │ │
│ │ regional or zonal │   │ and backups       │   │ scheduler, upgrades   │ │
│ └──────────────────┘   └──────────────────┘   └───────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                              CUSTOMER VPC
┌──────────────────────────────────────────────────────────────────────────┐
│ ┌──────────────────────────────┐        ┌──────────────────────────────┐ │
│ │ GKE Standard                  │        │ GKE Autopilot                │ │
│ │ customer-visible node pools   │        │ Google-managed nodes         │ │
│ │ tune machine types and pools  │        │ pay around requested pods     │ │
│ │ more control, more work       │        │ fewer node decisions          │ │
│ └──────────────────────────────┘        └──────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

GKE Standard is the better fit when you need precise control over machine types, node images, DaemonSets, specialized hardware, or cost optimization through committed capacity.
Autopilot is the better fit when teams want a stronger managed experience and can live within its constraints.
The practical question is whether your platform value comes from tuning nodes or from removing node tuning as a developer concern.

A [Standard cluster creation command](https://cloud.google.com/kubernetes-engine/docs/concepts/release-channels) exposes the decisions directly.
The example uses a regional cluster because high availability is a platform concern, not an optional decoration.
It also enables autoscaling and workload identity because those two choices shape day-two operations.

```bash
gcloud container clusters create dojo-gke-standard \
  --region us-central1 \
  --release-channel regular \
  --cluster-version 1.35 \
  --machine-type e2-standard-4 \
  --num-nodes 2 \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 5 \
  --enable-autorepair \
  --enable-autoupgrade \
  --workload-pool "${PROJECT_ID}.svc.id.goog"
```

[Autopilot removes more node management from the platform team](https://cloud.google.com/kubernetes-engine/docs/concepts/autopilot-overview).
That is attractive for teams that have small platform staffs, variable workloads, or internal customers who should not care about VM shapes.
The tradeoff is that [Autopilot enforces guardrails and may reject workloads that assume node-level privileges](https://cloud.google.com/kubernetes-engine/docs/concepts/autopilot-security).

```bash
gcloud container clusters create-auto dojo-gke-autopilot \
  --region us-central1 \
  --release-channel regular
```

Autopilot makes resource requests more important, because [the platform uses them as a scheduling and billing signal](https://cloud.google.com/kubernetes-engine/docs/concepts/autopilot-resource-requests).
A workload with no requests is not merely sloppy; it loses the information Autopilot needs to place and price the pod correctly.
That is why the manifest below treats requests as part of the application contract.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: catalog-api
  namespace: store
spec:
  replicas: 3
  selector:
    matchLabels:
      app: catalog-api
  template:
    metadata:
      labels:
        app: catalog-api
    spec:
      containers:
        - name: catalog-api
          image: nginx:1.27
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: 500m
              memory: 512Mi
            limits:
              cpu: "1"
              memory: 1Gi
```

GKE Workload Identity is the parallel to EKS IRSA.
[A Kubernetes service account is bound to a Google service account](https://cloud.google.com/kubernetes-engine/docs/concepts/workload-identity), and the pod receives cloud access through that binding rather than a static key.
The design goal is the same across providers: make the workload identity specific, auditable, and revocable.

```bash
gcloud iam service-accounts create catalog-reader \
  --display-name "Catalog API object reader"

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member "serviceAccount:catalog-reader@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role "roles/storage.objectViewer"

gcloud iam service-accounts add-iam-policy-binding \
  "catalog-reader@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:${PROJECT_ID}.svc.id.goog[store/catalog-api]"
```

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: catalog-api
  namespace: store
  annotations:
    iam.gke.io/gcp-service-account: catalog-reader@PROJECT_ID.iam.gserviceaccount.com
```

GKE is often a strong default for greenfield Kubernetes teams because the defaults are mature and Autopilot can reduce infrastructure decisions.
It is not automatically the best answer for every company.
If most data and identity are already in AWS or Azure, moving compute to GKE can create avoidable network paths unless there is a clear reason to migrate adjacent services too.

### Azure AKS: Enterprise Integration And Azure-Native Operations

AKS is commonly attractive when the organization already uses Azure networking, Microsoft Entra ID, Azure Policy, Azure Monitor, Key Vault, or Windows container workloads.
Its value is not only the [Kubernetes control plane](https://learn.microsoft.com/en-us/azure/aks/what-is-aks).
Its value is that Kubernetes can become part of an existing enterprise Azure operating model.

```ascii
AKS ARCHITECTURE
────────────────────────────────────────────────────────────────────────────

                         MICROSOFT MANAGED CONTROL PLANE
┌──────────────────────────────────────────────────────────────────────────┐
│ ┌──────────────────┐   ┌──────────────────┐   ┌───────────────────────┐ │
│ │ Kubernetes API    │   │ Managed etcd      │   │ Controllers,          │ │
│ │ Azure integrated  │   │ and lifecycle     │   │ scheduler, upgrades   │ │
│ └──────────────────┘   └──────────────────┘   └───────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                              CUSTOMER VNET
┌──────────────────────────────────────────────────────────────────────────┐
│ ┌──────────────────────┐  ┌──────────────────────┐  ┌─────────────────┐ │
│ │ System node pool      │  │ User node pools       │  │ Virtual nodes   │ │
│ │ required components   │  │ application workloads │  │ burst via ACI   │ │
│ │ keep it boring        │  │ Linux or Windows      │  │ special cases   │ │
│ └──────────────────────┘  └──────────────────────┘  └─────────────────┘ │
│              │                         │                    │            │
│              └──── Azure CNI, managed identity, policy ─────┘            │
└──────────────────────────────────────────────────────────────────────────┘
```

[AKS separates system and user node pools](https://learn.microsoft.com/en-us/azure/aks/use-system-pools), which is a useful operational habit.
System components should not compete with unpredictable application workloads when avoidable.
A platform baseline should keep the system pool stable and use user pools for workload-specific scaling, taints, Windows nodes, GPU nodes, or spot capacity.

The following command creates a learning AKS cluster with managed identity and [Azure CNI](https://learn.microsoft.com/en-us/azure/aks/concepts-network-cni-overview).
A production baseline would normally add private cluster settings, authorized IP ranges if public access remains, policy configuration, and explicit node pool strategy.
The point here is to read the command as a set of operating choices, not a magic incantation.

```bash
az group create \
  --name dojo-aks-rg \
  --location eastus

az aks create \
  --resource-group dojo-aks-rg \
  --name dojo-aks-managed \
  --kubernetes-version 1.35 \
  --node-count 3 \
  --node-vm-size Standard_D4s_v5 \
  --network-plugin azure \
  --enable-managed-identity \
  --enable-addons monitoring \
  --generate-ssh-keys
```

```bash
az aks get-credentials \
  --resource-group dojo-aks-rg \
  --name dojo-aks-managed

k get nodes -o wide
k get pods -A
```

[AKS Workload Identity uses an OIDC issuer and federated credentials](https://learn.microsoft.com/en-us/azure/aks/workload-identity-overview) so pods can access Azure resources through managed identity.
Again, the provider syntax differs but the platform principle is the same.
A pod should receive the narrow cloud permissions needed for its job, not inherit broad node or cluster permissions.

```bash
az aks update \
  --resource-group dojo-aks-rg \
  --name dojo-aks-managed \
  --enable-oidc-issuer \
  --enable-workload-identity

az identity create \
  --name catalog-reader-identity \
  --resource-group dojo-aks-rg

CLIENT_ID=$(az identity show \
  --name catalog-reader-identity \
  --resource-group dojo-aks-rg \
  --query clientId \
  --output tsv)

OIDC_ISSUER=$(az aks show \
  --resource-group dojo-aks-rg \
  --name dojo-aks-managed \
  --query oidcIssuerProfile.issuerUrl \
  --output tsv)
```

```bash
az identity federated-credential create \
  --name catalog-api-federation \
  --identity-name catalog-reader-identity \
  --resource-group dojo-aks-rg \
  --issuer "${OIDC_ISSUER}" \
  --subject system:serviceaccount:store:catalog-api \
  --audience api://AzureADTokenExchange
```

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: catalog-api
  namespace: store
  annotations:
    azure.workload.identity/client-id: CLIENT_ID
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: catalog-api
  namespace: store
spec:
  replicas: 3
  selector:
    matchLabels:
      app: catalog-api
  template:
    metadata:
      labels:
        app: catalog-api
        azure.workload.identity/use: "true"
    spec:
      serviceAccountName: catalog-api
      containers:
        - name: azure-cli
          image: mcr.microsoft.com/azure-cli:2.63.0
          command:
            - /bin/sh
            - -c
            - az storage account list --output table && sleep 3600
          resources:
            requests:
              cpu: 100m
              memory: 256Mi
            limits:
              cpu: 500m
              memory: 512Mi
```

AKS deserves special attention when Windows containers are not a side case.
[Kubernetes can run Windows workloads](https://learn.microsoft.com/en-us/azure/aks/windows-containerd) on other providers too, but Azure's enterprise estate, identity integration, and Windows operational familiarity often make AKS easier for organizations already invested in Microsoft platforms.
The right question is not "can the provider run Windows" but "which provider makes Windows operations supportable for this team."

> **Pause and predict:** Your security team requires Microsoft Entra-based access review for cluster administrators, but your application data lives in AWS RDS.
> Would AKS automatically be the right answer, or would you first compare identity integration value against cross-cloud data path cost?

AKS is usually strongest when Azure is already the enterprise control plane.
It is weaker when the cluster would constantly reach into another provider for databases, queues, object storage, or analytics without private connectivity and clear incident ownership.
As with EKS and GKE, the best answer depends on where the surrounding system already lives.

### Side-By-Side Comparison With The Right Caution

Feature comparisons are useful when they help you ask better questions.
They are harmful when they imply that every row has equal weight for every organization.
A Windows support row may decide the whole platform for one company and be irrelevant for another.

| Dimension | EKS | GKE | AKS |
|-----------|-----|-----|-----|
| Best-fit cloud gravity | AWS services, IAM, VPC, RDS, S3, SQS, MSK | Google Cloud services, strong Kubernetes defaults, BigQuery, GCS | Azure services, Entra ID, Azure Policy, Windows, enterprise networking |
| Common operating mode | Managed node groups plus provider add-ons | Standard node pools or Autopilot | System and user node pools with Azure integrations |
| Serverless or reduced-node mode | EKS Fargate for selected pod profiles | GKE Autopilot for broad node abstraction | Virtual nodes and Azure Container Instances for burst patterns |
| Identity pattern | IRSA or newer pod identity patterns using AWS IAM | Workload Identity with Google service accounts | Workload Identity with managed identities and federation |
| Networking personality | VPC CNI integrates pods with AWS VPC addressing | Mature GKE networking with strong defaults | Azure CNI and VNET integration for enterprise Azure networks |
| Upgrade posture | Explicit planning with managed options and add-on awareness | Release channels and strong auto-management options | Azure-driven upgrade paths with enterprise governance integration |
| Main hidden cost risk | NAT gateways, load balancers, cross-zone traffic, many clusters | Autopilot requests, logging volume, network transfer, premium features | Load balancers, logging, public IPs, node pools, paid support or SLA tiers |
| Main design risk | Underestimating AWS integration assembly work | Assuming Autopilot allows every node-level pattern | Treating Azure enterprise integration as a substitute for workload design |

A simple provider rule can guide early conversations.
Choose EKS when AWS data gravity and IAM integration dominate.
Choose GKE when Kubernetes operational maturity, strong defaults, or Autopilot-style abstraction dominate.
Choose AKS when Azure enterprise integration, Entra governance, or Windows operational fit dominates.

That rule is intentionally incomplete.
It gives you a starting hypothesis, not a final answer.
The final answer comes from the workload profile, risk model, cost model, and migration plan.

---

## Core Section 4: The Shared Design Surfaces That Decide Success

Provider choice matters, but the same design surfaces appear in every managed Kubernetes project.
The cluster must have a network boundary, an identity boundary, a node lifecycle plan, an upgrade plan, an observability path, and a cost feedback loop.
If any of those are missing, the platform is not production-ready even when the cluster was created successfully.

### Networking: Private By Default, Explicit Where Public Is Needed

Managed cluster networking has two different questions.
First, who can reach the Kubernetes API server.
Second, how do workloads reach each other, cloud services, and the internet.
Teams often focus on the second question and forget that API server exposure is itself a security decision.

```ascii
NETWORKING QUESTIONS FOR EVERY MANAGED CLUSTER
────────────────────────────────────────────────────────────────────────────

                  ┌──────────────────────────────┐
                  │ Kubernetes API endpoint       │
                  │ public, private, or restricted│
                  └──────────────┬───────────────┘
                                 │
                                 ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│ Pod-to-pod traffic   │   │ Pod-to-cloud traffic │   │ Internet ingress     │
│ CNI, policies, mesh  │   │ private endpoints    │   │ LB, Ingress, Gateway │
└─────────────────────┘   └─────────────────────┘   └─────────────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────┐
                  │ Cost and evidence             │
                  │ egress, NAT, logs, flow data   │
                  └──────────────────────────────┘
```

A private cluster is not automatically secure, and a public endpoint is not automatically irresponsible.
The point is that access should be intentional.
A platform team should be able to explain which networks can reach the API, how administrators authenticate, how CI/CD deploys, and how emergency access is audited.

Network policy is another area where managed services do not remove design work.
Kubernetes Services make communication easy; they do not decide whether communication is allowed.
If [every namespace can reach every other namespace by default](https://kubernetes.io/docs/concepts/services-networking/network-policies/), a compromised workload may move laterally even though the control plane itself is provider-managed.

A minimal network policy example helps make the idea concrete.
The policy below allows the `web` namespace to call the `catalog-api` pods on port 80 while denying unrelated callers if the namespace has default-deny policy in place.
It is provider-neutral Kubernetes, but each managed service may use a different implementation path under the hood.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-web-to-catalog
  namespace: store
spec:
  podSelector:
    matchLabels:
      app: catalog-api
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              purpose: web
      ports:
        - protocol: TCP
          port: 80
```

The debugging habit is to follow the path in layers.
If DNS fails, check CoreDNS and service discovery.
If DNS works but connection fails, check network policy, security groups or NSGs, route tables, and service endpoints.
If connection works but authorization fails, move from networking to identity and application permissions.

```bash
k run netcheck \
  --image=curlimages/curl:8.9.1 \
  --restart=Never \
  --rm \
  -it \
  -- curl -v http://catalog-api.store.svc.cluster.local
```

### Identity: Workload Identity Is The Managed Kubernetes Security Line

Workload identity is the difference between "pods can access cloud APIs" and "this specific workload can access this specific cloud API for this specific reason."
Every major managed provider has a mechanism for this.
The names differ, but the platform principle does not.

| Provider | Kubernetes Object | Cloud Identity Object | Trust Mechanism | Main Review Question |
|----------|-------------------|-----------------------|-----------------|----------------------|
| EKS | ServiceAccount | IAM role | OIDC federation through IRSA or pod identity | Does this service account map to one narrow AWS role? |
| GKE | ServiceAccount | Google service account | Workload Identity federation | Does this namespace and service account need this IAM role? |
| AKS | ServiceAccount | Managed identity | Federated credential through OIDC issuer | Can this pod use only the Azure permissions it needs? |

The wrong pattern is to put cloud credentials in a Kubernetes Secret and call the problem solved.
That moves the risk into [etcd](https://kubernetes.io/docs/concepts/configuration/secret/), CI/CD logs, secret syncing tools, and developer laptops.
Managed workload identity exists so that credentials can be short-lived, scoped, auditable, and revoked through the cloud provider's IAM system.

A good platform baseline makes static cloud keys an exception.
Exceptions may exist for legacy software, but they should have expiration dates and migration owners.
Without that pressure, teams keep the weakest identity pattern because it works everywhere and requires the least initial thought.

### Node Lifecycle: Standard Pools, Spot Capacity, And Serverless Modes

Managed Kubernetes still needs capacity planning.
Nodes may be provider-managed, but workload scheduling remains your problem.
[Requests, limits](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/), affinity, topology spread, taints, tolerations, and disruption budgets determine whether the cluster behaves well during deploys, upgrades, and traffic spikes.

```ascii
NODE OPERATING MODES
────────────────────────────────────────────────────────────────────────────

┌──────────────────────┐   ┌──────────────────────┐   ┌──────────────────────┐
│ Standard node pools   │   │ Spot or preemptible   │   │ Serverless/autopilot │
│ predictable capacity  │   │ cheap interruptible   │   │ less node ownership  │
│ best for steady load  │   │ best for batch jobs   │   │ best for bursty apps │
└──────────────────────┘   └──────────────────────┘   └──────────────────────┘
          │                           │                           │
          ▼                           ▼                           ▼
 reserve and tune             tolerate interruption          define requests well
```

Standard node pools are usually best for stable production services with predictable resource usage.
They allow committed-use discounts, reserved instances, custom machine types, and detailed scheduling control.
They also require the platform team to care about node image updates, drain behavior, and capacity fragmentation.

Spot or preemptible capacity is useful for workloads that can be interrupted safely.
Batch jobs, stateless workers with queues, and noncritical environments are common fits.
The platform must enforce disruption handling because cheap capacity becomes expensive if interrupted work corrupts state or pages humans.

Serverless or autopilot-style modes reduce node management, but they do not remove workload engineering.
Pods still need requests, health checks, disruption budgets, and clear startup behavior.
These modes often punish sloppy resource declarations because the scheduler and bill both depend on declared intent.

The manifest below shows a portable baseline for a stateless application.
It is not provider-specific, which is the point.
Good Kubernetes workload hygiene travels across EKS, GKE, and AKS.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: checkout-api
  namespace: store
spec:
  replicas: 4
  selector:
    matchLabels:
      app: checkout-api
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  template:
    metadata:
      labels:
        app: checkout-api
    spec:
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: ScheduleAnyway
          labelSelector:
            matchLabels:
              app: checkout-api
      containers:
        - name: checkout-api
          image: nginx:1.27
          ports:
            - containerPort: 80
          readinessProbe:
            httpGet:
              path: /
              port: 80
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /
              port: 80
            periodSeconds: 20
          resources:
            requests:
              cpu: 250m
              memory: 256Mi
            limits:
              cpu: 1
              memory: 768Mi
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: checkout-api
  namespace: store
spec:
  minAvailable: 3
  selector:
    matchLabels:
      app: checkout-api
```

> **Stop and think:** If the cluster autoscaler cannot add a node because the cloud account reached a regional quota, would you classify that as a Kubernetes failure, a cloud capacity failure, or a platform governance failure?
> The most useful answer is often "all three layers interact," which changes who needs to join the incident bridge.

### Upgrades: Managed Does Not Mean Surprise-Free

Managed providers offer version channels, patch automation, and control-plane upgrade paths.
That is valuable, but it can create a false sense of safety.
The provider can upgrade Kubernetes; it cannot guarantee that every deprecated API, webhook, controller, or fragile workload in your cluster will behave correctly afterward.

A responsible upgrade process starts before the provider announces a deadline.
The platform team should scan for deprecated APIs, test critical workloads in a staging cluster, verify add-on compatibility, review disruption budgets, and communicate maintenance windows.
The provider's upgrade mechanism is the final step, not the whole process.

```bash
k get apiservices
k get validatingwebhookconfigurations
k get mutatingwebhookconfigurations
k get pdb -A
k get deployments -A -o wide
```

The most common upgrade mistake is ignoring admission webhooks.
[A failing webhook can block pod creation, deployment rollouts, or controller reconciliation](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/) after an upgrade.
Managed Kubernetes keeps the API server alive, but your webhooks can still turn a healthy API into a cluster that rejects the work your teams need to do.

### Observability: Provider Dashboards Are A Starting Point

EKS, GKE, and AKS all integrate with native logging and monitoring tools.
Those integrations are helpful, but they are not a replacement for platform-level SLOs.
A dashboard that shows node CPU does not tell you whether developers can deploy or whether customers can complete checkout.

A managed Kubernetes observability baseline should include API server availability, admission latency, pod scheduling latency, node readiness, cluster autoscaler decisions, DNS error rate, ingress error rate, and cloud API throttling.
Those signals cross the provider and Kubernetes boundary.
They are the difference between "the cluster is up" and "the platform is usable."

| Signal | Why It Matters | First Place To Look |
|--------|----------------|--------------------|
| API server latency | Slow API calls break deploys and controllers | Provider control plane metrics and client-side errors |
| Pending pods | Capacity, quota, taints, or scheduling constraints may block work | `k describe pod`, autoscaler logs, cloud quotas |
| DNS failures | Service discovery failure looks like app failure | CoreDNS logs, node networking, network policy |
| Load balancer provisioning delay | Cloud integration may be throttled or misconfigured | Service events and provider load balancer controller logs |
| Workload identity errors | Pods may run but fail cloud API calls | ServiceAccount annotations, IAM bindings, token audience |
| Upgrade blocks | Deprecated APIs and webhooks can break rollout | API deprecation scans and webhook health |

A strong platform team turns these signals into runbooks.
The runbook should not say "check Kubernetes."
It should say which command narrows the failure, which provider console shows the matching cloud-side evidence, and who owns the next action.
This reduces the time spent arguing whether the problem is "Kubernetes" or "cloud."

---

## Core Section 5: Cost, Multi-Cloud, And The Senior-Level Tradeoff

Cost in managed Kubernetes is rarely just the [control plane line item](https://aws.amazon.com/eks/pricing/).
The [control plane](https://azure.microsoft.com/en-us/pricing/details/kubernetes-service/) may be visible because it is easy to count, but worker compute, network transfer, NAT, load balancers, logging, storage, support, and engineering time usually dominate.
A senior platform engineer models the whole system before declaring a provider cheaper.

```ascii
MANAGED KUBERNETES COST STACK
────────────────────────────────────────────────────────────────────────────

┌──────────────────────────────────────────────────────────────────────────┐
│ Engineering time: upgrades, incidents, platform support, migration        │
├──────────────────────────────────────────────────────────────────────────┤
│ Observability: logs, metrics, traces, retention, and query volume         │
├──────────────────────────────────────────────────────────────────────────┤
│ Network: cross-zone, cross-region, internet egress, NAT, private links    │
├──────────────────────────────────────────────────────────────────────────┤
│ Runtime: VMs, spot capacity, GPUs, serverless pods, reservations          │
├──────────────────────────────────────────────────────────────────────────┤
│ Cluster: control plane fee, paid SLA tier, management fee, support plan   │
└──────────────────────────────────────────────────────────────────────────┘
```

A common mistake is to compare three tiny clusters and extrapolate to production.
That hides the real drivers.
A chatty service mesh can turn cross-zone traffic into a major bill.
A logging agent can send high-cardinality debug logs into expensive retention.
A [serverless pod mode](https://cloud.google.com/kubernetes-engine/pricing) can save operations time while costing more for steady workloads with predictable utilization.

The example below is deliberately approximate and should be replaced with current provider pricing before a real purchasing decision.
Its purpose is to show the model, not to freeze a price sheet in curriculum.
The exact numbers change, but the categories and tradeoffs remain stable.

| Monthly Cost Category | EKS-Style Cluster | GKE-Style Cluster | AKS-Style Cluster | What To Validate Before Deciding |
|-----------------------|------------------:|------------------:|------------------:|----------------------------------|
| Cluster management or SLA | provider-specific | provider-specific | provider-specific | Current region pricing, free-tier rules, and paid SLA needs |
| Worker compute | workload-dependent | workload-dependent | workload-dependent | VM family, reservations, spot use, and autoscaling behavior |
| Load balancers and ingress | traffic-dependent | traffic-dependent | traffic-dependent | Internal versus public services and Gateway or Ingress design |
| Network transfer | often decisive | often decisive | often decisive | Cross-zone, NAT, internet, and inter-cloud traffic patterns |
| Storage | workload-dependent | workload-dependent | workload-dependent | Block, file, object, snapshots, and backup retention |
| Observability | usage-dependent | usage-dependent | usage-dependent | Log volume, metrics cardinality, trace sampling, retention |
| Migration and training | one-time but real | one-time but real | one-time but real | Terraform, CI/CD, IAM, runbooks, and team familiarity |

Multi-cloud Kubernetes is the advanced version of this cost conversation.
It can reduce specific costs or satisfy regulatory constraints, but it also multiplies platform surfaces.
Every additional provider adds identity patterns, networking paths, billing models, support processes, quota systems, and failure modes.

A realistic multi-cloud decision starts with the reason.
If European customers require data processing in a region where Azure contracts and controls are already approved, AKS may be justified for that slice.
If public API traffic has a better economics and CDN path through Google Cloud, GKE may be justified for edge-facing services.
If data systems remain in AWS, EKS may remain the right home for data-adjacent workloads.

```ascii
WORKLOAD PLACEMENT BY BUSINESS REASON
────────────────────────────────────────────────────────────────────────────

┌──────────────────────────────────────────────────────────────────────────┐
│ EKS: data-adjacent services                                              │
│ Reason: existing AWS databases, queues, IAM roles, and private networking │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ asynchronous events or replicated data
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ GKE: public API and web edge                                             │
│ Reason: strong managed defaults, traffic pattern, and platform simplicity │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ regulated regional workflow
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ AKS: enterprise and regional compliance workloads                         │
│ Reason: Entra governance, Azure Policy, Windows support, approved regions │
└──────────────────────────────────────────────────────────────────────────┘
```

The architecture above is not a recommendation for everyone.
It is a demonstration of matching workload slices to provider strengths.
A team that copies it without the same business reasons inherits complexity without the payoff.

The multi-cloud anti-pattern is pretending that Kubernetes makes clouds interchangeable.
Kubernetes standardizes deployment primitives, not every surrounding service.
Object storage permissions, private networking, load balancer behavior, DNS, managed databases, and observability all remain provider-shaped.

A better goal is portability with intentional anchoring.
Portable manifests, Helm charts, GitOps workflows, and policy-as-code can reduce switching cost.
Intentional anchoring accepts that a workload may be deeply tied to one provider because the surrounding services create real value.
The platform decision should name both: what is portable, and what is deliberately provider-native.

### Worked Example: Writing A Provider Decision Record

A decision record makes the tradeoff reviewable.
It does not need to be a novel, but it should connect evidence to a decision.
The following worked example shows how a senior platform engineer might document a choice for a mid-sized SaaS company.

```text
Decision: Use EKS managed node groups for the first production managed Kubernetes platform.

Context:
The production database, object storage, message queues, and existing Terraform modules are already in AWS.
The platform team can operate node pools but does not want to own etcd, API server upgrades, or control-plane availability.
The security team requires pod-level cloud permissions and auditable access paths.

Options considered:
1. EKS with managed node groups.
2. GKE Autopilot with cross-cloud access to AWS data services.
3. AKS with Microsoft Entra integration and cross-cloud access to AWS data services.

Decision:
Choose EKS for the first production platform because AWS data gravity and existing delivery automation dominate.
Use IRSA for workload identity, private subnets for nodes, restricted API endpoint access, managed add-ons, and a documented upgrade window.

Consequences:
The platform keeps AWS-native integration and minimizes migration risk.
The team accepts EKS-specific add-on management and must model NAT, load balancer, and cross-zone traffic costs.
GKE and AKS remain future options if analytics or enterprise identity requirements become dominant enough to justify migration.
```

This record is strong because it says why the losing options lost.
It does not claim GKE or AKS are worse products.
It explains that, for this context, their benefits did not outweigh the cost of moving compute away from AWS data gravity.

> **Pause and predict:** If this company later adopts BigQuery as its primary analytics system and the exporter becomes its largest workload, which part of the decision record would you revisit first?
> The correct move is not to rewrite history; it is to use the recorded reversal criteria to decide whether a new workload slice deserves a different platform.

A decision record should be paired with an operating baseline.
The baseline is where the platform team turns the choice into repeatable defaults.
Without it, every application team becomes a cluster designer, and managed Kubernetes becomes another source of inconsistency.

| Baseline Area | Default For Production | Exception Process |
|---------------|------------------------|-------------------|
| API access | Private endpoint or tightly restricted public endpoint | Security review with time-bound approval |
| Workload identity | Provider-native workload identity for all cloud API access | Legacy key exception with migration owner |
| Node pools | Managed node pools or Autopilot-style mode with documented sizing | Custom nodes reviewed by platform team |
| Ingress | Standard Gateway or Ingress class with TLS automation | Direct load balancer only when justified |
| Network policy | Namespace default-deny plus approved service paths | Temporary broad access with expiry |
| Upgrades | Staging validation before production minor upgrades | Emergency patch process for critical fixes |
| Cost controls | Labels, budgets, quota alerts, and owner metadata | Budget owner approval for high-cost workloads |

The final senior-level skill is knowing when not to use managed Kubernetes at all.
If workloads run at disconnected edge locations, require custom kernels, need air-gapped operation, or must comply with a requirement that forbids provider-operated control planes, self-managed Kubernetes may still be appropriate.
Managed Kubernetes is the default for many cloud workloads, not a universal law.

---

## Did You Know?

1. **Managed Kubernetes still requires a platform owner.** Providers can keep the control plane available, but they do not design namespace boundaries, approve cloud permissions, tune workload requests, or decide which teams may expose public services.
2. **Autopilot and serverless pod modes shift the cost signal toward declared resources.** A pod with inflated CPU and memory requests can become expensive even if its actual utilization is low, which makes resource hygiene part of financial governance.
3. **Workload identity is one of the biggest security wins in managed Kubernetes.** It replaces long-lived cloud keys in pods with scoped, auditable, short-lived credentials issued through provider-managed identity systems.
4. **Multi-cloud Kubernetes reduces some risks while creating others.** It can solve data residency, acquisition, or pricing problems, but it also adds identity, networking, billing, observability, and incident coordination surfaces.

---

## Common Mistakes

| Mistake | Why It Hurts | Better Approach |
|---------|--------------|-----------------|
| Choosing a provider from a feature checklist alone | Equal-weight checklists hide the workload constraints that actually decide success | Start with workload profile, data gravity, identity model, traffic pattern, and team maturity |
| Treating managed Kubernetes as fully outsourced operations | The provider manages the control plane, but workload reliability and exposure remain customer-owned | Write a responsibility boundary and runbook for every production cluster |
| Leaving pods on broad node-level cloud permissions | A single compromised pod may inherit permissions unrelated to its job | Use IRSA, GKE Workload Identity, or AKS Workload Identity with narrow roles |
| Ignoring network transfer during provider selection | Cross-zone, NAT, inter-region, and inter-cloud traffic can dominate the bill | Model real traffic paths before choosing provider or multi-cloud placement |
| Using Autopilot or serverless mode without resource discipline | Bad requests and limits become both scheduling problems and billing problems | Require requests, limits, probes, and workload reviews before production deployment |
| Running public cluster endpoints by habit | Administrative APIs become exposed beyond the intended operator path | Prefer private endpoints or tightly restricted access with audited break-glass procedures |
| Upgrading only the control plane in the plan | Deprecated APIs, webhooks, add-ons, and workloads can fail even when the provider upgrade succeeds | Test staging clusters, scan API usage, validate add-ons, and communicate disruption windows |
| Starting multi-cloud without a business reason | Teams inherit duplicated tooling and unclear incident ownership without enough payoff | Use multi-cloud only for named drivers such as data residency, acquisition, or measurable cost reduction |

---

## Quiz

### Question 1

Your company already runs PostgreSQL, object storage, and queues in AWS. A team proposes GKE Autopilot because they like the reduced node management model. The application is latency-sensitive and makes frequent database calls. How should you evaluate the proposal before approving it?

<details>
<summary>Show Answer</summary>

Start by mapping the runtime path, not by comparing product preference. Frequent calls from GKE to AWS databases would introduce cross-cloud latency, private connectivity design, egress cost, and incident ownership complexity. GKE Autopilot may still be attractive if the team is also moving the data layer or if the operational savings clearly outweigh the network cost, but the proposal is incomplete until it models data gravity, traffic volume, private connectivity, and rollback strategy. A likely recommendation is EKS for the latency-sensitive data-adjacent workload, with GKE reconsidered for workloads that do not depend heavily on AWS services.
</details>

### Question 2

A development team migrated to EKS and stored AWS access keys in Kubernetes Secrets because "the cluster is managed now." During a security review, you find that several namespaces can read those Secrets. What should you change, and why?

<details>
<summary>Show Answer</summary>

Replace static AWS keys with workload identity, such as IRSA or the current EKS pod identity pattern used by your platform. Each workload should use a dedicated Kubernetes service account mapped to a narrow IAM role. This reduces blast radius because a compromised pod receives only the permissions intended for that service account, and credentials are short-lived rather than copied into Secrets. You should also review namespace RBAC, rotate the exposed keys, and add policy that prevents new static cloud credentials from being introduced without an exception.
</details>

### Question 3

A team wants GKE Autopilot for a service that runs a privileged DaemonSet for host-level packet capture on every node. The service is used only during rare debugging sessions. What design response should you give?

<details>
<summary>Show Answer</summary>

GKE Autopilot is probably the wrong fit for that specific requirement because it intentionally limits node-level access and privileged host patterns. You should separate the need from the proposed platform: the team needs occasional packet capture, not necessarily Autopilot. Options include using GKE Standard for the debugging environment, using provider-native flow logs and managed network telemetry, or creating a controlled break-glass diagnostic path. The answer should preserve Autopilot for workloads that fit its constraints while refusing to force a host-level tool into a mode designed to remove host ownership.
</details>

### Question 4

An enterprise already uses Microsoft Entra ID, Azure Policy, Azure Monitor, and Windows-based internal applications. A new platform team is choosing a managed Kubernetes provider for mixed Linux and Windows workloads. Which provider would you recommend first, and what evidence would still need validation?

<details>
<summary>Show Answer</summary>

AKS is the first provider to evaluate seriously because the surrounding enterprise operating model is already Azure-centered and Windows support is likely easier to govern there. The recommendation is not automatic, though. You still need to validate where the application data lives, whether Azure regions meet latency and compliance needs, how Windows node pools will be patched, what the cost looks like under expected traffic, and whether workload identity satisfies the security model. A strong answer names AKS as the leading candidate while requiring workload and cost evidence before final approval.
</details>

### Question 5

A platform team enabled automatic control-plane upgrades on a managed cluster. After the upgrade, new Deployments hang because an admission webhook no longer responds correctly. The provider status page shows the control plane as healthy. How do you debug and explain the incident?

<details>
<summary>Show Answer</summary>

Debug this common managed-cluster failure by separating the provider-managed control plane from the customer-managed nodes and components. The API server can be healthy while a customer-installed admission webhook blocks object creation. Start by checking events, webhook configurations, webhook pod readiness, service endpoints, and logs for the webhook backing service. Then review whether the webhook version was tested against the new Kubernetes minor version. The incident explanation should say that the managed upgrade succeeded at the control-plane layer, but the platform's upgrade process failed to validate customer-owned admission components.
</details>

### Question 6

A finance team asks why the managed Kubernetes bill increased after moving a steady production workload from standard node pools to a serverless or Autopilot-style mode. The application traffic did not grow. What do you investigate?

<details>
<summary>Show Answer</summary>

Investigate requested CPU and memory, replica counts, minimum billing behavior, logging volume, and whether the workload is steady enough that reserved or committed node capacity would be cheaper. Autopilot-style modes often reduce operations work, but they may cost more for predictable workloads with inflated resource requests. The right response is not simply to roll back; compare the value of reduced node management against the increased runtime cost, then right-size requests or move only steady workloads back to standard pools if the economics justify it.
</details>

### Question 7

A company wants one cluster in each major cloud "for portability." There is no data residency requirement, no acquisition constraint, and no measured provider-specific cost advantage. What should your architecture review say?

<details>
<summary>Show Answer</summary>

The review should challenge the decision because portability alone does not justify three operating surfaces. Kubernetes standardizes part of deployment, but identity, networking, storage, load balancing, observability, quotas, support, and billing remain provider-specific. A better design is to build portable delivery practices first, such as GitOps, policy-as-code, container standards, and provider-neutral workload manifests where practical. Multi-cloud should wait until there is a named business driver that outweighs the complexity tax.
</details>

### Question 8

Your AKS cluster has a system node pool and a user node pool. Application pods are scheduled onto the system pool during a traffic spike, and platform components become unstable. What should you change?

<details>
<summary>Show Answer</summary>

Protect the system pool by using taints, tolerations, labels, and scheduling policy so ordinary application pods land on user pools. Then size the system pool for platform components and create user pools that match workload needs, such as Linux, Windows, GPU, spot, or high-memory nodes. The issue is not that AKS has system pools; the issue is that the platform did not enforce the boundary. Verification should include checking pod placement, node taints, tolerations, and autoscaler behavior during a controlled load test.
</details>

---

## Hands-On Exercise

### Task: Build A Managed Kubernetes Provider Decision Record

You do not need three paid cloud accounts to complete the main learning objective of this module.
The exercise asks you to evaluate a workload, create a local decision record, and run provider-neutral Kubernetes checks against any available cluster.
If you have access to EKS, GKE, or AKS, you can optionally create a short-lived test cluster, but the required outcome is the architecture decision and the verification habit.

### Scenario

You are the platform engineer for a company called Northwind Payments.
The company runs a checkout API, a fraud scoring worker, and a reporting exporter.
The checkout database is in AWS RDS, the fraud team uses Python batch jobs with bursty CPU needs, the reporting team is considering BigQuery, and the enterprise security team uses Microsoft Entra ID for workforce access reviews.

Your CTO asks for a recommendation by the end of the week.
They do not want a generic product comparison.
They want a decision that says which managed Kubernetes provider should host the first production platform, which operating mode should be used, what risks remain, and what evidence would cause the team to revisit the decision.

### Step 1: Write The Workload Profile

Create a file named `managed-kubernetes-decision.md` in your notes or working directory.
Fill in the following template with concrete statements rather than single-word answers.
The quality of the recommendation depends on how honestly you describe the workload.

```markdown
# Managed Kubernetes Decision Record: Northwind Payments

## Workload Profile

Business criticality:
- Checkout API is revenue-critical and must remain available during promotions.
- Fraud scoring is important but can tolerate queued retries.
- Reporting exporter is batch-oriented and can move on a schedule.

Runtime pattern:
- Checkout API is steady with predictable peaks.
- Fraud scoring is bursty and CPU-heavy.
- Reporting exporter moves large datasets daily.

Data gravity:
- Checkout database currently lives in AWS RDS.
- Queueing and object storage are currently in AWS.
- Reporting may move toward BigQuery, but that migration is not complete.

Identity boundary:
- Workloads need cloud access to databases, queues, object storage, and possibly analytics.
- Workforce access reviews are standardized through Microsoft Entra ID.

Network boundary:
- Checkout API is public through a controlled ingress path.
- Database traffic should remain private and low-latency.
- Reporting traffic volume must be cost-modeled.

Operations model:
- Platform team can operate node pools but does not want to run control planes.
- Application teams expect a paved road for deployment and cloud permissions.

Cost driver:
- Checkout cost is likely compute plus database adjacency.
- Fraud cost is burst CPU.
- Reporting cost may become data transfer or analytics platform cost.
```

### Step 2: Score The Provider Options

Use the matrix below and assign `Strong`, `Medium`, or `Weak` for each provider.
Do not score based on preference.
Score based on the scenario evidence.

| Factor | EKS | GKE | AKS | Evidence You Used |
|--------|-----|-----|-----|-------------------|
| Current data gravity |  |  |  |  |
| Workforce identity fit |  |  |  |  |
| Bursty compute fit |  |  |  |  |
| Reporting future fit |  |  |  |  |
| Migration effort |  |  |  |  |
| Team familiarity |  |  |  |  |
| Cost uncertainty |  |  |  |  |
| Security model clarity |  |  |  |  |

A strong answer will probably discover that no provider wins every row.
That is normal.
The goal is to make the tradeoff explicit enough that leaders understand what they are accepting.

### Step 3: Recommend The First Production Platform

Write a recommendation in this format.
You may choose any provider if your reasoning is coherent, but you must name the losing options and the reversal criteria.
A recommendation that says "EKS because AWS" without tradeoff analysis is incomplete.

```markdown
## Recommendation

Recommended first production platform:
- Provider:
- Operating mode:
- Initial region strategy:
- Node strategy:
- Workload identity strategy:
- Network exposure strategy:

Why this option wins:
- 

Why the alternatives did not win:
- GKE:
- AKS:

Risks we accept:
- 

Reversal criteria:
- 
```

### Step 4: Create A Portable Workload Baseline

Apply the following namespace and workload to any Kubernetes cluster you can safely use.
This can be a local kind cluster, an existing sandbox managed cluster, or a short-lived cloud test cluster.
The goal is to verify portable workload hygiene before provider-specific integration.

```bash
kubectl create namespace store
kubectl label namespace store purpose=web
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: checkout-api
  namespace: store
spec:
  replicas: 3
  selector:
    matchLabels:
      app: checkout-api
  template:
    metadata:
      labels:
        app: checkout-api
    spec:
      containers:
        - name: checkout-api
          image: nginx:1.27
          ports:
            - containerPort: 80
          readinessProbe:
            httpGet:
              path: /
              port: 80
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /
              port: 80
            periodSeconds: 20
          resources:
            requests:
              cpu: 200m
              memory: 256Mi
            limits:
              cpu: 750m
              memory: 512Mi
---
apiVersion: v1
kind: Service
metadata:
  name: checkout-api
  namespace: store
spec:
  selector:
    app: checkout-api
  ports:
    - name: http
      port: 80
      targetPort: 80
```

Save the manifest as `checkout-api.yaml`, then apply and verify it.
If you use a managed cluster, confirm that you are not creating an external load balancer unless you intend to pay for it.
The Service above is intentionally internal by default.

```bash
kubectl apply -f checkout-api.yaml
k get deploy,svc,pods -n store
k describe deploy checkout-api -n store
```

### Step 5: Add Disruption And Network Intent

Add a PodDisruptionBudget and a basic NetworkPolicy.
The disruption budget teaches upgrade readiness, while the policy teaches that managed Kubernetes still needs explicit service boundaries.
If your cluster does not enforce NetworkPolicy, document that as a platform gap rather than silently ignoring it.

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: checkout-api
  namespace: store
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: checkout-api
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-store-namespace
  namespace: store
spec:
  podSelector:
    matchLabels:
      app: checkout-api
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              purpose: web
      ports:
        - protocol: TCP
          port: 80
```

```bash
kubectl apply -f checkout-api-policy.yaml
k get pdb,networkpolicy -n store
k describe pdb checkout-api -n store
```

### Step 6: Optional Provider Creation Commands

Use these commands only in a sandbox account with budget alerts and cleanup discipline.
They are included so you can compare the provider experience, not because the exercise requires spending money.
Always check current provider pricing and supported Kubernetes versions before creating real clusters.

```bash
eksctl create cluster \
  --name dojo-eks-compare \
  --region us-west-2 \
  --version 1.35 \
  --nodegroup-name general-workers \
  --node-type m6i.large \
  --nodes 2 \
  --nodes-min 1 \
  --nodes-max 4 \
  --managed
```

```bash
gcloud container clusters create-auto dojo-gke-compare \
  --region us-central1 \
  --release-channel regular
```

```bash
az group create \
  --name dojo-aks-compare-rg \
  --location eastus

az aks create \
  --resource-group dojo-aks-compare-rg \
  --name dojo-aks-compare \
  --kubernetes-version 1.35 \
  --node-count 2 \
  --node-vm-size Standard_D4s_v5 \
  --network-plugin azure \
  --enable-managed-identity \
  --generate-ssh-keys
```

### Step 7: Compare The Operational Experience

Fill in this table after either reading the provider commands carefully or running a short-lived test.
The answers should describe operational consequences, not just whether a command succeeded.
For example, "GKE Autopilot did not require node sizing" is more useful than "easy."

| Aspect | EKS Notes | GKE Notes | AKS Notes |
|--------|-----------|-----------|-----------|
| Cluster creation decisions |  |  |  |
| Node ownership model |  |  |  |
| Workload identity setup |  |  |  |
| Private networking choices |  |  |  |
| Upgrade planning needs |  |  |  |
| Cost questions to validate |  |  |  |
| Best-fit workload slice |  |  |  |
| Main risk to mitigate |  |  |  |

### Step 8: Cleanup

If you created real cloud clusters, delete them before ending the exercise.
A managed cluster that was useful for an hour can become an avoidable bill if it stays alive for a weekend.
Cleanup is part of production discipline, not an afterthought.

```bash
eksctl delete cluster \
  --name dojo-eks-compare \
  --region us-west-2
```

```bash
gcloud container clusters delete dojo-gke-compare \
  --region us-central1 \
  --quiet
```

```bash
az group delete \
  --name dojo-aks-compare-rg \
  --yes
```

### Success Criteria

- [ ] You completed a workload profile that names business criticality, runtime pattern, data gravity, identity boundary, network boundary, operating model, and cost driver.
- [ ] You scored EKS, GKE, and AKS against scenario evidence rather than personal preference or a single pricing claim.
- [ ] You wrote a recommendation that names the chosen provider, operating mode, identity strategy, node strategy, and network exposure strategy.
- [ ] You documented why the losing providers did not win for this scenario, without claiming they are inferior in every context.
- [ ] You named at least two reversal criteria that would cause the team to revisit the provider decision later.
- [ ] You applied or reviewed a portable Kubernetes workload baseline with requests, limits, probes, Service, PodDisruptionBudget, and NetworkPolicy.
- [ ] You verified the workload with `k get`, `k describe`, and a clear explanation of what each result proves.
- [ ] If you created cloud resources, you deleted them and recorded which cleanup commands were run.

### Reflection Prompt

After completing the exercise, write three sentences that you could say in an architecture review.
The first sentence should state your recommendation.
The second sentence should state the most important tradeoff.
The third sentence should state the condition that would make you revisit the decision.
If you cannot write those sentences clearly, your decision record still needs work.

---

## Next Module

Next up: [Module 14.7: RKE2](../module-14.7-rke2/) — enterprise-hardened Kubernetes with CIS profiles and embedded container runtime.

## Sources

- [docs.aws.amazon.com: what is eks.html](https://docs.aws.amazon.com/eks/latest/userguide/what-is-eks.html) — The Amazon EKS overview directly describes EKS as managed Kubernetes and states that AWS manages the control plane.
- [docs.aws.amazon.com: managed node groups.html](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html) — The EKS managed node groups page directly states that managed node groups automate node provisioning and lifecycle management.
- [docs.aws.amazon.com: fargate profile.html](https://docs.aws.amazon.com/eks/latest/userguide/fargate-profile.html) — The EKS Fargate profile documentation explains that selectors determine which pods run on Fargate.
- [docs.aws.amazon.com: eks add ons.html](https://docs.aws.amazon.com/eks/latest/userguide/eks-add-ons.html) — The Amazon EKS add-ons page lists the named add-ons and their management model.
- [docs.aws.amazon.com: managing vpc cni.html](https://docs.aws.amazon.com/eks/latest/userguide/managing-vpc-cni.html) — The EKS VPC CNI documentation directly states that the add-on assigns private IPv4 or IPv6 addresses from the VPC to pods.
- [docs.aws.amazon.com: iam roles for service accounts.html](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html) — The EKS IRSA page describes associating IAM roles with Kubernetes service accounts through OIDC instead of distributing AWS credentials.
- [cloud.google.com: choose cluster mode](https://cloud.google.com/kubernetes-engine/docs/concepts/choose-cluster-mode) — The GKE mode-selection page explains Standard and Autopilot operation modes and their tradeoffs.
- [cloud.google.com: autopilot overview](https://cloud.google.com/kubernetes-engine/docs/concepts/autopilot-overview) — The Autopilot overview states that Google manages worker nodes and node lifecycle tasks.
- [cloud.google.com: autopilot resource requests](https://cloud.google.com/kubernetes-engine/docs/concepts/autopilot-resource-requests) — The Autopilot resource requests page explains how Autopilot uses and adjusts pod resource requests, including billing-model implications.
- [cloud.google.com: workload identity](https://cloud.google.com/kubernetes-engine/docs/concepts/workload-identity) — The GKE Workload Identity Federation page directly describes keyless access and fine-grained identity for workloads.
- [cloud.google.com: autopilot security](https://cloud.google.com/kubernetes-engine/docs/concepts/autopilot-security) — The Autopilot security page documents restrictions on privileged containers, host namespaces, host networking, and node-level access.
- [cloud.google.com: release channels](https://cloud.google.com/kubernetes-engine/docs/concepts/release-channels) — The GKE release channels documentation explains channel-based version and upgrade management.
- [learn.microsoft.com: what is aks](https://learn.microsoft.com/en-us/azure/aks/what-is-aks) — The AKS overview states that Azure automatically creates and manages the AKS control plane.
- [learn.microsoft.com: use system pools](https://learn.microsoft.com/en-us/azure/aks/use-system-pools) — The AKS system node pools page directly defines system and user node pool purposes.
- [learn.microsoft.com: workload identity overview](https://learn.microsoft.com/en-us/azure/aks/workload-identity-overview) — The AKS Workload Identity overview directly describes service account token projection, OIDC federation, and managed identity integration.
- [learn.microsoft.com: virtual nodes](https://learn.microsoft.com/en-us/azure/aks/virtual-nodes) — The AKS virtual nodes page directly explains the Azure Container Instances integration.
- [learn.microsoft.com: windows containerd](https://learn.microsoft.com/en-us/azure/aks/windows-containerd) — The AKS Windows Server node pool documentation directly covers creating Windows Server node pools for containers.
- [learn.microsoft.com: concepts network cni overview](https://learn.microsoft.com/en-us/azure/aks/concepts-network-cni-overview) — The AKS CNI overview describes CNI plugins, pod IP assignment, routing, and virtual network connectivity.
- [kubernetes.io: network policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/) — The Kubernetes NetworkPolicy documentation directly states plugin enforcement requirements and allow-rule behavior.
- [kubernetes.io: manage resources containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/) — The Kubernetes resource management page directly describes scheduler use of requests and limit enforcement.
- [kubernetes.io: disruptions](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/) — The Kubernetes disruptions page documents PDB behavior, voluntary disruptions, drains, and upgrade-related disruption handling.
- [kubernetes.io: extensible admission controllers](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/) — The dynamic admission control documentation explains validating webhooks, request rejection, and failurePolicy behavior.
- [kubernetes.io: deprecation guide](https://kubernetes.io/docs/reference/using-api/deprecation-guide/) — The Kubernetes deprecated API migration guide is the primary source for API removals and migration requirements across releases.
- [kubernetes.io: secret](https://kubernetes.io/docs/concepts/configuration/secret/) — The Kubernetes Secrets page directly states where Secrets are stored and discusses default at-rest exposure.
- [aws.amazon.com: pricing](https://aws.amazon.com/eks/pricing/) — The Amazon EKS pricing page directly describes per-cluster pricing and separate charges for worker-node resources and related AWS infrastructure.
- [cloud.google.com: pricing](https://cloud.google.com/kubernetes-engine/pricing) — The GKE pricing page directly covers cluster management fees, compute resources, operation modes, and ingress fees.
- [azure.microsoft.com: kubernetes service](https://azure.microsoft.com/en-us/pricing/details/kubernetes-service/) — The AKS pricing page directly describes control-plane tiers and compute pricing.
