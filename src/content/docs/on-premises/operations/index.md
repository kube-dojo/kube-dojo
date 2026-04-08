---
title: "Day-2 Operations"
sidebar:
  order: 0
---

Day-2 operations on bare metal Kubernetes clusters are fundamentally different from managed cloud services. There is no "upgrade cluster" button, no auto-replacing failed nodes, no built-in observability stack. You own the hardware, the OS, the control plane, and every component in between.

These modules cover the operational practices that keep on-premises clusters healthy, current, and scalable over multi-year hardware lifecycles.

## Modules

| Module | Description | Time |
|--------|-------------|------|
| [7.1 Kubernetes Upgrades on Bare Metal](module-7.1-upgrades/) | kubeadm upgrade path, drain strategies, rollback, version skew | 60 min |
| [7.2 Hardware Lifecycle & Firmware](module-7.2-hardware-lifecycle/) | BIOS/firmware updates, disk replacement, SMART monitoring, Redfish API | 60 min |
| [7.3 Node Failure & Auto-Remediation](module-7.3-node-remediation/) | Machine Health Checks, node problem detector, automated reboot/reprovision | 60 min |
| [7.4 Observability Without Cloud Services](module-7.4-observability/) | Self-hosted Prometheus + Thanos, Grafana, Loki, IPMI exporter | 60 min |
| [7.5 Capacity Expansion & Hardware Refresh](module-7.5-capacity-expansion/) | Adding racks, mixed CPU generations, topology spread, refresh cycles | 60 min |
