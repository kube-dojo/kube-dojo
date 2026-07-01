## DECISION REQUIRED — default UK translation author for the ~160 remaining ai/ai-ml modules

**Context:** s189 REDO of the s188 author A/B (the s188 "deepseek wins" was provisional — run without the `sources` MCP and without Sonnet-5). Now #2131 is shipped (deepseek can author corpus-grounded), so the redo compared **deepseek+MCP vs Sonnet-5-high** on `ai-for-kubernetes-platform-work/module-1.3` (~8.1K words) through identical guards + gates + objective metrics + a comparative agy semantic review + opus/glossary adjudication. Full scoreboard: `docs/session-state/2026-07-01-session-189-uk-author-ab-redo-2131.html`.

**Result — NUANCED, no clean winner:**

| Axis | deepseek+MCP | Sonnet-5-high |
|---|---|---|
| Structural parity / ratio | perfect / 0.94 | perfect / 0.936 |
| Code-switches (guard) | **1** | **6** (keeps English K8s nouns in prose) |
| `Pod→Под` glossary (prose) | ✅ follows | ❌ keeps `Pod` |
| K8s term fidelity (taint/pending/SLO-burn) | ❌ `зараження`/`завислі`/`вигорання` (wrong) | ✅ correct |
| Shared idiom-calques | yes (both) | yes (both) |
| Cost | cheap | subscription quota, 645s |
| Adjudicated gate-invisible defects | ~11 (several convention-fixable) | ~7 (incl. glossary violations) |

**Key finding:** MCP-grounding did **not** materially help deepseek — it barely called the tools even when the brief instructed it to; its semantic/false-friend weakness persists. Sonnet-5 has better technical-term fidelity but code-switches more, violates the `Pod→Под` prose rule, and costs subscription quota.

**Options:**
- **A (recommended) — keep deepseek** as default, but bake the known false-friends into the fidelity brief (taints→keep `taint`; pending→`у стані Pending`/`в стані очікування`; SLO burn→`вичерпання бюджету`) + keep opus/MCP adjudication as the quality gate. Cheapest; the redo showed no quality gap large enough to justify switching + Sonnet-5's cost.
- **B — switch to Sonnet-5** for the ai/ai-ml volume (better raw technical fidelity), accept higher cost + a code-switch/`Pod→Под` cleanup pass in the pipeline.
- **C — hybrid**: deepseek default for most modules; Sonnet-5 for the most technical/K8s-primitive-heavy modules where its term fidelity pays off.

**Orchestrator recommendation:** **A** — the adjudicated defect gap is small and mostly brief-fixable; deepseek is far cheaper and glossary-consistent; MCP+opus adjudication already catches the semantic misses at review time. Revisit if a brief-hardened deepseek still misses core terms.

**Awaiting:** user choice (A / B / C or override). On decision, move this file to `docs/decisions/2026-07-01-uk-default-translation-author.md` with the chosen option, then resume ai volume (`ai-for-kubernetes-platform-work` 1.1–1.4 + index; 1.3 already A/B-drafted on branch `ab13-<winner>`, needs the shared idiom-calque fix-pass before shipping).
