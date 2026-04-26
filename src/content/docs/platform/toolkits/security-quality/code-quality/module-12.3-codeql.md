---
title: "Module 12.3: CodeQL - Query Your Code Like a Database"
slug: platform/toolkits/security-quality/code-quality/module-12.3-codeql
sidebar:
  order: 4
---

## Complexity: [COMPLEX]
## Time to Complete: 60-75 minutes

---

## Prerequisites

Before starting this module, you should have completed:

- [DevSecOps Discipline](/platform/disciplines/reliability-security/devsecops/) - security scanning concepts, risk triage, and shift-left practices
- [Module 11.3: GitHub Advanced](/platform/toolkits/cicd-delivery/source-control/module-11.3-github-advanced/) - GitHub Actions and GitHub Advanced Security concepts
- Programming experience in JavaScript, TypeScript, Python, Java, Go, C#, C/C++, Ruby, or Swift
- Basic familiarity with vulnerability classes such as SQL injection, command injection, XSS, insecure deserialization, and secret exposure
- Comfort reading CI workflow YAML and interpreting security scanner output

---

## Learning Outcomes

After completing this module, you will be able to:

- **Design** a CodeQL scanning workflow that matches a repository's language mix, build requirements, and security review process.
- **Analyze** a vulnerable code path by identifying sources, sinks, sanitizers, and the data flow that connects them.
- **Implement** a custom CodeQL query for an application-specific vulnerability pattern and run it against a real database.
- **Evaluate** CodeQL results by separating true vulnerabilities from noisy findings and deciding when to tune a query, suppress an alert, or fix code.
- **Compare** CodeQL with pattern-matching scanners such as Semgrep and choose the right tool for a specific detection problem.

---

## Why This Module Matters

A platform security engineer was asked to explain why a payment team's "clean" repository still failed an external penetration test. The repository already had a static analysis tool in CI, and every pull request showed a green check. The tool was not broken in the obvious sense: it ran on every change, produced reports, and blocked the most blatant dangerous calls. Yet the attacker found a command injection flaw that crossed a controller, a helper module, and a wrapper around the operating system shell.

The problem was not that the old scanner saw nothing. It saw too much of the wrong thing. It flagged every suspicious shell helper, including internal calls that only used constant arguments, but it missed the one path where an HTTP query parameter flowed through a formatting function and into the shell wrapper. The scanner matched syntax; the vulnerability lived in the relationship between values across files.

CodeQL changes that conversation because it treats code as queryable data. It builds a database that records syntax, types, call relationships, control flow, and data flow, then lets you ask security questions against that database. Instead of asking "where does this string appear," you can ask "where can untrusted request data reach a dangerous function without passing through a sanitizer?"

That distinction matters for platform teams because they do not only scan one repository once. They operate shared CI templates, reusable security policies, organization-wide alert workflows, and exception processes. A weak scanner creates noise at scale. A well-designed CodeQL rollout can turn one security lesson into a reusable query that protects every service using the same framework pattern.

The goal of this module is not to make you memorize CodeQL syntax. The goal is to teach you how to reason from a real vulnerability pattern to a query, from a query result to a fix, and from one repository scan to a sustainable platform control.

---

## 1. From Pattern Matching to Semantic Analysis

Most static scanners start with a useful but limited idea: dangerous syntax is often near dangerous behavior. A rule might flag calls to `eval`, string concatenation in SQL statements, or hardcoded tokens assigned to variables with suspicious names. Those rules are fast, understandable, and often valuable. They also struggle when the same danger is hidden behind helper functions, framework abstractions, or values that move through several layers before reaching the risky operation.

CodeQL starts by extracting a codebase into a relational database. For interpreted languages such as Python and JavaScript, extraction usually happens from source files. For compiled languages such as Java, C#, C/C++, and Go, CodeQL may need to observe a build so it can understand generated artifacts, dependencies, and type information accurately. Once the database exists, queries run against that extracted model rather than scanning text line by line.

That database model is what lets CodeQL express security questions in the language of program behavior. A query can select function calls, method receivers, route handlers, imported packages, or tainted data paths. A path query can show the learner or reviewer not only the final dangerous call, but also the source value and each step in the flow that made the call reachable.

```text
CODEQL ARCHITECTURE
──────────────────────────────────────────────────────────────────────────────

┌────────────────────────────────────────────────────────────────────────────┐
│                                CODEBASE                                    │
│                                                                            │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────────┐ │
│  │  api/routes.js    │    │  lib/query.js     │    │  db/client.js        │ │
│  │  request input    │───▶│  string builder   │───▶│  database execution │ │
│  └──────────────────┘    └──────────────────┘    └──────────────────────┘ │
│                                                                            │
└──────────────────────────────────────┬─────────────────────────────────────┘
                                       │
                                       │ codeql database create
                                       ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                              CODEQL DATABASE                               │
│                                                                            │
│  ┌──────────────────────┬──────────────────────┬────────────────────────┐ │
│  │  Syntax facts         │  Semantic facts       │  Flow facts            │ │
│  │  files, calls, AST    │  types, imports       │  data and control flow │ │
│  └──────────────────────┴──────────────────────┴────────────────────────┘ │
│                                                                            │
└──────────────────────────────────────┬─────────────────────────────────────┘
                                       │
                                       │ codeql database analyze
                                       ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                              QUERY RESULTS                                 │
│                                                                            │
│  Source: req.query.id                                                       │
│  Path:   route handler → buildQuery → db.query                              │
│  Sink:   SQL execution without parameterization                             │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

A useful mental model is to think of CodeQL as "SQL for code facts," but that phrase is incomplete. CodeQL is not SQL syntax, and it does more than query tables. It uses object-oriented libraries for each supported language, plus data-flow and taint-tracking libraries that understand how values can move through programs. You still write declarative queries, but those queries operate on a rich model of code rather than raw rows from a hand-built schema.

| Scanner style | Good at | Weak at | Example decision |
|---|---|---|---|
| Regex or grep-like search | Finding exact strings and obvious forbidden calls | Distinguishing safe from unsafe use | Search for accidental use of a deprecated helper |
| Pattern-matching SAST | Finding local syntax shapes | Following values through custom abstractions | Flag direct `db.query("... " + id)` patterns |
| Semantic SAST with CodeQL | Following relationships, calls, and data flow | Requiring setup, database creation, and query design | Find request data reaching SQL execution through helpers |
| Runtime testing | Confirming behavior in a running system | Exhaustively exploring all code paths | Prove one suspected injection path is exploitable |

### Active Check: Choose the Right Level of Analysis

Your team has a Node.js service where every SQL query goes through a helper named `runQuery`. Some calls pass constant strings, some pass parameterized query objects, and a few build strings from request parameters before calling the helper. Before reading further, decide whether a regex search, a local pattern rule, or a CodeQL data-flow query is the better starting point. Write down the reason, not just the tool name.

A strong answer is that CodeQL is the better starting point when the risky value can be constructed away from the sink. A regex search for `runQuery` will find too many safe calls, and a local pattern can miss the case where the string is built in a helper. You still might use simple search for inventory, but the security question is about flow from untrusted input to a dangerous operation.

---

## 2. Building and Running a CodeQL Database

A CodeQL scan has two major phases: database creation and query execution. Database creation extracts facts from the codebase. Query execution applies one or more query packs against that database and emits results, often in SARIF format so GitHub code scanning or another security system can display them.

The important platform-engineering decision is that database creation must match the repository's build reality. JavaScript and Python projects are often extraction-friendly without a build command. Java, Kotlin, C#, C/C++, and some Go projects may need an explicit build command so CodeQL can see generated sources, dependency graphs, and compiler-resolved information. If extraction is wrong, query results can be incomplete even when the query is well written.

```bash
# Install the GitHub CLI extension if your workstation uses gh.
gh extension install github/gh-codeql

# Verify the CodeQL CLI is available through your chosen installation path.
codeql version

# Create a database for a JavaScript or TypeScript project.
codeql database create js-db \
  --language=javascript \
  --source-root=.

# Create a database for a Python project.
codeql database create py-db \
  --language=python \
  --source-root=.

# Create a database for a Java project that must be compiled.
codeql database create java-db \
  --language=java \
  --command="mvn -DskipTests compile"

# Analyze a JavaScript database with the extended security suite.
codeql database analyze js-db \
  codeql/javascript-queries:codeql-suites/javascript-security-extended.qls \
  --format=sarif-latest \
  --output=codeql-results.sarif
```

A common beginner mistake is to treat a successful database creation command as proof that extraction was complete. The command can finish while silently extracting less useful information than expected, especially when build scripts are skipped or generated code is absent. Senior practitioners check the extraction logs, compare expected languages against detected languages, and investigate surprisingly empty result sets before declaring a scan healthy.

In GitHub Actions, the CodeQL action wraps this process in three steps: initialize, autobuild or custom build, and analyze. The default setup is often enough for simple repositories. Platform teams usually move to an explicit configuration file once they need custom query packs, path exclusions, query filters, or monorepo-specific behavior.

```yaml
# .github/workflows/codeql.yml
name: CodeQL

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: "0 6 * * 1"

jobs:
  analyze:
    name: Analyze
    runs-on: ubuntu-latest

    permissions:
      actions: read
      contents: read
      security-events: write

    strategy:
      fail-fast: false
      matrix:
        language: ["javascript", "python"]

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
          queries: security-extended,security-and-quality
          config-file: .github/codeql/codeql-config.yml

      - name: Autobuild
        uses: github/codeql-action/autobuild@v3

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3
        with:
          category: "/language:${{ matrix.language }}"
```

```yaml
# .github/codeql/codeql-config.yml
name: "Platform CodeQL Configuration"

queries:
  - uses: security-extended
  - uses: security-and-quality
  - uses: ./.github/codeql/custom-queries

paths:
  - src/
  - services/

paths-ignore:
  - "**/test/**"
  - "**/tests/**"
  - "**/vendor/**"
  - "**/*.min.js"

query-filters:
  - exclude:
      id: js/useless-expression
  - include:
      precision: high
```

The configuration above makes several choices that should be explicit in a production review. It scans application paths, avoids vendored or generated code, includes extended security and quality queries, and admits only high-precision results after excluding a known noisy query. Those choices are not universally correct. A security-critical library may intentionally scan tests for insecure examples, while a monorepo may need separate workflows per service because a single broad scan is too slow for pull requests.

| Repository shape | Recommended CodeQL setup | Reasoning checkpoint |
|---|---|---|
| Small single-language service | Default setup with `security-extended` | Fast feedback matters more than custom tuning at first |
| Polyglot service | Matrix per supported language | Results are easier to triage when categories are separated |
| Monorepo with many services | Service-scoped workflows or path-based triggers | One global scan may be too slow and too noisy |
| Compiled enterprise app | Explicit build command | Autobuild can miss custom build steps and generated sources |
| Framework-heavy platform | Custom query pack | Built-in queries may not know local request and sanitizer patterns |

### Pause and Predict: What Breaks First?

A Java repository uses Gradle, generated sources, and annotation processors. The team enables CodeQL with `autobuild` and sees almost no alerts. Predict two possible explanations before looking at the logs. Then decide which evidence would separate "the code is clean" from "the database is incomplete."

The strongest first checks are extraction logs and build behavior. If the build did not run the annotation processors or generated source step, CodeQL may have missed important code. If the database contains the expected packages and call graph but produces few findings, the result may be plausible. Treat unusually quiet scans as something to validate, not something to celebrate automatically.

---

## 3. Reading CodeQL Queries as Security Arguments

A CodeQL query is a security argument written in executable form. It says, "These program elements matter, these relationships make them risky, and these results are worth reporting." Reading a query well means identifying the claim before getting lost in syntax.

Most beginner queries follow a `from`, `where`, `select` shape. The `from` clause names the kinds of code elements under consideration. The `where` clause narrows those elements to the risky pattern. The `select` clause reports the location and message. For simple structural findings, this is enough.

```ql
/**
 * @name Direct call to dangerous JavaScript evaluation
 * @description Finds calls that execute strings as code.
 * @kind problem
 * @problem.severity warning
 * @precision medium
 * @id custom/direct-eval-like-call
 */

import javascript

from CallExpr call
where
  call.getCalleeName() = ["eval", "Function"] and
  call.getNumArgument() > 0
select call, "This call can execute a string as code; verify the argument cannot be attacker-controlled."
```

This query is intentionally simple. It does not prove exploitability because it does not ask where the argument came from. It is still useful as an inventory query during migration away from dangerous APIs. If you used it as a blocking security gate, it would likely create noise because constant or build-time-only uses may not be exploitable in the deployed application.

Query metadata matters because it controls how results are interpreted by tools and humans. The `@kind` field tells CodeQL whether the result is a simple problem or a path problem. Severity and precision help triage. Tags connect findings to security taxonomies and make it easier to filter results across many repositories.

```ql
/**
 * @name User input reaches shell command
 * @description Tracks request-controlled values into child process execution.
 * @kind path-problem
 * @problem.severity error
 * @security-severity 9.1
 * @precision high
 * @id custom/request-to-shell
 * @tags security
 *       external/cwe/cwe-078
 */
```

The metadata should not exaggerate the query's proof. A query that only finds suspicious local syntax should not claim high precision unless it has been tested against real safe and unsafe cases. A path query with well-defined sources, sinks, and sanitizers can often justify higher precision because the result includes the causal path a developer needs to inspect.

| Query part | Teaching question | Review risk |
|---|---|---|
| `import javascript` | Which language library defines the code model? | Wrong library means the query cannot see the intended constructs |
| `from CallExpr call` | What code elements are candidates? | Too broad can make the query slow or noisy |
| `where call.getCalleeName() = "eval"` | What makes a candidate suspicious? | Local syntax may not prove vulnerability |
| `select call, "message"` | What will the developer see? | Vague messages slow triage |
| `@kind path-problem` | Does the query need source-to-sink evidence? | Missing path data makes complex findings hard to trust |

### Stop and Think: Is This Query a Gate or a Lens?

Suppose you write a query that finds every call to a dangerous helper named `runRawSql`. The helper is used by migrations, admin-only reports, and request handlers. Would you use the query to block every pull request immediately, or would you first use it as an inventory lens? Explain what additional condition would make it safe enough to become a blocking rule.

A reasonable answer is to start as an inventory lens and graduate to a blocking rule once the query distinguishes untrusted request-controlled inputs from controlled administrative or migration inputs. Platform security controls become more durable when their enforcement level matches their precision.

---

## 4. Worked Example: From One Vulnerability to a Path Query

The fastest way to understand CodeQL is to start with a concrete bug. The following Express service has one command injection vulnerability. The dangerous behavior is not simply "there is a call to `exec`." The bug is that request input reaches `exec` without validation or allow-listing.

```bash
mkdir codeql-worked-example
cd codeql-worked-example
npm init -y
npm install express
```

```javascript
// app.js
const express = require("express");
const { exec } = require("child_process");

const app = express();

function normalizeHost(value) {
  return String(value).trim().toLowerCase();
}

function runLookup(host) {
  return exec(`nslookup ${host}`);
}

app.get("/lookup", (req, res) => {
  const host = normalizeHost(req.query.host);
  runLookup(host);
  res.json({ queued: true });
});

app.get("/health", (_req, res) => {
  exec("uptime");
  res.json({ ok: true });
});

app.listen(3000);
```

A local structural query for `exec` would find both `/lookup` and `/health`. That is not enough. The `/health` call uses a constant string and may still deserve review, but it is not the same risk as attacker-controlled input flowing into a shell command. The security argument needs a source, a sink, and a flow relation between them.

```text
DATA FLOW PATH FOR THE BUG
──────────────────────────────────────────────────────────────────────────────

┌────────────────────────────┐
│ Source                     │
│ req.query.host             │
└──────────────┬─────────────┘
               │
               ▼
┌────────────────────────────┐
│ Transformation             │
│ normalizeHost(...)         │
│ trims and lowercases only  │
└──────────────┬─────────────┘
               │
               ▼
┌────────────────────────────┐
│ Helper boundary            │
│ runLookup(host)            │
└──────────────┬─────────────┘
               │
               ▼
┌────────────────────────────┐
│ Sink                       │
│ exec(`nslookup ${host}`)   │
└────────────────────────────┘
```

The transformation is important. Many real-world false positives happen because a query treats every helper as dangerous or every helper as safe. `normalizeHost` changes formatting but does not prove the value is a valid hostname. A safer implementation would use an allow-list, a strict parser, or avoid shell invocation entirely by using a library API.

A CodeQL taint-tracking query models that reasoning. The exact libraries evolve between CodeQL releases, so production teams should check the current language documentation when writing query packs. The core shape remains stable: define sources, define sinks, optionally define sanitizers, and report paths where tainted data reaches a sink.

```ql
/**
 * @name Request parameter reaches shell execution
 * @description Finds Express request query values passed to child_process exec.
 * @kind path-problem
 * @problem.severity error
 * @security-severity 9.1
 * @precision high
 * @id custom/request-query-to-exec
 * @tags security
 *       external/cwe/cwe-078
 */

import javascript
import DataFlow::PathGraph

class RequestQuerySource extends DataFlow::Node {
  RequestQuerySource() {
    exists(PropAccess queryAccess |
      queryAccess.getPropertyName() = "query" and
      this = DataFlow::valueNode(queryAccess.getAPropertyRead())
    )
  }
}

class ExecSink extends DataFlow::Node {
  ExecSink() {
    exists(CallExpr call |
      call.getCalleeName() = "exec" and
      this = DataFlow::valueNode(call.getArgument(0))
    )
  }
}

class ShellCommandConfig extends TaintTracking::Configuration {
  ShellCommandConfig() {
    this = "ShellCommandConfig"
  }

  override predicate isSource(DataFlow::Node source) {
    source instanceof RequestQuerySource
  }

  override predicate isSink(DataFlow::Node sink) {
    sink instanceof ExecSink
  }

  override predicate isSanitizer(DataFlow::Node node) {
    exists(CallExpr call |
      call.getCalleeName() = "assertSafeHostname" and
      node = DataFlow::valueNode(call)
    )
  }
}

from ShellCommandConfig cfg, DataFlow::PathNode source, DataFlow::PathNode sink
where cfg.hasFlowPath(source, sink)
select sink.getNode(), source, sink,
  "Request query data reaches shell execution without a recognized hostname sanitizer."
```

The sanitizer definition is deliberately narrow. If the team has a real `assertSafeHostname` function that rejects unsafe values, the query can treat values returned by that function as safe. It should not treat `trim`, `toLowerCase`, or `String` as sanitizers because those functions do not remove shell metacharacters or constrain the value to a safe domain.

A senior review of this query would ask three questions. First, does the source model actually capture the framework's request values? Second, does the sink model cover the dangerous APIs used in this codebase, such as `execFile`, `spawn`, or wrapper functions? Third, does the sanitizer model match real validation behavior rather than trusting names that merely sound safe?

```javascript
// Safer direction: avoid shell interpolation and validate domain shape.
const dns = require("dns").promises;

function assertSafeHostname(value) {
  const host = String(value).trim().toLowerCase();

  if (!/^[a-z0-9.-]+$/.test(host)) {
    throw new Error("invalid hostname");
  }

  if (host.length > 253 || host.includes("..")) {
    throw new Error("invalid hostname");
  }

  return host;
}

app.get("/lookup-safe", async (req, res) => {
  const host = assertSafeHostname(req.query.host);
  const result = await dns.lookup(host);
  res.json(result);
});
```

### Active Check: Classify the Flow

In the vulnerable example, decide whether each function is a source, sink, sanitizer, or neutral transformation: `req.query.host`, `normalizeHost`, `runLookup`, `exec`, and `assertSafeHostname`. Then explain why treating `normalizeHost` as a sanitizer would create a false negative.

The intended classification is that `req.query.host` is a source, `exec` is the sink, `assertSafeHostname` can be a sanitizer if its implementation is strict, and `normalizeHost` is only a neutral transformation. `runLookup` is a helper boundary that passes tainted data into the sink. Calling it a sanitizer would hide the exact path attackers can exploit.

---

## 5. Variant Analysis and Custom Query Packs

Variant analysis is the practice of turning one discovered bug into a reusable detector for the entire codebase or organization. It is one of the main reasons CodeQL belongs in platform engineering rather than only in one-off security research. When a team fixes a bug manually, only that bug is gone. When the team encodes the pattern as a query, the platform can find existing variants and stop new ones from entering.

The workflow starts with a real vulnerability, not with a generic rule idea. You inspect the bug, identify what made it exploitable, write the narrowest query that captures that pattern, and run it against nearby code. After the query finds true variants, you broaden it carefully. The discipline is to generalize the vulnerability mechanism without generalizing so far that every suspicious-looking construct becomes an alert.

```text
VARIANT ANALYSIS WORKFLOW
──────────────────────────────────────────────────────────────────────────────

┌────────────────────────────┐
│ 1. Investigate one bug      │
│    Confirm exploit path     │
└──────────────┬─────────────┘
               │
               ▼
┌────────────────────────────┐
│ 2. Name the pattern         │
│    Source + sink + missing  │
│    guard or sanitizer       │
└──────────────┬─────────────┘
               │
               ▼
┌────────────────────────────┐
│ 3. Write a narrow query     │
│    Prefer true positives    │
│    over broad guesses       │
└──────────────┬─────────────┘
               │
               ▼
┌────────────────────────────┐
│ 4. Run across repositories  │
│    Triage and tune results  │
└──────────────┬─────────────┘
               │
               ▼
┌────────────────────────────┐
│ 5. Add to CI query pack     │
│    Prevent recurrence       │
└────────────────────────────┘
```

Consider an internal API pattern where admin endpoints check only whether a header exists. The first bug appears in one route, but the pattern probably exists elsewhere because developers copy route templates. The query should not search for the literal route name. It should search for authentication decisions based on header presence without value comparison or middleware enforcement.

```python
# Vulnerable pattern: presence check only.
@app.route("/api/admin/users")
def list_users():
    if request.headers.get("X-Admin-Token"):
        return jsonify(get_all_users())

    return jsonify({"error": "unauthorized"}), 401
```

```python
# Safer pattern: compare against a trusted expected value.
@app.route("/api/admin/users")
def list_users():
    expected = os.environ["ADMIN_TOKEN"]

    if request.headers.get("X-Admin-Token") == expected:
        return jsonify(get_all_users())

    return jsonify({"error": "unauthorized"}), 401
```

```text
AUTHENTICATION VARIANT ANALYSIS
──────────────────────────────────────────────────────────────────────────────

┌──────────────────────────────────────────────┐
│ Original bug                                  │
│ Header exists, but value is not verified      │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│ Generalized pattern                           │
│ Sensitive route branches on request header    │
│ truthiness rather than equality or middleware │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│ Query result classes                          │
│ True positive: presence-only admin guard      │
│ Review needed: webhook signature precheck     │
│ False positive: public route feature flag     │
└──────────────────────────────────────────────┘
```

When a query becomes useful, package it. A query pack gives the organization a versioned unit that can be shared across repositories. It also gives reviewers a place to test query behavior with known vulnerable and known safe fixtures. Treat query packs like production code: review them, test them, version them, and document their intended enforcement level.

```yaml
# .github/codeql/custom-queries/qlpack.yml
name: platform-security/custom-codeql-queries
version: 1.0.0
dependencies:
  codeql/javascript-all: "*"
  codeql/python-all: "*"
```

```text
CUSTOM QUERY PACK LAYOUT
──────────────────────────────────────────────────────────────────────────────

.github/
└── codeql/
    └── custom-queries/
        ├── qlpack.yml
        ├── javascript/
        │   ├── RequestToShell.ql
        │   └── MissingCsrf.ql
        ├── python/
        │   └── HeaderPresenceAuth.ql
        └── test/
            ├── vulnerable-app.js
            ├── safe-app.js
            └── expected-results.md
```

The strongest query packs are not collections of clever syntax tricks. They are encoded incident learnings. Each query should answer why the organization cares, what kind of result it produces, how confident the team is, and what a developer should do when it fires. A vague query message pushes work onto every service team; a precise query message turns the alert into a guided remediation path.

| Query pack maturity | Typical behavior | Platform action |
|---|---|---|
| Experimental | Run manually against known repositories | Collect examples and tune sources and sinks |
| Advisory | Publish results without blocking merges | Teach teams how to interpret and fix alerts |
| Enforced | Block pull requests on high-confidence findings | Require tests, ownership, and suppression policy |
| Retired | No longer relevant because framework changed | Remove or archive with migration notes |

### Pause and Predict: Which Query Should Become Shared?

A security engineer writes two queries after an incident. Query A finds any function whose name contains `token`. Query B finds request headers used as authorization checks without comparison against a trusted expected value. Which one is a better candidate for an organization query pack, and what test fixtures would you require before enforcement?

Query B is the better candidate because it encodes a vulnerability mechanism rather than a suspicious word. Good fixtures would include a vulnerable presence-only route, a safe equality check, a safe middleware-protected route, and a public route that mentions a token without making an authorization decision.

---

## 6. Operating CodeQL in CI Without Drowning Teams

CodeQL succeeds or fails as an operating practice, not just as a scanner. A technically accurate alert can still fail if it reaches the wrong owner, appears too late in the delivery flow, or lacks enough context for the service team to act. A platform team must design feedback loops, not merely enable a workflow file.

The first operating decision is where CodeQL runs. Pull request scans are best for preventing new high-confidence vulnerabilities, but they must be fast enough that developers do not route around them. Scheduled scans are better for newly released queries, dependency model improvements, and deeper suites that are too expensive for every pull request. Manual scans are useful during incident response and variant analysis.

```text
CODEQL OPERATING MODEL
──────────────────────────────────────────────────────────────────────────────

┌──────────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│ Pull request scan     │────▶│ Prevent new issues    │────▶│ Fast, focused    │
│ high precision only   │     │ before merge          │     │ blocking allowed │
└──────────────────────┘     └──────────────────────┘     └─────────────────┘

┌──────────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│ Scheduled scan        │────▶│ Find older variants   │────▶│ Broader suites   │
│ weekly or nightly     │     │ after query updates   │     │ triage workflow  │
└──────────────────────┘     └──────────────────────┘     └─────────────────┘

┌──────────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│ Incident scan         │────▶│ Hunt related bugs     │────▶│ Custom query     │
│ targeted repositories │     │ during response       │     │ security-owned   │
└──────────────────────┘     └──────────────────────┘     └─────────────────┘
```

Tuning should be evidence-based. If a query produces many false positives, do not immediately disable it everywhere. Inspect the results and classify the cause. The source model might be too broad, the sanitizer model might be missing a real validation helper, the sink might include safe wrapper functions, or the repository might need path exclusions for test fixtures. Each cause leads to a different fix.

```yaml
# Example: keep a strong suite, but exclude one noisy query by ID.
query-filters:
  - exclude:
      id: js/unused-local-variable

# Example: include only high precision findings in a blocking PR workflow.
query-filters:
  - include:
      precision: high
      problem.severity: error
```

Suppression policy is also part of the teaching system. Developers should not be told "never suppress" because some findings are accepted risk or false positives. They should be required to explain why a suppression is correct, link to an issue or risk decision when appropriate, and prefer query tuning when many teams hit the same false positive. A suppression without a reason is technical debt; a suppression with evidence can be an auditable decision.

| Alert outcome | What it means | Good next action |
|---|---|---|
| True positive, exploitable | Real vulnerability with reachable path | Fix code and add regression coverage |
| True positive, low impact | Real issue but limited exposure | Fix by priority or document risk acceptance |
| False positive from missing sanitizer | Query does not know a safe validation helper | Add sanitizer model and test fixture |
| False positive from generated code | Scanner sees code the team does not maintain | Exclude generated path or adjust workflow |
| Duplicate alert | Same root cause reported multiple times | Fix root cause and tune reporting if needed |
| Unclear finding | Result lacks enough evidence | Reproduce path, inspect SARIF, or improve query message |

CodeQL and Semgrep often coexist in mature platforms. Semgrep is excellent for fast local structural rules, policy checks, and language-agnostic patterns that do not need deep data-flow modeling. CodeQL is stronger when the question depends on semantic relationships across files and functions. The right comparison is not "which tool is better," but "which tool can prove the condition with acceptable noise and runtime."

| Detection need | Prefer CodeQL when | Prefer Semgrep when |
|---|---|---|
| Request data reaches SQL execution | Flow crosses helpers or files | Pattern is local and simple |
| Deprecated API usage | Type or call graph matters | Exact syntax is enough |
| Organization coding policy | Policy depends on semantic context | Rule is quick syntax matching |
| Variant analysis after incident | Need source-to-sink path proof | Need rapid broad inventory |
| Developer pre-commit feedback | Query runtime is acceptable | Fast local feedback is critical |

### Active Check: Tune or Suppress?

A custom CodeQL query reports twenty findings where request data reaches `renderHtml`. Fifteen are real XSS risks. Five pass through a shared `escapeHtml` helper that the query does not recognize. Should the team suppress those five alerts, disable the query, or update the query? Explain the operational reason.

The best answer is to update the query with a sanitizer model for `escapeHtml` and add safe fixtures proving the change. Suppressing five alerts treats the symptom in individual repositories. Disabling the query loses fifteen real findings. Query tuning turns the triage lesson into a platform improvement.

---

## Did You Know?

- CodeQL originated from research into semantic code analysis and became part of GitHub after GitHub acquired Semmle. That history explains why CodeQL feels more like a query language over program facts than a traditional rule file format.
- CodeQL results are commonly emitted as SARIF, the Static Analysis Results Interchange Format. SARIF allows code scanning systems to display locations, messages, severities, and path traces consistently across tools.
- Public repositories on GitHub can use CodeQL code scanning without needing the same commercial licensing model as private enterprise repositories. That makes open-source projects a useful place to study real query behavior and alert examples.
- CodeQL query packs let security knowledge move from one incident responder's workstation into repeatable CI. This is the key platform-engineering benefit: the organization can preserve a hard-won lesson as executable policy.

---

## Common Mistakes

| Mistake | Why It Hurts | Better Approach |
|---|---|---|
| Treating a successful database creation as proof of full coverage | Extraction can succeed while missing generated code, build-time types, or compiled artifacts | Review extraction logs and verify expected packages, languages, and build steps are represented |
| Blocking pull requests with broad experimental queries | Developers experience noisy failures and lose trust in the security gate | Run experimental queries in advisory mode until true-positive rates are understood |
| Defining sanitizers by name alone | A function named `cleanInput` may only trim whitespace or normalize case | Inspect implementation and add fixtures proving safe and unsafe flows |
| Scanning every monorepo path with one workflow | Results become slow, noisy, and hard to route to owners | Scope workflows by service, language, path, or ownership boundary |
| Ignoring scheduled scans after enabling PR scans | New CodeQL queries and updated libraries can find older bugs that PR scans never revisit | Run scheduled scans and triage newly discovered historical findings |
| Replacing incident analysis with generic query writing | The query may encode a vague suspicion rather than the actual vulnerability mechanism | Start from a confirmed bug, then generalize sources, sinks, and missing guards carefully |
| Suppressing alerts without rationale | Future reviewers cannot distinguish accepted risk from triage fatigue | Require suppression comments, issue links, or query tuning proposals |
| Comparing tools only by alert count | Fewer alerts can mean better precision or weaker coverage | Compare by true positives, fixability, runtime, developer experience, and missed-risk analysis |

---

## Quiz

### Question 1

Your team enables CodeQL on a Java service that uses a custom Gradle build and annotation-generated controllers. The first scheduled scan finishes quickly and reports no security alerts. A manager asks whether the service is clean. What should you check before answering, and why?

<details>
<summary>Show Answer</summary>

Do not treat the empty result set as proof of safety until you validate extraction. Check the CodeQL build and extraction logs, confirm the Gradle build ran the annotation processors, and verify that the generated controller packages appear in the database. If generated endpoints are absent, CodeQL may have analyzed only part of the application. A clean scan is meaningful only after the database represents the code paths where vulnerabilities could exist.
</details>

### Question 2

A Node.js repository has a helper named `runQuery(sql)` used by migrations, background jobs, and HTTP route handlers. A developer proposes a CodeQL query that reports every call to `runQuery`. How would you improve the query before making it a blocking CI rule?

<details>
<summary>Show Answer</summary>

Make the query prove a risky flow rather than merely inventory a helper call. Model HTTP request fields such as `req.body`, `req.query`, and `req.params` as sources, model `runQuery` as a sink or as a step toward the database sink, and add sanitizers or safe parameterization patterns. Keep the broad query as an advisory inventory if it is useful, but use a source-to-sink path query for blocking because migrations and constant background queries are not the same risk as request-controlled SQL.
</details>

### Question 3

During incident response, you find one Flask admin endpoint that grants access when `request.headers.get("X-Admin-Token")` is truthy. Several teams copied the same route template. What CodeQL variant-analysis strategy would you use?

<details>
<summary>Show Answer</summary>

Generalize the bug into the mechanism: a sensitive route branches on the presence of an authorization header without comparing it to a trusted value or using approved middleware. Write a query that finds header access used directly as a condition, then exclude or separately classify routes protected by known authentication decorators. Test it against one vulnerable fixture, one safe equality check, one middleware-protected route, and one public route that reads headers for non-authentication purposes.
</details>

### Question 4

A custom command-injection query reports a path from `req.query.host` through `normalizeHost()` into `exec()`. The service owner says `normalizeHost()` lowercases and trims the value, so the alert is safe. How should you evaluate that claim?

<details>
<summary>Show Answer</summary>

Lowercasing and trimming are transformations, not security sanitizers for shell execution. Ask whether the function constrains the value to a safe hostname grammar or, better, whether the code can avoid shell execution entirely. If `normalizeHost()` does not reject shell metacharacters and invalid hostnames, the CodeQL alert remains valid. The safer fix is strict validation plus a non-shell DNS API, or a carefully modeled sanitizer only after the implementation proves safety.
</details>

### Question 5

A platform team sees many CodeQL alerts from test fixtures that intentionally contain vulnerable examples. Developers want to disable the affected query globally. What would you recommend instead?

<details>
<summary>Show Answer</summary>

Do not disable a useful query globally because test fixtures are noisy. Scope the scan with `paths-ignore` for intentional vulnerable fixtures, or separate educational test data from production application paths. If the same query finds real vulnerabilities in application code, disabling it would remove useful protection. The tuning should match the cause: generated, vendored, or intentionally vulnerable paths need path controls, not query removal.
</details>

### Question 6

A Semgrep rule already finds direct string concatenation inside `db.query(...)`. A security engineer wants to replace it with CodeQL. In what scenario is the replacement justified, and in what scenario is keeping Semgrep reasonable?

<details>
<summary>Show Answer</summary>

CodeQL is justified when vulnerable SQL strings are built in helpers, passed through multiple functions, or wrapped by framework-specific database abstractions. The security question then depends on data flow and semantic relationships. Keeping Semgrep is reasonable when the risky pattern is local, stable, and can be detected quickly with low noise, such as direct concatenation in the same call expression. Mature platforms often use both tools for different detection classes.
</details>

### Question 7

A CodeQL path query has high true-positive value, but developers complain that the result message says only "unsafe flow." What change would improve remediation without weakening detection?

<details>
<summary>Show Answer</summary>

Improve the `select` message and query documentation so the alert explains the source, sink, missing guard, and preferred remediation. For example, say that request-controlled data reaches shell execution without an approved hostname validator, and recommend using a non-shell API or a specific validation helper. Better messages reduce triage time while preserving the same detection logic.
</details>

### Question 8

A team wants to add a newly written custom query directly to the required pull-request gate across all repositories. It has only been tested against the incident repository where it was created. What rollout plan would you propose?

<details>
<summary>Show Answer</summary>

Start with advisory or scheduled scans across representative repositories, triage the results, and add fixtures for true positives, safe cases, and known false-positive patterns. Tune sources, sinks, and sanitizers based on evidence. Once the query has clear ownership, documentation, and acceptable precision, move high-severity findings into the blocking pull-request gate. This rollout protects developer trust while still turning the incident lesson into a reusable control.
</details>

---

## Hands-On Exercise

### Task: Build and Tune a Custom CodeQL Query

In this exercise, you will create a small vulnerable Express application, build a CodeQL database, run built-in analysis, write a custom query for missing CSRF protection on state-changing routes, and then reason about a false positive. The goal is not only to make a query return a result. The goal is to practice the same loop a platform team uses: define the risk, run the detector, inspect the result, and tune the rule.

### Success Criteria

- [ ] You create a sample Express application with at least one unsafe state-changing endpoint and one safe endpoint.
- [ ] You create a JavaScript CodeQL database from the sample application.
- [ ] You run the built-in JavaScript security query suite and save results in a machine-readable format.
- [ ] You write a custom query that reports the unsafe state-changing endpoint.
- [ ] You explain why the safe endpoint should not be reported.
- [ ] You identify one likely false-positive case and describe how you would tune the query before enforcing it in CI.
- [ ] You record the source, sink, and missing guard represented by your custom query.

### Step 1: Create the Sample Application

```bash
mkdir codeql-csrf-lab
cd codeql-csrf-lab
npm init -y
npm install express csurf
```

```javascript
// app.js
const express = require("express");
const csrf = require("csurf");

const app = express();
const csrfProtection = csrf({ cookie: false });

app.use(express.json());

function performTransfer(to, amount) {
  return { to, amount, status: "queued" };
}

function updateSettings(settings) {
  return { settings, status: "updated" };
}

function receiveWebhook(payload) {
  return { received: Boolean(payload) };
}

// Vulnerable: state-changing route without CSRF middleware.
app.post("/api/transfer", (req, res) => {
  const { to, amount } = req.body;
  res.json(performTransfer(to, amount));
});

// Safe: state-changing route with CSRF middleware.
app.post("/api/settings", csrfProtection, (req, res) => {
  res.json(updateSettings(req.body));
});

// Review-needed: webhook routes often use signatures instead of CSRF.
app.post("/api/webhook/payment", (req, res) => {
  res.json(receiveWebhook(req.body));
});

app.listen(3000);
```

The application intentionally includes three categories. `/api/transfer` is the target vulnerability because it changes state and has no CSRF protection. `/api/settings` is the safe comparison case because it includes explicit CSRF middleware. `/api/webhook/payment` is a realistic review case because webhook endpoints often use signature verification rather than browser CSRF tokens; a production query may need to classify or exclude these routes depending on your platform policy.

### Step 2: Create a CodeQL Database

```bash
codeql database create js-db \
  --language=javascript \
  --source-root=.
```

After the command finishes, inspect the output. You are looking for evidence that JavaScript extraction actually happened and that `app.js` was included. If the database creation fails, fix the local environment before writing queries. Query debugging is frustrating when the database itself is incomplete.

### Step 3: Run Built-In Security Queries

```bash
codeql database analyze js-db \
  codeql/javascript-queries:codeql-suites/javascript-security-extended.qls \
  --format=sarif-latest \
  --output=results.sarif
```

Open `results.sarif` or upload it to a SARIF viewer if you have one available. The built-in suite may not report your custom CSRF policy exactly as your organization wants it. That is the point of the exercise: built-in rules are strong general coverage, while custom queries encode local framework and policy decisions.

### Step 4: Create a Custom Query Pack

```bash
mkdir -p queries
```

```yaml
# queries/qlpack.yml
name: local/csrf-training-queries
version: 1.0.0
dependencies:
  codeql/javascript-all: "*"
```

A query pack gives your custom query a dependency context. In a real platform repository, this folder would be reviewed and versioned alongside tests and documentation. For this lab, it gives CodeQL enough metadata to resolve the JavaScript libraries used by the query.

### Step 5: Write the First Query

```ql
/**
 * @name State-changing Express route without visible CSRF middleware
 * @description Finds POST, PUT, PATCH, or DELETE routes that do not include middleware with csrf in the name.
 * @kind problem
 * @problem.severity warning
 * @precision medium
 * @id local/missing-csrf-on-state-changing-route
 * @tags security
 *       external/cwe/cwe-352
 */

import javascript
import semmle.javascript.frameworks.Express

from Express::RouteHandler handler
where
  handler.getHttpMethod() = ["post", "put", "patch", "delete"] and
  not handler.getRoutePattern().matches("/api/webhook%") and
  not exists(Expr middleware |
    middleware = handler.getAMiddleware() and
    middleware.toString().toLowerCase().matches("%csrf%")
  )
select handler,
  "State-changing route '" + handler.getRoutePattern() + "' has no visible CSRF middleware."
```

This query is intentionally a training query, not a perfect production rule. It demonstrates structural reasoning over Express routes and middleware. It also encodes a policy choice: webhook routes are excluded from this CSRF check because they usually need signature verification instead. In a real organization, you might replace that exclusion with a separate query requiring webhook signature validation.

### Step 6: Run the Custom Query

```bash
codeql query run queries/MissingCsrf.ql \
  --database=js-db
```

If you saved the file under a different name, adjust the command. The expected target is `/api/transfer`. If `/api/settings` appears, your middleware detection is too weak. If `/api/webhook/payment` appears, decide whether that is a policy failure or a deliberate review case.

### Step 7: Analyze the Result Like a Reviewer

Write down the result in this form:

```text
Custom query review
──────────────────────────────────────────────────────────────────────────────

Finding:
  /api/transfer is a state-changing POST route without visible CSRF middleware.

Source:
  Browser-originated request body submitted to an authenticated state-changing route.

Sink:
  Application state change performed by performTransfer(to, amount).

Missing guard:
  No CSRF middleware or equivalent anti-CSRF design is visible in the route chain.

Safe comparison:
  /api/settings includes csrfProtection before the handler.

Review-needed comparison:
  /api/webhook/payment may need signature verification instead of CSRF middleware.
```

This written explanation is not busywork. It is how you prevent custom query packs from becoming mysterious alert generators. A developer receiving the alert should understand the security model, not merely the syntax pattern.

### Step 8: Propose One Tuning Improvement

Choose one tuning improvement before imagining this query in CI. For example, you might model approved CSRF middleware names more precisely, require a separate webhook signature query, or classify routes under `/api/internal/` differently. Write the tuning as a testable statement: "The query should report X, should not report Y, and should explain Z." That phrasing turns a vague preference into a reviewable query requirement.

### Step 9: Optional CI Configuration

```yaml
# .github/codeql/codeql-config.yml
name: "CodeQL with local CSRF query"

queries:
  - uses: security-extended
  - uses: ./.github/codeql/custom-queries

paths:
  - src/

paths-ignore:
  - "**/test/**"
  - "**/fixtures/**"
```

Use this configuration only after moving the query pack into the repository and testing it with representative safe and unsafe examples. A custom query should enter CI as an engineered control, not as a one-off experiment copied from a lab.

---

## Next Module

[Module 12.4: Snyk](../module-12.4-snyk/) - Dependency and container scanning.
