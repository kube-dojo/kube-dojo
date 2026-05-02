---
revision_pending: false
title: "Module 7.8: SST - The Modern Serverless Framework"
slug: platform/toolkits/infrastructure-networking/iac-tools/module-7.8-sst
sidebar:
  order: 9
---

# Module 7.8: SST - The Modern Serverless Framework

## Complexity: [MEDIUM]

## Time to Complete: 45-50 minutes

## Prerequisites

Before starting this module, you should have completed:

- [Module 7.1: Terraform](../module-7.1-terraform/) - Infrastructure as Code basics
- [Module 7.5: CloudFormation](../module-7.5-cloudformation/) - AWS-native IaC
- JavaScript/TypeScript fundamentals
- AWS account with CLI configured
- Understanding of serverless concepts such as Lambda and API Gateway

If you later connect SST-managed outputs to Kubernetes workloads, assume Kubernetes 1.35 or newer and introduce the shortcut with `alias k=kubectl` before showing learners the `k` command form. SST itself does not require Kubernetes for the exercises in this module, but platform teams often bridge the two worlds when a serverless control plane calls services that still run on clusters.

## Learning Outcomes

After completing this module, you will be able to:

- **Design SST APIs** that combine API Gateway routes, Lambda handlers, DynamoDB tables, and frontend hosting without hand-written IAM policies.
- **Implement resource binding** so application code receives table names, URLs, and permissions through SST instead of fragile environment strings.
- **Debug live Lambda development** by predicting how requests move through the SST stub, local code, WebSocket tunnel, and real AWS services.
- **Evaluate SST tradeoffs** against raw CDK, Serverless Framework, LocalStack, and Kubernetes-first delivery for team workflows and production risk.

## Why This Module Matters

A payments team at a growing fintech had a problem that looked like a productivity annoyance until finance translated it into money. Engineers were waiting through CloudFormation updates to test small Lambda changes, and each loop pulled them out of the debugging context just long enough to miss the next clue. The daily waste was not one dramatic outage; it was a quiet tax paid in five-minute chunks, spread across dozens of deploys and several expensive engineers.

The worst incident started with a typo in a Lambda environment variable. The team could not reproduce the failure locally because their emulator accepted a configuration shape that API Gateway and DynamoDB in AWS rejected under the real IAM policy. By the time they had added logging, redeployed, waited for CloudWatch, and repeated the loop, a small defect had consumed most of an afternoon and delayed a customer-facing release that carried real revenue pressure.

SST matters because it attacks that loop directly. It treats infrastructure and application code as one TypeScript-defined system, gives functions real cloud resources during development, and removes much of the glue work that usually lives in YAML, IAM snippets, and environment variable conventions. This module teaches SST as an operating model, not as a shortcut command: you will design a small API, reason about live Lambda development, use binding to reduce configuration drift, and decide when SST is the right tool instead of forcing it into every platform problem.

The lead developer opened a new Serverless Framework project. For a simple REST API with authentication, he needed a large configuration file before any business logic existed, and the team still had to understand CloudFormation references, API Gateway events, IAM actions, and Lambda handler conventions at the same time.

```yaml
# serverless.yml - 150+ lines just to start
service: my-api
frameworkVersion: '3'
provider:
  name: aws
  runtime: nodejs18.x
  environment:
    TABLE_NAME: !Ref UsersTable
  iam:
    role:
      statements:
        - Effect: Allow
          Action:
            - dynamodb:Query
            - dynamodb:Scan
            - dynamodb:GetItem
            - dynamodb:PutItem
          Resource: !GetAtt UsersTable.Arn

functions:
  api:
    handler: handler.main
    events:
      - http:
          path: /{proxy+}
          method: any
          authorizer:
            name: authorizer
            type: TOKEN
            # ...another 20 lines

resources:
  Resources:
    UsersTable:
      Type: AWS::DynamoDB::Table
      # ...another 30 lines
```

The pain in that file is not that YAML is bad by itself. The pain is that intent is scattered across several abstraction layers, so a reader must mentally join the table reference, Lambda environment, IAM policy, API event, and handler code before they can answer a simple question: can this route write a user record safely? SST’s promise is to move that intent into code that can be typed, refactored, reviewed, and executed in a development loop that uses real AWS behavior.

SST changes this completely in the preserved v2-style construct example below. Current SST v3 applications express the same idea with the component and linking APIs, while many existing projects still contain `Api`, `Table`, and `bind()` code like this. Read the example for the shape of the design: infrastructure resources are declared beside routes, and the relationship between a route and its table is explicit instead of hidden in a detached policy block.

```typescript
// sst.config.ts
export default {
  config(_input) {
    return { name: "my-api", region: "us-east-1" };
  },
  stacks(app) {
    app.stack(function API({ stack }) {
      const table = new Table(stack, "users", {
        fields: { userId: "string" },
        primaryIndex: { partitionKey: "userId" },
      });

      const api = new Api(stack, "api", {
        routes: {
          "GET /users/{id}": "packages/functions/src/get.handler",
          "POST /users": "packages/functions/src/create.handler",
        },
      });

      api.bind([table]); // Automatic IAM permissions!

      stack.addOutputs({ ApiEndpoint: api.url });
    });
  },
};
```

```bash
npx sst dev  # Live Lambda development in 10 seconds
```

The point is not that SST makes distributed systems simple. API Gateway can still reject malformed routes, DynamoDB can still throttle poorly designed keys, and Lambda can still hide latency behind cold starts. The point is that the feedback loop becomes honest: a request can travel through real AWS entry points while your handler code reloads locally, so the team sees integration defects before a production deployment becomes the first realistic test.

Version awareness matters because SST’s public API has evolved. The examples preserved in this module use the familiar v2 construct style, including `Api`, `Table`, `NextjsSite`, and `bind()`, because many production codebases still use that shape and learners will encounter it during migrations. Newer SST v3 projects use a different component model and resource linking vocabulary, but the architectural ideas remain recognizable: define the app in code, connect resources to compute intentionally, and use the CLI to run a development workflow that reflects the deployed system.

That distinction is important during evaluation. A team should not copy a v2 construct example into a v3 project and expect every import to compile unchanged, but they also should not miss the transferable lesson because the syntax changed. The durable lesson is that SST tries to collapse the distance between infrastructure declarations and application runtime access. When reviewing an SST app, ask whether the resource relationship is visible, typed, stage-aware, and easy to test under realistic cloud behavior.

The migration conversation should start with inventory rather than enthusiasm. List the current serverless entry points, the resources they touch, the deployment time for common changes, the number of hand-written policies, and the places where local behavior differs from AWS. If those pain points are concentrated around Lambda, API Gateway, DynamoDB, queues, buckets, and frontend deployment, SST has a strong case. If the pain is mostly about cluster lifecycle, long-running services, or organization-wide account vending, SST may be only a small part of the answer.

The strongest teams document both the syntax version and the operating principle in their internal examples. A template can say, “This sample uses the current SST component API; older services may use construct imports and `bind()` for the same dependency pattern.” That single sentence saves future reviewers from treating a version mismatch as an architecture debate, and it keeps the team focused on the actual questions: what resource exists, who can use it, how is it deployed, and how do we debug it when the edge behavior is surprising?

## SST's Operating Model

SST is best understood as an application framework wrapped around infrastructure as code. Traditional IaC starts with resources, then asks application developers to consume outputs through naming conventions, environment variables, or generated deployment artifacts. SST starts with the full application boundary: routes, functions, queues, tables, buckets, scheduled jobs, and frontends are all parts of one app definition, so the framework can infer permissions, inject metadata, and run a development environment that mirrors production relationships.

The architecture diagram from the original module captures the core split. In development, SST deploys enough real AWS infrastructure to receive events, then forwards invocations to code on your machine. In production, SST performs a normal deployment of cloud resources and packaged functions. The same routes and resource relationships exist in both paths, which is why debugging a live development request teaches you something useful about the deployed system.

```
SST ARCHITECTURE
─────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────┐
│                      SST CLI                                    │
│                                                                  │
│  sst dev      │  sst deploy    │  sst remove   │  sst console  │
└────────┬────────────────┬─────────────────────────────────────────┘
         │                │
         │ Development    │ Production
         ▼                ▼
┌─────────────────┐   ┌─────────────────┐
│  LIVE LAMBDA    │   │  STANDARD       │
│  DEVELOPMENT    │   │  DEPLOYMENT     │
│                 │   │                 │
│ ┌─────────────┐ │   │  ┌───────────┐ │
│ │ Local Code  │ │   │  │ Pulumi/TF │ │
│ │ ─────────── │ │   │  │ Engine    │ │
│ │ WebSocket   │ │   │  └─────┬─────┘ │
│ │ Tunnel      │ │   │        │       │
│ └──────┬──────┘ │   │        ▼       │
│        │        │   │  ┌───────────┐ │
│        ▼        │   │  │ AWS       │ │
│ ┌─────────────┐ │   │  │ Resources │ │
│ │ Lambda Stub │ │   │  │           │ │
│ │ (in AWS)    │ │   │  │ Lambda    │ │
│ │             │ │   │  │ DynamoDB  │ │
│ │ Forwards to │ │   │  │ S3, etc   │ │
│ │ local code  │ │   │  └───────────┘ │
│ └─────────────┘ │   │                 │
└─────────────────┘   └─────────────────┘

LIVE LAMBDA DEV FLOW:
─────────────────────────────────────────────────────────────────

1. Request hits API Gateway / Lambda trigger
2. SST's stub Lambda receives event
3. Event sent via WebSocket to your machine
4. Local code executes
5. Response sent back via WebSocket
6. Lambda returns response to caller

= Real AWS context + local development speed
```

Notice the practical tradeoff hidden inside that flow. The developer experience is much faster because handler code runs locally, yet the request still depends on an AWS account, deployed resources, network connectivity, and a live tunnel. That means `sst dev` is not a replacement for unit tests, and it is not the right inner loop for every pure function. It is the right loop when the bug is likely to live in the boundary between application code and cloud services.

Pause and predict: if the local laptop goes offline while API Gateway is still sending traffic to the development stub, which part of the path keeps working and which part fails? The API endpoint can still exist because it is real AWS infrastructure, but the invocation path that depends on the tunnel to your machine will fail or time out. That prediction matters because it reminds you not to share personal development endpoints as stable integration environments.

For platform engineers, SST’s operating model also changes the ownership conversation. A central platform team can provide templates, guardrails, CI/CD conventions, and shared observability, while product engineers still own route-level application behavior in TypeScript. The right boundary is not “platform writes all infrastructure” or “application teams write everything”; the right boundary is a reviewed app definition that makes dependencies visible enough for both groups to reason about risk.

## Designing SST APIs and Resource Binding

The smallest useful SST application usually combines an HTTP route, a Lambda handler, and a stateful resource. Without a framework, the route must know how to invoke the function, the function must know the table name, and the role must know which table actions are allowed. Those are three opportunities for drift. SST’s binding or linking system exists because teams repeatedly made mistakes when they copied a table name into an environment variable but forgot to update the IAM policy or the runtime type.

The older `bind()` examples in this module and the current resource linking model both solve the same class of problem. A resource is declared once, attached to the compute that needs it, and exposed to code through generated metadata. That does not remove the need to design the table correctly, but it removes a surprising amount of accidental complexity around how the function discovers and is allowed to use the table.

```
SST BINDING SYSTEM
─────────────────────────────────────────────────────────────────

TRADITIONAL (Environment Variables):
─────────────────────────────────────────────────────────────────
// Infrastructure
environment: {
  TABLE_NAME: table.tableName,
  BUCKET_NAME: bucket.bucketName,
  QUEUE_URL: queue.queueUrl,
}

// Application
const tableName = process.env.TABLE_NAME!;  // String, no type safety
const client = new DynamoDBClient({});
// Have to know the API yourself

SST BINDING:
─────────────────────────────────────────────────────────────────
// Infrastructure
api.bind([table, bucket, queue]);

// Application
import { Table, Bucket, Queue } from "sst/node/table";

const users = Table.users;  // Typed!
// users.tableName available
// SST generates typed SDK

const result = await users.put({  // Type-safe operations
  userId: "123",
  name: "Alice"
});

WHAT BINDING DOES:
─────────────────────────────────────────────────────────────────
1. Generates IAM permissions automatically
2. Injects resource metadata (ARN, name, URL)
3. Creates type definitions for your IDE
4. Works identically in dev and prod
```

The important design habit is to bind only the resources a route needs. If every function receives every table, bucket, and queue because it is convenient during development, the app slowly recreates the same broad-permission problem that IaC was supposed to prevent. Binding is powerful because it narrows intent: this handler reads from the notes table, that worker consumes the resize queue, and the frontend receives only the public API URL it needs for server-side rendering.

TypeScript adds value here because it turns some infrastructure mistakes into editor feedback instead of deployment feedback. A misspelled resource variable in YAML can survive until the framework renders a template or the function starts without the expected value. In code, an undefined variable or mismatched construct is easier for the compiler and IDE to catch before a cloud deployment begins. Type safety does not prove the architecture is correct, but it removes a class of avoidable spelling and refactoring errors from the critical path.

```typescript
// YAML: deploys, fails at runtime
// environment:
//   TBALE_NAME: !Ref NotesTable  # Typo not caught

// TypeScript: immediate red squiggle
api.bind([tabel]);  // Error: 'tabel' is not defined
```

The example is intentionally small, because the effect compounds with codebase size. A rename that touches a table, several handlers, a frontend server component, and a background worker is exactly where stringly typed infrastructure conventions become expensive. When resource access is represented in generated types and imported symbols, the development environment can help locate broken references during the edit, not after a failed deploy or a production error.

Binding also changes how teams talk about least privilege. Instead of starting with an IAM JSON document and asking whether the actions look reasonable, a reviewer can start with the application relationship and ask whether that relationship is too broad. This is a healthier conversation for product teams because it connects permission review to feature behavior: the create-note route needs write access, the list route may need query access, and the stats route may need read-only access to a different projection or table.

The basic API example keeps the table and routes close enough that a reviewer can follow the security shape without opening several files. The table’s partition key tells you the access pattern, the route map tells you the HTTP surface, and `api.bind([table])` tells you every route in that API can access the table. That last point is useful, but it is also a reason to split APIs or bind at a narrower level in larger systems.

```bash
# Create new SST project
npx create-sst@latest my-app
cd my-app

# Project structure:
# ├── sst.config.ts      # SST configuration
# ├── packages/
# │   ├── functions/     # Lambda functions
# │   └── core/          # Shared code
# └── package.json

# Install dependencies
npm install

# Start development mode
npx sst dev
```

Before running this, what output do you expect from the first successful deployment? You should expect SST to create or update cloud resources, print the API endpoint, and keep a local process alive for live function execution. If the command instead exits immediately, check AWS credentials, region selection, dependency installation, and whether the project template matches the SST major version you intended to use.

```typescript
// sst.config.ts
import { Api, Table } from "sst/constructs";

export default {
  config(_input) {
    return {
      name: "my-api",
      region: "us-east-1",
    };
  },
  stacks(app) {
    app.stack(function APIStack({ stack }) {
      // Create DynamoDB table
      const table = new Table(stack, "Notes", {
        fields: {
          userId: "string",
          noteId: "string",
        },
        primaryIndex: { partitionKey: "userId", sortKey: "noteId" },
      });

      // Create API with routes
      const api = new Api(stack, "Api", {
        routes: {
          "GET /notes": "packages/functions/src/list.handler",
          "GET /notes/{id}": "packages/functions/src/get.handler",
          "POST /notes": "packages/functions/src/create.handler",
          "DELETE /notes/{id}": "packages/functions/src/delete.handler",
        },
      });

      // Bind table to all API routes
      api.bind([table]);

      // Output the API endpoint
      stack.addOutputs({
        ApiEndpoint: api.url,
      });
    });
  },
};
```

The table design in that example is intentionally simple, but the operational lesson is deeper than “write this config.” The partition key makes every note belong to a user, and the sort key makes individual notes addressable under that user. If the team later adds collaboration, sharing, or search, the table model must be revisited rather than hidden behind the convenience of a generated binding. SST can wire a resource correctly; it cannot rescue a data model that does not match the product’s queries.

The handler below shows the payoff of binding from the application side. The code imports a typed resource object instead of trusting a string from `process.env`, then sends a normal DynamoDB command. You still need input validation, authentication, authorization, and error handling in production, but the handler no longer carries an extra burden of discovering its infrastructure by convention.

```typescript
// packages/functions/src/create.ts
import { Table } from "sst/node/table";
import { APIGatewayProxyHandlerV2 } from "aws-lambda";
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { PutCommand, DynamoDBDocumentClient } from "@aws-sdk/lib-dynamodb";
import { randomUUID } from "crypto";

const client = DynamoDBDocumentClient.from(new DynamoDBClient({}));

export const handler: APIGatewayProxyHandlerV2 = async (event) => {
  const data = JSON.parse(event.body || "{}");

  const params = {
    TableName: Table.Notes.tableName, // Type-safe!
    Item: {
      userId: "user-123", // Would come from auth
      noteId: randomUUID(),
      content: data.content,
      createdAt: Date.now(),
    },
  };

  await client.send(new PutCommand(params));

  return {
    statusCode: 201,
    body: JSON.stringify(params.Item),
  };
};
```

A full-stack SST app extends the same relationship to frontend deployment. The frontend does not need to know how API Gateway was created; it needs a stable URL exposed by the app definition. That is a valuable boundary because frontend teams can consume an output that moves across stages, while infrastructure reviewers still see the route map, table, and site relationship in one place.

```typescript
// sst.config.ts with Next.js frontend
import { Api, Table, NextjsSite } from "sst/constructs";

export default {
  config(_input) {
    return { name: "fullstack-app", region: "us-east-1" };
  },
  stacks(app) {
    app.stack(function FullStack({ stack }) {
      const table = new Table(stack, "Data", {
        fields: { pk: "string", sk: "string" },
        primaryIndex: { partitionKey: "pk", sortKey: "sk" },
      });

      const api = new Api(stack, "Api", {
        routes: {
          "GET /items": "packages/functions/src/list.handler",
          "POST /items": "packages/functions/src/create.handler",
        },
      });

      api.bind([table]);

      // Next.js frontend
      const site = new NextjsSite(stack, "Site", {
        path: "packages/web",
        environment: {
          NEXT_PUBLIC_API_URL: api.url,
        },
      });

      stack.addOutputs({
        ApiEndpoint: api.url,
        SiteUrl: site.url,
      });
    });
  },
};
```

There is one subtle security distinction in the frontend example. A public client-side variable is not a secret; it is a published address. That is fine for an API URL, but it would be wrong for credentials, private table names that imply tenant data, or operational tokens. SST’s generated links help with server-side access, yet browser-exposed values still need the same threat modeling you would apply in any web application.

For multi-tenant products, the app definition should make tenant isolation easier to explain rather than harder. SST can help by making the resources and stages visible, but it does not decide whether tenants share a table, use a tenant key prefix, receive separate accounts, or require per-tenant encryption boundaries. The correct decision depends on regulatory requirements, blast radius, expected tenant count, and operational cost. Keep that decision in architecture notes beside the SST app, because future route additions will inherit the isolation assumptions you choose now.

For event-driven products, apply the same reasoning to queues and background workers. A queue consumer that processes billing events should not automatically inherit access to upload buckets or user-profile tables because they happen to live in the same app. When teams split dependencies by workflow, the app definition becomes a map of business processes. That map is useful during incident response because responders can see which function can produce or consume a given side effect.

## Debugging Live Lambda Development

Live Lambda development is the feature that most teams notice first because it changes the emotional texture of debugging. Instead of deploying, waiting, invoking, scanning delayed logs, and repeating, you keep a local process running while AWS events reach your code. The result feels like ordinary application development, but the context is still the cloud: IAM is real, API Gateway events are real, and DynamoDB responses are real.

```bash
# Start live development
npx sst dev

# Output:
# ✓ Deployed:
#   API: https://xxxx.execute-api.us-east-1.amazonaws.com
#
# ✓ Ready for requests
# |  Outputs:
# |  ApiEndpoint: https://xxxx.execute-api.us-east-1.amazonaws.com

# Now edit packages/functions/src/create.ts
# Save the file
# Changes are instant - no redeploy needed!
```

The debugging trick is to separate infrastructure changes from code changes. Editing a handler body should be nearly instant because the local runtime can reload code. Changing a route, table schema, permission relationship, or stage-level configuration may still require an infrastructure update. Teams that understand that distinction are less likely to blame SST for a slow loop when they are actually changing the cloud shape rather than the local application behavior.

```typescript
// Set breakpoints in VS Code
// packages/functions/src/create.ts
export const handler: APIGatewayProxyHandlerV2 = async (event) => {
  debugger; // Hit this breakpoint!

  const data = JSON.parse(event.body || "{}");
  // Step through code with full AWS context
  // Real DynamoDB, real S3, real everything
};
```

```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug SST",
      "type": "node",
      "request": "launch",
      "runtimeExecutable": "${workspaceRoot}/node_modules/.bin/sst",
      "runtimeArgs": ["dev"],
      "console": "integratedTerminal",
      "skipFiles": ["<node_internals>/**"],
      "env": {
        "AWS_PROFILE": "your-profile"
      }
    }
  ]
}
```

Which approach would you choose here and why: a unit test, a mocked LocalStack run, or `sst dev` against real AWS? For pure validation logic, the unit test is faster and cheaper. For API Gateway event shape, IAM permission, DynamoDB condition expression, or route integration behavior, `sst dev` gives a more faithful signal because the bug often lives in the boundary between your code and AWS.

The preserved war story below is deliberately financial because platform decisions compete for time and attention. Even if your exact numbers differ, the categories are familiar: deploy wait time, incident cost, emulator maintenance, and developer confidence. A framework migration is not justified because a tool is fashionable; it is justified when the team can show a smaller feedback loop, fewer integration surprises, and clearer ownership of production behavior.

```
TYPICAL BUG FIX CYCLE (BEFORE SST):
─────────────────────────────────────────────────────────────────

T+0:00  Discover bug in production
T+0:05  Reproduce locally (fail - LocalStack doesn't match)
T+0:15  Add logging, deploy to dev (5 min wait)
T+0:20  Trigger bug, check CloudWatch logs (2 min lag)
T+0:25  Find issue in DynamoDB query
T+0:30  Fix code, deploy again (5 min wait)
T+0:35  Test fix, discover another issue
T+0:40  Fix, deploy again (5 min wait)
T+0:45  Test passes
T+0:50  Deploy to staging (5 min wait)
T+0:55  Run integration tests (5 min)
T+1:00  Deploy to production (5 min wait)
─────────────────────────────────────────────────────────────────
TOTAL: 1 hour for a simple bug fix
```

That timeline is not only slow; it is cognitively expensive. Every wait creates a chance to open another task, lose the exact state of the failing request, or accept a vague explanation because the cost of another experiment feels too high. Faster feedback changes behavior because engineers try smaller hypotheses, gather better evidence, and stop treating production-like testing as a scarce resource.

```
TYPICAL BUG FIX CYCLE (WITH SST):
─────────────────────────────────────────────────────────────────

T+0:00  Discover bug
T+0:02  `npx sst dev` (if not already running)
T+0:03  Reproduce locally against REAL AWS (instant)
T+0:05  Set breakpoint, step through code
T+0:08  Find issue
T+0:10  Fix code, save file (instant reload)
T+0:11  Test fix (instant)
T+0:12  Run tests
T+0:15  Deploy to staging (`npx sst deploy --stage staging`)
T+0:18  Integration tests pass
T+0:20  Deploy to production
─────────────────────────────────────────────────────────────────
TOTAL: 20 minutes, including deployment
```

The metrics table should be read as a decision model, not a universal benchmark. If your team deploys twice a day and already has excellent integration tests, SST may still help, but the financial case will be smaller. If your team is shipping dozens of serverless changes daily and spending most debugging time on integration behavior, the return can be substantial because the framework attacks the dominant delay in the workflow.

| Metric | Before (Serverless Framework) | After (SST) | Change |
|--------|-------------------------------|-------------|--------|
| Local iteration time | 5 min | 5 sec | -98% |
| Daily wait time | 60-80 min | 10-15 min | -80% |
| Bugs caught locally | 30% | 95% | +216% |
| Production incidents | 8/month | 2/month | -75% |
| Developer satisfaction | "Painful" | "Actually fun" | ∞ |

Financial models are only useful when the assumptions are visible. The table below preserves the original module’s calculation, but a real team should replace every number with local data: engineer cost, deploy count, average wait, defect rate, incident cost, and onboarding time. The exercise is valuable even if the result argues against migration, because it forces the team to describe the problem in operational terms instead of arguing about tool preference.

| Category | Before | After | Savings |
|----------|--------|-------|---------|
| Deployment wait time (25 devs × 70 min/day × $75/hr) | $657,000 | $131,000 | $526,000 |
| Production incidents (6 fewer × $15K avg) | $120,000 | $30,000 | $90,000 |
| LocalStack maintenance & debugging | $45,000 | $0 | $45,000 |
| **Total Annual Impact** | **$822,000** | **$161,000** | **$661,000** |
| Less: SST setup & training | | -$12,000 | |
| **Net Annual Savings** | | | **$649,000** |

The best debugging sessions with SST end with a better mental model, not just a fixed line of code. When you can see the request event, the linked resource metadata, the DynamoDB command, and the response in one loop, you learn how the system behaves under realistic conditions. That learning compounds across a team because fewer defects are explained as mysterious cloud behavior and more are traced to specific design choices.

## Stages, Console, and Team Workflow

Stages are SST’s answer to the question every platform team asks after the first successful demo: how do we keep development, staging, production, and temporary environments from stepping on one another? A stage names an isolated copy of the application’s resources. The same configuration can be deployed with different stage names, producing separate APIs, tables, and function names that let teams test without overwriting production state.

The important discipline is to treat stages as environments with lifecycle rules. A personal development stage can be ephemeral and cheap; a staging stage may need production-like data shape and tighter observability; a production stage needs controlled deployment, review, and rollback procedures. SST gives a convenient mechanism, but the organization still has to define who can create stages, how long preview stages live, and which secrets or permissions are allowed in each one.

The SST Console fits into that workflow as an operational lens. It can show functions, logs, invocations, and resources in a more application-centered way than jumping between AWS service pages. That does not eliminate CloudWatch, X-Ray, IAM Access Analyzer, or your normal observability stack, but it gives developers a fast place to answer the first debugging question: what happened when this route ran?

```
SST CONSOLE FEATURES
─────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────┐
│  SST Console - my-app/dev                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  FUNCTIONS                     LOGS (Real-time)                 │
│  ├── Api/GET_notes             ┌─────────────────────────────┐ │
│  │   └── 12 invocations        │ 10:23:45 START RequestId... │ │
│  ├── Api/POST_notes            │ 10:23:45 INFO  Creating...  │ │
│  │   └── 5 invocations         │ 10:23:46 INFO  Item: {...}  │ │
│  └── Api/DELETE_notes          │ 10:23:46 END   Duration...  │ │
│      └── 2 invocations         └─────────────────────────────┘ │
│                                                                  │
│  RESOURCES                     INVOCATION DETAILS              │
│  ├── Table: Notes              ┌─────────────────────────────┐ │
│  ├── Api: Api                  │ Request:                    │ │
│  └── Bucket: Uploads           │   POST /notes               │ │
│                                │   Body: {"content": "..."}  │ │
│                                │                             │ │
│                                │ Response:                   │ │
│                                │   201 Created               │ │
│                                │   {"noteId": "abc-123"}     │ │
│                                └─────────────────────────────┘ │
│                                                                  │
│  [ Invoke Function ] [ View DynamoDB ] [ Explore S3 ]          │
└─────────────────────────────────────────────────────────────────┘

Access: npx sst console (opens browser)
```

Console-driven debugging works best when paired with structured logs and consistent request identifiers. If every handler logs a tenant ID, request ID, route name, and meaningful domain event, the console becomes a fast path to understanding. If handlers log unstructured strings, sensitive data, or nothing at all, the console can only show that a function ran; it cannot create observability discipline after the fact.

SST also intersects with CI/CD differently than a purely local developer tool. Teams should use `sst dev` for development and controlled `sst deploy --stage ...` commands from CI for shared or production environments. Deploying production from a laptop makes the happy path easy and the audit path weak, because the build machine, dependency cache, credentials, and review trail become inconsistent.

```bash
npx sst dev                    # Creates 'dev' stage (default)
npx sst deploy --stage staging # Creates 'staging' stage
npx sst deploy --stage prod    # Creates 'prod' stage
```

The stage commands above are simple, but the policy around them is the real architecture. A mature team decides which stages can be created by pull requests, which require approval, which are protected by separate AWS accounts, and which are cleaned up automatically. SST gives you a naming and deployment mechanism; platform engineering turns that mechanism into a reliable operating practice.

A useful stage policy includes cost controls. Preview environments are attractive because they let reviewers test real infrastructure before merge, but they can quietly accumulate tables, logs, domains, and queues if nobody owns cleanup. The cleanup rule should be boring and automatic: close the pull request, remove the stage, and verify the deletion in CI or a scheduled janitor job. Humans are good at designing the policy; they are poor at remembering every temporary environment during a busy release week.

A useful stage policy also includes data rules. Development stages should not point at production tables simply because that is the fastest way to see realistic records. If realistic data is required, create sanitized seed data or controlled read replicas with explicit approval. SST makes it easy to create isolated resources, so use that isolation to protect customers rather than bypassing it for convenience.

Observability should be part of the stage design from the first useful deployment. Give every stage enough logging, metrics, and alarms for its purpose, but do not pretend every stage needs production paging. A personal stage may need console logs and low retention, while staging may need integration-test dashboards, and production needs alerting with ownership. The point is to make the observability tier intentional rather than accidental.

Security review becomes easier when stages, bindings, and deployment paths are described together. A reviewer can ask whether production deploys run from CI, whether production stages use separate credentials, whether preview stages expire, and whether linked resources expose secrets only to server-side code. These questions are more concrete than a generic “is the serverless app secure?” checklist, and they match the way SST applications are actually built.

## Patterns & Anti-Patterns

Use the application-boundary pattern when a feature naturally includes routes, functions, data, and a small frontend surface. Keep those resources in one SST app definition so reviewers can understand the feature as a deployed unit. This pattern scales when teams maintain clear package boundaries, avoid hidden shared globals, and split resources when permissions or release cadence start to diverge.

Use the narrow-link pattern when binding resources to functions. Attach only the table, bucket, queue, or secret that a handler needs for its job, then let generated types and permissions make that dependency explicit. The scaling benefit is review clarity: a security reviewer can tell which function can touch which data without reconstructing IAM by hand.

Use the stage-lifecycle pattern for preview environments and personal development stages. Define how stages are named, who can create them, how long they live, and which data they may access. This pattern prevents the common failure where preview environments become invisible production-like systems with stale data, broad credentials, and no owner.

Avoid the “everything bound to everything” anti-pattern. Teams fall into it because early demos are easier when every function can see every resource, but that convenience erases the main security advantage of explicit dependencies. The better alternative is to split APIs or functions by permission boundary and bind resources at the smallest useful scope.

Avoid treating `sst dev` as a complete test strategy. It is excellent for integration feedback, but it is slower and more expensive than unit tests for pure logic, and it still depends on a live cloud account. The better alternative is a layered test strategy: unit tests for deterministic logic, contract or integration tests for service boundaries, and `sst dev` for exploratory debugging against real AWS behavior.

Avoid laptop-driven production deployment. It feels efficient when the team is small, but it makes build reproducibility, credential control, and auditability worse as the product grows. The better alternative is to run production deployment from CI, keep stage-specific secrets under controlled management, and reserve local commands for personal or short-lived stages.

Avoid assuming SST is a Kubernetes replacement. SST can deploy serverless and full-stack cloud applications very effectively, and it can coexist with Kubernetes services, but a cluster-heavy platform with service meshes, long-running controllers, and custom operators may need a Kubernetes-first delivery model. The better question is whether the workload’s operational shape is event-driven and cloud-service-centric enough for SST’s strengths.

Another strong pattern is the measured-migration pattern. Start with one service whose pain is visible, whose blast radius is limited, and whose integration points match SST’s strengths. Measure deploy time, defect discovery, review clarity, and operational load before and after the migration. A small successful migration teaches the organization how to handle stages, secrets, CI deploys, and console debugging without asking every team to change their workflow at once.

Another useful anti-pattern is the framework-as-architecture shortcut. Teams sometimes adopt SST and assume the application is now well designed because the deployment experience is pleasant. That is backwards. SST can make dependencies more visible, but it cannot choose partition keys, define tenant boundaries, set retry policies, or decide how errors should be exposed to users. The better alternative is to use SST’s clarity as a review surface for those design decisions.

Treat examples as patterns, not prescriptions. The URL shortener in this module is a good teaching vehicle because it has a small route surface and an obvious table, but production URL shorteners need abuse controls, safe redirect policies, analytics retention, domain configuration, and rate limiting. A learner who copies the code without the surrounding reasoning has missed the point. A learner who can adapt the pattern to a safer product design has learned the real skill.

## Decision Framework

Choose SST when the application is AWS-first, TypeScript-friendly, and dominated by serverless or managed-service integrations. The strongest fit is a product team that owns HTTP APIs, scheduled jobs, queues, tables, buckets, and a frontend, and that loses time to slow deploy loops or configuration drift. SST’s value grows when the same people need to reason about infrastructure relationships and application code in one reviewable place.

Choose raw CDK when the organization already has deep CDK expertise, custom constructs, and a deployment pipeline that works well enough that live Lambda development is not the bottleneck. CDK can model almost any AWS architecture, but it does not automatically give the same app-centered development loop. If the team needs maximum AWS modeling flexibility and is comfortable building its own developer experience, CDK remains a strong option.

Choose Serverless Framework when the team needs a mature plugin ecosystem, broad provider familiarity, or compatibility with an existing YAML-based estate. It can still be an effective tool, especially for organizations with established conventions. The tradeoff is that large YAML configurations and hand-maintained IAM often become harder to refactor than TypeScript app definitions as the codebase grows.

Choose Kubernetes-first tooling when the workload is mostly long-running services, custom controllers, cluster networking, or multi-tenant platform primitives. SST can call Kubernetes services, and some teams use both, but the center of gravity matters. If the operational questions are pod scheduling, cluster upgrades, admission policy, and service mesh behavior, start with Kubernetes tooling and use SST only where serverless edges genuinely help.

Choose LocalStack or another emulator when offline development is essential, cloud accounts are unavailable, or cost controls make real-service development impractical. The tradeoff is fidelity: an emulator can be fast and private, but it may differ from AWS in event shape, IAM behavior, service limits, or edge cases. SST’s live model accepts cloud dependency in exchange for a more realistic signal.

The decision should end with an explicit risk statement. For example: “We will use SST for the URL shortener because API Gateway, Lambda, and DynamoDB integration is the main risk, and live development reduces that risk. We will not move the existing Kubernetes billing worker because its core complexity is long-running batch orchestration, not serverless routing.” That kind of statement prevents tool adoption from becoming a vague preference.

Evaluate team skill honestly. SST’s TypeScript-first model is a benefit when developers are comfortable reading and reviewing TypeScript, but it can create friction for teams whose infrastructure reviewers only understand declarative templates. That friction is solvable with training, templates, and examples, yet it is still a migration cost. A good adoption plan budgets time for reviewers to learn the app definition style instead of assuming the tool will explain itself.

Evaluate compliance and account boundaries early. Some organizations require strict separation between development and production accounts, controlled promotion of artifacts, or pre-approved infrastructure modules. SST can operate within disciplined workflows, but the team must design those workflows rather than relying on a developer’s local command history. The decision framework should include where state is stored, how credentials are issued, how approvals happen, and how emergency rollback works.

Evaluate exit cost with the same seriousness as adoption speed. SST uses cloud resources that can be reasoned about independently, but the app definition, linking model, and development workflow are still framework choices. If the team may need to return to raw IaC later, keep resource names, data models, and deployment ownership clean enough that migration is possible. The healthiest adoption treats SST as a productivity layer over understandable infrastructure, not as magic that nobody can inspect.

## Did You Know?

- **SST v3 moved the public mental model toward a single `sst.config.ts` app definition** — the current docs describe apps as infrastructure and application wiring defined in code, with CLI commands such as `sst dev` and `sst deploy` driving local workflow and production deployment.
- **SST resource linking generates type files** — the linking docs describe generated `sst-env.d.ts` files in the project root and near the consuming package, which is why teammates can get IDE help for linked resources instead of guessing environment variable names.
- **Live development is not pure local emulation** — SST’s workflow deploys cloud-facing pieces and runs functions live through a development loop, so it is closer to an integration environment than a mock-only test harness.
- **Stage names are architecture, not decoration** — a stage such as `dev`, `staging`, `prod`, or `pr-123` namespaces resources and should map to cleanup, data, credential, and deployment rules that the team can explain.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Not using `sst dev` | The team treats SST as only a deployment wrapper and keeps the old deploy-wait-debug loop. | Make live development the default for integration debugging, then document when unit tests or CI deploys are the better loop. |
| Manual IAM policies everywhere | Engineers are used to copying policies from CloudFormation or Serverless Framework examples. | Use binding or linking for normal resource access, and add explicit policies only when the generated relationship is too broad or too narrow. |
| Hardcoding environment values | Early prototypes often ship with copied table names, API URLs, or stage-specific constants. | Use SST outputs, config, and linked resources so stage changes do not require code edits. |
| Ignoring SST Console | Developers jump directly to CloudWatch or the AWS Console because that is the older habit. | Use SST Console for first-pass invocation debugging, then move to deeper AWS tools when you need service-level analysis. |
| Deploying production from a laptop | Small teams optimize for speed and forget reproducibility, audit trails, and credential boundaries. | Run production deploys from CI with reviewed commits, controlled credentials, and clear stage names. |
| Not typing handlers | JavaScript examples get copied without event types, so route shape mistakes appear at runtime. | Use handler types such as `APIGatewayProxyHandlerV2` and validate request bodies at the edge. |
| Skipping tests because live dev feels real | Real AWS feedback can create false confidence if pure logic and edge cases are not tested cheaply. | Keep unit tests for deterministic code, integration tests for contracts, and `sst dev` for exploratory cloud-bound debugging. |
| One giant stack | The first version is convenient, then every function receives broad permissions and every change touches the same deployment unit. | Split by permission boundary, ownership, or release cadence before the app becomes too tangled to review. |

## Quiz

<details><summary>Question 1: Your team can reproduce a payment bug only after deployment, and LocalStack accepts requests that fail through the real API Gateway route. What should you try first, and what result would prove the issue is integration-related?</summary>

Use `sst dev` against a development stage and send the failing request through the real API endpoint while the handler runs locally. If the same failure appears with the real API Gateway event, real IAM role, and real DynamoDB table, the bug is probably in the boundary between application code and AWS behavior rather than in local business logic alone. That evidence narrows the search because you can inspect the event shape, permissions, and DynamoDB command without waiting for a full redeploy after every code change. A unit test may still be needed after the fix, but it is not the first tool when the emulator is already suspect.

</details>

<details><summary>Question 2: A reviewer sees `api.bind([table])` on an API that contains public read routes and private write routes. What should they question before approving the design?</summary>

They should ask whether every route in that API really needs the table permissions created by the binding. Binding at a broad API level is convenient, but it can grant more access than a route needs, especially when public and private behavior share the same construct. The better design may split routes by permission boundary or bind resources to narrower compute units so intent remains visible. The reviewer is not rejecting binding; they are making sure the dependency is as small as the workload allows.

</details>

<details><summary>Question 3: During `sst dev`, handler edits reload quickly, but adding a new route takes noticeably longer. How do you explain the difference to a teammate?</summary>

Handler edits usually affect local application code, so SST can reload the code path without rebuilding the cloud shape. Adding a route changes infrastructure because API Gateway and the deployed development stub need to know about the new entry point. That means SST has to update real cloud resources before the route can receive traffic. The key debugging habit is to classify each change as code behavior or infrastructure shape before deciding whether the loop is unexpectedly slow.

</details>

<details><summary>Question 4: A startup wants preview environments for every pull request but has no cleanup policy. What risk does this create in an SST stage-based workflow?</summary>

Each preview stage can create its own APIs, tables, functions, and supporting resources, so unmanaged stages can become a cost, security, and data-governance problem. The risk is not that stages are bad; the risk is that they are real environments without ownership rules. A safer workflow names preview stages predictably, limits credentials and data access, and removes the stage automatically when the pull request closes. That policy turns SST stages into a controlled capability instead of a hidden fleet.

</details>

<details><summary>Question 5: Your platform team already has a strong Kubernetes delivery system and most workloads are long-running services. Where might SST still fit, and where should it not be forced?</summary>

SST may fit at serverless edges such as webhooks, lightweight APIs, scheduled jobs, or frontends that call into the platform. It should not be forced into workloads whose main complexity is pod scheduling, service mesh policy, long-running controller behavior, or cluster lifecycle management. The right decision compares workload shape rather than tool popularity. A mixed architecture can be sensible when each tool owns the part of the system it models well.

</details>

<details><summary>Question 6: A Lambda handler reads `process.env.TABLE_NAME!`, and a deploy fails because the table name changed between stages. What SST practice reduces this class of error?</summary>

Use resource binding or linking so the handler receives generated resource metadata and permissions from the app definition. That keeps the resource relationship in the infrastructure code and gives application code a typed way to access the table name. It also reduces the chance that a stage-specific name is copied into source code or missed during refactoring. The fix should include reviewing the permission boundary, not just replacing one string with another.

</details>

<details><summary>Question 7: A production deployment was run from a developer laptop and nobody can reproduce the build artifact. What process change should accompany SST adoption?</summary>

Production deployments should run from CI using reviewed commits, controlled credentials, and explicit stage names. SST makes deployment easy, but easy local deployment is not the same as reproducible production delivery. Moving production deploys to CI preserves auditability and makes dependency versions, environment variables, and credentials easier to control. Developers can still use local stages for fast feedback while shared stages follow a stricter path.

</details>

<details><summary>Question 8: A team says SST eliminates the need for tests because live development uses real AWS resources. How would you correct that claim?</summary>

Live development improves integration fidelity, but it does not replace fast deterministic tests for business logic, validation, and edge cases. Real AWS feedback is valuable when the risk lives in service integration, IAM, event shape, or deployment wiring. Unit tests are still cheaper and more precise for pure code paths, and CI tests still protect shared branches from regressions. A strong SST workflow layers these approaches instead of treating one tool as a complete quality strategy.

</details>

## Hands-On Exercise

In this exercise, you will build a URL shortener API that uses SST for an API Gateway surface, Lambda handlers, DynamoDB storage, live development, and a production-style stage deployment. The exercise preserves the original module’s code assets, so the examples use the classic SST construct imports. If you are starting a new SST v3 application, map the same architecture to current components and `link` semantics while keeping the design reasoning unchanged.

### Task: Build a URL Shortener API with SST

The goal is not only to make a short link work. The goal is to practice reading the app definition as an architecture document: the table stores URL records, the API exposes create and redirect routes, the handlers use the linked table, and the console gives you a fast debugging path. Treat each task as a chance to predict how the request will move before you run the command.

### Setup

```bash
# 1. Create project
npx create-sst@latest url-shortener
cd url-shortener
npm install
```

### Tasks

- [ ] Create the SST app definition with a `Urls` table, three API routes, and table binding for the handlers.
- [ ] Implement the shorten handler so it validates input, writes a short code to DynamoDB, and returns the public short URL.
- [ ] Implement the redirect handler so it loads the code, increments the click counter, and returns a `302` response.
- [ ] Run live development, send create and redirect requests, and inspect invocation behavior in the SST Console.
- [ ] Deploy a production stage, record the endpoint, and explain what resources are isolated from your development stage.

The app definition is the most important file to review before writing handler code. Ask yourself whether the route list, table key, and binding relationship explain the system without opening the function files. If they do, the configuration is acting as architecture rather than as a pile of deployment instructions.

```typescript
// sst.config.ts
import { Api, Table } from "sst/constructs";

export default {
  config(_input) {
    return {
      name: "url-shortener",
      region: "us-east-1",
    };
  },
  stacks(app) {
    app.stack(function URLStack({ stack }) {
      const table = new Table(stack, "Urls", {
        fields: {
          shortCode: "string",
        },
        primaryIndex: { partitionKey: "shortCode" },
      });

      const api = new Api(stack, "Api", {
        routes: {
          "POST /shorten": "packages/functions/src/shorten.handler",
          "GET /{code}": "packages/functions/src/redirect.handler",
          "GET /stats/{code}": "packages/functions/src/stats.handler",
        },
      });

      api.bind([table]);

      stack.addOutputs({
        ApiEndpoint: api.url,
      });
    });
  },
};
```

The shorten handler below deliberately keeps the input model small so you can focus on the SST relationship. In a production service, you would validate URL format, reject internal network targets, add abuse protection, and associate links with an authenticated owner. Those concerns are application security concerns; SST helps with resource access, but it does not decide which URLs your business should accept.

```typescript
// packages/functions/src/shorten.ts
import { Table } from "sst/node/table";
import { APIGatewayProxyHandlerV2 } from "aws-lambda";
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { PutCommand, DynamoDBDocumentClient } from "@aws-sdk/lib-dynamodb";
import { randomBytes } from "crypto";

const client = DynamoDBDocumentClient.from(new DynamoDBClient({}));

export const handler: APIGatewayProxyHandlerV2 = async (event) => {
  const { url } = JSON.parse(event.body || "{}");

  if (!url) {
    return {
      statusCode: 400,
      body: JSON.stringify({ error: "URL required" }),
    };
  }

  const shortCode = randomBytes(4).toString("hex");

  await client.send(
    new PutCommand({
      TableName: Table.Urls.tableName,
      Item: {
        shortCode,
        longUrl: url,
        clicks: 0,
        createdAt: Date.now(),
      },
    })
  );

  const shortUrl = `${event.requestContext.domainName}/${shortCode}`;

  return {
    statusCode: 201,
    body: JSON.stringify({
      shortCode,
      shortUrl: `https://${shortUrl}`,
    }),
  };
};
```

The redirect handler demonstrates a common serverless pattern: one request performs a read, a small state update, and a redirect response. The code is easy to follow, but it also exposes production questions you should ask during review. What happens under concurrent clicks, how will missing records be measured, and should redirects be protected from unsafe destinations?

```typescript
// packages/functions/src/redirect.ts
import { Table } from "sst/node/table";
import { APIGatewayProxyHandlerV2 } from "aws-lambda";
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import {
  GetCommand,
  UpdateCommand,
  DynamoDBDocumentClient,
} from "@aws-sdk/lib-dynamodb";

const client = DynamoDBDocumentClient.from(new DynamoDBClient({}));

export const handler: APIGatewayProxyHandlerV2 = async (event) => {
  const code = event.pathParameters?.code;

  if (!code) {
    return { statusCode: 400, body: "Code required" };
  }

  const result = await client.send(
    new GetCommand({
      TableName: Table.Urls.tableName,
      Key: { shortCode: code },
    })
  );

  if (!result.Item) {
    return { statusCode: 404, body: "Not found" };
  }

  // Increment click count
  await client.send(
    new UpdateCommand({
      TableName: Table.Urls.tableName,
      Key: { shortCode: code },
      UpdateExpression: "SET clicks = clicks + :inc",
      ExpressionAttributeValues: { ":inc": 1 },
    })
  );

  return {
    statusCode: 302,
    headers: { Location: result.Item.longUrl },
    body: "",
  };
};
```

Run the workflow slowly the first time and write down what you expect before each request. You should see the API endpoint, a successful shorten response, a redirect response, and invocation details in the console. If something fails, classify the failure first: credentials, deployment, route mapping, handler parsing, DynamoDB permission, table key, or response shape.

```bash
# 2. Start development
npx sst dev

# 3. Test the API
curl -X POST https://xxxx.execute-api.us-east-1.amazonaws.com/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/very/long/path"}'

# Response: {"shortCode": "a1b2c3d4", "shortUrl": "https://xxxx.../a1b2c3d4"}

# 4. Test redirect
curl -v https://xxxx.execute-api.us-east-1.amazonaws.com/a1b2c3d4
# Should 302 redirect to example.com

# 5. Open SST Console
npx sst console
# View invocations, logs, DynamoDB contents

# 6. Make a code change and save
# Watch instant reload in terminal

# 7. Deploy to production
npx sst deploy --stage prod
```

### Solutions

<details><summary>Solution notes for the app definition</summary>

The app definition is successful when it creates a `Urls` table with `shortCode` as the partition key, exposes `POST /shorten`, `GET /{code}`, and `GET /stats/{code}`, and binds the table to the API handlers. The important reasoning is that every handler using `Table.Urls.tableName` depends on that binding relationship. If a handler fails with a missing resource value or access denied error, inspect the binding before changing application logic. In a larger app, consider whether all three routes deserve the same table permissions.

</details>

<details><summary>Solution notes for the handlers</summary>

The shorten handler should reject an empty body, create a code, write an item with `clicks: 0`, and return a JSON response containing the short URL. The redirect handler should read by `shortCode`, return `404` when the record is absent, increment the counter, and return a `302` with a `Location` header. If the redirect works but the counter does not update, focus on the `UpdateExpression`, table key, and IAM permissions generated by the binding.

</details>

<details><summary>Solution notes for live development and stages</summary>

During `sst dev`, handler edits should reload without a full infrastructure redeploy, while route or table changes may trigger cloud updates. The console should show function invocations and logs that correspond to your curl requests. A production deployment with `--stage prod` should create resources isolated from your development stage, which means data written during development should not appear in production unless you intentionally migrate or seed it. Clean up experimental stages when they are no longer needed.

</details>

### Success Criteria

- [ ] Live development mode starts and prints an API endpoint.
- [ ] `POST /shorten` stores a record in DynamoDB and returns a short URL.
- [ ] `GET /{code}` returns a redirect for an existing code and a clear failure for a missing code.
- [ ] SST Console shows invocations, logs, and the relevant resources for the development stage.
- [ ] The production stage deploy is separate from the development stage, and you can explain which resources changed.

## Sources

- [SST Documentation](https://sst.dev/)
- [SST GitHub](https://github.com/sst/sst)
- [SST Discord](https://discord.gg/sst)
- [SST Examples](https://sst.dev/examples)
- [Ion (v3) Announcement](https://sst.dev/blog/moving-away-from-cdk)
- [SST: What is SST](https://sst.dev/docs/)
- [SST Workflow](https://sst.dev/docs/workflow/)
- [SST Resource Linking](https://sst.dev/docs/linking/)
- [SST CLI Reference](https://sst.dev/docs/reference/cli/)
- [SST ApiGatewayV2 Component](https://sst.dev/docs/component/aws/apigatewayv2/)
- [AWS Lambda with API Gateway](https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway.html)
- [Amazon API Gateway HTTP APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api.html)
- [Amazon DynamoDB Developer Guide](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html)

## Next Module

Next: [Module 7.9: System Initiative](../module-7.9-system-initiative/) — compare SST’s code-first serverless workflow with a model-driven automation platform that treats infrastructure and application relationships as an editable system graph.
