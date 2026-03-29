---
title: "Module 7.2: Text Processing"
slug: linux/operations/shell-scripting/module-7.2-text-processing
sidebar:
  order: 3
---
> **Shell Scripting** | Complexity: `[MEDIUM]` | Time: 30-35 min

## Prerequisites

Before starting this module:
- **Required**: [Module 7.1: Bash Fundamentals](../module-7.1-bash-fundamentals/)
- **Required**: Basic regex understanding
- **Helpful**: [Module 6.2: Log Analysis](../troubleshooting/module-6.2-log-analysis/)

---

## Why This Module Matters

Linux is a text-based operating system. Configurations, logs, and data are mostly text. Mastering text processing tools lets you extract, transform, and analyze data without writing programs.

Understanding text processing helps you:

- **Parse logs** — Extract errors, patterns, metrics
- **Transform data** — Convert between formats
- **Process command output** — Parse kubectl, docker, git
- **Automate analysis** — Build reporting scripts

grep, sed, awk, and jq are the Swiss Army knives of DevOps.

---

## Did You Know?

- **grep was created in 1973** — Ken Thompson wrote it at Bell Labs. The name comes from the ed command `g/re/p` (global regex print).

- **awk is a programming language** — Named after its creators (Aho, Weinberger, Kernighan), awk has variables, functions, and control flow. Most people only use 1% of its features.

- **sed is non-interactive ed** — Created for batch editing, sed processes text line by line. The cryptic syntax (`s/old/new/g`) comes directly from ed.

- **jq is "like sed for JSON"** — Created in 2012, jq fills the gap for structured data that grep/sed/awk can't handle elegantly.

---

## grep: Pattern Matching

### Basic Usage

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

### Regex Patterns

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

### Context and Inversion

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

### Recursive Search

```bash
# Search in directory
grep -r "TODO" /path/to/code/

# With file pattern
grep -r --include="*.py" "import" .

# Exclude patterns
grep -r --exclude="*.log" "error" .
grep -r --exclude-dir=".git" "pattern" .
```

---

## sed: Stream Editor

### Substitution

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

### Addressing

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

### Common Operations

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

### Capture Groups

```bash
# Capture and reuse
sed 's/\(.*\):\(.*\)/\2:\1/' file.txt  # Swap around colon

# Extended regex (-E)
sed -E 's/([0-9]+)-([0-9]+)/\2-\1/' file.txt  # Swap numbers

# Named groups (GNU sed)
sed -E 's/([a-z]+)@([a-z]+)/User: \1, Domain: \2/' emails.txt
```

---

## awk: Pattern Processing

### Basic Syntax

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

### Built-in Variables

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

### Pattern Matching

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

### Calculations

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

### Grouping and Counting

```bash
# Count by field
awk '{count[$1]++} END {for (k in count) print k, count[k]}' file.txt

# Sum by group
awk '{sum[$1] += $2} END {for (k in sum) print k, sum[k]}' file.txt

# Unique values
awk '!seen[$1]++' file.txt
```

---

## jq: JSON Processing

### Basic Navigation

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

### Arrays

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

### Filtering

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

### Construction

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

### kubectl with jq

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

---

## Combining Tools

### Pipelines

```bash
# Common patterns
cat file.txt | grep "error" | wc -l                    # Count errors
ps aux | awk '{print $1}' | sort | uniq -c | sort -rn  # Process count by user
kubectl get pods | grep -v Running | awk '{print $1}'  # Non-running pods

# Complex pipeline
cat access.log | \
  grep -E "^[0-9]" | \
  awk '{print $1}' | \
  sort | \
  uniq -c | \
  sort -rn | \
  head -10
```

### xargs

```bash
# Execute command for each line
echo "file1 file2" | xargs rm

# One argument at a time
cat files.txt | xargs -I {} cp {} /backup/

# Parallel execution
cat urls.txt | xargs -P 4 -I {} curl -s {}

# With find
find . -name "*.tmp" | xargs rm
find . -name "*.log" -print0 | xargs -0 rm  # Handle spaces
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| `cat file | grep` | Useless use of cat | `grep pattern file` |
| Unquoted variables in awk | Word splitting | Use `"$var"` |
| sed without -i backup | Data loss | Use `-i.bak` |
| Not escaping in regex | Pattern doesn't match | Escape special chars |
| jq without -r | Extra quotes in output | Use `-r` for raw |
| grep binary files | Garbled output | Use `--text` or skip |

---

## Quiz

### Question 1
How do you extract the first column from a colon-separated file?

<details>
<summary>Show Answer</summary>

```bash
awk -F: '{print $1}' file.txt
# Or
cut -d: -f1 file.txt
```

`-F:` sets the field separator to colon.
`$1` is the first field.

For `/etc/passwd`:
```bash
awk -F: '{print $1}' /etc/passwd
# root
# daemon
# ...
```

</details>

### Question 2
How do you replace all occurrences of "foo" with "bar" in a file?

<details>
<summary>Show Answer</summary>

```bash
# Preview change
sed 's/foo/bar/g' file.txt

# In-place edit
sed -i 's/foo/bar/g' file.txt

# With backup
sed -i.bak 's/foo/bar/g' file.txt
```

The `g` flag means "global" — all occurrences on each line. Without it, only the first occurrence per line is replaced.

</details>

### Question 3
How do you count unique values in the first column?

<details>
<summary>Show Answer</summary>

```bash
awk '{print $1}' file.txt | sort | uniq -c | sort -rn
```

Or with awk only:
```bash
awk '{count[$1]++} END {for (k in count) print count[k], k}' file.txt | sort -rn
```

The pipeline version:
1. Extract first column
2. Sort (required for uniq)
3. Count unique values
4. Sort by count descending

</details>

### Question 4
How do you extract all pod names from `kubectl get pods -o json`?

<details>
<summary>Show Answer</summary>

```bash
kubectl get pods -o json | jq -r '.items[].metadata.name'
```

Breakdown:
- `.items[]` - iterate over all items
- `.metadata.name` - get the name field
- `-r` - raw output (no quotes)

Alternative using kubectl's jsonpath:
```bash
kubectl get pods -o jsonpath='{.items[*].metadata.name}'
```

</details>

### Question 5
How do you get lines containing "error" but not "debug"?

<details>
<summary>Show Answer</summary>

```bash
grep "error" file.txt | grep -v "debug"
```

Or in one grep with regex:
```bash
grep -E "error" file.txt | grep -v "debug"
```

Or with awk:
```bash
awk '/error/ && !/debug/' file.txt
```

The `grep -v` inverts the match, excluding lines containing "debug".

</details>

---

## Hands-On Exercise

### Text Processing Practice

**Objective**: Use grep, sed, awk, and jq to process text and JSON data.

**Environment**: Any Linux system

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
cat /tmp/data.json | jq .

# 2. Get version
cat /tmp/data.json | jq -r '.version'

# 3. List all names
cat /tmp/data.json | jq -r '.users[].name'

# 4. Filter admins
cat /tmp/data.json | jq '.users[] | select(.role == "admin")'

# 5. Create new structure
cat /tmp/data.json | jq '.users | map({username: .name, isAdmin: (.role == "admin")})'
```

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

### Success Criteria

- [ ] Used grep with patterns and context
- [ ] Used sed for substitution and deletion
- [ ] Used awk for field extraction and aggregation
- [ ] Used jq for JSON parsing and filtering
- [ ] Combined tools in pipelines

---

## Key Takeaways

1. **grep for finding** — Pattern matching in text

2. **sed for transforming** — Search and replace, line operations

3. **awk for processing** — Column extraction, calculations, grouping

4. **jq for JSON** — Like sed/awk but for structured data

5. **Pipelines combine power** — Chain tools for complex processing

---

## What's Next?

In **Module 7.3: Practical Scripts**, you'll learn how to write production-quality scripts with proper error handling, logging, and common patterns.

---

## Further Reading

- [GNU Grep Manual](https://www.gnu.org/software/grep/manual/)
- [sed One-Liners](https://catonmat.net/sed-one-liners-explained-part-one)
- [AWK One-Liners](https://catonmat.net/awk-one-liners-explained-part-one)
- [jq Manual](https://stedolan.github.io/jq/manual/)
