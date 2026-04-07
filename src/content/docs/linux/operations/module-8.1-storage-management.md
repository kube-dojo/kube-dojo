---
title: "Module 8.1: Storage Management"
slug: linux/operations/module-8.1-storage-management
sidebar:
  order: 1
lab:
  id: linux-8.1-storage-management
  url: https://killercoda.com/kubedojo/scenario/linux-8.1-storage-management
  duration: "35 min"
  difficulty: intermediate
  environment: ubuntu
---
> **Operations — LFCS** | Complexity: `[COMPLEX]` | Time: 45-55 min

## Prerequisites

Before starting this module:
- **Required**: [Module 1.3: Filesystem Hierarchy](../foundations/system-essentials/module-1.3-filesystem-hierarchy/) for understanding mount points and inodes
- **Required**: [Module 1.1: Kernel Architecture](../foundations/system-essentials/module-1.1-kernel-architecture/) for understanding kernel/userspace boundary
- **Helpful**: [Module 5.4: I/O Performance](performance/module-5.4-io-performance/) for storage monitoring context

---

## What You'll Be Able to Do

After this module, you will be able to:
- **Configure** disk partitions, filesystems, and mount points using fdisk, mkfs, and fstab
- **Manage** LVM volumes (create, extend, snapshot) for flexible storage allocation
- **Diagnose** disk space issues using df, du, and lsblk and explain inode exhaustion
- **Implement** a storage strategy appropriate for Kubernetes node storage requirements

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

```mermaid
graph TD
    A[Physical Disk (/dev/sda)] --> B{Partition 1 (/dev/sda1)}
    B --> C[/boot (ext4)]
    A --> D{Partition 2 (/dev/sda2)}
    D --> E[LVM Physical Volume]
    E --> F[Volume Group (vg_data)]
    F --> G[Logical Volume (lv_root)]
    G --> H[/ (ext4)]
    F --> I[Logical Volume (lv_home)]
    I --> J[/home (xfs)]
    A --> K{Partition 3 (/dev/sda3)}
    K --> L[swap]
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

```mermaid
graph TD
    PV1[Physical Volume (/dev/sdb1)] --> VG[Volume Group (vg_storage)]
    PV2[Physical Volume (/dev/sdc1)] --> VG
    VG -- "Total: 50G, Free: 30G" --> LV1[Logical Volume (lv_data)]
    LV1 --> DataMount[/data (ext4)]
    VG -- "Total: 50G, Free: 30G" --> LV2[Logical Volume (lv_logs)]
    LV2 --> LogsMount[/var/log (xfs)]
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

> **Quick Check**: You have a `vg_webservers` volume group with two physical volumes. You need to expand `/var/www/html` which is on `lv_html` within `vg_webservers`. You just added a new physical disk `/dev/sde`. What's the *most efficient* sequence of commands to expand the filesystem without downtime? Think about which LVM commands are needed and how to handle the filesystem resizing.

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

> **Pause and predict**: Your production database server unexpectedly rebooted after a routine kernel update. When it came back online, the `/var/lib/postgresql/data` directory, which is a critical XFS filesystem on an LVM logical volume, was empty. Upon investigation, you discover the `fstab` entry for this mount point was missing. What immediate steps would you take to restore access to the data, and how would you prevent this from happening again?

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

> **Stop and think**: You're configuring a new web server that needs to access user-uploaded content stored on a central NFS server. The content should be read-only for the web server, and the web server should not crash if the NFS server is temporarily unavailable during boot. What `/etc/fstab` entry would you create for `/var/www/uploads` (assuming the NFS export is `nfs.example.com:/srv/webuploads`)? Explain your choice of options.

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
# A common, often overlooked, storage issue is inode exhaustion.
# Each file or directory on a filesystem consumes one inode.
# If a filesystem runs out of inodes, you cannot create new files,
# even if there is plenty of disk space available. This often happens
# in environments with many small files, such as build caches or mail servers.

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

## Kubernetes Node Storage Strategy

When managing storage for Kubernetes nodes, the approach differs significantly from traditional server storage. Kubernetes introduces concepts like Pods, Persistent Volumes (PVs), Persistent Volume Claims (PVCs), and StorageClasses, which abstract away the underlying storage details.

**Key considerations for Kubernetes node storage:**

1.  **Ephemeral vs. Persistent Storage**:
    *   **Ephemeral**: Data that is not expected to persist beyond the life of a Pod. `emptyDir` volumes are a good example, often mounted as local directories for temporary data, caches, or logs.
    *   **Persistent**: Data that needs to survive Pod restarts, node failures, or Pod migrations. This requires Persistent Volumes (PVs) backed by network storage (e.g., NFS, iSCSI, cloud block storage) or local persistent storage options.

2.  **Local vs. Network Storage**:
    *   **Local Storage**: Disks directly attached to the Kubernetes node. Can be used for `hostPath` volumes (often discouraged for production due to portability issues), or as local PVs (with careful management) for high-performance, low-latency applications that are resilient to node failures.
    *   **Network Storage**: Storage provided by a central storage system (e.g., NFS, GlusterFS, Ceph, cloud providers' block/file storage). This is typically preferred for persistent storage as it allows Pods to be moved between nodes without data loss.

3.  **Storage Provisioning**:
    *   **Static Provisioning**: An administrator manually creates PVs, which Pods then claim via PVCs.
    *   **Dynamic Provisioning**: StorageClasses are used to dynamically provision PVs on demand when a PVC is created. This typically relies on Container Storage Interface (CSI) drivers specific to the storage system (e.g., `aws-ebs`, `azure-disk`, `nfs-subdir-external-provisioner`).

4.  **Swap on Kubernetes Nodes**:
    *   Kubernetes generally recommends **disabling swap** on worker nodes. The Kubelet (the agent that runs on each node) has a configuration option `failSwapOn` which defaults to true, meaning if swap is enabled, the Kubelet will fail to start. This is because swap can lead to unpredictable performance, especially for memory-sensitive applications, and can interfere with Kubernetes' memory management and scheduling decisions. While it can be manually disabled, it's generally best practice to design applications to run within their allocated memory limits.

Choosing the right storage strategy involves balancing performance, cost, redundancy, and portability for your specific workloads. For most production Kubernetes deployments, dynamic provisioning with network-attached storage via CSI drivers is the standard.

---

## Quiz

Test your storage management knowledge:

**Question 1**: A new application server requires a 50GB filesystem at `/appdata`. Your server currently has a single 200GB disk (`/dev/sda`) with `/dev/sda1` mounted as `/` (20GB) and the remaining space unpartitioned. You also have an unused 100GB disk (`/dev/sdb`). Describe the commands you would use to create the `/appdata` filesystem using LVM, ensuring it's resilient to future growth, and mount it persistently.

<details>
<summary>Show Answer</summary>

The most flexible approach is to incorporate both available storage chunks into LVM.

1.  **Initialize `/dev/sdb` as a Physical Volume (PV)**:
    ```bash
    sudo pvcreate /dev/sdb
    ```
    This command marks the entire `/dev/sdb` disk for use by LVM.

2.  **Create a new partition on `/dev/sda` for LVM**:
    *   Use `fdisk` to create a new partition on `/dev/sda` using the unpartitioned space, setting its type to LVM (type `8e`).
    *   For example, if `/dev/sda` has 180GB free: `sudo fdisk /dev/sda`, then `n` for new, `p` for primary, accept defaults for partition number and size, then `t` to change type, `8e` for Linux LVM, and `w` to write changes.
    *   Inform the kernel of the changes: `sudo partprobe /dev/sda`

3.  **Initialize the new partition on `/dev/sda` as a PV**:
    ```bash
    sudo pvcreate /dev/sda2 # Assuming the new partition is sda2
    ```

4.  **Create a Volume Group (VG) incorporating both PVs**:
    ```bash
    sudo vgcreate vg_appdata /dev/sdb /dev/sda2
    ```
    This creates a volume group named `vg_appdata` that can span both disks, giving you maximum flexibility.

5.  **Create a Logical Volume (LV) for `/appdata`**:
    ```bash
    sudo lvcreate -n lv_appdata -L 50G vg_appdata
    ```
    This creates a 50GB logical volume within `vg_appdata`. The `-L` flag specifies the size, and `-n` specifies the name.

6.  **Create an ext4 filesystem on the Logical Volume**:
    ```bash
    sudo mkfs.ext4 /dev/vg_appdata/lv_appdata
    ```
    The `mkfs.ext4` command formats the logical volume with an ext4 filesystem.

7.  **Create the mount point and mount the filesystem**:
    ```bash
    sudo mkdir -p /appdata
    sudo mount /dev/vg_appdata/lv_appdata /appdata
    ```
    This makes the filesystem accessible at `/appdata`.

8.  **Add an entry to `/etc/fstab` for persistent mounting**:
    ```bash
    UUID=$(sudo blkid -s UUID -o value /dev/vg_appdata/lv_appdata)
    echo "UUID=$UUID  /appdata  ext4  defaults  0  2" | sudo tee -a /etc/fstab
    ```
    Using the UUID ensures the mount is persistent and reliable, even if device names change. The `defaults` option provides standard mount behaviors, `0` skips dump, and `2` allows `fsck` to check it after the root filesystem.

</details>

**Question 2**: You're monitoring a build server, and `df -h` shows plenty of disk space free (e.g., 70% used), but `df -i` reports 100% inode usage on `/var/lib/docker`. Suddenly, new Docker images cannot be pulled, and builds start failing with "No space left on device" errors. Explain why this is happening and what initial steps you would take to diagnose and resolve it.

<details>
<summary>Show Answer</summary>

This scenario is a classic case of **inode exhaustion**. Even though there's free disk *space*, the filesystem has run out of available *inodes*. An inode is a data structure on a Unix-style filesystem that stores information about a file or a directory, such as its ownership, permissions, and location on the disk. Every file and directory consumes one inode.

**Why it's happening**: Docker layers, build artifacts, and caches often consist of a very large number of small files. Each of these small files, no matter how tiny, requires an inode. When the filesystem reaches its maximum number of allocated inodes, no new files or directories can be created, regardless of how much free block space remains. The "No space left on device" error message can be misleading in this context, as it refers to the *logical* space for creating file entries, not necessarily the *physical* disk blocks.

**Initial steps to diagnose and resolve**:

1.  **Verify Inode Usage**: Confirm the `df -i` output and compare it with `df -h`. This will clearly show if inodes are the bottleneck, not disk space.
2.  **Identify Inode Consumers**: Use `find` and `du` to locate directories containing a large number of files.
    *   `sudo find /var/lib/docker -xdev -printf '%h\n' | sort | uniq -c | sort -rh | head -10` can help identify directories with the most files (and thus inodes).
    *   `sudo du -sh /var/lib/docker/*` will show actual disk usage, which might be low for directories with many small files.
3.  **Clean Up Unnecessary Files/Directories**:
    *   For Docker, the primary solution is to prune old images, containers, volumes, and build caches.
        *   `sudo docker system prune -a` (use with caution in production as it removes all unused data).
        *   `sudo docker image prune -a` for images.
        *   `sudo docker volume prune` for volumes.
        *   `sudo docker builder prune` for build caches.
    *   Look for any other application-specific caches or temporary directories within `/var/lib/docker` or its subdirectories that might be accumulating many small files.
4.  **Consider Filesystem Re-creation/Resizing (if pruning isn't enough)**:
    *   If inode exhaustion is a recurring problem, the filesystem may have been created with too few inodes for its workload. A long-term solution might involve backing up data, re-creating the filesystem with a higher inode-to-block ratio (e.g., using `mkfs.ext4 -i 16384` for more inodes per block), and then restoring the data. This is a more drastic measure requiring downtime.

</details>

**Question 3**: Your development team reports that their applications, which rely on a network share mounted via NFS, are occasionally experiencing slow file operations and sometimes even hanging. The NFS server is located in a different data center with varying network latency. What `fstab` options would you add or modify to improve the client-side experience, mitigating the impact of network issues, and explain why each option is beneficial?

<details>
<summary>Show Answer</summary>

For NFS mounts in environments with potentially unreliable or high-latency networks, several `fstab` options can significantly improve robustness and user experience.

Assuming a base entry like:
`nfs.example.com:/data  /mnt/data  nfs  defaults,nofail,_netdev  0  0`

Here are key additions/modifications:

1.  **`soft`**:
    *   **Benefit**: This option ensures that if the NFS server becomes unresponsive, the client will return an error to the calling process after a certain timeout, rather than hanging indefinitely. This prevents applications from freezing and allows them to handle the error gracefully.
    *   **Why**: Without `soft` (the default is `hard`), if the NFS server goes down, any process attempting to access the mount will hang until the server recovers, potentially freezing the entire application or even the server itself. While `hard` mounts are safer for data integrity (they keep retrying until successful writes), `soft` is often preferred for applications where responsiveness is more critical than absolute certainty of every write, and data integrity is handled by the application layer (e.g., retries).

2.  **`timeo=14` (or similar value)**:
    *   **Benefit**: Sets the timeout (in tenths of a second) for how long the client waits for an RPC response from the server before retrying. A value of `14` means 1.4 seconds. Lowering this can make `soft` mounts fail faster.
    *   **Why**: In a high-latency environment, the default timeout might be too short, leading to unnecessary retries or errors. Conversely, if it's too high, failures take longer to detect. Adjusting this allows fine-tuning responsiveness.

3.  **`retrans=3` (or similar value)**:
    *   **Benefit**: Specifies the number of times the NFS client retries a request before giving up (if `soft` mount) or reporting an error (if `hard` mount).
    *   **Why**: Increasing `retrans` can help overcome transient network glitches by allowing more retries before a definite failure. If combined with `soft`, a higher `retrans` might still lead to delays, but it gives the network more chances to recover.

4.  **`actimeo=0` (or `noac`)**:
    *   **Benefit**: Disables or significantly reduces client-side attribute caching.
    *   **Why**: In environments where files might be rapidly changed by multiple clients or the server itself, client-side caching can lead to clients seeing stale data. `actimeo=0` forces the client to re-validate file attributes (like size, modification time) with the server more frequently, ensuring clients see the most up-to-date state, albeit with a slight performance overhead.

5.  **`vers=4.2` (or highest supported)**:
    *   **Benefit**: Explicitly specifies the NFS protocol version. Newer versions (like 4.x) offer better performance, security, and stateful operations compared to older versions (like 3).
    *   **Why**: Ensuring the client uses the most modern, efficient protocol can inherently improve reliability and speed. NFSv4.x, for instance, typically uses a single TCP connection, simplifying firewall rules and improving performance over WANs.

**Example `fstab` entry with these options**:
`nfs.example.com:/data  /mnt/data  nfs  defaults,nofail,_netdev,soft,timeo=14,retrans=3,actimeo=0,vers=4.2  0  0`

These options collectively make the NFS client more resilient to network fluctuations and improve the responsiveness of applications interacting with the share.

</details>

**Question 4**: Your Kubernetes cluster is experiencing node instability. You notice that some worker nodes, especially those running memory-intensive workloads, occasionally become "NotReady" and Pods are evicted. Upon investigation, you find that swap space is enabled on these nodes. Why does Kubernetes typically recommend disabling swap on worker nodes, and how would you permanently disable swap on a Linux node to comply with Kubernetes best practices?

<details>
<summary>Show Answer</summary>

**Why Kubernetes recommends disabling swap**:

Kubernetes strongly recommends disabling swap on worker nodes primarily because it can lead to **unpredictable and often detrimental behavior for containerized applications** and the Kubernetes scheduler.

1.  **Performance Instability**: When a system starts swapping, it moves less-used pages of memory to disk. Disk I/O is orders of magnitude slower than RAM access. This causes significant performance degradation and introduces unpredictable latencies for applications. In a Kubernetes environment, where many applications might compete for resources, swapping can lead to "noisy neighbor" issues and make it difficult to reason about application performance.
2.  **Resource Management Interference**: Kubernetes (specifically the Kubelet) makes scheduling decisions based on declared CPU and memory requests/limits. When swap is enabled, the operating system can effectively "hide" actual memory pressure from the Kubelet by moving pages to swap. This means the Kubelet might believe a node has sufficient memory when, in reality, applications are suffering due to excessive swapping. This interferes with accurate resource allocation, scheduling, and out-of-memory (OOM) killing decisions.
3.  **Inconsistent OOM Behavior**: With swap enabled, the Linux kernel's Out-Of-Memory (OOM) killer might intervene less predictably. Instead of quickly terminating a misbehaving process when RAM is exhausted, the system might swap heavily first, prolonging the suffering before an eventual OOM kill, or even leading to node instability. Kubernetes prefers to manage OOM situations more explicitly based on Pod resource limits.
4.  **Simplicity and Predictability**: Disabling swap simplifies resource management. It ensures that when a Pod consumes its allocated memory, the OOM killer will step in directly, making resource issues easier to diagnose and providing a more consistent and predictable environment for workloads.

**How to permanently disable swap on a Linux node**:

1.  **Disable swap for the current session**:
    ```bash
    sudo swapoff -a
    ```
    This command immediately deactivates all configured swap areas.

2.  **Remove swap entries from `/etc/fstab`**:
    *   Edit the `/etc/fstab` file:
        ```bash
        sudo vi /etc/fstab
        ```
    *   Locate and comment out (or delete) any lines that specify `swap` as the filesystem type. A typical swap entry looks like this:
        `UUID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx none swap sw 0 0`
        or
        `/swapfile none swap sw 0 0`
    *   After commenting it out, it should look like:
        `# UUID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx none swap sw 0 0`

By performing both steps, swap will be disabled immediately and will not be re-enabled after a reboot, aligning the node with Kubernetes best practices.

</details>

**Question 5**: A critical web application is deployed on an LVM logical volume `/dev/vg_web/lv_data` mounted at `/var/www/html`. This filesystem is running low on space. You've just added a new 100GB physical disk `/dev/sdc` to the server. What is the most efficient and safest way to expand `/var/www/html` by 50GB without taking the web application offline? Provide the exact commands and briefly explain each step.

<details>
<summary>Show Answer</summary>

The most efficient and safest way to expand `/var/www/html` without downtime, leveraging LVM's capabilities, involves these steps:

1.  **Initialize the new disk as a Physical Volume (PV)**:
    ```bash
    sudo pvcreate /dev/sdc
    ```
    *   **Explanation**: This command marks `/dev/sdc` as a physical volume, making it available for use by LVM. This is the foundational step to integrate the new disk into your flexible storage pool.

2.  **Extend the existing Volume Group (VG) with the new PV**:
    ```bash
    sudo vgextend vg_web /dev/sdc
    ```
    *   **Explanation**: This command adds the newly created physical volume (`/dev/sdc`) to the `vg_web` volume group. This increases the total capacity of `vg_web`, allowing its logical volumes (like `lv_data`) to be extended. At this point, the filesystem (`/var/www/html`) is still online and unchanged.

3.  **Extend the Logical Volume (LV) and resize the filesystem in one command**:
    ```bash
    sudo lvextend -L +50G -r /dev/vg_web/lv_data
    ```
    *   **Explanation**: This is the critical "money skill" command.
        *   `lvextend -L +50G /dev/vg_web/lv_data`: This extends the logical volume `lv_data` by an additional 50 Gigabytes. The `+` is crucial, indicating an *addition* to the current size, not setting a new absolute size.
        *   `-r`: This flag is incredibly important for efficiency and safety. It tells `lvextend` to automatically resize the *filesystem* residing on the logical volume after the underlying logical volume has been extended. This bypasses the need for separate `resize2fs` (for ext4) or `xfs_growfs` (for XFS) commands. Since most modern Linux filesystems (ext4, XFS) can be grown online, this step can typically be performed without unmounting `/var/www/html`, thus avoiding application downtime.

After these steps, the `/var/www/html` filesystem will be expanded by 50GB, the web application will remain online throughout the process, and the new disk space will be immediately available.

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
---