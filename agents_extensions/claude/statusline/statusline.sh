#!/usr/bin/env bash
# Claude Code statusline — kubedojo project (mirrors learn-ukrainian).
#
# Reads Claude Code status JSON from stdin and renders:
#   [MODEL] cwd-basename [wt:worktree-name] (branch*) [ctx: N%]
#   [effort: level] [think] [5h: N%] [7d: N%]
#
# Segments:
#   [MODEL]        .model.display_name, omitted if missing
#   cwd-basename   basename(.workspace.current_dir), pwd fallback
#   [wt:...]       basename(.workspace.git_worktree), omitted if not in a worktree
#   (branch*)      git branch + `*` if dirty
#   [ctx: UK/BK (N%)] context window — color-coded green<50, yellow 50-79,
#                    red 80+. U=used Ktokens, B=budget Ktokens, N=percent.
#                    Used tokens read with three-tier degradation:
#                      1) PRIMARY: .transcript_path → tail JSONL → sum
#                         .message.usage.{input_tokens, cache_read_input_tokens,
#                         cache_creation_input_tokens} from latest assistant
#                         turn. Most reliable — .transcript_path is in the
#                         official statusline schema.
#                      2) FALLBACK: .context_window.used_tokens (or
#                         .input_tokens / .tokens.used). Works on clients
#                         that populate the context_window block directly.
#                      3) BARE: .context_window.used_percentage as the last
#                         resort if no token count is available.
#                    Budget read from .context_window.budget (or .max_tokens
#                    / .total_tokens), else the CLAUDE_CODE_AUTO_COMPACT_WINDOW
#                    env var, else 1000000. Omitted entirely until the first
#                    API call populates usage.
#   [effort: ...]  .effort.level — low/medium default, high/xhigh bold,
#                    max red. Omitted for pre-2.1.119 clients.
#   [think]        .thinking.enabled — emitted only when true. Omitted for
#                    pre-2.1.119 clients.
#   [5h: N%]       .rate_limits.five_hour.used_percentage — subscription
#                    budget. Only shown when elevated (60%+ yellow, 80%+ red).
#                    Stays silent while healthy — no noise in normal use.
#   [7d: N%]       .rate_limits.seven_day.used_percentage — weekly budget.
#                    Same threshold scheme as 5h.
#
# NOTE: .cost.total_cost_usd is deliberately NOT rendered. The field is a
# client-side API-equivalent estimate that is meaningless for Claude Max
# subscription users (which is the primary intended user of this project).
# The actionable subscription metrics are the 5h and 7d rate-limit windows.
#
# Schema reference: https://code.claude.com/docs/en/statusline.md
#
# Graceful degradation:
#   - If `jq` is not installed, script exits silently (empty status line).
#   - Any missing / null JSON field is dropped from output silently.
#   - Claude Code <2.1.119 does not provide effort/thinking fields; those
#     segments are omitted silently.
#   - If any git op fails, branch segment is omitted.
#
# Design notes:
#   - ANSI escapes use printf '%b' at render time so terminals that don't
#     support color still render the text (codes just show as literals in
#     the rare case the terminal is truly ancient — acceptable fallback).
#   - Script is intentionally cheap: no network, no external state, only
#     `git` + `jq` + `printf`. Statusline fires on every event.
#
# Debug: uncomment the tee line below to capture incoming JSON at
#        /tmp/.statusline-input.json for schema inspection.

set -u

command -v jq >/dev/null 2>&1 || exit 0

input=$(</dev/stdin)
# printf '%s' "$input" > /tmp/.statusline-input.json  # debug

json_get() {
  printf '%s' "$input" | jq -r "$1 // empty" 2>/dev/null
}

# ── Segments ────────────────────────────────────────────────────

model=$(json_get '.model.display_name')

cwd=$(json_get '.workspace.current_dir')
[ -z "$cwd" ] && cwd=$(json_get '.cwd')
[ -z "$cwd" ] && cwd=$(pwd)
cwd_name=$(basename "$cwd")

worktree=$(json_get '.workspace.git_worktree')
wt_seg=""
[ -n "$worktree" ] && wt_seg="[wt:$(basename "$worktree")]"

# Branch + dirty marker
branch_seg=""
if git -C "$cwd" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  branch=$(git -C "$cwd" symbolic-ref --quiet --short HEAD 2>/dev/null \
           || git -C "$cwd" rev-parse --short HEAD 2>/dev/null \
           || true)
  dirty=""
  [ -n "$(git -C "$cwd" status --porcelain 2>/dev/null)" ] && dirty="*"
  [ -n "$branch" ] && branch_seg="($branch$dirty)"
fi

# Context window — UK/BK (N%) format with three-tier degradation.
#
# Tier 1 (primary): .transcript_path → tail the JSONL → sum the latest
#   assistant turn's .message.usage.{input_tokens, cache_read_input_tokens,
#   cache_creation_input_tokens}. This is the documented, stable path —
#   .transcript_path is in the official statusline schema and the usage
#   shape is the Anthropic API contract.
# Tier 2 (fallback): direct .context_window.* JSON reads, in case a
#   future client version populates that block.
# Tier 3 (bare): .context_window.used_percentage with no K/K, if neither
#   tier produced a token count.
ctx_seg=""
ctx_pct=$(json_get '.context_window.used_percentage')
ctx_used=""

# Tier 1: transcript-JSONL parsing.
transcript_path=$(json_get '.transcript_path')
if [ -n "$transcript_path" ] && [ -f "$transcript_path" ]; then
  usage_json=$(tail -200 "$transcript_path" 2>/dev/null \
    | jq -s '[.[] | select(.type == "assistant" and .message.usage != null)] | last | .message.usage // empty' 2>/dev/null)
  if [ -n "$usage_json" ] && [ "$usage_json" != "null" ] && [ "$usage_json" != "empty" ]; then
    inp=$(printf '%s' "$usage_json" | jq -r '.input_tokens // 0' 2>/dev/null)
    cr=$(printf '%s'  "$usage_json" | jq -r '.cache_read_input_tokens // 0' 2>/dev/null)
    cc=$(printf '%s'  "$usage_json" | jq -r '.cache_creation_input_tokens // 0' 2>/dev/null)
    ctx_used=$(( ${inp:-0} + ${cr:-0} + ${cc:-0} ))
    [ "$ctx_used" = "0" ] && ctx_used=""    # no usage yet → treat as missing
  fi
fi

# Tier 2: direct JSON field reads.
[ -z "$ctx_used" ] && ctx_used=$(json_get '.context_window.used_tokens')
[ -z "$ctx_used" ] && ctx_used=$(json_get '.context_window.input_tokens')
[ -z "$ctx_used" ] && ctx_used=$(json_get '.context_window.tokens.used')

# Budget — same precedence as before.
ctx_budget=$(json_get '.context_window.budget')
[ -z "$ctx_budget" ] && ctx_budget=$(json_get '.context_window.max_tokens')
[ -z "$ctx_budget" ] && ctx_budget=$(json_get '.context_window.total_tokens')
[ -z "$ctx_budget" ] && ctx_budget="${CLAUDE_CODE_AUTO_COMPACT_WINDOW:-1000000}"

# If JSON didn't give us a percent but we have used+budget numerics, compute it.
if [ -z "$ctx_pct" ] && [ -n "$ctx_used" ] && [ -n "$ctx_budget" ] \
   && printf '%d' "$ctx_used"   >/dev/null 2>&1 \
   && printf '%d' "$ctx_budget" >/dev/null 2>&1 \
   && [ "$ctx_budget" -gt 0 ]; then
  ctx_pct=$(( ctx_used * 100 / ctx_budget ))
fi

if [ -n "$ctx_pct" ]; then
  ctx_int=$(printf '%.0f' "$ctx_pct" 2>/dev/null) || ctx_int=""
  if [ -n "$ctx_int" ]; then
    if   [ "$ctx_int" -ge 80 ]; then ctx_color="\033[31m"   # red
    elif [ "$ctx_int" -ge 50 ]; then ctx_color="\033[33m"   # yellow
    else                             ctx_color="\033[32m"   # green
    fi
    # Render UK/BK (N%) when we have numeric token counts; else bare N%.
    if [ -n "$ctx_used" ] && printf '%d' "$ctx_used" >/dev/null 2>&1 \
       && [ -n "$ctx_budget" ] && printf '%d' "$ctx_budget" >/dev/null 2>&1; then
      # Round to nearest thousand: (x + 500) / 1000.
      ctx_used_k=$(( (ctx_used + 500) / 1000 ))
      ctx_budget_k=$(( (ctx_budget + 500) / 1000 ))
      ctx_seg="${ctx_color}[ctx: ${ctx_used_k}K/${ctx_budget_k}K (${ctx_int}%)]\033[0m"
    else
      ctx_seg="${ctx_color}[ctx: ${ctx_int}%]\033[0m"
    fi
  fi
fi

# Effort level
effort_seg=""
effort_level=$(json_get '.effort.level')
if [ -n "$effort_level" ]; then
  case "$effort_level" in
    high|xhigh) effort_seg="\033[1m[effort: ${effort_level}]\033[0m" ;;
    max)        effort_seg="\033[31m[effort: ${effort_level}]\033[0m" ;;
    *)          effort_seg="[effort: ${effort_level}]" ;;
  esac
fi

# Thinking mode
thinking_seg=""
thinking_enabled=$(json_get '.thinking.enabled')
[ "$thinking_enabled" = "true" ] && thinking_seg="[think]"

# Rate-limit segment helper — only surface when elevated (60%+).
# Accepts a label (e.g. "5h", "7d") and a jq path, returns coloured
# segment on stdout or empty string.
rate_limit_seg() {
  local label=$1 path=$2 pct int
  pct=$(json_get "$path")
  [ -z "$pct" ] && return 0
  int=$(printf '%.0f' "$pct" 2>/dev/null) || return 0
  if   [ "$int" -ge 80 ]; then printf '\033[31m[%s: %d%%]\033[0m' "$label" "$int"
  elif [ "$int" -ge 60 ]; then printf '\033[33m[%s: %d%%]\033[0m' "$label" "$int"
  fi
}

rl5h_seg=$(rate_limit_seg "5h" ".rate_limits.five_hour.used_percentage")
rl7d_seg=$(rate_limit_seg "7d" ".rate_limits.seven_day.used_percentage")

# ── Assemble ────────────────────────────────────────────────────

parts=()
[ -n "$model" ]      && parts+=("[$model]")
parts+=("$cwd_name")
[ -n "$wt_seg" ]     && parts+=("$wt_seg")
[ -n "$branch_seg" ] && parts+=("$branch_seg")
[ -n "$ctx_seg" ]    && parts+=("$ctx_seg")
[ -n "$effort_seg" ] && parts+=("$effort_seg")
[ -n "$thinking_seg" ] && parts+=("$thinking_seg")
[ -n "$rl5h_seg" ]   && parts+=("$rl5h_seg")
[ -n "$rl7d_seg" ]   && parts+=("$rl7d_seg")

# %b interprets the ANSI escape codes embedded in coloured segments.
printf '%b\n' "${parts[*]}"
