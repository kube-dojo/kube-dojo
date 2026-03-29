---
title: "Module 3.8: Azure Functions & Serverless"
slug: cloud/azure-essentials/module-3.8-functions
sidebar:
  order: 9
---
**Complexity**: [MEDIUM] | **Time to Complete**: 2h | **Prerequisites**: Module 3.4 (Blob Storage), Module 3.1 (Entra ID)

## Why This Module Matters

In 2022, an e-commerce company was processing product image uploads. Their workflow was simple: a customer uploads an image, the application resizes it into three formats (thumbnail, medium, large), and stores the results. They ran this on a pair of D4s_v5 VMs behind a load balancer, running a Node.js process that polled an upload queue every 500 milliseconds. The two VMs cost $280/month. During business hours, they processed about 200 images per hour. Between midnight and 6 AM, they processed zero. On Black Friday, they processed 15,000 images per hour and the VMs could not keep up, causing a 3-hour backlog of unprocessed images. After migrating to Azure Functions with a Blob trigger, images were processed within 2 seconds of upload, regardless of volume. The Functions scaled automatically from zero to hundreds of concurrent executions during Black Friday, and back to zero at night. Their monthly bill dropped from $280 to $23---and the image processing backlog disappeared permanently.

Azure Functions is Microsoft's function-as-a-service (FaaS) platform. You write a small piece of code---a function---that is triggered by an event (an HTTP request, a new blob, a queue message, a timer). Azure handles everything else: provisioning infrastructure, scaling, patching, and monitoring. You pay only for the compute time your code consumes, measured in gigabyte-seconds.

In this module, you will learn the three hosting plans for Functions, how triggers and bindings eliminate boilerplate integration code, and how Durable Functions orchestrate multi-step workflows. By the end, you will build a function triggered by a blob upload that processes data and writes results to Cosmos DB using output bindings.

---

## Hosting Plans: Where Your Functions Run

The hosting plan determines the scaling behavior, available resources, and pricing model for your Functions. Choosing the right plan is one of the most consequential decisions.

| Feature | Consumption | Flex Consumption | Premium (EP) | Dedicated (ASP) |
| :--- | :--- | :--- | :--- | :--- |
| **Scaling** | 0 to 200 instances | 0 to 1000 instances | 1 to 100 instances | Manual or autoscale |
| **Scale to zero** | Yes | Yes | Optional (min 1) | No |
| **Cold start** | Yes (1-10 seconds) | Reduced (pre-warmed) | No (always warm) | No (always running) |
| **Max execution** | 5 min (default, 10 max) | 30 min | Unlimited | Unlimited |
| **Memory** | 1.5 GB | Up to 4 GB | 3.5-14 GB | Plan-dependent |
| **VNet integration** | No | Yes | Yes | Yes |
| **Cost model** | Per execution + GB-s | Per execution + GB-s | Per instance hour | Per App Service Plan |
| **Free grant** | 1M executions + 400K GB-s/month | Similar | None | None |
| **Best for** | Event-driven, sporadic | Event-driven, predictable | Low latency, always ready | Existing ASP, long jobs |

```text
    Decision Tree:

    Does your function need VNet access?
    ├── YES → Is cost a primary concern?
    │         ├── YES → Flex Consumption (scales to zero, VNet support)
    │         └── NO  → Premium EP1 (no cold start, VNet, unlimited duration)
    │
    └── NO  → Is execution time always under 5 minutes?
              ├── YES → Consumption (cheapest, simplest)
              └── NO  → Premium or Dedicated
```

```bash
# Create a Consumption plan Function App (Python requires Linux)
az functionapp create \
  --resource-group myRG \
  --consumption-plan-location eastus2 \
  --runtime python \
  --runtime-version 3.11 \
  --os-type Linux \
  --functions-version 4 \
  --name kubedojo-func-$(openssl rand -hex 4) \
  --storage-account "$STORAGE_NAME"

# Create a Premium plan Function App
az functionapp plan create \
  --resource-group myRG \
  --name kubedojo-premium-plan \
  --location eastus2 \
  --sku EP1 \
  --min-instances 1 \
  --max-burst 20

az functionapp create \
  --resource-group myRG \
  --plan kubedojo-premium-plan \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name kubedojo-premium-func \
  --storage-account "$STORAGE_NAME"
```

### Understanding Cold Start

Cold start is the latency added when a function executes for the first time (or after an idle period). It happens because Azure needs to allocate a worker, load the runtime, and initialize your code.

```text
    Cold Start Breakdown (Consumption Plan, Python):

    ┌──────────────────────────────────────────────────────────┐
    │                      Total: 3-8 seconds                  │
    │                                                          │
    │  ┌─────────┐ ┌──────────┐ ┌───────────┐ ┌────────────┐  │
    │  │ Worker  │ │ Runtime  │ │ Dep Load  │ │ Your Code  │  │
    │  │ Alloc   │ │ Init     │ │ (pip pkgs)│ │ Init       │  │
    │  │ ~1-2s   │ │ ~0.5-1s  │ │ ~1-4s     │ │ ~0.2-1s    │  │
    │  └─────────┘ └──────────┘ └───────────┘ └────────────┘  │
    │                                                          │
    │  Mitigation strategies:                                  │
    │  1. Keep dependencies minimal (fewer pip packages)       │
    │  2. Use Premium plan (always-warm instances)             │
    │  3. Use Flex Consumption (pre-provisioned instances)     │
    │  4. Avoid heavy initialization in function startup       │
    └──────────────────────────────────────────────────────────┘
```

**War Story**: A payment processing company chose the Consumption plan for their webhook handler. Most requests completed in 200ms. But once every 15-20 minutes, the function would cold start, adding 6 seconds of latency. Their payment provider interpreted these 6-second responses as timeouts and marked them as failed, triggering retry logic that created duplicate transactions. Switching to Premium plan with 1 minimum instance eliminated cold starts entirely, and the duplicate transaction problem vanished overnight.

---

## Triggers and Bindings: The Power of Declarative Integration

Triggers and bindings are what make Azure Functions genuinely productive. A **trigger** is the event that causes a function to execute. A **binding** is a declarative connection to another Azure service that handles the boilerplate of reading from or writing to that service.

### Trigger Types

| Trigger | Event Source | Common Use Case |
| :--- | :--- | :--- |
| **HTTP** | HTTP request | REST APIs, webhooks |
| **Timer** | Cron schedule | Scheduled tasks, cleanup jobs |
| **Blob** | New/modified blob | Image processing, file transformation |
| **Queue** | Queue message | Async task processing |
| **Service Bus** | SB message | Enterprise messaging |
| **Event Hub** | Streaming events | IoT, telemetry processing |
| **Cosmos DB** | Document change feed | Real-time data synchronization |
| **Event Grid** | Azure events | Resource change reactions |

### Input and Output Bindings

```text
    ┌──────────────────────────────────────────────────────────┐
    │                    Azure Function                         │
    │                                                          │
    │  Input Bindings          Function Code       Output Bindings
    │  ┌────────────┐         ┌──────────┐        ┌────────────┐
    │  │ Blob       │ ──────► │          │ ──────► │ Cosmos DB  │
    │  │ Storage    │         │  Your    │        │ Document   │
    │  └────────────┘         │  Code    │        └────────────┘
    │  ┌────────────┐         │          │        ┌────────────┐
    │  │ Table      │ ──────► │  (just   │ ──────► │ Queue      │
    │  │ Storage    │         │   the    │        │ Message    │
    │  └────────────┘         │  logic)  │        └────────────┘
    │                         │          │        ┌────────────┐
    │  Trigger:               │          │ ──────► │ SendGrid   │
    │  ┌────────────┐         │          │        │ Email      │
    │  │ Queue      │ ──────► │          │        └────────────┘
    │  │ Message    │         └──────────┘
    │  └────────────┘
    │                                                          │
    │  Without bindings: 50+ lines of SDK setup code           │
    │  With bindings: 0 lines of SDK code (declarative)        │
    └──────────────────────────────────────────────────────────┘
```

### Python Function Examples

```python
# function_app.py - Timer trigger (run every 30 minutes)
import azure.functions as func
import logging

app = func.FunctionApp()

@app.timer_trigger(
    schedule="0 */30 * * * *",  # Every 30 minutes
    arg_name="timer",
    run_on_startup=False
)
def cleanup_job(timer: func.TimerRequest) -> None:
    if timer.past_due:
        logging.warning("Timer is past due!")
    logging.info("Running scheduled cleanup...")
    # Your cleanup logic here
```

```python
# HTTP trigger with Cosmos DB output binding
@app.route(route="orders", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
@app.cosmos_db_output(
    arg_name="outputDocument",
    database_name="OrdersDB",
    container_name="orders",
    connection="CosmosDBConnection"
)
def create_order(req: func.HttpRequest, outputDocument: func.Out[func.Document]) -> func.HttpResponse:
    order = req.get_json()
    order["id"] = str(uuid.uuid4())
    order["createdAt"] = datetime.utcnow().isoformat()

    # Write to Cosmos DB via output binding (no SDK code needed!)
    outputDocument.set(func.Document.from_dict(order))

    return func.HttpResponse(
        json.dumps({"orderId": order["id"]}),
        status_code=201,
        mimetype="application/json"
    )
```

```python
# Blob trigger with Queue output binding
@app.blob_trigger(
    arg_name="inputBlob",
    path="uploads/{name}",
    connection="StorageConnection"
)
@app.queue_output(
    arg_name="outputQueue",
    queue_name="processing-results",
    connection="StorageConnection"
)
def process_upload(inputBlob: func.InputStream, outputQueue: func.Out[str]) -> None:
    logging.info(f"Processing blob: {inputBlob.name}, Size: {inputBlob.length} bytes")

    # Process the blob content
    content = inputBlob.read()
    result = {
        "blobName": inputBlob.name,
        "size": inputBlob.length,
        "processedAt": datetime.utcnow().isoformat()
    }

    # Send result to queue via output binding
    outputQueue.set(json.dumps(result))
    logging.info(f"Result queued for {inputBlob.name}")
```

### Deploying Functions

```bash
# Initialize a new Function project locally
func init MyFunctionProject --python

# Create a new function
cd MyFunctionProject
func new --name ProcessBlob --template "Azure Blob Storage trigger"

# Run locally
func start

# Deploy to Azure
func azure functionapp publish kubedojo-func-xxxx

# Or deploy via Azure CLI with zip deploy
cd MyFunctionProject
zip -r function.zip . -x ".venv/*"
az functionapp deployment source config-zip \
  --resource-group myRG \
  --name kubedojo-func-xxxx \
  --src function.zip
```

---

## Durable Functions: Orchestrating Complex Workflows

Regular Azure Functions are stateless---each execution is independent. Durable Functions add state management, enabling you to write multi-step workflows, fan-out/fan-in patterns, and human interaction patterns.

### Patterns

```text
    Pattern 1: Function Chaining
    ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
    │  Step 1  │ ──► │  Step 2  │ ──► │  Step 3  │ ──► │  Step 4  │
    │ Validate │     │ Enrich  │     │ Process │     │ Notify  │
    └─────────┘     └─────────┘     └─────────┘     └─────────┘

    Pattern 2: Fan-Out / Fan-In
                    ┌─────────┐
               ┌──► │ Task A  │ ──┐
    ┌────────┐ │    └─────────┘   │    ┌──────────┐
    │ Start  │─┤    ┌─────────┐   ├──► │ Aggregate│
    └────────┘ │    │ Task B  │   │    └──────────┘
               ├──► └─────────┘ ──┤
               │    ┌─────────┐   │
               └──► │ Task C  │ ──┘
                    └─────────┘

    Pattern 3: Async HTTP API (Long-Running)
    Client ──► Start ──► Return Status URL
                │
                └──► Poll Status URL until complete
                         │
                         └──► Get Result
```

```python
# Durable Functions example: Image processing pipeline
import azure.functions as func
import azure.durable_functions as df

app = func.FunctionApp()

# Orchestrator function (coordinates the workflow)
@app.orchestration_trigger(context_name="context")
def image_pipeline(context: df.DurableOrchestrationContext):
    # Input: blob URL from the trigger
    blob_url = context.get_input()

    # Step 1: Validate the image
    validation = yield context.call_activity("validate_image", blob_url)
    if not validation["valid"]:
        return {"status": "rejected", "reason": validation["reason"]}

    # Step 2: Fan-out - create multiple sizes in parallel
    parallel_tasks = [
        context.call_activity("resize_image", {"url": blob_url, "size": "thumbnail"}),
        context.call_activity("resize_image", {"url": blob_url, "size": "medium"}),
        context.call_activity("resize_image", {"url": blob_url, "size": "large"}),
    ]
    results = yield context.task_all(parallel_tasks)

    # Step 3: Save metadata to database
    metadata = yield context.call_activity("save_metadata", {
        "original": blob_url,
        "variants": results
    })

    return {"status": "completed", "metadata": metadata}

# Activity functions (do the actual work)
@app.activity_trigger(input_name="blobUrl")
def validate_image(blobUrl: str) -> dict:
    # Validate image format, size, etc.
    return {"valid": True, "format": "jpeg", "dimensions": "3024x4032"}

@app.activity_trigger(input_name="params")
def resize_image(params: dict) -> str:
    # Resize the image (actual PIL/Pillow code would go here)
    return f"resized/{params['size']}/{params['url'].split('/')[-1]}"

@app.activity_trigger(input_name="data")
def save_metadata(data: dict) -> dict:
    # Save to Cosmos DB or Table Storage
    return {"id": "img-12345", "saved": True}

# HTTP trigger to start the orchestration
@app.route(route="start-pipeline", methods=["POST"])
@app.durable_client_input(client_name="client")
async def start_pipeline(req: func.HttpRequest, client) -> func.HttpResponse:
    blob_url = req.get_json().get("blobUrl")
    instance_id = await client.start_new("image_pipeline", client_input=blob_url)

    return client.create_check_status_response(req, instance_id)
```

Durable Functions store their state in Azure Storage (tables and queues), enabling them to run for days, weeks, or even months. An orchestration can be paused (waiting for a human approval, for example) and resumed without consuming any compute.

---

## Function App Configuration and Security

### Application Settings and Secrets

```bash
# Set an application setting (becomes an environment variable)
az functionapp config appsettings set \
  --resource-group myRG \
  --name kubedojo-func-xxxx \
  --settings "COSMOS_DB_ENDPOINT=https://mydb.documents.azure.com:443/"

# Reference Key Vault secrets (recommended over plain text)
az functionapp config appsettings set \
  --resource-group myRG \
  --name kubedojo-func-xxxx \
  --settings "CosmosDBConnection=@Microsoft.KeyVault(SecretUri=https://myvault.vault.azure.net/secrets/cosmos-connection/)"

# Enable managed identity for Key Vault access
az functionapp identity assign --resource-group myRG --name kubedojo-func-xxxx
```

### Authentication and Authorization

```bash
# Function-level auth (API key in header or query string)
# Configured per-function via authLevel in the trigger decorator

# App-level auth with Entra ID (Easy Auth)
az webapp auth microsoft update \
  --resource-group myRG \
  --name kubedojo-func-xxxx \
  --client-id "$APP_CLIENT_ID" \
  --issuer "https://login.microsoftonline.com/$TENANT_ID/v2.0"
```

---

## Did You Know?

1. **Azure Functions Consumption plan has processed trillions of executions** since its launch. The free grant of 1 million executions and 400,000 GB-seconds per month means that many small-to-medium applications run entirely for free. A function that executes 100,000 times per month at 128 MB memory and 200ms average duration uses only 2,560 GB-seconds---well within the free tier.

2. **Durable Functions can run for up to 7 days on the Consumption plan** (the orchestrator itself; individual activity functions still have the 5-10 minute limit). On Premium and Dedicated plans, they can run indefinitely. One retail company uses a Durable Function orchestration that runs for 30 days, managing a month-long A/B test lifecycle with periodic check-ins and automatic completion.

3. **Blob triggers use a polling mechanism, not events.** When you use a Blob trigger, Azure Functions scans the blob container for changes every few seconds. This means there can be a delay of up to 60 seconds between a blob being uploaded and the function executing. For real-time processing, use an Event Grid trigger (which is event-driven and near-instant) that subscribes to the blob storage account's BlobCreated events.

4. **Azure Functions supports custom handlers**, meaning you can write functions in any language that can listen on an HTTP port---Rust, Go, Ruby, or even Bash scripts. The Functions runtime sends trigger data to your custom handler via HTTP, and your handler sends back the response. This opens Azure Functions to languages that are not natively supported.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| Choosing Consumption plan for latency-sensitive APIs | Consumption is the default and cheapest | Use Premium or Flex Consumption for APIs where cold start latency is unacceptable. The extra cost of keeping 1 instance warm is usually justified. |
| Writing functions that take longer than 5 minutes on Consumption | Developers do not check the timeout limit during development | Move long-running work to Durable Functions (activity functions can run up to 5 min each, but the orchestration chains them). Or switch to Premium plan. |
| Using Blob triggers when Event Grid triggers are more appropriate | Blob trigger is the first result in documentation | Blob triggers poll (up to 60s delay). Event Grid triggers are event-driven (sub-second). Use Event Grid for time-sensitive processing. |
| Storing connection strings in Application Settings as plain text | It is the quickest way to configure bindings | Use Key Vault references: `@Microsoft.KeyVault(SecretUri=...)`. Enable managed identity on the Function App and grant it Key Vault Secrets User role. |
| Not configuring retry policies for queue/event triggers | The default retry behavior is not always appropriate | Configure `maxRetryCount` and `retryStrategy` (fixed or exponential backoff) in host.json. Without retries, transient failures cause permanent message loss. |
| Writing large, monolithic functions instead of chaining small ones | It seems simpler to put all logic in one function | Break complex workflows into small, focused functions. Use Durable Functions for orchestration. Small functions are easier to test, debug, and scale independently. |
| Not setting FUNCTIONS_WORKER_PROCESS_COUNT for CPU-intensive work | The default is 1 worker process | For Python functions (GIL limitation), increase FUNCTIONS_WORKER_PROCESS_COUNT to utilize multiple cores. Each process handles requests independently. |
| Ignoring the cold start impact of large dependency packages | Adding dependencies is easy; understanding their boot cost is not | Profile your cold start time. Remove unused packages. Use slim base images. For Python, consider using layers or pre-compiled wheels. |

---

## Quiz

<details>
<summary>1. When would you choose Azure Functions Premium plan over Consumption plan?</summary>

Choose Premium when you need any of these: no cold starts (Premium keeps instances pre-warmed), VNet integration (Consumption cannot connect to private VNets), execution times longer than 10 minutes, more memory (up to 14 GB vs 1.5 GB), or consistent performance for latency-sensitive workloads. Premium is also better when your function runs frequently enough that the per-execution cost of Consumption exceeds the per-instance cost of Premium. The break-even point is roughly 3-5 million executions per month depending on duration and memory.
</details>

<details>
<summary>2. Explain the difference between a trigger and a binding in Azure Functions.</summary>

A trigger is the event that causes a function to execute. Every function has exactly one trigger. Examples: an HTTP request, a new blob, a queue message, or a timer schedule. The trigger defines when the function runs. A binding is a declarative connection to another service for reading (input binding) or writing (output binding). Bindings are optional---you can have zero or many. They eliminate the boilerplate of initializing SDKs, authenticating, and managing connections. For example, a Cosmos DB output binding lets you write a document to Cosmos DB by simply setting a return value, without any Cosmos DB SDK code.
</details>

<details>
<summary>3. A blob trigger function processes uploaded images. You notice a 30-45 second delay between upload and processing. Why, and how would you fix it?</summary>

Blob triggers use a polling mechanism that scans the container for changes periodically. The polling interval can be up to 60 seconds, which explains the delay. To fix this, switch from a Blob trigger to an Event Grid trigger. Configure the storage account to emit BlobCreated events to Event Grid, and configure the Function to trigger on those events. Event Grid delivers events in near-real-time (typically under 1 second), eliminating the polling delay. The function code stays essentially the same---only the trigger configuration changes.
</details>

<details>
<summary>4. What problem do Durable Functions solve that regular Azure Functions cannot?</summary>

Regular Azure Functions are stateless and short-lived. They cannot maintain state between executions, coordinate multiple steps, or wait for external events. Durable Functions add stateful orchestration, enabling patterns like function chaining (sequential steps), fan-out/fan-in (parallel processing), async HTTP APIs (long-running operations with status polling), human interaction (wait for approval), and aggregation (collect events over time). The orchestrator function maintains state in Azure Storage, so it can be suspended and resumed without consuming compute. This enables workflows that span minutes, hours, or even weeks.
</details>

<details>
<summary>5. How does Azure Functions handle scaling differently on the Consumption plan vs. Premium plan?</summary>

On Consumption, Azure manages all scaling automatically. When events arrive (queue messages, HTTP requests), Azure allocates workers and scales out to handle them. It can scale from 0 to 200 instances. You have no control over the scaling behavior. On Premium, you set a minimum number of always-warm instances (typically 1) and a maximum burst count. Azure pre-warms instances to avoid cold starts and scales within your configured bounds. Premium scaling is faster because instances are already provisioned, while Consumption requires allocating new workers from a shared pool.
</details>

<details>
<summary>6. You have a function that processes orders and needs to: validate the order, charge the credit card, update inventory, and send a confirmation email. How would you architect this with Azure Functions?</summary>

Use a Durable Functions orchestrator with four activity functions. The orchestrator function calls each activity sequentially: validate_order, charge_card, update_inventory, send_email. If any step fails, the orchestrator can implement compensation logic (e.g., if update_inventory fails after charge_card succeeds, call a refund_card activity). The orchestrator maintains the workflow state, so if a failure occurs mid-workflow, it can resume from where it left off after the issue is fixed. Each activity function is independently scalable and testable. Using Durable Functions instead of chaining via queues gives you a single, readable workflow definition instead of scattered trigger-based functions.
</details>

---

## Hands-On Exercise: Blob Trigger to Process and Store in Cosmos DB

In this exercise, you will create an Azure Function triggered by blob uploads that processes the file metadata and stores the result in Cosmos DB via an output binding.

**Prerequisites**: Azure CLI, Azure Functions Core Tools (`func`), Python 3.11+.

### Task 1: Create Infrastructure

```bash
RG="kubedojo-functions-lab"
LOCATION="eastus2"
STORAGE_NAME="kubedojofunc$(openssl rand -hex 4)"
FUNC_NAME="kubedojofunc$(openssl rand -hex 4)"
COSMOS_NAME="kubedojocosmos$(openssl rand -hex 4)"

az group create --name "$RG" --location "$LOCATION"

# Create storage account for the Function App
az storage account create \
  --name "$STORAGE_NAME" \
  --resource-group "$RG" \
  --location "$LOCATION" \
  --sku Standard_LRS

# Create a blob container for uploads
az storage container create \
  --name "uploads" \
  --account-name "$STORAGE_NAME"

# Create Cosmos DB account
az cosmosdb create \
  --name "$COSMOS_NAME" \
  --resource-group "$RG" \
  --kind GlobalDocumentDB \
  --default-consistency-level Session \
  --locations regionName="$LOCATION" failoverPriority=0

# Create Cosmos DB database and container
az cosmosdb sql database create \
  --account-name "$COSMOS_NAME" \
  --resource-group "$RG" \
  --name "ProcessingDB"

az cosmosdb sql container create \
  --account-name "$COSMOS_NAME" \
  --resource-group "$RG" \
  --database-name "ProcessingDB" \
  --name "results" \
  --partition-key-path "/blobName"
```

<details>
<summary>Verify Task 1</summary>

```bash
az cosmosdb sql container show \
  --account-name "$COSMOS_NAME" -g "$RG" \
  --database-name "ProcessingDB" --name "results" \
  --query '{Name:name, PartitionKey:resource.partitionKey.paths[0]}' -o table
```
</details>

### Task 2: Create the Function App

```bash
# Create a Consumption plan Function App
az functionapp create \
  --resource-group "$RG" \
  --consumption-plan-location "$LOCATION" \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name "$FUNC_NAME" \
  --storage-account "$STORAGE_NAME"

# Get connection strings
STORAGE_CONN=$(az storage account show-connection-string \
  -n "$STORAGE_NAME" -g "$RG" --query connectionString -o tsv)
COSMOS_CONN=$(az cosmosdb keys list \
  --name "$COSMOS_NAME" -g "$RG" --type connection-strings \
  --query 'connectionStrings[0].connectionString' -o tsv)

# Configure app settings
az functionapp config appsettings set \
  --resource-group "$RG" \
  --name "$FUNC_NAME" \
  --settings \
    "StorageConnection=$STORAGE_CONN" \
    "CosmosDBConnection=$COSMOS_CONN"
```

<details>
<summary>Verify Task 2</summary>

```bash
az functionapp show -g "$RG" -n "$FUNC_NAME" \
  --query '{Name:name, State:state, Runtime:siteConfig.linuxFxVersion}' -o table
```
</details>

### Task 3: Write the Function Code

```bash
# Create project directory
mkdir -p /tmp/functions-lab && cd /tmp/functions-lab

# Initialize the project
func init --python --model V2
```

Now create the function code:

```bash
cat > /tmp/functions-lab/function_app.py << 'PYEOF'
import azure.functions as func
import json
import uuid
import logging
from datetime import datetime

app = func.FunctionApp()

@app.blob_trigger(
    arg_name="inputBlob",
    path="uploads/{name}",
    connection="StorageConnection"
)
@app.cosmos_db_output(
    arg_name="outputDocument",
    database_name="ProcessingDB",
    container_name="results",
    connection="CosmosDBConnection"
)
def process_upload(inputBlob: func.InputStream, outputDocument: func.Out[func.Document]):
    """Process uploaded blobs and store metadata in Cosmos DB."""

    blob_name = inputBlob.name
    blob_size = inputBlob.length
    content = inputBlob.read()

    logging.info(f"Processing blob: {blob_name}, Size: {blob_size} bytes")

    # Determine content type based on extension
    extension = blob_name.rsplit(".", 1)[-1].lower() if "." in blob_name else "unknown"
    content_types = {
        "json": "application/json",
        "csv": "text/csv",
        "txt": "text/plain",
        "jpg": "image/jpeg",
        "png": "image/png",
        "pdf": "application/pdf"
    }

    # Build the metadata document
    result = {
        "id": str(uuid.uuid4()),
        "blobName": blob_name.split("/")[-1],
        "fullPath": blob_name,
        "sizeBytes": blob_size,
        "extension": extension,
        "contentType": content_types.get(extension, "application/octet-stream"),
        "processedAt": datetime.utcnow().isoformat() + "Z",
        "status": "processed"
    }

    # If it is a JSON file, count the records
    if extension == "json":
        try:
            data = json.loads(content)
            if isinstance(data, list):
                result["recordCount"] = len(data)
            result["status"] = "processed_with_analysis"
        except json.JSONDecodeError:
            result["status"] = "invalid_json"

    # Write to Cosmos DB via output binding
    outputDocument.set(func.Document.from_dict(result))
    logging.info(f"Stored metadata for {blob_name} in Cosmos DB with id {result['id']}")
PYEOF

# Update requirements.txt
cat > /tmp/functions-lab/requirements.txt << 'EOF'
azure-functions
azure-cosmos
EOF
```

<details>
<summary>Verify Task 3</summary>

```bash
ls -la /tmp/functions-lab/function_app.py
cat /tmp/functions-lab/requirements.txt
```

You should see the function_app.py file and requirements.txt.
</details>

### Task 4: Deploy the Function

```bash
cd /tmp/functions-lab
func azure functionapp publish "$FUNC_NAME"
```

<details>
<summary>Verify Task 4</summary>

```bash
az functionapp function list -g "$RG" -n "$FUNC_NAME" \
  --query '[].{Name:name, Trigger:config.bindings[0].type}' -o table
```

You should see the `process_upload` function with a `blobTrigger`.
</details>

### Task 5: Test the Function by Uploading Blobs

```bash
# Upload a JSON file
echo '[{"user": "alice", "action": "login"}, {"user": "bob", "action": "purchase"}]' > /tmp/test-data.json
az storage blob upload \
  --container-name "uploads" \
  --file /tmp/test-data.json \
  --name "test-data.json" \
  --account-name "$STORAGE_NAME" \
  --connection-string "$STORAGE_CONN"

# Upload a text file
echo "Hello from KubeDojo Functions lab" > /tmp/readme.txt
az storage blob upload \
  --container-name "uploads" \
  --file /tmp/readme.txt \
  --name "readme.txt" \
  --account-name "$STORAGE_NAME" \
  --connection-string "$STORAGE_CONN"

# Wait for processing (blob trigger polling delay)
echo "Waiting 60 seconds for blob trigger to process..."
sleep 60

# Check function execution logs
az functionapp log tail -g "$RG" -n "$FUNC_NAME" --timeout 10 2>/dev/null || \
  echo "Check logs in the Azure portal: Function App > Functions > process_upload > Monitor"
```

<details>
<summary>Verify Task 5</summary>

```bash
# Query Cosmos DB for the processed results
az cosmosdb sql query \
  --account-name "$COSMOS_NAME" \
  --resource-group "$RG" \
  --database-name "ProcessingDB" \
  --container-name "results" \
  --query-text "SELECT c.blobName, c.sizeBytes, c.extension, c.status, c.processedAt FROM c" \
  -o table 2>/dev/null || \
az cosmosdb sql container show \
  --account-name "$COSMOS_NAME" -g "$RG" \
  --database-name "ProcessingDB" --name "results" \
  --query resource.id -o tsv
```

You should see two documents in Cosmos DB: one for test-data.json (with recordCount=2 and status=processed_with_analysis) and one for readme.txt (with status=processed).
</details>

### Cleanup

```bash
az group delete --name "$RG" --yes --no-wait
rm -rf /tmp/functions-lab /tmp/test-data.json /tmp/readme.txt
```

### Success Criteria

- [ ] Storage account with uploads container created
- [ ] Cosmos DB account with ProcessingDB database and results container created
- [ ] Function App deployed with blob trigger and Cosmos DB output binding
- [ ] JSON file uploaded and processed (metadata stored in Cosmos DB with record count)
- [ ] Text file uploaded and processed (metadata stored in Cosmos DB)
- [ ] Function execution visible in logs or monitor

---

## Next Module

[Module 3.9: Azure Key Vault](module-3.9-key-vault/) --- Learn how to securely manage secrets, encryption keys, and certificates with Azure Key Vault, and integrate it with your applications using Managed Identities.
