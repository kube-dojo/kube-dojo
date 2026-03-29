---
title: "Module 7.4: DevOps Automation"
slug: linux/operations/shell-scripting/module-7.4-devops-automation
sidebar:
  order: 5
---
> **Shell Scripting** | Complexity: `[MEDIUM]` | Time: 30-35 min

## Prerequisites

Before starting this module:
- **Required**: [Module 7.3: Practical Scripts](../module-7.3-practical-scripts/)
- **Required**: Basic kubectl knowledge
- **Helpful**: CI/CD experience

---

## Why This Module Matters

DevOps work is repetitive. Deployments, health checks, log analysis, cluster management—all these tasks benefit from automation. Shell scripts are often the right tool: they're portable, require no installation, and compose well with existing tools.

Understanding DevOps automation helps you:

- **Speed up operations** — One command instead of many
- **Reduce errors** — Scripts don't make typos
- **Enable self-service** — Others can use your scripts
- **Document processes** — Scripts are runnable documentation

The best automation is the kind you forget exists because it just works.

---

## Did You Know?

- **kubectl is designed for scripting** — JSON output, `-o jsonpath`, and `--dry-run=client` are all meant for automation.

- **CI/CD pipelines are just shell scripts** — Whether it's GitHub Actions, GitLab CI, or Jenkins, the core is running shell commands.

- **Most outages involve shell scripts** — Either directly (bad script) or indirectly (manual steps that should have been scripted).

- **SSH can be automated too** — But prefer tools like Ansible for multi-host operations. Shell scripts are for single-host tasks or kubectl orchestration.

---

## kubectl Scripting

### Output Formats

```bash
# JSON for full data
kubectl get pods -o json

# JSONPath for specific fields
kubectl get pods -o jsonpath='{.items[*].metadata.name}'

# Custom columns
kubectl get pods -o custom-columns='NAME:.metadata.name,STATUS:.status.phase'

# YAML for config
kubectl get deployment nginx -o yaml

# Name only
kubectl get pods -o name
# pod/nginx-abc123
```

### Common Patterns

```bash
# Get all pod names
kubectl get pods -o jsonpath='{.items[*].metadata.name}' | tr ' ' '\n'

# Get images used
kubectl get pods -o jsonpath='{.items[*].spec.containers[*].image}' | tr ' ' '\n' | sort -u

# Get pods not Running
kubectl get pods --field-selector='status.phase!=Running'

# Get pods by label
kubectl get pods -l app=nginx -o name

# Watch for changes
kubectl get pods -w

# Wait for condition
kubectl wait --for=condition=Ready pod -l app=nginx --timeout=60s
```

### Scripted Operations

```bash
#!/bin/bash
# Restart all pods in a deployment

restart_deployment() {
    local deployment=$1
    local namespace=${2:-default}

    echo "Restarting deployment: $deployment in namespace: $namespace"

    kubectl rollout restart deployment "$deployment" -n "$namespace"
    kubectl rollout status deployment "$deployment" -n "$namespace" --timeout=5m

    echo "Restart complete"
}

restart_deployment nginx production
```

---

## Health Check Scripts

### Pod Health Check

```bash
#!/bin/bash
set -euo pipefail

check_pods() {
    local namespace=${1:---all-namespaces}

    echo "Checking pod health..."

    # Count by status
    echo "=== Pod Status Summary ==="
    kubectl get pods $namespace --no-headers | awk '{print $3}' | sort | uniq -c | sort -rn

    # List non-running pods
    local unhealthy=$(kubectl get pods $namespace --no-headers | awk '$3 != "Running" && $3 != "Completed" {print $1}')

    if [[ -n "$unhealthy" ]]; then
        echo ""
        echo "=== Unhealthy Pods ==="
        kubectl get pods $namespace | grep -E "^NAME|$(echo $unhealthy | tr ' ' '|')"
        return 1
    fi

    echo ""
    echo "All pods healthy!"
    return 0
}

check_pods "$@"
```

### Node Health Check

```bash
#!/bin/bash
set -euo pipefail

check_nodes() {
    echo "=== Node Status ==="
    kubectl get nodes

    echo ""
    echo "=== Node Conditions ==="
    kubectl get nodes -o json | jq -r '
        .items[] |
        "Node: \(.metadata.name)",
        (.status.conditions[] | "  \(.type): \(.status)"),
        ""
    '

    echo "=== Resource Usage ==="
    kubectl top nodes 2>/dev/null || echo "Metrics server not available"

    # Check for NotReady nodes
    local not_ready=$(kubectl get nodes --no-headers | awk '$2 != "Ready" {print $1}')
    if [[ -n "$not_ready" ]]; then
        echo ""
        echo "WARNING: NotReady nodes: $not_ready"
        return 1
    fi
}

check_nodes
```

### Service Health Check

```bash
#!/bin/bash
set -euo pipefail

check_service() {
    local service=$1
    local namespace=${2:-default}

    echo "Checking service: $service in namespace: $namespace"

    # Service exists?
    kubectl get svc "$service" -n "$namespace" > /dev/null 2>&1 || {
        echo "ERROR: Service not found"
        return 1
    }

    # Has endpoints?
    local endpoints=$(kubectl get endpoints "$service" -n "$namespace" -o jsonpath='{.subsets[*].addresses[*].ip}')

    if [[ -z "$endpoints" ]]; then
        echo "ERROR: No endpoints for service"
        kubectl get endpoints "$service" -n "$namespace"
        return 1
    fi

    echo "Endpoints: $endpoints"

    # Try to connect (from inside cluster)
    local cluster_ip=$(kubectl get svc "$service" -n "$namespace" -o jsonpath='{.spec.clusterIP}')
    local port=$(kubectl get svc "$service" -n "$namespace" -o jsonpath='{.spec.ports[0].port}')

    echo "ClusterIP: $cluster_ip:$port"
    echo "Service appears healthy"
}

check_service "$@"
```

---

## Deployment Scripts

### Safe Deployment

```bash
#!/bin/bash
set -euo pipefail

deploy() {
    local image=$1
    local deployment=${2:-app}
    local namespace=${3:-default}

    echo "Deploying $image to $deployment in $namespace"

    # Record current image for rollback
    local current_image=$(kubectl get deployment "$deployment" -n "$namespace" \
        -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null || echo "none")
    echo "Current image: $current_image"

    # Update image
    kubectl set image deployment/"$deployment" \
        "${deployment}=${image}" \
        -n "$namespace"

    # Wait for rollout
    if ! kubectl rollout status deployment/"$deployment" -n "$namespace" --timeout=5m; then
        echo "ERROR: Rollout failed, initiating rollback"
        kubectl rollout undo deployment/"$deployment" -n "$namespace"
        kubectl rollout status deployment/"$deployment" -n "$namespace" --timeout=5m
        return 1
    fi

    echo "Deployment successful"
}

deploy "$@"
```

### Blue-Green Script

```bash
#!/bin/bash
set -euo pipefail

blue_green_deploy() {
    local app=$1
    local new_image=$2
    local namespace=${3:-default}

    local active=$(kubectl get svc "$app" -n "$namespace" \
        -o jsonpath='{.spec.selector.version}')

    local inactive
    if [[ "$active" == "blue" ]]; then
        inactive="green"
    else
        inactive="blue"
    fi

    echo "Active: $active, Deploying to: $inactive"

    # Update inactive deployment
    kubectl set image deployment/"${app}-${inactive}" \
        "${app}=${new_image}" -n "$namespace"

    # Wait for ready
    kubectl rollout status deployment/"${app}-${inactive}" \
        -n "$namespace" --timeout=5m

    # Health check
    echo "Running health check on $inactive..."
    sleep 10  # Wait for pods to stabilize

    # Switch service
    echo "Switching service to $inactive"
    kubectl patch svc "$app" -n "$namespace" \
        -p "{\"spec\":{\"selector\":{\"version\":\"$inactive\"}}}"

    echo "Blue-green deployment complete"
    echo "Previous version ($active) is still running"
    echo "Run: kubectl scale deployment/${app}-${active} --replicas=0"
}

blue_green_deploy "$@"
```

---

## Log Analysis Scripts

### Pod Log Aggregator

```bash
#!/bin/bash
set -euo pipefail

aggregate_logs() {
    local label=$1
    local namespace=${2:-default}
    local since=${3:-1h}

    echo "Aggregating logs for pods with label: $label"

    local pods=$(kubectl get pods -l "$label" -n "$namespace" -o name)

    if [[ -z "$pods" ]]; then
        echo "No pods found"
        return 1
    fi

    for pod in $pods; do
        echo "=== ${pod} ==="
        kubectl logs "$pod" -n "$namespace" --since="$since" | tail -50
        echo ""
    done
}

aggregate_logs "$@"
```

### Error Finder

```bash
#!/bin/bash
set -euo pipefail

find_errors() {
    local namespace=${1:---all-namespaces}
    local since=${2:-1h}

    echo "Finding errors in pods..."

    local pods=$(kubectl get pods $namespace -o name)

    for pod in $pods; do
        local ns=""
        if [[ "$namespace" == "--all-namespaces" ]]; then
            ns=$(echo "$pod" | cut -d/ -f1)
            pod=$(echo "$pod" | cut -d/ -f2)
        fi

        local errors=$(kubectl logs "$pod" ${ns:+-n $ns} --since="$since" 2>/dev/null | \
            grep -iE "error|exception|fatal|panic" | head -5)

        if [[ -n "$errors" ]]; then
            echo "=== $pod ==="
            echo "$errors"
            echo ""
        fi
    done
}

find_errors "$@"
```

---

## CI/CD Helpers

### Version Bumping

```bash
#!/bin/bash
set -euo pipefail

bump_version() {
    local current=$1
    local type=${2:-patch}

    IFS='.' read -r major minor patch <<< "$current"

    case $type in
        major) ((major++)); minor=0; patch=0 ;;
        minor) ((minor++)); patch=0 ;;
        patch) ((patch++)) ;;
        *) echo "Unknown type: $type"; return 1 ;;
    esac

    echo "${major}.${minor}.${patch}"
}

# Usage
current=$(cat VERSION)
new=$(bump_version "$current" patch)
echo "$new" > VERSION
git add VERSION
git commit -m "Bump version to $new"
```

### Build Script

```bash
#!/bin/bash
set -euo pipefail

readonly APP_NAME=${APP_NAME:-myapp}
readonly REGISTRY=${REGISTRY:-docker.io}
readonly VERSION=$(git describe --tags --always --dirty)

build() {
    echo "Building ${APP_NAME}:${VERSION}"

    docker build \
        --build-arg VERSION="$VERSION" \
        --build-arg BUILD_TIME="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        -t "${REGISTRY}/${APP_NAME}:${VERSION}" \
        -t "${REGISTRY}/${APP_NAME}:latest" \
        .

    echo "Build complete: ${REGISTRY}/${APP_NAME}:${VERSION}"
}

push() {
    echo "Pushing to registry..."
    docker push "${REGISTRY}/${APP_NAME}:${VERSION}"
    docker push "${REGISTRY}/${APP_NAME}:latest"
}

main() {
    local cmd=${1:-build}
    case $cmd in
        build) build ;;
        push) push ;;
        all) build && push ;;
        *) echo "Usage: $0 {build|push|all}" ;;
    esac
}

main "$@"
```

### Deployment Pipeline Helper

```bash
#!/bin/bash
set -euo pipefail

# Validate deployment
validate_deploy() {
    local deployment=$1
    local namespace=$2
    local timeout=${3:-300}

    local start=$(date +%s)

    while true; do
        local ready=$(kubectl get deployment "$deployment" -n "$namespace" \
            -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo 0)
        local desired=$(kubectl get deployment "$deployment" -n "$namespace" \
            -o jsonpath='{.spec.replicas}')

        echo "Ready: $ready / $desired"

        if [[ "$ready" == "$desired" ]] && [[ "$ready" != "0" ]]; then
            echo "Deployment ready!"
            return 0
        fi

        local elapsed=$(($(date +%s) - start))
        if [[ $elapsed -gt $timeout ]]; then
            echo "Timeout waiting for deployment"
            return 1
        fi

        sleep 5
    done
}

# Run smoke tests
smoke_test() {
    local url=$1
    local expected=${2:-200}

    echo "Testing $url"
    local status=$(curl -s -o /dev/null -w '%{http_code}' "$url")

    if [[ "$status" == "$expected" ]]; then
        echo "OK: Got $status"
        return 0
    else
        echo "FAIL: Expected $expected, got $status"
        return 1
    fi
}
```

---

## Operational Scripts

### Namespace Cleanup

```bash
#!/bin/bash
set -euo pipefail

cleanup_namespace() {
    local namespace=$1
    local dry_run=${2:-true}

    echo "Cleaning up namespace: $namespace"

    # Find completed/failed pods
    local pods=$(kubectl get pods -n "$namespace" \
        --field-selector='status.phase!=Running,status.phase!=Pending' \
        -o name 2>/dev/null)

    if [[ -z "$pods" ]]; then
        echo "No pods to clean"
        return 0
    fi

    echo "Pods to delete:"
    echo "$pods"

    if [[ "$dry_run" == "false" ]]; then
        echo "$pods" | xargs -r kubectl delete -n "$namespace"
        echo "Cleanup complete"
    else
        echo "[DRY RUN] Would delete above pods"
    fi
}

cleanup_namespace "${1:-default}" "${2:-true}"
```

### Resource Report

```bash
#!/bin/bash
set -euo pipefail

resource_report() {
    local namespace=${1:---all-namespaces}

    echo "=== Resource Report ==="
    echo "Generated: $(date)"
    echo ""

    echo "=== Node Resources ==="
    kubectl top nodes 2>/dev/null || echo "Metrics unavailable"
    echo ""

    echo "=== Pod Resources ==="
    kubectl top pods $namespace 2>/dev/null | head -20 || echo "Metrics unavailable"
    echo ""

    echo "=== Deployments ==="
    kubectl get deployments $namespace --no-headers | \
        awk '{printf "%-40s %s/%s\n", $1, $2, $3}'
    echo ""

    echo "=== PVCs ==="
    kubectl get pvc $namespace --no-headers | \
        awk '{printf "%-40s %-10s %s\n", $1, $4, $3}'
}

resource_report "$@"
```

### Secret Backup

```bash
#!/bin/bash
set -euo pipefail

backup_secrets() {
    local namespace=${1:-default}
    local backup_dir=${2:-./secrets-backup}

    mkdir -p "$backup_dir"

    echo "Backing up secrets from namespace: $namespace"

    local secrets=$(kubectl get secrets -n "$namespace" -o name)

    for secret in $secrets; do
        local name=$(basename "$secret")
        echo "Backing up: $name"

        kubectl get "$secret" -n "$namespace" -o yaml | \
            grep -v "resourceVersion\|uid\|creationTimestamp" > \
            "${backup_dir}/${namespace}-${name}.yaml"
    done

    echo "Backup complete: $backup_dir"
    ls -la "$backup_dir"
}

backup_secrets "$@"
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No error handling in pipelines | CI passes when it shouldn't | Use `set -e`, check exit codes |
| Hardcoded namespaces | Script only works in one place | Accept namespace as parameter |
| No dry-run mode | Dangerous to test | Always add `--dry-run` option |
| Ignoring kubectl failures | Partial operations | Check return codes |
| No timeout on waits | Infinite loops | Always set timeouts |
| Secrets in scripts | Security risk | Use environment variables |

---

## Quiz

### Question 1
How do you get just the names of all pods in a namespace?

<details>
<summary>Show Answer</summary>

Several ways:

```bash
# Using -o name
kubectl get pods -n default -o name
# pod/nginx-abc123
# pod/redis-def456

# Using jsonpath
kubectl get pods -n default -o jsonpath='{.items[*].metadata.name}'
# nginx-abc123 redis-def456

# Using custom-columns
kubectl get pods -n default -o custom-columns=':metadata.name' --no-headers
# nginx-abc123
# redis-def456
```

`-o name` is simplest, but includes `pod/` prefix.

</details>

### Question 2
How do you wait for a deployment to be ready in a script?

<details>
<summary>Show Answer</summary>

```bash
kubectl rollout status deployment/nginx --timeout=5m
```

Or with `kubectl wait`:
```bash
kubectl wait --for=condition=Available deployment/nginx --timeout=300s
```

For pods:
```bash
kubectl wait --for=condition=Ready pod -l app=nginx --timeout=60s
```

Always include `--timeout` to prevent infinite waits.

</details>

### Question 3
How do you safely update a deployment image in a script?

<details>
<summary>Show Answer</summary>

```bash
# Update image
kubectl set image deployment/myapp myapp=myapp:v2

# Wait for rollout
if ! kubectl rollout status deployment/myapp --timeout=5m; then
    echo "Rollout failed, rolling back"
    kubectl rollout undo deployment/myapp
    exit 1
fi
```

Key points:
- Use `kubectl set image` (not `kubectl apply` for just image changes)
- Wait for `rollout status`
- Handle failure with `rollout undo`
- Set timeouts

</details>

### Question 4
What's the difference between `kubectl get pods -o json | jq` and `kubectl get pods -o jsonpath`?

<details>
<summary>Show Answer</summary>

**jsonpath** (built-in):
- No external dependency
- Simpler syntax for basic queries
- Limited transformation capabilities

```bash
kubectl get pods -o jsonpath='{.items[*].metadata.name}'
```

**jq** (external):
- Requires jq installed
- More powerful querying and transformation
- Better for complex operations

```bash
kubectl get pods -o json | jq -r '.items[].metadata.name'
```

Use jsonpath for simple extractions, jq for complex transformations.

</details>

### Question 5
How do you make a script work in any namespace?

<details>
<summary>Show Answer</summary>

Accept namespace as a parameter with a default:

```bash
#!/bin/bash
namespace=${1:-default}

kubectl get pods -n "$namespace"
```

Or use a flag:
```bash
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--namespace) namespace=$2; shift 2 ;;
        *) break ;;
    esac
done
namespace=${namespace:-default}

kubectl get pods -n "$namespace"
```

Never hardcode namespaces in reusable scripts.

</details>

---

## Hands-On Exercise

### Building DevOps Scripts

**Objective**: Create practical DevOps automation scripts.

**Environment**: Kubernetes cluster (kind, minikube, or real)

#### Script 1: Cluster Health Check

```bash
cat > /tmp/cluster-health.sh << 'EOF'
#!/bin/bash
set -euo pipefail

echo "=== Cluster Health Check ==="
echo "Time: $(date)"
echo ""

# Nodes
echo "=== Nodes ==="
kubectl get nodes -o wide
echo ""

# Check node conditions
echo "=== Node Issues ==="
kubectl get nodes -o json | jq -r '
  .items[] |
  select(.status.conditions[] | select(.type != "Ready" and .status == "True")) |
  "WARNING: \(.metadata.name) has issues"
' || echo "All nodes healthy"
echo ""

# Pods not running
echo "=== Non-Running Pods ==="
kubectl get pods --all-namespaces --field-selector='status.phase!=Running,status.phase!=Succeeded' 2>/dev/null || echo "All pods running"
echo ""

# Resource usage (if metrics available)
echo "=== Resource Usage ==="
kubectl top nodes 2>/dev/null || echo "Metrics not available"
echo ""

echo "Health check complete"
EOF

chmod +x /tmp/cluster-health.sh
/tmp/cluster-health.sh
```

#### Script 2: Deployment Helper

```bash
cat > /tmp/deploy-helper.sh << 'EOF'
#!/bin/bash
set -euo pipefail

usage() {
    echo "Usage: $0 <deployment> <image> [-n namespace] [--dry-run]"
    exit 1
}

[[ $# -lt 2 ]] && usage

deployment=$1
image=$2
namespace="default"
dry_run=""

shift 2
while [[ $# -gt 0 ]]; do
    case $1 in
        -n) namespace=$2; shift 2 ;;
        --dry-run) dry_run="--dry-run=client"; shift ;;
        *) usage ;;
    esac
done

echo "Deployment: $deployment"
echo "Image: $image"
echo "Namespace: $namespace"
[[ -n "$dry_run" ]] && echo "DRY RUN MODE"

# Current image
current=$(kubectl get deployment "$deployment" -n "$namespace" \
    -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null || echo "none")
echo "Current image: $current"
echo ""

if [[ "$current" == "$image" ]]; then
    echo "Already running this image"
    exit 0
fi

# Update
echo "Updating deployment..."
kubectl set image deployment/"$deployment" "$deployment=$image" -n "$namespace" $dry_run

if [[ -z "$dry_run" ]]; then
    echo "Waiting for rollout..."
    kubectl rollout status deployment/"$deployment" -n "$namespace" --timeout=5m
fi

echo "Done"
EOF

chmod +x /tmp/deploy-helper.sh

# Test (dry run)
/tmp/deploy-helper.sh nginx nginx:latest -n default --dry-run
```

#### Script 3: Log Searcher

```bash
cat > /tmp/log-search.sh << 'EOF'
#!/bin/bash
set -euo pipefail

pattern=${1:-"error"}
namespace=${2:---all-namespaces}
since=${3:-1h}

echo "Searching for '$pattern' in logs..."
echo "Namespace: $namespace"
echo "Since: $since"
echo ""

found=0
for pod in $(kubectl get pods $namespace -o name); do
    # Get namespace if all namespaces
    if [[ "$namespace" == "--all-namespaces" ]]; then
        ns=$(echo "$pod" | cut -d'/' -f1)
        pod_name=$(echo "$pod" | cut -d'/' -f2)
        ns_flag="-n $ns"
    else
        pod_name=$(basename "$pod")
        ns_flag="-n $namespace"
    fi

    matches=$(kubectl logs "$pod_name" $ns_flag --since="$since" 2>/dev/null | \
        grep -i "$pattern" | head -5 || true)

    if [[ -n "$matches" ]]; then
        echo "=== $pod_name ==="
        echo "$matches"
        echo ""
        ((found++)) || true
    fi
done

echo "Found matches in $found pods"
EOF

chmod +x /tmp/log-search.sh
/tmp/log-search.sh "error" default "1h"
```

#### Script 4: Resource Analyzer

```bash
cat > /tmp/resource-analyzer.sh << 'EOF'
#!/bin/bash
set -euo pipefail

namespace=${1:-default}

echo "=== Resource Analysis for namespace: $namespace ==="
echo ""

# CPU and Memory requests/limits
echo "=== Container Resources ==="
kubectl get pods -n "$namespace" -o json | jq -r '
  .items[] |
  .spec.containers[] |
  "\(.name): CPU: \(.resources.requests.cpu // "none")/\(.resources.limits.cpu // "none") MEM: \(.resources.requests.memory // "none")/\(.resources.limits.memory // "none")"
'

echo ""
echo "=== Containers without limits ==="
kubectl get pods -n "$namespace" -o json | jq -r '
  .items[] |
  .spec.containers[] |
  select(.resources.limits == null or .resources.limits == {}) |
  .name
' | sort -u || echo "All containers have limits"

echo ""
echo "=== PVC Usage ==="
kubectl get pvc -n "$namespace" --no-headers | \
    awk '{printf "%-30s %-10s %s\n", $1, $4, $3}'
EOF

chmod +x /tmp/resource-analyzer.sh
/tmp/resource-analyzer.sh default
```

### Success Criteria

- [ ] Created cluster health check script
- [ ] Built deployment helper with dry-run mode
- [ ] Implemented log searcher across pods
- [ ] Created resource analyzer
- [ ] All scripts handle errors gracefully

---

## Key Takeaways

1. **kubectl is scriptable** — Use `-o json`, jsonpath, and jq

2. **Always add dry-run** — Test safely before executing

3. **Handle failures** — `rollout undo` for failed deployments

4. **Set timeouts** — Never wait forever

5. **Make scripts reusable** — Parameters for namespace, labels, etc.

---

## Congratulations!

You've completed the **Linux Deep Dive Track**! You now have a solid foundation in:
- Linux fundamentals (kernel, processes, filesystems)
- Container primitives (namespaces, cgroups, capabilities)
- Networking (TCP/IP, DNS, iptables)
- Security hardening (AppArmor, SELinux, seccomp)
- Performance analysis (USE method, CPU, memory, I/O)
- Troubleshooting (systematic debugging, logs, processes, network)
- Shell scripting (Bash, text processing, automation)

These skills are essential for Kubernetes administration, SRE, and DevOps work.

---

## Further Reading

- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Bash Automation Best Practices](https://bertvv.github.io/cheat-sheets/Bash.html)
- [12 Factor App](https://12factor.net/) — CI/CD principles
- [Kustomize](https://kustomize.io/) — For complex deployments beyond scripts
