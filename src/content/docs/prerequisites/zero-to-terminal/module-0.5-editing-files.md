---
title: "Module 0.5: Editing Files"
slug: prerequisites/zero-to-terminal/module-0.5-editing-files
sidebar:
  order: 6
lab:
  id: "prereq-0.5-editing-files"
  url: "https://killercoda.com/kubedojo/scenario/prereq-0.5-editing-files"
  duration: "20 min"
  difficulty: "beginner"
  environment: "ubuntu"
---
> **Complexity**: `[QUICK]` - Type what you see, save, done
>
> **Time to Complete**: 25 minutes
>
> **Prerequisites**: [Module 0.3 - First Terminal Commands](../module-0.3-first-commands/)

---

## What You'll Be Able to Do

After this module, you will be able to:
- **Create and edit** files using `nano` from the terminal without a graphical editor
- **Write** a simple bash script that combines multiple commands into one file
- **Make** a script executable with `chmod +x` and explain why this step is necessary
- **Choose** between `nano` and `vim` and explain when you'd use each

---

## Why This Module Matters

In the last module, you created files with `touch` -- but they were empty. Empty files are like blank order tickets in a restaurant kitchen. Useful for reserving a spot, but not much else until someone writes on them.

In the real world, you'll need to edit files constantly:
- **Configuration files** tell programs how to behave (like the house rules in a kitchen)
- **Scripts** are files that contain a sequence of commands (like a recipe card)
- **Kubernetes manifests** are files that tell Kubernetes what to run (you'll get there!)

Consider a real-world incident at a major tech company: a junior engineer needed to update a simple setting in a load balancer. They opened the `nginx.conf` file in `nano`, accidentally typed a few stray characters while trying to save, and saved the file. Within minutes, the entire site went down, costing thousands of dollars in revenue. Why? Because they were editing directly on the production server without realizing it, and a single typo in a configuration file can break a service. 

You need to be able to open a file, write in it, save it, and close it -- all from the terminal. No mouse. No graphical text editor. Just you and the keyboard. Learning to edit files safely in the terminal isn't just about writing text; it's about navigating the control room of your servers with precision.

---

## Why Edit Files in the Terminal?

"Can't I just use Notepad or TextEdit?"

You can -- on your own computer. But remember from Module 0.1: almost every server runs Linux, and servers usually don't have a graphical interface. When you connect to a remote server (which you'll learn in Module 0.7), there's no mouse, no desktop, no Notepad. There's just the terminal.

The terminal text editor is the chef's knife of computing. It's not the fanciest tool, but you'll use it everywhere.

---

## Meet nano: Your First Terminal Editor

There are many text editors that run in the terminal. The two most famous are **vim** and **nano**.

We're starting with **nano** because:

| nano | vim |
|------|-----|
| Works the way you'd expect | Has a steep learning curve |
| Type and it types | You need to press `i` before you can type |
| Menu at the bottom shows you how to save and quit | People famously get stuck and can't figure out how to exit |
| Perfect for beginners | Powerful but overwhelming at first |

There's no shame in using nano. Many experienced engineers use it for quick edits. You'll learn vim later when you're ready for more power.

> **Fun fact**: "How to exit vim" is one of the most searched programming questions on the internet. Over 2 million people have viewed that question on Stack Overflow. With nano, you'll never have that problem.

---

## Opening nano

Let's create and edit a file. First, make sure you're in your home directory:

```bash
cd ~
```

Now open nano with a new file:

```bash
nano hello.txt
```

Your screen will change completely. You'll see something like this:

```
  GNU nano 9.0                    hello.txt







^G Help    ^O Write Out  ^W Where Is   ^K Cut       ^C Location
^X Exit    ^R Read File  ^\ Replace    ^U Paste     ^T Execute
```

Let's break this down:

- **Top line**: The editor name and your file name
- **Middle area**: This is where you type (it's blank because the file is new)
- **Bottom two lines**: The menu showing available commands

---

## The ^ Symbol Means Ctrl

This is the one thing that confuses everyone at first:

> **The `^` symbol means "hold the Ctrl key."**

So when you see `^O Write Out`, that means: "Press Ctrl and O at the same time to save the file."

| What You See | What You Press | What It Does |
|-------------|---------------|-------------|
| `^O` | Ctrl + O | Save the file |
| `^X` | Ctrl + X | Exit nano |
| `^K` | Ctrl + K | Cut the current line |
| `^U` | Ctrl + U | Paste a cut line |
| `^W` | Ctrl + W | Search for text |
| `^G` | Ctrl + G | Show help |

That's it. Six key combos and you can do everything you need.

---

## Typing Text

This is the easy part: **just type.**

With nano open, type the following (press Enter at the end of each line):

```
Welcome to the Kitchen!
Today's special: Learning to edit files.
Chef says: You're doing great.
```

Your screen should now show:

```
  GNU nano 9.0                    hello.txt                    Modified

Welcome to the Kitchen!
Today's special: Learning to edit files.
Chef says: You're doing great.


^G Help    ^O Write Out  ^W Where Is   ^K Cut       ^C Location
^X Exit    ^R Read File  ^\ Replace    ^U Paste     ^T Execute
```

Notice the word **Modified** in the top line. That means you've made changes that haven't been saved yet.

---

## Saving: Ctrl + O

Let's save. Press:

```
Ctrl + O
```

nano will ask you to confirm the file name:

```
File Name to Write: hello.txt
```

Press **Enter** to confirm. The "Modified" indicator disappears. Your file is saved.

---

## Exiting: Ctrl + X

To leave nano and return to the terminal:

```
Ctrl + X
```

If you've made changes since your last save, nano will ask:

```
Save modified buffer?  Y Yes  N No  ^C Cancel
```

Press `Y` to save and exit, `N` to exit without saving, or `Ctrl + C` to cancel and stay in nano.

---

## Verify Your File: `cat`

Now that you're back in the terminal, let's confirm the file was saved. The `cat` command prints a file's contents to the screen:

```bash
cat hello.txt
```

Expected output:

```
Welcome to the Kitchen!
Today's special: Learning to edit files.
Chef says: You're doing great.
```

`cat` is short for "concatenate" (it can combine multiple files), but most people use it to quickly peek at a file's contents. Think of it as reading a note without picking it up -- you just glance at it.

---

## Editing an Existing File

To edit a file that already exists, just open it the same way:

```bash
nano hello.txt
```

Your text is there. Use the arrow keys to move around. Type to add text. Use Backspace/Delete to remove text.

Add a new line at the bottom:

```
PS: The pantry is fully stocked.
```

Save with `Ctrl + O`, Enter. Exit with `Ctrl + X`.

---

## Cut and Paste Lines

nano has simple cut and paste for entire lines:

1. Move your cursor to the line you want to cut
2. Press **Ctrl + K** to cut it (the line disappears)
3. Move your cursor to where you want to paste it
4. Press **Ctrl + U** to paste it

You can cut multiple lines by pressing `Ctrl + K` multiple times -- they stack up. Then `Ctrl + U` pastes them all.

This is like the chef rearranging the order of steps in a recipe.

---

## Search for Text

Working with a long file and need to find something? Press **Ctrl + W**, type what you're looking for, and press Enter.

```
Ctrl + W
```

nano will prompt:

```
Search:
```

Type `special` and press Enter. The cursor jumps to the first occurrence of "special" in the file.

Press `Ctrl + W` and then Enter again (without typing anything) to find the next occurrence.

---

## Your First Script

Now let's do something powerful: write a script. A script is just a text file that contains commands the computer can run. It's a recipe card for the terminal.

### Step 1: Create the script

```bash
nano my-first-script.sh
```

> **Stop and think**: This script starts with a strange line: `#!/bin/bash`. What do you think it does? It's called a "shebang" — it's the script's way of telling the computer "I'm written in bash, use the bash program to run me." Without it, the computer wouldn't know how to interpret the file. You'll see this line at the top of every shell script you encounter.

Type the following exactly:

```bash
#!/bin/bash

echo "Welcome to the kitchen!"
echo "Today's date is: $(date)"
echo "You are logged in as: $(whoami)"
echo "Your current directory is: $(pwd)"
echo ""
echo "Great job, chef! Your first script works!"
```

Let's understand each line:

- `#!/bin/bash` -- This is called a "shebang." It tells the computer "use the bash program to run this file." Every script needs this as the first line. (Yes, "shebang" is a real term.)
- `echo` -- A command that prints text to the screen. Think of it as the kitchen yelling "Order up!"
- `$(date)` -- Runs the `date` command and inserts the result. The `$()` syntax means "run this command and give me the output."
- `$(whoami)` -- Runs `whoami`, which tells you your username.
- `$(pwd)` -- You know this one -- it prints your current directory.

### Step 2: Save and exit

Press `Ctrl + O`, Enter, then `Ctrl + X`.

### Step 3: Make it executable

> **Pause and predict**: Before running `chmod`, try to run the script directly: `./my-first-script.sh`. What happens? You should get "Permission denied." This is intentional — new files are just data by default. The computer needs explicit permission to treat a file as a program. This is a security feature, not a bug.

Right now, the file is just text. The computer won't run it because it doesn't have *permission* to be executed. Let's fix that:

```bash
chmod +x my-first-script.sh
```

`chmod` stands for **ch**ange **mod**e. The `+x` means "add execute permission." You're telling the restaurant manager: "This isn't just a document -- it's a recipe that should be cooked."

### Step 4: Run it

```bash
./my-first-script.sh
```

The `./` means "run this file from the current directory." Expected output:

```
Welcome to the kitchen!
Today's date is: Sun Mar 23 14:30:00 UTC 2026
You are logged in as: yourname
Your current directory is: /Users/yourname

Great job, chef! Your first script works!
```

You just wrote and executed your first program. That's not nothing -- that's everything.

---

## A Note on vim

You'll encounter vim eventually. It's incredibly powerful and used by many senior engineers, though it is not installed by default on all minimal Linux distributions. But vim has a famously steep learning curve because it works in "modes" -- you can't just open it and start typing.

We're not ignoring vim. We're saving it for when you have more context. Right now, nano gets the job done, and learning to walk before you run is how chefs train too.

When you're ready, vim will be there. For now, nano is your friend.

---

## Did You Know?

- **nano is a clone of a clone.** It was created as a free replacement for an editor called `pstrict` which was a replacement for `pstrict` ... actually, nano is a free replacement for `pico`, which was the editor built into the Pine email client from 1989. The name `nano` derives from the SI prefix system, reflecting its role as a successor to pico (nano is 1,000 times larger than pico).

- **The oldest surviving text editor still in use is `ed`, created in 1969.** It was written by Ken Thompson, one of the creators of Unix. `ed` is a "line editor" -- you can't see the whole file at once. You edit one line at a time. Engineers in the 1970s wrote entire operating systems using `ed`. Your experience with nano is luxurious by comparison.

- **Configuration files run the world.** Nearly every piece of software reads a text configuration file when it starts up. Your web server, your database, Kubernetes itself -- they all read text files to know how to behave. The ability to edit these files from the terminal is one of the most practical skills in all of computing.

---

## Common Mistakes

| Mistake | Why It's a Problem | What to Do Instead |
|---------|-------------------|-------------------|
| Pressing Ctrl+Z instead of Ctrl+X to exit | Ctrl+Z suspends nano (hides it) instead of closing it. The file stays open in the background | If you accidentally suspend, type `fg` to bring nano back. Then use Ctrl+X to exit properly |
| Forgetting to save before exiting | Your changes are lost | Always Ctrl+O to save before Ctrl+X to exit. Or just press Ctrl+X and say Y when asked to save |
| Not adding `#!/bin/bash` to scripts | The system doesn't know how to run the file | Always make the first line of a bash script `#!/bin/bash` |
| Forgetting `chmod +x` before running a script | You get "Permission denied" | Run `chmod +x filename.sh` to make the file executable |
| Using `nano` when you meant to use `cat` | You accidentally open the file for editing when you just wanted to read it | Use `cat filename` to view a file without editing it |
| Editing a file on a remote server thinking it is local | You might accidentally change production configuration instead of your local testing files, causing unexpected downtime | Always check your prompt (like `user@server`) or run `hostname` to confirm which machine you are currently editing files on |
| Opening a binary file (like an image or compiled program) in nano and saving it | Nano will try to read the binary data as text, and saving it will corrupt the file permanently | Only use nano for plain text files (scripts, configs, logs). Use `file filename` to check the file type before opening |

---

## Quiz

1. **You are editing a crucial configuration file and the nano menu at the bottom tells you to press `^O` to Write Out. You try typing the caret symbol (`^`) and then the letter `O`, but it just types "^O" into your file. What went wrong?**
   <details>
   <summary>Answer</summary>
   You interpreted the `^` symbol literally instead of as a modifier key. In terminal applications like nano, the `^` symbol represents the Ctrl (Control) key on your keyboard. Therefore, `^O` means you should hold down the Ctrl key and press the letter O at the same time. This is a standard convention in Unix-like systems for showing keyboard shortcuts. By typing the characters individually, you were just adding raw text to your document instead of executing the save command.
   </details>

2. **You've spent 15 minutes carefully writing a bash script in nano. You press Ctrl+X to exit, but you accidentally press 'N' when prompted to "Save modified buffer?". What happens to your script, and what should you have done differently to ensure your work was safe?**
   <details>
   <summary>Answer</summary>
   Your script changes are permanently lost because pressing 'N' tells nano to discard all modifications made since the last save. Unlike modern graphical editors with autosave or history features, terminal editors do exactly what you tell them in the moment. To prevent this, you should form the habit of manually saving your file before attempting to exit. You do this by pressing Ctrl+O (Write Out) and hitting Enter to confirm the file name, which writes your changes to the disk immediately. Once saved, the "Modified" indicator at the top disappears, and you can safely exit with Ctrl+X.
   </details>

3. **You download a script from a coworker that ends in `.sh`. You make it executable and try to run it, but your system throws an error saying it doesn't know how to execute the file. Upon opening it in nano, you see the first line is simply `echo "Starting backup"`. What crucial element is missing, and why does the system need it?**
   <details>
   <summary>Answer</summary>
   The script is missing its "shebang" line (e.g., `#!/bin/bash`) at the very top of the file. Without this line, the operating system's program loader doesn't know which interpreter program should be used to read and execute the subsequent instructions. The shebang acts as a strict directive, telling the system whether to pass the file's contents to bash, python, node, or another interpreter. Because it was missing, the system attempted to guess or use a default execution method, which failed because the context wasn't explicitly defined.
   </details>

4. **You've written a perfect script to automate your server backups, saved it as `backup.sh`, and typed `./backup.sh` to run it. Instead of your backup starting, the terminal sternly replies: `Permission denied`. Why did the system block your script, and how do you resolve this?**
   <details>
   <summary>Answer</summary>
   The system blocked your script because, by default, newly created text files only have read and write permissions, not execute permissions. This is a fundamental security feature in Linux designed to prevent arbitrary text files or downloaded data from being accidentally or maliciously run as programs. To resolve this, you must explicitly grant the file the right to be executed by running `chmod +x backup.sh`. This changes the file's mode, signaling to the operating system that you, the owner, vouch for this file and authorize it to run as a program.
   </details>

5. **You wrote a script called `backup.sh` and tried to run it with `./backup.sh`. You got "Permission denied." Then you ran `chmod +x backup.sh` and tried again — now it says "line 1: syntax error." What are the TWO things that went wrong, and in what order should you fix them?**
   <details>
   <summary>Answer</summary>
   The first issue was that your file lacked execute permissions, which is standard for newly created files as a security measure; this was correctly resolved using `chmod +x`. The second issue is that the script itself contains invalid instructions, most likely a malformed shebang on the first line (such as `#bin/bash` instead of `#!/bin/bash`). You must always address permission issues first because the system won't even attempt to read the syntax of a file it isn't allowed to execute. Once permissions are granted, the interpreter can read the file, encounter the bad syntax, and provide a helpful error message pointing directly to line 1. To fix the remaining issue, you should open the file in nano and correct the typo on the first line.
   </details>

---

## Hands-On Exercise: Kitchen Memo Board

Create a "memo board" for the restaurant kitchen, practice editing, and write a script.

### Part 1: Create and edit a memo

```bash
cd ~
nano kitchen-memo.txt
```

Type the following five lines:

```
=== KITCHEN MEMO BOARD ===
1. Morning prep starts at 6 AM
2. New menu items arriving Thursday
3. Remember: clean as you go
4. Staff meeting at 3 PM Friday
```

Save with `Ctrl + O`, Enter. Exit with `Ctrl + X`.

Verify your work:

```bash
cat kitchen-memo.txt
```

You should see all five lines printed exactly as you typed them.

### Part 2: Edit the memo

Open it again:

```bash
nano kitchen-memo.txt
```

Add a sixth line at the bottom:

```
5. Chef says: great work today, team!
```

Save and exit (`Ctrl + O`, Enter, `Ctrl + X`).

Verify:

```bash
cat kitchen-memo.txt
```

All six lines should be there.

### Part 3: Write a cleanup script

```bash
nano kitchen-report.sh
```

Type:

```bash
#!/bin/bash

echo "=== Kitchen Status Report ==="
echo "Date: $(date)"
echo "Chef on duty: $(whoami)"
echo ""
echo "--- Memo Board Contents ---"
cat kitchen-memo.txt
echo ""
echo "--- Files in current directory ---"
ls
echo ""
echo "Report complete. Kitchen is running smoothly!"
```

Save and exit.

Make it executable and run it:

```bash
chmod +x kitchen-report.sh
./kitchen-report.sh
```

Expected output (details will vary):

```
=== Kitchen Status Report ===
Date: Sun Mar 23 14:45:00 UTC 2026
Chef on duty: yourname

--- Memo Board Contents ---
=== KITCHEN MEMO BOARD ===
1. Morning prep starts at 6 AM
2. New menu items arriving Thursday
3. Remember: clean as you go
4. Staff meeting at 3 PM Friday
5. Chef says: great work today, team!

--- Files in current directory ---
hello.txt    kitchen-memo.txt    kitchen-report.sh    my-first-script.sh
...

Report complete. Kitchen is running smoothly!
```

### Part 4: Clean up

```bash
rm hello.txt kitchen-memo.txt kitchen-report.sh my-first-script.sh
```

**Success criteria**: You created a file with nano, edited it, wrote a bash script that reads from another file, made it executable, and ran it. You're not just using the terminal anymore -- you're *programming* in it.

---

## What's Next?

**Next Module**: [Module 0.6: Git Basics](../module-0.6-git-basics/) — Learn to track your work with version control, the foundation of all modern software delivery.

---

> **You just used a tool that senior engineers use every day. You belong here.**