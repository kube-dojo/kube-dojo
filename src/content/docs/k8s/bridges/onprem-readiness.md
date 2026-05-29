---
title: "Are You Ready for On-Prem Kubernetes?"
sidebar:
  order: 1
---

This bridge is for learners who can operate Kubernetes in managed-cloud or certification-style environments and are considering bare-metal or on-premises clusters. It closes the readiness gap between using a cloud provider's managed assumptions and owning hardware, networking, storage, provisioning, control-plane availability, and load-balancing behavior yourself.

## Diagnostic — Are You Ready?

- [ ] You can draw a basic spine-leaf network from memory and explain where racks, ToR switches, uplinks, and routing boundaries sit.
- [ ] You have PXE-booted a physical server or can explain the DHCP, TFTP, iPXE, firmware, and installer handoff.
- [ ] You can explain the difference between cattle and pets at the hardware layer, including how failed disks, NICs, DIMMs, and nodes are replaced.
- [ ] You can size CPU, RAM, disk, and GPU capacity for sustained workloads instead of bursty cloud instances.
- [ ] You understand BGP route advertisement well enough to explain why MetalLB in BGP mode changes upstream routing behavior.
- [ ] You can explain when kube-vip, MetalLB, and an external load balancer solve different problems.
- [ ] You have operated Ceph, Rook, Longhorn, Portworx, or another distributed storage system beyond a demo install.
- [ ] You can describe how etcd quorum fails when physical fault domains are mapped poorly.
- [ ] You know what happens when a rack loses power, a switch reloads, or a storage backplane degrades.
- [ ] You can separate workload availability from infrastructure availability when no managed control plane exists.
- [ ] You can estimate the procurement, delivery, burn-in, and replacement cycle for server hardware.
- [ ] You have a plan for monitoring hardware health, firmware drift, and physical inventory.

## Skills Gap Map

| What you have | What you need | Where to study it |
|---|---|---|
| Kubernetes API fluency | Physical infrastructure ownership | [Planning & Economics](/on-premises/planning/) |
| CKA-style cluster operations | Linux host and kernel confidence | [Linux Deep Dive](/linux/) |
| Managed node groups | Bare-metal provisioning workflow | [Bare Metal Provisioning](/on-premises/provisioning/) |
| Cloud load balancers | BGP, VIPs, and bare-metal service exposure | [On-Premises Networking](/on-premises/networking/) |
| Cloud block storage | Ceph and distributed storage operations | [On-Premises Storage](/on-premises/storage/) |
| Cloud failure domains | Rack, power, switch, and disk fault domains | [Planning & Economics](/on-premises/planning/) |
| Managed control plane expectations | Self-managed control-plane lifecycle | [Bare Metal Provisioning](/on-premises/provisioning/) |
| Single-cluster administration | Multi-cluster recovery and placement patterns | [Multi-Cluster Patterns](/on-premises/multi-cluster/) |
| Application troubleshooting | Infrastructure troubleshooting below Kubernetes | [Linux Deep Dive](/linux/) |
| Cloud cost awareness | Capital expense, depreciation, spares, and utilization | [Planning & Economics](/on-premises/planning/) |

## Sequenced Path

1. Start with [Linux Deep Dive](/linux/).
   Why this step: on-premises Kubernetes failures often begin below Kubernetes, in the kernel, disks, networking stack, firmware, or host services.

2. Read [Planning & Economics](/on-premises/planning/).
   Why this step: bare-metal clusters are capacity plans and operating commitments before they are Kubernetes clusters.

3. Work through [Bare Metal Provisioning](/on-premises/provisioning/).
   Why this step: repeatable node installation is the difference between a recoverable fleet and a pile of special-case servers.

4. Study [On-Premises Networking](/on-premises/networking/).
   Why this step: service exposure, node reachability, BGP route advertisement, VIP failover, and rack topology determine whether workloads are reachable under failure.

5. Study [On-Premises Storage](/on-premises/storage/).
   Why this step: stateful workloads on bare metal depend on storage systems that must be designed, monitored, repaired, and upgraded.

6. Move to [Multi-Cluster Patterns](/on-premises/multi-cluster/).
   Why this step: a single on-premises cluster is rarely the final reliability boundary for production, training, or regulated workloads.

## Anti-patterns

- Assuming managed-cloud habits transfer unchanged to physical infrastructure.
- Treating the control plane as someone else's uptime responsibility.
- Designing service exposure before understanding BGP, VIP failover, and upstream routing.
- Running stateful workloads before mastering the storage system that backs them.
- Buying hardware before defining workload profiles, failure domains, spares, and lifecycle policy.
- Treating rack power, cooling, firmware, and physical inventory as secondary details.

## What success looks like

- You can explain the cluster design from rack power to Kubernetes service exposure.
- You can rebuild a failed node without hand-crafted recovery steps.
- You can justify storage choices for stateless, stateful, and training workloads.
- You can describe how traffic reaches a service when a node, switch, or rack fails.
- You can map etcd, storage replicas, and workload replicas to real failure domains.
- You can tell when a problem belongs to Kubernetes, Linux, networking, hardware, or storage.

## First module to read

Start with [Planning & Economics](/on-premises/planning/).
