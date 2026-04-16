---
title: "LFCS Running Systems and Networking Practice"
slug: k8s/lfcs/module-1.3-running-systems-and-networking-practice
sidebar:
  order: 103
---

> **LFCS Track** | Complexity: `[COMPLEX]` | Time: 45-60 min

**Reading Time**: 45-60 minutes

## Prerequisites

Before starting this module:
- **Required**: [LFCS Exam Strategy and Workflow](./module-1.1-exam-strategy-and-workflow/)
- **Required**: [LFCS Essential Commands Practice](./module-1.2-essential-commands-practice/)
- **Helpful**: [Module 1.2: Processes & systemd](/linux/foundations/system-essentials/module-1.2-processes-systemd/)
- **Helpful**: [Module 3.1: TCP/IP Essentials](/linux/foundations/networking/module-3.1-tcp-ip-essentials/)
- **Helpful**: [Module 3.4: iptables & netfilter](/linux/foundations/networking/module-3.4-iptables-netfilter/)

## What You'll Be Able To Do

After this module, you will be able to:
- inspect and repair running services without guessing
- manage systemd units, targets, and logs from the CLI
- schedule recurring or one-time tasks with `cron` and `at`
- validate and repair basic networking state under exam pressure
- load, inspect, and unload safe kernel modules with evidence
- separate temporary route fixes from boot-persistent network configuration
- work through a simple troubleshooting ladder instead of jumping straight to random fixes

## Why This Module Matters

LFCS often hides the real problem behind a symptom. A service fails because the port is wrong, a route is missing, a config file is malformed, or a task never got scheduled. This module is about reading the machine correctly before changing it.

If you can operate `systemd`, inspect logs, and confirm network state cleanly, you can recover from many exam tasks without panic.

## The Running-System Troubleshooting Ladder

When something is broken, move in this order:
1. process
2. unit
3. log
4. config
5. network
6. persistence

That sequence keeps you from guessing too early.

### Process Inspection

```bash
ps aux | grep nginx
top
pgrep -a ssh
kill -TERM <pid>
kill -KILL <pid>
nice -n 10 long-job
renice 5 -p <pid>
```

### systemd Control

```bash
systemctl status ssh
systemctl start nginx
systemctl stop nginx
systemctl enable nginx
systemctl disable nginx
systemctl restart nginx
systemctl list-units --type=service
systemctl get-default
systemctl set-default multi-user.target
```

### Logs and Boot State

```bash
journalctl -u nginx
journalctl -xe
journalctl -b
journalctl -b -1
systemctl --failed
systemctl isolate rescue.target
shutdown -r +5 "LFCS practice reboot"
shutdown -c
```

## Practice Drills

### Drill 1: Rescue a Failing Service

Simulate a broken service:
- stop a service
- change its config in a way that prevents start
- use `systemctl status` and `journalctl` to find the failure
- fix the config
- restart and verify

What this trains:
- reading service state
- using logs as evidence
- making a minimal correction

### Boot Targets Quick Reference

The exam assumes you know these without looking them up:

| Target | Old Runlevel | Purpose |
|--------|-------------|---------|
| `poweroff.target` | 0 | Halt the system |
| `rescue.target` | 1 | Single-user, minimal services |
| `multi-user.target` | 3 | Full multi-user, no GUI |
| `graphical.target` | 5 | Multi-user with display manager |
| `reboot.target` | 6 | Reboot |
| `emergency.target` | — | Minimal root shell, no services |

Key distinction: `rescue.target` mounts filesystems and starts basic services. `emergency.target` gives you a root shell with almost nothing running — use it when rescue itself is broken.

**Changing targets at runtime vs. at boot:**

```bash
# Runtime — switch now without changing default
systemctl isolate rescue.target

# Persistent — change what boots next time
systemctl set-default multi-user.target
systemctl get-default

# GRUB override — append to kernel command line during boot:
# systemd.unit=rescue.target
```

### Drill 2: Rebuild a Boot Target

Practice switching the default target:
- inspect the current default with `systemctl get-default`
- set `multi-user.target` as default
- confirm with `systemctl get-default`
- isolate into `rescue.target` (only in a disposable VM)
- switch the default back to its original value
- inspect previous boot logs with `journalctl -b -1`

What this trains:
- boot-target fluency
- recovery without rebooting blindly
- confidence with isolate vs. set-default

### Cron and At — Syntax and Exam Patterns

**Crontab field layout:**

```
┌───────────── minute (0-59)
│ ┌───────────── hour (0-23)
│ │ ┌───────────── day of month (1-31)
│ │ │ ┌───────────── month (1-12)
│ │ │ │ ┌───────────── day of week (0-7, 0 and 7 = Sunday)
│ │ │ │ │
* * * * *  command
```

**Common exam patterns:**

```bash
# every 15 minutes
*/15 * * * * /usr/local/bin/healthcheck.sh

# daily at 2:30 AM
30 2 * * * /usr/local/bin/backup.sh

# every Monday at 6 AM
0 6 * * 1 /usr/local/bin/weekly-report.sh

# first of every month at midnight
0 0 1 * * /usr/local/bin/monthly-rotate.sh
```

**Crontab management:**

```bash
crontab -e                  # edit current user's crontab
crontab -l                  # list current user's crontab
crontab -r                  # remove current user's crontab
sudo crontab -u alice -e    # edit another user's crontab
sudo crontab -u alice -l    # list another user's crontab
```

**System-wide cron directories (no crontab needed):**

```bash
ls /etc/cron.d/             # drop-in cron files
ls /etc/cron.daily/         # scripts that run daily
ls /etc/cron.hourly/        # scripts that run hourly
ls /etc/cron.weekly/        # scripts that run weekly
```

**at — one-time scheduled tasks:**

```bash
echo "/usr/local/bin/cleanup.sh" | at now + 30 minutes
echo "/usr/local/bin/migrate.sh" | at 02:00 tomorrow
atq                         # list pending at jobs
atrm 3                      # remove job number 3
at -c 3                     # show job 3 contents
```

**Access control:**

```bash
cat /etc/at.allow           # if this exists, only listed users can use at
cat /etc/at.deny            # if allow doesn't exist, deny blocks listed users
cat /etc/cron.allow
cat /etc/cron.deny
```

### Drill 3: Schedule Work

Use both `cron` and `at` with full verification:

**Part A — cron:**
- run `crontab -l` to see if anything is already scheduled
- add a job that runs every 5 minutes: `*/5 * * * * echo "heartbeat" >> /tmp/cron-test.log`
- verify with `crontab -l`
- wait 5 minutes and check `/tmp/cron-test.log`
- remove the job with `crontab -e` or `crontab -r`
- confirm removal with `crontab -l`

**Part B — at:**
- schedule a one-time job: `echo "echo done > /tmp/at-test.log" | at now + 1 minute`
- list it with `atq`
- inspect the job with `at -c <job_number>`
- after it runs, verify `/tmp/at-test.log` exists
- clean up: `rm /tmp/at-test.log`

**Part C — access control:**
- check whether `/etc/cron.allow` or `/etc/cron.deny` exists
- create a test user, add them to `/etc/at.deny`, and verify they cannot schedule at jobs
- remove the deny entry and clean up

What this trains:
- crontab syntax from memory
- at queue management
- access control awareness
- cleanup discipline

### Drill 4: Network Triage

Use a simple connectivity ladder:
- verify link state
- check IP address assignment
- inspect the route table
- test DNS resolution
- verify service reachability on the expected port

Useful commands:

```bash
ip addr
ip route
ip route add 10.20.30.0/24 via 192.168.1.1
ip route del 10.20.30.0/24 via 192.168.1.1
ss -tulpen
ping -c 3 8.8.8.8
getent hosts example.com
nmcli device status
systemctl is-enabled NetworkManager
```

### Kernel Module Workflow

Most LFCS kernel-module tasks are operational, not magical. You need to identify the module, confirm what it does, load it, verify the result, and remove it cleanly when the task is done.

**Inspection and runtime loading:**

```bash
lsmod                           # list all loaded modules
lsmod | grep '^dummy'           # check if a specific module is loaded
modinfo dummy                   # show module description, parameters, dependencies
sudo modprobe dummy             # load module (resolves dependencies automatically)
sudo modprobe -r dummy          # unload module
```

**Persistent module loading (survives reboot):**

```bash
# Load at every boot — add a file in /etc/modules-load.d/
echo "dummy" | sudo tee /etc/modules-load.d/dummy.conf

# Verify the file is in place
cat /etc/modules-load.d/dummy.conf
```

**Blacklisting a module (prevent loading):**

```bash
# Prevent a module from loading automatically
echo "blacklist pcspkr" | sudo tee /etc/modprobe.d/blacklist-pcspkr.conf

# Verify
grep pcspkr /etc/modprobe.d/*.conf
```

**Module parameters:**

```bash
# Show available parameters
modinfo -p dummy

# Load with a parameter
sudo modprobe dummy numdummies=2

# Check current parameter value (if module exposes it)
cat /sys/module/dummy/parameters/numdummies 2>/dev/null
```

**Key distinction**: `insmod` loads a module by file path and does not resolve dependencies. `modprobe` loads by name and handles dependencies. The exam expects `modprobe`.

### Static Routes — Temporary vs. Persistent

The exam tests whether you know the difference between "works now" and "works after reboot."

**Temporary routes (lost on reboot):**

```bash
# Add a route
sudo ip route add 10.20.30.0/24 via 192.168.1.1

# Add a default gateway
sudo ip route add default via 192.168.1.1

# Verify
ip route show
ip route get 10.20.30.5

# Remove
sudo ip route del 10.20.30.0/24 via 192.168.1.1
```

**Persistent routes on Ubuntu 22.04 (Netplan):**

```yaml
# /etc/netplan/01-static-routes.yaml
network:
  version: 2
  ethernets:
    ens33:
      routes:
        - to: 10.20.30.0/24
          via: 192.168.1.1
```

```bash
sudo netplan apply
ip route show | grep 10.20.30
```

**Persistent routes with NetworkManager (if Netplan is not in use):**

```bash
sudo nmcli connection modify "Wired connection 1" +ipv4.routes "10.20.30.0/24 192.168.1.1"
sudo nmcli connection up "Wired connection 1"
```

### Network Services at Boot

LFCS expects you to prove that a network service survives reboot, not just that it runs now.

**Standard pattern:**

```bash
# Check what manages networking
systemctl is-active NetworkManager
systemctl is-active systemd-networkd

# Ensure the right service is enabled at boot
systemctl is-enabled NetworkManager
sudo systemctl enable NetworkManager

# Check a specific network-facing service
systemctl is-enabled ssh
sudo systemctl enable --now ssh
ss -tlnp | grep :22
```

**Verify persistence:**

```bash
# After enabling, confirm the symlink exists
ls -l /etc/systemd/system/multi-user.target.wants/ | grep ssh

# Or use:
systemctl list-unit-files --type=service --state=enabled | grep ssh
```

### Drill 5: Static Routes and Network Services at Boot

Practice the difference between "fixed right now" and "fixed after reboot":

**Part A — temporary route:**
- add a route to `10.99.0.0/16` via your default gateway
- verify with `ip route show`
- test reachability with `ip route get 10.99.0.1`
- remove the route
- verify it is gone

**Part B — persistent route (Netplan):**
- create a Netplan YAML that adds the same route
- apply with `sudo netplan apply`
- verify the route appears in `ip route show`
- remove the YAML and reapply to clean up

**Part C — network service persistence:**
- pick a service (e.g., `ssh`)
- check if it is enabled at boot with `systemctl is-enabled`
- if not, enable it
- verify the enable symlink exists
- confirm the service is listening with `ss -tlnp`

What this trains:
- route-table fluency
- the Netplan workflow that Ubuntu 22.04 actually uses
- service persistence awareness
- temporary versus persistent networking changes

### Drill 6: Kernel Module Practice

Use a safe module such as `dummy` if it exists:
- inspect it with `modinfo`
- load it with `modprobe`
- confirm it appears in `lsmod`
- remove it
- explain how you would make module loading persistent if the task required it

What this trains:
- kernel-module evidence gathering
- safe load and unload workflow
- runtime versus persistent module state

### Drill 7: Shutdown and Recovery Discipline

Practice the boot and recovery tasks candidates often avoid:
- inspect the default target
- switch to `multi-user.target`
- isolate into `rescue.target` in a disposable practice environment
- schedule a reboot
- cancel the reboot
- inspect both the current and previous boot logs

What this trains:
- target and recovery fluency
- safe shutdown control
- reading boot history instead of guessing

## SSH and Remote Access

LFCS can include remote administration tasks, so you should be comfortable with:
- connecting with `ssh`
- copying files with `scp`
- checking host keys and known hosts
- verifying that the service is enabled and reachable

```bash
ssh user@server
scp file.txt user@server:/tmp/
ssh -v user@server
```

## Verification Checklist

Before you move on, confirm:
- you can read `systemctl status` output without flinching
- you can explain why a service is failing from the logs
- you can change the default target and verify it
- you know the difference between `rescue.target` and `emergency.target`
- you can write a crontab entry from memory using the five-field format
- you can schedule and remove both `cron` and `at` jobs
- you know where `cron.allow` and `cron.deny` live
- you can load and unload a kernel module and prove the result with `lsmod`
- you can make module loading persistent via `/etc/modules-load.d/`
- you can blacklist a module via `/etc/modprobe.d/`
- you can tell the difference between link, IP, route, DNS, and firewall problems
- you can add a temporary static route and explain where persistent routes go on Ubuntu 22.04
- you can verify a network service is enabled at boot and listening on its port
- you can remove a scheduled job after testing it

## Common Failure Modes

- restarting a service repeatedly without reading its logs
- changing the wrong unit file or the wrong connection profile
- assuming DNS is broken when the route is missing
- editing persistent network config before proving the route change solves the problem
- loading a module before checking what it is supposed to do
- forgetting that scheduled tasks need cleanup after testing
- rebooting too early instead of verifying state first

## Summary

Running-system work is LFCS's recovery layer. It turns a machine from "looks broken" into "understood and repaired."

If you can inspect service state, chase the error into logs, and confirm network behavior without wandering, you are ready for the kinds of problems that steal time from weaker candidates.
