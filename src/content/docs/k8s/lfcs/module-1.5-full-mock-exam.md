---
title: "LFCS Full Mock Exam"
slug: k8s/lfcs/module-1.5-full-mock-exam
sidebar:
  order: 105
---

> **LFCS Track** | Complexity: `[COMPLEX]` | Time: 90-120 min

**Reading Time**: 20-30 minutes to brief, then a full timed run

## Prerequisites

Before starting this module:
- **Required**: [LFCS Exam Strategy and Workflow](./module-1.1-exam-strategy-and-workflow/)
- **Required**: [LFCS Essential Commands Practice](./module-1.2-essential-commands-practice/)
- **Required**: [LFCS Running Systems and Networking Practice](./module-1.3-running-systems-and-networking-practice/)
- **Required**: [LFCS Storage, Services, and Users Practice](./module-1.4-storage-services-and-users-practice/)
- **Helpful**: the full Linux track sections on essentials, networking, operations, and security

## What You'll Be Able To Do

After this module, you will be able to:
- run an LFCS-style practice session under time pressure
- prioritize easy points without getting trapped on one hard task
- keep a minimal task queue and verify every completed change
- identify weak domains from your own performance, not from guesswork
- repeat the mock with better pacing until your workflow is stable

## Why This Module Exists

Real exam prep needs an integrated run, not just isolated skills. You may know individual commands and still fail because your pacing, order, or verification habit is weak.

This module is the bridge between knowledge and performance. It turns the earlier practice modules into a single timed system.

## How To Use This Module

Run it in a clean Linux VM or lab environment:
- no browser notes unless you absolutely need them
- no copying answers from another session
- terminal only
- set a timer before you start

Suggested approach:
1. read the task list once
2. mark the easy items
3. solve and verify the quick wins first
4. return to the harder items with remaining time
5. do a final pass for missed verification

## Mock Exam Structure

Use this as a representative LFCS practice run. Do not try to memorize the order forever. Learn the pattern.

### Task 1: Essential Commands

You are given a directory tree with mixed files.

Goal:
- locate one file by name
- extract a line from another file
- create a compressed archive of a chosen directory
- verify the archive can be restored

### Task 2: Users and Permissions

You are asked to provision access for a new operator.

Goal:
- create the user
- add the user to the correct supplementary group
- set directory ownership and mode correctly
- verify access with `id` and an actual file test

### Task 3: Running Systems

A service is not starting as expected.

Goal:
- inspect its unit state
- find the failure reason in logs
- correct the issue
- restart the service and verify it remains active

### Task 4: Networking

A host is not behaving correctly on the network.

Goal:
- verify IP and route configuration
- confirm name resolution
- check listening services or firewall state if needed
- prove that connectivity works after the fix

### Task 5: Storage

A data path needs to be persistent.

Goal:
- create or identify a filesystem
- mount it at the correct path
- make the mount survive reboot
- validate with `mount`, `findmnt`, and `df`

### Task 6: Scheduled Task

A recurring admin action must run automatically.

Goal:
- add a `cron` entry or one-time `at` job
- verify that it exists
- remove it cleanly after the test

## Scoring Rubric

When you finish, score yourself in three buckets:
- **Correctness**: did the system end in the right state?
- **Verification**: did you prove each result?
- **Pacing**: did you leave enough time for a final pass?

You do not need to score perfectly to learn something useful. You do need to identify where you wasted time or trusted unverified changes.

## Debrief Checklist

After the run, answer these questions:
- which task took the longest?
- which command family slowed you down?
- did you verify too late or too often?
- did you lose time on a mistake you could have skipped?
- what is the one command pattern to rehearse next?

## Failure Patterns This Mock Exposes

- starting with the hardest task because it feels urgent
- solving a task but forgetting to confirm the state
- over-focusing on a broken item while easier points remain untouched
- not leaving time for cleanup and review
- taking notes that are too detailed to be useful

## What Good Looks Like

A strong mock run looks calm:
- quick wins handled first
- one or two harder tasks completed with verification
- no panic rework loops
- a short debrief at the end that produces a better second run

## Summary

This is the module that tells you whether your LFCS prep is real.

If you can finish a timed mixed-domain run, verify every meaningful change, and still have time to review your own weak spots, then you are preparing like a candidate who will perform well under exam conditions.
