# Session handoff — Claude Part 3 (Symbolic AI, Ch11–16) — 2026-04-27

Audience: the next Claude session that picks up Part 3 of the AI History book.

## State

**Part 3 (#401) ownership**: Claude (claimed in this session, README updated, comment on Track #401).

**Branch**: `claude/394-part3-symbolic-ai` → `epic/394-ai-history` via PR **#419**.

**Open task list** (use `TaskList` to see live state — IDs may renumber):

| Task | Status |
|---|---|
| Dispatch Gemini Ch11 review | in_progress (running in bridge as `ch11-gemini-review-2026-04-27`, PID 67363, model `gemini-3-flash-preview`) |
| Tighten Ch11 Scene 2 (dartray.pdf + McCarthy retrospective deeper crawl) | pending |
| Integrate Gemini Ch11 review | pending — blocked by dispatch |
| Ch12 (Logic Theorist & GPS) — full 8-file contract | pending — blocked by Gemini integration |
| Ch13 (LISP) — full 8-file contract | pending — blocked by Ch12 |
| Ch14 (The Perceptron) | pending — blocked by Ch13 |
| Ch15 (Gradient Descent Concept) | pending — blocked by Ch14 |
| Ch16 (Cold War Blank Check) | pending — blocked by Ch15 |

## Per-chapter delivery template

Every chapter in this Part follows the same standard, calibrated against Codex Ch24:

1. **Build full 8-file wiki**: `brief.md`, `sources.md`, `timeline.md`, `people.md`, `infrastructure-log.md`, `scene-sketches.md`, `open-questions.md`, `status.yaml`.
2. **brief.md must contain `## Prose Capacity Plan`** with each layer citing (a) a specific scene, (b) at least one source identifier from sources.md (per #416 gate).
3. **sources.md Scene-Level Claim Table**: every load-bearing claim has a row. Every row has Green/Yellow/Red status. No claim Green without a verified page anchor.
4. **Cross-family review by BOTH Codex and Gemini** (per `feedback_dual_review_required.md`):
   - Codex via `scripts/ab ask-codex` with `CODEX_BRIDGE_MODE=danger` — anchor extraction with shell tools
   - Gemini via `scripts/ab ask-gemini` — gap analysis + independent verification
5. **Status progression**: `researching` → `capacity_plan_drafted` → `capacity_plan_anchored` → `accepted`. Drafting unlocks only at `accepted` (both reviewers approve + human pass).

## Ch11 specific state (2026-04-27, end of this session)

- Status: **`capacity_plan_anchored`** as of commit `a454a791`.
- Codex review: **APPROVED** with 4 must-fixes (all integrated). 7 claims promoted to Green via `pdftotext` on Stanford Dartmouth Proposal PDF (pp. 1, 2, 4, 5).
- Gemini review: **IN FLIGHT** at session end. Resume by checking the bridge:
  ```bash
  /Users/krisztiankoos/projects/kubedojo/scripts/ab status
  ```
  Output appears in `/var/folders/pd/wvj52r1j3bd4z9y3dfc2k4180000gn/T/*ch11-gemini-review*.txt` once complete.
- After Gemini review integrated → flip status to `accepted` → unlock prose drafting.

## Tractable anchor upgrades for Ch11 (do BEFORE drafting)

Per Codex's anchor-hunt findings, two more Yellow → Green promotions are tractable without archive trips:
1. Fetch G. Solomonoff *dartray.pdf* (`world.std.com/~rjs/dartray.pdf`) — anchors naming/attendance synthesis at pp. 5-10.
2. Deeper crawl of McCarthy "What is Artificial Intelligence?" retrospective (`www-formal.stanford.edu/jmc/whatisai/`) — Codex tried subpages 1-5 and didn't find the naming-decision passage. Try further subpages or alternate hosts.

Both would lift Scene 2 (Naming Decision) from majority-Yellow to majority-Green.

## Archive-blocked items (defer or escalate to human)

- McCarthy-to-Morison 1956 letter, McCarthy December 1956 postmortem (Stanford McCarthy Papers)
- Allen Newell oral history (CHM)
- Trenchard More attendance/report (Solomonoff archive linkage)
- McCorduck interview tapes (CHM)
- Rockefeller Foundation grant records (RAC, North Tarrytown NY)
- MIT Wiener Papers (Wiener exclusion question)
- McCorduck 1979 / Crevier 1993 / Nilsson 2010 page anchors (need physical book scans)

These are deferred. The chapter can reach `accepted` without them — they would lift specific Yellow scenes to Green as stretch upgrades. The Wiener exclusion (Q1) is the only Red, and the Boundary Contract already says no load-bearing scene drafts from it.

## Ch12 starter notes (when Ch11 hits `accepted`)

Ch12 = Logic Theorist & GPS (Newell-Simon). Pairs cleanly with Ch11 because Newell-Simon arrived at Dartmouth with Logic Theorist; Ch11 Scene 3 references it as the only running program; Ch12 picks up the program's full history.

Likely primary sources:
- Newell & Simon, "The Logic Theory Machine", IRE Transactions on Information Theory 1956 (already in Ch11 sources, deepen here)
- Newell, Shaw, Simon, "Empirical Explorations of the Logic Theory Machine", Western Joint Computer Conference 1957
- Newell & Simon, "GPS, A Program That Simulates Human Thought", 1961
- Allen Newell oral history (CHM)
- Herbert Simon, *Models of My Life* (1991) autobiography
- Solomonoff Papers (cross-link to Ch11)

Likely secondary sources: McCorduck 1979 (extensive Newell-Simon coverage), Crevier 1993, Nilsson 2010, Pamela McCorduck interviews.

Boundary contract preview: Logic Theorist as the *first running symbolic-AI program*, not as the *first AI program* (the McCulloch-Pitts neural simulators predate it but in different paradigm). GPS as the move from problem-specific solver to general-purpose problem-solving architecture. Don't conflate the two — they had different ambitions and different limitations.

## Memory entries this session

New durable lessons saved to memory:
- `feedback_team_over_solo_for_book.md` — for #394 chapters Claude owns, default to team collaboration; finish one Part fully before claiming a second
- `feedback_dual_review_required.md` — chapter contracts need approval from BOTH Gemini AND Codex
- `feedback_chapter_word_count_via_contract.md` (existing) — chapters hit the word count their Plan budgets
- `feedback_chapter_word_count_via_contract.md` was added earlier in the session and validated this turn

## Cold-start function

```bash
# 1. Where are we?
curl -s http://127.0.0.1:8768/api/briefing/session?compact=1
gh pr view 419 --json mergeable,mergeStateStatus,reviewDecision

# 2. What's the current task?
TaskList   # claude harness

# 3. Did Gemini's Ch11 review return?
/Users/krisztiankoos/projects/kubedojo/scripts/ab status
ls -lt /var/folders/pd/wvj52r1j3bd4z9y3dfc2k4180000gn/T/*ch11-gemini-review*.txt 2>/dev/null

# 4. What's the latest commit on the Part 3 branch?
git -C /Users/krisztiankoos/projects/kubedojo/.worktrees/claude-394-part3 log --oneline -5

# 5. What Part 3 chapters exist on disk?
ls /Users/krisztiankoos/projects/kubedojo/.worktrees/claude-394-part3/docs/research/ai-history/chapters/ | grep -E "ch-1[1-6]"

# 6. #388 batch alive?
/bin/ps -p $(cat /Users/krisztiankoos/projects/kubedojo/logs/quality/batch.pid) -o pid,etime
```

## Open question for the human editor

Once Ch11 hits `accepted`, the question of whether to **draft Ch11's prose now** or **first build all 6 contracts (Ch11-Ch16) then draft as a batch** is open. Drafting in series gives a faster first-published-chapter milestone; building all 6 contracts first surfaces cross-chapter dependencies (LISP underlies the Ch12 program; ARPA in Ch16 funds the Ch12-15 work) that might lead to contract revisions. Recommend: contracts in series Ch11→Ch16 first, then prose drafting in series. Don't backlog 6 incomplete prose drafts.
