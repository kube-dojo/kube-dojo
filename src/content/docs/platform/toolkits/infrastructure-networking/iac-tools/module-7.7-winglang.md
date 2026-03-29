---
title: "Module 7.7: Wing - The Cloud-Oriented Programming Language"
slug: platform/toolkits/infrastructure-networking/iac-tools/module-7.7-winglang
sidebar:
  order: 8
---
## Complexity: [COMPLEX]
## Time to Complete: 50-55 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [Module 7.1: Terraform](module-7.1-terraform/) - Traditional IaC concepts
- [Module 7.3: Pulumi](module-7.3-pulumi/) - Programming language approach to IaC
- Programming fundamentals (any language)
- [Distributed Systems Foundation](../../../foundations/distributed-systems/) - Cloud architecture
- AWS or simulator setup for exercises

---

## Why This Module Matters

**What If Infrastructure and Application Code Were One?**

The incident post-mortem filled three pages. A fintech startup had deployed a Lambda function to production. It worked in staging. In production, it crashed immediately with "AccessDenied." The IAM policy was missing a single permission: `sqs:SendMessage`.

The root cause analysis was damning:

| Timeline | Action | Time |
|----------|--------|------|
| 9:00 AM | Engineer writes Lambda handler in TypeScript | 2 hours |
| 11:00 AM | Engineer writes Terraform for SQS, Lambda, triggers | 1.5 hours |
| 12:30 PM | Code review catches missing DynamoDB permissions | 30 min fix |
| 1:30 PM | Deploy to staging, manual testing passes | 45 min |
| 2:15 PM | Deploy to production | 10 min |
| 2:25 PM | Production crash—SQS permission missing | Downtime starts |
| 3:45 PM | Root cause found (SQS added in week 2, IAM not updated) | 80 min |
| 4:00 PM | Fix deployed | Downtime ends: **1hr 35min** |

Total incident cost: $47,000 (SLA credits + engineer time + customer churn).

The CTO called an all-hands: "We have seven files for one Lambda. Handler code in TypeScript, infrastructure in Terraform, permissions in a separate IAM file, tests mocking AWS services, CI/CD deploying in order. The IAM file has to manually track every resource the handler touches. Of course we miss things."

An engineer raised her hand: "What if the infrastructure was just part of the code? What if the compiler knew what permissions we needed?"

**Wing changes this completely.** In Wing, she wrote:

```wing
bring cloud;

let bucket = new cloud.Bucket();
let topic = new cloud.Topic();

bucket.onCreate(inflight (key: str) => {
  let content = bucket.get(key);
  let processed = processFile(content);
  topic.publish("File ${key} processed: ${processed}");
});
```

Infrastructure, permissions, event bindings, and application logic—all in one place. The compiler generates the Terraform and bundled Lambda code. The simulator runs it locally. The mental model is unified.

Wing isn't another IaC tool. It's a programming language where the cloud is the computer.

---

## Did You Know?

- **Wing raised $20M to reinvent cloud development** — Backed by Battery Ventures and prominent angels, Wing's Series A bet that cloud-native programming languages are the future. The CDK creator's credibility convinced investors that the IaC/application split costs enterprises millions annually.

- **One startup cut their serverless onboarding from 3 weeks to 2 days** — A YC company reported that new engineers could ship Lambda features in 48 hours with Wing versus 15+ days learning Terraform, IAM, CDK patterns, and testing frameworks separately. At $150K/year engineering cost, that's $5,000+ saved per hire.

- **Wing's simulator eliminates $500-2,000/month in dev AWS costs** — Developers running `wing it` instead of deploying to AWS staging accounts save substantial cloud bills. One team of 8 engineers reported their AWS dev account dropped from $2,100/month to $400/month after adopting Wing.

- **The CDK creator left AWS to build Wing** — Elad Ben-Israel led AWS CDK, which now has 10,000+ GitHub stars and billions of deployments. He saw CDK's limitations firsthand: it still requires separate application code, manual IAM, and AWS-mocked tests. Wing was his answer to "what CDK should have been."

---

## Wing Architecture

```
WING COMPILATION MODEL
─────────────────────────────────────────────────────────────────

Source Code:
┌─────────────────────────────────────────────────────────────────┐
│ bring cloud;                                                     │
│                                                                  │
│ let bucket = new cloud.Bucket();        // Preflight (infra)    │
│ let queue = new cloud.Queue();          // Preflight (infra)    │
│                                                                  │
│ queue.setConsumer(inflight (msg: str) => {  // Inflight (app)  │
│   bucket.put("processed/${msg}", processData(msg));             │
│ });                                                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                    Wing Compiler
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
        ▼                                           ▼
┌─────────────────────────┐           ┌─────────────────────────┐
│   PREFLIGHT OUTPUT       │           │   INFLIGHT OUTPUT        │
│   (Infrastructure)       │           │   (Application)          │
├─────────────────────────┤           ├─────────────────────────┤
│                          │           │                          │
│  Terraform HCL:          │           │  JavaScript bundle:      │
│  ┌────────────────────┐ │           │  ┌────────────────────┐ │
│  │resource "aws_s3_   │ │           │  │exports.handler =   │ │
│  │  bucket" "bucket"  │ │           │  │  async (event) => {│ │
│  │  {...}             │ │           │  │  // Your logic     │ │
│  │                    │ │           │  │  bucket.put(...)   │ │
│  │resource "aws_sqs_  │ │           │  │}                   │ │
│  │  queue" "queue"    │ │           │  └────────────────────┘ │
│  │  {...}             │ │           │                          │
│  │                    │ │           │  Plus: IAM permissions   │
│  │resource "aws_      │ │           │  injected as env vars    │
│  │  lambda_function"  │ │           │                          │
│  │  {...}             │ │           │                          │
│  └────────────────────┘ │           │                          │
└─────────────────────────┘           └─────────────────────────┘
```

### Preflight vs Inflight

```
THE TWO PHASES OF WING
─────────────────────────────────────────────────────────────────

PREFLIGHT (Compile Time → Infrastructure)
─────────────────────────────────────────────────────────────────
• Runs during compilation
• Creates cloud resources
• Defines topology
• Generates Terraform
• Happens ONCE at deploy time

Examples:
├── new cloud.Bucket()           // Creates S3 bucket
├── new cloud.Function(...)      // Creates Lambda
├── bucket.addObject(...)        // Adds to bucket at deploy
└── let config = getSecrets();   // Fetches build-time secrets

INFLIGHT (Runtime → Application)
─────────────────────────────────────────────────────────────────
• Runs in cloud functions
• Handles requests/events
• Business logic
• Executes MANY times at runtime

Examples:
├── bucket.put(key, value)       // Runtime S3 write
├── queue.push(message)          // Runtime SQS send
├── await fetch(url)             // Runtime HTTP call
└── let result = compute(data);  // Runtime calculation

THE BOUNDARY:
─────────────────────────────────────────────────────────────────
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  // Preflight context                                           │
│  let bucket = new cloud.Bucket();  // ✓ Creates infrastructure │
│  let name = "my-bucket";            // ✓ String available here │
│                                                                  │
│  bucket.onEvent(inflight () => {                                │
│    // Inflight context                                          │
│    bucket.put("key", "value");  // ✓ Uses bucket reference     │
│    // bucket.delete();          // ✗ Can't modify infra at runtime
│    // let b = new cloud.Bucket(); // ✗ Can't create infra     │
│  });                                                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

Compiler ERROR if you cross the boundary wrong.
```

---

## Getting Started with Wing

### Installation

```bash
# Install Wing CLI
npm install -g winglang

# Verify installation
wing --version

# Create new project
mkdir wing-demo && cd wing-demo
wing init

# Project structure:
# ├── main.w          # Main Wing file
# ├── package.json    # Dependencies
# └── target/         # Compiled output (generated)
```

### Hello Wing

```wing
// main.w
bring cloud;

// Preflight: Create a bucket
let bucket = new cloud.Bucket();

// Preflight: Create a function that uses the bucket
new cloud.Function(inflight () => {
  bucket.put("hello.txt", "Hello from Wing!");
  let content = bucket.get("hello.txt");
  log("Content: ${content}");
}) as "greeter";
```

```bash
# Run in local simulator
wing it main.w

# Open http://localhost:3000 for Wing Console
# Click "greeter" function to invoke it
# See "hello.txt" appear in the bucket

# Compile to Terraform
wing compile main.w --target tf-aws

# Output in target/main.tfaws/
# ├── main.tf.json
# ├── function/       # Bundled Lambda code
# └── ...
```

### Real Example: Image Processing Pipeline

```wing
// image-processor.w
bring cloud;
bring util;

// Infrastructure (preflight)
let uploadBucket = new cloud.Bucket() as "uploads";
let processedBucket = new cloud.Bucket() as "processed";
let notificationTopic = new cloud.Topic() as "notifications";
let processingQueue = new cloud.Queue() as "processing-queue";

// When file uploaded, queue for processing
uploadBucket.onCreate(inflight (key: str) => {
  log("New upload: ${key}");
  processingQueue.push(key);
});

// Process queued files
processingQueue.setConsumer(inflight (message: str) => {
  let key = message;
  log("Processing: ${key}");

  // Get original file
  let original = uploadBucket.get(key);

  // Simulate image processing
  let processed = processImage(original);

  // Store processed version
  let processedKey = "processed-${key}";
  processedBucket.put(processedKey, processed);

  // Notify subscribers
  notificationTopic.publish(Json.stringify({
    original: key,
    processed: processedKey,
    timestamp: util.datetime.now()
  }));

  log("Completed: ${key} -> ${processedKey}");
});

// Notification handler
notificationTopic.onMessage(inflight (message: str) => {
  let data = Json.parse(message);
  log("Image processed: ${data}");
});

// Helper function (inflight)
inflight fn processImage(content: str): str {
  // In real app: call ImageMagick, Sharp, etc.
  return "PROCESSED:${content}";
}
```

```bash
# Run locally with full simulation
wing it image-processor.w

# In Wing Console:
# 1. Upload file to "uploads" bucket
# 2. Watch message appear in "processing-queue"
# 3. See processed file in "processed" bucket
# 4. See notification in "notifications" topic

# Deploy to AWS
wing compile image-processor.w --target tf-aws
cd target/image-processor.tfaws
terraform init && terraform apply
```

---

## Wing's Standard Library

```wing
// cloud module - portable cloud resources
bring cloud;

let bucket = new cloud.Bucket();           // S3, GCS, Azure Blob
let queue = new cloud.Queue();             // SQS, Cloud Tasks, Storage Queue
let topic = new cloud.Topic();             // SNS, Pub/Sub, Service Bus
let fn = new cloud.Function(handler);      // Lambda, Cloud Functions
let api = new cloud.Api();                 // API Gateway
let counter = new cloud.Counter();         // DynamoDB, Datastore
let table = new cloud.Table(schema);       // DynamoDB, Datastore
let schedule = new cloud.Schedule();       // EventBridge, Cloud Scheduler
let secret = new cloud.Secret();           // Secrets Manager

// HTTP module
bring http;
let response = inflight http.get("https://api.example.com");

// Math module
bring math;
let random = math.random();

// Util module
bring util;
let now = util.datetime.now();
let uuid = util.uuid();

// Expect module (testing)
bring expect;
expect.equal(1 + 1, 2);
```

### Building APIs

```wing
bring cloud;
bring http;

let api = new cloud.Api();
let users = new cloud.Bucket();

api.get("/users/{id}", inflight (req: cloud.ApiRequest): cloud.ApiResponse => {
  let id = req.vars.get("id");

  try {
    let user = users.get("user-${id}");
    return cloud.ApiResponse {
      status: 200,
      body: user
    };
  } catch {
    return cloud.ApiResponse {
      status: 404,
      body: Json.stringify({ error: "User not found" })
    };
  }
});

api.post("/users", inflight (req: cloud.ApiRequest): cloud.ApiResponse => {
  let body = Json.parse(req.body ?? "{}");
  let id = util.uuid();

  users.put("user-${id}", Json.stringify(body));

  return cloud.ApiResponse {
    status: 201,
    body: Json.stringify({ id: id })
  };
});

// After deployment, api.url contains the endpoint URL
```

---

## War Story: From 6 Files to 1

*How a fintech startup reduced their serverless complexity by 85%*

### The Situation

A payments startup had a Lambda function that:
1. Received payment webhook
2. Validated signature
3. Stored in DynamoDB
4. Sent to SQS for processing
5. Published metrics to CloudWatch
6. Notified ops via SNS on errors

Their codebase:

```
payment-handler/
├── src/
│   └── handler.ts          # 150 lines
├── terraform/
│   ├── main.tf             # 200 lines
│   ├── iam.tf              # 80 lines
│   ├── variables.tf        # 40 lines
│   └── outputs.tf          # 20 lines
├── test/
│   ├── handler.test.ts     # 250 lines
│   └── mocks/              # 100 lines of AWS mocks
├── package.json
├── tsconfig.json
└── jest.config.js
─────────────────────────
Total: 850+ lines, 10 files
```

### Problems

1. **Scattered IAM** — Adding DynamoDB access meant editing `iam.tf`, forgetting meant runtime errors
2. **Test complexity** — Mocking AWS services was half their test code
3. **Deployment ordering** — Create DynamoDB before Lambda, update Lambda after
4. **Env var management** — Pass ARNs via environment variables, typos happened
5. **Local development** — Couldn't test end-to-end locally

### The Wing Rewrite

```wing
// payment-handler.w
bring cloud;
bring http;

// Infrastructure + permissions handled automatically
let payments = new cloud.Table(
  name: "payments",
  primaryKey: "id",
  columns: { status: "string", amount: "number" }
);

let processingQueue = new cloud.Queue() as "payment-processing";
let errorTopic = new cloud.Topic() as "payment-errors";
let metrics = new cloud.Counter() as "payment-count";

let api = new cloud.Api();

api.post("/webhook", inflight (req: cloud.ApiRequest): cloud.ApiResponse => {
  try {
    // Validate signature
    let signature = req.headers?.get("x-signature") ?? "";
    if !validateSignature(req.body ?? "", signature) {
      return cloud.ApiResponse { status: 401, body: "Invalid signature" };
    }

    // Parse and store
    let payment = Json.parse(req.body ?? "{}");
    let id = payment.get("id").asStr();

    payments.insert(id, {
      status: "pending",
      amount: payment.get("amount").asNum()
    });

    // Queue for processing
    processingQueue.push(id);

    // Increment metrics
    metrics.inc();

    return cloud.ApiResponse {
      status: 200,
      body: Json.stringify({ received: id })
    };
  } catch e {
    // Notify ops on error
    errorTopic.publish("Payment error: ${e}");

    return cloud.ApiResponse {
      status: 500,
      body: Json.stringify({ error: "Processing failed" })
    };
  }
});

inflight fn validateSignature(body: str, signature: str): bool {
  // Real implementation would use crypto
  return signature.length > 0;
}
```

```bash
# Test locally with full simulation
wing test payment-handler.w

# Test file (payment-handler.test.w)
bring expect;

test "processes valid payment" {
  let response = http.post(api.url + "/webhook", {
    body: Json.stringify({ id: "pay_123", amount: 100 }),
    headers: { "x-signature": "valid" }
  });

  expect.equal(response.status, 200);
  expect.ok(payments.get("pay_123") != nil);
}
```

### Results

| Metric | Before (TS+TF) | After (Wing) | Change |
|--------|----------------|--------------|--------|
| Files | 10 | 2 | -80% |
| Lines of code | 850 | 120 | -86% |
| Test setup | 100 lines | 0 (built-in) | -100% |
| Time to local test | 30s (mocks) | 5s (simulator) | -83% |
| IAM bugs/month | ~2 | 0 | -100% |
| Deploy failures | ~15% | ~2% | -87% |

### Financial Impact

| Category | Before (Annual) | After (Annual) | Savings |
|----------|-----------------|----------------|---------|
| **IAM incident cost** | $94,000 | $0 | $94,000 |
| (2 incidents × $47K each) | | | |
| **Developer time on IaC** | $78,000 | $26,000 | $52,000 |
| (3 devs × 20% time × $130K) | (3 devs × 7% time) | | |
| **AWS dev/staging costs** | $25,200 | $4,800 | $20,400 |
| (Mocking requires real AWS) | (Simulator is free) | | |
| **Deploy failure recovery** | $31,200 | $4,200 | $27,000 |
| (15% × 4 deploys/week × $100/hr) | (2% failure rate) | | |
| **Onboarding cost** | $15,000 | $5,000 | $10,000 |
| (3 weeks × 2 hires/year) | (1 week learning) | | |
| **Total First Year** | **$243,400** | **$40,000** | **$203,400** |

The CFO's summary: "We're not just saving money—we eliminated an entire category of production incidents. The $47,000 outage that started this journey? It literally cannot happen anymore. The compiler won't let it."

### Key Insight

> "Wing didn't just reduce code—it eliminated entire categories of bugs. IAM errors? Gone, the compiler generates them. Test mocks? Gone, the simulator is real. Environment variables? Gone, references are type-safe."

---

## Common Mistakes

| Mistake | Why It's Bad | Better Approach |
|---------|--------------|-----------------|
| Mixing preflight and inflight | Compiler error | Understand the boundary clearly |
| Ignoring the simulator | Missing Wing's killer feature | Use `wing it` for development |
| Fighting the abstractions | Leads to workarounds | Use `lift` for custom resources |
| Deploying without compile | Terraform fails | Always compile first |
| Not using Wing Console | Blind debugging | Console shows resource state |
| Expecting all clouds | Wing is AWS-focused | Check target platform support |
| Large inflight closures | Slow Lambda cold starts | Keep inflight code minimal |
| Skipping types | Runtime errors | Use Wing's type system |

---

## Hands-On Exercise

### Task: Build a URL Shortener in Wing

**Objective**: Create a URL shortener service that demonstrates Wing's infrastructure-as-code model.

**Success Criteria**:
1. API endpoint to create short URLs
2. Redirect endpoint that redirects to original URL
3. Counter tracking total redirects
4. All running in local simulator

### Steps

```wing
// url-shortener.w
bring cloud;
bring util;
bring http;

// Storage for URL mappings
let urls = new cloud.Bucket() as "url-store";
let counter = new cloud.Counter() as "redirect-counter";

let api = new cloud.Api() as "shortener-api";

// Create short URL
api.post("/shorten", inflight (req: cloud.ApiRequest): cloud.ApiResponse => {
  let body = Json.parse(req.body ?? "{}");
  let longUrl = body.get("url").asStr();

  // Generate short code
  let shortCode = util.uuid().substring(0, 8);

  // Store mapping
  urls.put(shortCode, longUrl);

  let shortUrl = "${api.url}/${shortCode}";

  return cloud.ApiResponse {
    status: 201,
    body: Json.stringify({
      short_url: shortUrl,
      code: shortCode
    })
  };
});

// Redirect to original URL
api.get("/{code}", inflight (req: cloud.ApiRequest): cloud.ApiResponse => {
  let code = req.vars.get("code");

  try {
    let longUrl = urls.get(code);

    // Track redirect
    counter.inc();

    return cloud.ApiResponse {
      status: 302,
      headers: { "Location": longUrl }
    };
  } catch {
    return cloud.ApiResponse {
      status: 404,
      body: "URL not found"
    };
  }
});

// Get stats
api.get("/stats", inflight (req: cloud.ApiRequest): cloud.ApiResponse => {
  let count = counter.peek();

  return cloud.ApiResponse {
    status: 200,
    body: Json.stringify({ total_redirects: count })
  };
});

// Expose for testing
pub let apiUrl = api.url;
```

```bash
# 1. Run in simulator
wing it url-shortener.w

# 2. Open Wing Console (http://localhost:3000)
# You'll see:
# - url-store bucket
# - redirect-counter counter
# - shortener-api with endpoints

# 3. Test via curl (in another terminal)
# Create short URL
curl -X POST http://localhost:XXXX/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.example.com/very/long/path"}'

# Response: {"short_url": "http://localhost:XXXX/abc12345", "code": "abc12345"}

# 4. Test redirect
curl -v http://localhost:XXXX/abc12345
# Should show 302 redirect to example.com

# 5. Check stats
curl http://localhost:XXXX/stats
# Response: {"total_redirects": 1}

# 6. Write a test
```

```wing
// url-shortener.test.w
bring expect;
bring http;
bring "./url-shortener.w" as app;

test "creates and redirects URL" {
  // Create short URL
  let createResponse = http.post("${app.apiUrl}/shorten", {
    headers: { "Content-Type": "application/json" },
    body: Json.stringify({ url: "https://example.com" })
  });

  expect.equal(createResponse.status, 201);

  let body = Json.parse(createResponse.body);
  let code = body.get("code").asStr();

  // Verify redirect
  let redirectResponse = http.get("${app.apiUrl}/${code}");
  expect.equal(redirectResponse.status, 302);
}

test "returns 404 for unknown code" {
  let response = http.get("${app.apiUrl}/nonexistent");
  expect.equal(response.status, 404);
}

test "tracks redirect count" {
  // Create and use a URL
  let createResponse = http.post("${app.apiUrl}/shorten", {
    headers: { "Content-Type": "application/json" },
    body: Json.stringify({ url: "https://example.com" })
  });

  let body = Json.parse(createResponse.body);
  let code = body.get("code").asStr();

  // Redirect 3 times
  http.get("${app.apiUrl}/${code}");
  http.get("${app.apiUrl}/${code}");
  http.get("${app.apiUrl}/${code}");

  // Check stats
  let statsResponse = http.get("${app.apiUrl}/stats");
  let stats = Json.parse(statsResponse.body);

  expect.ok(stats.get("total_redirects").asNum() >= 3);
}
```

```bash
# Run tests
wing test url-shortener.test.w

# Compile for AWS
wing compile url-shortener.w --target tf-aws

# Inspect generated Terraform
cat target/url-shortener.tfaws/main.tf.json | jq
```

---

## Quiz

### Question 1
What is the difference between preflight and inflight in Wing?

<details>
<summary>Show Answer</summary>

**Preflight runs at compile/deploy time; inflight runs at request time**

- **Preflight**: Creates infrastructure (buckets, queues, functions). Runs once during `wing compile` or `terraform apply`.
- **Inflight**: Application code that runs inside cloud functions. Runs many times in response to events.

The `inflight` keyword marks code that runs at runtime.
</details>

### Question 2
How does Wing handle IAM permissions?

<details>
<summary>Show Answer</summary>

**Automatically generated based on resource usage**

When you write `bucket.put(...)` in an inflight context, Wing:
1. Detects the bucket reference is used at runtime
2. Generates IAM policy allowing `s3:PutObject`
3. Attaches policy to the Lambda's execution role
4. Injects bucket name as environment variable

No manual IAM required—permissions flow from code.
</details>

### Question 3
What does `wing it` do?

<details>
<summary>Show Answer</summary>

**Runs your Wing application in a local simulator**

`wing it main.w` starts:
- Local simulator for all cloud resources
- Wing Console (web UI) for interaction
- Hot-reload on code changes

You can test S3, SQS, Lambda, API Gateway—all locally without AWS credentials.
</details>

### Question 4
How does Wing compare to Pulumi?

<details>
<summary>Show Answer</summary>

**Wing has a dedicated language; Pulumi uses existing languages**

| Aspect | Wing | Pulumi |
|--------|------|--------|
| Language | Wing (new) | TypeScript, Python, Go |
| Local testing | Built-in simulator | Requires mocks |
| Compile target | Terraform | Pulumi engine |
| Infra/app boundary | Language-level | Convention |
| Learning curve | New language | Existing skills |

Wing is more opinionated but provides better local development.
</details>

### Question 5
What output does `wing compile` produce?

<details>
<summary>Show Answer</summary>

**Terraform HCL + bundled application code**

For `--target tf-aws`, Wing generates:
- `main.tf.json` — Terraform configuration
- `function/` — Bundled JavaScript for Lambda
- Supporting files for providers, variables

You can run `terraform apply` on the output directly.
</details>

### Question 6
Can Wing target clouds other than AWS?

<details>
<summary>Show Answer</summary>

**Yes, but AWS is most mature**

Wing supports:
- `tf-aws` — AWS via Terraform (most complete)
- `tf-azure` — Azure via Terraform (partial)
- `tf-gcp` — GCP via Terraform (early)
- `sim` — Local simulator (full)

The `cloud.Bucket` abstraction maps to S3, Azure Blob, or GCS depending on target.
</details>

### Question 7
How do you test Wing applications?

<details>
<summary>Show Answer</summary>

**Built-in test framework with simulator**

```wing
bring expect;

test "my feature works" {
  // Runs in simulator
  let result = myFunction();
  expect.equal(result, expected);
}
```

Tests run against real (simulated) resources, not mocks. `wing test` executes all tests.
</details>

### Question 8
Who created Wing and why?

<details>
<summary>Show Answer</summary>

**Elad Ben-Israel, creator of AWS CDK**

After leading CDK at AWS, he saw limitations:
- CDK still separates infra and app code
- Testing requires mocking AWS
- Permissions are still manual
- No local simulation

Wing was designed to solve these problems with a purpose-built language where cloud is the runtime.
</details>

---

## Key Takeaways

1. **Unified model** — Infrastructure and application in one language
2. **Preflight/inflight** — Compile-time vs runtime separation
3. **Automatic IAM** — Permissions derived from code usage
4. **Local simulator** — Test full stack without cloud credentials
5. **Terraform output** — Compiles to standard Terraform
6. **Type-safe references** — Resource handles are typed
7. **Wing Console** — Visual development and debugging
8. **Testing built-in** — Real resources, not mocks
9. **Cloud-agnostic** — Abstraction layer for portability
10. **Early but promising** — AWS mature, others developing

---

## Next Steps

- **Next Module**: [Module 7.8: SST](module-7.8-sst/) — Serverless Stack
- **Related**: [Module 7.3: Pulumi](module-7.3-pulumi/) — Compare approaches
- **Related**: [Platforms Toolkit](../platforms/) — Platform abstractions

---

## Further Reading

- [Wing Documentation](https://www.winglang.io/docs)
- [Wing GitHub](https://github.com/winglang/wing)
- [Wing Playground](https://www.winglang.io/play)
- [Wing Blog](https://www.winglang.io/blog)
- [Preflight/Inflight Explained](https://www.winglang.io/docs/concepts/inflights)

---

*"Wing asks: What if the cloud was your computer? What if infrastructure was just part of your program? The answer is a language where S3 buckets and Lambda functions are first-class citizens."*
