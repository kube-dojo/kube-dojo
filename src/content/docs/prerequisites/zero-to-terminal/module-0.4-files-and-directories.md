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

Here's something wild about Linux (the operating system that Kubernetes runs on):

**Almost everything is represented as a file.**

- Your actual files? Files.
- Your keyboard? The system sees it as a file (`/dev/input/event0`).
- Your hard drive? A file (`/dev/sda`).
- Running programs? They have entries in `/proc/` that look like files.

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
| `~` | **Shorthand for your home directory** | A nickname for your workstation |
| `/etc/` | System configuration files | The restaurant's policy manual and recipe standards |
| `/tmp/` | Temporary files (deleted on reboot) | The prep table — used during cooking, cleaned up after |
| `/var/log/` | Log files (records of what happened) | The order history book |

> The `~` (tilde) character is a shortcut. Instead of typing `/home/yourname/`, you can just type `~`. Your terminal knows what you mean. It's like having a nickname — easier to use than the full thing.

### On macOS

macOS is slightly different. Your home directory is at `/Users/yourname/` instead of `/home/yourname/`. But `~` still works as the shortcut, so you rarely need to think about this.

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

Now let's look inside files. You have several tools, each useful in different situations:

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
| `x` | Execute | Can run it as a program | Can enter the directory (`cd` into it) |
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

Don't worry about changing permissions yet — just know how to read them. We'll cover `chmod` when you need it.

---

## Did You Know?

> 1. **The `/` root directory is called "root" because the directory tree grows downward.** Just like a real tree, the root is at the top and branches extend below. Every single file on your computer is somewhere on a branch that connects back up to `/`.
>
> 2. **The `~` shortcut was chosen because of keyboard layout.** On the ADM-3A terminal (made in the 1970s, one of the first video terminals), the Home key was on the same key as the `~` symbol. So `~` became the shorthand for the home directory, and it stuck for over 50 years.
>
> 3. **Linux treats everything as a file — including your keyboard.** When you press a key, the kernel writes that keypress to a file-like interface. Programs read from that interface to know what you typed. This "everything is a file" philosophy is why Linux can be controlled entirely from the terminal — there's always a file to read or write.

---

## Common Mistakes

| Mistake | What Happens | Fix |
|---------|-------------|-----|
| `cd` into a file instead of a directory | `Not a directory` error | Use `cat` or `head` to read files; use `cd` for directories |
| Forgetting a space between command and path | `cdDocuments: command not found` | Always put a space: `cd Documents` |
| Using backslashes `\` instead of forward slashes `/` | Path not found | Linux/macOS uses forward slashes: `/home/you/Documents` |
| Creating a file when you meant a directory | You get a file named "recipes" instead of a folder | Use `mkdir` for directories, `touch` for files |
| Getting lost in nested directories | No idea where you are | Run `pwd` to see your location, or `cd ~` to go home |
| Typo in a path name | `No such file or directory` | Use `ls` first to see what's there, then type carefully (or use Tab completion — press **Tab** to auto-complete names!) |

> **Pro tip: Tab completion.** Start typing a file or directory name and press **Tab**. The terminal will auto-complete it for you. If there are multiple matches, press **Tab** twice to see all options. This saves typing and avoids typos.

---

## Quiz

**Question 1**: What command shows your current location in the directory tree?

<details>
<summary>Show Answer</summary>

```bash
$ pwd
```

It stands for **Print Working Directory** and shows the full path to where you are.

</details>

**Question 2**: What does `~` represent?

<details>
<summary>Show Answer</summary>

Your **home directory**. It's a shortcut so you don't have to type the full path (like `/home/yourname/`).

</details>

**Question 3**: What's the difference between `ls` and `ls -a`?

<details>
<summary>Show Answer</summary>

`ls` shows only visible files and directories. `ls -a` shows **all** files, including hidden files (dotfiles) that start with a `.` character.

</details>

**Question 4**: If you see `-rw-r-----` on a file, who can read it?

<details>
<summary>Show Answer</summary>

- **Owner** can read and write (`rw-`).
- **Group** can read only (`r--`).
- **Others** have no permissions (`---`).

So the owner and members of the file's group can read it. Everyone else is blocked.

</details>

**Question 5**: What is the difference between `/home/yourname/Documents` and `Documents`?

<details>
<summary>Show Answer</summary>

`/home/yourname/Documents` is an **absolute path** — it works from anywhere because it starts from root (`/`).

`Documents` is a **relative path** — it only works if you're currently in `/home/yourname/`.

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

```bash
$ ls -l recipes/appetizers/
```

You should see the permission string for your bruschetta file.

8. **Check for hidden files in your home directory:**

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

> 💡 You just used a tool that senior engineers use every day. You belong here.

---

## What's Next?

You can now navigate the filesystem, create files and directories, read files, and understand permissions. The kitchen is starting to feel familiar.

**Next Module**: [Module 0.5: Editing Files](../module-0.5-editing-files/) — Learn how to actually put content inside files using a text editor that runs right in your terminal.
