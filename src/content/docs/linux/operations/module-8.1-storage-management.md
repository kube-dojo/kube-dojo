---
title: "Module 8.1: Storage Management"
slug: linux/operations/module-8.1-storage-management
sidebar:
  order: 1
---
> **Operations — LFCS** | Complexity: `[COMPLEX]` | Time: 45-55 min

## Prerequisites

Before starting this module:
- **Required**: [Module 1.3: Filesystem Hierarchy](../foundations/system-essentials/module-1.3-filesystem-hierarchy/) for understanding mount points and inodes
- **Required**: [Module 1.1: Kernel Architecture](../foundations/system-essentials/module-1.1-kernel-architecture/) for understanding kernel/userspace boundary
- **Helpful**: [Module 5.4: I/O Performance](performance/module-5.4-io-performance/) for storage monitoring context

---

## Why This Module Matters

Storage management is one of those skills that separates "I can use Linux" from "I can run Linux in production." When a disk fills up at 3 AM, when a database needs more space without downtime, when teams need shared storage across servers — that's when LVM, NFS, and filesystem skills become critical.

Understanding storage helps you:

- **Resize volumes without downtime** — LVM lets you grow filesystems while they're mounted
- **Share data across servers** — NFS is still the backbone of shared storage in many environments
- **Prevent disasters** — Proper fstab configuration prevents boot failures
- **Pass the LFCS exam** — Storage is 20% of the exam weight

If you've ever run `df -h`, panicked at 100% usage, and didn't know what to do next — this module fixes that.

---

## Did You Know?

- **LVM was invented in 1998** by Heinz Mauelshagen for Linux. Before LVM, resizing a partition meant backing up data, deleting the partition, recreating it larger, then restoring. LVM made this a one-command operation.

- **NFS v4 is 20+ years old** — Released in 2003, NFSv4 added strong security (Kerberos), stateful operation, and compound operations. Yet many production systems still accidentally run NFSv3.

- **A bad fstab entry can prevent boot** — If you add an NFS mount to `/etc/fstab` without the `nofail` option, your server won't boot if the NFS server is unreachable. This has caused more outages than anyone wants to admit.

---

## Partitions and Filesystems

### Disk Layout Basics

Before we touch LVM, understand what's underneath:

```
Physical Disk (/dev/sda)
├── Partition 1 (/dev/sda1) → /boot (ext4)
├── Partition 2 (/dev/sda2) → LVM Physical Volume
│   └── Volume Group (vg_data)
│       ├── Logical Volume (lv_root) → / (ext4)
│       └── Logical Volume (lv_home) → /home (xfs)
└── Partition 3 (/dev/sda3) → swap
```

### Listing Disks and Partitions

```bash
# List all block devices
lsblk

# Output example:
# NAME                  MAJ:MIN RM  SIZE RO TYPE MOUNTPOINTS
# sda                     8:0    0   50G  0 disk
# ├─sda1                  8:1    0    1G  0 part /boot
# ├─sda2                  8:2    0   49G  0 part
# │ ├─vg_data-lv_root   253:0    0   30G  0 lvm  /
# │ └─vg_data-lv_home   253:1    0   19G  0 lvm  /home
# sdb                     8:16   0   20G  0 disk

# Detailed partition info
fdisk -l /dev/sda

# Show partition table type
blkid
```

### Creating Partitions

```bash
# Interactive partitioning with fdisk
sudo fdisk /dev/sdb

# Key commands inside fdisk:
#   n - new partition
#   p - print partition table
#   t - change partition type (8e for LVM)
#   w - write changes and exit
#   q - quit without saving

# Non-interactive example: create a single partition using entire disk
echo -e "n\np\n1\n\n\nt\n8e\nw" | sudo fdisk /dev/sdb

# Inform kernel of partition changes (if disk was in use)
sudo partprobe /dev/sdb
```

### Creating Filesystems

```bash
# Create ext4 filesystem
sudo mkfs.ext4 /dev/sdb1

# Create XFS filesystem
sudo mkfs.xfs /dev/sdb1

# Create ext4 with specific options
sudo mkfs.ext4 -L "data_vol" -m 1 /dev/sdb1
# -L: label
# -m 1: reserve only 1% for root (default is 5%)

# Check filesystem type
blkid /dev/sdb1
# /dev/sdb1: UUID="a1b2c3..." TYPE="ext4" LABEL="data_vol"
```

### ext4 vs XFS — When to Use Which

| Feature | ext4 | XFS |
|---------|------|-----|
| Shrink filesystem | Yes | No |
| Max file size | 16 TB | 8 EB |
| Best for | General purpose, small-medium volumes | Large files, high throughput |
| Default on | Ubuntu, Debian | RHEL, Rocky |
| LFCS exam | Know both | Know both |

---

## LVM (Logical Volume Manager)

LVM is the single most important storage concept for the LFCS. It adds a layer of abstraction between physical disks and filesystems, giving you flexibility that raw partitions can't provide.

### LVM Architecture

```
Physical Volumes (PV)     Volume Groups (VG)      Logical Volumes (LV)
┌──────────┐             ┌──────────────────┐     ┌─────────────┐
│ /dev/sdb1│─────┐       │                  │     │  lv_data    │→ /data (ext4)
└──────────┘     ├──────▶│    vg_storage     │────▶│  (20G)      │
┌──────────┐     │       │                  │     └─────────────┘
│ /dev/sdc1│─────┘       │  Total: 50G      │     ┌─────────────┐
└──────────┘             │  Free: 30G       │────▶│  lv_logs    │→ /var/log (xfs)
                         │                  │     │  (10G)      │
                         └──────────────────┘     └─────────────┘
```

**Key insight**: Logical volumes can span multiple physical disks, and you can add more physical disks to a volume group at any time. This is why LVM is standard in production.

### Step 1: Create Physical Volumes

```bash
# Mark a partition (or whole disk) as an LVM physical volume
sudo pvcreate /dev/sdb1
# Physical volume "/dev/sdb1" successfully created.

# You can also use whole disks (no partition needed)
sudo pvcreate /dev/sdc

# List physical volumes
sudo pvs
# PV         VG    Fmt  Attr PSize  PFree
# /dev/sdb1        lvm2 ---  20.00g 20.00g

# Detailed info
sudo pvdisplay /dev/sdb1
```

### Step 2: Create Volume Groups

```bash
# Create a volume group from one or more PVs
sudo vgcreate vg_storage /dev/sdb1
# Volume group "vg_storage" successfully created

# Add another PV to an existing VG
sudo pvcreate /dev/sdc1
sudo vgextend vg_storage /dev/sdc1
# Volume group "vg_storage" successfully extended

# List volume groups
sudo vgs
# VG         #PV #LV #SN Attr   VSize  VFree
# vg_storage   2   0   0 wz--n- 39.99g 39.99g

# Detailed info
sudo vgdisplay vg_storage
```

### Step 3: Create Logical Volumes

```bash
# Create a logical volume with specific size
sudo lvcreate -n lv_data -L 20G vg_storage
# Logical volume "lv_data" created.

# Create using percentage of free space
sudo lvcreate -n lv_logs -l 50%FREE vg_storage
# Uses 50% of remaining free space

# List logical volumes
sudo lvs
# LV      VG         Attr       LSize
# lv_data vg_storage -wi-a----- 20.00g
# lv_logs vg_storage -wi-a----- 10.00g

# The logical volume device path
ls -la /dev/vg_storage/lv_data
# This is a symlink to /dev/dm-X
```

### Step 4: Format and Mount

```bash
# Create filesystem on the logical volume
sudo mkfs.ext4 /dev/vg_storage/lv_data
sudo mkfs.xfs /dev/vg_storage/lv_logs

# Create mount points
sudo mkdir -p /data /var/log/app

# Mount
sudo mount /dev/vg_storage/lv_data /data
sudo mount /dev/vg_storage/lv_logs /var/log/app

# Verify
df -h /data /var/log/app
```

### Extending Logical Volumes (The Money Skill)

This is what makes LVM worth it — growing storage without downtime:

```bash
# Extend the logical volume by 5G
sudo lvextend -L +5G /dev/vg_storage/lv_data

# Resize the filesystem to use the new space
# For ext4:
sudo resize2fs /dev/vg_storage/lv_data

# For XFS:
sudo xfs_growfs /data  # Note: XFS uses mount point, not device

# Or do both in one command (ext4 and XFS)
sudo lvextend -L +5G -r /dev/vg_storage/lv_data
# The -r flag automatically resizes the filesystem

# Extend to use ALL remaining free space
sudo lvextend -l +100%FREE -r /dev/vg_storage/lv_data
```

> **Exam tip**: Always use `lvextend -r` to resize the filesystem in the same step. Forgetting to resize the filesystem after extending the LV is a classic mistake — the LV is bigger but the filesystem doesn't know it.

### Common Mistakes with LVM

| Mistake | What Happens | Fix |
|---------|-------------|-----|
| `lvextend` without `resize2fs`/`xfs_growfs` | LV is bigger but filesystem still old size | Run `resize2fs` or use `lvextend -r` |
| `-L 5G` instead of `-L +5G` | Sets total to 5G instead of adding 5G (may shrink!) | Always use `+` for relative sizing |
| Forgetting `pvcreate` before `vgextend` | `vgextend` fails: device not a PV | Run `pvcreate` first |
| Shrinking XFS | XFS cannot be shrunk, only grown | Use ext4 if shrinking may be needed |
| Not updating fstab | Mount lost on reboot | Add entry to `/etc/fstab` |

---

## Filesystem Mounting and fstab

### Manual Mounting

```bash
# Basic mount
sudo mount /dev/vg_storage/lv_data /data

# Mount with options
sudo mount -o rw,noatime,noexec /dev/sdb1 /mnt/usb

# Mount by UUID (more reliable than device name)
sudo mount UUID="a1b2c3d4-5678-90ab-cdef-1234567890ab" /data

# List all mounts
mount | column -t
# Or more readable:
findmnt --real

# Unmount
sudo umount /data
```

### Persistent Mounts with /etc/fstab

```bash
# Find the UUID of a device
blkid /dev/vg_storage/lv_data
# /dev/vg_storage/lv_data: UUID="a1b2c3d4-..." TYPE="ext4"

# Edit fstab
sudo vi /etc/fstab
```

The fstab format:

```
# <device>                                 <mountpoint>  <type>  <options>       <dump> <pass>
UUID=a1b2c3d4-5678-90ab-cdef-1234567890ab  /data         ext4    defaults        0      2
/dev/vg_storage/lv_logs                    /var/log/app  xfs     defaults,noatime 0     2
```

**Field breakdown**:
- **device**: UUID (preferred) or device path
- **mountpoint**: Where to mount
- **type**: ext4, xfs, nfs, swap, etc.
- **options**: `defaults` = rw,suid,dev,exec,auto,nouser,async
- **dump**: 0 = don't backup (almost always 0)
- **pass**: fsck order (0 = skip, 1 = root, 2 = other)

```bash
# CRITICAL: Test fstab before rebooting!
sudo mount -a
# If this fails, fix fstab before rebooting or your system won't boot

# Verify
df -h
```

> **War story**: A junior sysadmin added an NFS mount to fstab without the `nofail` option. The NFS server went down for maintenance over the weekend. On Monday, every server that had been rebooted (for kernel updates) was stuck in emergency mode because they couldn't mount the NFS share during boot. Forty servers, all needing console access to fix a single line in fstab. The fix took 3 hours. The lesson took 3 seconds: always use `nofail` for network mounts, and always run `mount -a` to test.

---

## NFS (Network File System)

NFS allows you to share directories over the network. It's old, it's simple, it works.

### NFS Server Setup

```bash
# Install NFS server
sudo apt update && sudo apt install -y nfs-kernel-server

# Create shared directory
sudo mkdir -p /srv/nfs/shared
sudo chown nobody:nogroup /srv/nfs/shared
sudo chmod 755 /srv/nfs/shared

# Configure exports
sudo vi /etc/exports
```

The `/etc/exports` file:

```
# Format: <directory> <client>(options)

# Share with specific network
/srv/nfs/shared    192.168.1.0/24(rw,sync,no_subtree_check,no_root_squash)

# Share read-only with everyone
/srv/nfs/readonly  *(ro,sync,no_subtree_check)

# Share with specific host
/srv/nfs/backup    backup-server.local(rw,sync,no_subtree_check)
```

**Key options**:
- `rw` / `ro`: Read-write or read-only
- `sync`: Write to disk before responding (safer, slower)
- `no_subtree_check`: Improves reliability
- `no_root_squash`: Remote root acts as root (dangerous but sometimes needed)
- `root_squash`: Remote root mapped to nobody (default, safer)

```bash
# Apply export changes
sudo exportfs -ra

# List current exports
sudo exportfs -v

# Start and enable NFS server
sudo systemctl enable --now nfs-kernel-server

# Verify NFS is listening
sudo ss -tlnp | grep -E '(2049|111)'
```

### NFS Client Setup

```bash
# Install NFS client
sudo apt install -y nfs-common

# Show available exports from server
showmount -e 192.168.1.10

# Create mount point and mount
sudo mkdir -p /mnt/nfs/shared
sudo mount -t nfs 192.168.1.10:/srv/nfs/shared /mnt/nfs/shared

# Verify
df -h /mnt/nfs/shared
mount | grep nfs

# Add to fstab for persistent mount
echo "192.168.1.10:/srv/nfs/shared  /mnt/nfs/shared  nfs  defaults,nofail,_netdev  0  0" | sudo tee -a /etc/fstab
```

**Important fstab options for NFS**:
- `nofail`: Don't halt boot if mount fails
- `_netdev`: Wait for network before mounting
- `bg`: Retry in background if server unreachable at boot

---

## Swap Space

Swap provides overflow space when physical RAM is full. On modern systems with plenty of RAM, swap is less critical but still expected on the LFCS exam.

### Creating Swap from a Partition

```bash
# Create swap on a partition
sudo mkswap /dev/sdb2
# Setting up swapspace version 1, size = 2 GiB

# Enable swap
sudo swapon /dev/sdb2

# Verify
sudo swapon --show
# NAME      TYPE      SIZE USED PRIO
# /dev/sdb2 partition   2G   0B   -2

# Add to fstab
echo "UUID=$(blkid -s UUID -o value /dev/sdb2)  none  swap  sw  0  0" | sudo tee -a /etc/fstab
```

### Creating Swap from a File

```bash
# Create a 2GB swap file
sudo dd if=/dev/zero of=/swapfile bs=1M count=2048

# Set permissions (swap files MUST be 600)
sudo chmod 600 /swapfile

# Format as swap
sudo mkswap /swapfile

# Enable
sudo swapon /swapfile

# Add to fstab
echo "/swapfile  none  swap  sw  0  0" | sudo tee -a /etc/fstab

# Verify all swap
free -h
```

### Managing Swap

```bash
# Show all swap spaces
swapon --show

# Disable a specific swap
sudo swapoff /dev/sdb2

# Disable ALL swap (useful for Kubernetes nodes)
sudo swapoff -a

# Check swappiness (how aggressively kernel uses swap)
cat /proc/sys/vm/swappiness
# Default: 60 (range 0-100)

# Reduce swappiness temporarily
sudo sysctl vm.swappiness=10

# Make permanent
echo "vm.swappiness=10" | sudo tee -a /etc/sysctl.d/99-swap.conf
sudo sysctl -p /etc/sysctl.d/99-swap.conf
```

---

## RAID Management

RAID (Redundant Array of Independent Disks) combines multiple physical disks into a single logical unit for redundancy, performance, or both. On Linux, software RAID is managed with `mdadm`.

### RAID Levels Quick Reference

| Level | Minimum Disks | Redundancy | Use Case |
|-------|--------------|------------|----------|
| RAID 0 | 2 | None (striping only) | Performance, no data protection |
| RAID 1 | 2 | Mirror (50% capacity) | Boot drives, critical data |
| RAID 5 | 3 | Single parity (1 disk can fail) | General purpose, good balance |
| RAID 10 | 4 | Mirror + stripe | Databases, high performance + safety |

### Creating RAID Arrays

```bash
# Install mdadm
sudo apt install -y mdadm   # Debian/Ubuntu
sudo dnf install -y mdadm   # RHEL/Rocky

# Create RAID 1 (mirror) from two disks
sudo mdadm --create /dev/md0 --level=1 --raid-devices=2 /dev/sdb /dev/sdc

# Create RAID 5 (parity) from three disks
sudo mdadm --create /dev/md1 --level=5 --raid-devices=3 /dev/sdd /dev/sde /dev/sdf

# Create RAID 10 (mirror + stripe) from four disks
sudo mdadm --create /dev/md2 --level=10 --raid-devices=4 /dev/sdg /dev/sdh /dev/sdi /dev/sdj

# Watch the initial sync progress
cat /proc/mdstat
```

### Saving RAID Configuration

```bash
# Scan and save to config (CRITICAL — without this, array won't reassemble on boot)
sudo mdadm --detail --scan | sudo tee -a /etc/mdadm/mdadm.conf

# On RHEL/Rocky the path is /etc/mdadm.conf
sudo mdadm --detail --scan | sudo tee -a /etc/mdadm.conf

# Update initramfs so the array is available at boot
sudo update-initramfs -u   # Debian/Ubuntu
sudo dracut --force        # RHEL/Rocky
```

### Using the RAID Array

```bash
# Create filesystem on the array
sudo mkfs.ext4 /dev/md0

# Mount it
sudo mkdir -p /mnt/raid
sudo mount /dev/md0 /mnt/raid

# Add to fstab for persistent mount
echo "UUID=$(blkid -s UUID -o value /dev/md0)  /mnt/raid  ext4  defaults  0  2" | sudo tee -a /etc/fstab
```

### Monitoring and Status

```bash
# Check status of all arrays
cat /proc/mdstat

# Detailed info for a specific array
sudo mdadm --detail /dev/md0
# Shows state, active devices, rebuild progress, etc.

# Check individual disk status
sudo mdadm --examine /dev/sdb

# Enable email alerts for failures (set MAILADDR in mdadm.conf)
# Then start the monitor
sudo mdadm --monitor --daemonise --mail=admin@example.com /dev/md0
```

### Recovery — Replacing a Failed Disk

```bash
# 1. Identify the failed disk
sudo mdadm --detail /dev/md0
# Look for "faulty" or "removed" state

# 2. Mark the failed disk (if not already marked)
sudo mdadm /dev/md0 --fail /dev/sdb

# 3. Remove the failed disk
sudo mdadm /dev/md0 --remove /dev/sdb

# 4. Add replacement disk
sudo mdadm /dev/md0 --add /dev/sdk

# 5. Watch rebuild progress
watch cat /proc/mdstat
```

> **Exam tip**: The LFCS may ask you to create a RAID array, add it to the config, and verify it survives a reboot. Always remember: `mdadm --detail --scan >> /etc/mdadm/mdadm.conf` and `update-initramfs -u`.

---

## Automount with autofs

Autofs mounts filesystems on demand (when accessed) and unmounts them after a timeout. This is useful for NFS shares that aren't always needed.

### Setting Up autofs

```bash
# Install autofs
sudo apt install -y autofs

# Configure the master map
sudo vi /etc/auto.master
```

The master map (`/etc/auto.master`):

```
# Format: <mount-point-parent>  <map-file>  [options]

/mnt/nfs    /etc/auto.nfs    --timeout=60
```

The map file (`/etc/auto.nfs`):

```
# Format: <key>  [options]  <location>

# When someone accesses /mnt/nfs/shared, autofs mounts NFS
shared    -rw,soft    192.168.1.10:/srv/nfs/shared

# Multiple NFS shares
docs      -ro,soft    192.168.1.10:/srv/nfs/docs
backup    -rw,soft    192.168.1.10:/srv/nfs/backup
```

```bash
# Enable and start autofs
sudo systemctl enable --now autofs

# Test: access the mount point (autofs creates it on demand)
ls /mnt/nfs/shared
# This triggers the mount automatically

# Verify it mounted
mount | grep autofs
df -h /mnt/nfs/shared

# After 60 seconds of inactivity, it auto-unmounts
```

### Wildcard Maps

```bash
# Mount any subdirectory from NFS server automatically
# In /etc/auto.nfs:
*    -rw,soft    192.168.1.10:/srv/nfs/&

# Now /mnt/nfs/anything will mount 192.168.1.10:/srv/nfs/anything
```

---

## Storage Monitoring

### Disk Space

```bash
# Filesystem usage
df -h
# Filesystem                     Size  Used Avail Use% Mounted on
# /dev/mapper/vg_data-lv_root    30G   12G   17G  42% /

# Inodes usage (running out of inodes = can't create files even with space)
df -i

# Directory sizes
du -sh /var/log/*
du -sh /home/* | sort -rh | head -10

# Find large files
find / -xdev -type f -size +100M -exec ls -lh {} \; 2>/dev/null

# Check what's using space in current directory
du -h --max-depth=1 | sort -rh
```

### I/O Monitoring

```bash
# Real-time I/O stats per device
iostat -xz 2
# Key columns: %util (100% = saturated), await (latency in ms)

# Per-process I/O
sudo iotop -o
# Shows which processes are doing I/O right now

# Disk health (if smartmontools installed)
sudo smartctl -a /dev/sda
```

### LVM Monitoring

```bash
# Quick summary of all LVM components
sudo pvs  # Physical volumes
sudo vgs  # Volume groups
sudo lvs  # Logical volumes

# Detailed information
sudo pvdisplay
sudo vgdisplay
sudo lvdisplay

# Check free space in volume group
sudo vgs -o +vg_free
```

---

## Quiz

Test your storage management knowledge:

**Question 1**: What three LVM commands create the physical volume, volume group, and logical volume (in order)?

<details>
<summary>Show Answer</summary>

1. `pvcreate` — Marks a partition/disk as a physical volume
2. `vgcreate` — Groups one or more PVs into a volume group
3. `lvcreate` — Creates a logical volume within a volume group

Example flow:
```bash
sudo pvcreate /dev/sdb1
sudo vgcreate vg_data /dev/sdb1
sudo lvcreate -n lv_app -L 10G vg_data
```

</details>

**Question 2**: You ran `lvextend -L +10G /dev/vg_data/lv_app` but `df -h` still shows the old size. What did you forget?

<details>
<summary>Show Answer</summary>

You need to resize the filesystem after extending the logical volume:
- For ext4: `sudo resize2fs /dev/vg_data/lv_app`
- For XFS: `sudo xfs_growfs /mount/point`
- Or use `lvextend -r` to do both in one command

</details>

**Question 3**: What fstab options should you always use for NFS mounts, and why?

<details>
<summary>Show Answer</summary>

- `nofail` — Prevents the system from halting boot if the NFS server is unreachable
- `_netdev` — Tells the system to wait for network connectivity before attempting the mount

Example fstab entry:
```
192.168.1.10:/share  /mnt/share  nfs  defaults,nofail,_netdev  0  0
```

Without `nofail`, an unreachable NFS server will drop your system into emergency mode on boot.

</details>

**Question 4**: What's the difference between `mkswap` and `swapon`?

<details>
<summary>Show Answer</summary>

- `mkswap` formats a partition or file as swap space (like `mkfs` but for swap). It writes a swap header.
- `swapon` activates the swap space so the kernel starts using it.

You need both: `mkswap` first (once), then `swapon` (each boot, or via fstab).

</details>

**Question 5**: You need to add 20G of storage to `/data` which is on LVM. The volume group has no free space. You've added a new disk `/dev/sdd`. What are the steps?

<details>
<summary>Show Answer</summary>

```bash
# 1. Create physical volume on new disk
sudo pvcreate /dev/sdd

# 2. Extend the volume group
sudo vgextend vg_storage /dev/sdd

# 3. Extend the logical volume and resize filesystem
sudo lvextend -L +20G -r /dev/vg_storage/lv_data
```

Three commands. No downtime. This is why LVM exists.

</details>

---

## Hands-On Exercise: Build a Complete LVM Storage Stack

**Objective**: Create an LVM setup from scratch, mount it persistently, and extend it.

**Environment**: A Linux VM with at least two unused disks (or use loopback devices).

### Setup (Using Loopback Devices as Practice Disks)

```bash
# Create two virtual "disks" (100MB each — small for practice)
sudo dd if=/dev/zero of=/tmp/disk1.img bs=1M count=100
sudo dd if=/dev/zero of=/tmp/disk2.img bs=1M count=100

# Attach them as loop devices
sudo losetup /dev/loop10 /tmp/disk1.img
sudo losetup /dev/loop11 /tmp/disk2.img

# Verify
lsblk | grep loop1
```

### Tasks

**Task 1**: Create an LVM stack

```bash
# Create physical volumes
sudo pvcreate /dev/loop10 /dev/loop11

# Create volume group
sudo vgcreate vg_practice /dev/loop10

# Create logical volume (80MB from 100MB disk)
sudo lvcreate -n lv_exercise -L 80M vg_practice

# Create filesystem
sudo mkfs.ext4 /dev/vg_practice/lv_exercise

# Mount it
sudo mkdir -p /mnt/exercise
sudo mount /dev/vg_practice/lv_exercise /mnt/exercise
```

**Task 2**: Write data and extend

```bash
# Write some test data
sudo dd if=/dev/urandom of=/mnt/exercise/testfile bs=1M count=50

# Check usage
df -h /mnt/exercise

# Extend: add second disk to VG, then grow LV
sudo vgextend vg_practice /dev/loop11
sudo lvextend -l +100%FREE -r /dev/vg_practice/lv_exercise

# Verify data still intact and filesystem larger
df -h /mnt/exercise
md5sum /mnt/exercise/testfile
```

**Task 3**: Add persistent fstab entry

```bash
# Get UUID
blkid /dev/vg_practice/lv_exercise

# Add to fstab (use the UUID from above)
echo "UUID=$(blkid -s UUID -o value /dev/vg_practice/lv_exercise)  /mnt/exercise  ext4  defaults  0  2" | sudo tee -a /etc/fstab

# Test
sudo umount /mnt/exercise
sudo mount -a
df -h /mnt/exercise
```

### Success Criteria

- [ ] Physical volumes created with `pvcreate`
- [ ] Volume group created and extended with `vgcreate`/`vgextend`
- [ ] Logical volume created and extended with `lvcreate`/`lvextend`
- [ ] Filesystem created, mounted, and data survived extension
- [ ] Persistent mount in `/etc/fstab` tested with `mount -a`

### Cleanup

```bash
sudo umount /mnt/exercise
sudo lvremove -f /dev/vg_practice/lv_exercise
sudo vgremove vg_practice
sudo pvremove /dev/loop10 /dev/loop11
sudo losetup -d /dev/loop10 /dev/loop11
rm /tmp/disk1.img /tmp/disk2.img
# Remove the fstab entry you added
sudo sed -i '/vg_practice/d' /etc/fstab
```

---

## Next Module

Continue with [Module 8.2: Network Administration](../module-8.2-network-administration/) to cover firewall configuration, NAT, network bonding, and other LFCS networking topics.
