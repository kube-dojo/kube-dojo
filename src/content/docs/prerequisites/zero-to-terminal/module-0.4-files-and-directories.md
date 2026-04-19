---
title: "Module 0.4: Files and Directories"
slug: prerequisites/zero-to-terminal/module-0.4-files-and-directories
sidebar:
  order: 5
lab:
  id: "prereq-0.4-files-directories"
  url: "https://killercoda.com/kubedojo/scenario/prereq-0.4-files-directories"
  duration: "20 min"
  difficulty: "beginner"
  environment: "ubuntu"
---
> **Complexity**: `[QUICK]` - Absolute beginner
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: [Module 0.2: What is a Terminal?](../module-0.2-what-is-a-terminal/) — You should be able to open a terminal and type commands.

---

## What You'll Be Able to Do

After this module, you will be able to:
- **Navigate** absolute and relative paths and explain the difference
- **Read** files using `cat`, `head`, and `tail` and choose the right tool for the job
- **Interpret** file permissions from `ls -l` output (who can read, write, execute)
- **Find** hidden dotfiles and explain why they exist

---

## Why This Module Matters

Everything on your computer — every photo, every song, every application, every setting — is stored as a **file**. And those files are organized into **directories** (also called folders).

When you use a GUI, you see colorful folder icons and file icons. You double-click to open them. But behind the scenes, your computer thinks about files and directories as a tree of text paths, like `/home/yourname/Documents/report.txt`.

In Kubernetes and cloud engineering, you'll constantly work with files: configuration files, scripts, logs, manifests. If you can't navigate files and directories from the terminal, you'll be lost. This module fixes that.

---

## What is a File?

A **file** is a container for information stored on your computer.

Think of it like a piece of paper with writing on it. The paper has:

- A **name** (so you can find it): `grocery-list.txt`
- **Contents** (the actual information): "eggs, milk, bread"
- A **location** (where it's stored): on your desk, in a drawer, in a filing cabinet

Files can contain anything:
- Text (like a note or a configuration)
- Code (instructions for the computer)
- Images (your photos)
- Music, videos, databases, and more

> In our restaurant kitchen analogy: a file is like a **recipe card**. It has a name ("Tomato Soup"), contents (the actual recipe), and it's stored somewhere (the recipe box, a shelf, a drawer).

### Everything is a File (Really!)

Here's something wild about Linux, the operating system used on most Kubernetes nodes:

**Almost everything is represented as a file.**

- Your actual files? Files.
- Your keyboard? The system sees it as a file ([`/dev/input/event0`](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/7/html/storage_administration_guide/ch-filesystem)).
- Your hard drive? A file (`/dev/sda`).
- Running programs? They have entries in [`/proc/`](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/4/html/reference_guide/ch-proc) that look like files.

You don't need to worry about device files right now. Just know that the concept of "files" in Linux goes much deeper than documents and photos. This design philosophy is one reason Linux is so powerful — everything can be read, written, and manipulated using the same set of tools.

---

## What is a Directory?

A **directory** is a container for files (and other directories). It's the same thing as a **folder** — literally the same concept, just a different name.

- GUI users say "folder" (because the icon looks like a paper folder).
- Terminal users say "directory" (the technical term).

> In the kitchen: a directory is like a **drawer** or a **shelf**. Your recipe cards (files) go into drawers (directories). Drawers can contain other drawers (subdirectories).

---

## The Directory Tree

Your computer organizes all files and directories into a **tree** structure. It starts from a single point at the top and branches downward.

```
/                          <-- The "root" — the very top, the ground floor
├── home/                  <-- Where user accounts live
│   └── yourname/          <-- YOUR home directory
│       ├── Documents/
│       ├── Downloads/
│       ├── Desktop/
│       └── projects/
├── etc/                   <-- System configuration files
├── var/                   <-- Variable data (logs, databases)
├── tmp/                   <-- Temporary files
└── usr/                   <-- User programs and utilities
```

### Key Locations

| Path | What It Is | Kitchen Analogy |
|------|-----------|-----------------|
| `/` | **Root directory** — the very top of the tree | The building itself — everything is inside it |
| `/home/yourname/` | **Your home directory** — your personal space | Your personal workstation in the kitchen |
| [`~`](https://www.redhat.com/en/blog/navigating-linux-filesystem) | **Shorthand for your home directory** | A nickname for your workstation |
| `/etc/` | System configuration files | The restaurant's policy manual and recipe standards |
| `/tmp/` | Temporary files that may be cleaned automatically depending on system policy | The prep table — used during cooking, sometimes cleaned up automatically |
| `/var/log/` | Log files (records of what happened) | The order history book |

> The `~` (tilde) character is a shortcut. Instead of typing `/home/yourname/`, you can just type `~`. Your terminal knows what you mean. It's like having a nickname — easier to use than the full thing.

> **Why This Matters in K8s**: As a Kubernetes engineer, you will constantly interact with specific files in these exact directories. You will configure your cluster access by editing [`~/.kube/config`](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_config). You will debug system components by reading manifests in [`/etc/kubernetes/manifests/`](https://kubernetes.io/docs/reference/setup-tools/kubeadm/implementation-details/). And when things break, you will hunt for clues in [`/var/log/pods/` or `/var/log/containers/`](https://kubernetes.io/docs/tutorials/cluster-management/kubelet-standalone/).

### On macOS

macOS is slightly different. Your home directory is at [`/Users/yourname/` instead of `/home/yourname/`](https://en.wikipedia.org/wiki/Home_directory). But `~` still works as the shortcut, so you rarely need to think about this.

---

## Navigating: Where Am I?

When you open a terminal, you're "standing" in a directory — usually your home directory. The terminal doesn't show you a visual map; you need to ask.

### `pwd` — Print Working Directory

"Where am I right now?"

```bash
$ pwd
/home/yourname
```

`pwd` stands for **Print Working Directory**. It shows you the full path to where you currently are.

> Kitchen analogy: "What room am I standing in?" — pwd answers that.

### `ls` — List Contents

"What's in this room?"

```bash
$ ls
Desktop    Documents    Downloads    Music    Pictures
```

`ls` stands for **list**. It shows you the files and directories in your current location.

You can add options to see more detail:

```bash
$ ls -l
```

The `-l` flag means "long format." Now you'll see something like:

```
drwxr-xr-x  2 yourname yourname 4096 Mar 23 10:00 Desktop
drwxr-xr-x  3 yourname yourname 4096 Mar 23 09:45 Documents
-rw-r--r--  1 yourname yourname  220 Mar 23 08:30 notes.txt
```

Don't panic — we'll decode this shortly.

### `cd` — Change Directory

"Move to a different room."

```bash
$ cd Documents
$ pwd
/home/yourname/Documents
```

`cd` stands for **change directory**. You tell it where to go, and it takes you there.

Some essential `cd` shortcuts:

| Command | Where It Takes You | Analogy |
|---------|-------------------|---------|
| `cd ~` or just `cd` | Your home directory | "Go back to my workstation" |
| `cd ..` | One level up (the parent directory) | "Go to the room that contains this room" |
| `cd -` | The last directory you were in | "Go back to where I just was" |
| `cd /` | The root directory | "Go to the ground floor" |

---

## Absolute vs. Relative Paths

This is an important concept. There are two ways to describe where a file or directory is:

### Absolute Path (Full Address)

An absolute path starts from the root (`/`) and gives the complete location:

```
/home/yourname/Documents/report.txt
```

It's like giving a full street address: **123 Main Street, Springfield, IL 62701, USA**. No matter where you are in the world, this address points to exactly one place.

### Relative Path (Directions from Here)

A relative path describes the location relative to where you currently are:

```
Documents/report.txt
```

It's like saying: **"Two blocks left, then one block up."** These directions only work if you know the starting point.

### Example

```bash
$ pwd
/home/yourname

# These two commands do the same thing:
$ cd /home/yourname/Documents       # Absolute path
$ cd Documents                       # Relative path (works because we're in /home/yourname)
```

### Special Path Symbols

| Symbol | Meaning | Example |
|--------|---------|---------|
| `/` | Root directory (at the start) or path separator | `/home/yourname` |
| `~` | Your home directory | `~/Documents` = `/home/yourname/Documents` |
| `.` | Current directory ("here") | `./script.sh` = "script.sh in this directory" |
| `..` | Parent directory ("up one level") | `../Downloads` = "go up, then into Downloads" |

---

## Reading Files

Now let's look inside files. You have several tools, each useful in different situations.

> **Think about it**: You need to check the last few lines of a log file that's 10,000 lines long. Would you use a command that shows the whole file, or one that shows just the end? Keep this in mind as you read about `cat`, `head`, and `tail` below — each exists because it solves a different problem.

### `cat` — Show the Whole File

```bash
$ cat notes.txt
This is my first note.
I wrote it in the terminal!
```

`cat` stands for "concatenate" (joining things together), but most people use it to display a file's contents. It dumps the entire file to your screen.

> Kitchen analogy: `cat` is like reading an entire recipe card out loud, start to finish.

**When to use**: Small files (under 50 lines).

### `head` — Show the First 10 Lines

```bash
$ head long-file.txt
```

This shows only the first 10 lines. You can change the number:

```bash
$ head -n 5 long-file.txt    # Show first 5 lines
```

> Kitchen analogy: "Just read me the title and ingredients — I don't need the full recipe."

### `tail` — Show the Last 10 Lines

```bash
$ tail log-file.txt
```

Shows the last 10 lines. Extremely useful for reading log files, where the newest entries are at the bottom.

```bash
$ tail -n 20 log-file.txt    # Show last 20 lines
```

> Kitchen analogy: "What were the last few orders that came in?"

---

## Creating Files and Directories

### `mkdir` — Make a Directory

```bash
$ mkdir recipes
```

This creates a new directory called `recipes` in your current location.

To create nested directories (a directory inside a directory inside a directory):

```bash
$ mkdir -p recipes/italian/pasta
```

The `-p` flag means "create parent directories as needed." Without it, you'd get an error if `recipes/` or `recipes/italian/` didn't already exist.

### `touch` — Create an Empty File

```bash
$ touch shopping-list.txt
```

This creates a new, empty file. (If the file already exists, it updates the file's timestamp without changing the contents.)

> Kitchen analogy: `mkdir` is building a new drawer. `touch` is placing a blank recipe card in it.

---

## Hidden Files (Dotfiles)

Some files and directories start with a dot (`.`). These are called **hidden files** or **dotfiles**.

```bash
$ ls
Documents    Downloads    Music

$ ls -a
.   ..   .bashrc   .config   Documents   Downloads   Music
```

The `-a` flag means "all" — including hidden files.

Hidden files usually contain configuration and settings. Some common ones:

| File | What It Does |
|------|-------------|
| `.bashrc` | Settings for your bash terminal |
| `.zshrc` | Settings for your zsh terminal (macOS default) |
| `.config/` | Directory containing app configurations |
| `.ssh/` | SSH keys (used for secure connections) |
| `.gitconfig` | Git settings |

> These files are hidden because you don't need to see them every day, and accidentally deleting them could mess up your settings. They're like the electrical wiring behind the kitchen walls — important but usually out of sight.

---

## File Permissions Basics

> **Pause and predict**: When you run `ls -l`, you see something like `-rw-r--r--` next to each file. What do you think those letters mean? The `r` might remind you of "read", `w` of "write"... and the dashes? Take a guess before reading on.

Remember when we ran `ls -l` and saw this?

```
drwxr-xr-x  2 yourname yourname 4096 Mar 23 10:00 Desktop
-rw-r--r--  1 yourname yourname  220 Mar 23 08:30 notes.txt
```

Let's decode the first column: `-rw-r--r--`

### The Permission String

```
-  rw-  r--  r--
|  |    |    |
|  |    |    └── Others (everyone else) permissions
|  |    └── Group permissions
|  └── Owner (you) permissions
└── File type (- = file, d = directory)
```

### The Three Permissions

| Letter | Permission | For Files | For Directories |
|--------|-----------|-----------|-----------------|
| `r` | Read | Can see the contents | Can list what's inside |
| `w` | Write | Can change the contents | Can add or remove files |
| `x` | Execute | Can run it as a program | [Can enter the directory (`cd` into it)](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/8/html/configuring_basic_system_settings/managing-file-system-permissions_configuring-basic-system-settings) |
| `-` | No permission | Cannot do that action | Cannot do that action |

### Reading the Example

```
-rw-r--r--  notes.txt
```

- `-` : This is a regular file (not a directory)
- `rw-` : Owner can **read** and **write** (but not execute)
- `r--` : Group can **read** only
- `r--` : Others can **read** only

```
drwxr-xr-x  Desktop
```

- `d` : This is a **directory**
- `rwx` : Owner can read, write, and enter
- `r-x` : Group can read and enter (but not add/remove files)
- `r-x` : Others can read and enter (but not add/remove files)

> Kitchen analogy: Permissions are like **who has which key**. The head chef (owner) has the key to everything. The sous-chefs (group) can open most drawers. The waitstaff (others) can only peek through the window.

> **Example**: A world-readable configuration file containing secrets can let anyone with local access read those credentials. Restrictive permissions such as `-rw-------` are a common way to reduce that risk.

Don't worry about changing permissions yet — just know how to read them. We'll cover `chmod` when you need it.

---

## Did You Know?

> 1. **The `/` root directory is called "root" because the directory tree grows downward.** Just like a real tree, the root is at the top and branches extend below. Every single file on your computer is somewhere on a branch that connects back up to `/`.
>
> 2. **The `~` shortcut expands to your home directory in the shell.** You do not need to memorize the full path such as `/home/yourname/` or `/Users/yourname/`. The exact historical reason `~` was chosen is often told as trivia, but the useful fact is simply that shells treat it as shorthand for your home directory.
>
> 3. **Linux treats everything as a file — including your keyboard.** When you press a key, the kernel writes that keypress to a file-like interface. Programs read from that interface to know what you typed. This "everything is a file" philosophy is why Linux can be controlled entirely from the terminal — there's always a file to read or write.

---

## Common Mistakes

| Mistake | What Happens | Fix | Real-World Impact |
|---------|-------------|-----|-------------------|
| `cd` into a file instead of a directory | `Not a directory` error | Use `cat` or `head` to read files; use `cd` for directories | Wastes time during a critical incident when you are trying to navigate to logs. |
| Forgetting a space between command and path | `cdDocuments: command not found` | Always put a space: `cd Documents` | Minor annoyance, but scripts with missing spaces will fail to execute in automated pipelines. |
| Using backslashes `\` instead of forward slashes `/` | Path not found | Linux/macOS uses forward slashes: `/home/you/Documents` | A script written on Windows might break completely when deployed to a Linux Kubernetes node. |
| Creating a file when you meant a directory | You get a file named "recipes" instead of a folder | Use `mkdir` for directories, `touch` for files | Applications expecting a directory to write logs into will crash if a file exists there instead. |
| Getting lost in nested directories | No idea where you are | Run `pwd` to see your location, or `cd ~` to go home | You might accidentally delete or overwrite files in the wrong environment (e.g., prod instead of dev). |
| Typo in a path name | `No such file or directory` | Use `ls` first to see what's there, then type carefully (or use Tab completion!) | Automated backup scripts will silently fail to back up data if the target path is misspelled. |

> **Pro tip: Tab completion.** Start typing a file or directory name and press **Tab**. The terminal will auto-complete it for you. If there are multiple matches, press **Tab** twice to see all options. This saves typing and avoids typos.

---

## Quiz

**Question 1**: You are reading documentation that tells you to copy a license key into `~/.kube/config`. However, your current working directory is `/var/log/pods/`. Where exactly does the `~` symbol direct the system to look for this file, and why is this shortcut used instead of the full path?

<details>
<summary>Show Answer</summary>

The system will look in your user's home directory (e.g., `/home/yourname/.kube/config` on Linux or `/Users/yourname/.kube/config` on macOS). The `~` acts as a dynamic shortcut that always resolves to the current user's home directory. This is incredibly useful in documentation and scripts because it works flawlessly regardless of what your specific username is or which operating system you are using. By using `~`, developers can write a single command that works across everyone's personal machine without needing to be customized.

</details>

**Question 2**: You just downloaded a tool that includes a `.env` file containing secret API keys. When you type `ls` in the directory, the file doesn't show up. Why does this happen, and what command must you run to verify the file is actually there?

<details>
<summary>Show Answer</summary>

You must run `ls -a` (or `ls --all`) to see it. The file doesn't show up with a standard `ls` command because its name starts with a dot (`.`), making it a hidden file. Operating systems hide dotfiles by default to keep directories visually clean, as these files typically contain configuration or environmental data that you don't need to interact with during normal, day-to-day file browsing. The `-a` flag specifically overrides this default behavior to reveal everything present in the directory.

</details>

**Question 3**: A junior developer is frustrated that they can't easily find their `.bashrc` terminal configuration file in their home folder using the GUI file explorer. Why are configuration files like `.bashrc` hidden by default, and what could go wrong if they were fully visible alongside regular documents?

<details>
<summary>Show Answer</summary>

Configuration files are hidden by default to protect them from accidental modification or deletion. If files like `.bashrc` were visible alongside everyday documents, a user might mistakenly delete them while cleaning up old files, or accidentally alter them when trying to open a regular text document. Deleting or breaking these files can instantly corrupt your terminal environment, break application settings, or lock you out of certain tools. Hiding them ensures that only users who specifically intend to modify configurations will interact with them.

</details>

**Question 4**: You are currently troubleshooting an application and your terminal is in `/home/user/projects/app/src`. You realize you need to read the instructions located in `/home/user/projects/app/README.md`. Write the command to read this file using a relative path, and explain why a relative path might be preferred here.

<details>
<summary>Show Answer</summary>

The command is `cat ../README.md` (or `head ../README.md`). The `..` tells the system to move one level up into the `app` directory, and then look for the `README.md` file. A relative path is preferred here because it's much faster to type than the full absolute path (`/home/user/projects/app/README.md`). During an active troubleshooting session, navigating with relative paths saves time, reduces the chance of typos, and makes it easier to move around within a localized project structure.

</details>

**Question 5**: A deployment script is failing. Inside the script, it tries to access a configuration file by calling `cd config/`. However, the script only works when run from a specific folder, and breaks when run from anywhere else. What is the fundamental difference between using `config/` versus `/etc/app/config/`, and why did the script break?

<details>
<summary>Show Answer</summary>

The script broke because it used a relative path (`config/`), which depends entirely on your current working directory when the script is executed. If you aren't in the parent directory of `config/`, the system won't find it and the script will fail. In contrast, `/etc/app/config/` is an absolute path. Absolute paths start from the root directory (`/`) and provide the exact, unambiguous location of the target, guaranteeing the script will find the folder regardless of where it is executed from.

</details>

**Question 6**: You are investigating a security alert. A sensitive file containing customer emails has the permission string `-rw-r-----`. The file is owned by the user `admin` and belongs to the group `support`. If a new user joins the `support` group, what exact actions can they perform on this file, and what prevents them from modifying it?

<details>
<summary>Show Answer</summary>

A user in the `support` group can only **read** the file's contents, because the group permission segment is `r--`. They cannot modify or delete the contents because the write (`w`) permission is missing for the group. Only the file owner (`admin`) has both read and write permissions (`rw-`). This separation ensures that support staff can view the necessary information to assist customers without accidentally altering or corrupting the sensitive data.

</details>

**Question 7**: A production Kubernetes node is crashing, and the system log file `/var/log/syslog` has grown to over 500,000 lines. You need to quickly identify the error that occurred right before the crash. Which command should you use to view the file, and why would running `cat /var/log/syslog` be a disastrous choice in this scenario?

<details>
<summary>Show Answer</summary>

You should use `tail -n 50 /var/log/syslog` (or similar) to view just the end of the file. Using `cat` would be a disastrous choice because it would attempt to print all 500,000 lines to your terminal at once. This would flood your screen, freeze your terminal session, and make it completely impossible to locate the critical error messages hidden at the very bottom of the file where the most recent events are recorded. The `tail` command exists precisely for this use case, allowing you to efficiently check the most recent system logs.

</details>

---

## Hands-On Exercise: Building Your First Directory Structure

### Objective

Create a directory structure, add files, read them, and check permissions — all from the terminal.

### Steps

1. **Go to your home directory:**

```bash
$ cd ~
$ pwd
```

Confirm you see your home directory path.

2. **Create a project directory structure:**

```bash
$ mkdir -p kubedojo-practice/recipes/appetizers
$ mkdir -p kubedojo-practice/recipes/main-courses
$ mkdir -p kubedojo-practice/recipes/desserts
```

3. **Navigate into it:**

```bash
$ cd kubedojo-practice
$ ls
```

You should see: `recipes`

4. **Create some files:**

```bash
$ touch recipes/appetizers/bruschetta.txt
$ touch recipes/main-courses/pasta-carbonara.txt
$ touch recipes/desserts/tiramisu.txt
```

5. **Add content to a file** (we'll use `echo` with `>` to write to a file):

```bash
$ echo "Ingredients: bread, tomatoes, basil, olive oil" > recipes/appetizers/bruschetta.txt
$ echo "Ingredients: pasta, eggs, pancetta, parmesan" > recipes/main-courses/pasta-carbonara.txt
$ echo "Ingredients: coffee, mascarpone, ladyfingers, cocoa" > recipes/desserts/tiramisu.txt
```

> The `>` symbol means "send the output into this file" instead of displaying it on screen. Think of it as redirecting the chef's response from being spoken aloud to being written on a recipe card.

6. **Read the files:**

```bash
$ cat recipes/appetizers/bruschetta.txt
$ head recipes/main-courses/pasta-carbonara.txt
$ tail recipes/desserts/tiramisu.txt
```

7. **Check permissions:**

> **Stop and think**: Before you run the next command, what permission string do you expect to see on the `bruschetta.txt` file? (Hint: You created it, so you are the owner. Can you read and write to it?)

```bash
$ ls -l recipes/appetizers/
```

You should see the permission string for your bruschetta file.

8. **Check for hidden files in your home directory:**

> **Pause and predict**: If you ran just `ls ~` without the `-a` flag, would you see files like `.bashrc` or `.config`? Why or why not?

```bash
$ ls -a ~
```

Look for files starting with `.` — those are your dotfiles!

9. **Navigate around:**

```bash
$ cd recipes/desserts
$ pwd                          # Where are you?
$ cd ..                        # Go up one level
$ pwd                          # Now where?
$ cd ~                         # Go home
$ pwd                          # Back home
```

### Success Criteria

You've completed this exercise when you can:

- [ ] Navigate to your home directory with `cd ~`
- [ ] Create nested directories with `mkdir -p`
- [ ] Create files with `touch`
- [ ] Write content to files with `echo "text" > file`
- [ ] Read files with `cat`, `head`, and `tail`
- [ ] Check file permissions with `ls -l`
- [ ] View hidden files with `ls -a`
- [ ] Navigate with `cd`, `cd ..`, and `cd ~`

---

> You just used a tool that senior engineers use every day. You belong here.

---

## What's Next?

You can now navigate the filesystem, create files and directories, read files, and understand permissions. The kitchen is starting to feel familiar.

**Next Module**: [Module 0.5: Editing Files](../module-0.5-editing-files/) — Learn how to actually put content inside files using a text editor that runs right in your terminal.

## Sources

- [RHEL Storage Administration Guide: File systems](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/7/html/storage_administration_guide/ch-filesystem) — Background on Linux filesystem concepts, including device-related entries under `/dev`.
- [The /proc Virtual Filesystem](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/4/html/reference_guide/ch-proc) — Describes how Linux exposes process and kernel state through `/proc`.
- [A beginner's guide to navigating the Linux filesystem](https://www.redhat.com/en/blog/navigating-linux-filesystem) — Reinforces the path concepts used in this module, including `/`, `.`, `..`, and `~`.
- [kubectl config reference](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_config) — Documents kubectl configuration behavior and the default kubeconfig location when overrides are not set.
- [kubeadm implementation details](https://kubernetes.io/docs/reference/setup-tools/kubeadm/implementation-details/) — Explains where kubeadm places static Pod manifests for control-plane components.
- [Running Kubernetes node components standalone](https://kubernetes.io/docs/tutorials/cluster-management/kubelet-standalone/) — Shows node-level filesystem paths used for pod and container logs.
- [Home directory](https://en.wikipedia.org/wiki/Home_directory) — Summarizes conventional home-directory locations across operating systems, including macOS.
- [Managing file system permissions](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/8/html/configuring_basic_system_settings/managing-file-system-permissions_configuring-basic-system-settings) — Explains permission strings, ownership bits, and directory execute behavior.
- [Logging Architecture](https://kubernetes.io/docs/concepts/cluster-administration/logging/) — Connects filesystem navigation skills to real Kubernetes troubleshooting on cluster nodes.
- [Least Privilege Principle](https://owasp.org/www-community/controls/Least_Privilege_Principle) — Further reading on why sensitive files should be readable only by the minimum required users.
