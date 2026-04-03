#!/bin/bash
# KubeDojo - Claude Code Wrapper
# Ensures extensions are deployed and starts Claude

set -e

# Ensure ~/.local/bin is in PATH (where claude installs by default)
export PATH="$HOME/.local/bin:$PATH"
hash -r 2>/dev/null || true  # Clear command cache

# Get script directory (project root)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starting Claude in KubeDojo project..."
echo "Project: $PROJECT_DIR"

# Preflight check: Verify required tools
echo "Preflight check..."
MISSING_TOOLS=""
for tool in git gh kubectl; do
    if ! command -v $tool &> /dev/null; then
        MISSING_TOOLS="$MISSING_TOOLS $tool"
    fi
done

if [ -n "$MISSING_TOOLS" ]; then
    echo "Warning: Optional tools not found:$MISSING_TOOLS"
    echo "   (These are recommended but not required to start)"
fi

# Check for npx (required to launch Claude Code)
if ! command -v npx &> /dev/null; then
    echo "Error: npx not found"
    echo "   Install Node.js: https://nodejs.org/"
    exit 1
fi
echo "npx found"

# Change to project directory
cd "$PROJECT_DIR"

# Show current branch
if git rev-parse --git-dir > /dev/null 2>&1; then
    CURRENT_BRANCH=$(git branch --show-current)
    echo "Current branch: $CURRENT_BRANCH"

    # Check for uncommitted changes
    if [ -n "$(git status --porcelain)" ]; then
        echo "Uncommitted changes detected"
    fi
fi

# Deploy Claude skills (always run to ensure up-to-date)
if [ -f "package.json" ] && grep -q "claude:deploy" package.json 2>/dev/null; then
    echo "Checking Claude skills..."
    npm run claude:deploy --silent 2>/dev/null || true
    echo "Skills deployed"
fi

# Show KubeDojo status (dynamically from STATUS.md)
echo ""
echo "KUBEDOJO - Cloud Native Curriculum"

if [ -f "STATUS.md" ]; then
    # Extract current state line
    CURRENT_STATE=$(grep -A1 "## Current State" STATUS.md | tail -1 | sed 's/^\*\*//' | sed 's/\*\*.*//')
    if [ -n "$CURRENT_STATE" ]; then
        echo "   Status: $CURRENT_STATE"
    fi

    # Extract curriculum summary table
    echo "   Tracks:"
    grep -E "^\| (Prerequisites|Linux|Cloud|Certifications|Platform) \|" STATUS.md 2>/dev/null | while read line; do
        NAME=$(echo "$line" | cut -d'|' -f2 | xargs)
        MODULES=$(echo "$line" | cut -d'|' -f3 | xargs)
        STATUS=$(echo "$line" | cut -d'|' -f4 | xargs)
        echo "       $NAME: $MODULES modules ($STATUS)"
    done

    # Extract first TODO item
    NEXT=$(grep -m1 "^\- \[ \]" STATUS.md | sed 's/^- \[ \] //')
    if [ -n "$NEXT" ]; then
        echo "   Next: $NEXT"
    fi
else
    echo "   (STATUS.md not found - run from project root)"
fi

echo "   Issues: https://github.com/kube-dojo/kube-dojo.github.io/issues"
echo "   Commands: /review-module, /review-part, /verify-technical"

# Check if kubectl can connect (optional)
if command -v kubectl &> /dev/null; then
    if kubectl cluster-info &> /dev/null 2>&1; then
        CLUSTER_NAME=$(kubectl config current-context 2>/dev/null || echo "unknown")
        echo "   K8s cluster: $CLUSTER_NAME (connected)"
    else
        echo "   K8s cluster: (not connected)"
    fi
fi

echo ""

# Launch via npx to avoid cache bugs (stale binary + prompt caching issues)
# See: https://reddit.com/r/ClaudeAI/comments/1s7mkn3/
echo "Launching Claude Code via npx (cache-safe)..."
npx @anthropic-ai/claude-code@latest --chrome --permission-mode bypassPermissions "$@"
