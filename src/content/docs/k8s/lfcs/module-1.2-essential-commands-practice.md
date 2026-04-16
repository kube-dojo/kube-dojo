---
title: "LFCS Essential Commands Practice"
slug: k8s/lfcs/module-1.2-essential-commands-practice
sidebar:
  order: 102
---

> **LFCS Track** | Complexity: `[MEDIUM]` | Time: 45-60 min

**Reading Time**: 45-60 minutes

## Prerequisites

Before starting this module:
- **Required**: [LFCS Exam Strategy and Workflow](./module-1.1-exam-strategy-and-workflow/) for the pacing model
- **Required**: [Module 1.3: Filesystem Hierarchy](/linux/foundations/system-essentials/module-1.3-filesystem-hierarchy/) for paths, links, and file layout
- **Helpful**: [Module 7.2: Text Processing](/linux/operations/shell-scripting/module-7.2-text-processing/) for pipes, filters, and search

## What You'll Be Able to Do

After this module, you will be able to:
- move quickly through routine LFCS command tasks without freezing up
- create, inspect, copy, move, search, and archive files from the terminal
- combine redirection, pipes, globbing, and text filters into reliable one-liners
- verify command results immediately instead of assuming they worked
- choose the fastest safe command for the state you need to create

## Why This Module Matters

Essential commands are the exam's entry fee. If you can navigate files, manipulate text, search system state, and confirm your work quickly, everything else becomes easier.

LFCS does not reward perfect explanations. It rewards correct terminal actions under time pressure. This module is designed to make the obvious commands automatic so you spend less attention on mechanics and more on the actual task.

## The Command Families You Must Own

### Files and Directories

```bash
pwd
ls -lah
cd /path/to/dir
mkdir -p /srv/app/{config,data,logs}
cp source.txt dest.txt
mv oldname.txt newname.txt
rm -r temp-dir
touch /tmp/checkpoint
```

### Links and File Metadata

```bash
ln file-a file-a.hardlink
ln -s /etc/systemd/system/my.service /tmp/my.service
stat /etc/hosts
file /bin/ls
```

### Search and Read

```bash
find /var/log -name "*.log"
find /etc -type f -mtime -1
grep -R "error" /var/log
sed -n '1,20p' /etc/fstab
awk '{print $1, $3}' /etc/passwd
```

### Redirection and Pipes

```bash
command > out.txt
command 2> err.txt
command >> append.txt
command | grep -i warning
cat input.txt | sort | uniq -c | sort -nr
```

### Archives and Compression

```bash
tar -czf backup.tgz /etc/myapp
tar -xzf backup.tgz -C /tmp/restore
gzip file.txt
gunzip file.txt.gz
```

## Practice Drills

### Drill 1: File Tree Recovery

Set up a small directory tree, then recreate it from memory:
- make three directories under `/tmp`
- place one text file in each
- create one hard link and one symbolic link
- confirm the difference with `ls -li` and `readlink`

What this trains:
- filesystem navigation
- link semantics
- fast metadata checking

### Drill 2: Search Under Pressure

Use `find`, `grep`, `sed`, and `awk` on a live system:
- locate a file by name
- search for a string in a log directory
- print the first 10 lines of a config file
- extract one field from a colon-delimited file

What this trains:
- pattern recognition
- text filtering
- choosing the right tool instead of overcomplicating the task

### Drill 3: Archive and Restore

Create a backup, move it, and restore it:
- archive a directory with `tar`
- compress it
- restore it to a new path
- verify file count and a sample checksum or timestamp

What this trains:
- safe backup habits
- archive creation and extraction
- post-action verification

### Drill 4: Redirect Correctly

Practice writing output and errors separately:
- send normal output to a file
- send errors to a different file
- append to an existing file
- combine multiple commands in a pipeline

What this trains:
- exam-style shell control
- debugging output without losing context

## Verification Checklist

Before you move on, confirm:
- you know the difference between `>` and `>>`
- you can explain when to use `cp` vs `mv`
- you can find a file by name and by content
- you can inspect file type, ownership, and permissions quickly
- you can create and restore a simple archive without looking up syntax

## Common Failure Modes

- using `cat` for everything instead of choosing a focused reader
- forgetting that stderr is separate from stdout
- over-editing a file when a small change is enough
- searching the whole filesystem when a narrower path would do
- assuming a command worked without checking the result

## Exam Habit

When a task looks simple, do not rush past verification. A correct command that produced the wrong state is still wrong.

The fastest LFCS candidates are not the ones who type the most. They are the ones who use a small set of commands very deliberately and can prove the result immediately.

## Summary

Essential commands are not the whole exam, but they are the base layer that keeps every other task from becoming expensive.

If you can navigate, inspect, search, transform, and archive comfortably, then the rest of LFCS becomes a sequence of administrative problems instead of a syntax quiz.
