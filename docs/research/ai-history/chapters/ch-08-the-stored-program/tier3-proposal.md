# Tier 3 proposal — Chapter 8: The Stored Program

Per `docs/research/ai-history/READER_AIDS.md` Tier 3 workflow. Author: Claude. Reviewer: Codex (cross-family adversarial).

## Element 1 — Pull-quote (`:::note`, ≤1 per chapter)

**Status: SKIPPED**

Rationale: Rule (b). Every quote-worthy sentence in Ch08 is already inside a prose paragraph that introduces and contextualises it. Candidates considered:

- McNulty's blueprint quote: "Somebody gave us a whole stack of blueprints, and these were the wiring diagrams for all the panels, and they said 'Here, figure out how the machine works and then figure out how to program it.'" Already quoted in-prose with the framing about security clearances; an additional callout would duplicate.
- Bartik on ENIAC's program trays: "instead of having a program counter... it had program trays which you plugged in and out of to stimulate the next operation." Already in-prose with adequate framing.
- Bartik on the role switch: "Our role switched, so that we really were programmers." Already in-prose, paragraph ends on the load-bearing claim.
- Von Neumann's tentative §2.5 unified-memory clause: "it is nevertheless tempting to treat the entire memory as one organ, and to have its parts even as interchangeable as possible." Already in-prose, paragraph carries the "uncharacteristic tentativeness" frame.
- IAS §1.3 unified-memory rule: "Conceptually we have discussed two different forms of memory: storage of numbers and storage of orders. If, however, the orders to the machine are reduced to a numerical code and if the machine can in some fashion distinguish a number from an order, the memory organ can be used to store both numbers and orders." Already in-prose at full length, framed as the cleanly-stated rule that the *First Draft* lacked.
- Von Neumann's biological analogy (§2.6): "The three specific parts CA, CC (together C) and M correspond to the associative neurons in the human nervous system." Already in-prose with the McCulloch-Pitts citation pointer.
- Eckert OH 13 on motive: "Look, he sold all our ideas through the back door to IBM as a consultant for them." + "von Neumann went down and published all that stuff." Already quoted in-prose, with the "important discipline is to keep the layers separate" paragraph immediately afterwards doing the contextual work that a callout would only repeat.
- Bartik on the 1948 retrofit relief: "rendered the horrendous problem of programming the ENIAC gone, in Bartik's phrasing." Already in-prose with attribution.
- Godfrey on the unfinished sections: "throughout the text von Neumann refers to subsequent Sections which apparently were never written. Most prominently, the Sections on programming and on the input/output system are missing." Already in-prose, framed by the immediately following claim that the missing sections were not peripheral omissions.
- Bartik's later claim: "the ENIAC was really the first stored program computer, actually." Already in-prose, immediately qualified by Haigh-Priestley-Rope's "strictly speaking" caveat.

Pull-quote: SKIP per (b). No candidate sentence would do *new* work as a callout that the surrounding prose has not already done.

## Element 2 — Plain-reading aside on a dense paragraph (`:::tip[Plain reading]`)

**Status: SKIPPED**

Rationale: `READER_AIDS.md` item 10 reserves plain-reading callouts for *symbolically* dense paragraphs (mathematical formulas, derivations, abstract definitions stacked) — explicitly *not* narratively dense paragraphs (history, biography, who-said-what). Ch08 is one of the most narratively dense chapters in Part 1: it tells an institutional history (the Moore School / IAS / IBM / Manchester / Cambridge), a credit dispute (Eckert vs. von Neumann), and a legal history (Honeywell v. Sperry Rand). Closest candidates to symbolic density:

- **The five organs paragraph** (CA, CC, M, I, O). REJECTED — this is a taxonomy of named subsystems, each unpacked in the paragraphs around it. Not symbolically dense in item 10's sense; explicitly the kind of "abstract definitions stacked" that gets refused unless the unpacking is missing, which here it is not.
- **The flag-bit construction paragraph** (Haigh-Priestley-Rope's reconstruction of how the *First Draft* distinguished numbers from orders inside unified memory). REJECTED — the paragraph contains its own plain reading: "That arrangement let a program safely modify its own instructions—a structural necessity for performing loops and conditional branches in the *First Draft*'s order code, where instruction modification was the only mechanism provided…" The next paragraph then bridges to "Later von Neumann–style designs would drop the flag-bit construction once richer instruction sets made self-modifying code optional rather than load-bearing." Adding a callout would only repeat the in-paragraph plain reading.
- **The three-paradigm decomposition paragraph** (Haigh, Priestley, and Rope's modern-code-paradigm / von-Neumann-architecture-paradigm / EDVAC-hardware-paradigm split). REJECTED — taxonomic, not symbolically dense. The paragraph introduces each name and immediately gives an example. The "this is why the chapter cannot end by awarding a single medal" paragraph then walks through which question maps to which paradigm. Plain reading is already present.
- **The 1948 ENIAC 60-order code paragraph** (Bartik on Clippinger, von Neumann recommending 1-address instruction). REJECTED — narrative, not symbolic.
- **The IAS §1.3 unified-memory rule.** REJECTED — the rule is stated in plain English in the chapter prose ("storage of numbers and storage of orders... the memory organ can be used to store both"). No symbolic density.
- **The 1973 *Honeywell v. Sperry Rand* paragraph.** REJECTED — narrative/legal history, not symbolic.

No paragraph in Ch08 satisfies the symbolic-density criterion. SKIP per item 10's explicit permission to refuse where no paragraph is genuinely (symbolically) dense.

## Element 3 — Inline parenthetical definition (Starlight tooltip)

**Status: SKIPPED**

Rationale: `READER_AIDS.md` item 8 — universal SKIP across every chapter until a non-destructive tooltip component lands. Ch08's specialist terms (*First Draft*, ENIAC, EDVAC, stored-program, modern code paradigm, von Neumann architecture, order code) are covered by the Plain-words glossary above.

---

## Author's prediction

Calibration: Ch01 2/5; Ch02 0/4; Ch03 1/3; Ch04 0/3; Ch05 0/3; Ch06 0/3; Ch07 0/3. Ch08 has the same shape as the 0/3 group — narratively dense throughout, every quote-worthy sentence already in-prose, no paragraph symbolically dense in item 10's strict sense. Predicting **0/3** with all-AGREE from Codex. Open to a counter-proposal, especially if Codex sees a paragraph that is symbolically dense in a way I've missed.
