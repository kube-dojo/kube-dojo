---
title: "Module 0.6: Git Basics — Track Your Work"
slug: prerequisites/zero-to-terminal/module-0.6-git-basics
sidebar:
  order: 7
---

# Module 0.6: Git Basics — Track Your Work

**Complexity**: [BEGINNER]
**Time to Complete**: 45 minutes
**Prerequisites**: Module 0.5 (Editing Files)

## Learning Outcomes

After completing this module, you will be able to:
- Initialize local Git repositories and configure user identities for accurate commit attribution.
- Construct a logical commit history by selectively staging file modifications using `git add` and `git commit`.
- Diagnose unexpected repository states by analyzing `git status`, `git log`, and `git diff` outputs.
- Synchronize local repositories with remote servers using `git push` and `git pull`.
- Formulate a `.gitignore` file to prevent sensitive data or generated artifacts from being tracked.

## Why This Module Matters

Teams that manage infrastructure files on a shared drive without version control can easily change the wrong environment by mistake and have no reliable audit trail when something breaks.

When the system failed, the team could see only the current broken file state. Without version control, they had to reconstruct the previous configuration manually, which slowed recovery and made the incident more damaging.

Version control prevents this exact scenario. [Git, the industry standard for version control](https://en.wikipedia.org/wiki/Git), acts as an unbreakable time machine for your code and configuration. It records every change, identifies exactly who made it, and usually allows you to quickly return to a previous committed state. In the modern cloud-native world, infrastructure is defined as code. If you cannot track, review, and revert your infrastructure code with absolute certainty, you are operating a disaster waiting to happen. Mastering Git is not optional for platform engineers; it is the foundational skill upon which all reliable automation and collaboration is built. 

Modern CI/CD pipelines rely on a version-controlled source of truth, and Git is the system most teams use for that job. The entire premise of automated deployments relies on a single, trusted source of truth that triggers automation whenever a new, approved change is detected. If you do not understand Git, you cannot understand modern software delivery.

## Section 1: The Concept of Version Control and Git's Architecture

Before typing any commands, you must understand how Git thinks about your files. Many beginners struggle with Git because they treat it like a simple backup tool (like Dropbox or Google Drive). Git is entirely different. Git does not just sync files continuously in the background; it takes deliberate, immutable snapshots of your project at specific points in time, but only when you explicitly command it to do so.

Think of Git like a video game with manual save points. You can play the game, make mistakes, take damage, and explore dead ends. As long as you explicitly create a "save point" before trying a dangerous boss fight, you can always reload that exact state if things go wrong. Git works the same way, but for your text files.

### Centralized vs. Distributed Version Control

Historically, version control systems like Subversion (SVN) or Team Foundation Server (TFS) were centralized. There was one master server that held the history. If you wanted to view the history or make a commit, you had to be connected to the internet to talk to that server. If the server went down, nobody could work.

Git is a **distributed** version control system. When you use Git, you do not just download the latest files; you download the entire history of the project. Your local laptop becomes a fully functioning repository. You can view history, compare versions, and make commits while completely offline on an airplane. You only need the internet when you want to synchronize your history with someone else's.

### The Three Trees of Git

Git manages your files by moving them through three distinct logical areas, often called "trees." Understanding this pipeline is the key to diagnosing almost any Git problem.

```text
+---------------------+       +---------------------+       +---------------------+
|                     |       |                     |       |                     |
|  Working Directory  | ----> |    Staging Area     | ----> |     Repository      |
|  (Your local files) |       | (The loading dock)  |       | (The saved history) |
|                     |       |                     |       |                     |
+---------------------+       +---------------------+       +---------------------+
           |                             |                             |
           |   1. Modify files           |                             |
           |---------------------------->|                             |
           |                             |   2. Group changes          |
           |                             |---------------------------->|
           |                             |                             |
           |                                                           |
           |<----------------------------------------------------------|
                               3. Restore old versions
```

1. **The Working Directory**: This is your current workspace on your computer. It contains the actual files you are editing, deleting, or creating. When you open a file in Vim or VS Code, you are modifying the Working Directory. Git sees these changes but has not saved them yet.
2. **The Staging Area (Index)**: This is a crucial intermediate step unique to Git. Think of it as a loading dock or a staging area for a photoshoot. Before you take the final snapshot, you choose exactly which modified files to place on the stage. You can stage some files while leaving others behind. This allows you to craft highly focused, logical commits even if you modified fifty files at once.
3. **The Repository (Commit History)**: This is the permanent database where Git stores your snapshots (called commits). Once files are committed here, they are safely recorded in history with an author name, a timestamp, and a descriptive message. A commit is mathematically sealed; it cannot be secretly altered without changing its unique identifier.

### Active Learning: Pause and Predict
> **Pause and predict**: You have just finished a long debugging session. You fixed a database connection bug in `db.py`, but while hunting for the bug, you also added temporary print statements to `auth.py` and `api.py` that you don't want to save permanently. How does Git's Three Trees architecture allow you to create a clean history in this scenario without losing your temporary debug code in the working directory?
>
> *Prediction check: The Three Trees architecture decouples your working files from what gets saved. You can use the Staging Area to selectively stage only `db.py` for the next commit. The temporary print statements in `auth.py` and `api.py` remain safely in your Working Directory for you to continue using or delete later, without ever polluting the permanent Repository history.*

## Section 2: Setting the Stage: Installation and Configuration

Git is a command-line tool at its core. While graphical interfaces exist, learning the terminal commands is mandatory for platform engineering, as you will often be using Git on remote servers without graphical capabilities. Most modern Linux distributions and macOS come with Git pre-installed, or it can be easily added via a standard package manager like `apt`, `yum`, or `brew`.

To verify your installation, open your terminal and check the version:

```bash
git --version
```

Expected output:
```text
git version 2.39.2
```

### Identity Configuration

Git records author and committer identity in each commit, and in normal day-to-day use you should configure `user.name` and `user.email` so your commits are attributed correctly. This is critical for accountability—if an infrastructure change brings down production, the team needs to know who to ask about the rationale behind the change.

You configure this using the `git config` command. The `--global` flag applies these settings to all repositories on your current computer by writing them to a hidden file in your home directory (`~/.gitconfig`).

```bash
# Set your name (use your real name, this appears in the history)
git config --global user.name "Alex Chen"

# Set your email address
git config --global user.email "alex.chen@example.com"
```

You can verify your configuration at any time by asking Git to list all its current settings:

```bash
git config --list
```

### Initializing a Repository: git init

To tell Git to start tracking a project, you must initialize a repository in the root directory of your project. Let us create a new directory for a hypothetical Kubernetes project and initialize Git within it.

```bash
# Create a new directory
mkdir k8s-webapp
cd k8s-webapp

# Tell Git to start tracking this directory
git init
```

Expected output:
```text
Initialized empty Git repository in /home/alex/k8s-webapp/.git/
```

What exactly did `git init` do? It did not magically scan your hard drive. It simply created a hidden directory named `.git` inside your `k8s-webapp` folder. This hidden `.git` directory is the actual "Repository" from our Three Trees model. It is where Git stores all the internal database objects, the compressed file contents, the commit history graph, and the local configuration for this specific project. 

If you delete the `.git` directory, you delete all version history for the project, though your current working files will remain untouched on the disk.

```bash
# List all files, including hidden ones
ls -la
```

Expected output:
```text
total 12
drwxr-xr-x 3 alex alex 4096 Oct 12 10:00 .
drwxr-xr-x 5 alex alex 4096 Oct 12 09:59 ..
drwxr-xr-x 7 alex alex 4096 Oct 12 10:00 .git
```

With your repository successfully initialized and your identity configured, you have laid the essential groundwork. Next, we will explore how to populate this repository by deliberately moving files through Git's lifecycle to create your first committed snapshots.

## Section 3: The Snapshot Lifecycle: Add, Commit, and Status

Now that we have an active repository, let us walk through the daily workflow of tracking files. The command you will use more than any other—hundreds of times a day—is `git status`. It acts as your compass, telling you exactly where your files are within the Three Trees.

### Step 1: Modifying the Working Directory

Let us create our first file, a basic Kubernetes namespace configuration.

```bash
cat << 'EOF' > namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: webapp-prod
EOF
```

Run `git status` to see what Git thinks about this newly created file:

```bash
git status
```

Output:
```text
On branch main

No commits yet

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	namespace.yaml

nothing added to commit but untracked files present (use "git add" to track)
```

Git recognizes that a file exists in the Working Directory, but it lists it as "Untracked." This means Git is not currently tracking this file. It is not monitoring it for changes, and it will not automatically back it up. Git only tracks what you explicitly tell it to track.

### Step 2: Moving to the Staging Area (git add)

To tell Git we want to include this file in our very first snapshot, we must move it to the Staging Area (the loading dock) using the `git add` command.

```bash
git add namespace.yaml
```

Run `git status` again to observe the state change:

```bash
git status
```

Output:
```text
On branch main

No commits yet

Changes to be committed:
  (use "git rm --cached <file>..." to unstage)
	new file:   namespace.yaml
```

The file has moved. It is now categorized under "Changes to be committed". It is sitting on the loading dock, waiting for the photographer to take the picture.

### Step 3: Taking the Snapshot (git commit)

To permanently save the staged changes into the Repository, we use `git commit`. Every commit requires a commit message explaining *why* the change was made. Writing good commit messages is a core professional skill. A good message explains the intent and context, not just what lines changed.

```bash
git commit -m "feat: add production namespace definition"
```

Output:
```text
[main (root-commit) a1b2c3d] feat: add production namespace definition
 1 file changed, 4 insertions(+)
 create mode 100644 namespace.yaml
```

Let us check `git status` one more time to see the final result of our workflow:

```bash
git status
```

Output:
```text
On branch main
nothing to commit, working tree clean
```

Your Working Directory is now described as "clean." This means every tracked file currently sitting in your Working Directory matches the latest snapshot stored in the `.git` database. There are no pending changes.

### War Story: The Accidental Secret Commit

A junior developer was testing an application locally that required an AWS access key. For convenience, they hardcoded the key directly into their `deployment.yaml` file just to see if the pods would start. It worked. Excited, they ran `git add .` (a command which indiscriminately stages every changed file in the entire directory) and then ran `git commit -m "fix deployment"`.

They then pushed the code to a public repository. Exposed cloud credentials in public repositories can be discovered quickly by automated scanners and abused to create expensive resources before a team notices.

**The Lesson**: Never blindly use `git add .` unless you are absolutely certain what you have changed. Always run `git status` and `git diff` before staging to ensure you are not accidentally committing passwords, API keys, private ssh keys, or temporary debugging files.

Now that you know how to safely construct snapshots, you will inevitably need to inspect past snapshots or review the exact modifications made to individual files over time. In the next section, we will delve into the commands that allow you to analyze your commit history and examine precise file differences.

## Section 4: Traveling Through Time: Log and Diff

Once you have made multiple commits, you need robust ways to view the history timeline and understand exactly what has changed between different points in time. 

Let us make another change to our project. We will update the namespace file to add a label, a common task in Kubernetes for organizational purposes.

```bash
cat << 'EOF' > namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: webapp-prod
  labels:
    environment: production
EOF
```

### Seeing What Changed: git diff

Before you ever stage or commit a file, you should always verify exactly what lines you modified. Memory is fallible; the diff is objective. The `git diff` command compares your current Working Directory against the last snapshot you took.

```bash
git diff
```

Output:
```text
diff --git a/namespace.yaml b/namespace.yaml
index e46b825..8394c41 100644
--- a/namespace.yaml
+++ b/namespace.yaml
@@ -2,3 +2,5 @@ apiVersion: v1
 kind: Namespace
 metadata:
   name: webapp-prod
+  labels:
+    environment: production
```

**How to decipher a diff output:**
- The `--- a/namespace.yaml` and `+++ b/namespace.yaml` headers show the two versions of the files being compared (old vs new).
- `@@ -2,3 +2,5 @@` is a chunk header. It provides context to the system about roughly where in the file the changes occurred.
- Lines starting with a space character are unchanged context lines. Git shows them to help you orient yourself.
- Lines starting with a `+` (usually highlighted in green) are entirely new additions.
- Lines starting with a `-` (usually highlighted in red) are deletions. If you changed a line, Git represents it as deleting the old line and adding the new line.

### Active Learning: Diff Reading
> **Pause and predict**: Imagine you ran `git diff` on a deployment file and saw the following output:
>
> ```text
> @@ -10,3 +10,3 @@
>  spec:
>    replicas: 3
> -  image: nginx:1.14
> +  image: nginx:1.24
> ```
>
> Before reading further, what exactly did the engineer do in this file? Be specific.
>
> *Prediction check: The engineer did not add a completely new structural element. They modified an existing line. They deleted the line specifying the Nginx container version 1.14 and replaced it with a line specifying version 1.24. This represents a container image version upgrade.*

Now that we have verified our changes are correct and contain no secrets, let us stage and commit our label addition:

```bash
git add namespace.yaml
git commit -m "chore: add environment label to namespace"
```

### Viewing History: git log

To see the timeline of your snapshots, use the `git log` command. This opens a pager (usually `less`) showing your history in reverse chronological order (newest first).

```bash
git log
```

Output:
```text
commit 9f8e7d6c5b4a39281716151413121110abcdef12 (HEAD -> main)
Author: Alex Chen <alex.chen@example.com>
Date:   Wed Oct 12 10:45:12 2023 -0400

    chore: add environment label to namespace

commit a1b2c3d4e5f60718293a4b5c6d7e8f9012345678
Author: Alex Chen <alex.chen@example.com>
Date:   Wed Oct 12 10:15:30 2023 -0400

    feat: add production namespace definition
```

Notice the 40-character hexadecimal strings shown above. In most repositories, this is the commit hash generated with SHA-1. It is a mathematically generated unique identifier for that specific snapshot and reflects the file contents, author, date, and parent commit. You can use this hash to inspect or restore that exact point in history. Newer repositories can also be configured to use SHA-256, but the examples in this module use the common SHA-1 format.

For a more compact view, which is especially useful when you are investigating a repository with thousands of commits over several years, use the `--oneline` flag:

```bash
git log --oneline
```

Output:
```text
9f8e7d6 chore: add environment label to namespace
a1b2c3d feat: add production namespace definition
```

You can also use `git log -p` to see the actual diffs introduced by every single commit in history, allowing you to see not just *that* a commit happened, but exactly *what lines* were altered by it.

Mastering the ability to navigate your local timeline provides immense confidence when experimenting with infrastructure code. However, modern engineering is a team effort; the next section will introduce how to safely share your local history with remote servers to collaborate seamlessly with others.

## Section 5: Collaborating with the World: Remotes, Push, and Pull

Up until this point, everything we have done exists entirely on your local laptop's hard drive. If your computer crashes, or if you drop a cup of coffee on it, your entire project history is permanently gone. Furthermore, nobody else on your team can see your work. 

To collaborate with others and back up your work, you must connect your local repository to a remote server, such as GitHub, GitLab, or Bitbucket.

### What is a Remote?

A "remote" is simply another Git repository hosted on a network or the internet. Because Git is decentralized, everyone has a full, standalone copy of the history. "Pushing" and "Pulling" are the explicit actions we take to synchronize our local timeline with the remote timeline. 

```text
+-----------------------+                    +-----------------------+
|                       |                    |                       |
|   Local Repository    |                    |   Remote Repository   |
|   (Your Laptop)       |                    |   (GitHub/GitLab)     |
|                       |                    |                       |
|  commit C (HEAD)      | ==== git push ===> |  commit C             |
|  commit B             |                    |  commit B             |
|  commit A             | <=== git pull ==== |  commit A             |
|                       |                    |                       |
+-----------------------+                    +-----------------------+
```

### Connecting to a Remote

When you create an empty repository on a platform like GitHub, the platform provides you with a connection URL (usually HTTPS or SSH). You tell your local Git installation to connect to this URL using the `git remote add` command. 

By industry convention, the primary, default remote server is almost always named `origin`.

```bash
# Example command (do not run unless you have a real repository URL prepared)
git remote add origin https://github.com/yourusername/k8s-webapp.git
```

If you join a company and want to download an existing project, you do not use `git init` and `git remote add`. Instead, you use `git clone <url>`. Cloning automatically initializes a local repository, adds the remote as `origin`, and downloads all the history and files in one step.

### Pushing Changes (git push)

To upload your locally created commits to the remote server, you "push" them. You must specify the remote name (usually `origin`) and the branch name you are pushing (often `main` or `master`).

```bash
# Push your main branch to the origin remote for the first time
git push -u origin main
```

The `-u` flag stands for "upstream." You only need to use it the very first time you push a new branch. It creates a persistent tracking link between your local `main` branch and the remote `main` branch. In the future, you can simply type `git push` without any arguments, and Git will know exactly where to send the data.

### Pulling Changes (git pull)

If a teammate makes changes, commits them locally, and pushes them to GitHub, your local repository will *not* update automatically. Git will never change your local files without your explicit permission. You must actively reach out to the server, download their new commits, and integrate them into your local history using `git pull`.

```bash
# Fetch changes from the remote and merge them into your local branch
git pull origin main
```

Under the hood, `git pull` is actually a macro that runs two distinct commands in sequence: `git fetch` (which safely downloads the new commits from the remote without modifying your working files) and `git merge` (which attempts to seamlessly combine the downloaded changes with your current working directory).

### Active Learning: Remote Synchronization
> **Pause and predict**: You spent the morning working offline and made two local commits. Meanwhile, your teammate pushed three commits to the same branch on the remote server. What will happen if you blindly run `git push origin main` when you reconnect to the internet?
> 
> *Prediction check: The push will be rejected by the remote server. Git will recognize that the remote branch has commits that your local branch lacks, preventing you from unintentionally overwriting your teammate's work. You must run `git pull` to fetch and integrate their changes into your local history before you can successfully push your combined timeline.*

## Section 6: Ignoring the Noise: .gitignore

In any real-world software or infrastructure project, there are numerous files that you **never** want to commit to version control. These include:
- Compiled binaries, executable files, or build artifacts (e.g., `.exe`, `.jar`, `/dist/` directories).
- Log files generated by your application during testing.
- Operating system hidden files (e.g., `.DS_Store` generated by macOS Finder).
- **Secrets, API keys, database passwords, and local environment variables** (e.g., `.env` files).

If you accidentally commit these, you bloat the repository size or, worse, cause a severe security breach. To tell Git to pretend these files do not exist entirely, you create a plain text file named `.gitignore` in the root folder of your project.

Let us create a `.gitignore` tailored for our cloud-native environment.

```bash
cat << 'EOF' > .gitignore
# Ignore operating system generated files
.DS_Store
Thumbs.db

# Ignore local secret and credential files
.env
secret-keys.yaml
kubeconfig-local

# Ignore terraform state files (if we add Infrastructure as Code later)
*.tfstate
*.tfstate.backup
.terraform/
EOF
```

Git reads this file top-to-bottom. Any untracked file that matches a pattern listed in the `.gitignore` will normally not show up in `git status` as untracked. This makes it much less likely that you will accidentally stage it with a wildcard command like `git add .`.

### Active Learning: Pattern Matching
> **Pause and predict**: Given the `.gitignore` file above, which of the following three newly created files would still show up as "Untracked" when you run `git status`? 1) `main.tfstate`, 2) `secret-keys.yaml`, 3) `secret-keys.txt`.
>
> *Prediction check: Only `secret-keys.txt` will show up as untracked. `main.tfstate` is ignored by the `*.tfstate` wildcard rule, and `secret-keys.yaml` is explicitly ignored by name. `secret-keys.txt` does not match any ignore pattern, so Git will continue to flag it as an untracked file.*

### Active Learning: The Late Ignore
> **Pause and predict**: You have a file named `database-creds.txt` that you created last week. You committed it to Git a few days ago. Today, you realize your mistake and add `database-creds.txt` to your `.gitignore` file. You modify the credentials file, and run `git status`. Will Git ignore the changes?
>
> *Prediction check: No, Git will not ignore the changes. The `.gitignore` file only prevents **untracked** files from being added to the database. Once a file is tracked (committed), Git will continue tracking it regardless of what the `.gitignore` says. You must explicitly remove it from tracking using `git rm --cached database-creds.txt` before the ignore rule takes effect.*

## Did You Know?

1. **Git was built in two weeks.** In 2005, the Linux kernel project lost its free BitKeeper arrangement, which pushed Linus Torvalds and the community to create Git quickly as a replacement.
2. **The name is a self-deprecating insult.** Torvalds, known for his abrasive humor, named the system ["Git" (British slang for a stubborn, unpleasant, or incompetent person)](https://en.wikipedia.org/wiki/Git). He famously joked at a conference, "I'm an egotistical bastard, and I name all my projects after myself. First Linux, now Git."
3. **Git does not track empty directories.** Git does not track empty directories on their own. If a team wants an otherwise empty directory to exist in the repository, it usually adds a small placeholder file inside it.
4. **Colossal collision resistance.** Historically, Git has identified objects with 40-character SHA-1 values. Accidental collisions are extremely unlikely in normal use, but SHA-1 is no longer considered strong enough for long-term cryptographic collision resistance, which is one reason newer Git work supports SHA-256.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| **Accidentally committing a password/secret** | Using the indiscriminate `git add .` command without reviewing `git status` first, accidentally dragging a `.env` file into the staging area. | If unpushed: `git reset HEAD~1` to undo the commit locally. If pushed, **the secret is compromised**. You must promptly revoke or rotate the credential in AWS/GCP. Do not just delete it in a new commit; the history is permanent. |
| **"fatal: refusing to merge unrelated histories"** | You initialized a repository locally, and initialized a separate repository on GitHub with a default README, then tried to pull. Git thinks they are two completely different, unrelated projects. | Run `git pull origin main --allow-unrelated-histories` to forcefully instruct Git to combine the two distinct timelines into one. |
| **"Updates were rejected because the remote contains work that you do not have locally"** | A teammate pushed new commits to the GitHub server while you were working offline. Git refuses to let you push and overwrite their work. | Run `git pull` first to download and integrate their changes into your local branch. Resolve any potential merge conflicts, then run `git push`. |
| **Empty or meaningless commit messages** | Rushing the job. Using vague messages like `git commit -m "update"` or `git commit -m "fixed stuff"`. | Use `git commit --amend -m "new better message"` if you haven't pushed yet. Develop a professional habit of writing "Why" not just "What". |
| **Forgetting to stage files before committing** | Running `git commit -m "message"` while your changes are still sitting in the Working Directory, entirely bypassing the Staging Area. | Run `git status` to see what is unstaged. Run `git add <file>` to move the changes to the stage, then retry the `git commit` command. |
| **Committing massive binary files** | Accidentally adding compiled artifacts, database memory dumps, or large videos to the repository. Git is designed for text tracking, not large binaries. | Remove the file from the tracking database with `git rm --cached <file>`, commit the removal, and immediately add the file type to your `.gitignore`. |

## Quiz

<details>
<summary>1. Your team just deployed a new Kubernetes configuration, and the cluster immediately crashed. You need to quickly see who made the last change and what their commit message was. Which command do you run?</summary>
You should run `git log` or `git log --oneline`. This command displays the commit history in reverse chronological order, showing the author, the timestamp, and the commit message for each snapshot. By analyzing this output, you can instantly identify who made the recent changes and read their explanation for why the change was necessary. This rapid historical visibility is exactly why version control is critical during a production incident.
</details>

<details>
<summary>2. You have modified a `service.yaml` file on your laptop to expose a new port. You type `git commit -m "expose port 8080"`, but Git returns a message saying "nothing added to commit but untracked files present". What did you forget to do?</summary>
You forgot to move the file from the Working Directory to the Staging Area using the `git add` command. Git's architecture requires you to explicitly select which files should be included in the next snapshot. Because you bypassed the Staging Area, Git saw your modified file but refused to automatically include it in the repository. You must run `git add service.yaml` before you attempt to commit again.
</details>

<details>
<summary>3. You are about to stage `configMap.yaml`, but you cannot remember if you set the database password to the testing password or left the production password in there. What command should you run to inspect the exact lines you changed before staging?</summary>
You should run `git diff` to view the exact line-by-line changes. This command compares your current Working Directory against the last saved snapshot in the repository. It will display the removed lines in red and the added lines in green, allowing you to objectively verify the contents of the file. Relying on this command prevents you from accidentally committing production secrets into the permanent history graph.
</details>

<details>
<summary>4. You just joined a new project. You clone the repository and discover Git does not know your `user.name` and `user.email`, so it tells you to run `git config` before committing. Why is this necessary, and how is that different from the authentication prompts you might see during `git push`?</summary>
Git requires an author identity when you create a commit, so `user.name` and `user.email` must be configured before `git commit` can record who authored the snapshot. That identity is stored in the commit metadata for accountability and traceability. By contrast, prompts during `git push` are usually remote authentication checks from the hosting service, such as an HTTPS credential helper, a personal access token, or SSH keys. In short: commit identity is local metadata for `git commit`; push-time authentication proves you are allowed to upload to the remote.
</details>

<details>
<summary>5. You created a file named `aws-credentials.json` on your local machine to test a script. You never want this file to be committed to the company repository. What exactly should you do to ensure it is ignored forever?</summary>
You must create a plain text file named `.gitignore` in the root of your repository if one does not already exist. Inside this file, you need to add the exact filename `aws-credentials.json` on a new line. Git reads this configuration file top-to-bottom and will automatically filter out any matching files from its tracking radar. This ensures the credentials file is much less likely to be accidentally staged or committed, helping prevent a severe security breach.
</details>

<details>
<summary>6. A junior developer is trying to "reset" a broken project to start over. They open their file explorer, delete the hidden `.git` folder, and then type `git status` in their terminal, expecting Git to realize the project was reset and show an empty history. What actually happens, and why?</summary>
When the developer types `git status`, the terminal will return a "fatal: not a git repository" error because they have completely destroyed the version control system for that folder. The hidden `.git` directory is not just a configuration file; it is the entire actual repository database containing all commits, branches, and historical snapshots. By deleting it, they did not reset the history—they permanently erased it locally, turning their project back into a normal, untracked folder on their operating system. The working files on their disk remain untouched, but Git no longer manages them.
</details>

<details>
<summary>7. You and a colleague are both modifying the same `nginx-deployment.yaml` file. They push a change that sets `replicas: 5` while you are offline. You locally change the same line to `replicas: 2` and attempt to push. Git rejects your push, so you run `git pull`. What happens next, and how do you resolve it?</summary>
Git will attempt to automatically merge the changes, but because you both modified the exact same line, it will pause and declare a merge conflict. It cannot safely guess whether the deployment should have 5 replicas or 2, so it leaves the decision to a human. To resolve the conflict, you must open the file in your editor and locate the conflict markers (which look like `<<<<<<< HEAD` and `>>>>>>>`). After manually editing the file to the desired state and removing the markers, you must use `git add` and `git commit` to finalize the merge before pushing.
</details>

## Hands-On Exercise

In this exercise, you will create a local repository from scratch, simulate a standard engineering workflow by making multiple logical commits, and observe the resulting history. We will use dummy Kubernetes configuration files to simulate a real infrastructure workflow.

### Task 1: Initialization
Create a new directory named `dojo-k8s-project` and navigate into it. Initialize an empty Git repository.
- [ ] Directory created and navigated into.
- [ ] Git repository initialized.

<details>
<summary>Solution: Task 1</summary>

```bash
mkdir dojo-k8s-project
cd dojo-k8s-project
git init
git status
```
</details>

### Task 2: The Initial Commit
Create a `README.md` file with the text "# KubeDojo Project". Stage the file and commit it with the message "docs: add initial readme".
- [ ] File created with correct content.
- [ ] File added to staging area.
- [ ] Commit successfully created.

<details>
<summary>Solution: Task 2</summary>

```bash
echo "# KubeDojo Project" > README.md
git status
git add README.md
git status
git commit -m "docs: add initial readme"
```
</details>

### Task 3: Simulating Infrastructure Development
Create a file named `deployment.yaml` and add the following dummy content:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
```
Stage and commit this file with the message "feat: add web deployment skeleton".
- [ ] File created.
- [ ] Commit successfully created with correct message.

<details>
<summary>Solution: Task 3</summary>

```bash
cat << 'EOF' > deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
EOF

git status
git add deployment.yaml
git commit -m "feat: add web deployment skeleton"
```
</details>

### Task 4: Modifying Existing Files
Open `deployment.yaml` and add `replicas: 3` under a `spec:` block, so it looks like this:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3
```
Use a command to view the exact differences before staging. Then, stage and commit the change with the message "fix: set deployment replicas to 3".
- [ ] File modified.
- [ ] Diff viewed successfully.
- [ ] Change staged and committed.

<details>
<summary>Solution: Task 4</summary>

```bash
# Modify the file using your preferred editor (nano, vim, or cat override)
cat << 'EOF' > deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3
EOF

# View the diff
git diff

# Stage and commit
git add deployment.yaml
git commit -m "fix: set deployment replicas to 3"
```
</details>

### Task 5: Reviewing the Timeline
Run a command to view your complete commit history in a compact, single-line format. Verify that all three of your commits are present in chronological order.
- [ ] History command executed.
- [ ] Three distinct commits visible in the output.

<details>
<summary>Solution: Task 5</summary>

```bash
git log --oneline
```
Output should look similar to:
```text
3b2a1c4 fix: set deployment replicas to 3
9f8e7d6 feat: add web deployment skeleton
1a2b3c4 docs: add initial readme
```
</details>

### Task 6: Bonus Challenge — Advanced Ignore Rules
You are working on a new application that generates numerous log files ending in `.log` across various directories. You want Git to ignore all of them to save space, but you must ensure that one specific file named `audit-trail.log` in the root directory is always tracked for compliance reasons.
Create a `.gitignore` file that achieves this exact configuration. Verify your solution by creating dummy files (e.g., `app.log`, `database.log`, and `audit-trail.log`) and checking `git status` to ensure only `audit-trail.log` is ready to be tracked.
- [ ] `.gitignore` file created with appropriate wildcard and exclusion rules.
- [ ] Dummy files created to test the rules.
- [ ] `git status` confirms only the required file is untracked.

<details>
<summary>Solution: Task 6</summary>

```bash
# Create the .gitignore file
cat << 'EOF' > .gitignore
*.log
!audit-trail.log
EOF

# Create dummy files
touch app.log
touch database.log
touch audit-trail.log

# Check status
git status
```
Git will show `.gitignore` and `audit-trail.log` as untracked files. The other `.log` files will be successfully ignored.
</details>

---

**Next Module**: [Module 0.7: What is Networking?](../module-0.7-what-is-networking/) — Now that you can track files, it is time to understand how computers actually talk to each other across the wires.

## Sources

- [Git](https://en.wikipedia.org/wiki/Git) — Overview of Git, including its history and naming background.
- [Git Guide](https://github.com/git-guides) — A concise beginner-friendly overview of Git concepts, commands, and workflow.
- [Git Guides: git pull](https://github.com/git-guides/git-pull) — Explains remote synchronization in the same beginner-friendly register as this module.
- [github/gitignore](https://github.com/github/gitignore) — Provides practical `.gitignore` examples learners can reuse immediately.
