# Gap Analysis: Chapter 14 - The Perceptron

Source: Gemini gap analysis (gemini-3-flash-preview, message #2919) on
PR #419 / Issue #401, recorded 2026-04-27. Codex authored the contract via
`codex exec` workspace-write earlier that day with 17 Green / 12 Yellow
/ 8 Red claims. Claude integrated Gemini's audit immediately and bumped
counts to 26 Green / 20 Yellow / 10 Red.

## Current Verdict

Research contract approved with status `capacity_plan_anchored` and
review_state `claude_integrated_gemini_gap_audit_2026-04-27`. Codex's
PDF/HTML extraction of `PsychRev58` p. 386, `POND61` (full archive.org
text including pp. vii-ix preface and table-of-contents convergence-
theorem location), the `Smithsonian-MarkI` object record, the
`NavyPhoto60` Commons metadata, and the `IRE60` abstract gives a strong
primary-source spine. Gemini's audit added the documented 1958 NPL
collision (`MTP59-NPL`), independent 1962 mathematical legitimacy
(`Block62-RMP`, `Novikoff62`), the Stanford ADALINE contemporary
(`WidrowHoff60`), the Hubel-Wiesel V1 resonance (`HubelWiesel59-62`),
the Tobermory program-continuity beat (`Tobermory62-65`), and the 1971
historiographic-muting beat (`Rosenblatt71`). Two Yellow→Red splits were
applied: NYT direct-Rosenblatt-attribution and the precise "400
photocells" figure cited in prose without operator-manual extraction.

## Gemini's Audit (verbatim categories, integrated)

### Must-fix (substantive gaps that block accepted status)

1. **Missing NPL 1958 Symposium Beat:** the *Mechanisation of Thought
   Processes* symposium placed Rosenblatt's "Two Theorems," Selfridge's
   "Pandemonium," and McCarthy's "Programs with Common Sense" in a
   single proceedings volume. Without this scene, the rivalry feels
   retrospective, not 1958-documented. **Integrated** — added
   `MTP59-NPL` primary source and Scene 5 collision beat.
2. **Contemporary Scientific Legitimacy:** add H. D. Block's 1962
   *Reviews of Modern Physics* exposition and Albert Novikoff's 1962
   convergence proof to anchor the program's mathematical seriousness
   outside Rosenblatt's own voice. **Integrated** — added `Block62-RMP`
   and `Novikoff62` primary sources and Scene 4 independent-legitimacy
   beat.
3. **Stanford ADALINE Contemporary:** Widrow-Hoff (1960) at Stanford is
   a contemporary analog-hardware learning program; without it, Mark I
   reads as an isolated Buffalo quirk. **Integrated** — added
   `WidrowHoff60` primary source and Scene 5 cybernetic-family beat.
4. **Wightman/Hay Team Depth:** Project PARA (Hay/Murray operator
   manual) and the Wightman/Martin engineering credit must be a Scene
   3 beat, not a passing name list. **Integrated** — Scene 3 renamed
   "The Machine the Engineering Team Built," explicit engineering-team
   beat blocking the lone-genius framing.

### Should-add (gap-fills that strengthen but don't block)

1. **Hubel-Wiesel V1 Resonance:** the 1959-1962 V1 receptive-field
   hierarchy is structurally similar to Rosenblatt's S/A/R hierarchy.
   **Integrated** — added `HubelWiesel59-62` primary source and Scene 2
   structural-resonance beat with influence direction held agnostic.
2. **Tobermory:** Wightman's auditory-perceptron successor extends the
   program beyond 1960 Mark I. **Integrated** — added `Tobermory62-65`
   worklist source and Scene 5 program-continuity beat.
3. **1971 Boating Death Historiographic Muting:** the connectionist
   counter-narrative lost its primary defender between 1971 and the
   late-1970s revival. **Integrated** — added `Rosenblatt71` worklist
   source and Scene 5 historiographic-fade beat (kept non-melodramatic
   per anti-padding rule).
4. **Over-curated Demo Conflict:** keep humility about whether reported
   Mark I successes were highly curated closed-world demos.
   **Integrated** — added Scene 3 drafting warning + Scene-Level Claim
   Table row.

### Framing observations (boundary contract notes)

1. **Simulations-as-supplementary guardrail:** the IBM 704 / Burroughs
   220 simulations must be framed as supplementary to Mark I, not as
   substitutes. **Integrated** — explicit guardrail added in
   infrastructure-log Digital Simulation Infrastructure section.
2. **Rosenblatt's NOVEL contribution:** not the threshold neuron
   (McCulloch-Pitts 1943) and not learning in general (Hebb 1949), but
   specifically the supervised error-correction reinforcement procedure
   on the random A-layer connections plus the convergence theorem.
   **Integrated** — added Scene 2 Novel-Contribution Beat and Hard
   Framing Constraint in brief.md.
3. **Selfridge Pandemonium cybernetic-cousin link:** tighten the link
   in the cybernetic-family beat. **Integrated** — Pandemonium named
   alongside Widrow-Hoff and Wightman in Scene 5 cybernetic-family
   beat.

### Yellow → Red proposals

1. **NYT "walk, talk..." attribution as Rosenblatt's technical voice
   without resolved attribution direction → Red.** Until `NYT58`
   original scan resolves whether the wording is Rosenblatt's quoted
   speech, a Navy spokesperson's claim, or a reporter's paraphrase,
   the chapter must not attribute the precise sentence to Rosenblatt's
   technical voice. **Integrated** — Scene-Level Claim Table Red row
   added; Hard Framing Constraint and open-questions worklist updated.
2. **Precise "400 photocells" figure cited in prose without
   operator-manual extraction → Red.** Secondary sources vary on Mark
   I hardware counts and using one without the primary engineering
   manual risks factual drift. **Integrated** — Scene-Level Claim
   Table Red row added; brief.md Hard Framing Constraint added; prose
   must use "approximately 400 photocells" or "a roughly 20x20 sensory
   array" until `MarkI-Manual60` is page-extracted.

## Claims Still Yellow or Red

| Claim Area | Status | Why |
|---|---|---|
| Mark I hardware specifics (400 photocells, motor-driven potentiometers, exact A/R-unit counts) | Yellow general / Red precise | `MarkI-Manual60` metadata Green; pages not extracted; precise figures Red in prose. |
| NYT "walk, talk..." attribution direction | Yellow paraphrase / Red as Rosenblatt's technical voice | `NYT58` original scan needed. |
| 1958 NPL symposium session order, discussant remarks | Yellow | `MTP59-NPL` paper-list co-presence Green; session/discussion pages pending. |
| Block 1962 / Novikoff 1962 argument and proof structure | Yellow | Bibliographic existence Green; pages not extracted. |
| Widrow-Hoff ADALINE structural comparison with Mark I | Yellow | `WidrowHoff60` bibliographic record Green; pages not extracted. |
| Hubel-Wiesel V1 influence direction | Yellow | Resonance is structural; influence direction unsettled. |
| Tobermory continuity record | Yellow | Project existence well-attested in secondary; specific publications pending. |
| Rosenblatt 1971 sailing-accident detail | Yellow | Widely cited in secondary; primary obituary pending. |
| `TwoTheorems59` (HMSO 1959) separability theorem pages | Yellow | Bibliographic identification Green; pages 421-456 not extracted. |
| `VG1196G1` (1958 first full CAL report) | Yellow | `PsychRev58` p. 386 says article is adapted from this; report pages not extracted. |
| Mark I public demonstration date (June 23 vs June 24, 1960) | Yellow | `NavyPhoto60` release Green at June 24; secondary snippets mention June 23. |

Eight Red framings remain forbidden in prose: Perceptron as failed in
1958-1962; Rosenblatt as inventor of neural networks; Mark I as merely
a digital algorithm; Rosenblatt at Dartmouth; Minsky-Papert as Ch14's
climax; arbitrary nonlinear capability by 1962; 1969 critique imported
backward; the chapter's last page becoming Ch17. Plus the two new Red
splits: NYT direct-Rosenblatt-attribution; precise 400-photocell count
in prose.

## Required Anchors Before Prose Readiness

- `MarkI-Manual60` (Hay & Murray, 1960) DTIC pages: 400 photocells,
  20x20 retina, motor-driven potentiometers, A-unit/R-unit counts,
  plugboard, training controls, Figure 2 component layout.
- `NYT58` original article scan: exact wording, page, headline, byline,
  and attribution direction (lifts the Red on direct-Rosenblatt
  attribution).
- `MTP59-NPL` proceedings pages: at minimum the table of contents and
  Rosenblatt/Selfridge/McCarthy session-order context.
- `Block62-RMP` and `Novikoff62` pages: argument structure and tightened
  proof relationship to `POND61` chapter 5.
- `WidrowHoff60` IRE WESCON 1960 pages: ADALINE architecture for the
  Stanford-contemporary structural comparison.
- `Rosenblatt71` primary obituary: lifts the Yellow on the
  historiographic-muting beat.

## Scene Strength

| Scene | Strength | Notes |
|---|---|---|
| Scene 1 — Not Dartmouth, Buffalo | Strong | `PsychRev58` p. 386 + `POND61` pp. vii-ix anchor CAL/ONR setting. |
| Scene 2 — The Paper Perceptron + Hubel-Wiesel resonance + novel-contribution beat | Strong | `PsychRev58` problem statement + `POND61` table-of-contents pp. 79-92 anchor S/A/R/reinforcement vocabulary; Hubel-Wiesel resonance is Yellow but bibliographically Green. |
| Scene 3 — The Machine the Engineering Team Built | Medium-strong | `Smithsonian-MarkI` + `NavyPhoto60` + `POND61` p. ix engineering credit anchor the team beat; precise hardware counts await `MarkI-Manual60` extraction. |
| Scene 4 — The Theorem Under the Hype + Block/Novikoff legitimacy | Strong | `POND61` pp. 97-117 + pp. 153-193 + p. 189 anchor convergence/separability/discrimination/limits; Block62 and Novikoff62 are Green at bibliographic level. |
| Scene 5 — The 1958 Collision + Cybernetic Family + Historiographic Fade | Medium-strong | `MTP59-NPL` co-presence Green; ADALINE / Tobermory / 1971-death Yellow until pages/obituary anchored. |

## Word Count Assessment

- Core range now: 4,000-4,500 words (capped because the operator
  manual, the full NYT scan, the NPL proceedings pages, the Block
  1962 and Novikoff 1962 page extractions, and the Widrow-Hoff ADALINE
  pages remain unextracted).
- Stretch range with the above six extractions: 5,000-6,000 words.

The stretch range is `4k-7k stretch` per the Word Count Discipline
labels: possible if the named extraction gaps are filled.

## Responsible Expansion Path

To reach 4,000-7,000 words without bloat:

- Ground Scene 3 in Wightman/Martin/Hay/Murray engineering-team
  primary anchors plus `Smithsonian-MarkI` cabinet description; do not
  invent demonstration dialogue.
- Use Block 1962 and Novikoff 1962 as the independent-mathematical-
  legitimacy layer in Scene 4 to avoid leaning solely on Rosenblatt's
  own authority.
- Use the NPL 1958 proceedings table of contents as primary historical
  evidence of the cybernetic-vs-symbolic split, not as an invented
  backstage scene.
- Use Widrow-Hoff ADALINE for one paragraph of cybernetic-family
  context, not a parallel ADALINE history.
- Frame the 1971 historiographic-muting note in one careful paragraph;
  do not let it become a tragic coda.
- Keep simulations supplementary to Mark I throughout.

## Handoff Requests

- Codex anchor verification: confirm Codex's `pdftotext`+`grep`
  workflow can extract `MarkI-Manual60` from DTIC, the original
  `NYT58` from NYTimes archive, and `MTP59-NPL` proceedings pages.
- Locate `Block62-RMP` from APS / institutional repository for the
  structure of Block's 1962 mathematical exposition.
- Locate `Novikoff62` from the *Symposium on the Mathematical Theory
  of Automata* proceedings for the tightened convergence-proof
  statement.
- Locate `WidrowHoff60` from Stanford archives or IRE records.
- Decide whether the Hubel-Wiesel resonance beat needs full Hubel
  1959 + Hubel-Wiesel 1962 page extracts or whether bibliographic
  Green suffices for the resonance-only framing.
- Locate a primary obituary for Frank Rosenblatt to lift the Yellow
  on the 1971 sailing-accident historiographic note.
- Decide whether `Tobermory62-65` primary publications are needed for
  the program-continuity beat, or whether Cornell records suffice.
