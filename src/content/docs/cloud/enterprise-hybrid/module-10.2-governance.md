---
title: "Module 10.2: Cloud Governance & Policy as Code"
slug: cloud/enterprise-hybrid/module-10.2-governance
sidebar:
  order: 3
---
**Complexity**: [COMPLEX] | **Time to Complete**: 2.5h | **Prerequisites**: Enterprise Landing Zones (Module 10.1), Kubernetes RBAC basics, YAML/JSON fundamentals

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Implement policy-as-code using OPA Gatekeeper, Kyverno, and cloud-native policy engines for Kubernetes governance**
- **Configure cloud governance frameworks (AWS Config Rules, Azure Policy, GCP Organization Policies) for Kubernetes infrastructure**
- **Design tag-based governance strategies that enforce cost allocation, ownership, and compliance across clusters**
- **Deploy automated remediation workflows that detect and correct governance violations without human intervention**

---

## Why This Module Matters

In September 2022, a mid-size e-commerce company experienced a data breach that exposed 2.3 million customer records. The root cause was embarrassingly simple: a developer created an S3 bucket with public read access to store product images, then accidentally uploaded a database export to the same bucket. The company had an AWS SCP that was supposed to prevent public S3 buckets, but it had been written eighteen months earlier and only covered the `s3:PutBucketAcl` action -- it did not account for the newer `s3:PutBucketPublicAccessBlock` API. Meanwhile, their EKS clusters had no admission control at all. Kubernetes Services of type LoadBalancer were routinely creating internet-facing ALBs without any review, and environment variables in pod specs regularly contained plaintext database credentials.

The investigation revealed a pattern that is alarmingly common: the cloud governance team and the Kubernetes platform team operated in completely separate silos. The SCP team did not know what Kyverno was. The platform team did not know what SCPs were. There was no unified view of "what policies exist" or "are we compliant" across the stack. The breach cost the company $4.2 million in regulatory fines, notification costs, and lost customer trust.

Policy as Code solves this problem by treating governance rules the same way you treat application code: version-controlled, tested, peer-reviewed, and automatically enforced. In this module, you will learn how cloud provider policy systems work (SCPs, Azure Policy, GCP Org Policies), how Kubernetes policy engines (Kyverno, OPA Gatekeeper) complement them, how to build a unified governance model that covers the entire stack, and how to manage exceptions without creating security holes.

---

## The Policy Pyramid

Governance in a cloud-native enterprise is not a single layer. It is a pyramid with each layer handling different concerns at different points in the resource lifecycle.

```text
┌─────────────────────────────────────────────────┐
│                                                   │
│          Layer 5: RUNTIME DETECTION               │
│          Falco, KubeArmor, GuardDuty             │
│          "Is something bad happening NOW?"         │
│                                                   │
│       ┌──────────────────────────────────┐        │
│       │   Layer 4: K8s ADMISSION CONTROL │        │
│       │   Kyverno, OPA Gatekeeper        │        │
│       │   "Should this K8s resource be   │        │
│       │    created?"                      │        │
│       └──────────────────────────────────┘        │
│                                                   │
│    ┌───────────────────────────────────────┐      │
│    │   Layer 3: IaC VALIDATION             │      │
│    │   Checkov, tfsec, OPA/Conftest        │      │
│    │   "Is the Terraform/Bicep correct     │      │
│    │    before we apply it?"               │      │
│    └───────────────────────────────────────┘      │
│                                                   │
│  ┌──────────────────────────────────────────┐     │
│  │   Layer 2: CLOUD PROVIDER POLICIES        │     │
│  │   SCPs, Azure Policy, GCP Org Policies    │     │
│  │   "What API calls are allowed?"           │     │
│  └──────────────────────────────────────────┘     │
│                                                   │
│  ┌──────────────────────────────────────────┐     │
│  │   Layer 1: IDENTITY & ACCESS (IAM)        │     │
│  │   "Who can do what?"                      │     │
│  └──────────────────────────────────────────┘     │
│                                                   │
└─────────────────────────────────────────────────┘
```

Each layer catches things the layer below cannot. IAM controls who can call APIs, but it cannot enforce that every S3 bucket has encryption. SCPs can enforce encryption, but they cannot inspect Kubernetes manifests. Admission control can reject bad manifests, but it cannot stop a running container from spawning a reverse shell. Runtime detection catches that.

---

## Cloud Provider Policy Systems

### AWS Service Control Policies (SCPs)

SCPs are the top-level preventive control in AWS Organizations. They define the maximum permissions available to any principal in an account. Think of them as a ceiling -- even if an IAM policy grants `s3:*`, an SCP that denies `s3:DeleteBucket` wins.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyUnapprovedRegions",
      "Effect": "Deny",
      "Action": "*",
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:RequestedRegion": [
            "us-east-1",
            "us-west-2",
            "eu-west-1"
          ]
        },
        "ForAllValues:StringNotLike": {
          "aws:PrincipalArn": [
            "arn:aws:iam::*:role/OrganizationAdmin"
          ]
        }
      }
    },
    {
      "Sid": "DenyPublicEKS",
      "Effect": "Deny",
      "Action": [
        "eks:CreateCluster",
        "eks:UpdateClusterConfig"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "eks:endpointPublicAccess": "true"
        }
      }
    },
    {
      "Sid": "RequireIMDSv2",
      "Effect": "Deny",
      "Action": "ec2:RunInstances",
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "StringNotEquals": {
          "ec2:MetadataHttpTokens": "required"
        }
      }
    },
    {
      "Sid": "DenyLeaveOrganization",
      "Effect": "Deny",
      "Action": "organizations:LeaveOrganization",
      "Resource": "*"
    }
  ]
}
```

**SCP gotchas** that trip up most teams:

- SCPs do not grant permissions, they only restrict. An SCP that allows `s3:*` does not give anyone S3 access -- it just does not restrict it.
- SCPs do not apply to the management account. This is by design but is a common blindspot.
- SCPs have a 5,120 character limit per policy. Complex organizations often hit this and need to split policies across multiple SCPs.
- SCPs are evaluated with an implicit deny. If an action is not explicitly allowed by an SCP in the path from root to account, it is denied.

### Azure Policy

Azure Policy takes a different approach: instead of simple allow/deny, it supports multiple **effects** that determine what happens when a resource violates the policy.

```json
{
  "properties": {
    "displayName": "AKS clusters must use Azure CNI with network policy",
    "policyType": "Custom",
    "mode": "Indexed",
    "description": "Ensures all AKS clusters use Azure CNI networking with Calico or Azure network policy enabled.",
    "parameters": {},
    "policyRule": {
      "if": {
        "allOf": [
          {
            "field": "type",
            "equals": "Microsoft.ContainerService/managedClusters"
          },
          {
            "anyOf": [
              {
                "field": "Microsoft.ContainerService/managedClusters/networkProfile.networkPlugin",
                "notEquals": "azure"
              },
              {
                "field": "Microsoft.ContainerService/managedClusters/networkProfile.networkPolicy",
                "exists": "false"
              }
            ]
          }
        ]
      },
      "then": {
        "effect": "Deny"
      }
    }
  }
}
```

Azure Policy effects:

| Effect | Behavior | Use Case |
| :--- | :--- | :--- |
| `Deny` | Block resource creation/update | Preventive: enforce hard requirements |
| `Audit` | Allow but log non-compliance | Detective: visibility without blocking |
| `DeployIfNotExists` | Auto-remediate by deploying a resource | Enforce logging, diagnostics, extensions |
| `Modify` | Alter resource properties during creation | Add tags, enable encryption automatically |
| `Disabled` | Policy exists but is not enforced | Testing or temporary exception |
| `DenyAction` | Block specific actions on existing resources | Prevent deletion of critical resources |

The `DeployIfNotExists` effect is particularly powerful for Kubernetes. You can create a policy that automatically installs Azure Policy for AKS (which runs OPA Gatekeeper inside the cluster) whenever an AKS cluster is created:

```json
{
  "if": {
    "field": "type",
    "equals": "Microsoft.ContainerService/managedClusters"
  },
  "then": {
    "effect": "DeployIfNotExists",
    "details": {
      "type": "Microsoft.ContainerService/managedClusters/extensions",
      "name": "microsoft-azure-policy",
      "existenceCondition": {
        "field": "Microsoft.ContainerService/managedClusters/extensions/extensionType",
        "equals": "microsoft.policyinsights"
      },
      "deployment": {
        "properties": {
          "mode": "incremental",
          "template": {
            "resources": [
              {
                "type": "Microsoft.ContainerService/managedClusters/extensions",
                "apiVersion": "2023-05-01",
                "name": "[concat(field('name'), '/microsoft-azure-policy')]",
                "properties": {
                  "extensionType": "microsoft.policyinsights",
                  "autoUpgradeMinorVersion": true
                }
              }
            ]
          }
        }
      }
    }
  }
}
```

### GCP Organization Policies

GCP Organization Policies use **constraints** -- predefined or custom rules that restrict resource configurations across the organization hierarchy.

```yaml
# Deny public GKE clusters
constraint: constraints/container.restrictPublicCluster
listPolicy:
  allValues: DENY

---
# Restrict which regions can host GKE clusters
constraint: constraints/gcp.resourceLocations
listPolicy:
  allowedValues:
    - us-central1
    - us-east4
    - europe-west1

---
# Require Shielded GKE Nodes
constraint: constraints/container.requireShieldedNodes
booleanPolicy:
  enforced: true
```

GCP also supports **custom organization policy constraints** using Common Expression Language (CEL):

```yaml
# Custom constraint: GKE clusters must have Binary Authorization enabled
apiVersion: orgpolicy.googleapis.com/v2
kind: CustomConstraint
metadata:
  name: custom.gkeRequireBinaryAuthorization
spec:
  resourceTypes:
    - container.googleapis.com/Cluster
  condition: >
    resource.binaryAuthorization.evaluationMode == "PROJECT_SINGLETON_POLICY_ENFORCE"
  actionType: DENY
  displayName: "GKE clusters must enable Binary Authorization"
  description: "All GKE clusters must have Binary Authorization enabled to enforce container image signing."
```

---

## Kubernetes Policy Engines: Kyverno vs OPA Gatekeeper

Cloud provider policies stop at the cloud API boundary. Once a Kubernetes cluster exists, you need an in-cluster policy engine to govern what gets deployed inside it.

### Kyverno

Kyverno uses Kubernetes-native YAML to define policies. If you can write a Kubernetes manifest, you can write a Kyverno policy. This is its primary advantage: the learning curve is minimal for teams already fluent in YAML.

```yaml
# Kyverno: Deny containers running as root
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: deny-run-as-root
  annotations:
    policies.kyverno.io/title: Deny Running as Root
    policies.kyverno.io/severity: high
spec:
  validationFailureAction: Enforce
  background: true
  rules:
    - name: check-run-as-non-root
      match:
        any:
          - resources:
              kinds:
                - Pod
      validate:
        message: >
          Running as root is not allowed. Set
          spec.securityContext.runAsNonRoot to true or
          spec.containers[*].securityContext.runAsNonRoot to true.
        pattern:
          spec:
            =(initContainers):
              - securityContext:
                  runAsNonRoot: true
            containers:
              - securityContext:
                  runAsNonRoot: true
---
# Kyverno: Mutate to add default resource limits
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: add-default-resources
spec:
  rules:
    - name: add-default-limits
      match:
        any:
          - resources:
              kinds:
                - Pod
      mutate:
        patchStrategicMerge:
          spec:
            containers:
              - (name): "*"
                resources:
                  limits:
                    +(memory): "256Mi"
                    +(cpu): "200m"
                  requests:
                    +(memory): "128Mi"
                    +(cpu): "100m"
---
# Kyverno: Generate NetworkPolicy for every new namespace
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: generate-default-networkpolicy
spec:
  rules:
    - name: default-deny-ingress
      match:
        any:
          - resources:
              kinds:
                - Namespace
      exclude:
        any:
          - resources:
              namespaces:
                - kube-system
                - kube-public
      generate:
        apiVersion: networking.k8s.io/v1
        kind: NetworkPolicy
        name: default-deny-ingress
        namespace: "{{request.object.metadata.name}}"
        synchronize: true
        data:
          spec:
            podSelector: {}
            policyTypes:
              - Ingress
```

### OPA Gatekeeper

Gatekeeper uses Rego, a purpose-built policy language from Open Policy Agent. Rego is more powerful than YAML patterns but has a steeper learning curve. Gatekeeper separates the policy **template** (the logic) from the **constraint** (the configuration).

```yaml
# Gatekeeper: ConstraintTemplate (the logic)
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8sdenypublicloadbalancer
spec:
  crd:
    spec:
      names:
        kind: K8sDenyPublicLoadBalancer
      validation:
        openAPIV3Schema:
          type: object
          properties:
            allowedNamespaces:
              type: array
              items:
                type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8sdenypublicloadbalancer

        violation[{"msg": msg}] {
          input.review.object.kind == "Service"
          input.review.object.spec.type == "LoadBalancer"
          not input.review.object.metadata.annotations["service.beta.kubernetes.io/aws-load-balancer-internal"]
          namespace := input.review.object.metadata.namespace
          not namespace_allowed(namespace)
          msg := sprintf("Public LoadBalancer services are not allowed in namespace '%v'. Add annotation 'service.beta.kubernetes.io/aws-load-balancer-internal: true' or use an allowed namespace.", [namespace])
        }

        namespace_allowed(namespace) {
          allowed := input.parameters.allowedNamespaces[_]
          namespace == allowed
        }
---
# Gatekeeper: Constraint (the configuration)
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sDenyPublicLoadBalancer
metadata:
  name: deny-public-lb-except-ingress
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Service"]
  parameters:
    allowedNamespaces:
      - ingress-nginx
      - istio-system
```

### Kyverno vs Gatekeeper Decision Matrix

| Feature | Kyverno | OPA Gatekeeper |
| :--- | :--- | :--- |
| **Policy language** | Kubernetes-native YAML | Rego (purpose-built) |
| **Learning curve** | Low (YAML knowledge sufficient) | High (Rego is a new language) |
| **Validation** | Yes | Yes |
| **Mutation** | Yes (native) | Yes (external data, more complex) |
| **Generation** | Yes (create resources from policies) | No |
| **Image verification** | Yes (cosign, Notary) | Via external data |
| **Background scanning** | Yes (audit existing resources) | Yes (audit existing resources) |
| **Policy exceptions** | PolicyException resource | Config constraint match exclusions |
| **Multi-tenancy** | Namespace-scoped policies | Namespace-scoped constraints |
| **CNCF status** | Incubating | Graduated (via OPA) |
| **Best for** | Teams wanting simplicity and mutation/generation | Teams needing complex logic or already using OPA |

---

## Mapping Cloud Policies to Kubernetes Policies

The real power of Policy as Code comes from creating a unified governance model where cloud policies and Kubernetes policies reinforce each other. Here is a mapping of common enterprise requirements across both layers:

| Requirement | Cloud Policy | Kubernetes Policy |
| :--- | :--- | :--- |
| No public endpoints | SCP: deny public EKS/AKS/GKE | Kyverno: deny Service type LoadBalancer without internal annotation |
| Encryption at rest | SCP: deny unencrypted EBS/disks | Kyverno: require encrypted StorageClass |
| Image provenance | ECR/ACR/Artifact Registry policies | Kyverno: verify image signatures (cosign) |
| Resource tagging | SCP: deny untagged resources | Kyverno: require labels matching cloud tags |
| Network segmentation | SCP: deny public subnets in EKS VPCs | Kyverno: generate NetworkPolicy on namespace creation |
| Least privilege | IAM: minimal role permissions | Kyverno: deny privileged containers, deny hostNetwork |
| Logging | SCP: require CloudTrail/audit logs | Kyverno: require sidecar logging or FluentBit DaemonSet |
| Cost control | AWS Budgets / Azure Cost Alerts | Kyverno: enforce resource limits, deny unrestricted replicas |

### Example: Unified Policy for Image Provenance

This is how a single governance requirement ("all container images must be signed") spans both cloud and Kubernetes layers:

```bash
# Layer 1 (Cloud): ECR repository policy requiring signed images
aws ecr put-lifecycle-policy --repository-name my-app \
  --lifecycle-policy-text '{
    "rules": [{
      "rulePriority": 1,
      "description": "Keep only signed images",
      "selection": {
        "tagStatus": "tagged",
        "tagPrefixList": ["v"],
        "countType": "imageCountMoreThan",
        "countNumber": 50
      },
      "action": { "type": "expire" }
    }]
  }'
```

```yaml
# Layer 2 (Kubernetes): Kyverno policy verifying cosign signatures
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signatures
spec:
  validationFailureAction: Enforce
  webhookTimeoutSeconds: 30
  rules:
    - name: verify-cosign-signature
      match:
        any:
          - resources:
              kinds:
                - Pod
      verifyImages:
        - imageReferences:
            - "123456789012.dkr.ecr.*.amazonaws.com/*"
          attestors:
            - entries:
                - keyless:
                    subject: "https://github.com/my-org/*"
                    issuer: "https://token.actions.githubusercontent.com"
                    rekor:
                      url: "https://rekor.sigstore.dev"
          mutateDigest: true
          verifyDigest: true
```

---

## Exception Management

Every governance system needs a way to handle legitimate exceptions. The question is whether exceptions are managed through bureaucratic approval processes or through code.

### The Exception Anti-Pattern

```text
BAD: Exception via email
  1. Developer emails security team: "I need public LB for 2 weeks"
  2. Security team discusses in Slack
  3. Someone says "ok" in a thread
  4. Developer manually edits the policy
  5. Exception is never removed
  6. 18 months later, auditor finds 200 "temporary" exceptions
```

### The Policy Exception Pattern

```yaml
# Kyverno PolicyException (the right way)
apiVersion: kyverno.io/v2beta1
kind: PolicyException
metadata:
  name: allow-public-lb-for-demo
  namespace: demo-team
  labels:
    exception-owner: security-team
    exception-ticket: SEC-4521
    exception-expires: "2025-04-15"
spec:
  exceptions:
    - policyName: deny-public-loadbalancer
      ruleNames:
        - check-internal-annotation
  match:
    any:
      - resources:
          kinds:
            - Service
          namespaces:
            - demo-team
          names:
            - demo-frontend-svc
  conditions:
    any:
      - key: "{{request.object.metadata.annotations.exception-approved-by}}"
        operator: Equals
        value: "security-team"
```

```bash
# Automated exception lifecycle with expiry checking
cat <<'SCRIPT' > /tmp/check-expired-exceptions.sh
#!/bin/bash
# Run this in CI/CD or as a CronJob
TODAY=$(date +%Y-%m-%d)

kubectl get policyexception -A -o json | jq -r \
  '.items[] |
   select(.metadata.labels."exception-expires" != null) |
   select(.metadata.labels."exception-expires" < "'$TODAY'") |
   "\(.metadata.namespace)/\(.metadata.name) expired on \(.metadata.labels."exception-expires")"'
SCRIPT
```

### Shift-Left: Catching Policy Violations Before Deployment

The most effective governance catches violations as early as possible -- ideally before the code leaves the developer's machine.

```text
┌──────────────────────────────────────────────────────────┐
│  SHIFT-LEFT POLICY ENFORCEMENT PIPELINE                    │
│                                                            │
│  Local Dev     ──►  CI Pipeline  ──►  Admission   ──►     │
│  (pre-commit)       (PR checks)      (runtime)            │
│                                                            │
│  kyverno-cli        kyverno-cli     Kyverno webhook       │
│  conftest           checkov          Gatekeeper            │
│  kubeconform        tfsec            webhook               │
│                     OPA/Conftest                           │
│                                                            │
│  Cost: $0           Cost: $0        Cost: Blocked          │
│  (instant fix)      (PR feedback)   deployment             │
└──────────────────────────────────────────────────────────┘
```

```bash
# Pre-commit hook: validate K8s manifests against Kyverno policies
# .pre-commit-config.yaml entry:
# - repo: local
#   hooks:
#     - id: kyverno-validate
#       name: Kyverno Policy Check
#       entry: bash -c 'kyverno apply policies/ --resource $@' --
#       files: '\.ya?ml$'

# CI pipeline step: validate with kyverno-cli
kyverno apply policies/ \
  --resource deployment.yaml \
  --policy-report \
  --output /tmp/policy-report.json

# Check the report
cat /tmp/policy-report.json | jq '.summary'
# { "pass": 12, "fail": 0, "warn": 2, "error": 0 }

# CI pipeline step: validate Terraform with Checkov
checkov -d ./terraform \
  --framework terraform \
  --check CKV_AWS_39,CKV_AWS_58,CKV_AWS_337 \
  --output json

# CI pipeline step: validate with Conftest (OPA for config files)
conftest test deployment.yaml \
  --policy ./opa-policies/ \
  --output json
```

---

## Did You Know?

1. AWS SCPs were originally limited to 2,048 characters when launched in 2017. Enterprise customers hit this limit so frequently that AWS increased it to 5,120 characters in 2019. Even at 5,120 characters, complex organizations regularly hit the ceiling and must split single logical policies across multiple SCP documents. Azure Policy has no such character limit, which is one reason Azure policies tend to be more detailed than AWS SCPs.

2. OPA (Open Policy Agent) evaluates over 10 billion policy decisions per day across its production deployments globally. Netflix alone processes over 500 million OPA decisions daily for API authorization. The Rego language was designed specifically because existing policy languages (like AWS IAM JSON) could not express complex cross-resource relationships needed for modern authorization.

3. Kyverno was created in 2019 by Nirmata specifically because OPA Gatekeeper's Rego language was a barrier to adoption for Kubernetes platform teams. In a 2024 CNCF survey, 58% of organizations using Kubernetes policy engines chose Kyverno, compared to 34% for OPA Gatekeeper. The most commonly cited reason was "we already know YAML."

4. The concept of "Policy as Code" was formalized by HashiCorp's Sentinel in 2017, but the practice dates back to SELinux mandatory access control policies in the early 2000s. The key innovation was not writing policies in code (that was always possible) but treating policies with the same software engineering practices as application code: version control, testing, peer review, and continuous deployment.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| **Cloud policies and K8s policies designed in silos** | Different teams own each layer. Cloud team does not understand K8s. Platform team does not understand SCPs. | Create a unified governance council. Map every compliance requirement across both layers. Use the mapping table approach from this module. |
| **Audit-only policies that never become enforced** | Teams set policies to "audit" mode for testing and never flip to "enforce" because they fear breaking things. | Set a timeline: 30 days audit, then enforce. Use CI/CD policy validation (shift-left) to catch violations before they hit the cluster. |
| **Exception without expiry** | Rushed exception granted to unblock a release. No one tracks the cleanup. | Every exception must have a ticket number, an owner, and an expiry date. Automate expiry checking with a CronJob or CI pipeline. |
| **Over-relying on cloud policies, ignoring K8s** | "Our SCPs are comprehensive, we do not need Kyverno." But SCPs cannot see inside a Kubernetes cluster. | Cloud policies protect cloud resources. K8s policies protect workloads. You need both. A public LoadBalancer can bypass cloud firewall rules entirely. |
| **Writing Rego when YAML would suffice** | Engineering team defaults to Gatekeeper because "OPA is the standard." But their policies are simple pattern matching. | Evaluate both Kyverno and Gatekeeper honestly. If your policies are mostly "require label X" or "deny privilege Y," Kyverno is simpler. Use Gatekeeper when you need cross-resource logic. |
| **Not testing policies before deployment** | Policy deployed directly to production cluster. A mutation policy with a typo adds invalid annotations to every pod. Cluster-wide outage. | Always test policies in a staging cluster first. Use `kyverno apply` or `gator test` in CI. Run in audit mode before enforce mode. |
| **SCP character limit workarounds using wildcards** | SCP too long, so engineer replaces specific actions with `*` wildcards. This makes the policy either too permissive or too restrictive. | Split complex SCPs into multiple policies. Use condition keys instead of action lists where possible. AWS allows up to 5 SCPs per OU. |
| **Forgetting the management account** | SCPs do not apply to the management account. Critical governance gaps exist there. | Use the management account only for Organizations management. Move all workloads to member accounts. Apply detective controls (Config rules, GuardDuty) to the management account separately. |

---

## Quiz

<details>
<summary>Question 1: An AWS SCP denies all actions in region ap-southeast-1. A developer assumes an IAM role that has full S3 access (s3:*) and tries to create a bucket in ap-southeast-1. What happens and why?</summary>

The request is **denied**. SCPs define the maximum available permissions for all principals in an account. Even though the IAM policy grants `s3:*`, the SCP creates a ceiling that blocks all actions in ap-southeast-1. The effective permissions are the intersection of the IAM policy and all SCPs in the path from the organization root to the account. SCPs do not grant permissions -- they only restrict them. This is a fundamental difference from IAM policies and is the reason SCPs are so effective as guardrails: no one in the account, regardless of their IAM permissions, can bypass the SCP.
</details>

<details>
<summary>Question 2: Your company uses Azure Policy with a "Deny" effect to prevent AKS clusters without network policy enabled. A team creates an AKS cluster via Terraform and the deployment fails. They request an exception. How should you handle this?</summary>

Create a **policy exemption** in Azure Policy using the `Microsoft.Authorization/policyExemptions` resource. Azure Policy supports two exemption categories: `Waiver` (the resource is non-compliant but exempted) and `Mitigated` (the requirement is met through other means). The exemption should be scoped to the specific resource, have an expiration date, and reference a tracking ticket. In code:

```json
{
  "properties": {
    "policyAssignmentId": "/providers/Microsoft.Management/managementGroups/.../providers/Microsoft.Authorization/policyAssignments/...",
    "exemptionCategory": "Waiver",
    "expiresOn": "2025-06-15T00:00:00Z",
    "description": "Temporary: team-beta needs kubenet for legacy migration. Ticket: SEC-2341"
  }
}
```

Never disable the entire policy. Scope exceptions to the narrowest possible resource.
</details>

<details>
<summary>Question 3: Explain the difference between Kyverno's "validate", "mutate", and "generate" rule types. Give one example of when you would use each.</summary>

**Validate** checks whether a resource meets criteria and blocks it if not. Example: require all pods to have `runAsNonRoot: true`. **Mutate** modifies a resource during admission, adding or changing fields. Example: automatically inject a sidecar container or add default resource limits to pods that lack them. **Generate** creates a new resource when a triggering resource is created. Example: automatically create a NetworkPolicy with default-deny-ingress whenever a new namespace is created. Validate is the most common (enforcement), mutate reduces developer burden (sane defaults), and generate ensures baseline configuration (consistency). An enterprise typically uses all three: generate for namespace baselines, mutate for defaults, and validate for hard security requirements.
</details>

<details>
<summary>Question 4: Your CI pipeline uses Checkov to validate Terraform and kyverno-cli to validate Kubernetes manifests. A developer's PR passes both checks, but the deployment is still rejected by the Kyverno webhook in the cluster. How is this possible?</summary>

Several scenarios can cause this: (1) The cluster has **newer policies** that the CI pipeline does not have. The pipeline validates against a snapshot of policies, but someone added a new policy to the cluster after the CI policy set was last updated. (2) The Kyverno webhook evaluates the **final rendered resource**, which may differ from the manifest file. Helm templating, Kustomize overlays, or ArgoCD sync might modify the manifest between CI validation and cluster admission. (3) The policy uses **external data** (like ConfigMap references or API calls) that produce different results in the cluster than in CI. The fix is to keep CI policy sets in sync with cluster policies via GitOps, and to validate the fully-rendered manifests (post-Helm, post-Kustomize), not the source templates.
</details>

<details>
<summary>Question 5: An organization has 300 Kubernetes clusters across 3 cloud providers. They want a single policy set that works everywhere. Should they use Kyverno or OPA Gatekeeper? Justify your answer.</summary>

For **pure Kubernetes policy**, either can work since both run as admission webhooks and are cloud-agnostic. However, if the goal is a single policy language across the entire stack (cloud resources + Kubernetes + CI/CD + API authorization), **OPA Gatekeeper** has an advantage because Rego policies can be reused with standalone OPA for Terraform validation (Conftest), API authorization, and custom services. Kyverno is Kubernetes-specific -- it cannot validate Terraform or authorize API calls. That said, at 300 clusters, operational simplicity matters enormously. Kyverno's YAML-based policies are easier for platform teams to maintain across a large fleet without deep Rego expertise. The pragmatic choice for most organizations: Kyverno for Kubernetes admission control, Conftest/OPA for IaC validation, and a mapping document that ensures both policy sets enforce the same governance requirements.
</details>

<details>
<summary>Question 6: What happens if a Kyverno mutation policy and a validation policy conflict? For example, the mutation policy adds a label, but the validation policy requires a different value for that label.</summary>

Kyverno processes **mutations before validations** in a deterministic order. If a mutation policy adds label `env: default` and a validation policy requires `env` to match the namespace annotation `environment`, the validation will fail because the mutated value does not match. This is a policy design bug, not a Kyverno bug. The fix is to ensure mutation and validation policies are designed as a coherent set. Best practice: the mutation policy should read the desired value from context (like namespace labels) rather than hardcoding. Use `kyverno apply` in CI to test the full pipeline (mutation + validation) together against sample resources to catch these conflicts before deployment.
</details>

---

## Hands-On Exercise: Build a Unified Cloud + K8s Governance Pipeline

In this exercise, you will create a multi-layer governance system that validates both infrastructure code and Kubernetes manifests, implements shift-left policy checking, and manages exceptions properly.

**What you will build:**

```text
┌──────────────────────────────────────────────────────┐
│  Governance Pipeline                                   │
│                                                        │
│  1. Pre-commit: validate YAML with kubeconform         │
│  2. CI: check manifests against Kyverno policies       │
│  3. CI: check Terraform against OPA/Conftest           │
│  4. Cluster: enforce with Kyverno admission webhook    │
│  5. Audit: scan existing resources for compliance      │
│  6. Exception: managed PolicyException with expiry     │
└──────────────────────────────────────────────────────┘
```

### Task 1: Set Up the Policy Test Environment

Create a kind cluster and install Kyverno for admission control.

<details>
<summary>Solution</summary>

```bash
# Create the governance lab cluster
kind create cluster --name governance-lab

# Install Kyverno
helm repo add kyverno https://kyverno.github.io/kyverno/
helm repo update
helm install kyverno kyverno/kyverno -n kyverno --create-namespace --wait

# Verify Kyverno is running
k get pods -n kyverno
```

</details>

### Task 2: Create a Comprehensive Policy Set

Deploy a set of enterprise policies that cover security, cost, and operational concerns.

<details>
<summary>Solution</summary>

```bash
cat <<'EOF' | k apply -f -
# Policy 1: Deny privileged containers
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: deny-privileged
spec:
  validationFailureAction: Enforce
  rules:
    - name: deny-privileged-containers
      match:
        any:
          - resources:
              kinds:
                - Pod
      exclude:
        any:
          - resources:
              namespaces:
                - kube-system
                - kyverno
      validate:
        message: "Privileged containers are denied by governance policy GOV-001."
        pattern:
          spec:
            containers:
              - securityContext:
                  privileged: "!true"
---
# Policy 2: Require resource limits
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-resource-limits
spec:
  validationFailureAction: Enforce
  rules:
    - name: check-limits
      match:
        any:
          - resources:
              kinds:
                - Pod
      exclude:
        any:
          - resources:
              namespaces:
                - kube-system
                - kyverno
      validate:
        message: "All containers must have CPU and memory limits (GOV-002)."
        pattern:
          spec:
            containers:
              - resources:
                  limits:
                    memory: "?*"
                    cpu: "?*"
---
# Policy 3: Deny latest tag
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: deny-latest-tag
spec:
  validationFailureAction: Enforce
  rules:
    - name: check-image-tag
      match:
        any:
          - resources:
              kinds:
                - Pod
      exclude:
        any:
          - resources:
              namespaces:
                - kube-system
                - kyverno
      validate:
        message: "Images must use a specific tag, not ':latest' (GOV-003)."
        pattern:
          spec:
            containers:
              - image: "!*:latest"
---
# Policy 4: Require team and cost-center labels on namespaces
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-namespace-labels
spec:
  validationFailureAction: Enforce
  rules:
    - name: check-labels
      match:
        any:
          - resources:
              kinds:
                - Namespace
      exclude:
        any:
          - resources:
              names:
                - kube-*
                - default
                - kyverno
      validate:
        message: "Namespaces must have 'team' and 'cost-center' labels (GOV-004)."
        pattern:
          metadata:
            labels:
              team: "?*"
              cost-center: "?*"
---
# Policy 5: Generate default NetworkPolicy on namespace creation
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: generate-network-policy
spec:
  rules:
    - name: default-deny-ingress
      match:
        any:
          - resources:
              kinds:
                - Namespace
      exclude:
        any:
          - resources:
              names:
                - kube-*
                - default
                - kyverno
      generate:
        apiVersion: networking.k8s.io/v1
        kind: NetworkPolicy
        name: default-deny-ingress
        namespace: "{{request.object.metadata.name}}"
        synchronize: true
        data:
          spec:
            podSelector: {}
            policyTypes:
              - Ingress
---
# Policy 6: Mutate to add standard labels
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: add-governance-labels
spec:
  rules:
    - name: add-managed-by-label
      match:
        any:
          - resources:
              kinds:
                - Deployment
                - StatefulSet
      mutate:
        patchStrategicMerge:
          metadata:
            labels:
              +(governance.company.com/policy-version): "2.1"
              +(governance.company.com/managed-by): "platform-team"
EOF

echo "Policies deployed:"
k get clusterpolicy
```

</details>

### Task 3: Shift-Left with kyverno-cli

Install kyverno-cli and validate manifests before they reach the cluster.

<details>
<summary>Solution</summary>

```bash
# Install kyverno CLI
# On macOS:
brew install kyverno
# Or download directly:
# curl -LO https://github.com/kyverno/kyverno/releases/latest/download/kyverno-cli_v1.13.0_linux_amd64.tar.gz

# Create a sample set of manifests to validate
mkdir -p /tmp/governance-lab/manifests /tmp/governance-lab/policies

# Export cluster policies to local files for CLI validation
k get clusterpolicy deny-privileged -o yaml > /tmp/governance-lab/policies/deny-privileged.yaml
k get clusterpolicy require-resource-limits -o yaml > /tmp/governance-lab/policies/require-limits.yaml
k get clusterpolicy deny-latest-tag -o yaml > /tmp/governance-lab/policies/deny-latest.yaml

# Create a GOOD manifest
cat <<'EOF' > /tmp/governance-lab/manifests/good-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  namespace: team-alpha
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
        - name: web
          image: nginx:1.27.3
          securityContext:
            privileged: false
            runAsNonRoot: true
            runAsUser: 1000
          resources:
            limits:
              cpu: 200m
              memory: 256Mi
            requests:
              cpu: 100m
              memory: 128Mi
EOF

# Create a BAD manifest (multiple violations)
cat <<'EOF' > /tmp/governance-lab/manifests/bad-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: yolo-app
  namespace: team-beta
spec:
  replicas: 1
  selector:
    matchLabels:
      app: yolo
  template:
    metadata:
      labels:
        app: yolo
    spec:
      containers:
        - name: danger
          image: nginx:latest
          securityContext:
            privileged: true
EOF

# Validate with kyverno-cli
echo "=== Validating GOOD manifest ==="
kyverno apply /tmp/governance-lab/policies/ \
  --resource /tmp/governance-lab/manifests/good-deployment.yaml 2>&1 || true

echo ""
echo "=== Validating BAD manifest ==="
kyverno apply /tmp/governance-lab/policies/ \
  --resource /tmp/governance-lab/manifests/bad-deployment.yaml 2>&1 || true
```

</details>

### Task 4: Test Policy Enforcement in the Cluster

Create a namespace and test that policies are enforced at admission time.

<details>
<summary>Solution</summary>

```bash
# Create a compliant namespace
cat <<'EOF' | k apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: team-alpha
  labels:
    team: alpha
    cost-center: cc-4521
EOF

# Verify NetworkPolicy was auto-generated
echo "Auto-generated NetworkPolicy:"
k get networkpolicy -n team-alpha

# Test: Deploy a non-compliant pod (should fail)
echo "--- Testing non-compliant pod (expect failure) ---"
cat <<'EOF' | k apply -f - 2>&1 || true
apiVersion: v1
kind: Pod
metadata:
  name: bad-pod
  namespace: team-alpha
spec:
  containers:
    - name: bad
      image: nginx:latest
      securityContext:
        privileged: true
EOF

# Test: Deploy a compliant pod (should succeed)
echo "--- Testing compliant pod (expect success) ---"
cat <<'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: good-pod
  namespace: team-alpha
spec:
  containers:
    - name: web
      image: nginx:1.27.3
      securityContext:
        privileged: false
      resources:
        limits:
          cpu: 100m
          memory: 128Mi
        requests:
          cpu: 50m
          memory: 64Mi
EOF

k get pods -n team-alpha
```

</details>

### Task 5: Implement a Policy Exception

Create a managed exception for a legitimate use case with tracking and expiry.

<details>
<summary>Solution</summary>

```bash
# Scenario: team-alpha needs a privileged init container for a volume
# permission fix (a common pattern with persistent volumes)

cat <<'EOF' | k apply -f -
apiVersion: kyverno.io/v2beta1
kind: PolicyException
metadata:
  name: allow-init-privileged-alpha
  namespace: team-alpha
  labels:
    exception-owner: security-team
    exception-ticket: SEC-8823
    exception-expires: "2025-06-01"
spec:
  exceptions:
    - policyName: deny-privileged
      ruleNames:
        - deny-privileged-containers
  match:
    any:
      - resources:
          kinds:
            - Pod
          namespaces:
            - team-alpha
  conditions:
    any:
      - key: "{{request.object.metadata.labels.exception-approved}}"
        operator: Equals
        value: "SEC-8823"
EOF

# Now test: a pod with the exception label should be allowed
echo "--- Testing with exception label ---"
cat <<'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: volume-fix-pod
  namespace: team-alpha
  labels:
    exception-approved: "SEC-8823"
spec:
  containers:
    - name: app
      image: nginx:1.27.3
      securityContext:
        privileged: true
      resources:
        limits:
          cpu: 100m
          memory: 128Mi
EOF

# List all exceptions
echo "Active exceptions:"
k get policyexception -A
```

</details>

### Task 6: Generate a Governance Compliance Report

Build a script that reports on policy compliance across all namespaces.

<details>
<summary>Solution</summary>

```bash
cat <<'SCRIPT' > /tmp/governance-report.sh
#!/bin/bash
echo "============================================="
echo "  GOVERNANCE COMPLIANCE REPORT"
echo "  Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "============================================="

echo ""
echo "--- Cluster Policies ---"
kubectl get clusterpolicy -o custom-columns=\
NAME:.metadata.name,\
ACTION:.spec.validationFailureAction,\
READY:.status.ready,\
RULES:.status.rulecount.validate

echo ""
echo "--- Policy Reports by Namespace ---"
for NS in $(kubectl get namespaces -o jsonpath='{.items[*].metadata.name}' | tr ' ' '\n' | grep -v kube- | grep -v default | grep -v kyverno); do
  PASS=$(kubectl get policyreport -n $NS -o jsonpath='{.items[*].summary.pass}' 2>/dev/null)
  FAIL=$(kubectl get policyreport -n $NS -o jsonpath='{.items[*].summary.fail}' 2>/dev/null)
  WARN=$(kubectl get policyreport -n $NS -o jsonpath='{.items[*].summary.warn}' 2>/dev/null)
  echo "  $NS: pass=${PASS:-0} fail=${FAIL:-0} warn=${WARN:-0}"
done

echo ""
echo "--- Active Exceptions ---"
kubectl get policyexception -A -o custom-columns=\
NAMESPACE:.metadata.namespace,\
NAME:.metadata.name,\
TICKET:.metadata.labels.exception-ticket,\
EXPIRES:.metadata.labels.exception-expires 2>/dev/null || echo "  No exceptions found"

echo ""
echo "--- Non-Compliant Resources (from background scan) ---"
kubectl get clusterpolicyreport -o json 2>/dev/null | \
  jq -r '.items[].results[] | select(.result == "fail") | "  \(.policy): \(.resources[0].namespace)/\(.resources[0].name) - \(.message)"' 2>/dev/null \
  || echo "  No violations found in background scan"

echo ""
echo "============================================="
SCRIPT

chmod +x /tmp/governance-report.sh
bash /tmp/governance-report.sh
```

</details>

### Clean Up

```bash
kind delete cluster --name governance-lab
rm -rf /tmp/governance-lab /tmp/governance-report.sh
```

### Success Criteria

- [ ] I deployed 6 Kyverno policies covering security, cost, and operational concerns
- [ ] I validated manifests locally using kyverno-cli (shift-left)
- [ ] I verified that non-compliant resources are blocked at admission
- [ ] I confirmed that compliant resources are admitted
- [ ] I verified that namespace creation auto-generates a NetworkPolicy
- [ ] I created a managed PolicyException with ticket tracking and expiry
- [ ] I generated a governance compliance report across all namespaces
- [ ] I can explain the five layers of the Policy Pyramid

---

## Next Module

Now that you understand how to enforce governance across cloud and Kubernetes, it is time to connect these policies to compliance frameworks. Head to [Module 10.3: Continuous Compliance & CSPM](../module-10.3-compliance/) to learn how to map your policies to SOC2, PCI-DSS, and HIPAA controls, automate evidence collection, and integrate Trivy and Falco with cloud security hubs.
