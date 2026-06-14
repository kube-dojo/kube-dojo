#!/usr/bin/env bash
# Cold-start ritual for a fresh KubeDojo agent session.
# Brings up services, emits local working-tree state, API orientation,
# and a STATUS.md fallback when the API is unreachable.
#
# Single source of truth for agent orientation — see also:
#   scripts/prompts/cold-start.md
#   .claude/skills/cold-start/SKILL.md
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

INCLUDE_MANIFEST=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --manifest)
      INCLUDE_MANIFEST=1
      shift
      ;;
    --issue)
      if [[ $# -lt 2 ]]; then
        echo "Missing argument for --issue" >&2
        exit 2
      fi
      KUBEDOJO_ISSUE="$2"
      shift 2
      ;;
    -h|--help)
      cat <<'EOF'
Usage: scripts/cold-start.sh [--manifest] [--issue N]

Deterministic cold-start for coding agents: services-up, workspace state,
pending decisions, then API orientation (briefing + orient + session pointer).

Options:
  --manifest           Append the /api/state/manifest section (route discovery)
  --issue N            Print issue-first reminder for GitHub issue #N
                       (same as KUBEDOJO_ISSUE=N; flag takes precedence)

Environment:
  KUBEDOJO_ISSUE=N     Print issue-first reminder for GitHub issue #N
  KUBEDOJO_API=URL       API base (default http://127.0.0.1:8768)
  KUBEDOJO_API_TIMEOUT=  curl --max-time seconds (default 2)

On API failure: prints STATUS.md excerpt + handoff path, exits 0.
EOF
      exit 0
      ;;
    *)
      echo "Unknown option: $1 (try --help)" >&2
      exit 2
      ;;
  esac
done

if [[ -n "${KUBEDOJO_ISSUE:-}" ]]; then
  echo "--- kubedojo:issue ---"
  echo "Parent task: gh issue view ${KUBEDOJO_ISSUE} --repo kube-dojo/kube-dojo.github.io"
  echo "Claim via: gh issue comment ${KUBEDOJO_ISSUE} --body \"Claiming — worktree .worktrees/<name>\""
  echo ""
fi

scripts/services-up >&2 || true

echo "--- kubedojo:workspace ---"
git status --short || true
# Read-only freshness check (#1961): a session that cold-starts from a primary
# behind origin/main can re-fire already-merged work (the learn-ukrainian
# Session-28/29 re-collision). Fetch is read-only and NEVER auto-pulls — we only
# warn (destructive/auto git on the user's tree is banned, see
# feedback_never_destructive_git_on_user_files). `|| true` keeps cold-start
# working offline.
git fetch --quiet origin main 2>/dev/null || true
behind=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo 0)
if [[ "${behind:-0}" -gt 0 ]]; then
  echo "⚠ primary is ${behind} commit(s) BEHIND origin/main — STATUS/handoff below may be stale."
  echo "  sync first (non-destructive): git pull --ff-only origin main"
fi
echo ""

echo "--- kubedojo:pending-decisions ---"
if pending=$(ls docs/decisions/pending/ 2>/dev/null | head -5); then
  printf '%s\n' "$pending"
else
  echo "(empty)"
fi
echo ""

API="${KUBEDOJO_API:-http://127.0.0.1:8768}"
MAX_TIME="${KUBEDOJO_API_TIMEOUT:-2}"
TMPDIR_COLD="/tmp/kubedojo_coldstart_$$"
mkdir -p "$TMPDIR_COLD"
trap 'rm -rf "$TMPDIR_COLD"' EXIT

api_get() {
  curl -sf --max-time "$MAX_TIME" "${API}${1}" 2>/dev/null
}

API_OK=0
for _ in 1 2 3 4 5; do
  if api_get "/api/briefing/session?compact=1" >"$TMPDIR_COLD/briefing.json"; then
    API_OK=1
    break
  fi
  sleep 1
done

if [[ "$API_OK" -eq 1 ]]; then
  echo "--- kubedojo:briefing ---"
  cat "$TMPDIR_COLD/briefing.json"
  echo ""

  echo "--- kubedojo:orient ---"
  if api_get "/api/orient" >"$TMPDIR_COLD/orient.json"; then
    cat "$TMPDIR_COLD/orient.json"
  else
    echo '{"error":"orient_unavailable"}'
  fi
  echo ""

  echo "--- kubedojo:session ---"
  if api_get "/api/session/current" >"$TMPDIR_COLD/session.json"; then
    cat "$TMPDIR_COLD/session.json"
  else
    echo '{"error":"session_unavailable"}'
  fi
  echo ""

  if [[ "$INCLUDE_MANIFEST" -eq 1 ]]; then
    echo "--- kubedojo:manifest ---"
    if api_get "/api/state/manifest" >"$TMPDIR_COLD/manifest.json"; then
      cat "$TMPDIR_COLD/manifest.json"
    else
      echo '{"error":"manifest_unavailable"}'
    fi
    echo ""
  fi

  echo "--- kubedojo:next-action ---"
  echo "Invoke /curriculum-orchestrator skill via the Skill tool before any other work."
  echo ""

  exit 0
fi

echo "--- kubedojo:api-down ---" >&2
echo "API down — falling back to STATUS.md" >&2
echo ""

echo "--- kubedojo:fallback ---"
echo "# STATUS.md (first 40 lines)"
head -n 40 STATUS.md
echo ""

echo "--- kubedojo:handoff-path ---"
handoff_path=$(awk '
  /^## Latest handoff/ { in_section=1; next }
  in_section && /^## / { exit }
  in_section && match($0, /docs\/session-state\/[A-Za-z0-9._\/-]+\.(html|md)/) {
    print substr($0, RSTART, RLENGTH)
    exit
  }
' STATUS.md)
if [ -z "$handoff_path" ]; then
  handoff_path="(could not parse Latest handoff path from STATUS.md)"
fi
echo "$handoff_path"
echo ""

echo "--- kubedojo:next-action ---"
echo "Invoke /curriculum-orchestrator skill via the Skill tool before any other work."

exit 0
