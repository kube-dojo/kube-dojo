---
title: "Module 6: The Digital Detective — Troubleshooting and Search"
description: "Master advanced Git search, forensics, and troubleshooting techniques to diagnose broken Kubernetes deployments."
sidebar:
  order: 6
---

# Module 6: The Digital Detective — Troubleshooting and Search

**Complexity**: [MEDIUM]  
**Time to Complete**: 90 minutes  
**Prerequisites**: Module 5 of Git Deep Dive  

## Learning Outcomes

After completing this module, you will be able to:

- **Diagnose** the exact commit that introduced a subtle configuration bug by implementing automated binary search algorithms with `git bisect run`.
- **Evaluate** the true lineage of code blocks across file renames, whitespace changes, and refactors to identify the original author using advanced `git blame` options.
- **Compare** and select appropriate search strategies to audit historical changes, utilizing Git's "Pickaxe" search (`git log -S`/`-G`) versus snapshot searches (`git grep`).
- **Design** targeted history filters to reconstruct precise audit trails for specific Kubernetes manifests, answering compliance questions about who changed what and when.
- **Implement** robust troubleshooting workflows that transition a broken cluster state into a quantifiable historical regression investigation.

## Why This Module Matters

It is 3:14 AM on Black Friday. The primary payment processing cluster, running perfectly for months, is suddenly dropping 15% of all incoming requests with a cryptic `503 Service Unavailable` error. The metrics dashboards are flashing red, the incident bridge is filling up with panicked executives, and the only clue you have is that the `payment-gateway` Kubernetes deployment manifest was "tweaked" sometime in the last 400 commits over the past three weeks by various platform engineering teams. 

Reverting the latest commit doesn't fix it. Rolling back the entire release is not an option because the release also contains critical, legally mandated compliance patches that went into effect at midnight. You need to find the exact line of YAML that broke the routing, you need to understand *why* that line was added, and you need to find it *fast*.

In these high-pressure moments, standard version control commands are insufficient. You are no longer a developer simply committing code; you are a digital detective conducting a forensic investigation on a live crime scene. While most engineers treat Git as a simple "save point" mechanism, its true power lies in its ability to dissect time. It holds the complete genomic sequence of your infrastructure. When something breaks, the answer is already in the repository, hidden among thousands of diffs. The difference between a five-minute resolution and a multi-hour outage is your ability to interrogate that history efficiently.

This module transitions you from simply saving history to actively weaponizing it for troubleshooting. You will learn how to automate the search for regressions using binary search algorithms, track the movement of copied-and-pasted code across your codebase to find its original author, and excavate your commit history for specific deleted configurations. By the end of this lesson, a repository with 10,000 commits will no longer be an intimidating haystack—it will be a structured, highly queryable database ready for your forensic commands.

## Section 1: The Binary Search Engine: `git bisect`

When a system fails but you don't know *when* the failure was introduced, reviewing commits one by one is a fool's errand. If you have 500 commits between a known working state (say, last month's release tag) and the currently broken state on `main`, checking each one linearly would take hours of tedious, error-prone work.

Git provides a built-in tool specifically engineered for this exact scenario: `git bisect`. It utilizes a fundamental computer science algorithm called **binary search** to find the offending commit in logarithmic time.

### The Mechanics of Binary Search

Imagine you are looking for a specific word in a 1,000-page physical dictionary. You don't read page 1, then page 2, then page 3. You open the book exactly to the middle (page 500). If your word comes alphabetically before the words on page 500, you instantly discard the entire right half of the book (pages 501-1000). You then open the left half to *its* middle (page 250), and repeat the process. With each and every step, you eliminate 50% of the remaining search space.

`git bisect` does exactly this with your Git commit history tree. You provide it with a "bad" commit (usually your current broken state, `HEAD`) and a "good" commit (a state in the past where you definitively know things worked). Git then automatically checks out the commit exactly halfway between them and pauses, essentially asking you: "Is the system broken at this specific commit?"

Based on your answer (`good` or `bad`), Git discards half the commits and moves to the middle of the remaining half.

```mermaid
flowchart TD
    subgraph S1 [Step 1: Test Midpoint C4]
        direction LR
        C1[C1: Good] --- C2[C2: ?] --- C3[C3: ?] --- C4{C4: Test} --- C5[C5: ?] --- C6[C6: ?] --- C7[C7: Bad]
    end

    subgraph S2 [Step 2: C4 is BAD, Test Midpoint C2]
        direction LR
        C1_2[C1: Good] --- C2_2{C2: Test} --- C3_2[C3: ?] --- C4_2[C4: Bad]
    end

    subgraph S3 [Step 3: C2 is GOOD, Test Midpoint C3]
        direction LR
        C2_3[C2: Good] --- C3_3{C3: Test} --- C4_3[C4: Bad]
    end
    
    S1 -->|Result: BAD| S2
    S2 -->|Result: GOOD| S3
    S3 -->|Result: GOOD| R[Conclusion: C4 is the first bad commit]
```

### The Manual Bisect Workflow in Practice

Let's walk through the standard manual workflow for a broken Kubernetes manifest. Suppose your `deployment.yaml` is suddenly failing API server validation, but you aren't sure which of the recent infrastructure-as-code changes caused the syntax error.

**Step 1: Initialize the session.**
```bash
git bisect start
```
This command activates the bisect mode. Git begins tracking your progress.

**Step 2: Define the Bad state.**
Mark the current (broken) state as bad. If you omit the commit hash, Git assumes your currently checked-out commit (`HEAD`) is the bad one.
```bash
git bisect bad
```

**Step 3: Define the Good state.**
You check your release notes and remember that version `v1.2.0` deployed perfectly last week. You mark that tag as the known good state.
```bash
git bisect good v1.2.0
```

Git calculates the distance between the two points and immediately responds:
```bash
Bisecting: 125 revisions left to test after this (roughly 7 steps)
[a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0] Update resource requests
```

At this moment, Git has physically checked out commit `a1b2c3d4`. Your repository is now in a "detached HEAD" state, "time-traveled" to the exact moment that commit was made.

> **Pause and predict**: If you run `kubectl apply --dry-run=server -f deployment.yaml` right now and it succeeds, what specific command should you issue to Git next?
>
> *Answer*: You must run `git bisect good`. This tells Git that the bug was introduced *after* this checked-out commit, allowing the algorithm to safely discard the older, left half of the search space.

**Step 4: The Testing Loop.**
You test the manifest. 
- If the dry-run fails with the validation error, type `git bisect bad`. 
- If the dry-run succeeds, type `git bisect good`. 
Git will automatically check out the next optimal midpoint and prompt you again.

**Step 5: The Reveal.**
After approximately 7 iterations, Git will pinpoint the exact breaking change:
```bash
b9c8d7e6f5g4h3i2j1k0l9m8n7o6p5q4r3s2t1u0 is the first bad commit
commit b9c8d7e6f5g4h3i2j1k0l9m8n7o6p5q4r3s2t1u0
Author: Alex Engineer <alex@example.com>
Date:   Tue Oct 24 14:32:11 2025 -0400

    chore: update apiVersion for HorizontalPodAutoscaler
```

**Step 6: Cleanup (Crucial!).**
Once you've identified the culprit, you must explicitly tell Git to terminate the forensic session. This returns your repository out of the detached HEAD state and back to the branch you were on before you started.
```bash
git bisect reset
```

### War Story: The Silent Helm Regression

A platform engineering team managing a multi-tenant cluster noticed that new tenants onboarded that morning were missing their default `NetworkPolicies`. No automated alerts fired, the pipelines succeeded, but the policies simply weren't rendering in the cluster. They knew the onboarding process worked flawlessly in the `v3.1.0` release tag, but the current `main` branch was silently failing. 

With over 200 commits touching various complex Helm chart templates across multiple repositories, finding a syntax typo manually by reviewing PRs was impossible. An engineer initiated a manual `git bisect`, testing the output of `helm template` at each step. In exactly 8 steps, Git found the breaking commit. It took 4 minutes to locate a missing YAML indentation block nested deep inside a helper template—a bug that would have taken hours of intense code review to spot with the human eye.

## Section 2: Automating Forensics: `git bisect run`

Manual bisection is incredibly powerful, but humans are inherently slow and prone to context-switching errors. If testing a single commit requires you to compile a Go binary, wait 45 seconds, check a log file output, and then manually type `git bisect good/bad`, you will quickly lose patience. Furthermore, manual testing is susceptible to human error—you might accidentally type `good` when a subtle error actually occurred.

The true, transformative magic of Git forensics unlocks when you combine `git bisect` with shell automation. 

`git bisect run` allows you to provide an executable script or a direct shell command. Git will automatically execute that command at every step of the bisection algorithm. 
- If the command exits with code `0` (success), Git automatically marks the current commit as **good**.
- If the command exits with code `1` through `124`, or `126-127` (general failures), Git automatically marks the current commit as **bad**.
- Exit code `125` is reserved for a special case: it tells Git the commit is **untestable** (e.g., the code fails to compile due to an unrelated issue), instructing Git to skip this commit and pick an adjacent one.

### Designing a Bulletproof Bisect Script

Suppose we have a complex `StatefulSet` manifest that is suddenly failing Kubernetes API server validation. We want to find the exact commit that introduced the invalid schema among 300 recent commits.

We can author a dedicated bash script, `test-manifest.sh`. 

*Crucial rule*: Your test script should ideally be located *outside* the Git repository you are testing (e.g., in `/tmp/`), or you must guarantee the script itself wasn't modified, renamed, or deleted during the historical timeline you are traversing!

```bash
#!/usr/bin/env bash
# Location: /tmp/test-manifest.sh

# We do NOT use 'set -e' because we want to capture the failure exit code manually,
# rather than having the script abort immediately.

echo "Testing commit: $(git rev-parse --short HEAD)"

# Run a dry-run apply against the API server to validate the YAML schema
kubectl apply -f k8s/production/statefulset.yaml --dry-run=server > /dev/null 2>&1

# Capture the exit code of the kubectl command
EXIT_CODE=$?

# Evaluate the exit code and communicate with git bisect
if [ $EXIT_CODE -eq 0 ]; then
    echo "Validation passed. Returning GOOD."
    exit 0 # Tells Git this commit is Good
else
    echo "Validation failed. Returning BAD."
    exit 1 # Tells Git this commit is Bad
fi
```

Make the script executable: 
```bash
chmod +x /tmp/test-manifest.sh
```

### Executing the Automated Run

With the script ready, we define our boundaries and unleash the automation. 

```bash
# 1. Initialize
git bisect start

# 2. Define the current broken state
git bisect bad HEAD

# 3. Define the last known working release
git bisect good v2.4.0

# 4. Hand over control to the script
git bisect run /tmp/test-manifest.sh
```

Git will now seize control of your terminal. It will rapidly check out commits, execute the script, evaluate the exit code, and calculate the next algorithmic jump entirely unattended. You will witness a flurry of text as it tests 10 or 20 commits in mere seconds.

```text
running /tmp/test-manifest.sh
Testing commit: 7a8b9c0
Validation passed. Returning GOOD.
Bisecting: 67 revisions left to test after this (roughly 6 steps)
...
running /tmp/test-manifest.sh
Testing commit: 1d2e3f4
Validation failed. Returning BAD.
Bisecting: 33 revisions left to test after this (roughly 5 steps)
...
f8e7d6c5b4a3c2d1e0f9a8b7c6d5e4f3a2b1c0d9 is the first bad commit
```

What would take an engineer 30 minutes of tedious manual environment setup and testing takes the automation loop 4 seconds.

### Handling Untestable Commits (Exit 125)

> **Pause and predict**: If you are using `git bisect run make test` to find a regression, and the `Makefile` itself was temporarily broken by a junior developer in the middle of your history (failing to compile entirely), what will happen to your bisection algorithm?
>
> *Answer*: If `make test` fails because of a raw compilation error that is *unrelated* to the logical bug you are hunting, the script will exit with a non-zero code. Git will blindly mark that commit as *bad* for the bug you are tracking! This false positive will completely derail the binary search, leading you to the wrong culprit.

To construct a robust bisect script, you must differentiate between the *bug occurring* and the *test failing to run at all*. This is where exit code `125` saves the day.

```bash
#!/usr/bin/env bash
# /tmp/robust-test.sh

# Step 1: Attempt to compile the binary
make build
if [ $? -ne 0 ]; then
    echo "Compilation failed! This commit is untestable."
    # Exit 125 tells git bisect: "Skip this commit and find another midpoint"
    exit 125 
fi

# Step 2: Run the actual test for the bug
./bin/app-tester --run-integration
if [ $? -eq 0 ]; then
    exit 0 # Good
else
    exit 1 # Bad
fi
```

By correctly utilizing exit code `125`, your automated bisection can elegantly step around broken builds, missing dependencies, and corrupted history states without losing its algorithmic path to the true regression.

## Section 3: The Code Archaeologist: `git blame` beyond the basics

Finding the specific commit that broke the system is often only half the battle. Once you locate the offending lines of code, you need context. You need to understand *why* the change was made. Was it a simple typo? A fundamental misunderstanding of the system architecture? Or was it a deliberate, calculated change to support a new feature that unfortunately triggered unintended side effects?

`git blame` is the archaeologist's brush. It annotates every single line in a file with the revision hash, the author's name, and the timestamp of when that specific line was last modified.

### The Overwhelming Standard Blame

Running a raw `git blame` on a large file is equivalent to drinking from a firehose:

```bash
git blame k8s/deployment.yaml
```

Output:
```text
^e2f3g4h (Alice     2024-01-10 09:00:00 -0400   1) apiVersion: apps/v1
^e2f3g4h (Alice     2024-01-10 09:00:00 -0400   2) kind: Deployment
b9c8d7e6 (Bob       2024-02-15 14:30:00 -0400   3) metadata:
b9c8d7e6 (Bob       2024-02-15 14:30:00 -0400   4)   name: payment-gateway
... (800 more lines)
```

This is unhelpful. When troubleshooting, you usually only care about a highly specific block of code that looks suspicious. 

### Targeted Blame: Line Ranges (`-L`)

If you know the suspected bug resides on lines 45 through 50, restrict the output aggressively:

```bash
git blame -L 45,50 k8s/deployment.yaml
```

More powerfully, you can utilize regular expressions to search for a specific function, stanza, or block name. For example, to blame only the `resources` block in a Kubernetes manifest without needing to know the exact line numbers:

```bash
git blame -L '/resources:/',+10 k8s/deployment.yaml
```
This tells Git: "Scan the file for the regex `/resources:/`, and print the blame annotations for that exact line plus the 10 lines immediately following it."

### Ignoring Formatting Noise (`-w` and `.git-blame-ignore-revs`)

A common frustration is running `git blame` only to discover that every single line in the file was "authored" by a CI bot that ran a code formatter (like `prettier` or `gofmt`), completely masking the human engineers who actually wrote the logic.

To pierce through whitespace-only changes, use the `-w` flag:

```bash
git blame -w k8s/deployment.yaml
```
Git will ignore commits that purely changed spaces to tabs, indentation, or trailing whitespace, and will reach further back in history to find the commit that introduced the actual text characters.

For massive repository-wide formatting overhauls (e.g., your team decided to convert a massive codebase from 2-space to 4-space indentation), `-w` isn't enough. You can explicitly instruct Git to completely ignore specific commits during blame resolution using an ignore file:

```bash
git config blame.ignoreRevsFile .git-blame-ignore-revs
```
Any commit hash placed inside the `.git-blame-ignore-revs` file will be skipped, allowing `git blame` to show the true authors of the code prior to the mass reformatting event.

### Following Code Movement (`-C`)

Here is where `git blame` transitions from a basic tool to advanced forensics. Often, the commit that a standard `git blame` points to is *not* the commit where the code was actually authored. It might merely be the commit where an engineer moved the code from one file to another, or refactored a monolithic file into smaller modules.

If Alice wrote a brilliant, complex Helm template in `helpers.tpl` six months ago, and Bob later moved that exact template block into a new `_ingress.tpl` file during a refactoring sprint, a standard `git blame` on `_ingress.tpl` will erroneously state that Bob wrote every line. This is useless if you need to ask the original author (Alice) why a specific, obscure logic gate exists.

Enter the `-C` (Copy/Movement) flag.

```bash
git blame -C k8s/charts/payment/_ingress.tpl
```

The `-C` flag forces Git to analyze the repository history and heuristically detect if the code on that line was copied or moved from *another file* within the same commit. If Git detects a move, it bypasses the refactoring commit and reports the *original* author and the *original* commit where the code was birthed.

You can escalate this search power by using `-C -C` or even `-C -C -C`. This forces Git to search aggressively across all commits and all files, regardless of whether the files were modified in the identical commit. (Note: This is computationally expensive on massive repositories, but invaluable for desperate forensics).

```bash
# Standard blame shows the refactoring commit:
c8d7e6f5 (Bob       2024-03-01 10:00:00 -0400 12) {{ include "mychart.labels" . | nindent 4 }}

# Blame with -C -C pierces the veil to find the true author:
a1b2c3d4 (Alice     2023-11-15 09:15:00 -0400 12) {{ include "mychart.labels" . | nindent 4 }}
```
*Notice how the advanced blame correctly attributes the line to Alice's original creation, looking straight past Bob's organizational commit.*

> **Stop and think**: Which approach would you choose here and why?
> You are auditing a critical `securityContext` block in a Pod manifest. The block looks highly suspicious and insecure. Standard `git blame` says "Jenkins CI User" last touched the lines. You check the Jenkins commit, and it was an automated task that converted all YAML files from 4 spaces to 2 spaces. How do you find the human who actually authored the insecure block?
>
> *Answer*: You must combine flags. You use `git blame -w` (which explicitly ignores whitespace changes) combined with `-C` (in case the block was also moved). The formatting commit purely altered whitespace, so `-w` will look right past it to the underlying text change.

## Section 4: The Pickaxe Search: `git log -S` and `-G`

Sometimes, you don't have a broken file to blame. Sometimes a configuration value simply *vanished* from the codebase, and you need to know exactly when, why, and who authorized the deletion.

Imagine your application requires an environment variable `DB_MAX_CONNECTIONS=100`. You inspect the current `deployment.yaml` and the variable is completely gone. Because the lines are deleted, `git blame` is useless (it can only annotate lines that physically exist in the current file).

> **Pause and predict**: You run `git grep` for the deleted environment variable and get nothing. Why?
>
> *Answer*: `git grep` exclusively searches the files as they exist in your *current* working directory (the snapshot). Because the variable was deleted in a previous commit, it physically no longer exists to be grepped. You need a tool that searches historical diffs instead of current files.

To find ghost code, you need the Git "Pickaxe".

### The `-S` Flag (String Addition/Deletion)

The `git log -S` command does not search the files currently on your hard drive. It searches the historical *diffs* (the patches) of all commits in the repository. It looks specifically for commits where the number of occurrences of a string changed—meaning the string was definitively added to or removed from the codebase.

```bash
git log -S "DB_MAX_CONNECTIONS" --oneline
```

Output:
```text
f9a8b7c Remove legacy database connection limits
a1b2c3d Add explicit connection limits for stability
```

You have instantly found the commit (`f9a8b7c`) that removed the value. You can now inspect it using `git show f9a8b7c` to see exactly who removed it, read their commit message, and review the pull request context to understand the rationale.

### The `-G` Flag (Regex Search in Diffs)

While `-S` is strict and looks for exact string additions or deletions, the `-G` flag utilizes Regular Expressions to search the historical diffs. This is crucial when you are looking for variations of a configuration.

If you want to find out when any CPU `limits` were historically modified in your manifests, searching for a static string won't work because the values fluctuate (e.g., `100m`, `500m`). You must search the diffs for the regex pattern `cpu:\s*[0-9]+m`:

```bash
git log -G "cpu:\s*[0-9]+m" --oneline -p
```

*(Adding the `-p` or `--patch` flag is a pro-tip. It tells Git to not just list the commit hashes, but to immediately output the actual diff for the matching commits, allowing you to visually verify the change without running secondary `git show` commands).*

Output snippet:
```diff
commit e4d3c2b1
Author: SRE Team <sre@example.com>
Date:   Mon Nov 05 11:20:00 2024 -0400

    feat: scale up frontend resources for holiday traffic

diff --git a/k8s/frontend-deployment.yaml b/k8s/frontend-deployment.yaml
--- a/k8s/frontend-deployment.yaml
+++ b/k8s/frontend-deployment.yaml
@@ -45,7 +45,7 @@
         resources:
           requests:
             cpu: 100m
-          limits:
-            cpu: 200m
+          limits:
+            cpu: 500m
```

### Comparison Matrix: Pickaxe vs. Snapshot Searches

It is critical to internalize the conceptual difference between Pickaxe queries (`git log -S`) and snapshot queries (`git grep`).

| Command | What it Searches | Use Case |
| :--- | :--- | :--- |
| **`git log -S "password"`** | Searches the *history of changes* (diffs) across all commits. | "Find me the commit where this string was added or removed." |
| **`git grep "password"`** | Searches the *current snapshot* (the files) of the specified commit. | "Does this string exist in the codebase right now?" |

If an API key was hardcoded into a manifest, committed to the repository, and then deleted in a subsequent commit two days later, `git grep "API_KEY"` will return absolutely nothing (because the current working directory is clean). However, `git log -S "API_KEY"` will vividly flag the commit where it was added and the commit where it was removed, revealing the hidden security breach in your repository's permanent record.

## Section 5: High-Speed Scanning: `git grep`

If you *are* searching for something that currently exists in your repository snapshot, you should completely abandon the standard Linux `grep` command and exclusively use `git grep`.

### Why `git grep` Dominates Standard `grep`

1. **Unmatched Speed**: `git grep` is exponentially faster because it only searches files tracked by Git. Standard `grep -rn` will waste massive amounts of I/O resources blindly traversing `.git/` objects, deep `node_modules/` folders, `venv/` environments, and compiled binaries that you don't care about.
2. **Contextual Awareness**: It intrinsically understands your repository structure and respects `.gitignore`.
3. **Time Travel Scanning**: This is its superpower. You can use `git grep` to search the entire codebase *as it existed* at any historical commit, tag, or remote branch, without ever needing to perform a slow `git checkout`.

### Searching Alternate Dimensions (Branches)

> **Stop and think**: Which tool would you choose? How would you search a colleague's branch for a specific configuration without checking it out or stashing your current uncommitted work?
>
> *Answer*: You append the remote branch name to `git grep`. Because `git grep` natively reads Git's internal tree objects, running `git grep "search-term" origin/their-branch` searches their snapshot directly from your current working directory.

Suppose a colleague sends a Slack message: "I added a `PodDisruptionBudget` manifest on my feature branch, but I can't remember what I named the file, and I need you to review it."

You don't need to stash your local changes and checkout their branch. You can search the tip of their branch directly from where you sit:

```bash
git grep "kind: PodDisruptionBudget" origin/feature-ha-setup
```

Output:
```text
origin/feature-ha-setup:k8s/infra/pdb-frontend.yaml:kind: PodDisruptionBudget
```
You instantly have the exact file path without touching your working directory.

### Complex Boolean Queries

`git grep` supports robust boolean logic (`--and`, `--or`, `--not`). If you want to find all Kubernetes service files that contain `kind: Service` but verify which ones are exposed as `type: LoadBalancer` to audit your public endpoints:

```bash
git grep -e "kind: Service" --and -e "type: LoadBalancer"
```

You can even combine this with Git's tree objects to search the entire repository history simultaneously. To search all branches and all historical commits for a specific, highly deprecated API version:

```bash
git grep "apiVersion: policy/v1beta1" $(git rev-list --all)
```
*(Warning: This command searches the raw contents of every single commit ever made across all branches. It may take several seconds on massive monorepos, but it is an incredibly powerful audit tool).*

## Section 6: Reconstructing Audit Trails: Filtering History

In enterprise infrastructure environments, troubleshooting heavily overlaps with compliance and auditing. When a Sev-1 incident concludes, management will demand a precise timeline of events. Git allows you to generate forensic audit trails by aggressively filtering the commit history.

The `git log` command contains highly specific filtering parameters that act like a SQL database query against your infrastructure history.

### Filtering by Time and Identity

To find all configuration changes made by a specific contractor since the beginning of the month:

```bash
git log --author="contractor.name" --since="2024-10-01" --oneline
```

### Filtering by File Path Lineage

If a specific `config/settings.yaml` file is causing issues, you do not care about the 5,000 commits modifying the application's Go code. You only care about commits that explicitly mutated that single YAML file.

```bash
git log --oneline -- config/settings.yaml
```
*(The double dash `--` is a critical Git convention. It explicitly tells Git: "Stop parsing command-line flags. Everything following this double dash is a literal file path, not a branch name or tag name").*

### Creating the Executive Audit Report

You are asked to provide a comprehensive compliance report of all changes made to the production Kubernetes manifests (`k8s/prod/`) during the mandated holiday change-freeze period (Dec 20 to Jan 2). You need to know not just the commit message, but exactly which files were altered.

```bash
git log \
  --since="2023-12-20" \
  --until="2024-01-02" \
  --name-status \
  -- k8s/prod/
```
The `--name-status` flag modifies the output. Instead of just showing the commit message, it attaches a granular list of files that were Modified (M), Added (A), or Deleted (D) in that specific commit.

Output:
```text
commit d4c3b2a1
Author: DevOps Bot <bot@example.com>
Date:   Wed Dec 27 03:00:00 2023 -0400

    Automated image tag update for frontend

M       k8s/prod/frontend-deployment.yaml
A       k8s/prod/frontend-configmap.yaml
```

### Formatting for CSV or Automation

If you need to export this data into a SIEM (Security Information and Event Management) system or a CSV spreadsheet for an auditor, use `--pretty=format`:

```bash
git log --since="2024-01-01" --pretty=format:"%h,%an,%ad,%s" --date=short -- k8s/
```
Output:
```text
a1b2c3d,Alice Engineer,2024-01-15,Update ingress rules
e4f5g6h,Bob Developer,2024-01-12,Fix typo in deployment
```

By mastering these targeted filters and formatting options, you transform Git from a passive code storage locker into an active, aggressively auditable database of infrastructure state.

## Did You Know?

1. **The Origin of the "Pickaxe"**: The `-S` flag is colloquially known as the "Pickaxe" search because it was originally engineered by Git developers to "mine" deep into the sedimentary history of a repository to find exactly where a specific block of code was buried or unearthed.
2. **`git bisect` has a Graphical View**: If you are in the middle of a complex bisection, lose track of your mental model, and get confused about your boundaries, running `git bisect visualize` (or `git bisect view`) will instantly open a graphical Git viewer (like `gitk`) showing exactly which commits are marked good, bad, and remaining to be tested.
3. **You Can Blame Backwards in Time**: While standard `git blame` finds the *origin* (addition) of a line, you can use `git blame --reverse START..END file` to find the exact commit where a line was definitively *deleted* or replaced within a specific revision range.
4. **Git Intelligently Skips Empty Commits**: If a commit in your automated `git bisect` range resulted in an empty diff (perhaps a merge commit that resolved no conflicts), `git bisect` is mathematically smart enough to skip testing it entirely, as an empty commit cannot possibly introduce a new logical bug to the codebase.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| **Forgetting `git bisect reset`** | After finding the bug, engineers celebrate and forget they are left in a "detached HEAD" state deep in the past. | Always execute `git bisect reset` immediately after concluding your investigation to return to your original branch. |
| **Testing Dirty Working Trees** | Trying to initiate `git bisect start` while you have uncommitted changes in your working directory. | Git will refuse to checkout the midpoints to protect your unsaved work. Run `git stash` to save your changes before starting a bisection. |
| **Using `git grep` to find deleted code** | Misunderstanding that `git grep` only searches the *current* state of the tree. It cannot find what is gone. | If you are hunting for code that was removed historically, you must switch tools and use the Pickaxe (`git log -S` or `-G`). |
| **Trusting blame on reformatted files** | Running tools like `prettier` or `gofmt` rewrites every line, making the automated formatter the "author" of the entire file. | Use `git blame -w` to aggressively ignore whitespace changes, and combine it with `-C` to follow code movement beyond simple edits. |
| **Writing bisect scripts that exit `1` on compile errors** | The test script fails because of an unrelated infrastructure error or missing package, marking the commit as "bad" for the specific bug you are tracking. | Ensure your script differentiates between the *specific bug* failing (exit `1`) and an *untestable environment* (exit `125`). |
| **Blaming the wrong branch** | Running `git blame` while currently checked out on an outdated, stale feature branch, missing recent fixes. | Always ensure you are on the correct target branch (e.g., `main`), or explicitly specify the branch: `git blame main -- file.txt`. |

## Quiz

<details>
<summary><strong>Question 1</strong>: You are running an automated <code>git bisect run ./test.sh</code>. On the third algorithm step, the commit checked out introduces a severe syntax error in your build Makefile that has absolutely nothing to do with the Kubernetes routing bug you are investigating. The build fails completely. What must <code>test.sh</code> do to handle this gracefully without ruining the bisection?</summary>

**Answer**: The script must be intelligent enough to detect the build/syntax error independently of the routing test and exit with code `125`. Exit code `125` specifically communicates to `git bisect` that the current commit is completely untestable. Git will then discard this commit from the calculation and select an adjacent commit to test instead, preserving the mathematical integrity of the binary search for the actual routing bug. This prevents the algorithm from falsely marking the commit as the source of the routing regression.
</details>

<details>
<summary><strong>Question 2</strong>: A critical security patch was applied to a Kubernetes `NetworkPolicy` three months ago. Today, a security scan reveals the vulnerability has returned. The policy file looks correct now, but you strongly suspect a contractor temporarily removed the patch last month before quietly putting it back. How do you definitively prove the patch was temporarily removed?</summary>

**Answer**: Utilize the Pickaxe search: `git log -S "your-specific-patch-string"`. Because `git log -S` searches the diffs for commits where the string was either added *or* removed, it will expose the entire timeline. If the output shows three distinct commits (the original addition, a removal commit, and a recent re-addition commit), you have incontrovertible proof the patch was temporarily reverted. Standard `git grep` would only show that the string exists currently, failing to expose the historical deletion and re-addition.
</details>

<details>
<summary><strong>Question 3</strong>: You are reviewing a monolithic `StatefulSet` manifest. `git blame` indicates that your junior engineer, Sam, wrote a highly complex, potentially dangerous storage volume configuration yesterday. However, during a code review, Sam claims they merely moved the file from `infra/` to `k8s/` during a reorg and didn't write the actual logic. How do you verify Sam's claim and locate the true author?</summary>

**Answer**: Execute `git blame -C k8s/statefulset.yaml`. The `-C` flag explicitly instructs Git to detect code movement and copying across files within the same commit. Git will look right past Sam's file-move commit and annotate the lines with the original author who wrote the storage configuration in the `infra/` directory months ago. By tracing the content rather than just the file path, you can accurately identify who originally designed the complex and dangerous volume configuration.
</details>

<details>
<summary><strong>Question 4</strong>: Your production API is returning 500 errors. You know it was stable at tag `v2.0` and is broken at `HEAD`. There are 800 commits between them. You want to automate finding the bug. You write a script `check-api.sh` that curls the `https://api.production.com/health` endpoint. You run `git bisect start HEAD v2.0` and then `git bisect run ./check-api.sh`. Why will this approach fundamentally fail?</summary>

**Answer**: Bisection relies on checking out historical code *locally*. `check-api.sh` is curling the *live production API*, which is utterly completely unaffected by your local Git repository checking out older commits. Your local Git state does not magically or instantly deploy to production at each bisection step. To automate this, your script must build and run the application locally (or deploy it to a local ephemeral cluster like Kind) based on the currently checked-out commit, and *then* curl that local endpoint.
</details>

<details>
<summary><strong>Question 5</strong>: You need to find a forgotten AWS API key (`AKIAIOSFODNN7EXAMPLE`) that someone accidentally committed to the repository months ago and later removed to cover their tracks. You run `git grep "AKIAIOSFODNN7EXAMPLE"`. It returns nothing. Why, and what is the correct command to find the breach?</summary>

**Answer**: `git grep` only searches the files as they exist in the currently checked-out snapshot (the working directory). Since the key was removed in a later commit, it physically does not exist in the current files. You must use `git log -S "AKIAIOSFODNN7EXAMPLE"` to search through the historical diffs of the entire repository to locate the exact commit where the key was originally added. This allows you to find exactly when the breach occurred and verify when it was eventually patched out.
</details>

<details>
<summary><strong>Question 6</strong>: You are auditing a messy commit history. You want to extract all commits made by the "platform-team" that specifically modified files inside the `k8s/networking/` directory, and you mandate seeing exactly which files were changed (Added, Modified, Deleted) in each commit. What exact command achieves this?</summary>

**Answer**: You must execute `git log --author="platform-team" --name-status -- k8s/networking/`. The `--author` flag filters by the committer name, the `--name-status` flag modifies the output to list the specific files altered in each commit, and the `--` followed by the directory path strictly limits the search to only commits that mutated that specific networking folder. Using these combined filters allows you to quickly generate an audit trail that pinpoints exact file modifications made by a specific group without being overwhelmed by unrelated repository activity. This approach is essential for compliance audits where precision and clarity of historical changes are legally mandated.
</details>

## Hands-On Exercise: The Case of the Broken Manifest

In this exercise, you will create a fresh repository with a simulated history, intentionally introduce a subtle bug, bury it under dozens of irrelevant commits, and then use `git bisect` and `git blame` to solve the forensic case.

### Step 1: Scenario Setup

First, we need to generate a repository with a deep history. Open your terminal, create a new directory, and execute the following bash script to simulate a month of active development.

```bash
mkdir k8s-forensics-lab && cd k8s-forensics-lab
git init

# Create the initial, perfectly working manifest
cat << 'EOF' > deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: nginx
        image: nginx:1.27.0
        ports:
        - containerPort: 80
EOF
git add deployment.yaml
git commit -m "Initial commit: working deployment"
git tag v1.0

# Simulate 20 good, benign commits
for i in {1..20}; do
  echo "# Comment $i" >> deployment.yaml
  git commit -am "chore: minor update $i"
done

# INTRODUCE THE BUG (Typo in containerPort: 80 -> 8080)
sed -i.bak 's/containerPort: 80/containerPort: 8080/' deployment.yaml
rm deployment.yaml.bak
git commit -am "fix: adjust port configuration for new ingress"

# Simulate 30 more commits completely burying the bug
for i in {21..50}; do
  echo "# Comment $i" >> deployment.yaml
  git commit -am "chore: minor update $i"
done
```

Your repository now contains over 50 commits. The current `deployment.yaml` has a critical bug (`containerPort: 8080` instead of `80`, which breaks the Nginx default internal routing), but it's buried deep in the git history.

### Step 2: Verify the Problem

Inspect the current file to confirm the broken state exists at `HEAD`.

```bash
cat deployment.yaml | grep containerPort
```
*Expected Output*: `containerPort: 8080` (This is incorrect, it must be 80).

### Step 3: Author the Validation Script

We will automate the search. We definitively know `containerPort: 80` is the correct state. We will author a script that explicitly checks for the correct port configuration.

Create a file named `/tmp/test-port.sh`:

```bash
#!/usr/bin/env bash
# Location: /tmp/test-port.sh

# Check if the deployment contains the correct exact string 'containerPort: 80'
# The '$' anchors the search to the end of the line, ensuring '8080' fails.
grep "containerPort: 80$" deployment.yaml > /dev/null

# grep exits 0 if the string is found (Good commit), 1 if not found (Bad commit)
exit $?
```
Make the test script executable:
```bash
chmod +x /tmp/test-port.sh
```

### Step 4: Execute the Automated Bisect

Now, instruct Git to algorithmically hunt down the bug.

- [ ] Initialize the bisect process: `git bisect start`
- [ ] Mark the current broken state: `git bisect bad HEAD`
- [ ] Mark the known good release tag: `git bisect good v1.0`
- [ ] Hand over execution to the automation script: `git bisect run /tmp/test-port.sh`

<details>
<summary><strong>View Expected Output</strong></summary>

```bash
running /tmp/test-port.sh
Bisecting: 12 revisions left to test after this (roughly 4 steps)
[some-hash] chore: minor update 26
...
running /tmp/test-port.sh
[hash] is the first bad commit
commit [hash]
Author: Your Name <your.email@example.com>
Date:   [Date]

    fix: adjust port configuration for new ingress
```
Git has successfully found the exact commit that mutated the port, traversing 50 commits and executing 5 tests in a fraction of a second.
</details>

### Step 5: Clean Up and Interrogate the Code

- [ ] Terminate the forensic session and return to reality: `git bisect reset`
- [ ] You now possess the commit message: `"fix: adjust port configuration for new ingress"`. Let's assume you want to see exactly who made that change on the line itself. Use targeted `git blame` against the port line.

```bash
git blame -L '/containerPort/',+1 deployment.yaml
```

<details>
<summary><strong>Solution Explanation</strong></summary>

The `git blame` command targets the regular expression `/containerPort/` and explicitly renders only that line. You will see the specific commit hash, your name (the committer), and the precise timestamp of when the port was incorrectly modified. By chaining automated bisection with targeted line-blame, you have achieved 100% forensic visibility into the infrastructure failure.
</details>

## Next Module

Now that you possess the ability to dissect history to locate regressions and build forensic audit trails, it is time to look outwards. Learn how to synchronize your local work with external servers, handle complex merge conflicts, and manage upstream changes safely in [Module 7: Professional Collaboration](../module-7-remotes-prs/).