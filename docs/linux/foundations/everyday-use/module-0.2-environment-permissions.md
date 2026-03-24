# Module 0.2: Environment & Permissions (Who You Are & Where You Are)

> **Everyday Use** | Complexity: `[QUICK]` | Time: 45 min

## Prerequisites

Before starting this module:
- **Required**: [Module 0.1: The CLI Power User](module-0.1-cli-power-user.md)
- **Environment**: Any Linux system (VM, WSL, or native)

---

## Why This Module Matters

Picture this. You download a script from a tutorial. You type `./deploy.sh`. The terminal spits back:

```
bash: ./deploy.sh: Permission denied
```

So you try again with `deploy.sh` (without the `./`). Now you get:

```
bash: deploy.sh: command not found
```

You stare at the screen. The file is *right there*. You can see it with `ls`. Why does Linux pretend it does not exist? And why, when you point directly at it, does Linux refuse to run it?

These two errors — "Permission denied" and "command not found" — are probably the most common frustrations for Linux beginners. They feel random and unfair. But they are not random at all. They come from two systems that are working exactly as designed:

1. **The Environment** — a collection of settings that tells your shell where to find programs, who you are, and how to behave
2. **Permissions** — a security system that controls who can read, write, and execute every single file on the system

Once you understand these two systems, those cryptic errors transform from brick walls into helpful signposts. You will know *exactly* what is wrong and *exactly* how to fix it. More importantly, when you start working with Kubernetes, you will understand why containers run as non-root, why ServiceAccounts exist, and why RBAC matters — because they are all built on these same permission concepts.

---

## Did You Know?

1. The `$PATH` variable was introduced in Unix Version 7 in 1979. Before that, you had to type the full path to every single command — imagine typing `/usr/bin/ls` every time you wanted to list files.

2. The numeric permission system (like `chmod 755`) is based on **octal** (base-8) numbers. Each digit represents three binary bits — one for read, one for write, one for execute. It is literally binary math you can do in your head.

3. The `sudo` command logs every single invocation to `/var/log/auth.log` (or `/var/log/secure` on RHEL-based systems). Your sysadmin can see exactly what you ran and when. There are no secrets with `sudo`.

4. On most Linux distributions, the root user's home directory is `/root`, not `/home/root`. Root is so special it does not even live in the same neighborhood as regular users.

---

## 1. Environment Variables: Your Terminal's Settings Panel

Think of environment variables like the **Settings app on your phone**. Your phone stores your language preference, your default browser, your wallpaper choice — all so that every app knows how to behave without asking you each time. Environment variables do the same thing for your terminal and every program that runs inside it.

An environment variable is simply a **name=value pair** stored in memory. By convention, the names use ALL_CAPS with underscores:

```bash
# See ALL your environment variables (there are a lot!)
env

# Or use printenv for the same thing
printenv

# See just one specific variable — the $ says "give me the value"
echo $USER
echo $HOME
```

### The Essential Variables You Should Know

| Variable | What It Stores | Example Value |
| :--- | :--- | :--- |
| `$USER` | Your current username | `alice` |
| `$HOME` | Path to your home directory | `/home/alice` |
| `$SHELL` | Your default shell program | `/bin/bash` |
| `$PWD` | Your current working directory | `/home/alice/projects` |
| `$EDITOR` | Your preferred text editor | `vim` or `nano` |
| `$LANG` | Your language and encoding | `en_US.UTF-8` |
| `$HOSTNAME` | The name of this machine | `web-server-01` |
| `$TERM` | Your terminal type | `xterm-256color` |
| `$PATH` | Where to find commands | (see next section) |

Try them right now:

```bash
echo "Hello, $USER! You are on $HOSTNAME."
echo "Your home is $HOME and your shell is $SHELL."
echo "You are currently in $PWD."
```

---

## 2. $PATH — The Most Important Variable You Will Ever Meet

When you type `ls` and press Enter, how does your shell know where the `ls` program lives? It does not search the entire hard drive — that would take forever. Instead, it checks a specific list of directories, in order, and runs the first match it finds. That list is your `$PATH`.

```bash
echo $PATH
```

You will see something like this (directories separated by colons):

```
/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/home/alice/bin
```

Here is how the shell uses it when you type a command:

```
You type: kubectl

Shell searches $PATH directories left to right:

  /usr/local/bin/kubectl  → does this exist? NO  → keep looking
  /usr/bin/kubectl        → does this exist? NO  → keep looking
  /bin/kubectl            → does this exist? NO  → keep looking
  /usr/sbin/kubectl       → does this exist? NO  → keep looking
  /sbin/kubectl           → does this exist? NO  → keep looking
  /home/alice/bin/kubectl → does this exist? YES → RUN IT!

If nothing found in any directory:
  → "bash: kubectl: command not found"
```

This is why `./deploy.sh` works but `deploy.sh` does not. The current directory (`.`) is **not** in your `$PATH` by default. When you type `deploy.sh`, the shell looks through every `$PATH` directory, never finds it, and gives up. When you type `./deploy.sh`, you are giving an explicit path — you are saying "run the file right here" — so the shell does not need `$PATH` at all.

### Finding Where Commands Live

```bash
# which — shows the full path of a command
which ls
# Output: /usr/bin/ls

which python3
# Output: /usr/bin/python3

# type — shows what the shell thinks a command is
type ls
# Output: ls is aliased to 'ls --color=auto'   (if aliased)
# Output: ls is /usr/bin/ls                      (if not)

type cd
# Output: cd is a shell builtin                  (built into bash itself)
```

### Adding a Directory to $PATH

Say you put custom scripts in `~/bin`. You need to add that directory to your `$PATH`:

```bash
# Temporary — lasts until you close the terminal
export PATH="$HOME/bin:$PATH"

# Verify it worked
echo $PATH
# Now /home/alice/bin appears at the front
```

Putting your directory at the **front** means your custom scripts get found first, before system commands with the same name. Putting it at the **end** means system commands take priority.

To make it permanent, add the `export PATH=...` line to your shell config file (covered in Section 4).

---

## 3. Setting Variables: `export` vs No `export`

This distinction trips up almost everyone. Watch carefully:

```bash
# Setting a variable WITHOUT export
GREETING="Hello from parent"
echo $GREETING        # Works! Prints: Hello from parent
bash                   # Start a child shell (a new process)
echo $GREETING        # Nothing! Empty! The child does not know about it
exit                   # Return to parent shell

# Setting a variable WITH export
export GREETING="Hello from parent"
echo $GREETING        # Works! Prints: Hello from parent
bash                   # Start a child shell
echo $GREETING        # Works! Prints: Hello from parent
exit                   # Return to parent shell
```

Why does this matter? Because every command you run is a **child process** of your shell. When you run a Python script, a Docker command, or kubectl, they are all child processes. If you set a variable without `export`, those programs cannot see it.

The rule is simple:

- **No `export`**: Variable exists only in your current shell session. Use this for quick throwaway values.
- **With `export`**: Variable is inherited by every child process. Use this for settings that programs need to see (like `$KUBECONFIG`, `$EDITOR`, `$JAVA_HOME`).

```bash
# Common exports you will see in Kubernetes work
export KUBECONFIG=~/.kube/config
export EDITOR=vim
export JAVA_HOME=/usr/lib/jvm/java-17

# Quick throwaway — no export needed
BACKUP_DATE=$(date +%Y-%m-%d)
echo "Backing up for $BACKUP_DATE"
```

### Unsetting Variables

```bash
# Remove a variable entirely
unset GREETING
echo $GREETING    # Nothing — it is gone
```

---

## 4. Shell Config Files: Making Changes Permanent

Every change you make in the terminal is **temporary** — it vanishes when you close the window. To make environment variables, aliases, and `$PATH` changes permanent, you need to add them to a **shell config file** that runs automatically when a new shell starts.

But which file? This is where it gets confusing, because there are several and they run at different times.

### When Each File Runs

```
┌──────────────────────────────────────────────────────────┐
│                   LOGIN SHELL                            │
│         (SSH session, first terminal on Linux)           │
│                                                          │
│   Runs: /etc/profile                                     │
│         → then the FIRST one found of:                   │
│           ~/.bash_profile                                │
│           ~/.bash_login                                  │
│           ~/.profile                                     │
│                                                          │
│   Think: "Welcome! Let me set up your entire session."   │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│               INTERACTIVE NON-LOGIN SHELL                │
│    (new terminal tab/window on desktop, typing bash)     │
│                                                          │
│   Runs: ~/.bashrc                                        │
│                                                          │
│   Think: "Just another shell, here are your shortcuts."  │
└──────────────────────────────────────────────────────────┘
```

In practice, most people want their settings in **every** shell. The standard trick is:

1. Put all your settings in `~/.bashrc`
2. Have `~/.bash_profile` source it:

```bash
# Contents of ~/.bash_profile
if [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi
```

This way, login shells load `.bashrc` too, and you only maintain one file.

**For Zsh users** (default on macOS): The equivalent is `~/.zshrc`. Zsh reads it for every interactive shell, login or not — much simpler.

### Reloading After Changes

After editing your config file, you do NOT need to close and reopen the terminal:

```bash
# Reload .bashrc immediately
source ~/.bashrc

# Shorthand (does the same thing)
. ~/.bashrc
```

---

## 5. Aliases: Your Custom Shortcut Commands

An alias is a custom shortcut that expands into a longer command. They save you keystrokes every single day.

```bash
# Create an alias
alias ll='ls -la'
alias ..='cd ..'
alias ...='cd ../..'
alias cls='clear'
alias ports='ss -tulnp'
alias myip='curl -s ifconfig.me'
```

### Practical Aliases for DevOps and Kubernetes

```bash
# Kubernetes — the k alias is used throughout KubeDojo
alias k='kubectl'
alias kgp='kubectl get pods'
alias kgs='kubectl get svc'
alias kgn='kubectl get nodes'
alias kaf='kubectl apply -f'
alias kdel='kubectl delete -f'
alias klog='kubectl logs -f'

# Docker
alias dps='docker ps'
alias dimg='docker images'
alias dex='docker exec -it'

# Safety nets — ask before overwriting
alias cp='cp -i'
alias mv='mv -i'
alias rm='rm -i'

# Quick system info
alias meminfo='free -h'
alias diskinfo='df -h'
alias cpuinfo='lscpu'
```

To make aliases permanent, add them to your `~/.bashrc`:

```bash
# Open your .bashrc and add aliases at the bottom
nano ~/.bashrc

# After adding aliases, reload
source ~/.bashrc
```

### Checking and Removing Aliases

```bash
# See all your current aliases
alias

# See what a specific alias expands to
alias ll
# Output: alias ll='ls -la'

# Temporarily bypass an alias (use the real command)
\ls          # The backslash skips the alias
command ls   # Another way to skip

# Remove an alias for this session
unalias ll
```

---

## 6. File Permissions: The rwx System

Linux is a **multi-user** operating system. Even if you are the only human using the machine, there are dozens of system users (like `www-data` for your web server, `postgres` for your database). Permissions ensure that your web server cannot read your SSH keys and your database cannot modify your application code.

Run `ls -l` in any directory:

```bash
ls -l /etc/passwd /bin/ls /home

# Output looks like:
# -rwxr-xr-x 1 root root  142144 Sep 5 2023 /bin/ls
# -rw-r--r-- 1 root root    2775 Mar 10 14:22 /etc/passwd
# drwxr-xr-x 3 root root    4096 Mar 10 14:22 /home
```

Let us decode that first column character by character:

```
 -  r  w  x  r  -  x  r  -  x
 │  │  │  │  │  │  │  │  │  │
 │  └──┴──┘  └──┴──┘  └──┴──┘
 │     │        │        │
 │   OWNER    GROUP    OTHERS
 │  (user)
 │
 └── File type
     - = regular file
     d = directory
     l = symbolic link
```

### What r, w, x Actually Mean

| Permission | On a File | On a Directory |
| :--- | :--- | :--- |
| `r` (read) | View the file contents (`cat`, `less`) | List the directory contents (`ls`) |
| `w` (write) | Modify or overwrite the file | Create, rename, or delete files inside it |
| `x` (execute) | Run the file as a program | Enter the directory (`cd`) |
| `-` (none) | Cannot do the action | Cannot do the action |

The directory permissions catch people off guard. A directory without `x` is like a room with a locked door — you cannot walk in, even if you know what is inside. A directory without `r` but with `x` is like a dark room — you can walk in and grab files if you know their names, but you cannot turn on the lights to see what is there.

### Reading Permission Strings — Practice

| String | Owner | Group | Others | Meaning |
| :--- | :--- | :--- | :--- | :--- |
| `-rwxr-xr-x` | rwx | r-x | r-x | Typical program — everyone can run it, only owner can edit |
| `-rw-r--r--` | rw- | r-- | r-- | Typical config file — everyone can read, only owner can edit |
| `-rw-------` | rw- | --- | --- | Private file — only owner can read and write |
| `-rwx------` | rwx | --- | --- | Private script — only owner can run it |
| `drwxr-xr-x` | rwx | r-x | r-x | Typical directory — everyone can enter and list, only owner can modify |
| `drwx------` | rwx | --- | --- | Private directory — only owner can enter |

---

## 7. Changing Permissions with `chmod`

`chmod` (change mode) modifies permissions. You can use it in two ways.

### Symbolic Mode — Human-Readable

Format: `chmod [who][operator][permission] file`

- **Who**: `u` (user/owner), `g` (group), `o` (others), `a` (all three)
- **Operator**: `+` (add), `-` (remove), `=` (set exactly)
- **Permission**: `r`, `w`, `x`

```bash
# Make a script executable for the owner
chmod u+x deploy.sh

# Remove write permission from group and others
chmod go-w config.yaml

# Give everyone read permission
chmod a+r README.md

# Set exact permissions — owner gets rwx, everyone else gets nothing
chmod u=rwx,go= secret-script.sh

# Add execute for everyone
chmod +x run-tests.sh        # Without specifying who, + applies to all

# Remove all permissions from others
chmod o= private-notes.txt   # = with nothing after it means "set to nothing"
```

### Numeric Mode — Fast and Precise

Each permission has a number: **read = 4, write = 2, execute = 1**. Add them up for each position (owner, group, others).

```
Permission  Binary  Decimal
---------   -----   -------
  ---        000       0     (no permissions)
  --x        001       1     (execute only)
  -w-        010       2     (write only)
  -wx        011       3     (write + execute)
  r--        100       4     (read only)
  r-x        101       5     (read + execute)
  rw-        110       6     (read + write)
  rwx        111       7     (read + write + execute)
```

You specify three digits: owner, group, others.

```bash
# 755 — owner: rwx (7), group: r-x (5), others: r-x (5)
# Standard for scripts and programs
chmod 755 deploy.sh

# 644 — owner: rw- (6), group: r-- (4), others: r-- (4)
# Standard for regular files
chmod 644 config.yaml

# 600 — owner: rw- (6), group: --- (0), others: --- (0)
# Private files (SSH keys, passwords)
chmod 600 ~/.ssh/id_rsa

# 700 — owner: rwx (7), group: --- (0), others: --- (0)
# Private directories, private scripts
chmod 700 ~/.ssh

# 444 — owner: r-- (4), group: r-- (4), others: r-- (4)
# Read-only for everyone (like a museum exhibit — look but do not touch)
chmod 444 important-record.txt
```

### The Most Common Permission Patterns

| Pattern | Numeric | Use Case |
| :--- | :--- | :--- |
| `rwxr-xr-x` | `755` | Programs, scripts, directories |
| `rw-r--r--` | `644` | Regular files, config files |
| `rw-------` | `600` | SSH private keys, secrets |
| `rwx------` | `700` | SSH directory, private scripts |
| `rwxrwxr-x` | `775` | Shared project directories |
| `rw-rw-r--` | `664` | Shared project files |

---

## 8. Ownership with `chown` and `chgrp`

Every file has two ownership attributes: a **user** (owner) and a **group**.

```bash
# Check ownership
ls -l myfile.txt
# -rw-r--r-- 1 alice developers 1024 Mar 10 14:22 myfile.txt
#               ^^^^^  ^^^^^^^^^^
#               owner    group
```

### Changing Ownership

```bash
# Change owner (requires sudo because you are giving away a file)
sudo chown bob myfile.txt

# Change group only
sudo chgrp developers myfile.txt

# Change both at once — user:group
sudo chown bob:developers myfile.txt

# Change ownership of a directory and EVERYTHING inside it (-R = recursive)
sudo chown -R alice:webteam /var/www/mysite

# Change only the group (useful if you are a member of the target group)
chgrp devops deployment.yaml     # No sudo needed if you belong to "devops"
```

### Why Ownership Matters for Kubernetes

When a container runs, it runs as a specific user (often root by default, which is a security risk). Kubernetes `securityContext` lets you set `runAsUser` and `runAsGroup` — the exact same user/group ownership concept you are learning here, just applied inside a container.

---

## 9. The Root User and `sudo`

### Root: The All-Powerful Superuser

Linux has one special user called `root` (UID 0). Root can:

- Read, write, and execute any file regardless of permissions
- Kill any process
- Modify any system configuration
- Bind to privileged ports (below 1024)
- Format disks, mount filesystems, do absolutely anything

This is why running as root is **dangerous**. A typo like `rm -rf /` (instead of `rm -rf ./`) would wipe the entire system. There is no "Are you sure?" prompt, no recycle bin, no undo.

### sudo: Borrow Root Power Safely

`sudo` stands for "superuser do." It lets an authorized regular user run a single command with root privileges:

```bash
# Install a package (requires root)
sudo apt update
sudo apt install nginx

# Edit a system file (requires root)
sudo nano /etc/hosts

# Restart a service (requires root)
sudo systemctl restart nginx

# See who you become when you use sudo
sudo whoami
# Output: root
```

When you run `sudo`, it asks for **your** password (not root's password). This confirms that the person at the keyboard is actually you and not someone who walked up to your unlocked laptop.

### The sudoers File

Not everyone can use `sudo`. The file `/etc/sudoers` controls who is allowed. You should **never** edit it directly — always use the special `visudo` command, which checks for syntax errors before saving (a broken sudoers file can lock you out of root access entirely).

```bash
# See your sudo privileges
sudo -l

# Common output shows something like:
# (ALL : ALL) ALL         — you can do anything as any user
# (ALL) NOPASSWD: ALL     — you can do anything without a password (common on cloud VMs)
```

On most systems, you get sudo access by being in a specific group:

- **Ubuntu/Debian**: The `sudo` group
- **RHEL/CentOS/Fedora**: The `wheel` group

```bash
# Check what groups you belong to
groups
# Output: alice sudo docker

# If "sudo" or "wheel" is in the list, you can use sudo
```

### Best Practices with sudo

```bash
# DO: Use sudo for specific commands that need it
sudo systemctl restart nginx

# DO NOT: Start a root shell and work in it
sudo -i        # Avoid this — you lose the safety net of per-command authorization
sudo su -      # Avoid this too — same problem

# DO NOT: Use sudo for things that do not need it
sudo cat myfile.txt    # If you own the file, just use cat!
sudo vim notes.txt     # The file will end up owned by root — now YOU cannot edit it
```

**War Story**: A junior engineer once ran `sudo vim` to edit a config file in their home directory. The file's ownership changed to root. Later, the application that needed to read that config file (running as a normal user) got "Permission denied" and crashed in production. The fix was a simple `chown`, but finding the cause took hours of debugging. The lesson: only use `sudo` when you actually need root privileges.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| "command not found" for a script in the current directory | The current directory `.` is not in `$PATH`. Typing `script.sh` makes the shell search `$PATH` only. | Run it with `./script.sh` (explicit path) or add its directory to `$PATH`. |
| "Permission denied" when running a script | The file does not have execute (`x`) permission. Linux requires it explicitly. | Run `chmod u+x script.sh` then try again. |
| Alias disappears after closing the terminal | You defined it in the shell but not in `~/.bashrc`. Shell settings do not persist automatically. | Add the `alias` line to `~/.bashrc` and run `source ~/.bashrc`. |
| `export` in `.bashrc` does not take effect | You edited the file but did not reload it. The running shell does not watch for file changes. | Run `source ~/.bashrc` or open a new terminal. |
| Using `sudo vim` to edit files you own | Creates the file as root-owned. Now your normal user cannot modify it. | Use `vim` without `sudo`. If already owned by root, run `sudo chown $USER file`. |
| Running as root all the time (`sudo su -`) | Feels convenient but removes all safety nets. One wrong `rm` can destroy everything. | Use `sudo` per command. Exit root shells immediately when done. |
| `chmod 777` on everything to "fix" permission errors | Gives everyone full access — a massive security hole. | Figure out which specific permission is missing and grant only that. Usually `chmod 755` or `644` is correct. |
| Forgetting the `-R` flag with `chown` or `chmod` | Only changes the directory itself, not the files inside it. | Use `-R` for recursive: `sudo chown -R alice:devs /project`. |

---

## Quiz

**Test yourself.** Try to answer before revealing the solution.

<details>
<summary>1. What does the $PATH variable do?</summary>

`$PATH` is a colon-separated list of directories. When you type a command name, the shell searches these directories from left to right to find the program to execute. If the command is not found in any `$PATH` directory, you get "command not found."
</details>

<details>
<summary>2. What is the difference between setting a variable with and without `export`?</summary>

Without `export`, the variable exists only in the current shell. With `export`, the variable is passed to all child processes (every command or script you run). Use `export` when programs need to see the variable (like `$KUBECONFIG`).
</details>

<details>
<summary>3. You see `-rwxr--r--` on a file. Who can execute it?</summary>

Only the **owner** (user) can execute it. The group has `r--` (read only) and others have `r--` (read only). Neither group nor others have the `x` bit.
</details>

<details>
<summary>4. What is the numeric chmod equivalent of rwxr-xr-x?</summary>

**755**. Owner: r(4)+w(2)+x(1)=7. Group: r(4)+x(1)=5. Others: r(4)+x(1)=5.
</details>

<details>
<summary>5. Why should you NOT use `chmod 777` to fix permission errors?</summary>

`chmod 777` gives read, write, and execute permissions to every user on the system. This is a serious security risk — any user or process could read, modify, or execute the file. Instead, determine what specific permission is needed and grant only that. For scripts, `755` is usually correct. For regular files, `644`. For private files, `600`.
</details>

<details>
<summary>6. What is the difference between ~/.bashrc and ~/.bash_profile?</summary>

`~/.bash_profile` runs for **login shells** (SSH sessions, first console login). `~/.bashrc` runs for **interactive non-login shells** (new terminal tabs, typing `bash`). Best practice is to put your settings in `~/.bashrc` and have `~/.bash_profile` source it, so you get the same config everywhere.
</details>

<details>
<summary>7. You run `sudo vim config.yaml` and later your app cannot read the file. What happened?</summary>

`sudo vim` created or saved the file as root (owner: root, group: root). Your application runs as a normal user and no longer has permission to read it. Fix it with `sudo chown $USER config.yaml`. Lesson: do not use `sudo` with editors unless you are editing system files.
</details>

<details>
<summary>8. A directory has permissions `drwxr-x---`. Can a user who belongs to the group list files in it? Can they create new files?</summary>

The group has `r-x`: they can **list** files (`r`) and **enter** the directory (`x`). But they cannot **create** new files because they do not have write (`w`) permission. Only the owner (who has `rwx`) can create, rename, or delete files inside.
</details>

---

## Hands-On Exercise: Environment and Permissions Boot Camp

**Scenario**: You are setting up a development environment on a new server. You need to configure your shell, create a project with proper permissions, and set up scripts that your team can use.

### Part 1: Environment Variables

```bash
# 1. Display your current username, home directory, and shell
echo "User: $USER"
echo "Home: $HOME"
echo "Shell: $SHELL"

# 2. See your entire $PATH, one directory per line (easier to read)
echo $PATH | tr ':' '\n'

# 3. Set a variable WITHOUT export — verify it does not reach child processes
PROJECT_NAME="kubedojo-lab"
echo $PROJECT_NAME         # Should print: kubedojo-lab
bash -c 'echo $PROJECT_NAME'   # Should print nothing (empty)

# 4. Now export it and verify the child process CAN see it
export PROJECT_NAME="kubedojo-lab"
bash -c 'echo $PROJECT_NAME'   # Should print: kubedojo-lab
```

### Part 2: Shell Configuration

```bash
# 5. Add useful aliases to your .bashrc
cat >> ~/.bashrc << 'EOF'

# --- KubeDojo Lab Aliases ---
alias ll='ls -la'
alias cls='clear'
alias ..='cd ..'
alias k='kubectl'
EOF

# 6. Reload your config and test
source ~/.bashrc
ll       # Should show detailed listing with hidden files
```

### Part 3: Permissions

```bash
# 7. Create a project directory structure
mkdir -p ~/lab-project/{scripts,config,secrets}

# 8. Create a deploy script
cat > ~/lab-project/scripts/deploy.sh << 'EOF'
#!/bin/bash
echo "Deploying $PROJECT_NAME..."
echo "Deploy complete at $(date)"
EOF

# 9. Try to run it — observe the error
~/lab-project/scripts/deploy.sh
# Expected: Permission denied

# 10. Check current permissions
ls -l ~/lab-project/scripts/deploy.sh
# Expected: -rw-r--r-- or -rw-rw-r-- (no x anywhere)

# 11. Add execute permission for the owner only
chmod u+x ~/lab-project/scripts/deploy.sh

# 12. Verify the permission changed
ls -l ~/lab-project/scripts/deploy.sh
# Expected: -rwxr--r-- (x added for owner)

# 13. Run it successfully
~/lab-project/scripts/deploy.sh
# Expected: "Deploying kubedojo-lab..." and timestamp
```

### Part 4: Securing Files

```bash
# 14. Create a "secret" config file
echo "DB_PASSWORD=supersecret123" > ~/lab-project/secrets/db.env

# 15. Lock it down — only you can read and write (numeric mode)
chmod 600 ~/lab-project/secrets/db.env

# 16. Verify
ls -l ~/lab-project/secrets/db.env
# Expected: -rw------- (only owner has rw)

# 17. Set the secrets directory so only you can enter it
chmod 700 ~/lab-project/secrets/

# 18. Verify the full structure
ls -la ~/lab-project/
ls -la ~/lab-project/scripts/
ls -la ~/lab-project/secrets/
```

### Success Criteria

You have completed this exercise successfully if:

- [ ] You can explain what `$PATH` does and why `./script.sh` works but `script.sh` does not
- [ ] Your aliases are saved in `~/.bashrc` and persist after running `source ~/.bashrc`
- [ ] `deploy.sh` has execute permission for the owner (`-rwxr--r--` or similar)
- [ ] `db.env` is locked down to owner-only access (`-rw-------` / `600`)
- [ ] The `secrets/` directory is locked to owner-only (`drwx------` / `700`)
- [ ] You did not use `sudo` for anything in this exercise (you should not need it for files you own)

### Cleanup

```bash
# When you are done experimenting
rm -rf ~/lab-project
# Optionally remove the aliases from ~/.bashrc if you do not want them
```

---

**Next Up:** [Module 0.3: Process & Resource Survival Guide](module-0.3-processes-resources.md) — Learn how to find running processes, monitor system resources, and stop runaway programs before they cause trouble.
