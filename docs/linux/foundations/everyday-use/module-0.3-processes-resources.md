# Module 0.3: Process & Resource Survival Guide

> **Everyday Use** | Complexity: `[QUICK]` | Time: 40 min

## Prerequisites

Before starting this module:
- **Required**: [Module 0.1: The CLI Power User](module-0.1-cli-power-user.md)
- **Helpful**: [Module 0.2: Environment & Permissions](module-0.2-environment-permissions.md)
- **Environment**: Any Linux system (VM, WSL, or native)

---

## Why This Module Matters

Your Linux machine is running dozens — sometimes hundreds — of programs right now, all at the same time. Your web browser, your terminal, your SSH session, that forgotten download script from two days ago. These running programs are called **processes**, and knowing how to find them, watch them, and stop them is one of the most important skills in DevOps.

Here is why:

- **Debugging starts with processes** — When something is slow or broken, the first question is always "what is running and how much is it eating?"
- **Servers do not fix themselves** — A runaway process eating 100% CPU at 3am will not politely stop. You need to know how to kill it
- **Disk space vanishes** — Containers, logs, and temp files will fill your disks. Knowing how to find what is eating space saves your production systems
- **Kubernetes runs processes** — Every container is a process. `kubectl exec`, pod termination, resource limits — they all map back to what you will learn here

Think of it this way: Module 0.1 taught you to navigate the house. This module teaches you to check who is home, what they are doing, and politely (or forcefully) ask them to leave.

---

## Did You Know?

- **Your system has a family tree of processes** — Every process has a parent. The very first process (PID 1) is the ancestor of everything else. When you open a terminal and run `ls`, your shell is the parent and `ls` is the child. Kill PID 1 and the entire system goes down. In Kubernetes, your app becomes PID 1 inside its container — which is why signal handling matters.

- **`kill` does not always kill** — Despite the name, the `kill` command actually sends *signals*. `kill` without options sends SIGTERM, which is more like a polite "please shut down." The process can ignore it entirely! Only `kill -9` (SIGKILL) is truly fatal, because the kernel handles it and the process never even sees it coming.

- **Linux invented "zombie" processes** — A zombie process is one that has finished running but is still hanging around in the process table because its parent has not picked up its exit status. Zombies use no CPU or memory — they are literally just a name in a list. But if thousands accumulate, you run out of process IDs and nothing new can start.

- **The `/proc` directory is a window into every process** — Each running process gets a folder at `/proc/<PID>/` full of live information. Want to know exactly what command started process 1234? Read `/proc/1234/cmdline`. Want its environment variables? `/proc/1234/environ`. This is not a log file — it is the kernel telling you what is happening right now.

---

## What Is a Process?

A **process** is simply a program that is currently running. When you type `ls` in your terminal, the `ls` program loads into memory, does its work, and exits. While it is running, it is a process.

Every process gets:

- **A PID** (Process ID) — a unique number that identifies it
- **A parent** (PPID) — the process that started it
- **Resources** — memory, CPU time, open files

Here is a simple analogy: a program on disk is like a recipe in a cookbook. A process is what happens when you actually start cooking — you have ingredients on the counter, pots on the stove, and timers running.

---

## Seeing What Is Running: `ps`

The `ps` command takes a snapshot of running processes — think of it as a photograph, not a video.

### Basic usage

```bash
# Show processes in your current terminal session
ps
```

Output looks like:

```
    PID TTY          TIME CMD
   1234 pts/0    00:00:00 bash
   5678 pts/0    00:00:00 ps
```

That is just your shell and the `ps` command itself. Not very exciting. To see everything:

### The all-powerful `ps aux`

```bash
# Show ALL processes from ALL users
ps aux
```

```
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.1 171584 13324 ?        Ss   Mar20   0:15 /sbin/init
root         2  0.0  0.0      0     0 ?        S    Mar20   0:00 [kthreadd]
www-data  1500  0.5  2.0 500000 40000 ?        S    Mar20   1:30 nginx: worker
you       3456  0.0  0.1  23456  5678 pts/0    Ss   10:00   0:00 -bash
```

Here is what each column means:

| Column | What It Tells You |
|--------|-------------------|
| USER | Who owns the process |
| PID | The process ID number |
| %CPU | How much CPU it is using right now |
| %MEM | How much memory it is using |
| VSZ | Virtual memory size (includes shared libraries — often misleadingly large) |
| RSS | Resident Set Size — actual physical memory used (the number you care about) |
| TTY | Which terminal it is attached to (`?` means it is a background service) |
| STAT | Process state (more on this below) |
| TIME | Total CPU time consumed |
| COMMAND | The command that started the process |

### Finding a specific process

Do not scroll through hundreds of lines. Filter:

```bash
# Find all processes with "nginx" in the name
ps aux | grep nginx

# Better: use pgrep (no grep noise in results)
pgrep -a nginx
```

### Understanding STAT codes

You will see letters in the STAT column:

| Code | Meaning |
|------|---------|
| S | Sleeping — waiting for something (most processes) |
| R | Running — actively using the CPU right now |
| T | Stopped — paused (you will learn how below) |
| Z | Zombie — finished but parent has not cleaned up |
| D | Disk sleep — waiting for I/O, cannot be interrupted |

A lowercase `s` after the state (like `Ss`) means it is a session leader, and `+` means it is in the foreground.

---

## Real-Time Monitoring: `top` and `htop`

While `ps` is a snapshot, `top` is a live dashboard that updates every few seconds.

### `top` basics

```bash
# Launch top
top
```

You will see something like:

```
top - 10:30:00 up 3 days,  2:15,  2 users,  load average: 0.52, 0.58, 0.59
Tasks: 143 total,   2 running, 140 sleeping,   0 stopped,   1 zombie
%Cpu(s):  5.0 us,  2.0 sy,  0.0 ni, 92.0 id,  1.0 wa,  0.0 hi,  0.0 si
MiB Mem :   7953.5 total,   2345.2 free,   3210.1 used,   2398.2 buff/cache
MiB Swap:   2048.0 total,   2048.0 free,      0.0 used.   4320.5 avail Mem

    PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
   1500 www-data  20   0  500000  40000   8192 S   5.0   2.0   1:30.00 nginx
   2100 mysql     20   0 1200000 300000  12000 S   3.0  15.0  12:45.00 mysqld
```

The top section gives you the system overview:

- **load average**: Three numbers (1-min, 5-min, 15-min). If these are higher than your CPU count, the system is overloaded. A 4-core machine with load average 4.0 is at capacity
- **Tasks**: How many processes exist and in which states
- **%Cpu**: `us` is user programs, `sy` is kernel, `id` is idle (idle is good!), `wa` is waiting for disk

**Useful keys while `top` is running:**

| Key | Action |
|-----|--------|
| `q` | Quit |
| `M` | Sort by memory usage |
| `P` | Sort by CPU usage |
| `k` | Kill a process (it will ask for the PID) |
| `1` | Toggle showing individual CPU cores |

### `htop` — the better `top`

`htop` is an improved version of `top` with colors, mouse support, and a much friendlier interface. It may not be installed by default:

```bash
# Install htop
# Debian/Ubuntu:
sudo apt install htop -y
# RHEL/Fedora:
sudo dnf install htop -y

# Run it
htop
```

Why `htop` is better for beginners:

- Color-coded CPU and memory bars at the top
- You can scroll through the process list with arrow keys
- Press `F5` to see a tree view (which process started which)
- Press `F9` to send a signal to a process
- Press `/` to search for a process by name
- Press `F6` to choose how to sort

For now, know that `htop` exists and try it. In your day-to-day work, most people reach for `htop` over `top`.

---

## Killing Processes: Signals, `kill`, and `killall`

Sometimes a process needs to stop. Maybe it is stuck, eating too much memory, or you just do not need it anymore. This is where signals come in.

### What are signals?

Signals are messages the operating system can deliver to a process. Think of them as tapping someone on the shoulder (SIGTERM) vs. physically dragging them out of the room (SIGKILL).

The two most important signals:

| Signal | Number | What Happens |
|--------|--------|-------------|
| SIGTERM | 15 | "Please shut down gracefully." The process receives this and can clean up — save files, close connections, finish writes. This is the polite way. |
| SIGKILL | 9 | "You are done. Now." The kernel terminates the process instantly. No cleanup, no saving, no last words. Use this only when SIGTERM fails. |

Other useful signals:

| Signal | Number | What Happens |
|--------|--------|-------------|
| SIGHUP | 1 | "Hangup" — many services reload their config when they receive this |
| SIGINT | 2 | Interrupt — this is what Ctrl+C sends |
| SIGSTOP | 19 | Pause the process (cannot be caught or ignored) |
| SIGCONT | 18 | Resume a paused process |

### Using `kill`

Despite the name, `kill` just sends a signal. By default, it sends SIGTERM:

```bash
# Send SIGTERM (the default — always try this first)
kill 1234

# Explicitly send SIGTERM
kill -15 1234
kill -TERM 1234

# Send SIGKILL (the nuclear option — use only if SIGTERM fails)
kill -9 1234
kill -KILL 1234

# Reload a service's config
kill -HUP 1234
```

### Using `killall` and `pkill`

If you know the process name but not the PID:

```bash
# Kill all processes named "nginx"
killall nginx

# Kill by partial name match
pkill sleep

# Kill all processes by a specific user
pkill -u username
```

### The golden rule: SIGTERM first, SIGKILL second

Always follow this order:

```
Step 1:  kill <PID>          # Sends SIGTERM — give it a few seconds
Step 2:  (wait 5 seconds)
Step 3:  kill -9 <PID>       # SIGKILL only if still running
```

Why? Because SIGTERM lets the process clean up. A database receiving SIGTERM can finish writing transactions and flush to disk. Hit it with SIGKILL and you might corrupt data.

This exact pattern happens in Kubernetes: when a pod is deleted, Kubernetes sends SIGTERM, waits 30 seconds (the `terminationGracePeriodSeconds`), and then sends SIGKILL if the process is still running.

---

## Background and Foreground Jobs

So far, every command you have run takes over your terminal until it finishes. But what if you want to run something that takes a long time and keep using your terminal?

### Running a command in the background with `&`

Add `&` at the end of any command:

```bash
# Run sleep in the background
sleep 300 &
# Output: [1] 12345
# [1] is the job number, 12345 is the PID
```

Your terminal is immediately available again. The process runs silently in the background.

### Checking background jobs with `jobs`

```bash
# See all background jobs in this terminal
jobs
# Output:
# [1]+  Running                 sleep 300 &
```

### Moving between foreground and background

```bash
# Start a long-running command
sleep 300

# Oh no, it is blocking my terminal! Press Ctrl+Z to PAUSE it
# Output: [1]+  Stopped                 sleep 300

# Now resume it in the BACKGROUND
bg
# Output: [1]+ sleep 300 &

# Or bring a background job back to the FOREGROUND
fg
# (Now sleep 300 is running in the foreground again)

# If you have multiple jobs, specify the job number
fg %1
bg %2
```

### Surviving terminal disconnects with `nohup`

Here is a trap that catches everyone at least once: you SSH into a server, start a long process, close your laptop, and the process dies. Why? Because when your terminal disconnects, it sends SIGHUP to all its child processes, which kills them.

`nohup` (short for "no hangup") prevents this:

```bash
# This will survive even if you disconnect from SSH
nohup ./long-running-script.sh &

# Output goes to nohup.out by default
# Redirect it if you prefer
nohup ./long-running-script.sh > /tmp/my-output.log 2>&1 &
```

A quick reference:

| Action | Command |
|--------|---------|
| Run in background | `command &` |
| List background jobs | `jobs` |
| Pause foreground process | `Ctrl+Z` |
| Resume in background | `bg` or `bg %N` |
| Bring to foreground | `fg` or `fg %N` |
| Survive disconnect | `nohup command &` |

---

## Disk Usage: Where Did All My Space Go?

Running out of disk space is one of the most common emergencies in DevOps. Logs grow, container images pile up, and temp files multiply. You need two tools: `df` to check overall disk space and `du` to find what is eating it.

### `df` — Disk Free (the big picture)

```bash
# Show disk usage in human-readable format
df -h
```

```
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   35G   13G  73% /
/dev/sda2       200G  180G   10G  95% /var
tmpfs           3.9G     0  3.9G   0% /dev/shm
```

The important columns:

| Column | Meaning |
|--------|---------|
| Size | Total size of the filesystem |
| Used | How much is consumed |
| Avail | How much is free |
| Use% | Percentage used — start worrying above 80%, panic above 95% |
| Mounted on | Where this filesystem is accessible in the directory tree |

In the example above, `/var` is at 95% — that is a problem waiting to happen. Logs are usually stored in `/var/log`, so this is extremely common on servers.

### `du` — Disk Usage (the detective)

`df` told you which disk is full. `du` helps you find which directories are the culprits:

```bash
# Show the size of the current directory
du -sh .

# Show sizes of immediate subdirectories, sorted by size
du -sh /* 2>/dev/null | sort -rh | head -10
```

```
15G     /var
8G      /usr
5G      /home
3G      /opt
1G      /tmp
```

Now drill down into the biggest offender:

```bash
# Dig into /var
du -sh /var/* 2>/dev/null | sort -rh | head -10
```

```
12G     /var/log
2G      /var/lib
500M    /var/cache
```

Found it! `/var/log` has 12GB. One more level:

```bash
du -sh /var/log/* 2>/dev/null | sort -rh | head -5
```

```
10G     /var/log/syslog.1
1.5G    /var/log/auth.log
500M    /var/log/kern.log
```

A 10GB rotated syslog. That is your culprit.

**The pattern**: Start wide with `df -h`, then drill down with `du -sh <dir>/* | sort -rh | head`.

### `lsblk` — List Block Devices

To see what physical disks and partitions exist on the system:

```bash
lsblk
```

```
NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
sda      8:0    0   50G  0 disk
├─sda1   8:1    0   49G  0 part /
└─sda2   8:2    0    1G  0 part [SWAP]
sdb      8:16   0  200G  0 disk
└─sdb1   8:17   0  200G  0 part /var
```

This shows you the physical layout: `sda` is a 50GB disk with two partitions, and `sdb` is a 200GB disk mounted at `/var`. This is useful when you need to understand why a particular mount point has limited space — it might be on a separate, smaller disk.

---

## Common Mistakes

| Mistake | Why It Is Bad | What To Do Instead |
|---------|---------------|-------------------|
| Using `kill -9` as the first option | Skips graceful shutdown — databases can corrupt, files can be half-written | Always try `kill <PID>` (SIGTERM) first, wait a few seconds, then `kill -9` only if needed |
| Forgetting `&` and Ctrl+C on a long task | Kills the process you actually wanted running | Use `Ctrl+Z` then `bg` to move it to the background without stopping it |
| Running `du -sh /` without `2>/dev/null` | Permission-denied errors flood your screen | Always pipe stderr: `du -sh /* 2>/dev/null \| sort -rh` |
| Ignoring `df` until the disk is 100% full | Services crash, logs stop writing, databases corrupt | Set up monitoring or check `df -h` regularly on servers |
| Using `nohup` but forgetting `&` | The command still runs in the foreground and blocks your terminal | Always combine them: `nohup command &` |
| Killing a process by PID without checking first | You might kill the wrong process if the PID was reused | Always run `ps -p <PID> -o cmd` first to confirm what you are about to kill |

---

## Quiz

### Question 1

What is the difference between `ps` and `top`?

<details>
<summary>Show Answer</summary>

`ps` takes a **snapshot** — it shows processes at a single moment in time and exits. `top` is a **live dashboard** that updates continuously (every few seconds by default).

Use `ps` when you need to filter or script. Use `top` or `htop` when you want to watch what is happening in real time.

</details>

### Question 2

You run `kill 5678` and the process is still running 10 seconds later. What happened, and what should you do next?

<details>
<summary>Show Answer</summary>

`kill` without a signal number sends **SIGTERM** (signal 15), which the process can catch and handle — or even ignore. If the process is stuck, ignoring signals, or in an uninterruptible state, SIGTERM will not work.

Your next step: send SIGKILL with `kill -9 5678`. This signal cannot be caught or ignored — the kernel terminates the process directly.

The only exception: processes in the `D` (uninterruptible sleep) state cannot be killed even with SIGKILL. Those usually indicate a storage or I/O problem that must be resolved at the system level.

</details>

### Question 3

You start a long backup script over SSH: `./backup.sh &`. You close your laptop and go home. When you check the server the next morning, the backup did not complete. What went wrong?

<details>
<summary>Show Answer</summary>

When your SSH session disconnected, the terminal sent **SIGHUP** to all its child processes, killing your backup script. Running a command with `&` only puts it in the background — it does not protect it from hangup signals.

The fix: use `nohup ./backup.sh &` — this tells the system to ignore SIGHUP for that process, so it survives disconnects. Alternatively, use tools like `tmux` or `screen` that keep sessions alive across disconnects.

</details>

### Question 4

A server is responding slowly. You run `df -h` and see that `/var` is at 98%. Describe the steps you would take to find and fix the problem.

<details>
<summary>Show Answer</summary>

Step-by-step:

1. **Find the biggest directories**: `du -sh /var/* 2>/dev/null | sort -rh | head -10`
2. **Drill down** into the largest directory (usually `/var/log`): `du -sh /var/log/* 2>/dev/null | sort -rh | head -10`
3. **Identify the culprit** — often a massive log file that was not rotated
4. **Fix it** — options include:
   - Truncate a huge log file: `> /var/log/huge-file.log` (empties it without deleting)
   - Remove old rotated logs: `rm /var/log/syslog.*.gz`
   - Clean package caches: `apt clean` or `dnf clean all`
5. **Prevent it** — ensure log rotation is configured properly (`/etc/logrotate.conf`)

Never just blindly delete files. Always check what they are first.

</details>

### Question 5

What does Ctrl+Z do, and how is it different from Ctrl+C?

<details>
<summary>Show Answer</summary>

- **Ctrl+C** sends **SIGINT** (signal 2), which tells the process to **terminate**. Most processes will stop and exit.
- **Ctrl+Z** sends **SIGTSTP** (signal 20), which **pauses** (suspends) the process. It is still alive, just frozen. You can resume it in the background with `bg` or in the foreground with `fg`.

Think of it this way: Ctrl+C kills the song. Ctrl+Z pauses it so you can resume later.

</details>

---

## Hands-On Exercise

### Process & Resource Scavenger Hunt

**Objective**: Practice finding, monitoring, and killing processes, plus investigating disk usage.

**Environment**: Any Linux system (VM, WSL, or native installation)

#### Part 1: Start a Background Process

```bash
# Start a sleep process in the background
sleep 600 &

# The shell tells you the job number and PID:
# [1] 12345

# Save the PID for later (your number will be different)
MY_PID=$!
echo "My background process PID is: $MY_PID"
```

#### Part 2: Find It with `ps`

```bash
# Find your sleep process using ps
ps aux | grep "sleep 600"

# Cleaner: use ps to show just that PID
ps -p $MY_PID -o pid,user,stat,cmd

# See it in the process tree
ps auxf | grep sleep
```

Verify that you can see the PID, that the STAT shows `S` (sleeping), and that the COMMAND is `sleep 600`.

#### Part 3: Watch It in `top`

```bash
# Launch top
top

# While top is running:
# 1. Press 'P' to sort by CPU
# 2. Press 'M' to sort by memory
# 3. Look for your sleep process (it will have near-zero CPU/MEM)
# 4. Press 'q' to quit
```

If you have `htop` installed, try that too — press `/` and type `sleep` to search for it.

#### Part 4: Kill It

```bash
# First, confirm the process is still running
ps -p $MY_PID -o pid,cmd

# Send SIGTERM (the polite way)
kill $MY_PID

# Verify it is gone
ps -p $MY_PID -o pid,cmd 2>/dev/null || echo "Process $MY_PID has been terminated."
```

If it were a stubborn process that did not respond to SIGTERM, you would follow up with `kill -9 $MY_PID`.

#### Part 5: Check Disk Space

```bash
# Get the big picture
df -h

# Find the largest directories at the root level
du -sh /* 2>/dev/null | sort -rh | head -10

# Drill into the largest directory (adjust path based on your output)
du -sh /var/* 2>/dev/null | sort -rh | head -5

# Check what physical disks and partitions exist
lsblk
```

#### Part 6: Bonus — Job Control

```bash
# Start three background sleeps
sleep 100 &
sleep 200 &
sleep 300 &

# List all jobs
jobs

# Bring the second one to the foreground
fg %2

# Pause it with Ctrl+Z
# Then resume it in the background
bg %2

# Kill all of them
killall sleep

# Verify they are all gone
jobs
```

### Success Criteria

- [ ] Started a background `sleep` process and noted its PID
- [ ] Found the process using `ps aux | grep` and confirmed its STAT code
- [ ] Opened `top` (or `htop`) and located the process in the list
- [ ] Killed the process with `kill` and verified it was gone with `ps`
- [ ] Ran `df -h` and identified which filesystem has the most usage
- [ ] Used `du -sh` to find the largest directory on the system
- [ ] (Bonus) Used `jobs`, `fg`, `bg`, and `killall` to manage multiple background jobs

---

## Next Module

You can find and kill processes, and you know where your disk space went. But who is managing all the services that start at boot — your web servers, databases, and schedulers? Time to learn about the system that orchestrates everything.

**Next**: [Module 0.4: Services & Logs Demystified](module-0.4-services-logs.md)
