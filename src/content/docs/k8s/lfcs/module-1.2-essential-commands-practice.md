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

LFCS tests several archive formats. Know the flags cold — you will not have time to look them up.

**tar with different compressors:**

```bash
# gzip (fastest, most common)
tar -czf backup.tar.gz /etc/myapp
tar -xzf backup.tar.gz -C /tmp/restore

# bzip2 (smaller archives, slower)
tar -cjf backup.tar.bz2 /etc/myapp
tar -xjf backup.tar.bz2 -C /tmp/restore

# xz (smallest archives, slowest)
tar -cJf backup.tar.xz /etc/myapp
tar -xJf backup.tar.xz -C /tmp/restore
```

**Standalone compression tools:**

```bash
gzip file.txt          # produces file.txt.gz, removes original
gunzip file.txt.gz     # restores file.txt
bzip2 file.txt         # produces file.txt.bz2
bunzip2 file.txt.bz2
xz file.txt            # produces file.txt.xz
unxz file.txt.xz
```

**zip/unzip (sometimes tested):**

```bash
zip -r backup.zip /srv/data
unzip backup.zip -d /tmp/restore
```

**cpio (rare but in the blueprint):**

```bash
find /etc/myapp -print | cpio -ov > backup.cpio
cpio -idv < backup.cpio
```

**Quick reference — compression flag in tar:**

| Flag | Compressor | Extension |
|------|-----------|-----------|
| `-z` | gzip | `.tar.gz` / `.tgz` |
| `-j` | bzip2 | `.tar.bz2` |
| `-J` | xz | `.tar.xz` |

**Archive verification — always prove the archive before moving on:**

```bash
tar -tzf backup.tar.gz             # list contents without extracting
tar -tjf backup.tar.bz2
tar -tJf backup.tar.xz
md5sum backup.tar.gz > backup.md5  # create checksum
md5sum -c backup.md5               # verify later
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

### Drill 3: Archive and Restore Under Time Pressure

Practice the full backup lifecycle with each major format. Set a timer — 5 minutes total for all three.

**Round 1 — gzip:**

```bash
mkdir -p /tmp/drill3/source && echo "data" > /tmp/drill3/source/file1.txt
tar -czf /tmp/drill3/backup.tar.gz -C /tmp/drill3 source
tar -tzf /tmp/drill3/backup.tar.gz
tar -xzf /tmp/drill3/backup.tar.gz -C /tmp/drill3/restore-gz
diff /tmp/drill3/source/file1.txt /tmp/drill3/restore-gz/source/file1.txt
```

**Round 2 — bzip2:**

```bash
tar -cjf /tmp/drill3/backup.tar.bz2 -C /tmp/drill3 source
tar -tjf /tmp/drill3/backup.tar.bz2
tar -xjf /tmp/drill3/backup.tar.bz2 -C /tmp/drill3/restore-bz2
```

**Round 3 — xz:**

```bash
tar -cJf /tmp/drill3/backup.tar.xz -C /tmp/drill3 source
tar -tJf /tmp/drill3/backup.tar.xz
tar -xJf /tmp/drill3/backup.tar.xz -C /tmp/drill3/restore-xz
```

**Verification pass (always do this):**

```bash
find /tmp/drill3/restore-gz -type f | wc -l
md5sum /tmp/drill3/source/file1.txt /tmp/drill3/restore-gz/source/file1.txt
```

What this trains:
- flag muscle memory for all three compression formats
- list-before-extract habit
- verification as the last step, not an afterthought
- working fast without skipping proof

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
