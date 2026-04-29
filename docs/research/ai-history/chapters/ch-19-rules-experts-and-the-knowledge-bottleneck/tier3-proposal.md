# Tier 3 Proposal — Chapter 19: Rules, Experts, and the Knowledge Bottleneck

Per `docs/research/ai-history/READER_AIDS.md` Tier 3 workflow. Author: Claude. Reviewer: Codex (cross-family).

## Element 8 — Inline parenthetical definition (Starlight tooltip)

**SKIPPED** — universal default.

## Element 9 — Pull-quote (at most 1)

The chapter centers on primary sources from the Buchanan/Shortliffe 1984 retrospective, Feigenbaum 1977, and Shortliffe 1983. Survey of candidates:

### Candidate A — Feigenbaum 1977: the knowledge-is-power thesis

Feigenbaum's IJCAI 1977 paper is the chapter's in-period movement manifesto. The chapter paraphrases his framing throughout the "After General Methods" section — that performance comes from knowledge, that knowledge engineering is the new craft, and that acquiring/representing/using knowledge are the core design issues. The chapter does not quote any Feigenbaum sentence verbatim.

The load-bearing sentence in the chapter's historiography is the "knowledge is power" move: expertise, not general methods, is the source of performance. A verbatim Feigenbaum sentence from pp.1014–1015 that names knowledge engineering and its components would be the natural pull-quote candidate for this chapter.

**Status: PROPOSED.** Feigenbaum 1977 is a Green primary source. The IJCAI 1977 paper is publicly accessible at the cited URL. The chapter's central claim — that MYCIN's era pivoted from general methods to domain knowledge — maps directly to Feigenbaum's own in-period formulation. A pull-quote here does new work: it gives the "knowledge engineering" movement a primary-source voice rather than leaving it as paraphrase. The annotation should name the intellectual lineage from Feigenbaum's 1977 claim to the commercialization arc that follows in Ch20/Ch21.

Working verbatim candidate (Codex to verify against pp.1014–1015 of the IJCAI proceedings):

> "The key to the power of these systems lies not in their inference strategies, but rather in the knowledge that they are given to work with."

If verbatim correct, insertion anchor: after the paragraph ending "...That made AI look more practical after the winter's skepticism. It also made the labor visible. If the knowledge was the source of power, then the acquisition of knowledge became the central problem." in the "## After General Methods" section.

Annotation (1 sentence, doing new work): names that Feigenbaum published this framing as the expert-system era's organizing principle in 1977, before the commercial boom, and that the same claim would become the rationale for the expert-system industry of the 1980s.

### Candidate B — Buchanan/Shortliffe 1984, Chapter 7: the bottleneck definition

Chapter 7 of the retrospective defines knowledge acquisition as "the transfer and transformation of problem-solving expertise from sources such as experts, textbooks, databases, or experience into a program." The chapter paraphrases this definition in the "## The Bottleneck Appears" section without quoting it verbatim.

**Status: SKIPPED** in favour of Candidate A. Cap is 1. The Buchanan/Shortliffe bottleneck definition is precise but technical — it is the kind of sentence that reads well as prose paraphrase. Feigenbaum 1977 carries more rhetorical weight as the movement's public manifesto sentence. The pull-quote cap is 1; Candidate A serves the chapter's hinge point (the pivot from general methods to knowledge as power) more directly.

### Candidate C — Shortliffe 1983: the non-deployment statement

Shortliffe's 1983 interview contains the direct retrospective on MYCIN's clinical non-use. The chapter paraphrases pp.286–287. A verbatim sentence about MYCIN's experimental status could land in "## A Strong Result, A Narrow Door."

**Status: SKIPPED.** The chapter's treatment of non-deployment is already one of its most carefully hedged passages, attributing multiple causes and explicitly refusing single-cause narration. A pull-quote from Shortliffe 1983 here risks either over-simplifying (if the chosen sentence isolates one cause) or being too hedged to serve as a pull-quote (if it accurately reflects the multi-cause framing). The paraphrase in prose does this work better than a boxed excerpt would.

## Element 10 — Plain-reading asides (0–3 per chapter)

Ch19 is primarily a narrative-historical chapter. Survey of symbolically dense paragraphs:

### Candidate D — Certainty-factor mechanism paragraph

The "## Uncertainty Without Full Probability" section explains certainty factors and their distinction from Bayesian probability. The relevant paragraph: "Its answer was the certainty factor. Facts and hypotheses could carry values that represented degrees of belief or disbelief within the system's own model. Rules could combine those measures as evidence accumulated..."

This paragraph is narratively dense (explaining a technical concept in plain prose) but is not symbolically dense in the READER_AIDS.md sense — it contains no mathematical formulas, derivations, or stacked abstract definitions. The prose already does the plain-reading work itself by using everyday language ("degrees of belief or disbelief," "supported to some degree rather than proved").

**Status: SKIPPED.** Not symbolically dense. The prose paragraph already paraphrases the technical concept accessibly. An aside would repeat the surrounding prose.

### Candidate E — Backward-chaining mechanism paragraph

The "## Rules as Frozen Expertise" section explains backward chaining: "Rather than simply running every rule forward from whatever facts were available, MYCIN could work backward from a goal. If the system needed to know whether an organism was likely, it asked for evidence relevant to that hypothesis..."

Again narratively dense but not symbolically dense. The prose explains the mechanism without notation, derivations, or stacked formalisms.

**Status: SKIPPED.** Not symbolically dense. The Ch19 prose is engineered to be readable throughout; the expert-system formalism is explained in plain English rather than symbolic notation.

### Candidate F — Knowledge-acquisition bottleneck paragraph

"That work was slow because expert knowledge is not always explicit. A physician may know what to do in a case without being able to state the rule in a form that handles every exception. A knowledge engineer may hear an expert's explanation, turn it into a rule, and then discover during testing that the rule behaves badly in a neighboring case."

**Status: SKIPPED.** Narratively dense (a description of a labor process) rather than symbolically dense. An aside would only paraphrase prose that is already a paraphrase of expert knowledge.

## Summary verdict

- Element 8: SKIP (universal).
- Element 9: 1 PROPOSED (Candidate A — Feigenbaum 1977 "knowledge is power" verbatim), 2 SKIPPED (B: Buchanan/Shortliffe bottleneck definition; C: Shortliffe 1983 non-deployment).
- Element 10: 0 PROPOSED, 3 SKIPPED (D: certainty-factor paragraph; E: backward-chaining paragraph; F: knowledge-acquisition paragraph — none symbolically dense).

**Total: 1 PROPOSED, 5 SKIPPED.**

Author asks Codex to:
1. Verify Candidate A's verbatim wording against Feigenbaum 1977 IJCAI proceedings pp.1014–1015 (URL: https://www.ijcai.org/Proceedings/77-2/Papers/092.pdf). APPROVE the exact sentence if found; REJECT if not present; REVISE with the correct verbatim sentence if a nearby formulation better serves the purpose.
2. Confirm or reject the SKIPs on Candidates B and C — specifically: does the Buchanan/Shortliffe Ch7 bottleneck definition sentence read better as a pull-quote than as prose paraphrase, and does Shortliffe 1983 contain a single clean sentence about MYCIN's non-deployment that does not oversimplify the multi-cause story?
3. Did I miss a paraphrased-but-not-quoted primary-source sentence in the MYCIN evaluation section (Ch31 pp.589–594) that would serve as the chapter's pull-quote more directly than Feigenbaum 1977?
