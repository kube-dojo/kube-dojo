---
title: "Module 12.2: Semgrep - Security Rules in Minutes"
slug: platform/toolkits/security-quality/code-quality/module-12.2-semgrep
sidebar:
  order: 3
---
## Complexity: [MEDIUM]
## Time to Complete: 45-50 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [Module 12.1: SonarQube](../module-12.1-sonarqube/) - Code quality fundamentals
- [DevSecOps Discipline](../../../disciplines/reliability-security/devsecops/) - Security integration concepts
- Basic regex understanding
- Programming experience in at least one language

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy Semgrep and configure custom rules for security-focused static analysis in CI/CD pipelines**
- **Implement Semgrep patterns for detecting OWASP vulnerabilities and insecure coding practices**
- **Configure Semgrep's autofix capabilities to automatically remediate detected code issues**
- **Compare Semgrep's pattern-based approach against CodeQL for security scanning speed and coverage trade-offs**


## Why This Module Matters

**The Custom Rule Problem**

You've just discovered a security issue in your codebase: developers are calling `dangerouslySetInnerHTML` in React without sanitization. You want to prevent this from happening again. You have two options:

**Option 1: Traditional SAST Rule**
1. Learn the SAST tool's proprietary rule language
2. Spend days understanding AST representations
3. Write and debug complex rule definitions
4. Wait for vendor to ship the update
5. Hope it doesn't break existing rules

**Option 2: Semgrep**
```yaml
rules:
  - id: dangerous-html-without-sanitize
    pattern: dangerouslySetInnerHTML={{__html: $X}}
    pattern-not: dangerouslySetInnerHTML={{__html: sanitize($X)}}
    message: "Use sanitize() before dangerouslySetInnerHTML"
    severity: ERROR
    languages: [javascript, typescript]
```

Five minutes. That's how long it takes to write a Semgrep rule. The pattern syntax looks like code, not regex hell. You can test it locally before committing. And it runs fast enough to block PRs without developers revolting.

Semgrep isn't trying to be the most sophisticated SAST tool—it's trying to be the most practical one. Low false positives, fast execution, and rules that humans can actually write and understand.

---

## Semgrep Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SEMGREP ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  YOUR CODEBASE                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  source.py    │  app.js    │  main.go    │  Server.java   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  SEMGREP ENGINE                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐ │  │
│  │  │   Parser    │   │  Pattern    │   │    Matching     │ │  │
│  │  │ (per lang)  │──▶│  Compiler   │──▶│    Engine       │ │  │
│  │  │             │   │             │   │  (semgrep-core) │ │  │
│  │  └─────────────┘   └─────────────┘   └─────────────────┘ │  │
│  │         │                                     │          │  │
│  │         ▼                                     ▼          │  │
│  │  ┌─────────────┐                    ┌─────────────────┐  │  │
│  │  │    AST      │                    │    Findings     │  │  │
│  │  │ (generic)   │                    │    (JSON/SARIF) │  │  │
│  │  └─────────────┘                    └─────────────────┘  │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  RULES                       │                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  Community    │  Your Custom    │  Semgrep Registry      │  │
│  │  Rulesets     │  Rules          │  (pro rules)           │  │
│  │  (p/owasp)    │  (.semgrep/)    │  (additional coverage) │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### How Semgrep Works

1. **Parse**: Convert source code to AST (Abstract Syntax Tree)
2. **Pattern Match**: Match your pattern against the AST
3. **Filter**: Apply `pattern-not`, `pattern-inside`, etc.
4. **Report**: Output findings in JSON, SARIF, or text

The key insight: Semgrep patterns look like code, but match against the AST. This means `foo(1, 2)` matches `foo(1,2)` and `foo( 1 , 2 )` because whitespace doesn't matter in the AST.

---

## Pattern Syntax Deep Dive

### Basic Patterns

```yaml
# Literal match
pattern: print("debug")

# Metavariable (captures any expression)
pattern: print($X)
# Matches: print("hello"), print(user.name), print(1+2)

# Ellipsis (matches zero or more arguments)
pattern: print(...)
# Matches: print(), print("a"), print("a", "b", "c")

# Typed metavariable (Python 3 type hints)
pattern: def $FUNC(...) -> str: ...
# Matches functions returning str
```

### Metavariables in Action

```yaml
rules:
  - id: hardcoded-password
    patterns:
      - pattern: $VAR = "..."
      - metavariable-regex:
          metavariable: $VAR
          regex: (?i)(password|passwd|pwd|secret|token|api_key)
    message: "Hardcoded credential in $VAR"
    severity: ERROR
    languages: [python]
```

```python
# Would match:
password = "hunter2"
API_KEY = "sk-1234567890"
db_passwd = "supersecret"

# Would NOT match:
username = "admin"
description = "password reset flow"
```

### Combining Patterns

```yaml
rules:
  - id: sql-injection
    patterns:
      # Must match this
      - pattern-either:
          - pattern: cursor.execute($QUERY)
          - pattern: db.query($QUERY)
      # AND must have string concat in query
      - pattern-inside: |
          $QUERY = ... + $USER_INPUT + ...
          ...
      # But NOT if parameterized
      - pattern-not-inside: |
          $QUERY = "... %s ..."
          ...
          cursor.execute($QUERY, ...)
    message: "SQL injection via string concatenation"
    severity: ERROR
    languages: [python]
```

### Pattern Operators Reference

| Operator | Purpose | Example |
|----------|---------|---------|
| `pattern` | Match this pattern | `pattern: eval($X)` |
| `pattern-not` | Don't match this | `pattern-not: eval("safe")` |
| `pattern-either` | Match any of these | Multiple patterns, OR logic |
| `pattern-inside` | Match inside this context | Function or class scope |
| `pattern-not-inside` | Don't match in this context | Exclude test files |
| `pattern-regex` | Regex on source | For when AST isn't enough |
| `metavariable-regex` | Regex on captured var | Filter by variable name |
| `metavariable-pattern` | Pattern on captured var | Nested matching |
| `metavariable-comparison` | Compare captured values | `$X < 10` |
| `focus-metavariable` | Report only this part | Precise error location |

---

## Real-World Rules

### Preventing JWT Without Verification

```yaml
rules:
  - id: jwt-decode-without-verify
    patterns:
      - pattern-either:
          - pattern: jwt.decode($TOKEN, ...)
          - pattern: jwt.decode($TOKEN)
      - pattern-not: jwt.decode($TOKEN, $KEY, ...)
      - pattern-not: jwt.decode($TOKEN, options={..., verify=True, ...})
    message: |
      JWT decoded without signature verification.
      Use jwt.decode(token, key, algorithms=['HS256']) instead.
    severity: ERROR
    languages: [python]
    metadata:
      cwe: "CWE-347: Improper Verification of Cryptographic Signature"
      owasp: "A02:2021 - Cryptographic Failures"
```

### Detecting Insecure Deserialization

```yaml
rules:
  - id: pickle-load-untrusted
    patterns:
      - pattern-either:
          - pattern: pickle.load($X)
          - pattern: pickle.loads($X)
      - pattern-not-inside: |
          # Safe: loading from trusted source
          with open("$TRUSTED_FILE", ...) as $F:
              ...
              pickle.load($F)
    message: |
      pickle.load() can execute arbitrary code. Never unpickle untrusted data.
      Use JSON or a safe serialization format instead.
    severity: ERROR
    languages: [python]
    metadata:
      cwe: "CWE-502: Deserialization of Untrusted Data"
      references:
        - https://docs.python.org/3/library/pickle.html#module-pickle
```

### React XSS Prevention

```yaml
rules:
  - id: react-dangerously-set-html
    patterns:
      - pattern: dangerouslySetInnerHTML={{__html: $CONTENT}}
      - pattern-not: dangerouslySetInnerHTML={{__html: DOMPurify.sanitize($CONTENT)}}
      - pattern-not: dangerouslySetInnerHTML={{__html: sanitizeHtml($CONTENT, ...)}}
    message: |
      dangerouslySetInnerHTML without sanitization may cause XSS.
      Use DOMPurify.sanitize() or similar.
    severity: ERROR
    languages: [javascript, typescript, jsx, tsx]
    metadata:
      cwe: "CWE-79: Cross-site Scripting (XSS)"
```

### Go Error Handling

```yaml
rules:
  - id: go-error-not-handled
    patterns:
      - pattern: $RET, $ERR := $FUNC(...)
      - pattern-not-inside: |
          $RET, $ERR := $FUNC(...)
          ...
          if $ERR != nil { ... }
    message: "Error returned by $FUNC is not checked"
    severity: WARNING
    languages: [go]
```

### Kubernetes Security

```yaml
rules:
  - id: k8s-privileged-container
    patterns:
      - pattern-inside: |
          spec:
            ...
            containers:
              ...
      - pattern: |
          securityContext:
            ...
            privileged: true
    message: "Container running in privileged mode"
    severity: ERROR
    languages: [yaml]
    paths:
      include:
        - "*.yaml"
        - "*.yml"
```

---

## Using Semgrep CLI

### Installation

```bash
# macOS
brew install semgrep

# Linux/Windows (pip)
pip install semgrep

# Docker
docker run --rm -v "$(pwd):/src" returntocorp/semgrep

# Verify installation
semgrep --version
```

### Running Scans

```bash
# Run community rules
semgrep --config=auto .

# Run specific rulesets
semgrep --config=p/owasp-top-ten .
semgrep --config=p/security-audit .
semgrep --config=p/secrets .

# Run your custom rules
semgrep --config=.semgrep/ .

# Combine rulesets
semgrep --config=p/python --config=.semgrep/ .

# Output formats
semgrep --config=auto --json -o results.json .
semgrep --config=auto --sarif -o results.sarif .

# Verbose for debugging
semgrep --config=rule.yaml --verbose .

# Test rules
semgrep --test --config=.semgrep/
```

### Filtering Results

```bash
# By severity
semgrep --config=auto --severity ERROR .

# Exclude paths
semgrep --config=auto --exclude tests/ --exclude vendor/ .

# Include only certain paths
semgrep --config=auto --include "*.py" .

# Baseline (only new findings)
semgrep --config=auto --baseline-commit HEAD~1 .
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Semgrep
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  semgrep:
    runs-on: ubuntu-latest
    container:
      image: returntocorp/semgrep
    steps:
      - uses: actions/checkout@v4

      - name: Run Semgrep
        run: |
          semgrep ci \
            --config=p/security-audit \
            --config=p/secrets \
            --config=.semgrep/ \
            --sarif --output=semgrep.sarif

      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: semgrep.sarif
        if: always()
```

### GitLab CI

```yaml
semgrep:
  stage: test
  image: returntocorp/semgrep
  script:
    - semgrep ci
        --config=p/security-audit
        --config=.semgrep/
        --gitlab-sast > gl-sast-report.json
  artifacts:
    reports:
      sast: gl-sast-report.json
  rules:
    - if: $CI_MERGE_REQUEST_IID
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/returntocorp/semgrep
    rev: v1.45.0
    hooks:
      - id: semgrep
        args: ['--config', 'p/secrets', '--config', '.semgrep/', '--error']
```

### Jenkins Pipeline

```groovy
pipeline {
    agent {
        docker {
            image 'returntocorp/semgrep'
        }
    }
    stages {
        stage('Security Scan') {
            steps {
                sh '''
                    semgrep ci \
                        --config=p/security-audit \
                        --config=.semgrep/ \
                        --junit-xml --output=semgrep-results.xml
                '''
                junit 'semgrep-results.xml'
            }
        }
    }
}
```

---

## Writing Custom Rules

### Rule Structure

```yaml
rules:
  - id: unique-rule-identifier
    # What to match
    pattern: dangerous_function($X)
    # Or more complex matching
    patterns:
      - pattern: ...
      - pattern-not: ...

    # Metadata
    message: "Human readable message with $X interpolation"
    severity: ERROR  # ERROR, WARNING, INFO
    languages: [python, javascript]  # Target languages

    # Optional metadata
    metadata:
      cwe: "CWE-XXX"
      owasp: "A0X:2021"
      category: security
      technology:
        - flask
      references:
        - https://example.com/security-advisory

    # File filtering
    paths:
      include:
        - "src/**/*.py"
      exclude:
        - "**/test/**"
        - "**/*_test.py"

    # Fix suggestion (autofix)
    fix: safe_function($X)
```

### Testing Rules

```python
# test_rule.py - Semgrep test file format

# ruleid: dangerous-function
dangerous_function(user_input)

# ok: dangerous-function
safe_function(user_input)

# todoruleid: dangerous-function
# This should match but doesn't yet
edge_case(user_input)
```

```bash
# Run tests
semgrep --test --config=rules/
```

### Example: Building a Complete Ruleset

```yaml
# .semgrep/flask-security.yaml
rules:
  # Flask Debug Mode
  - id: flask-debug-mode
    pattern: app.run(..., debug=True, ...)
    message: "Flask debug mode enabled. Disable in production."
    severity: ERROR
    languages: [python]
    metadata:
      category: security
      cwe: "CWE-489: Active Debug Code"

  # Flask Secret Key Hardcoded
  - id: flask-hardcoded-secret
    patterns:
      - pattern: app.secret_key = "..."
      - pattern: app.config["SECRET_KEY"] = "..."
    message: "Hardcoded Flask secret key. Use environment variable."
    severity: ERROR
    languages: [python]
    fix: app.secret_key = os.environ.get("SECRET_KEY")

  # Flask SQL Injection
  - id: flask-sql-injection
    patterns:
      - pattern-either:
          - pattern: db.execute($QUERY.format(...))
          - pattern: db.execute(f"...$X...")
          - pattern: db.execute("..." + $X + "...")
    message: "SQL injection via string formatting. Use parameterized queries."
    severity: ERROR
    languages: [python]
    metadata:
      cwe: "CWE-89: SQL Injection"

  # Missing CSRF Protection
  - id: flask-missing-csrf
    patterns:
      - pattern: |
          @app.route(..., methods=[..., "POST", ...])
          def $FUNC(...):
              ...
      - pattern-not-inside: |
          csrf = CSRFProtect(...)
          ...
    message: "POST route without CSRF protection"
    severity: WARNING
    languages: [python]
```

---

## Semgrep vs Other Tools

```
COMPARISON MATRIX
─────────────────────────────────────────────────────────────────

                    Semgrep      CodeQL       SonarQube
─────────────────────────────────────────────────────────────────
Rule Language       Pattern      QL (SQL-like) Java/Custom
Learning Curve      Low          High         Medium
Custom Rules        Easy         Complex      Difficult
Speed               Fast         Slow         Medium
False Positives     Low          Low          Medium
Languages           30+          15+          30+
Self-hosted         Free         Free         Limited
CI Integration      Excellent    Good         Good
Dataflow Analysis   Pro tier     Excellent    Basic
Interfile Analysis  Pro tier     Excellent    Yes

─────────────────────────────────────────────────────────────────

WHEN TO USE EACH:

Semgrep:
• Custom rules for your specific patterns
• Fast feedback in CI/CD
• Security team writing rules
• Low false positive tolerance

CodeQL:
• Deep vulnerability research
• Complex dataflow analysis
• GitHub-centric workflows
• Time/complexity not a concern

SonarQube:
• Code quality + security together
• Technical debt tracking needed
• Quality gates with coverage
• Enterprise compliance reporting
```

---

## War Story: The Framework Migration

**Company**: Payment processor, 80 engineers
**Challenge**: Migrating from deprecated crypto library to new standard

**The Situation**:

The security team discovered that the `old-crypto` library had known vulnerabilities. 500+ files used it across 12 services. Manual migration would take months and be error-prone.

**The Semgrep Approach**:

```yaml
# Phase 1: Find all usages
rules:
  - id: old-crypto-usage
    pattern-either:
      - pattern: import old_crypto
      - pattern: from old_crypto import ...
      - pattern: old_crypto.$FUNC(...)
    message: "Legacy crypto library usage. Migrate to new_crypto."
    severity: WARNING
    languages: [python]
```

```bash
# Baseline scan
$ semgrep --config=migration.yaml --json -o baseline.json .
Found: 847 usages across 523 files
```

```yaml
# Phase 2: Add autofix rules
rules:
  - id: migrate-encrypt
    pattern: old_crypto.encrypt($DATA, $KEY)
    fix: new_crypto.encrypt($DATA, key=$KEY, algorithm="AES-256-GCM")
    message: "Migrate to new_crypto.encrypt()"
    severity: WARNING
    languages: [python]

  - id: migrate-hash
    pattern: old_crypto.hash($DATA)
    fix: new_crypto.hash($DATA, algorithm="SHA-256")
    message: "Migrate to new_crypto.hash()"
    severity: WARNING
    languages: [python]
```

```bash
# Apply autofixes
$ semgrep --config=migration.yaml --autofix .
Applied 623 fixes automatically
```

```yaml
# Phase 3: Block new usages
rules:
  - id: block-old-crypto
    pattern-either:
      - pattern: import old_crypto
      - pattern: from old_crypto import ...
    message: |
      BLOCKED: old_crypto is deprecated.
      Use new_crypto instead. See migration guide: wiki/crypto-migration
    severity: ERROR
    languages: [python]
```

**Results**:

| Phase | Timeline | Effort |
|-------|----------|--------|
| Find all usages | 30 minutes | Automated |
| Auto-fix 75% of usages | 2 hours | Review only |
| Manual fix remaining 25% | 2 weeks | Edge cases |
| Block new usages | Permanent | Zero effort |

**Total Time**: 2 weeks instead of estimated 3 months

**Key Lessons**:
1. **Start with WARNING, graduate to ERROR**: Let developers fix before blocking
2. **Autofix where possible**: Review is faster than rewrite
3. **Leave blocking rules permanently**: Prevent regression
4. **Track progress with baseline**: Show weekly improvement to management

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Too specific patterns | Misses variations | Use metavariables, ellipsis |
| Too broad patterns | False positives | Add pattern-not exclusions |
| No testing | Rules break silently | Use semgrep --test |
| Ignoring metadata | Poor findings context | Add CWE, OWASP, references |
| Running all rules | Slow CI, noise | Curate rulesets for your stack |
| No baseline | Old findings block PRs | Use --baseline-commit |
| No autofix | Developers ignore findings | Add fix when pattern is clear |
| Single pattern only | Can't handle context | Combine with pattern-inside |

---

## Quiz

<details>
<summary>1. What is the difference between $X and ... in Semgrep patterns?</summary>

**Answer**:
- `$X` (metavariable): Captures a single expression and can be referenced elsewhere in the rule. Use to match specific values and reference them in the message or fix.

- `...` (ellipsis): Matches zero or more arguments, statements, or fields. Use when you don't care about the specific content.

Examples:
```yaml
# $X captures the argument
pattern: eval($X)
message: "eval called with $X"  # $X is interpolated

# ... matches any arguments
pattern: print(...)  # Matches print(), print(a), print(a, b, c)
```
</details>

<details>
<summary>2. How do pattern-inside and pattern-not-inside work?</summary>

**Answer**: They provide context for where patterns should (or shouldn't) match:

```yaml
patterns:
  # Match eval()
  - pattern: eval($X)
  # Only inside request handlers
  - pattern-inside: |
      @app.route(...)
      def $FUNC(...):
          ...
  # But not inside admin routes
  - pattern-not-inside: |
      @app.route("/admin/...")
      def $FUNC(...):
          ...
```

The primary `pattern` must match, AND it must be inside `pattern-inside`, AND it must NOT be inside `pattern-not-inside`.
</details>

<details>
<summary>3. What is metavariable-regex used for?</summary>

**Answer**: `metavariable-regex` applies a regex filter to a captured metavariable:

```yaml
patterns:
  - pattern: $VAR = "..."
  - metavariable-regex:
      metavariable: $VAR
      regex: (?i)(password|secret|token|api_key)
```

This matches variable assignments where the variable name looks like a credential. Without metavariable-regex, you'd match every string assignment.

Use cases:
- Variable naming conventions
- String content patterns
- Filtering by function names
</details>

<details>
<summary>4. How does Semgrep's autofix feature work?</summary>

**Answer**: The `fix` field provides a replacement pattern:

```yaml
rules:
  - id: use-pathlib
    pattern: os.path.join($A, $B)
    fix: Path($A) / $B
    message: "Use pathlib instead of os.path.join"
```

Running `semgrep --autofix`:
1. Finds all matches
2. Applies the fix pattern
3. Interpolates captured metavariables
4. Rewrites the file

Limitations:
- Must preserve captured metavariables exactly
- Complex fixes may need manual intervention
- Always review changes before committing
</details>

<details>
<summary>5. What are Semgrep's community rulesets and how do you use them?</summary>

**Answer**: Community rulesets are curated rule collections:

```bash
# Popular rulesets
semgrep --config=p/owasp-top-ten .     # OWASP vulnerabilities
semgrep --config=p/security-audit .    # General security
semgrep --config=p/secrets .           # Hardcoded secrets
semgrep --config=p/python .            # Python-specific
semgrep --config=p/javascript .        # JavaScript/TypeScript
semgrep --config=p/ci .                # CI/CD misconfigurations

# Auto (detects languages, picks relevant rules)
semgrep --config=auto .

# Combine multiple
semgrep --config=p/security-audit --config=p/secrets --config=.semgrep/ .
```

Registry at: https://semgrep.dev/explore
</details>

<details>
<summary>6. How do you test Semgrep rules?</summary>

**Answer**: Semgrep has built-in test support:

```python
# rules/test_sql_injection.py

# ruleid: sql-injection
query = "SELECT * FROM users WHERE id = " + user_id
cursor.execute(query)

# ok: sql-injection
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# todoruleid: sql-injection
# Known false negative - tracking for future fix
```

```bash
# Run tests (looks for test files matching rules)
semgrep --test --config=rules/

# Test specific rule
semgrep --test --config=rules/sql-injection.yaml
```

Annotations:
- `# ruleid: <id>` - Should match
- `# ok: <id>` - Should NOT match
- `# todoruleid: <id>` - Known missing match (future work)
</details>

<details>
<summary>7. What is the difference between Semgrep OSS and Semgrep Pro?</summary>

**Answer**:

| Feature | OSS (Free) | Pro (Paid) |
|---------|-----------|------------|
| Pattern matching | ✓ | ✓ |
| 2000+ community rules | ✓ | ✓ |
| Custom rules | ✓ | ✓ |
| CLI & CI | ✓ | ✓ |
| Dataflow analysis | ✗ | ✓ |
| Cross-file analysis | ✗ | ✓ |
| Pro rules (deeper coverage) | ✗ | ✓ |
| Dashboard & SBOM | ✗ | ✓ |
| SSO & Teams | ✗ | ✓ |

For most teams, OSS is sufficient. Pro is valuable for:
- Finding vulnerabilities that span multiple files
- Taint tracking (source → sink analysis)
- Enterprise compliance requirements
</details>

<details>
<summary>8. How do you reduce false positives in Semgrep rules?</summary>

**Answer**: Several techniques:

1. **pattern-not exclusions**:
```yaml
patterns:
  - pattern: eval($X)
  - pattern-not: eval("literal")  # Exclude known safe
```

2. **pattern-not-inside context**:
```yaml
patterns:
  - pattern: $FUNC(...)
  - pattern-not-inside: |
      def test_$NAME(...):  # Exclude test files
          ...
```

3. **Metavariable filtering**:
```yaml
patterns:
  - pattern: $VAR = "..."
  - metavariable-regex:
      metavariable: $VAR
      regex: ^(password|secret)$  # Only specific names
```

4. **Path exclusions**:
```yaml
paths:
  exclude:
    - "**/test/**"
    - "**/vendor/**"
```

5. **Start with WARNING**: Tune before making ERROR
</details>

---

## Hands-On Exercise

**Objective**: Write custom Semgrep rules to secure a Python Flask application.

### Part 1: Setup

```bash
# Create project directory
mkdir semgrep-lab && cd semgrep-lab

# Create vulnerable Flask app
cat > app.py << 'EOF'
from flask import Flask, request, render_template_string
import subprocess
import pickle
import hashlib

app = Flask(__name__)
app.secret_key = "supersecret123"  # Hardcoded secret

@app.route("/search")
def search():
    query = request.args.get("q")
    # SQL Injection
    results = db.execute(f"SELECT * FROM items WHERE name LIKE '%{query}%'")
    return results

@app.route("/run")
def run_command():
    cmd = request.args.get("cmd")
    # Command Injection
    output = subprocess.check_output(cmd, shell=True)
    return output

@app.route("/template")
def template():
    name = request.args.get("name")
    # SSTI vulnerability
    return render_template_string(f"Hello {name}!")

@app.route("/load")
def load_data():
    data = request.get_data()
    # Insecure deserialization
    return pickle.loads(data)

@app.route("/hash")
def hash_password():
    password = request.args.get("pw")
    # Weak hash
    return hashlib.md5(password.encode()).hexdigest()

if __name__ == "__main__":
    app.run(debug=True)  # Debug in production
EOF
```

### Part 2: Run Community Rules

```bash
# Install Semgrep
pip install semgrep

# Run security audit
semgrep --config=p/security-audit --config=p/python app.py

# How many findings?
semgrep --config=p/security-audit --config=p/python app.py --json | jq '.results | length'
```

### Part 3: Write Custom Rules

```bash
# Create rules directory
mkdir -p .semgrep

# Create custom ruleset
cat > .semgrep/flask-security.yaml << 'EOF'
rules:
  # Rule 1: Hardcoded Flask secret key
  - id: flask-hardcoded-secret
    patterns:
      - pattern-either:
          - pattern: app.secret_key = "..."
          - pattern: app.config["SECRET_KEY"] = "..."
    message: |
      Hardcoded Flask secret key detected.
      Use environment variable: app.secret_key = os.environ.get("SECRET_KEY")
    severity: ERROR
    languages: [python]
    fix: app.secret_key = os.environ.get("SECRET_KEY")
    metadata:
      cwe: "CWE-798: Use of Hard-coded Credentials"

  # Rule 2: Flask debug mode
  - id: flask-debug-enabled
    pattern: app.run(..., debug=True, ...)
    message: "Flask debug mode enabled. Disable in production."
    severity: ERROR
    languages: [python]
    fix: app.run(debug=False)
    metadata:
      cwe: "CWE-489: Active Debug Code"

  # Rule 3: render_template_string with user input
  - id: flask-ssti
    patterns:
      - pattern: render_template_string($TEMPLATE)
      - pattern-inside: |
          $VAR = request.$METHOD.get(...)
          ...
    message: |
      Server-Side Template Injection (SSTI) via render_template_string.
      Use render_template() with a file instead.
    severity: ERROR
    languages: [python]
    metadata:
      cwe: "CWE-94: Code Injection"

  # Rule 4: Weak hashing (MD5/SHA1)
  - id: weak-hash-algorithm
    patterns:
      - pattern-either:
          - pattern: hashlib.md5(...)
          - pattern: hashlib.sha1(...)
    message: |
      Weak hash algorithm ($1). Use SHA-256 or better:
      hashlib.sha256($X).hexdigest()
    severity: WARNING
    languages: [python]
    metadata:
      cwe: "CWE-328: Reversible One-Way Hash"
EOF
```

### Part 4: Test Your Rules

```bash
# Create test file
cat > .semgrep/test_flask_security.py << 'EOF'
from flask import Flask, render_template_string, request
import hashlib
import os

app = Flask(__name__)

# ruleid: flask-hardcoded-secret
app.secret_key = "hardcoded"

# ok: flask-hardcoded-secret
app.secret_key = os.environ.get("SECRET_KEY")

# ruleid: flask-debug-enabled
app.run(debug=True)

# ok: flask-debug-enabled
app.run(debug=False)

# ruleid: weak-hash-algorithm
hashlib.md5(b"test")

# ok: weak-hash-algorithm
hashlib.sha256(b"test")
EOF

# Run tests
semgrep --test --config=.semgrep/
```

### Part 5: Full Scan with Custom + Community Rules

```bash
# Combined scan
semgrep --config=p/python --config=.semgrep/ app.py

# Generate report
semgrep --config=p/python --config=.semgrep/ app.py --sarif -o report.sarif

# Apply autofixes
semgrep --config=.semgrep/ app.py --autofix --dryrun  # Preview
semgrep --config=.semgrep/ app.py --autofix           # Apply
```

### Success Criteria

- [ ] Community rules find SQL injection, command injection
- [ ] Custom rule catches hardcoded secret_key
- [ ] Custom rule catches debug=True
- [ ] Custom rule catches SSTI vulnerability
- [ ] Custom rule catches MD5 usage
- [ ] All tests pass with `semgrep --test`
- [ ] Autofix correctly replaces secret_key

---

## Key Takeaways

1. **Patterns look like code** — Not regex, not a query language—actual code
2. **Metavariables capture** — `$X` matches any expression and can be referenced
3. **Combine patterns** — `pattern-inside`, `pattern-not` reduce false positives
4. **Test your rules** — Built-in testing with `# ruleid:` annotations
5. **Autofix accelerates adoption** — Developers fix faster when fix is provided
6. **Start with community rules** — 2000+ rules ready to use
7. **Layer custom on top** — Your specific patterns + community baseline
8. **Run in CI but also pre-commit** — Catch before push, block before merge
9. **Baseline for legacy code** — Don't block PRs on old findings
10. **Iterate quickly** — 5-minute rule writing means rapid security coverage

---

## Did You Know?

> **Name Origin**: Semgrep stands for "semantic grep"—grep that understands code structure, not just text. The first version was called "sgrep" before the rename.

> **Speed Secret**: Semgrep compiles patterns into a specialized matching engine written in OCaml (semgrep-core). It's designed to be fast enough for pre-commit hooks.

> **Return Path**: Semgrep was created by r2c (now Semgrep Inc.), founded by former members of Facebook's static analysis team who built Infer and Zoncolan.

> **Community Growth**: The Semgrep Registry has grown from 500 rules in 2020 to over 3000+ rules in 2024, covering security, correctness, and best practices.

---

## Next Module

Continue to [Module 12.3: CodeQL](../module-12.3-codeql/) to learn about semantic code analysis with GitHub's powerful query language for finding complex vulnerabilities.
