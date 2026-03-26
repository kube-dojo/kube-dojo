---
title: "Bare Metal Provisioning"
sidebar:
  order: 1
---

How do you go from a rack of blank servers to a running Kubernetes cluster? This section covers the boot process, OS installation, and declarative infrastructure that turns hardware into a platform.

## Modules

| Module | Description | Time |
|--------|-------------|------|
| [2.1 Datacenter Fundamentals](module-2.1-datacenter-fundamentals/) | Racks, PDUs, UPS, cooling, IPMI/BMC/Redfish, out-of-band management | 45 min |
| [2.2 OS Provisioning & PXE Boot](module-2.2-pxe-provisioning/) | PXE/UEFI boot, DHCP/TFTP, MAAS, Tinkerbell, autoinstall | 60 min |
| [2.3 Immutable OS for Kubernetes](module-2.3-immutable-os/) | Talos Linux, Flatcar Container Linux, RHCOS, why immutable matters | 45 min |
| [2.4 Declarative Bare Metal](module-2.4-declarative-bare-metal/) | Cluster API for bare metal, Metal3, Sidero, machine lifecycle | 60 min |
