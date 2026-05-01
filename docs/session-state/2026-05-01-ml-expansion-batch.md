# Session handoff — 2026-05-01 — ML curriculum expansion (issue #677), 19 of 22 modules merged in one session

> Picks up immediately from `2026-04-30-night-7-followups.md` (which surfaced the classical-ml curriculum gap and locked the structural plan). This session executed Phase 0 + 19 of the 22-module expansion under issue #677. ML 2.7 is currently in flight; RL 2.1 not yet started; one pre-existing DL 1.7 cleanup PR remains.

## What shipped this session — full list

| PR | Module | Author | Lines | Iteration rounds |
|---|---|---|---|---|
| #680 | **Phase 0** — directory restructure (`classical-ml/` → `machine-learning/`), `reinforcement-learning/` peer, redirects, sidebar update, slug renumbering, `scripts/quality/check_citations.py` + `check_code_blocks.py`, **module 1.1 sklearn API/Pipelines rewrite** | Headless Claude (worktree-isolated) | 712 (1.1) | 3 review rounds (Codex caught 6 majors → fixed → 2 still-needs → fixed → approved) |
| #686 | **ML 1.3** Model Evaluation, Validation, Leakage & Calibration | Codex (gpt-5.5) | 925 | 1 (agent rewrote `import_module()` workaround Codex used → standard imports) |
| #691 | **ML 1.4** Feature Engineering & Preprocessing | Claude direct (Codex dispatch failed twice → documented fallback) | 802 | 3 review rounds (Codex caught 4 issues + 2 in re-review: ROC-AUC mislabel via `Pipeline.score()`, TargetEncoder log-odds error, hashing-bucket-as-ordinal, weak D4 opening) |
| #692 | **ML 1.2** Linear & Logistic Regression with Regularization | Codex | 1414 | 0 |
| #693 | **ML 1.5** Decision Trees & Random Forests | Codex + Claude post-process (slug fixes + reflow script) | 1168 | 1 inline (recurring slug-hallucination pattern) |
| #694 | **ML 1.7** Naive Bayes, k-NN & SVMs | Codex | 1388 | 0 (pinned-slug pattern eliminated hallucinations; verified via grep) |
| #695 | **ML 1.8** Unsupervised Learning: Clustering | Codex | 1158 | 0 |
| #696 | **ML 1.9** Anomaly Detection & Novelty Detection | Codex | 1184 | 0 (display-label minor: "Time-Series" vs "Time Series" hyphen difference accepted) |
| #697 | **ML 1.10** Dimensionality Reduction | Claude direct (fallback) | 1209 | 1 (Codex caught Step 8 of exercise teaching leakage; rewrote as deliberate-leakage demo + added 2 inline prompts) |
| #698 | **ML 1.11** Hyperparameter Optimization | Codex | 1362 | 0 (agent caught misattributed arxiv:1212.5745 — actually a dark-matter paper, not Bergstra & Bengio; used JMLR URL instead) |
| #699 | **RL 1.1** RL Practitioner Foundations | Codex | 856 | 0 |
| #700 | **DL 1.8** Self-Supervised Learning | Codex via direct orchestrator dispatch (agent timed out waiting) | 891 | 1 inline (orchestrator added second `Pause and decide` to clear ≥2 threshold) |
| #701 | **DL 1.9** Graph Neural Networks | Claude direct (fallback) | 935 | 2 review rounds (Codex caught major teaching bug — random transductive splits framed as leakage when they're standard practice; rewrote Section 11 + Section 10 mention + Common Mistakes row + learning outcome) |
| #702 | **ML 2.1** Class Imbalance & Cost-Sensitive Learning | Claude direct | 636 | 1 (Codex caught 4 issues: dead 2.2 forward link, sklearn-pipeline failure-mode mis-framing, SMOTEENN scope, MCC bullet contradicted module's own ROC-AUC table) |
| #703 | **ML 2.2** Interpretability + Failure Slicing | Codex + 1 inline fix (DL 1.7 stale-slug workaround) | 896 | 0 review rounds |
| #704 | **ML 2.3** Probabilistic & Bayesian ML with PyMC | Codex | 898 | 0 (agent caught 3 stale URLs in source list — ArviZ moved to python.arviz.org — and replaced) |
| #705 | **ML 2.4** Recommender Systems | Codex + 2 minor Claude fixes | 822 | 0 (agent caught **`implicit.readthedocs.io` is now hijacked spam content**; canonical is `benfred.github.io/implicit/`) |
| #706 | **ML 2.5** Conformal Prediction & Uncertainty Quantification | Codex | 900 | 0 (agent caught **MAPIE v1 API change** pre-dispatch — `MapieRegressor` deprecated; `SplitConformalRegressor`/`CrossConformalRegressor`/`ConformalizedQuantileRegressor` with `fit() → conformalize() → predict_interval()` workflow; re-pinned sources to `contrib.scikit-learn.org/MAPIE`) |
| #707 | **ML 2.6** Fairness & Bias Auditing | Codex via direct orchestrator dispatch | 899 | 1 fixup (changelog Edit failed silently due to file-modified-since-read; fixed in follow-up commit) |

**Total: Phase 0 + 18 modules under #677 + 1 stub-rewrite of module 1.1 = 19 PRs merged in one session.**

## What's still in flight

- **ML 2.7 Causal Inference for ML Practitioners** — **PR #708 opened post-handoff**. Claude-direct write per the documented Codex-fallback path; 9,809 words (denser than peers 2.5/2.6). The agent caught **two arxiv-ID hallucinations in the orchestrator's brief** during source curation (`1610.04018` was listed as "Athey & Wager causal forests" but is actually a colloidal physics paper — correct is `1510.04342`; `1706.03461` was reused for two different papers). Memory entry `feedback_verify_arxiv_ids_in_briefs.md` saved. **PR awaits cross-family Codex review + merge** in the next session — same flow as DL 1.9 and ML 2.1.

## What's NOT yet done under #677

1. **RL 2.1 Offline RL & Imitation Learning** (task #22) — pending; the last module of the locked plan. Brief format mirrors RL 1.1; cross-link to advanced-genai/1.4 RLHF.
2. **DL 1.7 cleanup PR** — pre-existing data inconsistency surfaced by ML 2.2 review and confirmed by orchestrator: file is named `module-1.7-transformers-from-scratch.md` but its frontmatter title is "Backpropagation and Autograd from Scratch" and its slug is `module-1.7-backpropagation-and-autograd-from-scratch`. The deep-learning index.md displays it as "Transformers from Scratch" (wrong). Several Tier-2 modules worked around this by avoiding the link. Cleanup options: (a) actually rewrite as a transformers-from-scratch module, or (b) rename the file + update the index display to "Backpropagation and Autograd from Scratch" to match the existing content. Recommend (b) as a small PR; (a) is a real curriculum decision.
3. **Issue #677 closure** — once ML 2.7 + RL 2.1 + (optionally) DL 1.7 cleanup ship, close #677.
4. **STATUS.md predecessor-chain reorganization** — this entry will be very long; consider whether the cross-thread notes section needs trimming or moving to archive.

## Patterns that locked in this session (operational lessons)

These are durable workflow patterns that should carry into future curriculum-batch sessions; saving the notable ones to memory.

### 1. The dispatch-and-fallback pattern

The agent runtime (background `Agent` tool) reliably dies waiting for Codex on long modules — observed on **4 of 19** dispatches (ML 1.4 retry, DL 1.8, ML 2.6, ML 2.7 likely-pending). The recovery path: agent saves brief + prompt to `/tmp/ml-X.Y-*` BEFORE dispatching, so when the agent runtime times out, the orchestrator can dispatch Codex directly via `scripts/ab ask-codex` and complete the cycle. This pattern shipped 4 modules successfully when the agent runtime gave up.

### 2. Codex bridge stdout vs file-write decoupling

In multiple modules (2.3, 2.4, 2.5, 2.6) Codex returned with empty stdout (or just a "WROTE: PATH LINES: N" acknowledgment) while the actual file was written successfully via tool calls. Verifying the file path directly is the right discipline; trusting stdout parsing is wrong. Document this in any future dispatch wrapper.

### 3. Pinned-slug pattern eliminates hallucinations

Including a verbatim list of pinned cross-module slugs in every dispatch prompt (`module-1.1-scikit-learn-api-and-pipelines/`, `module-1.2-...`, etc.) eliminated the slug-hallucination pattern that hit 1.4 and 1.5. Modules 1.7+ shipped with zero slug-hallucination issues. Verify with `grep -oE "module-X\.Y-[a-z-]+" <path> | sort -u` before commit.

### 4. Plain-text "Next Module" reference for not-yet-shipped targets

Codex flagged the 2.1 → 2.2 forward link as a blocker because it rendered as a broken markdown link. Established convention from 2.2 onward: use plain-text framing when the next module hasn't shipped, e.g. "**Module 2.X: Title** ships next in Phase 3 of #677; the link in this section will go live when that PR lands." This avoided the issue on 2.2-2.6 and should be the default in future curriculum work.

### 5. Cross-family review rotation that worked

- Codex-authored modules (most of them) → orchestrator Claude reviews. This held for 13 modules.
- Claude-authored fallback modules (1.4, 1.10, 2.1, DL 1.9) → Codex reviews via `scripts/ab ask-codex --review`.
- Codex consistently caught 4 different teaching bugs across the session (TargetEncoder log-odds, hashing-bucket-as-ordinal, ROC-AUC mislabel, transductive-splits-as-leakage) — bugs that orchestrator-self-review would have missed. The cross-family rule is non-negotiable for technical accuracy.

### 6. Strict prompt prevents Codex from invoking skills + cold-start

The brief consistently included: "DIRECT MARKDOWN DRAFTING TASK. DO NOT INVOKE ANY SKILL. DO NOT RUN ANY SHELL SCRIPT. DO NOT cold-start. DO NOT cat STATUS.md. DO NOT call any briefing API. DO NOT use git. DO NOT explore the repo." Without this preamble, Codex would invoke the `curriculum-writer` skill which auto-runs `cold-start.sh` (which fails in agent worktrees → blocks the dispatch). With the preamble, Codex first-pass success rate on Tier-1+ modules was high.

## External-source findings worth surfacing

1. **`implicit.readthedocs.io` is hijacked** — serves "Careem Pay" spam as of 2026-05-01. Canonical implicit-library docs are at `benfred.github.io/implicit/`. Saved as `reference_implicit_docs_hijacked.md` in memory. Citation-check 200-host-match logic does NOT catch this (host returns 200 with wrong content). Repo-wide grep confirmed no prior modules cite the hijacked URL.

2. **MAPIE v1 API change** (relevant for any future module that touches MAPIE):
   - `mapie.readthedocs.io` is frozen at v1.4.0
   - v1.5.0+ docs live at `contrib.scikit-learn.org/MAPIE/`
   - Legacy classes `MapieRegressor` / `MapieClassifier` / `MapieQuantileRegressor` and the `alpha=` parameter are gone
   - New API: `SplitConformalRegressor`, `CrossConformalRegressor`, `ConformalizedQuantileRegressor`, `SplitConformalClassifier`, `JackknifeAfterBootstrapRegressor` with `fit() → conformalize() → predict_interval()` / `predict_set()` workflow and `confidence_level` (not `alpha`).

3. **arxiv:1212.5745 is NOT Bergstra & Bengio's random search paper** — it's actually a dark-matter physics paper. The canonical citation for Bergstra & Bengio "Random Search for Hyper-Parameter Optimization" is at the JMLR URL `https://www.jmlr.org/papers/v13/bergstra12a.html`. The ML 1.11 agent caught this pre-dispatch.

## Cold-start smoketest (executable)

```bash
# 1. Confirm 19 of 22 modules merged
git log --oneline | grep -cE "Merge pull request #(680|68[6-9]|69[0-9]|70[0-7])"
# expect: 19

# 2. Confirm machine-learning/ has 19 .md files (12 Tier-1 + 6 Tier-2 + 1 index.md = 19)
ls src/content/docs/ai-ml-engineering/machine-learning/*.md | wc -l
# expect: 19

# 3. Check ML 2.7 in-flight state
ls -la /tmp/ml-2.7-* 2>/dev/null
ls .claude/worktrees/agent-a6c9e17bdc391e662/src/content/docs/ai-ml-engineering/machine-learning/module-2.7-*.md 2>/dev/null
# expect: brief + sources + prompt files; module file present if Codex finished, absent if still in flight

# 4. Confirm reinforcement-learning has 1 module on main (RL 1.1)
ls src/content/docs/ai-ml-engineering/reinforcement-learning/*.md
# expect: index.md + module-1.1-rl-practitioner-foundations.md

# 5. Confirm deep-learning has 9 modules (1.1-1.9)
ls src/content/docs/ai-ml-engineering/deep-learning/*.md | wc -l
# expect: 10 (index.md + 9 modules; 1.1-1.9)

# 6. Confirm DL 1.7 inconsistency still present
head -5 src/content/docs/ai-ml-engineering/deep-learning/module-1.7-transformers-from-scratch.md
# expect: title says "Backpropagation and Autograd from Scratch" — pre-existing bug

# 7. Confirm primary tree clean on main
git status -sb
# expect: ## main...origin/main (no dirty)

# 8. Check open PRs under #677
gh pr list --search "#677" --state open --json number,title --jq '.[] | "PR \(.number): \(.title)"'
# expect: 0 or 1 (depending on whether ML 2.7 has been opened yet)
```

## Cross-thread updates (for STATUS.md)

- **ADD to TODO**:
  - Wait for or recover ML 2.7 dispatch (agent `a6c9e17bdc391e662`); merge when ready
  - Dispatch RL 2.1 — the last module of the #677 plan
  - DL 1.7 cleanup PR — rename file + fix index display, OR rewrite as actual transformers-from-scratch module (curriculum decision)
  - Close #677 once 2.7 + RL 2.1 land

- **ADD to Cross-thread notes**:
  - **`implicit.readthedocs.io` domain is hijacked spam** — use `benfred.github.io/implicit/` for the implicit-library docs. Already in memory.
  - **MAPIE v1 API breaking change** documented in module 2.5; relevant for any future MAPIE work.
  - **DL 1.7 file/title/slug mismatch** is a pre-existing inconsistency that several Tier-2 modules worked around. Cleanup PR is queued.
  - **Pinned-slug + no-skill / no-cold-start preamble** is the proven dispatch pattern for Codex curriculum work; carry forward to future curriculum batches.
  - **Plain-text Next Module reference** is the convention when the target hasn't shipped yet (Codex 2.1 review caught the broken-link issue).

- **DROP from cross-thread**:
  - The "classical-ml curriculum gap" entry from the previous handoff — it's now resolved (12 modules in `machine-learning/`, 1 RL module, 2 DL extensions; 2 modules still pending under #677).

## Files modified this session (the bulk)

```
src/content/docs/ai-ml-engineering/machine-learning/                         [12 NEW + 1 rewrite + 2 renames]
src/content/docs/ai-ml-engineering/reinforcement-learning/                   [1 NEW + index]
src/content/docs/ai-ml-engineering/deep-learning/                            [2 NEW (1.8, 1.9)]
src/content/docs/ai-ml-engineering/index.md                                  [updated track hub]
src/content/docs/ai-ml-engineering/machine-learning/index.md                 [Tier-1 + Tier-2 module tables]
src/content/docs/ai-ml-engineering/reinforcement-learning/index.md           [new]
src/content/docs/ai-ml-engineering/deep-learning/index.md                    [+2 rows]
src/content/docs/changelog.md                                                [19 dated entries]
astro.config.mjs                                                             [sidebar + redirects from Phase 0]
scripts/quality/check_citations.py                                           [NEW from Phase 0]
scripts/quality/check_code_blocks.py                                         [NEW from Phase 0]
scripts/ai-ml/phase8-uk-translate.sh                                         [Phase 0: classical-ml → machine-learning + reinforcement-learning]
docs/citation-seeds/                                                         [3 renamed; 1 deleted (stale 1.1 research)]
~/.claude/projects/-Users-krisztiankoos-projects-kubedojo/memory/
  reference_implicit_docs_hijacked.md                                        [NEW]
  MEMORY.md                                                                  [pointer added]
docs/session-state/2026-05-01-ml-expansion-batch.md                          [this file]
STATUS.md                                                                    [predecessor + cross-thread updates]
```

All 19 PRs squash-merged through the standard `gh pr merge --merge` flow. Multiple agent-worktrees still locked from completed work; they self-clean when their lock processes exit. No primary-tree-detached state.

## Blockers

(none)
