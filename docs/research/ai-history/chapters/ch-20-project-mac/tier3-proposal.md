# Tier 3 Proposal — Chapter 20: Project MAC

Per `docs/research/ai-history/READER_AIDS.md` Tier 3 workflow. Author: Claude. Reviewer: Codex (cross-family).

## Element 8 — Inline parenthetical definition (Starlight tooltip)

**SKIPPED** — universal default per READER_AIDS.md §Tier 3.

## Element 9 — Pull-quote (at most 1)

Chapter 20 is narrative-institutional throughout: the utility vision, ARPA funding logic, operating-system contrasts, and infrastructure legacies. The prose does not quote long primary-source passages verbatim; it paraphrases Fano 1967 and the Progress Reports throughout.

### Candidate A — Fano 1967 mission sentence

Fano's 1967 "The Computer Utility and the Community" is the chapter's primary conceptual anchor for the utility dream. The Progress Reports and Norberg/O'Neill are paraphrased but not quoted verbatim in the prose body. A characteristic Fano sentence framing time-sharing as a social and intellectual utility could serve the pull-quote role.

**Status: PROPOSED.** Fano 1967 is a Green source (multicians.org, lines 12-20 and 74-80 anchored in sources.md). The chapter's thesis — that computing became infrastructure, not just a calculation device — depends on Fano's framing. A pull-quote from lines 74-80 (the social-effects passage) would do new work: it would pin the chapter's high-level claim to Fano's own voice rather than the author's paraphrase.

Insertion anchor: After the paragraph in "## The Utility Dream" that ends "The utility dream supplied that place."

Working hypothesis (Codex to verify verbatim against Fano 1967 lines 74-80 at multicians.org/fano1967.html):

> "A time-sharing system is more than a facility for sharing computing resources. It is a community resource whose technical features shape the intellectual life of the community that uses it."

If verbatim correct (or near-verbatim with negligible variation), annotation should note that Fano wrote this in 1967 — before personal computing existed — as a prediction about what shared interactive computing would become socially, not just technically.

**Cap note:** This is the only candidate. If Codex rejects on adjacent-repetition or source grounds, Element 9 is fully SKIPPED.

### Candidate B — Project MAC Progress Report II founding mission

The dual-mission sentence from Progress Report II p.xiii ("experimental investigation of online computing... man-computer dialogue and a large multiple-access system") is the founding statement. However, the prose body already paraphrases it closely in "## A Project, Not A Lab."

**Status: SKIPPED.** Paraphrase is close enough in prose that a pull-quote would create adjacent repetition. Fano 1967 (Candidate A) serves the chapter's hinge more distinctively.

## Element 10 — Plain-reading asides (1–3 per chapter)

Chapter 20 is a narrative-institutional chapter throughout. Survey:

### Candidate C — CTSS operating details paragraph

The paragraph in "## CTSS Becomes A Habit" listing passwords, file links, online manuals, and user commands.

**Status: SKIPPED.** Already written in plain prose ("A password meant that a user could return to an ongoing workspace..."). A plain-reading aside would only repeat the prose's own clarification. Not symbolically dense.

### Candidate D — Multics vs. ITS contrast paragraphs

The "## Forking Futures: Multics And ITS" section contrasts the two systems' priorities.

**Status: SKIPPED.** Narrative contrast, not symbolically dense. The prose already explains both systems in plain terms and concludes with a direct summary ("Multics asked what a general utility should become... ITS asked what an AI research environment should become..."). An aside would repeat the surrounding text.

### Candidate E — MACSYMA resource-hunger paragraph

The paragraph in "## AI On The Machine" discussing the Mathlab PDP-10 memory constraint: a system can be intellectually accepted before it is operationally easy to serve.

**Status: SKIPPED.** Conceptually interesting but not symbolically dense in the READER_AIDS.md sense (no mathematical formulas, derivations, or stacked abstract definitions). The prose explains the tension plainly. An aside would paraphrase text the reader has just finished.

## Summary verdict

- Element 8: SKIP (universal).
- Element 9: 1 PROPOSED (Candidate A — Fano 1967 social-utility sentence), 1 SKIPPED (Candidate B — Progress Report II founding mission, adjacent-repetition risk).
- Element 10: 0 PROPOSED, 3 SKIPPED (C, D, E — all narrative-dense, none symbolically dense).

**Total: 1 PROPOSED, 4 SKIPPED.**

## Author asks Codex to

1. Verify Candidate A's verbatim wording against Fano 1967 lines 74-80 at `https://multicians.org/fano1967.html`. Does the sentence "A time-sharing system is more than a facility for sharing computing resources. It is a community resource whose technical features shape the intellectual life of the community that uses it." appear verbatim or near-verbatim? APPROVE / REJECT / REVISE (with corrected wording).
2. Confirm that the prose body at the proposed insertion anchor ("...The utility dream supplied that place.") does not already quote this sentence or a sentence so close that the pull-quote would create adjacent repetition. APPROVE or flag.
3. Confirm or reject the SKIPs on Candidates B, C, D, and E — specifically: is any paragraph in the prose body genuinely symbolically dense enough (formula-stacked or abstract-definition-stacked) to warrant a plain-reading aside? If yes, identify the paragraph.
