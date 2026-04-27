---
qa_pending: true
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

Before starting this module, you should be comfortable reading process lists, interpreting systemd service status, and following logs over time. Process debugging is where those skills become operational: instead of asking only what a program reported, you ask what the kernel can prove the program is doing.

- **Required**: [Module 1.2: Processes & Systemd](/linux/foundations/system-essentials/module-1.2-processes-systemd/)
- **Required**: [Module 6.2: Log Analysis](../module-6.2-log-analysis/)
- **Helpful**: Basic shell pipelines, file descriptors, signals, and system calls

---

## What You'll Be Able to Do

After this module, you will be able to:

- **Diagnose** process hangs, crashes, and resource leaks by combining `/proc`, `ps`, `strace`, and `lsof` evidence.
- **Trace** system calls selectively so you can explain what a running process is waiting on without drowning in noise.
- **Evaluate** process states, file descriptors, limits, and kernel wait channels to separate CPU problems from I/O, lock, and lifecycle problems.
- **Debug** containerized processes by identifying namespaces, entering the right process context with `nsenter`, and checking the same Linux primitives from inside that context.
- **Design** a low-risk production debugging plan that gathers useful evidence while limiting performance impact and avoiding accidental data exposure.

---

## Why This Module Matters

A payment worker stops processing jobs during a release, but the logs show nothing except the last successful task. The service is still running, health checks are green, CPU is quiet, and the team keeps restarting it because that is the only lever they know. The restart makes the symptom disappear for twenty minutes, then the backlog starts growing again, and no one can explain whether the worker is blocked on storage, waiting for a lock, leaking descriptors, or silently spinning through failed retries.

This is the moment where process debugging matters. Logs describe what the application chose to say, but the kernel knows what the process actually asked for. If the process opened thousands of sockets, the kernel knows. If it is stuck waiting for a network filesystem, the scheduler knows. If it is repeatedly failing to read a missing configuration file, the system call stream will show the exact filename and error code.

Senior operators do not begin with the most powerful tool; they begin with the least invasive question that can falsify a theory. They look at the process state, confirm the command line, inspect open descriptors, compare limits, and only then attach heavier tracing when the cheaper evidence is insufficient. This module teaches that progression so you can debug a live process without turning a production incident into a second incident.

---

## Core Section 1: Build a Process Debugging Mental Model

A Linux process is not a mysterious black box once you know which boundary to inspect. The process has user-space code, shared libraries, kernel-facing system calls, open file descriptors, memory mappings, namespaces, limits, and scheduler state. Each tool in this module observes one layer of that stack, so the main skill is choosing the layer that matches the symptom.

When a service is hung, the first question is not "which command should I run?" The better question is "what kind of waiting would explain this symptom?" Waiting on disk, waiting on a socket, waiting on a lock, sleeping on a timer, and spinning in user-space all look different if you check the right evidence. A disciplined debugger narrows the search before attaching a tracer.

```text
+------------------------------- Process Debugging Layers -------------------------------+
| Symptom seen by humans     | Best first evidence         | Deeper tool if unclear       |
|----------------------------|-----------------------------|------------------------------|
| Process alive but idle     | ps state, wchan, /proc      | strace attached briefly      |
| Disk remains full          | lsof deleted files          | /proc/$PID/fd and restart    |
| Too many open files        | /proc/$PID/fd count, limits | strace -e trace=file         |
| Network call hangs         | lsof -i, ss, strace network | tcpdump in next module       |
| Child command disappears   | ps tree, strace -f          | service supervisor logs      |
| Container process differs  | namespaces, nsenter         | inspect from inside ns       |
+----------------------------------------------------------------------------------------+
```

The cheapest inspection points are read-only: `ps`, `/proc`, and `lsof` usually do not stop the process or intercept every kernel transition. Tracing tools such as `strace` and `ltrace` are more revealing, but they add overhead and can expose sensitive arguments, filenames, and environment data. That trade-off is acceptable during an incident only when you know what question the trace is supposed to answer.

Use this decision path as the starting point whenever a process behaves strangely. It is not a replacement for judgment, but it prevents the common mistake of jumping directly into a full unfiltered trace and then spending the next ten minutes scrolling through irrelevant system calls.

```mermaid
stateDiagram-v2
    direction TB
    state "Symptom reported" as Symptom
    state "Confirm PID and command" as Confirm
    state "Check state, wchan, parent" as State
    state "Inspect /proc and limits" as Proc
    state "Inspect descriptors with lsof" as Lsof
    state "Attach filtered strace" as Strace
    state "Trace libraries or enter namespace" as Deep
    state "Recommend fix or gather escalation bundle" as Fix

    Symptom --> Confirm : identify target
    Confirm --> State : process exists
    State --> Proc : state explains part of symptom
    Proc --> Lsof : descriptors or files matter
    Lsof --> Strace : live behavior still unknown
    Strace --> Deep : syscall layer not enough
    Deep --> Fix : evidence supports action
    Strace --> Fix : root cause found
    Proc --> Fix : stale file, limit, or env found
```

The same workflow applies whether the process is a local daemon, a shell command, or a container workload. The container case adds namespace boundaries, but the process still has descriptors, limits, system calls, and a scheduler state. You are learning Linux primitives, not a single troubleshooting recipe that only works on one distribution.

**Active learning prompt:** Your team says "the service is frozen." Before choosing a command, write down two competing theories: one where the process is waiting on the kernel, and one where it is actively doing user-space work. Which first command would distinguish those theories with the least risk?

A good answer usually starts with `ps -o pid,ppid,stat,wchan,comm -p "$PID"` and then uses the result to decide what to inspect next. If the process is sleeping in a recognizable wait channel, you have a kernel-side clue. If it is constantly runnable and burning CPU, you need a different path, possibly sampling or profiling instead of descriptor inspection.

---

## Core Section 2: Use `/proc` as the Ground Truth Baseline

The `/proc` filesystem is a live view of kernel process metadata. It is not an ordinary directory tree stored on disk; it is a virtual interface that lets you ask the kernel about processes, descriptors, memory maps, limits, environment variables, and namespace membership. That makes it the safest first stop for most investigations.

Begin by identifying the exact process you are debugging. In incidents, operators often inspect the wrong worker because several commands share the same name or a supervisor has already restarted the service. Confirm the PID, parent PID, command line, and start time before interpreting deeper evidence.

```bash
pgrep -a bash | head
PID="$(pgrep bash | head -n 1)"
printf 'Examining PID=%s\n' "$PID"
ps -o pid,ppid,lstart,stat,wchan,comm,args -p "$PID"
```

The command line and executable symlink answer different questions. `/proc/$PID/cmdline` shows the arguments used to start the process, while `/proc/$PID/exe` points to the executable image that is still mapped by the process. If a deployment replaced or deleted the binary on disk, the symlink can show a deleted marker even while the old program continues running from its mapped image.

```bash
tr '\0' ' ' < "/proc/$PID/cmdline"
printf '\n'
ls -l "/proc/$PID/exe"
ls -l "/proc/$PID/cwd"
```

Environment variables can explain behavior that never appears in logs. A process may read a proxy setting, feature flag, config path, or credential location from its environment during startup and then behave correctly according to that hidden input. Treat environment output as sensitive because it may contain tokens, passwords, and internal URLs.

```bash
tr '\0' '\n' < "/proc/$PID/environ" | sed -n '1,20p'
```

Resource limits are another high-value baseline because they connect application symptoms to kernel enforcement. "Too many open files" is not a vague application complaint; it usually means the process reached its soft `RLIMIT_NOFILE` limit or the service is leaking descriptors faster than it closes them. Comparing the limit with the current descriptor count tells you whether the process is near failure.

```bash
cat "/proc/$PID/limits" | sed -n '1,12p'
printf 'Open descriptor count: '
ls "/proc/$PID/fd" | wc -l
```

File descriptors are the most concrete evidence in many process incidents. A descriptor may point to a regular file, a socket, a pipe, an eventfd, a deleted file, a terminal, or a device. The process only sees small integers, but `/proc/$PID/fd` lets you map those integers back to the resources that keep the process connected to the system.

```bash
ls -l "/proc/$PID/fd" | sed -n '1,20p'
for fd in /proc/"$PID"/fdinfo/*; do
  printf '%s\n' "$fd"
  sed -n '1,5p' "$fd"
done | sed -n '1,30p'
```

Memory maps show which files and anonymous regions are mapped into the process. You do not need to become a memory forensics expert to use them well. In day-to-day operations, maps help you confirm which binary and libraries are loaded, whether a deleted library is still mapped, and whether the heap or anonymous mappings dominate the address space.

```bash
sed -n '1,20p' "/proc/$PID/maps"
grep -E 'VmSize|VmRSS|VmSwap|Threads' "/proc/$PID/status"
```

The status file is a compact summary that pairs well with `ps`. It includes the process state, thread count, memory figures, signal masks, and namespace-related identifiers on many systems. When the thread count climbs unexpectedly, combine this with descriptor inspection because thread leaks and descriptor leaks often appear together in overloaded services.

```bash
sed -n '1,80p' "/proc/$PID/status"
```

**Worked example:** Suppose an application reports `EMFILE`, which means it cannot open more files. Start with the descriptor count, compare it to the soft open-file limit, then sample the descriptor targets to see whether the leak is regular files, sockets, pipes, or duplicated descriptors. This sequence gives you evidence before you decide whether to restart, raise limits, or fix application cleanup.

```bash
PID="$(pgrep -n node || pgrep -n bash)"
echo "PID=$PID"
grep 'Max open files' "/proc/$PID/limits"
echo "Current descriptor count:"
ls "/proc/$PID/fd" | wc -l
echo "Descriptor sample:"
ls -l "/proc/$PID/fd" | sed -n '1,25p'
```

If the count is near the soft limit and most descriptors point to sockets, you probably have a connection lifecycle problem. If many descriptors point to deleted log files, you may have a rotation or cleanup problem. If the descriptors are duplicated pipes, inspect the parent and child process relationship because a pipeline or supervisor may be keeping resources open accidentally.

**Active learning prompt:** A process shows a low resident memory size but hundreds of descriptors pointing to deleted files. What user-visible symptom could that create, and why would restarting only that process release disk space even though the files were already removed from the directory tree?

The answer is that unlinked files still consume disk blocks while any process holds an open descriptor to them. Directory entries are gone, but the underlying inode remains alive until the final descriptor closes. A restart works because it closes the descriptors, not because it repairs the filesystem.

---

## Core Section 3: Trace System Calls with `strace` Without Losing the Plot

`strace` observes the boundary between a process and the kernel. It can show file opens, reads, writes, socket connections, process creation, signal handling, memory mappings, and many other system calls. This is powerful because even closed-source programs must use system calls to interact with files, networks, time, processes, and devices.

The cost is that tracing changes the system you observe. Every intercepted call must be reported, formatted, and copied to your terminal or output file. On a busy process, an unfiltered trace can slow the program heavily, flood your terminal, and expose sensitive data from arguments. Use `strace` as a scalpel: filtered, timed, and short.

Before tracing a production process, decide whether you need to run a command under trace or attach to an already running PID. Running under trace is safer for reproduction because you can isolate a small command. Attaching to a live process is appropriate when the problem only exists inside the long-running service, but you should filter aggressively and capture the output to a file.

```bash
strace -c true
strace -e trace=file ls /tmp >/tmp/ls.out 2>/tmp/ls.trace
sed -n '1,20p' /tmp/ls.trace
```

By default, `strace` writes trace output to standard error. The traced program still writes its normal output to standard output unless you redirect it. This matters during debugging because mixing program output and trace output makes evidence harder to read and may break scripts that expect clean output.

```bash
strace ls /tmp >/tmp/program-output.txt 2>/tmp/trace-output.txt
printf 'Program output:\n'
sed -n '1,10p' /tmp/program-output.txt
printf 'Trace output:\n'
sed -n '1,10p' /tmp/trace-output.txt
```

The most useful `strace` filters are categories. `trace=file` focuses on path-based operations such as opening, statting, renaming, and unlinking files. `trace=network` focuses on sockets and connection activity. `trace=process` follows fork, clone, exec, wait, and exit behavior. These categories make the trace match the theory you are testing.

```bash
strace -e trace=file cat /etc/passwd >/tmp/passwd.copy 2>/tmp/file.trace
strace -e trace=process bash -c 'echo child' >/tmp/child.out 2>/tmp/process.trace
strace -e trace=network curl -I -s https://example.com >/tmp/curl.headers 2>/tmp/network.trace
```

When debugging slowness, add timing. The `-T` option prints time spent inside each system call, which helps separate frequent cheap calls from rare expensive calls. The `-tt` option gives high-resolution timestamps, which helps correlate trace events with logs, metrics, and user reports.

```bash
strace -tt -T -e trace=file ls /usr/bin >/tmp/listing.out 2>/tmp/timed-file.trace
sed -n '1,20p' /tmp/timed-file.trace
```

When debugging child processes, remember that many services delegate work. A shell script may start a helper, a web server may fork workers, and a build command may exec several tools. Without `-f`, you can trace the parent and miss the child that actually fails.

```bash
strace -f -e trace=process,file bash -c 'printf hello | wc -c' >/tmp/pipeline.out 2>/tmp/fork.trace
sed -n '1,40p' /tmp/fork.trace
```

**Worked example:** A program reports "configuration failed" but does not say which file it tried to load. Use a file-only trace and look for `ENOENT`, `EACCES`, or surprising paths. This is more reliable than guessing because it shows the exact path the process asked the kernel to open.

```bash
strace -e trace=file cat /etc/hosts >/tmp/hosts.copy 2>/tmp/config.trace
grep -E 'openat|stat|access|ENOENT|EACCES' /tmp/config.trace | sed -n '1,30p'
```

If the trace shows repeated `ENOENT` for a path you did not expect, the problem is probably a search path, working directory, or environment issue. If it shows `EACCES`, the file exists but permissions, ownership, or mandatory access controls may block the process. If it shows a successful open followed by a failed read or parse, the problem moves above the kernel boundary.

**Active learning prompt:** You attach `strace -e trace=file` to a running service and see nothing during a failed HTTP request. What are two plausible explanations, and which filter would you try next if the request depends on an upstream API?

One explanation is that the failure path does not touch files at all; it may be waiting on a socket, timer, futex, or child process. Another is that you attached to the wrong worker or missed the child that handled the request. For an upstream API dependency, try `strace -f -e trace=network -p "$PID"` briefly, then detach after capturing the connection attempt.

For live processes, combine filtering with a timeout so the trace stops even if you forget to detach. This habit is especially useful during incidents because it keeps the evidence window short and lowers the chance of leaving a high-overhead tracer attached.

```bash
PID="$(pgrep -n bash)"
timeout 5s strace -tt -T -e trace=file -p "$PID" 2>/tmp/live-file.trace || true
sed -n '1,30p' /tmp/live-file.trace
```

Some systems restrict tracing for security. If attaching fails with an operation-not-permitted error, check whether you have the same UID, sufficient privileges, and a compatible `ptrace_scope` setting. Do not disable security controls casually on shared hosts; capture what you can from `/proc` first and escalate with a clear reason if tracing is necessary.

```bash
cat /proc/sys/kernel/yama/ptrace_scope 2>/dev/null || true
id
```

---

## Core Section 4: Interpret Process States, Wait Channels, and Zombies

Process state tells you how the scheduler sees the task right now. It does not give a root cause by itself, but it immediately rules some theories in or out. A high load average with low CPU can happen when many processes are waiting in uninterruptible I/O, while a single runnable process using a full core points toward CPU-bound work or a tight loop.

Use `ps` with explicit columns instead of relying only on the default output. The `STAT` column shows the state, `PPID` shows the parent relationship, and `WCHAN` shows the kernel wait channel when available. Together, these fields tell you whether to inspect storage, parent lifecycle, signals, locks, or application-level behavior.

```bash
ps -eo pid,ppid,stat,wchan,comm,args | sed -n '1,25p'
```

The common states are simple, but their implications are not. `R` means running or runnable, which includes processes waiting for CPU. `S` means interruptible sleep, often waiting for a timer, socket, pipe, or signal. `D` means uninterruptible sleep, usually waiting in kernel I/O where signals are deferred. `Z` means zombie, where the process has exited but the parent has not collected its status.

```text
+----------------------------- Process State Interpretation -----------------------------+
| STAT | Operational meaning             | Typical next question                         |
|------|---------------------------------|------------------------------------------------|
| R    | Running or ready for CPU        | Is CPU saturated, or is this a short sample?   |
| S    | Interruptible sleep             | Which event, socket, pipe, timer, or lock?     |
| D    | Uninterruptible sleep           | Which disk, network filesystem, or driver?     |
| Z    | Exited but not reaped           | Which parent failed to call wait?              |
| T    | Stopped or traced               | Was SIGSTOP, a debugger, or strace involved?   |
| I    | Idle kernel thread              | Usually not an application debugging target    |
+----------------------------------------------------------------------------------------+
```

A `D` state process cannot be fixed by sending stronger signals because the kernel will not deliver the signal until the blocking operation returns. That is why `kill -9` can appear ineffective: `SIGKILL` is pending, but the process is stuck in a section where interruption would risk corrupting kernel or device state. The useful response is to investigate the I/O path, not to repeat the kill command.

```bash
ps -eo pid,ppid,stat,wchan,comm,args | awk '$3 ~ /D/ {print}'
```

The kernel stack can sometimes show where a process is blocked, though access may require elevated privileges and kernel configuration support. Treat the stack as a clue rather than a complete diagnosis. A wait inside filesystem or block-device functions points toward storage; a socket wait points toward networking; a futex wait points toward user-space locking.

```bash
PID="$(pgrep -n bash)"
sudo cat "/proc/$PID/stack" 2>/dev/null || cat "/proc/$PID/wchan" 2>/dev/null || true
```

Zombies are different from hung processes. A zombie is already dead; it consumes a PID table entry and stores exit status until the parent collects it. Killing the zombie does not help because there is no running process body left to kill. You fix the parent or restart the service tree that owns the broken parent-child relationship.

```bash
ps -eo pid,ppid,stat,comm,args | awk '$3 ~ /Z/ {print}'
```

A single zombie is often a bug but not an immediate capacity emergency. Many zombies under the same parent indicate a supervisor or application process that is failing to reap children. In a container, zombie buildup can also reveal that the container entrypoint is not acting as a proper init process, which is why minimal init wrappers are used in some images.

```bash
ps -eo ppid=,stat= | awk '$2 ~ /Z/ {count[$1]++} END {for (p in count) print p, count[p]}' | sort -k2 -nr
```

**Active learning prompt:** A host has load average above its CPU count, but `top` shows almost no CPU usage. Several database and backup processes are in `D` state. What system component would you investigate before tuning application thread pools, and why?

You should investigate the I/O path first: local disk, cloud volume, NFS mount, storage network, or filesystem driver. Load average includes tasks waiting in uninterruptible I/O, so a high value does not always mean CPU pressure. Tuning thread pools can make the situation worse by creating more blocked work against the same failing storage dependency.

Signals are still useful when the process is in a normal interruptible state. `SIGTERM` asks for graceful shutdown, `SIGKILL` forces termination when deliverable, and `SIGSTOP` can freeze a process for inspection. Use them deliberately because signals alter the evidence you are collecting.

```bash
PID="$(pgrep -n sleep || true)"
if [ -n "$PID" ]; then
  ps -o pid,stat,comm -p "$PID"
fi
```

---

## Core Section 5: Use `lsof` to Connect Descriptors to Operational Symptoms

`lsof` answers a deceptively simple question: which process has which file open? In Linux, "file" includes regular files, directories, sockets, pipes, devices, and many kernel-backed handles. That makes `lsof` one of the best tools for explaining disk-full mysteries, port conflicts, unmount failures, descriptor leaks, and hidden connections.

Start with a process-specific view because whole-system `lsof` output can be large. Use numeric output for network investigations so DNS lookups and service-name translation do not slow the command or hide the actual port numbers. This habit also avoids confusing a debugging session with resolver problems.

```bash
PID="$(pgrep -n bash)"
lsof -p "$PID" | sed -n '1,30p'
lsof -p "$PID" -P -n | sed -n '1,30p'
```

When a filesystem remains full after deleting a large file, look for deleted files still held open. The directory entry may be gone, but disk blocks are retained until the last process closes the descriptor. Log rotation incidents often happen this way when a daemon keeps writing to the old file after rotation.

```bash
lsof -nP 2>/dev/null | grep deleted | sed -n '1,20p' || true
```

Port conflicts are another common use case. If a service cannot bind to a port, do not guess which process owns it; ask the kernel through tools that report socket ownership. `lsof -i` is often enough, and the next module will go deeper with `ss`, routing, and packet inspection.

```bash
sudo lsof -iTCP -sTCP:LISTEN -P -n 2>/dev/null | sed -n '1,30p'
sudo lsof -i :22 -P -n 2>/dev/null | sed -n '1,20p'
```

Unmount failures are usually descriptor problems in disguise. If a backup mount, removable disk, or network mount refuses to unmount, some process still has a file, working directory, or mapped object under that mount. `lsof` can identify the holder so you can decide whether to stop a service, move a shell, or wait for a job to finish.

```bash
MOUNT_POINT="/tmp"
lsof +D "$MOUNT_POINT" 2>/dev/null | sed -n '1,20p' || true
```

`lsof +D` recursively scans a directory tree and can be expensive on large filesystems. Use it when you have a specific mount or directory, not as a casual first command against a large production volume. When you only need a process view, `/proc/$PID/fd` is usually cheaper.

```bash
PID="$(pgrep -n bash)"
echo "Fast descriptor view:"
ls -l "/proc/$PID/fd" | sed -n '1,20p'
echo "Richer lsof view:"
lsof -p "$PID" -P -n | sed -n '1,20p'
```

**Worked example:** A deployment fails because the new service cannot bind port 8080. First identify the listener, then inspect its parent and command line. If the owner is an old process from the same service, you may have a shutdown problem; if it is a different service, you may have a configuration collision.

```bash
sudo lsof -iTCP:8080 -sTCP:LISTEN -P -n 2>/dev/null || true
OWNER_PID="$(sudo lsof -tiTCP:8080 -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
if [ -n "$OWNER_PID" ]; then
  ps -o pid,ppid,lstart,stat,comm,args -p "$OWNER_PID"
fi
```

**Active learning prompt:** You find that `/var/log/app.log (deleted)` is still open by a daemon, and `df -h` still shows the filesystem full. Would truncating the visible path help, and what action releases the blocks that are actually consuming space?

Truncating the visible path will not affect the unlinked inode held by the daemon. The blocks are released when the process closes the descriptor, which may happen through a graceful reload, restart, or application-specific log-reopen signal. In some emergency cases, operators truncate via `/proc/$PID/fd/$FD`, but that should be done carefully because it modifies what the running process still has open.

```bash
# Inspect only; do not modify descriptors unless you understand the process.
PID="$(pgrep -n bash)"
ls -l "/proc/$PID/fd" | sed -n '1,20p'
```

Descriptor count over time is often more useful than a single snapshot. If the count grows steadily under normal traffic and never falls, you likely have a leak. If it spikes during peak load and returns to baseline, the limit may be too low or the workload may need backpressure rather than a cleanup bug fix.

```bash
PID="$(pgrep -n bash)"
for i in 1 2 3 4 5; do
  printf '%s descriptors=%s\n' "$(date +%H:%M:%S)" "$(ls /proc/$PID/fd | wc -l)"
  sleep 1
done
```

---

## Core Section 6: Debug Library Calls, Threads, and Containers When Syscalls Are Not Enough

`strace` shows kernel interactions, but some failures occur before the kernel sees anything interesting. A program may allocate memory, format a string, parse a config buffer, call a shared library, or fail inside user-space logic. `ltrace` can reveal library calls for dynamically linked programs, which makes it useful for closed-source binaries and older C applications.

The distinction is practical rather than academic. If you need to know which path a program opened, use `strace`. If you need to know whether it called `malloc`, `strlen`, `getenv`, or a shared-library function before the open, `ltrace` may be more useful. Modern security settings, static binaries, stripped symbols, and language runtimes can limit what `ltrace` shows, so treat it as an optional deeper tool.

```bash
command -v ltrace >/dev/null 2>&1 && ltrace -e getenv,strlen ls /tmp >/tmp/ltrace.out 2>/tmp/ltrace.err || echo "ltrace not installed"
```

Threaded programs add another layer because each thread may be waiting on a different event. Linux represents threads as tasks under `/proc/$PID/task`, and each task has its own status, stack, and wait channel. If the process is alive but only one worker is stuck, inspecting the process as a single unit can hide the useful evidence.

```bash
PID="$(pgrep -n bash)"
ls "/proc/$PID/task" | sed -n '1,20p'
for tid in /proc/"$PID"/task/*; do
  printf '%s ' "$(basename "$tid")"
  cat "$tid/wchan" 2>/dev/null || true
done | sed -n '1,20p'
```

Futex waits are common in threaded applications. A futex is a fast user-space locking primitive with kernel assistance when a thread must sleep. Seeing futex activity in `strace` does not automatically mean the kernel is broken; it often means the application is waiting on a lock, condition variable, or runtime scheduler event.

```bash
PID="$(pgrep -n bash)"
timeout 3s strace -f -e trace=futex -p "$PID" 2>/tmp/futex.trace || true
sed -n '1,20p' /tmp/futex.trace
```

Container debugging uses the same process tools, but you must pay attention to namespaces. A PID inside a container may not match the PID seen from the host. Mount, network, IPC, UTS, user, and PID namespaces can all change what the process sees. `nsenter` lets you enter selected namespaces of a target process so commands run from the same perspective.

```bash
PID="$(pgrep -n bash)"
ls -l "/proc/$PID/ns"
```

When entering namespaces, be explicit and minimal. Entering all namespaces is useful for reproducing a process view, but sometimes you only need the network namespace or mount namespace. Always confirm the target PID belongs to the workload you intend to inspect, especially on hosts with many containers.

```bash
PID="$(pgrep -n bash)"
sudo nsenter --target "$PID" --mount --uts --ipc --net --pid ps -o pid,ppid,stat,comm,args 2>/dev/null | sed -n '1,20p' || true
```

In Kubernetes environments, the practical workflow is to identify the host PID of the container process using the container runtime or node tools, then enter that process's namespaces from the node. This module stays focused on Linux primitives, but the same evidence matters in Kubernetes 1.35 and later: descriptors, limits, states, namespaces, and system calls still explain what the workload is doing.

**Active learning prompt:** A containerized application can reach a service when tested from the host, but the application itself times out. Why might host-level `curl` be misleading, and which namespace would you enter first to test from the application's point of view?

Host-level `curl` uses the host network namespace, routing table, DNS configuration, and firewall context. The application may live in a different network namespace with different routes, DNS, or policy. Enter the target process's network namespace first, then run a minimal connection test from that perspective before changing application configuration.

```bash
PID="$(pgrep -n bash)"
sudo nsenter --target "$PID" --net ip route 2>/dev/null || true
sudo nsenter --target "$PID" --net getent hosts example.com 2>/dev/null || true
```

A senior debugging plan also includes privacy and blast-radius controls. Traces can capture file paths, hostnames, tokens in arguments, environment variables, and snippets of data passed to system calls. Capture to a restricted file, keep the trace window short, and redact before sharing evidence outside the incident team.

```bash
umask 077
PID="$(pgrep -n bash)"
timeout 5s strace -f -tt -T -s 120 -e trace=file,network -p "$PID" -o /tmp/process-debug.trace 2>/dev/null || true
ls -l /tmp/process-debug.trace
```

---

## Did You Know?

- **`/proc/$PID/exe` can point to a deleted binary** — A running process can continue executing an old mapped executable after a deployment replaces or removes the file, which is why process start time and executable symlink evidence matter during rollback investigations.

- **`strace` reports the kernel boundary, not application intent** — A failed `openat` tells you which path the process requested and which error the kernel returned, but you still need application context to explain why that path was chosen.

- **A zombie process has already exited** — The remaining entry exists so the parent can collect exit status, which means the durable fix is usually in the parent or supervisor rather than the zombie itself.

- **Deleted files can still consume disk space** — Removing a filename unlinks a directory entry, but blocks are not released until every process holding that inode closes its descriptor.

---

## Common Mistakes

| Mistake | Why It Hurts | Better Practice |
|---------|--------------|-----------------|
| Attaching unfiltered `strace` to a busy production process | The trace can slow the process, flood output, and expose sensitive arguments while still failing to answer a specific question. | Start with `/proc`, then attach briefly with `timeout`, `-e trace=...`, `-tt`, `-T`, and `-o` to capture a narrow evidence window. |
| Treating `D` state as a process-kill problem | `SIGKILL` cannot complete until the uninterruptible kernel wait returns, so repeated kill commands do not address the blocked I/O path. | Investigate storage, network filesystems, device drivers, and kernel stack clues before escalating to host or storage remediation. |
| Looking only at the process name | Multiple workers, old deployments, child helpers, and restarted supervisors can share similar names, leading you to debug the wrong PID. | Confirm PID, PPID, start time, command line, executable symlink, and process tree before interpreting evidence. |
| Ignoring open deleted files during disk-full incidents | The visible file may be gone, but the process can still hold the inode and keep disk blocks allocated. | Use `lsof | grep deleted` or inspect `/proc/$PID/fd`, then reload or restart the holder when operationally safe. |
| Forgetting child processes during tracing | The parent may only launch the failing helper, while the actual failed `open`, `connect`, or `execve` happens in a child. | Use `strace -f` when shells, supervisors, workers, or pipelines are involved, and capture process syscalls when lifecycle is suspicious. |
| Confusing `strace` and `ltrace` evidence | System calls prove kernel interactions, but library calls and user-space parsing can fail before anything meaningful reaches the kernel. | Use `strace` for files, sockets, processes, and signals; use `ltrace` selectively for dynamically linked library behavior. |
| Inspecting containers only from the host namespace | Host routes, DNS, mounts, and PIDs can differ from the application's view, causing misleading tests. | Identify the target process and use `nsenter` for the relevant namespace, especially network and mount namespaces. |
| Raising limits without confirming leaks | Increasing `nofile` can hide a descriptor leak until the next outage is larger and harder to recover. | Compare current descriptor count with limits, sample descriptor types, watch growth over time, and fix lifecycle cleanup when growth is unbounded. |

---

## Quiz

### Question 1

Your team deploys a new build of a Python worker. Four hours later, jobs stop completing, logs go quiet, and `systemctl status` still shows the service as active. You have the worker PID. What evidence would you gather first, and how would that evidence change your next command?

<details>
<summary>Show Answer</summary>

Start with low-risk process evidence: `ps -o pid,ppid,lstart,stat,wchan,comm,args -p "$PID"`, then inspect `/proc/$PID/fd`, `/proc/$PID/limits`, and relevant fields from `/proc/$PID/status`. If the process is in `D` state, the next path is I/O investigation and possibly `/proc/$PID/stack`; if it is in `S` state, inspect descriptors and attach a short filtered `strace` to see the blocking syscall; if it is in `R` state with high CPU, system-call tracing may be less useful than sampling or profiling. The key is that the state and wait channel decide the next tool, rather than using the same trace command for every incident.

</details>

### Question 2

A Node.js API starts returning "Too many open files" after a traffic spike. The service owner asks you to increase `LimitNOFILE` immediately because it will make the error disappear. How do you evaluate whether that is a safe mitigation or whether it hides a leak?

<details>
<summary>Show Answer</summary>

Compare the current descriptor count with the process limit, then inspect what those descriptors are. Use `grep 'Max open files' /proc/$PID/limits`, `ls /proc/$PID/fd | wc -l`, and `lsof -p "$PID" -P -n` to classify descriptors as sockets, files, pipes, or deleted files. Sample the count over time under stable traffic. If descriptors rise and never return to baseline, increasing the limit is only a temporary mitigation and the application likely leaks resources. If descriptors spike during known load and fall afterward, a higher limit plus backpressure may be reasonable while the team validates capacity.

</details>

### Question 3

A closed-source backup agent hangs every night during a filesystem scan. Logs stop at "scanning mounted volumes," and `ps` shows the process in `D` state with very low CPU usage. What conclusion should you avoid, and what should you inspect instead?

<details>
<summary>Show Answer</summary>

Avoid concluding that the application is CPU-starved or that `kill -9` will force immediate recovery. `D` state means the process is in uninterruptible sleep, commonly waiting for disk, network filesystem, or device I/O. Inspect `ps -o pid,stat,wchan`, `/proc/$PID/stack` if available, mount health, storage latency, NFS server status, kernel logs, and any volume touched by the scan. The root cause is likely below the application layer, so tuning application workers or repeatedly sending signals misses the mechanism.

</details>

### Question 4

A service fails only in production because it cannot find a configuration file, but the application log reports only "startup failed." You can reproduce the startup command safely in a staging shell. Which trace would you run, what errors would you look for, and how would you interpret the result?

<details>
<summary>Show Answer</summary>

Run a file-focused trace such as `strace -e trace=file -o /tmp/startup.trace ./service-command` and search for `openat`, `stat`, `access`, `ENOENT`, and `EACCES`. `ENOENT` means the process asked for a path the kernel could not find, so check working directory, environment variables, search paths, and packaging. `EACCES` means the file likely exists but permissions or security controls prevented access. A successful open followed by a later failure means the config file was found and the problem may be parsing or application-level validation rather than file discovery.

</details>

### Question 5

A containerized web service times out when connecting to an internal API. From the node host, `curl` to the same API succeeds, so a teammate says the network is fine. How do you test the claim from the process's point of view?

<details>
<summary>Show Answer</summary>

Host-level `curl` proves only that the host network namespace can reach the API. The containerized process may have a different network namespace, DNS configuration, route table, or policy. Identify the host PID for the process, inspect `/proc/$PID/ns`, then enter the network namespace with `sudo nsenter --target "$PID" --net` and run minimal checks such as `ip route`, `getent hosts`, and a connection test. If the command fails inside the namespace but succeeds on the host, the problem is in the workload's network context rather than the external API itself.

</details>

### Question 6

After log rotation, `rm` shows that a huge old log file is gone, but `df -h` still reports the filesystem as full. The application is still running and writes new logs elsewhere. What process-debugging evidence explains the discrepancy, and what action releases the space?

<details>
<summary>Show Answer</summary>

Use `lsof | grep deleted` or inspect `/proc/$PID/fd` for descriptors pointing to deleted files. The process may still hold the old unlinked log inode open, so the directory entry is gone but the disk blocks remain allocated. The space is released when the process closes the descriptor, usually through a graceful log reopen, reload, or restart. Truncating the new visible log path will not release blocks held by the deleted inode.

</details>

### Question 7

A shell wrapper starts a helper binary that fails quickly, but tracing the wrapper without options shows no useful failed `openat` or `connect` calls. What mistake might you have made, and how would you rerun the trace?

<details>
<summary>Show Answer</summary>

You may have traced only the parent shell while the failing behavior occurred in a child process after `fork`, `clone`, or `execve`. Rerun with `-f` so `strace` follows child processes, and filter for the theory you are testing. For example, use `strace -f -e trace=process,file -o /tmp/wrapper.trace ./wrapper.sh` for missing files or `strace -f -e trace=process,network -o /tmp/wrapper.trace ./wrapper.sh` for connection failures. The process lifecycle events help connect the parent wrapper to the child that actually failed.

</details>

---

## Hands-On Exercise

### Objective

You will debug live Linux processes using the same progression you would use during an incident: identify the process, inspect low-risk `/proc` evidence, classify descriptors, trace a narrow behavior, interpret state, and enter a namespace when possible. The exercise uses ordinary local commands so you can practice without a special service stack.

### Part 1: Establish a Safe Debugging Workspace

Create a temporary directory and record the tools available on your machine. This prevents your evidence files from mixing with unrelated shell output and forces you to notice when optional tools such as `strace`, `lsof`, or `ltrace` are missing.

```bash
WORKDIR="$(mktemp -d)"
echo "$WORKDIR"
command -v ps
command -v strace || true
command -v lsof || true
command -v ltrace || true
command -v nsenter || true
```

- [ ] You created a temporary workspace and can explain where trace files will be written.
- [ ] You confirmed whether `strace`, `lsof`, `ltrace`, and `nsenter` are installed.
- [ ] You understand which later steps may need `sudo` on your machine.

### Part 2: Inspect a Known Process Through `/proc`

Start a harmless long-running process, then inspect its command line, executable, working directory, limits, status, and descriptors. The goal is to build a baseline without tracing or changing the process.

```bash
sleep 600 &
TARGET_PID=$!
echo "TARGET_PID=$TARGET_PID"
ps -o pid,ppid,lstart,stat,wchan,comm,args -p "$TARGET_PID"
tr '\0' ' ' < "/proc/$TARGET_PID/cmdline"
printf '\n'
ls -l "/proc/$TARGET_PID/exe"
ls -l "/proc/$TARGET_PID/cwd"
grep -E 'State|Threads|VmRSS|VmSize|voluntary_ctxt_switches|nonvoluntary_ctxt_switches' "/proc/$TARGET_PID/status"
grep 'Max open files' "/proc/$TARGET_PID/limits"
ls -l "/proc/$TARGET_PID/fd"
```

- [ ] You identified the parent PID and process state of the target process.
- [ ] You compared command-line evidence with the executable symlink.
- [ ] You found the open-file limit and counted current descriptors.
- [ ] You inspected descriptor targets without using a tracing tool.

### Part 3: Trace a Narrow System Call Pattern

Use `strace` against small commands first so you can read the output before attaching to a live process. Separate program output from trace output, then compare a file trace with a process trace.

```bash
strace -e trace=file ls /tmp >"$WORKDIR/ls.out" 2>"$WORKDIR/ls-file.trace"
sed -n '1,20p' "$WORKDIR/ls-file.trace"
strace -f -e trace=process bash -c 'printf hello | wc -c' >"$WORKDIR/pipeline.out" 2>"$WORKDIR/pipeline-process.trace"
sed -n '1,40p' "$WORKDIR/pipeline-process.trace"
```

- [ ] You captured trace output separately from command output.
- [ ] You found at least one file-related syscall in the `ls` trace.
- [ ] You found process lifecycle calls in the pipeline trace.
- [ ] You can explain why `-f` matters for wrapper scripts and pipelines.

### Part 4: Attach Briefly to a Running Process

Attach to the `sleep` process with a timeout and observe what the process is waiting on. A sleeping process is intentionally quiet, so the useful lesson is how to attach, detach, and capture evidence without leaving a tracer running.

```bash
timeout 3s strace -tt -T -p "$TARGET_PID" -o "$WORKDIR/live-sleep.trace" 2>/dev/null || true
sed -n '1,30p' "$WORKDIR/live-sleep.trace"
ps -o pid,stat,wchan,comm,args -p "$TARGET_PID"
```

- [ ] You attached to a live process for a bounded amount of time.
- [ ] You captured the trace to a file instead of flooding the terminal.
- [ ] You checked the process state after tracing.
- [ ] You can explain why a quiet trace may be expected for `sleep`.

### Part 5: Create and Diagnose an Open Deleted File

This scenario reproduces a common disk-full incident safely in your temporary directory. A process opens a file, the directory entry is removed, and the descriptor remains open until the process exits.

```bash
python_script="$WORKDIR/hold_deleted.py"
printf '%s\n' \
'import os, time' \
'path = os.environ["HOLD_FILE"]' \
'f = open(path, "w")' \
'f.write("held data\n")' \
'f.flush()' \
'os.unlink(path)' \
'print(os.getpid(), flush=True)' \
'time.sleep(600)' > "$python_script"
HOLD_FILE="$WORKDIR/held.log" .venv/bin/python "$python_script" >"$WORKDIR/holder.pid" &
HOLDER_PID="$(cat "$WORKDIR/holder.pid")"
echo "HOLDER_PID=$HOLDER_PID"
ls -l "$WORKDIR" | sed -n '1,20p'
ls -l "/proc/$HOLDER_PID/fd" | sed -n '1,20p'
lsof -p "$HOLDER_PID" -P -n 2>/dev/null | sed -n '1,30p' || true
```

- [ ] You created a process that holds an unlinked file open.
- [ ] You found the deleted file through `/proc/$PID/fd` or `lsof`.
- [ ] You can explain why the file is absent from the directory but still exists as an open inode.
- [ ] You know that closing the descriptor or stopping the process releases the space.

### Part 6: Compare Descriptor Count and Limits

Use the holder process or your shell to compare descriptor count with resource limits. This step prepares you to investigate real `EMFILE` errors without immediately changing service configuration.

```bash
grep 'Max open files' "/proc/$HOLDER_PID/limits"
ls "/proc/$HOLDER_PID/fd" | wc -l
for i in 1 2 3 4 5; do
  printf '%s descriptors=%s\n' "$(date +%H:%M:%S)" "$(ls /proc/$HOLDER_PID/fd | wc -l)"
  sleep 1
done
```

- [ ] You found the soft and hard open-file limits.
- [ ] You measured current descriptor usage more than once.
- [ ] You can distinguish a stable descriptor count from a growing leak pattern.
- [ ] You can explain why raising limits without leak evidence is risky.

### Part 7: Inspect Process States and Parent Relationships

Look for unusual states on your system, then inspect the parent-child relationship for your exercise processes. You may not have any `D` or `Z` processes, which is normal; the goal is to practice the search pattern.

```bash
ps -eo pid,ppid,stat,wchan,comm,args | sed -n '1,30p'
ps -eo pid,ppid,stat,wchan,comm,args | awk '$3 ~ /D/ {print}' || true
ps -eo pid,ppid,stat,wchan,comm,args | awk '$3 ~ /Z/ {print}' || true
ps -o pid,ppid,stat,wchan,comm,args -p "$TARGET_PID","$HOLDER_PID"
```

- [ ] You listed process states with explicit `ps` columns.
- [ ] You searched for uninterruptible and zombie processes.
- [ ] You identified the parent of each exercise process.
- [ ] You can explain why a zombie fix usually targets the parent.

### Part 8: Inspect Namespace Context

Use your target process to inspect namespace links. If you have permission, enter the network namespace and compare the route view. On a normal host process, this may look identical to your shell, but the command pattern is the same one used for containers.

```bash
ls -l "/proc/$TARGET_PID/ns"
sudo nsenter --target "$TARGET_PID" --net ip route 2>/dev/null || ip route 2>/dev/null || true
sudo nsenter --target "$TARGET_PID" --mount pwd 2>/dev/null || true
```

- [ ] You inspected namespace identifiers for the target process.
- [ ] You attempted a namespace-aware command safely.
- [ ] You can explain why host-level tests may not match a container process.
- [ ] You know which namespace you would enter first for a network timeout.

### Part 9: Clean Up

Stop the processes you created and remove the temporary directory. Cleanup is part of operational discipline because stray debug processes and trace files can confuse later investigations.

```bash
kill "$TARGET_PID" "$HOLDER_PID" 2>/dev/null || true
wait "$TARGET_PID" "$HOLDER_PID" 2>/dev/null || true
rm -rf "$WORKDIR"
```

- [ ] You stopped the long-running exercise processes.
- [ ] You removed temporary traces and scripts.
- [ ] You verified that no exercise process remains.
- [ ] You can repeat the workflow on a real service with a narrower, safer evidence plan.

---

## Next Module

In **[Module 6.4: Network Debugging](../module-6.4-network-debugging/)**, you will extend the same troubleshooting discipline to sockets, routes, DNS, packet captures, and end-to-end network path analysis.
