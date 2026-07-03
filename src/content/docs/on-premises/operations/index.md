---
title: "Day-2 Operations"
sidebar:
  order: 0
---

Day-2 operations on bare metal Kubernetes clusters are fundamentally different from managed cloud services. There is no "upgrade cluster" button, no auto-replacing failed nodes, no built-in observability stack, and no default registries or pipelines. You own the hardware, the operating system, the control plane, and every component in between.

These modules cover the operational practices that keep on-premises clusters healthy, current, and scalable over multi-year hardware lifecycles. You will learn how to handle node failures, execute zero-downtime upgrades, manage hardware firmware, and build out the essential developer platform services—such as self-hosted CI/CD, image registries, and serverless capabilities—that make bare metal feel like a fully integrated cloud environment.

## Modules

| Module | Description | Time |
|--------|-------------|------|
| [Module 7.1: Kubernetes Upgrades on Bare Metal](module-7.1-upgrades/) | kubeadm upgrade path, drain strategies, rollback, version skew | 60 min |
| [Module 7.2: Hardware Lifecycle & Firmware](module-7.2-hardware-lifecycle/) | BIOS/firmware updates, disk replacement, SMART monitoring, Redfish API | 60 min |
| [Module 7.3: Node Failure & Auto-Remediation](module-7.3-node-remediation/) | Machine Health Checks, node problem detector, automated reboot/reprovision | 60 min |
| [Module 7.4: Observability Without Cloud Services](module-7.4-observability/) | Self-hosted Prometheus + Thanos, Grafana, Loki, IPMI exporter | 90 min |
| [Module 7.5: Capacity Expansion & Hardware Refresh](module-7.5-capacity-expansion/) | Adding racks, mixed CPU generations, topology spread, refresh cycles | 60 min |
| [Self-Hosted CI/CD](module-7.6-self-hosted-cicd/) | Building robust pipeline infrastructure, runners, and GitOps on bare metal | 60 min |
| [Self-Hosted Container Registry](module-7.7-self-hosted-registry/) | Deploying Harbor or similar registries, replication, caching, and vulnerability scanning | 60 min |
| [Observability at Scale](module-7.8-observability-at-scale/) | Long-term metric retention, high availability logging, and distributed tracing architectures | 90-120 min |
| [Serverless on Bare Metal](module-7.9-serverless-bare-metal/) | Implementing Knative, OpenFaaS, and event-driven architectures without cloud primitives | 60 min |