# Module 1.2: Processes & systemd

> **Linux Foundations** | Complexity: `[MEDIUM]` | Time: 30-35 min

## Prerequisites

Before starting this module:
- **Required**: [Module 1.1: Kernel & Architecture](module-1.1-kernel-architecture.md)
- **Helpful**: Have a Linux system available (VM, WSL, or native)

---

## Why This Module Matters

Everything running on Linux is a process. Your shell, your web server, your database, every container—they're all processes managed by the kernel.

Understanding processes is essential because:

- **Containers ARE processes** — A container is just a process with isolation
- **Kubernetes pods** contain processes running in containers
- **Debugging** requires understanding process states and signals
- **Resource management** is process management

When `kubectl exec` hangs, when a container won't stop, when your application becomes a zombie—you need to understand processes.

---

## Did You Know?

- **Process ID 1 is special** — It's the init system (usually systemd) and is the ancestor of ALL other processes. If PID 1 dies, the kernel panics. In containers, your main process becomes PID 1, which is why proper signal handling matters.

- **Linux can have over 4 million PIDs** — The maximum PID is controlled by `/proc/sys/kernel/pid_max`. The default is typically 32768 or 4194304 on 64-bit systems. Once exhausted, no new processes can start.

- **Fork bombs are simple but devastating** — The classic `:(){ :|:& };:` creates processes exponentially until the system runs out of PIDs or memory. This is why resource limits exist.

- **Zombie processes don't consume CPU or memory** — They're just an entry in the process table waiting for their parent to acknowledge their death. But too many zombies can exhaust the PID space.

---

## What Is a Process?

A **process** is a running instance of a program. It includes:

- **Code** — The program instructions
- **Memory** — Stack, heap, data segments
- **Resources** — Open files, network connections
- **Metadata** — PID, owner, state, priority

```
┌─────────────────────────────────────────────────────────┐
│                       PROCESS                            │
├─────────────────────────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │  Code   │ │  Stack  │ │  Heap   │ │  Data   │       │
│  │ (text)  │ │         │ │         │ │ Segment │       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │
├─────────────────────────────────────────────────────────┤
│  PID: 1234  │  PPID: 1  │  UID: 1000  │  State: R      │
├─────────────────────────────────────────────────────────┤
│  Open Files: stdin(0), stdout(1), stderr(2), /var/log  │
└─────────────────────────────────────────────────────────┘
```

### Process vs Program

| Program | Process |
|---------|---------|
| File on disk | Running in memory |
| Passive | Active |
| One copy | Many instances possible |
| `/usr/bin/nginx` | PIDs 1234, 1235, 1236 |

---

## Process Identification

### PIDs and PPIDs

Every process has:
- **PID** (Process ID) — Unique identifier
- **PPID** (Parent PID) — Who created this process

```bash
# See your current shell's PID
echo $$
# Output: 1234

# See parent PID
echo $PPID
# Output: 1000

# Detailed view
ps -p $$ -o pid,ppid,cmd
```

### The Process Tree

All processes form a tree, rooted at PID 1:

```bash
# View process tree
pstree -p

# Output example:
systemd(1)─┬─sshd(800)───sshd(1200)───bash(1234)───pstree(5678)
           ├─containerd(500)─┬─containerd-shim(600)───nginx(601)
           │                 └─containerd-shim(700)───python(701)
           └─kubelet(400)
```

### Special PIDs

| PID | Name | Purpose |
|-----|------|---------|
| 0 | Swapper/Idle | Kernel scheduler |
| 1 | Init/systemd | Parent of all user processes |
| 2 | kthreadd | Parent of kernel threads |

---

## Process Lifecycle

### Birth: fork() and exec()

New processes are created in two steps:

```
┌──────────┐    fork()     ┌──────────┐
│  Parent  │──────────────▶│  Child   │  (copy of parent)
│  (bash)  │               │  (bash)  │
└──────────┘               └────┬─────┘
                                │
                           exec("/bin/ls")
                                │
                                ▼
                           ┌──────────┐
                           │  Child   │  (now running ls)
                           │   (ls)   │
                           └──────────┘
```

1. **fork()** — Creates a copy of the parent process
2. **exec()** — Replaces the process image with a new program

```bash
# You can see this in action
strace -f -e fork,execve bash -c 'ls' 2>&1 | grep -E 'fork|exec'
```

### Process States

Processes cycle through states:

```
                        ┌─────────────┐
                        │   Created   │
                        └──────┬──────┘
                               │
                               ▼
        ┌───────────────────────────────────────────┐
        │                                           │
        ▼                                           │
  ┌───────────┐     schedule     ┌───────────┐     │
  │  Ready    │◄────────────────▶│  Running  │     │
  │ (Waiting  │                  │  (R)      │     │
  │  for CPU) │                  │           │     │
  └─────┬─────┘                  └─────┬─────┘     │
        │                              │           │
        │         I/O wait             │ exit()    │
        │    ┌─────────────────────────┤           │
        │    │                         │           │
        │    ▼                         ▼           │
        │ ┌───────────┐          ┌───────────┐    │
        │ │ Sleeping  │          │  Zombie   │    │
        │ │ (S or D)  │          │   (Z)     │    │
        │ └─────┬─────┘          └─────┬─────┘    │
        │       │                      │          │
        └───────┘     parent wait()    │          │
                      ┌────────────────┘          │
                      ▼                           │
                ┌───────────┐                     │
                │Terminated │─────────────────────┘
                └───────────┘
```

### State Codes in ps/top

| State | Meaning | Description |
|-------|---------|-------------|
| R | Running | Currently executing or ready to run |
| S | Sleeping | Waiting for an event (interruptible) |
| D | Disk sleep | Waiting for I/O (uninterruptible) |
| Z | Zombie | Terminated but not reaped by parent |
| T | Stopped | Stopped by signal (Ctrl+Z) |
| t | Tracing | Being debugged |

```bash
# See process states
ps aux | awk '{print $8}' | sort | uniq -c | sort -rn
```

### Death: exit() and wait()

```
┌──────────┐                    ┌──────────┐
│  Child   │ ──── exit(0) ────▶│  Zombie  │
│ (running)│                    │  (Z)     │
└──────────┘                    └────┬─────┘
                                     │
       ┌─────────────────────────────┘
       │  parent calls wait()
       ▼
┌──────────────┐
│  Terminated  │  (entry removed from process table)
└──────────────┘
```

---

## Signals

Signals are software interrupts used for inter-process communication.

### Common Signals

| Signal | Number | Default Action | Purpose |
|--------|--------|----------------|---------|
| SIGHUP | 1 | Terminate | Hangup (reload config) |
| SIGINT | 2 | Terminate | Interrupt (Ctrl+C) |
| SIGQUIT | 3 | Core dump | Quit with dump |
| SIGKILL | 9 | Terminate | Force kill (cannot be caught) |
| SIGTERM | 15 | Terminate | Graceful shutdown |
| SIGSTOP | 19 | Stop | Pause process (cannot be caught) |
| SIGCONT | 18 | Continue | Resume stopped process |
| SIGCHLD | 17 | Ignore | Child status changed |

### Sending Signals

```bash
# Send SIGTERM (default)
kill 1234

# Send SIGKILL
kill -9 1234
kill -KILL 1234

# Send SIGHUP (often reloads config)
kill -HUP 1234

# Send signal to process group
kill -TERM -1234  # Note the minus

# Kill by name
pkill nginx
killall nginx
```

### The SIGTERM vs SIGKILL Debate

```
SIGTERM (15)                    SIGKILL (9)
    │                               │
    ▼                               ▼
┌──────────────┐             ┌──────────────┐
│   Process    │             │    Kernel    │
│ can handle   │             │ terminates   │
│ gracefully   │             │ immediately  │
└──────────────┘             └──────────────┘
    │                               │
    ├── Flush buffers               ├── No cleanup
    ├── Close connections           ├── No flushing
    ├── Remove temp files           ├── Resources leaked
    └── Exit cleanly                └── Potentially corrupt
```

**Best practice**: Always try SIGTERM first, wait a few seconds, then SIGKILL only if necessary.

### Signals in Kubernetes

When Kubernetes terminates a pod:

```
1. kubectl delete pod
         │
         ▼
2. SIGTERM sent to PID 1 in container
         │
         │  (terminationGracePeriodSeconds, default 30s)
         │
         ▼
3. SIGKILL sent if still running
```

This is why your containerized applications **must handle SIGTERM**!

---

## systemd: The Modern Init

systemd is the init system and service manager for most Linux distributions.

### Why systemd?

| Old Init (SysV) | systemd |
|-----------------|---------|
| Sequential boot | Parallel boot |
| Shell scripts | Declarative units |
| Manual dependencies | Automatic dependencies |
| PID files | Cgroups tracking |
| No socket activation | Socket activation |

### systemd Concepts

```
┌─────────────────────────────────────────────────────────┐
│                     systemd (PID 1)                      │
├─────────────────────────────────────────────────────────┤
│  Units                                                   │
│  ├── Services (.service)  — Daemons and applications    │
│  ├── Sockets (.socket)    — Socket activation           │
│  ├── Targets (.target)    — Groups of units             │
│  ├── Mounts (.mount)      — Filesystem mounts           │
│  ├── Timers (.timer)      — Scheduled tasks             │
│  └── Paths (.path)        — Path monitoring             │
├─────────────────────────────────────────────────────────┤
│  Cgroups                                                 │
│  └── Resource control and process tracking              │
├─────────────────────────────────────────────────────────┤
│  Journal                                                 │
│  └── Centralized logging (journald)                     │
└─────────────────────────────────────────────────────────┘
```

### Essential systemctl Commands

```bash
# Service management
systemctl start nginx          # Start service
systemctl stop nginx           # Stop service
systemctl restart nginx        # Restart service
systemctl reload nginx         # Reload config (if supported)
systemctl status nginx         # Show status

# Enable/disable at boot
systemctl enable nginx         # Start on boot
systemctl disable nginx        # Don't start on boot
systemctl is-enabled nginx     # Check if enabled

# View all services
systemctl list-units --type=service
systemctl list-units --type=service --state=running

# Failed services
systemctl --failed

# System targets
systemctl get-default          # Current default target
systemctl list-units --type=target
```

### Anatomy of a Unit File

```ini
# /etc/systemd/system/myapp.service
[Unit]
Description=My Application
Documentation=https://example.com/docs
After=network.target           # Start after network
Wants=redis.service            # Soft dependency
Requires=postgresql.service    # Hard dependency

[Service]
Type=simple                    # forking, oneshot, notify, idle
ExecStart=/usr/bin/myapp
ExecReload=/bin/kill -HUP $MAINPID
ExecStop=/bin/kill -TERM $MAINPID
Restart=always                 # on-failure, on-abnormal, on-abort
RestartSec=5
User=myapp
Group=myapp
WorkingDirectory=/opt/myapp

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target     # Enable for this target
```

### Service Types

| Type | Description | Use When |
|------|-------------|----------|
| simple | Process started is the main process | Most applications |
| forking | Process forks and parent exits | Traditional daemons |
| oneshot | Process expected to exit | Scripts, setup tasks |
| notify | Like simple, sends notification | systemd-aware apps |
| idle | Like simple, waits for jobs | Low priority |

### Try This: Create a Service

```bash
# Create a simple service
sudo tee /etc/systemd/system/hello.service << 'EOF'
[Unit]
Description=Hello World Service
After=network.target

[Service]
Type=simple
ExecStart=/bin/bash -c 'while true; do echo "Hello at $(date)"; sleep 10; done'
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

# Start and check
sudo systemctl start hello
sudo systemctl status hello

# View logs
journalctl -u hello -f

# Cleanup
sudo systemctl stop hello
sudo systemctl disable hello
sudo rm /etc/systemd/system/hello.service
sudo systemctl daemon-reload
```

---

## Bootloader (GRUB2)

GRUB2 (GRand Unified Bootloader) is the first software that runs when a Linux system boots. It loads the kernel and initial ramdisk (initrd) into memory. Knowing GRUB2 is essential for the LFCS — you may need to change kernel parameters, recover a broken system, or install GRUB on a new disk.

### How the Boot Process Works

```
BIOS/UEFI → GRUB2 → Kernel + initrd → systemd (PID 1)
```

### GRUB2 Configuration

```bash
# The main config file is generated — NEVER edit it directly
# /boot/grub/grub.cfg (Debian/Ubuntu)
# /boot/grub2/grub.cfg (RHEL/Rocky)

# Instead, edit the defaults file:
sudo vi /etc/default/grub
```

Key settings in `/etc/default/grub`:

```bash
GRUB_TIMEOUT=5                          # Seconds to wait at boot menu
GRUB_DEFAULT=0                          # Boot first entry by default
GRUB_CMDLINE_LINUX_DEFAULT="quiet"      # Kernel params for default entry
GRUB_CMDLINE_LINUX=""                   # Kernel params for ALL entries
GRUB_DISABLE_RECOVERY="false"           # Show recovery mode entries
```

### Regenerating GRUB Config

```bash
# After editing /etc/default/grub, regenerate the config:
sudo update-grub                        # Debian/Ubuntu
sudo grub2-mkconfig -o /boot/grub2/grub.cfg   # RHEL/Rocky

# Install GRUB to a disk (e.g., after replacing boot disk)
sudo grub-install /dev/sda              # Debian/Ubuntu (BIOS)
sudo grub2-install /dev/sda             # RHEL/Rocky (BIOS)
```

### Editing Kernel Parameters at Boot

Sometimes you need to change kernel parameters at boot time — for example, to boot into single-user mode or troubleshoot a broken system:

1. Reboot the system and hold **Shift** (BIOS) or press **Esc** (UEFI) to show the GRUB menu
2. Select the kernel entry and press **e** to edit
3. Find the line starting with `linux` and append parameters at the end:
   - `single` or `1` — Boot into single-user/rescue mode
   - `systemd.unit=rescue.target` — systemd rescue mode
   - `systemd.unit=emergency.target` — Emergency shell (minimal)
   - `rd.break` — Break into initramfs before root is mounted (for password reset)
4. Press **Ctrl+X** or **F10** to boot with the modified parameters

### Rescue Mode and Password Recovery

```bash
# If you've lost the root password:
# 1. Boot with rd.break (edit GRUB line as above)
# 2. At the initramfs prompt:
mount -o remount,rw /sysroot
chroot /sysroot
passwd root
touch /.autorelabel    # Required on SELinux systems
exit
reboot
```

> **Exam tip**: The LFCS may ask you to change the default kernel parameters or recover a system with a lost root password. Memorize the GRUB edit workflow and the `rd.break` method.

---

## Viewing Processes

### ps Command

```bash
# Standard snapshot
ps aux

# Custom format
ps -eo pid,ppid,user,%cpu,%mem,stat,cmd --sort=-%mem | head

# Process tree
ps auxf

# For specific user
ps -u nginx

# Find specific process
ps aux | grep nginx
pgrep -a nginx
```

### Understanding ps Output

```
USER   PID  %CPU %MEM    VSZ   RSS TTY   STAT START   TIME COMMAND
root     1   0.0  0.1 171584 13324 ?     Ss   Dec01   0:15 /sbin/init
nginx  100   0.5  2.0 500000 40000 ?     S    Dec01   1:30 nginx: worker
```

| Column | Meaning |
|--------|---------|
| VSZ | Virtual memory size (includes shared libs) |
| RSS | Resident Set Size (actual memory used) |
| TTY | Terminal (? = daemon) |
| STAT | Process state |
| TIME | CPU time consumed |

### top and htop

```bash
# Basic top
top

# Sort by memory
top -o %MEM

# For specific user
top -u nginx

# Interactive htop (recommended)
htop
```

### Inside htop

```
  1  [||||||||                    32.0%]   Tasks: 143, 412 thr; 2 running
  2  [||                           4.0%]   Load average: 0.52 0.58 0.59
  Mem[|||||||||||||||      1.21G/7.77G]   Uptime: 15 days, 02:14:37
  Swp[                         0K/0K]

    PID USER      PRI  NI  VIRT   RES   SHR S CPU% MEM%   TIME+  Command
   1234 nginx      20   0  500M   40M  8192 S  0.5  2.0  1:30.00 nginx: worker
```

Key htop shortcuts:
- `F5` — Tree view
- `F6` — Sort by column
- `F9` — Send signal (kill)
- `k` — Kill process
- `u` — Filter by user
- `/` — Search

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Using `kill -9` first | No graceful shutdown, data loss | Always try SIGTERM first |
| Ignoring zombies | PID exhaustion | Fix the parent process |
| Not handling SIGTERM in containers | Slow pod termination | Implement signal handlers |
| Running services as root | Security risk | Use dedicated service users |
| Forgetting `daemon-reload` | Unit changes not applied | Always reload after editing units |
| Processes in D state | Can't kill, system hung | Usually I/O issues, check storage |

---

## Quiz

### Question 1
What's the difference between fork() and exec()?

<details>
<summary>Show Answer</summary>

- **fork()** creates a copy of the current process (new PID, same code)
- **exec()** replaces the current process's code with a new program

A new process typically uses both: fork() to create the child, then exec() to run the new program.

</details>

### Question 2
What is a zombie process and how is it created?

<details>
<summary>Show Answer</summary>

A **zombie** is a process that has terminated but whose parent hasn't called wait() to read its exit status. It exists in the process table but consumes no resources except the PID entry.

Created when: Child exits → Parent doesn't call wait() → Child becomes zombie

Fixed when: Parent calls wait() or parent dies (init inherits and reaps)

</details>

### Question 3
Why can't you kill a process in "D" (uninterruptible sleep) state?

<details>
<summary>Show Answer</summary>

Processes in D state are waiting for I/O (usually disk) to complete. They can't receive signals because they're in the middle of a kernel operation that can't be interrupted safely.

The only solution is to resolve the underlying I/O issue (fix storage, NFS mount, etc.) or reboot.

</details>

### Question 4
What happens when you run `systemctl enable nginx`?

<details>
<summary>Show Answer</summary>

It creates a symbolic link from the target's wants directory to the unit file:
```
/etc/systemd/system/multi-user.target.wants/nginx.service →
  /lib/systemd/system/nginx.service
```

This tells systemd to start nginx when the system reaches that target (usually at boot).

</details>

### Question 5
Why is PID 1 special in containers?

<details>
<summary>Show Answer</summary>

In containers, PID 1:
1. Receives SIGTERM when Kubernetes stops the pod
2. Must properly reap zombie children (no init to help)
3. Doesn't get default signal handlers (SIGTERM is ignored by default for PID 1!)

This is why many containers use tini or dumb-init as PID 1, or why applications need explicit SIGTERM handling.

</details>

---

## Hands-On Exercise

### Process Management Deep Dive

**Objective**: Master process viewing, signal handling, and systemd management.

**Environment**: Any Linux system with systemd

#### Part 1: Process Exploration

```bash
# 1. Find your shell's process info
echo "PID: $$, PPID: $PPID"
ps -p $$ -o pid,ppid,user,stat,cmd

# 2. View full process tree
pstree -p | head -30

# 3. Find all processes by state
ps aux | awk 'NR>1 {states[$8]++} END {for(s in states) print s, states[s]}'

# 4. Find processes consuming most memory
ps aux --sort=-%mem | head -10
```

#### Part 2: Signals in Action

```bash
# 1. Start a background process
sleep 300 &
PID=$!
echo "Started sleep with PID: $PID"

# 2. Check its state
ps -p $PID -o pid,stat,cmd

# 3. Stop it (SIGSTOP)
kill -STOP $PID
ps -p $PID -o pid,stat,cmd  # Should show T

# 4. Continue it (SIGCONT)
kill -CONT $PID
ps -p $PID -o pid,stat,cmd  # Should show S

# 5. Terminate gracefully
kill -TERM $PID

# 6. Verify it's gone
ps -p $PID 2>/dev/null || echo "Process terminated"
```

#### Part 3: Create a Zombie (Educational!)

```bash
# Create a script that creates a zombie
cat > /tmp/zombie_creator.sh << 'EOF'
#!/bin/bash
# Child process
(
    echo "Child PID: $$"
    exit 0
) &

# Parent sleeps without waiting
echo "Parent PID: $$"
echo "Check for zombie with: ps aux | grep defunct"
sleep 60
EOF

chmod +x /tmp/zombie_creator.sh

# Run it
/tmp/zombie_creator.sh &

# Check for zombie (in another terminal)
ps aux | grep defunct

# Cleanup
pkill -f zombie_creator
rm /tmp/zombie_creator.sh
```

#### Part 4: systemd Service Management

```bash
# 1. List running services
systemctl list-units --type=service --state=running | head -20

# 2. Check a specific service
systemctl status sshd || systemctl status ssh

# 3. View service logs
journalctl -u sshd -n 20 || journalctl -u ssh -n 20

# 4. Find failed services
systemctl --failed

# 5. View service dependencies
systemctl list-dependencies sshd || systemctl list-dependencies ssh
```

### Success Criteria

- [ ] Found your shell's PID and PPID
- [ ] Identified process states across the system
- [ ] Successfully sent STOP, CONT, and TERM signals
- [ ] Created and observed a zombie process
- [ ] Used systemctl to explore services

---

## Key Takeaways

1. **Processes are the foundation** — Everything running on Linux is a process, including containers

2. **fork() + exec() creates new processes** — Understanding this explains how shells launch programs

3. **Signals are inter-process communication** — SIGTERM for graceful shutdown, SIGKILL as last resort

4. **Zombies are waiting for parents** — They consume PIDs, not resources

5. **systemd manages everything** — Services, sockets, mounts, timers all managed through units

---

## What's Next?

In **Module 1.3: Filesystem Hierarchy**, you'll learn where everything lives in Linux—from configuration files to the magical `/proc` filesystem.

---

## Further Reading

- [systemd Documentation](https://www.freedesktop.org/software/systemd/man/)
- [The Linux Process Journey](https://blog.packagecloud.io/the-definitive-guide-to-linux-system-calls/)
- [Signals in Linux](https://man7.org/linux/man-pages/man7/signal.7.html)
- [Understanding Zombie Processes](https://blog.phusion.nl/2015/01/20/docker-and-the-pid-1-zombie-reaping-problem/)
