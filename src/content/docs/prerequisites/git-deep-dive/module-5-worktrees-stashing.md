---
title: "Module 5: Multi-Tasking Mastery — Worktrees and Stashing"
complexity: MEDIUM
time_to_complete: "60 minutes"
prerequisites: "Module 4 of Git Deep Dive"
next_module: "[Module 6: The Digital Detective](../module-6-troubleshooting/)"
sidebar:
  order: 5
---

# Module 5: Multi-Tasking Mastery — Worktrees and Stashing

## Learning Outcomes

By the end of this module, you will be able to:
- Implement `git worktree` to manage concurrent development efforts across multiple branches without disrupting your primary working directory.
- Diagnose and resolve orphaned or disconnected worktrees using lifecycle commands like `prune` and `remove`.
- Evaluate the precise technical trade-offs between `git stash`, `git worktree`, and multiple repository clones to select the optimal context-switching strategy for a given scenario.
- Execute advanced stash operations, including isolating untracked files, applying specific stashes from the stack, and recovering stashed changes into isolated branches.
- Design a resilient local development workflow that prevents uncommitted state loss during critical, time-sensitive production interruptions.

## Why This Module Matters

It was a Tuesday afternoon at a mid-sized fintech company. A senior platform engineer was deep into a complex refactoring of their Kubernetes ingress controller configuration. The working directory was a battlefield of modified YAML files, half-written Go tests for a custom operator, and temporarily tweaked Helm values. They were entirely focused on the intricate dependency chain between the new authentication middleware and the ingress routes. 

Suddenly, PagerDuty triggered. A critical vulnerability in the current production deployment of the ingress controller had been disclosed, and active exploitation was reported in the wild. The security team mandated an immediate hotfix to the `main` branch. The engineer had seconds to react. Panicking about losing their complex, uncommitted local state, they ran `git stash`. They checked out `main`, applied the hotfix, committed, and pushed. When they returned to their feature branch and ran `git stash pop`, they were greeted by a massive wall of merge conflicts. The hotfix had modified the exact same configuration blocks they were refactoring. In their haste, they had also forgotten to stash untracked files, leaving their local environment in an inconsistent, broken state. It took them four hours just to untangle the stash conflicts and reconstruct their original thought process. The financial impact of the initial vulnerability was zero, thanks to the quick fix, but the engineering velocity loss and sheer frustration were immense.

This scenario plays out daily in engineering teams worldwide. The fundamental problem is that Git branches, by default, share a single working directory. When the demands of the real world force you to context-switch rapidly, that single working directory becomes a massive bottleneck and a significant risk to your uncommitted work. This module teaches you how to completely eliminate this bottleneck. You will learn how to leverage Git Stash for minor, temporary state saves, and more importantly, how to master Git Worktrees to maintain multiple, concurrent, isolated working directories backed by a single local repository. Mastering these tools transitions you from a reactive engineer scrambling to save state, to a methodical operator who handles production emergencies with zero disruption to ongoing development.

## The Context Switch Problem

The core architecture of a standard Git clone involves a single `.git` directory and a single working tree (the actual files you edit). When you switch branches using `git checkout` or `git switch`, Git aggressively rewrites the files in your working tree to match the state of the target branch. 

If you have uncommitted changes—modified tracked files, staged changes, or untracked files—Git will often refuse to switch branches if the changes conflict with the target branch. Even if it allows the switch, carrying uncommitted changes across branches is a recipe for accidental commits and corrupted state. 

Historically, developers have used two primary workarounds for this limitation when interrupted:

1.  **The Multiple Clone Strategy**: Whenever a new task or hotfix arises, the developer runs `git clone` into a completely new directory.
2.  **The Stash-and-Pray Strategy**: The developer uses `git stash` to sweep uncommitted changes under the rug, switches branches, does the work, switches back, and tries to `pop` the changes.

Both approaches are fundamentally flawed for professional, high-velocity engineering.

### The True Cost of Multiple Clones

While cloning the repository multiple times provides perfect isolation, it is incredibly inefficient. Consider a large monorepo containing microservices, Kubernetes manifests, and Terraform code. A single clone might consume several gigabytes of disk space and take minutes to download. 

If you create a new clone for every hotfix or code review, you are duplicating the entire Git history (the object database inside the `.git` directory) every single time. 

Furthermore, these clones are completely disconnected from each other locally. If you fetch the latest changes from the remote in Clone A, Clone B remains entirely unaware of them. You must perform network operations in every single clone to keep them synchronized. If you want to test a branch from Clone A against a configuration in Clone B, you have to push to a remote and pull, or mess around with defining local remotes. It is a maintenance nightmare disguised as a solution.

### The Limits of `git stash`

`git stash` is a built-in mechanism that takes the dirty state of your working directory—your modified tracked files and staged changes—and saves it on a stack of unfinished changes, returning your working directory to a clean state matching the `HEAD` commit.

For very short, localized interruptions (e.g., pulling the latest changes before pushing), `git stash` is perfectly adequate. However, it scales extremely poorly when used as a primary context-switching tool for complex work.

When you stash changes, they lose their immediate context. If you stash work, spend three days on a hotfix, and then attempt to restore the stash, you often forget exactly what the stashed changes represent. More critically, if the underlying branch has advanced significantly or if you attempt to pop the stash onto a different branch, you will encounter severe, sometimes unresolvable merge conflicts.

> **Pause and predict: what do you think happens if you run `git stash` when you have newly created files that you haven't yet run `git add` on?**
>
> *Consider how Git tracks files before reading further.*

By default, `git stash` only saves changes to files that Git is already tracking. Newly created files are left completely untouched in your working directory. This often leads to situations where a developer thinks they have stashed their entire state, switches branches, and finds their new files cluttering the hotfix branch, potentially causing build failures or accidental inclusions.

## Mastering Git Stash for Micro-Interruptions

Despite its limitations for long-term context switching, `git stash` is an essential tool for micro-interruptions. To use it safely, you must move beyond the basic `git stash` and `git stash pop` commands and understand how to manage the stash stack effectively.

### Creating High-Context Stashes

Never run `git stash` without a message. A stash stack full of generic `WIP on branch-name` entries is practically useless after a few hours. Always use the `push` subcommand with the `-m` flag to provide context.

```bash
# Bad practice
git stash

# Good practice
git stash push -m "Mid-refactor of deployment.yaml resource limits"
```

If you are working on a new feature and have created new Kubernetes manifests that are not yet tracked by Git, you must explicitly tell the stash command to include them using the `-u` (or `--include-untracked`) flag.

```bash
# Stashes tracked modifications AND untracked new files
git stash push -u -m "Added new redis-deployment.yaml and modified configmap"
```

If you want to be incredibly thorough, you can use the `-a` (or `--all`) flag, which stashes tracked files, untracked files, and even files ignored by `.gitignore`. This is rarely necessary but useful if you need to completely sanitize a directory for testing.

### Navigating and Inspecting the Stash Stack

Every time you create a stash, it is pushed onto a stack. You can view this stack using `git stash list`.

```bash
git stash list
```

The output will look something like this:

```text
stash@{0}: On feature-auth: Added new redis-deployment.yaml and modified configmap
stash@{1}: On main: Mid-refactor of deployment.yaml resource limits
```

The most recent stash is always `stash@{0}`. As you add more, the older ones get pushed down the stack (incrementing their index).

Before applying a stash, you often want to see exactly what changes it contains. You can use the `show` subcommand with the `-p` (patch) flag to view the exact diff of the stashed changes.

```bash
git stash show -p stash@{1}
```

> **Try it now:** Initialize a temporary git repository, create a file, commit it, modify the file, and stash the changes. Run `git stash list`, then run `git stash show -p stash@{0}` to see your stashed modifications in patch format.

> **Stop and think:** You have 3 stashes. You apply `stash@{1}` and it works perfectly. What is the state of your stash stack now? Has anything changed?
>
> *Because you used `apply` instead of `pop`, the stash stack remains exactly the same. `stash@{1}` is still safely on the stack. The index numbers of your stashes do not change, ensuring you can still reference them or drop them manually later.*

### Restoring State: Apply vs. Pop

When you are ready to resume your work, you have two choices: `apply` or `pop`.

`git stash apply` takes the changes from a specified stash and applies them to your current working directory, **but leaves the stash intact on the stack.** This is the safest operation. If the application results in massive conflicts and you abort the process, your stashed state is still safely stored.

```bash
# Applies the most recent stash
git stash apply

# Applies a specific stash from the stack
git stash apply stash@{1}
```

`git stash pop` applies the changes and, if the application is successful (no conflicts), **immediately deletes the stash from the stack.** While convenient, this can be dangerous if you realize slightly too late that you popped the stash onto the wrong branch.

As a general rule for critical infrastructure code, always use `git stash apply`, verify the state, and then manually remove the stash using `git stash drop` when you are certain you no longer need it.

```bash
# Drop a specific stash
git stash drop stash@{1}

# Clear the entire stash stack (use with extreme caution)
git stash clear
```

### The Escape Hatch: Branching from a Stash

What happens when you stash complex changes, work on other things for a week, and then try to apply the stash back to your original branch, only to find that the branch has evolved so much that the conflicts are insurmountable?

Git provides a brilliant escape hatch: `git stash branch`. This command creates a brand new branch starting from the exact commit you were on when you originally created the stash, applies the stash to that new branch, and then drops the stash.

```bash
git stash branch recovered-auth-work stash@{0}
```

This isolates your stashed changes in a safe environment. You can then commit them cleanly to the new branch and figure out how to merge or rebase them into the mainline at your own pace, without dealing with immediate working directory conflicts.

### Mini-Exercise: Stashing Untracked Files

Before we move on to worktrees, let's practice the complete stash workflow, specifically handling untracked files and inspecting the stash stack.

1.  Initialize a new Git repository to act as your primary workspace:
    ```bash
    mkdir stash-practice && cd stash-practice
    git init
    ```
2.  Create an initial commit to establish a clean working tree:
    ```bash
    echo "v1" > config.txt
    git add config.txt
    git commit -m "Initial commit"
    ```
3.  Modify the tracked file and create a new, untracked file:
    ```bash
    echo "v2" > config.txt
    echo "secret-key" > .env
    ```
4.  Stash all changes, including the untracked file:
    ```bash
    git stash push -u -m "WIP on new config and secrets"
    ```
5.  Inspect your stash stack and the contents of the stash:
    ```bash
    git stash list
    git stash show -p stash@{0}
    ```
6.  Restore your stashed changes without removing them from the stack:
    ```bash
    git stash apply stash@{0}
    ```
    *Notice that your modifications to `config.txt` and the new `.env` file are back in your working directory.*

## The Power of Git Worktrees

If `git stash` is a temporary band-aid, `git worktree` is the permanent architectural solution to context switching. 

Introduced in Git 2.5, worktrees allow you to have multiple, independent working directories attached to a single Git repository. This means you can have the `main` branch checked out in one directory, `feature-auth` in another, and `hotfix-ingress` in a third, all simultaneously.

Crucially, because they share the same underlying `.git` object database:
1.  They consume very little additional disk space (only the size of the checked-out files, not the history).
2.  They instantly share network state. If you run `git fetch` in one worktree, the updated remote tracking branches are immediately available in all other worktrees.
3.  You can easily cherry-pick or merge commits between them without needing to push to a remote.

### Anatomy of a Worktree

Let's visualize how worktrees are structured on disk. 

When you run `git clone`, you create the "main" worktree. Inside this directory is the standard `.git` folder containing all the repository data.

```text
+-------------------------------------------------+
| Main Worktree: /projects/k8s-operator           |
|                                                 |
|  deploy/                                        |
|  src/                                           |
|  go.mod                                         |
|  .git/  <-- The actual repository database      |
|    objects/                                     |
|    refs/                                        |
|    worktrees/  <-- Sub-worktree configurations  |
+-------------------------------------------------+
```

When you add a new linked worktree (e.g., in a sibling directory), Git does not copy the repository. Instead, it creates a special `.git` file (not a directory) in the new location. This file contains a single line pointing back to the main repository. Inside the main repository's `.git/worktrees/` directory, Git stores the specific HEAD and index state for the linked worktree.

```text
+-------------------------------------------------+
| Linked Worktree: /projects/k8s-operator-hotfix  |
|                                                 |
|  deploy/                                        |
|  src/                                           |
|  go.mod                                         |
|  .git  <-- FILE pointing to main repo           |
|            (gitdir: /projects/k8s-operator/.git/worktrees/hotfix)
+-------------------------------------------------+
```

This architecture ensures perfect isolation of the working tree and the staging area (index), while maintaining a completely unified commit history and network state.

> **Stop and think:** If you run `git fetch` in worktree A, do you need to run `git fetch` again in worktree B to see the updated remote branches? Why or why not?
>
> *No, you do not need to run it again. Because all linked worktrees share the same underlying `.git` object database and references in the main repository, a network operation in one worktree updates the repository state for all of them instantly.*

### Creating and Managing Worktrees

To create a new worktree, you use the `git worktree add` command. You specify the path where you want the new directory created, and optionally, the branch you want to check out.

If you are working in `/projects/k8s-operator` and an urgent bug is reported on the `main` branch, you do not need to stash your current work. You simply create a new worktree for the hotfix.

```bash
# Usage: git worktree add <path> <branch>

# Create a new directory alongside your current one, 
# create a new branch called 'hotfix-cve', 
# and check it out starting from 'main'
git worktree add -b hotfix-cve ../k8s-operator-hotfix main
```

Git will output:
```text
Preparing worktree (new branch 'hotfix-cve')
HEAD is now at 8f3a9b2 Update ingress documentation
```

You now have a completely clean working directory at `../k8s-operator-hotfix` on the `hotfix-cve` branch. Your original directory remains completely untouched, exactly as you left it. You can open a new terminal tab, navigate to the hotfix directory, fix the vulnerability, test it, commit, and push. 

Once the hotfix is merged, you simply close that terminal tab, switch back to your original tab, and continue your feature work without skipping a beat.

> **Before running this, what output do you expect if you try to create a worktree for a branch that is already checked out in another worktree?**
>
> *Think about the constraints of a working directory.*

Git enforce a strict rule: a single branch can only be checked out in one worktree at a time. If you try to run `git worktree add ../another-dir feature-auth` while `feature-auth` is checked out in your main directory, Git will fiercely reject the command. This prevents schizophrenic states where two different directories are trying to update the same branch pointer simultaneously.

### Worktree Lifecycle: Listing and Pruning

To see all active worktrees attached to your repository, use the `list` command.

```bash
git worktree list
```

```text
/projects/k8s-operator         8f3a9b2 [feature-auth]
/projects/k8s-operator-hotfix  2c9b4e1 [hotfix-cve]
```

When you are finished with a worktree (e.g., the hotfix is merged and deleted remotely), you need to clean it up. The correct way to remove a worktree is using the `remove` command.

```bash
# This deletes the directory and cleans up the references in the main .git folder
git worktree remove ../k8s-operator-hotfix
```

Git will refuse to remove a worktree if it has uncommitted changes, protecting you from accidental data loss. You can force the removal with `-f`, but this should be avoided.

**The Accidental Deletion Scenario**

What happens if you bypass Git and simply use `rm -rf ../k8s-operator-hotfix`?

Your file system will delete the directory, but the main Git repository will still think the worktree exists. It will maintain the metadata in `.git/worktrees/hotfix` and will stubbornly refuse to let you check out the `hotfix-cve` branch anywhere else, claiming it is already checked out.

To fix this orphaned state, you must instruct Git to clean up its internal records of worktrees that no longer exist on disk.

```bash
git worktree prune
```

Running `prune` forces Git to verify the existence of every registered worktree path. If the path is missing, Git drops the internal tracking metadata, freeing up the branch to be checked out again.

## Decision Matrix: Stash vs. Worktree vs. Clone

Understanding when to use which tool is the hallmark of a senior engineer. Use this matrix to guide your workflow decisions.

> **Pause and predict:** Your colleague asks you to review their PR. They changed 2 files. You have no uncommitted work. What strategy do you use and why?
>
> *If you have no uncommitted work, you don't actually need stash or worktrees to save state! You can simply check out their branch in your current directory. However, if you want to keep your current branch checked out so you can instantly return to it without searching through branch history, creating a quick worktree is still an excellent choice to isolate the review context.*

| Scenario | Recommended Strategy | Technical Rationale |
| :--- | :--- | :--- |
| **Pulling latest changes** before pushing your local commits. | `git stash` | The interruption is measured in seconds. The context remains perfectly clear in your mind. The risk of major conflicts is low, and stash is the fastest local operation. |
| **Emergency production hotfix** while mid-feature. | `git worktree` | Requires a completely clean state. The hotfix might take hours or days, during which you will lose the mental context of a stash. You need absolute guarantee that feature code won't leak into the hotfix. |
| **Reviewing a colleague's massive Pull Request** while working on your own code. | `git worktree` | PR reviews often require running the code, modifying configuration, and running tests. Stashing your work to do this disrupts your flow and risks test database contamination if you share environment variables. A separate worktree provides isolation for building and testing the PR. |
| **Testing a completely different Kubernetes version** locally against the codebase. | `git clone` (Sometimes) | While a worktree isolates the files, things like `.env` files or global IDE configurations might still bleed across directories if they look at relative paths. If you need absolute, hermetic isolation (e.g., entirely different Docker environments bound to different directories), a full, separate clone might be justified, though rare. |
| **Trying out a speculative, experimental refactor** that you might throw away. | `git branch` (In current tree) | If you just want to try something quickly, commit your current state, create a new branch, and start hacking. Git branches are cheap. Stashing is unnecessary if you are willing to make WIP commits. |

## A Kubernetes War Story: The Operator Catastrophe

Consider a team developing a complex Kubernetes Operator in Go. The Operator manages highly available database clusters.

Engineer Alice is working on a major feature: implementing automated backups to AWS S3. Her working directory has 15 modified Go files, new CRD YAML definitions, and a local Minikube cluster running a specific configuration to test the backup logic.

A critical issue is escalated: the Operator is crashing in the production environment due to a race condition in the leader election logic. Alice is the only one who understands the leader election code.

**The Stash Approach (Failure Path):**
Alice runs `git stash`. She checks out `main`. She modifies the leader election code, writes a test, and pushes the fix. She switches back to her backup branch and runs `git stash pop`. 
Unfortunately, the leader election fix modified the same core controller initialization sequence that her backup feature touches. She is hit with complex Go conflicts. Furthermore, her local Minikube cluster was left running the backup feature's configuration, which now conflicts with the leader election tests she was trying to run locally. She spends hours fixing conflicts and resetting her local cluster state.

**The Worktree Approach (Success Path):**
Alice leaves her terminal exactly as it is. She opens a new terminal and runs `git worktree add ../operator-hotfix main`.
She navigates to the new directory. She fixes the leader election bug, runs the tests (perhaps spinning up a fresh, isolated KinD cluster for this specific directory), commits, and pushes.
She deletes the worktree. She returns to her original terminal. Her 15 modified files, her uncommitted CRDs, and her specific Minikube configuration are completely untouched, waiting exactly where she left them. No context lost, no merge conflicts, no wasted time.

## Did You Know?

1.  Git worktrees were heavily inspired by a third-party script called `git-new-workdir` which existed in the `contrib/` directory of the Git source code for years before being formalized into the core binary in 2015.
2.  When you use `git stash`, Git is actually creating internal commits. It creates one commit for the state of your staging area (index) and another commit for your working tree, tying them together in a unique structure that isn't part of any branch history.
3.  You can configure Git to always include untracked files when stashing by setting the global configuration `git config --global stash.showIncludeUntracked true`, though explicit flags are generally safer to prevent accidental stashing of large build artifacts.
4.  Git prevents you from deleting a branch if it is currently checked out in *any* worktree, providing a vital safety net against deleting work you are actively viewing in another terminal window.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| **Losing new files in a stash** | Running `git stash` without the `-u` flag leaves newly created (untracked) files in the working directory, leading to confusion when switching branches. | Always use `git stash push -u -m "msg"` when you have created new files. |
| **Stash stack amnesia** | Using bare `git stash` creates generic entries like `WIP on main`. After three days, you will have no idea what `stash@{2}` contains. | Never stash without a message. Use `git stash push -m "Context description"`. |
| **Orphaned worktree directories** | Deleting a worktree folder using `rm -rf` instead of `git worktree remove`. Git still believes the worktree exists and locks the branch. | Run `git worktree prune` to force Git to clean up missing directory references. |
| **Popping onto the wrong branch** | Using `git stash pop`, realizing you are on the wrong branch, and now having to untangle complex merge conflicts because the stash was instantly deleted from the stack. | Default to `git stash apply`. Only use `git drop` when you have verified the applied state is correct and stable. |
| **Trying to checkout a locked branch** | Attempting to checkout a branch that is currently active in another worktree. Git enforces strict branch exclusivity across worktrees. | Either switch the other worktree to a different branch, or commit/stash and remove that worktree entirely. |
| **Ignoring environment bleed** | Assuming worktrees isolate *everything*. While file paths are isolated, global environment variables, shared local databases (like a single Postgres instance), or fixed port bindings (e.g., a web server always binding to 8080) will still conflict across worktrees. | Use isolated environments per directory, such as dynamic port allocation or separate container networks for local testing. |

## Quiz

<details>
<summary>Question 1: You are deep into modifying a complex Helm chart for a new microservice. PagerDuty alerts you to a Sev-1 incident requiring a one-line configuration change on the `production` branch. Which command is the safest and most efficient way to isolate your current work while you handle the emergency?</summary>

**Answer:** `git worktree add ../incident-response production`. 
A worktree provides perfect isolation without the overhead of a full clone. It guarantees that your half-written Helm templates won't bleed into the production hotfix, and you won't have to deal with stash conflicts when you return to your feature. Because the working directory is entirely separate, you can freely modify files and run tests without affecting your primary development environment. Once the hotfix is complete, you simply delete the worktree and resume your previous task exactly where you left off.
</details>

<details>
<summary>Question 2: You ran `git stash` before switching branches to help a colleague debug an issue. Two days later, you return to your branch, run `git stash pop`, and are hit with massive merge conflicts because your colleague merged a major refactor in the meantime. What command could have saved you from manually resolving these immediate working directory conflicts?</summary>

**Answer:** `git stash branch new-recovery-branch`. 
If you suspect conflicts or if `apply` fails catastrophically, creating a branch directly from the stash isolates the changes into a clean commit history based on the exact point in time you created the stash. This bypasses the immediate conflict with the current state of the branch. You can then rebase or merge that new branch systematically, resolving conflicts one commit at a time using standard Git merge tools rather than dealing with a massive working directory conflict.
</details>

<details>
<summary>Question 3: You used `rm -rf ../testing-env` to delete a worktree directory you were using to test a Kubernetes deployment. Now, when you try to checkout the `test-deployment` branch in your main directory, Git complains that the branch is already checked out. How do you resolve this?</summary>

**Answer:** Run `git worktree prune` in the main repository. 
Bypassing Git and deleting the directory via the file system leaves the internal `.git/worktrees/` metadata orphaned. Git still believes the worktree exists because the reference files within the main `.git` directory were not removed. The `prune` command tells Git to verify the existence of all worktrees on disk and safely remove the internal records for any that are missing, which then unlocks the branch for use elsewhere.
</details>

<details>
<summary>Question 4: You are writing a new Python script to automate cluster scaling. You haven't run `git add` on the new script yet. You receive an urgent request to review a PR, so you run `git stash`, checkout the PR branch, and suddenly your new Python script is sitting in the directory of the PR branch. Why did this happen?</summary>

**Answer:** `git stash` ignores untracked files by default. 
Because the new Python script had never been added to the index, Git did not consider it part of the dirty state to be stashed. When you switched branches, the file simply remained in the working directory because it did not conflict with any tracked files on the target branch. To include it in the stash, you must explicitly tell Git to capture untracked files using the `-u` or `--include-untracked` flag: `git stash push -u -m "saving new script"`.
</details>

<details>
<summary>Question 5: You need to test a database migration script locally, but you don't want to disrupt your current environment. You are debating whether to run `git clone` into a new directory or use `git worktree add`. What is the fundamental architectural difference on disk between these two approaches?</summary>

**Answer:** A second `git clone` duplicates the entire object database (history, commits, blobs) creating an entirely independent `.git` directory, which consumes significant disk space and requires its own network operations. `git worktree add` creates a new working directory but uses a tiny `.git` file to point back to the *original* repository's object database. This means it shares the complete commit history and network state with your main repository while conserving disk space, making it a much more efficient choice for local testing.
</details>

<details>
<summary>Question 6: You are returning to work after a long weekend and find three stashes in your stack. You think `stash@{1}` contains the database configuration changes you need, but you want to be absolutely sure before applying it to your current working directory. What command should you use to verify the contents?</summary>

**Answer:** `git stash show -p stash@{1}`. 
This command acts like `git diff`, displaying the patch format of the changes stored in that specific stash. By reviewing the raw diff output, you can safely verify exactly which files were modified and what lines were changed without altering your current working directory. This prevents accidental application of the wrong stash and avoids potential merge conflicts if the stash contains unexpected changes.
</details>

## Hands-On Exercise: The Mid-Flight Hotfix

In this exercise, you will simulate a real-world interruption using Kubernetes manifests, demonstrating why worktrees are superior to stashing for complex context switches.

### Scenario Setup

1.  Initialize a new Git repository to act as your primary workspace.
    ```bash
    mkdir k8s-fleet-manager && cd k8s-fleet-manager
    git init
    ```
2.  Create a stable base state representing production.
    ```bash
    cat << 'EOF' > deployment.yaml
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: fleet-api
    spec:
      replicas: 2
      template:
        spec:
          containers:
          - name: api
            image: fleet-api:v1.0.0
    EOF
    git add deployment.yaml
    git commit -m "Initial production release v1.0.0"
    ```
3.  Create and checkout a new branch for a major feature: adding resource limits and liveness probes.
    ```bash
    git checkout -b feature/reliability-upgrade
    ```
4.  Begin your complex, unfinished work. Modify the deployment heavily.
    ```bash
    cat << 'EOF' > deployment.yaml
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: fleet-api
    spec:
      replicas: 2
      template:
        spec:
          containers:
          - name: api
            image: fleet-api:v1.1.0-rc1
            resources:
              requests:
                memory: "64Mi"
                cpu: "250m"
              limits:
                memory: "128Mi"
                cpu: "500m"
            livenessProbe:
              httpGet:
                path: /healthz
                port: 8080
              initialDelaySeconds: 3
              periodSeconds: 3
    EOF
    ```
    *Do not commit these changes. This represents your dirty working state.*

### The Interruption (Task)

A critical bug is reported in `fleet-api:v1.0.0` in production. You need to immediately patch the image version to `v1.0.1` on the `main` branch.

**Your constraints:** You cannot lose your complex resource/probe configuration, and you cannot risk merge conflicts when applying the hotfix.

### Execution

- [ ] Create a new worktree named `fleet-manager-hotfix` in the parent directory, creating a new branch `hotfix/image-patch` based on `main`.
- [ ] Navigate to the new worktree directory.
- [ ] Verify that `deployment.yaml` in this new directory is the clean, original production version (v1.0.0), lacking any of your reliability upgrades.
- [ ] Update the image tag in the hotfix directory to `fleet-api:v1.0.1`.
- [ ] Commit the hotfix.
- [ ] Safely remove the hotfix worktree using Git commands (do not use `rm -rf`).
- [ ] Return to your original directory and verify your reliability upgrades are still exactly as you left them, uncommitted and ready to continue.

<details>
<summary>Solution</summary>

1.  **Create the worktree:** Leave your current directory exactly as it is (dirty). Create the new environment.
    ```bash
    git worktree add -b hotfix/image-patch ../fleet-manager-hotfix main
    ```
2.  **Navigate and verify:**
    ```bash
    cd ../fleet-manager-hotfix
    cat deployment.yaml 
    # Notice it is the original v1.0.0 file. Your complex work is safely isolated elsewhere.
    ```
3.  **Apply and commit the hotfix:**
    ```bash
    # (Edit deployment.yaml to change image to v1.0.1, e.g., using sed)
    sed -i '' 's/v1.0.0/v1.0.1/g' deployment.yaml # macOS
    # sed -i 's/v1.0.0/v1.0.1/g' deployment.yaml # Linux
    
    git add deployment.yaml
    git commit -m "Hotfix: Update API image to v1.0.1 to resolve memory leak"
    ```
4.  **Cleanup the worktree:**
    ```bash
    # Move out of the directory before deleting it
    cd ../k8s-fleet-manager
    
    # Properly remove the worktree via Git
    git worktree remove ../fleet-manager-hotfix
    ```
5.  **Verify original state:**
    ```bash
    cat deployment.yaml
    # Your complex resource limits and liveness probes are still here, uncommitted, untouched.
    git status
    # Shows deployment.yaml as modified. You seamlessly survived the interruption.
    ```
</details>