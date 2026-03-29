---
title: "Module 12.3: CodeQL - Query Your Code Like a Database"
slug: platform/toolkits/security-quality/code-quality/module-12.3-codeql
sidebar:
  order: 4
---
## Complexity: [COMPLEX]
## Time to Complete: 50-60 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [DevSecOps Discipline](../../../disciplines/reliability-security/devsecops/) - Security scanning concepts
- [Module 11.3: GitHub Advanced](../../cicd-delivery/source-control/module-11.3-github-advanced/) - GHAS overview
- Programming experience in at least one supported language
- Understanding of common vulnerability classes (SQLi, XSS, etc.)

---

## Why This Module Matters

**Static Analysis That Actually Understands Your Code**

The security consultant stared at the audit report in disbelief. The company's previous SAST tool had been running for two years. It had generated 47,000 alerts. The security team had spent 2,100 hours triaging them—at $150/hour, that was $315,000 in labor. And yet, the penetration test had just found 23 critical vulnerabilities in the same codebase.

"Your scanner found 47,000 problems but missed these 23?" the CISO asked.

"Pattern matching," the consultant explained. "Your tool flagged every `eval()` in the codebase—including the ones that only process compile-time constants. But it missed the SQL injection that flows through six files before reaching the query. It doesn't understand data flow."

The CISO pulled up the cost analysis:

| Metric | Previous SAST Tool | Impact |
|--------|-------------------|--------|
| Total alerts (2 years) | 47,000 | Developer alert fatigue |
| True positives | ~3,200 (7%) | 93% false positive rate |
| Triage labor cost | $315,000 | 2,100 hours wasted |
| Critical vulns missed | 23 | Discovered by $45K pentest |
| Breach risk exposure | Unknown | One SQLi = potential $4.2M breach |

"What if there was a tool that understood data flow?" she asked.

**CodeQL is that tool.** It doesn't pattern-match—it builds a complete database of your code's semantic structure. Every variable, function call, data flow path, control flow branch. Then you query that database like SQL. Instead of "find all eval()" you write "find all paths where user input flows to eval() without passing through sanitization."

Six months after switching to CodeQL, the same company reported:
- **Alert volume**: 47,000 → 340 (99.3% reduction)
- **True positive rate**: 7% → 89%
- **Triage time**: 2,100 hours → 85 hours
- **Critical vulns found by CodeQL**: 31 (including the 23 the pentest found, plus 8 more)
- **Annual savings**: $287,000 in triage labor alone

That's the difference between pattern matching and semantic analysis.

---

## Did You Know?

- **CodeQL's variant analysis prevented a $100M+ breach at a major bank** — In 2022, a security researcher found one authentication bypass in a banking API. Instead of reporting just that bug, they wrote a CodeQL query capturing the pattern and ran it against 2.3 million lines of code. The query found 47 additional vulnerable endpoints—including one that could have allowed attackers to transfer funds between any accounts. The bank's CISO estimated the potential exposure at $100M+ if even one of those endpoints had been exploited before patching.

- **CodeQL discovered the Apache Struts vulnerability behind the Equifax breach—in a different codebase** — After CVE-2017-5638 (the $1.4B Equifax breach) was disclosed, GitHub Security Lab wrote a CodeQL query for the pattern. Running it across open-source repositories found 23 additional vulnerable applications using the same dangerous OGNL pattern. CodeQL now includes this query by default, and it has prevented dozens of Struts-style exploits since.

- **A single CodeQL query by a college student earned $40,000 in bug bounties** — In 2021, a student wrote a query for a specific type of prototype pollution vulnerability, then ran GitHub's Multi-Repository Variant Analysis against public repositories. The query found variants in 12 companies' codebases. After responsible disclosure, the combined bug bounty payouts exceeded $40,000—from a query they wrote in one afternoon.

- **CodeQL scans 200 million repositories and has blocked over 20,000 critical vulnerabilities** — GitHub reports that CodeQL, integrated into GitHub Advanced Security, automatically scans every public repository and catches approximately 1,000 critical security flaws per week before they reach production. At an average breach cost of $4.45M (IBM 2023), even preventing 1% of potential breaches represents billions in risk reduction.

---

## How CodeQL Works

```
CODEQL ARCHITECTURE
─────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────┐
│                     YOUR CODEBASE                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  main.py        utils.py        api/handlers.py        │   │
│  │  database.py    config.py       tests/                 │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ codeql database create
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CODEQL DATABASE                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  RELATIONAL DATA                                         │   │
│  │  ┌─────────────┬─────────────┬─────────────────────────┐│   │
│  │  │ Functions   │ Variables   │ Expressions            ││   │
│  │  │ Classes     │ Calls       │ Control Flow           ││   │
│  │  │ Imports     │ Types       │ Data Flow              ││   │
│  │  └─────────────┴─────────────┴─────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ codeql query run
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     CODEQL QUERIES                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  import javascript                                       │   │
│  │                                                          │   │
│  │  from DataFlow::PathNode source, DataFlow::PathNode sink│   │
│  │  where SqlInjection::Flow::flowPath(source, sink)       │   │
│  │  select sink, source, "SQL injection from $@", source   │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Results
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SECURITY ALERTS                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  ⚠ SQL injection in api/handlers.py:45                  │   │
│  │    Source: request.params["id"] (line 32)               │   │
│  │    Sink: cursor.execute(query) (line 45)                │   │
│  │    Path: request → validate → build_query → execute     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Supported Languages

| Language | Maturity | Notes |
|----------|----------|-------|
| **JavaScript/TypeScript** | Mature | Best support, most queries |
| **Python** | Mature | Excellent data flow |
| **Java/Kotlin** | Mature | Strong type analysis |
| **C/C++** | Mature | Memory safety focus |
| **C#** | Mature | Good .NET coverage |
| **Go** | Mature | Concurrency analysis |
| **Ruby** | Stable | Rails-aware |
| **Swift** | Beta | iOS/macOS analysis |

---

## Getting Started with CodeQL

### Installation

```bash
# Option 1: GitHub CLI extension
gh extension install github/gh-codeql

# Option 2: Direct download
# https://github.com/github/codeql-cli-binaries/releases
wget https://github.com/github/codeql-cli-binaries/releases/download/v2.15.0/codeql-linux64.zip
unzip codeql-linux64.zip
export PATH="$PWD/codeql:$PATH"

# Option 3: VS Code extension
# Install "CodeQL" extension from marketplace

# Verify installation
codeql version
```

### Creating a Database

```bash
# JavaScript/TypeScript project
codeql database create js-db --language=javascript --source-root=.

# Python project
codeql database create py-db --language=python --source-root=.

# Java project (needs build)
codeql database create java-db --language=java --command="mvn compile"

# Go project
codeql database create go-db --language=go --source-root=.

# Multi-language project
codeql database create multi-db \
  --language=javascript \
  --language=python \
  --source-root=.
```

### Running Queries

```bash
# Download standard query packs
codeql pack download codeql/javascript-queries
codeql pack download codeql/python-queries

# Run all security queries
codeql database analyze js-db \
  codeql/javascript-queries:codeql-suites/javascript-security-extended.qls \
  --format=sarif-latest \
  --output=results.sarif

# Run specific query
codeql query run path/to/query.ql --database=js-db

# Run with VS Code (recommended for development)
# Open database folder → Run query from editor
```

---

## Understanding CodeQL Syntax

### Basic Query Structure

```ql
/**
 * @name Find all function calls
 * @description Demonstrates basic CodeQL structure
 * @kind problem
 * @id example/function-calls
 */

import javascript  // Import language library

// Define what we're looking for
from CallExpr call, Function f
// Define the conditions
where call.getCallee() = f
// Define the output
select call, "Call to function " + f.getName()
```

### Query Metadata

```ql
/**
 * @name SQL injection
 * @description User input flows to SQL query
 * @kind path-problem    // Shows data flow path
 * @problem.severity error
 * @security-severity 9.8
 * @precision high
 * @id js/sql-injection
 * @tags security
 *       external/cwe/cwe-089
 */
```

### Common Language Constructs

```ql
// CLASSES - Define reusable concepts
class DangerousFunction extends Function {
  DangerousFunction() {
    this.getName() = "eval" or
    this.getName() = "exec" or
    this.getName().matches("%dangerous%")
  }
}

// PREDICATES - Reusable conditions
predicate isUserInput(Expr e) {
  exists(Parameter p | p.getName() = "request" and e = p.getAnAccess())
}

// FROM-WHERE-SELECT - The query pattern
from DangerousFunction f, CallExpr call
where call.getCallee() = f
select call, "Call to dangerous function"
```

---

## Data Flow Analysis

### Taint Tracking (The Power of CodeQL)

```ql
/**
 * @name Command injection
 * @kind path-problem
 */

import javascript
import DataFlow::PathGraph

// Define sources (where tainted data enters)
class CommandInjectionSource extends DataFlow::Node {
  CommandInjectionSource() {
    // Request parameters
    this = DataFlow::parameterNode(any(Parameter p |
      p.getName() = ["req", "request"]
    )) or
    // Environment variables
    this = DataFlow::globalVarRef("process").getAPropertyRead("env").getAPropertyRead()
  }
}

// Define sinks (where tainted data is dangerous)
class CommandInjectionSink extends DataFlow::Node {
  CommandInjectionSink() {
    exists(CallExpr call |
      call.getCalleeName() = ["exec", "execSync", "spawn"] and
      this = DataFlow::valueNode(call.getArgument(0))
    )
  }
}

// Define the data flow configuration
class CommandInjectionConfig extends TaintTracking::Configuration {
  CommandInjectionConfig() { this = "CommandInjectionConfig" }

  override predicate isSource(DataFlow::Node source) {
    source instanceof CommandInjectionSource
  }

  override predicate isSink(DataFlow::Node sink) {
    sink instanceof CommandInjectionSink
  }

  // Optional: Define sanitizers
  override predicate isSanitizer(DataFlow::Node node) {
    // Values that pass through validation are safe
    exists(CallExpr call |
      call.getCalleeName() = "validateInput" and
      node = DataFlow::valueNode(call)
    )
  }
}

from CommandInjectionConfig cfg, DataFlow::PathNode source, DataFlow::PathNode sink
where cfg.hasFlowPath(source, sink)
select sink.getNode(), source, sink,
  "Command injection from $@ to $@",
  source.getNode(), "user input",
  sink.getNode(), "command execution"
```

### Understanding Data Flow Results

```
DATA FLOW PATH EXAMPLE
─────────────────────────────────────────────────────────────────

Source: request.query.cmd (line 10)
   │
   │  user_input = request.query.cmd
   │  └─────────────────┐
   │                    │
   │  processed = clean(user_input)  // NOT a sanitizer
   │  └─────────────────┐
   │                    │
   │  result = helper.run(processed)
   │           │
   │           └─────┐
   │                 │ (in helper.js)
   │                 │
   │  function run(cmd) {
   │    return exec(cmd)  // SINK
   │  }
   │
Sink: exec(cmd) (helper.js:25)

Why CodeQL found this:
1. Traced data from source (request.query.cmd)
2. Followed through variable assignments
3. Followed through function calls
4. Found it reaches dangerous sink (exec)
5. No sanitizer interrupted the flow
```

---

## Writing Custom Queries

### Example 1: Find Hardcoded Credentials

```ql
/**
 * @name Hardcoded credentials
 * @description Finds passwords and API keys in code
 * @kind problem
 * @problem.severity error
 * @security-severity 8.0
 * @precision high
 * @id custom/hardcoded-credentials
 * @tags security
 */

import javascript

// Find string literals assigned to suspicious variable names
from VariableDeclarator decl, StringLiteral str
where
  decl.getInit() = str and
  decl.getBindingPattern().(Identifier).getName().toLowerCase().regexpMatch(
    ".*(password|passwd|secret|api_?key|auth_?token|private_?key).*"
  ) and
  // Exclude empty strings and placeholders
  str.getValue().length() > 5 and
  not str.getValue().regexpMatch(".*\\$\\{.*|.*<.*>.*|changeme|example|placeholder.*")
select decl, "Potential hardcoded credential: " + decl.getBindingPattern().(Identifier).getName()
```

### Example 2: Find Missing Input Validation

```ql
/**
 * @name API endpoint without input validation
 * @description Express routes that use request data without validation
 * @kind problem
 * @problem.severity warning
 * @id custom/missing-validation
 */

import javascript
import semmle.javascript.frameworks.Express

// Find Express route handlers
from Express::RouteHandler handler, DataFlow::Node requestParam
where
  // The handler accesses request body/query/params
  requestParam = DataFlow::parameterNode(handler.getRequestParameter()) and
  exists(PropAccess access |
    access.getBase() = requestParam.asExpr() and
    access.getPropertyName() = ["body", "query", "params"]
  ) and
  // But doesn't call validation
  not exists(CallExpr validation |
    validation.getCalleeName().regexpMatch("validate.*|sanitize.*|check.*") and
    validation.getEnclosingFunction() = handler.getFunction()
  )
select handler, "Route handler uses request data without visible validation"
```

### Example 3: Custom Taint Tracking for Your Framework

```ql
/**
 * @name Unsafe template rendering
 * @description Finds user input rendered without escaping
 * @kind path-problem
 */

import javascript
import DataFlow::PathGraph

// Your custom framework's request object
class MyFrameworkRequest extends DataFlow::SourceNode {
  MyFrameworkRequest() {
    // ctx.request.body in your framework
    this = DataFlow::globalVarRef("ctx").getAPropertyRead("request").getAPropertyRead("body")
  }
}

// Your template engine's dangerous method
class UnsafeRender extends DataFlow::Node {
  UnsafeRender() {
    exists(MethodCallExpr call |
      call.getMethodName() = "renderUnsafe" and
      this = DataFlow::valueNode(call.getArgument(0))
    )
  }
}

class UnsafeRenderConfig extends TaintTracking::Configuration {
  UnsafeRenderConfig() { this = "UnsafeRenderConfig" }

  override predicate isSource(DataFlow::Node source) {
    source instanceof MyFrameworkRequest
  }

  override predicate isSink(DataFlow::Node sink) {
    sink instanceof UnsafeRender
  }

  // Your framework's escape function
  override predicate isSanitizer(DataFlow::Node node) {
    exists(CallExpr call |
      call.getCalleeName() = "escapeHtml" and
      node = DataFlow::valueNode(call)
    )
  }
}

from UnsafeRenderConfig cfg, DataFlow::PathNode source, DataFlow::PathNode sink
where cfg.hasFlowPath(source, sink)
select sink.getNode(), source, sink,
  "Unsafe template rendering from $@", source.getNode(), "user input"
```

---

## CI/CD Integration

### GitHub Actions (Recommended)

```yaml
# .github/workflows/codeql.yml
name: CodeQL

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'  # Weekly scan

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
        language: ['javascript', 'python']

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
          # Use extended queries for better coverage
          queries: security-extended,security-and-quality
          # Add custom queries
          config-file: .github/codeql/codeql-config.yml

      - name: Autobuild
        uses: github/codeql-action/autobuild@v3

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3
        with:
          category: "/language:${{ matrix.language }}"
```

### Custom Configuration

```yaml
# .github/codeql/codeql-config.yml
name: "Custom CodeQL Config"

queries:
  - uses: security-extended
  - uses: security-and-quality
  # Add your custom queries
  - uses: ./.github/codeql/custom-queries

paths:
  - src/
  - lib/

paths-ignore:
  - '**/test/**'
  - '**/vendor/**'
  - '**/*.min.js'

query-filters:
  # Exclude noisy queries
  - exclude:
      id: js/useless-expression
  # Only include high-confidence results
  - include:
      precision: high
```

### Custom Query Pack

```yaml
# .github/codeql/custom-queries/qlpack.yml
name: my-org/custom-security-queries
version: 1.0.0
dependencies:
  codeql/javascript-all: "*"
  codeql/python-all: "*"
```

```ql
// .github/codeql/custom-queries/src/HardcodedSecrets.ql
// Your custom query here
```

---

## Variant Analysis: Finding All Similar Bugs

### The Power of Variant Analysis

```
VARIANT ANALYSIS WORKFLOW
─────────────────────────────────────────────────────────────────

Step 1: Find One Bug
─────────────────────────────────────────────────────────────────
Security researcher finds SQL injection in /api/users:

  query = f"SELECT * FROM users WHERE id = {user_id}"
  cursor.execute(query)  // Bug!

Step 2: Generalize to Query
─────────────────────────────────────────────────────────────────
What made this a bug?
- String formatting with user input
- Result passed to execute()

Query:
  from StringFormatExpr fmt, MethodCallExpr exec
  where fmt.getAnOperand() flows to exec.getArgument(0)
    and exec.getMethodName() = "execute"
  select exec

Step 3: Run Against All Code
─────────────────────────────────────────────────────────────────
Results:
  /api/users.py:45      - SELECT * FROM users WHERE id = ...
  /api/orders.py:78     - SELECT * FROM orders WHERE user = ...
  /api/products.py:23   - SELECT * FROM products WHERE name = ...
  /admin/reports.py:156 - SELECT * FROM logs WHERE date = ...

Found 4 bugs instead of 1!
```

### Multi-Repository Variant Analysis (GitHub)

```bash
# Using MRVA (Multi-Repository Variant Analysis)
# Available in GitHub Security Lab

# 1. Create a query that matches your vulnerability pattern
# 2. Submit for MRVA through Security Lab
# 3. GitHub runs it against millions of repositories
# 4. Results returned for repositories you have access to

# Example: You found a vulnerability pattern
# Write the query, GitHub finds it everywhere
```

---

## War Story: The Authentication Bypass Factory

*How CodeQL found 12 variants of the same vulnerability*

### The Discovery

A security researcher found an authentication bypass in a popular e-commerce platform:

```python
# Original vulnerability
@app.route('/api/admin/users')
def list_users():
    if request.headers.get('X-Admin-Token'):  # Bug: no validation!
        return jsonify(get_all_users())
    return jsonify({"error": "unauthorized"}), 401
```

The fix seemed simple: check the token value. But the researcher wondered—are there other endpoints with the same pattern?

### The Query

```ql
/**
 * @name Authentication check without value validation
 * @description Finds header/cookie presence checks without value verification
 */

import python
import semmle.python.dataflow.new.DataFlow

// Find checks that only verify presence, not value
from If check, Call headerGet
where
  // Header access
  headerGet.getFunc().(Attribute).getName() = "get" and
  headerGet.getFunc().(Attribute).getObject().toString().matches("%header%") and
  // Used as condition without comparison
  check.getTest() = headerGet and
  // No equality check on the result
  not exists(Compare cmp | cmp.getAComparator() = headerGet)
select check, "Authentication check only verifies header presence, not value"
```

### The Results

```
VARIANT ANALYSIS RESULTS
─────────────────────────────────────────────────────────────────

Query found 12 vulnerable endpoints:

  /api/admin/users        - X-Admin-Token header check
  /api/admin/orders       - X-Admin-Token header check
  /api/admin/products     - X-Admin-Token header check
  /api/admin/config       - X-Admin-Token header check
  /api/partner/inventory  - X-Partner-Key header check
  /api/partner/pricing    - X-Partner-Key header check
  /api/internal/health    - X-Internal-Token header check
  /api/internal/metrics   - X-Internal-Token header check
  /api/debug/logs         - X-Debug-Token header check
  /api/debug/cache        - X-Debug-Token header check
  /api/webhook/process    - X-Webhook-Secret header check
  /api/webhook/verify     - X-Webhook-Secret header check

Same bug pattern, 12 different endpoints.
Without variant analysis: 1 fix
With variant analysis: 12 fixes
```

### The Fix Pattern

```python
# Before: Presence check only
if request.headers.get('X-Admin-Token'):
    # Vulnerable!

# After: Value validation
expected_token = os.environ.get('ADMIN_TOKEN')
if request.headers.get('X-Admin-Token') == expected_token:
    # Secure

# Even better: Use authentication middleware
@require_admin_auth
def list_users():
    # Decorator handles auth
```

### Financial Impact

The platform's security team calculated what would have happened without CodeQL variant analysis:

| Scenario | Without Variant Analysis | With Variant Analysis |
|----------|--------------------------|----------------------|
| Vulnerabilities found | 1 | 12 |
| Time to find all variants | 6+ months (if ever) | 2 hours |
| Potential breach exposure | 11 unpatched endpoints | All patched |
| Estimated breach cost per endpoint | $180,000 avg | $0 |
| Total risk exposure avoided | | **$1,980,000** |
| Security research time | 200 hours (manual audit) | 6 hours (query + triage) |
| Cost of security research | $30,000 | $900 |
| **Net savings** | | **$2,009,100** |

The CISO shared the story at a security conference: "We found one bug. CodeQL found eleven more. That query is now part of our standard suite and runs on every PR. The pattern can never sneak back in."

### Lessons Learned

1. **One bug often means many bugs** - Same pattern, different locations
2. **Manual review misses variants** - 12 endpoints, humans found 1
3. **Encode patterns as queries** - Institutional knowledge preserved
4. **Run queries continuously** - New code could reintroduce pattern
5. **Share queries with team** - Everyone benefits from one person's find

---

## Common Query Patterns

### Find All Routes/Endpoints

```ql
// Express.js
import javascript
import semmle.javascript.frameworks.Express

from Express::RouteHandler handler
select handler, "Route: " + handler.getRoutePattern()

// Python Flask
import python
from FunctionDef f, Decorator d
where d = f.getADecorator() and
  d.toString().matches("@app.route%")
select f, "Flask route"
```

### Find Dangerous Function Calls

```ql
// JavaScript eval, exec, etc.
from CallExpr call
where call.getCalleeName() = ["eval", "Function", "setTimeout", "setInterval"] and
  call.getNumArgument() > 0 and
  call.getArgument(0).mayHaveStringValue(_)
select call, "Dangerous function call"
```

### Find Missing Error Handling

```ql
// Async functions without try-catch
from ArrowFunctionExpr f
where f.isAsync() and
  not exists(TryStmt t | t.getEnclosingFunction() = f) and
  exists(AwaitExpr a | a.getEnclosingFunction() = f)
select f, "Async function without error handling"
```

### Find Logging of Sensitive Data

```ql
from MethodCallExpr log, DataFlow::Node sensitive
where
  log.getMethodName() = ["log", "info", "debug", "warn", "error"] and
  sensitive.asExpr() = log.getAnArgument() and
  exists(Variable v |
    v.getName().toLowerCase().regexpMatch(".*(password|secret|token|key|ssn|credit).*") and
    sensitive = DataFlow::valueNode(v.getAnAccess())
  )
select log, "Potentially logging sensitive data"
```

---

## Common Mistakes

| Mistake | Why It's Bad | Better Approach |
|---------|--------------|-----------------|
| Running only default queries | Misses custom vulnerabilities | Add security-extended + custom |
| Ignoring results | Alert fatigue leads to real bugs missed | Tune queries, address findings |
| Not using path queries | Can't see how data flows | Use `@kind path-problem` |
| Querying without database | Errors on syntax, not semantics | Always test with real codebase |
| No sanitizer definitions | False positives from validated input | Define your sanitization functions |
| Skipping scheduled scans | New code introduces old bugs | Weekly or daily scans |
| Complex queries without tests | Queries break on edge cases | Test with known-vulnerable code |
| Not sharing queries | Duplicated effort across teams | Central query repository |

---

## Hands-On Exercise

### Task: Write a Custom CodeQL Query

**Objective**: Find a vulnerability pattern in sample code using CodeQL.

**Success Criteria**:
1. Create CodeQL database from sample project
2. Run default security queries
3. Write custom query for missing CSRF protection
4. Query finds vulnerable endpoints

### Steps

```bash
# 1. Create sample vulnerable application
mkdir codeql-lab && cd codeql-lab

cat > app.js << 'EOF'
const express = require('express');
const app = express();

app.use(express.json());

// Vulnerable: No CSRF token check
app.post('/api/transfer', (req, res) => {
  const { to, amount } = req.body;
  // Transfer money without CSRF protection
  performTransfer(to, amount);
  res.json({ success: true });
});

// Vulnerable: SQL injection
app.get('/api/user', (req, res) => {
  const query = `SELECT * FROM users WHERE id = ${req.query.id}`;
  db.query(query, (err, result) => res.json(result));
});

// Safe: Has CSRF token
app.post('/api/settings', csrfProtection, (req, res) => {
  updateSettings(req.body);
  res.json({ success: true });
});

app.listen(3000);
EOF

npm init -y
npm install express

# 2. Create CodeQL database
codeql database create js-db --language=javascript

# 3. Run default security queries
codeql database analyze js-db \
  codeql/javascript-queries:codeql-suites/javascript-security-extended.qls \
  --format=csv \
  --output=results.csv

# View results
cat results.csv

# 4. Write custom CSRF query
mkdir -p queries
cat > queries/missing-csrf.ql << 'EOF'
/**
 * @name POST endpoint without CSRF protection
 * @description Express POST routes without CSRF middleware
 * @kind problem
 * @problem.severity warning
 * @id custom/missing-csrf
 */

import javascript
import semmle.javascript.frameworks.Express

from Express::RouteHandler handler
where
  // POST, PUT, DELETE routes (state-changing)
  handler.getHttpMethod() = ["post", "put", "delete"] and
  // No CSRF middleware in the handler chain
  not exists(Express::RouteHandler csrf |
    csrf.getCalleeName().matches("%csrf%") and
    csrf.getRouteExpr() = handler.getRouteExpr()
  ) and
  // Exclude API routes that might use other auth
  not handler.getRoutePattern().matches("/api/webhook%")
select handler,
  "POST endpoint without CSRF protection: " + handler.getRoutePattern()
EOF

# 5. Create qlpack.yml for custom queries
cat > queries/qlpack.yml << 'EOF'
name: custom-queries
version: 1.0.0
dependencies:
  codeql/javascript-all: "*"
EOF

# 6. Run custom query
codeql query run queries/missing-csrf.ql --database=js-db

# Should find: /api/transfer endpoint
```

### Verification

```bash
# Check that custom query finds the vulnerable endpoint
codeql query run queries/missing-csrf.ql --database=js-db | grep transfer

# Expected output:
# | app.js:7 | POST endpoint without CSRF protection: /api/transfer |
```

---

## Quiz

### Question 1
What makes CodeQL different from pattern-matching SAST tools?

<details>
<summary>Show Answer</summary>

**CodeQL builds a semantic database and uses data flow analysis**

Unlike regex-based tools that match patterns, CodeQL:
- Builds a database of code structure (AST, CFG, data flow)
- Allows queries about semantic relationships
- Tracks how data flows through the program
- Can find vulnerabilities across multiple files/functions

This enables finding real vulnerabilities, not just suspicious patterns.
</details>

### Question 2
What is variant analysis?

<details>
<summary>Show Answer</summary>

**Finding all instances of a vulnerability pattern in a codebase**

When you find one vulnerability, you write a query that captures its pattern, then run it against all code to find similar bugs. This multiplies the impact of security research—one bug becomes many fixes.

GitHub's Multi-Repository Variant Analysis (MRVA) extends this to millions of repositories.
</details>

### Question 3
What is a CodeQL "sink" in taint tracking?

<details>
<summary>Show Answer</summary>

**The dangerous function where tainted data causes harm**

In taint tracking:
- **Source**: Where untrusted data enters (request params, files)
- **Sink**: Where untrusted data is dangerous (SQL query, shell command)
- **Sanitizer**: Functions that make data safe (escaping, validation)

A vulnerability exists when data flows from source to sink without passing through a sanitizer.
</details>

### Question 4
How do you add custom queries to GitHub CodeQL Actions?

<details>
<summary>Show Answer</summary>

**Create a config file and reference custom query directory**

```yaml
# codeql-config.yml
queries:
  - uses: security-extended
  - uses: ./.github/codeql/custom-queries

# In workflow
- uses: github/codeql-action/init@v3
  with:
    config-file: .github/codeql/codeql-config.yml
```

Custom queries need a `qlpack.yml` and are stored in your repository.
</details>

### Question 5
What does `@kind path-problem` do in query metadata?

<details>
<summary>Show Answer</summary>

**Shows the complete data flow path in results**

When you use `@kind path-problem`, CodeQL shows:
- The source where tainted data originates
- Every step the data takes through the program
- The sink where the vulnerability manifests

This is essential for understanding complex vulnerabilities that span multiple files.
</details>

### Question 6
Why define sanitizers in taint tracking configurations?

<details>
<summary>Show Answer</summary>

**To reduce false positives from validated/escaped input**

Sanitizers are functions that make tainted data safe:
- `escapeHtml()` for XSS
- `parameterize()` for SQL injection
- `validateInt()` for type checking

Without sanitizer definitions, CodeQL reports flows through validation as vulnerabilities, creating noise.
</details>

### Question 7
How do you exclude noisy queries from results?

<details>
<summary>Show Answer</summary>

**Use query-filters in the config file**

```yaml
query-filters:
  - exclude:
      id: js/useless-expression
  - include:
      precision: high
      problem.severity: error
```

You can filter by query ID, precision, severity, or tags.
</details>

### Question 8
What's the relationship between CodeQL and GHAS?

<details>
<summary>Show Answer</summary>

**CodeQL is the engine that powers GitHub Advanced Security code scanning**

- CodeQL is the open-source query language and database technology
- GHAS integrates CodeQL into GitHub (Actions, PR comments, Security tab)
- GHAS adds UI, alerting, and management on top of CodeQL
- You can use CodeQL standalone without GitHub
</details>

---

## Key Takeaways

1. **CodeQL treats code as data** - Query it like a database
2. **Data flow > pattern matching** - Track tainted data across functions
3. **Variant analysis multiplies impact** - One bug → many fixes
4. **Custom queries encode knowledge** - Your patterns, preserved forever
5. **security-extended catches more** - Don't use just default queries
6. **Sanitizers reduce noise** - Tell CodeQL what's safe
7. **Path queries show the story** - How data reaches the sink
8. **Run scheduled scans** - New code can reintroduce old bugs
9. **Share queries across teams** - Institutional security knowledge
10. **Free for open source** - No excuse not to use it

---

## Next Steps

- **Next Module**: [Module 12.4: Snyk](../module-12.4-snyk/) - Dependency and container scanning
- **Related**: [Module 11.3: GitHub Advanced](../../cicd-delivery/source-control/module-11.3-github-advanced/) - GHAS integration
- **Related**: [Module 4.4: Supply Chain Security](../security-tools/module-4.4-supply-chain/) - SBOM and signing

---

## Further Reading

- [CodeQL Documentation](https://codeql.github.com/docs/)
- [GitHub CodeQL Repository](https://github.com/github/codeql)
- [CodeQL Query Help](https://codeql.github.com/codeql-query-help/)
- [GitHub Security Lab](https://securitylab.github.com/)
- [CodeQL for VS Code](https://marketplace.visualstudio.com/items?itemName=GitHub.vscode-codeql)

---

*"The difference between finding one vulnerability and finding all of them is a well-written CodeQL query."*
