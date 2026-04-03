---
title: "Module 9.2: Managed Message Brokers & Event-Driven Kubernetes"
slug: cloud/managed-services/module-9.2-message-brokers
sidebar:
  order: 3
---
**Complexity**: [COMPLEX] | **Time to Complete**: 2.5h | **Prerequisites**: Module 9.1 (Relational Database Integration), Kubernetes Deployments and Services

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Configure Kubernetes workloads to consume from managed message brokers (Amazon MQ, Cloud Pub/Sub, Azure Service Bus)**
- **Implement event-driven autoscaling using KEDA with message queue depth as the scaling trigger**
- **Deploy dead-letter queue patterns and retry logic for reliable message processing in Kubernetes applications**
- **Compare managed message brokers across clouds and evaluate when to use self-hosted (RabbitMQ, NATS) alternatives on Kubernetes**

---

## Why This Module Matters

In March 2023, a logistics company processing 2 million package-tracking events per day ran RabbitMQ as a StatefulSet inside their GKE cluster. The system worked flawlessly for eight months. Then Black Friday arrived. Event volume spiked to 11 million per day. RabbitMQ's memory alarm triggered, blocking all publishers. The three-node cluster entered a split-brain state during a simultaneous node reschedule. Queue mirroring fell behind, and 340,000 tracking events were lost. Customers could not track packages for six hours. The company's SLA penalties totaled $1.2 million.

The postmortem conclusion was blunt: "We were operating a distributed messaging system that required deep RabbitMQ expertise we did not have. We should have used a managed service." They migrated to Amazon SQS within two weeks. SQS does not have memory alarms, split-brain scenarios, or queue mirroring to configure. It scales to any volume without intervention.

This module teaches you how to integrate managed message brokers -- SQS/SNS, Google Pub/Sub, and Azure Service Bus -- with Kubernetes workloads. You will learn how to use KEDA to autoscale consumers based on queue depth, handle dead-letter queues, design for exactly-once versus at-least-once delivery, and manage consumer groups across multiple Kubernetes Deployments.

---

## Messaging Fundamentals for Kubernetes Engineers

Before diving into cloud services, let's establish the core messaging patterns that every integration uses.

### Point-to-Point vs Publish-Subscribe

```
Point-to-Point (Queue):
  Producer --> [  Queue  ] --> Consumer
  Each message delivered to exactly one consumer

Pub/Sub (Topic + Subscriptions):
  Producer --> [ Topic ] --+--> Subscription A --> Consumer Group 1
                           |
                           +--> Subscription B --> Consumer Group 2
  Each message delivered to all subscriptions
```

### Delivery Guarantees

| Guarantee | Meaning | Risk | Used By |
|-----------|---------|------|---------|
| **At-most-once** | Message delivered 0 or 1 times | Data loss on failure | UDP-style telemetry |
| **At-least-once** | Message delivered 1+ times | Duplicates possible | SQS, Pub/Sub, Service Bus |
| **Exactly-once** | Message delivered exactly 1 time | Higher latency, complexity | Kafka transactions, Pub/Sub with dedup |

Most managed brokers provide **at-least-once** delivery by default. This means your consumer code must be **idempotent** -- processing the same message twice should produce the same result as processing it once.

```python
# BAD: Not idempotent -- double processing creates duplicate charges
def process_payment(message):
    charge_customer(message.customer_id, message.amount)

# GOOD: Idempotent -- uses a unique key to prevent duplicates
def process_payment(message):
    if not payment_exists(message.idempotency_key):
        charge_customer(message.customer_id, message.amount)
        record_payment(message.idempotency_key)
```

---

## Cloud Broker Comparison

| Feature | AWS SQS/SNS | Google Pub/Sub | Azure Service Bus |
|---------|-------------|----------------|-------------------|
| Queue model | SQS = queue, SNS = topic | Topic + Subscription | Queue or Topic + Subscription |
| Max message size | 256 KB (SQS), 256 KB (SNS) | 10 MB | 256 KB (Standard), 100 MB (Premium) |
| Retention | 1 min - 14 days | 7 days (configurable to 31) | Up to 14 days |
| Ordering | FIFO queues (strict per group) | Ordering keys | Sessions (strict per session) |
| Throughput | Nearly unlimited (Standard) | Unlimited | Depends on tier (Premium: 1000+ msg/s per unit) |
| Dead-letter | Built-in (maxReceiveCount) | Built-in (maxDeliveryAttempts) | Built-in (maxDeliveryCount) |
| Price per million | ~$0.40 (Standard) | ~$0.40 | ~$0.05 (Basic), varies by tier |

### AWS SQS/SNS: The Workhorse

SQS is the simplest managed queue -- no clusters, no partitions, no brokers. You create a queue and start sending messages.

```bash
# Create a standard queue
aws sqs create-queue --queue-name order-processing \
  --attributes '{
    "VisibilityTimeout": "300",
    "MessageRetentionPeriod": "1209600",
    "ReceiveMessageWaitTimeSeconds": "20"
  }'

# Create a dead-letter queue
aws sqs create-queue --queue-name order-processing-dlq

# Set up the redrive policy
DLQ_ARN=$(aws sqs get-queue-attributes \
  --queue-url $(aws sqs get-queue-url --queue-name order-processing-dlq --query QueueUrl --output text) \
  --attribute-names QueueArn --query 'Attributes.QueueArn' --output text)

aws sqs set-queue-attributes \
  --queue-url $(aws sqs get-queue-url --queue-name order-processing --query QueueUrl --output text) \
  --attributes "{\"RedrivePolicy\": \"{\\\"deadLetterTargetArn\\\":\\\"$DLQ_ARN\\\",\\\"maxReceiveCount\\\":\\\"3\\\"}\"}"

# Fan-out with SNS -> SQS
aws sns create-topic --name order-events
aws sns subscribe --topic-arn arn:aws:sns:us-east-1:123456789:order-events \
  --protocol sqs \
  --notification-endpoint arn:aws:sqs:us-east-1:123456789:order-processing
```

### Google Pub/Sub: The Scalable Option

```bash
# Create topic
gcloud pubsub topics create order-events

# Create subscription with dead-lettering
gcloud pubsub topics create order-events-dlq

gcloud pubsub subscriptions create order-processing \
  --topic=order-events \
  --ack-deadline=300 \
  --dead-letter-topic=order-events-dlq \
  --max-delivery-attempts=5 \
  --enable-exactly-once-delivery
```

### Azure Service Bus: The Enterprise Option

```bash
# Create namespace (Premium for VNET integration)
az servicebus namespace create \
  --resource-group myRG --name orders-bus \
  --sku Premium --capacity 1

# Create queue with dead-lettering
az servicebus queue create \
  --resource-group myRG --namespace-name orders-bus \
  --name order-processing \
  --max-delivery-count 3 \
  --default-message-time-to-live P14D \
  --dead-lettering-on-message-expiration true
```

---

## Kubernetes Consumer Deployments

The typical pattern is a Deployment running consumer pods that poll the queue.

### SQS Consumer Pod

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-processor
  namespace: processing
spec:
  replicas: 3
  selector:
    matchLabels:
      app: order-processor
  template:
    metadata:
      labels:
        app: order-processor
    spec:
      serviceAccountName: sqs-consumer
      containers:
        - name: consumer
          image: mycompany/order-processor:1.5.0
          env:
            - name: SQS_QUEUE_URL
              value: "https://sqs.us-east-1.amazonaws.com/123456789/order-processing"
            - name: SQS_WAIT_TIME_SECONDS
              value: "20"
            - name: SQS_MAX_MESSAGES
              value: "10"
            - name: SQS_VISIBILITY_TIMEOUT
              value: "300"
          resources:
            requests:
              cpu: 200m
              memory: 256Mi
            limits:
              cpu: 500m
              memory: 512Mi
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8081
            initialDelaySeconds: 10
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /readyz
              port: 8081
            initialDelaySeconds: 5
            periodSeconds: 10
```

### IAM for Queue Access (IRSA / Workload Identity)

Pods should never use static credentials to access message brokers. Use cloud-native workload identity.

```yaml
# AWS: IRSA ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: sqs-consumer
  namespace: processing
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789:role/SQSConsumerRole
---
# The IAM policy attached to SQSConsumerRole:
# {
#   "Effect": "Allow",
#   "Action": [
#     "sqs:ReceiveMessage",
#     "sqs:DeleteMessage",
#     "sqs:GetQueueAttributes",
#     "sqs:ChangeMessageVisibility"
#   ],
#   "Resource": "arn:aws:sqs:us-east-1:123456789:order-processing"
# }
```

```yaml
# GCP: Workload Identity
apiVersion: v1
kind: ServiceAccount
metadata:
  name: pubsub-consumer
  namespace: processing
  annotations:
    iam.gke.io/gcp-service-account: pubsub-consumer@my-project.iam.gserviceaccount.com
```

---

## KEDA: Autoscaling on Queue Depth

KEDA (Kubernetes Event-Driven Autoscaling) is the missing piece that makes message-driven architectures elastic. Instead of scaling on CPU (which is meaningless for I/O-bound queue consumers), KEDA scales based on the number of messages waiting in the queue.

### How KEDA Works

```
                    +------------------+
                    |   Cloud Queue    |
                    | (depth: 1500)    |
                    +--------+---------+
                             |
                             | poll metrics
                             v
                    +------------------+
                    |  KEDA Operator   |
                    | (ScaledObject)   |
                    +--------+---------+
                             |
                             | scale to: ceil(1500/100) = 15 pods
                             v
                    +------------------+
                    |    HPA           |
                    | (managed by KEDA)|
                    +--------+---------+
                             |
                             v
                    +------------------+
                    |   Deployment     |
                    | (15 replicas)    |
                    +------------------+
```

### Installing KEDA

```bash
helm repo add kedacore https://kedacore.github.io/charts
helm repo update
helm install keda kedacore/keda \
  --namespace keda --create-namespace \
  --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=arn:aws:iam::123456789:role/KEDARole
```

### KEDA ScaledObject for SQS

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: order-processor-scaler
  namespace: processing
spec:
  scaleTargetRef:
    name: order-processor
  minReplicaCount: 1
  maxReplicaCount: 50
  pollingInterval: 15
  cooldownPeriod: 120
  triggers:
    - type: aws-sqs-queue
      authenticationRef:
        name: keda-aws-credentials
      metadata:
        queueURL: https://sqs.us-east-1.amazonaws.com/123456789/order-processing
        queueLength: "100"
        awsRegion: us-east-1
        identityOwner: operator
---
apiVersion: keda.sh/v1alpha1
kind: TriggerAuthentication
metadata:
  name: keda-aws-credentials
  namespace: processing
spec:
  podIdentity:
    provider: aws-eks
```

The `queueLength: "100"` setting means KEDA will scale to ensure each pod handles at most 100 messages. If there are 1,500 messages in the queue, KEDA scales to 15 pods.

### KEDA ScaledObject for Pub/Sub

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: order-processor-scaler
  namespace: processing
spec:
  scaleTargetRef:
    name: order-processor
  minReplicaCount: 1
  maxReplicaCount: 30
  triggers:
    - type: gcp-pubsub
      metadata:
        subscriptionName: "projects/my-project/subscriptions/order-processing"
        mode: "SubscriptionSize"
        value: "50"
```

### KEDA ScaledObject for Azure Service Bus

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: order-processor-scaler
  namespace: processing
spec:
  scaleTargetRef:
    name: order-processor
  minReplicaCount: 0
  maxReplicaCount: 25
  triggers:
    - type: azure-servicebus
      metadata:
        queueName: order-processing
        namespace: orders-bus
        messageCount: "50"
      authenticationRef:
        name: azure-servicebus-auth
```

### Scale-to-Zero Considerations

KEDA can scale to zero (`minReplicaCount: 0`), which saves costs when queues are empty. But there is a latency cost: when the first message arrives, KEDA must detect it (on the next polling interval), create a pod, wait for the image pull, and wait for container startup. This can take 30-90 seconds.

**Use scale-to-zero when:**
- Processing is not latency-sensitive (batch jobs, analytics)
- Cost savings matter more than response time
- Queues are empty for long periods

**Keep minReplicaCount >= 1 when:**
- You need sub-second processing of new messages
- The application has expensive startup time (JVM, ML model loading)
- The queue always has some baseline traffic

---

## Dead-Letter Queues (DLQs)

A DLQ captures messages that fail processing repeatedly. Without a DLQ, poison messages -- messages that always fail -- block the queue forever as they are received, fail, become visible again, and repeat.

### DLQ Architecture

```
Producer --> [ Main Queue ] --> Consumer
                  |                |
                  |    fails 3x    |
                  |                v
                  +-------> [ DLQ ] --> Alert
                                        |
                                        v
                                   Manual Review
                                   or Reprocessing
```

### DLQ Consumer for Alerting

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dlq-monitor
  namespace: processing
spec:
  replicas: 1
  selector:
    matchLabels:
      app: dlq-monitor
  template:
    metadata:
      labels:
        app: dlq-monitor
    spec:
      containers:
        - name: monitor
          image: mycompany/dlq-monitor:1.0.0
          env:
            - name: DLQ_QUEUE_URL
              value: "https://sqs.us-east-1.amazonaws.com/123456789/order-processing-dlq"
            - name: SLACK_WEBHOOK_URL
              valueFrom:
                secretKeyRef:
                  name: slack-config
                  key: webhook-url
            - name: ALERT_THRESHOLD
              value: "5"
```

### Reprocessing DLQ Messages

```bash
# AWS: Move messages from DLQ back to main queue
aws sqs start-message-move-task \
  --source-arn arn:aws:sqs:us-east-1:123456789:order-processing-dlq \
  --destination-arn arn:aws:sqs:us-east-1:123456789:order-processing \
  --max-number-of-messages-per-second 10
```

---

## Consumer Groups and Competing Consumers

When multiple pods consume from the same queue, they are "competing consumers." The broker ensures each message goes to only one consumer. This is automatic with SQS and Service Bus queues. For Pub/Sub, each subscription is an independent consumer group.

### Multi-Consumer Architecture

```
                     order-events (SNS Topic / Pub/Sub Topic)
                           |
              +------------+-------------+
              |                          |
     order-processing           order-analytics
     (SQS Queue / Sub)         (SQS Queue / Sub)
         |                          |
    +----+----+                +----+----+
    |    |    |                |    |    |
   Pod  Pod  Pod              Pod  Pod  Pod
   (processors)               (analytics)
```

Each service gets its own subscription/queue. Messages fan out to all subscriptions, and within each subscription, competing consumers share the load.

```yaml
# Producer publishes to SNS topic from within a pod
apiVersion: batch/v1
kind: CronJob
metadata:
  name: order-publisher
  namespace: processing
spec:
  schedule: "*/5 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          serviceAccountName: sns-publisher
          containers:
            - name: publisher
              image: mycompany/order-publisher:1.0.0
              env:
                - name: SNS_TOPIC_ARN
                  value: "arn:aws:sns:us-east-1:123456789:order-events"
```

### Exactly-Once vs At-Least-Once in Practice

| Scenario | Recommended Guarantee | Why |
|----------|----------------------|-----|
| Payment processing | At-least-once + idempotency key | Exactly-once adds latency; idempotency is safer |
| Email notifications | At-least-once + deduplication window | Sending two emails is better than sending zero |
| Inventory updates | At-least-once + last-write-wins | Idempotent by nature (SET quantity = X) |
| Analytics events | At-least-once (duplicates acceptable) | Analytics pipelines handle dedup downstream |
| Financial ledger entries | Exactly-once (Kafka transactions) | Double-counting money is unacceptable |

For most Kubernetes workloads, **at-least-once with application-level idempotency** is the pragmatic choice. Exactly-once is expensive and complex -- only reach for it when the cost of a duplicate exceeds the cost of the complexity.

---

## Visibility Timeout and Message Lifecycle

One of the most misunderstood concepts in queue-based systems is the visibility timeout (SQS) or ack deadline (Pub/Sub).

```
Timeline for a single message:

  t=0     Message arrives in queue
  t=1     Consumer receives message (visibility timeout starts)
  t=1-59  Consumer processes message
  t=60    If not deleted/acked, message becomes visible again
          (another consumer will pick it up -- duplicate!)
```

### Setting the Right Timeout

The visibility timeout must be longer than your maximum processing time. But not too long -- if a consumer crashes, the message is stuck invisible until the timeout expires.

```python
# Good pattern: extend visibility during long processing
import boto3

sqs = boto3.client('sqs')

while True:
    response = sqs.receive_message(
        QueueUrl=QUEUE_URL,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=20,
        VisibilityTimeout=60
    )

    for message in response.get('Messages', []):
        try:
            # Start processing
            result = process_order(message['Body'])

            # If still processing after 45s, extend the timeout
            if result.needs_more_time:
                sqs.change_message_visibility(
                    QueueUrl=QUEUE_URL,
                    ReceiptHandle=message['ReceiptHandle'],
                    VisibilityTimeout=120
                )
                finalize_order(result)

            # Delete on success
            sqs.delete_message(
                QueueUrl=QUEUE_URL,
                ReceiptHandle=message['ReceiptHandle']
            )
        except Exception as e:
            # Don't delete -- message will become visible again
            log.error(f"Failed to process: {e}")
```

---

## Did You Know?

1. **Amazon SQS was one of the first AWS services ever launched** -- it went live in July 2004, two years before EC2 and S3. It has been processing messages for over 20 years and is one of the most battle-tested distributed systems in existence.

2. **Google Pub/Sub can handle over 500 million messages per second** across its global infrastructure. When YouTube processes upload events, comment notifications, and recommendation updates, Pub/Sub is the backbone carrying those events between services.

3. **KEDA has over 60 built-in scalers** as of 2025 -- not just cloud queues but also Kafka, RabbitMQ, PostgreSQL query results, Prometheus metrics, Cron schedules, and even GitHub runner queues. It has become the de facto standard for event-driven autoscaling in Kubernetes.

4. **The "visibility timeout" concept in SQS was inspired by the "lease" pattern** in distributed systems, where a resource is temporarily granted to a consumer with an expiration. This same pattern appears in Kubernetes itself -- node leases, leader election leases, and etcd TTLs all use the same fundamental idea.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|---------------|---------------|
| Setting visibility timeout shorter than processing time | Estimated processing time was optimistic | Measure P99 processing time and add 50% buffer; implement dynamic extension |
| Not implementing idempotency in consumers | "At-least-once means delivered once, right?" | Use idempotency keys (message dedup ID or database unique constraints) |
| Scaling KEDA on CPU instead of queue depth | HPA defaults are CPU-based | Use KEDA ScaledObject with queue-specific triggers |
| Missing dead-letter queue configuration | DLQ feels like an edge case during development | Always create a DLQ and a monitoring/alerting consumer for it |
| Using SQS Standard when FIFO is needed | Standard is the default and cheaper | Use FIFO queues with MessageGroupId for ordering-sensitive workloads |
| Processing messages in the readiness probe thread | Trying to block traffic during processing | Keep health probes on a separate HTTP server from message processing |
| Not setting `WaitTimeSeconds` (long polling) | Default is short polling (returns immediately) | Always set `WaitTimeSeconds: 20` for SQS to reduce empty responses and cost |
| Deleting messages before processing completes | "Optimistic" deletion to avoid duplicates | Only delete/ack after successful processing and any downstream writes |

---

## Quiz

<details>
<summary>1. Why is "at-least-once with idempotency" preferred over "exactly-once" for most Kubernetes workloads?</summary>

Exactly-once delivery requires coordination between the broker and the consumer, typically through distributed transactions or deduplication windows. This adds significant latency and complexity. At-least-once delivery is simpler and faster -- the broker guarantees the message will arrive, and the application ensures that processing it twice has no harmful side effects. Since Kubernetes pods can crash, restart, or lose network connectivity at any time, idempotent processing is needed regardless of the delivery guarantee. Building idempotency into your application gives you both reliability and simplicity.
</details>

<details>
<summary>2. How does KEDA determine the number of pod replicas to create for a queue-based scaler?</summary>

KEDA divides the current queue depth by the target value specified in the ScaledObject (e.g., `queueLength: "100"`). If there are 1,500 messages in the queue and the target is 100, KEDA calculates ceil(1500/100) = 15 replicas. This is bounded by `minReplicaCount` and `maxReplicaCount`. KEDA polls the queue metrics at the interval specified by `pollingInterval` (default 30 seconds). When the queue empties, KEDA waits for `cooldownPeriod` before scaling down, preventing rapid scale-up/scale-down oscillation.
</details>

<details>
<summary>3. What happens when a message's visibility timeout expires before the consumer finishes processing it?</summary>

The message becomes visible in the queue again, and another consumer (or the same one) will receive it. This results in duplicate processing -- both the original consumer (still working on it) and the new consumer process the same message. This is why visibility timeouts must exceed your maximum processing time, and why idempotent consumer design is essential. You can mitigate this by dynamically extending the visibility timeout during long processing with `ChangeMessageVisibility` (SQS) or `ModifyAckDeadline` (Pub/Sub).
</details>

<details>
<summary>4. Explain the difference between SNS + SQS fan-out and having multiple consumers on a single SQS queue.</summary>

Multiple consumers on a single SQS queue are competing consumers -- each message is delivered to exactly one consumer. This is load distribution. SNS + SQS fan-out creates independent copies of each message in separate queues. This is event fan-out -- every downstream service receives every message. For example, an "order-created" event might need to go to both a payment processor (SQS queue 1) and an analytics pipeline (SQS queue 2). Each queue has its own set of competing consumers, giving you both fan-out (every service gets the event) and load distribution (within each service).
</details>

<details>
<summary>5. Why should you keep `minReplicaCount: 1` for latency-sensitive queue consumers instead of using scale-to-zero?</summary>

When KEDA scales to zero, there are no pods running. When a new message arrives, KEDA must detect it on the next polling cycle, create a pod through the Deployment, wait for scheduling, image pull, and container startup. This cold-start delay can be 30-90 seconds or more, depending on image size and cluster conditions. For latency-sensitive workloads, this delay is unacceptable. Keeping at least one replica ensures immediate message processing. Scale-to-zero is appropriate for batch processing or workloads where queue emptiness is the normal state and latency is not critical.
</details>

<details>
<summary>6. What is a dead-letter queue and why is it critical for production message processing?</summary>

A dead-letter queue (DLQ) captures messages that have failed processing a configured number of times (e.g., 3 attempts). Without a DLQ, a "poison message" that always fails processing will cycle indefinitely -- received, failed, becomes visible, received again -- consuming CPU and blocking the queue. The DLQ isolates these failures so healthy messages continue flowing. In production, you should always monitor your DLQ with alerts, because messages in the DLQ represent either bugs in your consumer code or unexpected data formats. DLQ messages can be reprocessed after the bug is fixed.
</details>

<details>
<summary>7. How do consumer groups work differently in SQS versus Google Pub/Sub?</summary>

In SQS, consumer groups are implicit -- multiple consumers polling the same queue naturally compete for messages. There is no formal "group" concept. In Google Pub/Sub, consumer groups are explicit: each subscription is an independent consumer group. To create a new consumer group, you create a new subscription on the topic. All subscribers within one subscription compete for messages (load distribution), but each subscription independently receives all messages (fan-out). This makes Pub/Sub more flexible for multi-service architectures because you can add new consumer groups without modifying the publisher or existing consumers.
</details>

---

## Hands-On Exercise: Event-Driven Processing with KEDA

This exercise uses a local kind cluster with a simulated queue (Redis acting as a message broker) and KEDA for autoscaling.

### Setup

```bash
# Create kind cluster
kind create cluster --name event-lab

# Install KEDA
helm repo add kedacore https://kedacore.github.io/charts
helm repo update
helm install keda kedacore/keda --namespace keda --create-namespace
k wait --for=condition=ready pod -l app.kubernetes.io/name=keda-operator \
  --namespace keda --timeout=120s

# Install Redis (simulating a message queue)
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install redis bitnami/redis --namespace messaging --create-namespace \
  --set architecture=standalone \
  --set auth.password=lab-redis-pass \
  --set master.persistence.enabled=false
k wait --for=condition=ready pod -l app.kubernetes.io/name=redis \
  --namespace messaging --timeout=120s
```

### Task 1: Deploy a Queue Consumer

Create a Deployment that processes messages from a Redis list (simulating an SQS queue).

<details>
<summary>Solution</summary>

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: queue-consumer
  namespace: messaging
spec:
  replicas: 1
  selector:
    matchLabels:
      app: queue-consumer
  template:
    metadata:
      labels:
        app: queue-consumer
    spec:
      containers:
        - name: consumer
          image: redis:7
          command:
            - /bin/sh
            - -c
            - |
              while true; do
                MSG=$(redis-cli -h redis-master -a lab-redis-pass \
                  BRPOP order-queue 10 2>/dev/null)
                if [ -n "$MSG" ]; then
                  echo "Processed: $MSG"
                fi
              done
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
```

```bash
k apply -f /tmp/consumer.yaml
```
</details>

### Task 2: Configure KEDA ScaledObject for Redis

Create a KEDA ScaledObject that scales the consumer based on Redis list length.

<details>
<summary>Solution</summary>

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: redis-auth
  namespace: messaging
stringData:
  redis-url: redis://:lab-redis-pass@redis-master.messaging.svc:6379
---
apiVersion: keda.sh/v1alpha1
kind: TriggerAuthentication
metadata:
  name: redis-trigger-auth
  namespace: messaging
spec:
  secretTargetRef:
    - parameter: address
      name: redis-auth
      key: redis-url
---
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: queue-consumer-scaler
  namespace: messaging
spec:
  scaleTargetRef:
    name: queue-consumer
  minReplicaCount: 1
  maxReplicaCount: 10
  pollingInterval: 5
  cooldownPeriod: 30
  triggers:
    - type: redis
      metadata:
        listName: order-queue
        listLength: "10"
      authenticationRef:
        name: redis-trigger-auth
```

```bash
k apply -f /tmp/keda-scaledobject.yaml
```
</details>

### Task 3: Generate Load and Watch Scaling

Push 200 messages into the queue and watch KEDA scale the consumer.

<details>
<summary>Solution</summary>

```bash
# Push 200 messages to the queue
k run redis-producer --rm -it --image=redis:7 --namespace=messaging --restart=Never -- \
  /bin/sh -c '
  for i in $(seq 1 200); do
    redis-cli -h redis-master -a lab-redis-pass LPUSH order-queue "{\"orderId\": \"order-$i\", \"amount\": $((RANDOM % 1000))}" > /dev/null 2>&1
  done
  echo "Pushed 200 messages"
  redis-cli -h redis-master -a lab-redis-pass LLEN order-queue
  '

# Watch KEDA scale the deployment
k get scaledobject -n messaging -w &
k get pods -n messaging -l app=queue-consumer -w
```
</details>

### Task 4: Implement a Dead-Letter Queue Pattern

Create a second Redis list as a DLQ and modify the consumer to move failed messages there.

<details>
<summary>Solution</summary>

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: queue-consumer-dlq
  namespace: messaging
spec:
  replicas: 1
  selector:
    matchLabels:
      app: queue-consumer-dlq
  template:
    metadata:
      labels:
        app: queue-consumer-dlq
    spec:
      containers:
        - name: consumer
          image: redis:7
          command:
            - /bin/sh
            - -c
            - |
              RETRY_LIMIT=3
              while true; do
                MSG=$(redis-cli -h redis-master -a lab-redis-pass \
                  BRPOP order-queue 10 2>/dev/null | tail -1)
                if [ -n "$MSG" ]; then
                  # Simulate random failures (1 in 5 messages fail)
                  FAIL=$((RANDOM % 5))
                  if [ "$FAIL" -eq 0 ]; then
                    # Get retry count
                    RETRIES=$(redis-cli -h redis-master -a lab-redis-pass \
                      HGET "retries:$MSG" count 2>/dev/null)
                    RETRIES=${RETRIES:-0}
                    if [ "$RETRIES" -ge "$RETRY_LIMIT" ]; then
                      redis-cli -h redis-master -a lab-redis-pass \
                        LPUSH order-dlq "$MSG" > /dev/null 2>&1
                      redis-cli -h redis-master -a lab-redis-pass \
                        HDEL "retries:$MSG" count > /dev/null 2>&1
                      echo "DLQ: $MSG (exceeded $RETRY_LIMIT retries)"
                    else
                      redis-cli -h redis-master -a lab-redis-pass \
                        HINCRBY "retries:$MSG" count 1 > /dev/null 2>&1
                      redis-cli -h redis-master -a lab-redis-pass \
                        LPUSH order-queue "$MSG" > /dev/null 2>&1
                      echo "RETRY ($((RETRIES+1))/$RETRY_LIMIT): $MSG"
                    fi
                  else
                    echo "OK: $MSG"
                  fi
                fi
              done
```

```bash
k apply -f /tmp/consumer-dlq.yaml

# Check DLQ after some processing
k exec -n messaging deploy/queue-consumer-dlq -- \
  redis-cli -h redis-master -a lab-redis-pass LLEN order-dlq
```
</details>

### Task 5: Monitor DLQ with an Alert Consumer

Deploy a monitoring pod that watches the DLQ length.

<details>
<summary>Solution</summary>

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dlq-monitor
  namespace: messaging
spec:
  replicas: 1
  selector:
    matchLabels:
      app: dlq-monitor
  template:
    metadata:
      labels:
        app: dlq-monitor
    spec:
      containers:
        - name: monitor
          image: redis:7
          command:
            - /bin/sh
            - -c
            - |
              THRESHOLD=5
              while true; do
                DLQ_LEN=$(redis-cli -h redis-master -a lab-redis-pass \
                  LLEN order-dlq 2>/dev/null)
                echo "$(date): DLQ depth = $DLQ_LEN"
                if [ "$DLQ_LEN" -gt "$THRESHOLD" ]; then
                  echo "ALERT: DLQ depth $DLQ_LEN exceeds threshold $THRESHOLD!"
                fi
                sleep 15
              done
```

```bash
k apply -f /tmp/dlq-monitor.yaml
k logs -f -n messaging deploy/dlq-monitor
```
</details>

### Success Criteria

- [ ] KEDA ScaledObject is created and active
- [ ] Consumer pod count increases when 200 messages are pushed
- [ ] Pod count decreases after queue is drained
- [ ] Failed messages land in the DLQ (order-dlq Redis list)
- [ ] DLQ monitor detects and alerts on threshold breach

### Cleanup

```bash
kind delete cluster --name event-lab
```

---

**Next Module**: [Module 9.3: Serverless Interoperability (Lambda / Cloud Functions / Knative)](../module-9.3-serverless/) -- Learn when to use serverless alongside Kubernetes, how to trigger cloud functions from K8s events, and how Knative brings the serverless model directly into your cluster.
