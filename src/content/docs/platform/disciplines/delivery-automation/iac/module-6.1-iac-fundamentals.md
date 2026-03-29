---
title: "Module 6.1: IaC Fundamentals & Maturity Model"
slug: platform/disciplines/delivery-automation/iac/module-6.1-iac-fundamentals
sidebar:
  order: 2
---
> **Complexity**: `[MEDIUM]`
>
> **Time to Complete**: 35-40 minutes
>
> **Prerequisites**: [Module 1: Infrastructure as Code](../../../../prerequisites/modern-devops/module-1.1-infrastructure-as-code/)
>
> **Track**: Platform Engineering - IaC Discipline

---

**January 2019. A Fortune 500 financial services company attempts to migrate to the cloud and discovers their infrastructure is completely undocumented.**

The migration team opened tickets to understand the existing infrastructure. The responses were alarming: "I think Dave set that up, but he left two years ago." "That server? No idea what it does, but don't touch it." "We call it the mystery box—it's been running for seven years."

Three months into the migration, they'd mapped only 40% of their infrastructure. The rest existed as tribal knowledge, scattered scripts, and "just SSH in and check" procedures. **The migration that was budgeted for 18 months took 4 years and cost $340 million over budget.**

The post-mortem was brutal: "We didn't have infrastructure. We had accumulated technical debt shaped like servers."

Meanwhile, their competitor—a company half their size—completed a similar migration in 8 months. The difference? Every piece of infrastructure existed as code. Every change was version-controlled. Every environment could be recreated from scratch in hours.

This module teaches Infrastructure as Code fundamentals: not just the tools, but the principles, patterns, and maturity journey that separates organizations drowning in infrastructure chaos from those who treat infrastructure as a competitive advantage.

---

## Why This Module Matters

Infrastructure as Code isn't just about automation—it's about treating infrastructure with the same rigor as application code. Version control. Code review. Testing. Continuous integration. These practices transformed software development. IaC brings them to infrastructure.

Understanding IaC fundamentals helps you:
- Design infrastructure that's reproducible and auditable
- Choose the right tools for your organization's maturity level
- Build patterns that scale from startup to enterprise
- Avoid the "snowflake server" antipattern that kills agility

---

## What You'll Learn

- The IaC maturity model and where your organization fits
- Declarative vs imperative approaches and when to use each
- State management concepts that apply across all tools
- Version control strategies for infrastructure
- Environment parity and promotion patterns
- Common antipatterns and how to avoid them

---

## Part 1: The IaC Maturity Model

### 1.1 The Five Levels of IaC Maturity

```
IaC MATURITY MODEL
═══════════════════════════════════════════════════════════════

Level 0: MANUAL
─────────────────────────────────────────────────────────────
• Infrastructure created via console/UI clicks
• Changes undocumented or in wikis
• "Works on my machine" syndrome
• Recovery: Days to weeks
• Example: "Click through AWS console to create EC2"

Level 1: SCRIPTED
─────────────────────────────────────────────────────────────
• Bash/PowerShell scripts for common tasks
• Scripts may not be idempotent
• Partial automation, still manual decisions
• Recovery: Hours to days
• Example: "Run setup.sh to create the server"

Level 2: DECLARATIVE
─────────────────────────────────────────────────────────────
• Infrastructure defined in declarative configs
• Terraform, CloudFormation, or similar tools
• Version controlled but may not be reviewed
• Recovery: Minutes to hours
• Example: "terraform apply creates everything"

Level 3: COLLABORATIVE
─────────────────────────────────────────────────────────────
• Pull request workflow for all changes
• Code review required for infrastructure
• Automated validation (linting, security scanning)
• Recovery: Minutes
• Example: "PR → Review → Merge → Auto-apply"

Level 4: CONTINUOUS
─────────────────────────────────────────────────────────────
• GitOps: Git is the source of truth
• Continuous reconciliation
• Self-healing infrastructure
• Full audit trail
• Recovery: Automatic
• Example: "Push to Git → ArgoCD/Flux syncs state"

Level 5: SELF-SERVICE
─────────────────────────────────────────────────────────────
• Platform teams provide infrastructure APIs
• Developers request infrastructure declaratively
• Guardrails prevent misuse automatically
• Cost and compliance built-in
• Recovery: Automatic with self-service rebuild
• Example: "Developer creates CR → Platform provisions"
```

### 1.2 Assessing Your Organization

```
MATURITY ASSESSMENT QUESTIONS
═══════════════════════════════════════════════════════════════

REPRODUCIBILITY
─────────────────────────────────────────────────────────────
Q: Can you recreate your production environment from scratch?

Level 0: "No, we'd have to figure it out as we go"
Level 2: "Yes, but it takes a day of manual steps"
Level 4: "Yes, terraform apply and wait 30 minutes"
Level 5: "Yes, it's automatically recreated if destroyed"

CHANGE MANAGEMENT
─────────────────────────────────────────────────────────────
Q: How do infrastructure changes get made?

Level 0: "Someone SSHs in and makes changes"
Level 1: "We have scripts, but anyone can run them"
Level 3: "All changes go through PR review"
Level 5: "Developers request via API, platform provisions"

DRIFT DETECTION
─────────────────────────────────────────────────────────────
Q: Do you know if actual state matches desired state?

Level 0: "What's drift?"
Level 2: "We run terraform plan occasionally"
Level 4: "Continuous monitoring, alerts on drift"
Level 5: "Auto-remediation brings state back"

DISASTER RECOVERY
─────────────────────────────────────────────────────────────
Q: How long to recover from total infrastructure loss?

Level 0: "Weeks, if ever"
Level 2: "Days—we'd need to debug the scripts"
Level 4: "Hours—apply from Git"
Level 5: "Minutes—auto-rebuild from state"
```

---

## Part 2: Declarative vs Imperative

### 2.1 Understanding the Paradigms

```
DECLARATIVE VS IMPERATIVE
═══════════════════════════════════════════════════════════════

IMPERATIVE: "How to get there"
─────────────────────────────────────────────────────────────
You specify the exact steps to achieve the desired state.

    # Bash script (imperative)
    aws ec2 run-instances --image-id ami-12345 --count 1
    aws ec2 wait instance-running --instance-ids $INSTANCE_ID
    aws ec2 create-tags --resources $INSTANCE_ID --tags Key=Name,Value=web

    Problem: What if instance already exists?
    Problem: What if it exists but with wrong tags?
    Problem: Running again creates ANOTHER instance!

DECLARATIVE: "What should exist"
─────────────────────────────────────────────────────────────
You specify the desired end state. The tool figures out how.

    # Terraform (declarative)
    resource "aws_instance" "web" {
      ami           = "ami-12345"
      instance_type = "t3.micro"
      tags = {
        Name = "web"
      }
    }

    Benefit: Run multiple times, same result (idempotent)
    Benefit: Tool calculates delta from current state
    Benefit: Can show plan before applying

COMPARISON
─────────────────────────────────────────────────────────────
                    Imperative          Declarative
                    ─────────────       ─────────────
Idempotent?         Usually no          Yes
Learning curve      Lower               Higher
Flexibility         Maximum             Constrained
Debugging           Step-by-step        State comparison
Rollback            Manual              Often automatic
Example tools       Bash, Ansible*      Terraform, CF

*Ansible can be both depending on how you use it
```

### 2.2 When to Use Each

```
DECISION MATRIX
═══════════════════════════════════════════════════════════════

USE DECLARATIVE WHEN:
─────────────────────────────────────────────────────────────
✓ Managing cloud infrastructure (VMs, networks, databases)
✓ State needs to be tracked over time
✓ Multiple people manage the same infrastructure
✓ You need drift detection
✓ Rollback capability is important

USE IMPERATIVE WHEN:
─────────────────────────────────────────────────────────────
✓ One-time migration scripts
✓ Complex conditional logic
✓ Bootstrapping before declarative tools work
✓ Emergency procedures
✓ Tasks that aren't infrastructure (data migration)

HYBRID APPROACH (Common in practice)
─────────────────────────────────────────────────────────────
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Bootstrap (Imperative)                                │
│  └── Install Terraform, configure backends             │
│                                                         │
│  Infrastructure (Declarative)                          │
│  └── Terraform/CloudFormation for resources            │
│                                                         │
│  Configuration (Declarative or Imperative)             │
│  └── Ansible for OS config, or cloud-init              │
│                                                         │
│  Application (Declarative)                             │
│  └── Kubernetes manifests, Helm charts                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 2.3 Configuration as Code (CaC) vs Infrastructure as Code (IaC)

You will sometimes see the term **Configuration as Code (CaC)** alongside IaC. They are related but distinct practices:

```
CaC vs IaC
═══════════════════════════════════════════════════════════════

INFRASTRUCTURE AS CODE (IaC)
─────────────────────────────────────────────────────────────
Manages: Servers, networks, databases, load balancers, DNS
Tools:   Terraform, Pulumi, CloudFormation, Crossplane
Scope:   "The platform your applications run on"
Example: Provisioning an EKS cluster with 3 node groups

CONFIGURATION AS CODE (CaC)
─────────────────────────────────────────────────────────────
Manages: Application settings, feature flags, runtime config
Tools:   Ansible (config), ConfigMaps, Consul, LaunchDarkly
Scope:   "How your applications behave at runtime"
Example: Setting log levels, enabling a feature flag, tuning
         connection pool sizes

KEY DISTINCTION
─────────────────────────────────────────────────────────────
IaC answers:  "What infrastructure exists?"
CaC answers:  "How is the software on that infrastructure configured?"

In practice, they overlap. A Kubernetes ConfigMap is CaC (app
settings), but the cluster it lives on is IaC. Both should be
version-controlled, reviewed, and tested.
```

---

## Part 3: State Management Concepts

### 3.1 Why State Matters

```
THE STATE PROBLEM
═══════════════════════════════════════════════════════════════

Declarative IaC needs to know:
1. What SHOULD exist (your code)
2. What DOES exist (actual infrastructure)
3. What it CREATED before (state)

WHY STATE IS NECESSARY
─────────────────────────────────────────────────────────────

Without state, the tool can't know:
• Did I create this resource, or did someone else?
• What's the resource ID for updates/deletes?
• What was the previous configuration?

    Code says: "Create 3 servers"
    Reality: 3 servers exist

    Without state: Create 3 more? Or is this the same 3?
    With state: "I created these 3. IDs match. No changes."

STATE STORAGE OPTIONS
─────────────────────────────────────────────────────────────
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  LOCAL FILE (Development)                              │
│  ├── terraform.tfstate on disk                         │
│  ├── Simple but doesn't scale                          │
│  └── No locking, no sharing                            │
│                                                         │
│  REMOTE BACKEND (Production)                           │
│  ├── S3 + DynamoDB (AWS)                               │
│  ├── GCS + Cloud Storage (GCP)                         │
│  ├── Azure Blob + Table Storage                        │
│  ├── Terraform Cloud                                   │
│  └── Features: Locking, versioning, encryption         │
│                                                         │
│  KUBERNETES (Cloud-native)                             │
│  ├── Crossplane stores state in etcd                   │
│  ├── State is Kubernetes resources                     │
│  └── Reconciliation loop manages drift                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 3.2 State Locking and Consistency

```
CONCURRENT ACCESS PROBLEM
═══════════════════════════════════════════════════════════════

    Time    Alice                   Bob
    ─────   ─────────────────────   ─────────────────────
    T0      Reads state
    T1                              Reads state (same)
    T2      Plans: Add server
    T3                              Plans: Add server
    T4      Applies: Creates srv-1
    T5                              Applies: Creates srv-2
    T6      Writes state (srv-1)
    T7                              Writes state (srv-2)

    Result: State says srv-2 exists
            srv-1 is ORPHANED (no state reference)

THIS IS WHY LOCKING EXISTS
─────────────────────────────────────────────────────────────

With state locking:

    Time    Alice                   Bob
    ─────   ─────────────────────   ─────────────────────
    T0      Acquires lock ✓
    T1      Reads state
    T2                              Tries lock: BLOCKED
    T3      Plans, applies
    T4      Writes state
    T5      Releases lock
    T6                              Acquires lock ✓
    T7                              Reads UPDATED state

    Result: Both changes tracked correctly
```

---

## Part 4: Version Control Strategies

### 4.1 Repository Structure Patterns

```
REPOSITORY PATTERNS
═══════════════════════════════════════════════════════════════

MONOREPO (All infrastructure in one repo)
─────────────────────────────────────────────────────────────
infrastructure/
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   └── terraform.tfvars
│   ├── staging/
│   └── prod/
├── modules/
│   ├── vpc/
│   ├── eks/
│   └── rds/
└── global/
    ├── iam/
    └── dns/

✓ Easy to share modules
✓ Single PR can update all environments
✓ Easier to maintain consistency
✗ Large blast radius
✗ Slower CI for unrelated changes

POLYREPO (Separate repos per component/team)
─────────────────────────────────────────────────────────────
repo: infra-networking
repo: infra-eks
repo: infra-databases
repo: team-alpha-infra
repo: team-beta-infra

✓ Clear ownership
✓ Independent release cycles
✓ Smaller blast radius
✗ Module versioning complexity
✗ Harder to maintain consistency
✗ Cross-repo changes are painful

HYBRID (Monorepo for platform, polyrepo for teams)
─────────────────────────────────────────────────────────────
repo: platform-infrastructure (platform team)
├── modules/       (shared modules)
├── networking/
├── kubernetes/
└── security/

repo: team-alpha-infra (team alpha)
├── uses modules from platform-infrastructure
└── team-specific resources

repo: team-beta-infra (team beta)
└── same pattern

✓ Balance of control and autonomy
✓ Platform team governs shared resources
✓ Teams own their infrastructure
```

### 4.2 Branching and Environment Promotion

```
ENVIRONMENT PROMOTION PATTERNS
═══════════════════════════════════════════════════════════════

PATTERN 1: Directory per Environment
─────────────────────────────────────────────────────────────
All environments in same repo, same branch.

    main branch:
    ├── dev/main.tf      ← Changes here first
    ├── staging/main.tf  ← Promoted after dev testing
    └── prod/main.tf     ← Promoted after staging

    Workflow:
    1. PR changes to dev/
    2. Test in dev
    3. PR changes to staging/ (copy from dev)
    4. Test in staging
    5. PR changes to prod/ (copy from staging)

PATTERN 2: Branch per Environment
─────────────────────────────────────────────────────────────
Same code, different branches trigger different environments.

    main     → deploys to prod
    staging  → deploys to staging
    dev      → deploys to dev

    Workflow:
    1. PR to dev branch, merge, auto-deploys
    2. PR from dev to staging, merge, auto-deploys
    3. PR from staging to main, merge, auto-deploys

PATTERN 3: GitOps with Environment Overlays
─────────────────────────────────────────────────────────────
Base configuration with environment-specific patches.

    main branch:
    ├── base/
    │   ├── main.tf      ← Shared configuration
    │   └── variables.tf
    └── overlays/
        ├── dev/         ← dev-specific values
        ├── staging/
        └── prod/

    Workflow:
    1. Change base/ for structural changes
    2. Change overlays/ for environment-specific values
    3. CI applies base + overlay for each environment
```

---

## Part 5: Environment Parity

### 5.1 The Parity Principle

```
ENVIRONMENT PARITY
═══════════════════════════════════════════════════════════════

"Dev, staging, and prod should be as similar as possible."

WHY PARITY MATTERS
─────────────────────────────────────────────────────────────
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Without Parity:                                       │
│  "It works in dev" → breaks in prod                    │
│  Different versions, configs, network topologies       │
│  Production-only bugs discovered by customers          │
│                                                         │
│  With Parity:                                          │
│  Same code deploys everywhere                          │
│  Only size/scale differs (smaller dev instances)       │
│  Bugs found in dev/staging, not prod                   │
│                                                         │
└─────────────────────────────────────────────────────────┘

WHAT SHOULD BE THE SAME
─────────────────────────────────────────────────────────────
✓ Infrastructure architecture (same services, same layout)
✓ Software versions (OS, runtime, dependencies)
✓ Configuration structure (same keys, different values)
✓ Security controls (same policies, maybe relaxed in dev)
✓ Monitoring and logging (same metrics, different thresholds)

WHAT CAN DIFFER
─────────────────────────────────────────────────────────────
✓ Scale (fewer nodes in dev)
✓ Instance sizes (smaller in dev)
✓ Redundancy (single AZ in dev, multi-AZ in prod)
✓ Data (synthetic in dev, real in prod)
✓ Secrets (different credentials per environment)
```

### 5.2 Implementing Parity with IaC

```
PARITY IMPLEMENTATION
═══════════════════════════════════════════════════════════════

# variables.tf - Define what varies
variable "environment" {
  description = "Environment name"
  type        = string
}

variable "instance_count" {
  description = "Number of instances"
  type        = number
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
}

# main.tf - Same structure everywhere
resource "aws_instance" "app" {
  count         = var.instance_count
  ami           = data.aws_ami.app.id  # Same AMI
  instance_type = var.instance_type     # Different size

  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# environments/dev.tfvars
environment    = "dev"
instance_count = 1
instance_type  = "t3.small"

# environments/staging.tfvars
environment    = "staging"
instance_count = 2
instance_type  = "t3.medium"

# environments/prod.tfvars
environment    = "prod"
instance_count = 6
instance_type  = "t3.large"

SAME CODE, DIFFERENT SCALE
─────────────────────────────────────────────────────────────
    terraform apply -var-file=environments/dev.tfvars
    terraform apply -var-file=environments/staging.tfvars
    terraform apply -var-file=environments/prod.tfvars
```

---

## Part 6: Common Antipatterns

### 6.1 Antipatterns to Avoid

```
IaC ANTIPATTERNS
═══════════════════════════════════════════════════════════════

ANTIPATTERN 1: Snowflake Servers
─────────────────────────────────────────────────────────────
Problem: Each server is manually configured, unique
Symptom: "Don't touch production—nobody knows how it works"
Fix: Immutable infrastructure. Rebuild, don't repair.

ANTIPATTERN 2: Configuration Drift
─────────────────────────────────────────────────────────────
Problem: Manual changes made outside IaC
Symptom: terraform plan shows unexpected changes
Fix: Continuous drift detection, block console access

ANTIPATTERN 3: Copy-Paste Infrastructure
─────────────────────────────────────────────────────────────
Problem: Duplicated code across environments
Symptom: 3 copies of the same Terraform, all slightly different
Fix: Modules with environment-specific variables

ANTIPATTERN 4: Monster Modules
─────────────────────────────────────────────────────────────
Problem: One module that does everything
Symptom: 5000-line main.tf, 45-minute terraform apply
Fix: Small, composable modules with single responsibility

ANTIPATTERN 5: State File Chaos
─────────────────────────────────────────────────────────────
Problem: State files checked into Git, or lost
Symptom: "Where's the state file?" or merge conflicts in .tfstate
Fix: Remote backend with locking from day one

ANTIPATTERN 6: Secret Sprawl
─────────────────────────────────────────────────────────────
Problem: Secrets in terraform.tfvars or plain text
Symptom: Credentials in Git history
Fix: Secret manager (Vault, AWS Secrets Manager) + references
```

> **War Story: The $2.3 Million Snowflake Server**
>
> **March 2020. A logistics company's entire order processing system runs on one server that nobody understands.**
>
> The server had been running for 9 years. The original engineer had left. It ran a custom application with hand-tuned kernel parameters, undocumented cron jobs, and configuration scattered across 47 files.
>
> When the server's hardware failed, the recovery took 11 days. The team spent the first 3 days just figuring out what the server did. The next 5 days were spent recreating the configuration from memory and log archaeology. The final 3 days were debugging why the new server didn't work the same way.
>
> **The cost:**
> - $1.4 million in lost orders during the outage
> - $600K in expedited shipping to fulfill delayed orders
> - $300K in engineering overtime
>
> **The fix:** They spent 6 months converting everything to IaC. The server configuration is now 340 lines of Ansible. Recovery time: 47 minutes.

---

## Did You Know?

- **The term "Infrastructure as Code"** was popularized by Andrew Clay Shafer and Patrick Debois around 2008-2009, the same people who coined "DevOps." The concepts existed earlier, but the term crystallized the practice.

- **NASA's Mars missions** use IaC principles. Every configuration for flight software is version-controlled and reproducible. The Mars 2020 Perseverance rover's software deployment process influenced modern GitOps practices.

- **The US Department of Defense** mandates IaC for cloud deployments. Their Cloud Computing Security Requirements Guide (SRG) requires that "infrastructure configurations shall be defined in machine-readable formats and version controlled."

- **Terraform's state file format** hasn't fundamentally changed since 2014. The backward compatibility has been maintained across 10+ years and hundreds of releases—a testament to the importance of state management.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Starting with complex tools | Overwhelmed, abandoned | Start simple, grow maturity |
| No remote state from day one | Lost state, conflicts | Configure backend immediately |
| Manual changes "just this once" | Drift accumulates | Block console, require PRs |
| Not testing IaC changes | Broken prod deployments | Plan in CI, apply in CD |
| Hardcoded values everywhere | Can't reuse code | Variables and modules |
| Giant monolithic configs | Slow, risky changes | Small, focused modules |

---

## Quiz

1. **What are the five levels of IaC maturity, and what distinguishes Level 4 (Continuous) from Level 3 (Collaborative)?**
   <details>
   <summary>Answer</summary>

   **The five levels:**
   - Level 0: Manual (console clicks)
   - Level 1: Scripted (bash/PowerShell)
   - Level 2: Declarative (Terraform/CF)
   - Level 3: Collaborative (PR workflow)
   - Level 4: Continuous (GitOps)
   - Level 5: Self-Service (Platform APIs)

   **Level 3 vs Level 4:**
   - Level 3: Changes go through PR review, but apply is still triggered manually or semi-automatically
   - Level 4: Git IS the source of truth. Continuous reconciliation automatically syncs actual state to desired state. Self-healing—if someone makes a manual change, it's automatically reverted.

   Key difference: Level 3 is "GitOps lite" (Git for versioning), Level 4 is true GitOps (Git as single source of truth with continuous reconciliation).
   </details>

2. **Explain why declarative IaC is idempotent but imperative scripts typically are not.**
   <details>
   <summary>Answer</summary>

   **Idempotent** = Running multiple times produces the same result as running once.

   **Declarative is idempotent because:**
   - You declare the desired end state
   - The tool compares desired vs actual
   - Only makes changes to reach desired state
   - If already at desired state, does nothing

   ```
   Declarative: "3 servers should exist"
   Run 1: Creates 3 servers
   Run 2: 3 exist, 3 desired, no changes
   Run 3: Same—no changes
   ```

   **Imperative is NOT idempotent because:**
   - You specify the steps to execute
   - Script runs those steps regardless of current state
   - Running again repeats the actions

   ```
   Imperative: "Create 3 servers"
   Run 1: Creates 3 servers (total: 3)
   Run 2: Creates 3 more (total: 6)
   Run 3: Creates 3 more (total: 9)
   ```

   Making imperative scripts idempotent requires explicit checks, which adds complexity.
   </details>

3. **An organization has infrastructure in 3 environments (dev, staging, prod) with slight variations in each. They're experiencing "configuration drift" between environments. Design a solution using IaC principles.**
   <details>
   <summary>Answer</summary>

   **Problem:** Environments have diverged, making promotion unreliable.

   **Solution: Modules + Environment Variables**

   ```
   infrastructure/
   ├── modules/
   │   └── application/
   │       ├── main.tf      # Common structure
   │       ├── variables.tf # Parameterized differences
   │       └── outputs.tf
   └── environments/
       ├── dev/
       │   └── main.tf      # Calls module with dev values
       ├── staging/
       │   └── main.tf      # Calls module with staging values
       └── prod/
           └── main.tf      # Calls module with prod values
   ```

   **environments/dev/main.tf:**
   ```hcl
   module "app" {
     source         = "../../modules/application"
     environment    = "dev"
     instance_count = 1
     instance_type  = "t3.small"
   }
   ```

   **Key principles:**
   1. Single module defines the structure (enforces parity)
   2. Environment-specific values passed as variables
   3. Only allowed differences are parameterized
   4. Drift detected by comparing plans across environments
   </details>

4. **Why is state locking critical, and what happens if two engineers run `terraform apply` simultaneously without locking?**
   <details>
   <summary>Answer</summary>

   **Without locking, race conditions cause:**

   1. **Orphaned resources:** Both read the same state, both create resources, only one update wins. Resources from the "losing" apply become untracked.

   2. **State corruption:** Concurrent writes can create invalid state files with partial or conflicting information.

   3. **Duplicate resources:** Each apply thinks it needs to create resources that don't exist (in their view of state).

   **Example scenario:**
   ```
   T0: Alice reads state (0 servers)
   T1: Bob reads state (0 servers)
   T2: Alice creates server-a, updates state to [server-a]
   T3: Bob creates server-b, updates state to [server-b]
       (Bob's write overwrites Alice's)

   Result: Two servers exist, state only knows about server-b
           server-a is orphaned—can't be managed
   ```

   **With locking:**
   - First apply acquires lock
   - Second apply waits (or fails with "state locked")
   - Each apply sees the result of the previous one
   </details>

5. **Compare monorepo vs polyrepo strategies for IaC. A company has 5 teams and wants each team to manage their own infrastructure. Which pattern would you recommend and why?**
   <details>
   <summary>Answer</summary>

   **Recommendation: Hybrid approach**

   **Pattern:**
   - **Monorepo for platform team:** Shared modules, networking, security, Kubernetes clusters
   - **Polyrepo for each team:** Team-specific infrastructure using platform modules

   **Why hybrid:**

   | Aspect | Pure Monorepo | Pure Polyrepo | Hybrid |
   |--------|---------------|---------------|--------|
   | Team autonomy | Low | High | High |
   | Consistency | High | Low | High (via modules) |
   | Blast radius | Large | Small | Small |
   | Module sharing | Easy | Hard | Easy (versioned) |
   | CI complexity | High | Low | Medium |

   **Implementation:**
   ```
   # Platform team monorepo
   platform-infrastructure/
   ├── modules/          # Versioned, published modules
   ├── networking/       # Shared VPCs, DNS
   └── kubernetes/       # Shared clusters

   # Team polyrepos
   team-alpha-infra/     # Uses platform modules v2.1.0
   team-beta-infra/      # Uses platform modules v2.1.0
   team-gamma-infra/     # Uses platform modules v2.0.0 (upgrading)
   ```

   Teams get autonomy. Platform team ensures guardrails. Modules are versioned so teams upgrade on their schedule.
   </details>

6. **An organization wants to move from IaC Maturity Level 1 (Scripted) to Level 3 (Collaborative). Outline a 6-month roadmap.**
   <details>
   <summary>Answer</summary>

   **Month 1-2: Foundation**
   - [ ] Choose IaC tool (Terraform recommended for multi-cloud)
   - [ ] Set up remote backend with locking (S3 + DynamoDB)
   - [ ] Convert 1 non-critical environment to IaC
   - [ ] Train team on IaC basics
   - [ ] Establish coding standards (naming, structure)

   **Month 3-4: Migration**
   - [ ] Import existing infrastructure into state
   - [ ] Create modules for repeated patterns
   - [ ] Convert remaining environments
   - [ ] Set up CI pipeline for `terraform plan`
   - [ ] Add security scanning (Checkov/tfsec)

   **Month 5-6: Collaboration**
   - [ ] Require PR for all IaC changes
   - [ ] Set up PR automation (Atlantis or TFC)
   - [ ] Add code review requirements
   - [ ] Implement drift detection
   - [ ] Document runbooks and patterns
   - [ ] Run disaster recovery drill

   **Success criteria for Level 3:**
   - All infrastructure in Git
   - All changes via PR with review
   - Automated plan on PR, apply on merge
   - Drift detected within 24 hours
   - Any environment rebuildable from code
   </details>

7. **What is "configuration drift" and how does a Level 4 (Continuous) IaC practice prevent it?**
   <details>
   <summary>Answer</summary>

   **Configuration drift** is when actual infrastructure state diverges from the desired state defined in code. Causes include:
   - Manual changes via console/CLI
   - Out-of-band automation
   - Failed applies leaving partial state
   - External systems modifying resources

   **Level 4 (Continuous) prevents drift through:**

   1. **Continuous reconciliation:**
      - System constantly compares actual vs desired
      - Runs every few minutes (not just on commit)
      - Detects drift from any source

   2. **Automatic remediation:**
      - When drift detected, automatically corrects
      - "Self-healing" infrastructure
      - Manual changes are reverted

   3. **Git as sole source of truth:**
      - No other way to make changes
      - Console/CLI blocked or monitored
      - Changes only persist if in Git

   **Example (Flux/ArgoCD):**
   ```
   1. Engineer manually changes replica count to 5
   2. Reconciliation loop runs (every 3 min)
   3. Git says replicas: 3
   4. Actual is 5, desired is 3
   5. System automatically reverts to 3
   6. Alert sent: "Manual change detected and reverted"
   ```
   </details>

8. **Design an IaC workflow that supports the following requirements: (a) Multiple environments, (b) Team autonomy, (c) Security guardrails, (d) Audit trail.**
   <details>
   <summary>Answer</summary>

   **Architecture:**
   ```
   ┌─────────────────────────────────────────────────────────┐
   │                    Git Repository                       │
   │  ┌──────────────────────────────────────────────────┐  │
   │  │ modules/           (Platform team owns)          │  │
   │  │ ├── vpc/           Versioned, reviewed           │  │
   │  │ ├── eks/           Security embedded             │  │
   │  │ └── rds/                                         │  │
   │  └──────────────────────────────────────────────────┘  │
   │  ┌──────────────────────────────────────────────────┐  │
   │  │ teams/             (Teams own their dirs)        │  │
   │  │ ├── alpha/dev/                                   │  │
   │  │ ├── alpha/prod/                                  │  │
   │  │ ├── beta/dev/                                    │  │
   │  │ └── beta/prod/                                   │  │
   │  └──────────────────────────────────────────────────┘  │
   └─────────────────────────────────────────────────────────┘
                           │
                           ▼
   ┌─────────────────────────────────────────────────────────┐
   │                    CI/CD Pipeline                       │
   │  1. Lint & Format    (terraform fmt, validate)         │
   │  2. Security Scan    (Checkov, tfsec)                  │
   │  3. Cost Estimate    (Infracost)                       │
   │  4. Plan             (terraform plan)                  │
   │  5. Policy Check     (OPA/Sentinel)                    │
   │  6. Approval         (required for prod)               │
   │  7. Apply            (terraform apply)                 │
   │  8. Audit Log        (all actions logged)              │
   └─────────────────────────────────────────────────────────┘
   ```

   **Requirements mapping:**
   - **(a) Multiple environments:** Directory structure (teams/alpha/dev, teams/alpha/prod)
   - **(b) Team autonomy:** Teams own their directories, use approved modules
   - **(c) Security guardrails:** Checkov in CI, OPA policies, approved modules only
   - **(d) Audit trail:** Git history + CI logs + state file versioning

   **Policy example (OPA):**
   ```rego
   deny[msg] {
     input.resource_type == "aws_instance"
     not startswith(input.instance_type, "t3.")
     msg := "Only t3.* instances allowed"
   }
   ```
   </details>

---

## Hands-On Exercise

**Task**: Assess and plan your IaC maturity improvement.

**Part 1: Self-Assessment (10 minutes)**

Answer these questions about your current environment:

```bash
# Create assessment file
cat > iac-assessment.md << 'EOF'
# IaC Maturity Assessment

## Reproducibility
Q: Can you recreate production from scratch?
A: [ ] No / [ ] Days / [ ] Hours / [ ] Minutes / [ ] Automatic

## Change Management
Q: How do infrastructure changes happen?
A: [ ] SSH/Console / [ ] Scripts / [ ] IaC manual / [ ] IaC with PR / [ ] GitOps

## Drift Detection
Q: Do you detect configuration drift?
A: [ ] Never / [ ] Occasionally / [ ] Daily / [ ] Continuous / [ ] Auto-remediate

## Estimated Current Level: _____

## Target Level in 6 months: _____
EOF
```

**Part 2: Design Improvement Plan (15 minutes)**

Based on your assessment, create a plan:

```bash
cat > iac-improvement-plan.md << 'EOF'
# IaC Improvement Plan

## Current State
- Maturity Level:
- Main Pain Points:
  1.
  2.
  3.

## Target State (6 months)
- Target Maturity Level:
- Key Improvements:
  1.
  2.
  3.

## Quick Wins (First Month)
1. Set up remote state backend
2. Convert one service to IaC
3. Add terraform plan to CI

## Month 2-3 Goals
1.
2.

## Month 4-6 Goals
1.
2.

## Success Metrics
- [ ] All infrastructure in Git
- [ ] All changes via PR
- [ ] Recovery time < X hours
- [ ] Drift detected within X hours
EOF
```

**Part 3: Hands-On with Terraform (15 minutes)**

If you have Terraform installed, practice state concepts:

```bash
# Initialize with local state (for learning only)
mkdir -p iac-practice && cd iac-practice

cat > main.tf << 'EOF'
terraform {
  required_version = ">= 1.0"
}

resource "local_file" "example" {
  content  = "Hello, IaC!"
  filename = "${path.module}/hello.txt"
}
EOF

# Initialize and apply
terraform init
terraform plan
terraform apply -auto-approve

# Examine state
terraform state list
terraform state show local_file.example

# Make a change and see the plan
sed -i 's/Hello, IaC!/Hello, Infrastructure as Code!/' main.tf
terraform plan  # Notice it shows the change

# Apply the change
terraform apply -auto-approve

# Clean up
terraform destroy -auto-approve
```

**Success Criteria**:
- [ ] Completed self-assessment
- [ ] Created improvement plan with specific goals
- [ ] Understand state management concepts
- [ ] Can explain the difference between maturity levels

---

## Further Reading

- **"Infrastructure as Code"** by Kief Morris (O'Reilly). The definitive book on IaC principles and patterns.

- **"Terraform: Up & Running"** by Yevgeniy Brikman. Practical guide to Terraform with real-world examples.

- **"The Phoenix Project"** by Gene Kim. Novel that illustrates why IaC matters for organizational agility.

- **HashiCorp Learn** - learn.hashicorp.com. Free tutorials on Terraform from the creators.

---

## Key Takeaways

Before moving on, ensure you understand:

- [ ] **IaC maturity levels**: From manual (0) to self-service (5), and where your organization fits
- [ ] **Declarative vs imperative**: Declarative defines "what," imperative defines "how." Declarative is idempotent
- [ ] **State is critical**: State tracks what IaC created. Remote backends with locking are essential for teams
- [ ] **Version control is non-negotiable**: All infrastructure in Git, all changes via PR
- [ ] **Environment parity**: Same code, different variables. Minimize differences between dev/staging/prod
- [ ] **Avoid antipatterns**: Snowflakes, drift, copy-paste, giant modules, state chaos, secret sprawl
- [ ] **Start simple, grow maturity**: Don't jump to Level 5. Progress through levels intentionally
- [ ] **IaC is cultural**: Tools are easy; getting teams to embrace the workflow is hard

---

## Next Module

[Module 6.2: IaC Testing](../module-6.2-iac-testing/) - How to test infrastructure code before it reaches production.
