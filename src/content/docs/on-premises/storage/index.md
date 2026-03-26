---
title: "Storage"
sidebar:
  order: 1
---

On-premises storage is the most consequential infrastructure decision you will make. Cloud storage (EBS, Persistent Disk, Azure Disk) is abstracted — you request a volume and it appears. On bare metal, you choose the physical drives, design the storage topology, and run the software that turns local disks into a distributed storage system.

## Modules

| Module | Description | Time |
|--------|-------------|------|
| [4.1 Storage Architecture Decisions](module-4.1-storage-architecture/) | DAS vs NAS vs SAN, NVMe tiering, etcd storage | 45 min |
| [4.2 Software-Defined Storage (Ceph/Rook)](module-4.2-ceph-rook/) | Ceph architecture, Rook operator, performance tuning | 60 min |
| [4.3 Local Storage & Alternatives](module-4.3-local-storage/) | OpenEBS, Longhorn, LVM CSI, TopoLVM | 45 min |
