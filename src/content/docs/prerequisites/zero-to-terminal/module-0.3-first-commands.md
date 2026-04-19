---
title: "Module 0.3: First Terminal Commands"
slug: prerequisites/zero-to-terminal/module-0.3-first-commands
sidebar:
  order: 4
lab:
  id: "prereq-0.3-first-commands"
  url: "https://killercoda.com/kubedojo/scenario/prereq-0.3-first-commands"
  duration: "20 min"
  difficulty: "beginner"
  environment: "ubuntu"
---
> **Complexity**: `[QUICK]` - Follow along and type what you see
>
> **Time to Complete**: 25 minutes
>
> **Prerequisites**: [Module 0.1 - What is a Computer?](../module-0.1-what-is-a-computer/)

---

## What You'll Be Able to Do

After this module, you will be able to:
- **Navigate** the file system using `pwd`, `ls`, and `cd` without getting lost
- **Create** files and directories, and explain the difference between `cp` and `mv`
- **Delete** files safely with `rm` and explain why terminal deletions are immediate and usually unrecoverable for ordinary users
- **Combine** commands using pipes (`|`) to filter and search output

---

## Why This Module Matters

The terminal is how professionals talk to computers. Clicking buttons in a graphical interface is fine for everyday tasks, but when you need to manage servers, automate work, or use Kubernetes, the terminal is your primary tool.

Here's the thing: **the terminal isn't harder than a graphical interface. It's just different.** Instead of clicking a folder to open it, you type a command. Instead of dragging a file to move it, you type a command. Same actions, different method.

By the end of this module, you'll know 9 commands that cover a large share of everyday terminal work.

---

## Opening Your Terminal

Before we begin, you need to actually open a terminal.

**macOS**: Press `Cmd + Space`, type "Terminal", press Enter. (Or find it in Applications > Utilities > Terminal.)

**Windows**: Search for "PowerShell" in the Start menu. For this module, though, the command examples are written for a Unix-style shell on macOS, Linux, or Windows Subsystem for Linux (WSL). If you're using native PowerShell, expect some commands later in the module to differ.

**Linux**: Press `Ctrl + Alt + T` on most systems, or search for "Terminal" in your applications.

You should see something like this:

```
username@computername ~ $
```

That `$` (or `%` on some Macs) is the **prompt**. It means the terminal is waiting for you to type something. Think of it as the kitchen staff saying "Order, please!"

---

> Note: From this point on, examples assume a Unix-style shell: Terminal on macOS, a Linux terminal, or WSL on Windows.

## Your File System: The Restaurant Floor Plan

Before we start running commands, you need to understand one thing: your computer organizes files in a **tree structure**. Think of it like rooms in a building.

```
/ (the root -- the building itself)
├── Users/
│   └── yourname/          ← This is your "home directory"
│       ├── Desktop/
│       ├── Documents/
│       ├── Downloads/
│       └── Pictures/
├── Applications/
└── System/
```

Every file lives somewhere in this tree. Commands let you move through the tree, see what's in each room, and create or remove things.

---

## Command 1: `pwd` -- "Where Am I?"

**pwd** stands for **P**rint **W**orking **D**irectory. It tells you where you are right now.

Think of it as asking: "What room am I in?"

```bash
pwd
```

Expected output:
```
/Users/yourname
```

(On Linux, it might be `/home/yourname`. On Windows PowerShell, something like `C:\Users\yourname`.)

This is your **home directory** -- your personal space in the computer. It's like your own private office in the restaurant.

**When to use it**: Whenever you're not sure where you are. Even experienced engineers type `pwd` constantly. There's no shame in checking.

---

## Command 2: `ls` -- "What's Here?"

**ls** stands for **L**i**s**t. It shows you what's in your current directory (room).

```bash
ls
```

Expected output (yours will be different):
```
Desktop    Documents    Downloads    Music    Pictures
```

Want more details? Add the `-l` flag (that's a lowercase L, for "long format"):

```bash
ls -l
```

Expected output:
```
drwx------   4 yourname  staff   128 Mar 15 10:30 Desktop
drwx------   5 yourname  staff   160 Mar 20 09:15 Documents
drwx------  12 yourname  staff   384 Mar 22 14:45 Downloads
```

Don't worry about understanding every column yet. The important parts are the name (rightmost) and the date (when it was last changed).

> **Try it yourself**: Run `ls` in your home directory. Now run `ls -l`. What extra information do you see? You should notice dates, sizes, and some cryptic letters on the left. Don't worry about understanding all of it yet — just notice that the `-l` flag gives you more detail than plain `ls`.

Want to see hidden files too? (Files starting with a dot, like `.bashrc`, are hidden by default.)

```bash
ls -la
```

The `-a` means "all" -- show everything, including hidden files.

---

## Command 3: `cd` -- "Go Somewhere"

**cd** stands for **C**hange **D**irectory. It moves you to a different room.

```bash
cd Documents
```

Now check where you are:

```bash
pwd
```

Output:
```
/Users/yourname/Documents
```

You moved! You're now "inside" the Documents folder.

> **Pause and predict**: If `cd Documents` moves you forward into the Documents folder, what command do you think you would use to go backward out of it?

### Going back up: `cd ..`

The `..` means "the parent directory" -- the room that contains this room.

```bash
cd ..
```

```bash
pwd
```

Output:
```
/Users/yourname
```

You're back in your home directory.

### Going home: `cd ~`

No matter where you are in the file system, `cd ~` takes you home. The `~` symbol (called "tilde") is a shortcut for your home directory.

```bash
cd ~
```

This is like having a "return to base" button. Use it whenever you get lost.

### Going to a specific place: `cd /path/to/place`

You can jump directly to any location by typing the full path:

```bash
cd /tmp
```

```bash
pwd
```

Output:
```
/tmp
```

Now go back home:

```bash
cd ~
```

---

## Command 4: `mkdir` -- "Build a New Room"

**mkdir** stands for **M**a**k**e **Dir**ectory. It creates a new folder.

```bash
mkdir my-first-folder
```

Check that it worked:

```bash
ls
```

You should see `my-first-folder` in the list.

### Creating nested folders: `mkdir -p`

What if you want to create a folder inside a folder inside a folder? The `-p` flag (for "parents") creates the entire path at once:

```bash
mkdir -p restaurant/kitchen/prep-area
```

This creates three folders nested inside each other, even though `restaurant` and `kitchen` didn't exist yet.

---

## Command 5: `touch` -- "Create an Empty File"

**touch** creates an empty file. (Technically, it updates a file's timestamp, but if the file doesn't exist, it creates it.)

```bash
touch menu.txt
```

Check:

```bash
ls
```

You'll see `menu.txt` in your list. It's empty -- just a blank piece of paper waiting to be written on.

---

## Command 6: `cp` -- "Photocopy a File"

**cp** stands for **C**o**p**y. It makes a duplicate of a file.

```bash
cp menu.txt menu-backup.txt
```

Now you have two files: the original and the copy.

```bash
ls
```

Output:
```
menu-backup.txt    menu.txt    my-first-folder    restaurant
```

To copy a file into a folder:

```bash
cp menu.txt restaurant/
```

To copy an entire folder (and everything inside it), use `-r` (for "recursive" -- meaning "this folder and everything in it"):

```bash
cp -r restaurant restaurant-copy
```

---

## Command 7: `mv` -- "Move or Rename"

**mv** stands for **M**o**v**e. It does two things:

**Moving a file to another folder:**

```bash
mv menu-backup.txt restaurant/
```

The file is no longer here -- it's been moved into the `restaurant` folder. Unlike `cp`, the original doesn't stay behind.

**Renaming a file:**

```bash
mv menu.txt daily-specials.txt
```

The file `menu.txt` is gone. In its place is `daily-specials.txt`. Same file, new name. Moving and renaming are the same operation -- you're just changing where (or what) the file is called.

---

## Command 8: `rm` -- "Throw Away"

> **Stop and think**: When you delete a file by dragging it to the Trash on your desktop, where does it go? You can still recover it, right? Now think — what do you think happens when you delete a file in the terminal? Is there a Trash can? Take a guess before reading.

**rm** stands for **R**e**m**ove. It deletes a file.

```bash
rm daily-specials.txt
```

The file is gone.

### WARNING: There Is No Recycle Bin

This is the most important thing in this entire module:

> **`rm` does not move files to a trash can. It removes the file entry immediately, usually without an "Are you sure?" prompt or built-in undo. For everyday users, recovery is often difficult or impossible, although specialists may sometimes recover data before it is overwritten. If you need stronger assurance that data cannot be recovered, tools such as `shred` are used for that purpose.**

**Real-World War Story:** In 1998, Pixar came close to losing the in-progress animation work for *Toy Story 2*. A command run against the wrong directory of the production servers began recursively deleting character models, sets, and animations. People watched files disappear in real time and literally pulled the server's power plug to stop it, but a large fraction of the work was already gone. Pixar recovered because one of the supervising technical directors — who had been working from home with a newborn — had been copying the project to a computer at her house. Even that copy was a couple of weeks old, so they still had to reconstruct work on top of it. The lesson for you: `rm` does exactly what you tell it to, instantly, with no "Are you sure?" — treat it with the same respect you'd give a real kitchen knife.

**To delete a folder and everything inside it:**

```bash
rm -r restaurant-copy
```

The `-r` flag means "recursive" -- delete this folder and everything it contains. Be very careful with this.

**A classic dangerous example** (DO NOT RUN THIS, just know why people warn about it):

```bash
rm -rf /
```

On modern GNU/Linux systems, `rm` normally refuses to operate on `/` because of the default `--preserve-root` safety guard. Removing `/` requires explicitly disabling that protection with an unsafe flag such as `--no-preserve-root`.

Rule of thumb: always double-check what you're deleting before pressing Enter.

---

## Command 9: `clear` -- "Clean the Screen"

After running many commands, your screen gets cluttered. `clear` wipes the screen so you start fresh.

```bash
clear
```

Your screen is now clean. Nothing was deleted -- it just scrolled the old output out of view. You can still scroll up to see it.

**Keyboard shortcut**: On most terminals, `Ctrl + L` does the same thing.

---

## Quick Reference Card

Keep this handy until these become muscle memory:

| Command | What It Does | Kitchen Analogy |
|---------|-------------|-----------------|
| `pwd` | Shows where you are | "What room am I in?" |
| `ls` | Lists what's here | "What's on this shelf?" |
| `cd` | Moves to another place | "Walk to another room" |
| `mkdir` | Creates a new folder | "Build a new room" |
| `touch` | Creates an empty file | "Put a blank paper on the counter" |
| `cp` | Copies a file | "Photocopy this recipe" |
| `mv` | Moves or renames | "Move this to another shelf" or "relabel it" |
| `rm` | Deletes immediately | "Shred this paper" (no recycle bin by default) |
| `clear` | Cleans the screen | "Wipe the whiteboard" |

---

## When Pros Use These Commands

You might be wondering if professionals really use these basic commands every day. Absolutely. Here is how they look in the real world:

- **A DevOps engineer** uses `mkdir -p` to instantly create identical deployment directory structures across 50 servers at once.
- **A Site Reliability Engineer (SRE)** uses `ls -lt | head` during a major site outage to instantly find the most recently changed configuration file that might have caused the crash.
- **A Systems Administrator** uses `cd ~` and `pwd` constantly to re-orient themselves after jumping through dozens of different server environments.

### Honest Trade-Offs: When to Use the GUI

Let's be honest: the terminal isn't the best tool for *everything*. You should absolutely reach for a graphical file manager (like Finder or Windows Explorer) when:
- **Bulk Visual Sorting:** You need to visually browse and sort through hundreds of photos or design assets.
- **Drag-and-Drop Workflows:** You are dragging files between different applications, like dropping an image into a web browser.
- **Quick Previews:** You want to tap the spacebar to quickly preview a video or PDF without opening a full application.

Use the terminal when you need precision, automation, or remote access. Use the GUI when you need visual intuition. Professionals use both.

---

## Did You Know?

- **Command-line interfaces became common long before graphical mouse-and-windows interfaces became mainstream.** [Computers used text-only interfaces from the 1960s until the mid-1980s.](https://en.wikipedia.org/wiki/Command-line_interface) The graphical mouse-and-windows interface you're used to was [popularized by the Apple Macintosh in 1984](https://en.wikipedia.org/wiki/Classic_Mac_OS). When you use a terminal, you're using the original way humans talked to computers.

- **`ls` is one of the oldest commands still in use.** It dates back to 1961 in MIT's Compatible Time-Sharing System (CTSS), where it was called `LISTF`. The modern `ls` appeared in the first version of Unix in 1971. You're using a command that's over 50 years old.

- **The `~` (tilde) for home directory comes from a keyboard accident.** On early terminals, [the Home key and the `~` key were on the same physical key](https://en.wikipedia.org/wiki/Tilde). The convention stuck, and many Unix-like shells now use `~` to mean "home."

---

## Bonus: Connecting Commands with Pipes

This is a **bonus section** -- feel free to skim it now and come back later. You don't need to master this today.

Sometimes you want to take the output of one command and feed it into another command. That's what the **pipe** (`|`) does.

> Kitchen analogy: Think of it like an assembly line. One station chops the vegetables, then passes them down the line to the next station that cooks them. Each station does one job and hands off the result.

The `|` character (usually found above the Enter/Return key, typed with Shift + Backslash) sends the output of the command on its left into the command on its right.

**Show only the first 5 files:**

```bash
ls | head -5
```

`ls` lists everything, but `head -5` takes only the first 5 lines. Useful when a folder has hundreds of files.

**Search for a word inside a file:**

```bash
cat menu.txt | grep "pasta"
```

`cat` displays the file contents, and `grep "pasta"` filters to show only lines containing "pasta." (You'll use `grep` a LOT in your career.)

**Find a past command you typed:**

```bash
history | grep "mkdir"
```

`history` shows every command you've typed, and `grep "mkdir"` filters it down to only the ones that included "mkdir." Very handy when you can't remember the exact command you ran earlier.

You'll get more practice with pipes as the curriculum continues. For now, just remember: `|` connects commands like stations on an assembly line.

---

## Common Mistakes

| Mistake | Why It's a Problem | What to Do Instead |
|---------|-------------------|-------------------|
| Using `rm` without checking first | Files are removed immediately, and recovery is usually not available to normal users | Run `ls` first to see what you're about to delete |
| Forgetting `-r` when copying/removing folders | `cp folder newname` fails for directories | Use `cp -r folder newname` or `rm -r folder` |
| Spaces in file names | `mkdir my folder` creates TWO folders: "my" and "folder" | Use quotes: `mkdir "my folder"` or dashes: `mkdir my-folder` |
| Getting lost in the file system | You forget where you are and make files in the wrong place | Type `pwd` frequently. Use `cd ~` to go home when lost |
| Typing commands wrong and getting frustrated | Typos happen to everyone, every day | Use the up arrow key to recall your last command and fix it |

---

## Quiz

1. **You ran `mkdir projects` but the folder appeared in a completely unexpected location. What command should you have run BEFORE `mkdir`, and why?**
   <details>
   <summary>Answer</summary>
   You should have run `pwd` first to check where you were. `mkdir` creates the folder in your current working directory, and if you navigated somewhere unexpected earlier without realizing it, the folder ends up in the wrong place. This is the #1 beginner mistake — always know where you are before creating or deleting anything. Run `pwd`, verify you're in the right place, then proceed.
   </details>

2. **You need to reorganize your project folder. You want to keep your original logo file in the 'assets' folder but also need a version of it in the 'public' folder. Later, you realize a config file is in the wrong directory and needs to be relocated without leaving a duplicate behind. Which commands do you use for each task and why?**
   <details>
   <summary>Answer</summary>
   For the logo file, you use `cp` because you need a duplicate. `cp` (copy) creates a second identical file at the destination while leaving the original untouched, which is perfect for keeping your master asset safe. For the config file, you use `mv` because it needs to be relocated without leaving a messy duplicate behind. `mv` (move) removes the file from its original location and places it in the new one, keeping your directory structure clean.
   </details>

3. **You are cleaning up old log files in your terminal and accidentally type `rm production-db.sql` instead of `rm production.log`. You immediately hit `Ctrl+Z` and look for the 'Undo' button or the Trash bin to recover your database backup. What happens next and why?**
   <details>
   <summary>Answer</summary>
   You usually cannot recover the database backup file through `Ctrl+Z`, an Undo button, or a Trash bin. When you delete a file using `rm` in the terminal, it does not get moved to a temporary Trash or Recycle Bin like it does in a graphical interface. Instead, `rm` removes the directory entry immediately. For normal users, that means the file is effectively gone, although forensic or undelete tools may sometimes recover data before it is overwritten. There is no built-in undo feature or confirmation prompt by default, which is why you must always double-check your commands before pressing Enter.
   </details>

4. **You are starting a new web project and need to create a deep directory structure `app/frontend/components/buttons/` right away, but none of these folders exist yet. You try `mkdir app/frontend/components/buttons/` but the terminal throws an error. What command should you use instead and why did the first one fail?**
   <details>
   <summary>Answer</summary>
   You should use `mkdir -p app/frontend/components/buttons/` to create the structure. The standard `mkdir` command fails in this scenario because it can only create a new folder if its parent directory already exists. By adding the `-p` (parents) flag, you instruct the command to automatically create any missing parent directories along the specified path. This saves you from having to run the command four separate times.
   </details>

5. **You've been navigating through deep server logs for an hour and suddenly realize you have no idea which directory you are currently in, and you need to get back to your main user folder to run a script. What two commands do you use to figure out your location and return to your main folder, and why?**
   <details>
   <summary>Answer</summary>
   First, you use the `pwd` command to print your working directory, which tells you your exact current location in the file system so you can orient yourself. Then, you use the `cd ~` command to immediately jump back to your user's home directory. The tilde (`~`) symbol is a universal shortcut that always represents your home directory, regardless of how deep you are currently navigated. This combination quickly restores your context and puts you back in a safe, known location.
   </details>

---

## Hands-On Exercise: Build a Restaurant File Structure

Let's practice everything you've learned by creating a file structure for our imaginary restaurant.

### Step 1: Go to your home directory

```bash
cd ~
```

### Step 2: Create the restaurant structure

```bash
mkdir -p restaurant/kitchen/prep-area
mkdir -p restaurant/kitchen/cooking-stations
mkdir -p restaurant/dining-room
mkdir -p restaurant/storage/pantry
mkdir -p restaurant/storage/freezer
```

### Step 3: Create some files

```bash
touch restaurant/kitchen/prep-area/chopping-board.txt
touch restaurant/kitchen/cooking-stations/grill.txt
touch restaurant/kitchen/cooking-stations/oven.txt
touch restaurant/dining-room/table-1.txt
touch restaurant/dining-room/table-2.txt
touch restaurant/storage/pantry/flour.txt
touch restaurant/storage/pantry/sugar.txt
touch restaurant/storage/freezer/ice-cream.txt
```

### Step 4: Look at what you built

```bash
ls restaurant/
ls restaurant/kitchen/
ls restaurant/kitchen/cooking-stations/
```

Expected output for the last command:
```
grill.txt    oven.txt
```

### Step 5: Move some things around

The ice cream is melting! Move it from the freezer to the prep area:

```bash
mv restaurant/storage/freezer/ice-cream.txt restaurant/kitchen/prep-area/
```

Verify:

```bash
ls restaurant/kitchen/prep-area/
```

Expected output:
```
chopping-board.txt    ice-cream.txt
```

### Step 6: Make a backup of the menu

```bash
touch restaurant/menu.txt
cp restaurant/menu.txt restaurant/menu-backup.txt
ls restaurant/
```

### Step 7: Clean up

When you're done experimenting:

```bash
rm -r restaurant
```

Verify it's gone:

```bash
ls | grep restaurant
```

No output means it's gone.

**Success criteria**: You created a nested directory structure, created files inside it, moved files between directories, copied a file, and cleaned everything up. All without clicking a single button.

---

## What's Next?

In [Module 0.4: Files and Directories](../module-0.4-files-and-directories/), you'll dive deeper into how your computer organizes everything into files and folders, and how to navigate them like a pro.

---

> **You just used a tool that senior engineers use every day. You belong here.**

## Sources

- [Command-line interface](https://en.wikipedia.org/wiki/Command-line_interface) — Background on text-based computer interfaces and their long use before mainstream graphical systems.
- [Classic Mac OS](https://en.wikipedia.org/wiki/Classic_Mac_OS) — Overview of the original Macintosh software platform associated with the popularization of GUI computing in 1984.
- [Tilde](https://en.wikipedia.org/wiki/Tilde) — Explains the historical terminal-keyboard convention behind `~` as a home-directory shorthand.
- [Unix shell](https://en.wikipedia.org/wiki/Unix_shell) — Further reading on shells, prompts, commands, and the environment this module introduces.
- [ls](https://en.wikipedia.org/wiki/Ls) — Further reading on the `ls` command, including history and common options.
- [Pipeline (Unix)](https://en.wikipedia.org/wiki/Pipeline_%28Unix%29) — Further reading on how the pipe operator connects one command's output to another.
