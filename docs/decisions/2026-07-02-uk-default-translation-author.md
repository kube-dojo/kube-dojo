# DECISION — default UK translation author = Sonnet-5 + `sources` MCP (RESOLVED 2026-07-02)

**Decided by:** user, 2026-07-02 ("i say we use sonnet … i prefer quality").

## Question
Which model authors the ~160 remaining `ai`/`ai-ml` UK translations? s188 said deepseek; s189-round-1 (deepseek vs Sonnet-5-no-MCP) said "keep deepseek." Both were **wrong** — they tested an incomplete field. Per user directive, redone with **every model corpus-grounded via the `sources` MCP**.

## Full A/B (all models WITH MCP) — module-1.3 (low jargon) + Sonnet-5 confirm on module-2.4 (dense)
See `docs/session-state/2026-07-02-session-189b-*.html` and `scratchpad/ab_full_scoreboard.md`.

| model | K8s terms | jargon (dense 2.4) | code-switch | uses MCP? | write | cost |
|---|---|---|---|---|---|---|
| **Sonnet-5+MCP** ✅ | ✓✓✓ | translates (139 stray) | ~0–5 | **yes (12 calls + glossary)** | reliable | subscription |
| codex+MCP | ✓✓✓ (on light) | **under-translates (~976 on 2.4)** | 8 | native (unconfirmed) | reliable | subscription |
| deepseek+MCP | ✗✗✗ false-friends | translates (~142) | 1 | **no (~2 calls)** | reliable | cheap API |
| agy+MCP | ✓✓ | — | 1 | native | **flaky (sandbox-write)** | subscription |
| grok+MCP | ~translit | — | 0 | dispatch-flaky | ok | subscription |
| cursor+MCP | ✓ via NOT translating | — | 8 | native | ok (slow) | subscription |

## Why Sonnet-5+MCP
Only model that: (1) **fully translates** on BOTH light and jargon-dense modules (low stray-English like deepseek, unlike codex which leaves dense jargon English); (2) gets terms **semantically right** (unlike deepseek's `зараження`/`завислі`/`вигорання`); (3) near-zero code-switching; (4) **actually exploits the corpus MCP** — deepseek ignores it, so grounding it is pointless. Cost is subscription (same profile as codex; deepseek is the only cheap-API lane, declined for quality per user).

**Corrected reasoning (user caught this):** codex and Sonnet BOTH run on subscriptions the user already pays — neither is "cheaper" than the other; only deepseek is per-token. The earlier "codex is cheaper" claim was wrong.

## Execution
- Author = Sonnet-5 + `sources` MCP at **high effort**. NOTE: the claude dispatch adapter + Agent-tool have **no effort flag** today → high effort is triggered by a **prompt-level extended-thinking directive** in the fidelity brief (immediate); optionally add real effort plumbing to the claude adapter later (follow-up).
- The A/B ran Sonnet via a Claude **subagent** (because `dispatch_smart draft --agent claude --mcp` is gated off — allowedTools would be crippled). Production lane options: (a) formalize the subagent lane, or (b) wire a proper `claude draft --mcp sources` write path in dispatch_smart. **Follow-up issue to file.**
- **Bake idiom guidance into the brief** (translate MEANING, not literal): scavenger hunt→`хаотичний пошук`; bear the pager→`чергувати`; bridge call→`конференц-дзвінок`; command "against" server→`до/на`. These calques appeared across ALL models.
- **Keep-English K8s terms** per convention: `taint`, `Pod`→`Под` in prose (glossary).

## Then
Resume `ai` volume with Sonnet+MCP-high: `ai-for-kubernetes-platform-work` (5; 1.3 already Sonnet-drafted — needs idiom fix-pass + re-run at high effort) → `ai-native-work` (5) → `open-models-local-inference` (8) → `ai-ml-engineering` (142).
