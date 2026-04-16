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
systemctl --failed
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

### Drill 2: Rebuild a Boot Target

Practice switching the default target:
- inspect the current default
- set a non-graphical target
- confirm the new default
- switch it back

What this trains:
- boot-target fluency
- recovery without rebooting blindly

### Drill 3: Schedule Work

Use both `cron` and `at`:
- create a one-time delayed task with `at`
- create a recurring task with `crontab -e`
- inspect scheduled jobs
- remove them after verification

What this trains:
- time-based task control
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
ss -tulpen
ping -c 3 8.8.8.8
getent hosts example.com
nmcli device status
```

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
- you can tell the difference between link, IP, route, DNS, and firewall problems
- you can remove a scheduled job after testing it

## Common Failure Modes

- restarting a service repeatedly without reading its logs
- changing the wrong unit file or the wrong connection profile
- assuming DNS is broken when the route is missing
- forgetting that scheduled tasks need cleanup after testing
- rebooting too early instead of verifying state first

## Summary

Running-system work is LFCS's recovery layer. It turns a machine from "looks broken" into "understood and repaired."

If you can inspect service state, chase the error into logs, and confirm network behavior without wandering, you are ready for the kinds of problems that steal time from weaker candidates.
