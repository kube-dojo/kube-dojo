# Tier 3 Proposal — Chapter 14: The Perceptron

Per `docs/research/ai-history/READER_AIDS.md` Tier 3 workflow. Author: Claude. Reviewer: Codex (cross-family).

## Element 8 — Inline parenthetical definition (Starlight tooltip)

**SKIPPED** — universal default until a non-destructive tooltip component lands.

## Element 9 — Pull-quote (at most 1)

The chapter has zero verbatim quotes from primary sources. Strong candidate set:

### Candidate A — *New York Times* 8 July 1958 press rhetoric

The chapter's "Press, controversy, and historiographic muting" section paraphrases *NYT* 1958 ("New Navy Device Learns by Doing") rhetoric throughout but never quotes the headline-grabbing sentences directly. Source: `NYT58` is flagged Yellow in the contract until the original article scan is page-extracted.

The widely-quoted phrase is some variant of: a machine that the Navy expected would "be able to walk, talk, see, write, reproduce itself, and be conscious of its existence."

**Status: PROPOSED**, *pending Codex source verification.* If verbatim correct, this is the chapter's most quote-worthy press-rhetoric anchor — the exact thing the chapter argues against. Insert anchor: in the "Press, controversy, and historiographic muting" section, immediately after the paragraph introducing the *NYT* article.

If the NYT verbatim is too risky (Yellow source until page-extracted), Candidate B is the fallback.

### Candidate B — Rosenblatt's preface to *Principles of Neurodynamics* (1961)

The chapter (lines marked roughly 70–95 in the post-Tier-1 file) paraphrases Rosenblatt's preface complaint about press exuberance and his explicit distinction between perceptron research and "the invention of artificial-intelligence devices" (`POND61`, pp. vii–viii). The chapter does not quote the verbatim distinction.

**Status: PROPOSED as fallback**, *pending Codex source verification.* This sentence does work the chapter's prose paraphrases without quoting: Rosenblatt's own voice, drawing the cybernetic-vs-symbolic-AI line his own program would later be misremembered for crossing.

If Codex can verify wording, this becomes the safer choice (Green source).

## Element 10 — Plain-reading asides (1–3 per chapter)

Ch14 has math content (the convergence theorem). Survey:

### Candidate C — convergence theorem paragraph

The "Convergence and separability" section walks through the convergence claim and its bounded scope. Many of the related paragraphs are already plain-reading.

**Status: SKIPPED.** The section is paragraph-structured plain-reading already; the "if a solution exists under the stated conditions" framing is itself the gloss the aide would offer.

### Candidate D — linear separability hyperplane paragraph

Wherever the chapter explains linear separability (the geometric "hyperplane divides the classes" image).

**Status: SKIPPED.** The chapter already names the geometric reading; an aside would echo it.

### Candidate E — S/A/R unit architecture paragraph

The "Unit architecture and reinforcement" section describes the three-layer design.

**Status: SKIPPED.** The chapter explicitly walks through each unit type; Tier 1 glossary covers the abbreviation.

## Summary verdict

- Element 8: SKIP.
- Element 9: 2 PROPOSED (A — NYT press rhetoric, B — Rosenblatt preface as fallback). Cap is 1; Codex picks.
- Element 10: 0 PROPOSED, 3 SKIPPED.

**Total: 1 will land at most (Codex chooses A or B), 4 SKIPPED.**

Author asks Codex to:
1. Adjudicate A vs. B for Element 9. If A's NYT verbatim cannot be source-verified, recommend B. If both can be verified, recommend whichever does stronger thesis work (A is the "press rhetoric the chapter argues against"; B is "Rosenblatt's own pushback against the press").
2. Confirm or reject the SKIPs on plain-reading candidates C/D/E.
3. Identify any paraphrased-but-not-quoted primary-source sentence I missed.
