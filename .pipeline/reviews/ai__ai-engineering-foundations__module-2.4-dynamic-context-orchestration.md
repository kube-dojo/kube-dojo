## 2026-06-18T00:20:05Z — `REVIEW` — `APPROVE`
**Reviewer:** codex gpt-5.5 (cross-family R1) + opus-inline ground-check (traced lab code) → cursor fix → opus re-review. **PR #2022 (#2020).** Author: #1530. Verdict path: NEEDS_CHANGES → fixed → **APPROVE.**

P1 (fixed, commit 1729412f7):
1. Token ledger double-counted injected snippets (`tokens_used += inject_snippet.tokens` then a loop re-added every snippet) → removed the per-injection add; snippets counted once. tokens_used resets per turn → totals now correct.
2. "Phase A — baseline without stale eviction" still called `evict_stale_snippets()` unconditionally → added `evict: bool=True`; Phase A passes `evict=False` so the A/B comparison is valid.

Web-verified correct-and-current (defended): Anthropic 5-min default cache TTL + 1-hour option + tools/system/messages order; OpenAI exact-prefix caching, up-to-80% latency / 90% input-cost, cached_tokens. MCP 2025-11-25. P2 (deferred): cache TTL/cost facts woven through prose vs dated snapshot.
