---
title: "Multi-Cluster & Platform"
sidebar:
  order: 0
---

On-premises organizations rarely run a single Kubernetes cluster. As teams grow and workloads diversify, the need for multiple clusters emerges -- dev/staging/prod separation, regional deployments, tenant isolation, or simply blast-radius reduction. But unlike the cloud, where spinning up a new cluster takes minutes and costs only API calls, on-premises multi-cluster means managing physical servers, control plane placement, and lifecycle automation with limited hardware.

This section covers the infrastructure platforms that sit beneath Kubernetes (vSphere, OpenStack, Harvester), the control plane strategies that let you run many clusters on few servers (vCluster, Kamaji), and the declarative lifecycle tools that treat clusters as cattle (Cluster API on bare metal). We will also explore the complexities of managing fleets of clusters, Kubernetes-as-a-Service control planes like Gardener, and ensuring high availability across disparate geographical locations.

By the end of this section, you will understand how to design, deploy, and operate a multi-cluster architecture on bare metal or private cloud infrastructure, moving away from fragile "pet" clusters to a robust, automated platform engineering approach.

## Modules

| Module | Description | Time |
|--------|-------------|------|
| [Module 5.1: Private Cloud Platforms](module-5.1-private-cloud/) | VMware vSphere + Tanzu, OpenStack + Magnum, Harvester | 45 min |
| [Module 5.2: Multi-Cluster Control Planes](module-5.2-multi-cluster-control-planes/) | vCluster, Kamaji, shared vs dedicated control planes | 50 min |
| [Module 5.3: Cluster API on Bare Metal](module-5.3-cluster-api-bare-metal/) | CAPM3, CAPV, declarative lifecycle, GitOps-driven clusters | 50 min |
| [Fleet Management](module-5.4-fleet-management/) | Managing multiple clusters at scale, policy distribution, and centralized observability | 45 min |
| [Active-Active Multi-Site](module-5.5-active-active-multi-site/) | Disaster recovery, cross-cluster networking, global load balancing, and state replication | 60 min |
| [Module 5.6: Gardener](module-5.6-gardener/) | Open-source Kubernetes-as-a-Service; Gardens/Seeds/Shoots architecture; cluster lifecycle at scale; comparison vs Cluster API and Crossplane | 60 min |
| [Module 5.7: Multi-Cluster On-Prem](module-5.7-multi-cluster-on-prem/) | kube-vip virtual IPs (L2/BGP), Karmada federation policy, Liqo transparent offloading; layered architecture for the on-prem multi-cluster stack | 60-70 min |
| [Module 5.8: OpenStack on Kubernetes](module-5.8-openstack-on-kubernetes/) | Architectural inversion: OpenStack control plane as K8s workloads (OpenStack-Helm, Loci, Atmosphere); Ceph+Rook storage; OVN-Kubernetes+Neutron convergence; Magnum as K8s-on-OpenStack; CERN/Walmart/AT&T production realities | 60-70 min |