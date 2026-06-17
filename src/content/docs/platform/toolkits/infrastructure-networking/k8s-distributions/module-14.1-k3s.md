---
revision_pending: true
title: "Module 14.1: k3s - Lightweight Kubernetes for Edge"
slug: platform/toolkits/infrastructure-networking/k8s-distributions/module-14.1-k3s
sidebar:
  order: 2
---
> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: 45-50 minutes

## Overview

k3s is Kubernetes that fits on a Raspberry Pi, an industrial gateway, or a developer laptop with room to spare. Created by Rancher Labs founder Darren Shepherd in 2019 and now maintained under SUSE, k3s packages the Kubernetes control plane, node components, and a curated set of cluster add-ons into a single binary that is dramatically smaller than assembling upstream Kubernetes yourself. The project was donated to the CNCF in August 2020 and remains a Sandbox project as of mid-2026, with an active incubation application underway. k3s is not a fork: it is CNCF Certified Kubernetes, meaning the same API objects, the same kubectl workflows, and the same ecosystem of Helm charts and operators apply without translation layers.

What makes k3s worth studying in a distributions module is not brand loyalty but packaging philosophy. Upstream Kubernetes gives you composable primitives; a distribution makes opinionated choices about datastore, container runtime, CNI, ingress, load balancing, and storage so you can bootstrap a working cluster quickly. k3s optimizes for operational simplicity on small footprints—edge sites, CI runners, homelab nodes, air-gapped appliances, and ARM boards—while still exposing escape hatches when you want to bring your own ingress controller or external database. This module teaches you to deploy, configure, and operate k3s for those environments, with emphasis on the durable concepts (datastore tradeoffs, bundled components, HA topology) that survive version churn.

## Prerequisites

This module assumes you can operate a minimal Kubernetes cluster without reaching for a managed control plane. You should be comfortable creating Deployments and Services, reading pod logs, and applying manifests with kubectl. Linux fundamentals matter because k3s installs as a systemd service, writes configuration under `/etc/rancher/k3s`, and expects you to understand permissions on kubeconfig files. You also need SSH or console access to at least one Linux host—or a local VM tool like Multipass—because every exercise installs real binaries rather than simulating commands. Container runtime knowledge helps when you debug image pull failures: k3s uses containerd, and logs appear in `journalctl -u k3s` rather than Docker's familiar CLI unless you explicitly enable cri-dockerd.

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy k3s clusters on edge devices and resource-constrained environments with automated installation**, including single-node SQLite setups and multi-node clusters joined with node tokens
- **Configure k3s with embedded etcd, Traefik ingress, and ServiceLB for production-ready lightweight clusters**, including disabling bundled components when corporate standards require alternate controllers
- **Implement multi-node k3s clusters with server and agent roles for HA edge deployments**, including embedded-etcd quorum and external SQL datastores when SQLite is insufficient
- **Evaluate k3s against standard Kubernetes and peer distributions for edge computing, IoT, and development environments**, using capability-based comparison rather than marketing claims

Each outcome maps to a durable skill you can reuse when the next lightweight distribution ships: understanding what was bundled, what was removed, and which tradeoff you accepted when you ran the install script.


## Why This Module Matters

Kubernetes is everywhere in cloud data centers, but not every place that needs orchestration can afford a three-node etcd quorum, a dedicated ingress tier, and a platform team on call. Factory floors, retail backrooms, telecom cabinets, agricultural sensors, and CI runners often share a different constraint profile: limited RAM, intermittent connectivity, no on-site Kubernetes expert, and hardware that was purchased for a single application rather than for running a miniature data center. Traditional kubeadm clusters assume you will assemble and maintain each layer yourself, which is the right tradeoff when you need maximum control but the wrong default when you need a working cluster in fifteen minutes on a $50 board.

k3s exists because Rancher Labs asked a practical question: what is the smallest conformant Kubernetes you can ship as one binary with sensible defaults? The answer removed legacy in-tree cloud providers and storage drivers, bundled containerd as the sole CRI, and replaced the default etcd requirement with a pluggable datastore layer called kine that can back the API onto SQLite, embedded etcd, or external SQL. The result is real Kubernetes—same APIs, same kubectl, same Helm charts—not a parallel platform with compatibility caveats. You trade some configurability at install time for dramatically lower bootstrap friction, which is exactly what edge and appliance deployments need.

> **The Appliance Analogy**
>
> Think of upstream kubeadm as buying a professional kitchen: you choose every appliance, wire the plumbing, and hire staff who know how each piece works. k3s is closer to a well-designed food truck: the grill, fridge, and prep surface are already integrated, the footprint is small, and you can still swap the sauce vendor if you disable the default Traefik ingress and install your own controller. The truck is not "less serious" food—it is optimized for mobility and fast setup.

Understanding k3s as a distribution—not merely a "small Kubernetes"—helps you evaluate when it fits and when another distro or managed service is better. The durable lesson is how packaging choices (datastore, bundled ingress, ServiceLB for bare metal) shape operability long after you forget the exact version string printed by `k3s --version`.

## Did You Know?

- **Why "k3s"?**: Per the upstream docs, Kubernetes is a 10-letter word stylized as K8s; k3s is a 5-letter word stylized as K3s, evoking "half the size" in memory footprint—there is no long form and no official pronunciation
- **Origin**: Created by Rancher Labs founder Darren Shepherd; first public commits date to January 2019, and the project joined CNCF Sandbox on August 19, 2020
- **Not a fork**: k3s passes CNCF Kubernetes conformance certification—the same API machinery as upstream, with bundled components and a smaller binary rather than a divergent control plane
- **kine datastore abstraction**: k3s uses kine to translate Kubernetes storage operations onto SQLite, etcd, MySQL, MariaDB, or PostgreSQL, which is why a single-server SQLite setup and a three-server embedded-etcd HA setup share one distribution

## What a Kubernetes Distribution Actually Is

Before you touch an install script, it helps to separate upstream Kubernetes from the distributions that package it. Upstream Kubernetes—the code in `kubernetes/kubernetes`—defines the API machinery, controllers, scheduler, kubelet contract, and conformance tests. It does not, by itself, tell you which container runtime to use, how pods get IP addresses, how `type: LoadBalancer` services obtain external IPs on bare metal, or where the API server's state lives. Every production cluster makes those choices; a distribution makes them for you so bootstrap is repeatable.

The durable spine of any distribution decision is therefore a checklist of capabilities, not a brand name. You should know the default datastore and what HA mode it enables, which CNI ships out of the box, whether ingress and bare-metal load balancing are bundled, how nodes join and upgrade, and whether the result is conformant Kubernetes or a fork with API caveats. Version numbers and minimum RAM figures change quarterly; those capabilities and their tradeoffs persist across releases.

| Capability | k3s | k0s | MicroK8s | upstream kubeadm |
|---|---|---|---|---|
| Default single-node datastore | SQLite via kine | SQLite or embedded etcd | dqlite (embedded) | External etcd (you provision) |
| HA datastore mechanism | Embedded etcd (`--cluster-init`) or external SQL/etcd | Embedded etcd or external SQL | dqlite clustering (HA addon) | External etcd cluster (3+ members) |
| Bundled CNI | Flannel (configurable backend) | kube-router | Calico or Flannel (addons) | None—install Cilium, Calico, etc. |
| Bundled ingress | Traefik (disable with `--disable traefik`) | None by default | nginx ingress (addon) | None—install your controller |
| Bundled bare-metal Service LB | ServiceLB / Klipper (disable with `--disable servicelb`) | kube-router service proxy | MetalLB (addon) | Cloud provider integration or MetalLB |
| Install mechanism | curl install script or single binary | `get.k0s.sh` or binary; k0sctl for multi-node | snap package | kubeadm init/join on prepared OS |
| Packaging model | Single ~60–100MB binary + bundled containerd | Single binary with embedded containerd | Snap confinement | Discrete control-plane and node packages |
| Primary positioning | Edge, IoT, ARM, air-gap, dev/CI | Zero host dependencies, immutable state dir | Developer laptop, edge appliances | Full control, reference architecture |
| Conformance | CNCF Certified Kubernetes (Sandbox project) | CNCF Certified Kubernetes (Sandbox project) | CNCF Certified Kubernetes | Upstream reference implementation |

> **Landscape snapshot — as of 2026-06. This changes fast; verify against upstream docs before relying on specifics.**
>
> | Attribute | Current upstream snapshot |
> |---|---|
> | CNCF maturity | Sandbox (accepted 2020-08-19); incubation application active as of 2026-05 per [CNCF TOC issue #1957](https://github.com/cncf/toc/issues/1957) |
> | Binary size claim | Upstream tagline: "less than 100 MB" all-in-one binary ([docs.k3s.io](https://docs.k3s.io/)) |
> | Default bundled runtime | containerd (CRI); Docker optional via cri-dockerd |
> | Default CNI | Flannel with vxlan backend unless disabled |
> | Default ingress | Traefik Ingress controller |
> | Default Service LB | ServiceLB (Klipper) controller |
> | Default storage provisioner | local-path-provisioner (`local-path` StorageClass) |
> | Supported external DBs | etcd 3.5.x, MySQL 8.0/8.4, MariaDB 10.11/11.4, PostgreSQL 15/16/17 per [datastore docs](https://docs.k3s.io/datastore) |
> | Air-gap artifacts | `k3s` binary + `k3s-airgap-images-$ARCH.tar.zst` from [GitHub releases](https://github.com/k3s-io/k3s/releases) |
> | Automated upgrades | system-upgrade-controller + `rancher/k3s-upgrade` image via [upgrade plans](https://docs.k3s.io/upgrades/automated) |

No row in the Rosetta table declares a winner. k3s, k0s, and MicroK8s each optimize for different bootstrap stories: k3s for the smallest integrated edge binary, k0s for zero host dependencies and clean `/var/lib/k0s` state isolation, MicroK8s for snap-based laptop clusters, and kubeadm for teams that want to own every layer. Your job is to map workload constraints—offline sites, HA requirements, existing DBA skills, ARM boards—to capability rows, not to marketing adjectives.

## When k3s Fits—and When It Does Not

k3s shines when the problem statement includes footprint, bootstrap time, or bare-metal ergonomics. If you need Kubernetes on ARM64 industrial gateways, on a CI runner that must start in seconds, on a homelab Intel NUC, or on an air-gapped appliance that cannot pull from registries during install, the integrated binary removes days of assembly work. Scenarios with intermittent WAN benefit because a single-server SQLite cluster can run local caches and queue agents without maintaining a separate etcd fleet. Teams already standardized on SUSE or Rancher downstream tooling also gain a straight integration path, though this module stays distribution-neutral and does not require Rancher Manager.

k3s is the wrong default when you need maximum control-plane isolation without bundled ingress, when your security policy forbids any default controllers you did not vet, or when you already operate large etcd or SQL fleets with full-time DBAs who prefer kubeadm's explicit separation. It is also a weak match for multi-tenant clusters where hard multi-tenancy depends on cloud-provider integrations k3s deliberately removed. None of those are k3s bugs—they are packaging tradeoffs. The senior engineer move is to write down constraints first, then pick the distribution row that matches, rather than starting from a logo.

Regulated environments should pay extra attention to datastore mode and backup evidence. SQLite on a single server is easy to reason about but offers no control-plane redundancy; embedded etcd adds quorum maintenance; external SQL shifts liability to a database team already under audit. Document the mode in architecture decision records, snapshot regularly, and test restore quarterly—k3s makes clusters cheap to create, which tempts teams to skip recovery drills until they need them.

## k3s Architecture

At the process level, k3s collapses what kubeadm spreads across packages into one `k3s` executable that can run in `server` mode (control plane plus optional worker), `agent` mode (worker only), or both on a single node for development. The server embeds kube-apiserver, kube-controller-manager, kube-scheduler, the k3s tunnel proxy for agent connectivity, and the ServiceLB controller. Both server and agent run kubelet, kube-proxy, and containerd. Bundled cluster services—CoreDNS, Traefik, local-path-provisioner, metrics-server, the Helm controller, Flannel CNI, and kube-router's network policy controller—ship as static pods or embedded controllers depending on the component.

The architectural bet is integration over modularity at install time. Instead of prompting you to choose a CNI before the API server starts, k3s brings up a working pod network so beginners and automation pipelines see `Running` pods immediately. Instead of leaving `type: LoadBalancer` broken on bare metal, ServiceLB allocates node ports via a DaemonSet. Each bundled component is disable-able with `--disable <component>` so advanced teams can substitute MetalLB, nginx ingress, or a corporate-standard SQL datastore without switching distributions.

Recent upstream releases also bundle optional subsystems such as the Helm controller (for HelmChart CRDs), Spegel for distributed image mirroring in multi-node clusters, and host utilities like iptables pinned to known-good versions when distribution packages ship broken nftables backends. You do not need to enable or configure these on day one, but knowing they exist explains disk layout under `/var/lib/rancher/k3s` and helps when security scanners flag additional listening processes on worker nodes.

The datastore layer is the other major architectural fork. Single-server installs default to SQLite accessed through kine, which presents an etcd-compatible API to the Kubernetes storage layer while persisting rows in a local file. That keeps memory and disk overhead minimal for edge appliances. When you need control-plane HA, you either promote to embedded etcd across an odd number of server nodes (`--cluster-init` on the first, `--server` joins on the rest) or point all servers at an external MySQL, PostgreSQL, or etcd endpoint via `--datastore-endpoint`. The CAP tradeoff is familiar: SQLite is simple but single-writer; embedded etcd adds quorum maintenance; external SQL leverages existing DBA tooling but introduces network dependency for every API write.

```
k3s ARCHITECTURE DEEP DIVE
─────────────────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────────────────┐
│                          k3s Server Node                                    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      k3s Binary (~60MB)                             │   │
│  │                                                                     │   │
│  │  ┌──────────────────── Control Plane ───────────────────────┐      │   │
│  │  │                                                          │      │   │
│  │  │  kube-apiserver    kube-controller-manager    kube-scheduler    │   │
│  │  │  ─────────────────────────────────────────────────────────────  │   │
│  │  │  tunnel-proxy (server)    service-lb-controller                 │   │
│  │  │                                                          │      │   │
│  │  └──────────────────────────────────────────────────────────┘      │   │
│  │                                                                     │   │
│  │  ┌──────────────────── Node Components ─────────────────────┐      │   │
│  │  │                                                          │      │   │
│  │  │  kubelet    kube-proxy    containerd                            │   │
│  │  │                                                          │      │   │
│  │  └──────────────────────────────────────────────────────────┘      │   │
│  │                                                                     │   │
│  │  ┌──────────────────── Bundled Components ──────────────────┐      │   │
│  │  │                                                          │      │   │
│  │  │  Traefik        CoreDNS       Local Path      Flannel          │   │
│  │  │  (Ingress)      (DNS)         (Storage)       (CNI)            │   │
│  │  │                                                          │      │   │
│  │  │  ServiceLB      Metrics       Network Policy                    │   │
│  │  │  (Load Balancer) Server       Controller                        │   │
│  │  │                                                          │      │   │
│  │  └──────────────────────────────────────────────────────────┘      │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                      Datastore Options                                │ │
│  │                                                                       │ │
│  │  SQLite (default)  │  etcd (HA)  │  MySQL  │  PostgreSQL             │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│    k3s Agent Node   │   │    k3s Agent Node   │   │    k3s Agent Node   │
│                     │   │                     │   │                     │
│  ┌───────────────┐  │   │  ┌───────────────┐  │   │  ┌───────────────┐  │
│  │ k3s Binary    │  │   │  │ k3s Binary    │  │   │  │ k3s Binary    │  │
│  │               │  │   │  │               │  │   │  │               │  │
│  │ kubelet       │  │   │  │ kubelet       │  │   │  │ kubelet       │  │
│  │ kube-proxy    │  │   │  │ kube-proxy    │  │   │  │ kube-proxy    │  │
│  │ containerd    │  │   │  │ containerd    │  │   │  │ containerd    │  │
│  │ flannel       │  │   │  │ flannel       │  │   │  │ flannel       │  │
│  └───────────────┘  │   │  └───────────────┘  │   │  └───────────────┘  │
│                     │   │                     │   │                     │
└─────────────────────┘   └─────────────────────┘   └─────────────────────┘

WHAT'S DIFFERENT FROM UPSTREAM K8S:
─────────────────────────────────────────────────────────────────────────────

Removed:
✗ Legacy, alpha, non-default features
✗ In-tree cloud providers
✗ In-tree storage drivers
✗ Docker (uses containerd directly)

Added:
✓ SQLite datastore (single node)
✓ Embedded etcd (HA mode)
✓ Tunnel proxy (agent communication)
✓ ServiceLB (bare-metal load balancer)
✓ Local Path Provisioner
✓ Traefik Ingress Controller
✓ Flannel CNI (by default)
```

The diagram above is a reference map, not an inventory you must memorize. When troubleshooting, you will care most about three flows: how the API persists objects (datastore row), how agents maintain websocket tunnels to servers (tunnel proxy and embedded agent load balancer on port 6443), and which bundled DaemonSets answer DNS, ingress, and LoadBalancer requests. Removing in-tree cloud providers and legacy storage drivers shrinks the binary and eliminates code paths that edge clusters never exercise; that is a deliberate scope cut, not a missing feature you should patch back in manually.

## Installing k3s

Installation is where distribution opinions become concrete. The official path is a curl-piped script at `get.k3s.io` that downloads the release binary, installs a systemd (or openrc) unit, and writes configuration to `/etc/rancher/k3s/`. You can also place the binary directly from GitHub releases for quick tests. The script is idempotent enough for lab use but remember that re-running it without re-supplying prior flags can overwrite environment variables you set on the first pass—persistent intent belongs in `/etc/rancher/k3s/config.yaml` for production.

### Single Node Installation

Single-node mode is the fastest on-ramp: one `k3s server` process acts as control plane and worker, SQLite holds API state, and bundled components come up automatically. This is ideal for CI namespaces, laptop labs, and true single-appliance edge deployments where control-plane outage equals site outage anyway. The commands below install, verify the service, and copy kubeconfig so a non-root user can run kubectl without prefixing `k3s` every time.

```bash
# Install k3s server (includes agent)
curl -sfL https://get.k3s.io | sh -

# Check service status
sudo systemctl status k3s

# Get kubeconfig
sudo cat /etc/rancher/k3s/k3s.yaml

# Or use k3s kubectl directly
sudo k3s kubectl get nodes

# Copy kubeconfig for regular user
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER ~/.kube/config

# Now use regular kubectl
kubectl get nodes
```

After `kubectl get nodes` shows `Ready`, explore `kubectl get pods -A` to see bundled components in `kube-system`. You should find CoreDNS, Traefik (unless disabled), metrics-server, local-path-provisioner, and the Flannel DaemonSet. This is your checklist that the distribution finished bootstrapping—not just that the API server answered.

### Installation Options

Environment variables prefixed with `K3S_` and the `INSTALL_K3S_EXEC` string pass through to the systemd unit, which matters when you automate with cloud-init or Ansible. Common first-day tweaks include pinning a version for reproducibility, disabling Traefik when your platform standard is ingress-nginx, switching Flannel backends, enabling secrets encryption at rest, and relocating `--data-dir` to a larger disk partition on edge appliances with small root volumes.

```bash
# Install specific version
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="v1.28.5+k3s1" sh -

# Skip bundled components
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--disable traefik --disable servicelb" sh -

# Use different CNI
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--flannel-backend=none" sh -

# Enable secrets encryption
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--secrets-encryption" sh -

# Custom data directory
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--data-dir=/opt/k3s" sh -
```

`--secrets-encryption` wraps etcd/SQLite secrets at rest with a key you must back up—losing the key means losing access to sealed Secret objects. `--flannel-backend=none` is the escape hatch for bringing Cilium or Calico, but you must install a CNI before workloads schedule. Treat each flag as a contract: disabling defaults without provisioning replacements produces a cluster that is "up" yet unusable.

### Multi-Node Cluster

Multi-node topology splits responsibilities: servers run the control plane and may also schedule pods; agents run only kubelet and containerd and register to servers over a websocket tunnel maintained by an embedded client-side load balancer. Agents do not need outbound Internet if they can reach the server API on 6443, which matters for restricted edge VLANs. You will need the node token from the first server and a stable `K3S_URL` pointing at any server IP or, in HA setups, a load-balanced API address.

```bash
# Install server and get token
curl -sfL https://get.k3s.io | sh -

# Get the node token (needed for agents)
sudo cat /var/lib/rancher/k3s/server/node-token
```

**On each agent node:**

```bash
# Replace K3S_URL and K3S_TOKEN with actual values
curl -sfL https://get.k3s.io | K3S_URL=https://server-ip:6443 K3S_TOKEN=your-node-token sh -

# Verify agent joined
kubectl get nodes
```

When the agent appears as `Ready`, confirm it picked up pod CIDR allocation from Flannel and that `/etc/rancher/node/password` exists locally—k3s uses per-node password secrets in `kube-system` to prevent token replay attacks. If you rebuild an agent without deleting the old Node object, registration may fail until you remove the stale node and its `.node-password.k3s` secret.

### High Availability Setup

Production control-plane HA requires thinking about two separate problems: API availability (can kubectl and controllers reach a live apiserver?) and datastore durability (can object state survive server loss?). k3s addresses both with either embedded etcd across three or more server nodes or an external SQL/etcd cluster referenced by every server. Agents should always target a fixed registration address—DNS name or load balancer VIP—so joins survive the loss of any single server IP.

```
HA k3s ARCHITECTURE
─────────────────────────────────────────────────────────────────────────────

           ┌─────────────────────────────────────────┐
           │          Load Balancer                  │
           │     (HAProxy / cloud LB / DNS RR)       │
           │         api.k3s.example.com:6443        │
           └─────────────────────┬───────────────────┘
                                 │
       ┌─────────────────────────┼─────────────────────────┐
       │                         │                         │
       ▼                         ▼                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Server 1      │     │   Server 2      │     │   Server 3      │
│   (init node)   │◄───▶│                 │◄───▶│                 │
│                 │     │                 │     │                 │
│  ┌───────────┐  │     │  ┌───────────┐  │     │  ┌───────────┐  │
│  │ embedded  │◄─┼─────┼─▶│ embedded  │◄─┼─────┼─▶│ embedded  │  │
│  │   etcd    │  │     │  │   etcd    │  │     │  │   etcd    │  │
│  └───────────┘  │     │  └───────────┘  │     │  └───────────┘  │
└─────────────────┘     └─────────────────┘     └─────────────────┘

Option A: Embedded etcd (recommended for simplicity)
Option B: External datastore (MySQL, PostgreSQL, etcd)
```

**Using embedded etcd (recommended):**

Embedded etcd runs colocated on server nodes, so every server you add is simultaneously an apiserver host and an etcd member. Plan odd counts—three is the usual minimum—to maintain quorum during one failure. The first server must pass `--cluster-init` exactly once per cluster; subsequent servers use `--server` pointing at any existing member and share the same join token file located at `/var/lib/rancher/k3s/server/token` after initialization. Front the API with a TCP load balancer or DNS round-robin only after all members share consistent `tls-san` entries for the VIP hostname.

**Using external datastore:**

External datastores decouple API availability from etcd embedded on k3s nodes. Every server process connects to the same `datastore-endpoint`, which can be a managed MySQL or PostgreSQL cluster your organization already backs up. This pattern suits teams with DBA runbooks but adds network dependency: if the SQL endpoint is unreachable, the Kubernetes API stops accepting writes even when nodes are healthy. Match TLS options (`datastore-cafile`, cert/key files) to your database provider's requirements and store credentials in environment files with restrictive permissions rather than shell history.

```bash
# First server - initialize cluster
curl -sfL https://get.k3s.io | sh -s - server \
  --cluster-init \
  --tls-san=api.k3s.example.com

# Get token
sudo cat /var/lib/rancher/k3s/server/token

# Second and third servers - join cluster
curl -sfL https://get.k3s.io | sh -s - server \
  --server https://first-server-ip:6443 \
  --token <token-from-first-server> \
  --tls-san=api.k3s.example.com
```

**Using external datastore:**

```bash
# All servers point to external datastore
curl -sfL https://get.k3s.io | sh -s - server \
  --datastore-endpoint="mysql://user:password@tcp(host:3306)/k3s" \
  --tls-san=api.k3s.example.com

# Or PostgreSQL
curl -sfL https://get.k3s.io | sh -s - server \
  --datastore-endpoint="postgres://user:password@host:5432/k3s?sslmode=disable" \
  --tls-san=api.k3s.example.com
```

Embedded etcd is the path of least resistance when you do not already operate MySQL or PostgreSQL for other systems. External SQL shines when compliance mandates an existing HA database fleet or when backup tooling already covers Postgres. Either way, always include every client-facing API hostname and load balancer IP in `--tls-san` or `tls-san:` config entries—omitting the SAN is the most common cause of `x509: certificate is valid for ...` errors after you front servers with HAProxy.

### How Agent Registration and kine Fit Together

Two mechanisms confuse newcomers but explain why k3s "just works" on flaky networks: agent registration over a supervised websocket tunnel, and kine as the etcd API shim over SQL. When an agent starts, it opens a tunnel to the server address you provided, seeds an internal load balancer with that endpoint, then learns additional apiserver addresses from the `kubernetes` Endpoints object in `default`. The agent-side load balancer keeps a persistent connection pool so brief server outages do not require manual restarts—this is why a stable `K3S_URL` pointing at a VIP or DNS name matters more than any single server IP.

kine, meanwhile, lets the Kubernetes storage interface speak etcd3 semantics while persisting to SQLite or SQL rows. That is how the same apiserver binary can run on a Raspberry Pi with a local file and later migrate to a three-node etcd quorum without swapping distributions. External SQL mode introduces operational requirements: prepared statement support (PgBouncer needs care), schema migrations when revision counters approach two-billion row limits on legacy databases, and network latency on every write. Monitor `resourceVersion` in API list responses during upgrades—large jumps are normal; stalls near 2147483647 on old schemas require setting `KINE_SCHEMA_MIGRATION` per known-issues documentation.

## k3s Configuration

Day-two configuration merges three surfaces: the install-time environment, `/etc/rancher/k3s/config.yaml` (plus drop-ins in `config.yaml.d/`), and CLI flags for one-off changes. Critical server flags—`cluster-cidr`, `service-cidr`, `disable` entries, and datastore endpoints—must match across all servers or joins fail with `critical configuration value mismatch`. Treat server config like Terraform: the same inputs on every control-plane node, version-controlled in Git, applied before you declare the cluster production-ready.

### Server Configuration File

```yaml
# /etc/rancher/k3s/config.yaml
write-kubeconfig-mode: "0644"
tls-san:
  - "api.k3s.example.com"
  - "192.168.1.100"
cluster-cidr: "10.42.0.0/16"
service-cidr: "10.43.0.0/16"
cluster-dns: "10.43.0.10"
flannel-backend: "vxlan"
disable:
  - traefik  # Use your own ingress controller
secrets-encryption: true
kube-apiserver-arg:
  - "enable-admission-plugins=NodeRestriction,PodSecurity"
kubelet-arg:
  - "max-pods=250"
```

The sample enables NodeRestriction plus the Pod Security admission plugin (replacing the removed PodSecurityPolicy admission plugin). Tune `max-pods` against your CIDR size and hardware—edge nodes with 512MB RAM cannot honor 250 pods even if the kubelet accepts the setting. After editing config, restart `k3s` (server) or `k3s-agent` (agent) and verify with `kubectl get nodes -o wide` that labels and taints applied.

### Agent Configuration File

Agents only need server URL, token, and optional labels/taints. Keep agent config minimal: pushing control-plane flags to agents is a common copy-paste mistake that silently does nothing while giving a false sense of security hardening.

```yaml
# /etc/rancher/k3s/config.yaml (on agent nodes)
server: https://api.k3s.example.com:6443
token: your-node-token
node-label:
  - "node-type=worker"
  - "region=us-east"
kubelet-arg:
  - "max-pods=250"
```

### Disabling Default Components

Disabling bundled components is how you de-couple k3s from its defaults without switching distributions. Platform teams often disable Traefik and ServiceLB simultaneously, then install ingress-nginx plus MetalLB—or rely on an upstream hardware load balancer—to match data-center standards. Document the disable list in Git; upgrading k3s without preserving `--disable` flags resurrects Traefik and can hijack port 80 unexpectedly.

```bash
# Disable all optional components
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC=" \
  --disable traefik \
  --disable servicelb \
  --disable local-storage \
  --disable metrics-server \
  " sh -

# Then install your preferred alternatives
# Example: Install nginx-ingress instead of Traefik
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/baremetal/deploy.yaml
```

## Storage Options

Storage on k3s follows the same Kubernetes object model—PersistentVolumeClaims, StorageClasses, and dynamic provisioners—but edge clusters rarely have SAN arrays waiting. The default local-path-provisioner creates hostPath-backed volumes on the node where the pod landed, which is perfect for single-replica caches and dangerous for data that must survive node replacement. Understanding when local-path is "good enough" versus when you need replicated storage separates hobby clusters from production edge.

### Local Path Provisioner (Default)

Local-path is synchronous, simple, and node-local. ReadWriteOnce volumes bind to whichever node scheduled the pod, so StatefulSets with one replica work; multi-replica databases do not unless you accept split-brain risk. The PVC below requests the default `local-path` StorageClass and mounts into an nginx pod for demonstration—swap the image for your application once the mechanics feel familiar.

```yaml
# PVC using local-path StorageClass
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-data
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: local-path
  resources:
    requests:
      storage: 1Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: my-data
```

Data lives under `/var/lib/rancher/k3s/storage` on the scheduling node. Back up those host directories or use `k3s etcd-snapshot` for control-plane state—PVC data is not included in etcd snapshots. Before node maintenance, drain workloads and confirm no local-path PVCs remain bound to that node.

### Longhorn (Distributed Storage)

When you need replicated block storage across agents, Longhorn is a common additive choice: it runs entirely inside the cluster, suits small-footprint edge nodes, and exposes a StorageClass you can mark default. Installing Longhorn increases CPU and RAM overhead—budget accordingly on 2GB nodes. The commands below deploy Longhorn, wait for pods, create a `longhorn` StorageClass, and demote local-path from default.

```bash
# Install Longhorn
kubectl apply -f https://raw.githubusercontent.com/longhorn/longhorn/master/deploy/longhorn.yaml

# Wait for deployment
kubectl -n longhorn-system get pods -w

# Create StorageClass
cat <<EOF | kubectl apply -f -
kind: StorageClass
apiVersion: storage.k8s.io/v1
metadata:
  name: longhorn
provisioner: driver.longhorn.io
parameters:
  numberOfReplicas: "2"
  staleReplicaTimeout: "2880"
  fromBackup: ""
EOF

# Make Longhorn the default
kubectl patch storageclass local-path -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"false"}}}'
kubectl patch storageclass longhorn -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```

## Networking

Networking on k3s is where bundled opinions matter most for bare-metal and edge sites without cloud load balancers. Flannel provides overlay pod connectivity by default; ServiceLB satisfies `type: LoadBalancer` by launching a DaemonSet that binds host ports; Traefik terminates HTTP ingress rules; and kube-router enforces NetworkPolicy when you create policy objects. You can replace any layer, but the defaults exist so a freshly installed cluster can expose a Service and an Ingress without third-party charts.

### Service Load Balancer (ServiceLB)

Cloud providers implement LoadBalancer Services by provisioning external IPs automatically. On a factory-floor PC or Raspberry Pi cluster, no such integration exists—yet many Helm charts assume `kubectl get svc` will show an `EXTERNAL-IP`. ServiceLB closes that gap by listening on high node ports (or configured ranges) and routing traffic to pod endpoints. It is not a replacement for hardware load balancers in large data centers, but it prevents chart authors from hard-coding NodePort workarounds at every edge site.

```yaml
# Exposes Service on node's external IP
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8080
  selector:
    app: my-app
```

ServiceLB creates a DaemonSet that listens on the node ports:

```bash
# Check LoadBalancer services
kubectl get svc

# See the ServiceLB pods
kubectl -n kube-system get pods | grep svclb
```

DaemonSet pods named `svclb-*` appear per service. If you plan to use MetalLB or an external LB instead, disable ServiceLB at install time to avoid port conflicts on 80/443.

### Traefik Ingress Controller

Traefik watches Ingress and IngressRoute objects and terminates HTTP traffic on the node. Many teams disable it in favor of ingress-nginx or Envoy Gateway to align with corporate ingress standards. When you keep Traefik, annotate routes explicitly—entrypoints `web` and `websecure` map to ports Traefik opens by default, and missing annotations manifest as 404s that look like application bugs.

```yaml
# Ingress using Traefik
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
  annotations:
    traefik.ingress.kubernetes.io/router.entrypoints: web,websecure
spec:
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-service
            port:
              number: 80
```

### Network Policies

NetworkPolicy is off by default in many minimal clusters, but k3s ships kube-router's controller so policies take effect once you create objects. Policies are your edge safety net when compromised workloads attempt lateral movement over the pod network. Start restrictive: default-deny ingress, then allow labeled frontends to reach backends on specific ports.

```yaml
# Allow only frontend to access backend
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-policy
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
```

## Air-Gapped Installation

Air-gapped environments—defense networks, isolated factory VLANs, and compliance enclaves—cannot pull images or binaries at install time. k3s supports offline installation by prefetching the release binary, the compressed air-gap image bundle (`k3s-airgap-images-$ARCH.tar.zst`), and the install script on a bastion with Internet access, then transferring artifacts to target nodes. You must also ensure nodes have a default route (even a dummy route) so k3s can auto-detect the primary IP, per upstream documentation.

The workflow below mirrors the three-step upstream guide: stage images under `/var/lib/rancher/k3s/agent/images/`, place the binary in `/usr/local/bin/k3s`, and run `INSTALL_K3S_SKIP_DOWNLOAD=true` so the script configures systemd without reaching GitHub. SELinux-enabled hosts additionally need the `k3s-selinux` RPM available locally.

```bash
# On a machine with internet access:

# 1. Download k3s binary
wget https://github.com/k3s-io/k3s/releases/download/v1.28.5+k3s1/k3s

# 2. Download images archive
wget https://github.com/k3s-io/k3s/releases/download/v1.28.5+k3s1/k3s-airgap-images-amd64.tar.gz

# 3. Download install script
wget https://get.k3s.io -O install.sh

# Transfer all files to air-gapped machine, then:

# 4. Install images
sudo mkdir -p /var/lib/rancher/k3s/agent/images/
sudo cp k3s-airgap-images-amd64.tar.gz /var/lib/rancher/k3s/agent/images/

# 5. Install binary
sudo cp k3s /usr/local/bin/
sudo chmod +x /usr/local/bin/k3s

# 6. Run install script
chmod +x install.sh
INSTALL_K3S_SKIP_DOWNLOAD=true ./install.sh
```

After install, verify bundled images loaded with `sudo k3s ctr images list | head` before deploying workloads. Plan upgrades the same way: prefetch the next release's image tarball and binary before disconnecting from your transfer network. Operators in regulated sectors should checksum artifacts on the bastion and again on the isolated node to detect transfer corruption, then record versions in a change ticket so auditors can correlate cluster state with approved binaries.

## Upgrading k3s

Kubernetes upgrades are never "just bump the binary"—you must respect skew policies between control plane and kubelet, snapshot etcd/SQL state, and roll nodes in an order that preserves quorum. k3s simplifies packaging but not the semantics: server nodes upgrade before agents, and embedded-etcd clusters need at least one healthy member throughout.

### Manual Upgrade

Manual upgrades suit lab clusters and environments that forbid in-cluster controllers. Pin `INSTALL_K3S_VERSION` to a tested release, run the install script on each node, and restart services. Always read the release notes for Kubernetes minor bumps—admission defaults, API removals, and CNI flags change even when the k3s wrapper feels familiar.

```bash
# Check current version
k3s --version

# Download new version
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="v1.29.0+k3s1" sh -

# Restart service
sudo systemctl restart k3s

# Verify upgrade
k3s --version
kubectl get nodes
```

### Automated Upgrades with system-upgrade-controller

Fleet operators managing dozens of edge clusters rarely SSH to each node for patch Tuesday. Rancher's system-upgrade-controller watches `Plan` objects and cordons, drains, and upgrades nodes according to concurrency rules you define. The server plan targets control-plane nodes first; the agent plan waits on a `prepare` hook so servers finish before workers. Channels like `https://update.k3s.io/v1-release/channels/stable` track tested k3s releases—pin a specific channel in regulated environments instead of floating to latest automatically.

```bash
# Install System Upgrade Controller
kubectl apply -f https://github.com/rancher/system-upgrade-controller/releases/latest/download/system-upgrade-controller.yaml

# Create upgrade plan for servers
cat <<EOF | kubectl apply -f -
apiVersion: upgrade.cattle.io/v1
kind: Plan
metadata:
  name: server-plan
  namespace: system-upgrade
spec:
  concurrency: 1
  cordon: true
  nodeSelector:
    matchExpressions:
    - key: node-role.kubernetes.io/control-plane
      operator: In
      values:
      - "true"
  serviceAccountName: system-upgrade
  upgrade:
    image: rancher/k3s-upgrade
  channel: https://update.k3s.io/v1-release/channels/stable
EOF

# Create upgrade plan for agents
cat <<EOF | kubectl apply -f -
apiVersion: upgrade.cattle.io/v1
kind: Plan
metadata:
  name: agent-plan
  namespace: system-upgrade
spec:
  concurrency: 2
  cordon: true
  nodeSelector:
    matchExpressions:
    - key: node-role.kubernetes.io/control-plane
      operator: DoesNotExist
  prepare:
    args:
    - prepare
    - server-plan
    image: rancher/k3s-upgrade
  serviceAccountName: system-upgrade
  upgrade:
    image: rancher/k3s-upgrade
  channel: https://update.k3s.io/v1-release/channels/stable
EOF
```

Test upgrade plans in a staging cluster that mirrors production datastore mode (SQLite vs embedded etcd vs external SQL). A Plan that works on single-node SQLite may need concurrency `1` on etcd members to avoid quorum loss.

## Monitoring k3s

Observability splits into Kubernetes-native signals (pod logs, events, metrics-server summaries) and host-level signals (disk space for SQLite/etcd, systemd unit restarts, image pull errors in air-gap). Edge clusters fail quietly when `/var/lib/rancher` fills or when swap causes kubelet thrashing—monitor those paths aggressively because remote hands are scarce.

### Built-in Metrics Server

metrics-server ships enabled, powering `kubectl top` without extra Helm charts. It is sufficient for capacity conversations ("this node has 200m CPU left") but not a long-term metrics backend. Export Prometheus scrapes when you need retention, alerting, and dashboards.

```bash
# Check resource usage
kubectl top nodes
kubectl top pods -A

# Get detailed node metrics
kubectl describe node | grep -A 10 "Allocated resources"
```

### Prometheus Integration

Scrape the kube-apiserver `/metrics` endpoint with appropriate TLS and service account tokens when you centralize monitoring. Agent kubelet endpoints on 10250 follow the same pattern. Treat `insecure_skip_verify: true` as a lab-only shortcut—production scrapers should trust the cluster CA.

```yaml
# prometheus-scrape-config.yaml
# k3s exposes metrics on /metrics
- job_name: 'k3s-server'
  static_configs:
    - targets:
      - 'server-ip:6443'
  scheme: https
  tls_config:
    insecure_skip_verify: true  # Lab only—use proper CA in production
  bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token

- job_name: 'k3s-agent'
  static_configs:
    - targets:
      - 'agent-ip:10250'
  scheme: https
  tls_config:
    insecure_skip_verify: true  # Lab only—use proper CA in production
```

## Hypothetical scenario: The Retail Edge

The following narrative is illustrative—not a cited production incident. It shows how distribution choices play out when constraints collide.

A retail platform team needed Kubernetes at thousands of store locations. Each site had modest hardware (roughly 8GB RAM and two to four cores), unreliable WAN links, and no resident Linux administrator. They needed inventory APIs, point-of-sale integrations, and a local cache that survived overnight upstream outages. A kubeadm design with three control-plane nodes and external etcd never fit the hardware budget or staffing model.

k3s offered a different contract: one server process per store with SQLite or embedded etcd if they later clustered regional hubs, bundled Traefik for ingress, local-path for cache volumes, and ServiceLB so Helm charts requesting LoadBalancer Services worked without cloud integration. Fleet management—whether Rancher Fleet, GitOps agents, or custom Ansible—pushed manifests over intermittent links, while system-upgrade-controller applied patch channels during maintenance windows.

The lesson is structural: k3s did not make Kubernetes magically smaller in capability—it made the **packaging** small enough to colocate with store applications. Success still required backup strategy for local-path data, realistic pod resource requests, and a plan for quorum if they promoted sites to multi-server HA. Distribution choice removed bootstrap friction; engineering discipline still determined uptime.

Platform engineers reviewing a similar proposal today should ask for evidence on datastore mode per site, a diagram showing where ServiceLB ports are exposed on store firewalls, and a GitOps or fleet tool that tolerates offline reconciliation. Those questions apply to any lightweight distribution—the technology is approachable, but production edge still punishes vague operations assumptions.

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Using default token | Security vulnerability | Generate unique tokens per cluster |
| Not setting --tls-san | Certificate errors with LB | Include all access IPs/hostnames |
| Ignoring storage | Data loss on node failure | Use Longhorn or external storage |
| No HA setup | SPOF on single server | Deploy 3+ server nodes for production |
| Skipping upgrades | Security vulnerabilities | Use system-upgrade-controller |
| Not disabling swap | Kubelet issues | Disable swap on all nodes |
| Wrong flannel backend | Performance issues | Use wireguard for encrypted, vxlan for simple |
| No backup strategy | Cluster unrecoverable | Backup etcd/SQLite regularly |

The table above captures failure modes we see repeatedly when teams treat k3s like a disposable dev cluster but run production payloads on it. Tokens are not secrets you can leave at defaults—generate cluster-unique values and rotate them when staff leave. TLS SANs matter the moment you put a load balancer or DNS name in front of the API. Storage and backups are the silent killers: local-path data never enters etcd snapshots, so you need a filesystem or volume backup strategy alongside `k3s etcd-snapshot save` for control-plane recovery.

## Quiz

The questions below test whether you understand k3s as a packaging model, not just as a sequence of curl commands. Read each answer fully—it explains the tradeoff behind the correct choice.

<details>
<summary>1. What does k3s remove from upstream Kubernetes?</summary>

**Answer**: k3s removes: (1) Legacy, alpha, and non-default features, (2) In-tree cloud providers (AWS, GCP, Azure), (3) In-tree storage drivers, (4) Docker (uses containerd directly). These removals reduce the binary size by ~90% while maintaining full Kubernetes API compatibility.
</details>

<details>
<summary>2. What datastore options does k3s support?</summary>

**Answer**: k3s supports: (1) SQLite (default for single node), (2) Embedded etcd (for HA with --cluster-init), (3) External etcd cluster, (4) MySQL, (5) PostgreSQL. For single-node edge deployments, SQLite is perfect. For HA, embedded etcd is recommended for simplicity.
</details>

<details>
<summary>3. How do you join an agent node to an existing k3s cluster?</summary>

**Answer**: On the agent node, run: `curl -sfL https://get.k3s.io | K3S_URL=https://server:6443 K3S_TOKEN=<token> sh -`. The token is found at `/var/lib/rancher/k3s/server/node-token` on the server. The agent will automatically register with the cluster.
</details>

<details>
<summary>4. What is ServiceLB and why is it included in k3s?</summary>

**Answer**: ServiceLB (formerly Klipper) is a bare-metal load balancer included in k3s. When you create a LoadBalancer service, ServiceLB creates a DaemonSet that listens on the requested ports on each node. This provides LoadBalancer functionality without cloud provider integration or MetalLB—essential for edge deployments.
</details>

<details>
<summary>5. How do you disable bundled components in k3s?</summary>

**Answer**: Use the `--disable` flag: `k3s server --disable traefik --disable servicelb --disable local-storage`. Or in config.yaml: `disable: [traefik, servicelb, local-storage]`. This lets you use alternative components like nginx-ingress or MetalLB. Remember to install replacements before workloads request Ingress or LoadBalancer objects, otherwise Kubernetes will accept manifests that never receive external connectivity.
</details>

<details>
<summary>6. What's the difference between k3s server and k3s agent?</summary>

**Answer**: k3s server runs the control plane (API server, controller manager, scheduler) plus node components (kubelet, containerd). k3s agent runs only node components and connects to the server for cluster coordination. In single-node mode, the server is both control plane and worker. In multi-node mode, agents are dedicated workers.
</details>

<details>
<summary>7. How do you set up HA k3s with embedded etcd?</summary>

**Answer**: First server: `k3s server --cluster-init`. Get token from `/var/lib/rancher/k3s/server/token`. Additional servers: `k3s server --server https://first-server:6443 --token <token>`. Requires odd number of servers (3, 5, 7) for etcd quorum. All servers run both control plane and embedded etcd.
</details>

<details>
<summary>8. How do you perform air-gapped installation of k3s?</summary>

**Answer**: Download the k3s binary, airgap images tarball, and install script on an internet-connected machine. Transfer to air-gapped machine. Place images tarball in `/var/lib/rancher/k3s/agent/images/`. Place binary in `/usr/local/bin/k3s`. Run install script with `INSTALL_K3S_SKIP_DOWNLOAD=true`.
</details>

## Hands-On Exercise: Deploy HA k3s Cluster

This exercise walks through a realistic HA bootstrap: three server nodes with embedded etcd, two agents, a sample application exposed via ServiceLB, and a control-plane failure drill. You will need roughly 12GB of free RAM if you run all five Multipass VMs simultaneously; reduce agent count if your laptop is tighter. The goal is muscle memory for join tokens, TLS SAN planning, and verifying that etcd quorum survives losing one server.

### Objective
Deploy a high-availability k3s cluster with 3 server nodes and test failover.

### Environment Setup

Multipass provides Ubuntu VMs with minimal setup friction on macOS and Linux. If you already have five Linux machines on a flat network, substitute their IP addresses and skip Multipass entirely—the k3s commands are identical.

```bash
# Install Multipass (macOS)
brew install multipass

# Or on Ubuntu
sudo snap install multipass

# Create 3 server VMs
for i in 1 2 3; do
  multipass launch --name k3s-server-$i --cpus 2 --memory 2G --disk 10G
done

# Create 2 agent VMs
for i in 1 2; do
  multipass launch --name k3s-agent-$i --cpus 2 --memory 2G --disk 10G
done

# List VMs and get IPs
multipass list
```

### Step 1: Initialize First Server

The first server must run with `--cluster-init` so embedded etcd bootstraps a new cluster. Capture both the join token and the server IP before closing the shell—you will paste them multiple times. Including the primary IP in `--tls-san` prevents certificate errors when agents join by IP rather than hostname.

```bash
# SSH into first server
multipass shell k3s-server-1

# Install k3s with cluster-init
curl -sfL https://get.k3s.io | sh -s - server \
  --cluster-init \
  --tls-san=$(hostname -I | awk '{print $1}')

# Get the join token
sudo cat /var/lib/rancher/k3s/server/token

# Get server IP
hostname -I | awk '{print $1}'

# Exit shell
exit
```

### Step 2: Join Additional Servers

Servers two and three join the etcd quorum with `k3s server --server https://FIRST:6443 --token TOKEN`. They run both control-plane components and etcd members—this is not an agent-only join. Wait until `kubectl get nodes` on any server shows all three servers `Ready` before proceeding to agents.

```bash
# Get SERVER_IP and TOKEN from step 1, then:

# Server 2
multipass shell k3s-server-2
curl -sfL https://get.k3s.io | sh -s - server \
  --server https://SERVER_IP:6443 \
  --token TOKEN
exit

# Server 3
multipass shell k3s-server-3
curl -sfL https://get.k3s.io | sh -s - server \
  --server https://SERVER_IP:6443 \
  --token TOKEN
exit
```

### Step 3: Join Agent Nodes

Agents use the lighter `K3S_URL` + `K3S_TOKEN` install path without `--cluster-init`. They should land on servers two and three for workload scheduling while servers carry control-plane taints. If pods stay Pending, check that Flannel pods are Running and that no NetworkPolicy accidentally blocks CNI traffic.

```bash
# Agent 1
multipass shell k3s-agent-1
curl -sfL https://get.k3s.io | K3S_URL=https://SERVER_IP:6443 K3S_TOKEN=TOKEN sh -
exit

# Agent 2
multipass shell k3s-agent-2
curl -sfL https://get.k3s.io | K3S_URL=https://SERVER_IP:6443 K3S_TOKEN=TOKEN sh -
exit
```

### Step 4: Verify Cluster

Verification is more than a node list: confirm etcd membership with `k3s etcd-snapshot ls` and inspect `kube-system` for CoreDNS, Traefik, metrics-server, and svclb pods. A healthy HA cluster shows five nodes and three etcd members with no CrashLoopBackOff in system namespaces.

```bash
# From server-1
multipass shell k3s-server-1

# Check all nodes
sudo k3s kubectl get nodes

# Check etcd members
sudo k3s etcd-snapshot ls

# Check system pods
sudo k3s kubectl get pods -A

exit
```

### Step 5: Deploy Test Application

Creating a Deployment with three replicas tests scheduling across agents. Exposing it as `type: LoadBalancer` exercises ServiceLB—expect an EXTERNAL-IP that is actually a node IP plus high port. Note which node hosts each pod with `-o wide` so you can reason about local-path affinity later.

```bash
multipass shell k3s-server-1

# Create deployment
sudo k3s kubectl create deployment nginx --image=nginx --replicas=3

# Expose with LoadBalancer
sudo k3s kubectl expose deployment nginx --port=80 --type=LoadBalancer

# Check pods are distributed across agents
sudo k3s kubectl get pods -o wide

# Get LoadBalancer IP
sudo k3s kubectl get svc nginx
```

### Step 6: Test Failover

Stopping `k3s-server-1` simulates hardware failure. The API should remain available via servers two and three; etcd retains quorum at three members with one offline. Application traffic may shift nodes, but ServiceLB should keep answering until you drain workloads. Restart server one and confirm it rejoins without manual etcd surgery—if it does not, compare its `--token` and `--server` flags against the surviving members.

```bash
# From your host machine, stop a server
multipass stop k3s-server-1

# From server-2, check cluster health
multipass shell k3s-server-2
sudo k3s kubectl get nodes
# Server-1 should show NotReady

# Check etcd is still functional
sudo k3s kubectl get pods -A

# Application should still work
curl http://LOADBALANCER_IP

exit

# Bring server-1 back
multipass start k3s-server-1

# Verify it rejoins
multipass shell k3s-server-1
sudo k3s kubectl get nodes
```

### Success Criteria

- [ ] 3 server nodes running with embedded etcd
- [ ] 2 agent nodes joined to cluster
- [ ] Application deployed across agent nodes
- [ ] Cluster survives server-1 failure
- [ ] Server-1 successfully rejoins after restart

Document the token, server IP, and `tls-san` values you used in your lab notebook. HA joins fail for predictable reasons—mismatched `cluster-cidr`, rotated tokens without updating agents, or load balancer health checks that only probe HTTP port 80 while the API listens on 6443.

### Cleanup

When finished, delete the Multipass instances to reclaim RAM. If you plan to revisit the lab within a day, snapshot one server with `k3s etcd-snapshot save` so you can practice restore without repeating the join choreography.

```bash
# Delete all VMs
multipass delete --purge k3s-server-1 k3s-server-2 k3s-server-3 k3s-agent-1 k3s-agent-2
```

## Key Takeaways

1. **k3s is conformant Kubernetes, not a parallel platform** — CNCF certification means the same API objects, kubectl verbs, and Helm charts you use elsewhere apply here; the difference is packaging and bundled add-ons.
2. **Single-binary integration trades install-time modularity for speed** — containerd, Flannel, CoreDNS, Traefik, ServiceLB, and local-path-provisioner come up together; disable consciously when substituting corporate standards.
3. **Datastore choice drives HA story** — SQLite for single-server simplicity, embedded etcd for odd-numbered server quorum, external SQL when existing database operations must own backups and replication.
4. **ServiceLB and Traefik exist for bare-metal ergonomics** — they make LoadBalancer Services and Ingress resources work without cloud integrations; they are not mandatory if you prefer MetalLB or ingress-nginx.
5. **Agents are tunnel-connected workers** — registration uses tokens plus per-node password secrets; rebuilding a node requires deleting the old Node API object and secret to avoid identity collisions.
6. **Air-gap and upgrade paths mirror each other** — prefetch binaries and `k3s-airgap-images` tarballs, then use `INSTALL_K3S_SKIP_DOWNLOAD=true`; fleet upgrades can automate the same with system-upgrade-controller Plans.
7. **Edge production still demands backups and resource limits** — local-path data is node-local; etcd snapshots do not include PVC files; swap must stay off; and pod density must respect real RAM.
8. **Compare distributions on capabilities, not slogans** — use the Rosetta table mindset: datastore, CNI, ingress, LB, install mechanism, and positioning—then pick the tool that matches constraints.
9. **CNCF Sandbox status is a maturity signal, not a quality verdict** — verify current maturity and release notes before citing project level in compliance documents.
10. **k3s makes Kubernetes small enough to colocate with workloads, not small enough to skip operations** — distribution choice removes bootstrap friction; you still own upgrades, security patches, and data durability.

Treat this checklist as a pre-production review, not a post-install afterthought. If you cannot tick backups, datastore HA, and upgrade channel ownership, you have a lab cluster—regardless of how many nodes say `Ready`. Revisit the Rosetta table when stakeholders ask why you did not pick k0s or MicroK8s; the answer should be constraint-based, not habit. Write that decision down once and link to it from your cluster README so future you inherits the reasoning and avoids repeating the same architecture debates every single quarter review.

## Sources

- [docs.k3s.io](https://docs.k3s.io/) — Official k3s documentation homepage describing the lightweight distribution scope and bundled components.
- [docs.k3s.io: Architecture](https://docs.k3s.io/architecture) — Server versus agent roles, HA topology, and agent load-balancer registration mechanics.
- [docs.k3s.io: Cluster Datastore](https://docs.k3s.io/datastore) — kine-backed SQLite default, embedded etcd HA, and external SQL/etcd endpoint formats.
- [docs.k3s.io: Configuration Options](https://docs.k3s.io/installation/configuration) — Install script environment variables, config.yaml merge rules, and critical flag matching across servers.
- [docs.k3s.io: Air-Gap Install](https://docs.k3s.io/installation/airgap) — Offline image loading, `INSTALL_K3S_SKIP_DOWNLOAD`, and default-route requirements.
- [docs.k3s.io: Known Issues](https://docs.k3s.io/known-issues) — kine schema migration guidance, iptables caveats, and rootless experimental status.
- [docs.k3s.io: Automated Upgrades](https://docs.k3s.io/upgrades/automated) — system-upgrade-controller Plans and channel-based k3s upgrades.
- [docs.k3s.io: Network Policies](https://docs.k3s.io/networking/network-policies) — kube-router network policy controller bundled with k3s.
- [github.com: k3s-io/k3s](https://github.com/k3s-io/k3s) — Upstream source repository, issue tracker, and release artifacts.
- [github.com: k3s-io/k3s releases](https://github.com/k3s-io/k3s/releases) — Published binaries and `k3s-airgap-images` tarballs per version.
- [cncf.io: k3s project](https://www.cncf.io/projects/k3s/) — CNCF Sandbox acceptance date and project metadata.
- [github.com: cncf/toc issue #1957](https://github.com/cncf/toc/issues/1957) — Public incubation application tracking maturity progression as of 2026.
- [kubernetes.io: Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/) — Replacement for removed PodSecurityPolicy admission referenced in server configuration examples.
- [kubernetes.io: Certified Kubernetes](https://www.cncf.io/certification/software-conformance/) — Conformance program definition underpinning "same API, not a fork" claims.

## Next Module

Continue to [Module 14.2: k0s](../module-14.2-k0s/) — Zero-dependency Kubernetes with even cleaner architecture.

---

*"k3s doesn't make Kubernetes simpler—it makes Kubernetes small enough to fit where you need it."*
