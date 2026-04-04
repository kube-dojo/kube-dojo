---
title: "Module 3: History as a Choice — Interactive Rebasing"
sidebar:
  order: 3
---

**Complexity**: [MEDIUM]
**Time to Complete**: 90 minutes
**Prerequisites**: Module 2 of Git Deep Dive

## Learning Outcomes

- Reconstruct a fragmented commit history into a logical narrative using interactive rebase operations (squash, reword, fixup, drop).
- Diagnose and resolve merge conflicts that manifest iteratively during a multi-step rebase sequence.
- Formulate a strategy for excising accidentally committed sensitive data (such as cloud credentials or certificates) from a branch's permanent history.
- Compare and evaluate the technical trade-offs between merging and rebasing when synchronizing local feature branches with upstream changes.
- Execute a branch transplant using the `git rebase --onto` operation to migrate active work between divergent base branches.

## Why This Module Matters

An infrastructure engineer at a mid-sized e-commerce platform was tasked with migrating legacy authentication services to Kubernetes. During the development process, they created a `configmap.yaml` file to hold environment variables. For local testing, they temporarily hardcoded an AWS IAM access key with broad database permissions directly into the file and committed it. Three commits later, realizing the error, they deleted the access key, replaced it with a reference to a Kubernetes Secret, and committed the fix. The branch was pushed, reviewed, approved, and merged. The final state of the code was perfect. However, two weeks later, an automated credential scanner utilized by a malicious actor scraped the repository's historical commits. The scanner found the original commit containing the access key. Over a single weekend, the attackers spun up hundreds of expensive GPU instances across multiple AWS regions, resulting in an eighty thousand dollar cloud bill before the security team intervened. 

The engineer operated under a critical misunderstanding: they believed that deleting a line of code and committing the change erased the previous state. It does not. Git is an append-only ledger by default. A commit history is not merely a backup mechanism; it is a permanent audit log and a vital communication tool. A messy history full of "work in progress," "fixed typo," and "trying again" messages obscures the architectural intent of your changes and places an unreasonable cognitive burden on your reviewers. More severely, it leaves behind artifacts that can compromise your entire system.

In this module, you will learn how to wield interactive rebasing to shape your commit history into a clean, secure, and logical narrative. You will move from treating Git as a passive save button to using it as an active editorial tool, ensuring that the code you share with the world is exactly the story you intend to tell.

## The Philosophy of History Rewriting

Before we execute commands, we must understand the conceptual shift required for history rewriting. When you develop locally, your commits represent a stream of consciousness. You are solving problems sequentially, making mistakes, backing up, and trying new approaches. This is the correct way to work locally—commit frequently to establish save points. 

However, the history that is useful to you during development is rarely the history that is useful to a reviewer or a future maintainer attempting to understand your architectural decisions. A future engineer performing a `git blame` on a complex Kubernetes Deployment configuration does not need to see that it took you six tries to get the YAML indentation correct. They need a single, cohesive commit that introduces the Deployment with a comprehensive message explaining why specific resource limits were chosen.

### The Golden Rule of Rebasing

Rewriting history involves creating entirely new commits with new cryptographic hashes (SHAs). If you rewrite a commit that has already been pushed to a central repository and downloaded by other developers, you create a divergent timeline. 

**The Golden Rule:** Never rebase commits that exist outside your local repository. 

If you rebase a shared branch and force-push the result, the next time your colleagues attempt to pull, Git will see their local history and the new remote history as two completely separate sets of work. It will attempt to merge them, resulting in massive, confusing conflicts and a duplicated commit history. Rebasing is a tool for preparing your personal workspace before you share it. Once a branch is public and actively collaborated on by others, you must rely on standard merges or revert commits to move forward.

### Merging vs. Rebasing

When you need to integrate changes from a main branch into your feature branch, you have two primary mechanisms.

+---------------------------------------------------+
|               THE MERGE STRATEGY                  |
+---------------------------------------------------+
|                                                   |
| Feature Branch:     [C1] ---> [C2] ---> [C3]      |
|                    /                        \     |
|                   /                          \    |
| Main Branch:  [M1] --------> [M2] --------> [M3]  |
|                                                   |
| Result: A non-linear history with a merge commit. |
| The timeline shows exactly when things happened.  |
+---------------------------------------------------+

A merge preserves the exact chronological history. It creates a new "merge commit" that has two parents. This is factually accurate but can lead to a tangled, "diamond-patterned" commit graph that is difficult to read.

+---------------------------------------------------+
|               THE REBASE STRATEGY                 |
+---------------------------------------------------+
|                                                   |
| Feature Branch:                  [C1'] -> [C2']   |
|                                 /                 |
|                                /                  |
| Main Branch:  [M1] -> [M2] -> [M3]                |
|                                                   |
| Result: A linear history. Feature commits are     |
| re-written as if they were based on the latest    |
| main branch. Old [C1] and [C2] are discarded.     |
+---------------------------------------------------+

A rebase takes your feature branch commits, temporarily sets them aside, updates your branch to point to the latest main branch commit, and then replays your work on top of it. This creates a perfectly linear history, which makes tools like `git log` and `git bisect` significantly more effective. The trade-off is that it rewrites history—the original SHAs of your commits are destroyed and replaced with new ones.

**Pause and predict: What do you think happens if a merge conflict occurs during a rebase? Does it happen once at the end, or differently?**

*Answer: Because a rebase replays commits one by one, if multiple commits touch the same file that was modified in the main branch, you may have to resolve conflicts for every single commit being replayed. This iterative conflict resolution is the primary pain point of rebasing.*

## The Interactive Rebase Interface

The standard `git rebase <branch>` command operates automatically. Interactive rebasing, invoked with the `-i` or `--interactive` flag, pauses the process and opens a text editor, allowing you to intercept and modify the instructions Git uses to replay the commits.

To begin an interactive rebase against the main branch, you execute:

```bash
git rebase -i main
```

Alternatively, to rewrite the last 5 commits on your current branch regardless of the upstream base, you can use the relative reference `HEAD`:

```bash
git rebase -i HEAD~5
```

When the text editor opens, you will see an instruction sheet that looks like this:

```text
pick 3a2b1c4 Add initial deployment.yaml
pick 9f8e7d6 Fix YAML indentation in deployment
pick 5c4b3a2 Add service.yaml
pick 1d2c3b4 Add configmap.yaml with hardcoded db password
pick 7e6d5c4 Remove password, use secret reference
pick 8a9b0c1 Add liveness and readiness probes

# Rebase 8273645..8a9b0c1 onto 8273645 (6 commands)
#
# Commands:
# p, pick <commit> = use commit
# r, reword <commit> = use commit, but edit the commit message
# e, edit <commit> = use commit, but stop for amending
# s, squash <commit> = use commit, but meld into previous commit
# f, fixup <commit> = like "squash", but discard this commit's log message
# x, exec <command> = run command (the rest of the line) using shell
# d, drop <commit> = remove commit
```

**Crucial detail:** The commits are listed from oldest at the top to newest at the bottom. This is the inverse of `git log`. Git reads this file from top to bottom, applying each instruction sequentially.

### The Command Arsenal

Understanding the subtle differences between these commands is essential for effective history shaping.

| Command | Action | Primary Use Case |
| :--- | :--- | :--- |
| `pick` | Applies the commit exactly as it is. | Default action. Leaves the commit untouched. |
| `reword` | Applies the commit, but pauses to open an editor so you can change the message. | Fixing a typo in a commit message or adding more descriptive context. |
| `edit` | Applies the commit, then completely stops the rebase process, returning control to the terminal. | Splitting a large commit into smaller ones, or modifying the actual file contents of a historical commit. |
| `squash` | Melds the contents of this commit into the commit immediately above it. Pauses to let you combine their commit messages. | Combining related changes (e.g., a feature and its corresponding unit tests) into one logical unit. |
| `fixup` | Melds the contents into the commit above it, but entirely discards this commit's message. | Absorbing "fix typo" or "WIP" commits into the main feature commit without cluttering the final message. |
| `drop` | Completely ignores the commit. It will not be replayed. | Deleting experimental code or accidental commits entirely. (You can also just delete the line in the editor). |
| `exec` | Runs an arbitrary shell command after the previous line is applied. | Running a test suite or linter automatically after every commit to ensure the build isn't broken mid-history. |

+-------------------------------------------------------------+
|              INTERACTIVE REBASE EXECUTION ENGINE            |
+-------------------------------------------------------------+
|                                                             |
| [HEAD] Current State                                        |
|   |                                                         |
|   v                                                         |
| 1. Detach HEAD at the chosen base commit.                   |
|                                                             |
| 2. Read the instructions from the text editor.              |
|                                                             |
| 3. Apply the first commit in the list.                      |
|    +-- Is it 'pick'? Apply and move to next.                |
|    +-- Is it 'squash'? Apply, wait for message edit.        |
|    +-- Is it 'edit'? Apply, STOP execution, return control. |
|                                                             |
| 4. Repeat until the list is empty.                          |
|                                                             |
| 5. Point the original branch reference to the new HEAD.     |
|                                                             |
| 6. Garbage collect the old orphaned commits eventually.     |
+-------------------------------------------------------------+

## Crafting the Perfect Pull Request

Let us walk through a practical scenario. We are building a Kubernetes application tier. Our current branch history is the messy list shown earlier. We want to clean this up into a concise, logical history before opening a Pull Request.

Our goals for this rebase:
1. Combine the indentation fix into the initial deployment commit.
2. Completely remove the hardcoded password from history, keeping only the final secure state of the ConfigMap.
3. Combine the probes into the deployment commit.
4. Reword the final deployment commit message to be descriptive.

We run `git rebase -i HEAD~6`.

### Step 1: Reordering and Fixing Up

To achieve our goals, we must physically move lines around in the text editor. We move the `fixup` for the deployment indentation immediately under the deployment creation. We move the probe addition up as well.

We must handle the secret carefully. The secret was added in `1d2c3b4` and removed in `7e6d5c4`. If we `squash` or `fixup` the removal commit into the addition commit, the resulting combined commit will represent the net difference: the secret will never have existed. 

We edit the file to look like this:

```text
reword 3a2b1c4 Add initial deployment.yaml
fixup 9f8e7d6 Fix YAML indentation in deployment
fixup 8a9b0c1 Add liveness and readiness probes
pick 5c4b3a2 Add service.yaml
pick 1d2c3b4 Add configmap.yaml with hardcoded db password
fixup 7e6d5c4 Remove password, use secret reference
```

**Pause and predict: Look at the first block (reword, fixup, fixup). What will the final commit message be?**

*Answer: Because we used `reword` on the first commit and `fixup` on the subsequent ones, Git will open an editor for the first commit allowing us to write a new message, and it will completely discard the messages "Fix YAML indentation..." and "Add liveness...". The result is a single commit with our brand new message.*

### Step 2: Execution and Rewording

When we save and close the editor, Git begins executing the plan. It detaches HEAD at the base commit and starts applying.

1. It applies `3a2b1c4`. Because we specified `reword`, it immediately opens an editor. We change the message to: `feat: Implement Core Application Deployment with Health Checks`. We save and close.
2. It applies `9f8e7d6`. Because it's a `fixup`, it merges the file changes into the new commit without asking for a message.
3. It applies `8a9b0c1` as another `fixup`.
4. It applies `5c4b3a2` normally.
5. It applies `1d2c3b4`.
6. It applies `7e6d5c4`. Because it's a `fixup` attached to the ConfigMap creation, the addition and immediate deletion of the secret cancel each other out.

The resulting history is exactly two clean commits: the Deployment and the Service/ConfigMap combination. The sensitive credential has been permanently excised from the branch's history.

## Advanced Maneuvers: Surgical Edits and Transplants

### The `edit` Command: Splitting Commits

Sometimes you make a monolithic commit that contains changes for two entirely separate features. You need to split it. This is where the `edit` command shines.

During an interactive rebase, mark the monolithic commit with `edit`. When Git reaches that commit, it will apply the changes and then pause, returning you to the terminal.

```bash
Stopped at 5c4b3a2... Add service and ingress manifests
You can amend the commit now, with
  git commit --amend
Once you are satisfied with your changes, run
  git rebase --continue
```

At this point, the files are modified in your working directory, and the monolithic commit is the current HEAD. To split it, you must essentially "uncommit" the changes without losing the file modifications. 

```bash
# Reset HEAD to the previous commit, leaving files modified in the working tree
git reset HEAD~1

# Now stage only the service file
git add service.yaml
git commit -m "feat: Add internal routing Service"

# Next, stage the ingress file
git add ingress.yaml
git commit -m "feat: Expose application via Ingress"

# Resume the rebase operation
git rebase --continue
```

You have successfully rewritten a single historical commit into two distinct, logical commits.

### Transplanting with `--onto`

The `git rebase --onto` command is a powerful tool for transplanting a sequence of commits from one base to another. This is highly useful in a microservices environment where feature branches often depend on other feature branches.

Imagine you are working on `feature-db-migration`. Another team member is working on `feature-api-update`, which branches off your migration branch because it needs the new database schema. 

Your colleague merges `feature-db-migration` into `main`, but they use a "Squash and Merge" strategy on GitHub. Your original commit SHAs are gone, replaced by a single new SHA on main. Your `feature-api-update` branch is now based on ghost commits that no longer exist in the upstream history. If you try a standard `git rebase main`, Git will try to re-apply the database migration commits, causing massive conflicts.

You need to sever the API updates from the old ghost commits and graft them directly onto `main`.

+---------------------------------------------------+
|           TRANSPLANTING WITH --ONTO               |
+---------------------------------------------------+
|                                                   |
| BEFORE:                                           |
|                                                   |
| Main:    [M1] ---> [M2] (Squashed DB Migration)   |
|                                                   |
| Ghost:       [D1] ---> [D2] (Old DB Migration)    |
|                           \                       |
| API Branch:                [A1] ---> [A2]         |
|                                                   |
| COMMAND: git rebase --onto main D2 api-branch     |
|                                                   |
| AFTER:                                            |
|                                                   |
| Main:    [M1] ---> [M2]                           |
|                        \                          |
| API Branch:             [A1'] ---> [A2']          |
+---------------------------------------------------+

The syntax is:
`git rebase --onto <new-base> <old-upstream> <branch-to-move>`

In our scenario:
```bash
git rebase --onto main feature-db-migration feature-api-update
```
This command translates to: "Take all the commits on `feature-api-update` that are NOT on `feature-db-migration`, and replay them on top of `main`." 

## Resolving Conflicts During a Rebase

Because a rebase replays commits sequentially, you may encounter conflicts midway through the process. Git will pause and alert you:

```bash
CONFLICT (content): Merge conflict in deployment.yaml
error: could not apply 3a2b1c4... Add memory limits
```

When this happens, you are in a detached HEAD state at the specific step of the rebase that failed. 

1. Open the conflicting files and resolve the merge markers (`<<<<<<<`, `=======`, `>>>>>>>`).
2. Stage the resolved files using `git add deployment.yaml`.
3. Do **not** run `git commit`. The rebase engine is managing the commits.
4. Tell the engine to proceed by running `git rebase --continue`.

If you realize the rebase was a mistake and you are hopelessly lost in conflicts, you can always bail out safely:

```bash
git rebase --abort
```
This command instantly terminates the rebase operation and returns your branch to exactly the state it was in before you typed `git rebase -i`.

## Did You Know?

- The Linux kernel project strictly forbids merge commits from contributors. All patches submitted to the kernel must be rebased by the author to maintain a perfectly linear history, which ensures the `git bisect` tool can efficiently hunt down regressions.
- The `fixup` command was introduced in Git version 1.7.0 specifically because developers were tired of the repetitive manual labor of deleting commit messages in the text editor every time they used the `squash` command.
- You can configure Git to automatically set up rebasing whenever you pull from a remote repository by executing `git config --global pull.rebase true`. This saves you from accidentally creating unnecessary merge commits when syncing your local feature branch with upstream changes.
- The `exec` command in interactive rebase allows you to run a shell command (like a syntax linter or a unit test suite) after every single commit is applied. If the test fails, the rebase pauses, allowing you to fix the broken commit immediately, ensuring your history is buildable at every step.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| **Force pushing a shared branch** | You rebased a branch that others are already working on, rewriting the history they depend on. | Communicate immediately. If others haven't done much work, they can `git fetch` and `git reset --hard origin/branch`. If they have, you may need to revert the force push via the reflog. |
| **Using squash when fixup was intended** | Misunderstanding the difference. You end up in an editor screen cluttered with five different "fixed typo" messages that you have to manually delete. | Close the editor, abort the rebase (`git rebase --abort`), and restart using `fixup` (or `f`) instead. |
| **Getting stuck in an edit loop** | Using the `edit` command, making changes, but running `git commit` instead of `git commit --amend`. This adds a new commit rather than modifying the paused one. | Use `git reset HEAD~1` to unstage the erroneous commit, make your changes, run `git commit --amend`, and then `git rebase --continue`. |
| **Resolving the same conflict iteratively** | Multiple commits touch the same file in a way that conflicts with the new base. You have to resolve the exact same block of code 3 times. | Enable `git rerere` (Reuse Recorded Resolution). Run `git config --global rerere.enabled true`. Git will remember how you solved the conflict the first time and automatically apply it. |
| **Dropping commits unintentionally** | Deleting a line in the interactive rebase text editor thinking it only deletes the message, not realizing it drops the entire commit. | Abort the rebase if caught immediately. If completed, use `git reflog` to find the SHA of the branch before the rebase and `git reset --hard` back to it. |
| **Rebasing in the wrong direction** | Running `git rebase feature-branch` while checked out on `main`, instead of the other way around. | Abort immediately. If completed, use `git reflog` to reset `main` back to its original state. |

## Quiz

<details>
<summary>Question 1: You are rebasing a feature branch onto main. Midway through, Git pauses and reports a conflict in `service.yaml`. You open the file, resolve the conflict, and save it. What is your exact next step to resume the rebase?</summary>
You must stage the resolved file using `git add service.yaml`, and then execute `git rebase --continue`. You must NOT run `git commit`, as the rebase engine is already in the process of constructing the commit for you. Running commit manually will disrupt the sequence.
</details>

<details>
<summary>Question 2: You pushed `feature-auth` to the remote repository yesterday, and your colleague pulled it to help test. Today, you realize your local commit history is messy. Should you run an interactive rebase to clean it up before opening the Pull Request?</summary>
No. This violates the Golden Rule of rebasing. Because your colleague has already pulled the branch, rewriting the history and force-pushing will cause their local repository to diverge catastrophically from the remote. You must either coordinate with them to wipe their local branch, or accept the messy history and use standard merges.
</details>

<details>
<summary>Question 3: You have three commits: Commit A (Add Deployment), Commit B (WIP testing), and Commit C (Fix Deployment configuration). You want to combine them all into a single commit with a brand new message. Which sequence of interactive rebase commands should you use?</summary>
You should use `reword` on Commit A, `fixup` on Commit B, and `fixup` on Commit C. The `reword` command will pause to let you write the brand new message, while the two `fixup` commands will meld the file changes into Commit A while discarding their useless "WIP" and "Fix" messages automatically.
</details>

<details>
<summary>Question 4: You accidentally committed an API token in Commit 2 of your feature branch. You are currently on Commit 6. You start an interactive rebase to remove it. You change Commit 2's instruction to `edit`. Git pauses the rebase. What commands do you run to remove the token and continue?</summary>
First, open the file containing the token, delete the token, and save the file. Next, stage the file with `git add <filename>`. Then, modify the paused commit by running `git commit --amend`. Finally, tell the rebase engine to proceed by running `git rebase --continue`.
</details>

<details>
<summary>Question 5: Your team uses a "Squash and Merge" policy for Pull Requests. You branched `backend-v2` off of `backend-v1`. `backend-v1` was just squashed and merged into main. You need to update `backend-v2` with the latest main. Why is a standard `git rebase main` a bad idea here?</summary>
Because the original commits of `backend-v1` were squashed, their SHAs no longer exist on main; they were replaced by a single new SHA. If you do a standard rebase, Git will attempt to replay the original `backend-v1` commits (which are still in `backend-v2`'s history) onto main, resulting in massive conflicts because main already has those changes in a different form. You must use `git rebase --onto` to transplant only the specific `v2` commits.
</details>

<details>
<summary>Question 6: You are halfway through a complex interactive rebase and you realize you have made a terrible mistake resolving a conflict. The files are a mess and you want to completely bail out and return to the state before you typed the rebase command. What do you do?</summary>
You run `git rebase --abort`. This command acts as an immediate escape hatch. It stops the rebase engine, clears out the temporary rebase state, and resets your working directory and branch pointer back to exactly where they were before the rebase began.
</details>

## Hands-On Exercise

In this exercise, you will create a messy commit history containing Kubernetes manifests and a leaked secret, and then use interactive rebasing to sculpt it into a clean, professional history.

### Setup

Run the following bash script in a safe, empty directory to generate the repository and the messy history.

```bash
mkdir k8s-rebase-lab && cd k8s-rebase-lab
git init
git branch -M main
echo "# K8s Application" > README.md
git add README.md && git commit -m "Initial commit"
git checkout -b feature-web-app

# Commit 1
cat <<EOF > deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
EOF
git add deployment.yaml && git commit -m "add deployment"

# Commit 2
cat <<EOF > configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  DB_PASSWORD: "super-secret-admin-pass"
EOF
git add configmap.yaml && git commit -m "wip: add configmap for db"

# Commit 3
echo "  labels: {app: web}" >> deployment.yaml
git add deployment.yaml && git commit -m "fix typo in deployment labels"

# Commit 4
cat <<EOF > service.yaml
apiVersion: v1
kind: Service
metadata:
  name: web-svc
EOF
git add service.yaml && git commit -m "add service"

# Commit 5
sed -i.bak 's/super-secret-admin-pass/REDACTED/' configmap.yaml && rm configmap.yaml.bak
git add configmap.yaml && git commit -m "remove password from configmap"

# Commit 6
echo "  ports: [{port: 80}]" >> service.yaml
git add service.yaml && git commit -m "finish service ports"
```

### Tasks

You currently have 6 messy commits on the `feature-web-app` branch. Your goal is to use `git rebase -i main` to reduce this history to exactly two clean commits.

1. **Start the Rebase**: Initiate an interactive rebase against the `main` branch.
2. **Consolidate the Deployment**: Reorder the instructions so the deployment typo fix (Commit 3) immediately follows the initial deployment commit (Commit 1). Use `fixup` to meld them.
3. **Consolidate the Service**: Reorder the instructions so the service port addition (Commit 6) immediately follows the initial service commit (Commit 4). Use `fixup` to meld them.
4. **Purge the Secret**: Reorder the ConfigMap commits so the removal (Commit 5) immediately follows the addition (Commit 2). Use `fixup` to meld the removal into the addition. This ensures the plaintext password never exists in the final history.
5. **Rename the Commits**: Use the `reword` command on the remaining primary commits to give them professional, descriptive messages.
   - Commit 1 should be named: `feat: Add Web Application Deployment`
   - Commit 2 should be named: `feat: Configure Application Services and Environment` (You can squash/fixup the service and configmap commits together).

### Success Criteria

- [ ] Run `git log --oneline`. You should see exactly three commits total: the initial README commit, the Deployment commit, and the Service/ConfigMap commit.
- [ ] Run `git log -p`. Verify that the string `super-secret-admin-pass` does not appear anywhere in the diff history.
- [ ] There should be no commits containing the messages "fix typo", "wip", or "finish service".

<details>
<summary>Solution Guide</summary>

1. Run `git rebase -i main`.
2. The initial text editor will look like this (abbreviated hashes):
```text
pick 1111111 add deployment
pick 2222222 wip: add configmap for db
pick 3333333 fix typo in deployment labels
pick 4444444 add service
pick 5555555 remove password from configmap
pick 6666666 finish service ports
```
3. Edit the file to reorder and change commands. Move related items together. Use `reword` for the base items and `fixup` for the modifications.
```text
reword 1111111 add deployment
fixup 3333333 fix typo in deployment labels
reword 4444444 add service
fixup 6666666 finish service ports
pick 2222222 wip: add configmap for db
fixup 5555555 remove password from configmap
```
*(Note: To combine the Service and ConfigMap into one commit as requested in the final step, you could change the `pick` on the configmap to a `fixup` attached to the service).*
```text
reword 1111111 add deployment
fixup 3333333 fix typo in deployment labels
reword 4444444 add service
fixup 6666666 finish service ports
fixup 2222222 wip: add configmap for db
fixup 5555555 remove password from configmap
```
4. Save and close the editor.
5. Git will pause twice to let you edit the commit messages for the two items you marked with `reword`.
6. Enter `feat: Add Web Application Deployment` for the first, and `feat: Configure Application Services and Environment` for the second.
7. Verify success with `git log -p`.

</details>

## Next Module

Now that you can sculpt a perfect history, it is time to learn how to recover when things go horribly wrong in [Module 4: The Safety Net](../module-4-undo-recovery/).