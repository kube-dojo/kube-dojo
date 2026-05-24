---
date: 2026-05-23
decided: 2026-05-24
title: Primary cross-family reviewer for T0 content PRs — composer-2.5 vs deepseek-v4-pro
author: claude-opus-4-7 (orchestrator)
status: accepted
chosen_option: C
decider: user (krisztian)
---

> **DECIDED 2026-05-24 (session 51 start)**: User confirmed **Option C — task-class split**. Composer-2.5 = primary T0 content reviewer; codex = secondary; deepseek demoted to tertiary fallback. Routing change table below is now in effect. Also: claude/agy (agy routed to claude-sonnet) is OUT of cross-family review rotation during the 2026-05-23/24 throttle window — codex is the canonical fallback when composer-2.5 unavailable.

## DECISION REQUIRED — Primary cross-family reviewer for T0 content PRs

**Agents:** claude (orchestrator), codex (intended), cursor/composer-2.5 (intended), deepseek (intended). ab discuss attempted but blocked by a cursor adapter bug — see "Discussion process" below.

**Options:**
- **A** — Promote composer-2.5 to primary cross-family reviewer for T0 content PRs immediately. Deepseek becomes secondary.
- **B** — Keep deepseek as primary; add composer-2.5 as parallel R2 on all T0 PRs while promotion lasts. Decide later.
- **C** — Task-class split: composer-2.5 for content/lab-runnability reviews (its strength tonight); deepseek/codex for code/dispatcher/CI changes.
- **D** — Defer; n=1 + same-day deepseek glitch is insufficient. Run 3-5 more blind A/B trials before any routing change.

**Votes captured:**
- claude (orchestrator) → **Option C with strong lean on A** {empirical signal is unusually sharp; deepseek had two distinct failure modes today, not one; composer-2.5 actually ran bash locally to verify; but n=1 deserves caution and task-class split preserves a fallback path}
- codex → **not captured** (discuss ended before codex round)
- cursor (composer-2.5) → **not captured** (adapter bug — see below)
- deepseek → **partial round-1 response** {acknowledged "the failures are real" but full response truncated in discuss log}

**Disagreement surface:** the cursor adapter bug prevented true multi-agent deliberation. The substantive disagreement remains: does n=1 + same-day deepseek glitches justify a routing change, or is it noise.

## Orchestrator recommendation: **Option C — task-class split**

**Rationale (3 lines):**
- Tonight's #1475 R2 A/B was a strong signal in one direction (composer-2.5 caught 3 real bash bugs; deepseek APPROVE'd past them and hallucinated a karpenter URL as evidence). Same-day deepseek had a second failure mode on #1476 R1 (raw tool-call XML escape). That's a pattern, not a glitch.
- Composer-2.5 is on a Cursor promotion (free or discounted) — using it heavily NOW is cheap. Pay-per-call deepseek can be the fallback when composer-2.5 unavailable, with the rubber-stamp risk explicitly noted in briefs.
- Task-class split keeps deepseek's wins (content authoring per PR #1465, where it was sharp) and preserves the codex weekly cap for code/dispatcher reviews where it's been canonical.

**Concrete routing change (if Option C is approved):**

| Task class | Primary | Secondary | Notes |
|---|---|---|---|
| T0 content review (R1 + R2) | composer-2.5 | codex | deepseek demoted to tertiary fallback; bash-runnability brief required |
| Content authoring | codex / composer-2.5 / deepseek (rotation) | — | All proven |
| Code/dispatcher/CI review | codex | composer-2.5 | unchanged |
| Lab-runnability + ground-truth | composer-2.5 | codex | bash-runnability specialty |
| Translation review (UK) | gemini-cli (when quota back) | codex | unchanged |

## Empirical evidence

### PR #1475 R2 A/B (parallel, blind)
- **deepseek-v4-pro** → APPROVE (rubber-stamp). Spot-checks included a hallucinated `karpenter.sh/migrating-from-cas` URL not in the Sources list + wrong file path (`platform/private-cloud/` vs actual `on-premises/multi-cluster/`).
- **composer-2.5** → NEEDS_CHANGES with 4 findings:
  1. **HIGH** — `<https://...>` inside `bash` fences breaks Exercises 2 & 3 (shell input-redirection syntax). Composer-2.5 ran `bash` locally to confirm.
  2. **MEDIUM** — Prose says K8s 1.35; apt repo installs v1.30. Mismatch introduced by R1 fix-pass.
  3. **MEDIUM** — Exercise 3 kubeadm bootstrap missing Ubuntu 24.04 prereqs (swapoff, br_netfilter, containerd SystemdCgroup).
  4. **NIT** — `## Sources` after `## Next Module` (style only).
- Verifying: I (orchestrator) confirmed findings 1 + 3 by spot-check; karpenter URL is genuinely not in the file.
- Outcome: composer-2.5 fix-pass landed (`d995ef47`); codex R3 independent verification in flight.

### PR #1476 R1 (deepseek attempt)
- **deepseek-v4-pro** → produced raw `<｜｜DSML｜｜invoke>` tool-call escape syntax instead of an actual review. `OK: True` per dispatcher but `resp_chars: 1908` of useless plan-narrative + tool-call XML. Different failure mode than #1475.
- Re-routed to codex; result pending at time of writing.

### PR #1478 R1 (alternative reviewers)
- **agy** → first attempt errored on `cwd is mandatory for mode='danger'`. Re-fired with `--mode read-only` and that rejected too: `--agent agy always runs in danger mode`. Agy is unusable for review headless without `--worktree`, and worktree assignment for a read-only review is a misfit. 4 agy failures in 24h (2 yesterday, 2 today).
- **hermes** → routed to claude-sonnet-4-6 (default); silently failed in 4 s (`exited 0 with no stdout`). Likely hit Anthropic throttle.
- **codex** → fired with `--mode danger --worktree`; pending.

### Composer-2.5 author track record (tonight)
- **4/4 T0 author successes** on On-Premises Multi-Cluster track: PR #1475 (5.1), #1476 (5.3), #1477 (5.2), #1478 (5.4). All verifier passed=true tier=T0 body_words=5000. Build exit 0 each.
- Average dispatch time: ~17-18 minutes (1057s, 1112s observed).

## Discussion process (why ab discuss didn't complete)

Created channel `reviewer-promotion-2026-05-23`. Fired `scripts/ab discuss --with codex,cursor,deepseek --max-rounds 2`.

Round 1 outcome:
- **cursor (composer-2.5)**: failed with `error: unknown option '--- monitor: project state (volatile) --- ...`. The `monitor_state_snapshot` JSON injected into the discuss prompt was passed to cursor-agent's CLI, which parsed the leading `---` as a flag separator and bailed.
- **deepseek**: round-1 response landed in discuss log but appears truncated ("The failures are real..." cut off).
- **codex**: did not get to respond in this round.

This is an adapter bug — `scripts/ai_agent_bridge/_channels_cli.py` or `_cursor.py` should sanitize or quote the monitor state before passing it to cursor-agent. Memory `feedback_cursor_discuss_adapter_monitor_state_bug.md` recorded.

## What NOT to decide here

- Author-side composer-2.5 viability: already proven (4/4 tonight). Recommend writing `feedback_composer_2_5_viable_for_t0_content.md` once PR #1475 fully merges.
- The cursor discuss adapter fix: separate issue; track in a GH issue.
- Deepseek's authoring viability: PR #1465 is the proof point for that. This decision concerns REVIEWER role only.

## Awaiting user

Drop a ✓ next to A / B / C / D when you wake up. Orchestrator default (without user override) is to operate under **Option C** semantics until you decide.
