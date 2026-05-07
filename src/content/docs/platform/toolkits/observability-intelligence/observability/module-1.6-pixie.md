---
title: "Module 1.6: Pixie - Zero-Instrumentation Observability"
slug: platform/toolkits/observability-intelligence/observability/module-1.6-pixie
sidebar:
  order: 7
---

## Complexity: [MEDIUM]

**Time to Complete**: 90 minutes

**Prerequisites**: Module 1.1 (Prometheus), Module 1.2 (OpenTelemetry basics), basic Kubernetes troubleshooting, and comfort reading `kubectl` output.

**Kubernetes Version Target**: 1.35+

**Environment Assumption**: The examples assume a Linux Kubernetes cluster where privileged DaemonSets are allowed and eBPF is supported by the worker-node kernel.

---

## Learning Outcomes

After completing this module, you will be able to:

- **Evaluate** when Pixie's zero-instrumentation model is the right observability choice compared with OpenTelemetry, Prometheus, and traditional APM agents.
- **Deploy and validate** Pixie components in a Kubernetes cluster while checking the node, kernel, and permission constraints that commonly block eBPF tools.
- **Design** PxL queries that narrow a vague production symptom into service, endpoint, database, DNS, or network-level evidence.
- **Debug** a latency incident by moving from cluster-wide symptoms to a specific failing dependency without changing application code.
- **Recommend** an operating model for Pixie data retention, privacy boundaries, and long-term export in a platform engineering environment.

---

## Why This Module Matters

A platform engineer at a payments company gets paged because checkout latency has tripled during a promotion. The application team insists their service metrics look normal, the database team sees no sustained CPU pressure, and the networking team cannot reproduce the issue from their test pod. Everyone has a dashboard, but each dashboard shows only the part of the system its owner expected to instrument.

That is the real observability gap Pixie is designed to close. Traditional instrumentation is still valuable, especially when teams need business spans, custom metrics, and long-term history, but it only sees what engineers deliberately added to the code path. The hardest incidents often appear in the space between instrumented systems: DNS retries, connection churn, untracked internal HTTP calls, noisy pods sharing a node, or a dependency that nobody remembered was still in the request path.

[Pixie uses eBPF to observe workload behavior from the Linux kernel and Kubernetes metadata plane. Instead of asking each service to emit telemetry, Pixie watches the traffic, process activity, and protocol events already happening on every node.](https://github.com/pixie-io/pixie) That makes it especially useful during the first hour of an incident, when the platform team needs fast evidence before deciding whether to add permanent instrumentation, scale a dependency, fix a network policy, or escalate to an application owner.

This module teaches Pixie as a troubleshooting workflow, not as a collection of commands. You will first build a mental model for where Pixie sits, then learn how its architecture collects and queries telemetry, then walk through a worked incident from symptom to fix. By the end, you should be able to use Pixie responsibly: fast enough for production debugging, careful enough for sensitive payloads, and realistic enough to know when another observability tool should carry the long-term signal.

---

## Core Concepts: Why eBPF Changes the Debugging Starting Point

Application instrumentation starts inside the process. A developer imports an SDK, wraps important operations, emits metrics, and ships a new version. That gives excellent semantic context when the code was instrumented well, but it has two weaknesses during an unexpected incident: the missing signal cannot be queried retroactively, and unowned services rarely get instrumented on your timeline.

Pixie's starting point is different. It observes selected events from the kernel and enriches them with Kubernetes metadata, so the first debugging question changes from "did this service emit the right telemetry?" to "what behavior can we infer from traffic, processes, and protocol activity right now?" That shift matters in platform engineering because the platform team often has cluster-level responsibility without owning every application repository.

```ascii
+-----------------------------------------------------------------------+
|                           User Space                                  |
|                                                                       |
|  +----------------+   +----------------+   +----------------+         |
|  | checkout-api   |   | inventory-api  |   | postgres-client|         |
|  | no code change |   | no code change |   | no code change |         |
|  +-------+--------+   +-------+--------+   +-------+--------+         |
|          |                    |                    |                  |
+----------|--------------------|--------------------|------------------+
           |                    |                    |
+----------v--------------------v--------------------v------------------+
|                           Kernel Space                                |
|                                                                       |
|  +----------------+   +----------------+   +----------------+         |
|  | network probes |   | syscall probes |   | process probes |         |
|  +--------+-------+   +--------+-------+   +--------+-------+         |
|           |                    |                    |                 |
|           +--------------------+--------------------+                 |
|                                |                                      |
|                         +------v------+                               |
|                         | eBPF maps   |                               |
|                         | event data  |                               |
|                         +------+------|                               |
+--------------------------------|--------------------------------------+
                                 |
+--------------------------------v--------------------------------------+
|                         Pixie Edge Module                             |
|           reads events, parses protocols, attaches K8s context         |
+-----------------------------------------------------------------------+
```

The eBPF programs Pixie uses are not arbitrary kernel hacks. eBPF programs are verified before loading, run in a constrained environment, and exchange data with user-space collectors through kernel data structures such as maps and ring buffers. This does not make eBPF risk-free, but it explains why modern observability, security, and networking tools increasingly use it for low-overhead visibility.

Pixie is most powerful when you treat it as a short-loop investigation tool. You ask a question, inspect live evidence, refine the query, and then either fix the immediate issue or decide what permanent telemetry should exist. It is less suitable as the only observability system for compliance reports, quarter-long trend analysis, or business-level SLO reporting, because its default storage model is intentionally local and short-lived.

**Stop and think:** Your team owns a service that already emits OpenTelemetry spans, but a downstream dependency does not. A request is slow only when that dependency is called. Before reading further, decide which part of the request path application spans can prove, and which part a kernel-observed tool like Pixie might reveal faster.

A practical mental model is to separate "semantic truth" from "behavioral truth." OpenTelemetry can tell you that the code entered `ChargeCustomer` and attached a customer tier attribute. Prometheus can tell you that the checkout service is using more CPU than usual. Pixie can tell you that checkout pods are making repeated DNS lookups, sending HTTP requests to a specific internal service, or issuing slow PostgreSQL queries without waiting for a new deployment.

| Traditional Instrumentation | Pixie eBPF Observation |
|---|---|
| Requires application libraries, configuration, and redeployment. | Starts at the node and can observe many workloads without application changes. |
| Provides rich business context when developers add the right spans and labels. | Provides behavioral evidence from traffic, processes, and supported protocols. |
| Usually feeds long-term storage and alerting systems. | Focuses on live and recent debugging data inside the cluster. |
| Can miss services that are unowned, legacy, or temporarily deployed. | Can reveal uninstrumented services if the node and protocol are supported. |
| Best for durable SLOs, tracing strategy, and application-owned telemetry. | Best for rapid exploration, incident triage, and instrumentation gap discovery. |

The distinction is not a contest between tools. Senior platform engineers combine them because each tool answers a different kind of question. Pixie often discovers the hidden dependency or failing layer; OpenTelemetry and Prometheus often become the permanent mechanism for measuring that dependency after the team understands it.

---

## Pixie Architecture: What Runs in the Cluster

Pixie installs a set of Kubernetes components that separate collection, query execution, metadata enrichment, and optional cloud connectivity. The most important component to recognize during troubleshooting is the Pixie Edge Module, usually abbreviated as PEM. It runs on each node and collects local telemetry through eBPF programs and user-space protocol parsing.

```ascii
+--------------------------------------------------------------------------------+
|                              Kubernetes Cluster                                 |
|                                                                                |
|  +------------------------------------------------------------------------+    |
|  |                              pl namespace                              |    |
|  |                                                                        |    |
|  |  +------------------+   +------------------+   +-------------------+   |    |
|  |  | Vizier           |   | Metadata service |   | NATS              |   |    |
|  |  | query execution  |   | K8s enrichment   |   | internal messages |   |    |
|  |  +---------+--------+   +---------+--------+   +---------+---------+   |    |
|  |            |                      |                      |             |    |
|  |            +----------------------+----------------------+             |    |
|  |                                   |                                    |    |
|  |                         +---------v---------+                          |    |
|  |                         | Cloud connector   |                          |    |
|  |                         | optional UI path  |                          |    |
|  |                         +-------------------+                          |    |
|  +------------------------------------------------------------------------+    |
|                                                                                |
|  +-----------------------+   +-----------------------+   +------------------+   |
|  | Node A                |   | Node B                |   | Node C           |   |
|  | +-------------------+ |   | +-------------------+ |   | +--------------+ |   |
|  | | PEM DaemonSet pod | |   | | PEM DaemonSet pod | |   | | PEM pod      | |   |
|  | +---------+---------+ |   | +---------+---------+ |   | +------+-------+ |   |
|  |           | eBPF       |   |           | eBPF       |   |        | eBPF    |   |
|  | +---------v---------+ |   | +---------v---------+ |   | +------v-------+ |   |
|  | | Linux kernel      | |   | | Linux kernel      | |   | | kernel       | |   |
|  | +-------------------+ |   | +-------------------+ |   | +--------------+ |   |
|  +-----------------------+   +-----------------------+   +------------------+   |
+--------------------------------------------------------------------------------+
```

Vizier is the in-cluster query layer. When you run a PxL script, Vizier coordinates the query, requests data from the relevant PEMs, and returns a table or visualization. This split is why Pixie can query live distributed telemetry without sending every raw event to an external system first.

The metadata service connects low-level observations to Kubernetes names that humans can use. A packet alone is not helpful during an incident; a packet enriched with namespace, pod, service, container, and node information becomes actionable. This enrichment is the difference between saying "there is traffic on port 8080" and saying "the `checkout-api` pod in the `payments` namespace is calling `fraud-api` with increasing latency."

NATS and other internal components support communication inside the Pixie control plane. In normal day-to-day use, you rarely tune these directly, but you should know they exist because failed deployments often show up as missing pods or unhealthy services in the `pl` namespace. When Pixie looks broken, check the health of the platform components before assuming eBPF collection failed.

The cloud connector is optional depending on the deployment model. Some teams use Pixie Cloud or a vendor-hosted interface for dashboards and script management; stricter environments may prefer self-hosted control planes or limited export paths. The platform decision is not only technical. It also includes privacy boundaries, audit requirements, operational support, and whether request payloads may ever leave the cluster.

| Component | Role | What You Check During Troubleshooting |
|---|---|---|
| PEM | Per-node data collection through eBPF and protocol parsing. | Confirm the DaemonSet has one healthy pod per schedulable Linux node. |
| Vizier | Query execution and coordination across PEMs. | Check that queries reach the cluster and return data for expected namespaces. |
| Metadata service | Kubernetes context enrichment for observed events. | Validate that tables include pod, namespace, service, and node context. |
| NATS | Internal message bus used by Pixie components. | Inspect logs if components are healthy individually but cannot communicate. |
| Cloud connector | Optional path to Pixie UI or hosted control plane. | Confirm it matches the organization's connectivity and data policy. |

**Pause and predict:** If a node has application pods but no healthy PEM pod, which symptoms would you expect in a Pixie query: missing traffic from that node, wrong latency values for the whole cluster, or corrupted Kubernetes metadata? Write down your guess before comparing it with the explanation.

The most likely outcome is missing or incomplete traffic from workloads on that node. Pixie cannot collect local kernel events from a node where the PEM is not running, so cluster-wide views can look deceptively partial. That is why deployment validation must include node coverage, not only a green status for one central control-plane pod.

---

## Deployment and Validation: Install Pixie Like a Platform Capability

Installing Pixie is simple when the cluster permits the required privileges and kernel features. The hard part is not typing the install command; the hard part is validating that the environment can actually run eBPF collection safely. Managed Kubernetes offerings, hardened node images, restricted Pod Security policies, and private clusters can all change the deployment path.

Start by checking whether your cluster is a realistic candidate. Pixie generally expects Linux nodes with eBPF support, container runtime compatibility, and permission to run privileged collection components. If your organization blocks privileged DaemonSets completely, you need a policy conversation before you need a YAML tweak.

```bash
kubectl version --short
kubectl get nodes -o wide
kubectl get ns
```

After this point, the examples use the short alias `k` for `kubectl`. Define it in your shell only if you do not already have a different alias:

```bash
alias k=kubectl
```

A useful preflight check is to inspect node kernels and operating systems. The exact command depends on your access model, but the Kubernetes node object usually gives enough information to decide whether deeper node access is needed.

```bash
k get nodes -o custom-columns=NAME:.metadata.name,KERNEL:.status.nodeInfo.kernelVersion,OS:.status.nodeInfo.osImage,ARCH:.status.nodeInfo.architecture,CONTAINER_RUNTIME:.status.nodeInfo.containerRuntimeVersion
```

If your cluster allows the Pixie CLI workflow, the install path is direct. The CLI performs compatibility checks, deploys Pixie, and provides a convenient way to run scripts. In production, many platform teams still wrap this in change management and document the exact cluster, namespace, and access model.

```bash
bash -c "$(curl -fsSL https://withpixie.ai/install.sh)"
px deploy
px get viziers
```

Helm is often a better fit for GitOps-managed clusters. It lets you pin chart values, review changes, and place Pixie under the same deployment controls as the rest of the platform. The deploy key and cluster name are environment-specific, so they should come from your secret management system rather than being committed to a repository.

```bash
helm repo add pixie https://pixie-operator-charts.storage.googleapis.com
helm repo update
k create namespace pl
helm install pixie pixie/pixie-operator-chart \
  --namespace pl \
  --set deployKey="${PIXIE_DEPLOY_KEY}" \
  --set clusterName="lab-cluster"
```

A careful validation sequence checks more than whether the install command exited successfully. You want to prove that the namespace exists, the DaemonSet covered the expected nodes, the central components are healthy, and a simple query returns real workload data. Skipping this step creates a dangerous failure mode: the tool appears installed, but incident responders trust incomplete evidence.

```bash
k get pods -n pl -o wide
k get daemonset -n pl
k get events -n pl --sort-by=.lastTimestamp
px get viziers
```

When the PEM DaemonSet does not reach every node, read the scheduling reason before changing values. A taint, architecture mismatch, missing privilege, or unsupported node image leads to a different fix. Treat the DaemonSet status as a diagnostic clue, not just an error.

```bash
k describe daemonset -n pl
k describe pod -n pl -l name=pl-node-pem
```

| Deployment Check | Healthy Signal | What an Unhealthy Signal Usually Means |
|---|---|---|
| `pl` namespace exists | Pixie resources are grouped in the expected namespace. | The install did not complete or targeted the wrong context. |
| PEM DaemonSet desired equals ready | Every eligible node has a collector. | Taints, privileges, node selectors, or unsupported hosts are blocking coverage. |
| Vizier reports healthy | Query coordination is available. | Control-plane components may be crash-looping or unable to communicate. |
| Metadata appears in query results | Events are enriched with Kubernetes context. | Metadata service or RBAC permissions may be broken. |
| Recent workload traffic appears | eBPF collection and protocol parsing are working. | No traffic exists, protocol is unsupported, encryption hides payloads, or PEM coverage is incomplete. |

Self-hosted or air-gapped Pixie deployments require more operational maturity. You need to maintain the control plane, image registry access, certificates, upgrades, and compatibility with your Kubernetes versions. That approach can be justified for regulated environments, but it should be an explicit platform product decision rather than an improvised workaround during an outage.

```bash
git clone https://github.com/pixie-io/pixie.git
cd pixie
./scripts/deploy_cloud.sh
px deploy --cloud_addr="${PIXIE_CLOUD_ADDR}"
```

The first senior-level deployment decision is scope. You do not have to make Pixie available to every namespace on day one. A platform team may start with staging clusters, selected production namespaces, or incident-only access granted through break-glass controls. The right answer depends on your sensitivity to captured headers and payloads, your incident response model, and how mature your existing observability stack already is.

---

## PxL Querying: Turning Raw Events into Evidence

PxL, the Pixie Language, is a Python-like query language built around DataFrames. The important habit is to begin with a concrete operational question, not with a table name. "Show me all HTTP events" is rarely a good final query; "which endpoint in `checkout` has the highest p99 latency over the last five minutes, and does it correlate with errors?" is much closer to an incident-response question.

A minimal query starts with a DataFrame, filters the time window and scope, derives useful fields, aggregates by dimensions, and displays the result. This shape should feel familiar if you have used pandas, SQL, PromQL aggregation, or log analytics tools. The syntax is only the surface; the deeper skill is choosing dimensions that reduce noise without hiding the faulty path.

```python
import px

df = px.DataFrame('http_events', start_time='-5m')
df = df[df.namespace == 'payments']
df.latency_ms = df.resp_latency / 1000000

summary = df.groupby(['service', 'req_path', 'req_method']).agg(
    request_count=('latency_ms', px.count),
    p50_ms=('latency_ms', px.quantiles(0.5)),
    p99_ms=('latency_ms', px.quantiles(0.99)),
    error_rate=('resp_status', lambda status: px.mean(status >= 400) * 100),
)

summary = summary[summary.request_count > 10]
summary = summary.sort('p99_ms', ascending=False)

px.display(summary, 'Payments HTTP latency by endpoint')
```

The first filter should usually be a time window and a namespace. That keeps the query relevant and reduces memory pressure. During a live incident, a five-minute window often captures the current symptom while avoiding stale events from an earlier deploy or load test.

The next filter should reflect the user's symptom. If users report checkout failures, filter by the checkout namespace, service, route, or response status. If a dependency is suspected, group by caller and callee. If DNS seems likely, switch from `http_events` to `dns_events` and check response codes and latency. Good PxL querying is an iterative narrowing process.

| DataFrame | Best First Question | Example Investigation |
|---|---|---|
| `http_events` | Which services, paths, or status codes are slow or failing? | API latency, error spikes, unexpected internal calls. |
| `pgsql_events` | Which SQL statements or client services have high latency? | Slow database calls, repeated queries, missing indexes. |
| `mysql_events` | Which MySQL requests are frequent, slow, or failing? | Legacy service database pressure. |
| `dns_events` | Which names fail to resolve or take too long? | CoreDNS overload, bad service names, external lookup delays. |
| `conn_stats` | Which connections churn, reset, or accumulate retries? | Network instability, overloaded backends, noisy clients. |
| `process_stats` | Which processes consume CPU or memory on a node? | Node-level contention and unexpected workload behavior. |
| `network_stats` | Which pods or services generate unusual network volume? | Traffic spikes, data transfer regressions, runaway clients. |

A common mistake is to group too early by high-cardinality values such as full URLs, raw request bodies, or client IP addresses. That can produce a large table that looks impressive but does not guide a decision. Prefer stable dimensions first, such as namespace, service, route pattern, method, status class, node, or database statement family.

**Stop and think:** A query grouped by `req_path` shows hundreds of paths such as `/users/1001`, `/users/1002`, and `/users/1003`. What would you change before deciding that hundreds of endpoints are slow? The right move is to normalize or filter the paths so dynamic IDs do not masquerade as unique operational routes.

You also need to understand what Pixie can and cannot see. If traffic is encrypted inside the process and the payload never appears in a parsable form at the observation point, Pixie may show connection and timing metadata without useful body content. That is still valuable for latency and dependency mapping, but it changes the kind of conclusion you can draw.

```python
import px

df = px.DataFrame('dns_events', start_time='-10m')
df = df[df.namespace == 'payments']
df.latency_ms = df.resp_latency / 1000000

failures = df[df.resp_code != 0]
failures = failures.groupby(['service', 'query_name', 'resp_code']).agg(
    failure_count=('resp_code', px.count),
    max_latency_ms=('latency_ms', px.max),
)

failures = failures.sort('failure_count', ascending=False)

px.display(failures, 'DNS failures by service and name')
```

Senior operators use Pixie queries as evidence, not as verdicts. A Pixie table can tell you that DNS failures rose sharply for checkout pods, but it does not automatically prove whether CoreDNS replicas are undersized, a NetworkPolicy blocked traffic, a search path caused excessive lookups, or an upstream resolver is slow. The next step is to connect the Pixie observation with Kubernetes objects, recent changes, and workload behavior.

---

## Worked Example: Debugging a Slow Checkout Path

This worked example demonstrates the problem-solution scaffolding you should use during a real incident. The scenario is intentionally realistic: users report intermittent checkout latency, the application dashboard shows normal handler timing for successful requests, and the team does not know whether the delay is in the application, database, DNS, or a downstream service. Pixie is useful here because it can inspect behavior around the application without waiting for a new build.

### Problem Statement

The `checkout-api` service in the `payments` namespace has a user-visible p99 latency spike. The service already emits application metrics, but those metrics only measure time inside the main handler. The platform team needs to identify whether the slow path is an HTTP dependency, a database query, a DNS lookup, or node-level contention.

The first principle is to avoid guessing the layer. Start broad enough to see which service and endpoint are slow, then narrow one layer at a time. Each step should produce a decision: continue with HTTP, pivot to DNS, inspect database calls, or leave Pixie and check another system.

```ascii
+--------------------+
| User symptom       |
| checkout is slow   |
+---------+----------+
          |
          v
+--------------------+
| Step 1             |
| find slow endpoint |
+---------+----------+
          |
          v
+--------------------+
| Step 2             |
| inspect dependency |
| calls from service |
+---------+----------+
          |
          v
+--------------------+
| Step 3             |
| compare database   |
| and DNS evidence   |
+---------+----------+
          |
          v
+--------------------+
| Step 4             |
| recommend fix and  |
| permanent telemetry|
+--------------------+
```

### Step 1: Find the Slow Endpoint

The first query asks which endpoint has the highest p99 latency in the affected namespace. It filters to meaningful traffic volume so a single odd request does not dominate the result. The output should tell the responder whether the problem is concentrated or spread across many routes.

```python
import px

df = px.DataFrame('http_events', start_time='-5m')
df = df[df.namespace == 'payments']
df.latency_ms = df.resp_latency / 1000000

endpoints = df.groupby(['service', 'req_method', 'req_path']).agg(
    request_count=('latency_ms', px.count),
    p50_ms=('latency_ms', px.quantiles(0.5)),
    p99_ms=('latency_ms', px.quantiles(0.99)),
    error_rate=('resp_status', lambda status: px.mean(status >= 400) * 100),
)

endpoints = endpoints[endpoints.request_count > 20]
endpoints = endpoints.sort('p99_ms', ascending=False)

px.display(endpoints.head(20), 'Slow payment endpoints')
```

Suppose the result shows `checkout-api` and `POST /checkout` at the top, with a high p99 but a low error rate. That combination suggests users wait too long but usually receive a response. This points away from a simple crash loop and toward a slow dependency, retry, queueing, or resource contention problem.

### Step 2: Inspect Outbound Calls from the Service

The next query looks for calls involving checkout pods. Depending on the exact fields available in your Pixie version and scripts, you may use service, pod, namespace, or remote address fields to identify caller and callee. The teaching point is the same: separate the inbound symptom from outbound behavior.

```python
import px

df = px.DataFrame('http_events', start_time='-5m')
df = df[df.namespace == 'payments']
df = df[df.ctx['pod'].contains('checkout-api')]
df.latency_ms = df.resp_latency / 1000000

calls = df.groupby(['service', 'req_method', 'req_path', 'remote_addr']).agg(
    request_count=('latency_ms', px.count),
    p95_ms=('latency_ms', px.quantiles(0.95)),
    p99_ms=('latency_ms', px.quantiles(0.99)),
    errors=('resp_status', lambda status: px.sum(status >= 400)),
)

calls = calls[calls.request_count > 5]
calls = calls.sort('p99_ms', ascending=False)

px.display(calls, 'Checkout-related HTTP calls')
```

If this query shows high latency when checkout calls `fraud-api`, the investigation has narrowed. You still do not know whether `fraud-api` is slow internally, whether DNS delays the call, or whether the network path is unstable, but you have a concrete dependency to inspect. This is a better conversation with the application team than "checkout feels slow."

### Step 3: Compare Database and DNS Evidence

Now test competing explanations. A slow checkout might come from a database query, a DNS lookup before calling `fraud-api`, or both. You should run targeted queries rather than continuing to stare at the first latency table.

```python
import px

db = px.DataFrame('pgsql_events', start_time='-5m')
db = db[db.namespace == 'payments']
db.latency_ms = db.resp_latency / 1000000

queries = db.groupby(['service', 'req_body']).agg(
    execution_count=('latency_ms', px.count),
    avg_ms=('latency_ms', px.mean),
    p99_ms=('latency_ms', px.quantiles(0.99)),
)

queries = queries[queries.execution_count > 5]
queries = queries.sort('p99_ms', ascending=False)

px.display(queries.head(10), 'Payment PostgreSQL queries')
```

If database latency is normal, pivot to DNS. DNS is a classic source of delay that application-level handler timing may not expose clearly, especially when clients perform lookups repeatedly or retry through multiple resolvers.

```python
import px

dns = px.DataFrame('dns_events', start_time='-5m')
dns = dns[dns.namespace == 'payments']
dns = dns[dns.service.contains('checkout')]
dns.latency_ms = dns.resp_latency / 1000000

dns_summary = dns.groupby(['service', 'query_name', 'resp_code']).agg(
    lookup_count=('latency_ms', px.count),
    p95_ms=('latency_ms', px.quantiles(0.95)),
    max_ms=('latency_ms', px.max),
)

dns_summary = dns_summary.sort('p95_ms', ascending=False)

px.display(dns_summary, 'Checkout DNS behavior')
```

Assume the DNS result shows repeated slow lookups for `fraud-api.payments.svc.cluster.local`, while database latency remains normal. The platform team now has a strong hypothesis: checkout latency is dominated by name resolution or resolver load, not by the checkout handler itself. The next Kubernetes checks should inspect CoreDNS health, resolver configuration, and recent traffic changes.

```bash
k get pods -n kube-system -l k8s-app=kube-dns -o wide
k top pods -n kube-system
k logs -n kube-system -l k8s-app=kube-dns --tail=100
k get configmap -n kube-system coredns -o yaml
```

### Step 4: Recommend the Fix and the Permanent Signal

A senior response does not stop at identifying DNS as "the issue." It states the immediate mitigation, the evidence supporting it, and the telemetry that should remain after the incident. For example, the team might scale CoreDNS, add NodeLocal DNSCache, fix excessive client lookups, or change application connection reuse behavior.

The permanent signal should probably not be "run Pixie manually every time checkout is slow." Pixie helped discover the gap, but the follow-up may be Prometheus alerts on CoreDNS latency, OpenTelemetry spans around dependency calls, or a dashboard that correlates checkout latency with DNS failures. This is how Pixie complements the rest of the observability stack instead of becoming an isolated incident tool.

```ascii
+------------------------+        +-------------------------+
| Pixie discovery        |        | Long-term control       |
| DNS lookup latency     +------->| CoreDNS metrics alert   |
+------------------------+        +-------------------------+
| Slow dependency call   +------->| OTel client span        |
+------------------------+        +-------------------------+
| High query latency     +------->| DB dashboard and SLO    |
+------------------------+        +-------------------------+
| Node-level contention  +------->| capacity policy         |
+------------------------+        +-------------------------+
```

The lesson from the worked example is not that every slow request is DNS-related. The lesson is the sequence: start with the symptom, use Pixie to expose uninstrumented behavior, compare multiple explanations, and turn the result into both an immediate fix and a durable observability improvement. That sequence is what separates tool usage from engineering judgment.

---

## Practical Use Cases: From Question to Query

A practical Pixie use case should be framed as a problem and a decision, not just a code snippet. The following patterns are reusable during incidents and design reviews. Each begins with a scenario, explains what evidence the query should produce, and names the next decision a platform engineer can make.

### Use Case 1: Find Slow Endpoints Without Redeploying Services

Problem: Users report slowness in a namespace where several teams deploy services, and not every service emits consistent latency metrics. You need a quick ranking of service paths by tail latency so responders do not waste time on healthy services.

Solution approach: Query HTTP events, constrain the time window and namespace, compute latency in milliseconds, aggregate by service and path, and filter low-volume noise. This does not replace service-owned metrics, but it gives the incident channel a fast shared starting point.

```python
import px

df = px.DataFrame('http_events', start_time='-5m')
df = df[df.namespace == 'payments']
df.latency_ms = df.resp_latency / 1000000

slow = df.groupby(['service', 'req_path', 'req_method']).agg(
    request_count=('latency_ms', px.count),
    p50_ms=('latency_ms', px.quantiles(0.5)),
    p99_ms=('latency_ms', px.quantiles(0.99)),
    error_rate=('resp_status', lambda status: px.mean(status >= 400) * 100),
)

slow = slow[slow.request_count > 10]
slow = slow.sort('p99_ms', ascending=False)

px.display(slow.head(20), 'Slowest endpoints in payments')
```

Decision: If one endpoint dominates tail latency, assign investigation to that service path. If many unrelated endpoints are slow, shift attention toward shared infrastructure such as DNS, ingress, database, node pressure, or a common downstream dependency.

### Use Case 2: Trace a Suspicious Request Pattern

Problem: A single customer workflow triggers failures, but the team does not have a trace ID because the application was not instrumented. You know the route, customer-safe identifier, or request shape and need to inspect recent traffic around it.

Solution approach: Filter HTTP events by path or header patterns that are safe to inspect under your privacy policy. Select fields that help compare request timing, status, and response behavior. Be careful with body fields in production because Pixie may expose sensitive payloads when protocol parsing is enabled.

```python
import px

df = px.DataFrame('http_events', start_time='-30m')
df = df[df.namespace == 'payments']
df = df[df.req_path.contains('/checkout')]

detail = df[[
    'time_',
    'pod',
    'service',
    'req_method',
    'req_path',
    'resp_status',
    'resp_latency',
    'remote_addr',
]]

px.display(detail, 'Recent checkout requests')
```

Decision: If the suspicious pattern correlates with one pod, inspect that pod and node. If it correlates with one downstream address, inspect that dependency. If it correlates with large payloads or specific user actions, involve the application owner and add durable tracing around that workflow.

### Use Case 3: Analyze Database Queries Before Blaming the Database

Problem: A service owner says "the database is slow," but the database team sees normal cluster-wide metrics. You need to identify whether one application is issuing expensive queries, repeating queries too often, or experiencing occasional tail latency.

Solution approach: Query database protocol events, group by client service and normalized statement if available, and compare count, average latency, and p99 latency. Avoid dumping raw query bodies into chat or tickets if they may contain sensitive data.

```python
import px

df = px.DataFrame('pgsql_events', start_time='-10m')
df = df[df.namespace == 'payments']
df.latency_ms = df.resp_latency / 1000000

queries = df.groupby(['service', 'req_body']).agg(
    execution_count=('latency_ms', px.count),
    avg_ms=('latency_ms', px.mean),
    p99_ms=('latency_ms', px.quantiles(0.99)),
    max_ms=('latency_ms', px.max),
)

queries = queries[queries.execution_count > 3]
queries = queries.sort('p99_ms', ascending=False)

px.display(queries.head(15), 'PostgreSQL query latency')
```

Decision: If one statement has high average latency, examine indexing and query plans. If many simple statements repeat excessively, examine client caching or N+1 behavior. If p99 is high while average is normal, look for lock contention, connection pool saturation, or intermittent infrastructure pressure.

### Use Case 4: Build a Service Dependency Map During an Incident

Problem: The architecture diagram in the wiki is out of date, and responders disagree about which services are actually in the checkout path. You need observed communication edges from recent live traffic.

Solution approach: Query HTTP events and group by source and destination fields available in your Pixie environment. The exact field names can vary across scripts and versions, so validate the table schema in your cluster. The goal is an observed dependency list that can be compared with the expected design.

```python
import px

df = px.DataFrame('http_events', start_time='-5m')
df = df[df.namespace == 'payments']

df.source_pod = df.ctx['pod']
df.destination = df.remote_addr
df.latency_ms = df.resp_latency / 1000000

edges = df.groupby(['source_pod', 'destination']).agg(
    request_count=('latency_ms', px.count),
    p50_ms=('latency_ms', px.quantiles(0.5)),
    error_count=('resp_status', lambda status: px.sum(status >= 400)),
)

edges = edges.sort('request_count', ascending=False)

px.display(edges, 'Observed service dependencies')
```

Decision: If an unexpected dependency appears, verify whether it is legitimate, stale, or caused by misconfiguration. If an expected dependency is absent, confirm whether traffic is routed differently, encrypted in a way Pixie cannot parse, or missing because PEM coverage is incomplete.

### Use Case 5: Investigate DNS Failures and Resolver Pressure

Problem: Application logs show intermittent connection failures, but service endpoints are healthy. The failure might happen before the connection is made, so normal HTTP latency dashboards do not show the missing time clearly.

Solution approach: Query DNS events for failed response codes, slow responses, and repeated lookup patterns. Combine this with CoreDNS metrics and Kubernetes service discovery checks before changing application code.

```python
import px

df = px.DataFrame('dns_events', start_time='-10m')
df = df[df.namespace == 'payments']
df.latency_ms = df.resp_latency / 1000000

dns = df.groupby(['service', 'query_name', 'resp_code']).agg(
    lookup_count=('latency_ms', px.count),
    p95_ms=('latency_ms', px.quantiles(0.95)),
    failure_count=('resp_code', lambda code: px.sum(code != 0)),
)

dns = dns.sort('failure_count', ascending=False)

px.display(dns, 'DNS lookup health')
```

Decision: If failures concentrate on one service name, check Kubernetes Service and EndpointSlice objects. If failures affect many names, inspect CoreDNS capacity, node-local DNS configuration, upstream resolver behavior, and recent traffic spikes.

### Use Case 6: Export a Discovered Signal to a Durable System

Problem: Pixie helped identify a latency signal that should become part of normal operations. The team needs to export an aggregate, not every raw request, to avoid privacy and cost problems.

Solution approach: Aggregate the signal in PxL and send the summarized data through an approved export path such as an OpenTelemetry collector. In production, design the export with labels, retention, and ownership before relying on it for alerts.

```python
import px

df = px.DataFrame('http_events', start_time='-1m')
df = df[df.namespace == 'payments']
df.latency_ms = df.resp_latency / 1000000

metrics = df.groupby(['service', 'req_path']).agg(
    request_count=('latency_ms', px.count),
    p99_ms=('latency_ms', px.quantiles(0.99)),
    error_rate=('resp_status', lambda status: px.mean(status >= 400) * 100),
)

px.export(metrics, px.otel.Data(
    endpoint='otel-collector.observability.svc.cluster.local:4317',
    resource={'service.name': 'pixie-derived-http'},
))
```

Decision: Export only the aggregates that answer durable operational questions. Keep raw exploration in Pixie, and move stable service-level signals into the organization's normal metric, trace, or log retention platform.

---

## Operating Pixie Responsibly

Pixie changes the visibility boundary, so it also changes the responsibility boundary. A tool that can reveal request metadata, database statements, and sometimes payload-like content must be operated with clear access controls and data-handling rules. Platform teams should treat Pixie as production observability infrastructure, not as a harmless debugging toy.

The first operating question is who can run which scripts against which clusters. A developer debugging a staging namespace may need broad visibility there, while production access may require a narrower role, audit trail, or incident ticket. The right policy depends on your organization, but the wrong policy is no policy.

The second question is retention. Pixie's local, recent-data model is useful because it avoids turning every observed event into a permanent external record. However, it also means you cannot rely on Pixie alone for after-the-fact investigations days later. If a signal matters for SLOs, capacity planning, or compliance, export an aggregate to a durable backend.

The third question is performance overhead. eBPF observability is efficient, but no production collector is free. High-cardinality queries, very busy clusters, and broad payload inspection can create pressure. Good operators limit scope, aggregate early, and validate collector health during load rather than assuming the overhead is always negligible.

| Operating Concern | Practical Policy | Senior-Level Trade-Off |
|---|---|---|
| Production access | Use role-based access and incident procedures. | Faster debugging must be balanced against sensitive data exposure. |
| Payload visibility | Avoid displaying bodies unless explicitly approved. | Payloads help root cause analysis but can create privacy and audit risk. |
| Retention | Treat Pixie as recent, local evidence by default. | Durable trends belong in Prometheus, tracing, logs, or a data warehouse. |
| Query cost | Filter by namespace, time, service, and volume. | Wide exploration is useful briefly, but repeated broad queries become noise. |
| Export design | Export aggregates with stable labels. | Raw exports increase cost and risk without necessarily improving decisions. |
| Tool ownership | Assign platform ownership for upgrades and compatibility. | eBPF tools depend on node and kernel behavior, not only Kubernetes YAML. |

Pixie also fits into a broader observability architecture. Prometheus remains the standard choice for durable numeric metrics and alerting. OpenTelemetry remains the preferred path for application-owned traces and semantic spans. Logs remain essential for discrete application events and error details. Pixie fills the exploratory gap when you need to see what is happening before you know what should have been instrumented.

```ascii
+--------------------------------------------------------------------------------+
|                         Layered Observability Strategy                          |
|                                                                                |
|  +------------------+     +------------------+     +------------------+        |
|  | Pixie            |     | OpenTelemetry    |     | Prometheus       |        |
|  | live discovery   |     | semantic traces  |     | durable metrics  |        |
|  +---------+--------+     +---------+--------+     +---------+--------+        |
|            |                        |                        |                 |
|            v                        v                        v                 |
|  +----------------------------------------------------------------------------+|
|  | Incident workflow                                                           ||
|  | discover hidden behavior -> add permanent signal -> alert on durable SLO     ||
|  +----------------------------------------------------------------------------+|
+--------------------------------------------------------------------------------+
```

A strong platform practice is to close the loop after every Pixie-assisted incident. Ask what Pixie revealed that existing telemetry missed, then decide whether that signal should become a metric, span, log field, runbook check, or architecture change. If Pixie repeatedly discovers the same missing signal, the organization has an instrumentation backlog, not just an incident response technique.

---

## Did You Know?

- Pixie can observe many common application protocols without application code changes, which makes it especially useful for services that are legacy, third-party, or temporarily deployed during an incident.
- Pixie's in-cluster data model helps reduce unnecessary external data movement, but access controls still matter because observed headers, statements, and payload-like fields can be sensitive.
- eBPF programs are verified before loading into the Linux kernel, which is one reason modern observability and networking projects can use kernel-level hooks without shipping custom kernel modules.
- Pixie is often most valuable as an instrumentation gap detector: it shows what the platform should later measure permanently with OpenTelemetry, Prometheus, logs, or SLO dashboards.

---

## Common Mistakes

| Mistake | Why It Hurts | Better Practice |
|---|---|---|
| Treating a successful install as proof of full coverage. | Pixie may be missing data from nodes where PEM pods are unscheduled or unhealthy. | Check DaemonSet readiness, pod placement, and query results from expected namespaces. |
| Running broad queries during an incident without a question. | Large tables create cognitive load and can hide the decision responders need to make. | Start with the user symptom, then filter by time, namespace, service, and suspected layer. |
| Assuming Pixie replaces application instrumentation. | Pixie can reveal behavior, but it does not automatically provide business semantics or long-term SLO history. | Use Pixie for discovery and OpenTelemetry or Prometheus for durable, owned signals. |
| Displaying request bodies or SQL statements casually. | Sensitive data may appear in protocol-level fields and leak into tickets or chat tools. | Redact, aggregate, or avoid payload fields unless the incident process explicitly permits them. |
| Blaming the slowest dependency after one query. | A high p99 table shows correlation, not the full causal chain. | Compare HTTP, DNS, database, connection, and Kubernetes evidence before recommending a fix. |
| Ignoring managed-cluster restrictions. | Some environments restrict privileged pods, host access, or eBPF capabilities. | Validate provider support and security policy before promising cluster-wide Pixie coverage. |
| Exporting raw Pixie events as a long-term strategy. | Raw exports can increase cost, cardinality, and privacy risk while duplicating better telemetry systems. | Export carefully chosen aggregates with stable labels and documented ownership. |
| Forgetting to convert time units consistently. | Nanoseconds, microseconds, and milliseconds can be confused, leading to wrong severity estimates. | Convert latency fields explicitly and label displayed columns with units. |

---

## Quiz

### Question 1

Your team receives a page that checkout latency is high, but the checkout service's application metrics show normal handler duration. Pixie shows repeated slow DNS lookups from checkout pods to `fraud-api.payments.svc.cluster.local`. What should you check next, and why is that a better next step than redeploying checkout with more logging?

<details>
<summary>Show Answer</summary>

Check CoreDNS health, DNS configuration, service discovery objects, and resolver behavior before redeploying checkout. Pixie has shown that delay may occur before the application dependency call completes, so adding handler logs may still miss the resolver layer. Useful commands include checking CoreDNS pods, logs, resource usage, and the relevant Service and EndpointSlice objects. Redeploying checkout might be useful later, but the immediate evidence points to infrastructure-level name resolution.
</details>

### Question 2

A Pixie HTTP query shows that every endpoint in a namespace has elevated p99 latency at the same time, but error rates remain low. One engineer wants to focus on the route at the top of the table because it is the slowest. How would you refine the investigation before assigning blame to that service?

<details>
<summary>Show Answer</summary>

When many unrelated endpoints slow down together, suspect shared dependencies or infrastructure before blaming one route. Refine the investigation by grouping traffic by node, downstream service, DNS behavior, database latency, and connection statistics. Also check whether the affected pods share a node pool, ingress path, resolver, or database. The slowest route may simply have the highest sensitivity to a shared bottleneck.
</details>

### Question 3

You installed Pixie in a production cluster and `px get viziers` reports healthy, but a service running on one node never appears in query results. What is the most likely class of problem, and what Kubernetes evidence would you gather?

<details>
<summary>Show Answer</summary>

The likely problem is incomplete node-level collection rather than a global Pixie outage. Check the PEM DaemonSet desired and ready counts, PEM pod placement with `k get pods -n pl -o wide`, and pod or DaemonSet descriptions for taints, node selectors, privilege restrictions, architecture mismatch, or crash loops. If the node lacks a healthy PEM, Pixie cannot observe that node's local workload behavior.
</details>

### Question 4

During a database incident, a PxL query grouped by raw SQL body shows thousands of unique rows because user IDs and timestamps are embedded in statements. The table is too noisy to identify the real pattern. What would you change in the query or workflow?

<details>
<summary>Show Answer</summary>

Avoid treating every raw statement as a separate operational pattern. Normalize statements if the available data supports it, group first by service and stable query family, filter to meaningful execution counts, and compare p99, average latency, and frequency. If normalization is not available in the query, sample carefully and move detailed SQL analysis into the database's query tools. The goal is to find a decision-grade pattern, not to display every unique statement.
</details>

### Question 5

A security reviewer objects to Pixie because it may expose headers or request bodies. Your platform team still wants the rapid debugging benefits. What operating model would you recommend?

<details>
<summary>Show Answer</summary>

Recommend a controlled operating model rather than unrestricted access. Limit production access by role and incident process, document which fields may be displayed, avoid payload fields by default, prefer aggregate queries, and export only approved summaries to durable systems. Also validate whether the deployment model keeps data inside the cluster or sends metadata to an external control plane. This preserves debugging value while addressing data-handling risk.
</details>

### Question 6

Pixie shows that `checkout-api` calls `fraud-api` with high p99 latency, while OpenTelemetry traces from checkout only show a generic "external call" span. How should the team use both tools to improve future incident response?

<details>
<summary>Show Answer</summary>

Use Pixie to identify the specific dependency and behavior quickly, then improve OpenTelemetry instrumentation so the application emits semantic spans for the fraud dependency, including stable attributes such as dependency name, route, status, timeout, and retry count. Pixie remains useful for discovery and uninstrumented behavior, while OpenTelemetry becomes the durable, application-owned signal for future alerts and trace analysis.
</details>

### Question 7

A responder wants to export every Pixie HTTP event to long-term storage because an incident was hard to reconstruct after the default retention window passed. What alternative would you propose, and what trade-off does it make?

<details>
<summary>Show Answer</summary>

Export selected aggregates rather than every raw event. For example, export per-service request count, p99 latency, error rate, and DNS failure counts with stable labels. This trades raw forensic detail for lower cost, lower cardinality, and reduced privacy risk. If raw request reconstruction is truly required, it should be handled through an explicitly approved logging or tracing design, not an accidental Pixie data dump.
</details>

### Question 8

A team runs a Pixie query for slow endpoints and finds a route with only two requests and very high latency. Another route has thousands of requests and moderately high p99 latency. Which one should usually drive the incident response first, and what query change supports that decision?

<details>
<summary>Show Answer</summary>

The high-volume route should usually drive the response first because it affects more users and is less likely to be a one-off outlier. Add a minimum request-count filter and sort by a combination of p99 latency, error rate, and traffic volume. The two-request route may still deserve investigation later, but it should not dominate the incident unless those requests are business-critical or tied to severe failures.
</details>

---

## Hands-On Exercise: Debug a Performance Issue with Pixie

**Objective**: Use Pixie to investigate a simulated performance problem without adding application instrumentation, then recommend which permanent observability signal should be added after the investigation.

### Scenario

A demo application in the `pixie-demo` namespace has several services and a database dependency. Users report that one workflow is slow, but you do not know whether the bottleneck is HTTP routing, database latency, DNS resolution, or a specific pod. Your task is to use Pixie as an exploratory tool and produce a short incident note based on evidence.

### Setup

Create a namespace and deploy the sample application. The manifest comes from the Pixie demo repository, so run it only in a disposable lab cluster where external manifest application is allowed.

```bash
k create namespace pixie-demo
k apply -n pixie-demo -f https://raw.githubusercontent.com/pixie-io/pixie-demos/main/simple-gotracing/k8s/demo.yaml
k wait --for=condition=ready pod --all -n pixie-demo --timeout=120s
k get pods -n pixie-demo -o wide
```

Before using Pixie, confirm that Pixie itself has node coverage. This prevents a common false conclusion where the application looks quiet only because the relevant node is not being observed.

```bash
k get pods -n pl -o wide
k get daemonset -n pl
px get viziers
```

### Task 1: Establish the Slow Service and Endpoint

Run a PxL query that ranks endpoints in `pixie-demo` by p99 latency. Use a recent time window and filter out endpoints with tiny request counts.

```python
import px

df = px.DataFrame('http_events', start_time='-5m')
df = df[df.namespace == 'pixie-demo']
df.latency_ms = df.resp_latency / 1000000

endpoints = df.groupby(['service', 'req_method', 'req_path']).agg(
    request_count=('latency_ms', px.count),
    p50_ms=('latency_ms', px.quantiles(0.5)),
    p99_ms=('latency_ms', px.quantiles(0.99)),
    error_rate=('resp_status', lambda status: px.mean(status >= 400) * 100),
)

endpoints = endpoints[endpoints.request_count > 5]
endpoints = endpoints.sort('p99_ms', ascending=False)

px.display(endpoints.head(10), 'Slowest demo endpoints')
```

Write down the top service, method, path, p99 latency, and request count. If no traffic appears, generate traffic through the demo application's documented endpoint or inspect whether the pods are ready and reachable.

### Task 2: Check Whether the Slow Path Calls Another Service

Build a dependency view from recent HTTP traffic. Your goal is not a perfect architecture diagram; your goal is to identify whether the slow service depends on another observed endpoint.

```python
import px

df = px.DataFrame('http_events', start_time='-5m')
df = df[df.namespace == 'pixie-demo']
df.latency_ms = df.resp_latency / 1000000
df.source_pod = df.ctx['pod']
df.destination = df.remote_addr

edges = df.groupby(['source_pod', 'service', 'destination']).agg(
    request_count=('latency_ms', px.count),
    p95_ms=('latency_ms', px.quantiles(0.95)),
    error_count=('resp_status', lambda status: px.sum(status >= 400)),
)

edges = edges[edges.request_count > 3]
edges = edges.sort('p95_ms', ascending=False)

px.display(edges, 'Observed dependency edges')
```

Compare this output with the endpoint ranking from Task 1. If the same destination appears in both views, investigate it as a candidate bottleneck. If no dependency stands out, broaden the investigation to DNS, database, and node placement.

### Task 3: Test the Database Hypothesis

Run a database query analysis for PostgreSQL events. If the demo version you deploy does not emit PostgreSQL traffic, record that as evidence and explain why you pivoted.

```python
import px

df = px.DataFrame('pgsql_events', start_time='-5m')
df = df[df.namespace == 'pixie-demo']
df.latency_ms = df.resp_latency / 1000000

queries = df.groupby(['service', 'req_body']).agg(
    execution_count=('latency_ms', px.count),
    avg_ms=('latency_ms', px.mean),
    p99_ms=('latency_ms', px.quantiles(0.99)),
)

queries = queries[queries.execution_count > 2]
queries = queries.sort('p99_ms', ascending=False)

px.display(queries.head(10), 'Demo database query latency')
```

Decide whether database latency is likely the dominant bottleneck. A good answer cites the query output and explains whether latency, frequency, or both support the conclusion.

### Task 4: Test the DNS Hypothesis

Run a DNS-focused query and look for failures or slow lookups. DNS may not be the issue in your run, but the exercise is to compare evidence rather than force a predetermined answer.

```python
import px

df = px.DataFrame('dns_events', start_time='-5m')
df = df[df.namespace == 'pixie-demo']
df.latency_ms = df.resp_latency / 1000000

dns = df.groupby(['service', 'query_name', 'resp_code']).agg(
    lookup_count=('latency_ms', px.count),
    p95_ms=('latency_ms', px.quantiles(0.95)),
    failure_count=('resp_code', lambda code: px.sum(code != 0)),
)

dns = dns.sort('p95_ms', ascending=False)

px.display(dns.head(20), 'Demo DNS behavior')
```

If DNS looks suspicious, inspect CoreDNS and the relevant Kubernetes Service objects. If DNS looks healthy, state that explicitly and continue with the stronger hypothesis.

```bash
k get svc,endpointslices -n pixie-demo
k get pods -n kube-system -l k8s-app=kube-dns -o wide
```

### Task 5: Produce an Incident Note

Write a short note with four parts: symptom, evidence, likely cause, and recommended permanent signal. The permanent signal might be an OpenTelemetry span around a dependency, a Prometheus alert on DNS latency, a database query dashboard, or a service-level latency SLO.

Use this structure:

```text
Symptom:
The observed user-facing symptom was ...

Evidence:
Pixie showed ... in the HTTP query.
Pixie showed ... in the dependency, database, or DNS query.

Likely cause:
The most likely bottleneck is ... because ...

Permanent signal:
The team should add ... so this condition is visible without ad hoc investigation next time.
```

### Success Criteria

- [ ] Confirmed Pixie control-plane health and PEM node coverage before trusting query results.
- [ ] Identified the slowest meaningful service endpoint using traffic volume and p99 latency.
- [ ] Built an observed dependency view and compared it with the slow endpoint evidence.
- [ ] Tested at least two competing hypotheses, such as database latency and DNS behavior.
- [ ] Wrote an incident note that separates evidence from interpretation.
- [ ] Recommended one permanent observability signal that should exist after the incident.
- [ ] Completed the investigation without changing application code or redeploying the demo service.

### Cleanup

Remove the demo workload after the exercise. Leave Pixie installed only if your lab environment is intended to keep it for later modules.

```bash
k delete namespace pixie-demo
```

---

## Next Module

Continue to [Module 1.7: Hubble - Network Observability with Cilium](../module-1.7-hubble/) to learn how Cilium and Hubble expose network flows, service communication, and policy-aware observability.

## Sources

- [github.com: pixie](https://github.com/pixie-io/pixie) — The Pixie GitHub README directly states that Pixie uses eBPF for automatic telemetry collection without manual instrumentation.
- [OpenTelemetry Collector](https://opentelemetry.io/docs/collector/) — Relevant for the module's recommendation to turn Pixie discoveries into durable exported telemetry.
- [Kubernetes DaemonSet](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/) — Useful background for understanding why Pixie validates PEM coverage node by node.
