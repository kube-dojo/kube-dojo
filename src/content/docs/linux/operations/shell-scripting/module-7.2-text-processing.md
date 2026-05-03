---
revision_pending: false
title: "Module 7.2: Text Processing"
slug: linux/operations/shell-scripting/module-7.2-text-processing
sidebar:
  order: 3
lab:
  id: linux-7.2-text-processing
  url: https://killercoda.com/kubedojo/scenario/linux-7.2-text-processing
  duration: "35 min"
  difficulty: intermediate
  environment: ubuntu
---
# Module 7.2: Text Processing

> **Shell Scripting** | Complexity: `[MEDIUM]` | Time: 30-35 min. This chapter focuses on practical command-line analysis for operators who need accurate answers while a system is changing underneath them.

## Prerequisites

Before starting this module, make sure you can run basic Bash commands, recognize simple regular expressions, and explain why logs, process listings, and API output often need different parsing strategies.
- **Required**: [Module 7.1: Bash Fundamentals](../module-7.1-bash-fundamentals/)
- **Required**: Basic regex understanding
- **Helpful**: [Module 6.2: Log Analysis](/linux/operations/troubleshooting/module-6.2-log-analysis/)

## Learning Outcomes

After this module, you will be able to apply the classic Unix text-processing tools to real troubleshooting and automation tasks, then defend why each tool belongs in the pipeline.
- **Transform** logs and command output with `grep`, `sed`, `awk`, `jq`, `sort`, `uniq`, `tr`, `paste`, and pipelines.
- **Design** reliable parsing pipelines that choose the right boundary between plain text, delimited fields, and structured JSON.
- **Diagnose** unsafe text-processing commands before they damage files, exhaust memory, or hide important operational signals.
- **Implement** repeatable shell-analysis workflows for Linux services and Kubernetes 1.35+ clusters using `alias k=kubectl`.

## Why This Module Matters

At 02:18 on a Tuesday, an operations engineer at a regional payment processor received a page that looked harmless at first: checkout latency had climbed, but only for a handful of merchants. The dashboard showed healthy nodes, the database had spare capacity, and the newest deployment had already passed its smoke checks. The incident became expensive because the useful evidence was buried in plain text: application logs, proxy access lines, pod names, timestamps, and a JSON event feed from the platform layer. Nobody needed a new observability product during those first ten minutes; they needed the ability to carve a giant stream of text into the few lines that mattered.

The team eventually found that one partner integration was retrying a failed request path so quickly that it amplified a configuration typo into a customer-visible outage. The fastest path to the answer was not a full program. It was a sequence of small commands: `grep` to narrow the failure class, `awk` to group by endpoint and status, `sort` and `uniq` to rank repeated values, `sed` to normalize a noisy field, and `jq` to inspect the structured Kubernetes objects around the workload. That toolchain turned vague suspicion into evidence, and evidence gave the incident commander a safe mitigation.

Text processing is the daily language of Linux operations because so much operational truth appears as lines. Logs are lines, configuration files are lines, command output is often a table of lines, and even structured APIs are frequently inspected from a shell before they become dashboards or reports. When you can transform those lines deliberately, you stop treating the terminal as a place to copy and paste fragments. You start using it as a precise workbench for investigation, migration, cleanup, and automation.

This module teaches the decision-making behind the classic tools rather than presenting them as a bag of one-liners. `grep` finds records, `sed` edits streams, `awk` treats text as records and fields, and `jq` respects JSON structure instead of pretending it is plain text. The important skill is knowing which tool should own each step, how much data each step keeps in memory, and where a quick one-liner should become a script with tests and rollback.

## Reading Text as Records, Fields, and Streams

Before choosing a command, decide what shape the data has. A log line is a record, a whitespace-separated process listing is a rough field table, `/etc/passwd` is a colon-delimited file, and Kubernetes JSON is a nested document with arrays and objects. Tools fail when you lie about that shape. A regular expression can search JSON text, but it cannot safely understand whether a matching string is a field name, a field value, or a fragment inside an escaped string.

The shell pipeline model works because each command can be narrow. One command selects records, another extracts a field, another sorts, and another aggregates. This is similar to a workshop bench where each station has a purpose: one person marks the wood, one cuts, one sands, and one measures the final piece. The result is flexible, but only if every station receives material in the format it expects.

`grep` is your record selector. It reads lines and prints the ones whose text matches a pattern, which makes it excellent for logs, configuration files, and source trees. It is not a calculator, a CSV parser, or a JSON parser, and that limitation is useful because it keeps the command fast and predictable. The following examples preserve the basic search patterns you will use constantly during operations work.

```bash
# Search for pattern
grep "error" file.txt

# Case insensitive
grep -i "error" file.txt

# Show line numbers
grep -n "error" file.txt

# Count matches
grep -c "error" file.txt

# Files with matches
grep -l "error" *.log

# Files without matches
grep -L "error" *.log
```

Patterns let `grep` move beyond literal strings without turning the command into a full parser. Anchors such as `^` and `$` are useful when the position of a value matters, while alternation and counted repetition are useful when a team needs one pass over a large file. Be conservative with advanced regular-expression features in shared scripts. A lookbehind might be elegant on your laptop, but it can fail on systems where `grep -P` is unavailable or implemented differently.

```bash
# Basic patterns
grep "^Start"     # Lines starting with "Start"
grep "end$"       # Lines ending with "end"
grep "^$"         # Empty lines
grep "."          # Any character

# Extended regex (-E)
grep -E "error|warning" file.txt      # OR
grep -E "[0-9]{3}"       # Three digits
grep -E "https?"         # http or https

# Perl regex (-P)
grep -P "\d{4}-\d{2}-\d{2}"   # Date pattern
grep -P "(?<=error: ).+"      # Lookbehind
```

Context flags are powerful during incidents because they show neighboring lines without forcing you to open an editor. The tradeoff is that neighboring does not always mean causal. In a busy service, two threads can interleave messages, two containers can write to the same collector, and a buffered logger can flush later than the event occurred. Treat context as a clue that guides your next question, not as proof by itself.

```bash
# Lines before/after match
grep -B 3 "error"    # 3 lines before
grep -A 3 "error"    # 3 lines after
grep -C 3 "error"    # 3 lines both sides

# Invert match
grep -v "debug" file.txt   # Lines WITHOUT "debug"

# Only matching part
grep -o "[0-9]*" file.txt  # Extract numbers only
```

> **Stop and think**: `grep -B 3` shows the lines immediately preceding a match in the file. If multiple processes are writing to the same aggregate log stream asynchronously, does the physical line preceding the error guarantee chronological or causal relation to the error itself?

Recursive search is where `grep` becomes a codebase and filesystem investigation tool. The safest habit is to include and exclude deliberately because generated files, vendored directories, and binary blobs can waste time or produce unreadable output. When you know the file family you are searching, tell the command. That makes the result smaller, cheaper, and easier to review with another engineer.

```bash
# Search in directory
grep -r "TODO" /path/to/code/

# With file pattern
grep -r --include="*.py" "import" .

# Exclude patterns
grep -r --exclude="*.log" "error" .
grep -r --exclude-dir=".git" "pattern" .
```

The second layer is field extraction. `cut` is excellent when the input has a simple delimiter and you need fixed fields; `awk` is better when the decision depends on values, counts, or calculations; `tr` is useful for character-level cleanup; and `paste` joins files line by line when two streams share position. Choosing the smaller tool is not a badge of purity. It reduces the number of assumptions future readers must hold in their heads.

For Kubernetes examples in this module, set `alias k=kubectl` before using the short `k` form. The long command name still appears in older documentation, vendor examples, and pasted incident notes, so you must recognize both forms. In scripts and lab work, the alias keeps commands readable while still mapping directly to standard Kubernetes 1.35+ `kubectl` behavior.

```bash
alias k=kubectl
k get pods -o json | jq -r '.items[].metadata.name'
k get pods -o json | jq -r '.items[] | "\(.metadata.name): \(.spec.containers[0].image)"'
k get pods -o json | jq '.items[] | select(.status.phase == "Running")'
k get pods -o json | jq -r '.items[].spec.nodeName' | sort | uniq -c
```

Pause and predict: before running any pipeline that ends with `uniq -c`, what must be true about the order of the incoming records? If you skip the `sort` step, repeated values that are separated by other lines remain separate groups. That small ordering rule is responsible for many bad incident summaries because the command still prints plausible-looking counts.

## Editing Streams Safely with `sed`

`sed` exists for stream editing, which means it reads text, applies editing commands, and writes the result. That design is perfect for repeatable transformations such as replacing a hostname, deleting comments, printing a narrow range, or reshaping a delimited line. It is less ideal when the transformation needs deep context from the whole file, schema awareness, or a human review of every edit. The tool is sharp, so the safe workflow matters as much as the syntax.

Substitution is the operation most engineers learn first. The first form changes only the first match on each line, while the `g` flag changes every match on each line. That difference is not cosmetic. Replacing a single endpoint in a config file may be correct, but replacing every matching token in a certificate, generated block, or embedded example can silently alter content you did not intend to touch.

```bash
# Basic substitution
sed 's/old/new/' file.txt      # First occurrence
sed 's/old/new/g' file.txt     # All occurrences

# In-place editing
sed -i 's/old/new/g' file.txt

# Backup before editing
sed -i.bak 's/old/new/g' file.txt

# Case insensitive
sed 's/old/new/gi' file.txt
```

> **Pause and predict**: When using `sed -i` to edit a file in-place, `sed` actually creates a temporary file, writes the modified content to it, and then renames it over the original file. How might this behavior affect file ownership, permissions, or symlinks compared to using a shell redirect (`>`)?

Addressing tells `sed` where a command applies. You can target a single line, a line range, a matching pattern, or a range bounded by two patterns. This is the difference between "replace this token everywhere" and "replace it only inside the block that describes the staging database." In operational files, that scope is your guardrail because many identifiers repeat in comments, examples, defaults, and active settings.

```bash
# Line numbers
sed '5s/old/new/' file.txt     # Only line 5
sed '1,10s/old/new/g' file.txt # Lines 1-10

# Patterns
sed '/error/s/old/new/' file.txt      # Lines matching "error"
sed '/^#/d' file.txt                   # Delete comment lines

# Ranges
sed '/start/,/end/d' file.txt         # Delete from start to end
```

Common operations build from the same idea: match, delete, print, insert, append, or run multiple commands in sequence. Notice that `sed -n` changes the default behavior. Instead of printing every processed line, it prints only when told to print, which is why `sed -n '5p'` is useful for inspecting one line and `sed -n '/pattern/p'` behaves like a simple grep.

```bash
# Delete lines
sed '/pattern/d' file.txt      # Lines matching pattern
sed '1d' file.txt              # First line
sed '$d' file.txt              # Last line
sed '1,5d' file.txt            # Lines 1-5

# Print specific lines
sed -n '5p' file.txt           # Only line 5
sed -n '1,10p' file.txt        # Lines 1-10
sed -n '/pattern/p' file.txt   # Lines matching pattern

# Insert/Append
sed '1i\Header Line' file.txt  # Insert before line 1
sed '1a\After Line 1' file.txt # Append after line 1

# Multiple commands
sed -e 's/a/A/g' -e 's/b/B/g' file.txt
sed 's/a/A/g; s/b/B/g' file.txt
```

Capture groups make `sed` useful for rearranging text rather than merely replacing it. Basic regular expressions use escaped parentheses, while `-E` enables extended regular expressions with cleaner grouping syntax. The important habit is to test the expression without `-i` first, then apply the in-place edit with a backup only after the output looks right. A one-line mistake can produce a very large diff.

```bash
# Capture and reuse
sed 's/\(.*\):\(.*\)/\2:\1/' file.txt  # Swap around colon

# Extended regex (-E)
sed -E 's/([0-9]+)-([0-9]+)/\2-\1/' file.txt  # Swap numbers

# Named groups (GNU sed)
sed -E 's/([a-z]+)@([a-z]+)/User: \1, Domain: \2/' emails.txt
```

A practical example is a database migration where `db-old.local` must become `db-new.local`. The safe version escapes the dots because unescaped dots mean "any character" in regular expressions, and it creates a backup before changing the file. The risky version works only when the input is simple and the operator is lucky. That distinction is why production runbooks should include the exact command, the pre-check, and the rollback command.

When a text edit starts to depend on nested syntax, stop and reconsider. `sed` can remove comments from simple key-value files, but it cannot safely edit YAML or JSON when indentation, quoting, arrays, or multiline values matter. Use a structural tool for structural data. The point is not that `sed` is weak; the point is that a stream editor intentionally does not parse every file format in your environment.

## Processing Records with `awk`

`awk` is the bridge between one-line filtering and small programs. It reads records, splits each record into fields, checks patterns or conditions, and runs actions. For many operations tasks, that model is exactly enough: extract the first field from an access log, print rows where a status code is high, sum a latency column, or count requests by department, user, endpoint, or node.

The default field separator is whitespace, which makes `awk` pleasant for logs and command output that already behave like columns. As soon as a file uses a different delimiter, declare it with `-F`. This keeps the script honest. Future maintainers can see that `/etc/passwd` is colon-separated or that a report is comma-separated, and they do not have to reverse-engineer your assumptions from a clever expression.

```bash
# Print entire line
awk '{print}' file.txt

# Print specific fields
awk '{print $1}' file.txt      # First field
awk '{print $1, $3}' file.txt  # First and third
awk '{print $NF}' file.txt     # Last field

# Field separator
awk -F: '{print $1}' /etc/passwd
awk -F',' '{print $2}' data.csv
```

The built-in variables are what turn `awk` into a useful language. `$0` is the whole record, `$1` through `$n` are fields, `NF` tells you how many fields the current record has, and `NR` tells you which record you are processing. `BEGIN` runs before input is read and `END` runs after input is exhausted, which is why totals and summaries naturally live in `END` blocks.

```bash
# Variables
$0      # Entire line
$1-$n   # Fields
NF      # Number of fields
NR      # Record (line) number
FS      # Field separator
OFS     # Output field separator
RS      # Record separator

# Examples
awk '{print NR, $0}' file.txt          # Line numbers
awk -F: '{print NF, $0}' /etc/passwd   # Field count
awk 'END {print NR}' file.txt          # Total lines
```

Pattern-action pairs make `awk` readable when you treat them as "when this is true, do that." The pattern can be a regular expression, a numeric comparison, a string comparison, or a record-number condition. The action can print, update counters, calculate sums, or format a report. That structure is easier to debug than a pipeline that uses five `cut` commands to simulate logic.

```bash
# Pattern action
awk '/error/ {print}' file.txt
awk '/error/ {print $1}' file.txt

# Conditions
awk '$3 > 100 {print}' file.txt
awk '$1 == "root" {print}' /etc/passwd
awk 'NR > 10 {print}' file.txt        # Skip first 10 lines

# BEGIN and END
awk 'BEGIN {print "Header"} {print} END {print "Footer"}' file.txt
```

Calculations are where `awk` often replaces a quick spreadsheet. Summing a column, computing an average, and tracking a maximum can all happen while the file streams past. That is operationally valuable because a large log file does not need to be loaded into a GUI or copied into a database just to answer an immediate question. The cost is that you must validate field positions carefully.

```bash
# Sum column
awk '{sum += $1} END {print sum}' file.txt

# Average
awk '{sum += $1; count++} END {print sum/count}' file.txt

# Max/Min
awk 'NR==1 || $1>max {max=$1} END {print max}' file.txt

# Formatted output
awk '{printf "%-10s %5d\n", $1, $2}' file.txt
```

Associative arrays let `awk` group data without a separate database. The array key can be an IP address, department, endpoint, pod name, or any other field. This is how one-liners become incident dashboards in miniature: count by source, sum by group, sort the result, and inspect the largest values first. The hidden tradeoff is memory because every unique key must remain available until the `END` block runs.

```bash
# Count by field
awk '{count[$1]++} END {for (k in count) print k, count[k]}' file.txt

# Sum by group
awk '{sum[$1] += $2} END {for (k in sum) print k, sum[k]}' file.txt

# Unique values
awk '!seen[$1]++' file.txt
```

> **Stop and think**: The `awk` command `awk '!seen[$1]++'` elegantly filters out duplicate lines based on the first column. Since it relies on the associative array `seen` to track every unique value encountered, what happens to the system's memory if you run this against a 50GB access log with highly randomized, unique data points in that column?

The answer is that the process can grow until it hits memory pressure, swap, or an out-of-memory kill. For bounded values such as HTTP status codes or a known set of departments, in-memory grouping is excellent. For unbounded values such as request IDs or randomized tokens, prefer sorting to disk with `sort`, streaming approximate summaries, or a purpose-built data system. A command can be syntactically correct and still be operationally dangerous at scale.

Before running an `awk` command against production-sized data, sample the input and confirm the fields. `head`, `sed -n`, and `awk '{print NF, $0}'` are cheap sanity checks. A log format change that inserts a quoted user agent can shift every field after it, causing a command to average the wrong column while still printing a number. The danger is plausible output, not obvious failure.

## Working with JSON Through `jq`

JSON should be processed as JSON. This sounds obvious, but many fragile scripts begin as `grep` commands against JSON because the first few examples are small and pretty-printed. Once values are reordered, strings are escaped, arrays grow, or objects are printed on one line, text search becomes unreliable. `jq` solves that by parsing the document and letting you navigate fields, arrays, filters, and constructed output with a language designed for JSON.

Basic navigation starts with the identity filter `.` and field access. Use `-r` when the downstream consumer expects raw text rather than JSON strings with quotes. That flag is especially important in shell loops because a value printed as `"pod-a"` is valid JSON, but it is usually the wrong literal argument for `xargs`, `read`, or a command substitution.

```bash
# Pretty print
echo '{"name":"John"}' | jq .

# Get field
echo '{"name":"John"}' | jq '.name'
# "John"

# Raw output (no quotes)
echo '{"name":"John"}' | jq -r '.name'
# John

# Nested
echo '{"user":{"name":"John"}}' | jq '.user.name'
```

> **Pause and predict**: While tools like `grep` and `awk` process text sequentially line-by-line using constant memory, `jq` typically parses the entire JSON structure into an internal tree before filtering it. If you pipe a 5GB monolithic JSON file into a standard `jq` filter, what is the likely outcome on a container with a 512MB memory limit?

Arrays are where `jq` starts to feel different from line-oriented tools. `.[0]` selects one element, `.[]` iterates over all elements, and `length` asks about the collection itself. When a Kubernetes API response returns an object with an `items` array, `.items[]` is the step that turns the list into a stream of individual resources. After that, each resource can be inspected, filtered, or reshaped.

```bash
# Array element
echo '[1,2,3]' | jq '.[0]'
# 1

# All elements
echo '[1,2,3]' | jq '.[]'
# 1
# 2
# 3

# Length
echo '[1,2,3]' | jq 'length'
# 3

# Array of objects
echo '[{"name":"a"},{"name":"b"}]' | jq '.[].name'
# "a"
# "b"
```

Filtering and mapping are the JSON equivalents of narrowing and transforming a text stream. `select` keeps values that satisfy a condition, `map` transforms every array element, `sort` orders values, and `unique` removes duplicates after comparison. These operations know about JSON types, so numbers remain numbers and strings remain strings. That is safer than relying on textual coincidences.

```bash
# Select
echo '[{"name":"a","val":1},{"name":"b","val":2}]' | jq '.[] | select(.val > 1)'
# {"name":"b","val":2}

# Map
echo '[1,2,3]' | jq 'map(. * 2)'
# [2,4,6]

# Sort
echo '[3,1,2]' | jq 'sort'
# [1,2,3]

# Unique
echo '[1,1,2,2,3]' | jq 'unique'
# [1,2,3]
```

Construction lets you turn verbose API output into exactly the shape a human or script needs. This matters in operations because raw Kubernetes objects include far more data than most incident questions require. A focused object with the pod name, node, phase, and first container image can be reviewed quickly, stored as evidence, or piped into another command without carrying the entire API response.

```bash
# Create object
echo '{"a":1,"b":2}' | jq '{x: .a, y: .b}'
# {"x":1,"y":2}

# Create array
echo '{"a":1,"b":2}' | jq '[.a, .b]'
# [1,2]

# Keys and values
echo '{"a":1,"b":2}' | jq 'keys'
# ["a","b"]
echo '{"a":1,"b":2}' | jq 'to_entries'
# [{"key":"a","value":1},{"key":"b","value":2}]
```

Kubernetes is a practical place to use `jq` because the API already exposes structured objects. The examples below preserve the long `kubectl` form because you will see it in many vendor documents and old runbooks. In this course, use `k` after defining `alias k=kubectl`; the JSON filters are identical because the output shape comes from the Kubernetes API, not from the shell alias.

```bash
# Get pod names
kubectl get pods -o json | jq -r '.items[].metadata.name'

# Get image for each pod
kubectl get pods -o json | jq -r '.items[] | "\(.metadata.name): \(.spec.containers[0].image)"'

# Filter by status
kubectl get pods -o json | jq '.items[] | select(.status.phase == "Running")'

# Count pods per node
kubectl get pods -o json | jq -r '.items[].spec.nodeName' | sort | uniq -c
```

There are two common `jq` traps. The first is forgetting `-r`, which leaves quotes around values and breaks plain-text consumers. The second is treating huge JSON files like ordinary logs. Standard `jq` filters often need the parsed structure in memory, so a massive single JSON document can fail inside a constrained container. For large event streams, prefer newline-delimited JSON and filters that process one object at a time.

## Building Pipelines for Operational Questions

A useful pipeline begins with a question, not a command. "How many errors happened?" is a different question from "which source generated the most errors?" or "which endpoints are slow among successful requests?" If you start with the question, the pipeline becomes a sequence of transformations that can be checked at each step. If you start by pasting a clever command, you may not notice when the answer does not match the problem.

The simplest pattern is select, project, normalize, aggregate, and rank. Select records with `grep` or `awk`, project the useful field with `awk` or `jq`, normalize values with `tr` or `sed`, aggregate with `sort | uniq -c` or `awk` arrays, and rank with `sort -rn`. That shape appears everywhere: access logs, process tables, package lists, Kubernetes resources, and CI logs.

```bash
# Common patterns
grep "error" file.txt | wc -l                          # Count errors
ps aux | awk '{print $1}' | sort | uniq -c | sort -rn  # Process count by user
kubectl get pods | grep -v Running | awk '{print $1}'  # Non-running pods

# Complex pipeline
grep -E "^[0-9]" access.log | \
  awk '{print $1}' | \
  sort | \
  uniq -c | \
  sort -rn | \
  head -10
```

The non-running pod example is intentionally recognizable, but it also shows why structured output is often safer. Human-readable `kubectl get pods` tables can change columns, wrap values, or include headers that must be filtered away. JSON output with `jq` is more verbose to type, but it depends on API fields rather than display formatting. For one-time triage, the table pipeline may be fine; for automation, prefer structured output.

`xargs` turns lines into command arguments, which makes it useful for cleanup, copying, API checks, and parallel probes. The danger is that filenames, URLs, and resource names are not always as simple as a demo. Whitespace breaks naive `xargs`, empty input can produce surprising commands, and parallel execution can overload a service if you choose an aggressive value. Use null-delimited input from `find -print0` when filenames are involved.

```bash
# Execute command for each line
echo "file1 file2" | xargs rm

# One argument at a time
xargs -I {} cp {} /backup/ < files.txt

# Parallel execution
xargs -P 4 -I {} curl -s {} < urls.txt

# With find
find . -name "*.tmp" | xargs rm
find . -name "*.log" -print0 | xargs -0 rm  # Handle spaces
```

The pipeline debugging habit is to run each stage alone before adding the next stage. First inspect the raw match count, then inspect the projected field, then sort a sample, then count, then rank. This slows you down for a few seconds and saves minutes of false confidence. The more destructive the final command is, the more important it is to print the candidate list before executing anything.

Which approach would you choose here and why: a five-stage one-liner in a runbook, or a checked-in script with named variables and tests? The answer depends on repetition, blast radius, and audience. A one-liner is fine for an interactive investigation, but a command that deletes files, changes configs, restarts pods, or informs an executive incident report deserves version control and review.

Shell tools compose well because they exchange streams, but not every stream is equally safe. Text tables are convenient for humans, delimited data is convenient for field tools, and JSON is convenient for API objects. When a pipeline crosses those shapes, make the boundary explicit. That may mean adding `-o json`, declaring `-F:`, using `sort` before `uniq`, or stripping quotes with `jq -r`.

## Worked Example: From Raw Log to Operational Decision

Imagine an application team reports that "the API is slow" after a routine configuration rollout. That sentence is not yet a technical problem because it does not name an endpoint, status code, client, time window, or resource boundary. A good text-processing workflow turns that vague report into smaller questions. Which endpoints are returning errors? Which clients produce the most requests? Are the slowest requests also failing, or are they successful requests waiting on a backend dependency?

Start by selecting the narrowest records that still preserve the question. If the access log has one request per line, a status-code filter can reduce the investigation from thousands of lines to the subset with `5xx` responses. At this point, do not immediately count everything. Read a few matching lines first, because the sample tells you whether fields are where you expect, whether response times carry units, and whether quoted values contain spaces that can break field assumptions.

Once the sample looks stable, project only the fields you need. For an endpoint investigation, that might be client IP, method, path, status, and duration. Projection is not just a convenience. It removes distracting columns and makes the next command cheaper. It also creates a review point where another engineer can verify that field three really is the path and field five really is the duration before the pipeline becomes a metric.

Normalization comes next because logs often mix human-friendly strings with values you want to compare numerically. A response time such as `150ms` is readable, but `awk` needs the suffix removed before calculating an average or comparing it against a threshold. This is where `gsub(/ms/, "", $5)` is a legitimate transformation rather than cosmetic cleanup. The command changes the representation so the following comparison means what it says.

Aggregation should answer the incident question directly. If the goal is to find noisy clients, group by IP. If the goal is to find broken routes, group by endpoint and status. If the goal is to estimate impact, count affected requests and compare them with the total. Avoid producing a large report merely because the tools can do it. During an incident, a smaller result that supports a decision is more valuable than a broad result that nobody can interpret quickly.

Ranking is the final step for many investigations because humans inspect the top of a list first. `sort -rn | head` is useful only after the count or metric appears in a sortable column, so pay attention to output shape before ranking. A common mistake is sorting paths alphabetically when the intent was to sort counts numerically. When a command prints a neat table, ask whether the most important column is actually the one being ordered.

This same flow works against Kubernetes output when you choose JSON at the boundary. For example, a team might ask whether restarting pods are concentrated on one node. The reliable shape is `k get pods -o json`, the projection is `.items[].spec.nodeName`, the aggregation is `sort | uniq -c`, and the ranking is `sort -rn`. The workflow is identical to log analysis, but the extraction step uses `jq` because the input is structured API data.

The important lesson is that every stage has a contract. Selection decides which records are eligible, projection decides which fields matter, normalization decides how values compare, aggregation decides what gets counted, and ranking decides what a human sees first. If you cannot state the contract of a stage in plain language, the pipeline is probably too clever for a production runbook. Rename it, split it, or turn it into a script with intermediate output.

Before running this against a larger file, what output do you expect after each stage? Write down one expected line after selection, one expected projected row, and one expected aggregate. That small prediction exercise catches field shifts and missing sort steps early. It also gives you a quick way to explain the command during a handoff, which matters when the next operator inherits your terminal history.

There is a natural point where a one-liner should graduate into a script. If the command will be repeated across teams, included in a runbook, used for destructive action, or reported as evidence after an incident, give it names and checks. A script can validate input files, print its assumptions, handle empty results, and fail clearly. The shell tools remain the engine, but the script provides the seatbelts.

The reverse is also true: do not turn every investigation into a framework. The point of learning these commands is to move quickly from raw evidence to a defensible next step. A five-minute interactive pipeline can be exactly right when the blast radius is low and the output is only used to choose the next diagnostic command. Engineering judgment is knowing when speed is harmless and when repeatability is part of correctness.

The strongest operators keep both modes available. They can improvise at the prompt, but they also know how to slow down, preserve evidence, and make a pipeline reviewable. Text processing is not merely about remembering flags. It is about turning messy operational streams into statements that are specific enough to act on and transparent enough for another engineer to trust.

One useful review technique is to read the pipeline from right to left after you have built it. The final command tells you what kind of answer you promised, such as a ranked count, a filtered list, or a transformed file. The command before it tells you whether the final command receives the right shape. This reverse reading often reveals mismatches that forward reading misses, especially when an early stage silently drops a column or changes ordering.

Another technique is to keep the first successful sample beside the final command. Save ten representative input lines and the expected transformed output in an incident note or script comment when the command becomes operationally important. That small artifact makes future changes safer because a teammate can rerun the command against known input and see whether the behavior changed. It also prevents the common problem where a pipeline is copied months later after the log format has drifted.

Finally, separate evidence gathering from remediation. A pipeline that identifies files, pods, users, or requests should usually print its findings before another command acts on them. This creates a human checkpoint and gives you a record of what the automation believed at the time. When the next step is a deletion, restart, config rewrite, or security report, that checkpoint is not bureaucracy; it is the difference between a useful tool and an unexplained side effect.

## Patterns & Anti-Patterns

### Patterns

The first reliable pattern is "shape first, command second." Before you write the command, name the data shape and the invariant you depend on. If the input is line-oriented, `grep`, `sed`, and `awk` are natural. If the input is colon-delimited, `cut -d:` or `awk -F:` is honest. If the input is JSON, use `jq` and let the parser understand arrays, strings, and objects.

The second pattern is "inspect before mutate." Run `sed` without `-i`, print candidate files before passing them to `xargs rm`, and show the first few transformed rows before aggregating. This is the text-processing equivalent of a dry run. It reduces risk because you see whether your assumptions match the input before the command writes, deletes, restarts, or reports.

The third pattern is "stream when possible, store only when necessary." `grep`, `sed`, and many `awk` commands can process data as it arrives, which is excellent for large logs. Grouping by unbounded keys, sorting huge files, and parsing monolithic JSON can require significant memory or disk. A mature operator knows when a command is cheap because it streams and when it is expensive because it must remember.

### Anti-Patterns

The most common anti-pattern is "regex as a universal parser." Teams fall into it because the first example works, and the command is short enough to paste into chat. It fails when structure matters, especially with JSON, YAML, CSV quoting, or nested data. The better alternative is to use a parser for structured formats and reserve regex for textual selection or simple normalization.

Another anti-pattern is "plausible output means correct output." A pipeline can average the wrong column, count unsorted duplicates incorrectly, or include a header row while still printing a neat result. This is why operational pipelines should be built incrementally. Check representative input, verify field positions, and compare a small manual sample against the command before trusting the large result.

A third anti-pattern is "destructive text processing without rollback." In-place substitutions, mass deletes, and scripted restarts can be appropriate, but only after the target set is visible and recoverable. Use backups, version control, dry-run output, and narrow addressing. The goal is not to avoid automation; the goal is to make automation reversible enough that a typo does not become the incident.

## Decision Framework

Use this framework when you are deciding which tool should own a text-processing task. The right answer is usually the smallest tool that understands the shape of the data and the risk of the operation. If the result will feed a production change, choose the safer and more explicit path even when it takes a few more characters to type.

| Data shape or task | Prefer | Why it fits | Watch for |
|---|---|---|---|
| Find lines containing a pattern | `grep` | Fast line selection with clear include, exclude, and context flags | Context lines can mislead when logs interleave |
| Replace text in a stream | `sed` | Repeatable substitutions, deletions, and scoped edits | Test before `-i`; escape regex metacharacters |
| Extract fields or compute totals | `awk` | Records, fields, conditions, arrays, and calculations | Field shifts and unbounded grouping memory |
| Parse JSON API output | `jq` | Understands arrays, objects, types, and construction | Use `-r` for shell text; avoid huge monolithic JSON |
| Count repeated values | `sort | uniq -c` | Simple, transparent aggregation after ordering | `uniq` only counts adjacent duplicates |
| Execute one command per item | `xargs` | Converts streams into arguments and supports parallelism | Whitespace, empty input, and overload risk |

When speed matters, begin with the command that discards the most irrelevant data safely. That might be `grep` before `awk`, or a narrow `jq` filter before sorting pod names. When correctness matters more than typing speed, choose structured output and explicit delimiters. The fastest wrong answer is worse than a slower command that can be explained in a review.

For destructive changes, add a gate between selection and action. Print the list, count it, save it to a temporary file, and then run the action against that reviewed file. This pattern is especially valuable with `xargs` because the final command may be far removed from the selection logic. The reviewable boundary turns a fragile stream into an auditable artifact.

If the same decision comes up repeatedly, encode the framework in the command name or script interface. A script called `top-error-sources` is easier to review than a generic `analyze.sh` because the name states the operational question. Good names also discourage scope creep. When a text-processing helper starts answering unrelated questions, split it into smaller tools that match the pipeline philosophy you are practicing here.

The framework also helps during handoffs. Instead of saying "I ran some awk," describe the shape and decision: "I selected five-minute access-log records, projected endpoint and status, counted by endpoint, and ranked the largest error groups." That sentence is testable. Another engineer can inspect the exact stage where they disagree, replace one tool with a better one, or rerun the command against a different time window without debating the entire workflow.

## Did You Know?

- **`grep` was created in 1973** by Ken Thompson at Bell Labs, and its name comes from the `ed` command `g/re/p`, meaning global regular expression print.
- **`awk` is a programming language**, named after Alfred Aho, Peter Weinberger, and Brian Kernighan, with variables, associative arrays, functions, and control flow beyond simple one-liners.
- **`sed` is non-interactive `ed`**, built for batch editing streams line by line, which is why substitution syntax such as `s/old/new/g` still feels compact and old-school.
- **`jq` arrived in 2012** to fill the gap that classic text tools left for JSON, giving shell users a structural filter for data that does not behave safely as plain lines.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| `cat file | grep` | It feels natural to "send" a file into the next command, but `grep` already knows how to read files directly. | Use `grep pattern file` unless `cat` is genuinely combining multiple inputs or preserving a teaching example. |
| Unquoted variables in `awk` or shell wrappers | Shell word splitting and glob expansion can change the value before `awk` ever sees it. | Pass values with `awk -v name="$var" '...'` and quote shell variables at command boundaries. |
| Running `sed -i` without a backup or review | In-place edits are quick, and the terminal gives little friction before overwriting content. | Preview the command without `-i`, then use `sed -i.bak` or version control for rollback. |
| Not escaping regex metacharacters | Dots, brackets, and parentheses are easy to read as literal text even when the regex engine treats them specially. | Escape literal metacharacters or use a fixed-string tool when the pattern is not meant to be a regex. |
| Forgetting `jq -r` before shell loops | JSON strings with quotes look fine on screen but become awkward command arguments. | Use `jq -r` when the next command expects plain text rather than JSON. |
| Searching binary files with `grep` during recursive scans | Recursive searches walk into generated assets, database files, or compiled artifacts. | Constrain the search with `--include`, `--exclude`, and `--exclude-dir`, or skip binary-heavy paths. |
| Counting with `uniq -c` before sorting | The command still prints counts, so the mistake can look correct during a rushed investigation. | Sort on the grouping key first, then run `uniq -c`, then rank with `sort -rn`. |
| Parsing Kubernetes table output in automation | Human-readable tables are convenient, but columns and headers are display contracts, not API contracts. | Use `k get ... -o json | jq ...` for scripts that must survive formatting changes. |

## Quiz

<details>
<summary>Scenario: You are auditing system accounts on a legacy Linux server. The security team needs a plain list of usernames from `/etc/passwd`, whose first field is separated by colons. Which command do you choose, and why?</summary>

Use either `awk -F: '{print $1}' /etc/passwd` or `cut -d: -f1 /etc/passwd`. Both commands match the data shape because `/etc/passwd` is a simple delimiter-based file, not nested structure. `awk` is useful if you plan to add conditions later, while `cut` is smaller when extraction is the whole job. The important decision is declaring the colon delimiter instead of relying on whitespace splitting.

```bash
awk -F: '{print $1}' /etc/passwd
# Or
cut -d: -f1 /etc/passwd
```
</details>

<details>
<summary>Scenario: Your team is migrating an application to a new database cluster. You need to replace every `db-old.local` value with `db-new.local` in `db.conf`, but you need a fallback. What command and safety habit fit?</summary>

Run `sed -i.bak 's/db-old\.local/db-new.local/g' db.conf` after first previewing the same substitution without `-i`. The escaped dot prevents the pattern from matching any character between words, which keeps the replacement narrow. The `.bak` backup gives you a direct rollback if the command touched a line you did not intend. This is safer than redirecting output over the original file because the review and rollback steps are explicit.

```bash
sed -i.bak 's/db-old\.local/db-new\.local/g' db.conf
```
</details>

<details>
<summary>Scenario: A web server is receiving a traffic spike, and the first field in `access.log` is the client IP. You need the busiest IPs at the top. How do you build the pipeline?</summary>

Use `awk '{print $1}' access.log | sort | uniq -c | sort -rn`. `awk` projects the IP field so later commands process only the grouping key. The first `sort` is required because `uniq` only collapses adjacent matching lines. `uniq -c` adds counts, and `sort -rn` ranks those counts numerically from largest to smallest so the likely sources are visible first.

```bash
awk '{print $1}' access.log | sort | uniq -c | sort -rn
```
</details>

<details>
<summary>Scenario: Your Kubernetes 1.35+ script needs pod names from the API as raw text so it can iterate over them. You have defined `alias k=kubectl`. Which command is reliable?</summary>

Use `k get pods -o json | jq -r '.items[].metadata.name'`. The `-o json` flag asks Kubernetes for structured API output rather than a display table, and `.items[]` iterates through the returned list. The `.metadata.name` filter selects the field the script actually needs. The `-r` flag removes JSON string quotes, which makes the output safe for normal shell iteration.

```bash
k get pods -o json | jq -r '.items[].metadata.name'
```
</details>

<details>
<summary>Scenario: A log search for `Exception` is flooded with known `TimeoutException` messages. How do you keep the useful failures without writing an unreadable regex?</summary>

Use `grep "Exception" app.log | grep -v "TimeoutException"`. The first command is an inclusive filter that narrows the log to exception-related lines. The second command is an exclusive filter because `-v` drops the known noisy class. This two-stage approach is often easier to review than a single complex negative-lookaround expression, especially on systems where `grep -P` support varies.

```bash
grep "Exception" app.log | grep -v "TimeoutException"
```
</details>

<details>
<summary>Scenario: An `awk '!seen[$1]++'` command works on a sample log, but production has highly randomized request IDs in the first field. What failure mode should you expect?</summary>

Expect memory growth because the associative array must keep one key for every unique first-field value it has seen. With bounded keys, such as HTTP status codes, that pattern is efficient. With unbounded or randomized keys, it can consume memory until the process slows down or fails. A disk-backed `sort | uniq` approach or a purpose-built analytics system is safer for very large unique-key workloads.
</details>

<details>
<summary>Scenario: A teammate proposes parsing `k get pods` table output with `awk` in a nightly automation job. What do you recommend instead?</summary>

Recommend `k get pods -o json | jq ...` because automation should depend on API fields rather than human display columns. Table output is useful during interactive triage, but headers, spacing, and columns are presentation details. JSON gives you stable paths such as `.items[].status.phase` and `.items[].metadata.name`. The resulting command may be longer, but it is easier to maintain when Kubernetes output formatting changes.
</details>

## Hands-On Exercise

### Text Processing Practice

**Objective**: Use `grep`, `sed`, `awk`, and `jq` to process text and JSON data.

**Environment**: Any Linux system with the standard GNU text tools and `jq` installed. If you test the Kubernetes examples against a Kubernetes 1.35+ cluster, define `alias k=kubectl` first and use the `k` command form in your own notes.

The exercise uses small files under `/tmp` so you can run commands without risking important data. Treat each part as a miniature version of a real investigation: create the data, ask a precise question, run the command, and compare the output with what you expected. If your output differs, inspect the previous pipeline stage rather than editing the final command blindly.

#### Part 1: grep Practice

```bash
# Create sample data
cat > /tmp/logs.txt << 'EOF'
2024-01-15 10:00:00 INFO Starting application
2024-01-15 10:00:01 DEBUG Loading config
2024-01-15 10:00:02 INFO Connected to database
2024-01-15 10:00:03 WARNING Slow query detected
2024-01-15 10:00:04 ERROR Connection timeout
2024-01-15 10:00:05 INFO Retry successful
2024-01-15 10:00:06 DEBUG Cache hit
2024-01-15 10:00:07 ERROR Failed to authenticate
2024-01-15 10:00:08 INFO Shutdown complete
EOF

# 1. Find all errors
grep "ERROR" /tmp/logs.txt

# 2. Find errors and warnings
grep -E "ERROR|WARNING" /tmp/logs.txt

# 3. Count each log level
grep -oE "(INFO|DEBUG|WARNING|ERROR)" /tmp/logs.txt | sort | uniq -c

# 4. Show context around errors
grep -C 1 "ERROR" /tmp/logs.txt

# 5. Extract just the message
grep "ERROR" /tmp/logs.txt | grep -oE "[A-Z]+ .*$"
```

<details>
<summary>Solution notes for Part 1</summary>

The first two commands practice inclusive filtering, while the third command extracts only the level token before counting. The `sort` step before `uniq -c` is essential because repeated levels must be adjacent before `uniq` can collapse them. The context command should show one neighboring line before and after each error, and the final extraction should leave only the severity plus message text.
</details>

#### Part 2: sed Practice

```bash
# Create config file
cat > /tmp/config.txt << 'EOF'
# Database config
host=localhost
port=5432
database=myapp
user=admin
password=secret123
EOF

# 1. Remove comments
sed '/^#/d' /tmp/config.txt

# 2. Change port
sed 's/port=5432/port=5433/' /tmp/config.txt

# 3. Extract just values
sed -n 's/.*=//p' /tmp/config.txt

# 4. Convert to export statements
sed 's/^/export /' /tmp/config.txt | sed '/^export #/d'

# 5. Multiple substitutions
sed -e 's/localhost/db.example.com/' -e 's/5432/5433/' /tmp/config.txt
```

<details>
<summary>Solution notes for Part 2</summary>

These commands are intentionally non-destructive because they print transformed output without changing `/tmp/config.txt`. The comment deletion uses an anchored pattern, the port change targets one literal assignment, and the value extraction uses `-n` so only substitution matches are printed. In a real config migration, preview this way first, then rerun with a backup if an in-place edit is required.
</details>

#### Part 3: awk Practice

```bash
# Create data file
cat > /tmp/data.txt << 'EOF'
Alice 100 Engineering
Bob 150 Sales
Carol 120 Engineering
David 90 Marketing
Eve 200 Sales
Frank 110 Engineering
EOF

# 1. Print names and salaries
awk '{print $1, $2}' /tmp/data.txt

# 2. Total salary
awk '{sum += $2} END {print "Total:", sum}' /tmp/data.txt

# 3. Average salary
awk '{sum += $2; n++} END {print "Average:", sum/n}' /tmp/data.txt

# 4. Salary by department
awk '{dept[$3] += $2; count[$3]++} END {for (d in dept) print d, dept[d], count[d]}' /tmp/data.txt

# 5. Filter high earners
awk '$2 > 100 {print $1, $2}' /tmp/data.txt
```

<details>
<summary>Solution notes for Part 3</summary>

The file is whitespace-delimited, so default `awk` field splitting is enough. The total and average examples demonstrate state that accumulates while records stream past, and the department example uses associative arrays keyed by the third field. If the output order of departments differs on your machine, that is acceptable because basic `awk` array iteration does not guarantee sorted keys.
</details>

#### Part 4: jq Practice

```bash
# Create JSON file
cat > /tmp/data.json << 'EOF'
{
  "users": [
    {"name": "Alice", "age": 30, "role": "admin"},
    {"name": "Bob", "age": 25, "role": "user"},
    {"name": "Carol", "age": 35, "role": "admin"}
  ],
  "version": "1.0"
}
EOF

# 1. Pretty print
jq '.' /tmp/data.json

# 2. Get version
jq -r '.version' /tmp/data.json

# 3. List all names
jq -r '.users[].name' /tmp/data.json

# 4. Filter admins
jq '.users[] | select(.role == "admin")' /tmp/data.json

# 5. Create new structure
jq '.users | map({username: .name, isAdmin: (.role == "admin")})' /tmp/data.json
```

<details>
<summary>Solution notes for Part 4</summary>

The version and name commands use `-r` because those values are intended as plain text. The admin filter emits full JSON objects because preserving structure is useful when you want to inspect more than one field. The final command demonstrates construction by returning a new array of simpler objects, which is a common pattern when trimming verbose API responses.
</details>

#### Part 5: Combining Tools

```bash
# Create access log
cat > /tmp/access.log << 'EOF'
192.168.1.1 GET /api/users 200 150ms
192.168.1.2 POST /api/login 200 50ms
192.168.1.1 GET /api/data 500 300ms
192.168.1.3 GET /api/users 200 100ms
192.168.1.2 GET /api/data 200 80ms
192.168.1.1 GET /api/health 200 10ms
192.168.1.4 POST /api/login 401 20ms
192.168.1.1 GET /api/data 500 250ms
EOF

# 1. Count requests per IP
awk '{print $1}' /tmp/access.log | sort | uniq -c | sort -rn

# 2. Find all errors (5xx)
awk '$4 ~ /^5/ {print}' /tmp/access.log

# 3. Average response time
awk '{gsub(/ms/, "", $5); sum += $5; n++} END {print sum/n, "ms"}' /tmp/access.log

# 4. Requests per endpoint
awk '{count[$3]++} END {for (e in count) print e, count[e]}' /tmp/access.log | sort -k2 -rn

# 5. Slow requests (>100ms)
awk '{gsub(/ms/, "", $5); if ($5 > 100) print}' /tmp/access.log
```

<details>
<summary>Solution notes for Part 5</summary>

This part combines projection, filtering, aggregation, and ranking. The first command depends on `sort` before `uniq -c`, while the status-code filter uses a regular expression against the fourth field. The response-time commands strip the `ms` suffix before numeric comparison or averaging. That normalization step is small, but it is what turns text into a value that `awk` can calculate with.
</details>

### Success Criteria

- [ ] Transform logs and command output with `grep`, `sed`, `awk`, `jq`, `sort`, and `uniq` without losing the original question.
- [ ] Design parsing pipelines by identifying whether the input is plain text, delimited fields, or JSON before choosing tools.
- [ ] Diagnose unsafe text-processing commands by checking sort order, field positions, memory behavior, and destructive edits.
- [ ] Implement a repeatable Linux and Kubernetes 1.35+ workflow using `alias k=kubectl` and `k get ... -o json | jq ...` for API data.
- [ ] Explain why each stage in a multi-command pipeline is present and what would break if that stage were removed.

## Next Module

[Module 7.3: Practical Scripts](../module-7.3-practical-scripts/) shows how to turn these one-liners into production-quality scripts with error handling, logging, input validation, and safer operational patterns.

## Further Reading

- [GNU Grep Manual](https://www.gnu.org/software/grep/manual/)
- [GNU sed Manual](https://www.gnu.org/software/sed/manual/sed.html)
- [GNU awk User's Guide](https://www.gnu.org/software/gawk/manual/gawk.html)
- [jq Manual](https://jqlang.github.io/jq/manual/)
- [jq Manual legacy URL](https://stedolan.github.io/jq/manual/)
- [GNU Coreutils `sort` invocation](https://www.gnu.org/software/coreutils/manual/html_node/sort-invocation.html)
- [GNU Coreutils `uniq` invocation](https://www.gnu.org/software/coreutils/manual/html_node/uniq-invocation.html)
- [GNU Findutils `xargs` manual](https://www.gnu.org/software/findutils/manual/html_node/find_html/xargs-options.html)
- [Kubernetes: `kubectl` Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Kubernetes API Concepts](https://kubernetes.io/docs/reference/using-api/api-concepts/)
- [sed One-Liners](https://catonmat.net/sed-one-liners-explained-part-one)
- [AWK One-Liners](https://catonmat.net/awk-one-liners-explained-part-one)
