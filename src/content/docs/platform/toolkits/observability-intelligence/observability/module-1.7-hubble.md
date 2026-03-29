---
title: "Module 1.7: Hubble - Network Observability with Cilium"
slug: platform/toolkits/observability-intelligence/observability/module-1.7-hubble
sidebar:
  order: 8
---
## Complexity: [MEDIUM]

**Time to Complete**: 90 minutes
**Prerequisites**: Module 1.6 (Pixie), Basic networking concepts (TCP/IP, DNS), Kubernetes networking basics
**Learning Objectives**:
- Understand eBPF-based network observability
- Deploy Hubble with Cilium CNI
- Use Hubble CLI and UI to visualize network flows
- Troubleshoot network policies and connectivity issues

---

## Why This Module Matters

Traditional network troubleshooting in Kubernetes is painful. You end up running `tcpdump` in containers, parsing packet captures, and correlating logs across dozens of pods. Network policies are "deny by default" black boxes—when traffic is blocked, you rarely know why.

**Hubble changes network observability from guesswork to clarity.**

Built on Cilium's eBPF foundation, Hubble observes all network traffic at the kernel level. You see every connection, every packet, every policy decision—without modifying applications or installing sidecars. It's like having Wireshark for your entire cluster, but organized by Kubernetes resources.

> "Before Hubble, network debugging was 'add logs, redeploy, hope.' Now we see exactly what's happening—which pod talked to which service, what got blocked and why."

---

## Did You Know?

- Hubble processes **millions of network events per second** with minimal overhead thanks to eBPF
- The Hubble UI provides a **real-time service map** showing all connections between pods and services
- Hubble can show you **exactly which network policy** blocked a connection—no more guessing
- DNS visibility is built-in: you see every lookup, resolution time, and failure
- Hubble supports **HTTP/gRPC-layer observability** without any application changes
- The name "Hubble" is a reference to the space telescope—giving visibility into the dark spaces of your network

---

## Hubble Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                         Kubernetes Cluster                              │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                     Hubble Components                             │ │
│  │                                                                   │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌───────────────────────────┐ │ │
│  │  │ Hubble UI   │  │ Hubble Relay│  │     Hubble CLI            │ │ │
│  │  │ (Web)       │  │ (gRPC)      │  │     (hubble observe)      │ │ │
│  │  └──────┬──────┘  └──────┬──────┘  └─────────────┬─────────────┘ │ │
│  │         │                │                       │               │ │
│  │         └────────────────┼───────────────────────┘               │ │
│  │                          ▼                                        │ │
│  │              ┌──────────────────────┐                            │ │
│  │              │   gRPC API           │                            │ │
│  │              └──────────┬───────────┘                            │ │
│  └───────────────────────────┴──────────────────────────────────────┘ │
│                              │                                        │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐            │
│  │    Node 1     │  │    Node 2     │  │    Node 3     │            │
│  │  ┌─────────┐  │  │  ┌─────────┐  │  │  ┌─────────┐  │            │
│  │  │ Cilium  │  │  │  │ Cilium  │  │  │  │ Cilium  │  │            │
│  │  │ Agent   │  │  │  │ Agent   │  │  │  │ Agent   │  │            │
│  │  │ +Hubble │  │  │  │ +Hubble │  │  │  │ +Hubble │  │            │
│  │  └────┬────┘  │  │  └────┬────┘  │  │  └────┬────┘  │            │
│  │       │eBPF   │  │       │eBPF   │  │       │eBPF   │            │
│  │  ┌────┴────┐  │  │  ┌────┴────┐  │  │  ┌────┴────┐  │            │
│  │  │ Network │  │  │  │ Network │  │  │  │ Network │  │            │
│  │  │ Events  │  │  │  │ Events  │  │  │  │ Events  │  │            │
│  │  └─────────┘  │  │  └─────────┘  │  │  └─────────┘  │            │
│  └───────────────┘  └───────────────┘  └───────────────┘            │
└────────────────────────────────────────────────────────────────────────┘
```

### Components

| Component | Role | Description |
|-----------|------|-------------|
| **Cilium Agent** | Data collection | Runs on each node, collects network events via eBPF |
| **Hubble Server** | Event processing | Embedded in Cilium agent, provides gRPC API |
| **Hubble Relay** | Aggregation | Aggregates data from all nodes for cluster-wide queries |
| **Hubble CLI** | Command-line | Query flows from terminal (`hubble observe`) |
| **Hubble UI** | Visualization | Web UI with service maps and flow visualization |

---

## Installing Hubble

### Prerequisites

Hubble requires Cilium as your CNI. If you're not using Cilium yet:

```bash
# Install Cilium CLI
CILIUM_CLI_VERSION=$(curl -s https://raw.githubusercontent.com/cilium/cilium-cli/main/stable.txt)
curl -L --fail --remote-name-all \
  https://github.com/cilium/cilium-cli/releases/download/${CILIUM_CLI_VERSION}/cilium-linux-amd64.tar.gz
sudo tar xzvfC cilium-linux-amd64.tar.gz /usr/local/bin
```

### Option 1: Install Cilium with Hubble Enabled

```bash
# Install Cilium with Hubble
cilium install --version 1.14.4 \
  --set hubble.enabled=true \
  --set hubble.relay.enabled=true \
  --set hubble.ui.enabled=true

# Verify installation
cilium status --wait
```

### Option 2: Enable Hubble on Existing Cilium

```bash
# If Cilium is already installed via Helm
helm upgrade cilium cilium/cilium --namespace kube-system \
  --reuse-values \
  --set hubble.enabled=true \
  --set hubble.relay.enabled=true \
  --set hubble.ui.enabled=true \
  --set hubble.metrics.enabled="{dns,drop,tcp,flow,icmp,http}"
```

### Install Hubble CLI

```bash
# Install Hubble CLI
HUBBLE_VERSION=$(curl -s https://raw.githubusercontent.com/cilium/hubble/master/stable.txt)
curl -L --fail --remote-name-all \
  https://github.com/cilium/hubble/releases/download/$HUBBLE_VERSION/hubble-linux-amd64.tar.gz
sudo tar xzvfC hubble-linux-amd64.tar.gz /usr/local/bin

# Verify installation
hubble version
```

### Verify Hubble is Running

```bash
# Check Cilium status (includes Hubble)
cilium status

# Expected output includes:
# Hubble Relay:    OK
# Hubble UI:       OK

# Check Hubble status specifically
hubble status

# Output:
# Healthcheck (via localhost:4245): Ok
# Current/Max Flows: 8192/8192 (100.00%)
# Flows/s: 45.67
```

---

## Using the Hubble CLI

### Basic Flow Observation

```bash
# Observe all network flows in real-time
hubble observe

# Output:
# TIMESTAMP             SOURCE                  DESTINATION             TYPE    VERDICT
# Jun 15 14:23:01.123   default/frontend-xxx    default/api-xxx         L7/HTTP to-endpoint FORWARDED
# Jun 15 14:23:01.234   default/api-xxx         kube-system/coredns     L4/UDP  to-endpoint FORWARDED
```

### Filtering by Namespace

```bash
# Observe flows in a specific namespace
hubble observe --namespace production

# Observe flows from a specific pod
hubble observe --from-pod production/api-server-7b9f8c6d5-abcd

# Observe flows to a specific service
hubble observe --to-service kube-system/kube-dns
```

### Filtering by Verdict

```bash
# Show only dropped traffic (great for debugging)
hubble observe --verdict DROPPED

# Show only forwarded traffic
hubble observe --verdict FORWARDED

# Show traffic denied by network policy
hubble observe --verdict POLICY_DENIED
```

### Protocol-Specific Filtering

```bash
# Show only HTTP traffic
hubble observe --protocol HTTP

# Show only DNS traffic
hubble observe --protocol DNS

# Show TCP connection events
hubble observe --type trace:to-endpoint --type trace:from-endpoint
```

### Output Formats

```bash
# JSON output for processing
hubble observe --output json | jq '.flow.source.pod_name'

# Compact output (one line per flow)
hubble observe --output compact

# Dictionary output (detailed)
hubble observe --output dict
```

---

## Network Policy Debugging

One of Hubble's killer features is **network policy verdict visibility**.

### See Why Traffic Was Dropped

```bash
# Show all dropped traffic
hubble observe --verdict DROPPED

# Output:
# TIMESTAMP             SOURCE                  DESTINATION             TYPE    VERDICT
# Jun 15 14:23:01.123   default/frontend-xxx    default/db-xxx         L4/TCP  DROPPED (Policy denied)
#                       Policy: default/deny-all-db-access
```

### Trace Policy Decisions

```bash
# See exactly which policy allowed/denied traffic
hubble observe --verdict POLICY_DENIED --output json | jq '.flow.policy_match_type'

# Show the policy that matched
hubble observe --to-pod default/database-0 --output json | jq '.flow.traffic_direction, .flow.policy_match_type'
```

### Test Policy Before Applying

```bash
# Run in one terminal: watch traffic to your pod
hubble observe --to-pod default/my-app --verdict DROPPED

# In another terminal: apply your network policy
kubectl apply -f my-network-policy.yaml

# Immediately see if the policy is blocking expected traffic
```

---

## HTTP/L7 Observability

Hubble can parse HTTP traffic and show request-level details:

```bash
# Enable HTTP visibility (if not already)
# This requires Cilium to be configured with L7 policy

# Observe HTTP requests
hubble observe --protocol HTTP

# Output:
# TIMESTAMP             SOURCE                  DESTINATION             TYPE    VERDICT  HTTP INFO
# Jun 15 14:23:01.123   default/frontend       default/api             L7/HTTP FORWARDED GET /api/users 200
# Jun 15 14:23:01.456   default/frontend       default/api             L7/HTTP FORWARDED POST /api/orders 201
```

### HTTP Filtering

```bash
# Filter by HTTP method
hubble observe --http-method GET

# Filter by status code
hubble observe --http-status 500

# Filter by URL path
hubble observe --http-path /api/users
```

---

## The Hubble UI

### Accessing Hubble UI

```bash
# Port-forward the UI
cilium hubble ui

# Or manually
kubectl port-forward -n kube-system svc/hubble-ui 12000:80

# Open http://localhost:12000
```

### UI Features

The Hubble UI provides:

1. **Service Map**: Visual graph showing all service-to-service connections
2. **Flow Table**: Real-time table of network flows
3. **Namespace Filtering**: Focus on specific namespaces
4. **Protocol Breakdown**: See HTTP, TCP, DNS separately
5. **Policy Verdicts**: Visual indication of allowed/denied traffic

```
┌─────────────────────────────────────────────────────────────────┐
│                        Hubble UI                                │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    Service Map                            │ │
│  │                                                           │ │
│  │     ┌──────────┐         ┌──────────┐                    │ │
│  │     │ frontend │────────▶│   api    │                    │ │
│  │     └──────────┘         └────┬─────┘                    │ │
│  │                               │                          │ │
│  │                               ▼                          │ │
│  │     ┌──────────┐         ┌──────────┐                    │ │
│  │     │  redis   │◀────────│ database │                    │ │
│  │     └──────────┘         └──────────┘                    │ │
│  │                                                           │ │
│  │  Legend: ──▶ HTTP  ··▶ TCP  ╳ Dropped                   │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Flow Table                           │   │
│  │  Source        Destination      Protocol  Verdict       │   │
│  │  frontend-x    api-y            HTTP      FORWARDED     │   │
│  │  api-y         database-z       TCP       FORWARDED     │   │
│  │  api-y         external-ip      TCP       DROPPED       │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Hubble Metrics

Hubble can export Prometheus metrics for alerting and dashboards:

```bash
# Enable Hubble metrics in Cilium
helm upgrade cilium cilium/cilium --namespace kube-system \
  --reuse-values \
  --set hubble.metrics.enabled="{dns,drop,tcp,flow,icmp,http}"
```

### Available Metrics

| Metric | Description |
|--------|-------------|
| `hubble_flows_processed_total` | Total flows processed |
| `hubble_drop_total` | Dropped packets by reason |
| `hubble_tcp_flags_total` | TCP flag distribution |
| `hubble_dns_queries_total` | DNS queries by type |
| `hubble_http_requests_total` | HTTP requests by method/status |

### Example Prometheus Queries

```promql
# Dropped packets rate by reason
rate(hubble_drop_total[5m])

# HTTP error rate
sum(rate(hubble_http_requests_total{http_status=~"5.."}[5m]))
/
sum(rate(hubble_http_requests_total[5m]))

# DNS query latency
histogram_quantile(0.99, rate(hubble_dns_response_types_total[5m]))
```

---

## Hubble vs Other Network Observability Tools

| Feature | Hubble | Wireshark/tcpdump | Service Mesh Telemetry |
|---------|--------|-------------------|------------------------|
| **Deployment** | Automatic with Cilium | Manual per pod | Sidecar per pod |
| **Overhead** | Minimal (eBPF) | Moderate (packet capture) | Significant (proxy) |
| **Kubernetes-aware** | Yes | No | Yes |
| **Policy visibility** | Full verdict details | None | Partial |
| **Scale** | Cluster-wide | Single pod | Cluster-wide |
| **Real-time UI** | Yes | No | Varies |
| **L7 visibility** | With Cilium L7 policy | Yes (manual) | Yes |

---

## War Story: The Mysterious Database Timeouts

A SaaS company was experiencing intermittent database connection failures. Their application logs showed "connection timeout to PostgreSQL," but the database was healthy and had plenty of capacity.

**The Investigation**:
- Database monitoring: All green
- Application logs: Sporadic timeout errors
- Network team: "Network is fine"
- Everyone blamed everyone else

**Enter Hubble**:

```bash
# They ran this query:
hubble observe --to-pod database/postgres-0 --verdict DROPPED

# Output:
# TIMESTAMP             SOURCE                    DESTINATION              VERDICT
# Jun 15 14:23:01.123   production/api-6x4f2     database/postgres-0      DROPPED (Policy denied)
# Jun 15 14:23:05.789   production/api-9k2m3     database/postgres-0      DROPPED (Policy denied)
```

**The Discovery**:
A network policy was applied to the database namespace that only allowed connections from pods with a specific label. When new API pods were deployed, they didn't have the label—but the Kubernetes readiness probe passed before the first database connection attempt.

```yaml
# The problematic policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-api-to-database
  namespace: database
spec:
  ingress:
  - from:
    - podSelector:
        matchLabels:
          db-access: "true"  # <-- API pods were missing this label!
```

**The Fix**: Updated the API deployment to include the `db-access: "true"` label.

**The Lesson**: Without Hubble, they would have spent days debugging application code. Hubble showed the policy verdict in seconds.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Not enabling Hubble Relay | Can't see cluster-wide flows | Enable `hubble.relay.enabled=true` |
| Missing HTTP visibility | Only see L4 flows | Configure Cilium L7 policy for HTTP parsing |
| Hubble buffer too small | Missing flows during high traffic | Increase `hubble.flowBuffer` |
| Not using namespaces | Too much noise in output | Always filter with `--namespace` |
| Forgetting to check verdicts | Missing dropped traffic | Include `--verdict DROPPED` in debugging |
| Running without Cilium | Hubble requires Cilium CNI | Can't use Hubble with other CNIs |

---

## Advanced: Exporting to External Systems

### Export to OpenTelemetry

```bash
# Enable OTel export in Cilium
helm upgrade cilium cilium/cilium --namespace kube-system \
  --reuse-values \
  --set hubble.export.enabled=true \
  --set hubble.export.otelExporter.enabled=true \
  --set hubble.export.otelExporter.endpoint="otel-collector:4317"
```

### Export to S3 for Analysis

```bash
# Enable file export
helm upgrade cilium cilium/cilium --namespace kube-system \
  --reuse-values \
  --set hubble.export.enabled=true \
  --set hubble.export.fileExporter.enabled=true \
  --set hubble.export.fileExporter.path="/var/run/cilium/hubble/export"

# Then sync to S3 using a sidecar or cronjob
```

---

## Hands-On Exercise: Debug a Network Policy Issue

**Objective**: Use Hubble to identify and fix a broken network policy.

### Setup

```bash
# Create test namespaces
kubectl create namespace frontend
kubectl create namespace backend
kubectl create namespace database

# Deploy test applications
kubectl apply -f - <<EOF
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
    command: ["/bin/sh", "-c", "sleep infinity"]
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
EOF

# Wait for pods
kubectl wait --for=condition=ready pod -l app=frontend -n frontend --timeout=60s
kubectl wait --for=condition=ready pod -l app=api -n backend --timeout=60s
kubectl wait --for=condition=ready pod -l app=postgres -n database --timeout=60s
```

### Task 1: Verify Connectivity Works

```bash
# Test frontend -> api
kubectl exec -n frontend frontend -- curl -s api.backend.svc.cluster.local

# Test api -> postgres (just DNS for now)
kubectl exec -n backend api -- nslookup postgres.database.svc.cluster.local
```

### Task 2: Apply a Restrictive Network Policy

```bash
# Apply a network policy that's too restrictive
kubectl apply -f - <<EOF
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
    - podSelector:
        matchLabels:
          tier: web  # Note: frontend pod doesn't have this label
    ports:
    - port: 80
EOF
```

### Task 3: Use Hubble to Identify the Problem

```bash
# In one terminal: watch for dropped traffic
hubble observe --namespace backend --verdict DROPPED

# In another terminal: try to connect
kubectl exec -n frontend frontend -- curl -s --max-time 5 api.backend.svc.cluster.local
# This will timeout
```

You should see output like:
```
TIMESTAMP             SOURCE                    DESTINATION              VERDICT
Jun 15 14:23:01.123   frontend/frontend         backend/api              DROPPED (Policy denied)
```

### Task 4: Get More Details

```bash
# Get detailed policy information
hubble observe --to-pod backend/api --verdict DROPPED --output json | head -1 | jq '.'

# Look for:
# - traffic_direction
# - policy_match_type
# - drop_reason_desc
```

### Task 5: Fix the Network Policy

```bash
# Option 1: Add the label to the frontend pod
kubectl label pod -n frontend frontend tier=web

# Option 2: Update the network policy to match the actual label
kubectl apply -f - <<EOF
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
    - port: 80
EOF
```

### Task 6: Verify the Fix

```bash
# Watch for successful traffic
hubble observe --namespace backend --verdict FORWARDED

# Test connectivity again
kubectl exec -n frontend frontend -- curl -s api.backend.svc.cluster.local
# Should succeed now
```

### Success Criteria

- [ ] Identified that the network policy was blocking traffic
- [ ] Used Hubble to see the `DROPPED` verdict
- [ ] Understood which policy caused the block
- [ ] Fixed the policy or labels to allow traffic
- [ ] Verified the fix with Hubble showing `FORWARDED` verdicts

### Cleanup

```bash
kubectl delete namespace frontend backend database
```

---

## Quiz

### Question 1
What is Hubble and what CNI does it require?

<details>
<summary>Show Answer</summary>

**Hubble is an observability platform built on eBPF that requires Cilium as the CNI**

Hubble is tightly integrated with Cilium and leverages the same eBPF infrastructure that Cilium uses for networking. It cannot be used with other CNIs.
</details>

### Question 2
What command shows all dropped network traffic in Hubble?

<details>
<summary>Show Answer</summary>

**`hubble observe --verdict DROPPED`**

This filters the flow output to show only traffic that was dropped, which is invaluable for debugging network policy issues.
</details>

### Question 3
What is Hubble Relay and why is it needed?

<details>
<summary>Show Answer</summary>

**Hubble Relay aggregates network flow data from all nodes in the cluster**

Each Cilium agent collects flows for its node. Hubble Relay provides a single endpoint to query flows across all nodes, enabling cluster-wide observability.
</details>

### Question 4
How does Hubble help debug network policies?

<details>
<summary>Show Answer</summary>

**Hubble shows exactly which policy allowed or denied each network flow**

When traffic is dropped, Hubble shows the `POLICY_DENIED` verdict along with details about which policy matched. This eliminates guesswork when debugging policy issues.
</details>

### Question 5
What is the difference between L4 and L7 observability in Hubble?

<details>
<summary>Show Answer</summary>

**L4 shows TCP/UDP connection-level flows; L7 shows HTTP/gRPC request-level details**

L4 observability is automatic. L7 observability requires Cilium to be configured with L7 network policies, which enables parsing of HTTP traffic including method, path, and status codes.
</details>

### Question 6
How do you enable Hubble metrics for Prometheus?

<details>
<summary>Show Answer</summary>

**Set `hubble.metrics.enabled` with the desired metrics categories in the Cilium Helm values**

Example: `--set hubble.metrics.enabled="{dns,drop,tcp,flow,icmp,http}"` enables metrics for those categories.
</details>

### Question 7
What does the Hubble UI Service Map show?

<details>
<summary>Show Answer</summary>

**A real-time visual graph of all service-to-service connections in the cluster**

The service map shows pods/services as nodes and connections as edges, making it easy to understand traffic patterns and identify unexpected communication.
</details>

### Question 8
How can you filter Hubble output to show only HTTP 500 errors?

<details>
<summary>Show Answer</summary>

**`hubble observe --http-status 500`**

This requires L7 visibility to be enabled. You can also use ranges like `--http-status 5xx` for all server errors.
</details>

---

## Key Takeaways

1. **Hubble is Cilium's observability layer** - requires Cilium CNI
2. **eBPF provides kernel-level visibility** - see all traffic without sidecars
3. **Verdicts show policy decisions** - know exactly why traffic was dropped
4. **Hubble CLI is powerful** - filter by namespace, pod, protocol, verdict
5. **Service maps visualize dependencies** - see cluster topology in real-time
6. **L7 visibility is optional** - configure Cilium for HTTP-level details
7. **Metrics enable alerting** - export to Prometheus for dashboards
8. **Relay enables cluster-wide queries** - aggregate flows from all nodes
9. **Essential for network policy debugging** - no more guessing
10. **Low overhead** - eBPF makes it production-safe

---

## Further Reading

- [Hubble Documentation](https://docs.cilium.io/en/stable/observability/hubble/) - Official Cilium docs
- [Cilium Network Policies](https://docs.cilium.io/en/stable/security/policy/) - Understanding policy verdicts
- [Hubble Metrics Reference](https://docs.cilium.io/en/stable/observability/metrics/) - All available metrics
- [eBPF.io](https://ebpf.io/) - Understanding the underlying technology

---

## Next Module

Continue to [Module 1.8: Coroot](module-1.8-coroot/) to learn about auto-instrumentation observability platforms, or move to [Module 4.5: Tetragon](../../security-quality/security-tools/module-4.5-tetragon/) to explore eBPF-based security.
