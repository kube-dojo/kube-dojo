---
revision_pending: false
title: "Module 14.2: k0s - Zero Friction Kubernetes"
slug: platform/toolkits/infrastructure-networking/k8s-distributions/module-14.2-k0s
sidebar:
  order: 3
---
> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: 40-45 minutes

## Overview

k0s, pronounced "kay-zero-ess", is a Kubernetes distribution built around one deceptively simple operating idea: make the cluster software self-contained enough that the host operating system stops being the main installation project. Instead of asking you to prepare a container runtime package, add Kubernetes apt repositories, align RPM versions, and then let kubeadm assemble the cluster, k0s ships as a single self-extracting binary that carries the Kubernetes components and manages the pieces it needs under its own data directory.

That packaging choice is the reason k0s belongs in a distribution comparison module rather than a generic installation tutorial. A Kubernetes distribution is not a different API server; a conformant distribution still exposes the Kubernetes API you already know. The difference is the operational envelope around that API: what is bundled, how the control plane is supervised, which datastore is selected by default, how workers join, which network provider is installed, how upgrades are coordinated, and how much of the host must be prepared before the first kubelet starts.

k0s was originally built by Mirantis and is now a CNCF Sandbox project while also remaining a Mirantis-supported Kubernetes distribution. That combination matters because it separates two claims that learners often blur together. CNCF project maturity tells you where the project sits in CNCF governance, while Certified Kubernetes conformance tells you whether the Kubernetes APIs behave like upstream Kubernetes. k0s is CNCF Certified Kubernetes, so the API contract is the same Kubernetes contract; its distinctive value is the packaging and lifecycle model around that contract.

This module teaches k0s as a durable operating model rather than a product tour. We will focus on the single-binary architecture, the controller versus worker role split, Konnectivity reverse tunneling, k0sctl as the declarative bootstrap tool, and the datastore choices that decide whether a cluster is simple, highly available, or dependent on an external database. Version numbers and component versions are isolated in one dated snapshot so the learning survives normal release churn.

## Prerequisites

- Kubernetes fundamentals: pods, deployments, services, nodes, kubelet, and the Kubernetes API server.
- Linux command-line basics, including SSH, system services, and editing YAML files.
- Familiarity with kubeadm, k3s, or another Kubernetes installer is helpful but not required.
- Access to one or more Linux machines or virtual machines if you want to run the exercise.

## What You'll Be Able to Do

After completing this module, you will be able to:

- Explain why k0s uses a self-contained single-binary packaging model and how that differs from kubeadm host preparation.
- Choose between `controller`, `worker`, and `controller+worker` roles without accidentally mixing control-plane and workload risk.
- Describe how Konnectivity helps controller components reach private workers through a reverse tunnel.
- Select between Kine plus SQLite, embedded etcd, and external SQL datastores using the same HA tradeoff lens you use for other Kubernetes distributions.
- Use a `k0sctl.yaml` file to bootstrap and later update a multi-node k0s cluster from one declarative inventory.

## Why This Module Matters

k0s answers a practical platform question: what if the Kubernetes installation artifact were not a collection of host packages at all? In a kubeadm build, the host operating system is an active participant in the cluster assembly. You install a compatible container runtime, configure cgroups, add Kubernetes repositories, install kubeadm, kubelet, and kubectl packages, and then use kubeadm to lay down control-plane static pods. That model is explicit and close to upstream, but the host becomes part of the dependency graph.

k0s moves much of that dependency graph into the distribution. The host still needs a working kernel, cgroups, networking support, permissions, and an init system when you install k0s as a service, but it does not need a distribution-specific Kubernetes package repository or a preinstalled CRI runtime for the normal path. The k0s binary is statically linked and self-extracting, so the distribution can carry tested component versions together instead of asking each Linux flavor to provide them through its package manager.

Think of kubeadm as a professional kitchen that gives you a recipe and expects the ingredients, knives, pans, burners, and storage layout to be ready before cooking begins. k0s is closer to a sealed field kitchen: you still need a level surface, fuel, and people who know food safety, but the core cooking system arrives in one container. The tradeoff is not that one approach is universally better; the tradeoff is where you want explicit assembly versus packaged consistency.

This matters most when the infrastructure is not uniform. A platform team running one Ubuntu image in one cloud can standardize kubeadm prerequisites through image baking or configuration management. A team running on bare metal, edge sites, lab gear, appliance-like deployments, or several Linux families may care more about reducing the number of host-specific preparation steps. k0s is designed for that second pressure: less reliance on host packages, cleaner removal, and the same installation shape across many environments.

The other reason k0s matters is its role separation. Many lightweight distributions optimize for "make the first node useful immediately", which often means the control plane also schedules workloads unless you opt out. k0s defaults the other way: controller nodes run control-plane processes, and worker nodes run kubelet, containerd, kube-proxy unless disabled, CNI agents, and workloads. You can deliberately run a combined controller and worker for development, labs, or small edge nodes, but the distribution makes the separation a first-class concept.

That combination of self-contained packaging and explicit roles is the mental model to carry forward. k0s is not trying to teach you fewer Kubernetes fundamentals; it is trying to reduce the accidental Linux-distribution work around those fundamentals. You still need to understand certificates, API reachability, CNI behavior, datastore durability, and node lifecycle. The difference is that those decisions become clearer because they are not buried under a pile of package-manager preparation steps.

## Did You Know?

- **Single binary does not mean no kernel requirements**: k0s avoids package-manager and shared-library dependencies in the normal Linux binary path, but Kubernetes workers still need Linux kernel capabilities for containers, cgroups, namespaces, and networking.
- **Controllers are isolated by default**: a plain k0s controller does not run kubelet or containerd, so ordinary workloads are not scheduled there unless you choose a combined role.
- **Konnectivity is part of the design**: k0s uses Konnectivity so the API server can reach kubelets through a reverse tunnel, which is useful when workers live behind private networks or restrictive inbound firewalls.
- **CNCF project status and conformance are different**: k0s is a CNCF Sandbox project as of 2026-06, and k0s is also a CNCF Certified Kubernetes distribution. The first is project maturity; the second is API compatibility.

> **Landscape snapshot - as of 2026-06. This changes fast; verify against upstream docs and release notes before relying on specifics.**
>
> | Fact | k0s snapshot |
> |------|--------------|
> | Origin and stewardship | Built by Mirantis; accepted into CNCF at the Sandbox maturity level on 2025-01-19. |
> | Conformance | CNCF Certified Kubernetes distribution, meaning the Kubernetes API behavior is tested for conformance rather than forked into a separate API. |
> | Latest release observed at authoring time | GitHub lists `v1.36.1+k0s.0` as the latest k0s release, published on 2026-06-14. The curriculum examples below keep a Kubernetes 1.35-era pin unless you deliberately test the newer line. |
> | Supported Kubernetes lines shown on the project site | The project site lists Kubernetes `v1.35`, `v1.34`, and `v1.33`; verify the release page before pinning a production version. |
> | Minimum approximate hardware | Controller: 1 GB RAM and 1 vCPU. Worker: 0.5 GB RAM and 1 vCPU. Controller plus worker: 1 GB RAM and 1 vCPU. Real workloads need more. |
> | Architectures in current system requirements | `x86_64`, `aarch64`, `armv7l`, and `riscv64` with no precompiled binaries or CI coverage for the last one. |
> | Built-in CNI choices | Kube-router and Calico are bundled options; custom CNI is supported when you take responsibility for the plugin installation. |
> | Current component examples from release notes and docs | Kubernetes `v1.36.1`, containerd `v2.3.1`, CoreDNS `v1.14.2`, Calico `v3.32.0`, Kine `v0.16.2`, etcd `v3.6.12`, kube-router image `v2.10.0-iptables1.8.13-k0s.0`, and Traefik `v3.7.3` as a node-local load-balancer backend option. |

## k0s Architecture

The simplest way to read k0s architecture is to separate packaging from roles. Packaging says how the software arrives: one self-extracting binary that contains the components k0s manages. Roles say what a node actually does after the binary starts: a controller supervises the control plane and datastore pieces, a worker runs the node-level runtime and workloads, and a controller+worker does both on the same host.

That distinction prevents a common misunderstanding. "Single binary" does not mean "one process pretending to be Kubernetes." k0s still runs normal Kubernetes components such as kube-apiserver, kube-controller-manager, kube-scheduler, kubelet, kube-proxy unless disabled, containerd, CoreDNS, metrics-server, CNI agents, and datastore processes. The k0s binary acts as the packaging, supervisor, installer, and lifecycle entry point around those components.

The practical design question is therefore not whether k0s is "real Kubernetes"; conformance answers that. The practical question is whether you want a distribution that makes the host operating system less visible during installation and upgrades. That is powerful in mixed fleets, but it also means you should learn the k0s abstraction itself instead of assuming every troubleshooting step maps one-to-one to kubeadm static pods or package-managed kubelet units.

```
k0s ROLE MODEL

                           kubectl / clients
                                  |
                                  v
                    +-----------------------------+
                    | k0s controller node         |
                    |                             |
                    | kube-apiserver              |
                    | kube-controller-manager     |
                    | kube-scheduler              |
                    | datastore: etcd or Kine     |
                    | CoreDNS / metrics-server    |
                    | Konnectivity server         |
                    |                             |
                    | No workloads by default     |
                    +--------------+--------------+
                                   |
                      reverse tunnel / node APIs
                                   |
          +------------------------+------------------------+
          |                                                 |
          v                                                 v
+--------------------------+                    +--------------------------+
| k0s worker node          |                    | k0s worker node          |
|                          |                    |                          |
| kubelet                  |                    | kubelet                  |
| containerd + runc        |                    | containerd + runc        |
| kube-proxy unless off    |                    | kube-proxy unless off    |
| CNI agents               |                    | CNI agents               |
| application workloads    |                    | application workloads    |
+--------------------------+                    +--------------------------+
```

A controller-only node is attractive when the control plane is precious and scarce. It reduces accidental resource contention because a noisy application pod cannot consume CPU on the same node that is running the API server or datastore. It also makes incident response cleaner: if a worker melts down under workload pressure, you inspect workload scheduling, runtime, networking, and node health without first asking whether the controller was also hosting the failing application.

A worker-only node is the normal place for workloads. It joins the cluster with a role-specific token, starts the node-level services, establishes trust with the control plane, and runs pods just like any other Kubernetes worker. From the application author's perspective, a k0s worker is not a special Kubernetes dialect; it is a node in a conformant Kubernetes cluster with the usual kubelet and container runtime responsibilities.

A controller+worker node is the deliberate exception. It is useful for a laptop, lab VM, small appliance, or far-edge site where one machine must run the whole cluster. In k0sctl inventory this role is expressed as `controller+worker`; at the k0s command line the comparable shape is a controller with worker components enabled. You should treat this as a topology decision, not just an installation shortcut, because role changes after installation are not something to casually toggle on existing nodes.

Konnectivity is the less visible but important part of the architecture. Kubernetes controllers often need to reach kubelets for logs, exec, port-forward, metrics, and node operations. In many real networks, workers can initiate outbound traffic to the control plane, but the control plane cannot initiate inbound connections back to every worker because those workers sit behind NAT, private routing, edge firewalls, or customer networks. Konnectivity solves that by establishing a reverse tunnel from worker-side agents toward the control plane, allowing API-server-to-kubelet traffic to flow without requiring every worker to expose itself broadly.

The datastore story is the same CAP tradeoff you saw in sibling distribution modules. Kine plus SQLite is simple and local, which makes it excellent for single-node clusters and small demos because there is no quorum to design. Embedded etcd gives you a replicated control-plane datastore across controller nodes, but it introduces quorum, disk latency sensitivity, membership operations, and the need for a stable control-plane endpoint. External MySQL or PostgreSQL through Kine can work when an organization already has a managed database platform, but then Kubernetes availability depends on that external database being correctly operated.

### Cross-Distribution Rosetta

The table below compares durable capabilities rather than ranking the tools. Treat every cell as a design clue, not a verdict, because the right distribution depends on operational constraints such as air gap, host control, edge footprint, support model, and how much upstream assembly you want to own.

| Capability | k3s | k0s | MicroK8s | upstream kubeadm |
|------------|-----|-----|----------|------------------|
| Default datastore posture | SQLite for simple server setups, embedded etcd for HA, external SQL options through Kine | Kine plus SQLite for single-node, embedded etcd for HA, external SQL through Kine | dqlite for clustered MicroK8s control planes | etcd, usually as static pods or external etcd |
| HA mechanism | Multi-server with embedded etcd or external datastore | Multiple controllers with embedded etcd plus a stable API endpoint or external datastore | Multiple MicroK8s nodes with dqlite-backed HA | Multiple control-plane nodes with etcd quorum and a load balancer |
| Bundled CNI posture | Flannel by default, other options configurable | Kube-router or Calico built in, custom CNI allowed | Calico commonly used through add-ons and defaults that change by release | No CNI installed by kubeadm; you install one |
| Bundled ingress posture | Traefik is commonly bundled unless disabled | Ingress is an add-on choice rather than the core default | Ingress available through add-ons | None; install an ingress controller yourself |
| Bundled service load balancing | ServiceLB commonly bundled | No universal cloud load balancer; use provider integration, MetalLB, cloud controller, or another add-on | MetalLB available as an add-on | None; depends on cloud provider or add-on |
| Install mechanism | Install script and token join | Install script, role-specific tokens, and k0sctl inventory | Snap package and `microk8s` commands | Host packages plus `kubeadm init` and `kubeadm join` |
| Packaging model | Compact distribution binaries and managed components | Single self-extracting binary with minimal host package dependencies | Snap-based packaging | OS packages plus images and static pod manifests |
| Primary fit | Lightweight clusters, edge, and embedded-style deployments | Dependency-minimized clusters, mixed Linux fleets, edge, appliance, and controlled bare metal | Developer machines, labs, edge, and Ubuntu-centered operations | Upstream-aligned custom builds where you own every component choice |
| Conformance | Certified Kubernetes releases | Certified Kubernetes releases | Certified Kubernetes releases | Upstream Kubernetes baseline when assembled correctly |

## Installing k0s

The first installation choice is not "single node or multi-node"; it is "do I want this node to be expandable later?" The `--single` flag creates a convenient one-node cluster that includes controller and worker behavior, but upstream docs warn that it disables features needed for multi-node clusters. For a disposable demo, that is fine. For a lab you may expand next week, install a controller with worker components enabled instead of using `--single`.

### Single Node for Learning

This command sequence downloads the k0s binary, installs a single-node service, starts it, and uses the embedded `kubectl` to inspect the cluster. The important teaching point is that you are not preinstalling containerd or Kubernetes packages. You are still trusting a remote install script here, so production or air-gapped environments should download and verify release artifacts through your normal supply-chain process.

```bash
# Download the k0s binary through the upstream install script.
curl --proto '=https' --tlsv1.2 -sSf https://get.k0s.sh | sudo sh

# Inspect the installed version.
k0s version

# Disposable single-node cluster: controller and worker behavior on one host.
sudo k0s install controller --single --start

# Inspect the process role and workload setting.
sudo k0s status

# Use the kubectl embedded by k0s to inspect the node and system pods.
sudo k0s kubectl get nodes -o wide
sudo k0s kubectl get pods -A
```

The output should show one ready node after the control plane and worker components settle. If `k0s status` says the role is `controller` and workloads are enabled, remember that the role display and workload capability are related but not identical. A controller with worker components enabled is still a controller process, but it also runs the node-level pieces needed to host pods.

For a one-node cluster that you may later expand, use the controller-with-worker path instead. This keeps the node useful for workloads but avoids the special single-node mode that blocks later multi-node growth. The `--no-taints` choice makes regular workloads schedulable on the combined node; without it, Kubernetes taints may correctly keep ordinary application pods away from a control-plane node.

```bash
sudo k0s reset
sudo k0s install controller --enable-worker --no-taints --start
sudo k0s status
sudo k0s kubectl get nodes -o wide
```

That reset is intentionally destructive, which is why you should use it only on a learning machine or after you have backed up state. k0s reset is useful because it removes the service registration and k0s-managed data, but it is still a cluster teardown operation. Production removal should start with backups, workload migration, and an explicit decision about whether application persistent volumes are in scope.

### Multi-Node Manual Join

Manual join is the clearest way to understand the trust model. A controller starts first, then it creates role-specific join tokens. A worker token lets a host join as a worker, while a controller token lets another host join the control plane. These tokens are not just arbitrary shared secrets; they carry bootstrap trust information so the joining node can validate the cluster and present itself correctly.

```bash
# On the first controller.
curl --proto '=https' --tlsv1.2 -sSf https://get.k0s.sh | sudo sh
sudo k0s install controller --start
sudo k0s status

# Create an expiring worker token and copy it securely to each worker.
sudo k0s token create --role=worker --expiry=4h > worker.token
```

On each worker, the token connects the node to the controller and selects the worker role. In a real environment you would distribute the token through a secure channel, keep the expiry short, and avoid pasting it into shell history. For repeated multi-node work, k0sctl is preferable because it handles token creation and node sequencing from a single inventory.

```bash
# On each worker after copying worker.token to /tmp/worker.token.
curl --proto '=https' --tlsv1.2 -sSf https://get.k0s.sh | sudo sh
sudo k0s install worker --token-file /tmp/worker.token --start
sudo k0s status
```

Back on the controller, `kubectl get nodes` should show the joined workers. If the workers remain `NotReady`, troubleshoot in this order: host firewall, CNI pods, container runtime status, node clock skew, token expiry, and whether the worker can reach the controller address advertised in its bootstrap configuration. k0s removes many host package prerequisites, but it cannot remove the need for correct routing and time.

### Multi-Node Cluster with k0sctl

k0sctl is the normal tool once you have more than a toy topology. Its value is not that it hides Kubernetes; its value is that it turns node inventory, SSH connection details, roles, k0s version, and cluster configuration into one reviewable file. That file becomes the cluster bootstrap contract, closer to an infrastructure plan than a sequence of remembered shell commands.

The example below uses three hosts: one controller and two workers. It pins a curriculum-era k0s version for repeatability, selects Kube-router explicitly, and sets an API external address that clients and workers can use consistently. If you are building this for real, replace the addresses, SSH user, key path, and version after checking the current k0s release page.

```yaml
apiVersion: k0sctl.k0sproject.io/v1beta1
kind: Cluster
metadata:
  name: dojo-k0s
spec:
  hosts:
    - role: controller
      ssh:
        address: 10.10.0.10
        user: ubuntu
        keyPath: ~/.ssh/id_ed25519
    - role: worker
      ssh:
        address: 10.10.0.11
        user: ubuntu
        keyPath: ~/.ssh/id_ed25519
    - role: worker
      ssh:
        address: 10.10.0.12
        user: ubuntu
        keyPath: ~/.ssh/id_ed25519
  k0s:
    version: v1.35.4+k0s.0
    config:
      apiVersion: k0s.k0sproject.io/v1beta1
      kind: ClusterConfig
      metadata:
        name: dojo-k0s
      spec:
        api:
          externalAddress: 10.10.0.10
        network:
          provider: kuberouter
```

Applying the file is a reconciliation operation from your workstation. k0sctl connects to each host, inspects what is already there, downloads or uploads the k0s binary depending on configuration, creates tokens, joins nodes, and leaves you with a kubeconfig you can save locally. This is the main contrast with a k3s token-join workflow or a kubeadm join command: the join details exist inside one desired-state inventory instead of being scattered across terminals.

```bash
# Install k0sctl from the upstream release page for your OS and architecture.
k0sctl version

# Deploy or reconcile the cluster described by the inventory.
k0sctl apply --config k0sctl.yaml

# Fetch kubeconfig for normal kubectl use.
k0sctl kubeconfig --config k0sctl.yaml > kubeconfig
chmod 600 kubeconfig
KUBECONFIG=$PWD/kubeconfig kubectl get nodes -o wide
```

Read the apply output like you would read Terraform or Ansible output. A successful run should show connection, host detection, validation, configuration, installation, and join phases. A failed run is often more useful than a silent manual failure because it tells you which host failed and at which phase. The fix is usually an SSH permission issue, sudo privilege issue, firewall problem, wrong role on an already-installed node, or a version/configuration mismatch.

### High Availability Setup

High availability is not created by adding random controllers; it is created by combining a replicated datastore, multiple controllers, and a stable API endpoint. k0s can run embedded etcd on controller nodes, and k0sctl can generate and distribute shared certificates during bootstrap. You still need clients and workers to reach a stable control-plane address, either through an external TCP load balancer or through k0s control-plane load-balancing features that fit your network.

```yaml
apiVersion: k0sctl.k0sproject.io/v1beta1
kind: Cluster
metadata:
  name: dojo-k0s-ha
spec:
  hosts:
    - role: controller
      ssh:
        address: 10.20.0.10
        user: ubuntu
        keyPath: ~/.ssh/id_ed25519
    - role: controller
      ssh:
        address: 10.20.0.11
        user: ubuntu
        keyPath: ~/.ssh/id_ed25519
    - role: controller
      ssh:
        address: 10.20.0.12
        user: ubuntu
        keyPath: ~/.ssh/id_ed25519
    - role: worker
      ssh:
        address: 10.20.0.21
        user: ubuntu
        keyPath: ~/.ssh/id_ed25519
  k0s:
    version: v1.35.4+k0s.0
    config:
      apiVersion: k0s.k0sproject.io/v1beta1
      kind: ClusterConfig
      metadata:
        name: dojo-k0s-ha
      spec:
        api:
          externalAddress: api.k0s.example.test
          sans:
            - api.k0s.example.test
            - 10.20.0.10
            - 10.20.0.11
            - 10.20.0.12
        storage:
          type: etcd
        network:
          provider: calico
```

The storage line is the key change. In a single-node cluster, local SQLite through Kine is convenient because there is only one writer and no quorum design. In an HA control plane, embedded etcd is the normal in-cluster choice because each controller participates in replicated state. That gives you failure tolerance, but it also means disk latency, quorum math, odd member counts, and member replacement procedures become part of your operational runbook.

## k0s Configuration

k0s configuration lives in a `ClusterConfig` object, commonly written to `/etc/k0s/k0s.yaml` for local installation or nested under `spec.k0s.config` in a k0sctl inventory. This is another important difference from ad hoc installation commands: the durable cluster decisions should live in YAML that can be reviewed, diffed, and repeated, while transient bootstrap secrets should have short lifetimes.

### Configuration File Structure

The example below is intentionally partial. k0s supports partial configuration and fills defaults for omitted values, which keeps the file focused on decisions you actually own. A noisy full-default file can feel comforting, but it also creates a future maintenance burden because every default looks like a local policy. Keep the file explicit where you are making a platform decision and sparse where upstream defaults are acceptable.

```yaml
apiVersion: k0s.k0sproject.io/v1beta1
kind: ClusterConfig
metadata:
  name: dojo-k0s
spec:
  api:
    port: 6443
    k0sApiPort: 9443
    externalAddress: api.k0s.example.test
    sans:
      - api.k0s.example.test
      - 10.20.0.10

  storage:
    type: etcd

  network:
    provider: kuberouter
    podCIDR: 10.244.0.0/16
    serviceCIDR: 10.96.0.0/12
    clusterDomain: cluster.local
    kubeProxy:
      disabled: false
      mode: iptables

  telemetry:
    enabled: false
```

The `externalAddress` and `sans` fields deserve special attention. Kubernetes client certificates and worker bootstrap configuration need a stable API identity. If you install controllers behind a future load balancer but forget to include the load balancer DNS name or address in the certificate subject alternative names, the cluster may come up but later fail in ways that look like networking problems and are actually certificate identity problems.

The `telemetry` setting is included because platform teams should treat outbound telemetry as a policy decision. Some organizations allow anonymized usage telemetry from infrastructure tools; others disable it by default in regulated or air-gapped environments. The important practice is not the specific value in this example, but the fact that you record the decision rather than letting it hide in an unreviewed default.

### Network Provider Options

k0s bundles Kube-router and Calico as built-in CNI choices, and it can also run with a custom CNI. Choosing the CNI during cluster creation is a foundational decision because it shapes pod routing, network policy behavior, node firewall needs, service implementation details, and day-two troubleshooting. Treat it like choosing a filesystem or datastore, not like choosing a cosmetic add-on.

```yaml
spec:
  network:
    provider: kuberouter
    kuberouter:
      autoMTU: true
      hairpin: Enabled
      metricsPort: 8080
```

Kube-router fits k0s's minimal-core posture because it can provide pod networking with a relatively direct Linux networking model. It is also attractive in environments where BGP routing matters, though BGP design requires network engineering discipline and should not be enabled casually. The practical lesson is that "default CNI" does not mean "ignore networking"; it means "start from the distribution's tested path, then change only when your requirements justify it."

```yaml
spec:
  network:
    provider: calico
    calico:
      mode: vxlan
      overlay: Always
```

Calico is the familiar choice for teams that want its network policy ecosystem and operational model. In k0s, selecting Calico at install time lets the distribution manage the built-in Calico deployment path. If you need a custom Calico mode, dual-stack nuance, or advanced enterprise features, verify the current k0s networking docs and Calico docs together because both sides of the integration matter.

```yaml
spec:
  network:
    provider: custom
```

Custom CNI is the escape hatch for Cilium, Flannel, or another plugin. The word "custom" should make you slow down, because k0s will not magically install the plugin, place every host binary, or validate every plugin-specific kernel and firewall requirement for you. Custom CNI gives you control, but it also hands ownership of installation order and troubleshooting back to your platform team.

### Storage Configuration

Storage configuration is where k0s stops being a packaging discussion and becomes a reliability discussion. The Kubernetes API server needs a durable datastore. If that datastore is local SQLite, the blast radius is simple and the cluster is not HA. If that datastore is embedded etcd, the cluster can survive controller loss when quorum remains. If that datastore is external SQL, the cluster depends on the database team's HA story.

```yaml
spec:
  storage:
    type: kine
    kine:
      dataSource: sqlite:///var/lib/k0s/db/state.db
```

Kine plus SQLite is a good teaching and single-node choice because it removes the mental overhead of etcd membership. It is also a poor multi-controller HA choice because a local file database is not a replicated consensus system. When a module says "SQLite for single node", it is not insulting SQLite; it is placing SQLite in the topology where its simplicity is an advantage rather than a hidden availability limit.

```yaml
spec:
  storage:
    type: etcd
    etcd:
      peerAddress: 10.20.0.10
```

Embedded etcd is the normal HA path because k0s can manage etcd lifecycle on the controller nodes. You still need to design for quorum, disk quality, backups, and controller replacement. A three-controller etcd cluster can tolerate one controller failure; it cannot tolerate careless simultaneous maintenance of two members. HA is not a checkbox, it is a promise that your procedures must keep.

```yaml
spec:
  storage:
    type: kine
    kine:
      dataSource: postgres://k0s:REPLACE_ME@postgres.example.test:5432/k0s?sslmode=require
```

External SQL through Kine is useful when your organization already has a managed database platform with backups, monitoring, encryption, and failover. The benefit is that Kubernetes controllers do not have to operate their own datastore quorum. The cost is dependency inversion: if the external database is unavailable or misconfigured, your Kubernetes API is unavailable even if every controller host is healthy.

## Helm Integration

k0s includes Helm integration so cluster add-ons can be declared during bootstrap or through chart custom resources. This is useful for base components such as metrics, certificate management, ingress, storage helpers, or platform agents, but it should not become a dumping ground for every application team. The platform layer should install shared cluster services; application delivery should still have its own GitOps or release workflow.

```yaml
apiVersion: helm.k0sproject.io/v1beta1
kind: Chart
metadata:
  name: metrics-server
  namespace: kube-system
spec:
  chartName: metrics-server/metrics-server
  namespace: kube-system
  version: "3.13.0"
  values: |
    args:
      - --kubelet-preferred-address-types=InternalIP,Hostname
```

The chart custom resource approach is more GitOps-friendly than stuffing every chart into the original installer configuration, because each chart can be applied, reviewed, and reconciled as a Kubernetes resource. That also reduces unnecessary k0s restarts for add-on changes. The operational boundary is simple: use k0s to bootstrap the cluster substrate, then manage ongoing platform add-ons through resources that your normal Kubernetes tooling can inspect.

If you prefer to define bootstrap charts inside `k0s.yaml`, keep the list short and boring. A cluster that cannot start without its network plugin, DNS, metrics, and maybe certificate plumbing is normal. A cluster that tries to install the entire internal developer platform during control-plane bootstrap is harder to debug because the line between "Kubernetes is up" and "the platform app stack is healthy" disappears.

## Cluster API Integration

k0s can participate in Cluster API workflows through k0smotron and related providers. The durable concept here is not the exact CRD shape, because provider APIs evolve. The durable concept is that Cluster API turns clusters themselves into Kubernetes-managed resources: a management cluster reconciles workload clusters, while bootstrap and control-plane providers know how to create the specific distribution.

```bash
# Example only: provider names and versions change, so verify current docs.
clusterctl init \
  --infrastructure docker \
  --bootstrap k0sproject-k0smotron \
  --control-plane k0sproject-k0smotron
```

Use Cluster API when cluster lifecycle is itself a product you operate. If you create one or two clusters by hand, k0sctl is easier to understand and easier to debug. If you operate many workload clusters across teams, environments, or tenants, Cluster API gives you a reconciliation model, ownership boundaries, and integration points for fleet automation. k0sctl and Cluster API are not rivals; they sit at different layers of the lifecycle problem.

The review habit is to ask which actor owns drift correction. With manual commands, humans own drift correction. With k0sctl, the inventory file and k0sctl apply workflow own a large part of cluster drift. With Cluster API, controllers in a management cluster continuously reconcile desired state. More automation is powerful only when you are ready to operate the automation layer itself.

## Day-2 Operations

Day-two operations are where k0s's packaging simplicity stops being enough. A cluster that installs cleanly can still fail if you do not have backups, upgrade sequencing, certificate practices, datastore maintenance, network observability, and reset procedures. k0s gives you useful primitives, but you still need a runbook that states who runs them, when they are tested, and what evidence proves recovery works.

### Backup and Restore

k0s backup covers the k0s-managed control-plane state: certificates, datastore snapshots for etcd or Kine plus SQLite, k0s configuration, manifests under the k0s data directory, image bundles, and Helm configuration. It does not back up arbitrary application persistent volumes, and it does not magically protect an external database you selected through Kine. The backup scope is control-plane recovery, not whole-platform disaster recovery.

```bash
# On a controller node.
sudo mkdir -p /var/backups/k0s
sudo k0s backup --save-path /var/backups/k0s

# With k0sctl from the workstation that can reach the cluster hosts.
k0sctl backup --config k0sctl.yaml
```

The restore path should be tested before you need it. A backup file that has never been restored is only a hopeful artifact. For HA clusters, pay attention to the control-plane external address because worker components are configured to connect to it. If a restore changes that address unexpectedly, the restored control plane may be healthy while workers continue dialing the old endpoint.

### Upgrading k0s

The safest upgrade story is declarative: update the k0s version in `k0sctl.yaml`, review the release notes, check Kubernetes version skew, take a backup, and let k0sctl coordinate the node sequence. This gives you a change record and a repeatable workflow. A manual binary replacement can be appropriate for single-node labs, but it is less attractive for a fleet because it leaves sequencing and rollback evidence in human memory.

```bash
# Review the intended version in k0sctl.yaml first, then reconcile.
k0sctl apply --config k0sctl.yaml

# Confirm the Kubernetes and runtime view after the upgrade.
KUBECONFIG=$PWD/kubeconfig kubectl get nodes -o wide
```

Do not upgrade just because a version exists. Ask whether your current Kubernetes minor line is still supported, whether the new line changes containerd behavior, whether your CNI supports the target version, whether any deprecated API removals affect installed add-ons, and whether you have a tested restore point. Lightweight packaging shortens installation toil; it does not remove release engineering discipline.

### Reset and Cleanup

Reset is useful when you are rebuilding a lab, replacing a node, or cleaning a failed installation. It is also destructive. k0s reset stops and removes k0s-managed state, unregisters the service, and makes a best-effort attempt to clean network configuration. Custom CNI cleanup may still require plugin-specific work, and a reboot is often the cleanest way to remove leftover kernel networking state.

```bash
# Local destructive cleanup on a node.
sudo k0s stop
sudo k0s reset

# Remote destructive cleanup through k0sctl.
k0sctl reset --config k0sctl.yaml
```

The operational habit is to decide whether you are resetting a node or retiring part of a cluster. Resetting a worker without draining application pods can cause avoidable workload disruption. Resetting a controller without understanding datastore membership can reduce or break quorum. A clean uninstall command is not a substitute for a clean removal procedure.

## Monitoring and Troubleshooting

k0s troubleshooting starts with the same layered model as any Kubernetes cluster: host, k0s service, control-plane components, datastore, node runtime, CNI, DNS, then workloads. The distribution-specific commands help you locate the layer quickly, but you should still avoid jumping straight to application YAML when the kubelet cannot register or the CNI pods are crash-looping.

```bash
# On a node, inspect the k0s service and role.
sudo k0s status

# Inspect the API health from a controller.
sudo k0s kubectl get --raw /readyz?verbose

# Systemd logs use different service names by role.
sudo journalctl -u k0scontroller --no-pager -n 100
sudo journalctl -u k0sworker --no-pager -n 100

# Cluster-level view.
sudo k0s kubectl get nodes -o wide
sudo k0s kubectl get pods -A -o wide
```

If controller logs look healthy but workers are missing, check the worker's route to the controller address and the relevant ports before changing Kubernetes objects. If nodes register but pods cannot communicate, inspect the CNI pods, host firewall backend, MTU, and whether the chosen CNI matches the configuration used at cluster creation. Networking bugs often masquerade as DNS or application readiness failures because DNS is the first cross-pod call many workloads make.

```bash
# CNI-focused checks for the default Kube-router path.
sudo k0s kubectl -n kube-system get pods -l k8s-app=kube-router -o wide
sudo k0s kubectl -n kube-system logs -l k8s-app=kube-router --tail=80

# Lightweight in-cluster network test.
sudo k0s kubectl run netcheck \
  --image=busybox:1.36 \
  --restart=Never \
  --rm -it -- wget -qO- https://kubernetes.default.svc
```

That `wget` test is intentionally boring. It checks whether a pod can start, resolve the Kubernetes service name, and reach the API service through cluster networking. If it fails, the error text points your next step: image pull means registry or runtime, DNS lookup means CoreDNS or service discovery, connection refused means service or API path, timeout means CNI, routing, firewall, or proxy.

For HA clusters, add datastore checks to the normal triage sequence. A Kubernetes API server can be running while etcd is unhealthy, slow, or missing quorum. In k0s, the etcd lifecycle is managed for embedded etcd clusters, but you still need to watch disk latency, member health, and backup currency. When control-plane symptoms look random, always ask whether the datastore is actually healthy.

```bash
# On a controller in an embedded etcd cluster.
sudo k0s etcd member-list

# Confirm the API endpoint identity clients are using.
KUBECONFIG=$PWD/kubeconfig kubectl cluster-info
```

## Hypothetical scenario: Clean Slate Infrastructure

Hypothetical scenario: A fintech platform team inherits three small Kubernetes footprints: a cloud lab, an on-prem integration environment, and several edge boxes in partner sites. Each site was built by a different team, and every rebuild starts with a half-day argument about host packages. One image has an old containerd package, another blocks an apt repository, a third uses a firewall backend nobody documented, and the edge boxes are intentionally stripped down for security review.

The team first tries to standardize the kubeadm path. That is a reasonable instinct because kubeadm is close to upstream and familiar to many operators. The problem is not kubeadm itself; the problem is the unmanaged spread of host prerequisites. The team can make kubeadm work, but the real project becomes standardizing golden images, package repositories, runtime configuration, firewall behavior, and join documentation across environments that were never meant to look identical.

The k0s pilot reframes the problem. Instead of asking every environment to become the same Linux platform first, the team asks whether each host can satisfy the kernel and networking requirements and run the same k0s binary. Controllers are kept controller-only in the shared environments, small edge nodes use controller+worker where there is no spare hardware, and k0sctl inventories describe each site in Git. The team still has to solve routing, DNS, certificates, and backups, but the number of host-package variables drops sharply.

The lesson is not "always choose k0s." The lesson is that packaging is an architectural choice. If your main source of failure is inconsistent host preparation, a self-contained distribution can reduce drift. If your main requirement is maximum upstream assembly control, kubeadm may be the better fit. Good platform engineers choose the tool whose failure modes match the team's operating capacity.

## Common Mistakes

| Mistake | Problem | Better Approach |
|---------|---------|-----------------|
| Treating `--single` as a future-proof production shortcut | Single-node mode is convenient but intentionally not the path for later multi-node expansion | Use controller-only plus workers for production, or `--enable-worker --no-taints` for expandable single-host labs |
| Assuming "zero dependencies" means no host requirements | Kubernetes workers still need kernel, cgroup, namespace, networking, firewall, and privilege support | Run `k0s sysinfo`, read external runtime dependencies, and validate host images before rollout |
| Running workloads on controllers accidentally | Control-plane CPU, memory, and disk contention can turn an application incident into an API outage | Keep controllers isolated unless a controller+worker topology is an explicit edge or lab decision |
| Picking SQLite for a multi-controller HA design | Local SQLite through Kine is simple, not a replicated consensus datastore | Use embedded etcd for in-cluster HA or an external SQL datastore with its own HA guarantees |
| Changing node roles casually after installation | Role changes can conflict with existing service state, taints, and k0sctl inventory expectations | Decide `controller`, `worker`, or `controller+worker` before bootstrap and rotate nodes when topology must change |
| Forgetting the API external address and certificate SANs | Workers and clients may later fail TLS validation when a load balancer or DNS name is introduced | Configure `spec.api.externalAddress` and required SANs before creating the HA control plane |
| Treating bundled CNI as an afterthought | CNI choice affects routing, network policy, firewall rules, MTU, and troubleshooting procedures | Choose Kube-router, Calico, or custom CNI deliberately during cluster design and document why |
| Backing up only the k0s control plane | `k0s backup` does not capture arbitrary application persistent volumes or external database state | Pair k0s backups with application PV backups and external datastore backup policies |

## Quiz

Test your understanding of k0s by answering the questions before opening the details.

<details>
<summary>1. A team says k0s is "just kubeadm with a smaller installer." What is missing from that description?</summary>

The missing idea is packaging ownership. kubeadm assembles Kubernetes on a host where key prerequisites, especially the container runtime and Kubernetes packages, have already been installed and configured. k0s ships as a self-contained binary that supervises and manages the components it bundles. Both can produce conformant Kubernetes, but they put responsibility for host preparation, component version alignment, and lifecycle orchestration in different places.
</details>

<details>
<summary>2. When should you choose `controller`, `worker`, or `controller+worker`?</summary>

Choose `controller` for nodes that should run the control plane and datastore without hosting normal workloads. Choose `worker` for nodes that should run kubelet, runtime, CNI, and application pods. Choose `controller+worker` only when a node must do both, such as a lab, laptop, small appliance, or constrained edge site. The combined role is a topology decision because it couples workload risk to control-plane risk.
</details>

<details>
<summary>3. Why does Konnectivity matter in private worker networks?</summary>

The Kubernetes API server often needs to reach kubelets for logs, exec, port-forward, and metrics flows, but workers in edge or private networks may not accept inbound control-plane connections. Konnectivity lets worker-side agents establish a reverse tunnel toward the control plane. That preserves useful Kubernetes operations without requiring every worker to expose broad inbound access from the controller network.
</details>

<details>
<summary>4. A one-node k0s cluster may grow later. Why might `--single` be the wrong demo command?</summary>

The `--single` flag is ideal for a disposable one-node cluster because it creates a controller and worker in one easy step. The drawback is that the upstream docs describe it as disabling features needed for multi-node clusters. If the node may later become the first node in a larger lab, installing a controller with worker components enabled is a better starting shape than using single-node mode.
</details>

<details>
<summary>5. How should you decide between Kine plus SQLite, embedded etcd, and external SQL?</summary>

Start with the availability boundary. Kine plus SQLite keeps state local and simple, which is good for single-node clusters but not HA. Embedded etcd gives multiple controllers a replicated datastore, but requires quorum, reliable disks, and membership operations. External SQL moves the stateful reliability problem to a database platform, which is useful only if that database is actually operated with stronger availability than the cluster would have had itself.
</details>

<details>
<summary>6. What problem does k0sctl solve that manual token joins do not?</summary>

k0sctl turns a cluster into a declarative SSH inventory. It records hosts, roles, addresses, version, and cluster configuration in one file, then connects to nodes and performs the bootstrap or reconciliation steps. Manual token joins teach the mechanics, but they leave sequencing, token distribution, and desired-state documentation to humans. k0sctl gives the team a reviewable cluster plan.
</details>

<details>
<summary>7. Is k0s a CNCF project, a Mirantis product, or a conformant Kubernetes distribution?</summary>

As of the 2026-06 snapshot in this module, k0s is all three in different senses. It was built by Mirantis and has Mirantis commercial support around it. It is a CNCF Sandbox project, which is a project maturity and governance status. It is also CNCF Certified Kubernetes, which means the distribution's Kubernetes API behavior passes conformance expectations rather than being a separate Kubernetes-like API.
</details>

<details>
<summary>8. Why is a CNI decision hard to change after bootstrap?</summary>

The CNI controls pod addressing, routing, policy behavior, host interfaces, firewall programming, and sometimes service behavior. Once workloads, services, and nodes depend on that network model, replacing the provider is closer to a cluster migration than a small setting change. k0s supports Kube-router, Calico, and custom CNI, but the responsible choice is to decide during design and redeploy rather than casually mutate a live cluster.
</details>

## Hands-On Exercise: Deploy and Inspect a k0s Cluster Shape

### Objective

Use k0s directly for a single-node learning cluster, then create a k0sctl inventory that expresses the equivalent multi-node production intent. The exercise is designed so you can complete the first half on one Linux VM and still practice the k0sctl configuration model even if you do not have three reachable hosts.

### Environment Setup

Use a disposable Linux VM with systemd or OpenRC and enough resources for a small Kubernetes cluster. The current k0s system requirements list very small minimums, but a smoother lab experience usually comes from at least 2 vCPU and 2 GB RAM. Do not run this exercise on a workstation or server where removing `/var/lib/k0s` would surprise you.

```bash
# Optional but recommended: confirm the host looks suitable.
curl --proto '=https' --tlsv1.2 -sSf https://get.k0s.sh | sudo sh
sudo k0s sysinfo
```

### Step 1: Install an Expandable Single-Host Cluster

Install the node as a controller with worker components enabled rather than using `--single`. This gives you a one-host cluster for the lab while reinforcing the role distinction you would use if the cluster later gained workers.

```bash
sudo k0s install controller --enable-worker --no-taints --start
sleep 60
sudo k0s status
sudo k0s kubectl get nodes -o wide
sudo k0s kubectl get pods -A
```

### Step 2: Verify Workload Scheduling

Deploy a tiny workload and confirm it lands on the combined node. This verifies that worker components are active, the CNI is running, DNS is available, and the node is schedulable after `--no-taints`.

```bash
sudo k0s kubectl create deployment hello-k0s --image=nginx:1.27 --replicas=1
sudo k0s kubectl rollout status deployment/hello-k0s
sudo k0s kubectl get pods -o wide
sudo k0s kubectl delete deployment hello-k0s
```

### Step 3: Draft a k0sctl Inventory

Now write the multi-node intent you would use for a real environment. If you do not have the extra hosts, do not run `k0sctl apply`; the value of this step is learning how the topology becomes a reviewable file.

```bash
cat > k0sctl.yaml <<'EOF'
apiVersion: k0sctl.k0sproject.io/v1beta1
kind: Cluster
metadata:
  name: dojo-k0s-lab
spec:
  hosts:
    - role: controller
      ssh:
        address: 10.30.0.10
        user: ubuntu
        keyPath: ~/.ssh/id_ed25519
    - role: worker
      ssh:
        address: 10.30.0.11
        user: ubuntu
        keyPath: ~/.ssh/id_ed25519
    - role: worker
      ssh:
        address: 10.30.0.12
        user: ubuntu
        keyPath: ~/.ssh/id_ed25519
  k0s:
    version: v1.35.4+k0s.0
    config:
      apiVersion: k0s.k0sproject.io/v1beta1
      kind: ClusterConfig
      metadata:
        name: dojo-k0s-lab
      spec:
        api:
          externalAddress: 10.30.0.10
        storage:
          type: etcd
        network:
          provider: kuberouter
        telemetry:
          enabled: false
EOF
```

### Step 4: Review the Inventory Like a Platform Change

Before applying any cluster inventory, inspect it for topology mistakes. The questions are more important than the command: are controllers isolated, is the datastore compatible with the number of controllers, can every host reach the API address, are certificate names planned, and is the CNI choice documented?

```bash
grep -E 'role:|version:|externalAddress:|type:|provider:' k0sctl.yaml
```

### Step 5: Clean Up the Local Lab

Reset the local node only after you have deleted test workloads and confirmed there is no data you need. This reinforces the difference between a clean removal primitive and a safe production decommission procedure.

```bash
sudo k0s kubectl get all -A
sudo k0s stop
sudo k0s reset
```

### Success Criteria

- [ ] You can explain why `--enable-worker --no-taints` creates an expandable single-host lab while `--single` is a disposable shortcut.
- [ ] `sudo k0s status` shows a controller process with workloads enabled during the lab.
- [ ] `sudo k0s kubectl get nodes -o wide` shows the node ready before you deploy the test workload.
- [ ] The nginx deployment reaches rollout completion and is then removed cleanly.
- [ ] Your `k0sctl.yaml` separates controller and worker roles and records the chosen datastore and CNI.
- [ ] You can state what would need to change for a true HA inventory with three controllers and a stable load balancer address.

## Key Takeaways

1. k0s is a conformant Kubernetes distribution with a self-contained binary packaging model, not a forked Kubernetes API.
2. The strongest k0s idea is reduced host dependency: no Kubernetes package repository, no snap requirement, and no preinstalled CRI runtime for the normal path.
3. Controllers are isolated by default, workers run workloads, and controller+worker nodes should be deliberate exceptions for labs, appliances, or constrained edge sites.
4. Konnectivity supports private worker networks by reversing the control-plane-to-kubelet communication problem into a worker-initiated tunnel.
5. Kine plus SQLite is simple for single-node clusters, embedded etcd is the normal HA control-plane datastore, and external SQL shifts reliability to a database platform.
6. k0sctl turns multi-node bootstrap into a declarative inventory, which is easier to review and repeat than manual token joins.
7. Bundled CNI is a design decision, not a footnote; choose Kube-router, Calico, or custom CNI based on routing, policy, and operational requirements.
8. k0s backup protects k0s-managed control-plane state, not every application volume or external datastore dependency.
9. CNCF project maturity and Kubernetes conformance answer different questions; check both before making governance or compatibility claims.
10. The durable comparison between distributions is about capabilities and tradeoffs, not popularity or "best tool" claims.

## Sources

- https://k0sproject.io/
- https://github.com/k0sproject/k0s
- https://github.com/k0sproject/k0s/releases/tag/v1.36.1%2Bk0s.0
- https://www.cncf.io/projects/k0s/
- https://www.cncf.io/training/certification/software-conformance/
- https://docs.k0sproject.io/v1.35.4+k0s.0/architecture/
- https://docs.k0sproject.io/v1.35.4+k0s.0/system-requirements/
- https://docs.k0sproject.io/v1.35.4+k0s.0/external-runtime-deps/
- https://docs.k0sproject.io/v1.35.4+k0s.0/install/
- https://docs.k0sproject.io/v1.35.4+k0s.0/k0sctl-install/
- https://github.com/k0sproject/k0sctl
- https://docs.k0sproject.io/v1.35.4+k0s.0/configuration/
- https://docs.k0sproject.io/v1.35.4+k0s.0/networking/
- https://docs.k0sproject.io/v1.35.4+k0s.0/high-availability/
- https://docs.k0sproject.io/v1.35.4+k0s.0/backup/
- https://docs.k0sproject.io/v1.35.4+k0s.0/reset/
- https://docs.k0sproject.io/v1.35.4+k0s.0/helm-charts/
- https://docs.k0sproject.io/v1.35.4+k0s.0/runtime/

## Next Module

Continue to [Module 14.3: MicroK8s](../module-14.3-microk8s/) to compare k0s with Canonical's snap-packaged Kubernetes distribution and its add-on centered operating model.
