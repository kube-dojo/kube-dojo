---
title: "Planning & Economics"
sidebar:
  order: 0
---

Before buying a single server, you need to answer fundamental questions about your infrastructure strategy. The decision to run Kubernetes on your own hardware requires careful consideration of the trade-offs between cloud convenience and the control, performance, and long-term cost savings of an on-premises deployment. Should we go on-prem at all? How many servers do we need? How should we organize our clusters? What will it cost over three years?

In this section, we will explore the critical planning stages required for a successful on-premises Kubernetes initiative. We will evaluate the business case for repatriation, understand how to properly size servers for specific workloads, and design a cluster topology that ensures high availability and resilience across your physical data centers.

Finally, we will delve into the economics of running your own hardware. You will learn how to calculate Total Cost of Ownership (TCO), build a comprehensive budget encompassing CapEx and OpEx, and implement FinOps practices to track and charge back usage across your internal teams. By the end of these modules, you will have a solid foundation for designing and funding an enterprise-grade on-premises Kubernetes environment.

## Modules

| Module | Description | Time |
|--------|-------------|------|
| [Module 1.1: The Case for On-Premises Kubernetes](module-1.1-case-for-on-prem/) | Cloud vs on-prem decision framework, five drivers, breakeven analysis | 45 min |
| [Module 1.2: Server Sizing & Hardware Selection](module-1.2-server-sizing/) | CPU, RAM, NVMe, NUMA, GPU considerations | 60 min |
| [Module 1.3: Cluster Topology Planning](module-1.3-cluster-topology/) | Shared vs dedicated control planes, etcd sizing, rack-aware scheduling | 60 min |
| [Module 1.4: TCO & Budget Planning](module-1.4-tco-budget/) | CapEx vs OpEx, power/cooling, staffing, cloud breakeven | 45 min |
| [Module 1.5: On-Prem FinOps & Chargeback](module-1.5-onprem-finops-chargeback/) | Resource tracking, internal billing models, optimizing on-prem efficiency | 45 min |