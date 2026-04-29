# Session handoff — 2026-04-29 night-2 — Parts 2 & 3 reader-aids closed

> Picks up from `2026-04-29-part1-released.md`. This session shipped the seven remaining reader-aid chapters of canonical Parts 2 and 3, fixed the Mermaid-readability complaint (twice), and corrected a roadmap-scope error from the predecessor handoff.

## What was decided

1. **Predecessor handoff misnamed Parts 2/3.** The prior handoff said "Part 1 RELEASED (Ch01–Ch09)" and queued "Part 2 (Ch10–Ch17)" next. The canonical roadmap (`docs/research/ai-history/comprehensive-roadmap-72-chapters.md`) actually has Part 1 = Ch01–Ch05, **Part 2 = Ch06–Ch10**, **Part 3 = Ch11–Ch16**, Part 4 = Ch17–Ch23. So the "Part 1 release" was actually Part 1 + 4 of 5 Part 2 chapters; this session's job was Ch10 (closes Part 2) + Ch11–Ch16 (all of Part 3). Ch17 dropped from queue — it's Part 4.

2. **Mermaid readability needed two passes.** First fix (`cbf87960`) bumped font and made timelines render at natural width with horizontal scroll inside the column — user said still hard to read. Second fix (`00ce1f1b`) added a click-to-enlarge modal that clones the SVG, sizes it from the viewBox, and renders it with both-axis scrolling at fullscreen. Light + dark theme verified. Close via X / Escape / backdrop click; focus restores; body scroll locks. The inline view stays compact with a small "Click to enlarge" hint above each diagram.

3. **Tier 3 calibration consistent with Part 1.** Across Ch10–Ch16, the per-chapter pull-quote / plain-reading-aside calibration was 1/5, 1/5, 1/5, 1/7, 1/5, 1/7, 1/4. The pattern that held: **Codex caught at least one paraphrased-but-not-quoted primary-source sentence per chapter that the author's all-SKIP/single-PROPOSE missed or got wrong on source-fidelity grounds**. Source-PDF verification (often via OCR — Stanford WidrowHoff60, Congress.gov Statutes-at-Large) was Codex's main contribution.

4. **`scripts/ab ask-codex` wrapper is broken on stdin.** Two consecutive dispatches died silently with zero-byte output and exit 0. Direct `codex exec -m gpt-5.5 -c model_reasoning_effort=high < /tmp/prompt.txt` works first try. Documented as a feedback memory candidate at the end of this handoff.

5. **User caught a process gap: should delegate Tier 1 design to a headless Claude.** Inline iteration felt faster per chapter (~2 min vs ~5–8 min cold-start dispatch), but at scale that math is wrong — each inline chapter burned orchestrator context the headless dispatch was meant to protect. The pattern for Part 4+: dispatch the Tier 1 design (clean text-writing job) to `Agent(subagent_type="general-purpose")` while the orchestrator runs the Codex Tier 3 cycle in parallel. Memory `feedback_dispatch_to_headless_claude.md` was the rule and I should have applied it.

## What shipped on main this session

```
b4f4bc8d docs(ch16): land Tier 3 pull-quote — closes Part 3 (#562, #394)
2b1d2894 docs(ch16): add section headers + Tier 1 reader-aids (#562, #394)
b0ad6238 docs(ch15): land Tier 3 pull-quote per Codex verdict (#562, #394)
0139b897 docs(ch15): add section headers + Tier 1 + Tier 2 math sidebar (#562, #394)
c079ef24 docs(ch14): land Tier 3 pull-quote per Codex verdict (#562, #394)
c78b9559 docs(ch14): add Tier 1 reader-aids (#562, #394)
bb0715ad docs(ch13): land Tier 3 pull-quote per Codex verdict (#562, #394)
bf52de5e docs(ch13): add Tier 1 reader-aids (#562, #394)
574dcda4 docs(ch12): land Tier 3 pull-quote per Codex verdict (#562, #394)
025f8084 docs(ch12): add Tier 1 reader-aids (#562, #394)
8315c413 docs(ch11): land Tier 3 pull-quote per Codex verdict (#562, #394)
39374804 docs(ch11): add Tier 1 reader-aids — opens Part 3 (#562, #394)
5423a0be docs(ch10): land Tier 3 pull-quote per Codex verdict (#562, #394)
465e7bde docs(ch10): add Tier 1 reader-aids — closes Part 2 (#562, #394)
00ce1f1b feat(mermaid): click-to-enlarge modal — open diagram at natural size
cbf87960 fix(mermaid): render timelines at natural size; bump base font to 18px
```

14 chapter commits + 2 Mermaid fixes. All on `main`, all pushed. Build clean (1943 pages, ~37s).

### Tier 3 land tally (1-quote-cap calibration)

| Ch | Cap-cleared | Source verified by Codex | Notable |
|---|---|---|---|
| Ch10 | Mind §7 child-mind sentence | UMBC Mind PDF, pdftotext + grep | Author's all-SKIP overruled |
| Ch11 | Dartmouth proposal opening ("2 month, 10 man") | Stanford-hosted PDF | Author proposed; annotation tightened |
| Ch12 | P-1584 GPS-as-synthesis sentence | Bitsavers WESCON PDF | Author's wording compressed two claims; Codex pulled the right sentence |
| Ch13 | CACM 1960 formalism/theory sentence | Stanford HTML + LaTeX | Author proposed bibliographic opening; Codex pulled the thesis-bearing follow-up |
| Ch14 | POND61 brain-model sentence | IA POND61 scan | Author proposed NYT press; Codex declined on chapter-thesis grounds |
| Ch15 | WidrowHoff60 steepest-descent sentence | OCR'd Stanford PDF | Author's page anchor wrong (98 → 99); verbatim verified |
| Ch16 | Public Law 91-121 §203 statutory text | Congress.gov Statutes at Large PDF | Author proposed; verbatim verified as-written |

Plain-reading asides: 0 landed across all seven chapters. Tier 2 math sidebar landed on Ch15 (the only Ch10–Ch16 chapter on the math list).

## What's next

The natural next batch is **canonical Part 4 (Ch17–Ch23)** — seven chapters covering the first AI winter and the shift to expert systems:

| Ch | Status check (pre-aids) | Notes |
|---|---|---|
| Ch17 The Perceptron's Fall | Has 6 section headers; needs Tier 1 + Tier 3 only | Ch14 cross-link target — coordinate framing |
| Ch18 The Lighthill Devastation | TBD | |
| Ch19 Rules, Experts, and the Knowledge Bottleneck | TBD | |
| Ch20 Project MAC | TBD | Ch16's Project MAC content forward-references this |
| Ch21 The Rule-Based Fortune (XCON) | TBD | |
| Ch22 The LISP Machine Bubble | TBD | Ch13 forward-references this |
| Ch23 The Japanese Threat (Fifth Generation) | TBD | |

**Recommended workflow for Part 4** (per the headless-Claude rule):

```python
# For each chapter Ci, in batches of 3:
agent = Agent(
    subagent_type="general-purpose",
    description=f"Ch{Ci} Tier 1 reader-aids",
    prompt="""
    Read docs/research/ai-history/chapters/ch-XX-*/brief.md, people.md, timeline.md.
    Read src/content/docs/ai-history/ch-XX-*.md.
    Following the canonical pattern in docs/research/ai-history/READER_AIDS.md
    and the Ch01 prototype at src/content/docs/ai-history/ch-01-*.md, produce:
    1. The TL;DR (≤80 words) + Cast (≤6 rows) + Timeline (in-scope only) +
       Glossary (5–7 terms) inserted between frontmatter close and first
       prose line (or first ## section header).
    2. The "Why this still matters today" callout appended after the last
       prose paragraph, before any bibliography section.
    3. A `tier3-proposal.md` in the chapter's contract dir surveying pull-quote
       and plain-reading-aside candidates.
    Bit-identity rule: do not modify any prose body line. Verify with
    `git diff main -- ch-XX-*.md | grep '^-[^-]'` returning empty.
    Build verify with `npm run build`. Commit; do NOT push.
    Return commit SHA + a one-paragraph summary.
    """,
)
```

Then orchestrator dispatches Codex Tier 3 reviews via `cat /tmp/prompt | codex exec -m gpt-5.5 -c model_reasoning_effort=high` for each chapter, applies verdicts inline, and pushes batches.

## Cold-start smoketest (executable)

```bash
# 1. Confirm Parts 2 and 3 chapters are reader-aid-complete on main:
for f in src/content/docs/ai-history/ch-{10,11,12,13,14,15,16}-*.md; do
  printf "%-58s tldr=%s why=%s sections=%s\n" "$(basename $f)" \
    "$(grep -c ':::tip\[In one paragraph\]' $f)" \
    "$(grep -c 'Why this still matters' $f)" \
    "$(grep -c '^## ' $f)"
done

# 2. Ch15 Tier 2 math sidebar present:
grep -c 'The math, on demand' src/content/docs/ai-history/ch-15-the-gradient-descent-concept.md  # expect 1

# 3. Mermaid modal infrastructure present:
grep -c 'kd-mermaid-modal' src/css/custom.css  # expect ≥6 rules
grep -c 'openModal\|attachZoomHandler' src/scripts/mermaid-renderer.ts  # expect ≥3

# 4. Build verify:
npm run build 2>&1 | tail -3  # expect 1943+ pages, ~37s, 0 errors

# 5. Confirm sync with origin:
git status -sb && git log --oneline -3
```

Expected: every Ch10–Ch16 file shows `tldr=1 why=1 sections=≥4`; Ch15 has the math sidebar; build clean; main at `b4f4bc8d`.

## Cross-thread updates (for STATUS.md)

- **DROP** from cross-thread notes:
  - "Part 1 reader-aids RELEASED on main (Ch01–Ch09…)" → replace with **"Parts 1, 2, and 3 reader-aids RELEASED on main: Ch01–Ch16 all carry Tier 1 (TL;DR + Cast + Timeline + Glossary + Why-this-still-matters), Ch01/Ch04/Ch15 carry Tier 2 math sidebars, and 1-of-N Tier 3 pull-quotes landed per chapter under cross-family review."**

- **ADD** to cross-thread notes:
  - **Mermaid click-to-enlarge modal shipped** (`00ce1f1b`). Inline diagrams stay column-fit; click opens fullscreen modal with the SVG at natural viewBox size and both-axis scrolling. Light + dark themes. Escape / backdrop / X close.
  - **`scripts/ab ask-codex` wrapper drops stdin silently.** Direct `codex exec -m gpt-5.5 -c model_reasoning_effort=high < /tmp/prompt.txt` is the working invocation. Confirmed twice this session.
  - **Headless-Claude delegation rule reinforced** (memory `feedback_dispatch_to_headless_claude.md`). Tier 1 reader-aid design is exactly the kind of clean text-writing job that should go to `Agent(subagent_type="general-purpose")` so the orchestrator's context survives the batch. Plan locked in for Part 4.
  - **Codex Part 9 chain still in flight** — past Ch65, ch66 just merged (`26e1c7ce` and `9e73f6a7`). Don't disturb.

## Pace data

- Cold start (briefing + status + reading prior handoff): ~3 min
- Mermaid sizing investigation + first fix: ~10 min
- Mermaid click-to-enlarge modal feature: ~25 min (typescript + CSS + dev-server screenshot verification)
- Per-chapter reader-aid cycle (read brief → design Tier 1 → build → tier3 proposal → Codex dispatch → apply verdict → commit + push): ~12 min wall-clock per chapter, including ~3–8 min of Codex think time
- Total: 7 chapters × 12 min = ~85 min for Parts 2/3 reader-aids alone
- Mermaid + reader aids + handoff: ~2.5 hours total

## Blockers (none acquired this session)

- `scripts/ab ask-codex` stdin bug remains (worked around with direct `codex exec`)
- Tier 3 review depends on Codex availability; sequential-dispatch rule stays (per `feedback_codex_dispatch_sequential.md`) but the user clarified Codex can have several sessions, so the orchestrator can fan out parallel reviews
