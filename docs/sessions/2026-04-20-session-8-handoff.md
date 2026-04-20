---
title: Session 8 handoff — yaml-less allowlist bug, pipeline_v3 prune-and-continue, codex auth expired mid-batch
date: 2026-04-20
---

# TL;DR

Final count: **29 modules lifted from 1.5 → 5.0** (from 13 to 42 at ≥4.0).
Target was 100. Did not hit it.

Three reasons the number landed lower than ambition:

1. **~2.5 hours burned on a silent PyYAML bug** — fetch_citation.py
   disabled the allowlist when yaml was missing, so every URL was
   rejected as off_allowlist and every "committed" run produced an
   empty `## Sources` heading (worse than no run). Three early
   commits (f97eee87, a58514a6, 2c555868) are this.
2. **Verify-abort logic too strict** — pipeline_v3 aborted the whole
   module on any Gate B failure. Claim-dense modules (AI/ML,
   enterprise cloud) hit this often. Patched to prune-and-continue.
3. **Codex auth expired mid-batch** — `403 Forbidden on
   wss://chatgpt.com/backend-api/codex/responses`. Batches 32+ all
   returned research_schema_issues as fast auth-failure responses.
   You need `codex login` to proceed further.

Nothing pushed. 35 commits on main.

# What to do first when you return

```bash
codex login        # required — auth is dead
# then verify:
echo "return {}" | codex exec --full-auto --skip-git-repo-check
```

Once codex is live, decide: retry the ~30 failed modules from the
session 8 batch, or expand the batch to a third tranche. Either way
the pipeline is now working correctly (proven by 29 successful modules
pre-expiry).

# Numbers

| Metric | Start | End | Delta |
|---|---:|---:|---:|
| Modules at ≥4.0 | 13 | 42 | +29 |
| Critical (<2.0) | 690 | 661 | −29 |
| Avg score | 1.60 | 1.74 | +0.14 |

Session 8 commits on main: 35 (32 content + 3 infra fixes). 

Content commits landed before codex expired. After ~iteration 30 of
the v3-patched batch, every event was `research_schema_issues` — that's
the codex 403 signature surfaced through the pipeline.

# What's been fixed and why

## `5bce66b8` — fail-fast on missing PyYAML

Previously:

```python
try:
    import yaml
except ImportError:
    yaml = None
```

…then `_load_allowlist` returned `{"tiers": {}}` when `yaml is None`.
Every URL tested against an empty allowlist gets tier=None, rejected
as off_allowlist, and pruned from the seed. Research stage looked
fine ("31 claims proposed, 22 rejected") but 100% of the reject
reasons were `off_allowlist`. Modules landed with `## Sources` heading
+ zero links. Commit showed a diff but the scorer still applied the
1.5 cap.

Fix: raise at import time on missing PyYAML, and raise if the
allowlist YAML is missing. Pipelines that mutate repo content should
never degrade silently. Also added `scripts/pipeline_v3_batch_commit.py`
— wrapper that runs `pipeline_v3` per module key and commits
clean/residuals_queued runs inline, writing JSONL progress logs.

**How to avoid next session**: invoke pipeline scripts via
`.venv/bin/python scripts/...` never plain `python3 scripts/...`.
The homebrew python3 shim does not have yaml; the .venv does. The
fail-fast now makes the error loud, but the right interpreter is
still the right answer.

## `46706353` — prune verify failures instead of aborting

pipeline_v3 used to abort the whole module if Gate B (verify) flagged
any claim as `UNSUPPORTED` or `CONTRADICTED`:

```python
if v.get("failing_count", 0) > 0:
    return _finalize(run_record, "verify_unsupported_or_contradicted", ...)
```

For claim-dense modules (AI/ML, K8s deep dives, cloud managed
services), this hit ~50% of candidates — one unverifiable claim
killed the run. Session 7's ZTT + `/ai` modules had fewer hard
claims so rarely tripped this path, which is why session 7's plan
looked viable and this bug surfaced only now.

Fix: on verify failure, drop failing claims from the seed and
continue. Only abort if zero citable content remains (no supported
claims AND no further_reading). Gate B rejects the specific URL, not
the claim itself — further_reading stays valid because it's
allowlist+HTTP-checked independently, so inject can still write a
proper Sources section.

Helper: `pipeline_v3.py:_prune_failed_cited_claims`.

## `261b2ec3` — strip bare/duplicate Sources headings

Three pre-fix commits (f97eee87, a58514a6, 2c555868) landed with
empty `## Sources` headings. `_strip_sources_section` is only called
by the diff-lint, not the inject body-write, so running the fixed
pipeline on these modules produced duplicate headings (first empty,
then populated). Cleanup commit stripped the empty ones pre-emptively
before the re-runs.

# Scorer cap explained (important for planning)

`scripts/local_api.py:build_quality_scores`:

```python
base = 0.4/0.9/1.4/1.8/2.1   # by line count
score = base + title(0.6) + quiz(0.8) + exercise(0.8) + diagram(0.7)
if not has_citations:
    score = min(score, 1.5)   # hard cap
```

So a 938-LOC module with quiz + exercise + diagram scores 5.0 but
drops to 1.5 with no `## Sources` section. The 690-module "critical"
count is overwhelmingly this cap, not thin teaching content. Running
v3 on any structurally complete module is a direct shot from 1.5 → 5.0.

597 modules fit the "structurally complete, uncited" pattern. Session
8 cleared 29 of them.

# Session 8 batching run artifacts

Batch files: `.pipeline/v3/batches/session-8-v3-t{1,2}.txt` (60 each)
Logs (JSONL progress): `.pipeline/v3/batches/session-8-t{1,2}-v3.log`

Per-module timing: 8–31 min (median ~12). Bridge is sequential so
parallel tranches share the codex/gemini queue; parallelism bought
maybe 20% overlap, nowhere near 2× speedup.

## Commit pattern per module

`scripts/pipeline_v3_batch_commit.py` commits each clean or
residuals_queued run with:

```
content(citations): apply v3 pipeline to <module_key>

status=<clean|residuals_queued>
```

Status legend:
- `clean` — 0 residuals, all claims resolved, Sources written
- `residuals_queued` — Sources written but Gate C/D flagged items
  for human review in `.pipeline/v3/human-review/<key>.json`
- `verify_unsupported_or_contradicted` — now rare post-patch
- `inject_failed` — Codex inject dispatch or diff-lint failed
- `research_schema_issues` — Codex research returned malformed JSON
  (includes the auth-expiry state — look for duration_s < 200)

## Hit rate observed pre-expiry

~53% commit rate over ~30 processed modules. Breakdown of misses:

- `inject_failed`: ~12 modules. Often transient; retry usually works.
- `research_schema_issues`: ~8 before auth-expiry wave, then all
  subsequent modules. Before the auth wave, this was Codex emitting
  genuinely malformed JSON (retry usually works).

Plus ~10 pure auth-expiry failures after Codex session dropped.

# How to retry the session 8 failures

The failed modules are recoverable — nothing is poisoned. Recipe
after `codex login`:

```bash
# Extract failed module keys from the tranche logs
.venv/bin/python - << 'EOF'
import json
from pathlib import Path
failed = set()
for label in ("session-8-t1-v3", "session-8-t2-v3"):
    p = Path(f".pipeline/v3/batches/{label}.log")
    for line in p.read_text().splitlines():
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("commit", {}).get("committed") is False:
            failed.add(d["key"])
Path(".pipeline/v3/batches/session-8-retry.txt").write_text(
    "\n".join(sorted(failed)) + "\n")
print(f"wrote {len(failed)} keys to session-8-retry.txt")
EOF

# For a failed module, DELETE the stale seed so research re-runs fresh
for key in $(cat .pipeline/v3/batches/session-8-retry.txt); do
    flat=$(echo "$key" | tr '/' '-')
    rm -f "docs/citation-seeds/${flat}.json" ".pipeline/v3/runs/${flat}.json"
done

# Relaunch
nohup .venv/bin/python scripts/pipeline_v3_batch_commit.py \
    --from-file .pipeline/v3/batches/session-8-retry.txt \
    --label session-8-retry \
    > .pipeline/v3/batches/session-8-retry.stdout 2>&1 </dev/null &
```

Expected retry success rate: ~60–70% based on session 7 pattern. So
~20 more modules → total around 50 at ≥4.0.

# Genuinely thin modules still need pipeline_v4

The ~46 modules flagged as "thin, no quiz" or "thin, no citations"
cannot be rescued by citation-only v3. They need real expansion:

- rewrite thin body into narrative teaching (not append-only)
- add quiz/mistakes/exercise if structurally missing
- then v3 citation on the stable content

Issue [#322](https://github.com/kube-dojo/kube-dojo.github.io/issues/322)
carries the v4 design. Feedback memory `feedback_teaching_not_listicles.md`
captures the quality bar: dry fact-dumps fail as teaching even when
the rubric passes, so v4's expand stage must REWRITE thin bodies,
not just bolt on missing sections.

# Cold-start playbook for session 9

1. `codex login`; verify with a short `codex exec`.
2. Read this handoff + [#322](https://github.com/kube-dojo/kube-dojo.github.io/issues/322).
3. `curl -s http://127.0.0.1:8768/api/briefing/session?compact=1`.
4. Confirm clean tree: `git status -s`.
5. Count current state: `curl .../api/quality/scores | jq '[.modules[] | select(.score >= 4)] | length'`.
6. Prefer the section pipeline for adjacent uncited modules:
   `./.venv/bin/python scripts/pipeline_v3_section.py <section-path>`.
   This now runs `section_source_discovery` once, then keeps research
   per-module but constrained to the shared pool.
7. Use `scripts/pipeline_v3.py` only for one-off reruns or cleanup on a
   single module.
8. Retry session 8 failures (recipe above) only when you explicitly want
   the legacy per-module path.
9. After the 597-module citation queue drains, pivot to v4 for the
   genuinely-thin 46.
10. `git push` only after you eyeball the commit diffs.

# References

- `scripts/pipeline_v3.py` — orchestrator with prune-and-continue
- `scripts/pipeline_v3_section.py` — preferred section runner with
  shared source discovery
- `scripts/section_source_discovery.py` — writes
  `docs/citation-pools/<section>.json`
- `scripts/pipeline_v3_batch_commit.py` — per-module commit wrapper
- `scripts/fetch_citation.py` — now fails fast on missing PyYAML
- `.pipeline/v3/batches/` — tranche files + JSONL logs
- `.pipeline/v3/runs/` — per-module run records
- `docs/sessions/2026-04-20-session-7-handoff.md` — prior handoff
- [#322](https://github.com/kube-dojo/kube-dojo.github.io/issues/322) — pipeline_v4 design

# Candid lessons

- Smoke-testing on a single outlier module (agent-memory, 0
  further_reading in session 7 seed) produced a false negative
  about the pipeline and wasted investigation time before I checked
  broader seed data. Sampling should always be N > 1.
- "Silent fallback to empty allowlist" is the kind of defensive
  programming that makes correct-looking failures. Every config
  source that gates pipeline decisions should raise on absence,
  not degrade. Now fixed for yaml+allowlist; might be other silent
  fallbacks in the stack.
- Bridge parallelism buys ~20% not 2×. Session 7's "two batches
  interleave without conflict" is about correctness, not speed.
  Throughput is roughly fixed by the serialized codex/gemini queue.
- Should have verified codex auth status at session start. A 5-second
  `codex exec "return {}"` would have caught expiry before I launched
  long batches. Adding to next session's cold-start playbook.
