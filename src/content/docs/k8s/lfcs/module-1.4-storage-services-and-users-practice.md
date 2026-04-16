---
title: "LFCS Storage, Services, and Users Practice"
slug: k8s/lfcs/module-1.4-storage-services-and-users-practice
sidebar:
  order: 104
---

> **LFCS Track** | Complexity: `[COMPLEX]` | Time: 50-70 min

**Reading Time**: 50-70 minutes

## Prerequisites

Before starting this module:
- **Required**: [LFCS Exam Strategy and Workflow](./module-1.1-exam-strategy-and-workflow/)
- **Required**: [LFCS Essential Commands Practice](./module-1.2-essential-commands-practice/)
- **Required**: [LFCS Running Systems and Networking Practice](./module-1.3-running-systems-and-networking-practice/)
- **Helpful**: [Module 1.4: Users & Permissions](/linux/foundations/system-essentials/module-1.4-users-permissions/)
- **Helpful**: [Module 8.1: Storage Management](/linux/operations/module-8.1-storage-management/)

## What You'll Be Able To Do

After this module, you will be able to:
- create and manage users, groups, and sudo access cleanly
- control permissions and ownership without breaking access
- create filesystems, mount them persistently, and verify the result
- expand storage with LVM when a basic partition is not enough
- install, enable, and persist services in a way that survives reboot

## Why This Module Matters

This is where LFCS becomes real system administration. Users, filesystems, services, and mounts are the things that can break a small server in obvious ways and a production server in expensive ways.

The exam expects you to make those changes safely, then prove that they survived the change.

## Users, Groups, and Sudo

### Core Commands

```bash
useradd alice
passwd alice
usermod -aG sudo alice
groupadd ops
getent passwd alice
getent group ops
id alice
sudo -l
visudo
```

### Ownership and Permissions

```bash
chown alice:ops /srv/app/config.yml
chmod 640 /srv/app/config.yml
chmod u+rwx,g+rx,o-r /srv/app
setfacl -m u:alice:rw /srv/app/shared.txt
```

### What To Verify

- the user exists
- the user is in the expected groups
- sudo access is actually effective
- the target path has the intended ownership and mode
- access survives a new shell session

## Storage Skills LFCS Actually Wants

### Filesystems and Mounts

```bash
lsblk
blkid
mkfs.ext4 /dev/sdb1
mkfs.xfs /dev/sdb1
mkdir -p /data
mount /dev/sdb1 /data
findmnt /data
```

### Persistent Mounts

```bash
UUID=$(blkid -s UUID -o value /dev/sdb1)
echo "UUID=$UUID /data ext4 defaults 0 2" | sudo tee -a /etc/fstab
mount -a
```

### LVM Basics

```bash
pvcreate /dev/sdb1
vgcreate vg_data /dev/sdb1
lvcreate -n lv_app -L 10G vg_data
mkfs.ext4 /dev/vg_data/lv_app
mount /dev/vg_data/lv_app /srv/app
```

### What To Verify

- `lsblk` shows the intended hierarchy
- `findmnt` shows the expected mount point
- `df -h` confirms the filesystem size
- the mount entry in `/etc/fstab` is valid
- the system still boots after a mount test

## Services You Should Be Able To Control

```bash
apt update
apt install -y nginx
systemctl enable --now nginx
systemctl status nginx
systemctl is-enabled nginx
systemctl restart nginx
systemctl daemon-reload
```

For LFCS, service work is rarely about exotic tuning. It is about:
- installing the package
- starting the unit
- enabling it at boot
- proving it stays active

## Practice Drills

### Drill 1: Build a Shared Admin Area

Create a directory tree for a team:
- create a group
- create two users
- add both users to the group
- create a shared directory
- make sure the group can read and write it

What this trains:
- user and group management
- practical permissions
- access verification

### Drill 2: Make Storage Persistent

Use a spare disk or loopback file:
- create a filesystem
- mount it
- add a valid `fstab` entry
- unmount and remount with `mount -a`
- confirm persistence

What this trains:
- storage confidence
- boot-safe configuration
- validation before moving on

### Drill 3: Expand With LVM

Practice the full path:
- create a PV
- create a VG
- create an LV
- format and mount it
- extend it and recheck the size

What this trains:
- storage abstraction
- safe resizing
- checking changes after expansion

### Drill 4: Install and Persist a Service

Pick a simple daemon:
- install it
- enable it
- start it
- confirm it survives a reboot or service restart

What this trains:
- package to service workflow
- persistence, not just launch

## Verification Checklist

Before you move on, confirm:
- you can create and inspect users without guessing
- you can distinguish ownership problems from permission problems
- you can mount and remount a filesystem safely
- you know how to test `/etc/fstab` entries before a reboot surprises you
- you can create a service that starts automatically

## Common Failure Modes

- editing `/etc/fstab` without testing it
- changing permissions instead of fixing ownership, or vice versa
- forgetting `-aG` when adding a user to a supplementary group
- mounting the wrong block device because you did not verify `lsblk`
- enabling a service but never confirming it actually starts

## Summary

This module is where LFCS starts feeling like real admin work.

If you can manage users, permissions, mounts, LVM, and services cleanly, you have the core mechanics that let the exam stop being a collection of isolated commands and start being a normal operating routine.
