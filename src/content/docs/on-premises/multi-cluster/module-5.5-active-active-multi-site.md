---
title: "Active-Active Multi-Site"
description: "Implement global load balancing and cross-DC data replication for bare-metal Kubernetes multi-site architectures."
slug: on-premises/multi-cluster/module-5.5-active-active-multi-site
sidebar:
  order: 55
---

# Active-Active Multi-Site

## Learning Outcomes

*   Configure bare-metal Global Server Load Balancing (GSLB) using DNS zone delegation.
*   Implement BGP Anycast for stateless multi-site traffic distribution.
*   Diagnose split-brain scenarios and implement quorum-based witness sites.
*   Compare synchronous and asynchronous database replication topologies for bare-metal.
*   Deploy and validate a multi-site Distributed SQL architecture using topology spread constraints.

## The Physics of Active-Active

> **Stop and think**: How does the speed of light physical limit impact application design when moving from a single datacenter to an active-active multi-site architecture?

Operating an active-active architecture across physically separated datacenters is bounded by the speed of light. Every architectural decision in a multi-site setup is a negotiation with latency. 

Fiber optic transmission incurs roughly 1 millisecond of latency per 100 kilometers of distance, excluding the processing overhead of switches, routers, and firewalls. When applications run active-active, read and write operations must cross this boundary. 

If Datacenter A (DC-A) and Datacenter B (DC-B) are 500km apart, the absolute minimum Round Trip Time (RTT) is ~10ms. For stateless microservices, 10ms is negligible. For synchronous database replication requiring distributed consensus (e.g., Paxos or Raft) or certification-based replication (e.g., Galera), a single transaction might require multiple round trips, inflating a 2ms local write to a 40ms multi-site write.

:::tip
**The 5ms Rule**
For legacy synchronous replication (like Galera Cluster), keep datacenter RTT under 5ms (typically <50km apart, often called "Campus Area Networks"). For Distributed SQL (CockroachDB, YugabyteDB), RTT can be higher (up to 100ms), but application timeouts and retry budgets must be explicitly tuned to absorb the consensus latency.
:::

## Global Traffic Management (GTM) on Bare Metal

In cloud environments, Global Traffic Management is handled by managed services (Route 53, Cloudflare, Cloud DNS). On bare metal, routing ingress traffic to the optimal datacenter requires managing your own edge routing. There are two primary patterns: DNS-based GSLB and BGP Anycast.

### DNS-based GSLB (K8gb)

DNS-based Global Server Load Balancing delegates a specific subdomain (e.g., `app.global.internal.corp`) to Name Servers running inside your Kubernetes clusters. 

Tools like **K8gb** (Kubernetes Global Balancer) operate as Cloud Native GSLB. They deploy CoreDNS instances that act as authoritative nameservers for your delegated zones. 

1.  An Ingress object is annotated with `k8gb.io/strategy: roundRobin` (or `failover`, `geoip`).
2.  K8gb controllers in DC-A and DC-B communicate via Custom Resource Definitions (CRDs) exchanged over the WAN.
3.  When a client requests `app.global.internal.corp`, the enterprise DNS forwards the query to the K8gb CoreDNS instances.
4.  K8gb returns the A record of the Ingress controller in the healthiest, closest datacenter.

```mermaid
graph TD
    Client[Client] -->|DNS Query| CorpDNS[Enterprise DNS]
    CorpDNS -->|Zone Delegation| K8gbA[K8gb CoreDNS DC-A]
    CorpDNS -->|Zone Delegation| K8gbB[K8gb CoreDNS DC-B]
    K8gbA -.->|Health/CRD Sync| K8gbB
    K8gbA -->|Returns IP A| Client
    Client -->|HTTPS Traffic| IngressA[Ingress DC-A]
```

**Failure Mode:** DNS caching. Clients and intermediate ISPs routinely ignore TTLs. If DC-A fails, K8gb removes DC-A's IP from the DNS response, but clients caching the old IP will experience downtime until their local cache expires.

### BGP Anycast

Anycast involves announcing the exact same IP address (a /32 VIP) from multiple datacenters using BGP (Border Gateway Protocol).

The enterprise routers forward client packets to the datacenter with the shortest BGP path. If DC-A goes offline, its Top-of-Rack (ToR) router withdraws the BGP route. The enterprise network converges, and traffic immediately routes to DC-B.

:::caution
**The TCP Reset Gotcha**
Anycast is stateless. If the network topology changes while a TCP connection is established (e.g., a link flaps, changing the shortest path), subsequent packets for that session will be routed to the *other* datacenter. Because the other datacenter's Ingress controller has no TCP state for this connection, it responds with a TCP RST (Reset). Anycast is highly effective for UDP (like DNS) or short-lived stateless HTTP requests, but volatile for long-lived WebSockets or large file transfers.
:::

## Data Replication and Consensus

Stateless compute is trivial to span across sites. State is the hard problem. An active-active database must handle writes at both locations and resolve conflicts without data corruption.

### The Two-Datacenter Trap (Split-Brain)

> **Pause and predict**: If you only have two datacenters, how can you deploy a quorum-based distributed database without risking a complete halt during a network partition?

The most common architectural failure in bare-metal multi-site design is attempting active-active storage across exactly two datacenters. 

If the WAN link between DC-A and DC-B fails, both datacenters remain online but cannot communicate. 
*   If both accept writes, they diverge. When the link returns, resolving conflicting writes (Split-Brain) requires manual, destructive intervention.
*   To prevent this, databases use Quorum (Strict Majority). 
*   Quorum formula: `(N / 2) + 1`. 
*   In a 2-node (or 2-DC) cluster, quorum is 2. If the link fails, neither site can see 2 nodes. Both sites lose quorum. The entire database halts to protect data integrity.

**The Fix: The Witness Site (DC-C)**
Active-active storage requires a minimum of three distinct fault domains. The third site does not need heavy compute; it acts as a "Witness" or tie-breaker. If the WAN fails between DC-A and DC-B, the site that can still communicate with the Witness site achieves quorum (2 out of 3) and remains active.

### Bare Metal Database Comparison

| Feature | Galera (MariaDB) | CockroachDB | YugabyteDB |
| :--- | :--- | :--- | :--- |
| **Architecture** | Synchronous Multi-Master | Distributed SQL ('multi-active availability') | Distributed SQL (Raft) |
| **Ideal RTT** | < 5ms | < 50ms | < 50ms |
| **Storage Engine** | InnoDB | Pebble (LSM Tree) | DocDB (RocksDB) |
| **K8s Operator** | MariaDB Operator | CockroachDB Operator | YugabyteDB Operator |
| **Conflict Handling** | Certification (Rollback on conflict) | Raft Consensus (Leader election) | Raft Consensus |
| **Read Scaling** | Local reads (stale possible) | Follower Reads | Follower Reads |

*Note: CockroachDB explicitly uses "multi-active availability" (not classical active-active) where all replicas serve reads and writes with consensus replication. Additionally, if considering Vitess (CNCF Graduated, latest release v23.0.3), note that it does NOT support active-active (multi-master) replication natively, relying instead on VReplication for cross-cluster data movement.*

**Production Gotcha: Galera Flow Control**
In an active-active Galera cluster, replication operates at the speed of the slowest node. If a WAN link degrades, or a node in DC-B experiences disk I/O latency, Galera triggers "Flow Control." It pauses writes across the *entire global cluster* (including DC-A) to allow the lagging node to catch up. A localized storage issue in one datacenter causes a global application outage.

## Hands-on Lab

This lab simulates a multi-site active-active database deployment using CockroachDB across a single Kubernetes cluster. We will use node labels and topology spread constraints to simulate Datacenter A, Datacenter B, and a Witness site, demonstrating quorum survival and failure.

### Prerequisites

*   `kind` installed (v0.22.0+)
*   `kubectl` installed
*   `helm` installed (v3.14.0+)

### Step 1: Provision a Topology-Aware Cluster

Create a Kind configuration file that defines 5 worker nodes. We will apply custom labels to simulate three distinct zones.

```yaml
# kind-multisite.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
  - role: worker
  - role: worker
  - role: worker
  - role: worker
```

Create the cluster:

```bash
kind create cluster --config kind-multisite.yaml --name multisite
```

Label the nodes to simulate two full datacenters and one witness datacenter:

```bash
# Datacenter A (2 nodes)
kubectl label node multisite-worker topology.kubernetes.io/zone=dc-a
kubectl label node multisite-worker2 topology.kubernetes.io/zone=dc-a

# Datacenter B (2 nodes)
kubectl label node multisite-worker3 topology.kubernetes.io/zone=dc-b
kubectl label node multisite-worker4 topology.kubernetes.io/zone=dc-b

# Witness Site (1 node)
kubectl label node multisite-worker5 topology.kubernetes.io/zone=dc-witness
```

Verify the topology:

```bash
kubectl get nodes -L topology.kubernetes.io/zone
```
*Expected Output: Nodes listed with `dc-a`, `dc-b`, and `dc-witness` zones.*

### Step 2: Deploy CockroachDB with Topology Spread

Add the CockroachDB Helm repository:

```bash
helm repo add cockroachdb https://charts.cockroachdb.com
helm repo update
```

Create a custom `values.yaml` to force CockroachDB pods to spread evenly across our simulated zones. This ensures that no single datacenter failure can take down a majority of the database pods.

```yaml
# crdb-values.yaml
statefulset:
  replicas: 5
conf:
  single-node: false
topologySpreadConstraints:
  maxSkew: 1
  topologyKey: topology.kubernetes.io/zone
  whenUnsatisfiable: DoNotSchedule
  labelSelector:
    matchLabels:
      app.kubernetes.io/name: cockroachdb
```

Install CockroachDB:

```bash
helm install crdb cockroachdb/cockroachdb -f crdb-values.yaml --version 14.1.2 --wait
```

### Step 3: Verify the Cluster and Data Insertion

Check that the pods are running and verify their distribution across the zones:

```bash
kubectl get pods -o wide -l app.kubernetes.io/name=cockroachdb
```
*Expected Output: 5 pods running. Look at the `NODE` column to confirm they are scheduled across `multisite-worker` through `multisite-worker5`.*

Initialize the cluster and write some test data:

```bash
# Access the built-in SQL client
kubectl exec -it crdb-cockroachdb-0 -- ./cockroach sql --insecure

# Inside the SQL prompt:
CREATE DATABASE bank;
USE bank;
CREATE TABLE accounts (id INT PRIMARY KEY, balance DECIMAL);
INSERT INTO accounts VALUES (1, 1000.50), (2, 5000.00);
SELECT * FROM accounts;
\q
```

### Step 4: Simulate Datacenter Failure (DC-B goes down)

We will simulate a hard failure of `dc-b` by cordoning the nodes and deleting the pods running on them. 

Identify the nodes in `dc-b` and cordon them so nothing reschedules:

```bash
kubectl cordon multisite-worker3 multisite-worker4
```

Delete the CockroachDB pods running on `dc-b`:

```bash
# Find the pods on dc-b
kubectl get pods -o wide | grep dc-b

# Delete those specific pods (e.g., crdb-cockroachdb-3, crdb-cockroachdb-4)
kubectl delete pod crdb-cockroachdb-3 crdb-cockroachdb-4 --force
```

### Step 5: Verify Quorum Survival

Datacenter B is completely offline. However, DC-A (2 nodes) and the Witness Site (1 node) provide 3 out of 5 nodes. The cluster maintains quorum.

Attempt to read and write data from a surviving pod in DC-A:

```bash
kubectl exec -it crdb-cockroachdb-0 -- ./cockroach sql --insecure

# Inside the SQL prompt:
SELECT * FROM bank.accounts;
INSERT INTO bank.accounts VALUES (3, 250.00);
SELECT * FROM bank.accounts;
\q
```
*Expected Output: The queries execute successfully. The cluster is operating normally despite a full datacenter loss.*

### Step 6: Simulate Quorum Loss (Split-Brain Prevention)

Now, simulate the loss of the Witness site. The cluster now only has DC-A online (2 out of 5 nodes). Quorum is lost.

```bash
kubectl cordon multisite-worker5
kubectl delete pod crdb-cockroachdb-2 --force # Assuming this was on worker5
```

Attempt to read or write data:

```bash
kubectl exec -it crdb-cockroachdb-0 -- ./cockroach sql --insecure

# Inside the SQL prompt:
SELECT * FROM bank.accounts;
```
*Expected Output: The query hangs or returns an error (e.g., `rpc error: code = Unavailable`). The database intentionally halts to prevent split-brain data corruption.*

**Cleanup:**

```bash
kind delete cluster --name multisite
```

## Practitioner Gotchas

1.  **Asymmetric Routing Blackholes:** In bare-metal BGP Anycast setups, packets from a client might enter through DC-A, but the return traffic from the pod might egress out of DC-B. If stateful edge firewalls exist, DC-B's firewall drops the return packets because it never saw the TCP SYN. Ensure stateful firewalls are bypassed for Anycast VIPs, or use Direct Server Return (DSR) topologies carefully.
2.  **Stale DNS TTLs during Failover:** When using DNS GSLB to fail over from DC-A to DC-B, downstream clients (like Java JVMs or ISP DNS resolvers) often ignore your `TTL=30` and cache the dead IP for minutes or hours. Always combine DNS GSLB with localized retry logic in the client application.
3.  **The Replication Queue OOM:** If a WAN link degrades severely (but doesn't fail entirely), asynchronous replication queues build up in RAM. If the application keeps writing at high velocity, the publisher database can exhaust memory and trigger the Linux OOM Killer, turning a network degradation into a hard database crash. Monitor replication lag and set aggressive memory limits on replication buffers.
4.  **Misconfigured Failure Domains:** Deploying a distributed database and setting `topologyKey: kubernetes.io/hostname` instead of a region/zone label. The database thinks 3 nodes in the same rack constitute 3 fault domains. When the rack loses power, quorum is lost instantly. Always align Kubernetes topology keys with actual physical fault domains.

## Quiz

**1. You are running a Galera Cluster synchronously across two bare-metal datacenters. Datacenter A experiences a severe storage IOPS degradation, causing local disk writes to take 500ms. Your applications in Datacenter B are writing to the local Galera nodes. What is the immediate impact on the applications running in Datacenter B?**
*   A) Applications in DC-B will continue writing normally; DC-A will eventually catch up asynchronously.
*   B) Applications in DC-B will experience 500ms write latency because Galera flow control forces the cluster to the speed of the slowest node.
*   C) DC-A will automatically be evicted from the cluster to preserve DC-B's performance.
*   D) Applications in DC-B will experience split-brain until the IOPS degrade resolves.
*   *Correct Answer: B*
*   *Why:* Galera uses synchronous multi-master replication where every node must certify a transaction before it is committed. To prevent faster nodes from overwhelming slower nodes with replication events, Galera implements a mechanism called Flow Control. When a node's replication queue grows too large—such as when disk IOPS degrade—it broadcasts a pause signal to the entire cluster. Consequently, the healthy nodes in Datacenter B will throttle their write speeds to match the degraded node in Datacenter A, causing global application latency.

**2. Your infrastructure team proposes deploying a highly available active-active database cluster across exactly two bare-metal datacenters. The datacenters are connected via a dedicated redundant fiber link. Why is this specific two-datacenter architecture considered a critical anti-pattern for stateful workloads?**
*   A) Routing algorithms cannot balance traffic 50/50 without a third node.
*   B) Synchronous replication requires three nodes to compress data payloads.
*   C) In the event of a network partition between the two datacenters, neither can achieve a strict majority (quorum), causing the database to halt to prevent split-brain.
*   D) BGP Anycast only supports odd numbers of origins.
*   *Correct Answer: C*
*   *Why:* Distributed consensus systems (like Raft or Paxos) rely on a quorum, defined as `(N / 2) + 1`, to safely commit writes and elect leaders. In a two-datacenter deployment, each site holds 50% of the voting nodes. If the WAN link connecting them fails, neither site can communicate with the other to form a majority. To protect data integrity and prevent both sites from accepting conflicting writes (a split-brain scenario), the database clusters in both datacenters will intentionally halt write operations, resulting in a complete database outage despite the hardware being online.

**3. Your enterprise uses BGP Anycast to route ingress traffic to two geographically separated bare-metal datacenters. A client initiates a large file download from a pod in Datacenter A. Halfway through the transfer, a core network router flaps, causing the BGP shortest-path to shift to Datacenter B. What happens to the client's existing file download?**
*   A) The downloads continue seamlessly because Kube-Proxy syncs connection states between clusters.
*   B) The download fails with a TCP Reset (RST) because Datacenter B receives packets for an established TCP session it does not recognize.
*   C) The downloads pause temporarily while DNS propagates the new path.
*   D) The router holds the TCP state in memory and proxies the rest of the stream to DC-A.
*   *Correct Answer: B*
*   *Why:* BGP Anycast is a stateless routing mechanism that directs packets to the topologically closest destination advertising the IP address. When the routing path shifts, packets belonging to the client's established TCP connection are suddenly routed to the Ingress controller in Datacenter B instead of Datacenter A. Because the Ingress controller in Datacenter B has no memory of the initial TCP handshake or sequence numbers for this connection, it assumes the incoming packets are invalid. It responds with a TCP RST, abruptly terminating the client's connection and failing the download.

**4. Your platform team has implemented K8gb for Global Server Load Balancing across two bare-metal Kubernetes clusters (DC-East and DC-West). When a client application queries the global domain name `api.global.internal` during a partial outage in DC-East, how do the K8gb controllers ensure the client is correctly routed to the healthiest datacenter?**
*   A) By hijacking BGP routes from the Top-of-Rack switches.
*   B) By acting as authoritative DNS Name Servers and dynamically returning A records based on cluster health data synchronized via Custom Resources.
*   C) By deploying an Envoy proxy at the enterprise network edge to inspect HTTP headers.
*   D) By modifying the client's local `/etc/hosts` file via a DaemonSet.
*   *Correct Answer: B*
*   *Why:* K8gb operates as a Cloud Native GSLB by running CoreDNS instances inside your Kubernetes clusters that act as authoritative nameservers for delegated subdomains. The K8gb controllers continuously monitor local Ingress health and exchange this state with other clusters using Custom Resource Definitions (CRDs) over the WAN. When a DNS query arrives, the K8gb CoreDNS instance evaluates the synchronized health data and returns the IP address (A record) of the optimal, healthy datacenter. This ensures clients are dynamically routed away from failed sites without relying on external cloud load balancers.

**5. A development team is migrating an application to a multi-site Distributed SQL database (CockroachDB) spanning New York and London, with a known network Round Trip Time (RTT) of 80ms. While CockroachDB handles the replication, what architectural adjustments must the application developers make to ensure stability?**
*   A) Nothing, CockroachDB masks all latency from the application layer.
*   B) Configure the application to use UDP for all database writes.
*   C) Implement aggressive client-side connection pooling and increase application timeouts and retry budgets to accommodate the >80ms consensus latency per transaction.
*   D) Switch the database to Galera to enforce local read/write speeds.
*   *Correct Answer: C*
*   *Why:* Distributed SQL databases like CockroachDB use consensus protocols (like Raft) to ensure strong consistency, which requires multiple network round trips to achieve a quorum for every write operation. Because the speed of light dictates an 80ms RTT between New York and London, a single transaction will inherently take significantly longer than a local database write. If the application is not tuned to expect this increased latency, it will prematurely timeout or exhaust its connection pool waiting for responses. This leads to application-level instability and failed transactions despite the database functioning correctly under the hood.

## Further Reading

*   [CockroachDB Multi-Region Capabilities](https://www.cockroachlabs.com/docs/stable/multiregion-overview.html)
*   [K8gb - Cloud Native Kubernetes Global Balancer](https://www.k8gb.io/docs/)
*   [Galera Cluster Flow Control](https://galeracluster.com/library/documentation/flow-control.html)
*   [Kubernetes Topology Spread Constraints](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/)