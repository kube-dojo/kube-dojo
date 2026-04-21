import re

module_content = """---
title: "Module 14.7: RKE2 - Enterprise Hardened Kubernetes"
slug: platform/toolkits/infrastructure-networking/k8s-distributions/module-14.7-rke2
sidebar:
  order: 8
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 50-55 minutes

## Learning Outcomes

After completing this module, you will be able to:

- **Design** air-gapped Kubernetes architectures using RKE2's self-contained artifact bundles.
- **Implement** CIS Benchmark-compliant clusters with automated hardening profiles out-of-the-box.
- **Diagnose** SELinux and AppArmor policy violations in strict, enterprise-hardened container environments.
- **Compare** FIPS 140-2 compliant cryptography modules in RKE2 against standard upstream Kubernetes cryptography.
- **Evaluate** RKE2 against k3s and kubeadm to determine the correct distribution for highly regulated use cases.

## Why This Module Matters

It was 2:00 AM on a Friday, and the engineering team at a mid-sized defense contractor was in full panic mode. They had just spent six months migrating their legacy applications to a shiny new Kubernetes platform built on standard `kubeadm`. The migration was flawless, the performance was stellar, and the developers loved it. Then, the federal auditors arrived.

Within two hours, the audit team flagged fifty-four critical violations. The cluster was not using FIPS 140-2 validated cryptographic modules. The control plane components were communicating using algorithms not approved by the National Institute of Standards and Technology (NIST). Furthermore, they failed almost every check in the CIS Kubernetes Benchmark because containers were running as root, host network namespaces were accessible, and etcd was completely unhardened. The company was given thirty days to achieve compliance, or they would lose a $40 million contract. Remediation using vanilla Kubernetes would require compiling custom binaries, maintaining private forks of Kubernetes components, and manual configuration of hundreds of security settings.

This is why RKE2 (Rancher Kubernetes Engine 2) exists. Originally known as "RKE Government," RKE2 was built specifically for environments where security and compliance are not optional "Day 2" activities, but fundamental requirements. It brings the operational simplicity of k3s—single binaries, declarative configurations—but replaces the lightweight components with enterprise-grade, FIPS-compliant, deeply hardened alternatives. In a world where supply chain attacks and zero-day vulnerabilities are the norm, RKE2 is the armored vehicle of Kubernetes distributions.

## 1. What is RKE2 and Why Does It Exist?

To understand RKE2, you have to understand the evolution of Rancher's distributions. Rancher initially created RKE1, an engine that deployed Kubernetes entirely within Docker containers. Later, they created k3s, a lightweight distribution for edge devices.

RKE2 is the synthesis of both, originally tailored for the US Federal Government but now widely adopted by banks, healthcare providers, and enterprises. 

**Analogy:** If `k3s` is a lightweight, agile dune buggy built to race across resource-constrained edge environments, and `kubeadm` is a kit-car you build yourself in the garage, then `RKE2` is an armored personnel carrier. It's heavier, it has thicker glass, and you can't hot-wire it easily, but when you are driving through a warzone (or a federal audit), it is exactly what you want.

### The Three Pillars of RKE2

1. **CIS Hardened by Default:** RKE2 passes the Center for Internet Security (CIS) Kubernetes Benchmark with minimal configuration. It explicitly disables insecure defaults.
2. **FIPS 140-2 Compliance:** By leveraging a custom, FIPS-validated version of the Go compiler (`go-fips`), all compiled binaries in RKE2 use federal-grade cryptographic algorithms.
3. **No Docker:** RKE2 uses `containerd` as its runtime exclusively. It does not depend on Docker, reducing the attack surface by removing the Docker daemon socket entirely.

> **Pause and Predict:** If RKE2 completely removes the Docker daemon and relies solely on containerd, what happens to legacy CI/CD pipelines running inside the cluster that try to mount `/var/run/docker.sock` to build images? 

*(Answer: The pipelines will break immediately. Without the Docker socket, tools like Docker-in-Docker (DinD) fail. You must migrate to daemonless image builders like Kaniko, Buildah, or Podman.)*

## 2. Architecture Deep Dive

While RKE2 shares the deployment mechanics of k3s (single binary, server and agent roles), its internal payload is vastly different.

```text
RKE2 ARCHITECTURE DEEP DIVE
─────────────────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────────────────┐
│                          RKE2 Server Node                                   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      RKE2 Binary (~150MB+)                          │   │
│  │                                                                     │   │
│  │  ┌──────────────────── Control Plane ───────────────────────┐      │   │
│  │  │  kube-apiserver                                          │      │   │
│  │  │  kube-controller-manager      (FIPS-140-2 Compiled)      │      │   │
│  │  │  kube-scheduler                                          │      │   │
│  │  └──────────────────────────────────────────────────────────┘      │   │
│  │                                                                     │   │
│  │  ┌──────────────────── Datastore ───────────────────────────┐      │   │
│  │  │                                                          │      │   │
│  │  │                   Embedded etcd                          │      │   │
│  │  │             (Not SQLite like k3s)                        │      │   │
│  │  │                                                          │      │   │
│  │  └──────────────────────────────────────────────────────────┘      │   │
│  │                                                                     │   │
│  │  ┌──────────────────── Bundled Components ──────────────────┐      │   │
│  │  │                                                          │      │   │
│  │  │  NGINX Ingress     CoreDNS         Canal CNI             │      │   │
│  │  │  (Replaces         (Hardened)      (Calico + Flannel)    │      │   │
│  │  │   Traefik)                         (Multus optional)     │      │   │
│  │  │                                                          │      │   │
│  │  └──────────────────────────────────────────────────────────┘      │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────── Host Security Layer ─────────────────────────────┐ │
│  │                                                                      │ │
│  │  SELinux Policies  │  AppArmor Profiles  │  CIS Benchmark Limits │ │
│  │                                                                      │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Differences: RKE2 vs k3s

| Component | k3s | RKE2 | Why the change? |
|-----------|-----|------|-----------------|
| **Datastore** | SQLite (default) | Embedded etcd | Enterprises require highly available, horizontally scalable data stores. |
| **Ingress** | Traefik | NGINX | NGINX is more widely adopted in enterprise environments and supports strict FIPS mode. |
| **CNI** | Flannel | Canal (or Cilium/Multus) | Canal provides Calico's network policies combined with Flannel's easy overlay, critical for zero-trust networks. |
| **Compiler** | Standard Go | `go-fips` | Federal compliance requires validated crypto modules. |

### The Canal CNI

By default, RKE2 deploys Canal. Canal is a combination of two popular technologies:
- **Flannel** handles the network overlay (VXLAN), assigning IP addresses to pods and routing traffic between nodes.
- **Calico** handles Network Policies, allowing you to restrict traffic between namespaces and pods for zero-trust security.

## 3. CIS Benchmark Compliance and Security Profiles

The Center for Internet Security (CIS) publishes a benchmark for securing Kubernetes. Running a standard `kubeadm` cluster and running the `kube-bench` tool will typically result in dozens of "FAIL" or "WARN" results. 

RKE2 is designed to pass these checks natively. However, because strict CIS compliance can break standard workloads, RKE2 requires you to explicitly opt-in via a configuration flag.

### Applying the CIS Profile

To enable CIS hardening, you define a profile in the RKE2 config file (`/etc/rancher/rke2/config.yaml`):

```yaml
# /etc/rancher/rke2/config.yaml
profile: "cis-1.23"
selinux: true
```

When you start RKE2 with this profile, it enforces:
1. **Pod Security Admissions (PSA):** Forces namespaces to adhere to restricted pod security standards.
2. **Hardened Control Plane:** Secures etcd with strict peer-to-peer mutual TLS (mTLS).
3. **Network Policies:** Drops unencrypted traffic defaults where possible.
4. **Node Restrictions:** Restricts kubelet permissions, disabling anonymous authentication.

### War Story: The Root of All Evil

A financial services company deployed RKE2 with the `cis-1.23` profile enabled. They immediately attempted to deploy their legacy application stack, which included an older version of Elasticsearch. The pods continuously crashed with `CreateContainerError`.

Investigation revealed the pods were attempting to run `sysctl -w vm.max_map_count=262144` during initialization. The CIS profile enforces a Pod Security Admission policy that prevents containers from running in privileged mode or modifying host-level sysctl parameters. The team had to re-architect their deployment, applying the sysctl changes at the host level via Ansible, and removing the privileged context from the Elasticsearch pod. Security via constraint forced better operational practices.

> **Before running an RKE2 cluster with a strict CIS profile, what output do you expect if a developer tries to deploy an NGINX container that binds to port 80?**

*(Answer: The pod will be rejected by the API server. Binding to ports below 1024 requires the `NET_BIND_SERVICE` capability, which is often dropped or blocked by default in strict restricted profiles.)*

## 4. Air-Gapped Operations

For military, intelligence, or heavily regulated industrial environments, Kubernetes nodes have zero internet access. You cannot run `docker pull nginx`. 

RKE2 is engineered for this. Unlike distributions that download components dynamically during installation, RKE2 can be deployed completely offline using tarball artifacts.

### The Air-Gap Workflow

```text
AIR-GAPPED DEPLOYMENT FLOW
─────────────────────────────────────────────────────────────────────────────

  Internet-Connected        Sneakernet /       Air-Gapped Environment
  Workstation               Data Diode
┌─────────────────────┐   ┌──────────────┐   ┌───────────────────────────┐
│                     │   │              │   │                           │
│ 1. Download RKE2    │   │              │   │ 4. Install binary         │
│    Binary           ├───┼─▶ USB Drive  ├───┼─▶                         │
│                     │   │   Optical    │   │ 5. Place image tarball in │
│ 2. Download RKE2    │   │   Media      │   │    /var/lib/rancher/...   │
│    Images Tarball   │   │              │   │                           │
│                     │   │              │   │ 6. systemctl start rke2   │
│ 3. Download Install │   │              │   │                           │
│    Script           │   │              │   │                           │
└─────────────────────┘   └──────────────┘   └───────────────────────────┘
```

1. You download the RKE2 binary, the installation script, and the **Images Tarball** (`rke2-images.linux-amd64.tar.zst`).
2. Transfer these files into the secure environment.
3. Place the images tarball into `/var/lib/rancher/rke2/agent/images/`.
4. When RKE2 starts, `containerd` automatically unpacks this tarball and seeds the local image cache. It never attempts to reach `registry.k8s.io`.

For application workloads, you must configure RKE2 to use a private, air-gapped registry (like Harbor or Nexus) by configuring `/etc/rancher/rke2/registries.yaml`.

```yaml
# /etc/rancher/rke2/registries.yaml
mirrors:
  "docker.io":
    endpoint:
      - "https://private-registry.internal.corp"
```

## 5. Windows Node Support

Enterprise environments often have a mix of Linux and Windows workloads. RKE2 supports hybrid clusters, allowing you to add Windows worker nodes to a Linux control plane.

To run Windows nodes, RKE2 requires **Calico** as the CNI, because Canal's Flannel component has limited Windows compatibility in strict environments.

When a Windows node joins, RKE2 deploys the Windows-specific kubelet and kube-proxy as native Windows services, allowing you to schedule `.NET` or legacy IIS applications natively alongside your modern Linux microservices.

## Did You Know?

- **RKE2 replaced RKE1's Docker dependency because of the dockershim deprecation.** By moving to containerd, RKE2 future-proofed itself against Kubernetes removing native Docker support.
- **FIPS 140-2 isn't just a configuration flag.** It requires the actual software binaries to be compiled differently. The `go-fips` compiler replaces standard Go cryptography with modules validated by the US government.
- **You can run RKE2 agents without root.** While the server (control plane) requires root, RKE2 has experimental support for rootless agents, further locking down the attack surface.
- **RKE2 is the default provisioner in Rancher v2.6+.** If you spin up a custom cluster using the Rancher UI today, it provisions RKE2 under the hood, replacing the older Docker-based RKE1.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| **Failing to configure SELinux** | Enterprise Linux distros have SELinux enforcing by default. If `rke2-selinux` RPM isn't installed, pods are blocked from mounting host paths. | Run `yum install -y rke2-selinux` before starting the cluster. |
| **Forgetting the agent token** | Agents cannot join the cluster without the secure token generated by the server. | Retrieve the token from `/var/lib/rancher/rke2/server/node-token` on the master and pass it to agents via config. |
| **Misconfiguring registries in Air-Gap** | Forgetting to map `registry.k8s.io` to the internal mirror causes core add-ons to hang in `ImagePullBackOff`. | Map all necessary upstream registries in `/etc/rancher/rke2/registries.yaml`. |
| **Deploying Canal with Windows nodes** | Canal (specifically the Flannel VXLAN) struggles with hybrid Windows/Linux networking. | Switch the CNI to Calico during server installation (`cni: calico` in config.yaml). |
| **Losing the etcd snapshots** | Embedded etcd requires backup strategies just like external etcd, but the paths are specific to RKE2. | Configure automated snapshots in `config.yaml` (`etcd-snapshot-schedule-cron`). |
| **Modifying FIPS mode post-install** | FIPS mode must be enabled at the OS kernel level *before* RKE2 is installed. You cannot simply toggle it later. | Boot the Linux host with FIPS mode enabled in GRUB, then install RKE2. |

## Quiz

<details>
<summary>1. Your security team mandates that your new Kubernetes cluster must comply with FIPS 140-2. You have installed RKE2. However, the auditor notes that the host operating system's kernel is not running in FIPS mode. Is the RKE2 installation compliant?</summary>
No. While RKE2 is compiled with `go-fips` and uses validated cryptographic modules, true FIPS compliance requires the underlying host operating system (e.g., Red Hat Enterprise Linux) to have FIPS mode enabled at the kernel level. Without the OS in FIPS mode, the environment is not fully compliant.
</details>

<details>
<summary>2. You deploy a legacy application to an RKE2 cluster running the `cis-1.23` profile. The application's pod goes into `CrashLoopBackOff` because it cannot bind to port 80. Why does this happen, and what is the proper architectural fix?</summary>
This happens because the CIS profile enforces Pod Security Admissions (PSA) that drop the `NET_BIND_SERVICE` capability, preventing non-root users from binding to privileged ports (below 1024). The proper fix is to reconfigure the application to listen on an unprivileged port (like 8080) and use a Kubernetes Service to map port 80 to the application's port 8080.
</details>

<details>
<summary>3. You are deploying RKE2 in a completely air-gapped nuclear facility. You copied the RKE2 binary to the server and ran `systemctl start rke2-server`. The service starts, but the `kube-system` pods are all stuck in `ImagePullBackOff`. What crucial step did you miss?</summary>
You forgot to download the RKE2 Images Tarball (`rke2-images.linux-amd64.tar.zst`) and place it in the `/var/lib/rancher/rke2/agent/images/` directory before starting the service. Without this tarball, `containerd` cannot seed its local cache and attempts to reach the internet to download the core system images.
</details>

<details>
<summary>4. Your team wants to run a hybrid cluster with Linux control plane nodes and Windows worker nodes. You install RKE2 with the default configuration. When you join the Windows nodes, pod-to-pod networking fails. What is the most likely cause?</summary>
RKE2 defaults to the Canal CNI (Flannel + Calico). Canal is not optimized for hybrid Windows/Linux networking out-of-the-box. You must configure RKE2 to use the pure Calico CNI (`cni: calico`) in the server's `config.yaml` before bootstrapping the cluster to properly support Windows nodes.
</details>

<details>
<summary>5. A developer complains that their CI/CD pipeline, which builds Docker images using a `docker.sock` volume mount, is failing on the new RKE2 cluster. What is the fundamental reason for this failure?</summary>
RKE2 explicitly removes Docker and the Docker daemon in favor of `containerd`. Therefore, there is no `/var/run/docker.sock` file on the host nodes to mount. The pipeline must be refactored to use a daemonless image builder like Kaniko or Buildah.
</details>

<details>
<summary>6. You need to ensure that your RKE2 cluster is highly available. Unlike k3s, which defaults to SQLite, what datastore does RKE2 use by default, and how is it deployed?</summary>
RKE2 uses etcd by default. It is deployed as an embedded service running directly on the RKE2 server (control plane) nodes, automatically forming a quorum as you add more server nodes to the cluster.
</details>

## Hands-On Exercise: Deploying a Hardened RKE2 Cluster

In this exercise, you will deploy a hardened RKE2 server, configure a strict CIS profile, and verify the security posture.

### Setup Requirements
- A Linux VM (Ubuntu 22.04 or RHEL 8/9) with at least 4GB RAM and 2 CPUs.
- Root or sudo access.

### Task 1: Create the Hardened Configuration

Before installing RKE2, you must configure it. RKE2 reads from `/etc/rancher/rke2/config.yaml`.

1. Create the configuration directory:
   ```bash
   sudo mkdir -p /etc/rancher/rke2
   ```

2. Create the configuration file enabling the CIS profile:
   ```bash
   cat <<EOF | sudo tee /etc/rancher/rke2/config.yaml
   profile: "cis-1.23"
   selinux: true
   write-kubeconfig-mode: "0644"
   EOF
   ```

### Task 2: Install and Start RKE2

1. Run the RKE2 installation script. (Note: In a true air-gap, you would execute the binary directly, but we will use the script for simplicity).
   ```bash
   curl -sfL https://get.rke2.io | sudo sh -
   ```

2. Enable and start the RKE2 Server service. This may take 3-5 minutes as it downloads core images.
   ```bash
   sudo systemctl enable rke2-server.service
   sudo systemctl start rke2-server.service
   ```

3. Configure your local kubectl to use the RKE2 context:
   ```bash
   mkdir -p ~/.kube
   sudo cp /etc/rancher/rke2/rke2.yaml ~/.kube/config
   sudo chown $USER:$USER ~/.kube/config
   alias k=kubectl
   ```

4. Verify the node is ready:
   ```bash
   k get nodes
   ```

### Task 3: Verify the CIS Restrictions

Let's attempt to deploy a privileged pod to verify our CIS hardening is active.

1. Create a pod manifest that requests privileged access:
   ```bash
   cat <<EOF > bad-pod.yaml
   apiVersion: v1
   kind: Pod
   metadata:
     name: privileged-pod
     namespace: default
   spec:
     containers:
     - name: shell
       image: alpine:latest
       command: ["sleep", "3600"]
       securityContext:
         privileged: true
   EOF
   ```

2. Attempt to apply the pod:
   ```bash
   k apply -f bad-pod.yaml
   ```

3. Observe the rejection. You should receive an error from the Pod Security Admission controller stating that privileged containers are forbidden by the restricted policy.

### Task 4: Configure an Air-Gap Registry Mirror (Simulated)

Even if you aren't air-gapped, configuring a registry mirror is a crucial RKE2 skill.

1. Create the registry configuration file:
   ```bash
   sudo mkdir -p /etc/rancher/rke2/
   cat <<EOF | sudo tee /etc/rancher/rke2/registries.yaml
   mirrors:
     "docker.io":
       endpoint:
         - "https://registry-1.docker.io"
     "quay.io":
       endpoint:
         - "https://quay.io"
   EOF
   ```

2. Restart the RKE2 service to apply the registry configuration:
   ```bash
   sudo systemctl restart rke2-server
   ```

### Success Criteria

- [ ] You have successfully deployed an RKE2 server node.
- [ ] You have verified the node status is `Ready` using the RKE2 kubeconfig.
- [ ] You attempted to deploy a privileged pod and confirmed it was rejected by the CIS profile constraints.
- [ ] You created a `registries.yaml` file to configure container registry mirroring.

## Next Module

Now that you've mastered lightweight and hardened distributions, it's time to explore the giants: [Module 14.6: Managed Kubernetes](module-14.6-managed-kubernetes/) — diving into EKS, GKE, and AKS.
"""

index_content = """---
title: "Kubernetes Distributions Toolkit"
sidebar:
  order: 0
  label: "K8s Distributions"
---
> **Toolkit Track** | 7 Modules | ~6 hours total

## Overview

The Kubernetes Distributions Toolkit covers lightweight Kubernetes alternatives for edge, IoT, development, and resource-constrained environments. When vanilla Kubernetes is too heavy—requiring too much RAM, too many nodes, or too complex to manage—these distributions deliver Kubernetes-compatible APIs with dramatically lower overhead.

This toolkit applies concepts from [Systems Thinking](../../../foundations/systems-thinking/) and [Platform Engineering](../../../disciplines/core-platform/platform-engineering/).

## Prerequisites

Before starting this toolkit:
- Kubernetes fundamentals (kubectl, deployments, services)
- Container runtime basics (containerd, Docker)
- Basic Linux system administration
- Understanding of when you'd use Kubernetes vs simpler alternatives

## Modules

| # | Module | Complexity | Time |
|---|--------|------------|------|
| 14.1 | [k3s](module-14.1-k3s/) | `[MEDIUM]` | 45-50 min |
| 14.2 | [k0s](module-14.2-k0s/) | `[MEDIUM]` | 40-45 min |
| 14.3 | [MicroK8s](module-14.3-microk8s/) | `[MEDIUM]` | 40-45 min |
| 14.4 | [Talos](module-14.4-talos/) | `[COMPLEX]` | 50-55 min |
| 14.5 | [OpenShift](module-14.5-openshift/) | `[COMPLEX]` | 50-55 min |
| 14.6 | [Managed Kubernetes](module-14.6-managed-kubernetes/) | `[COMPLEX]` | 55-60 min |
| 14.7 | [RKE2](module-14.7-rke2/) | `[COMPLEX]` | 50-55 min |

## Learning Outcomes

After completing this toolkit, you will be able to:

1. **Deploy k3s** — The most popular lightweight Kubernetes for edge
2. **Run k0s** — Zero-friction Kubernetes for any environment
3. **Use MicroK8s** — Canonical's snap-based Kubernetes
4. **Understand Talos** — Immutable OS built specifically for Kubernetes
5. **Navigate OpenShift** — Enterprise Kubernetes with batteries included
6. **Compare managed services** — EKS vs GKE vs AKS decision making
7. **Choose the right distribution** — Match requirements to distribution strengths
8. **Deploy RKE2** — Enterprise-hardened, FIPS-compliant Kubernetes

## Distribution Selection Guide

```
WHICH KUBERNETES DISTRIBUTION?
─────────────────────────────────────────────────────────────────────────────

"I need Kubernetes on edge devices with limited resources"
└──▶ k3s
     • 512MB RAM minimum (production: 1GB)
     • Single binary, ~60MB
     • Built-in: Traefik, Local Storage, SQLite
     • CNCF Sandbox project
     • Most popular edge K8s

"I need enterprise security, FIPS compliance, and CIS hardening"
└──▶ RKE2
     • Hardened by default, passes CIS Benchmark
     • FIPS 140-2 validated cryptography
     • Single binary, optimized for air-gap
     • Default Rancher provisioner
     • Ideal for defense and regulated industries

"I want zero dependencies, single binary, works anywhere"
└──▶ k0s
     • ~180MB single binary
     • No host dependencies (even for HA)
     • Built-in: kube-router, containerd
     • Cluster API support
     • Enterprise support (Mirantis)

"I'm using Ubuntu/Canonical ecosystem"
└──▶ MicroK8s
     • Snap-based installation
     • Add-ons via microk8s enable
     • Tight Ubuntu integration
     • Built-in: dns, storage, dashboard
     • Popular for development

"I need vanilla Kubernetes behavior"
└──▶ kubeadm / Cluster API
     • Full upstream K8s
     • Most compatible
     • More resources required
     • Production proven at scale

COMPARISON MATRIX:
─────────────────────────────────────────────────────────────────────────────
                    k3s         k0s         MicroK8s    RKE2        kubeadm
─────────────────────────────────────────────────────────────────────────────
Min RAM            512MB       512MB       512MB       4GB         2GB
Binary size        ~60MB       ~180MB      Via snap    ~150MB+     ~300MB
Architecture       ARM/AMD64   ARM/AMD64   ARM/AMD64   AMD64       ARM/AMD64
HA built-in        ✓ (embed)   ✓           ✓           ✓ (embed)   Manual
Datastore          SQLite/etc  SQLite/etc  Dqlite      etcd        etcd
Install method     curl|bash   curl|bash   snap        curl|bash   apt/yum
CNCF project       Sandbox     No          No          No          Yes
Air-gap support    ✓           ✓           ✓           ✓ (native)  ✓
Windows nodes      ✓           ✓           Limited     ✓           ✓
Cert rotation      Auto        Auto        Auto        Auto        Manual
FIPS 140-2         No          No          No          ✓           Manual
```

## The Lightweight Kubernetes Landscape

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  KUBERNETES DISTRIBUTION LANDSCAPE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  UPSTREAM KUBERNETES                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  kubeadm         │  Cluster API      │  kOps                        │   │
│  │  (official)      │  (declarative)    │  (AWS-focused)               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  LIGHTWEIGHT DISTRIBUTIONS                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  k3s                  k0s                  MicroK8s                │   │
│  │  ┌─────────────┐     ┌─────────────┐      ┌─────────────┐         │   │
│  │  │ Rancher/SUSE│     │  Mirantis   │      │  Canonical  │         │   │
│  │  │ Edge focus  │     │ Zero deps   │      │ Snap-based  │         │   │
│  │  │ CNCF Sandbox│     │             │      │ Ubuntu      │         │   │
│  │  └─────────────┘     └─────────────┘      └─────────────┘         │   │
│  │                                                                     │   │
│  │  Kind                 minikube              k3d                    │   │
│  │  ┌─────────────┐     ┌─────────────┐      ┌─────────────┐         │   │
│  │  │  K8s in     │     │  VM-based   │      │ k3s in      │         │   │
│  │  │  Docker     │     │  local dev  │      │ Docker      │         │   │
│  │  │  (testing)  │     │  (original) │      │ (fast)      │         │   │
│  │  └─────────────┘     └─────────────┘      └─────────────┘         │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  HARDENED / ENTERPRISE                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  RKE2                 OpenShift             Talos                  │   │
│  │  ┌─────────────┐     ┌─────────────┐      ┌─────────────┐         │   │
│  │  │ Federal/CIS │     │ Enterprise  │      │ Immutable   │         │   │
│  │  │ FIPS secure │     │ Batteries-in│      │ API-only    │         │   │
│  │  └─────────────┘     └─────────────┘      └─────────────┘         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MANAGED KUBERNETES                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  EKS (AWS)     │  GKE (Google)   │  AKS (Azure)   │  DOKS (DO)     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Use Case Decision Tree

```
USE CASE DECISION TREE
─────────────────────────────────────────────────────────────────────────────

Start: What's your primary use case?
                    │
    ┌───────────────┼───────────────┬───────────────┬───────────────┐
    │               │               │               │               │
    ▼               ▼               ▼               ▼               ▼
Edge/IoT?      Development?    Production?    Air-gapped?    Federal/Compliance?
    │               │               │               │               │
    │ Yes           │ Yes           │ Yes           │ Yes           │ Yes
    ▼               ▼               ▼               ▼               ▼
k3s             Kind/k3d       Assess needs    k3s or k0s      RKE2
(smallest,      (fastest,      │               (both support   (FIPS 140-2,
 most proven)    ephemeral)    │               offline install) CIS hardened)
                               │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
              <100 nodes?            >100 nodes?
                    │                     │
                    ▼                     ▼
              k3s or k0s            kubeadm/EKS/GKE
              (either works,        (need full scale)
               choose ecosystem)

RESOURCE CONSTRAINTS:
─────────────────────────────────────────────────────────────────────────────
<1GB RAM available        →  k3s (most optimized for low memory)
1-2GB RAM available       →  k3s, k0s, or MicroK8s (all work)
>2GB RAM available        →  Any distribution, consider features
>4GB RAM available        →  RKE2 (ideal for security over efficiency)
ARM devices               →  k3s (best ARM support), k0s, MicroK8s
x86_64 only               →  All options available
```

## Architecture Comparison

### k3s Architecture

```
k3s ARCHITECTURE
─────────────────────────────────────────────────────────────────────────────

                    ┌─────────────────────────────────────────┐
                    │           k3s Server (Master)           │
                    │                                         │
                    │  ┌─────────────────────────────────────┐│
                    │  │          k3s Binary (~60MB)         ││
                    │  │                                     ││
                    │  │  API Server │ Controller │ Scheduler││
                    │  │  ─────────────────────────────────  ││
                    │  │  kube-proxy │ kubelet │ containerd  ││
                    │  │  ─────────────────────────────────  ││
                    │  │  Traefik │ CoreDNS │ Local Path    ││
                    │  │  ─────────────────────────────────  ││
                    │  │       Flannel (default CNI)         ││
                    │  └─────────────────────────────────────┘│
                    │                    │                    │
                    │  ┌─────────────────▼─────────────────┐  │
                    │  │   SQLite (default) / etcd / MySQL │  │
                    │  │          PostgreSQL                │  │
                    │  └───────────────────────────────────┘  │
                    └────────────────────┬────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
           ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
           │   k3s Agent   │    │   k3s Agent   │    │   k3s Agent   │
           │   (Worker)    │    │   (Worker)    │    │   (Worker)    │
           │               │    │               │    │               │
           │  kubelet      │    │  kubelet      │    │  kubelet      │
           │  kube-proxy   │    │  kube-proxy   │    │  kube-proxy   │
           │  containerd   │    │  containerd   │    │  containerd   │
           └───────────────┘    └───────────────┘    └───────────────┘

WHAT'S REMOVED FROM UPSTREAM K8S:
─────────────────────────────────────────────────────────────────────────────
✗ etcd (replaced with SQLite for single-node)
✗ Cloud controller manager
✗ Legacy/alpha features
✗ In-tree storage drivers
✗ In-tree cloud providers

WHAT'S BUNDLED:
─────────────────────────────────────────────────────────────────────────────
✓ Traefik Ingress Controller
✓ CoreDNS
✓ Flannel CNI
✓ Local Path Provisioner
✓ Service Load Balancer
✓ Network Policy Controller
```

### k0s Architecture

```
k0s ARCHITECTURE
─────────────────────────────────────────────────────────────────────────────

                    ┌─────────────────────────────────────────┐
                    │          k0s Controller Node            │
                    │                                         │
                    │  ┌─────────────────────────────────────┐│
                    │  │         k0s Binary (~180MB)         ││
                    │  │                                     ││
                    │  │  API Server │ Controller │ Scheduler││
                    │  │  ─────────────────────────────────  ││
                    │  │  kube-proxy │ konnectivity-server   ││
                    │  │  ─────────────────────────────────  ││
                    │  │           kube-router              ││
                    │  │  (CNI, network policy, service LB) ││
                    │  └─────────────────────────────────────┘│
                    │                    │                    │
                    │  ┌─────────────────▼─────────────────┐  │
                    │  │     etcd (embedded) / SQLite      │  │
                    │  │           MySQL / PostgreSQL       │  │
                    │  └───────────────────────────────────┘  │
                    └────────────────────┬────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
           ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
           │   k0s Worker  │    │   k0s Worker  │    │   k0s Worker  │
           │               │    │               │    │               │
           │  kubelet      │    │  kubelet      │    │  kubelet      │
           │  containerd   │    │  containerd   │    │  containerd   │
           │  kube-proxy   │    │  kube-proxy   │    │  kube-proxy   │
           └───────────────┘    └───────────────┘    └───────────────┘

KEY DIFFERENTIATOR: Zero Host Dependencies
─────────────────────────────────────────────────────────────────────────────
• All components bundled in single binary
• No kubelet or containerd required on host
• k0s brings its own container runtime
• Clean /var/lib/k0s directory for all state
```

## Common Architectures

### Single Node (Development/Edge)

```
SINGLE NODE DEPLOYMENT
─────────────────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────────────┐
│                         Single Node                                      │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    k3s/k0s/MicroK8s                              │   │
│  │                                                                   │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐                │   │
│  │  │ Control    │  │  Worker    │  │  Storage   │                │   │
│  │  │ Plane      │  │  (kubelet) │  │  (SQLite)  │                │   │
│  │  └────────────┘  └────────────┘  └────────────┘                │   │
│  │                                                                   │   │
│  │  ┌──────────────────────────────────────────────────────────┐   │   │
│  │  │                     Workloads                             │   │   │
│  │  │  [App1] [App2] [App3] [DB] [Cache]                       │   │   │
│  │  └──────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

Use cases:
• Development workstations
• Edge devices (retail, manufacturing)
• CI/CD runners
• Home lab / learning
```

### High Availability (Production)

```
HIGH AVAILABILITY DEPLOYMENT
─────────────────────────────────────────────────────────────────────────────

        ┌───────────────────────────────────────────────────────┐
        │                   Load Balancer                       │
        │              (HAProxy / cloud LB)                     │
        └───────────────────────────┬───────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│  Server 1     │           │  Server 2     │           │  Server 3     │
│  (control)    │◄─────────▶│  (control)    │◄─────────▶│  (control)    │
│               │           │               │           │               │
│  ┌─────────┐  │           │  ┌─────────┐  │           │  ┌─────────┐  │
│  │  etcd   │◄─┼───────────┼─▶│  etcd   │◄─┼───────────┼─▶│  etcd   │  │
│  └─────────┘  │           │  └─────────┘  │           │  └─────────┘  │
└───────────────┘           └───────────────┘           └───────────────┘
        │                           │                           │
        └───────────────────────────┴───────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│   Agent 1     │           │   Agent 2     │           │   Agent N     │
│   (worker)    │           │   (worker)    │           │   (worker)    │
└───────────────┘           └───────────────┘           └───────────────┘

HA OPTIONS BY DISTRIBUTION:
─────────────────────────────────────────────────────────────────────────────
k3s:      --cluster-init (embedded etcd) or external DB
k0s:      k0sctl for automated HA setup
MicroK8s: microk8s add-node (Dqlite clustering)
RKE2:     Embedded etcd (join servers with token)
```

## Study Path

```
Module 14.1: k3s
     │
     │  Most popular lightweight K8s
     │  Best for edge and IoT
     │  CNCF Sandbox project
     ▼
Module 14.2: k0s
     │
     │  Zero dependencies
     │  Clean architecture
     │  Cluster API support
     ▼
Module 14.3: MicroK8s
     │
     │  Snap-based
     │  Add-on ecosystem
     │  Ubuntu integration
     ▼
Module 14.4: Talos
     │
     │  Immutable OS
     │  API-only management
     │  Maximum security
     ▼
Module 14.5: OpenShift
     │
     │  Enterprise platform
     │  Batteries included
     │  Red Hat support
     ▼
Module 14.6: Managed Kubernetes
     │
     │  EKS vs GKE vs AKS
     │  Provider comparison
     │  Cost optimization
     ▼
Module 14.7: RKE2
     │
     │  Enterprise hardened
     │  CIS Benchmark compliance
     │  FIPS 140-2 validated
     ▼
[Toolkit Complete] → Next: CI/CD Pipelines Toolkit
```

## Resource Requirements

```
RESOURCE COMPARISON
─────────────────────────────────────────────────────────────────────────────

                    k3s         k0s         MicroK8s    RKE2        kubeadm
─────────────────────────────────────────────────────────────────────────────
MINIMUM (Dev/Test):
─────────────────────────────────────────────────────────────────────────────
RAM (server)       512MB       512MB       540MB       4GB         2GB
RAM (agent)        75MB        100MB       100MB       2GB         100MB
Disk               200MB       300MB       2GB         10GB        2GB
CPU                1 core      1 core      1 core      2 cores     2 cores

RECOMMENDED (Production):
─────────────────────────────────────────────────────────────────────────────
RAM (server)       2GB         2GB         2GB         8GB         4GB
RAM (agent)        512MB       512MB       512MB       4GB         1GB
Disk               10GB        10GB        20GB        40GB        20GB
CPU                2 cores     2 cores     2 cores     4 cores     2 cores
```

## Hands-On Focus

| Module | Key Exercise |
|--------|--------------|
| k3s | Deploy HA cluster, run workloads, configure storage |
| k0s | Zero-dependency install, cluster-api bootstrap |
| MicroK8s | Snap install, enable add-ons, cluster join |
| Talos | Deploy cluster, verify security, API management |
| OpenShift | S2I builds, Routes, BuildConfigs |
| Managed K8s | Multi-provider comparison, cost analysis |
| RKE2 | Deploy CIS hardened cluster, verify air-gap registry |

## Related Tracks

- **Before**: [Container Registries Toolkit](../../cicd-delivery/container-registries/) — Store images for your cluster
- **Related**: [Developer Experience Toolkit](../../developer-experience/) — Local K8s options
- **Related**: [IaC Tools Toolkit](../iac-tools/) — Automate cluster provisioning
- **After**: [CI/CD Pipelines Toolkit](../../cicd-delivery/ci-cd-pipelines/) — Deploy to your clusters

---

*"The best Kubernetes distribution is the one that fits your constraints. Sometimes that's vanilla K8s, sometimes it's 60MB running on a Raspberry Pi."*
"""

with open("src/content/docs/platform/toolkits/infrastructure-networking/k8s-distributions/module-14.7-rke2.md", "w") as f:
    f.write(module_content)

with open("src/content/docs/platform/toolkits/infrastructure-networking/k8s-distributions/index.md", "w") as f:
    f.write(index_content)
