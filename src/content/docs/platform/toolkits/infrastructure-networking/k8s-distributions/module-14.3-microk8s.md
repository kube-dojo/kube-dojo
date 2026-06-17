---
revision_pending: false
title: "Module 14.3: MicroK8s - Snap-Based Kubernetes from Canonical"
slug: platform/toolkits/infrastructure-networking/k8s-distributions/module-14.3-microk8s
sidebar:
  order: 4
---
> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: 40-45 minutes

## Overview

MicroK8s is Kubernetes delivered as a snap — Canonical's answer to the question "what if installing a production-grade Kubernetes cluster felt as natural as installing any other package on Ubuntu?" It is a CNCF-certified Kubernetes distribution that packages the entire control plane, the kubelet, the container runtime, a distributed datastore, and thirty-plus optional add-ons into a single snap that auto-updates through Canonical's release channels. You install it with one command. You enable DNS, storage, ingress, and monitoring with one command each. And when you need high availability, you add nodes with one command.

But MicroK8s is more than convenience. It represents a deliberate architectural bet: that the snap confinement model — a sandboxed, transactionally updated, channel-tracked package format — can deliver Kubernetes with less operational toil than traditional tarball-and-systemd installations, while the dqlite datastore can provide Raft-consensus HA with a fraction of etcd's operational surface. That bet has consequences for how you upgrade, how you debug, and what happens when a node fails. This module teaches you MicroK8s from first principles: not just the commands, but why they exist and what tradeoffs they encode.

## Prerequisites

- Kubernetes fundamentals (kubectl, deployments, services)
- Linux command-line basics
- Ubuntu or snap-capable Linux system
- Understanding of container runtimes

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy MicroK8s with snap-based installation and configure add-ons for development workflows**
- **Configure MicroK8s clustering for multi-node HA setups using the built-in join mechanism**
- **Implement MicroK8s add-ons for GPU workloads, observability, and service mesh capabilities**
- **Compare MicroK8s's add-on ecosystem against K3s and K0s for developer and edge use cases**


## Why This Module Matters

To understand why MicroK8s exists, you first need to understand what a Kubernetes distribution is and why anyone bothers to build one. Upstream Kubernetes — the source code in the kubernetes/kubernetes repository — does not ship as a single installable artifact that you can run on a server and call done. The upstream project produces component binaries: kube-apiserver, kube-controller-manager, kube-scheduler, kubelet, and kube-proxy. To turn those binaries into a working cluster, you must independently choose and configure a container runtime, a CNI networking plugin, a CSI storage driver, an ingress controller, a mechanism for exposing LoadBalancer services, and a datastore for cluster state. Each of those choices cascades into further decisions about certificate management, upgrade sequencing, observability integration, and security posture. Getting all of them right — and keeping them right across upgrades — is the operational burden that a Kubernetes distribution absorbs on your behalf.

A distribution is a curated, tested, integrated bundle of these components, shipped with a defined upgrade path, a support model, and a set of opinions about how the pieces should fit together. kubeadm, the reference installer maintained by the upstream Kubernetes project, gives you the closest thing to a "vanilla" assembly experience: it bootstraps the control plane, generates certificates, and leaves the CNI and ingress choices to you. It is the baseline against which every distribution is measured. MicroK8s departs from that baseline in three fundamental ways.

First, it wraps everything in a snap. A snap is not just a package — it is a confined execution environment with transactional updates, automatic rollback on failure, and release channels that map to stability levels. When you install MicroK8s, Snapcraft downloads a signed, verifiable bundle that includes the Kubernetes binaries, containerd, dqlite, and all the add-on manifests. Updates happen automatically within the channel you track (so `1.34/stable` receives patch releases without manual intervention), and if an update breaks something, `snap revert microk8s` takes you back to the previous working revision. This is a fundamentally different operational model from downloading a binary and wiring up systemd units yourself — it outsources packaging discipline to the snap ecosystem and lets you treat Kubernetes version management like any other system package.

Second, MicroK8s replaces etcd with dqlite for its default datastore. Dqlite is a distributed SQL database built by Canonical on top of SQLite and the Raft consensus algorithm. Each MicroK8s node runs a dqlite process. When you form a cluster of three or more nodes, the dqlite instances elect a leader via Raft, replicate writes to a quorum of followers, and present a familiar SQL interface to the control plane. The rationale is simplicity: SQLite has orders of magnitude fewer lines of code than etcd, it is one of the most heavily tested software libraries in existence, and its operational surface — backups are file copies, recovery is file replacement — is far smaller than etcd's. The tradeoff is scale. Dqlite has not been battle-tested at the extreme cluster sizes that etcd handles (thousands of nodes, tens of thousands of concurrent watches). For the 3-to-20-node clusters that MicroK8s targets — developer workstations, CI runners, edge appliances, small production deployments — dqlite is a pragmatic fit. If you need larger scale, MicroK8s also supports an etcd add-on.

Third, MicroK8s takes a curated-extension approach to optional components. In k3s, the default CNI (Flannel), ingress controller (Traefik), service load-balancer (Klipper), and storage provisioner (local-path) are compiled into the single binary and enabled by default. You disable them if you don't want them. MicroK8s inverts this: nothing beyond the core control plane is enabled until you explicitly opt in with `microk8s enable`. Each add-on — DNS, storage, ingress, MetalLB, Prometheus, Grafana, Istio, GPU operator, and thirty more — is a tested, version-locked manifest maintained in the MicroK8s source tree by Canonical. When you enable one, you are not pulling an arbitrary Helm chart from the internet; you are invoking an integration that has been verified against the specific Kubernetes version in your snap channel. This curated-extension model means you only run what you need, but you also get the assurance that what you run has been tested as part of the distribution.

This module teaches you to operate MicroK8s with an understanding of these architectural decisions. By the end, you will not just know the commands — you will know why the snap model matters for upgrade safety, why dqlite changes your HA planning, and when the curated add-on approach serves you better than a bundled-by-default distribution.

## Cross-Distribution Comparison

Before diving into MicroK8s specifics, here is how the three lightweight distributions and the upstream kubeadm baseline compare on the dimensions that matter for cluster operations. Each row represents a capability. The cells tell you what each distribution ships — and, implicitly, what tradeoffs you accept by choosing it.

| Capability | kubeadm (baseline) | k3s | k0s | MicroK8s |
|---|---|---|---|---|
| Default datastore | etcd (you deploy) | SQLite (single-node), embedded etcd (HA) | etcd (embedded, no external dependency) | dqlite (distributed SQLite) |
| HA mechanism | External etcd cluster (manual) | Embedded etcd (3+ servers) | Embedded etcd (3+ controllers) | Dqlite Raft (3+ nodes, `microk8s add-node`) |
| Bundled CNI | None (you choose) | Flannel (default), Cilium (option) | kube-router (default), Calico (option) | Calico (built-in, no add-on needed) |
| Bundled ingress | None (you choose) | Traefik (bundled in binary) | None (you add) | nginx (via `microk8s enable ingress`) |
| Bundled service LB | None (cloud-provider or MetalLB) | Klipper (ServiceLB) | None (you add) | MetalLB (via `microk8s enable metallb`) |
| Bundled storage | None (you choose) | Local Path Provisioner | None (you add) | hostpath-storage (via `microk8s enable storage`) |
| Install mechanism | curl + tar + systemd units | curl + script or single binary | Single binary + systemd unit | snap install (transactional, auto-updating) |
| Packaging model | Component binaries + manifests | Single binary (~60 MB, all-in-one) | Single binary (~160 MB, modular) | Snap package (sandboxed, channel-tracked) |
| Primary use case | Production reference, custom clusters | Edge, IoT, resource-constrained, dev | Multi-platform, zero host deps | Ubuntu-native dev, CI, appliances, edge |
| CNCF conformance | Baseline (reference) | Certified | Certified | Certified |

> **Landscape snapshot — as of 2026-06. This changes fast; verify against upstream docs before relying on specifics.**
>
> - MicroK8s latest stable channels: 1.33, 1.34, 1.35 (most recent stable 1.35/stable, published 2026-04; tracked per minor version)
> - Minimum resources: 540 MB RAM (idle), recommended 4 GB+ for workloads, 2+ vCPUs
> - Supported architectures: amd64, arm64 (Raspberry Pi 4+, AWS Graviton, Apple Silicon multipass)
> - Strict confinement snap variant available for hardened environments (requires manual interface connections)
> - Snap refresh cadence: patch releases auto-apply within the tracked channel; minor version upgrades require explicit channel switch
> - Bundled containerd version: pinned per MicroK8s release; verify with `microk8s ctr version`
> - CNCF maturity: Certified Kubernetes (conformant distribution, passes all conformance tests)
> - Community support: Ubuntu Discourse, #microk8s on Kubernetes Slack, GitHub issues at canonical/microk8s

## Did You Know?

- **Snap Delivery**: MicroK8s is delivered via snap — automatic updates, rollbacks, and confined execution. If an update breaks your cluster, `snap revert microk8s` returns you to the previous working revision in seconds.
- **Dqlite**: Uses Dqlite (distributed SQLite with Raft consensus) instead of etcd for clustering — simpler operational surface, smaller resource footprint, same Raft durability guarantees for clusters up to ~20 nodes.
- **CNCF Certified**: Passes all Kubernetes conformance tests. Applications written against MicroK8s run identically on any other CNCF-certified Kubernetes — same API, same semantics, no vendor lock-in.
- **GPU Support**: Ships a native NVIDIA GPU operator add-on for AI/ML workloads. `microk8s enable gpu` configures the NVIDIA container toolkit, device plugin, and GPU feature discovery automatically.

## MicroK8s Architecture

Before you run `snap install microk8s --classic`, it is worth understanding what that command actually places on your machine. The snap contains the full Kubernetes control plane — kube-apiserver, kube-controller-manager, and kube-scheduler — plus the kubelet as a system daemon, kube-proxy for network rules, and containerd as the container runtime. All of these run inside the snap's confined mount namespace, writing configuration to `/var/snap/microk8s/current/args/` and persistent data to `/var/snap/microk8s/common/`. The `--classic` flag relaxes snap confinement because a Kubernetes node needs to create network interfaces, mount filesystems, and manage cgroups — operations that strict confinement would block. Canonical also ships a strict-confinement variant for environments where security policy demands it, but it requires manually connecting snap interfaces and is not the default path.

The architecture diagram below shows how these components layer together. Notice the add-on system at the bottom: each add-on is a script at `/snap/microk8s/current/addons/<name>/enable` that applies Kubernetes manifests, waits for pods to reach readiness, and configures integration with other add-ons. The add-ons are version-locked to the MicroK8s release — when you track `1.34/stable`, you receive add-on manifests tested against Kubernetes 1.34, and when you refresh to `1.35/stable`, the add-ons update in lockstep.

```
MicroK8s ARCHITECTURE
─────────────────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────────────────┐
│                         MicroK8s Node                                       │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     Snap Package                                    │   │
│  │                     /snap/microk8s                                  │   │
│  │                                                                     │   │
│  │  ┌──────────────────── Core Services ───────────────────────┐      │   │
│  │  │                                                          │      │   │
│  │  │  kube-apiserver    kube-controller-manager    kube-scheduler    │   │
│  │  │  kubelet           kube-proxy                containerd         │   │
│  │  │                                                          │      │   │
│  │  └──────────────────────────────────────────────────────────┘      │   │
│  │                                                                     │   │
│  │  ┌──────────────────── Datastore ───────────────────────────┐      │   │
│  │  │                                                          │      │   │
│  │  │  Dqlite (distributed SQLite) - HA clustering             │      │   │
│  │  │  or etcd (optional via add-on)                           │      │   │
│  │  │                                                          │      │   │
│  │  └──────────────────────────────────────────────────────────┘      │   │
│  │                                                                     │   │
│  │  ┌──────────────────── Add-ons System ──────────────────────┐      │   │
│  │  │                                                          │      │   │
│  │  │  dns        │  storage     │  ingress      │  dashboard │      │   │
│  │  │  prometheus │  registry    │  metallb      │  istio     │      │   │
│  │  │  gpu        │  cert-manager│  observability│  argocd    │      │   │
│  │  │  ... and 30+ more                                       │      │   │
│  │  │                                                          │      │   │
│  │  └──────────────────────────────────────────────────────────┘      │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                      Data Locations                                    │ │
│  │                                                                       │ │
│  │  Config: /var/snap/microk8s/current                                  │ │
│  │  Data:   /var/snap/microk8s/common                                   │ │
│  │  Images: /var/snap/microk8s/common/var/lib/containerd               │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

ADD-ON ARCHITECTURE:
─────────────────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────────────────┐
│                           Add-on System                                      │
│                                                                             │
│  microk8s enable <addon>                                                    │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  /snap/microk8s/current/addons/<addon>/enable                       │   │
│  │                                                                     │   │
│  │  1. Apply manifests (kubectl apply -f)                             │   │
│  │  2. Wait for pods to be ready                                       │   │
│  │  3. Configure integration with other add-ons                        │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Add-on Categories:                                                         │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Core:         dns, storage, ingress, dashboard                            │
│  Networking:   metallb, cilium, multus                                     │
│  Observability: prometheus, observability (Loki+Grafana+Tempo)            │
│  Security:     cert-manager, rbac                                          │
│  CI/CD:        registry, argocd, fluxcd                                    │
│  AI/ML:        gpu, kubeflow                                               │
│  Service Mesh: istio, linkerd                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Installing MicroK8s

Installation is the first place where the snap model diverges from traditional Kubernetes setup. With kubeadm, you install a container runtime, install kubeadm/kubelet/kubectl packages, run `kubeadm init`, configure a CNI, and then repeat variations of this on each node. With MicroK8s, the snap bundles everything — binaries, runtime, datastore — into one package, and the installation is a single command followed by group membership configuration.

The `--classic` flag matters. Snaps normally run under strict confinement: they see a private `/tmp`, cannot access host files outside designated interfaces, and operate with a restricted system call filter. A Kubernetes control plane cannot function under those constraints — it needs to manage network interfaces (for CNI and kube-proxy), mount volumes (for the kubelet and CSI), write to cgroup filesystems, and bind to privileged ports. The `--classic` flag disables confinement, giving MicroK8s the same access to the host as a traditionally installed service. Canonical provides a strict-confinement variant as an alternative; it requires you to manually connect snap interfaces (`snap connect microk8s:hardware-observe`, `snap connect microk8s:network-control`, and several others), which is more secure but more work to set up. For development and most production use, `--classic` is the recommended path.

After installation, you add your user to the `microk8s` group. This avoids the need to prefix every command with `sudo` — the group membership grants access to the MicroK8s socket that the snap exposes. The `newgrp microk8s` command (or logging out and back in) activates the group membership in your current shell session.

### Quick Install (Ubuntu)

```bash
# Install MicroK8s
sudo snap install microk8s --classic

# Add user to microk8s group (avoid sudo)
sudo usermod -a -G microk8s $USER
sudo chown -R $USER ~/.kube
newgrp microk8s

# Check status
microk8s status --wait-ready

# Enable essential add-ons
microk8s enable dns storage
```

### Install Specific Version

The snap channel model is one of MicroK8s's strongest operational features. Each Kubernetes minor version has its own set of channels — `1.34/stable`, `1.34/candidate`, `1.34/beta`, `1.34/edge` — and `latest/stable` tracks the most recent stable release. When you install with `--channel=1.34/stable`, you receive the latest patch release on the 1.34 line. When 1.34.4 ships, snap refreshes you automatically. When 1.35.0 ships, you stay on 1.34.x until you explicitly switch channels. This gives you the best of both worlds: automatic patch updates for security and bug fixes, plus deliberate control over minor-version upgrades.

```bash
# List available versions
snap info microk8s

# Install specific channel
sudo snap install microk8s --classic --channel=1.34/stable

# Track latest patch releases for 1.34
sudo snap refresh microk8s --channel=1.34/stable
```

### Install on Other Linux Distributions

MicroK8s is Ubuntu-native, but it works on any Linux distribution that supports snapd. The snap daemon itself is available on most major distributions, though the integration quality varies — Ubuntu has the deepest snapd integration, followed by Debian and Fedora. On distributions without native snapd support, you can install it manually, but expect to debug interface connections and AppArmor profiles. The `--classic` flag mitigates most of these issues by disabling confinement, but if strict confinement matters to your environment, use Ubuntu.

```bash
# Install snapd first (if not on Ubuntu)
# Fedora
sudo dnf install snapd
sudo ln -s /var/lib/snapd/snap /snap

# Debian
sudo apt install snapd

# Then install MicroK8s
sudo snap install microk8s --classic
```

## Add-ons System

The add-on system is where MicroK8s's curated-extension philosophy becomes concrete. In a distribution like k3s, the CNI, ingress controller, service load-balancer, and storage provisioner are compiled into the single binary — they are present and running from the moment you start the service. This is convenient for getting a fully functional cluster in seconds, but it means you are running components you may not need, each consuming memory and CPU, each representing an attack surface, each requiring updates you may not have opted into. MicroK8s takes the opposite approach: nothing beyond the bare control plane plus Calico CNI is active until you explicitly enable it. Each add-on you enable is tested against your specific Kubernetes version and maintained in the MicroK8s source tree by Canonical.

When you run `microk8s enable dns`, the command invokes a script at `/snap/microk8s/current/addons/dns/enable`. That script applies CoreDNS manifests, waits for the CoreDNS pods to become ready, and registers the DNS service with the cluster. If you later run `microk8s disable dns`, the corresponding `disable` script tears everything down cleanly. The same pattern holds for every add-on: enable, verify, integrate; disable, teardown, clean up. This is not a Helm chart or a raw manifest applied outside the distribution's control — it is a first-class integration tested as part of the release.

The add-ons are categorized by function, and understanding those categories helps you plan your cluster. Core add-ons (DNS, storage, ingress, dashboard) are the ones you enable on almost every cluster. Networking add-ons (MetalLB, Cilium, Multus) extend how pods communicate within and outside the cluster. Observability add-ons (Prometheus, the full observability stack with Loki, Grafana, and Tempo) give you metrics, logs, and traces. Security add-ons (cert-manager, RBAC) handle TLS certificates and access control. CI/CD add-ons (local registry, ArgoCD, FluxCD) turn MicroK8s into a development platform. AI/ML add-ons (GPU operator, Kubeflow) configure hardware acceleration and ML pipelines. The full catalog has over thirty add-ons, and Canonical adds more with each release.

A note on the CNI: MicroK8s ships with Calico enabled by default — you do not need to enable a separate CNI add-on as you do with kubeadm. The built-in Calico provides network policy enforcement in addition to basic pod networking, which is a security advantage over Flannel-only configurations. If you prefer Cilium for its eBPF-based data plane, `microk8s enable cilium` replaces Calico.

### Core Add-ons

The core add-ons form the foundation that nearly every MicroK8s cluster needs. CoreDNS provides cluster-local name resolution — without it, pods cannot find each other by service name, and practically nothing works. The hostpath storage provisioner creates PersistentVolumes backed by directories on the node's filesystem, which is sufficient for development and single-node deployments but not for multi-node HA (a pod scheduled on node B cannot access a hostpath PV on node A). The Kubernetes Dashboard gives you a web UI for inspecting and managing cluster resources, though you should be aware that it exposes significant cluster access and must be secured behind authentication in any shared environment. The nginx ingress controller translates Kubernetes Ingress resources into nginx configuration, handling TLS termination, path-based routing, and virtual hosting. And the metrics-server collects resource usage data from the kubelet, feeding both `kubectl top` and the Horizontal Pod Autoscaler.

Each of these add-ons solves a specific infrastructure problem that, in a kubeadm cluster, you would solve by finding, installing, configuring, and maintaining a separate component — often from a different vendor with its own release cycle. The MicroK8s add-on system collapses that into a single, tested command, with the tradeoff that you are accepting Canonical's chosen version and configuration defaults. For most development and small-production use cases, that tradeoff is worth it. For production clusters with specific version-pinning or configuration requirements, you may want to deploy your own ingress controller or storage provisioner outside the add-on system — MicroK8s does not prevent this; it is a standard Kubernetes cluster, and you can apply any manifest you choose.

```bash
# DNS (CoreDNS) - required for most workloads
microk8s enable dns

# Storage (hostpath provisioner)
microk8s enable storage

# Dashboard (Kubernetes Dashboard)
microk8s enable dashboard

# Get dashboard token
microk8s kubectl describe secret -n kube-system microk8s-dashboard-token

# Ingress (nginx ingress controller)
microk8s enable ingress

# Metrics Server (for kubectl top)
microk8s enable metrics-server
```

### Networking Add-ons

MetalLB deserves special attention because it solves a problem that every bare-metal Kubernetes cluster faces: how do you expose a Service of type LoadBalancer without a cloud provider's load-balancer integration? In AWS, the cloud-controller-manager provisions an ELB. In your home lab or on-prem cluster, there is no such integration. MetalLB fills that gap by responding to ARP requests (Layer 2 mode) or speaking BGP to your router (BGP mode), assigning an IP from a range you specify to each LoadBalancer service. The command `microk8s enable metallb:192.168.1.200-192.168.1.220` both enables the add-on and configures the IP pool in one step — no separate ConfigMap to create, no YAML to apply.

```bash
# MetalLB (bare-metal load balancer)
microk8s enable metallb:192.168.1.200-192.168.1.220

# Or with interactive configuration
microk8s enable metallb
# Enter IP range when prompted

# Cilium (eBPF-based CNI)
microk8s enable cilium

# Multus (multiple network interfaces)
microk8s enable multus
```

### Observability Add-ons

The observability add-on — distinct from the legacy `prometheus` add-on — deploys a full Grafana LGTM stack: Loki for log aggregation, Grafana for visualization, Tempo for distributed tracing, and Mimir (or Prometheus) for metrics. This is a significant operational shortcut compared to assembling these components yourself. A single `microk8s enable observability` command deploys the entire stack, configures scrape targets for your cluster, and pre-loads Kubernetes dashboards in Grafana. The tradeoff is resource consumption — the full stack can consume 2-4 GB of RAM depending on retention settings — so plan your node sizing accordingly. For lighter-weight monitoring, the legacy `prometheus` add-on deploys just Prometheus and Grafana with fewer components.

```bash
# Prometheus + Grafana (legacy)
microk8s enable prometheus

# Observability stack (Prometheus + Loki + Grafana + Tempo)
microk8s enable observability

# Access Grafana
microk8s kubectl port-forward -n observability svc/grafana 3000:80
```

### Security Add-ons

```bash
# cert-manager
microk8s enable cert-manager

# RBAC (enabled by default on newer versions)
microk8s enable rbac
```

### AI/ML Add-ons

The GPU add-on automates what is otherwise a multi-step manual process: installing the NVIDIA container toolkit, configuring the nvidia-container-runtime as a containerd runtime handler, deploying the NVIDIA device plugin daemonset, and enabling GPU feature discovery for node labelling. After `microk8s enable gpu`, pods that request `nvidia.com/gpu` resources are scheduled to GPU-equipped nodes and have access to the host's NVIDIA drivers through the container runtime. The add-on handles driver compatibility checks and will fail with a clear error message if the NVIDIA drivers are missing or mismatched.

```bash
# GPU support (NVIDIA)
microk8s enable gpu

# Kubeflow (full ML platform)
microk8s enable kubeflow
```

### CI/CD Add-ons

The local registry add-on is particularly valuable for development workflows. It deploys a Docker Registry v2 instance inside the cluster, exposed on `localhost:32000` on the host. You push images to it from your local Docker daemon, and pods reference those images in their container specs. This eliminates the need for an external registry during development — no Docker Hub rate limits, no AWS ECR authentication, no Harbor instance to manage. The registry uses hostpath storage by default, so images survive MicroK8s restarts but not node destruction. For persistent storage, enable the storage add-on first and the registry will provision a PVC.

```bash
# Local registry
microk8s enable registry

# Push to local registry
docker tag myapp localhost:32000/myapp:v1
docker push localhost:32000/myapp:v1

# ArgoCD
microk8s enable argocd

# FluxCD
microk8s enable fluxcd
```

### List All Add-ons

```bash
microk8s status

# Example output:
# addons:
#   enabled:
#     dns
#     storage
#     dashboard
#   disabled:
#     ambassador
#     cilium
#     gpu
#     ...
```

## Multi-Node Clustering

A single-node MicroK8s cluster is useful for development, but production workloads demand high availability. MicroK8s achieves HA through dqlite, a distributed SQLite implementation built on the Raft consensus algorithm. Understanding how dqlite maintains consistency across nodes will help you plan your cluster topology and debug failures.

Raft works by electing a leader from among the participating nodes. The leader receives all write requests from the API server, appends them to its log, and replicates them to a majority (quorum) of followers. Only after a majority acknowledges the write does the leader commit it and return success to the client. This means a cluster of three nodes can tolerate one node failure and remain operational; a cluster of five can tolerate two. The leader also sends periodic heartbeats to followers — if followers stop hearing from the leader, they initiate a new election. The election happens automatically; MicroK8s handles leader transitions without manual intervention.

The practical implication for MicroK8s clustering is that you need an odd number of nodes (3, 5, 7) for a resilient HA configuration. With two nodes, you have no failure tolerance — if either node goes down, the remaining node cannot form a quorum and the cluster becomes read-only. With three nodes, you can lose one and keep operating. The `microk8s add-node` command on the primary generates a join token; you run `microk8s join <token>` on additional nodes, and they automatically join the dqlite cluster and sync the datastore. The entire operation — from fresh install to three-node HA — takes about five minutes.

One important distinction from etcd-based clusters: dqlite does not require you to manage separate etcd certificates, etcd peer URLs, or etcd membership. The `add-node` / `remove-node` / `leave` commands handle cluster membership changes through MicroK8s's clustering API, which manages the dqlite membership behind the scenes. If a node leaves ungracefully (power loss, kernel panic), you run `microk8s remove-node <name>` on a surviving node to evict it from the cluster. The remaining nodes continue operating with the new membership.

MicroK8s uses Dqlite (distributed SQLite) for HA:

```
Dqlite Clustering
─────────────────────────────────────────────────────────────────────────────

       ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
       │    Node 1     │     │    Node 2     │     │    Node 3     │
       │   (leader)    │     │  (follower)   │     │  (follower)   │
       │               │     │               │     │               │
       │  ┌─────────┐  │     │  ┌─────────┐  │     │  ┌─────────┐  │
       │  │ Dqlite  │◄─┼─────┼─▶│ Dqlite  │◄─┼─────┼─▶│ Dqlite  │  │
       │  └─────────┘  │     │  └─────────┘  │     │  └─────────┘  │
       │               │     │               │     │               │
       │  API Server   │     │  API Server   │     │  API Server   │
       │  Controller   │     │  Controller   │     │  Controller   │
       │  Scheduler    │     │  Scheduler    │     │  Scheduler    │
       └───────────────┘     └───────────────┘     └───────────────┘

Benefits of Dqlite:
• Simpler than etcd (SQLite semantics)
• Lower resource usage
• Automatic leader election
• Raft consensus for durability
```

### Add Nodes

Joining a node to a MicroK8s cluster is simpler than any other Kubernetes distribution's equivalent operation, and understanding why reveals the architectural difference dqlite makes. In an etcd-based cluster (whether kubeadm, k3s with embedded etcd, or k0s), adding a control-plane node requires you to generate new certificates for the joining node, configure etcd peer URLs, update the etcd membership, and ensure the new node's API server can reach the existing etcd cluster. MicroK8s collapses all of this into `microk8s add-node` because dqlite is managed by MicroK8s's clustering API rather than by a separate etcd operator. The join token encodes the primary's IP address, port, and a cryptographic secret that proves the joining node is authorized to participate in the Raft group. Once joined, the new node's dqlite instance syncs the full datastore from the leader and begins participating in consensus immediately — no manual certificate distribution, no etcd member list updates, no kubeadm config to propagate.

**On the first node (primary):**

```bash
# Generate join token
microk8s add-node

# Output:
# Join node with:
# microk8s join 192.168.1.10:25000/abc123...
```

**On additional nodes:**

```bash
# Install MicroK8s
sudo snap install microk8s --classic

# Join the cluster
microk8s join 192.168.1.10:25000/abc123...

# Verify on primary
microk8s kubectl get nodes
```

### Remove Nodes

Cluster membership hygiene matters for Raft consensus health. When a node leaves the cluster ungracefully — power loss, kernel panic, network partition that outlasts the heartbeat timeout — the remaining nodes continue operating, but the dqlite cluster still considers the departed node a member. This is not catastrophic (Raft tolerates failed nodes as long as a quorum remains), but it does mean the cluster is running in a degraded state: every write must still be replicated to a quorum of the configured membership, and the departed node counts toward that configuration even though it will never acknowledge a write. Running `microk8s remove-node <name>` on a surviving node evicts the departed node from the dqlite cluster, restoring full operational resilience. If the node left cleanly with `microk8s leave`, it removes itself from the membership, and no manual cleanup is needed. The distinction matters: `leave` is a graceful departure; `remove-node` is a forced eviction for ungraceful failures. Use the right one for the situation.

```bash
# On the node to remove
microk8s leave

# On remaining nodes (if needed)
microk8s remove-node <node-name>
```

## Configuration

MicroK8s stores component arguments in flat files under `/var/snap/microk8s/current/args/` — one file per component. This is simpler than kubeadm's cluster configuration, which layers kubelet configuration, kube-proxy configuration, and control-plane configuration across multiple YAML files and ConfigMaps. To change the API server's admission plugins, you edit `/var/snap/microk8s/current/args/kube-apiserver` and restart MicroK8s. There is no `kubeadm upgrade apply` dance, no `kubeadm config migrate` for configuration version changes — MicroK8s handles the component lifecycle directly through snap services. The downside is that these argument files are snap-internal; if you uninstall the snap, they are removed. Back them up if your configuration is non-trivial.

### Accessing kubeconfig

```bash
# Use microk8s kubectl directly
microk8s kubectl get nodes

# Export kubeconfig for external tools
microk8s config > ~/.kube/config

# Or merge with existing config
KUBECONFIG=~/.kube/config:~/.kube/microk8s.config kubectl config view --flatten > ~/.kube/merged.config

# Create alias for convenience
alias kubectl='microk8s kubectl'
```

### Customizing API Server

```bash
# Edit API server arguments
sudo nano /var/snap/microk8s/current/args/kube-apiserver

# Add or modify arguments like:
# --enable-admission-plugins=NodeRestriction,PodSecurityPolicy
# --audit-log-path=/var/log/kubernetes/audit.log

# Restart to apply
microk8s stop
microk8s start
```

### Customizing kubelet

```bash
# Edit kubelet arguments
sudo nano /var/snap/microk8s/current/args/kubelet

# Example customizations:
# --max-pods=250
# --system-reserved=cpu=100m,memory=256Mi

# Restart
microk8s stop
microk8s start
```

### Container Runtime Configuration

MicroK8s uses containerd, and its configuration lives at `/var/snap/microk8s/current/args/containerd-template.toml`. This is a standard containerd configuration file, which means any containerd documentation applies — registry mirrors, snapshotter configuration, runtime handler registration all work the same way they would in a non-snap containerd installation. The only difference is the file path. If you need to add an insecure registry mirror (common in air-gapped or development environments), edit the `plugins."io.containerd.grpc.v1.cri".registry.mirrors` section of this file.

```bash
# containerd configuration
sudo nano /var/snap/microk8s/current/args/containerd-template.toml

# Add insecure registries
[plugins."io.containerd.grpc.v1.cri".registry.mirrors."myregistry.local:5000"]
  endpoint = ["http://myregistry.local:5000"]

# Restart containerd
microk8s stop
microk8s start
```

## Upgrading MicroK8s

The upgrade experience is where snap's transactional update model pays off most visibly. In a kubeadm-managed cluster, upgrading involves draining nodes, upgrading kubeadm, running `kubeadm upgrade plan` and `kubeadm upgrade apply`, upgrading kubelet and kubectl on each node, and uncordoning. It is a deliberate, multi-step process designed for production clusters where downtime is expensive. MicroK8s, by contrast, updates automatically within your channel — if you track `1.34/stable`, the snap daemon downloads and applies patch releases (1.34.3 → 1.34.4) on its refresh schedule, typically daily. This is convenient but carries risk: a patch release, however well-tested, could introduce a regression that breaks your workloads in the middle of the night.

For production, you should understand three controls: channel selection determines what you receive, refresh holding prevents automatic updates, and rollback gives you a safety net. Track a specific stable channel (`1.34/stable`), not `latest/stable`, so you control when minor-version upgrades happen. Hold refreshes during critical periods with `snap refresh --hold microk8s` and unhold when you are ready to test. And if an update breaks something, `snap revert microk8s` restores the previous revision — the snap keeps the last several revisions cached on disk, so rollback is a matter of seconds, not a multi-node drain-and-rebuild.

The channel naming convention maps directly to upstream Kubernetes versions: `1.34/stable` is Kubernetes 1.34, latest patch. `1.34/candidate` is the release candidate for the next patch. `1.34/beta` is the beta. `1.34/edge` is the bleeding edge — updated on every commit, useful for testing upcoming features but never for production. The `latest` track mirrors the most recent stable upstream release and is reasonable for development environments where you want the newest Kubernetes features as soon as Canonical packages them.

### Automatic Updates (Default)

```bash
# Check current channel
snap info microk8s

# Snaps update automatically by default
# To refresh immediately:
sudo snap refresh microk8s

# To hold automatic updates:
sudo snap refresh --hold microk8s

# To unhold:
sudo snap refresh --unhold microk8s
```

### Track Specific Channel

```bash
# Switch to a different Kubernetes version
sudo snap refresh microk8s --channel=1.35/stable

# Available channels:
# 1.34/stable, 1.34/candidate, 1.34/beta, 1.34/edge
# 1.35/stable, 1.35/candidate, ...
# latest/stable, latest/edge
```

### Rollback

```bash
# Revert to previous version
sudo snap revert microk8s

# List available revisions
snap list --all microk8s
```

## Air-Gapped Installation

Environments without internet access — military installations, financial data centers, manufacturing floors — need Kubernetes too. MicroK8s supports air-gapped deployment through snap's offline installation mechanism. On a connected machine, you download the snap and its cryptographic assertion file. The assertion is a signed document that verifies the snap's integrity and publisher — without it, snapd refuses to install. On the air-gapped machine, you acknowledge the assertion and install the snap from the local file. The snap contains all the Kubernetes binaries, so the cluster starts without internet access.

The container image problem is separate. While the snap includes the Kubernetes components, your application images are not bundled. You must export images from a connected registry (`docker save`), transfer them to the air-gapped machine, and import them into containerd with `microk8s ctr image import`. If you have many images, deploy the local registry add-on on a connected machine, push images to it, export the registry's storage directory, and seed the air-gapped registry with the same directory structure. For production air-gapped deployments, combine MicroK8s with a mirrored registry like Harbor or a generic Docker Registry instance.

```bash
# On connected machine:

# Download the snap
snap download microk8s --channel=1.34/stable

# This creates:
# microk8s_NNNN.snap
# microk8s_NNNN.assert

# Transfer to air-gapped machine, then:

# Install assertion first
sudo snap ack microk8s_NNNN.assert

# Install snap
sudo snap install microk8s_NNNN.snap --classic

# Import container images
# First, export from connected machine:
docker save myimage:tag | gzip > myimage.tar.gz

# On air-gapped machine:
microk8s ctr image import myimage.tar.gz
```

## Troubleshooting

When MicroK8s misbehaves, the tooling that snap provides often shortens the diagnostic cycle dramatically compared to a traditional Kubernetes installation. In a kubeadm cluster, debugging a failed API server means checking systemd unit status, grepping through `/var/log/kubernetes`, verifying certificate expiration dates, and cross-referencing kubeadm configuration against running arguments. MicroK8s consolidates most of this into two commands: `microk8s status` tells you which services are running and which add-ons are enabled, and `microk8s inspect` produces a comprehensive diagnostic tarball that Canonical's support team (and the community on Discourse) can use to triage issues without asking you twenty questions about your environment.

The inspect command is worth understanding in detail because it solves a real operational problem: when you post a question to a forum saying "my MicroK8s cluster is broken," the first response is almost always "please run microk8s inspect and attach the report." The report includes the output of `microk8s status`, the contents of every argument file under `/var/snap/microk8s/current/args/`, the dqlite cluster membership state, recent log excerpts from each snap service, containerd configuration, and the current state of all enabled add-ons. It is a point-in-time snapshot that captures the cluster's configuration without requiring you to manually collect a dozen different files. For privacy, it redacts IP addresses and tokens — you can share it publicly without exposing your cluster's internal addresses.

### Common Issues

```bash
# Check MicroK8s status
microk8s status

# Inspect logs
microk8s inspect

# Check kubelet logs
journalctl -u snap.microk8s.daemon-kubelet

# Check API server logs
journalctl -u snap.microk8s.daemon-apiserver

# Reset everything (destructive!)
microk8s reset

# Start fresh
microk8s stop
microk8s start
```

### Network Issues

Network problems in MicroK8s almost always trace to one of three causes: the CNI pods are not running, DNS resolution is failing, or the kube-proxy rules are stale. Verify the CNI pods first — `microk8s kubectl get pods -n kube-system -l k8s-app=calico-node` should show all nodes with running Calico pods. If Calico is not running, pods cannot get IP addresses, and nothing else will work. Next, test DNS resolution from inside the cluster with a disposable pod. If `nslookup kubernetes` fails inside the cluster, the CoreDNS pods are not running or the kube-dns service is misconfigured. Finally, if services are not reachable but pods are running, check whether kube-proxy is applying iptables rules correctly — restarting MicroK8s forces a fresh iptables sync.

```bash
# Check CNI pods
microk8s kubectl get pods -n kube-system -l k8s-app=calico-node

# Check DNS resolution
microk8s kubectl run test --image=busybox --rm -it --restart=Never -- nslookup kubernetes

# Verify cluster DNS
microk8s kubectl get svc -n kube-system kube-dns
```

### Storage Issues

```bash
# Check storage provisioner
microk8s kubectl get pods -n kube-system -l k8s-app=hostpath-provisioner

# Check PVCs
microk8s kubectl get pvc -A

# Check PVs
microk8s kubectl get pv
```

## Illustrative Scenario: The Ubuntu-Native Platform

> **Hypothetical scenario:** This narrative illustrates the operational patterns MicroK8s enables in an Ubuntu-native environment. It is not a specific, dated public incident — if you know of a real, verifiable MicroK8s production incident worth documenting, please open an issue or PR against this module.

A software company standardized on Ubuntu across their entire stack: 200+ developers on Ubuntu workstations, CI/CD on Ubuntu runners, and production on Ubuntu servers spanning both bare metal and cloud. Their existing tooling was built around the snap ecosystem. The challenge was that developers needed local Kubernetes for daily work, CI/CD needed ephemeral Kubernetes clusters for integration tests, and production needed highly available Kubernetes — all three environments had to behave identically, or configuration drift would cause "works on my machine" failures that eroded trust in the deployment pipeline.

MicroK8s won because it delivered the same installation command, the same add-on invocation, and the same operational behavior across every environment. A developer's laptop, a GitHub Actions runner, and a production server all ran `sudo snap install microk8s --classic` followed by the same add-on sequence. The add-on advantage showed when the team defined a standard environment configuration: developers enabled `dns storage registry ingress observability` for local debugging, CI enabled `dns storage` for lightweight test clusters, and production enabled `dns storage metallb cert-manager prometheus` for secure, monitored workloads. Each environment added only what it needed, but the core `microk8s enable` commands were identical.

For GitOps integration, the team enabled ArgoCD on every cluster and pointed it at the same Git repository. The Application custom resources were identical across environments — only the target cluster URL differed. This meant a PR merged to the main branch propagated through development, CI staging, and production with no per-environment modifications to the deployment manifests. The results were dramatic: developer onboarding dropped from two hours to fifteen minutes, "works on my machine" incidents fell by roughly 90%, CI pipeline times improved through snap caching, and production configuration drift — the silent killer of operational confidence — approached zero. When your entire stack runs on Ubuntu and you value operational consistency across environments, the snap-based deployment model eliminates the configuration drift that accumulates when each environment installs Kubernetes through a different mechanism.

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Not enabling dns | Services can't resolve names | Always `microk8s enable dns` first |
| Forgetting storage | PVCs stay pending | Enable storage add-on early |
| Using sudo with kubectl | Permission issues | Add user to microk8s group |
| Holding updates too long | Security vulnerabilities | Track stable channel, update regularly |
| Not waiting for ready | Commands fail randomly | Use `microk8s status --wait-ready` |
| Ignoring inspect output | Missed configuration issues | Run `microk8s inspect` when debugging |
| Wrong channel for production | Unstable features | Use stable channel, not edge |
| No resource limits | Workloads starve microk8s | Set limits on applications |

## Quiz

Test your understanding of MicroK8s:

<details>
<summary>1. What makes MicroK8s unique compared to k3s and k0s?</summary>

**Answer**: MicroK8s is delivered via snap packages with an integrated add-on system. Unlike k3s (single binary) or k0s (zero deps), MicroK8s uses snap's features: automatic updates, rollbacks, confined execution, and channel-based version tracking. The add-on system (`microk8s enable`) makes installing components trivial.
</details>

<details>
<summary>2. What is Dqlite and why does MicroK8s use it?</summary>

**Answer**: Dqlite is distributed SQLite with Raft consensus. MicroK8s uses it instead of etcd for HA clustering. Benefits: simpler than etcd, lower resource usage, SQLite semantics (familiar), automatic leader election. Trade-off: less battle-tested than etcd at extreme scale.
</details>

<details>
<summary>3. How do you enable a LoadBalancer service on bare metal with MicroK8s?</summary>

**Answer**: Use the MetalLB add-on: `microk8s enable metallb:IP_RANGE`. For example, `microk8s enable metallb:192.168.1.200-192.168.1.250`. MetalLB provides Layer 2 or BGP-based load balancing for Services of type LoadBalancer.
</details>

<details>
<summary>4. How do you join additional nodes to a MicroK8s cluster?</summary>

**Answer**: On the primary node, run `microk8s add-node` to generate a join command. On the new node, install MicroK8s and run the provided `microk8s join <primary-ip>:<port>/<token>` command. The cluster uses Dqlite for consensus, requiring odd numbers of nodes for HA.
</details>

<details>
<summary>5. How do you perform an air-gapped installation of MicroK8s?</summary>

**Answer**: On a connected machine: `snap download microk8s --channel=1.34/stable`. Transfer the .snap and .assert files to the air-gapped machine. Install: `sudo snap ack microk8s_NNNN.assert` then `sudo snap install microk8s_NNNN.snap --classic`. Import container images with `microk8s ctr image import`.
</details>

<details>
<summary>6. How do you customize the Kubernetes API server in MicroK8s?</summary>

**Answer**: Edit `/var/snap/microk8s/current/args/kube-apiserver` to add or modify arguments. Then restart MicroK8s with `microk8s stop && microk8s start`. Similar files exist for kubelet, scheduler, and other components in the same directory.
</details>

<details>
<summary>7. What's the difference between stable and edge channels?</summary>

**Answer**: Stable channels (e.g., `1.34/stable`) receive tested releases suitable for production. Edge channels receive latest builds, possibly unstable. Candidate and beta are between. For production, always use stable. For testing new features, use edge with caution.
</details>

<details>
<summary>8. How do you access the local registry add-on?</summary>

**Answer**: Enable with `microk8s enable registry`. It runs on `localhost:32000`. Push images: `docker tag myapp localhost:32000/myapp:v1 && docker push localhost:32000/myapp:v1`. In pod specs, reference as `localhost:32000/myapp:v1` (from within the cluster, use `registry.container-registry.svc.cluster.local:5000`).
</details>

## Hands-On Exercise: Full-Stack MicroK8s Deployment

This exercise takes you from an empty Ubuntu machine to a functioning development platform with monitoring, ingress, and a sample application. By the end, you will have executed the complete MicroK8s workflow — install, add-on enablement, application deployment, and observability access — and you will understand what each step provisions and why the ordering matters. DNS must be enabled before any service discovery works. Storage must be enabled before the registry or any PVC-dependent workload. The ingress controller must be running before your Ingress resources do anything. Follow the steps in order; each builds on the previous.

### Objective
Deploy a complete development environment with MicroK8s including monitoring, ingress, and a sample application.

### Step 1: Install MicroK8s

```bash
# Install MicroK8s
sudo snap install microk8s --classic

# Configure user access
sudo usermod -a -G microk8s $USER
sudo chown -R $USER ~/.kube
newgrp microk8s

# Wait for ready
microk8s status --wait-ready
```

### Step 2: Enable Essential Add-ons

The order here matters. DNS must be running before anything that uses service discovery — which is almost everything. CoreDNS registers itself as the cluster DNS service, and until it is running and its service endpoint is populated, pods cannot resolve service names. Storage must be running before the registry or any application that creates PersistentVolumeClaims, because the hostpath provisioner is what turns a PVC into an actual directory on the node's filesystem. The ingress controller needs to be running and its admission webhook registered before you create Ingress resources — otherwise those resources are accepted by the API server but never acted upon. Metrics-server must be running before `kubectl top` returns data, because `kubectl top` queries the metrics API aggregated by the metrics-server rather than scraping kubelet metrics endpoints directly. Enable them in this sequence and wait for each to reach readiness before moving on.

```bash
# Enable core add-ons
microk8s enable dns
microk8s enable storage
microk8s enable ingress
microk8s enable metrics-server

# Wait for all pods
microk8s kubectl wait --for=condition=ready pod -n kube-system -l k8s-app=kube-dns --timeout=60s
```

### Step 3: Enable Observability Stack

The observability stack deploys Prometheus for metrics, Loki for logs, Grafana for dashboards, and Tempo for traces. This is resource-intensive — expect 2-4 GB of RAM consumed at steady state — so plan your node size accordingly. If you are on a machine with less than 8 GB of RAM, use the lighter `prometheus` add-on instead. The `--timeout=120s` on the wait command accounts for the large container images and startup time.

```bash
# Enable full observability (Prometheus + Grafana + Loki + Tempo)
microk8s enable observability

# Wait for stack to be ready
microk8s kubectl wait --for=condition=ready pod -n observability -l app.kubernetes.io/name=grafana --timeout=120s

# Check status
microk8s kubectl get pods -n observability
```

### Step 4: Enable Local Registry

```bash
# Enable registry
microk8s enable registry

# Check registry is running
microk8s kubectl get pods -n container-registry
```

### Step 5: Deploy Sample Application

This step deploys a complete application — Deployment, Service, and Ingress — into a dedicated namespace. The Deployment creates three nginx replicas with resource requests and limits, which is important for production behavior: without limits, a single runaway pod can consume all node resources. The Ingress configures nginx to route traffic from `web-app.local` to the Service. The `/etc/hosts` entry maps the hostname to localhost so you can test with curl.

```bash
# Create namespace
microk8s kubectl create namespace demo

# Create deployment
cat <<EOF | microk8s kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  namespace: demo
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
      - name: nginx
        image: nginx:alpine
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
---
apiVersion: v1
kind: Service
metadata:
  name: web-app
  namespace: demo
spec:
  selector:
    app: web-app
  ports:
  - port: 80
    targetPort: 80
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-app
  namespace: demo
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: web-app.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-app
            port:
              number: 80
EOF

# Add host entry
echo "127.0.0.1 web-app.local" | sudo tee -a /etc/hosts

# Test application
curl http://web-app.local
```

### Step 6: Access Observability

Grafana is deployed with a default admin password stored in a Kubernetes Secret. The `jsonpath` extraction below retrieves it. Port-forwarding is the simplest way to access Grafana from your workstation — in production, you would expose it through the ingress controller with TLS. The pre-loaded dashboards under "Kubernetes / Compute Resources / Namespace" and "Kubernetes / Networking / Namespace" give you immediate visibility into your workload.

```bash
# Port-forward Grafana
microk8s kubectl port-forward -n observability svc/kube-prom-stack-grafana 3000:80 &

# Get Grafana password
microk8s kubectl get secret -n observability kube-prom-stack-grafana -o jsonpath='{.data.admin-password}' | base64 -d; echo

# Open http://localhost:3000
# Username: admin
# Password: (from above command)

# Explore dashboards:
# - Kubernetes / Compute Resources / Namespace
# - Kubernetes / Networking / Namespace
```

### Step 7: Test Metrics

The metrics-server add-on you enabled in Step 2 collects resource usage from kubelet's built-in metrics endpoint. The `kubectl top` commands query the metrics-server's API, not the kubelet directly, so this also verifies that the metrics-server is running and scraping data successfully. Scaling the deployment to 5 replicas and rechecking the top output demonstrates that the metrics pipeline updates correctly as pods come and go.

```bash
# Check node resources
microk8s kubectl top nodes

# Check pod resources
microk8s kubectl top pods -n demo

# Scale and observe
microk8s kubectl scale deployment web-app -n demo --replicas=5
microk8s kubectl top pods -n demo
```

### Step 8: Multi-Node Setup (Optional)

If you have additional machines available, adding nodes demonstrates the full clustering workflow in about five minutes:

```bash
# On primary
microk8s add-node
# Copy the join command

# On secondary
sudo snap install microk8s --classic
microk8s join 192.168.x.x:25000/token...

# Verify
microk8s kubectl get nodes
```

If you do not have additional machines, skip this step — the single-node cluster you have deployed is fully functional for the remaining exercises. The add-node workflow is covered in detail in the Multi-Node Clustering section earlier in this module.

### Success Criteria

- [ ] MicroK8s installed and running
- [ ] DNS, storage, ingress add-ons enabled
- [ ] Observability stack deployed
- [ ] Local registry available
- [ ] Sample application accessible via ingress
- [ ] Grafana dashboards showing metrics
- [ ] `kubectl top` returning data

### Cleanup

```bash
# Stop port-forwards
pkill -f "port-forward"

# Delete demo namespace
microk8s kubectl delete namespace demo

# Disable add-ons
microk8s disable observability
microk8s disable registry
microk8s disable ingress
microk8s disable metrics-server

# Or reset entirely
microk8s reset

# Uninstall
sudo snap remove microk8s
```

## Key Takeaways

1. **Snap-based delivery**: Automatic updates, rollbacks, version channels
2. **Add-on ecosystem**: 30+ add-ons for common functionality
3. **`microk8s enable` is powerful**: Complex stacks in one command
4. **Dqlite for clustering**: Simpler HA than etcd
5. **Ubuntu-native integration**: Best experience on Ubuntu
6. **Channel-based versions**: Stable for production, edge for testing
7. **Built-in registry**: Easy local image storage
8. **Observability stack**: Full monitoring with one command
9. **Group permissions**: Add user to microk8s group, avoid sudo
10. **Inspect for debugging**: `microk8s inspect` is comprehensive

## Toolkit Summary

You have completed the Kubernetes Distributions Toolkit. Across four modules, you have learned how k3s, k0s, MicroK8s, and the kubeadm baseline differ in their approach to packaging Kubernetes — differences that shape your operational experience from installation through upgrades to troubleshooting. The table below distills the decision into its essential tradeoffs:

| Distribution | Best For | Key Feature |
|--------------|----------|-------------|
| **k3s** | Edge, IoT, resource-constrained | Smallest footprint (~60MB) |
| **k0s** | Multi-platform, zero-dependency | Self-contained binary with runtime |
| **MicroK8s** | Ubuntu ecosystem, developers | Add-on system, snap delivery |

**Choose based on your constraints:**
- Need smallest footprint? → k3s
- Need zero host dependencies? → k0s
- Using Ubuntu and want batteries-included? → MicroK8s
- Need vanilla Kubernetes at scale? → kubeadm

## Next Module

Continue to [Module 14.4: Talos](../module-14.4-talos/) — an API-driven, immutable Kubernetes OS that eliminates SSH and the shell entirely.

## Sources

- [microk8s.io: docs](https://microk8s.io/docs) — Official MicroK8s documentation covering installation, add-ons, clustering, and troubleshooting.
- [github.com: canonical/microk8s](https://github.com/canonical/microk8s) — Source repository for MicroK8s, including add-on manifests, clustering logic, and release tooling.
- [snapcraft.io: microk8s](https://snapcraft.io/microk8s) — Snap listing showing available channels, version history, and install statistics.
- [github.com: canonical/dqlite](https://github.com/canonical/dqlite) — Dqlite source repository with Raft consensus implementation and SQLite integration details.
- [dqlite.io: docs](https://dqlite.io/docs) — Dqlite documentation covering the Raft protocol binding, C API, and clustering semantics.
- [snapcraft.io: docs](https://snapcraft.io/docs) — Snapcraft documentation on snap confinement, channels, refresh schedules, and interface connections.
- [cncf.io: software conformance](https://www.cncf.io/certification/software-conformance/) — CNCF Certified Kubernetes program listing and conformance test results.
- [kubernetes.io: kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/) — Upstream kubeadm reference installation documentation for baseline comparison.
- [github.com: k3s-io/k3s](https://github.com/k3s-io/k3s) — k3s source repository for cross-distribution comparison of bundled components and architecture.
- [github.com: k0sproject/k0s](https://github.com/k0sproject/k0s) — k0s source repository for cross-distribution comparison of zero-dependency packaging.
- [discourse.ubuntu.com: microk8s](https://discourse.ubuntu.com/c/kubernetes/microk8s) — Ubuntu Discourse forum for MicroK8s announcements, troubleshooting, and community support.
- [canonical.com: blog](https://canonical.com/blog) — Canonical blog with MicroK8s release announcements, architecture deep-dives, and customer case studies.

---

*"MicroK8s makes Kubernetes feel native to Ubuntu. For Ubuntu shops, that's not a small thing—that's everything."*
