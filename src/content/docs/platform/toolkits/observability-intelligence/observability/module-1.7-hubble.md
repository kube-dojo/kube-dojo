---
title: "Module 1.7: Hubble - Network Observability with Cilium"
slug: platform/toolkits/observability-intelligence/observability/module-1.7-hubble
sidebar:
  order: 8
---

## Complexity: [MEDIUM]

**Time to Complete**: 90 minutes

**Prerequisites**: Module 1.6 (Pixie), basic TCP/IP and DNS concepts, Kubernetes Services, Labels, Namespaces, and NetworkPolicy basics.

## Learning Outcomes

After completing this module, you will be able to:

- **Deploy** Hubble on a Cilium-backed Kubernetes cluster and verify that node-local flow collection, Hubble Relay, Hubble UI, and the CLI are working together.
- **Debug** failed service-to-service communication by filtering Hubble flows by namespace, pod, service, protocol, and verdict.
- **Compare** Hubble's eBPF-based flow visibility with packet capture, service mesh telemetry, and application logs so you can choose the right tool for an incident.
- **Evaluate** network policy behavior by connecting flow verdicts, labels, DNS requests, and Kubernetes policy selectors into one troubleshooting path.
- **Design** a practical observability workflow that exports useful Hubble metrics to Prometheus without turning network telemetry into unfiltered noise.

## Why This Module Matters

A platform engineer joins an incident bridge because checkout requests are timing out during a release. The application team sees generic database connection errors, the database team sees normal CPU and connection capacity, and the network team cannot find a failing node. Everyone has partial evidence, but nobody can answer the operational question that matters: which workload tried to talk to which destination, and what did the datapath decide to do with that traffic?

That gap is where Kubernetes network incidents become slow. Traditional troubleshooting often starts with shelling into pods, running `tcpdump`, comparing logs, and hoping the failing request repeats while the right capture is running. Those tools still matter, but they are awkward when the failure depends on labels, namespaces, Services, DNS names, network policies, and short-lived pods that may disappear before the capture begins.

Hubble changes the starting point. Because it is built on Cilium's eBPF datapath, it observes network flows where packet decisions happen, then attaches Kubernetes context such as pod names, namespaces, identities, Services, DNS records, protocols, and policy verdicts. Instead of asking only "did the application log an error," you can ask "did traffic leave the frontend pod, did it resolve the expected service name, did it reach the backend identity, and did any policy deny it?"

This module teaches Hubble as an operational debugging tool, not as a screenshot generator. You will start with the architecture, then install and verify the components, then use flow filters to diagnose increasingly realistic failures. By the end, Hubble should feel less like another dashboard and more like a structured way to test hypotheses about Kubernetes network behavior.

## Core Content

### 1. Build the Mental Model Before Running Commands

Hubble is not a separate CNI, packet sniffer sidecar, or service mesh. It is the observability layer for Cilium, and Cilium is the component that owns the network datapath. Cilium programs eBPF logic into the Linux kernel so packets can be observed and acted on without bouncing every decision through user-space proxies.

That detail matters because it explains both Hubble's strength and its boundary. Hubble can show you flow events, identities, DNS visibility, drop reasons, and policy verdicts because Cilium sees those decisions in the datapath. Hubble cannot be dropped into a cluster that uses another CNI and magically observe the same information, because the underlying instrumentation comes from Cilium.

A useful mental model is to think in three layers. The node layer collects flows from the local Cilium agent. The aggregation layer, Hubble Relay, gives clients a cluster-wide query point. The access layer, Hubble CLI and Hubble UI, lets humans and automation inspect the resulting stream.

```text
+------------------------------------------------------------------------------+
|                              Kubernetes Cluster                              |
|                                                                              |
|  +----------------------------- Access Layer --------------------------------+ |
|  |                                                                          | |
|  |   +-------------------+      +-------------------+      +---------------+ | |
|  |   | Hubble UI         |      | Hubble CLI        |      | Prometheus    | | |
|  |   | service map       |      | hubble observe    |      | metrics scrape| | |
|  |   +---------+---------+      +---------+---------+      +-------+-------+ | |
|  |             |                          |                        |         | |
|  +-------------+--------------------------+------------------------+---------+ |
|                                |                                             |
|                                v                                             |
|  +--------------------------- Aggregation Layer ----------------------------+ |
|  |                                                                          | |
|  |                         +---------------------+                          | |
|  |                         | Hubble Relay        |                          | |
|  |                         | cluster-wide gRPC   |                          | |
|  |                         +----------+----------+                          | |
|  |                                    |                                     | |
|  +------------------------------------+-------------------------------------+ |
|                                       |                                      |
|        +------------------------------+------------------------------+       |
|        |                              |                              |       |
|        v                              v                              v       |
|  +------------+                 +------------+                 +------------+ |
|  | Node one   |                 | Node two   |                 | Node three | |
|  | Cilium     |                 | Cilium     |                 | Cilium     | |
|  | agent plus |                 | agent plus |                 | agent plus | |
|  | Hubble     |                 | Hubble     |                 | Hubble     | |
|  | server     |                 | server     |                 | server     | |
|  +-----+------+                 +-----+------+                 +-----+------+ |
|        |                              |                              |       |
|        v                              v                              v       |
|  +------------+                 +------------+                 +------------+ |
|  | eBPF flow  |                 | eBPF flow  |                 | eBPF flow  | |
|  | events     |                 | events     |                 | events     | |
|  +------------+                 +------------+                 +------------+ |
|                                                                              |
+------------------------------------------------------------------------------+
```

The CLI and UI do not collect packets themselves. They query Relay, and Relay queries the Hubble servers embedded with Cilium agents on each node. If Relay is missing, you may still have node-local visibility, but your cluster-wide view will be incomplete or inconvenient.

| Component | Operational role | What you should verify first |
|---|---|---|
| Cilium agent | Programs the datapath and exposes node-local Hubble flow data | Each node has a healthy Cilium pod, and Hubble is enabled in Cilium values |
| Hubble server | Runs with the Cilium agent and serves flows for that node | Cilium status reports Hubble as enabled and reachable |
| Hubble Relay | Aggregates node-local flows into a cluster-wide API | Relay deployment is ready and `hubble status` can connect through it |
| Hubble CLI | Filters flows from a terminal during incidents and exercises | `hubble observe` returns current flows instead of only connection errors |
| Hubble UI | Visualizes service relationships and recent flow details | Port-forwarding opens the UI and the service map reflects live traffic |
| Prometheus metrics | Converts selected flow categories into time-series signals | Only useful metric categories are enabled and scraped by Prometheus |

**Stop and think:** If `hubble observe --verdict DROPPED` returns nothing during an incident, does that prove the network is healthy? It does not. It proves Hubble did not see dropped flows matching your current query while the command was running. You still need to check whether you filtered the right namespace, whether the failing request happened during the observation window, whether Relay can reach all nodes, and whether the problem is above the network layer.

### 2. Install Hubble With a Verification-First Habit

Installing Hubble is straightforward when Cilium is already your CNI, but operational confidence comes from verifying each dependency in order. First verify Cilium, then verify Hubble inside Cilium, then verify Relay, then verify the CLI and UI. If you skip that sequence, a later troubleshooting session can be confused by an observability failure that looks like an application failure.

The examples below use full commands first. In later commands, `k` is used as the standard shorthand alias for `kubectl`; define it in your shell only after you understand that it is just an alias for the same Kubernetes CLI.

```bash
alias k=kubectl
```

For a new lab cluster, install Cilium with Hubble, Relay, UI, and a focused metrics set enabled. In production, you would pin versions through your platform's normal release process and test values in a non-production cluster before changing the datapath.

```bash
cilium install \
  --set hubble.enabled=true \
  --set hubble.relay.enabled=true \
  --set hubble.ui.enabled=true \
  --set hubble.metrics.enabled="{dns,drop,tcp,flow,icmp,http}"
```

Wait for Cilium to report readiness before you test Hubble itself. This step checks the health of the Cilium-managed networking layer rather than only checking whether Kubernetes created a Deployment object.

```bash
cilium status --wait
```

If Cilium already exists and was installed through Helm, enable Hubble through a Helm upgrade that reuses the existing values. This approach avoids accidentally resetting unrelated Cilium settings during a small observability change.

```bash
helm upgrade cilium cilium/cilium \
  --namespace kube-system \
  --reuse-values \
  --set hubble.enabled=true \
  --set hubble.relay.enabled=true \
  --set hubble.ui.enabled=true \
  --set hubble.metrics.enabled="{dns,drop,tcp,flow,icmp,http}"
```

Install the Hubble CLI on the workstation or runner that will query the cluster. The CLI is not the data collector; it is the client that asks Relay for flow records.

```bash
HUBBLE_VERSION=$(curl -s https://raw.githubusercontent.com/cilium/hubble/master/stable.txt)

curl -L --fail --remote-name-all \
  "https://github.com/cilium/hubble/releases/download/${HUBBLE_VERSION}/hubble-linux-amd64.tar.gz"

sudo tar xzvfC hubble-linux-amd64.tar.gz /usr/local/bin
```

Now test the pieces in a sequence that narrows failure quickly. A healthy result from `cilium status` should show Cilium ready and Hubble components available. A healthy result from `hubble status` should show that the CLI can reach the Hubble API and that flows are being observed.

```bash
cilium status

hubble status
```

Expected status output varies by version and cluster shape, but the important details are stable. You want Relay to be reachable, the observed flow buffer to be active, and current flow counters to change when workloads communicate.

```text
Healthcheck (via localhost:4245): Ok
Current/Max Flows: 8192/8192
Flows/s: 12.5
Connected Nodes: 3/3
```

When the UI is enabled, open it through the Cilium helper command or an explicit port-forward. Prefer `127.0.0.1` in local instructions because it avoids ambiguity about IPv4 and IPv6 localhost resolution.

```bash
cilium hubble ui

k -n kube-system port-forward svc/hubble-ui 12000:80
```

Open `http://127.0.0.1:12000` and generate a few requests between pods if the service map looks empty. Hubble is event-driven; a quiet lab cluster may show little until traffic actually happens.

```text
+--------------------------------------------------------------------------+
|                                Hubble UI                                 |
|                                                                          |
|  +------------------------------ Service Map ---------------------------+ |
|  |                                                                      | |
|  |      +-------------+        HTTP 200         +-------------+         | |
|  |      | frontend    | ----------------------> | api         |         | |
|  |      | ns: shop    |                         | ns: shop    |         | |
|  |      +------+------+                         +------+------+         | |
|  |             |                                       |                | |
|  |             | DNS A lookup                          | TCP 5432       | |
|  |             v                                       v                | |
|  |      +-------------+                         +-------------+         | |
|  |      | kube-dns    |                         | postgres    |         | |
|  |      | kube-system |                         | ns: data    |         | |
|  |      +-------------+                         +-------------+         | |
|  |                                                                      | |
|  +----------------------------------------------------------------------+ |
|                                                                          |
|  +------------------------------ Flow Table ----------------------------+ |
|  | Source            Destination          Protocol     Verdict           | |
|  | shop/frontend     shop/api             HTTP         FORWARDED         | |
|  | shop/frontend     kube-system/kube-dns DNS          FORWARDED         | |
|  | shop/api          data/postgres        TCP          DROPPED           | |
|  +----------------------------------------------------------------------+ |
|                                                                          |
+--------------------------------------------------------------------------+
```

**Pause and predict:** You enable Hubble UI but the service map remains blank while all pods are ready. Before changing Helm values, what is the simplest test you should run? Generate traffic between two known pods, then run `hubble observe` at the same time. A blank UI can mean "no recent flows" rather than "Hubble is broken."

### 3. Read Flows as Evidence, Not as Noise

The fastest way to make Hubble useless is to run `hubble observe` with no filters in a busy cluster and stare at a scrolling wall of events. Senior operators start with a question, translate that question into a filter, and then change one variable at a time. Hubble is powerful because it can answer precise questions, not because every flow is equally important.

Start broad only long enough to prove that the stream works. Then narrow by namespace, pod, service, protocol, verdict, or direction. The goal is to move from "the system is broken" to "this identity sent this protocol to this destination and received this verdict."

```bash
hubble observe
```

A compact flow line usually gives you timestamp, source, destination, protocol, direction, and verdict. Treat it like a structured clue. The source and destination tell you which Kubernetes identities are involved. The protocol tells you which layer you are observing. The verdict tells you whether the datapath forwarded, dropped, or denied the traffic.

```text
Apr 26 10:15:12.521 shop/frontend-6b8d9 shop/api-7d6c9 L7/HTTP to-endpoint FORWARDED GET /checkout 200
Apr 26 10:15:12.548 shop/api-7d6c9 kube-system/coredns L7/DNS to-endpoint FORWARDED A postgres.data.svc.cluster.local
Apr 26 10:15:12.552 shop/api-7d6c9 data/postgres-0 L4/TCP to-endpoint DROPPED Policy denied
```

The three lines above tell a story. The frontend reached the API successfully, the API asked DNS for the database service name, and the API's TCP connection to the database pod was dropped by policy. That is very different from "PostgreSQL is down" or "DNS is broken."

Use namespace filters when you know the application boundary. This keeps shared cluster traffic from hiding the evidence you care about.

```bash
hubble observe --namespace shop
```

Use source and destination filters when the incident has a known caller or callee. These filters are especially useful during rollout incidents where only one version or one Deployment is failing.

```bash
hubble observe --from-pod shop/frontend-6b8d9

hubble observe --to-pod data/postgres-0

hubble observe --to-service kube-system/kube-dns
```

Use verdict filters when the symptom suggests denied or dropped traffic. A timeout often deserves a dropped-flow query before a deep application trace, because denied traffic may never produce a useful application-level error.

```bash
hubble observe --verdict DROPPED

hubble observe --verdict POLICY_DENIED
```

Use protocol filters when you are testing a layer-specific hypothesis. DNS failures, TCP resets, and HTTP server errors look different in Hubble, and they lead to different owners and fixes.

```bash
hubble observe --protocol DNS

hubble observe --protocol TCP

hubble observe --protocol HTTP
```

The choice of output format depends on the task. Human triage usually starts with compact output. Automation and deep inspection usually need JSON because you can extract exact fields without parsing columns by hand.

```bash
hubble observe --output compact

hubble observe --output json | jq '.flow | {source, destination, verdict, drop_reason_desc}'
```

A practical debugging loop uses two terminals. In the first terminal, run the most specific Hubble query you can defend. In the second terminal, generate one request that should succeed or fail. This removes guesswork about whether the relevant request happened during your observation window.

```bash
hubble observe --namespace shop --to-pod data/postgres-0 --verdict DROPPED
```

```bash
k -n shop exec deploy/api -- sh -c 'nc -vz postgres.data.svc.cluster.local 5432'
```

| Question you are asking | Hubble filter to start with | What a useful answer looks like |
|---|---|---|
| Is anything being denied by policy right now? | `hubble observe --verdict POLICY_DENIED` | A source, destination, and denied verdict appear during the failing request |
| Is this namespace producing the failure? | `hubble observe --namespace shop` | Only flows from the application boundary are shown |
| Is DNS part of the symptom? | `hubble observe --protocol DNS` | Query names, response types, and failures are visible |
| Is one pod version the caller? | `hubble observe --from-pod shop/api-abc123` | Flows from the suspected pod can be compared with a healthy pod |
| Is the database actually receiving traffic? | `hubble observe --to-pod data/postgres-0` | Successful or dropped inbound flows to the database identity are visible |
| Is this an HTTP error rather than network denial? | `hubble observe --protocol HTTP` | HTTP method, path, and status appear when L7 visibility is enabled |

**Stop and think:** A checkout request returns HTTP 500, and Hubble shows `FORWARDED` HTTP traffic from frontend to API. Should you keep debugging NetworkPolicy first? Probably not. A forwarded verdict means the datapath allowed that leg, so the next hypothesis should move toward API behavior, downstream calls, or another flow from the API to a dependency.

### 4. Debug Network Policy With a Worked Example

NetworkPolicy debugging is where Hubble often pays for itself first. Kubernetes policies are selector-based, and selector mistakes are easy to miss in review. A policy can be syntactically valid, applied successfully, and still deny the traffic the team intended to allow.

The worked example below follows a pattern you can reuse during real incidents. First establish the expected path. Then observe the failing request. Then inspect the policy selectors and pod labels. Finally choose whether to fix the policy, the labels, or the application boundary.

Imagine a simple checkout system. The `shop/frontend` pod calls `shop/api`, and the `shop/api` pod connects to `data/postgres`. A new deny-by-default policy was added to the `data` namespace, and the checkout path now times out.

```text
+--------------------+        HTTP         +--------------------+
| shop/frontend      | ------------------> | shop/api           |
| labels: app=web    |                     | labels: app=api    |
+--------------------+                     +---------+----------+
                                                    |
                                                    | TCP 5432
                                                    v
                                          +--------------------+
                                          | data/postgres      |
                                          | labels: app=db     |
                                          +--------------------+

Expected policy intent:
- allow shop/api to connect to data/postgres on TCP 5432
- deny every other inbound connection to data/postgres
```

Start with a targeted Hubble query against the destination. This avoids unrelated drops from other namespaces and makes the evidence easier to read.

```bash
hubble observe --to-pod data/postgres-0 --verdict DROPPED --output compact
```

Generate one failing request from the API pod. The exact command depends on the image, but `nc` is enough to test a TCP connection when it is available.

```bash
k -n shop exec deploy/api -- sh -c 'nc -vz postgres.data.svc.cluster.local 5432'
```

Hubble now shows a policy denial against the database destination.

```text
Apr 26 10:38:22.191 shop/api-5f6d9 data/postgres-0 L4/TCP to-endpoint DROPPED Policy denied
```

The flow proves that the request reached the datapath and was denied before it reached the database container. That moves the investigation away from database capacity and toward label or policy matching.

Inspect the policy that protects the database pods. The example policy below intends to allow API pods, but it matches `role: api` while the Deployment uses `app: api`.

```bash
k -n data get networkpolicy allow-api-to-postgres -o yaml
```

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-api-to-postgres
  namespace: data
spec:
  podSelector:
    matchLabels:
      app: db
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: shop
      podSelector:
        matchLabels:
          role: api
    ports:
    - protocol: TCP
      port: 5432
```

Now inspect the API labels rather than guessing. Selector bugs are evidence problems; you want the actual label set from the running workload.

```bash
k -n shop get pod -l app=api --show-labels
```

```text
NAME                       READY   STATUS    RESTARTS   AGE   LABELS
api-5f6d9cbb9c-r8k2m       1/1     Running   0          12m   app=api,pod-template-hash=5f6d9cbb9c
```

The policy and pod labels do not align. You have two defensible fixes. You can change the workload to include `role: api` if that label is part of the platform's identity standard, or you can change the policy selector to match `app: api` if that is the correct label contract for this application. Do not choose by habit; choose by the label standard your organization uses.

Here is the policy-side fix when `app: api` is the intended selector. It preserves the namespace selector so a pod named `api` in another namespace is not accidentally allowed.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-api-to-postgres
  namespace: data
spec:
  podSelector:
    matchLabels:
      app: db
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: shop
      podSelector:
        matchLabels:
          app: api
    ports:
    - protocol: TCP
      port: 5432
```

Apply the fix, then rerun the same Hubble query while generating the same request. Using the same query matters because it validates the exact failure path you observed earlier.

```bash
k apply -f allow-api-to-postgres.yaml

hubble observe --to-pod data/postgres-0 --output compact
```

```bash
k -n shop exec deploy/api -- sh -c 'nc -vz postgres.data.svc.cluster.local 5432'
```

A successful result should now show a forwarded TCP flow instead of a dropped one. If the request still fails, keep the query focused and inspect whether DNS, service endpoints, or another policy layer is the next obstacle.

```text
Apr 26 10:43:11.083 shop/api-5f6d9 data/postgres-0 L4/TCP to-endpoint FORWARDED
```

This worked example is deliberately simple, but the reasoning pattern scales. Hubble gives you a flow verdict, Kubernetes gives you policy and label state, and your job is to connect them without inventing a story that the evidence does not support.

| Evidence | What it suggests | Next action |
|---|---|---|
| `DROPPED Policy denied` to the expected destination | The datapath denied the flow, commonly through policy | Inspect NetworkPolicy, Cilium policy, labels, namespaces, and identities |
| DNS query is missing before a service connection | The application may not be resolving the expected name | Observe DNS flows and test the exact DNS name from the caller pod |
| DNS succeeds but TCP to the service backend drops | Name resolution works, but the datapath blocks or cannot route the connection | Filter by destination pod or service and inspect policy verdicts |
| Frontend to API is forwarded but API to database drops | The first hop is healthy, and the downstream dependency path is failing | Move the Hubble filter from frontend traffic to API egress |
| Flows appear from only some pod replicas | Labels, rollout version, node placement, or identity state may differ | Compare labels and flow output for a healthy and unhealthy replica |
| No matching flows appear during a reproduced failure | The request may not be leaving the pod, your filter may be wrong, or Relay may be incomplete | Reduce filters, verify Relay node coverage, and test with a direct command |

### 5. Use L7 Visibility, Metrics, and the UI Deliberately

Hubble can show Layer 7 information such as HTTP methods, paths, status codes, DNS queries, and gRPC visibility when Cilium is configured to observe that traffic. This is powerful, but it should be used with intent. Layer 4 tells you whether a connection was allowed or dropped; Layer 7 helps you understand request behavior after the network path exists.

For HTTP troubleshooting, first check whether L7 visibility is enabled for the traffic you care about. If it is enabled, Hubble can show request methods, paths, and response statuses. If it is not enabled, you may still see TCP flows, but you should not expect HTTP fields to appear.

```bash
hubble observe --protocol HTTP --namespace shop
```

```text
Apr 26 11:02:19.302 shop/frontend shop/api L7/HTTP to-endpoint FORWARDED GET /checkout 200
Apr 26 11:02:20.106 shop/frontend shop/api L7/HTTP to-endpoint FORWARDED POST /orders 500
```

This output changes your incident path. A `FORWARDED` HTTP 500 is not a network denial. It says the request reached the service and the service returned a server error. Hubble can still help by showing which downstream calls followed, but the owner discussion should shift toward application behavior and dependencies.

DNS visibility is often the bridge between application symptoms and network facts. Many "network" incidents begin with a bad service name, a missing endpoint, or an unexpected external lookup. Hubble's DNS flow records can show the queried name and response behavior while keeping the query tied to the source workload.

```bash
hubble observe --protocol DNS --from-pod shop/api-5f6d9
```

For alerting, use Hubble metrics as trend signals rather than as a replacement for flow investigation. Prometheus metrics are aggregated over time; flow output gives specific examples. Good operations use both: metrics tell you that drops increased, and Hubble flow queries show which identities and destinations explain the increase.

```promql
rate(hubble_drop_total[5m])
```

```promql
sum(rate(hubble_http_requests_total{http_status=~"5.."}[5m]))
/
sum(rate(hubble_http_requests_total[5m]))
```

```promql
sum by (protocol) (rate(hubble_flows_processed_total[5m]))
```

Be selective when enabling metrics categories. DNS, drop, TCP, flow, ICMP, and HTTP can all be useful, but more metrics are not automatically better. Every metric family adds cardinality, storage, and dashboard maintenance, so choose metrics that connect to operational questions your team actually acts on.

| Signal | Good alerting use | Bad alerting use |
|---|---|---|
| Drop rate | Detect sudden increases in denied or dropped traffic for critical namespaces | Page on any single dropped packet in a noisy shared cluster |
| DNS errors | Catch service discovery failures after a rollout or DNS outage | Treat every NXDOMAIN as an incident without workload context |
| HTTP error ratio | Correlate network paths with application server errors | Assume every HTTP 500 is caused by the network |
| Flow volume | Notice traffic shape changes during releases or incidents | Use raw flow volume as a service health score |
| TCP flags | Investigate connection reset or handshake patterns | Alert without a baseline for the workload's normal behavior |
| ICMP | Debug reachability and network diagnostics in controlled environments | Enable broadly without knowing whether teams use ICMP meaningfully |

The UI is most useful when humans need to form or challenge a mental model quickly. During an incident, a service map can reveal an unexpected dependency or a missing edge faster than a terminal can. During a design review, it can show whether actual runtime communication matches the architecture diagram.

The CLI is better when you need precision, repeatability, and copyable evidence. A senior troubleshooting habit is to use the UI to orient and the CLI to prove. The UI helps you ask a better question; the CLI gives you the exact flow record that belongs in the incident timeline.

```text
+----------------------+-------------------------+----------------------------+
| Task                 | Prefer Hubble UI        | Prefer Hubble CLI          |
+----------------------+-------------------------+----------------------------+
| First orientation    | See service map quickly | Use broad filters if no UI |
| Incident evidence    | Screenshot relationships| Capture exact flow records |
| Automation           | Not suitable            | JSON output with jq        |
| Policy debugging     | Helpful for topology    | Essential for verdicts     |
| Team walkthrough     | Strong visual aid       | Good for command replay    |
| Metrics correlation  | Limited                 | Pair with Prometheus query |
+----------------------+-------------------------+----------------------------+
```

### 6. Compare Hubble With Nearby Tools and Design the Workflow

Hubble does not replace every network observability tool. It gives Cilium-aware, Kubernetes-aware flow visibility with low overhead and strong policy context. Packet capture, service mesh telemetry, application tracing, logs, and node metrics still have their places. The skill is knowing where Hubble should sit in the diagnostic order.

Use Hubble early when the symptom might involve service reachability, DNS, network policy, unexpected dependencies, or traffic direction. Use packet capture when you need payload-level packet evidence beyond what Hubble exposes. Use service mesh telemetry when you need mesh-level retries, mTLS identities, route rules, or proxy behavior. Use application traces when the request is forwarded but business logic or downstream latency is the suspected failure.

| Tool | Best question it answers | Main limitation |
|---|---|---|
| Hubble | Which Kubernetes identity talked to which destination, and what verdict did the datapath produce? | Requires Cilium and does not replace every packet-level or application-level detail |
| tcpdump or Wireshark | What packets appeared on this interface, with exact low-level protocol details? | Usually local, manual, and weak on Kubernetes identity context |
| Service mesh telemetry | What did the proxy observe for HTTP, gRPC, mTLS, retries, and routes? | Depends on mesh coverage and may miss traffic outside the mesh |
| Application logs | What did the application believe happened in its own code path? | Often lacks network policy and datapath context |
| Distributed tracing | Which service spans contributed to request latency or failure? | Requires instrumentation and usually starts after the request reaches the application |
| Prometheus metrics | Is a network-related signal increasing over time? | Aggregates behavior and rarely explains a single failed request by itself |

A mature workflow connects these tools instead of forcing them to compete. Start with the symptom and scope. Use metrics to see whether the issue is widespread or isolated. Use Hubble to verify the network path and policy decisions. Use logs and traces once Hubble shows that traffic is forwarded into the application path. Escalate to packet capture only when the flow evidence points to a deeper protocol or node-level question.

The best platform teams also turn incident lessons into reusable filters and dashboards. If a checkout dependency failed once because of a policy selector, create a runbook command that observes checkout-to-database drops. If DNS failures caused a release incident, add a dashboard panel for DNS response behavior by namespace. Hubble is most valuable when it becomes part of the team's repeatable troubleshooting language.

## Did You Know?

- Hubble gets its Kubernetes-aware flow context from Cilium's eBPF datapath, which is why it can connect network events to pods, namespaces, identities, Services, DNS, and policy verdicts.
- Hubble Relay is what makes a cluster-wide query practical; without it, each node's local Hubble server only knows about flows observed on that node.
- Hubble's Layer 7 visibility depends on Cilium configuration and policy context, so HTTP fields may be absent even when Layer 4 TCP flows are visible.
- Hubble metrics are most useful when they are paired with targeted flow queries, because metrics show trends while flow records show concrete examples.

## Common Mistakes

| Mistake | Why it hurts | Better practice |
|---|---|---|
| Installing Hubble without verifying Cilium health first | Hubble depends on the Cilium datapath, so a Cilium issue can masquerade as an observability issue | Run `cilium status --wait` before interpreting Hubble output |
| Forgetting Hubble Relay in multi-node clusters | Node-local visibility can miss flows from other nodes and produce misleading confidence | Enable Relay and confirm `hubble status` reports connected nodes |
| Running unfiltered `hubble observe` during a noisy incident | Important evidence scrolls past and the team starts pattern-matching instead of testing hypotheses | Begin broad only for health, then filter by namespace, pod, destination, protocol, or verdict |
| Treating no dropped flows as proof of no network problem | The failing request may not have occurred during the query, or your filters may exclude it | Reproduce one request while the query is running and reduce filters if needed |
| Assuming every HTTP 500 is a network policy issue | A forwarded HTTP 500 usually means the network path succeeded and the application returned an error | Follow the next downstream flow or move to logs and traces after confirming `FORWARDED` |
| Enabling every metric category everywhere | High-cardinality telemetry can become expensive and difficult to interpret | Enable metrics that support concrete alerts, dashboards, or runbooks |
| Fixing policy selectors without checking live pod labels | YAML intent and runtime labels often drift, especially during rollouts | Compare NetworkPolicy selectors with `k get pod --show-labels` before changing policy |
| Using the UI as the only incident record | Screenshots help orientation but are weak evidence for exact timing and verdict fields | Capture CLI output or JSON flow records for the incident timeline |

## Quiz

### Question 1

Your team deploys a new `payments` release, and the `checkout` service starts timing out when it calls `payments.payments.svc.cluster.local`. The Hubble UI shows no obvious red edge, but users are still failing requests. What Hubble CLI workflow would you run before changing any policy?

<details>
<summary>Show Answer</summary>

Run a focused observation while reproducing one request, for example `hubble observe --namespace payments --verdict DROPPED` or `hubble observe --to-service payments/payments --output compact`, then generate a single checkout request. The important move is pairing a targeted query with a controlled reproduction. If no matching flows appear, reduce filters and verify Relay coverage before concluding that policy is not involved.
</details>

### Question 2

A developer says, "Hubble shows `FORWARDED` from frontend to API, so the network is completely fine." The user-facing request still fails with a server error. How would you evaluate that claim?

<details>
<summary>Show Answer</summary>

The claim is too broad. A forwarded frontend-to-API flow only proves that one hop was allowed by the datapath. You would next inspect API-to-dependency flows, HTTP status fields if L7 visibility is enabled, DNS lookups from the API pod, and application logs or traces. Hubble helps narrow the failing segment rather than proving the entire request path is healthy from one flow.
</details>

### Question 3

A database NetworkPolicy is supposed to allow traffic from `shop/api`, but Hubble shows `DROPPED Policy denied` for `shop/api` to `data/postgres-0`. What evidence should you collect before editing the policy?

<details>
<summary>Show Answer</summary>

Collect the exact Hubble flow, the NetworkPolicy YAML, the labels on the source pods, the labels on the destination pods, and the namespace labels involved in the selector. The likely issue is a selector mismatch, but the fix should be based on runtime labels and intended label contracts. Editing the policy without checking labels can accidentally allow the wrong workloads.
</details>

### Question 4

After enabling Hubble metrics, Prometheus shows a sudden increase in `hubble_drop_total` for a shared cluster. A teammate wants to page the database team immediately. What should you do next?

<details>
<summary>Show Answer</summary>

Use the metric as a trend signal, then run Hubble flow queries to identify source namespaces, destinations, verdict reasons, and timing. A shared-cluster drop increase may come from expected policy enforcement, a noisy test namespace, or a real incident. You should page a team only after connecting the aggregate metric to concrete affected workloads or services.
</details>

### Question 5

A service map in Hubble UI shows `frontend` calling `api`, but it does not show `api` calling `postgres`. The application logs show database timeouts. What are two plausible explanations, and how would you distinguish them?

<details>
<summary>Show Answer</summary>

One explanation is that the API never attempts the database connection because the request fails earlier in application code. Another is that your observation window or UI view missed the flow. Distinguish them by running `hubble observe --from-pod <api-pod> --output compact` while triggering one request, then separately observe DNS and TCP flows to the database service or pod.
</details>

### Question 6

Your cluster uses Cilium and Hubble, but a platform review asks whether Hubble replaces packet capture for all network investigations. How would you recommend using the tools together?

<details>
<summary>Show Answer</summary>

Use Hubble early for Kubernetes-aware flow evidence, policy verdicts, DNS visibility, identities, and service relationships. Use packet capture when you need low-level packet details that Hubble does not expose, such as protocol edge cases or payload-level inspection in a controlled environment. Hubble narrows the search space; packet capture remains useful for deeper protocol analysis.
</details>

### Question 7

A rollout creates two API ReplicaSets. One works, and one cannot reach Redis. Hubble shows drops only from pods in the new ReplicaSet. What should your next investigation step be?

<details>
<summary>Show Answer</summary>

Compare labels and identities between the working and failing pods, then compare the relevant NetworkPolicy selectors. Because only the new ReplicaSet fails, the likely cause is label drift, namespace or identity mismatch, or a rollout template change rather than a global Redis outage. Hubble has already narrowed the problem to a specific source group.
</details>

### Question 8

An HTTP dashboard built from Hubble metrics shows a high error ratio for `shop/api`, but Hubble CLI shows forwarded traffic for frontend-to-API requests. What follow-up evidence would help decide whether this is a network incident or an application incident?

<details>
<summary>Show Answer</summary>

Inspect Hubble flows from `shop/api` to its downstream dependencies, including DNS and database or cache traffic, while reproducing a failing request. If downstream flows are denied or dropped, the network path remains suspect. If the network path is forwarded and HTTP statuses show the API returning errors, move to application logs, traces, recent deploy changes, and dependency health.
</details>

## Hands-On Exercise: Diagnose and Fix a Policy-Denied Flow

**Objective**: Use Hubble to identify a broken NetworkPolicy, explain why it failed, apply a minimal fix, and verify the corrected traffic with flow evidence.

This exercise assumes a Kubernetes cluster running Cilium with Hubble and Hubble Relay enabled. It creates three namespaces and a small application path: a frontend pod calls an API service, and the API namespace is protected by a policy that initially uses the wrong selector.

### Step 1: Prepare the Lab Namespaces

Create the namespaces and confirm they exist before applying workloads. Keeping each tier in its own namespace makes the policy behavior easier to see in Hubble output.

```bash
k create namespace frontend
k create namespace backend
k create namespace database

k get namespaces frontend backend database
```

### Step 2: Deploy the Test Workloads

Apply the frontend curl pod, backend nginx API pod, backend Service, database pod, and database Service. The database workload is present to make the topology realistic, but the main failure you will debug is frontend-to-backend ingress.

```bash
k apply -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: frontend
  namespace: frontend
  labels:
    app: frontend
spec:
  containers:
  - name: curl
    image: curlimages/curl:latest
    command:
    - /bin/sh
    - -c
    - sleep infinity
---
apiVersion: v1
kind: Pod
metadata:
  name: api
  namespace: backend
  labels:
    app: api
spec:
  containers:
  - name: nginx
    image: nginx:alpine
---
apiVersion: v1
kind: Service
metadata:
  name: api
  namespace: backend
spec:
  selector:
    app: api
  ports:
  - port: 80
    targetPort: 80
---
apiVersion: v1
kind: Pod
metadata:
  name: postgres
  namespace: database
  labels:
    app: postgres
spec:
  containers:
  - name: postgres
    image: postgres:15-alpine
    env:
    - name: POSTGRES_PASSWORD
      value: testpass
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: database
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
EOF
```

Wait for the pods to become ready. This step prevents you from confusing startup delay with network failure.

```bash
k wait --for=condition=ready pod/frontend -n frontend --timeout=90s
k wait --for=condition=ready pod/api -n backend --timeout=90s
k wait --for=condition=ready pod/postgres -n database --timeout=90s
```

### Step 3: Prove the Baseline Path Works

Before applying policy, test the frontend-to-API path. A baseline matters because it proves the Service name, endpoints, and pod readiness are correct before you introduce the policy failure.

```bash
k -n frontend exec frontend -- curl -s --max-time 5 api.backend.svc.cluster.local
```

You should receive the default nginx response. If this fails before policy is applied, fix the workload or Service first because Hubble would otherwise be explaining the wrong problem.

### Step 4: Apply a Policy With an Intentional Selector Bug

Apply a NetworkPolicy that selects the backend API pod but only allows ingress from pods labeled `tier: web`. The frontend pod has `app: frontend`, so the policy will deny the expected caller.

```bash
k apply -f - <<'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-policy
  namespace: backend
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: frontend
      podSelector:
        matchLabels:
          tier: web
    ports:
    - protocol: TCP
      port: 80
EOF
```

### Step 5: Observe the Failed Request With Hubble

Open one terminal and watch for dropped traffic to the backend namespace. The filter is intentionally narrow enough to catch the exercise failure without showing unrelated cluster traffic.

```bash
hubble observe --namespace backend --verdict DROPPED --output compact
```

In a second terminal, trigger the failing request from the frontend pod. Use a short timeout so the exercise does not hang while the policy denies the connection.

```bash
k -n frontend exec frontend -- curl -s --max-time 5 api.backend.svc.cluster.local
```

You should see a Hubble flow showing traffic from `frontend/frontend` to `backend/api` with a dropped or policy-denied verdict. Record the source, destination, protocol, and verdict in your notes before you inspect the policy.

### Step 6: Explain the Failure From Kubernetes State

Inspect the policy and the frontend labels. The goal is to explain the denial without guessing.

```bash
k -n backend get networkpolicy api-policy -o yaml

k -n frontend get pod frontend --show-labels
```

The policy allows `tier: web`, but the pod has `app: frontend`. That mismatch is the reason the policy denies traffic. Hubble showed the datapath verdict; Kubernetes state explains why the selector did not match.

### Step 7: Fix the Policy Using the Actual Label Contract

Apply a corrected policy that matches the frontend namespace and the `app: frontend` pod label. This is a policy-side fix; in a real platform, you would choose this or a label-side fix based on the team's labeling standard.

```bash
k apply -f - <<'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-policy
  namespace: backend
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: frontend
      podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 80
EOF
```

### Step 8: Verify the Fix With the Same Evidence Path

Run a forwarded-flow query while repeating the request. Using the same source and destination proves that you fixed the original path rather than merely finding a different path that works.

```bash
hubble observe --namespace backend --verdict FORWARDED --output compact
```

```bash
k -n frontend exec frontend -- curl -s --max-time 5 api.backend.svc.cluster.local
```

You should now see a forwarded flow from the frontend pod to the backend API pod or Service. The curl command should also return the nginx response again.

### Step 9: Optional Extension for Senior Practice

Add a second frontend pod with a different label, then decide whether the policy should allow it. Use Hubble to prove your decision. This extension forces you to separate "make the demo pass" from "design the right access boundary."

```bash
k -n frontend run frontend-canary \
  --image=curlimages/curl:latest \
  --labels=app=frontend-canary \
  --command -- /bin/sh -c 'sleep infinity'

k wait --for=condition=ready pod/frontend-canary -n frontend --timeout=90s

k -n frontend exec frontend-canary -- curl -s --max-time 5 api.backend.svc.cluster.local
```

If the canary should be allowed, update the labels or policy intentionally and verify the new flow. If it should not be allowed, keep the policy narrow and use Hubble output to prove the denial is expected.

### Success Criteria

- [ ] You verified baseline connectivity before applying the restrictive policy.
- [ ] You reproduced the failure while a targeted Hubble query was running.
- [ ] You identified the dropped or policy-denied verdict for frontend-to-backend traffic.
- [ ] You compared the NetworkPolicy selector with the live frontend pod labels.
- [ ] You explained why the original selector did not match the intended source pod.
- [ ] You applied a minimal fix that matches the intended access boundary.
- [ ] You verified the corrected path with a forwarded Hubble flow.
- [ ] You can state whether the issue belonged to DNS, Service routing, pod readiness, or policy selection.

### Cleanup

Remove the lab namespaces after you finish. Deleting the namespaces removes the pods, Services, and NetworkPolicy created during the exercise.

```bash
k delete namespace frontend backend database
```

## Next Module

Continue to [Module 1.8: Coroot](../module-1.8-coroot/) to learn how correlation-focused observability platforms connect metrics, logs, traces, and topology into service-level diagnosis, or move to [Module 4.5: Tetragon](/platform/toolkits/security-quality/security-tools/module-4.5-tetragon/) to explore eBPF-based runtime security.
