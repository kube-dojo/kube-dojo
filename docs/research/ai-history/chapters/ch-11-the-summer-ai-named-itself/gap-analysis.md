# Gap Analysis: Chapter 11 - The Summer AI Named Itself

Source: dual-reviewer pass on PR #419 / Issue #401, recorded 2026-04-27.
Claude authored the original contract; Codex (gpt-5.5) provided the
first cross-family review and anchor extraction (commit `a454a791`);
Gemini (gemini-3-flash-preview) provided the second cross-family review
with hallucination filter applied (commit `63d0ba87`). This is the
first chapter in Part 3 to receive the full Codex+Gemini dual-reviewer
treatment per the dual-review policy adopted 2026-04-27.

## Current Verdict

Research contract approved with status `capacity_plan_anchored`. Claim
counts after both reviewers integrated: **13 Green / 12 Yellow / 1 Red**
(the single Red is the Wiener exclusion claim, archive-blocked at the
Rockefeller / Norbert Wiener correspondence level). Pending human final
pass and ideally promotion of 2-3 additional Yellow Scene-2 claims via
the McCarthy 2007 retrospective before drafting unlocks.

## Codex Review (first cross-family, gpt-5.5)

Verdict: NEEDS_CHANGES with 4 must-fix findings — all addressed in
commit `a454a791`.

### Must-fix integrations from Codex

1. **Honest-close layer in Prose Capacity Plan had no scene/source
   anchor** — folded into Scene 5 layer (1,000-1,500 words) with named
   sources. Plan now passes the #416 capacity-plan gate cleanly.
2. **Three scene-sketches beats lacked rows in the sources.md
   Scene-Level Claim Table** — added rows for "four organizers as
   gatekeepers", "Logic Theorist + LISP as next-gen programs", and
   "AI as established label by early 1960s".
3. **Wiener-personality beat treated as near-fact despite
   open-questions Q1 marking the issue Red** — demoted to "contested
   interpretation across secondary sources" with explicit do-not-draft
   note.
4. **"Coined the term" language inconsistent with Q4 marked
   non-blocking** — downgraded to "named the program /
   institutionalized the term" across brief.md, sources.md, and
   people.md. Q4 stays non-blocking; Q6 (week-level dates) moved out
   of blocking section per its own "Minor" note.

### Codex anchor extraction (7 claims promoted to Green)

Codex used `curl` + `pdftotext` on the Stanford-hosted Dartmouth
Proposal PDF (which Claude's WebFetch couldn't read — the PDF was
CCITT Fax encoded, but Codex's shell tooling handled it). Seven claims
promoted to Green from primary `DartmouthProposal55` p. 1, 2, 4, 5:

- Aug 31, 1955 submission, four signatories (p. 1).
- Opening conjecture: "every aspect of learning... can be precisely
  described that a machine can simulate it" (p. 1).
- 7 research topics (p. 2).
- 2-month / 10-man framing (p. 2).
- Dartmouth College, Hanover NH, summer 1956 (p. 2).
- $13,500 requested amount (p. 4).
- Shannon's planned partial attendance (p. 5).

The granted ~$7,500 amount stays Yellow (archive-blocked at the
Rockefeller Foundation correspondence level).

### Sources added per Codex's anchor-hunt

- G. Solomonoff *dartray.pdf* (secondary synthesis, fetchable).
- Specific Solomonoff archive items (rayattend, trenattend, mccarthylist
  — image-only, hand-verification needed).
- McCarthy-to-Morison 1956 letter, McCarthy December 1956 postmortem,
  McCarthy 1959 "Programs with Common Sense" (archive-blocked at
  primary level).

## Gemini Review (second cross-family, gemini-3-flash-preview)

Verdict: NEEDS_CHANGES with 4 substantive findings, integrated with
hallucination filter applied in commit `63d0ba87`. Per
`feedback_gemini_hallucinates_anchors.md` (memory adopted 2026-04-27),
no Gemini-cited claim is promoted to Green without independent
verification by `curl` + `pdftotext` or Codex equivalent.

### Filtered integration

- **DECLINED — Mauchly/IRE March 1956 claim:** not findable in
  `dartray.pdf`; Gemini's IRE Transactions citation could not be
  independently verified.
- **DECLINED — verbatim McCarthy quote URL:** `jmc.stanford.edu/
  history/...` returns 404. Substance of McCarthy's naming motive
  was kept and re-anchored to `dartray.pdf` paraphrasing McCorduck
  1979 p. 53 (which Claude verified via local `pdftotext` on
  `dartray.pdf`).
- **ACCEPTED — Solomonoff precision finding:** verified independently.
  The workshop ran 8 weeks (June 18 – Aug 17, 1956) per Ray
  Solomonoff's notes [34]; three people (Ray, Marvin, McCarthy)
  attended full-time.
- **ACCEPTED — Moor 2006 "founding a community" framing:**
  incorporated into Scene 5 phrasing.

### Independent Claude anchor extraction (6 new Green claims)

Claude's own `dartray.pdf` `pdftotext` pass yielded 6 new Green claims
beyond Codex's 7:

- 8-week duration (June 18 – Aug 17, 1956) corrects the "6 weeks"
  secondary myth — Ray's notes [34] verified.
- Three full-time attendees (Ray Solomonoff, Marvin Minsky, John
  McCarthy).
- McCarthy naming motive (paraphrase chain dartray → McCorduck p. 53).
- Alternative names list (cybernetics, automata theory, complex
  information processing, thinking machines).
- Trenchard More's 3-week rotation in place of Nathaniel Rochester.
- Date reconciliation: Aug 31 drafted (Stanford PDF cover) vs Sep 2
  sent (dartray) — both now Green, reconciled.

## Claims Still Yellow or Red

| Claim Area | Status | Why |
|---|---|---|
| Mauchly/IRE March 1956 mention of "AI" | Yellow | Gemini-cited; could not verify via `dartray.pdf` or `curl`+`pdftotext`; still worth pursuing. |
| Granted Rockefeller Foundation amount (~$7,500) | Yellow | Archive-blocked at the Rockefeller Foundation correspondence level. |
| Pre-1955 informal use of "AI" by Solomonoff or others | Yellow | Open question per Codex review; would refine "named the program, didn't coin first" framing. |
| Wiener exclusion from Dartmouth | Red | Archive-blocked at Norbert Wiener correspondence level. Existing secondary speculation is contested; do not draft. |
| Five Scene-2 attendee biographical claims | Yellow | Claude has Codex's 7 + own 6 anchors for the workshop level; individual attendee depth (especially Solomonoff, More, Selfridge) needs additional primary anchors. |
| McCarthy 2007 retrospective naming-decision passage | Yellow | Codex followed the index and subpages 1-5 and did NOT find the naming-decision passage. Worth a deeper crawl. |

## Required Anchors Before Prose Readiness

- McCarthy 2007 retrospective: locate the naming-decision passage on
  alternate hosted versions (Stanford www-formal subpages 6+) or the
  Hofstra retrospective volume.
- Mauchly/IRE March 1956 verification or formal removal from the
  contract.
- Decide whether the granted Rockefeller amount must be Green for
  prose readiness or whether Yellow plus the requested-amount Green
  is sufficient.
- 2-3 additional Yellow Scene-2 attendee claims to Green via
  Solomonoff archive image hand-verification or oral history
  transcripts.

## Scene Strength

| Scene | Strength | Notes |
|---|---|---|
| Scene 1 — The 1955 Proposal: McCarthy, Minsky, Rochester, Shannon | Strong | `DartmouthProposal55` pp. 1-5 anchor the four-signatory framing, Aug 31 submission, $13,500 request, 7 topics, 2-month / 10-man framing, Hanover summer 1956. |
| Scene 2 — Who Actually Showed Up: 8 weeks, 3 full-time + rotators | Strong (post-Gemini integration) | `dartray.pdf` notes [34] anchor 8-week run, 3 full-time attendees, More 3-week rotation; Solomonoff archive image-only items still need hand-verification for individual depth. |
| Scene 3 — The Naming Question: cybernetics vs. AI | Medium-strong | McCarthy naming motive paraphrased via McCorduck 1979 p. 53; alternative names list anchored. |
| Scene 4 — The Workshop's Output: LT, IPL, GPS prelude | Medium-strong | Cross-link to Ch12 LT/GPS sources; Logic Theorist + LISP-as-future-program anchors added by Codex. |
| Scene 5 — Naming, Not Founding: long-tail community formation | Strong | Moor 2006 "founding a community" framing integrated; Honest-close layer now anchored to Scene 5. |

## Word Count Assessment

- Core range now: `4k-7k supported`. Codex's 7 + Claude's 6 + Gemini's
  filtered framing additions support a 4,500-6,000 word chapter
  without padding.
- Stretch range with 2-3 additional Scene-2 attendee Green claims +
  the McCarthy 2007 naming passage: 6,000-7,000 words.

## Responsible Expansion Path

To reach 4,000-7,000 words without bloat:

- Open in 1955 with the proposal's four-signatory framing and
  $13,500 request, anchored to `DartmouthProposal55` pp. 1, 4.
- Move to the actual 8-week workshop with 3 full-time attendees,
  anchored to Solomonoff's notes [34]; do not assert specific
  "discussion sessions" without primary records.
- Use the alternative-names list (cybernetics, automata theory,
  complex information processing, thinking machines) to anchor the
  naming-question scene, not modern hindsight.
- Frame the chapter as "naming the program, institutionalizing the
  term" — not "founding AI" — per the Boundary Contract's downgrade
  of "coined the term."
- Keep Wiener exclusion as a one-paragraph contested-interpretation
  note; do not draft a Wiener-personality scene.

## Handoff Requests

- Locate the McCarthy 2007 retrospective naming-decision passage on
  alternate hosted versions or the Moor 2006 *Hofstra Lectures*
  volume.
- Decide whether to drop or pursue the Mauchly/IRE March 1956 claim;
  it currently has no verified anchor.
- Decide whether the granted Rockefeller amount Yellow is acceptable
  for prose, or whether Codex's archive-block flag should hold the
  scene at the requested-amount level only.
- Hand-verify the Solomonoff archive image-only items (rayattend,
  trenattend, mccarthylist) for any additional Scene-2 attendee
  depth.
