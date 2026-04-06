---
title: "Module 2.1: GCP Identity, IAM & Resource Hierarchy"
slug: cloud/gcp-essentials/module-2.1-iam
sidebar:
  order: 2
---
**Complexity**: [MEDIUM] | **Time to Complete**: 2h | **Prerequisites**: Cloud Native 101

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Configure GCP IAM policies across the resource hierarchy (Organization, Folders, Projects) with proper inheritance**
- **Implement least-privilege service accounts with Workload Identity Federation to eliminate exported key files**
- **Design custom IAM roles that precisely scope permissions beyond predefined roles for production workloads**
- **Diagnose IAM policy evaluation failures using Policy Troubleshooter and audit log analysis**

---

## Why This Module Matters

In September 2020, a mid-sized fintech company discovered that their entire Google Cloud production environment had been compromised. The root cause was not a sophisticated exploit or a zero-day vulnerability. A developer had created a service account with Project Owner permissions "temporarily" to debug an integration issue with Cloud Storage. That service account key was committed to a private GitHub repository. When the repository was briefly made public during an open-source release, automated scanners harvested the key within minutes. Because the service account had Owner-level access to the production project, the attacker was able to exfiltrate customer financial records, spin up cryptocurrency mining instances across multiple regions, and delete audit logs. The total cost exceeded $2.3 million in direct damages, not including the regulatory fines that followed.

This incident reveals the fundamental truth about Google Cloud Platform security: **the resource hierarchy is your blast radius, and IAM is the control plane for everything**. Unlike traditional infrastructure where network firewalls form the primary defense, in GCP every single action---creating a VM, reading a storage object, deploying a Cloud Run service---flows through IAM. If your IAM posture is weak, every other security measure becomes irrelevant. An attacker with the right IAM permissions can bypass VPC firewalls, read encrypted data, and delete entire projects with a single API call.

In this module, you will learn how GCP organizes resources into a hierarchy (Organization, Folders, and Projects), how IAM policies are inherited through that hierarchy, and how to design access control that follows the principle of least privilege. You will understand the critical differences between basic roles, predefined roles, and custom roles. Most importantly, you will learn how to handle service accounts correctly---because misconfigured service accounts remain the number one attack vector in cloud breaches.

---

## The Resource Hierarchy: Your Organizational Blueprint

Before you can understand IAM in GCP, you must understand *where* IAM policies live. In GCP, resources are organized into a strict hierarchy, and IAM policies **inherit downward** through that hierarchy. This is fundamentally different from AWS, where each account is largely isolated and cross-account access requires explicit trust policies.

### The Four Levels

```text
                    ┌───────────────────────┐
                    │    Organization        │  ← Tied to your Google Workspace
                    │   (example.com)        │     or Cloud Identity domain
                    └───────────┬───────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                   │
    ┌─────────▼────────┐ ┌─────▼──────┐  ┌────────▼────────┐
    │  Folder:          │ │  Folder:    │  │  Folder:         │
    │  Engineering      │ │  Finance    │  │  Shared Services │
    └────────┬──────────┘ └─────┬──────┘  └────────┬─────────┘
             │                  │                   │
     ┌───────┼───────┐         │           ┌───────┼───────┐
     │               │         │           │               │
┌────▼────┐  ┌──────▼──┐ ┌────▼────┐ ┌────▼────┐  ┌──────▼──┐
│ Project: │  │ Project: │ │ Project:│ │ Project: │  │ Project: │
│ eng-dev  │  │ eng-prod │ │ fin-prod│ │ shared-  │  │ shared-  │
│          │  │          │ │         │ │ logging  │  │ networking│
└──────────┘  └──────────┘ └─────────┘ └──────────┘  └──────────┘
     │               │
     │               │
  Resources       Resources
  (VMs, GCS,      (VMs, GCS,
   GKE, etc.)      GKE, etc.)
```

**Organization**: The root node. It is automatically created when you set up Google Workspace or Cloud Identity for your domain. Every resource in your company ultimately lives under this node. IAM policies set here apply to *everything* underneath.

**Folders**: Optional grouping mechanism. Folders let you organize projects by team, environment, or business unit. You can nest folders up to 10 levels deep (though more than 3-4 levels is generally a sign of over-engineering). Folders are the primary tool for applying environment-wide policies---for example, denying external IP addresses on all VMs in a "Production" folder.

**Projects**: The fundamental unit of resource ownership. Every GCP resource (a VM, a GCS bucket, a Cloud Run service) belongs to exactly one project. Projects provide billing boundaries, API enablement boundaries, and the default scope for most IAM operations. Each project has three identifiers:

| Identifier | Example | Mutable | Unique Across |
| :--- | :--- | :--- | :--- |
| **Project Name** | "Engineering Dev" | Yes | Not unique (display only) |
| **Project ID** | `eng-dev-382910` | No (set at creation) | Globally unique, forever |
| **Project Number** | `481726359042` | No (auto-assigned) | Globally unique, forever |

**Resources**: The actual GCP services and objects you create. VMs, databases, storage buckets, Pub/Sub topics---they all live inside a project.

> **Pause and predict**: If you move a Project from the "Engineering" folder to the "Finance" folder, what happens to the IAM policies applied to the Project?
> <details>
> <summary>Answer</summary>
> The project will immediately lose all permissions inherited from the "Engineering" folder and instantly inherit all permissions applied to the "Finance" folder. Any IAM policies applied directly to the Project itself will remain unchanged. This dynamic inheritance is why moving projects across folders is a high-risk operation.
> </details>

### Policy Inheritance: The Cascade Effect

This is the single most important concept to understand about GCP IAM. **IAM policies are additive and inherit downward**. If you grant a user the `roles/editor` role at the Organization level, that user has Editor permissions on every single project in the entire organization. You cannot revoke an inherited permission at a lower level (though you can use Organization Policy Constraints or IAM Deny Policies to restrict specific actions).

```bash
# View the IAM policy at the organization level
gcloud organizations get-iam-policy ORGANIZATION_ID

# View the IAM policy at a folder level
gcloud resource-manager folders get-iam-policy FOLDER_ID

# View the IAM policy at a project level
gcloud projects get-iam-policy PROJECT_ID

# Check IAM bindings directly on this project
# (does NOT include inherited permissions from org/folders)
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:user:alice@example.com" \
  --format="table(bindings.role)"
```

A practical analogy: Think of the resource hierarchy like a building. The Organization is the master key---anyone with the master key can open every door. Folders are floor-level keys, and Projects are individual room keys. You can always grant more specific access at lower levels, but you cannot take away access that was granted at a higher level (without using deny policies, which we will cover shortly).

### Organization Policies vs IAM Policies

New GCP practitioners often confuse Organization Policies with IAM policies. They are fundamentally different tools:

| Aspect | IAM Policy | Organization Policy |
| :--- | :--- | :--- |
| **What it controls** | Who can do what (identity-based) | What is allowed to exist (resource-based) |
| **Example** | "Alice can create VMs" | "No VM can have an external IP" |
| **Scope** | Org, Folder, Project, Resource | Org, Folder, Project |
| **Override behavior** | Additive (cannot revoke inherited) | Can override parent (with boolean constraints) |
| **Use case** | Access control | Guardrails, compliance enforcement |

```bash
# List available organization policy constraints
gcloud org-policies list --organization=ORGANIZATION_ID

# Set a constraint to deny external IPs on all VMs in a folder
gcloud org-policies set-policy policy.yaml --folder=FOLDER_ID
```

Example `policy.yaml` to block external IPs:

```yaml
constraint: constraints/compute.vmExternalIpAccess
listPolicy:
  allValues: DENY
```

---

## Principals and IAM Roles: The Access Control Model

### Principals: Who Can Act?

A principal in GCP is any identity that can be authenticated and authorized. GCP supports several principal types:

| Principal Type | Format | Use Case |
| :--- | :--- | :--- |
| **Google Account** | `user:alice@example.com` | Human users with Google accounts |
| **Service Account** | `serviceAccount:sa@project.iam.gserviceaccount.com` | Applications, VMs, Cloud Run services |
| **Google Group** | `group:devs@example.com` | Teams of humans (recommended over individual grants) |
| **Google Workspace Domain** | `domain:example.com` | Everyone in the organization |
| **allAuthenticatedUsers** | `allAuthenticatedUsers` | Any Google account (dangerous) |
| **allUsers** | `allUsers` | Anyone on the internet (very dangerous) |

**Best Practice**: Always use Google Groups for human access. Granting roles to individual users creates an audit nightmare and makes offboarding error-prone. When an engineer leaves, you remove them from the group. You do not need to hunt through dozens of IAM policies across projects.

### The Three Types of Roles

GCP has three categories of IAM roles, and understanding the distinction is critical for both security and operations.

#### 1. Basic Roles (Formerly "Primitive Roles")

These are the broadest roles in GCP. They existed before the modern IAM system and are considered **legacy roles** that should be avoided in production.

| Role | Permissions | When to Use |
| :--- | :--- | :--- |
| `roles/viewer` | Read-only access to all resources | Never in production (too broad) |
| `roles/editor` | Read-write access to most resources | Never in production (can modify everything) |
| `roles/owner` | Full control including IAM and billing | Only for initial setup, then remove |

The `roles/editor` role is particularly dangerous because it grants write access to nearly everything *except* IAM policy modification. Many teams use it as a shortcut for developers, not realizing it allows deleting databases, modifying firewall rules, and reading secrets.

#### 2. Predefined Roles

Google maintains hundreds of predefined roles that follow the principle of least privilege for specific services. These are the roles you should be using day-to-day.

```bash
# List all predefined roles (there are 1000+)
gcloud iam roles list --filter="name:roles/"

# View the permissions in a specific predefined role
gcloud iam roles describe roles/storage.objectViewer

# Search for roles related to a specific service
gcloud iam roles list --filter="name:roles/cloudsql"
```

Common predefined roles you will use constantly:

| Role | What It Grants |
| :--- | :--- |
| `roles/storage.objectViewer` | Read GCS objects (not list buckets) |
| `roles/storage.objectAdmin` | Full control over GCS objects |
| `roles/compute.instanceAdmin.v1` | Manage Compute Engine instances |
| `roles/run.invoker` | Invoke Cloud Run services |
| `roles/cloudsql.client` | Connect to Cloud SQL instances |
| `roles/logging.viewer` | Read Cloud Logging logs |
| `roles/monitoring.viewer` | Read Cloud Monitoring metrics |
| `roles/iam.serviceAccountUser` | Act as (impersonate) a service account |

> **Stop and think**: Your developers need to deploy Cloud Run services and connect them to Cloud SQL. Should you create a custom role combining both sets of permissions, or grant multiple predefined roles?
> <details>
> <summary>Answer</summary>
> You should grant multiple predefined roles (e.g., `roles/run.admin` and `roles/cloudsql.client`). Predefined roles are maintained by Google and automatically updated when new permissions are added to a service. Custom roles must be manually maintained, which becomes an operational burden. Only use custom roles when predefined roles are explicitly too broad or too narrow.
> </details>

#### 3. Custom Roles

When predefined roles are either too broad or too narrow, you can create custom roles with exactly the permissions you need.

```bash
# Create a custom role from a YAML definition
gcloud iam roles create customStorageReader \
  --project=my-project \
  --file=role-definition.yaml

# role-definition.yaml
cat <<'YAML'
title: "Custom Storage Reader"
description: "Can read objects and list buckets, but not delete"
stage: "GA"
includedPermissions:
  - storage.buckets.list
  - storage.objects.get
  - storage.objects.list
YAML

# List custom roles in a project
gcloud iam roles list --project=my-project

# Update a custom role (add a permission)
gcloud iam roles update customStorageReader \
  --project=my-project \
  --add-permissions=storage.buckets.get
```

Custom roles have some gotchas:
- They can be created at the Organization or Project level (not Folder level).
- They support a maximum of 3000 permissions.
- Some permissions cannot be used in custom roles (check the documentation for `TESTING` or `NOT_SUPPORTED` launch stages).
- You must manage their lifecycle yourself---when Google adds new permissions to a service, your custom roles do not automatically get updated.

### IAM Deny Policies

Introduced in 2022, IAM Deny Policies solve the inheritance problem. Remember that IAM policies are additive---you cannot revoke inherited permissions. Deny policies allow you to explicitly deny specific permissions, overriding any allow policies.

```bash
# Create a deny policy that prevents anyone from deleting projects
# (even if they have Owner role)
gcloud iam policies create prevent-project-deletion \
  --attachment-point="cloudresourcemanager.googleapis.com/organizations/ORGANIZATION_ID" \
  --kind=denypolicies \
  --policy-file=deny-policy.json
```

```json
{
  "displayName": "Prevent Project Deletion",
  "rules": [
    {
      "denyRule": {
        "deniedPrincipals": [
          "principalSet://goog/public:all"
        ],
        "exceptionPrincipals": [
          "principal://goog/subject/admin@example.com"
        ],
        "deniedPermissions": [
          "cloudresourcemanager.googleapis.com/projects.delete"
        ]
      }
    }
  ]
}
```

Deny policies are evaluated **before** allow policies. The evaluation order is:

```text
1. Organization Policy Constraints  →  "Is this action even allowed to exist?"
2. IAM Deny Policies                →  "Is this action explicitly denied?"
3. IAM Allow Policies               →  "Is this action explicitly allowed?"
4. Default: DENY                    →  "If no allow policy matches, deny."
```

---

## Service Accounts: Machine Identity Done Right

Service accounts are the most critical---and most frequently misconfigured---aspect of GCP IAM. They represent non-human identities used by applications, VMs, and services.

### Types of Service Accounts

| Type | Created By | Example | Managed By |
| :--- | :--- | :--- | :--- |
| **User-managed** | You | `my-app@my-project.iam.gserviceaccount.com` | You (full control) |
| **Default** | GCP (auto) | `PROJECT_NUMBER-compute@developer.gserviceaccount.com` | You (but auto-created) |
| **Google-managed** | GCP | `service-PROJECT_NUMBER@compute-system.iam.gserviceaccount.com` | Google (do not modify) |

**War Story**: The default Compute Engine service account (`PROJECT_NUMBER-compute@developer.gserviceaccount.com`) is automatically granted the `roles/editor` role on the project. This means that every VM you create without specifying a service account gets Editor access to your entire project. This is the single most common privilege escalation vector in GCP. Always create dedicated service accounts with minimal permissions.

```bash
# Create a dedicated service account
gcloud iam service-accounts create gcs-reader \
  --display-name="GCS Reader for Data Pipeline" \
  --project=my-project

# Grant it only the permissions it needs
gcloud projects add-iam-binding my-project \
  --member="serviceAccount:gcs-reader@my-project.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

# Create a VM using this dedicated service account
gcloud compute instances create data-worker \
  --service-account=gcs-reader@my-project.iam.gserviceaccount.com \
  --scopes=cloud-platform \
  --zone=us-central1-a
```

### Service Account Keys: The Danger Zone

Service account keys are JSON files containing long-lived credentials. They are the GCP equivalent of AWS access keys, and they are equally dangerous.

```bash
# Creating a key (avoid this whenever possible)
gcloud iam service-accounts keys create key.json \
  --iam-account=my-sa@my-project.iam.gserviceaccount.com

# List existing keys for a service account
gcloud iam service-accounts keys list \
  --iam-account=my-sa@my-project.iam.gserviceaccount.com

# Delete a key
gcloud iam service-accounts keys delete KEY_ID \
  --iam-account=my-sa@my-project.iam.gserviceaccount.com
```

**Rule of thumb**: If you are creating a service account key, you are probably doing it wrong. In nearly every case, there is a better alternative:

| Scenario | Instead of Keys, Use |
| :--- | :--- |
| Code running on GCE/GKE | Attached service account (metadata server) |
| Cloud Run / Cloud Functions | Attached service account (automatic) |
| CI/CD from GitHub Actions | Workload Identity Federation |
| CI/CD from GitLab | Workload Identity Federation |
| On-premises application | Workload Identity Federation |
| Local development | `gcloud auth application-default login` |

### Service Account Impersonation

Instead of downloading keys, you can **impersonate** a service account. This gives you temporary credentials without creating a persistent key file.

```bash
# Impersonate a service account for a single command
gcloud storage ls gs://my-bucket \
  --impersonate-service-account=gcs-reader@my-project.iam.gserviceaccount.com

# Set impersonation for all subsequent gcloud commands
gcloud config set auth/impersonate_service_account \
  gcs-reader@my-project.iam.gserviceaccount.com

# To stop impersonating
gcloud config unset auth/impersonate_service_account
```

For impersonation to work, the caller must have the `roles/iam.serviceAccountTokenCreator` role on the target service account.

---

## Workload Identity Federation: Keyless Authentication

Workload Identity Federation allows external identities (from AWS, Azure, GitHub Actions, GitLab CI, or any OIDC/SAML provider) to access GCP resources **without service account keys**. This is the modern, recommended approach for any workload running outside of GCP.

### How It Works

```text
  ┌─────────────────┐     1. Get OIDC Token      ┌─────────────────┐
  │  External        │ ──────────────────────────> │  Identity        │
  │  Workload        │                             │  Provider        │
  │  (GitHub Actions,│     2. OIDC Token           │  (GitHub, AWS,   │
  │   AWS, on-prem)  │ <────────────────────────── │   GitLab, etc.)  │
  └────────┬─────────┘                             └──────────────────┘
           │
           │  3. Exchange OIDC token for
           │     GCP STS token
           ▼
  ┌─────────────────┐     4. STS token             ┌──────────────────┐
  │  GCP Security    │ ──────────────────────────> │  GCP Service      │
  │  Token Service   │                             │  Account          │
  │  (STS)           │     5. Short-lived           │  (impersonated)   │
  │                  │        SA credentials        │                   │
  └──────────────────┘                             └────────┬──────────┘
                                                            │
                                                   6. Access GCP resources
                                                            │
                                                            ▼
                                                   ┌──────────────────┐
                                                   │  GCP Resources    │
                                                   │  (GCS, BigQuery,  │
                                                   │   Cloud Run, etc.)│
                                                   └──────────────────┘
```

### Setting Up Workload Identity Federation for GitHub Actions

This is one of the most common use cases---deploying to GCP from GitHub Actions without storing service account keys as GitHub secrets.

```bash
# Step 1: Create a Workload Identity Pool
gcloud iam workload-identity-pools create "github-pool" \
  --project="my-project" \
  --location="global" \
  --display-name="GitHub Actions Pool"

# Step 2: Create a Provider in the pool (for GitHub OIDC)
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --project="my-project" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# Step 3: Create a service account for GitHub Actions to impersonate
gcloud iam service-accounts create github-deployer \
  --display-name="GitHub Actions Deployer" \
  --project=my-project

# Step 4: Grant the service account permissions it needs
gcloud projects add-iam-binding my-project \
  --member="serviceAccount:github-deployer@my-project.iam.gserviceaccount.com" \
  --role="roles/run.admin"

# Step 5: Allow the GitHub repo to impersonate the service account
gcloud iam service-accounts add-iam-binding \
  github-deployer@my-project.iam.gserviceaccount.com \
  --project="my-project" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/my-org/my-repo"
```

Then in your GitHub Actions workflow:

```yaml
# .github/workflows/deploy.yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write  # Required for OIDC
    steps:
      - uses: actions/checkout@v4

      - id: auth
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: "projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider"
          service_account: "github-deployer@my-project.iam.gserviceaccount.com"

      - name: Deploy to Cloud Run
        uses: google-github-actions/deploy-cloudrun@v2
        with:
          service: my-api
          region: us-central1
          image: us-central1-docker.pkg.dev/my-project/my-repo/my-api:latest
```

---

## IAM Best Practices and Audit

### The IAM Recommender

GCP includes a built-in tool that analyzes your actual permission usage and recommends tighter roles.

```bash
# List IAM recommendations for a project
gcloud recommender recommendations list \
  --project=my-project \
  --location=global \
  --recommender=google.iam.policy.Recommender \
  --format="table(content.operationGroups[0].operations[0].resource, content.operationGroups[0].operations[0].value.bindings[0].role)"
```

### Audit Logging

Every IAM action in GCP is logged to Cloud Audit Logs. There are three types:

- **Admin Activity logs**: Always on, free. Logs IAM policy changes, resource creation/deletion.
- **Data Access logs**: Must be enabled, incurs cost. Logs who read/wrote data.
- **System Event logs**: Always on, free. Logs GCP system actions (live migration, etc.).

```bash
# Enable Data Access audit logs for Cloud Storage
gcloud projects get-iam-policy my-project --format=json > policy.json
# Edit policy.json to add auditConfigs, then set it back
gcloud projects set-iam-policy my-project policy.json

# Query audit logs for IAM changes
gcloud logging read 'logName="projects/my-project/logs/cloudaudit.googleapis.com%2Factivity" AND protoPayload.methodName="SetIamPolicy"' \
  --limit=10 \
  --format=json
```

---

## Diagnosing Access Issues: Policy Troubleshooter

When a user or service account gets a `403 Permission Denied` error, guessing which role is missing is a frustrating waste of time. GCP provides the **Policy Troubleshooter** specifically to answer the question: *"Why does (or doesn't) this principal have this permission on this resource?"*

The Policy Troubleshooter evaluates:
1. The principal's direct IAM bindings on the resource.
2. Inherited IAM bindings from parent projects, folders, and organizations.
3. IAM Deny policies that might be blocking access.
4. The roles granted, expanding them to check if the specific API permission is included.

```bash
# Check if a specific service account has permission to list objects in a bucket
gcloud policy-troubleshoot iam \
  //storage.googleapis.com/projects/_/buckets/my-bucket \
  --principal="serviceAccount:gcs-reader@my-project.iam.gserviceaccount.com" \
  --permission="storage.objects.list"
```

The output will clearly state whether access is `GRANTED` or `DENIED` and, crucially, it will show the exact binding (or lack thereof) that resulted in the decision. 

**Pro-tip for troubleshooting with Audit Logs**: If you don't know exactly which permission is missing, look at the Cloud Audit Logs first. Find the `403` error in the logs, look at the `protoPayload.authorizationInfo` field, and it will tell you exactly which permission was evaluated and returned false. Then, use the Policy Troubleshooter to determine *why* they don't have that permission.

---

## Did You Know?

1. **GCP has over 11,000 individual IAM permissions** spread across hundreds of services. The `roles/editor` basic role grants access to roughly 6,000 of them. This is why predefined roles with 5-20 permissions are always the better choice.

2. **Service account keys never expire by default**. Unlike AWS access keys (which have no built-in expiration either), GCP does not enforce rotation. An abandoned key from 2019 is still valid today unless someone explicitly deletes it. Google recommends setting an Organization Policy to disable key creation entirely (`constraints/iam.disableServiceAccountKeyCreation`).

3. **The project number (not the project ID) is what GCP uses internally**. When you see `service-481726359042@compute-system.iam.gserviceaccount.com`, the number is the project number. Project IDs are just human-friendly aliases. Even if you delete a project, its project ID can never be reused by anyone, ever.

4. **IAM Conditions let you create time-bound access**. You can grant a role that automatically expires. For example, you can give an on-call engineer `roles/compute.instanceAdmin` that is only valid for 8 hours, or grant access only during business hours in a specific timezone. This eliminates the "forgot to revoke access" problem entirely.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| Using `roles/editor` for developers | It seems like a reasonable "developer" role | Use predefined roles like `roles/compute.instanceAdmin.v1` + `roles/storage.objectViewer` |
| Granting IAM at the Organization level | Convenience; applies everywhere at once | Grant at the lowest possible level (project or resource) |
| Using the default Compute Engine SA | It is automatic; you don't have to do anything | Always create dedicated service accounts per workload |
| Creating service account keys | External tools "require" a JSON key file | Use Workload Identity Federation or impersonation instead |
| Granting `allUsers` or `allAuthenticatedUsers` | Quick fix when auth is "not working" | Debug the actual auth issue; these grants expose data publicly |
| Not using Google Groups | Adding individual users is faster initially | Always create groups; they simplify audits and offboarding |
| Ignoring IAM Recommender suggestions | Teams do not know the Recommender exists | Schedule monthly reviews of IAM Recommender output |
| Forgetting about inherited permissions | The hierarchy is invisible in the console by default | Use `gcloud asset search-all-iam-policies` to see the full picture |

---

## Quiz

<details>
<summary>1. Scenario: An engineer leaves the company. You remove them from the 'gcp-developers' Google Group. However, they are still able to modify instances in the 'sandbox' project. Why might this happen, and how do you find out?</summary>

They likely have a direct IAM binding on the project or a specific resource (like a VM), bypassing the Google Group. IAM policies are additive, so removing them from the group only removes the group's inherited permissions. To find out, use `gcloud asset search-all-iam-policies` to search across the organization for their specific email address, or use the Policy Troubleshooter if you know which resource they are modifying.
</details>

<details>
<summary>2. Scenario: Your CI/CD pipeline in GitLab needs to deploy a container to Cloud Run. The security team has strictly forbidden the creation of long-lived service account JSON keys. How do you authenticate the pipeline?</summary>

You must implement Workload Identity Federation. This involves creating a Workload Identity Pool and a Provider configured to trust GitLab's OIDC issuer. The GitLab pipeline uses its native JWT to authenticate to the provider, which exchanges it for a short-lived GCP STS token. The pipeline then uses this token to impersonate a specific GCP service account that holds the `roles/run.admin` permission, completely eliminating the need for persistent secrets.
</details>

<details>
<summary>3. Scenario: You assign <code>roles/storage.objectAdmin</code> to a service account at the Folder level. You want to prevent this service account from deleting objects in one specific production project within that folder. Can you do this by removing the role in the project's IAM policy? Why or why not?</summary>

No, you cannot achieve this by modifying the project's allow policy. In GCP, IAM allow policies are additive and inherit downward; you cannot subtract or override an inherited allow permission by simply omitting it at a lower level. To block the deletion, you must create an IAM Deny Policy attached to the production project that explicitly denies the `storage.objects.delete` permission for that specific service account. The Deny policy will take precedence over the inherited Allow policy.
</details>

<details>
<summary>4. Scenario: A developer complains they are getting a `403 Permission Denied` when trying to view Cloud SQL backups. They insist they have the `roles/editor` role on the project. How do you systematically identify the missing permission without blindly guessing?</summary>

First, check the Cloud Audit Logs for the specific `403` error event. Expand the `protoPayload.authorizationInfo` field in the log entry to see the exact API permission that was evaluated and rejected (e.g., `cloudsql.backupRuns.get`). Once you have the exact permission string, use the IAM Policy Troubleshooter in the console or CLI, inputting the developer's email, the resource name, and the permission. The troubleshooter will analyze the role bindings and explain exactly why the permission is missing or blocked by a deny policy.
</details>

<details>
<summary>5. Scenario: A developer manually created a VM to run an internal script without explicitly specifying a service account. Two days later, a security scanner alerts that the VM has full read-write access to every resource in the project. Why did this happen?</summary>

When a Compute Engine VM is created without specifying a service account, GCP automatically assigns it the default Compute Engine service account. This default service account is automatically granted the legacy `roles/editor` role on the project when the API is first enabled. Because `roles/editor` grants sweeping read-write access to almost all GCP services, the VM effectively inherited administrative power over the entire project. This violates the principle of least privilege.
</details>

---

## Hands-On Exercise: Multi-Project IAM with Least Privilege

### Objective

Set up a realistic multi-project environment with proper IAM controls: a Dev project and a Prod project, each with dedicated service accounts following least privilege, integrating Workload Identity Federation and utilizing the Policy Troubleshooter.

### Prerequisites

- `gcloud` CLI installed and authenticated
- Billing account linked (both projects will be within free tier)
- Organization access (or use two standalone projects if no org)

### Tasks

**Task 1: Create the Project Structure**

Create two projects simulating a Dev/Prod split.

<details>
<summary>Solution</summary>

```bash
# Generate unique project IDs (project IDs must be globally unique)
export DEV_PROJECT="iam-lab-dev-$(date +%s | tail -c 7)"
export PROD_PROJECT="iam-lab-prod-$(date +%s | tail -c 7)"

# Create the dev project
gcloud projects create $DEV_PROJECT --name="IAM Lab Dev"

# Create the prod project
gcloud projects create $PROD_PROJECT --name="IAM Lab Prod"

# Link billing (replace BILLING_ACCOUNT_ID with your billing account)
gcloud billing projects link $DEV_PROJECT --billing-account=BILLING_ACCOUNT_ID
gcloud billing projects link $PROD_PROJECT --billing-account=BILLING_ACCOUNT_ID

# Enable required APIs in both projects
for PROJECT in $DEV_PROJECT $PROD_PROJECT; do
  gcloud services enable \
    storage.googleapis.com \
    iam.googleapis.com \
    --project=$PROJECT
done

echo "Dev Project: $DEV_PROJECT"
echo "Prod Project: $PROD_PROJECT"
```
</details>

**Task 2: Create Dedicated Service Accounts**

Create a service account in the Dev project for a data pipeline that needs to read from Cloud Storage in Dev and write logs.

<details>
<summary>Solution</summary>

```bash
# Create the service account in the dev project
gcloud iam service-accounts create data-pipeline \
  --display-name="Data Pipeline SA" \
  --project=$DEV_PROJECT

export DEV_SA="data-pipeline@${DEV_PROJECT}.iam.gserviceaccount.com"

# Grant minimal permissions: read GCS objects
gcloud projects add-iam-binding $DEV_PROJECT \
  --member="serviceAccount:$DEV_SA" \
  --role="roles/storage.objectViewer"

# Grant permission to write logs
gcloud projects add-iam-binding $DEV_PROJECT \
  --member="serviceAccount:$DEV_SA" \
  --role="roles/logging.logWriter"

# Verify the bindings
gcloud projects get-iam-policy $DEV_PROJECT \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:$DEV_SA" \
  --format="table(bindings.role)"
```
</details>

**Task 3: Create a Prod Service Account with Cross-Project Access**

Create a service account in the Prod project that can read from a GCS bucket in the Dev project (simulating a promotion pipeline).

<details>
<summary>Solution</summary>

```bash
# Create service account in prod
gcloud iam service-accounts create artifact-reader \
  --display-name="Artifact Reader for Prod" \
  --project=$PROD_PROJECT

export PROD_SA="artifact-reader@${PROD_PROJECT}.iam.gserviceaccount.com"

# Grant it read access to the DEV project's storage (cross-project)
gcloud projects add-iam-binding $DEV_PROJECT \
  --member="serviceAccount:$PROD_SA" \
  --role="roles/storage.objectViewer"

# Create a test bucket in dev and upload a file
gcloud storage buckets create gs://${DEV_PROJECT}-artifacts \
  --project=$DEV_PROJECT \
  --location=us-central1

echo "build-v1.0.tar.gz" | gcloud storage cp - gs://${DEV_PROJECT}-artifacts/build-v1.0.tar.gz \
  --project=$DEV_PROJECT

# Verify the prod SA can read from the dev bucket using impersonation
gcloud storage ls gs://${DEV_PROJECT}-artifacts/ \
  --impersonate-service-account=$PROD_SA
```
</details>

**Task 4: Configure Workload Identity Federation for GitHub Actions**

Simulate configuring keyless authentication for a GitHub repository deploying to the Dev project.

<details>
<summary>Solution</summary>

```bash
# Create a Workload Identity Pool
gcloud iam workload-identity-pools create "github-actions-pool" \
  --project=$DEV_PROJECT \
  --location="global" \
  --display-name="GitHub Actions Pool"

# Create an OIDC Provider in the pool
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --project=$DEV_PROJECT \
  --location="global" \
  --workload-identity-pool="github-actions-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# Allow a specific GitHub repository to impersonate the dev service account
export PROJECT_NUM=$(gcloud projects describe $DEV_PROJECT --format="value(projectNumber)")
export REPO_NAME="my-org/my-repo"

gcloud iam service-accounts add-iam-binding $DEV_SA \
  --project=$DEV_PROJECT \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUM}/locations/global/workloadIdentityPools/github-actions-pool/attribute.repository/${REPO_NAME}"
```
</details>

**Task 5: Diagnose Access with Policy Troubleshooter**

Test why the Dev service account cannot delete objects in the Dev bucket.

<details>
<summary>Solution</summary>

```bash
# Attempt to check deletion permission using the troubleshooter
# (Remember we only granted roles/storage.objectViewer earlier)
gcloud policy-troubleshoot iam \
  //storage.googleapis.com/projects/_/buckets/${DEV_PROJECT}-artifacts \
  --principal="serviceAccount:$DEV_SA" \
  --permission="storage.objects.delete" \
  --project=$DEV_PROJECT

# The output should clearly indicate "DENIED" and show that no bindings grant this permission.
```
</details>

**Task 6: Audit the IAM Configuration**

List all IAM bindings for both projects and identify any overly permissive roles.

<details>
<summary>Solution</summary>

```bash
# Audit dev project IAM
echo "=== Dev Project IAM Bindings ==="
gcloud projects get-iam-policy $DEV_PROJECT \
  --format="table(bindings.role, bindings.members)"

# Audit prod project IAM
echo "=== Prod Project IAM Bindings ==="
gcloud projects get-iam-policy $PROD_PROJECT \
  --format="table(bindings.role, bindings.members)"

# Check for dangerous basic roles
echo "=== Checking for Basic Roles (should be minimal) ==="
for PROJECT in $DEV_PROJECT $PROD_PROJECT; do
  echo "Project: $PROJECT"
  gcloud projects get-iam-policy $PROJECT \
    --flatten="bindings[]" \
    --filter="bindings.role:(roles/editor OR roles/owner OR roles/viewer)" \
    --format="table(bindings.role, bindings.members)"
done

# List all service accounts and their keys
for PROJECT in $DEV_PROJECT $PROD_PROJECT; do
  echo "=== Service Accounts in $PROJECT ==="
  gcloud iam service-accounts list --project=$PROJECT \
    --format="table(email, displayName)"
done
```
</details>

**Task 7: Implement a Custom Role**

Create a custom role that allows listing and reading GCS objects but not deleting them.

<details>
<summary>Solution</summary>

```bash
# Create the custom role definition
cat > /tmp/custom-reader-role.yaml <<'YAML'
title: "Safe Storage Reader"
description: "Can list and read GCS objects but cannot delete or overwrite"
stage: "GA"
includedPermissions:
  - storage.buckets.get
  - storage.buckets.list
  - storage.objects.get
  - storage.objects.list
YAML

# Create the custom role in the prod project
gcloud iam roles create safeStorageReader \
  --project=$PROD_PROJECT \
  --file=/tmp/custom-reader-role.yaml

# Verify the custom role was created
gcloud iam roles describe safeStorageReader --project=$PROD_PROJECT

# Grant the custom role to the prod service account
gcloud projects add-iam-binding $PROD_PROJECT \
  --member="serviceAccount:$PROD_SA" \
  --role="projects/${PROD_PROJECT}/roles/safeStorageReader"
```
</details>

**Task 8: Clean Up**

Remove all resources to avoid charges.

<details>
<summary>Solution</summary>

```bash
# Delete the test bucket
gcloud storage rm -r gs://${DEV_PROJECT}-artifacts/

# Delete the projects (this deletes all resources inside them)
gcloud projects delete $DEV_PROJECT --quiet
gcloud projects delete $PROD_PROJECT --quiet

echo "Cleanup complete. Projects scheduled for deletion (30-day recovery window)."
```
</details>

### Success Criteria

- [ ] Two projects created with billing linked
- [ ] Dedicated service accounts created (not using default SA)
- [ ] Cross-project access configured using minimal roles
- [ ] Workload Identity Federation pool and provider configured
- [ ] IAM access diagnosed using Policy Troubleshooter
- [ ] Custom role created and assigned
- [ ] No basic roles (Editor/Owner) granted to service accounts
- [ ] All resources cleaned up

---

## Next Module

Next up: **[Module 2.2: VPC Networking](../module-2.2-vpc/)** --- Learn how GCP's global VPC model differs from other clouds, configure firewall rules using service account targets, and build a Shared VPC connecting multiple projects through a single network.