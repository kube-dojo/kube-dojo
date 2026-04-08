---
title: "Multi-Cluster & Platform"
sidebar:
  order: 0
---

On-premises organizations rarely run a single Kubernetes cluster. As teams grow and workloads diversify, the need for multiple clusters emerges -- dev/staging/prod separation, regional deployments, tenant isolation, or simply blast-radius reduction. But unlike the cloud, where spinning up a new cluster takes minutes and costs only API calls, on-premises multi-cluster means managing physical servers, control plane placement, and lifecycle automation with limited hardware.

This section covers the infrastructure platforms that sit beneath Kubernetes (vSphere, OpenStack, Harvester), the control plane strategies that let you run many clusters on few servers (vCluster, Kamaji), and the declarative lifecycle tools that treat clusters as cattle (Cluster API on bare metal).

## Modules

| Module | Description | Time |
|--------|-------------|------|
| [5.1 Private Cloud Platforms](module-5.1-private-cloud/) | VMware vSphere + Tanzu, OpenStack + Magnum, Harvester | 45 min |
| [5.2 Multi-Cluster Control Planes](module-5.2-multi-cluster-control-planes/) | vCluster, Kamaji, shared vs dedicated control planes | 50 min |
| [5.3 Cluster API on Bare Metal](module-5.3-cluster-api-bare-metal/) | CAPM3, CAPV, declarative lifecycle, GitOps-driven clusters | 50 min |
