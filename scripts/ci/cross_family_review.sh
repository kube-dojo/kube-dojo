#!/usr/bin/env bash
# CI cross-family review — call a model's chat-completions endpoint with the
# PR diff and post the verdict as a tagged PR comment. Comment-only; never
# blocks merge. See .github/workflows/cross-family-code-review.yml for the
# job-level wiring.
#
# Required env (set by the job):
#   PR_NUMBER         — pull request number
#   BASE_REF          — base branch ref (e.g. main)
#   MODEL_TAG         — short label printed at the top of the comment
#                       (e.g. "deepseek-v4-pro" or "gemini-3.5-flash@high")
#   API_ENDPOINT      — full URL to a /chat/completions endpoint
#   API_KEY           — bearer token for that endpoint
#   API_MODEL         — model ID the endpoint expects (e.g. "deepseek-chat",
#                       "gemini-3.5-flash")
#   REASONING_EFFORT  — optional. If set, included as a top-level
#                       "reasoning_effort" field (e.g. "high"). Quietly ignored
#                       by endpoints that don't support it.
#   GH_TOKEN          — auth for `gh` CLI (workflow's GITHUB_TOKEN is fine)
#
# Cost discipline:
#   - Truncate diffs to MAX_DIFF_CHARS (default 60_000 chars ≈ 15K tokens).
#     A truncation notice is appended so the model knows.
#   - One API call per job. No retries on success. One retry on transient 5xx.
#   - Workflow timeout-minutes is the hard ceiling; this script has no extra
#     timeout of its own beyond curl's --max-time.

set -euo pipefail

: "${PR_NUMBER:?PR_NUMBER required}"
: "${BASE_REF:?BASE_REF required}"
: "${MODEL_TAG:?MODEL_TAG required}"
: "${API_ENDPOINT:?API_ENDPOINT required}"
: "${API_KEY:?API_KEY required}"
: "${API_MODEL:?API_MODEL required}"
: "${GH_TOKEN:?GH_TOKEN required}"

MAX_DIFF_CHARS=${MAX_DIFF_CHARS:-60000}
REASONING_EFFORT=${REASONING_EFFORT:-}

# ── 1. Build the diff payload ───────────────────────────────────────────────
# Use the merge-base so we review only what this PR adds, not unrelated
# history. fetch-depth=0 in the job makes both refs resolvable.
git fetch --no-tags --depth=200 origin "$BASE_REF" >/dev/null 2>&1 || true
DIFF=$(git diff "origin/${BASE_REF}...HEAD" 2>/dev/null || true)

if [ -z "$DIFF" ]; then
  echo "No diff against origin/${BASE_REF}; nothing to review."
  exit 0
fi

DIFF_LEN=${#DIFF}
TRUNC_NOTE=""
if [ "$DIFF_LEN" -gt "$MAX_DIFF_CHARS" ]; then
  DIFF=${DIFF:0:$MAX_DIFF_CHARS}
  TRUNC_NOTE=$'\n\n[diff truncated to '"${MAX_DIFF_CHARS}"$' chars of '"${DIFF_LEN}"$' total; reviewer is reviewing the head of the diff only]'
fi

# ── 2. Build the prompt ─────────────────────────────────────────────────────
SYSTEM_PROMPT=$(cat <<'EOF'
You are a CI safety-net cross-family reviewer for the KubeDojo curriculum repo
(https://github.com/kube-dojo/kube-dojo.github.io). Primary review for this PR
already happens locally via composer-2.5 — your job is the *secondary* sanity
check, not the gate.

Review the diff and output EXACTLY this structure (Markdown):

VERDICT: APPROVE | APPROVE_WITH_NITS | NEEDS_CHANGES

Scores (1-5 each, one per line):
- Technical accuracy: N/5 — <one phrase>
- Lab/bash runnability: N/5 — <one phrase>
- Citation discipline (URLs/papers/repos cited and reachable): N/5 — <one phrase>
- Pedagogical structure (if content): N/5 — <one phrase, or "N/A — not content">
- Security / CI safety (if .github or scripts): N/5 — <one phrase, or "N/A">

Findings:
- One bullet per concrete issue. Format: `path:line — problem → fix`. Skip if
  no concrete issues; do not invent ones to fill space.

Out of scope (skip silently): style preferences, doc-only nits in unrelated
files, hypothetical future failures. Focus on what would break if this merges
today.

This review is COMMENT-ONLY. You do not have merge authority. Do not pretend
you are merging.
EOF
)

USER_PROMPT=$(printf 'PR #%s diff against %s:\n\n```diff\n%s\n```%s' \
  "$PR_NUMBER" "$BASE_REF" "$DIFF" "$TRUNC_NOTE")

# ── 3. Build the JSON body ──────────────────────────────────────────────────
# OpenAI-compatible /chat/completions shape works for DeepSeek directly and for
# the Gemini OpenAI-compatibility endpoint. The optional reasoning_effort
# field is passed through verbatim.
REQ_BODY=$(jq -n \
  --arg model "$API_MODEL" \
  --arg sys "$SYSTEM_PROMPT" \
  --arg usr "$USER_PROMPT" \
  --arg effort "$REASONING_EFFORT" \
  '{
    model: $model,
    messages: [
      { role: "system", content: $sys },
      { role: "user",   content: $usr }
    ],
    temperature: 0.2,
    stream: false
  } + ( if $effort == "" then {} else { reasoning_effort: $effort } end )')

# ── 4. Call the API (one retry on transient 5xx) ────────────────────────────
call_api() {
  curl -sS --max-time 240 \
    -w '\n__HTTP_STATUS__%{http_code}' \
    -H "Authorization: Bearer ${API_KEY}" \
    -H 'Content-Type: application/json' \
    -X POST "$API_ENDPOINT" \
    --data-binary "$REQ_BODY"
}

RAW=$(call_api || true)
STATUS=${RAW##*__HTTP_STATUS__}
BODY=${RAW%__HTTP_STATUS__*}

if [ "$STATUS" -ge 500 ] && [ "$STATUS" -lt 600 ]; then
  echo "Transient ${STATUS} from $API_ENDPOINT; retrying once after 5s..." >&2
  sleep 5
  RAW=$(call_api || true)
  STATUS=${RAW##*__HTTP_STATUS__}
  BODY=${RAW%__HTTP_STATUS__*}
fi

if [ "$STATUS" -ge 400 ]; then
  echo "API ${STATUS} from $API_ENDPOINT. Body excerpt:" >&2
  printf '%s\n' "$BODY" | head -c 800 >&2
  # Comment-only — post a brief failure note instead of exiting non-zero,
  # so the workflow stays a soft signal and doesn't block merge.
  FAILURE_BODY=$(printf '## CI cross-family review — %s\n\n_HTTP %s from `%s`. Review skipped; see job logs. This does not block merge._\n' \
    "$MODEL_TAG" "$STATUS" "$API_ENDPOINT")
  gh pr comment "$PR_NUMBER" --body "$FAILURE_BODY" || true
  exit 0
fi

# ── 5. Extract the model's reply ────────────────────────────────────────────
REPLY=$(printf '%s' "$BODY" | jq -r '.choices[0].message.content // .choices[0].message // empty' 2>/dev/null || true)
if [ -z "$REPLY" ]; then
  echo "Could not parse choices[0].message.content from response. Body excerpt:" >&2
  printf '%s\n' "$BODY" | head -c 800 >&2
  FAILURE_BODY=$(printf '## CI cross-family review — %s\n\n_Empty / unparseable response from `%s`. Review skipped; see job logs. This does not block merge._\n' \
    "$MODEL_TAG" "$API_ENDPOINT")
  gh pr comment "$PR_NUMBER" --body "$FAILURE_BODY" || true
  exit 0
fi

# ── 6. Post the comment ─────────────────────────────────────────────────────
COMMENT_BODY=$(printf '## CI cross-family review — %s\n\n_Comment-only safety-net per `docs/decisions/2026-05-24-reviewer-routing-composer-2-5.md`. Primary review remains composer-2.5 local. Treat this as a secondary signal._\n\n---\n\n%s\n' \
  "$MODEL_TAG" "$REPLY")

gh pr comment "$PR_NUMBER" --body "$COMMENT_BODY"
echo "Posted review comment for ${MODEL_TAG} on PR #${PR_NUMBER}."
