---
title: "Module 3.2: Repository Strategies"
slug: platform/disciplines/delivery-automation/gitops/module-3.2-repository-strategies
sidebar:
  order: 3
---
> **Discipline Module** | Complexity: `[MEDIUM]` | Time: 30-35 min

## Prerequisites

Before starting this module:
- **Required**: [Module 3.1: What is GitOps?](../module-3.1-what-is-gitops/) — GitOps fundamentals
- **Required**: Git branching and PR workflow experience
- **Recommended**: Experience managing multiple services/environments

---

## Why This Module Matters

You've decided to adopt GitOps. Great! Now where do you put things?

This seemingly simple question determines:
- **Who can change what**: Access control
- **How fast you can deploy**: Sync times, blast radius
- **How teams collaborate**: Coupling vs autonomy
- **How you recover from disasters**: What to restore from where

Bad repository structure creates friction. Good structure enables flow.

This module helps you choose the right structure for your organization.

---

## The Core Decision: Monorepo vs Polyrepo

### Monorepo

All configuration in a single repository.

```
gitops-config/
├── apps/
│   ├── frontend/
│   │   ├── base/
│   │   └── overlays/
│   │       ├── dev/
│   │       ├── staging/
│   │       └── prod/
│   ├── backend/
│   │   ├── base/
│   │   └── overlays/
│   └── database/
├── infrastructure/
│   ├── cert-manager/
│   ├── ingress-nginx/
│   └── monitoring/
└── clusters/
    ├── dev/
    ├── staging/
    └── prod/
```

**Pros:**
- Single place to see everything
- Easier cross-cutting changes
- Simplified tooling
- Single set of access controls

**Cons:**
- Can become large and slow
- Tight coupling between teams
- Harder to scale permissions
- One repo's issues affect everyone

**Best for:**
- Smaller organizations (< 50 engineers)
- Platform teams managing infrastructure
- Strong central control needed

### Polyrepo

Configuration spread across multiple repositories.

```
# Repository: team-a-config
team-a-config/
├── service-1/
│   └── overlays/
└── service-2/
    └── overlays/

# Repository: team-b-config
team-b-config/
├── api-gateway/
└── auth-service/

# Repository: platform-config
platform-config/
├── infrastructure/
├── policies/
└── cluster-addons/
```

**Pros:**
- Team autonomy
- Fine-grained access control
- Independent scaling
- Smaller, focused repos

**Cons:**
- Harder to see full picture
- Cross-cutting changes need multiple PRs
- More tooling complexity
- Potential for drift between repos

**Best for:**
- Larger organizations
- Strong team boundaries
- High autonomy cultures

### Hybrid Approach

Most organizations land somewhere in between:

```
# Platform repo (central team)
platform-config/
├── infrastructure/
├── policies/
└── base-configs/

# Team repos (each team owns)
team-a-apps/
├── service-1/
└── service-2/

team-b-apps/
├── api/
└── worker/
```

**Platform repo**: Shared infrastructure, policies, base configurations
**Team repos**: Team-specific applications and customizations

---

## App Repo vs Config Repo

Another key decision: where does configuration live relative to application code?

### Single Repo (App + Config Together)

```
my-service/
├── src/
│   └── main.go
├── Dockerfile
├── Makefile
└── deploy/
    ├── base/
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   └── kustomization.yaml
    └── overlays/
        ├── dev/
        ├── staging/
        └── prod/
```

**Pros:**
- Everything in one place
- App and config versioned together
- Simpler for small teams
- Natural code review includes deploy changes

**Cons:**
- App changes trigger config pipeline
- Config changes trigger app pipeline
- Different audiences (dev vs ops)
- CI/CD complexity

### Separate Repos

```
# Repository: my-service (app code)
my-service/
├── src/
├── Dockerfile
└── Makefile

# Repository: my-service-config (GitOps config)
my-service-config/
├── base/
│   ├── deployment.yaml
│   └── service.yaml
└── overlays/
    ├── dev/
    ├── staging/
    └── prod/
```

**Pros:**
- Clean separation of concerns
- Different permissions (devs vs ops)
- Config changes don't rebuild app
- Clear GitOps boundary

**Cons:**
- Two repos to manage
- Coordination needed
- More complex CI/CD

### The Common Pattern

Most teams settle on:

```
┌─────────────────────────────────────────────────────────────┐
│                      Application Repo                        │
│                                                              │
│  Source code + Dockerfile + CI pipeline                      │
│  CI builds image, pushes to registry                         │
│  CI updates image tag in Config Repo                         │
└───────────────────────────┬─────────────────────────────────┘
                            │
                    Updates image tag
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                       Config Repo                            │
│                                                              │
│  Kubernetes manifests, Kustomize overlays                   │
│  GitOps agent watches this repo                              │
│  Agent syncs to cluster                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Try This: Map Your Current Structure

Draw your current repository structure:

```
Current structure:
├── Where is app code? _________________
├── Where are Kubernetes manifests? _________________
├── Where is infrastructure config? _________________
├── How many repos total? _________________

Questions:
1. Can a team deploy without touching other teams' repos? Y/N
2. Can you see all deployed services in one place? Y/N
3. Do app changes require config changes in separate commits? Y/N
4. Are permissions appropriately scoped? Y/N
```

---

## Directory Structures

How you organize files within repos matters as much as which repos you use.

### Environment-Based Structure

```
my-service/
├── base/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── configmap.yaml
│   └── kustomization.yaml
└── overlays/
    ├── dev/
    │   ├── kustomization.yaml
    │   ├── replica-patch.yaml
    │   └── config-patch.yaml
    ├── staging/
    │   ├── kustomization.yaml
    │   └── replica-patch.yaml
    └── prod/
        ├── kustomization.yaml
        ├── replica-patch.yaml
        ├── hpa.yaml
        └── pdb.yaml
```

**How Kustomize works:**

```yaml
# base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
  - service.yaml
  - configmap.yaml

# overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
patches:
  - replica-patch.yaml
  - hpa.yaml
  - pdb.yaml
```

### Cluster-Based Structure

When managing multiple clusters:

```
clusters/
├── dev-cluster/
│   ├── kustomization.yaml
│   ├── apps/
│   │   ├── frontend/
│   │   └── backend/
│   └── infrastructure/
│       ├── cert-manager/
│       └── ingress/
├── staging-cluster/
│   └── ...
└── prod-cluster/
    ├── us-east/
    │   └── ...
    └── eu-west/
        └── ...
```

### Application-Centric Structure

Organized by application, then environment:

```
apps/
├── frontend/
│   ├── base/
│   └── overlays/
│       ├── dev/
│       ├── staging/
│       └── prod/
├── backend/
│   ├── base/
│   └── overlays/
├── worker/
│   └── ...
└── infrastructure/
    ├── monitoring/
    ├── logging/
    └── ingress/
```

### Choosing a Structure

| Factor | Environment-Based | Cluster-Based | App-Centric |
|--------|-------------------|---------------|-------------|
| "What's in prod?" | Check each app's prod/ | Check prod-cluster/ | Check each app's prod/ |
| "What apps in this cluster?" | Check multiple places | One place | Check multiple places |
| "All configs for this app?" | One place | Multiple clusters | One place |
| Best for | Single cluster per env | Multi-region/cluster | App-focused teams |

---

## Did You Know?

1. **Google's entire codebase lives in one repository** with billions of files. They built custom tooling (Piper) to make this work. Most organizations can't replicate this.

2. **The "trunk-based development" pattern** pairs well with directory-per-environment GitOps. Short-lived branches for changes, merge to main, promote through directories.

3. **Spotify pioneered many polyrepo patterns** for autonomy, but found they needed strong conventions and tooling to avoid chaos. Their "Golden Path" concept addresses this.

4. **Microsoft's Windows codebase moved to Git** in 2017 with over 3.5 million files—they had to create Git Virtual File System (GVFS, now VFS for Git) to make it practical. Repository strategy isn't just about organization, it's about tooling limitations.

---

## War Story: The Branch Strategy That Backfired

A company I worked with tried branch-per-environment GitOps:

**The Setup:**
```
main branch → production
staging branch → staging
develop branch → development
```

**The Theory:**
- Merge develop → staging to promote
- Merge staging → main to go to prod
- Each environment has "its own branch"

**What Actually Happened:**

Week 1: "This is clean!"

Week 4:
```
develop: 127 commits ahead of staging
staging: 43 commits ahead of main
```

Week 8:
- Merging staging → main caused massive conflicts
- Some features accidentally skipped staging
- "Which branch has the fix?" became common
- Cherry-picks created divergence
- Team spent hours resolving merge conflicts

**The Root Problem:**

Branches diverge. That's what branches do. Environment promotion isn't the same as code development.

**The Fix:**

Switched to directory-per-environment:

```
config-repo/
└── my-service/
    ├── base/
    └── overlays/
        ├── dev/      ← always in main
        ├── staging/  ← always in main
        └── prod/     ← always in main
```

Promotion became:
```bash
# Copy dev image tag to staging
yq eval '.images[0].newTag = "v1.2.3"' -i overlays/staging/kustomization.yaml

# PR, review, merge
# GitOps agent syncs staging
```

**Results:**
- No merge conflicts
- Clear promotion path
- All envs visible in one branch
- PR shows exactly what changes

**Lesson**: Branches are for code development, not environment promotion.

---

## Branch Strategies (And Why to Avoid Them)

### The Temptation

Branches feel natural for environments:
- "main is prod"
- "develop is dev"
- "we control promotion with merges"

### The Problems

**Problem 1: Divergence**
```
Branches naturally diverge. Environments shouldn't.

develop: adds feature A, B, C
staging: only has A, B (C not promoted)
main: only has A (B pending)

Now you have three different states to reason about.
```

**Problem 2: Merge Conflicts**
```
Config conflicts are worse than code conflicts.
Code: "which version of this function?"
Config: "which version of the cluster state?"

Bad merges → bad deployments.
```

**Problem 3: Lost Changes**
```
Feature in develop, cherry-picked to main,
but staging branch never got it.

"Why is this bug in staging but not prod?"
```

**Problem 4: Audit Complexity**
```
Q: "What changed between staging and prod?"
A: "Let me diff two branches that have
    diverged significantly..."

vs. Directory-based:
A: "Let me diff two directories on main."
```

### When Branches Might Work

- Very simple setups (2 environments max)
- Full lockstep promotion (always all changes)
- Strong discipline and tooling
- Small teams with clear ownership

### The Recommendation

**Use directories, not branches, for environment separation.**

```
# Instead of:
git checkout staging
git merge develop

# Do:
# Update prod/kustomization.yaml with new image tag
git commit -m "Promote v1.2.3 to prod"
git push origin main
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Branch-per-environment | Divergence, merge hell | Directory-per-environment |
| Giant monorepo without tooling | Slow, coupled | Split or invest in tooling |
| Too many small repos | Fragmentation, no visibility | Consolidate by team/domain |
| Mixing app code and config | Wrong triggers, permissions | Separate config repo |
| No clear ownership | Confusion, drift | Document who owns what |
| Inconsistent structure | Hard to automate | Standardize patterns |

---

## Quiz: Check Your Understanding

### Question 1
Why is branch-per-environment problematic for GitOps?

<details>
<summary>Show Answer</summary>

Several reasons:

1. **Branches diverge**: Unlike code, environment configs shouldn't diverge from each other except for intentional differences (replicas, resources)

2. **Merge conflicts**: Config merge conflicts can cause deployment failures

3. **Lost changes**: Cherry-picks and selective merges can miss changes

4. **Audit difficulty**: Comparing branches that have diverged is harder than comparing directories

5. **Cognitive load**: "Which branch is truth for which env?"

**Better approach**: Directory-per-environment on a single branch (main). Promotion = update the directory, PR, merge.

</details>

### Question 2
When would you choose polyrepo over monorepo?

<details>
<summary>Show Answer</summary>

Choose polyrepo when:

1. **Large organization**: Many teams, need independence
2. **Strong team boundaries**: Teams shouldn't see/change each other's configs
3. **Different access needs**: Varying permission requirements
4. **Scale concerns**: Single repo would be too large
5. **Autonomy culture**: Teams want full ownership

Choose monorepo when:

1. **Small organization**: < 50 engineers typically
2. **Central platform team**: Manages most config
3. **Cross-cutting changes**: Frequent changes affecting multiple services
4. **Visibility**: Need to see everything in one place

Most organizations use **hybrid**: platform monorepo + team polyrepos.

</details>

### Question 3
You have 10 microservices and 3 environments (dev, staging, prod). How would you structure the config repo(s)?

<details>
<summary>Show Answer</summary>

Several valid approaches:

**Option A: Single repo, app-centric**
```
config/
├── services/
│   ├── service-1/
│   │   ├── base/
│   │   └── overlays/{dev,staging,prod}
│   ├── service-2/
│   │   ├── base/
│   │   └── overlays/{dev,staging,prod}
│   └── ... (10 services)
└── infrastructure/
    └── overlays/{dev,staging,prod}
```

**Option B: Single repo, env-centric**
```
config/
├── dev/
│   ├── services/
│   └── infrastructure/
├── staging/
│   └── ...
└── prod/
    └── ...
```

**Option C: Team repos (if teams own different services)**
```
team-a-config/ (services 1-4)
team-b-config/ (services 5-7)
team-c-config/ (services 8-10)
platform-config/ (infrastructure)
```

**Recommendation**: Option A is most common for 10 services.
- Base reduces duplication
- Overlays capture env differences
- One place per service

</details>

### Question 4
How does CI interact with GitOps config repos?

<details>
<summary>Show Answer</summary>

Typical flow:

```
1. Developer pushes code to app repo
2. CI builds and tests
3. CI builds container image
4. CI pushes image to registry (e.g., myapp:v1.2.3)
5. CI updates config repo:
   - Clone config repo
   - Update image tag in dev overlay
   - Commit and push (or create PR)
6. GitOps agent detects config repo change
7. Agent syncs new image to cluster
```

**Key points:**
- CI doesn't deploy directly to cluster
- CI only updates Git (image tags)
- GitOps agent does actual deployment
- Image tag is the link between CI and GitOps

**Example CI step (GitHub Actions):**
```yaml
- name: Update config repo
  run: |
    git clone https://github.com/org/config-repo
    cd config-repo
    yq eval '.images[0].newTag = "${{ env.IMAGE_TAG }}"' \
      -i services/myapp/overlays/dev/kustomization.yaml
    git commit -am "Update myapp to ${{ env.IMAGE_TAG }}"
    git push
```

</details>

---

## Hands-On Exercise: Design Your Repository Structure

Design a GitOps repository structure for a scenario.

### Scenario

Your organization has:
- 3 teams (Platform, Frontend, Backend)
- 8 services total:
  - Platform: cert-manager, ingress-nginx, monitoring
  - Frontend: web-app, mobile-api
  - Backend: user-service, order-service, notification-service
- 3 environments: dev, staging, prod
- Each team wants autonomy over their services
- Platform team needs to set base policies

### Your Task

**Part 1: Repository Decision**

```markdown
## Repository Strategy

How many repos? [ ] 1 (monorepo) [ ] 4 (team repos) [ ] Other: ___

Rationale:
_________________________________________________
_________________________________________________

Who owns each repo?
- Repo 1: _______________ Owner: _______________
- Repo 2: _______________ Owner: _______________
- ...
```

**Part 2: Directory Structure**

Design the structure for one of the repos:

```markdown
## Directory Structure for: _______________

repo-name/
├──
├──
├──
└──

Explain your choices:
- Why this structure? _______________
- How do environments differ? _______________
- Where are base configs? _______________
```

**Part 3: Promotion Flow**

How does a change get from dev to prod?

```markdown
## Promotion Flow

1. Developer makes change: _______________
2. Change gets to dev: _______________
3. Promote to staging: _______________
4. Promote to prod: _______________

Automation opportunities:
- _______________
- _______________
```

**Part 4: Access Control**

```markdown
## Access Control

| Repo | Read Access | Write Access | Admin |
|------|-------------|--------------|-------|
|      |             |              |       |
|      |             |              |       |

Branch protection rules:
- main: _______________
```

### Success Criteria

- [ ] Chose monorepo/polyrepo with clear rationale
- [ ] Designed directory structure for at least one repo
- [ ] Defined environment promotion flow
- [ ] Documented access control approach
- [ ] Avoided branch-per-environment

---

## Key Takeaways

1. **Monorepo vs Polyrepo**: Choose based on org size, team autonomy, access needs
2. **Separate app and config repos**: Different cadences, different permissions
3. **Directory-per-environment**: Avoid branch-per-environment pattern
4. **Use Kustomize base/overlays**: Reduce duplication, capture differences
5. **CI updates Git, GitOps deploys**: Clean separation of concerns

---

## Further Reading

**Books**:
- **"GitOps and Kubernetes"** — Chapter on Repository Strategies
- **"Monorepo vs Polyrepo"** — Various blog comparisons

**Articles**:
- **"GitOps Repository Strategies"** — Weaveworks
- **"Why We Use a Monorepo"** — Various tech blog posts
- **"Kustomize Best Practices"** — Kubernetes docs

**Tools**:
- **Kustomize**: kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/
- **Helm**: For chart-based templating
- **yq**: YAML manipulation for CI

---

## Summary

Repository strategy determines how smoothly GitOps operates.

Key decisions:
- **Monorepo vs Polyrepo**: Based on org size and autonomy needs
- **App repo vs Config repo**: Typically separate for GitOps
- **Directory structure**: Environment-based with base/overlays
- **Branch strategy**: Avoid branch-per-env; use directory-per-env

There's no universally "right" answer — but there are patterns that work better for different situations. Start simple, evolve as needed.

---

## Next Module

Continue to [Module 3.3: Environment Promotion](../module-3.3-environment-promotion/) to learn strategies for moving changes safely through environments.

---

*"The best repository structure is the one your team can actually follow."* — GitOps Wisdom
