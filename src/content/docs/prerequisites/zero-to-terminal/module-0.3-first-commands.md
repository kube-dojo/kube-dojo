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

## Why This Module Matters

The terminal is how professionals talk to computers. Clicking buttons in a graphical interface is fine for everyday tasks, but when you need to manage servers, automate work, or use Kubernetes, the terminal is your primary tool.

Here's the thing: **the terminal isn't harder than a graphical interface. It's just different.** Instead of clicking a folder to open it, you type a command. Instead of dragging a file to move it, you type a command. Same actions, different method.

By the end of this module, you'll know the 9 commands that cover about 80% of everyday terminal work.

---

## Opening Your Terminal

Before we begin, you need to actually open a terminal.

**macOS**: Press `Cmd + Space`, type "Terminal", press Enter. (Or find it in Applications > Utilities > Terminal.)

**Windows**: Search for "PowerShell" in the Start menu. (Most commands below work in PowerShell. For full compatibility, install [Windows Terminal](https://aka.ms/terminal) and [WSL](https://learn.microsoft.com/en-us/windows/wsl/install) -- but don't worry about that today.)

**Linux**: Press `Ctrl + Alt + T` on most systems, or search for "Terminal" in your applications.

You should see something like this:

```
username@computername ~ $
```

That `$` (or `%` on some Macs) is the **prompt**. It means the terminal is waiting for you to type something. Think of it as the kitchen staff saying "Order, please!"

---

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

**rm** stands for **R**e**m**ove. It deletes a file.

```bash
rm daily-specials.txt
```

The file is gone.

### WARNING: There Is No Recycle Bin

This is the most important thing in this entire module:

> **`rm` does not move files to a trash can. It deletes them permanently. There is no undo. There is no "Are you sure?" prompt. The file is gone.**

Think of it this way: in a graphical interface, deleting a file moves it to the Trash/Recycle Bin. You can recover it. With `rm`, the file is shredded immediately.

**To delete a folder and everything inside it:**

```bash
rm -r restaurant-copy
```

The `-r` flag means "recursive" -- delete this folder and everything it contains. Be very careful with this.

**The most dangerous command in computing** (DO NOT RUN THIS, just know it exists):

```
rm -rf /    ← NEVER DO THIS. Deletes everything on the computer. Everything.
```

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
| `rm` | Deletes permanently | "Shred this paper" (NO recycle bin!) |
| `clear` | Cleans the screen | "Wipe the whiteboard" |

---

## Did You Know?

- **The terminal predates the mouse by decades.** Computers used text-only interfaces from the 1960s until the mid-1980s. The graphical mouse-and-windows interface you're used to was popularized by the Apple Macintosh in 1984. When you use a terminal, you're using the original way humans talked to computers.

- **`ls` is one of the oldest commands still in use.** It dates back to 1961 in MIT's Compatible Time-Sharing System (CTSS), where it was called `LISTF`. The modern `ls` appeared in the first version of Unix in 1971. You're using a command that's over 50 years old.

- **The `~` (tilde) for home directory comes from a keyboard accident.** On early terminals, the Home key and the `~` key were on the same physical key. The convention stuck, and now every terminal in the world uses `~` to mean "home."

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
| Using `rm` without checking first | Files are permanently deleted -- no undo | Run `ls` first to see what you're about to delete |
| Forgetting `-r` when copying/removing folders | `cp folder newname` fails for directories | Use `cp -r folder newname` or `rm -r folder` |
| Spaces in file names | `mkdir my folder` creates TWO folders: "my" and "folder" | Use quotes: `mkdir "my folder"` or dashes: `mkdir my-folder` |
| Getting lost in the file system | You forget where you are and make files in the wrong place | Type `pwd` frequently. Use `cd ~` to go home when lost |
| Typing commands wrong and getting frustrated | Typos happen to everyone, every day | Use the up arrow key to recall your last command and fix it |

---

## Quiz

1. **What does `pwd` stand for, and what does it do?**
   <details>
   <summary>Answer</summary>
   pwd stands for Print Working Directory. It shows you the full path of the directory (folder) you're currently in. It's like asking "what room am I in?" in our kitchen analogy.
   </details>

2. **What's the difference between `cp` and `mv`?**
   <details>
   <summary>Answer</summary>
   `cp` (copy) creates a duplicate -- the original file stays where it is, and a new copy appears at the destination. `mv` (move) relocates the file -- it disappears from the original location and appears at the new one. Think of it as photocopying vs physically moving a piece of paper.
   </details>

3. **Why is `rm` dangerous compared to deleting files in a graphical interface?**
   <details>
   <summary>Answer</summary>
   When you delete a file in a graphical interface (Finder, File Explorer), it goes to the Trash/Recycle Bin and can be recovered. When you use `rm` in the terminal, the file is permanently deleted immediately. There is no trash can, no undo, and no confirmation prompt (unless you add the `-i` flag).
   </details>

4. **How do you create a nested folder structure like `project/src/components` in one command?**
   <details>
   <summary>Answer</summary>
   Use `mkdir -p project/src/components`. The `-p` flag (for "parents") tells mkdir to create all the parent directories that don't exist yet. Without `-p`, it would fail because `project` and `project/src` don't exist yet.
   </details>

5. **You're lost in the file system. What two commands get you back to safety?**
   <details>
   <summary>Answer</summary>
   `pwd` tells you where you are (so you can orient yourself), and `cd ~` takes you back to your home directory no matter where you are. The `~` (tilde) symbol is a shortcut that always means "my home directory."
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

In [Module 0.5: Editing Files](../module-0.5-editing-files/), you'll learn how to actually put content inside files using a text editor that runs right in your terminal. Creating empty files is useful, but filling them with content is where the real work happens.

---

> **You just used a tool that senior engineers use every day. You belong here.**
