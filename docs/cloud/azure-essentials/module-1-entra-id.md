# Microsoft Entra ID & Azure RBAC
**Complexity**: [MEDIUM] | **Time to Complete**: 2.5h | **Prerequisites**: Cloud Native 101

## Why This Module Matters

In March 2021, a security researcher discovered that a misconfigured Azure Active Directory application in a Fortune 500 company exposed the email inboxes and SharePoint files of over 16,000 employees. The application had been registered years earlier by a contractor who had long since left the company. Nobody revoked the app's permissions because nobody knew it existed. The application's client secret had been committed to a public GitHub repository, and an attacker had been quietly reading executive emails for months before the breach was discovered. The estimated cost of the incident, including regulatory fines, legal fees, and lost business, exceeded $30 million.

This story illustrates a critical truth about Azure: **identity is not just security---it is the foundation of everything**. Every action in Azure, from creating a virtual machine to reading a blob in storage, flows through the identity layer. Unlike traditional on-premises environments where you might rely on network segmentation and firewall rules as your primary defense, Azure's control plane is entirely identity-driven. If an attacker compromises a service principal with Contributor access to your subscription, no amount of network security groups will prevent them from deleting your databases.

In this module, you will learn how Microsoft Entra ID (formerly Azure Active Directory) works as the identity backbone of Azure. You will understand the hierarchy of tenants, management groups, and subscriptions. You will learn the critical differences between Entra ID roles and Azure RBAC roles---a distinction that trips up even experienced engineers. And you will master Managed Identities, the mechanism that eliminates the need for credentials in your applications entirely. By the end, you will be able to design an identity strategy that follows the principle of least privilege from the ground up.

---

## Azure's Identity Backbone: Microsoft Entra ID

Before you create a single resource in Azure, you need to understand the identity layer that governs everything. Microsoft Entra ID (still frequently called Azure AD in documentation, CLI tools, and everyday conversation) is a cloud-based identity and access management service. Think of it as the bouncer at every door in the Azure building. Every person, every application, every automated process must present credentials to Entra ID before Azure will do anything.

### What Entra ID Is (and What It Is Not)

Entra ID is **not** the same as on-premises Active Directory Domain Services (AD DS). This is one of the most persistent misconceptions in the Azure world. AD DS uses Kerberos and LDAP for authentication, organizes objects into Organizational Units (OUs) with Group Policy Objects (GPOs), and requires domain controllers running on Windows Server. Entra ID uses OAuth 2.0, OpenID Connect, and SAML for authentication, has a flat structure (no OUs, no GPOs), and is a fully managed cloud service.

```text
    On-Premises AD DS                     Microsoft Entra ID
    ─────────────────                     ──────────────────
    Kerberos / NTLM / LDAP               OAuth 2.0 / OIDC / SAML
    Organizational Units (OUs)            Flat directory (no OUs)
    Group Policy Objects (GPOs)           Conditional Access Policies
    Domain Controllers (servers)          Fully managed SaaS
    Forest / Domain / Trust model         Tenant model
    On-prem network required              Internet-accessible
    Supports LDAP queries                 Supports Microsoft Graph API
```

If your organization has on-premises AD DS and wants to use the same identities in Azure, you use **Entra Connect** (formerly Azure AD Connect) to synchronize identities. This hybrid setup is extremely common in enterprises.

### The Tenant: Your Identity Boundary

A **tenant** is a dedicated instance of Entra ID that your organization receives when it signs up for any Microsoft cloud service (Azure, Microsoft 365, Dynamics 365). Think of a tenant as your organization's apartment in a massive apartment building. You share the building infrastructure with other tenants, but your apartment is completely isolated---nobody else can see your users, groups, or applications.

Every tenant has a unique identifier (a GUID) and at least one verified domain. By default, you get a domain like `yourcompany.onmicrosoft.com`, but you can (and should) add your own custom domain.

```bash
# View your current tenant
az account show --query '{TenantId:tenantId, SubscriptionName:name}' -o table

# List all tenants your account has access to
az account tenant list -o table

# Show detailed tenant information
az rest --method GET --url "https://graph.microsoft.com/v1.0/organization" \
  --query "value[0].{DisplayName:displayName, TenantId:id, Domains:verifiedDomains[].name}"
```

### The Hierarchy: Management Groups, Subscriptions, and Resource Groups

Azure organizes resources in a four-level hierarchy. Understanding this hierarchy is essential because **access control and policy inheritance flow from top to bottom**.

```text
    ┌─────────────────────────────────────────────────────────┐
    │                  Root Management Group                   │
    │          (Automatically created per tenant)              │
    │                                                         │
    │   ┌─────────────────────┐  ┌──────────────────────┐     │
    │   │  MG: Production     │  │  MG: Non-Production  │     │
    │   │                     │  │                      │     │
    │   │ ┌─────────────────┐ │  │ ┌──────────────────┐ │     │
    │   │ │ Sub: Prod-App1  │ │  │ │ Sub: Dev         │ │     │
    │   │ │                 │ │  │ │                  │ │     │
    │   │ │ ┌─────────────┐ │ │  │ │ ┌──────────────┐ │ │     │
    │   │ │ │ RG: webapp  │ │ │  │ │ │ RG: sandbox  │ │ │     │
    │   │ │ │  - App Svc  │ │ │  │ │ │  - VM        │ │ │     │
    │   │ │ │  - SQL DB   │ │ │  │ │ │  - VNet      │ │ │     │
    │   │ │ └─────────────┘ │ │  │ │ └──────────────┘ │ │     │
    │   │ └─────────────────┘ │  │ └──────────────────┘ │     │
    │   └─────────────────────┘  └──────────────────────┘     │
    └─────────────────────────────────────────────────────────┘

    Inheritance flows DOWN:
    Policy assigned at MG: Production → applies to ALL subscriptions,
    resource groups, and resources beneath it.
```

| Level | Purpose | Key Facts |
| :--- | :--- | :--- |
| **Management Group** | Organize subscriptions into governance hierarchies | Up to 6 levels deep (excluding root). Max 10,000 MGs per tenant. |
| **Subscription** | Billing boundary and access control boundary | Each subscription trusts exactly one Entra ID tenant. Max ~500 resource groups per sub (soft limit). |
| **Resource Group** | Logical container for related resources | Resources can only exist in one RG. Deleting RG deletes ALL resources inside. |
| **Resource** | The actual thing (VM, database, storage account) | Inherits RBAC and policy from all levels above. |

A common mistake is treating subscriptions as purely a billing construct. They are also **security boundaries**. A user with Owner on Subscription A has zero access to Subscription B by default, even if both subscriptions are in the same tenant. This is why large organizations use multiple subscriptions to isolate environments and teams.

```bash
# List management groups
az account management-group list -o table

# Create a management group
az account management-group create --name "Production" --display-name "Production Workloads"

# Move a subscription under a management group
az account management-group subscription add \
  --name "Production" \
  --subscription "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# List subscriptions in the current tenant
az account list -o table --query '[].{Name:name, Id:id, State:state}'
```

---

## Identities in Entra ID: Users, Groups, Service Principals, and Managed Identities

Now that you understand the organizational structure, let's dive into the identity types. In Azure, there are fundamentally two categories of identities: **human identities** (people who log in) and **workload identities** (applications and services that authenticate programmatically).

### Users

An Entra ID user represents a person. Users can be **cloud-only** (created directly in Entra ID) or **synced** (synchronized from on-premises AD DS via Entra Connect). Users can also be **guest users**, invited from other Entra ID tenants or external email providers via B2B collaboration.

```bash
# Create a cloud-only user
az ad user create \
  --display-name "Alice Engineer" \
  --user-principal-name "alice@yourcompany.onmicrosoft.com" \
  --password "TemporaryP@ss123!" \
  --force-change-password-next-sign-in true

# List all users (first 10)
az ad user list --query '[:10].{Name:displayName, UPN:userPrincipalName, Type:userType}' -o table

# Get a specific user
az ad user show --id "alice@yourcompany.onmicrosoft.com"
```

### Groups

Groups simplify access management. Instead of assigning roles to individual users, you assign roles to groups and add users to the groups. Entra ID has two group types:

- **Security groups**: Used for managing access to resources. This is what you'll use 90% of the time.
- **Microsoft 365 groups**: Used for collaboration (shared mailbox, SharePoint site, Teams channel). Also usable for RBAC, but carry extra baggage.

Groups can have **assigned membership** (manually add/remove members) or **dynamic membership** (members are automatically added/removed based on user attributes like department or job title). Dynamic groups require Entra ID P1 or P2 licensing.

```bash
# Create a security group
az ad group create \
  --display-name "Platform Engineers" \
  --mail-nickname "platform-engineers"

# Add a user to a group
USER_ID=$(az ad user show --id "alice@yourcompany.onmicrosoft.com" --query id -o tsv)
GROUP_ID=$(az ad group show --group "Platform Engineers" --query id -o tsv)
az ad group member add --group "$GROUP_ID" --member-id "$USER_ID"

# List group members
az ad group member list --group "Platform Engineers" --query '[].displayName' -o tsv
```

### Service Principals (App Registrations)

A **service principal** is the identity that an application uses to authenticate with Entra ID. But there is a subtle two-step process that confuses many people:

1. **App Registration**: A global definition of your application. Think of it as the blueprint. It lives in your home tenant and defines what permissions the app needs, what redirect URIs it uses, and what credentials it has.
2. **Service Principal (Enterprise Application)**: A local instance of the app in a specific tenant. Think of it as an installation of the blueprint. When you grant an app access to resources, you are granting access to the service principal, not the app registration.

```text
    ┌──────────────────────────────────────────┐
    │           App Registration               │
    │        (Blueprint / Template)             │
    │                                          │
    │  - Application (client) ID               │
    │  - Redirect URIs                         │
    │  - API Permissions declared               │
    │  - Client secrets / certificates         │
    │                                          │
    │  Lives in: Home tenant only              │
    └──────────────────┬───────────────────────┘
                       │
                       │  Creates
                       ▼
    ┌──────────────────────────────────────────┐
    │         Service Principal                │
    │     (Enterprise Application)             │
    │                                          │
    │  - Object ID (unique per tenant)         │
    │  - Role assignments (Azure RBAC)         │
    │  - Consent grants (API permissions)      │
    │                                          │
    │  Lives in: Each tenant that uses the app │
    └──────────────────────────────────────────┘
```

```bash
# Create an app registration (automatically creates service principal in home tenant)
az ad app create --display-name "my-cicd-pipeline"

# Get the app ID
APP_ID=$(az ad app list --display-name "my-cicd-pipeline" --query '[0].appId' -o tsv)

# Create a client secret (AVOID THIS -- use federated credentials or certificates instead)
az ad app credential reset --id "$APP_ID" --years 1

# Preferred: Create federated credential for GitHub Actions (OIDC -- no secrets!)
az ad app federated-credential create --id "$APP_ID" --parameters '{
  "name": "github-actions-main",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:myorg/myrepo:ref:refs/heads/main",
  "audiences": ["api://AzureADTokenExchange"]
}'
```

**War Story**: A fintech startup stored a service principal's client secret in a `.env` file that was accidentally committed to a public repository. Automated scanners picked it up within 14 minutes. The service principal had Contributor access to their production subscription. By the time the team noticed, the attacker had created 38 cryptocurrency mining VMs across three regions, racking up $12,000 in compute charges before the subscription's spending limit kicked in. The fix? Managed Identities for Azure workloads and OIDC federation for CI/CD pipelines. Zero secrets to leak.

### Managed Identities: The Gold Standard

A **Managed Identity** is a special type of service principal that Azure manages for you. You never see or handle credentials---Azure automatically provisions, rotates, and revokes the tokens behind the scenes. This is the single most important identity concept for application developers on Azure.

There are two types:

| Feature | System-Assigned | User-Assigned |
| :--- | :--- | :--- |
| **Lifecycle** | Tied to the resource (delete VM = delete identity) | Independent (persists until you delete it) |
| **Sharing** | One-to-one (each resource gets its own) | One-to-many (multiple resources share one) |
| **Creation** | Enable on the resource | Create separately, then assign to resources |
| **Naming** | Named after the resource | You choose the name |
| **Best for** | Single-resource scenarios, simpler management | Shared access patterns, pre-provisioning |
| **RBAC management** | Role assignments per resource | Role assignments per identity (shared) |

```bash
# Enable system-assigned managed identity on a VM
az vm identity assign --resource-group myRG --name myVM

# Create a user-assigned managed identity
az identity create --resource-group myRG --name "app-identity"

# Assign the user-assigned identity to a VM
IDENTITY_ID=$(az identity show -g myRG -n "app-identity" --query id -o tsv)
az vm identity assign --resource-group myRG --name myVM --identities "$IDENTITY_ID"

# Grant the managed identity access to a Key Vault
PRINCIPAL_ID=$(az identity show -g myRG -n "app-identity" --query principalId -o tsv)
az role assignment create \
  --assignee "$PRINCIPAL_ID" \
  --role "Key Vault Secrets User" \
  --scope "/subscriptions/<sub-id>/resourceGroups/myRG/providers/Microsoft.KeyVault/vaults/myVault"
```

When your application code runs on a resource with a Managed Identity, it can acquire tokens without any credentials:

```python
# Python example using azure-identity SDK
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# DefaultAzureCredential automatically detects Managed Identity
credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://myvault.vault.azure.net/", credential=credential)

secret = client.get_secret("database-connection-string")
print(f"Secret value: {secret.value}")
```

The `DefaultAzureCredential` class tries multiple authentication methods in order: environment variables, Managed Identity, Azure CLI, Visual Studio Code, and others. In production on Azure, it finds the Managed Identity automatically. On your laptop, it falls back to your Azure CLI login. This makes the same code work everywhere without changes.

---

## Azure RBAC vs Entra ID Roles: The Great Confusion

This is the section that will save you hours of frustration. Azure has **two separate role systems** that operate at different layers, and confusing them is one of the most common mistakes in the Azure ecosystem.

### Entra ID Roles (Directory Roles)

These roles control access to **Entra ID itself**---the directory. They govern who can create users, manage groups, register applications, configure Conditional Access policies, and perform other directory operations.

Examples:
- **Global Administrator**: Full access to Entra ID and all Microsoft services (the "root" of your tenant)
- **User Administrator**: Can create and manage users and groups
- **Application Administrator**: Can manage app registrations and enterprise applications
- **Security Reader**: Read-only access to security features

### Azure RBAC Roles (Resource Roles)

These roles control access to **Azure resources**---VMs, storage accounts, databases, networks, and everything else you deploy. They operate on the management group / subscription / resource group / resource hierarchy.

The four fundamental built-in roles:

| Role | What It Can Do | Scope |
| :--- | :--- | :--- |
| **Owner** | Full access + can assign roles to others | Can manage everything and delegate |
| **Contributor** | Full access to resources, but cannot assign roles | Can create/delete/modify resources |
| **Reader** | View-only access | Can see resources but not change anything |
| **User Access Administrator** | Can only manage role assignments | Can grant/revoke access but not modify resources |

```text
    ┌─────────────────────────────────────────────────────────────┐
    │                     Entra ID Tenant                         │
    │                                                             │
    │  ┌───────────────────────────────────────────────────────┐  │
    │  │         Entra ID Roles (Directory Scope)              │  │
    │  │  Global Admin, User Admin, App Admin, etc.            │  │
    │  │  Controls: Users, Groups, Apps, Policies              │  │
    │  └───────────────────────────────────────────────────────┘  │
    │                                                             │
    │  ┌───────────────────────────────────────────────────────┐  │
    │  │         Azure RBAC Roles (Resource Scope)             │  │
    │  │  Owner, Contributor, Reader, custom roles             │  │
    │  │  Controls: VMs, Storage, Networks, Databases          │  │
    │  │                                                       │  │
    │  │  Scope: Management Group → Subscription →             │  │
    │  │         Resource Group → Resource                     │  │
    │  └───────────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────────┘

    KEY INSIGHT: Global Administrator does NOT automatically have
    Azure RBAC access. They must "elevate" themselves first.
```

This is a critical detail: a **Global Administrator** in Entra ID does **not** automatically have Owner or Contributor access to Azure subscriptions. They can *elevate* themselves to get User Access Administrator at the root scope, but it is not automatic. Conversely, an **Owner** on an Azure subscription cannot create or manage Entra ID users.

```bash
# List Azure RBAC role assignments at subscription scope
az role assignment list --scope "/subscriptions/<sub-id>" -o table

# List all built-in Azure RBAC roles
az role definition list --query "[?roleType=='BuiltInRole'].{Name:roleName, Description:description}" -o table

# Show what a specific role can do
az role definition list --name "Contributor" --query '[0].{Actions:permissions[0].actions, NotActions:permissions[0].notActions}'
```

### Custom RBAC Roles

When built-in roles are too broad or don't fit your needs, you create custom roles. A custom role is a JSON definition that specifies exactly which actions are allowed or denied.

```json
{
  "Name": "VM Operator",
  "Description": "Can start, stop, and restart VMs but not create or delete them",
  "Actions": [
    "Microsoft.Compute/virtualMachines/start/action",
    "Microsoft.Compute/virtualMachines/restart/action",
    "Microsoft.Compute/virtualMachines/deallocate/action",
    "Microsoft.Compute/virtualMachines/powerOff/action",
    "Microsoft.Compute/virtualMachines/read",
    "Microsoft.Compute/virtualMachines/instanceView/read",
    "Microsoft.Resources/subscriptions/resourceGroups/read"
  ],
  "NotActions": [],
  "DataActions": [],
  "NotDataActions": [],
  "AssignableScopes": [
    "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  ]
}
```

```bash
# Create a custom role from a JSON file
az role definition create --role-definition @vm-operator-role.json

# Assign the custom role
az role assignment create \
  --assignee "alice@yourcompany.onmicrosoft.com" \
  --role "VM Operator" \
  --scope "/subscriptions/<sub-id>/resourceGroups/production"

# List custom roles in your subscription
az role definition list --custom-role-only true -o table
```

An important distinction: **Actions** vs **DataActions**. Actions control *management plane* operations (creating, deleting, configuring resources). DataActions control *data plane* operations (reading blobs in storage, sending messages to a queue). The role `Storage Blob Data Reader` uses DataActions, not Actions, because it grants access to the data inside storage, not to the storage account management operations.

---

## Conditional Access: Context-Aware Security

Conditional Access policies are the enforcement engine of Entra ID. They evaluate conditions (who, where, what device, what app) and make access decisions (allow, block, require MFA). Think of them as programmable if/then rules for authentication.

```text
    ┌──────────────────────────────────────────────────────────┐
    │                 Conditional Access Policy                 │
    ├──────────────┬───────────────────────────────────────────┤
    │  Assignments │  Conditions              │  Controls      │
    │  (WHO)       │  (WHERE/WHEN/HOW)        │  (THEN WHAT)   │
    ├──────────────┼───────────────────────────┼────────────────┤
    │ Users/Groups │ Sign-in risk (AI-based)   │ Block access   │
    │ Apps         │ Device platform (iOS,etc) │ Require MFA    │
    │ Roles        │ Location (IP ranges)      │ Require device │
    │              │ Client app type           │ Session limits │
    │              │ Device state              │ App controls   │
    └──────────────┴───────────────────────────┴────────────────┘
```

Common Conditional Access patterns:

1. **Require MFA for all Global Administrators** (this should be your first policy)
2. **Block sign-ins from countries where you have no employees**
3. **Require compliant devices for accessing sensitive applications**
4. **Force re-authentication every 4 hours for Azure portal access**

Conditional Access requires at least Entra ID P1 licensing. You can view and manage policies through the Azure portal or Microsoft Graph API:

```bash
# List Conditional Access policies via Graph API
az rest --method GET \
  --url "https://graph.microsoft.com/v1.0/identity/conditionalAccess/policies" \
  --query "value[].{Name:displayName, State:state}"
```

---

## Did You Know?

1. **Microsoft Entra ID was renamed from Azure Active Directory in July 2023**, but the CLI commands still use `az ad` (not `az entra`), the PowerShell module is still `AzureAD`, and many API endpoints still reference `azure-active-directory`. This naming mismatch will persist for years because changing API surfaces would break millions of integrations worldwide.

2. **A single Entra ID tenant can contain up to 50,000 app registrations and 300,000 service principals** (as of 2025 limits). Large enterprises with extensive Microsoft 365 usage often approach the service principal limit because every Microsoft first-party app, third-party SaaS integration, and internal tool creates one.

3. **Managed Identities use the same token endpoint as any OIDC identity**, specifically the Azure Instance Metadata Service (IMDS) at `169.254.169.254`. When your code calls `DefaultAzureCredential()`, it makes an HTTP request to `http://169.254.169.254/metadata/identity/oauth2/token`. This link-local address is only accessible from within the Azure resource---it is unreachable from the internet, which is what makes Managed Identities secure by design.

4. **Azure RBAC evaluates role assignments in under 5 milliseconds per API call**, but propagation of a new role assignment can take up to 10 minutes. This delay catches people during deployments---you assign a role and immediately try to use it, and it fails. Always build in a wait or retry mechanism when programmatically assigning roles.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| Using client secrets for service principals in production workloads on Azure | It's the "easy" way shown in many tutorials | Use Managed Identities for Azure-hosted workloads. Use OIDC federated credentials for external CI/CD. |
| Granting Owner at subscription scope "just to get things working" | Contributor seems insufficient during initial setup | Identify the specific actions needed and use a narrower built-in role or create a custom role. |
| Confusing Entra ID roles with Azure RBAC roles | The naming is genuinely confusing, and both appear in the portal | Remember: Entra ID roles = directory operations. RBAC roles = resource operations. Check which scope you need. |
| Not using groups for role assignments | It seems faster to assign roles directly to users | Always assign RBAC roles to groups, then manage group membership. This scales and is auditable. |
| Leaving orphaned service principal secrets active | Teams create secrets for one-off tasks and forget them | Set short expiration dates. Audit with `az ad app credential list`. Use workload identity federation. |
| Setting system-assigned identity when user-assigned is more appropriate | System-assigned is the default in most tutorials | If multiple resources need the same identity/permissions, use user-assigned. It simplifies role management. |
| Not restricting the AssignableScopes of custom roles | Developers copy examples that use subscription scope | Scope custom roles to the narrowest possible scope (resource group when possible). |
| Skipping Conditional Access for break-glass accounts | Emergency accounts seem like they should bypass everything | Create Conditional Access policies for break-glass accounts that require MFA but allow access from any location. Monitor these accounts with alerts. |

---

## Quiz

<details>
<summary>1. What is the fundamental difference between a Management Group and a Subscription in Azure?</summary>

A Management Group is a governance container used to organize subscriptions into hierarchies for applying policies and access control at scale. A Subscription is both a billing boundary and an access control boundary where resources actually live. Management Groups cannot contain resources directly---they only contain other Management Groups or Subscriptions. Policies and RBAC assigned at a Management Group level are inherited by all Subscriptions beneath it, making Management Groups the tool for enterprise-wide governance.
</details>

<details>
<summary>2. You assign the Global Administrator role to a user. Can they immediately create and delete Azure VMs? Why or why not?</summary>

No, not immediately. Global Administrator is an Entra ID directory role, not an Azure RBAC role. It grants full control over the directory (users, groups, apps, policies) but does not automatically include Azure resource management permissions. A Global Administrator must first "elevate" their access in the Azure portal (Properties > Access management for Azure resources), which grants them the User Access Administrator role at the root scope (/). From there, they can assign themselves an Azure RBAC role like Owner or Contributor on the relevant subscription.
</details>

<details>
<summary>3. When should you use a User-Assigned Managed Identity instead of a System-Assigned one?</summary>

Use a User-Assigned Managed Identity when multiple resources need the same set of permissions (e.g., three VMs all needing access to the same Key Vault and Storage Account). With system-assigned identities, you would need to create three separate role assignments. With a user-assigned identity, you create one identity, assign roles once, and attach it to all three VMs. User-assigned identities are also better for pre-provisioning scenarios where you need the identity to exist before the resource is created, or when the resource lifecycle and the identity lifecycle should be independent.
</details>

<details>
<summary>4. What is the difference between Actions and DataActions in an Azure RBAC role definition?</summary>

Actions control management plane operations---creating, configuring, and deleting Azure resources. For example, `Microsoft.Storage/storageAccounts/write` lets you create or modify a storage account. DataActions control data plane operations---interacting with the data inside a resource. For example, `Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read` lets you read the contents of blobs. A role like Contributor has broad Actions but zero DataActions, meaning a Contributor can manage a storage account but cannot read the blobs inside it.
</details>

<details>
<summary>5. Why is it a security risk to assign RBAC roles directly to individual users instead of groups?</summary>

Assigning roles directly to users creates several problems. First, it does not scale---when you have 50 engineers, managing individual assignments becomes unworkable. Second, it is not auditable---you cannot quickly answer "who has access to what" without checking every resource. Third, when someone leaves the team, you must remember to remove every individual assignment instead of just removing them from a group. Fourth, it violates the principle of least privilege because over time, individuals accumulate role assignments that were meant to be temporary, and nobody cleans them up.
</details>

<details>
<summary>6. An application running on an Azure VM needs to read secrets from Key Vault. Describe the most secure way to set this up.</summary>

Enable a Managed Identity on the VM (system-assigned if the identity lifecycle should match the VM, user-assigned if shared across resources). Then create an RBAC role assignment granting the Managed Identity the "Key Vault Secrets User" role, scoped to the specific Key Vault resource (not the resource group or subscription). In the application code, use `DefaultAzureCredential` from the Azure SDK, which will automatically detect and use the Managed Identity to acquire tokens. No secrets, connection strings, or credentials are stored anywhere in code, configuration files, or environment variables.
</details>

<details>
<summary>7. What happens to a system-assigned Managed Identity when you delete the Azure resource it is attached to?</summary>

The system-assigned Managed Identity is automatically deleted along with the resource. This includes the service principal in Entra ID and all role assignments associated with that identity. This is one of the advantages of system-assigned identities---there are no orphaned identities to clean up. However, it is also a risk: if you accidentally delete and recreate a VM, the new VM gets a new identity with a different principal ID, and you must recreate all role assignments.
</details>

---

## Hands-On Exercise: Custom RBAC Role + Managed Identity on a VM

In this exercise, you will create a custom RBAC role, set up a VM with a Managed Identity, and verify that the identity can only perform the actions allowed by the custom role.

**Prerequisites**: Azure CLI installed and authenticated (`az login`), a resource group to work in.

### Task 1: Create a Resource Group for the Exercise

```bash
# Set variables
RG_NAME="kubedojo-identity-lab"
LOCATION="eastus2"

# Create the resource group
az group create --name "$RG_NAME" --location "$LOCATION"
```

<details>
<summary>Verify Task 1</summary>

```bash
az group show --name "$RG_NAME" --query '{Name:name, Location:location, State:properties.provisioningState}' -o table
```

You should see the resource group with `Succeeded` state.
</details>

### Task 2: Create a Custom RBAC Role (Storage Blob Lister)

Create a custom role that can only list storage accounts and list blobs---but not read, write, or delete blob contents.

```bash
# Create the role definition file
cat > /tmp/blob-lister-role.json << 'EOF'
{
  "Name": "Storage Blob Lister",
  "Description": "Can list storage accounts and enumerate blobs but cannot read or modify blob content",
  "Actions": [
    "Microsoft.Storage/storageAccounts/read",
    "Microsoft.Storage/storageAccounts/listkeys/action",
    "Microsoft.Resources/subscriptions/resourceGroups/read"
  ],
  "DataActions": [
    "Microsoft.Storage/storageAccounts/blobServices/containers/read",
    "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read"
  ],
  "NotDataActions": [
    "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/write",
    "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/delete"
  ],
  "AssignableScopes": [
    "/subscriptions/YOUR_SUB_ID"
  ]
}
EOF

# Replace with your subscription ID
SUB_ID=$(az account show --query id -o tsv)
sed -i '' "s|YOUR_SUB_ID|$SUB_ID|g" /tmp/blob-lister-role.json 2>/dev/null || \
sed -i "s|YOUR_SUB_ID|$SUB_ID|g" /tmp/blob-lister-role.json

# Create the custom role
az role definition create --role-definition @/tmp/blob-lister-role.json
```

<details>
<summary>Verify Task 2</summary>

```bash
az role definition list --name "Storage Blob Lister" \
  --query '[0].{Name:roleName, Type:roleType, Actions:permissions[0].actions}' -o json
```

You should see the custom role with `CustomRole` type and the actions you defined.
</details>

### Task 3: Create a Storage Account with a Test Blob

```bash
# Create storage account (name must be globally unique)
STORAGE_NAME="kubedojolab$(openssl rand -hex 4)"
az storage account create \
  --name "$STORAGE_NAME" \
  --resource-group "$RG_NAME" \
  --location "$LOCATION" \
  --sku Standard_LRS

# Create a container
az storage container create \
  --name "testcontainer" \
  --account-name "$STORAGE_NAME" \
  --auth-mode login

# Upload a test blob
echo "Hello from KubeDojo identity lab" > /tmp/testfile.txt
az storage blob upload \
  --container-name "testcontainer" \
  --file /tmp/testfile.txt \
  --name "testfile.txt" \
  --account-name "$STORAGE_NAME" \
  --auth-mode login
```

<details>
<summary>Verify Task 3</summary>

```bash
az storage blob list --container-name "testcontainer" \
  --account-name "$STORAGE_NAME" --auth-mode login \
  --query '[].name' -o tsv
```

You should see `testfile.txt`.
</details>

### Task 4: Create a VM with a System-Assigned Managed Identity

```bash
az vm create \
  --resource-group "$RG_NAME" \
  --name "identity-lab-vm" \
  --image Ubuntu2204 \
  --size Standard_B1s \
  --admin-username azureuser \
  --generate-ssh-keys \
  --assign-identity '[system]' \
  --output table
```

<details>
<summary>Verify Task 4</summary>

```bash
az vm identity show --resource-group "$RG_NAME" --name "identity-lab-vm" \
  --query '{Type:type, PrincipalId:principalId}' -o table
```

You should see `SystemAssigned` type and a principal ID (a GUID).
</details>

### Task 5: Assign the Custom Role to the VM's Managed Identity

```bash
# Get the VM's managed identity principal ID
VM_PRINCIPAL_ID=$(az vm identity show \
  --resource-group "$RG_NAME" \
  --name "identity-lab-vm" \
  --query principalId -o tsv)

# Assign the custom role scoped to the storage account
STORAGE_ID=$(az storage account show --name "$STORAGE_NAME" --resource-group "$RG_NAME" --query id -o tsv)

az role assignment create \
  --assignee "$VM_PRINCIPAL_ID" \
  --role "Storage Blob Lister" \
  --scope "$STORAGE_ID"

# Wait for propagation
echo "Waiting 60 seconds for role assignment propagation..."
sleep 60
```

<details>
<summary>Verify Task 5</summary>

```bash
az role assignment list \
  --assignee "$VM_PRINCIPAL_ID" \
  --scope "$STORAGE_ID" \
  --query '[].{Role:roleDefinitionName, Scope:scope}' -o table
```

You should see `Storage Blob Lister` assigned at the storage account scope.
</details>

### Task 6: Test the Managed Identity from Inside the VM

SSH into the VM and verify that the Managed Identity can list blobs but cannot delete them.

```bash
# SSH into the VM
VM_IP=$(az vm show -g "$RG_NAME" -n "identity-lab-vm" -d --query publicIpAddress -o tsv)
ssh azureuser@"$VM_IP"

# Inside the VM, install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login using the VM's managed identity
az login --identity

# This should SUCCEED: list blobs
az storage blob list --container-name "testcontainer" \
  --account-name "$STORAGE_NAME" --auth-mode login \
  --query '[].name' -o tsv

# This should SUCCEED: read blob content
az storage blob download --container-name "testcontainer" \
  --name "testfile.txt" --file /tmp/downloaded.txt \
  --account-name "$STORAGE_NAME" --auth-mode login
cat /tmp/downloaded.txt

# This should FAIL: delete blob (NotDataActions blocks this)
az storage blob delete --container-name "testcontainer" \
  --name "testfile.txt" \
  --account-name "$STORAGE_NAME" --auth-mode login
# Expected: AuthorizationPermissionMismatch error
```

<details>
<summary>Verify Task 6</summary>

If the list and read operations succeed but the delete operation returns an authorization error, you have successfully configured a custom RBAC role with a Managed Identity. The identity can enumerate and read blobs but cannot modify or delete them.
</details>

### Cleanup

```bash
# Delete everything
az group delete --name "$RG_NAME" --yes --no-wait
az role definition delete --name "Storage Blob Lister"
```

### Success Criteria

- [ ] Custom RBAC role "Storage Blob Lister" created with specific actions and data actions
- [ ] Storage account created with a test blob in a container
- [ ] VM created with system-assigned Managed Identity enabled
- [ ] Custom role assigned to the VM's Managed Identity at storage account scope
- [ ] From inside the VM, Managed Identity can list and read blobs
- [ ] From inside the VM, Managed Identity cannot delete blobs (authorization error)

---

## Next Module

[Module 2: Virtual Networks (VNet)](module-2-vnet.md) --- Learn how Azure networking works, from VNets and subnets to NSGs, peering, and the hub-and-spoke architecture that every enterprise uses.
