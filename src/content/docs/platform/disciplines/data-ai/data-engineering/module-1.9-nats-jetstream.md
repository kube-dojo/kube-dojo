---
title: "NATS JetStream on Kubernetes"
description: "Run production NATS JetStream on Kubernetes via the NACK operator - clusters, streams, consumers, security, observability, and operations."
slug: platform/disciplines/data-ai/data-engineering/module-1.9-nats-jetstream
revision_pending: false
sidebar:
  order: 19
---
> **Complexity**: `[COMPLEX]`
>
> **Time to Complete**: 3 hours
>
> **Prerequisites**: [Module 1.1 - Stateful Workloads & Storage](../module-1.1-stateful-workloads/), [Module 1.7 - Event Streaming Fundamentals](../module-1.7-event-streaming-fundamentals/), [Module 1.8 - CloudEvents and Event-Driven Architecture](../module-1.8-cloudevents-event-driven-arch/), Kubernetes StatefulSets, Helm, Prometheus basics, and comfort reading messaging-system diagrams

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Design** a Kubernetes NATS JetStream topology with Helm, StatefulSet scheduling, NACK ownership, and quorum-aware storage.
- **Implement** Stream and Consumer CRDs with retention, replica, storage, and subject choices that match workload behavior.
- **Compare** NATS Core, JetStream, and Kafka-style streaming trade-offs for request/reply, work queues, fan-out, and replay.
- **Secure and observe** a NATS deployment using accounts, NKey/JWT auth, TLS boundaries, Prometheus metrics, and alert thresholds.
- **Diagnose** pod failure, stream lag, backup, leaf node, and gateway choices without breaking JetStream durability.

## Why This Module Matters

The payments platform did not need another log pipeline. It needed the fraud service to ask for a decision, the checkout service to receive a quick answer, the ledger service to retain the final event, and a small operations team to run the system without turning every sprint into broker maintenance. Kafka could have done parts of that job, but the team was not building a multi-terabyte analytics backbone. They needed low-latency messaging, request/reply, work queues, and selective persistence in one operational surface.

NATS fits that shape when the problem begins with service communication and only some subjects need durability. Core NATS routes messages by subject to active subscribers, so it is excellent for request/reply, fan-out notifications, and lightweight command traffic. JetStream adds persistence, replay, pull consumers, durable state, key/value buckets, and object storage on top of the same subject space. The result is not "Kafka but smaller"; it is a different design center where subjects are the routing language and streams are storage policies attached to parts of that language.

Kubernetes makes the decision more interesting. A single NATS server is simple, but production JetStream needs stable identity, persistent volumes, quorum-aware replicas, pod spreading, monitoring, security boundaries, and declarative stream ownership. The official NATS Kubernetes path uses the Helm chart to run the server cluster as a StatefulSet, while NACK reconciles JetStream resources such as Streams, Consumers, Accounts, KeyValue buckets, and ObjectStores. That split is important because it prevents a common beginner mistake: installing NACK and assuming it created the broker.

The closest sibling in this track is [Module 1.2 - Apache Kafka on Kubernetes](../module-1.2-kafka/). Strimzi owns the whole Kafka lifecycle, including brokers, topics, users, and rebalancing. NATS today is a two-layer operator path: Helm owns the server workload, and NACK owns JetStream desired state. That difference changes what you review in GitOps, what you alert on, and what you blame during an outage. You will learn the mechanics, but the bigger skill is choosing where NATS belongs in a platform architecture.

The analogy is a campus mailroom. Core NATS is the runner who moves envelopes to anyone currently waiting at the right desk. JetStream is the set of locked shelves behind the counter where important envelope classes are stored until the right team signs for them. NACK is the inventory clerk who keeps the shelves and pickup rules matching the written policy. Kubernetes is the building manager that keeps the mailroom staffed, powered, and spread across rooms so one flood does not take every shelf with it.

> **Stop and think**: If your workload needs every event retained for analytics, every consumer group isolated, and partitions planned months ahead, Kafka may still be the better tool. If your workload needs service messaging first and durable replay for selected subject families, NATS JetStream deserves serious consideration.

## Why NATS Fits the Operator Path

NATS starts from subject-based messaging rather than a topic log. A publisher sends to a subject such as `orders.created.us-east`, subscribers express interest in exact subjects or wildcard patterns, and the server routes messages to interested clients without clients knowing where each other live. That location transparency is why NATS often appears in control planes, edge systems, microservice request/reply paths, and event fabrics where service identity changes faster than the message contract. Subjects are not just names; they are the address space of the system.

JetStream changes the durability story without replacing that address space. A stream captures messages matching one or more subject patterns and applies limits such as retention policy, storage type, replica count, maximum age, and maximum bytes. A consumer tracks delivery state for a stream, including acknowledgment policy, redelivery behavior, filtering, and durable identity. This separation lets one subject family behave like a work queue, another like a replayable event feed, and another like an ephemeral notification lane.

Use NATS when the primary question is "who is interested in this message right now, and which subset must be persisted?" Use Kafka when the primary question is "how do we retain a high-throughput ordered log for many independent readers over a long retention window?" That is not a value judgment. It is an operational fit question. Kafka makes partitions explicit and treats retained logs as the center of the universe; NATS makes subjects explicit and lets you decide which subjects deserve JetStream storage.

The operator path is attractive because JetStream configuration is too important to hide in application startup code. A developer can call the JetStream API to create a stream, but that makes production policy drift invisible to platform review. With NACK, a stream such as `ORDERS` becomes a Kubernetes object with a spec, status, events, and Git history. The platform team can review whether replicas are three, storage is file-backed, subjects are narrow, and work-queue retention is intentional before the first producer starts.

The trade-off is ownership clarity. The official NATS Helm chart deploys the NATS server cluster as Kubernetes resources, while NACK reconciles JetStream resources against that cluster. Older tutorials may mention a `NatsCluster` CRD from the deprecated `nats-operator`; current primary guidance points learners at the Helm chart for server bootstrap and NACK for JetStream desired state. If your organization wraps the chart in an internal `NatsCluster` abstraction, review the generated StatefulSet and values as the real production contract.

The mental model below keeps the layers separate:

```text
+---------------- Kubernetes platform ----------------+
| Namespace, StatefulSet, PVCs, Services, Pod spread   |
|   created by the official NATS Helm chart            |
+-----------------------+-----------------------------+
                        |
                        v
+---------------- NATS server cluster -----------------+
| Core NATS subjects, routes, accounts, JetStream Raft |
|   one NATS server process per StatefulSet pod         |
+-----------------------+-----------------------------+
                        |
                        v
+---------------- NACK reconciler ---------------------+
| Stream, Consumer, Account, KeyValue, ObjectStore CRs |
|   translated into JetStream API calls and status      |
+------------------------------------------------------+
```

Production story: CNCF's NATS project page links a DeFacto case study that describes 27.5 million events published over a 100-hour period, which is a useful reminder that NATS is not only a toy broker for demos. The more important lesson is architectural rather than numerical. Teams choose NATS when the shape of the problem values a unified messaging fabric across edge, cloud, and hybrid deployments, then they add JetStream where selected traffic needs persistence and replay.

> **Pause and predict**: A team wants low-latency request/reply between services, durable order events for recovery, and a simple work queue for PDF generation. Which parts should use Core NATS, which parts should use JetStream, and which parts might still belong in Kafka?

## NACK Operator and Cluster Bootstrap

The NATS server cluster is the foundation. On Kubernetes, the official chart creates a StatefulSet, a headless service, a client service, config, optional monitoring, and a `nats-box` deployment that includes the `nats` CLI. Enabling clustering gives each pod a stable identity and a route mesh. Enabling JetStream gives each server local storage and the ability to participate in replicated stream and consumer state. Enabling file storage with PVCs is the normal choice for production durability.

The NACK controller is installed after the server cluster has a stable NATS URL. It connects to NATS like an administrative client and reconciles Kubernetes CRDs into JetStream resources. In legacy mode, NACK manages Streams and Consumers. In control-loop mode, it can also reconcile Accounts, KeyValue, and ObjectStore resources. The practical takeaway is simple: Helm values are your server-cluster desired state, and NACK CRDs are your messaging-resource desired state.

For a three-pod JetStream cluster, scheduling matters as much as YAML correctness. Three replicas only protect you if they do not collapse onto the same node or failure domain. In a kind lab, that means three worker nodes and strict pod spreading across hostnames. In a real cluster, it means topology spread constraints or required pod anti-affinity across nodes, plus storage classes that do not silently bind every PVC to the same fragile device. A replicated stream cannot outvote a node failure if two replicas lived on that node.

A production-grade chart values file should make the topology obvious. The exact values evolve with chart releases, so treat this as the shape to review rather than a magic incantation. Notice that server replicas live under `config.cluster.replicas`, JetStream file storage gets a PVC, the Prometheus exporter is enabled separately from the NATS monitor endpoint, and pod spread is explicit. The NATS chart is doing the Kubernetes workload work that a deprecated `NatsCluster` CRD used to imply.

```yaml
# nats-lab-values.yaml
config:
  cluster:
    enabled: true
    replicas: 3
  jetstream:
    enabled: true
    fileStore:
      enabled: true
      pvc:
        enabled: true
        size: 2Gi
    memoryStore:
      enabled: true
      maxSize: 256Mi
  monitor:
    enabled: true

promExporter:
  enabled: true
  podMonitor:
    enabled: false

podTemplate:
  topologySpreadConstraints:
    kubernetes.io/hostname:
      maxSkew: 1
      whenUnsatisfiable: DoNotSchedule
  merge:
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchLabels:
                  app.kubernetes.io/name: nats
                  app.kubernetes.io/instance: nats
              topologyKey: kubernetes.io/hostname

podDisruptionBudget:
  enabled: true

natsBox:
  enabled: true
```

Install order should be boring. Add the NATS Helm repository, install the server cluster, wait for the StatefulSet rollout, install NACK with the NATS service URL, then wait for the controller. If NACK starts before NATS is reachable, it should recover, but clean ordering removes noise from the lab and from production automation. A namespaced controller is a good default for platform teams that run multiple NATS systems in one Kubernetes cluster.

```bash
helm repo add nats https://nats-io.github.io/k8s/helm/charts/
helm repo update

helm upgrade --install nats nats/nats \
  --namespace nats \
  --create-namespace \
  --values nats-lab-values.yaml \
  --wait

kubectl -n nats rollout status statefulset/nats --timeout=300s

helm upgrade --install nack nats/nack \
  --namespace nats \
  --set namespaced=true \
  --set jetstream.nats.url=nats://nats.nats.svc.cluster.local:4222 \
  --set 'jetstream.additionalArgs={--control-loop}' \
  --wait

kubectl -n nats rollout status deployment/nack --timeout=180s
```

Server pools are an architectural pattern rather than a required first lab feature. You may run a core messaging pool with memory-only JetStream disabled, a storage pool with SSD-backed JetStream enabled, or region-specific pools connected through gateways and leaf nodes. The chart exposes patch and merge hooks for NATS server config, pod templates, and services, so mature platforms often wrap those values in their own higher-level interface. The important review point is whether the abstraction still exposes durability, topology, security, and observability choices.

After bootstrap, validate the three layers independently. Kubernetes should show three ready NATS pods and three PVCs. NATS should report three servers in the cluster and JetStream enabled. NACK should show its deployment ready and the CRDs available. This avoids a confusing failure mode where Kubernetes is green, NACK is green, but JetStream is not actually enabled on the server cluster. Green pods are not the same thing as a durable messaging fabric.

```bash
kubectl -n nats get pods,pvc
kubectl -n nats get crd | grep jetstream.nats.io
kubectl -n nats exec deployment/nats-box -- nats server list
kubectl -n nats exec deployment/nats-box -- nats account info
```

> **Stop and think**: If `kubectl get pods` is healthy but `nats account info` does not show JetStream, which layer is misconfigured: Kubernetes scheduling, server config, or NACK reconciliation?

## JetStream Streams Consumers and Retention

A stream is the storage policy for a subject set. It does not have to own every subject in the system, and it should not own subjects accidentally. A stream named `ORDERS` might capture `orders.created`, `orders.paid`, and `orders.cancelled`, while a request/reply subject such as `fraud.check` remains Core NATS only. This is one of the strongest JetStream design skills: make persistence intentional instead of turning every message into retained data.

Retention policy defines when stored messages can leave. `limits` retention keeps messages until configured limits such as age, count, or bytes remove them, which is the closest fit for replayable event history. `workqueue` retention deletes each message after successful acknowledgment by its matching consumer, which fits task queues where one worker should complete the job. `interest` retention keeps messages only while matching consumers have interest, which is useful but easy to misuse because publishing before consumers exist can discard data.

Storage type changes the failure model. File storage persists stream data to disk and is the default production choice for business events, commands that must survive restarts, and work items that cannot be recreated. Memory storage is fast and can be useful for short-lived, low-risk traffic, but it is not a substitute for durable event history. Replicas change the quorum model. A stream with three replicas can tolerate one server loss while preserving majority, assuming pods and volumes are spread across failure domains.

Consumers are delivery state, not just subscriber names. A durable pull consumer can track which messages have been delivered and acknowledged, survive client restarts, and let horizontally scaled workers fetch batches under application control. A push consumer sends messages to a delivery subject, which can be elegant for simple integrations but requires care around flow control, ack policy, and queue semantics. NATS documentation recommends pull consumers for new projects when scalability, detailed flow control, or error handling matter.

Here is a stream and pull consumer pair managed by NACK. The stream uses file storage, three replicas, explicit subjects, bounded age and bytes, and `limits` retention. The consumer is durable, filters one subject, requires explicit acknowledgments, limits redelivery, and starts from all available messages. In a real platform, put these resources in the same GitOps path as the application contract that publishes and consumes them, not in an application init container.

```yaml
# orders-jetstream.yaml
apiVersion: jetstream.nats.io/v1beta2
kind: Stream
metadata:
  name: orders-stream
  namespace: nats
spec:
  name: ORDERS
  subjects:
    - orders.created
    - orders.paid
    - orders.cancelled
  storage: file
  replicas: 3
  retention: limits
  maxAge: 24h
  maxBytes: 1073741824
  discard: old
---
apiVersion: jetstream.nats.io/v1beta2
kind: Consumer
metadata:
  name: order-worker
  namespace: nats
spec:
  streamName: ORDERS
  durableName: order-worker
  deliverPolicy: all
  filterSubject: orders.created
  ackPolicy: explicit
  ackWait: 30s
  maxDeliver: 5
  replayPolicy: instant
```

Work-queue retention is the place where NATS can surprise Kafka-shaped thinking. In Kafka, multiple consumer groups can independently read the same retained topic. In a JetStream work queue, a message should be consumed once for a subject filter and then removed after acknowledgment. That is perfect for jobs such as invoice rendering or image resizing, but it is wrong for analytics fan-out where several independent teams need the same event. For fan-out, use `limits` retention and separate durable consumers.

Key/value buckets sit on top of streams and are useful for small, immediately consistent maps such as feature flags, service routing hints, or coordination metadata. They are not a relational database and they are not a replacement for application state, but they can remove a surprising amount of custom "watch this config subject and rebuild a map" code. With NACK, KeyValue resources require control-loop mode, so platform teams should decide explicitly whether that controller mode is part of their supported surface.

The worked example is an order pipeline. Checkout publishes `orders.created`; a fulfillment worker pulls from a durable consumer; analytics reads from a separate durable consumer over the same stream; and a PDF rendering queue uses a different stream with `workqueue` retention. The order event is retained for replay, but the PDF job is deleted after success. That split is the difference between an event history and a task queue, even though both are expressed through JetStream.

```text
orders.created ---> Stream ORDERS retention=limits replicas=3
                     | consumer fulfillment-created ack=explicit
                     | consumer analytics-created ack=explicit
                     |
pdf.render.request -> Stream PDF_TASKS retention=workqueue replicas=3
                       consumer pdf-workers ack=explicit
```

> **Pause and predict**: If analytics needs to replay last night's `orders.created` events after a bug fix, why would `workqueue` retention be the wrong policy for the `ORDERS` stream?

## Subjects Message Patterns and Security

Subject design is the NATS equivalent of API design. A subject such as `orders.created.us-east.store-17` gives operators, security policy, stream filters, and consumers useful routing context. A subject such as `events` moves all meaning into payloads, which makes authorization, debugging, and stream capture harder. NATS supports wildcard subscriptions with `*` for one token and `>` for one or more trailing tokens, so a subject hierarchy should be stable enough for humans and precise enough for policy.

A good subject hierarchy starts broad and ends specific. Use the first token for a domain or product boundary, the next tokens for event or command meaning, and the final tokens for region, tenant, or entity only when those dimensions are needed for routing or authorization. Do not encode the entire payload into the subject. Headers and payloads still exist for metadata and business data. The subject should answer "where should this message go?" rather than "what is every fact about this message?"

NATS gives you several message patterns in one fabric. Plain publish/subscribe broadcasts to all interested subscribers. Queue subscriptions distribute matching Core NATS messages across one member of a queue group. Request/reply lets a client send a request to a subject and wait for a response on an inbox. JetStream pull consumers let workers fetch durable messages under their own backpressure. These patterns can coexist, but they should not be blurred in documentation or review.

The simplest decision guide is to ask what should happen when nobody is listening. If a message should disappear, Core NATS publish/subscribe is likely fine. If a caller needs an immediate answer, request/reply is the fit. If one worker must eventually complete a task, use JetStream with work-queue retention or a durable pull consumer. If several teams must independently replay an event, use JetStream limits retention with separate consumers. If the message must feed a long-term analytics lake, revisit Kafka or object storage integration.

Security is also subject-aware. NATS supports TLS for encrypted connections, authentication for client identity, authorization for publish/subscribe permissions, and multi-tenancy through accounts. Accounts create independent subject namespaces, so `orders.created` in one account is not automatically visible to another account. Exports and imports can intentionally share streams or services between accounts, which is powerful for platform teams that need tenant isolation without duplicating every broker deployment.

NKey and JWT-based security are worth understanding because they change operational ownership. With NKeys, clients prove control of a private key by signing a server challenge; the server does not need to store the private key. With decentralized JWT authentication, operators issue accounts, accounts issue users, and servers validate the trust chain. In Kubernetes, that usually means credentials live in Secrets, NATS contexts mount into `nats-box` or applications, and account boundaries map to teams or environments.

TLS has two boundaries. Client TLS protects application-to-server traffic on the NATS client port, while route, gateway, and leaf node TLS protect server-to-server traffic. A lab may run without TLS so learners can focus on JetStream mechanics, but production should treat plaintext client and route traffic as a temporary exception. The chart supports TLS secret mounts for NATS, cluster, gateway, and leaf node listeners; your platform wrapper should make those choices explicit rather than burying them in a values file nobody reviews.

Subject authorization should be narrow enough to prevent accidental cross-domain writes. A checkout producer might publish `orders.created` and request `fraud.check`, but it should not subscribe to `payments.>` or publish into `$JS.API.>`. A fulfillment worker might subscribe through its durable consumer and publish `orders.fulfilled`, but it should not have permission to delete streams. NACK and administrative credentials need broader rights, which is exactly why those credentials deserve their own account and secret handling.

The security failure mode is often not a dramatic break-in. It is an overbroad wildcard granted for convenience, a shared token reused by every service, or a stream subject pattern that captures data from a tenant it should not see. Those mistakes are hard to clean up after messages have been persisted. Design subjects, accounts, and stream filters together. A neat subject hierarchy makes authorization review possible; a messy hierarchy forces security policy to become a pile of exceptions.

## Observability with Prometheus Surveyor and Alerts

NATS exposes several kinds of operational signals. The server has HTTP monitoring endpoints such as `varz`, `connz`, `routez`, `gatewayz`, and `jsz`. The Prometheus exporter converts selected endpoint data into metrics. NATS Surveyor takes a different approach by using a system account and NATS events to observe servers. The `nats` CLI can show server lists, stream info, consumer state, events, round-trip latency, and account limits from inside `nats-box` or an operator workstation.

Observability should answer four questions before it tries to answer everything. Is the server cluster healthy? Is JetStream enabled and within storage limits? Are streams and consumers keeping up? Are clients failing because of auth, reconnect, slow consumer, or backpressure problems? Dashboards that only show CPU and pod readiness miss the entire messaging layer. Dashboards that only show JetStream storage miss client churn and route health. You need both Kubernetes and NATS-native signals.

The first alert family is availability. Alert when fewer than the expected number of NATS pods are ready, when route count drops, when a StatefulSet rollout stalls, or when the Prometheus scrape target disappears. For a three-node JetStream cluster, one pod loss is degraded but survivable; two pod losses are an emergency for streams with three replicas. Pair Kubernetes readiness alerts with NATS cluster membership alerts so the on-call engineer can distinguish a Kubernetes scheduling problem from a NATS route problem.

The second alert family is JetStream durability. Alert when a clustered stream or consumer loses quorum, when stream leader election churns repeatedly, when replicas are offline for longer than a short maintenance window, or when a stream reports lost messages. NATS JetStream emits advisories for leader election and quorum loss, and the CLI can show replica health in `nats stream info`. These alerts deserve higher severity than generic pod restarts because they speak directly to message durability.

The third alert family is lag and storage pressure. Consumer lag is not only a Kafka concept; JetStream consumers can fall behind when workers are slow, stuck, or underprovisioned. Stream storage usage should alert before limits delete old messages unexpectedly or reject new writes under a discard-new policy. A practical starting threshold is warning at roughly 70 percent of a stream or account storage budget and critical near 85 percent, then tune based on how quickly the workload can grow.

The fourth alert family is slow consumers and redelivery. A slow Core NATS subscriber can be disconnected if it cannot keep up. A JetStream consumer with rising redeliveries may be failing business logic, timing out acknowledgments, or hitting a downstream dependency. Alert on redelivery rate, `num_ack_pending`, and age of the oldest pending message, not only on pod restarts. A worker deployment can look healthy while every message is being retried until `maxDeliver` is exhausted.

Surveyor and Prometheus exporter choices depend on your platform. The exporter is straightforward when the monitor port is reachable to Prometheus and you choose endpoint flags intentionally. Surveyor is useful when system-account events are already part of your NATS security model and you want advisory-driven visibility. Many teams use both during migration: exporter metrics for dashboards and alert math, CLI and event subscriptions for incident diagnosis. The module lab enables the exporter because it is the shortest path to visible metrics.

These example Prometheus rules are intentionally conservative. Names may vary by exporter version and selected endpoint flags, so treat them as patterns to adapt after you inspect real metrics. The teaching point is the threshold logic: alert on missing scrape, storage approaching budget, consumers falling behind, and quorum loss. If your dashboard cannot answer those questions, it is not production observability for JetStream.

```yaml
# nats-jetstream-alerts.yaml
groups:
  - name: nats-jetstream
    rules:
      - alert: NatsExporterMissing
        expr: up{job=~".*nats.*"} == 0
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "NATS metrics target is not being scraped"
          description: "Prometheus cannot scrape the NATS exporter or monitor endpoint."

      - alert: NatsJetStreamStorageHigh
        expr: nats_varz_jetstream_stats_store / nats_varz_jetstream_config_max_store > 0.70
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "JetStream storage usage is above 70 percent"
          description: "Review stream limits, retention policy, and consumer lag before eviction or publish rejection."

      - alert: NatsJetStreamConsumerBacklogGrowing
        expr: increase(nats_consumer_num_pending[10m]) > 1000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "JetStream consumer backlog is growing"
          description: "Workers may be too slow, failing acknowledgments, or blocked by a downstream dependency."
```

> **Stop and think**: A consumer deployment has all pods ready, but `num_ack_pending` rises for twenty minutes and redeliveries begin. Is this a Kubernetes availability problem, an application correctness problem, or a JetStream configuration problem? What evidence would separate the three?

## Operations Backup Leaf Nodes and Cross-Cluster Mesh

Operations begin with a hard truth: replicated streams are not backups. Three JetStream replicas help survive server or node failure, but they do not protect you from accidental deletion, a bad retention change, a buggy producer overwriting a compacted state pattern, or an operator applying the wrong stream spec. For file-backed streams, the `nats stream backup` command creates a snapshot containing stream data and durable consumer state. Restore testing is the only way to know whether that backup is useful.

Backups should have a runbook, not just a cron entry. Decide which streams are backed up, how often, where backup artifacts are stored, how integrity is checked, and how restore is practiced without corrupting production. A critical order stream may need frequent backups and a tested restore into a staging account. A work queue with recreateable jobs may need no backup but a strong dead-letter and replay story. Memory streams do not support snapshots, which is another reason to reserve memory storage for low-risk data.

```bash
kubectl -n nats exec deployment/nats-box -- \
  nats stream backup ORDERS /tmp/orders-backup --no-progress

kubectl -n nats exec deployment/nats-box -- \
  nats stream restore /tmp/orders-backup --no-progress
```

Leaf nodes solve a different problem: locality. A factory, retail store, vehicle, or small regional cluster may need local NATS service even when the WAN is slow or intermittent. A leaf node connects a local NATS server to a remote NATS system, routes messages according to subject interest and permissions, and can keep local traffic local. Leaf nodes are useful when clients should talk to a nearby server but selected subjects still need to reach the central platform.

JetStream on leaf nodes needs careful design. You can run JetStream at the edge for local durability, run JetStream centrally and use leaf connections for access, or combine the two with explicit subject and account boundaries. Do not assume a leaf node magically gives active-active durable storage. Decide where the stream leader lives, what happens during disconnection, whether producers can continue locally, and how duplicate or delayed messages are reconciled when the link returns.

Gateways and superclusters connect clusters, not individual edge servers. Gateways form a mesh between clusters while reducing the connection explosion that a naive full cluster mesh would create. They are useful for multi-region NATS deployments where each region has its own local cluster and accounts need controlled cross-region interest propagation. Queue semantics prefer local subscribers first and can fail over when no local interest exists, which is useful but must be tested before you call it disaster recovery.

Cross-cluster design should separate messaging reachability from data recovery. A gateway can move messages between clusters according to interest. It does not replace a stream backup, a tested restore plan, or an application-level decision about which region owns a durable subject. If two regions accept writes for the same business entity without a conflict strategy, the messaging layer cannot invent one. NATS gives you the network fabric; your architecture still owns consistency, idempotency, and recovery objectives.

Operational readiness also includes upgrades. NATS server, NACK, the Helm chart, Prometheus exporter, and client libraries all have versions. Upgrade one layer at a time, watch route and JetStream health, and verify Stream and Consumer statuses after reconciliation. Because NACK enforces desired state, an emergency manual change made through the CLI may be reverted by the controller. That is good in steady state and surprising during incident response, so the runbook must say which source of truth wins.

The final design review should sound like a set of failure questions. What if one pod dies? What if one node and its volume disappear? What if a consumer is deployed with a bad ack path? What if storage reaches the stream limit at 03:00? What if a team asks for another account? What if an edge site disconnects for a day? If your NATS design answers those questions concretely, you are operating a platform component rather than a convenient message broker.

## Did You Know?

- **NATS was accepted into CNCF at the Incubating maturity level on March 15, 2018**: the project page positions it as connective technology for distributed systems across device, edge, cloud, and hybrid deployments.
- **NACK control-loop mode expands beyond Streams and Consumers**: the NACK README documents support for KeyValue, ObjectStore, and Account resources when the controller is started with control-loop arguments.
- **JetStream file streams are not the same as an immediate disk fsync on every publish**: NATS documentation describes a configurable sync interval for file-backed streams, so durability settings belong in production review.
- **The `nats` CLI can manage streams, consumers, key/value buckets, backups, and restores**: the Kubernetes chart's `nats-box` deployment gives you a ready-made administrative shell inside the cluster.

## Common Mistakes

| Mistake | Why it hurts | Better practice |
|---------|--------------|-----------------|
| Installing NACK and assuming it created NATS | NACK reconciles JetStream resources against an existing server cluster | Install the NATS Helm chart first, then point NACK at the service URL |
| Using deprecated `NatsCluster` examples blindly | Old operator examples do not reflect the current official Helm-plus-NACK path | Treat Helm values as server desired state and NACK CRDs as JetStream desired state |
| Setting stream replicas to one for business events | A pod or node loss can remove the only durable copy | Use three replicas for critical streams and spread pods across failure domains |
| Capturing broad subjects such as `>` in one stream | Sensitive or unrelated traffic may be persisted accidentally | Capture narrow subject families and review stream filters like API contracts |
| Using work-queue retention for analytics fan-out | Messages disappear after the worker acknowledges them | Use limits retention with separate durable consumers for independent readers |
| Granting every service publish and subscribe on `>` | One compromised or buggy client can read or write the whole fabric | Use accounts, scoped users, and subject permissions for each service role |
| Watching only Kubernetes pod readiness | Messaging failures can happen while pods are ready | Monitor route health, JetStream storage, consumer lag, redeliveries, and quorum advisories |
| Treating three replicas as a backup | Replication does not protect against bad config or deletion | Run tested `nats stream backup` and restore exercises for critical file streams |

## Quiz

### 1. Helm is green, NACK is red

Your platform pipeline installs the NATS Helm chart successfully, but every `Stream` CRD stays in an errored state. The NACK logs show connection failures to `nats://nats.default.svc.cluster.local:4222`, while the NATS release was installed in the `nats` namespace. What should you change, and why is this not a Stream spec problem?

<details>
<summary>Answer</summary>

Change the NACK `jetstream.nats.url` to the service name that actually exists, such as `nats://nats.nats.svc.cluster.local:4222` for a release named `nats` in the `nats` namespace. The Stream spec may be valid, but NACK cannot reconcile it until the controller can connect to the server cluster. This tests the design outcome around Helm, NACK ownership, and the separation between server desired state and JetStream desired state.
</details>

### 2. Work queue or replayable event history

A team creates one `ORDERS` stream with `workqueue` retention. Fulfillment workers process `orders.created`, and analytics wants to replay the same events every morning to rebuild a projection. Analytics only sees new messages that fulfillment has not acknowledged yet. What design change should you recommend?

<details>
<summary>Answer</summary>

Use a replayable stream with `limits` retention for `orders.created` and give fulfillment and analytics separate durable consumers. Work-queue retention is for one successful processing path per subject filter; it deletes messages after acknowledgment. Analytics fan-out requires retained history and independent consumer state. If fulfillment truly needs task semantics, create a separate work-queue stream for fulfillment tasks derived from the order event.
</details>

### 3. Consumer lag with ready pods

The `order-worker` Deployment has all replicas ready, but `num_ack_pending` and redeliveries keep rising. Storage usage is also climbing toward the stream limit. What should you inspect before scaling the NATS StatefulSet?

<details>
<summary>Answer</summary>

Inspect the worker acknowledgment path, downstream dependencies, `ackWait`, `maxDeliver`, and the age of pending messages. Ready pods only prove Kubernetes scheduled the application; they do not prove messages are being processed and acknowledged. Scaling NATS may not help if the consumer is failing business logic or timing out. This diagnosis aligns observability signals with application behavior before changing broker capacity.
</details>

### 4. One pod failure in a three-replica stream

You delete `nats-0` during maintenance. The `ORDERS` stream has `replicas: 3`, and pods were spread across three nodes. Producers continue to publish, but `nats stream info ORDERS` shows one offline replica until the pod returns. Is the system healthy, degraded, or broken, and what evidence matters?

<details>
<summary>Answer</summary>

It is degraded but should remain available because two of three replicas still provide a majority. The evidence that matters is stream leader health, replica status, quorum advisories, successful publish acknowledgments, and consumer progress. If two replicas are offline, the system becomes an emergency for that stream. Pod spreading is part of why one pod failure does not remove a majority.
</details>

### 5. Account isolation for tenant traffic

Two product teams both use subjects under `orders.>`, but they must not see each other's messages. A developer proposes one shared account with naming conventions such as `orders.team-a.*` and `orders.team-b.*`. Why might accounts be a better boundary, and what still needs review?

<details>
<summary>Answer</summary>

Accounts provide independent subject namespaces, so the same subject in two accounts is isolated unless exports and imports intentionally connect them. Naming conventions inside one account depend on every permission being correct forever. Accounts are a stronger tenancy boundary, but exports, imports, user permissions, NACK credentials, stream filters, and operational access still need review. Account isolation is not a replacement for subject policy; it makes policy tractable.
</details>

### 6. Leaf node during a WAN outage

A factory site uses a local leaf node connected to the central NATS cluster. The WAN fails for six hours. Local services must continue request/reply, but only selected machine events should be persisted centrally after reconnection. What architecture questions must be answered before this is safe?

<details>
<summary>Answer</summary>

Decide whether JetStream storage exists locally, centrally, or both; which subjects are allowed over the leaf connection; whether local producers can continue while disconnected; how delayed messages are identified; and how duplicates are handled after reconnection. Leaf nodes provide locality and controlled routing, not automatic conflict resolution. The application and platform must define ownership, idempotency, and recovery behavior for durable subjects.
</details>

## Hands-On Lab: Three-Node kind NATS JetStream

Hypothetical scenario: your platform team has approved NATS JetStream for a lightweight order-event fabric. Your task is to create a three-node kind cluster, install NATS with JetStream and NACK, declare a stream and durable consumer, publish and consume messages through `nats-box`, then kill one pod and prove the replicated stream remains available while the cluster repairs itself.

### Part 1: Create a three-node kind cluster

Create a local cluster with one control-plane node and three worker nodes. The extra workers make the anti-affinity and topology-spread settings meaningful, even on a laptop. If your environment pins a Kubernetes 1.35 kind node image, add the published image tag to this file; otherwise use your local kind default for the lab mechanics.

```yaml
# kind-nats.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
  - role: worker
  - role: worker
```

```bash
kind create cluster --name nats-js-lab --config kind-nats.yaml
kubectl cluster-info --context kind-nats-js-lab
```

- [ ] The kind cluster exists and `kubectl get nodes` shows one control-plane node plus three workers.
- [ ] You can explain why three worker nodes make the JetStream replica exercise more realistic.

### Part 2: Install NATS and NACK

Apply the `nats-lab-values.yaml` file from the bootstrap section, then install the server cluster and NACK. The current official path uses Helm values for the NATS server StatefulSet rather than a live `NatsCluster` CRD; the YAML you are creating is still the cluster declaration that code review should own.

```bash
kubectl config use-context kind-nats-js-lab

helm repo add nats https://nats-io.github.io/k8s/helm/charts/
helm repo update

helm upgrade --install nats nats/nats \
  --namespace nats \
  --create-namespace \
  --values nats-lab-values.yaml \
  --wait

helm upgrade --install nack nats/nack \
  --namespace nats \
  --set namespaced=true \
  --set jetstream.nats.url=nats://nats.nats.svc.cluster.local:4222 \
  --set 'jetstream.additionalArgs={--control-loop}' \
  --wait
```

```bash
kubectl -n nats rollout status statefulset/nats --timeout=300s
kubectl -n nats rollout status deployment/nack --timeout=180s
kubectl -n nats get pods -o wide
```

- [ ] The `nats` StatefulSet has three ready pods.
- [ ] The `nack` Deployment is ready in the `nats` namespace.
- [ ] The NATS pods are spread across different kind worker nodes.

### Part 3: Create a Stream and Consumer with NACK

Apply the `orders-jetstream.yaml` file from the stream section. Watch the Kubernetes resource status first, then verify the actual server state through the CLI. This two-step check matters because it proves both reconciliation and broker state, not only that the API server accepted a YAML document.

```bash
kubectl apply -f orders-jetstream.yaml
kubectl -n nats get streams,consumers
kubectl -n nats describe stream orders-stream
kubectl -n nats describe consumer order-worker
```

```bash
kubectl -n nats exec deployment/nats-box -- nats stream info ORDERS
kubectl -n nats exec deployment/nats-box -- nats consumer info ORDERS order-worker
```

- [ ] The `orders-stream` resource reports ready or synced status.
- [ ] The `order-worker` consumer exists and uses explicit acknowledgment.
- [ ] `nats stream info ORDERS` shows file storage and three replicas.

### Part 4: Publish and consume messages

Publish a few order events to the captured subject and pull them through the durable consumer. The expected behavior is that each message is stored, delivered, acknowledged, and then no longer pending for that consumer. Publish to a subject outside the stream as a negative test and confirm it does not appear in `ORDERS`.

```bash
kubectl -n nats exec deployment/nats-box -- \
  nats pub orders.created '{"order_id":"ord-1001","total":129.90}'

kubectl -n nats exec deployment/nats-box -- \
  nats pub orders.created '{"order_id":"ord-1002","total":58.25}'

kubectl -n nats exec deployment/nats-box -- \
  nats consumer next ORDERS order-worker --count=2 --ack

kubectl -n nats exec deployment/nats-box -- \
  nats pub inventory.adjusted '{"sku":"sku-7","delta":-1}'

kubectl -n nats exec deployment/nats-box -- nats stream info ORDERS
```

- [ ] The two `orders.created` messages are consumed and acknowledged.
- [ ] The `inventory.adjusted` message does not increase the `ORDERS` stream message count.
- [ ] You can explain how the stream subjects, consumer filter, and ack policy produced that behavior.

### Part 5: Kill a pod and observe quorum behavior

Delete one NATS pod and immediately inspect the stream. A correctly spread three-replica stream should continue with a majority while Kubernetes recreates the pod. Do not delete two pods in the first pass. The point is to observe a degraded-but-available state and then a return to full replica health.

```bash
kubectl -n nats delete pod nats-0
kubectl -n nats get pods -w
```

In another terminal, publish and consume while the pod is restarting:

```bash
kubectl -n nats exec deployment/nats-box -- \
  nats pub orders.created '{"order_id":"ord-1003","total":77.00}'

kubectl -n nats exec deployment/nats-box -- \
  nats consumer next ORDERS order-worker --count=1 --ack

kubectl -n nats exec deployment/nats-box -- nats stream info ORDERS
```

After the pod returns, verify all replicas are healthy:

```bash
kubectl -n nats wait pod/nats-0 --for=condition=Ready --timeout=300s
kubectl -n nats exec deployment/nats-box -- nats stream info ORDERS
```

- [ ] Publishing and consuming still work with one NATS pod temporarily unavailable.
- [ ] `nats stream info ORDERS` shows one degraded replica during the restart or full health after recovery.
- [ ] You can explain why one failure is survivable for a three-replica stream and why two failures are different.

### Part 6: Inspect metrics and clean up

Use port-forwarding to inspect the exporter and monitor endpoints, then clean up the lab resources. If your cluster has Prometheus Operator installed, you can enable `promExporter.podMonitor.enabled`; otherwise direct endpoint inspection is enough for this lab.

```bash
kubectl -n nats port-forward statefulset/nats 8222:8222
```

```bash
kubectl -n nats exec deployment/nats-box -- nats server report
kubectl -n nats exec deployment/nats-box -- nats stream report
kubectl -n nats exec deployment/nats-box -- nats consumer report ORDERS
```

```bash
kubectl delete -f orders-jetstream.yaml
helm -n nats uninstall nack
helm -n nats uninstall nats
kubectl delete namespace nats
kind delete cluster --name nats-js-lab
```

- [ ] You can show one server report and one stream report from the CLI.
- [ ] You can identify which metrics or reports would alert on storage pressure and consumer backlog.
- [ ] You removed the lab cluster and can repeat the install from Git-tracked YAML.

## Scenario Exercises

Exercise scenario: a platform team wants to offer NATS to several product teams in one Kubernetes cluster. Design the account model, namespace model, NACK controller placement, and secret ownership. Your answer should state whether each team gets a separate NATS account, whether NACK is namespaced or cluster-wide, how stream CRs are reviewed, and how subject imports or exports are approved. Include one example subject permission for a producer and one for a consumer.

Exercise scenario: a consumer group is falling behind during a flash sale, but producers must stay online. Decide whether you would scale workers, increase `ackWait`, change `maxDeliver`, split subjects into multiple streams, add NATS server capacity, or move the workload to Kafka. Your answer should use evidence from `nats consumer info`, stream storage usage, pod CPU, downstream latency, and redelivery counts rather than assuming the broker is the bottleneck.

Exercise scenario: an edge site uses a local NATS server connected by leaf node to a central cluster. The site loses WAN access for a full business day and reconnects with delayed events. Write a recovery plan that covers which subjects were allowed to persist locally, how duplicate events are detected, how central consumers know an event is delayed, and whether replay should go through the same stream or a quarantine stream. Include at least one idempotency key and one alert.

Exercise scenario: a compliance review finds that the `ORDERS` stream captures `orders.>` and includes subjects carrying customer support notes that should not be persisted in the analytics account. Propose a safer subject hierarchy and migration plan. Your answer should cover a new stream filter, account or user permission changes, consumer cutover, backup before migration, and a test that proves the sensitive subject no longer appears in `nats stream info` or a sample replay.

## Sources

- [NATS and Kubernetes](https://docs.nats.io/running-a-nats-service/nats-kubernetes) - official guidance for using the NATS Helm chart on Kubernetes.
- [nats-io/nack](https://github.com/nats-io/nack) - NATS Controllers for Kubernetes, including Stream and Consumer CRD examples and controller modes.
- [nats-io/k8s](https://github.com/nats-io/k8s) - official NATS Kubernetes Helm chart repository.
- [NATS JetStream concepts](https://docs.nats.io/nats-concepts/jetstream) - persistence, stream storage, and JetStream behavior.
- [JetStream Streams](https://docs.nats.io/nats-concepts/jetstream/streams) - retention policies, storage types, stream limits, and subject capture.
- [JetStream Consumers](https://docs.nats.io/nats-concepts/jetstream/consumers) - durable and ephemeral consumers, push and pull delivery, and acknowledgment behavior.
- [NATS Subject-Based Messaging](https://docs.nats.io/nats-concepts/subjects) - subject hierarchy, wildcard behavior, and naming guidance.
- [Securing NATS](https://docs.nats.io/running-a-nats-service/configuration/securing_nats) - TLS, authentication, and authorization overview.
- [NATS Authentication](https://docs.nats.io/running-a-nats-service/configuration/securing_nats/auth_intro) - account isolation and authentication methods.
- [Decentralized JWT Authentication/Authorization](https://docs.nats.io/running-a-nats-service/configuration/securing_nats/auth_intro/jwt) - operator, account, and user trust chain model.
- [NKeys](https://docs.nats.io/running-a-nats-service/configuration/securing_nats/auth_intro/nkey_auth) - challenge-response authentication with public/private NKey pairs.
- [NATS Monitoring](https://docs.nats.io/running-a-nats-service/nats_admin/monitoring) - monitoring endpoints, Prometheus exporter, and Grafana guidance.
- [Monitoring JetStream](https://docs.nats.io/running-a-nats-service/nats_admin/monitoring/monitoring_jetstream) - JetStream advisories, leader election, and quorum events.
- [Leaf Nodes](https://docs.nats.io/running-a-nats-service/configuration/leafnodes) - edge and local-server connectivity model.
- [Super-cluster with Gateways](https://docs.nats.io/running-a-nats-service/configuration/gateways) - gateway behavior for connecting NATS clusters.
- [JetStream Key/Value Store](https://docs.nats.io/nats-concepts/jetstream/key-value-store) - KV bucket semantics and stream-backed implementation.
- [NATS CLI](https://docs.nats.io/using-nats/nats-tools/nats_cli) - CLI commands for NATS, JetStream, monitoring, backup, and restore operations.
- [JetStream Disaster Recovery](https://docs.nats.io/running-a-nats-service/nats_admin/jetstream_admin/disaster_recovery) - stream and account backup/restore guidance.
- [Prometheus NATS Exporter](https://github.com/nats-io/prometheus-nats-exporter) - exporter behavior and supported NATS monitoring endpoints.
- [CNCF NATS project page](https://www.cncf.io/projects/nats/) - project status, positioning, and linked case studies.
- [Deprecated nats-operator](https://github.com/nats-io/nats-operator) - historical `NatsCluster` CRD reference used to explain why current labs use Helm instead.

## Next Module

You've completed the Data Engineering module sequence through Kafka, Flink, Spark, Airflow, lakehouse design, event streaming fundamentals, CloudEvents, and NATS JetStream. Continue to the [MLOps discipline](../../mlops/) when you are ready to connect event-driven data movement to model training, feature pipelines, and production inference workflows, or revisit [Module 1.8 - CloudEvents and Event-Driven Architecture](../module-1.8-cloudevents-event-driven-arch/) to pair standardized event envelopes with the NATS subject and JetStream designs from this module.
