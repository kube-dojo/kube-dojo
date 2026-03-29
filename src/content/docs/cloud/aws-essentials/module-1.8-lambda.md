---
title: "Module 1.8: AWS Lambda & Serverless Patterns"
slug: cloud/aws-essentials/module-1.8-lambda
sidebar:
  order: 9
---
## Complexity: [MEDIUM]
## Time to Complete: 2 hours

---

## Prerequisites

Before starting this module, you should have completed:
- [Module 1.1: IAM & Security Foundations](module-1.1-iam/)
- [Module 1.4: S3 & Storage Fundamentals](module-1.4-s3/)
- Basic Python or Node.js knowledge (Lambda examples use Python)
- AWS CLI configured with appropriate permissions

---

## Why This Module Matters

In 2019, a ride-sharing company was processing GPS telemetry data from 50,000 drivers. Every second, each driver's phone sent a location update. That is 50,000 events per second, with massive spikes during rush hours and near-zero traffic at 3 AM. They were running this on a fleet of 200 EC2 instances, auto-scaling between 80 and 200 based on traffic. The problem: the scaling was always 3-4 minutes behind the actual load. Rush hour started, requests queued up, and location data became stale -- which meant inaccurate ETAs for riders. Off-peak, they were paying for 80 instances doing almost nothing.

They replaced the ingestion layer with Lambda functions triggered by Amazon Kinesis. Each batch of GPS events triggered a Lambda invocation. During rush hour, AWS automatically ran thousands of Lambda instances concurrently. At 3 AM, it ran nearly zero. Scaling was instantaneous. Their infrastructure bill dropped 62% because they stopped paying for idle compute. More importantly, location data was always fresh because there was never a queue building up waiting for servers to scale.

AWS Lambda is the original serverless compute platform. Launched in 2014, it introduced the idea that you should write code and let the cloud provider handle everything else: provisioning, scaling, patching, and high availability. You pay only for the milliseconds your code actually runs. In this module, you will learn how Lambda works under the hood, the event sources that trigger it, how to handle cold starts, how to orchestrate complex workflows with Step Functions, and how to build a real event-driven pipeline that processes files uploaded to S3.

---

## How Lambda Works

Lambda's execution model is fundamentally different from containers or VMs. Understanding this model is essential for writing effective Lambda functions.

### The Execution Environment Lifecycle

```
Lambda Execution Environment Lifecycle:

Request 1 (Cold Start):
+------------------------------------------------------------+
| INIT Phase (billed as part of invocation duration)          |
| [Download code] -> [Start runtime] -> [Run init code]      |
| Extension init -> Runtime init -> Function init              |
| ~100ms-10s depending on language, package size, VPC          |
+------------------------------------------------------------+
| INVOKE Phase (billed per invocation)                        |
| [Run handler function] -> [Return response]                 |
| This is your actual code executing                          |
+------------------------------------------------------------+

Request 2 (Warm Start - same environment reused):
+------------------------------------------------------------+
| INVOKE Phase only (no INIT)                                 |
| [Run handler function] -> [Return response]                 |
| Init code NOT re-executed, connections reused               |
+------------------------------------------------------------+

Request 3 (Warm Start - reused again):
+------------------------------------------------------------+
| INVOKE Phase only                                           |
| [Run handler function] -> [Return response]                 |
+------------------------------------------------------------+

... (Environment stays warm for 5-15 minutes of inactivity)

Request N (after idle timeout - Cold Start again):
+------------------------------------------------------------+
| INIT Phase                                                   |
| [Download code] -> [Start runtime] -> [Run init code]       |
+------------------------------------------------------------+
| INVOKE Phase                                                 |
| [Run handler function] -> [Return response]                 |
+------------------------------------------------------------+
```

The critical insight: **code outside your handler function runs once per cold start, then is reused across invocations.** This is where you should initialize database connections, load configuration, and import heavy libraries.

```python
# lambda_function.py

import boto3
import json
import os

# INIT CODE - runs once per cold start, reused across invocations
# Put expensive initialization HERE
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])
print("Cold start: initialized DynamoDB client")

def handler(event, context):
    """
    HANDLER CODE - runs on every invocation
    Keep this lean and fast
    """
    # The 'table' variable is already initialized from the cold start
    response = table.get_item(Key={'id': event['id']})

    return {
        'statusCode': 200,
        'body': json.dumps(response.get('Item', {}))
    }
```

### Lambda Execution Limits

| Limit | Value | Can Be Increased? |
|-------|-------|-------------------|
| Max execution time | 15 minutes | No (hard limit) |
| Memory allocation | 128 MB - 10,240 MB | No (choose within range) |
| vCPU | Proportional to memory (1,769 MB = 1 vCPU) | No |
| Ephemeral storage (/tmp) | 512 MB - 10,240 MB | Configurable |
| Deployment package (zip) | 50 MB (250 MB unzipped) | No |
| Container image size | 10 GB | No |
| Concurrent executions | 1,000 per region (default) | Yes (up to tens of thousands) |
| Burst concurrency | 500-3,000 (varies by region) | No |
| Environment variables | 4 KB total | No |
| Layers | 5 layers per function | No |

The memory-to-CPU relationship is the most important detail here. Lambda does not let you configure CPU independently. At 1,769 MB of memory, you get 1 full vCPU. At 128 MB, you get a fraction. CPU-bound workloads (image processing, data transformation) need more memory even if they do not use the RAM -- because they need the CPU that comes with it.

---

## Event Sources and Triggers

Lambda functions do not run on their own. They are triggered by events from other AWS services. Understanding the trigger patterns is essential for designing event-driven architectures.

### Synchronous Invocations

The caller waits for Lambda to finish and gets the response back. Errors are returned to the caller.

```
Synchronous Pattern:

API Gateway --> Lambda --> Response --> API Gateway --> Client
                  |
                  v
               DynamoDB

Client waits for the entire chain to complete.
Timeout: API Gateway has a 29-second limit.
```

```bash
# Create a Lambda function
aws lambda create-function \
  --function-name api-handler \
  --runtime python3.12 \
  --role arn:aws:iam::123456789012:role/lambda-execution-role \
  --handler lambda_function.handler \
  --zip-file fileb://function.zip \
  --timeout 30 \
  --memory-size 256

# Invoke synchronously (RequestResponse)
aws lambda invoke \
  --function-name api-handler \
  --invocation-type RequestResponse \
  --payload '{"id": "user-123"}' \
  response.json

cat response.json
```

### Asynchronous Invocations

The caller sends the event and immediately gets a 202 (Accepted). Lambda processes it in the background with built-in retry logic (2 retries by default).

```
Asynchronous Pattern:

S3 Event ------> Lambda Event Queue ------> Lambda
(PutObject)      (managed by AWS)            (processes async)
                                                |
S3 gets 202      If Lambda fails:              v
immediately      Retry 1 (after ~1 min)     Process image
                 Retry 2 (after ~2 min)
                 Then: send to DLQ or
                 EventBridge destination
```

```bash
# Configure async invocation settings
aws lambda put-function-event-invoke-config \
  --function-name image-processor \
  --maximum-retry-attempts 2 \
  --maximum-event-age-in-seconds 3600 \
  --destination-config '{
    "OnSuccess": {
      "Destination": "arn:aws:sqs:us-east-1:123456789012:success-queue"
    },
    "OnFailure": {
      "Destination": "arn:aws:sqs:us-east-1:123456789012:dead-letter-queue"
    }
  }'
```

### Stream-Based (Polling) Invocations

Lambda polls a stream (Kinesis, DynamoDB Streams, SQS) and processes batches of records.

```
Stream Pattern:

SQS Queue: [msg1] [msg2] [msg3] [msg4] [msg5] [msg6] ...
                \___________/        \___________/
                  Batch 1              Batch 2
                    |                    |
                    v                    v
                Lambda A             Lambda B
                (concurrent)         (concurrent)
```

```bash
# Create an SQS trigger for Lambda
aws lambda create-event-source-mapping \
  --function-name order-processor \
  --event-source-arn arn:aws:sqs:us-east-1:123456789012:orders-queue \
  --batch-size 10 \
  --maximum-batching-window-in-seconds 5 \
  --function-response-types ReportBatchItemFailures
```

### Trigger Pattern Reference

| Trigger Source | Invocation Type | Retry Behavior | Common Use Case |
|---------------|----------------|----------------|-----------------|
| API Gateway | Synchronous | Caller retries | REST APIs, webhooks |
| ALB | Synchronous | Caller retries | HTTP services behind ALB |
| S3 Events | Asynchronous | 2 retries + DLQ | File processing pipelines |
| EventBridge | Asynchronous | 2 retries + DLQ | Event-driven microservices |
| SNS | Asynchronous | 2 retries + DLQ | Fan-out notifications |
| SQS | Polling | Message returns to queue | Queue processing, decoupling |
| Kinesis | Polling | Retries until data expires | Real-time stream processing |
| DynamoDB Streams | Polling | Retries until data expires | Change data capture (CDC) |
| CloudWatch Events | Asynchronous | 2 retries | Scheduled tasks (cron) |
| Cognito | Synchronous | No retry | Auth triggers |

---

## Cold Starts: Understanding and Mitigating

Cold starts are Lambda's most discussed limitation. Let us look at the actual numbers and what you can do about them.

### Cold Start Duration by Runtime

| Runtime | Typical Cold Start | With VPC | With Provisioned Concurrency |
|---------|-------------------|----------|------------------------------|
| Python 3.12 | 150-400 ms | 200-500 ms | ~0 ms (warm) |
| Node.js 20 | 150-350 ms | 200-500 ms | ~0 ms (warm) |
| Java 21 | 800-3000 ms | 1000-4000 ms | ~0 ms (warm) |
| .NET 8 | 400-900 ms | 500-1200 ms | ~0 ms (warm) |
| Go (AL2023) | 80-200 ms | 100-300 ms | ~0 ms (warm) |
| Rust (AL2023) | 50-150 ms | 80-250 ms | ~0 ms (warm) |
| Container image | 500-5000 ms | 600-6000 ms | ~0 ms (warm) |

VPC cold starts used to add 8-12 seconds. Since 2019 (Hyperplane ENI), VPC cold starts add only 50-200 ms. This is no longer a reason to avoid VPC-attached Lambda functions.

### Minimizing Cold Starts

**1. Keep your deployment package small:**

```bash
# Bad: 250 MB package with everything
pip install boto3 pandas numpy scipy scikit-learn -t .
# This includes hundreds of MB of unused code

# Better: Only install what you need
pip install boto3 -t .  # boto3 is actually pre-installed in Lambda runtime

# Best: Use Lambda Layers for shared dependencies
# Your function package stays tiny, dependencies are in layers
```

**2. Initialize connections outside the handler:**

```python
# BAD: Connection created on every invocation
def handler(event, context):
    import boto3  # Import on every call
    client = boto3.client('s3')  # New client on every call
    return client.get_object(Bucket='my-bucket', Key=event['key'])

# GOOD: Connection created once, reused
import boto3  # Import once at cold start
client = boto3.client('s3')  # Client created once

def handler(event, context):
    return client.get_object(Bucket='my-bucket', Key=event['key'])
```

**3. Use Provisioned Concurrency for latency-sensitive workloads:**

```bash
# Provision 10 warm environments for the production alias
aws lambda put-provisioned-concurrency-config \
  --function-name api-handler \
  --qualifier production \
  --provisioned-concurrent-executions 10

# Check provisioned concurrency status
aws lambda get-provisioned-concurrency-config \
  --function-name api-handler \
  --qualifier production

# Use Application Auto Scaling to adjust provisioned concurrency
aws application-autoscaling register-scalable-target \
  --service-namespace lambda \
  --resource-id function:api-handler:production \
  --scalable-dimension lambda:function:ProvisionedConcurrency \
  --min-capacity 5 \
  --max-capacity 50

aws application-autoscaling put-scaling-policy \
  --service-namespace lambda \
  --resource-id function:api-handler:production \
  --scalable-dimension lambda:function:ProvisionedConcurrency \
  --policy-name utilization-tracking \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 0.7,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "LambdaProvisionedConcurrencyUtilization"
    }
  }'
```

Provisioned concurrency costs extra (you pay for the warm environments even when idle), so use it selectively -- for user-facing APIs where P99 latency matters, not for background processing.

---

## Lambda Layers

Layers let you package shared dependencies separately from your function code. This reduces deployment package size and enables sharing common libraries across functions.

```
Lambda Layers:

Function Code (your handler)        <- Deployed frequently (seconds)
         |
    +----+----+----+
    |    |    |    |
  Layer1  Layer2  Layer3             <- Deployed rarely (shared)
  (boto3) (pandas) (custom-utils)

Layers are extracted to /opt/ in the execution environment.
Runtime-specific paths:
  Python: /opt/python/
  Node.js: /opt/nodejs/
  Java: /opt/java/lib/
```

```bash
# Create a layer with Python dependencies
mkdir -p python-layer/python
pip install requests pillow -t python-layer/python/
cd python-layer && zip -r ../my-layer.zip python/

# Publish the layer
LAYER_ARN=$(aws lambda publish-layer-version \
  --layer-name common-dependencies \
  --zip-file fileb://my-layer.zip \
  --compatible-runtimes python3.12 \
  --compatible-architectures x86_64 arm64 \
  --query 'LayerVersionArn' --output text)

echo "Layer ARN: ${LAYER_ARN}"

# Add the layer to a function
aws lambda update-function-configuration \
  --function-name image-processor \
  --layers ${LAYER_ARN}
```

### When to Use Layers vs Container Images

| Approach | Best For | Limits |
|----------|---------|--------|
| Zip package only | Simple functions < 50 MB | 50 MB zipped, 250 MB unzipped |
| Zip + Layers | Shared dependencies, moderate size | 5 layers, 250 MB total unzipped |
| Container Image | Large dependencies (ML models, binaries) | 10 GB image size |

For anything involving machine learning libraries (PyTorch, TensorFlow), scientific computing (scipy, numpy), or custom binaries, use container images. The 10 GB limit gives you far more room.

---

## Step Functions: Orchestrating Workflows

When a single Lambda function is not enough, AWS Step Functions lets you chain Lambda functions (and other AWS services) into state machines with built-in error handling, retries, and branching logic.

### Why Not Just Call Lambda from Lambda?

You could have one Lambda function invoke another, but this creates several problems:

```
Anti-Pattern: Lambda calling Lambda

Lambda A (15 min timeout)
  |
  +-> Lambda B (15 min timeout)
  |     |
  |     +-> Lambda C (15 min timeout)
  |           |
  |           +-> Lambda D
  |
  Problem 1: Lambda A is WAITING (and PAYING) while B, C, D run
  Problem 2: If C fails, how does A know? Error handling is manual
  Problem 3: If A times out, B/C/D become orphans
  Problem 4: No visibility into the workflow state

Better: Step Functions

Step Function State Machine
  |
  +-> State 1: Invoke Lambda A
  |     Success -> State 2
  |     Failure -> Error Handler
  |
  +-> State 2: Invoke Lambda B
  |     Success -> State 3
  |     Failure -> Retry (3x) -> Error Handler
  |
  +-> State 3: Choice
        Condition A -> Invoke Lambda C
        Condition B -> Invoke Lambda D
        Default -> End

  Each Lambda runs independently (no waiting)
  Built-in retries, error handling, and timeout management
  Visual workflow in the AWS Console
  Full execution history for debugging
```

### Creating a Step Function

```bash
# Create the state machine definition
cat > /tmp/state-machine.json <<'EOF'
{
  "Comment": "Image processing pipeline",
  "StartAt": "ValidateInput",
  "States": {
    "ValidateInput": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:validate-input",
      "Next": "GenerateThumbnail",
      "Catch": [{
        "ErrorEquals": ["ValidationError"],
        "Next": "HandleError",
        "ResultPath": "$.error"
      }]
    },
    "GenerateThumbnail": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:generate-thumbnail",
      "Retry": [{
        "ErrorEquals": ["States.TaskFailed"],
        "IntervalSeconds": 3,
        "MaxAttempts": 2,
        "BackoffRate": 2.0
      }],
      "Next": "StoreMetadata"
    },
    "StoreMetadata": {
      "Type": "Task",
      "Resource": "arn:aws:states:::dynamodb:putItem",
      "Parameters": {
        "TableName": "image-metadata",
        "Item": {
          "imageId": {"S.$": "$.imageId"},
          "thumbnailKey": {"S.$": "$.thumbnailKey"},
          "processedAt": {"S.$": "$$.State.EnteredTime"}
        }
      },
      "Next": "NotifyComplete"
    },
    "NotifyComplete": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "arn:aws:sns:us-east-1:123456789012:image-processed",
        "Message.$": "States.Format('Image {} processed successfully', $.imageId)"
      },
      "End": true
    },
    "HandleError": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "arn:aws:sns:us-east-1:123456789012:processing-errors",
        "Message.$": "States.Format('Error processing image: {}', $.error.Cause)"
      },
      "End": true
    }
  }
}
EOF

# Create the IAM role for Step Functions
aws iam create-role \
  --role-name step-functions-execution-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "states.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Attach permissions
aws iam put-role-policy \
  --role-name step-functions-execution-role \
  --policy-name StepFunctionsPermissions \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": "lambda:InvokeFunction",
        "Resource": "arn:aws:lambda:us-east-1:123456789012:function:*"
      },
      {
        "Effect": "Allow",
        "Action": ["dynamodb:PutItem"],
        "Resource": "arn:aws:dynamodb:us-east-1:123456789012:table/image-metadata"
      },
      {
        "Effect": "Allow",
        "Action": "sns:Publish",
        "Resource": "arn:aws:sns:us-east-1:123456789012:*"
      }
    ]
  }'

# Create the state machine
aws stepfunctions create-state-machine \
  --name image-processing-pipeline \
  --definition file:///tmp/state-machine.json \
  --role-arn arn:aws:iam::123456789012:role/step-functions-execution-role \
  --type STANDARD
```

### Standard vs Express Workflows

| Feature | Standard | Express |
|---------|----------|---------|
| Max duration | 1 year | 5 minutes |
| Pricing | Per state transition ($0.025/1000) | Per execution + duration |
| Execution history | 90 days in console | CloudWatch Logs only |
| At-least-once vs exactly-once | Exactly once | At-least-once |
| Best for | Long-running, business-critical workflows | High-volume, short-duration processing |

Use Standard for order processing, approval workflows, and anything that needs to wait for human input. Use Express for real-time data processing, IoT event handling, and high-throughput transformation pipelines.

---

## Event-Driven Architecture Patterns

Lambda enables powerful event-driven patterns. Here are the three you will use most often.

### Pattern 1: S3 Event Processing

```
S3 Bucket                Lambda              Output Bucket
+--------+    Event     +--------+   PUT    +--------+
| Upload |----------->  | Process|--------> | Output |
| image  |  PutObject   | resize |          | thumb  |
+--------+              +--------+          +--------+
                            |
                            v
                        DynamoDB
                        (metadata)
```

```bash
# Add S3 trigger permission
aws lambda add-permission \
  --function-name image-processor \
  --statement-id s3-trigger \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn arn:aws:s3:::upload-bucket \
  --source-account 123456789012

# Configure S3 to send events to Lambda
aws s3api put-bucket-notification-configuration \
  --bucket upload-bucket \
  --notification-configuration '{
    "LambdaFunctionConfigurations": [
      {
        "LambdaFunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:image-processor",
        "Events": ["s3:ObjectCreated:*"],
        "Filter": {
          "Key": {
            "FilterRules": [
              {"Name": "prefix", "Value": "uploads/"},
              {"Name": "suffix", "Value": ".jpg"}
            ]
          }
        }
      }
    ]
  }'
```

### Pattern 2: Fan-Out with SNS

```
                          +-> Lambda A (send email)
                         /
SNS Topic ---> Subscribe +-> Lambda B (update dashboard)
                         \
                          +-> SQS Queue -> Lambda C (async processing)
```

### Pattern 3: Event Bus with EventBridge

```
Source Service        EventBridge           Target Functions
+-----------+    +------------------+
| Order API | -> | Rule: order.*    | --> Lambda: process-order
+-----------+    | Rule: order.paid | --> Lambda: send-receipt
                 | Rule: order.ship | --> Lambda: notify-warehouse
| Payment   | -> | Rule: payment.*  | --> Lambda: update-ledger
+-----------+    +------------------+
```

```bash
# Create an EventBridge rule
aws events put-rule \
  --name order-created-rule \
  --event-pattern '{
    "source": ["com.myapp.orders"],
    "detail-type": ["OrderCreated"],
    "detail": {
      "total": [{"numeric": [">", 100]}]
    }
  }'

# Add Lambda as a target
aws events put-targets \
  --rule order-created-rule \
  --targets '[{
    "Id": "process-high-value-order",
    "Arn": "arn:aws:lambda:us-east-1:123456789012:function:high-value-order-processor"
  }]'
```

---

## Did You Know?

1. **Lambda was announced at AWS re:Invent 2014 and initially supported only Node.js.** The launch demo was a function that resized images uploaded to S3 -- the exact exercise at the end of this module. Tim Wagner, the "father of Lambda," later said the hardest engineering problem was not running the code but making the billing work at millisecond granularity. AWS had to build entirely new metering infrastructure to charge in 1ms increments.

2. **Every Lambda function runs inside a Firecracker microVM**, the same open-source virtualization technology that powers Fargate. Firecracker was specifically built for Lambda and later open-sourced. Each microVM provides hardware-level isolation between tenants, booting in under 125 milliseconds. Before Firecracker, Lambda used containers on shared EC2 instances -- Firecracker was built because containers alone did not provide strong enough security isolation for a multi-tenant compute platform.

3. **Lambda's theoretical maximum concurrency** across all functions in a region defaults to 1,000, but AWS routinely grants increases to 100,000+ for enterprise accounts. Netflix runs hundreds of thousands of concurrent Lambda executions during peak hours for tasks like video encoding, data validation, and internal automation. At that scale, Lambda is managing more compute resources than most companies' entire infrastructure.

4. **Lambda@Edge and CloudFront Functions let you run code at 450+ edge locations worldwide**, executing within single-digit milliseconds of the end user. Lambda@Edge supports full Lambda runtimes (Node.js, Python) with up to 5-second execution time, while CloudFront Functions use a restricted JavaScript runtime but execute in under 1 millisecond. Common uses include request/response manipulation, A/B testing, authentication, and URL rewriting -- all without the request ever reaching your origin server.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|---------------|---------------|
| Initializing SDK clients inside the handler | Developers follow the same patterns they use in web applications | Move all initialization (SDK clients, DB connections, config loading) outside the handler function. This code runs once per cold start and is reused for subsequent invocations |
| Setting timeout too close to the expected duration | Developers measure average execution time and set timeout just above it | Set timeout to 3-5x the expected P95 duration. Network calls to downstream services can be slow under load. A function that normally takes 2 seconds should have a 10-second timeout |
| Using Lambda for long-running processes | Lambda seems simpler than ECS for everything | Lambda has a 15-minute hard limit. For processes longer than 5-10 minutes, use ECS Fargate or Step Functions to chain multiple Lambda invocations |
| Not configuring dead letter queues for async invocations | DLQs seem optional and add complexity | Without a DLQ or failure destination, events that fail all retries are silently dropped. Always configure either a DLQ (SQS) or an OnFailure destination for asynchronous triggers |
| Using the same concurrency for all functions | Default is account-level 1,000 shared across all functions | Set reserved concurrency on critical functions to guarantee capacity. A runaway non-critical function can starve your production API by consuming all available concurrency |
| Not using ARM64 (Graviton) processors | x86_64 is the default, and developers do not think to change it | ARM64 functions cost 20% less and often run faster. Unless you have x86-specific compiled dependencies, always use arm64 architecture |
| Packaging the entire node_modules or site-packages | Default build includes everything, including dev dependencies | Use `--only=production` for npm or create a requirements.txt with only runtime dependencies. Use Lambda Layers for heavy shared libraries. Smaller packages = faster cold starts |
| Recursive Lambda invocations | Lambda writes to S3, which triggers the same Lambda, which writes to S3... | Use different source and destination buckets, or apply event filters (prefix/suffix) to prevent the function from triggering itself. AWS added recursive invocation detection in 2023, but prevention is better |

---

## Quiz

<details>
<summary>1. Why should you initialize database connections and SDK clients outside the Lambda handler function?</summary>

Lambda reuses execution environments across invocations. Code outside the handler runs once during the cold start (INIT phase) and persists in memory for subsequent invocations. If you create a database connection inside the handler, you create a new connection on every single invocation -- which is slow (adding 50-200ms per call), wasteful (opening and closing connections unnecessarily), and can exhaust database connection limits under high concurrency. By initializing outside the handler, the connection is created once and reused for the lifetime of the execution environment (typically 5-15 minutes of inactivity).
</details>

<details>
<summary>2. A Lambda function processes SQS messages in batches of 10. One message in the batch causes an error. Without proper configuration, what happens to all 10 messages?</summary>

Without `ReportBatchItemFailures` configured, if your function throws an error while processing any message in the batch, Lambda considers the entire batch as failed. All 10 messages return to the queue and will be processed again -- including the 9 that succeeded. This causes duplicate processing of successful messages and keeps failing on the same bad message. The fix is to enable `ReportBatchItemFailures` in the event source mapping and have your function return a list of failed message IDs in the `batchItemFailures` response field. Lambda then only returns the specific failed messages to the queue while acknowledging the successful ones.
</details>

<details>
<summary>3. Explain the difference between reserved concurrency and provisioned concurrency.</summary>

Reserved concurrency sets a maximum limit on how many concurrent executions a function can have, carved out from the account-level pool. If you reserve 100 for a function, that function can never exceed 100 concurrent executions, and those 100 are guaranteed even if other functions are consuming the rest of the pool. Provisioned concurrency, on the other hand, keeps a specified number of execution environments pre-initialized and warm, eliminating cold starts. You pay for provisioned environments whether they are used or not. Reserved concurrency is about capacity management and isolation (free). Provisioned concurrency is about latency optimization (costs money). They serve different purposes and can be used together.
</details>

<details>
<summary>4. Your Lambda function is configured with 128 MB of memory and processes image files. It runs slowly even though memory usage is only 40 MB. Why, and how do you fix it?</summary>

Lambda allocates CPU proportionally to memory. At 128 MB, you get a tiny fraction of a vCPU. Image processing is CPU-intensive, so your function is CPU-starved even though it has plenty of RAM. The fix is to increase the memory allocation. At 1,769 MB, you get 1 full vCPU. For image processing, try 1,024-2,048 MB. The function will run faster and may actually cost less because the reduced execution time offsets the higher per-millisecond cost. AWS provides the Lambda Power Tuning tool (an open-source Step Functions-based tool) that automatically tests your function at different memory settings and finds the optimal cost/performance balance.
</details>

<details>
<summary>5. Why would you choose Step Functions over having one Lambda function invoke another Lambda function directly?</summary>

Direct Lambda-to-Lambda invocation has several problems. The calling function must wait (and pay) while the called function runs. If the called function fails, you must implement retry logic manually in your code. If the calling function times out, the called function becomes an orphan with no coordination. There is no built-in visibility into the workflow state. Step Functions solves all of these: each Lambda runs independently (no waiting), retries are declarative (no code), error handling is standardized with catch/fallback states, execution history is visual and persisted for 90 days, and workflows can pause for up to a year waiting for external input. The trade-off is cost ($0.025 per 1,000 state transitions), but for any workflow with more than 2 steps, it pays for itself in reduced debugging time alone.
</details>

<details>
<summary>6. What happens if your Lambda function writes to the same S3 bucket that triggers it?</summary>

This creates a recursive invocation loop. The function is triggered by an S3 PutObject event, processes the file, writes output to the same bucket, which triggers another invocation, which processes and writes again, ad infinitum. This can generate millions of invocations in minutes, resulting in massive costs and potential service disruption. AWS added recursive invocation detection in 2023, which automatically stops the function after detecting 16 recursive calls. However, you should prevent this by design: use separate input and output buckets, or configure S3 event filters with different prefixes (e.g., trigger on `uploads/` prefix, write to `processed/` prefix). Never rely on automatic detection as your primary defense.
</details>

<details>
<summary>7. When should you use Lambda container images instead of zip packages?</summary>

Use container images when your deployment package exceeds the 250 MB unzipped limit for zip packages, or when your function depends on large native binaries, ML models, or system libraries that are difficult to manage in zip format. Container images support up to 10 GB, giving you 40x more space. They also let you use your existing Docker build pipeline and test locally with `docker run`. The trade-off is slightly slower cold starts (500-5000ms vs 150-400ms for zip) because the image must be pulled and extracted. For functions with heavy dependencies (PyTorch, TensorFlow, OpenCV, Puppeteer), container images are the practical choice.
</details>

---

## Hands-On Exercise: S3 Upload to Lambda Thumbnail Generator

In this exercise, you will build an event-driven pipeline: when an image is uploaded to an S3 bucket, a Lambda function automatically generates a thumbnail and stores it in an output bucket.

### Setup

```bash
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export REGION="us-east-1"
export INPUT_BUCKET="kubedojo-lambda-input-${ACCOUNT_ID}"
export OUTPUT_BUCKET="kubedojo-lambda-output-${ACCOUNT_ID}"
export FUNCTION_NAME="kubedojo-thumbnail-generator"
```

### Task 1: Create the S3 Buckets

<details>
<summary>Solution</summary>

```bash
# Create input bucket
aws s3api create-bucket \
  --bucket ${INPUT_BUCKET} \
  --region ${REGION}

# Create output bucket
aws s3api create-bucket \
  --bucket ${OUTPUT_BUCKET} \
  --region ${REGION}

echo "Input bucket: ${INPUT_BUCKET}"
echo "Output bucket: ${OUTPUT_BUCKET}"
```
</details>

### Task 2: Create the Lambda Function Code

Write the thumbnail generator function with Pillow.

<details>
<summary>Solution</summary>

```bash
mkdir -p /tmp/lambda-exercise && cd /tmp/lambda-exercise

# Create the Lambda function code
cat > lambda_function.py <<'PYTHON'
import boto3
import json
import os
import urllib.parse
from io import BytesIO

# Initialize clients outside handler (reused across invocations)
s3_client = boto3.client('s3')
OUTPUT_BUCKET = os.environ['OUTPUT_BUCKET']
THUMBNAIL_SIZE = (200, 200)

def handler(event, context):
    """Process S3 PutObject events and generate thumbnails."""

    # Import Pillow here to keep cold start fast if there is no image
    from PIL import Image

    for record in event['Records']:
        # Extract bucket and key from the S3 event
        source_bucket = record['s3']['bucket']['name']
        source_key = urllib.parse.unquote_plus(
            record['s3']['object']['key'], encoding='utf-8'
        )

        print(f"Processing: s3://{source_bucket}/{source_key}")

        # Skip if not an image
        if not source_key.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            print(f"Skipping non-image file: {source_key}")
            continue

        try:
            # Download the original image
            response = s3_client.get_object(
                Bucket=source_bucket, Key=source_key
            )
            image_data = response['Body'].read()
            original_size = len(image_data)

            # Open and resize the image
            image = Image.open(BytesIO(image_data))
            image.thumbnail(THUMBNAIL_SIZE, Image.LANCZOS)

            # Save thumbnail to buffer
            buffer = BytesIO()
            output_format = 'JPEG' if source_key.lower().endswith(('.jpg', '.jpeg')) else 'PNG'
            image.save(buffer, format=output_format, quality=85)
            buffer.seek(0)
            thumbnail_size = buffer.getbuffer().nbytes

            # Generate output key
            filename = os.path.basename(source_key)
            name, ext = os.path.splitext(filename)
            output_key = f"thumbnails/{name}-thumb{ext}"

            # Upload thumbnail to output bucket
            content_type = 'image/jpeg' if output_format == 'JPEG' else 'image/png'
            s3_client.put_object(
                Bucket=OUTPUT_BUCKET,
                Key=output_key,
                Body=buffer,
                ContentType=content_type,
                Metadata={
                    'original-bucket': source_bucket,
                    'original-key': source_key,
                    'original-size': str(original_size),
                    'thumbnail-size': str(thumbnail_size)
                }
            )

            print(f"Thumbnail saved: s3://{OUTPUT_BUCKET}/{output_key} "
                  f"({original_size} -> {thumbnail_size} bytes)")

        except Exception as e:
            print(f"Error processing {source_key}: {str(e)}")
            raise

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Processed {len(event["Records"])} image(s)',
        })
    }
PYTHON

echo "Lambda function code created"
```
</details>

### Task 3: Create the Lambda Layer with Pillow

<details>
<summary>Solution</summary>

```bash
cd /tmp/lambda-exercise

# Create a layer with Pillow
mkdir -p pillow-layer/python
pip install Pillow -t pillow-layer/python/ --platform manylinux2014_x86_64 --only-binary=:all:
cd pillow-layer && zip -r ../pillow-layer.zip python/
cd ..

# Publish the layer
LAYER_ARN=$(aws lambda publish-layer-version \
  --layer-name pillow \
  --zip-file fileb://pillow-layer.zip \
  --compatible-runtimes python3.12 \
  --compatible-architectures x86_64 \
  --query 'LayerVersionArn' --output text)

echo "Layer ARN: ${LAYER_ARN}"
```
</details>

### Task 4: Create the IAM Role and Deploy the Function

<details>
<summary>Solution</summary>

```bash
# Create the execution role
aws iam create-role \
  --role-name lambda-thumbnail-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Attach basic Lambda execution policy (CloudWatch Logs)
aws iam attach-role-policy \
  --role-name lambda-thumbnail-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Add S3 read/write permissions
aws iam put-role-policy \
  --role-name lambda-thumbnail-role \
  --policy-name S3Access \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": ["s3:GetObject"],
        "Resource": "arn:aws:s3:::'"${INPUT_BUCKET}"'/*"
      },
      {
        "Effect": "Allow",
        "Action": ["s3:PutObject"],
        "Resource": "arn:aws:s3:::'"${OUTPUT_BUCKET}"'/*"
      }
    ]
  }'

# Wait for IAM propagation
echo "Waiting 10 seconds for IAM role propagation..."
sleep 10

# Package the function
cd /tmp/lambda-exercise
zip function.zip lambda_function.py

# Create the Lambda function
aws lambda create-function \
  --function-name ${FUNCTION_NAME} \
  --runtime python3.12 \
  --role arn:aws:iam::${ACCOUNT_ID}:role/lambda-thumbnail-role \
  --handler lambda_function.handler \
  --zip-file fileb://function.zip \
  --timeout 60 \
  --memory-size 512 \
  --environment "Variables={OUTPUT_BUCKET=${OUTPUT_BUCKET}}" \
  --layers ${LAYER_ARN}

echo "Function created: ${FUNCTION_NAME}"
```
</details>

### Task 5: Configure the S3 Trigger

<details>
<summary>Solution</summary>

```bash
# Grant S3 permission to invoke the Lambda function
aws lambda add-permission \
  --function-name ${FUNCTION_NAME} \
  --statement-id s3-trigger-permission \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn arn:aws:s3:::${INPUT_BUCKET} \
  --source-account ${ACCOUNT_ID}

# Configure S3 bucket notification
aws s3api put-bucket-notification-configuration \
  --bucket ${INPUT_BUCKET} \
  --notification-configuration '{
    "LambdaFunctionConfigurations": [
      {
        "LambdaFunctionArn": "arn:aws:lambda:'"${REGION}"':'"${ACCOUNT_ID}"':function:'"${FUNCTION_NAME}"'",
        "Events": ["s3:ObjectCreated:*"],
        "Filter": {
          "Key": {
            "FilterRules": [
              {"Name": "prefix", "Value": "uploads/"},
              {"Name": "suffix", "Value": ".jpg"}
            ]
          }
        }
      }
    ]
  }'

echo "S3 trigger configured"
```
</details>

### Task 6: Test the Pipeline End-to-End

Upload an image and verify the thumbnail is generated.

<details>
<summary>Solution</summary>

```bash
# Create a test image (a simple 1000x1000 red square)
python3 -c "
from PIL import Image
img = Image.new('RGB', (1000, 1000), color='red')
img.save('/tmp/lambda-exercise/test-image.jpg', 'JPEG')
print('Test image created: 1000x1000 red square')
"

# Upload to the input bucket
aws s3 cp /tmp/lambda-exercise/test-image.jpg \
  s3://${INPUT_BUCKET}/uploads/test-image.jpg

echo "Uploaded test image. Waiting 10 seconds for processing..."
sleep 10

# Check the output bucket for the thumbnail
aws s3 ls s3://${OUTPUT_BUCKET}/thumbnails/

# Download and verify the thumbnail
aws s3 cp s3://${OUTPUT_BUCKET}/thumbnails/test-image-thumb.jpg \
  /tmp/lambda-exercise/thumbnail.jpg

python3 -c "
from PIL import Image
img = Image.open('/tmp/lambda-exercise/thumbnail.jpg')
print(f'Thumbnail size: {img.size}')
print(f'Format: {img.format}')
"

# Check Lambda logs
LOG_STREAM=$(aws logs describe-log-streams \
  --log-group-name /aws/lambda/${FUNCTION_NAME} \
  --order-by LastEventTime --descending --limit 1 \
  --query 'logStreams[0].logStreamName' --output text)

aws logs get-log-events \
  --log-group-name /aws/lambda/${FUNCTION_NAME} \
  --log-stream-name "${LOG_STREAM}" \
  --limit 20 \
  --query 'events[*].message' --output text
```
</details>

### Cleanup

<details>
<summary>Solution</summary>

```bash
# Delete S3 bucket contents and buckets
aws s3 rm s3://${INPUT_BUCKET} --recursive
aws s3 rm s3://${OUTPUT_BUCKET} --recursive
aws s3api delete-bucket --bucket ${INPUT_BUCKET}
aws s3api delete-bucket --bucket ${OUTPUT_BUCKET}

# Delete Lambda function
aws lambda delete-function --function-name ${FUNCTION_NAME}

# Delete Lambda layer
aws lambda delete-layer-version \
  --layer-name pillow --version-number 1

# Delete IAM role (detach policies first)
aws iam detach-role-policy \
  --role-name lambda-thumbnail-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam delete-role-policy \
  --role-name lambda-thumbnail-role \
  --policy-name S3Access

aws iam delete-role --role-name lambda-thumbnail-role

# Delete CloudWatch log group
aws logs delete-log-group \
  --log-group-name /aws/lambda/${FUNCTION_NAME}

# Clean up local files
rm -rf /tmp/lambda-exercise

echo "Cleanup complete"
```
</details>

### Success Criteria

- [ ] Input and output S3 buckets created
- [ ] Lambda function deployed with Pillow layer
- [ ] IAM role created with least-privilege S3 access
- [ ] S3 trigger configured with prefix and suffix filters
- [ ] Uploading a .jpg to uploads/ generates a thumbnail in the output bucket
- [ ] Thumbnail dimensions are 200x200 or smaller (maintaining aspect ratio)
- [ ] Lambda logs show successful processing
- [ ] All resources cleaned up

---

## Next Module

Next up: **[Module 1.9: Secrets Manager](module-1.9-secrets/)** -- Learn to manage sensitive configuration data (database credentials, API keys, certificates) securely with automatic rotation, cross-account sharing, and integration with Lambda, ECS, and EKS.
