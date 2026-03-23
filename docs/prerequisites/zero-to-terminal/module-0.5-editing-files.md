# Module 0.5: Editing Files

> **Complexity**: `[QUICK]` - Type what you see, save, done
>
> **Time to Complete**: 25 minutes
>
> **Prerequisites**: [Module 0.3 - First Terminal Commands](module-0.3-first-commands.md)

---

## Why This Module Matters

In the last module, you created files with `touch` -- but they were empty. Empty files are like blank order tickets in a restaurant kitchen. Useful for reserving a spot, but not much else until someone writes on them.

In the real world, you'll need to edit files constantly:
- **Configuration files** tell programs how to behave (like the house rules in a kitchen)
- **Scripts** are files that contain a sequence of commands (like a recipe card)
- **Kubernetes manifests** are files that tell Kubernetes what to run (you'll get there!)

You need to be able to open a file, write in it, save it, and close it -- all from the terminal. No mouse. No graphical text editor. Just you and the keyboard.

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
  GNU nano 6.2                    hello.txt







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
  GNU nano 6.2                    hello.txt                    Modified

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

You'll encounter vim eventually. It's incredibly powerful, used by many senior engineers, and is installed on virtually every Linux system. But vim has a famously steep learning curve because it works in "modes" -- you can't just open it and start typing.

We're not ignoring vim. We're saving it for when you have more context. Right now, nano gets the job done, and learning to walk before you run is how chefs train too.

When you're ready, vim will be there. For now, nano is your friend.

---

## Did You Know?

- **nano is a clone of a clone.** It was created as a free replacement for an editor called `pstrict` which was a replacement for `pstrict` ... actually, nano is a free replacement for `pico`, which was the editor built into the Pine email client from the 1990s. `nano` stands for "nano's ANOther editor" -- a recursive acronym, which is a nerdy tradition in programming.

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

---

## Quiz

1. **What does the `^` symbol mean in nano's menu?**
   <details>
   <summary>Answer</summary>
   The `^` symbol means the Ctrl key. So `^O` means "press Ctrl and O at the same time" and `^X` means "press Ctrl and X at the same time." This is nano's way of showing keyboard shortcuts.
   </details>

2. **How do you save a file in nano?**
   <details>
   <summary>Answer</summary>
   Press Ctrl+O (shown as ^O in nano's menu), then press Enter to confirm the file name. This writes the file to disk. The "Modified" indicator in the top bar will disappear once the file is saved.
   </details>

3. **What is a "shebang" and why do scripts need one?**
   <details>
   <summary>Answer</summary>
   A shebang is the `#!/bin/bash` line at the very top of a script. It tells the operating system which program should interpret and run the script. Without it, the system doesn't know whether to treat the file as a bash script, a Python script, or something else. The name comes from the "#!" characters: hash + bang = shebang.
   </details>

4. **What does `chmod +x` do, and why do you need it?**
   <details>
   <summary>Answer</summary>
   `chmod +x` adds execute permission to a file. By default, new text files are just data -- the system won't run them as programs. Adding execute permission tells the system "this file contains instructions that should be executed." Without it, you'll get a "Permission denied" error when trying to run the script.
   </details>

5. **What's the difference between `nano hello.txt` and `cat hello.txt`?**
   <details>
   <summary>Answer</summary>
   `nano hello.txt` opens the file in an interactive editor where you can modify the contents, save, and exit. `cat hello.txt` simply prints the file's contents to the terminal screen and immediately returns you to the prompt -- it's read-only, just for viewing. Use `cat` when you want to look, and `nano` when you want to change.
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

In [Module 0.7: Servers and SSH](module-0.7-servers-and-ssh.md), you'll learn what a server is and how to connect to one remotely. Everything you've learned so far -- commands, file editing, scripts -- works exactly the same on a remote server. The only difference is that you'll be controlling a kitchen in another building.

---

> **You just used a tool that senior engineers use every day. You belong here.**
