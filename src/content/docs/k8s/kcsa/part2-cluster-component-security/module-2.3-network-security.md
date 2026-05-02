---
revision_pending: false
title: "Module 2.3: Network Security"
slug: k8s/kcsa/part2-cluster-component-security/module-2.3-network-security
sidebar:
  order: 4
---

# Module 2.3: Network Security

> **Complexity**: `[MEDIUM]` - Core knowledge
>
> **Time to Complete**: 35-40 minutes
>
> **Prerequisites**: [Module 2.2: Node Security](../module-2.2-node-security/)

This module uses Kubernetes 1.35+ behavior and the short command alias `k` for `kubectl`. If you run the examples in a lab cluster, define the alias once in your shell with `alias k=kubectl`, then use the shorter form consistently so the commands match the lesson.


## What You'll Be Able to Do

After completing this module, you will be able to apply these outcomes in design reviews, lab validation, and incident-response conversations about Kubernetes network exposure:

1. **Evaluate** the Kubernetes flat network model and its security implications for lateral movement
2. **Design** NetworkPolicy coverage that isolates namespaces, workloads, ingress paths, and egress paths
3. **Diagnose** CNI policy enforcement gaps before relying on a policy as a control
4. **Implement** service mesh mTLS and workload identity as a complement to Layer 3 and Layer 4 policy
5. **Compare** network policy, CNI encryption, and service mesh authorization when choosing a defense-in-depth design


## Why This Module Matters

In late 2018, a large electric-vehicle manufacturer disclosed that attackers had abused an exposed Kubernetes dashboard to run cryptocurrency mining workloads in its cloud account. Public reporting focused on the visible mistake, but the deeper lesson was about trust boundaries: once the intruder reached the cluster control surface, weak segmentation turned a single foothold into a much broader blast radius. The direct cost was not only compute waste; it was incident response time, engineering distraction, secret-rotation work, and the uncomfortable question every security team asks after containment: what else could that workload have reached while it was running?

Kubernetes makes distributed systems feel clean because a pod can reach a service name without caring which node holds the endpoint. That convenience is intentional, and it is one reason the platform scales operationally. The security cost is just as intentional: the default network is open until you add controls, and namespaces are organizational labels rather than packet filters. A compromised frontend, a debug container left too permissive, or a vulnerable internal API can become a route toward databases, message brokers, metadata services, and control-plane-adjacent endpoints if the cluster has no deliberate network policy.

This module teaches network security as an engineering design problem, not as a pile of YAML snippets. You will start with the default flat model, then add NetworkPolicy in a way that makes traffic dependencies visible instead of mysterious. You will check whether the CNI actually enforces the policies you write, because a policy object without an enforcing dataplane is only documentation. Finally, you will compare network policy with mTLS and service mesh authorization so you can decide when simple segmentation is enough and when identity-aware encryption belongs in the design.


## Evaluate the Flat Network Model

Kubernetes networking begins from a useful promise: every pod gets an IP address, every pod can normally reach every other pod without network address translation, and services provide stable virtual names for changing endpoints. That model removes a lot of application plumbing. Developers do not need to hard-code node addresses, load balancers can target pods across nodes, and rolling deployments can swap endpoints without changing client configuration. The model is operationally elegant because it treats the cluster as one routable fabric.

The security problem is that routing convenience is not the same as authorization. By default, a pod in a development namespace can attempt to open a TCP connection to a pod in a production namespace, and Kubernetes itself will not block that packet merely because the namespaces differ. If the destination application accepts the connection, the cluster network has done its default job. That is why namespace names, service names, and labels are not security controls until an enforcing component uses them in a policy decision.

```text
┌─────────────────────────────────────────────────────────────┐
│              DEFAULT KUBERNETES NETWORKING                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  BY DEFAULT:                                                │
│  • All pods can communicate with all other pods             │
│  • No network isolation between namespaces                  │
│  • Any pod can reach any service                            │
│  • Pods can reach external networks                         │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         ALL PODS ←──────────────→ ALL PODS          │    │
│  │                                                     │    │
│  │  Pod A ───→ Pod B ───→ Pod C ───→ Pod D             │    │
│  │    ↑                                 │              │    │
│  │    └─────────────────────────────────┘              │    │
│  │                                                     │    │
│  │  No restrictions, full mesh connectivity            │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  THIS IS DANGEROUS:                                         │
│  • Compromised pod can scan entire cluster                  │
│  • Lateral movement is trivial                              │
│  • No defense in depth                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Think about the flat network like an office building where every room has a door but none of the doors have locks. The floor plan is efficient, and people can move quickly, yet a visitor who enters one room can try every other handle. Kubernetes labels the rooms beautifully, but labels alone do not lock them. NetworkPolicy is the system that starts turning labels into controlled doors, and service mesh identity can later decide whether the person at the door is really who they claim to be.

A practical security review starts by asking which communications are business requirements rather than habits. Frontend pods may need to reach backend pods on port 8080, backend pods may need to reach a database on 5432, and every tier may need DNS. That is a very different statement from "all pods can reach all pods." The first statement can be reviewed, tested, and monitored; the second statement is a blank check for any compromised workload.

Pause and predict: if a cluster has no NetworkPolicy objects at all, what do you expect to happen when a temporary troubleshooting pod in `default` tries to connect to a database service in `production`? The important detail is not whether the database accepts the login. The network path itself is open unless another control outside Kubernetes blocks it, so the connection attempt reaches the destination network endpoint.

The consequence is lateral movement. Attackers rarely need every credential in the cluster on day one; they need a path from the first weak workload to something more valuable. A pod with a vulnerable web framework might let them run commands, scan service DNS names, try common ports, and identify internal systems that were never intended to be internet-facing. Flat networking turns that scanning phase into a cluster-wide exercise unless segmentation is already in place.

Kubernetes does not treat this openness as a bug because many clusters run platform components, operators, service discovery, admission systems, and observability agents that genuinely need cross-workload communication. A default-deny posture would break many naive installations. The platform therefore gives you the primitives and expects the cluster operator to choose a policy model appropriate to the environment. For KCSA-level security reasoning, that distinction matters: Kubernetes provides mechanisms, while your architecture supplies the security intent.

One war story repeats across many internal platforms. A team adds a new reporting service that reads from a message queue and writes to an analytics database. During launch week, an engineer deploys a debug pod with a package manager and shell tools to inspect the queue. Months later, that pod image pattern is copied into another namespace, where it retains broad network reach. Nothing looks alarming in Kubernetes events, but the cluster has quietly normalized a workload that can probe far more than it needs.

The safer habit is to define traffic contracts while the application is still small. If a namespace holds a three-tier application, write down which tier initiates each connection, which port is required, whether DNS is needed, and whether external egress is legitimate. That contract becomes your NetworkPolicy inventory. It also becomes a test plan: if an unexpected pod can reach the database, the design has drifted away from the contract.

Another useful review habit is to separate reachability from permission. Reachability asks whether packets can arrive at a socket. Permission asks whether the receiving service should accept the caller and action. Kubernetes network policy mostly helps with reachability, while application authentication and mesh authorization help with permission. If you collapse those ideas, you may overtrust one layer. A database login failure does not prove segmentation, and a network timeout does not prove the application has correct authorization.

For platform teams, the flat model also creates a communication challenge. Application teams often assume that a namespace named `prod` is naturally more protected than a namespace named `dev`, because many tools present namespaces as strong organizational containers. A senior reviewer should make the implicit model explicit: namespaces group API objects, RBAC can limit who changes those objects, resource quotas can limit consumption, and NetworkPolicy can limit traffic. Each boundary must be configured separately, and each boundary needs its own test.


## Diagnose CNI Policy Enforcement

NetworkPolicy is part of the Kubernetes API, but the API server does not enforce packet filtering by itself. The actual enforcement belongs to the cluster networking implementation, usually called the Container Network Interface plugin. That separation is easy to miss because the policy object can be accepted, stored, and shown by `k get networkpolicy` even when the dataplane ignores it. A security control that can be created but not enforced is one of the most dangerous failure modes because dashboards look green while traffic remains open.

```text
┌─────────────────────────────────────────────────────────────┐
│              CNI PLUGIN RESPONSIBILITIES                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  BASIC NETWORKING                                           │
│  • Assign IP addresses to pods                              │
│  • Enable pod-to-pod communication                          │
│  • Route traffic between nodes                              │
│                                                             │
│  SECURITY FEATURES (varies by plugin)                       │
│  • Network policy enforcement                               │
│  • Encryption in transit                                    │
│  • Egress controls                                          │
│  • Observability and logging                                │
│                                                             │
│  COMMON CNI PLUGINS                                         │
│  ┌──────────────┬────────────────────────────────────┐     │
│  │ Plugin       │ Network Policy Support             │     │
│  ├──────────────┼────────────────────────────────────┤     │
│  │ Calico       │ Full (plus extensions)             │     │
│  │ Cilium       │ Full (plus extensions)             │     │
│  │ Weave        │ Full                               │     │
│  │ Flannel      │ None (basic networking only)       │     │
│  │ AWS VPC CNI  │ Via network policy features/add-on │     │
│  └──────────────┴────────────────────────────────────┘     │
│                                                             │
│  WARNING: Some CNIs provide connectivity but not policy.    │
│  Choose a CNI that supports your security requirements.     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

A CNI plugin is best understood as the part of the cluster that wires pod network interfaces, assigns routes, and programs the rules that decide whether packets move. Some plugins focus on basic connectivity, some add policy enforcement, and some add encryption, identity, observability, or eBPF-based controls. The Kubernetes NetworkPolicy specification describes portable intent, but each implementation chooses how to translate that intent into iptables rules, eBPF programs, cloud security controls, or another dataplane mechanism.

Before you rely on a policy, verify both capability and behavior. Capability means the plugin documentation says NetworkPolicy is supported for the cluster mode you use. Behavior means an actual packet that should be denied is denied in your cluster. Those are different checks. Managed Kubernetes versions, cloud add-ons, and CNI configuration flags can change what is enforced, so policy review should include a live negative test rather than only reading manifests.

```bash
alias k=kubectl
k get pods -n kube-system -o wide
k get networkpolicy -A
k api-resources | grep -i networkpolicy
```

Those commands tell you what is installed and what policies exist, but they do not prove enforcement. The API resource can exist because Kubernetes supports the object type, while the CNI may still not act on it. A useful lab test creates two pods, applies a deny policy to one namespace, and then attempts a connection that should fail. If the connection still works after the policy selects the destination pod, the cluster is not enforcing the control you think you deployed.

```bash
k create namespace netsec-lab
k -n netsec-lab run web --image=nginx:1.27 --labels=app=web --port=80
k -n netsec-lab run probe --image=curlimages/curl:8.10.1 --restart=Never -- sleep 3600
k -n netsec-lab expose pod web --port=80
k -n netsec-lab exec probe -- curl -sS --max-time 3 http://web
```

The first connection should work in a default-open namespace because no policy selects the `web` pod. That baseline matters because it proves your test is meaningful; you have shown that the service, DNS, and endpoint are healthy before applying a deny. Security tests that skip the baseline often misread unrelated DNS failures, image pull failures, or service misconfiguration as policy success.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-web-ingress
  namespace: netsec-lab
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
  - Ingress
```

```bash
k apply -f deny-web-ingress.yaml
k -n netsec-lab exec probe -- curl -sS --max-time 3 http://web
```

After the deny policy is applied, the connection should time out or fail because the selected pod has no allowed ingress sources. If it still succeeds, do not debug the YAML first. Ask whether the CNI enforces NetworkPolicy, whether the policy namespace matches the pod namespace, whether the selected labels match the destination pod, and whether another policy allows the traffic. This order prevents a common review mistake: polishing policy syntax while the real issue is an unenforced dataplane.

Before running this, what output do you expect from the second `curl`, and which observation would prove that your CNI is not enforcing NetworkPolicy? A refusal from the application is not the same as a network deny, and a DNS lookup error is not the same as ingress isolation. You are looking for a change from reachable to unreachable after the policy selects the pod.

CNI choice also affects operational visibility. Calico and Cilium can expose policy decisions, flow logs, or policy trace tooling depending on configuration. Those features help when a deny works too well and an application breaks after a rollout. A simple plugin without policy visibility may still be acceptable for a small non-sensitive cluster, but the tradeoff should be explicit. In regulated or multi-team environments, the ability to prove which policy allowed or denied a flow often becomes part of the security control itself.

The important exam-ready point is that NetworkPolicy has two halves: Kubernetes intent and CNI enforcement. The manifest expresses intent in a portable API. The plugin turns that intent into real packet handling. A design review that checks only one half is incomplete, and a production rollout that skips a negative connectivity test can leave the team believing it has segmentation when the cluster still behaves as a flat network.

Policy coverage should be measured from the workload perspective rather than from the object count. Ten NetworkPolicy objects can still leave a critical pod unselected, while two focused policies can isolate a small namespace effectively. During review, list the pods that handle sensitive data, check which policies select them for ingress and egress, and then test one denied path for each sensitive tier. This turns coverage from a vague statement into evidence: selected pods, selected directions, allowed sources, allowed destinations, and observed denies.

When diagnosing a failed deny, resist the urge to treat the CNI as a black box. The CNI is part of the security boundary, so its version, mode, and configuration belong in the review. Managed offerings sometimes enable policy through an add-on, and self-managed clusters may run a plugin that supports policy only after specific components are installed. Record that dependency in the platform documentation. Future cluster upgrades, node-image changes, and add-on migrations can otherwise remove or alter enforcement without any application manifest changing.


## Design NetworkPolicy Coverage

NetworkPolicy uses selectors to decide which pods are isolated and which traffic is allowed. The most important rule is additive behavior: if no policy selects a pod for a direction, that direction remains open; once at least one policy selects the pod for that direction, only traffic allowed by the union of matching policies is permitted. This means policy design is less like writing one firewall file and more like building a set of small permissions that accumulate into the intended traffic contract.

```text
┌─────────────────────────────────────────────────────────────┐
│              NETWORK POLICY CONCEPT                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Network policies are ADDITIVE:                             │
│  • No policy = allow all traffic                            │
│  • Policy exists = default deny for selected pods           │
│  • Multiple policies = union of allowed traffic             │
│                                                             │
│  POLICY COMPONENTS:                                         │
│                                                             │
│  podSelector:     Which pods this policy applies to         │
│  policyTypes:     [Ingress, Egress] or both                 │
│  ingress:         Rules for incoming traffic                │
│  egress:          Rules for outgoing traffic                │
│                                                             │
│  SELECTOR OPTIONS:                                          │
│  • podSelector       - Match by pod labels                  │
│  • namespaceSelector - Match by namespace labels            │
│  • ipBlock           - Match by CIDR range                  │
│  • ports             - Match by port/protocol               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The easiest safe starting point is default deny for the namespace, followed by explicit allows for required paths. A default deny policy with `podSelector: {}` selects every pod in that namespace. If it lists `Ingress` and has no ingress rules, selected pods receive no ingress except traffic allowed by another policy. If it lists `Egress` and has no egress rules, selected pods cannot initiate outbound traffic except traffic another policy permits. The absence of rules is the deny; the presence of another policy supplies the allowance.

```yaml
# Default deny all ingress in namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: production
spec:
  podSelector: {}  # Selects all pods in namespace
  policyTypes:
  - Ingress
  # No ingress rules = deny all ingress
```

```yaml
# Default deny all egress in namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-egress
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Egress
  # No egress rules = deny all egress
```

Default deny is powerful because it turns unknown traffic into visible breakage during controlled testing rather than invisible exposure during an incident. The tradeoff is that applications often depend on more flows than developers remember. DNS, metrics scraping, health checks, admission webhooks, object storage, package repositories, and license services can all become accidental dependencies. A mature rollout therefore uses inventory, staged namespaces, and targeted probes rather than applying a broad egress deny to a busy production namespace with no rehearsal.

Once the baseline is in place, allow the smallest meaningful path. A frontend-to-backend rule should select the backend as the destination, name the frontend selector as the source, and restrict the port. That direction matters. Ingress rules are written from the perspective of the selected destination pod, not from the initiating client. Engineers often read the policy name and assume it selects the client; the `spec.podSelector` is the destination for ingress and the source for egress.

```yaml
# Allow frontend to communicate with backend
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: production
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

This policy does not grant the frontend general access to the namespace. It grants traffic from pods labeled `app: frontend` to pods labeled `app: backend` on TCP 8080, and only as ingress to the selected backend pods. If backend pods also need egress isolation, you must write egress policy separately. That separation is not redundancy; it is how Kubernetes lets you control incoming and outgoing paths independently.

Namespace isolation is the next design layer. Many organizations use namespaces for teams, stages, tenants, or application boundaries, and then assume those boundaries imply network separation. They do not. A namespace boundary becomes network isolation only when a policy selects pods and limits sources to the same namespace or to approved namespace labels. The policy below allows traffic only from pods in the same namespace because a `podSelector` without a `namespaceSelector` matches pods in the policy's namespace.

```text
┌─────────────────────────────────────────────────────────────┐
│              NAMESPACE ISOLATION PATTERN                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  BEFORE (Default - No Isolation):                           │
│  ┌────────────────┐    ┌────────────────┐                  │
│  │ namespace: dev │←──→│ namespace: prod│                  │
│  │ Pod A ←────────┼────┼───→ Pod B      │                  │
│  └────────────────┘    └────────────────┘                  │
│  All namespaces can communicate                             │
│                                                             │
│  AFTER (Namespace Isolation):                               │
│  ┌────────────────┐    ┌────────────────┐                  │
│  │ namespace: dev │ ✗  │ namespace: prod│                  │
│  │ Pod A ─────────┼────┼───X Pod B      │                  │
│  └────────────────┘    └────────────────┘                  │
│  Cross-namespace traffic blocked                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

```yaml
# Only allow traffic from same namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-same-namespace
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector: {}  # Any pod in same namespace
```

The same-namespace pattern is useful for quick containment, but it is not a complete application design. A production namespace might legitimately need ingress from a shared ingress-controller namespace, metrics from an observability namespace, or calls from a batch-processing namespace. When that happens, use namespace labels deliberately. Label the approved source namespace, match that label in the policy, and document who owns the label so a casual namespace edit does not become an authorization bypass.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-ingress-controller
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: frontend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          platform.kubedojo.io/ingress: "true"
      podSelector:
        matchLabels:
          app.kubernetes.io/name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8080
```

Database isolation deserves special care because databases tend to hold the data an attacker actually wants. A database should not be reachable from frontend pods, debug pods, cron jobs, or arbitrary workloads that share the namespace. It should accept traffic from the backend role on the database port, and it should have egress only if replication, backups, or external storage truly require it. The policy shape below preserves the original backend-to-database pattern while making the destination explicit.

```yaml
# Only allow backend pods to reach database
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: database-access
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: database
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          role: backend
    ports:
    - protocol: TCP
      port: 5432
```

Egress policy is where many good intentions break applications. The most common failure is forgetting DNS. Once an egress policy selects a pod, the pod can no longer send packets to CoreDNS unless a policy allows UDP and often TCP port 53 to the DNS pods. Some clusters label CoreDNS as `k8s-app: kube-dns`; others use different labels, especially in managed services or hardened installations. Do not copy DNS policy blindly. Inspect the actual labels in `kube-system` before relying on an example.

```bash
k -n kube-system get pods --show-labels | grep -E 'coredns|kube-dns'
k -n production get pods --show-labels
k -n production describe networkpolicy database-access
```

Which approach would you choose here and why: one broad egress policy that allows all pods to reach DNS and the internet, or tier-specific egress policies that allow only the destinations each tier needs? The broad rule is faster to deploy but leaves exfiltration paths open. Tier-specific egress takes more inventory work, yet it gives you a reviewable map of which workloads can send data where.

Worked example: a three-tier app has `tier=frontend`, `tier=backend`, and `tier=database`. The frontend receives traffic from an ingress controller, calls the backend on 8080, and needs DNS. The backend calls the database on 5432, sends metrics to an observability namespace, and needs DNS. The database accepts backend traffic only and sends backup traffic to a known object-storage CIDR. Those statements are the design; the YAML is only the encoding. If the design cannot be stated in this plain language, the policy is not ready.

NetworkPolicy has limits you should not hide from yourself. Standard policies are namespace-scoped, so there is no single built-in cluster-wide default deny object. Policies usually operate at Layer 3 and Layer 4, so they match IP blocks, selectors, ports, and protocols rather than HTTP paths or user identities. They do not encrypt traffic. They also depend heavily on labels, which means label governance is part of network security. If a developer can add `role=backend` to any pod without review, a selector-based policy may allow more than intended.

There is a second selector trap around `namespaceSelector` and `podSelector` combinations. In a single `from` entry, a namespace selector and a pod selector are combined so that both must match: pods with the selected labels inside namespaces with the selected labels. In separate `from` entries, they are alternatives. That difference can widen access unexpectedly. When a policy crosses namespace boundaries, read the indentation slowly and convert the rule into plain English before approving it.

Ingress and egress policies should also be owned by the team that understands the application dependency graph, not only by the central security team. Central teams can provide templates, guardrails, and review standards, but application maintainers know when a backend starts calling a new cache, queue, or external API. The best operating model is shared: the platform team defines secure defaults and label conventions, while service owners update policy alongside service dependencies. That keeps policy close enough to the application to stay accurate.


## Implement mTLS and Workload Identity

NetworkPolicy decides which network paths should exist, but it does not prove the identity of the application inside a pod and it does not encrypt application traffic by itself. If a packet is allowed from frontend to backend on port 8080, the CNI forwards that packet according to policy. The payload may still be plaintext, and the backend may still need a separate way to know whether the caller is an authentic frontend workload. That is the gap service mesh mTLS is designed to close.

```text
┌─────────────────────────────────────────────────────────────┐
│              SERVICE MESH ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WITHOUT SERVICE MESH:                                      │
│  ┌─────────┐                    ┌─────────┐                 │
│  │  Pod A  │ ─── HTTP/TCP ───→ │  Pod B  │                 │
│  │  (app)  │                    │  (app)  │                 │
│  └─────────┘                    └─────────┘                 │
│  Unencrypted, no identity                                   │
│                                                             │
│  WITH SERVICE MESH:                                         │
│  ┌─────────────────┐            ┌─────────────────┐         │
│  │  Pod A          │            │  Pod B          │         │
│  │  ┌─────┐┌─────┐│            │┌─────┐┌─────┐   │         │
│  │  │ app ││proxy│├── mTLS ───→│proxy ││ app │   │         │
│  │  └─────┘└─────┘│            │└─────┘└─────┘   │         │
│  └─────────────────┘            └─────────────────┘         │
│  Encrypted, identity-based, observable                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

A service mesh normally inserts a proxy next to each application container or uses an ambient dataplane to intercept workload traffic. The mesh issues certificates to workloads, rotates them, and uses mutual TLS so both sides authenticate each other. The application can keep speaking HTTP or gRPC locally while the mesh handles encryption and identity between workloads. That design is attractive because it centralizes a hard security concern, but it also adds moving parts, failure modes, and operational overhead.

```text
┌─────────────────────────────────────────────────────────────┐
│              mTLS EXPLAINED                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  REGULAR TLS (one-way)                                      │
│  Client ──────→ Server                                      │
│  • Client verifies server identity                          │
│  • Server doesn't verify client                             │
│  • Like HTTPS to a website                                  │
│                                                             │
│  MUTUAL TLS (two-way)                                       │
│  Client ←─────→ Server                                      │
│  • Client verifies server identity                          │
│  • Server verifies client identity                          │
│  • Both parties authenticated                               │
│                                                             │
│  IN KUBERNETES:                                             │
│  • Service mesh handles mTLS automatically                  │
│  • Each pod gets a certificate                              │
│  • Certificates rotated automatically                       │
│  • Zero Trust networking achieved                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Mutual TLS is more than encryption. It gives the server a cryptographic reason to trust that the caller is a specific workload identity rather than just some pod with network reach. In a well-configured mesh, authorization can say that `frontend` may call `backend` on a narrow set of routes, while a debug pod in the same namespace cannot. NetworkPolicy may still allow or deny the TCP path, but the mesh can make a richer decision after the connection reaches the proxy.

| Feature | Description |
|---------|-------------|
| **mTLS** | Automatic encryption between services |
| **Identity** | Cryptographic identity for each workload |
| **Authorization** | Fine-grained access policies |
| **Observability** | Traffic metrics, tracing |
| **Traffic control** | Rate limiting, retries, timeouts |

Those features are powerful, but they should not lead to "mesh solves everything" thinking. Service mesh usually protects traffic that participates in the mesh. It may not cover host-network pods, node-local agents, traffic that bypasses sidecars, or components excluded from injection. NetworkPolicy remains useful because it constrains packet paths before application-layer policy is even evaluated. Defense in depth means the mesh and the CNI disagree safely: if either layer denies an unexpected path, the path fails.

```text
┌─────────────────────────────────────────────────────────────┐
│              WHY ENCRYPT INTERNAL TRAFFIC?                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  "But it's inside my network, why encrypt?"                 │
│                                                             │
│  THREAT: Network eavesdropping                              │
│  • Compromised node can sniff traffic                       │
│  • Network devices could be compromised                     │
│  • Cloud provider could theoretically observe               │
│                                                             │
│  THREAT: Man-in-the-middle attacks                          │
│  • Without mTLS, pods can impersonate others                │
│  • No verification of "who is talking to who"               │
│                                                             │
│  COMPLIANCE:                                                │
│  • Many regulations require encryption in transit           │
│  • PCI-DSS, HIPAA, SOC2 often require it                    │
│                                                             │
│  ZERO TRUST:                                                │
│  • Assume the network is compromised                        │
│  • Encrypt everything, verify everything                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

A common production pattern is to start with NetworkPolicy for coarse isolation and add service mesh mTLS for sensitive service-to-service calls. For example, a payment namespace might deny all ingress except from ingress gateways and approved backend namespaces, then require mTLS inside the namespace and enforce service identities at the mesh layer. If a compromised pod lands in a neighboring namespace, the CNI blocks most paths. If it reaches a permitted port through a mislabel or approved gateway, the mesh still demands the right identity.

| Mesh | Description |
|------|-------------|
| **Istio** | Full-featured, complex, widely adopted |
| **Linkerd** | Lightweight, simple, fast |
| **Cilium** | eBPF-based, combined CNI and mesh |
| **Consul Connect** | HashiCorp's service mesh |

Choosing among mesh options is not only a feature comparison. Istio offers extensive traffic management and policy surfaces, which can be valuable in large platform teams but demanding for small teams. Linkerd emphasizes simplicity and automatic mTLS, which can reduce operational friction. Cilium can combine CNI policy, eBPF observability, and encryption features in one ecosystem. Consul Connect may fit organizations already invested in HashiCorp service discovery. The right choice depends on who will operate it during incidents, upgrades, and certificate rotations.

Pause and predict: NetworkPolicy allows `frontend` to reach `backend`, and the mesh requires mTLS for `backend`. What happens if a pod without a mesh identity tries to call `backend` from an allowed source namespace? The packet may pass the CNI rule if selectors match, but the mesh proxy should reject the connection because the peer cannot complete the required identity handshake. That is the point of layered controls.

Encryption scope also deserves precise language. Some CNI plugins can encrypt node-to-node pod traffic using mechanisms such as WireGuard or IPsec. That protects traffic on the wire between nodes, but it may not provide workload-level identity or HTTP-aware authorization. Service mesh mTLS provides workload identity and can support Layer 7 policy, but only for traffic in the mesh path. Both approaches can be valid. Confusion starts when teams say "encrypted" without naming what is encrypted, where keys live, and which identity is authenticated.

The operational burden is real. Mesh certificates must rotate reliably, sidecars or ambient components must be upgraded, policy rollouts need staged validation, and observability systems must distinguish network denies from application denies. A broken mesh control plane can affect deployments or traffic behavior even when application code did not change. That does not make service mesh a bad idea; it means mTLS should be introduced with ownership, runbooks, and rollback plans rather than as a checkbox after an audit finding.

When a mesh is introduced after NetworkPolicy, plan the migration path carefully. Start by observing traffic and enabling permissive mTLS modes where the mesh supports them, then move sensitive namespaces toward strict modes once every workload is enrolled and tested. If strict mTLS is enabled before all clients have sidecars or compatible identities, failures can look like random application outages. A calm migration treats identity as a rollout with dependencies, health checks, and rollback criteria, not as a switch flipped across the cluster.

Identity naming also matters. Workload identities should map to service accounts, namespaces, and deployment ownership in a way humans can audit. If every service runs under a broad default service account, mTLS proves only that "some workload in this namespace" connected, which may not be enough for sensitive APIs. Pair mesh identity with service account hygiene from earlier security modules. Network security gets stronger when workload identity, RBAC, labels, and policy all describe the same architecture.


## Compare Controls in a Defense-in-Depth Design

Network security choices become easier when you separate the questions each control answers. NetworkPolicy asks, "Is this source allowed to open this network path to this destination and port?" CNI encryption asks, "Can an observer on the network read packets between nodes or endpoints?" Service mesh mTLS asks, "Can both workloads prove their identities and establish an encrypted session?" Mesh authorization asks, "Is this authenticated caller allowed to perform this application-level action?" These controls overlap, but they are not identical.

| Control | Best At | Main Blind Spot | Typical Owner |
|---------|---------|-----------------|---------------|
| NetworkPolicy | Namespace and pod segmentation by selector, CIDR, port, and protocol | No built-in encryption or Layer 7 request awareness | Platform networking team |
| CNI encryption | Protecting pod traffic on the wire between nodes or dataplane endpoints | May not provide workload identity or HTTP authorization | Platform networking team |
| Service mesh mTLS | Workload identity, certificate rotation, and encrypted service-to-service sessions | Only protects traffic that participates in the mesh path | Platform or service mesh team |
| Mesh authorization | Method, path, principal, and service-level policy | Depends on correct mesh enrollment and proxy enforcement | Application platform team |
| Application auth | Business authorization and user-aware decisions | Cannot replace network segmentation after compromise | Application team |

The practical design sequence is usually coarse to fine. First, select a CNI that enforces policy and apply default-deny baselines to sensitive namespaces. Second, allow known service paths with narrow selectors and ports. Third, add egress controls for workloads that handle sensitive data or credentials. Fourth, introduce mTLS where plaintext traffic, workload impersonation, or compliance requirements justify the complexity. Fifth, add Layer 7 authorization for APIs whose risk cannot be captured by a port number.

The sequence should remain testable. For every important path, write a positive test and a negative test. A positive test proves the application can still do its job. A negative test proves an unapproved pod, namespace, or identity cannot do the same thing. Without both sides, you either have a brittle security design that breaks production or a comfortable design that permits the attacker path you meant to close.

War story: a financial services platform team once rolled out egress deny policies to a namespace holding internal APIs. The change passed a manifest review because every backend-to-database path was represented, but production error rates climbed after deployment. The missing dependency was not the database; it was a token introspection endpoint used during authentication and a DNS TCP fallback path triggered by large responses. The fix was not to abandon egress policy. The fix was to add dependency discovery, staged shadow testing, and explicit exceptions that were reviewed like code.

This is why network policy design belongs in normal delivery workflows. Labels should be part of deployment conventions, policy changes should be reviewed beside application changes, and new service dependencies should update the traffic contract. A policy repository that nobody touches after initial rollout becomes stale quickly. The cluster will keep accepting deployments, service names will keep resolving, and the network will gradually diverge from the security model unless policy review is treated as a living practice.

A final comparison point is failure behavior. NetworkPolicy failures often appear as timeouts, mesh mTLS failures may appear as TLS handshake errors or proxy-denied responses, and application authorization failures may appear as HTTP 403 responses or domain-specific error messages. Good runbooks teach responders how to distinguish those layers. Without that discipline, teams may loosen the wrong control during an outage. The fastest recovery is not always the safest recovery; the right goal is to identify which layer blocked which request and whether the block matched the intended policy.

For KCSA preparation, practice narrating the control stack in simple language. A strong answer sounds like this: "The CNI enforces NetworkPolicy to limit pod reachability, egress policy limits exfiltration paths, CNI or mesh encryption protects traffic in transit, and service mesh mTLS gives workloads cryptographic identity for sensitive service calls." That explanation is more useful than listing product names because it ties each mechanism to the threat it addresses.


## Patterns & Anti-Patterns

Patterns in Kubernetes network security are useful because they encode operational lessons that are easy to forget under delivery pressure. A good pattern should tell you when to use it, why it works, and how it scales as the cluster gains more namespaces and teams. The table below favors patterns that can be tested with ordinary Kubernetes resources and improved later with CNI or mesh-specific features.

| Pattern | When to Use It | Why It Works | Scaling Consideration |
|---------|----------------|--------------|-----------------------|
| Namespace default deny | Any namespace with production, regulated, or multi-team workloads | It turns implicit reachability into explicit allows | Apply with templates or policy-as-code so new namespaces start isolated |
| Tier-to-tier allow rules | Applications with clear frontend, backend, and data tiers | It matches traffic to application architecture instead of arbitrary pod names | Require stable labels and ownership for label changes |
| DNS as an explicit dependency | Any namespace with egress isolation | It prevents silent service discovery failures after egress deny | Inspect actual CoreDNS labels per cluster before copying examples |
| Negative connectivity tests | Every material policy rollout | It proves that denied traffic is really denied by the CNI | Automate probes in CI or pre-production namespaces |
| Mesh mTLS for sensitive APIs | Services carrying credentials, payment data, personal data, or privileged control actions | It adds encryption and workload identity above network reachability | Assign ownership for certificates, upgrades, and policy debugging |

Anti-patterns usually appear because teams try to reduce friction. They deploy a broad allow rule to stop an outage, let labels drift because a release is urgent, or assume a namespace name carries more meaning than it actually does. These shortcuts feel reasonable in the moment, but they remove the evidence trail a security team needs during an incident.

| Anti-pattern | What Goes Wrong | Better Alternative |
|--------------|-----------------|--------------------|
| Policy objects on a non-enforcing CNI | The API accepts manifests while packets remain unrestricted | Prove enforcement with live deny tests before claiming coverage |
| One giant allow-all egress exception | Compromised pods can exfiltrate data to arbitrary destinations | Write tier-specific egress rules and review external dependencies |
| Trusting namespace boundaries alone | Cross-namespace traffic remains open by default | Add namespace isolation policies with approved namespace labels |
| Label sprawl without ownership | Any workload can accidentally match privileged allow rules | Define label conventions and review security-sensitive labels |
| Mesh-only segmentation | Non-mesh or bypass traffic may remain reachable | Keep NetworkPolicy as the coarse network boundary |

The healthy pattern is boring: write down intended flows, encode them narrowly, test allowed and denied cases, and revisit the contract when the application changes. Kubernetes gives you dynamic infrastructure, which means yesterday's correct policy can become incomplete tomorrow. Treat the policy set as application architecture, not as a one-time security artifact.


## Decision Framework

Use this framework when you need to decide which network security control belongs in a design. Start with the threat, not with the tool. If the risk is broad lateral movement between pods, NetworkPolicy is the first control to evaluate. If the risk is packet visibility on the node or underlying network, encryption becomes central. If the risk is workload impersonation or application-level authorization, service mesh identity and policy may be required.

```text
┌─────────────────────────────────────────────────────────────┐
│          NETWORK SECURITY DECISION FLOW                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Do pods need unrestricted namespace-wide reachability?   │
│     ├─ No  → Apply namespace default deny                   │
│     └─ Yes → Document why and add monitoring                │
│                                                             │
│  2. Do specific tiers need specific ports only?              │
│     ├─ Yes → Add tier-to-tier NetworkPolicies               │
│     └─ No  → Revisit application dependency map             │
│                                                             │
│  3. Could sensitive data cross a node or network boundary?   │
│     ├─ Yes → Evaluate CNI encryption or service mesh mTLS   │
│     └─ No  → Confirm with data classification               │
│                                                             │
│  4. Must the receiver verify workload identity?              │
│     ├─ Yes → Require mTLS and identity-aware authorization  │
│     └─ No  → NetworkPolicy may be enough for this path      │
│                                                             │
│  5. Do you need HTTP method, path, or principal rules?       │
│     ├─ Yes → Add mesh or application-layer authorization    │
│     └─ No  → Keep Layer 3/4 policy simple and testable      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

| Situation | Primary Control | Add When Needed | Reasoning |
|-----------|-----------------|-----------------|-----------|
| New production namespace | Default deny NetworkPolicy | Namespace templates and CI probes | Prevents silent open-by-default exposure from the first deployment |
| Three-tier internal app | Tier-specific ingress and egress policy | Mesh mTLS for sensitive backend calls | Encodes expected application paths and limits lateral movement |
| PCI-scoped service traffic | NetworkPolicy plus mTLS | Layer 7 authorization for APIs | Segmentation controls reachability while mTLS protects confidentiality and identity |
| Cluster using basic connectivity-only CNI | CNI replacement or policy add-on | Policy tests after migration | NetworkPolicy cannot protect traffic without an enforcing dataplane |
| Mixed mesh and non-mesh workloads | NetworkPolicy baseline | Mesh authorization for enrolled services | Coarse policy covers bypass paths while mesh handles identity-aware calls |

The decision framework also helps during audits. Rather than saying "we use Cilium" or "we installed Istio," describe the risk and the control that addresses it. For lateral movement, show default deny and negative connectivity tests. For encryption, show the mTLS mode or CNI encryption configuration and a way to verify it. For identity, show which workload identities are allowed. Auditors and incident responders both need evidence, not product names.


## Did You Know?

- **NetworkPolicy became stable in Kubernetes 1.8**, which means the core API has been around for years, but enforcement still depends on the CNI plugin in the cluster.

- **Network policies are namespaced**, so a standard Kubernetes NetworkPolicy cannot create one cluster-wide default deny object for every namespace at once.

- **mTLS authenticates both sides of a connection**, unlike ordinary one-way TLS where the client verifies the server but the server may not verify the client certificate.

- **eBPF-based CNIs such as Cilium can enforce policy in the Linux kernel dataplane**, which enables policy, observability, and load-balancing designs that differ from traditional iptables-heavy approaches.


## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Creating NetworkPolicy on a CNI that does not enforce it | The API server accepts the object, so the manifest looks successful in reviews | Confirm CNI support and run a negative connectivity test before claiming the control works |
| Forgetting DNS after egress isolation | DNS feels like platform plumbing rather than an application dependency | Allow UDP and TCP 53 to the actual DNS pods selected by labels in your cluster |
| Writing ingress policy but assuming egress is controlled too | Engineers read the policy name as a full traffic contract | Define ingress and egress separately, then test each direction with probes |
| Matching privileged access with casual labels | Labels are easy to add during deployments and can drift over time | Treat security-sensitive labels as owned API fields and review changes to them |
| Allowing all egress to avoid launch risk | Teams fear breaking hidden dependencies during rollout | Discover dependencies in staging, then allow named destinations and ports by tier |
| Assuming service mesh replaces NetworkPolicy | Mesh policy may not cover non-mesh, host-network, or bypass traffic | Keep NetworkPolicy as the coarse network boundary and use mesh identity above it |
| Copying namespaceSelector examples without namespace label governance | A namespace label can become an authorization decision without ownership | Restrict who can set security-relevant namespace labels and audit them regularly |
| Treating encryption as identity | Encrypted traffic can still come from the wrong workload if peer identity is not verified | Use mTLS or another authenticated identity mechanism when receivers must trust callers |


## Quiz

<details><summary>Question 1: Your team deploys a production namespace with no NetworkPolicy objects, and a temporary pod in `default` can connect to the production database service. What do you check and change first?</summary>

Start by recognizing that this is expected default Kubernetes behavior, not proof that the database service is misconfigured. Check whether the cluster CNI enforces NetworkPolicy, then add a namespace default-deny baseline and explicit database ingress rules from the backend role. The first safe change is not a broad deny copied into production blindly; it is a tested policy design that includes required flows such as backend access and DNS. This answer maps to the flat network model because the issue is lateral reachability created by default-open pod networking.

</details>

<details><summary>Question 2: A backend pod is selected by two ingress policies. One allows `app=frontend` on port 8080, and another allows `app=monitoring` on port 9090. A frontend pod tries port 9090. Is the traffic allowed?</summary>

The traffic is denied because NetworkPolicy allows the union of complete allowed rules, not a mix-and-match combination of sources and ports. The union here is frontend on 8080 or monitoring on 9090. Frontend on 9090 satisfies neither allowed path. This is why policy reviews should read each rule as a source-and-port tuple rather than as separate piles of allowed labels and allowed ports.

</details>

<details><summary>Question 3: A security lead finds that NetworkPolicy manifests exist, but a deny test still allows traffic to a selected pod. What diagnosis should come before editing selectors?</summary>

Verify that the CNI plugin supports and has enabled NetworkPolicy enforcement in this cluster mode. Kubernetes can store NetworkPolicy objects even when the dataplane does not enforce them, so a successful `k apply` is not proof of protection. After capability is confirmed, inspect namespace placement, pod labels, policy selectors, and any additional policies that may allow the flow. This order prevents wasting time on YAML changes when the enforcement layer is absent.

</details>

<details><summary>Question 4: Your payment backend must prove that callers are approved workloads and must encrypt pod-to-pod traffic. NetworkPolicy already restricts the port. What should you add?</summary>

Add workload-authenticated encryption such as service mesh mTLS, then use identity-aware authorization for the payment backend. NetworkPolicy restricts reachability at Layer 3 and Layer 4, but it does not authenticate the application identity inside the caller pod and does not encrypt payloads by itself. mTLS lets both sides verify peer identity while encrypting the session. Keep NetworkPolicy in place because it still limits which network paths can reach the mesh-protected service.

</details>

<details><summary>Question 5: An egress policy rollout breaks service-name resolution for pods that otherwise have correct application allow rules. What was probably missed?</summary>

The policy probably forgot DNS egress to CoreDNS or kube-dns. Once egress policy selects a pod, outbound DNS is denied unless explicitly allowed, and service discovery fails before the application can reach its intended destination. The fix is to inspect the DNS pod labels in `kube-system` and allow UDP and TCP 53 to those pods. This should be tested as part of every egress policy rollout because DNS is a hidden dependency in nearly every Kubernetes application.

</details>

<details><summary>Question 6: A colleague says Istio AuthorizationPolicy makes Kubernetes NetworkPolicy redundant. How do you respond in a design review?</summary>

They are complementary controls. NetworkPolicy constrains network reachability before traffic reaches the service proxy, while Istio authorization can make identity-aware or request-aware decisions after mTLS and proxy processing. Mesh policy may not protect non-mesh workloads or bypass paths, and NetworkPolicy cannot express HTTP methods or workload principals by itself. A strong design uses NetworkPolicy for coarse segmentation and mesh policy for authenticated service-level authorization where the risk justifies it.

</details>

<details><summary>Question 7: A platform team wants one standard policy for all new namespaces. What minimum evidence should they require before calling the pattern safe?</summary>

They should require proof that the CNI enforces policy, a default-deny baseline, explicit allow templates for DNS and approved platform traffic, and positive plus negative connectivity tests. The policy should also define label ownership, because namespace and pod labels can become authorization inputs. A standard template is valuable only if it is paired with validation in real clusters. Otherwise the organization may scale a false sense of segmentation across every new namespace.

</details>


## Hands-On Exercise: Network Policy Design

In this exercise, you will design and test policies for a three-tier application in a lab namespace. The goal is not to memorize a perfect YAML file; it is to practice converting traffic requirements into selectors, ports, directions, and validation checks. Use a disposable cluster where your CNI supports NetworkPolicy, because the negative tests are part of the lesson.

**Scenario**: Design network policies for a three-tier application where each tier has a distinct label, a narrow set of required connections, and a clear review expectation that arbitrary pod-to-pod traffic should fail.

- Frontend pods (label: `tier=frontend`)
- Backend pods (label: `tier=backend`)
- Database pods (label: `tier=database`)

The requirements below describe the intended traffic contract in plain language before you encode it as Kubernetes policy:

1. Frontend can receive traffic from anywhere
2. Backend can only receive traffic from frontend
3. Database can only receive traffic from backend
4. No pod should have unrestricted egress

### Setup

Create a namespace and three simple pods. In a real cluster you would use Deployments, but pods keep the lab small enough to inspect directly. The commands below assume you already created the `k` alias described at the start of the module.

```bash
k create namespace app
k -n app run frontend --image=nginx:1.27 --labels=tier=frontend --port=80
k -n app run backend --image=nginx:1.27 --labels=tier=backend --port=8080
k -n app run database --image=postgres:17 --labels=tier=database --env=POSTGRES_PASSWORD=example-only --port=5432
k -n app run probe --image=curlimages/curl:8.10.1 --restart=Never -- sleep 3600
k -n app get pods --show-labels
```

### Tasks

- [ ] Confirm that your CNI enforces NetworkPolicy by running one reachable baseline test and one denied test.
- [ ] Create a default-deny policy that selects every pod in the `app` namespace for ingress and egress.
- [ ] Allow frontend ingress from anywhere while keeping backend and database protected from arbitrary sources.
- [ ] Allow frontend egress to backend on 8080 and backend egress to database on 5432.
- [ ] Add DNS egress rules using the actual CoreDNS or kube-dns labels from your cluster.
- [ ] Document one positive test and one negative test for each tier so reviewers can verify the design.

<details><summary>Solution</summary>

```yaml
# 1. Default deny all ingress and egress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: app
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
# 2. Allow ingress to frontend from anywhere
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: frontend-ingress
  namespace: app
spec:
  podSelector:
    matchLabels:
      tier: frontend
  policyTypes:
  - Ingress
  ingress:
  - {}  # Allow from anywhere
# 3. Allow frontend to reach backend
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-from-frontend
  namespace: app
spec:
  podSelector:
    matchLabels:
      tier: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: frontend
    ports:
    - port: 8080
# 4. Allow backend to reach database
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: database-from-backend
  namespace: app
spec:
  podSelector:
    matchLabels:
      tier: database
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: backend
    ports:
    - port: 5432
# 5. Allow frontend egress to backend
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: frontend-egress
  namespace: app
spec:
  podSelector:
    matchLabels:
      tier: frontend
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector:
        matchLabels:
          tier: backend
    ports:
    - port: 8080
  - to:  # Allow DNS
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - port: 53
      protocol: UDP
# 6. Allow backend egress to database
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-egress
  namespace: app
spec:
  podSelector:
    matchLabels:
      tier: backend
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector:
        matchLabels:
          tier: database
    ports:
    - port: 5432
  - to:  # Allow DNS
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - port: 53
      protocol: UDP
```

The solution preserves the core three-tier design, but you should adapt DNS selectors to your cluster. Some clusters label DNS pods differently, and some require TCP 53 as well as UDP 53. You should also add database egress only if the database truly needs backups, replication, or external services.

</details>

### Success Criteria

- [ ] `app` namespace has a default-deny policy selecting all pods for ingress and egress.
- [ ] Frontend ingress works from an approved source, and backend ingress from an arbitrary probe pod fails.
- [ ] Backend can reach database on 5432, and frontend cannot reach database directly.
- [ ] DNS resolution still works for tiers that need service discovery.
- [ ] `k describe networkpolicy -n app` shows selectors and ports that match the documented traffic contract.


## Operational Recap

Network security in Kubernetes requires active configuration. The default fabric is designed for connectivity, not for isolation, so the secure posture comes from the policies, labels, dataplane capabilities, and identity systems you add around it. Keep this recap table close during reviews because it separates the major concepts that teams often blend together.

| Concept | Key Points |
|---------|------------|
| **Default Behavior** | All pods can reach all pods - implement default deny |
| **CNI Plugins** | Choose one that supports network policies (Calico, Cilium) |
| **Network Policies** | Additive, namespace-scoped, require explicit allows |
| **Service Mesh** | Provides mTLS, identity, and fine-grained authorization |
| **mTLS** | Encrypts traffic AND verifies both parties |

Key patterns remain straightforward even when the underlying implementation is sophisticated. Start with default deny, allow only required traffic, consider egress controls for data-bearing workloads, use mTLS for sensitive communications, and verify that your CNI supports the policy semantics you depend on. The best designs are not the longest YAML files; they are the designs whose intended traffic can be explained, tested, and defended during an incident.

## Sources

- [Kubernetes: Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- [Kubernetes: Cluster Networking](https://kubernetes.io/docs/concepts/cluster-administration/networking/)
- [Kubernetes: Services, Load Balancing, and Networking](https://kubernetes.io/docs/concepts/services-networking/)
- [Kubernetes: Declare Network Policy](https://kubernetes.io/docs/tasks/administer-cluster/declare-network-policy/)
- [CNI Specification](https://www.cni.dev/docs/spec/)
- [Calico: Kubernetes Default Deny Policy](https://docs.tigera.io/calico/latest/network-policy/get-started/kubernetes-default-deny)
- [Cilium: Kubernetes Network Policy](https://docs.cilium.io/en/stable/network/kubernetes/policy/)
- [Cilium: Transparent Encryption](https://docs.cilium.io/en/stable/security/network/encryption/)
- [Istio: Security](https://istio.io/latest/docs/concepts/security/)
- [Linkerd: Automatic mTLS](https://linkerd.io/2/features/automatic-mtls/)
- [Amazon EKS: Network Policy](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy.html)

## Next Module

[Module 2.4: PKI and Certificates](../module-2.4-pki-certificates/) - Next you will connect network identity to the certificate machinery Kubernetes depends on for trusted control-plane and workload communication.
