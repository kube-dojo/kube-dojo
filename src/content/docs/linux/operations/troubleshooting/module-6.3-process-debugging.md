---
title: "Module 6.3: Process Debugging"
slug: linux/operations/troubleshooting/module-6.3-process-debugging
sidebar:
  order: 4
lab:
  id: linux-6.3-process-debugging
  url: https://killercoda.com/kubedojo/scenario/linux-6.3-process-debugging
  duration: "35 min"
  difficulty: advanced
  environment: ubuntu
---
> **Linux Troubleshooting** | Complexity: `[COMPLEX]` | Time: 30-35 min

## Prerequisites

Before starting this module:
- **Required**: [Module 1.2: Processes & Systemd](../../foundations/system-essentials/module-1.2-processes-systemd/)
- **Required**: [Module 6.2: Log Analysis](../module-6.2-log-analysis/)
- **Helpful**: Understanding of system calls

---

## What You'll Be Able to Do

After this module, you will be able to:
- **Diagnose** process hangs, crashes, and resource leaks using strace, lsof, and /proc
- **Trace** system calls to understand what a process is actually doing
- **Identify** file descriptor leaks, zombie processes, and stuck I/O operations
- **Debug** container processes by entering their namespace with nsenter

---

## Why This Module Matters

When logs don't tell the whole story, you need to look deeper. Process debugging lets you see exactly what a program is doing: what files it opens, what system calls it makes, and where it's stuck.

Understanding process debugging helps you:

- **Debug black boxes** — See inside programs without source code
- **Find what's blocking** — Why is this process stuck?
- **Trace failures** — What call failed and why?
- **Understand behavior** — What does this process actually do?

Sometimes the only way to understand a problem is to watch the process in action.

---

## Did You Know?

- **strace intercepts system calls** — Every interaction with the kernel (file I/O, network, process control) goes through system calls. strace shows all of them.

- **/proc is a goldmine** — Every process has a virtual directory under /proc with detailed information: file descriptors, memory maps, environment, limits.

- **Processes have over 400 system calls available** — From `read` and `write` to `clone` and `epoll_wait`. Most programs use only 20-30.

- **strace can slow programs 100x** — The overhead of intercepting every system call is significant. Use selectively in production.

---

## The /proc Filesystem

> **Stop and think**: If an application binary is accidentally deleted from the disk while the process is still running, how might you use the `/proc` filesystem to recover the executable?

### Process Information

```bash
# Every process has a directory
ls /proc/1/  # PID 1 (init/systemd)

# Key files:
# cmdline  - Command and arguments
# cwd      - Current working directory (symlink)
# environ  - Environment variables
# exe      - Executable (symlink)
# fd/      - File descriptors
# limits   - Resource limits
# maps     - Memory mappings
# stat     - Process status
# status   - Human-readable status
```

### Examining a Process

```bash
# Get PID
PID=$(pgrep nginx | head -1)

# Command line
cat /proc/$PID/cmdline | tr '\0' ' '
# nginx: master process /usr/sbin/nginx

# Working directory
ls -l /proc/$PID/cwd
# lrwxrwxrwx 1 root root 0 Jan 15 10:00 /proc/1234/cwd -> /

# Executable
ls -l /proc/$PID/exe
# lrwxrwxrwx 1 root root 0 Jan 15 10:00 /proc/1234/exe -> /usr/sbin/nginx

# Environment
cat /proc/$PID/environ | tr '\0' '\n'
# PATH=/usr/local/sbin:/usr/local/bin:...
# LANG=en_US.UTF-8
```

### File Descriptors

```bash
# List open file descriptors
ls -l /proc/$PID/fd/
# lrwx------ 1 root root 64 Jan 15 10:00 0 -> /dev/null
# lrwx------ 1 root root 64 Jan 15 10:00 1 -> /var/log/nginx/access.log
# lrwx------ 1 root root 64 Jan 15 10:00 2 -> /var/log/nginx/error.log
# lrwx------ 1 root root 64 Jan 15 10:00 3 -> socket:[12345]

# Count open files
ls /proc/$PID/fd/ | wc -l

# File descriptor info
cat /proc/$PID/fdinfo/3
# pos:    0
# flags:  02
# mnt_id: 28
```

### Resource Limits

```bash
# View limits
cat /proc/$PID/limits
# Limit                     Soft Limit           Hard Limit           Units
# Max open files            1024                 1048576              files
# Max processes             30000                30000                processes
# Max file size             unlimited            unlimited            bytes
```

### Memory Maps

```bash
# Memory layout
cat /proc/$PID/maps | head -20
# 55d7f8a00000-55d7f8a02000 r--p 00000000 08:01 123456 /usr/sbin/nginx
# 55d7f8a02000-55d7f8a50000 r-xp 00002000 08:01 123456 /usr/sbin/nginx
# 7f8b1234000-7f8b1235000 rw-p 00000000 00:00 0      [heap]

# Memory summary
cat /proc/$PID/status | grep -E "VmSize|VmRSS|VmSwap"
# VmSize:   234567 kB
# VmRSS:    12345 kB
# VmSwap:   0 kB
```

---

## strace

> **Pause and predict**: If you run `strace ls /tmp`, will the actual output of the `ls` command be printed before, during, or after the `strace` output?

### Basic Usage

```bash
# Trace a command
strace ls /tmp
# execve("/bin/ls", ["ls", "/tmp"], 0x7fff...) = 0
# ...
# openat(AT_FDCWD, "/tmp", O_RDONLY|O_NONBLOCK|O_DIRECTORY) = 3
# ...

# Attach to running process
strace -p 1234

# Detach with Ctrl+C

# Trace with timestamps
strace -t ls /tmp        # HH:MM:SS
strace -tt ls /tmp       # HH:MM:SS.microseconds
strace -r ls /tmp        # Relative time since last call
```

### Filtering System Calls

```bash
# Only file operations
strace -e trace=file ls /tmp

# Only network operations
strace -e trace=network curl google.com

# Only process operations
strace -e trace=process bash -c "ls"

# Categories:
# file    - open, stat, chmod, unlink, rename, ...
# network - socket, connect, accept, send, recv, ...
# process - fork, clone, execve, exit, wait, ...
# signal  - signal, sigaction, kill, ...
# ipc     - shmget, semget, msgget, ...
# memory  - mmap, mprotect, brk, ...

# Specific calls
strace -e open,read,write cat /etc/passwd
```

### Output and Formatting

```bash
# Write to file
strace -o /tmp/trace.log ls /tmp

# Include child processes
strace -f bash -c "ls | grep foo"

# Limit string length (default 32)
strace -s 200 cat /etc/passwd

# Summarize calls
strace -c ls /tmp
# % time     seconds  usecs/call     calls    errors syscall
# ------ ----------- ----------- --------- --------- ----------------
#  40.00    0.000004           4         1           write
#  30.00    0.000003           0        10           read
#  ...

# Print only errors
strace -Z ls /nonexistent 2>&1 | head
```

### Common Patterns

```bash
# What files does it open?
strace -e openat,open ls 2>&1 | grep -v ENOENT

# What's it connecting to?
strace -e connect nginx 2>&1

# Why is it slow?
strace -tt -T curl -s http://example.com 2>&1 | tail
# -T shows time spent in each call

# What config is it reading?
strace -e openat myapp 2>&1 | grep -E "\.conf|\.cfg|\.yaml"
```

---

## Process States

> **Stop and think**: Why is it impossible to forcefully terminate (`kill -9`) a process that is currently in the 'D' (Uninterruptible sleep) state?

### Understanding States

```bash
ps aux
# USER  PID %CPU %MEM   VSZ   RSS TTY STAT START TIME COMMAND
# root    1  0.0  0.1 12345  6789 ?   Ss   Jan15 0:01 /sbin/init

# STAT column meanings:
# S  Sleeping (waiting for event)
# R  Running or runnable
# D  Uninterruptible sleep (usually I/O)
# Z  Zombie (finished but not reaped)
# T  Stopped (by signal or debugger)
# I  Idle kernel thread
```

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROCESS STATES                                │
│                                                                  │
│  ┌──────────┐     schedule      ┌──────────┐                    │
│  │ RUNNING  │◄──────────────────│ RUNNABLE │                    │
│  │   (R)    │                   │   (R)    │                    │
│  └────┬─────┘                   └────▲─────┘                    │
│       │                              │                          │
│       │ wait for event               │ event occurred           │
│       ▼                              │                          │
│  ┌──────────┐                   ┌────┴─────┐                    │
│  │ SLEEPING │──────────────────▶│ WAKING   │                    │
│  │   (S)    │                   │          │                    │
│  └──────────┘                   └──────────┘                    │
│                                                                  │
│  Special states:                                                 │
│  D = Uninterruptible (can't be killed, waiting for I/O)        │
│  Z = Zombie (exited but parent hasn't called wait())           │
│  T = Stopped (SIGSTOP or debugger)                             │
└─────────────────────────────────────────────────────────────────┘
```

### Finding Problem States

```bash
# Find D state (stuck in I/O)
ps aux | awk '$8 ~ /D/ {print}'

# Find zombies
ps aux | awk '$8 ~ /Z/ {print}'

# Or
ps -eo pid,ppid,stat,comm | grep -E "^|Z"

# Count by state
ps -eo stat | sort | uniq -c | sort -rn
```

---

## Debugging Stuck Processes

### Process Hanging?

```bash
# 1. Check what state it's in
ps -o pid,stat,wchan -p $PID
# WCHAN = kernel function where it's waiting

# 2. Check what it's waiting for
cat /proc/$PID/stack
# Shows kernel stack trace

# 3. Check open files/sockets
ls -l /proc/$PID/fd/
lsof -p $PID

# 4. Attach strace
sudo strace -p $PID
# See what call it's stuck on
```

### Process Using Too Much CPU?

```bash
# 1. Identify process
top -p $PID

# 2. What's it doing?
strace -c -p $PID
# Ctrl+C after a few seconds
# Shows breakdown of time spent

# 3. Profile (if perf available)
sudo perf top -p $PID
```

### Process Using Too Much Memory?

```bash
# 1. Check memory
cat /proc/$PID/status | grep -E "Vm|Mem"

# 2. Memory map
cat /proc/$PID/smaps_rollup

# 3. Heap analysis (if heap dump supported)
# Depends on application (Java: jmap, Python: tracemalloc)
```

---

## lsof

### List Open Files

```bash
# All open files by process
lsof -p $PID

# Who has a file open?
lsof /var/log/syslog

# Who's using a port?
lsof -i :80

# Network connections
lsof -i -P -n
# -P = numeric ports
# -n = numeric hosts

# Deleted but held files
lsof | grep deleted
# Common cause of "disk full" when df shows space
```

### Common Patterns

```bash
# Files open by user
lsof -u username

# Files in a directory
lsof +D /var/log/

# TCP connections to host
lsof -i @192.168.1.1

# What's preventing unmount?
lsof /mnt/point
```

---

## ltrace

### Library Calls

```bash
# Trace library calls (not system calls)
ltrace ls /tmp

# Output shows:
# strlen("tmp")  = 3
# malloc(4096)   = 0x55555556a2a0
# ...

# Compare with strace
# strace  = kernel interface (syscalls)
# ltrace  = library interface (libc, etc.)

# Filter by library
ltrace -l libc.so.6 ls /tmp
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| strace in production | Major performance hit | Use -p briefly, filter with -e |
| Ignoring D state | Process waiting for I/O | Check disk, NFS, network storage |
| Not checking parent | Zombie's parent should reap | Find PPID, fix parent process |
| Missing file descriptors | Process can't open files | Check limits, leaked FDs |
| Over-tracing | Too much output | Filter with -e option |
| Forgetting -f | Miss child processes | Use -f to follow forks |

---

## Quiz

### Question 1
An application team reports that their Node.js service is crashing with a "Too many open files" error. You have the PID of the running Node.js process. How would you investigate which specific files and connections the process currently holds open to find the leak?

<details>
<summary>Show Answer</summary>

You can investigate the open file descriptors using multiple methods, depending on the level of detail you need. Exploring the `/proc` filesystem is the fastest approach because it directly queries the kernel's data structures in memory without invoking external binaries that parse complex states. Alternatively, `lsof` provides a much richer, formatted output that maps file descriptors to actual file paths, network sockets, and pipes, making it easier for humans to read. If you suspect the process is actively opening files in a loop right now, attaching `strace` allows you to monitor the real-time file opening behavior as it happens.

```bash
# 1. /proc filesystem
ls -l /proc/$PID/fd/

# 2. lsof
lsof -p $PID

# 3. strace (for new opens)
strace -e openat -p $PID
```

`/proc/$PID/fd/` is fastest and doesn't affect the process. `lsof` gives more detail. `strace` shows new file operations in real-time.

</details>

### Question 2
You are troubleshooting a legacy database server that is suddenly unresponsive. When you run `ps aux`, you notice several critical processes are stuck in the 'D' state. The system load average is extremely high, but CPU usage is near 0%. What does this state indicate about the root cause, and how should you proceed?

<details>
<summary>Show Answer</summary>

The 'D' state indicates **Uninterruptible sleep** — meaning the process is waiting for an I/O operation to complete and cannot be interrupted, not even by a `SIGKILL` (kill -9) signal. This state is designed to protect data integrity, ensuring a process doesn't terminate halfway through writing to hardware. Because the process is asleep, it doesn't consume CPU cycles, which explains the near 0% CPU usage despite a skyrocketing load average (which counts processes waiting for I/O). The root cause is almost always hardware-related, such as a failing physical disk, a disconnected NFS mount, or an overloaded storage array.

Common causes:
- Waiting for disk I/O
- Waiting for NFS or network filesystem
- Hardware problems

Characteristics:
- Cannot be killed with SIGKILL
- Will complete when I/O finishes (or times out)
- Many D state processes = I/O subsystem problem

Check:
```bash
ps aux | awk '$8 ~ /D/'
cat /proc/$PID/stack  # See kernel function
```

</details>

### Question 3
A custom proxy application is failing to connect to an external API, but it doesn't log any useful error messages. You decide to use `strace` on the running process to see what's happening. The process is extremely busy doing file I/O, so a standard `strace` generates too much noise. How can you isolate only the network connection attempts?

<details>
<summary>Show Answer</summary>

You can isolate network activity by passing the `-e trace=network` filter or specifying exact system calls like `-e connect` to `strace`. Filtering system calls at the tracing level is critical for performance and readability because busy applications can generate thousands of system calls per second, overwhelming your terminal and making it impossible to spot the failure. By restricting the trace to network operations, you force the kernel to only report events related to sockets, significantly reducing overhead and allowing you to pinpoint exactly when the application attempts to reach out and whether the connection is refused or timing out.

```bash
strace -e trace=network command
```

This traces: socket, bind, connect, listen, accept, send, recv, etc.

For a running process:
```bash
sudo strace -e trace=network -p $PID
```

To see what a program connects to:
```bash
strace -e connect curl http://example.com 2>&1
# Shows: connect(3, {sa_family=AF_INET, ...}, 16) = 0
```

</details>

### Question 4
You are reverse-engineering a compiled binary without source code to figure out why it is crashing on startup. You suspect it might be failing when trying to allocate memory or format a string internally before it even tries to read a file. Which tool would you use to verify this, and why would the other tracing tool not show this activity?

<details>
<summary>Show Answer</summary>

You would use `ltrace` to verify internal memory allocations or string formatting because these are library functions, whereas `strace` only intercepts requests made directly to the Linux kernel. When a program formats a string using something like `printf`, it executes entirely in user space within the C standard library. The kernel is completely unaware of this operation until the library finally decides to output the result via a `write` system call. Therefore, `strace` is blind to the internal mechanics of shared libraries, making `ltrace` the necessary choice for debugging user-space library interactions before they hit the kernel boundary.

**strace** traces **system calls** — interactions with the kernel:
- File operations (open, read, write)
- Process operations (fork, exec, exit)
- Network (socket, connect, send)
- Low-level, kernel interface

**ltrace** traces **library calls** — interactions with shared libraries:
- libc functions (malloc, printf, strlen)
- Other libraries the program uses
- Higher-level, user-space interface

Example:
- `printf("hello")` calls `write(1, "hello", 5)`
- ltrace shows `printf`, strace shows `write`

Use strace for I/O, network, system behavior. Use ltrace for library-level debugging.

</details>

### Question 5
A background data processing daemon has been running for 12 hours but hasn't updated its output file or written any logs in the last hour. The process is still alive and shows an 'S' (Interruptible Sleep) state in `top`. What steps would you take to figure out exactly what the daemon is currently waiting on?

<details>
<summary>Show Answer</summary>

To diagnose a process stuck in an 'S' state, you must progressively investigate its kernel stack, system calls, and open files to identify the blocking resource. Because an 'S' state simply means the process is waiting for some event (like input, a lock, or a timer) to wake it up, just looking at `ps` or `top` won't tell you the cause. Checking `/proc/$PID/stack` reveals the exact kernel function the process is sleeping in, while attaching `strace` allows you to see the last system call that hasn't returned yet. Correlating that system call with the process's open file descriptors via `lsof` usually reveals the culprit, such as a blocked pipe or a locked file.

Step by step:

```bash
# 1. Check state
ps -o pid,stat,wchan -p $PID
# STAT tells you state, WCHAN tells kernel function

# 2. Check kernel stack
cat /proc/$PID/stack
# Shows what kernel call it's in

# 3. Attach strace
sudo strace -p $PID
# Shows last/current syscall

# 4. Check what it's waiting on
ls -l /proc/$PID/fd/
lsof -p $PID
# Look for network, disk, locks
```

Common causes:
- D state: I/O (disk, NFS, network storage)
- S state on connect: waiting for network
- S state on flock: waiting for lock
- S state on read from pipe: waiting for input

</details>

---

## Hands-On Exercise

### Process Debugging Practice

**Objective**: Use /proc, strace, and lsof to examine process behavior.

**Environment**: Linux system with root access

#### Part 1: Exploring /proc

```bash
# 1. Find a process to examine
pgrep -l bash
PID=$(pgrep bash | head -1)
echo "Examining PID: $PID"

# 2. Command line
cat /proc/$PID/cmdline | tr '\0' ' '; echo

# 3. Working directory
ls -l /proc/$PID/cwd

# 4. Executable
ls -l /proc/$PID/exe

# 5. Open file descriptors
ls -l /proc/$PID/fd/

# 6. Environment variables
cat /proc/$PID/environ | tr '\0' '\n' | head -10

# 7. Memory info
cat /proc/$PID/status | grep -E "Vm|Mem"

# 8. Resource limits
cat /proc/$PID/limits | head -10
```

#### Part 2: Basic strace

```bash
# 1. Trace a simple command
strace -c ls /tmp
# Shows summary of syscalls

# 2. Trace with output
strace ls /tmp 2>&1 | head -20

# 3. Trace file operations only
strace -e trace=file ls /tmp 2>&1 | head -20

# 4. Trace with timestamps
strace -tt ls /tmp 2>&1 | head -10

# 5. Trace and time calls
strace -T cat /etc/passwd 2>&1 | tail -10
# -T shows time in each call
```

#### Part 3: strace Filtering

```bash
# 1. What config files does a program read?
strace -e openat cat /etc/passwd 2>&1

# 2. What network calls?
strace -e trace=network curl -s http://example.com 2>&1 | head -20

# 3. Trace child processes
strace -f bash -c "echo hello | cat" 2>&1 | tail -20

# 4. Write to file
strace -o /tmp/trace.log ls /tmp
head -30 /tmp/trace.log
```

#### Part 4: lsof

```bash
# 1. Current shell's open files
lsof -p $$

# 2. What's using port 22? (if sshd running)
sudo lsof -i :22 2>/dev/null | head -10

# 3. Network connections
lsof -i -P -n | head -20

# 4. Files in a directory
lsof +D /var/log/ 2>/dev/null | head -10
```

#### Part 5: Process States

```bash
# 1. Check process states
ps aux | head -20

# 2. Find any D state (if any)
ps aux | awk '$8 ~ /D/ {print}' || echo "No D state processes"

# 3. Find zombies (if any)
ps aux | awk '$8 ~ /Z/ {print}' || echo "No zombie processes"

# 4. Count by state
ps -eo stat | sort | uniq -c | sort -rn

# 5. Check your shell's state
ps -o pid,stat,wchan -p $$
```

#### Part 6: Debugging Scenario

```bash
# Create a process to debug
sleep 300 &
SLEEP_PID=$!
echo "Created sleep process: $SLEEP_PID"

# 1. Check state
ps -o pid,stat,wchan -p $SLEEP_PID

# 2. Check what it's doing
cat /proc/$SLEEP_PID/stack 2>/dev/null || echo "Stack not available"

# 3. Attach strace briefly
timeout 2 strace -p $SLEEP_PID 2>&1 || true

# 4. Check open files
ls -l /proc/$SLEEP_PID/fd/

# 5. Clean up
kill $SLEEP_PID
```

### Success Criteria

- [ ] Explored /proc filesystem for a process
- [ ] Used strace to trace system calls
- [ ] Filtered strace output by syscall type
- [ ] Used lsof to find open files and ports
- [ ] Checked process states with ps
- [ ] Debugged a simple process

---

## Key Takeaways

1. **/proc has everything** — File descriptors, memory, limits, stack traces

2. **strace shows syscalls** — What the process is actually doing

3. **Filter strace output** — Use `-e trace=` to reduce noise

4. **lsof finds open files** — Including network connections

5. **Process state matters** — D state means I/O, Z means zombie

---

## What's Next?

In **Module 6.4: Network Debugging**, you'll learn how to diagnose network connectivity issues using tcpdump, ss, and systematic network troubleshooting.

---

## Further Reading

- [strace man page](https://man7.org/linux/man-pages/man1/strace.1.html)
- [Brendan Gregg's perf Examples](https://www.brendangregg.com/perf.html)
- [/proc filesystem documentation](https://www.kernel.org/doc/html/latest/filesystems/proc.html)
- [lsof Quick Start](https://danielmiessler.com/p/lsof/)