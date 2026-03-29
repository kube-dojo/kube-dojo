---
title: "Module 0.8: Software and Packages"
slug: prerequisites/zero-to-terminal/module-0.8-software-and-packages
sidebar:
  order: 9
---
> **Complexity**: `[QUICK]` - Absolute beginner
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: [Module 0.6: What is Networking?](module-0.6-what-is-networking/) — You should be comfortable with the terminal, files, and basic networking concepts.

---

## Why This Module Matters

To work with Kubernetes, Docker, and cloud tools, you'll need to **install software** on your computer — not by downloading installers from websites and clicking "Next, Next, Finish," but by typing a single command in the terminal.

This module teaches you how software works, what package managers are, and how to install your first tools from the command line. These are skills you'll use literally every day in engineering.

---

## What is Software?

Let's start from the very beginning.

**Software** is a set of instructions that tells a computer what to do. When you open a web browser, play a video, or run a command in the terminal — software is making it happen.

Software is written by humans in **programming languages** — languages like Python, Go, Java, or JavaScript that are designed to be readable by both humans and computers (sort of).

Here's a tiny example in Python:

```python
print("Hello, World!")
```

That's software. One line that tells the computer: "Display the text Hello, World! on the screen."

> Kitchen analogy: Software is a **recipe**. It's the instructions for making a dish. The computer is the chef that follows the recipe exactly as written. Programming languages are the language the recipe is written in (English, French, etc.).

---

## From Source Code to Running Program

There's a journey every piece of software takes from "words typed by a human" to "something your computer can run":

### Step 1: Source Code

This is what programmers write. It looks like text:

```go
package main

import "fmt"

func main() {
    fmt.Println("Hello from Go!")
}
```

You can read it (more or less). Your computer cannot run it directly.

### Step 2: Compilation (For Some Languages)

Some languages need to be **compiled** — translated from human-readable code into **machine code** (binary — the 1s and 0s your computer's processor understands).

```
Source Code  →  Compiler  →  Binary (executable)
(recipe)        (translator)  (the finished dish, ready to serve)
```

The result is called a **binary** or **executable** — a file your computer can actually run.

> Kitchen analogy: Source code is the recipe on paper. Compilation is the cooking process. The binary is the finished dish, plated and ready to eat.

### Step 3: Execution

You **run** (execute) the binary, and the computer follows the instructions.

```bash
$ ./my-program
Hello from Go!
```

> Not all languages need compilation. Python, for example, is **interpreted** — it reads and runs the code line by line, like a chef reading the recipe one step at a time while cooking. Languages like Go, C, and Rust are compiled first, then run — like a chef prep-cooking everything beforehand.

---

## What is a Package?

Installing software from source code is complicated. You'd need to:

1. Download the source code
2. Install the right compiler
3. Compile it
4. Move the binary to the right place
5. Hope nothing went wrong

A **package** wraps all of that up into a neat bundle. It's the source code, already compiled (usually), bundled with instructions for where to install it and what else it needs.

> Kitchen analogy: A package is a **meal kit** (like Blue Apron or HelloFresh). Instead of going to the grocery store, finding every ingredient, and figuring out quantities, someone has bundled everything together for you. Just open the box and follow the simple instructions.

---

## What is a Package Manager?

A **package manager** is a tool that downloads, installs, updates, and removes packages for you. It's like an **app store** for your terminal.

Instead of visiting a website, downloading a file, and clicking through an installer, you type one command:

```bash
$ sudo apt install htop       # On Ubuntu/Debian Linux
$ brew install htop            # On macOS
```

And the package manager:
1. Finds the package in its catalog
2. Downloads it
3. Installs it
4. Sets it up so you can use it

### Common Package Managers

| Package Manager | Operating System | Install Command |
|----------------|-----------------|-----------------|
| **apt** | Ubuntu, Debian (Linux) | `sudo apt install package-name` |
| **dnf** / **yum** | Fedora, RHEL, CentOS (Linux) | `sudo dnf install package-name` |
| **brew** (Homebrew) | macOS (and Linux) | `brew install package-name` |
| **pacman** | Arch Linux | `sudo pacman -S package-name` |
| **choco** | Windows | `choco install package-name` |

> In this curriculum, we'll mostly use **apt** (for Linux) and **brew** (for macOS) since those are the most common in the Kubernetes world.

---

## What is `sudo`?

You'll notice some commands start with `sudo`. This is important.

**`sudo`** stands for **"superuser do"** — it runs a command with **administrator privileges**.

Your computer has a safety system: regular users can't install software system-wide, change system files, or do anything that might break the computer. This is on purpose. It prevents accidents and keeps your system secure.

But installing software requires writing files to system directories that regular users can't touch. So you use `sudo` to temporarily become the **superuser** (also called **root** — the all-powerful administrator account).

```bash
$ apt install htop              # ❌ Permission denied
$ sudo apt install htop         # ✅ Works! (asks for your password)
```

When you type `sudo`, you'll be asked for your password. This is your user password — the same one you use to log in. When you type it, you won't see any characters appear on screen (no dots, no stars, nothing). This is normal and intentional — it prevents someone looking over your shoulder from counting characters. Just type your password and press Enter.

> Kitchen analogy: `sudo` is like the **manager's key**. Most staff can work in the kitchen, but to access the supply room or change the thermostat, you need the manager's key. `sudo` gives you that key temporarily.

### On macOS with Homebrew

Homebrew (`brew`) is designed so that you usually **don't need `sudo`**. It installs packages into your user space, not system directories. This is one reason Homebrew is popular — less fiddling with permissions.

```bash
$ brew install htop             # ✅ Works without sudo on macOS
```

---

## Dependencies: Software That Needs Other Software

Software rarely works alone. Most programs need other programs or libraries to function. These are called **dependencies**.

For example:
- A web application might depend on a database
- A command-line tool might depend on a specific library
- A Python program depends on Python being installed

> Kitchen analogy: Dependencies are like **ingredients for ingredients**. To make the special sauce, you need mayonnaise. But to make mayonnaise, you need eggs and oil. The eggs and oil are dependencies of the mayonnaise, which is itself a dependency of the special sauce.

### Why Dependencies Matter

**The good news**: Package managers handle dependencies automatically. When you install a package, the package manager also installs everything that package needs.

```bash
$ sudo apt install some-program
Reading package lists... Done
The following additional packages will be installed:
  dependency-1 dependency-2 dependency-3
```

The package manager figures out the whole chain of dependencies and installs them all. You don't need to track them down yourself.

**The less-good news**: Sometimes dependencies conflict with each other. Program A needs version 1.0 of a library, but Program B needs version 2.0. This is called **dependency hell**, and it's one of the problems that containers (which you'll learn about soon) were invented to solve.

---

## Installing Your First Packages

Let's install some useful tools. Follow the instructions for your operating system.

### Updating the Package List

Before installing anything, update your package manager's catalog. Think of it as refreshing the list of what's available:

**Ubuntu/Debian Linux:**

```bash
$ sudo apt update
```

This doesn't install or change anything — it just downloads the latest list of available packages and their versions.

**macOS:**

First, if you don't have Homebrew installed yet, install it now:

```bash
# First, install Homebrew (macOS only — skip if you already have it)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

> This may take a few minutes. It will ask for your password (the one you use to log into your Mac).

Once Homebrew is installed, update it:

```bash
$ brew update
```

### Installing `htop` — A System Monitor

`htop` is a visual tool that shows you what programs are running on your computer, how much CPU and memory they're using, and more.

**Ubuntu/Debian Linux:**

```bash
$ sudo apt install htop
```

**macOS:**

```bash
$ brew install htop
```

Now run it:

```bash
$ htop
```

You'll see a colorful display showing CPU usage, memory usage, and running processes (programs). This is like looking at the kitchen's order board — you can see everything that's happening at once.

**Press `q` to quit htop.**

### Installing `tree` — A Directory Visualizer

Remember how we created directories in Module 0.4? `tree` shows directory structures in a beautiful visual format.

**Ubuntu/Debian Linux:**

```bash
$ sudo apt install tree
```

**macOS:**

```bash
$ brew install tree
```

Now try it:

```bash
$ tree ~/kubedojo-practice
```

You should see something like:

```
/home/yourname/kubedojo-practice
└── recipes
    ├── appetizers
    │   └── bruschetta.txt
    ├── desserts
    │   └── tiramisu.txt
    └── main-courses
        └── pasta-carbonara.txt
```

(If you completed the exercise in Module 0.4. If not, `tree` still works — just try it on any directory.)

---

## Updating and Removing Software

### Updating All Installed Packages

Over time, the software on your computer gets updates — bug fixes, security patches, new features. You should update regularly.

**Ubuntu/Debian Linux:**

```bash
$ sudo apt update              # Refresh the package list
$ sudo apt upgrade             # Install available updates
```

You can combine them:

```bash
$ sudo apt update && sudo apt upgrade
```

The `&&` means "run the second command only if the first one succeeds." Think of it as: "Refresh the list AND THEN install updates."

**macOS:**

```bash
$ brew update && brew upgrade
```

### Removing Software

**Ubuntu/Debian Linux:**

```bash
$ sudo apt remove package-name
```

**macOS:**

```bash
$ brew uninstall package-name
```

### Searching for Packages

Not sure what a package is called?

**Ubuntu/Debian Linux:**

```bash
$ apt search keyword
```

**macOS:**

```bash
$ brew search keyword
```

---

## Did You Know?

> 1. **Homebrew (the macOS package manager) was created in 2009 by a developer who was frustrated that macOS didn't have a proper package manager.** Max Howell built it as an open-source project. Today, it has over 6,000 packages and is used by millions of developers. The name is a beer-brewing metaphor: packages are called "formulae," the install location is called the "Cellar," and the whole system "brews" your software.
>
> 2. **The `apt` package manager on Ubuntu has access to over 60,000 packages.** That's 60,000 programs you can install with a single command. From text editors to databases to games to scientific computing tools — it's one of the largest software catalogs in the world, and it's all free.
>
> 3. **The concept of `sudo` came from a real security need.** In 1980, programmers at SUNY Buffalo needed a way to let trusted users run specific commands as root without sharing the root password. They created `sudo` — originally standing for "superuser do." The system logs every `sudo` command, so administrators can audit who did what. Today, `sudo` is used on virtually every Linux and macOS system.

---

## Common Mistakes

| Mistake | What Happens | Fix |
|---------|-------------|-----|
| Forgetting `sudo` on Linux | `Permission denied` or `Operation not permitted` | Add `sudo` before the command: `sudo apt install ...` |
| Using `sudo` with `brew` on macOS | Homebrew warns you or things install wrong | Don't use `sudo` with `brew` — it doesn't need it |
| Not running `apt update` first | Might install an old version or not find the package | Always run `sudo apt update` before installing on Linux |
| Typo in package name | `Unable to locate package htoop` | Check the spelling or use `apt search` / `brew search` to find the right name |
| Not reading the output | Missing important warnings or errors | Read what the terminal tells you! It often explains exactly what went wrong |
| Pressing Enter during password prompt without typing anything | Authentication failure | Type your password (you won't see characters) and then press Enter |

---

## Quiz

**Question 1**: What is a package manager?

<details>
<summary>Show Answer</summary>

A tool that automatically downloads, installs, updates, and removes software packages. It's like an app store for the terminal. Examples: `apt` (Ubuntu/Debian), `brew` (macOS), `dnf` (Fedora).

</details>

**Question 2**: What does `sudo` stand for and why do you need it?

<details>
<summary>Show Answer</summary>

`sudo` stands for **"superuser do."** You need it because installing software system-wide requires administrator (root) privileges. Regular users can't write to system directories for security reasons. `sudo` temporarily elevates your permissions.

</details>

**Question 3**: What is a dependency?

<details>
<summary>Show Answer</summary>

A dependency is a piece of software that another piece of software needs to work. For example, if Program A requires Library B, then Library B is a dependency of Program A. Package managers handle dependencies automatically.

</details>

**Question 4**: What's the difference between `apt update` and `apt upgrade`?

<details>
<summary>Show Answer</summary>

- `apt update` refreshes the list of available packages and their versions (downloads the latest catalog). It doesn't install or change anything.
- `apt upgrade` actually installs the available updates for your installed packages.

You need to run `update` before `upgrade` so the system knows what updates are available.

</details>

**Question 5**: Why don't you see characters when typing your password after `sudo`?

<details>
<summary>Show Answer</summary>

It's a security feature. By showing no characters (not even dots or asterisks), it prevents anyone watching your screen from seeing how long your password is. Just type your password and press Enter — it's being received even though nothing appears.

</details>

---

## Hands-On Exercise: Your First Software Installations

### Objective

Use your package manager to install, run, and explore new software from the terminal.

### Steps

1. **Update your package manager:**

On Ubuntu/Debian Linux:
```bash
$ sudo apt update
```

On macOS:
```bash
$ brew update
```

2. **Install htop:**

On Ubuntu/Debian Linux:
```bash
$ sudo apt install htop -y
```

On macOS:
```bash
$ brew install htop
```

The `-y` flag (on apt) means "yes to all prompts" — it automatically confirms the installation without asking "Are you sure? [Y/n]".

3. **Run htop and explore:**

```bash
$ htop
```

Observe:
- The CPU usage bars at the top
- The memory usage bar
- The list of running processes
- Each process has a PID (Process ID — a unique number)

Press `q` to quit.

4. **Install tree:**

On Ubuntu/Debian Linux:
```bash
$ sudo apt install tree -y
```

On macOS:
```bash
$ brew install tree
```

5. **Use tree to visualize a directory:**

```bash
$ tree ~/kubedojo-practice
```

If you don't have `kubedojo-practice`, try:

```bash
$ tree ~ -L 1
```

The `-L 1` flag means "only show 1 level deep" — useful for large directories.

6. **Check what's installed:**

On Ubuntu/Debian Linux:
```bash
$ apt list --installed | head -20
```

On macOS:
```bash
$ brew list
```

7. **Search for a package:**

On Ubuntu/Debian Linux:
```bash
$ apt search "system monitor"
```

On macOS:
```bash
$ brew search "monitor"
```

8. **Check the version of an installed tool:**

```bash
$ htop --version
```

Most programs support `--version` or `-v` to show their version number. This is useful when troubleshooting: "Which version of this tool do I have?"

### Success Criteria

You've completed this exercise when you can:

- [ ] Update your package manager
- [ ] Install `htop` and run it (and quit with `q`)
- [ ] Install `tree` and use it to display a directory
- [ ] Search for packages by keyword
- [ ] Check the version of an installed tool

---

> 💡 You just used a tool that senior engineers use every day. You belong here.

---

## What's Next?

You now know how software gets from code to a running program, how to install tools with a package manager, and what `sudo` does. Your terminal toolkit is growing.

From here, you have the foundation to start learning about containers, cloud computing, and eventually Kubernetes. Every tool in the Kubernetes ecosystem — `kubectl`, `helm`, `kind`, `docker` — gets installed exactly the way you just learned.

**Continue to**: [Part 2: Cloud Native 101](../cloud-native-101/module-1.1-what-are-containers/) — Now that you're comfortable with the terminal, it's time to learn what containers are and why they changed everything.
