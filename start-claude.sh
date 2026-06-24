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

# Claude Code runs as a standalone native binary (no Node/npx needed); the
# presence check + install hint lives next to the launch at the bottom.

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

# Autocompact effectively disabled — set to the full 1M cap so it cannot
# trigger before the model itself hits the window limit. We never want
# auto-compact: it is destructive (summarizes context, loses fidelity).
# Instead, durable session handoff via docs/session-state/YYYY-MM-DD-*.html
# + STATUS.md happens at ~500K used (statusline goes bold-red at that point;
# see agents_extensions/claude/statusline/statusline.sh handoff-discipline bands).
export CLAUDE_CODE_AUTO_COMPACT_WINDOW=1000000

# Launch the self-updating native build straight from PATH (installed to
# ~/.local/bin via `claude install`; PATH is prepended at the top of this
# script). This mirrors how start-codex.sh runs `codex` from PATH.
#
# We deliberately no longer use `npx @anthropic-ai/claude-code@latest`. With the
# native-binary packaging the npm package ships a 500-byte error stub at
# bin/claude.exe that a postinstall must overwrite with the ~220MB binary; under
# npx that step is flaky and the broken stub gets *cached* in ~/.npm/_npx — the
# recurring "claude native binary not installed" failure. The native install has
# no such step. npx's only real benefit was staleness-avoidance, which the
# background `claude update` below covers without the fragility.
if ! command -v claude >/dev/null 2>&1; then
    echo "Error: 'claude' not found on PATH."
    echo "  Install the self-updating native build:"
    echo "      curl -fsSL https://claude.ai/install.sh | bash"
    echo "  (it installs to ~/.local/bin, which this script already puts on PATH)"
    exit 1
fi

# Keep it current without blocking startup: this refreshes the binary for the
# NEXT launch (the native updater writes a new versioned dir + repoints the
# symlink; it never touches the running process). No-op when already latest or
# offline.
( claude update >/dev/null 2>&1 & )

# --- headroom routing: DISABLED (user, 2026-06-24, s181) ---
# Headroom proxy routing turned OFF. Its pre-upstream compression tripped the
# 30s stream-idle timeout on large model outputs (full-chapter translation
# Writes) and made large Read outputs lossy ([N compressed...] silently drops
# source -- see feedback_never_translate_from_compressed_read). Launch Claude
# DIRECT, no proxy. Force-unset the routing vars regardless of shell/.profile so
# nothing leaks through. The proxy daemon may keep running idle (harmless) --
# stop it separately from a clean session if desired; do NOT `headroom install`.
# To RE-ENABLE: restore the prior "headroom routing guard" block from git
# history (present until this commit) and confirm the proxy is healthy.
unset ANTHROPIC_BASE_URL OPENAI_BASE_URL COPILOT_PROVIDER_BASE_URL
echo "headroom routing DISABLED -- launching Claude DIRECT (no proxy)"
# --- end headroom routing ---

echo "Launching Claude Code (native build from PATH: $(command -v claude))..."
exec claude --chrome --permission-mode bypassPermissions "$@"
