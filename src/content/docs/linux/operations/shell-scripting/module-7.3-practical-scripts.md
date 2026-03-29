---
title: "Module 7.3: Practical Scripts"
slug: linux/operations/shell-scripting/module-7.3-practical-scripts
sidebar:
  order: 4
---
> **Shell Scripting** | Complexity: `[MEDIUM]` | Time: 25-30 min

## Prerequisites

Before starting this module:
- **Required**: [Module 7.1: Bash Fundamentals](../module-7.1-bash-fundamentals/)
- **Required**: [Module 7.2: Text Processing](../module-7.2-text-processing/)
- **Helpful**: Experience with operational tasks

---

## Why This Module Matters

Writing a script that works once is easy. Writing a script that works reliably in production is harder. This module covers patterns that make scripts maintainable, debuggable, and safe.

Understanding practical scripting helps you:

- **Write reliable automation** — Scripts that don't break at 3 AM
- **Debug issues faster** — Proper logging and error messages
- **Maintain scripts** — Code others (and future you) can understand
- **Handle edge cases** — Empty inputs, missing files, network failures

The difference between a hack and automation is error handling.

---

## Did You Know?

- **Most production scripts are under 100 lines** — Long scripts should be refactored into multiple scripts or a proper programming language.

- **ShellCheck finds 90% of bugs** — A static analysis tool that catches common Bash mistakes before you run the script.

- **Exit codes are contracts** — Returning the right exit code lets other scripts and tools (like systemd) know what happened.

- **Temporary files are dangerous** — Race conditions, leftover files, and security issues. Use `mktemp` and cleanup traps.

---

## Script Template

### Production-Ready Starter

```bash
#!/bin/bash
#
# Script: script-name.sh
# Description: Brief description of what this script does
# Usage: ./script-name.sh [options] <arguments>
#

set -euo pipefail

# === Configuration ===
readonly SCRIPT_NAME=$(basename "$0")
readonly SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
readonly LOG_FILE="/var/log/${SCRIPT_NAME%.sh}.log"

# === Logging ===
log() {
    local level=$1
    shift
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $*" | tee -a "$LOG_FILE"
}

log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "$@"; }
log_error() { log "ERROR" "$@" >&2; }

# === Error Handling ===
die() {
    log_error "$@"
    exit 1
}

# === Cleanup ===
cleanup() {
    local exit_code=$?
    # Add cleanup tasks here
    rm -f "${TEMP_FILE:-}"
    exit $exit_code
}
trap cleanup EXIT

# === Argument Parsing ===
usage() {
    cat << EOF
Usage: $SCRIPT_NAME [options] <argument>

Description:
    Brief description of what this script does.

Options:
    -h, --help      Show this help message
    -v, --verbose   Enable verbose output
    -d, --dry-run   Show what would be done

Arguments:
    argument        Description of required argument

Examples:
    $SCRIPT_NAME -v input.txt
    $SCRIPT_NAME --dry-run /path/to/file
EOF
    exit 0
}

# === Main Logic ===
main() {
    local verbose=false
    local dry_run=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help) usage ;;
            -v|--verbose) verbose=true; shift ;;
            -d|--dry-run) dry_run=true; shift ;;
            -*) die "Unknown option: $1" ;;
            *) break ;;
        esac
    done

    # Validate arguments
    [[ $# -lt 1 ]] && die "Missing required argument. Use -h for help."

    local input=$1

    # Validate input
    [[ -f "$input" ]] || die "File not found: $input"

    # Do the work
    log_info "Processing: $input"
    if [[ "$dry_run" == true ]]; then
        log_info "Dry run - would process $input"
    else
        # Actual processing here
        log_info "Done"
    fi
}

main "$@"
```

---

## Error Handling Patterns

### Safe Mode

```bash
#!/bin/bash
set -euo pipefail

# -e: Exit on any error
# -u: Exit on undefined variable
# -o pipefail: Exit on pipe failure

# Sometimes you want to handle errors yourself
set +e  # Temporarily disable
command_that_might_fail
exit_code=$?
set -e  # Re-enable

if [[ $exit_code -ne 0 ]]; then
    echo "Command failed with $exit_code"
fi
```

### Trap for Cleanup

```bash
# Cleanup on exit, error, or interrupt
cleanup() {
    local exit_code=$?
    log "Cleaning up..."
    rm -f "$TEMP_FILE"
    [[ -d "$TEMP_DIR" ]] && rm -rf "$TEMP_DIR"
    exit $exit_code
}

trap cleanup EXIT       # Normal exit
trap cleanup ERR        # On error
trap cleanup INT TERM   # Ctrl+C, kill
```

### Retry Logic

```bash
retry() {
    local max_attempts=$1
    local delay=$2
    shift 2
    local cmd="$@"

    local attempt=1
    while [[ $attempt -le $max_attempts ]]; do
        log_info "Attempt $attempt/$max_attempts: $cmd"
        if eval "$cmd"; then
            return 0
        fi
        log_warn "Failed, waiting ${delay}s..."
        sleep "$delay"
        ((attempt++))
    done

    log_error "All $max_attempts attempts failed"
    return 1
}

# Usage
retry 3 5 curl -s http://example.com/api
```

### Timeout

```bash
# Using timeout command
timeout 30 long_running_command

# Check result
if timeout 10 curl -s http://example.com > /dev/null; then
    echo "Success"
else
    echo "Timeout or failure"
fi

# Custom timeout with background process
run_with_timeout() {
    local timeout=$1
    shift
    "$@" &
    local pid=$!

    ( sleep "$timeout"; kill -9 $pid 2>/dev/null ) &
    local killer=$!

    wait $pid 2>/dev/null
    local result=$?

    kill $killer 2>/dev/null
    return $result
}
```

---

## Logging Patterns

### Structured Logging

```bash
# Log levels
LOG_LEVEL=${LOG_LEVEL:-INFO}

declare -A LOG_LEVELS=([DEBUG]=0 [INFO]=1 [WARN]=2 [ERROR]=3)

log() {
    local level=$1
    shift
    local level_num=${LOG_LEVELS[$level]:-1}
    local threshold=${LOG_LEVELS[$LOG_LEVEL]:-1}

    if [[ $level_num -ge $threshold ]]; then
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        printf '[%s] [%s] %s\n' "$timestamp" "$level" "$*"
    fi
}

# Usage
LOG_LEVEL=DEBUG
log DEBUG "Detailed info"
log INFO "Normal message"
log WARN "Warning!"
log ERROR "Error!"
```

### Log to File and Console

```bash
# Redirect all output to log file while keeping console
exec > >(tee -a "$LOG_FILE") 2>&1

# Or for specific commands
echo "This goes to console and log" | tee -a "$LOG_FILE"

# Errors to stderr and log
log_error() {
    echo "[ERROR] $*" | tee -a "$LOG_FILE" >&2
}
```

### Progress Indication

```bash
# Simple progress
for i in {1..100}; do
    printf "\rProgress: %d%%" "$i"
    sleep 0.1
done
echo

# Spinner
spin() {
    local pid=$1
    local chars="⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    local i=0
    while kill -0 "$pid" 2>/dev/null; do
        printf "\r${chars:i++%${#chars}:1} Working..."
        sleep 0.1
    done
    printf "\r"
}

long_command &
spin $!
wait
echo "Done!"
```

---

## Input Validation

### Argument Checking

```bash
# Required arguments
[[ $# -lt 2 ]] && die "Usage: $0 <source> <dest>"

# Validate file exists
validate_file() {
    local file=$1
    [[ -f "$file" ]] || die "Not a file: $file"
    [[ -r "$file" ]] || die "Cannot read: $file"
}

# Validate directory
validate_dir() {
    local dir=$1
    [[ -d "$dir" ]] || die "Not a directory: $dir"
    [[ -w "$dir" ]] || die "Cannot write to: $dir"
}

# Validate command exists
require_command() {
    local cmd=$1
    command -v "$cmd" &>/dev/null || die "Required command not found: $cmd"
}

require_command kubectl
require_command jq
```

### Input Sanitization

```bash
# Remove dangerous characters
sanitize() {
    local input=$1
    # Remove everything except alphanumeric, dash, underscore, dot
    echo "${input//[^a-zA-Z0-9._-]/}"
}

# Validate is number
is_number() {
    [[ $1 =~ ^[0-9]+$ ]]
}

# Validate IP address
is_ip() {
    [[ $1 =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]
}

# Safe default
port=${1:-8080}
is_number "$port" || die "Invalid port: $port"
```

---

## File Handling

### Safe Temporary Files

```bash
# Create temp file
TEMP_FILE=$(mktemp)
trap 'rm -f "$TEMP_FILE"' EXIT

# Create temp directory
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

# With prefix
TEMP_FILE=$(mktemp /tmp/myscript.XXXXXX)

# Never do this (race condition, predictable)
# TEMP_FILE=/tmp/myscript.tmp  # BAD!
```

### Atomic File Operations

```bash
# Atomic write (write to temp, then move)
atomic_write() {
    local dest=$1
    local temp=$(mktemp "${dest}.XXXXXX")

    cat > "$temp"  # Write stdin to temp

    chmod --reference="$dest" "$temp" 2>/dev/null || chmod 644 "$temp"
    mv "$temp" "$dest"  # Atomic rename
}

# Usage
generate_config | atomic_write /etc/app/config.yaml
```

### File Locking

```bash
# Lock file for single instance
LOCK_FILE="/var/run/${SCRIPT_NAME}.lock"

acquire_lock() {
    exec 9>"$LOCK_FILE"
    if ! flock -n 9; then
        die "Another instance is running"
    fi
}

release_lock() {
    flock -u 9
    rm -f "$LOCK_FILE"
}

trap release_lock EXIT
acquire_lock
```

---

## Common Patterns

### Confirm Before Action

```bash
confirm() {
    local prompt=${1:-"Continue?"}
    read -rp "$prompt [y/N] " response
    [[ "$response" =~ ^[yY]$ ]]
}

# Usage
if confirm "Delete all files?"; then
    rm -rf /path/to/files
fi

# With default yes
confirm_yes() {
    local prompt=${1:-"Continue?"}
    read -rp "$prompt [Y/n] " response
    [[ ! "$response" =~ ^[nN]$ ]]
}
```

### Dry Run Mode

```bash
DRY_RUN=${DRY_RUN:-false}

run() {
    if [[ "$DRY_RUN" == true ]]; then
        echo "[DRY RUN] $*"
    else
        "$@"
    fi
}

# Usage
run rm -f /tmp/file
run kubectl delete pod nginx
```

### Parallel Execution

```bash
# Process files in parallel
process_parallel() {
    local max_jobs=$1
    shift

    local pids=()
    for item in "$@"; do
        process_item "$item" &
        pids+=($!)

        if [[ ${#pids[@]} -ge $max_jobs ]]; then
            wait -n  # Wait for any job to finish
            pids=($(jobs -rp))  # Update running pids
        fi
    done
    wait  # Wait for remaining
}

# Usage
process_parallel 4 file1 file2 file3 file4 file5
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No shebang | Script might run with wrong shell | Always `#!/bin/bash` |
| Unquoted variables | Breaks on spaces | Always `"$var"` |
| No `set -e` | Errors ignored | Use `set -euo pipefail` |
| Hardcoded paths | Not portable | Use variables, find paths |
| No cleanup | Temp files left behind | Use trap EXIT |
| Parsing ls output | Breaks on special filenames | Use globs or find |

---

## Quiz

### Question 1
What does `set -euo pipefail` do?

<details>
<summary>Show Answer</summary>

Three separate options:

- **`-e`** (errexit): Exit immediately if a command returns non-zero
- **`-u`** (nounset): Exit if an undefined variable is used
- **`-o pipefail`**: The pipeline returns the exit code of the rightmost failing command

Without pipefail:
```bash
false | true  # Exit code 0
```

With pipefail:
```bash
false | true  # Exit code 1
```

This is the recommended start for reliable scripts.

</details>

### Question 2
Why is `rm -rf "$TEMP_DIR"` in a trap better than at the end of the script?

<details>
<summary>Show Answer</summary>

**The trap runs on ANY exit**, including:
- Normal script completion
- `set -e` triggering on error
- Ctrl+C (SIGINT)
- `kill` (SIGTERM)

Without a trap, if the script errors out early, the temp directory remains.

```bash
trap 'rm -rf "$TEMP_DIR"' EXIT
TEMP_DIR=$(mktemp -d)
```

The trap is registered before creating the temp dir, ensuring cleanup even if mktemp somehow fails later in a more complex script.

</details>

### Question 3
How do you ensure a script only runs one instance at a time?

<details>
<summary>Show Answer</summary>

**File locking with flock**:

```bash
LOCK_FILE="/var/run/myscript.lock"

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
    echo "Another instance is running" >&2
    exit 1
fi
```

- Opens file descriptor 9 to the lock file
- `flock -n 9` tries to acquire an exclusive lock
- `-n` makes it non-blocking (fail immediately if locked)
- Lock is released when script exits

Alternative: Check for PID file, but that has race conditions.

</details>

### Question 4
What's wrong with `TEMP=/tmp/myscript.tmp`?

<details>
<summary>Show Answer</summary>

Several problems:

1. **Predictable path** — Security risk (symlink attacks)
2. **Race condition** — Two instances overwrite each other
3. **Not cleaned up** — If script crashes, file remains

Correct approach:
```bash
TEMP=$(mktemp)
trap 'rm -f "$TEMP"' EXIT
```

- `mktemp` creates unique filename
- `trap` ensures cleanup
- Permissions are secure by default

</details>

### Question 5
How do you safely write to a config file that other processes might be reading?

<details>
<summary>Show Answer</summary>

**Atomic write** — write to temp file, then rename:

```bash
generate_config() {
    echo "key=value"
    # ...
}

DEST=/etc/app/config.yaml
TEMP=$(mktemp "${DEST}.XXXXXX")

generate_config > "$TEMP"
chmod 644 "$TEMP"
mv "$TEMP" "$DEST"  # Atomic on same filesystem
```

Why it works:
- `mv` on same filesystem is atomic (rename syscall)
- Other processes never see partial file
- If generation fails, original untouched

</details>

---

## Hands-On Exercise

### Building a Practical Script

**Objective**: Create a production-quality script using patterns from this module.

**Environment**: Any Linux system with Bash

#### Build: Log Analyzer Script

```bash
cat > /tmp/log-analyzer.sh << 'SCRIPT'
#!/bin/bash
#
# Script: log-analyzer.sh
# Description: Analyze log files and report statistics
# Usage: ./log-analyzer.sh [-v] [-n TOP] <logfile>
#

set -euo pipefail

# === Configuration ===
readonly SCRIPT_NAME=$(basename "$0")
readonly VERSION="1.0.0"

# === Defaults ===
VERBOSE=false
TOP_COUNT=10

# === Logging ===
log_info() { echo "[INFO] $*"; }
log_debug() { [[ "$VERBOSE" == true ]] && echo "[DEBUG] $*" || true; }
log_error() { echo "[ERROR] $*" >&2; }

# === Error Handling ===
die() {
    log_error "$@"
    exit 1
}

# === Usage ===
usage() {
    cat << EOF
Usage: $SCRIPT_NAME [options] <logfile>

Analyze log files and report statistics.

Options:
    -h, --help      Show this help message
    -v, --verbose   Enable verbose output
    -n, --top NUM   Show top N results (default: 10)
    --version       Show version

Examples:
    $SCRIPT_NAME /var/log/syslog
    $SCRIPT_NAME -v -n 5 app.log
EOF
    exit 0
}

# === Functions ===
count_by_field() {
    local file=$1
    local field=$2
    log_debug "Counting by field $field"
    awk "{print \$$field}" "$file" | sort | uniq -c | sort -rn | head -n "$TOP_COUNT"
}

analyze_log() {
    local file=$1

    log_info "Analyzing: $file"
    echo

    # Basic stats
    local total_lines=$(wc -l < "$file")
    echo "Total lines: $total_lines"
    echo

    # If it looks like a syslog/access log
    if head -1 "$file" | grep -qE '^[A-Z][a-z]{2} [0-9]|^[0-9]{4}-[0-9]{2}'; then
        echo "=== Log Level Distribution ==="
        grep -oE '(INFO|DEBUG|WARN|WARNING|ERROR|FATAL)' "$file" 2>/dev/null | \
            sort | uniq -c | sort -rn || echo "No log levels found"
        echo
    fi

    # Word frequency
    echo "=== Most Common Words ==="
    tr -cs 'A-Za-z' '\n' < "$file" | \
        tr '[:upper:]' '[:lower:]' | \
        sort | uniq -c | sort -rn | head -n "$TOP_COUNT"
    echo

    log_info "Analysis complete"
}

# === Main ===
main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help) usage ;;
            --version) echo "$SCRIPT_NAME $VERSION"; exit 0 ;;
            -v|--verbose) VERBOSE=true; shift ;;
            -n|--top)
                [[ -n "${2:-}" ]] || die "Missing value for $1"
                TOP_COUNT=$2
                shift 2
                ;;
            -*) die "Unknown option: $1. Use -h for help." ;;
            *) break ;;
        esac
    done

    # Validate arguments
    [[ $# -lt 1 ]] && die "Missing log file. Use -h for help."

    local logfile=$1

    # Validate input
    [[ -f "$logfile" ]] || die "File not found: $logfile"
    [[ -r "$logfile" ]] || die "Cannot read: $logfile"
    [[ -s "$logfile" ]] || die "File is empty: $logfile"

    log_debug "TOP_COUNT=$TOP_COUNT"
    log_debug "VERBOSE=$VERBOSE"

    analyze_log "$logfile"
}

main "$@"
SCRIPT

chmod +x /tmp/log-analyzer.sh
```

#### Test the Script

```bash
# Create test log
cat > /tmp/test.log << 'EOF'
2024-01-15 10:00:00 INFO Application started
2024-01-15 10:00:01 DEBUG Loading configuration
2024-01-15 10:00:02 INFO Connected to database
2024-01-15 10:00:03 WARNING Slow query detected
2024-01-15 10:00:04 ERROR Connection timeout
2024-01-15 10:00:05 INFO Retrying connection
2024-01-15 10:00:06 DEBUG Cache miss
2024-01-15 10:00:07 INFO Connection established
2024-01-15 10:00:08 ERROR Authentication failed
2024-01-15 10:00:09 WARN Rate limit exceeded
2024-01-15 10:00:10 INFO Request processed successfully
EOF

# Test runs
/tmp/log-analyzer.sh --help
/tmp/log-analyzer.sh --version
/tmp/log-analyzer.sh /tmp/test.log
/tmp/log-analyzer.sh -v -n 5 /tmp/test.log

# Test error handling
/tmp/log-analyzer.sh /nonexistent 2>&1 || true
/tmp/log-analyzer.sh --invalid 2>&1 || true
```

#### Extend the Script

```bash
# Add these features:
# 1. Output format option (text/json)
# 2. Date range filtering
# 3. Error-only mode

# Example addition for error-only:
# Add to argument parsing:
#   -e|--errors) ERRORS_ONLY=true; shift ;;

# Add to analyze_log:
#   if [[ "$ERRORS_ONLY" == true ]]; then
#       grep -E "ERROR|FATAL" "$file"
#       return
#   fi
```

### Success Criteria

- [ ] Script uses `set -euo pipefail`
- [ ] Has proper argument parsing with help
- [ ] Validates input files
- [ ] Has logging functions
- [ ] Handles errors gracefully
- [ ] Runs without errors on valid input

---

## Key Takeaways

1. **Start with `set -euo pipefail`** — Catch errors early

2. **Use traps for cleanup** — Always clean up temp files

3. **Validate all inputs** — Don't trust arguments or files

4. **Log meaningfully** — Future debugging depends on it

5. **Dry-run mode is essential** — Test safely before executing

---

## What's Next?

In **Module 7.4: DevOps Automation**, you'll apply these patterns to real operational tasks—kubectl wrappers, deployment scripts, and CI/CD automation.

---

## Further Reading

- [ShellCheck](https://www.shellcheck.net/) — Lint your scripts
- [Bash Strict Mode](http://redsymbol.net/articles/unofficial-bash-strict-mode/)
- [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html)
- [Pure Bash Bible](https://github.com/dylanaraps/pure-bash-bible)
