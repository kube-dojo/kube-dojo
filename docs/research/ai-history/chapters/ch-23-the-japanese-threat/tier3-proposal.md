# Tier 3 Proposal — Chapter 23: The Japanese Threat

Per `docs/research/ai-history/READER_AIDS.md` Tier 3 workflow. Author: Claude. Reviewer: Codex (cross-family).

## Element 8 — Inline parenthetical definition (Starlight tooltip)

**SKIPPED** — universal default per READER_AIDS.md §Tier 3.

## Element 9 — Pull-quote (at most 1)

The chapter is narratively dense (institutional history, geopolitical perception, technical architecture arc) and weaves primary-source paraphrase throughout rather than sustained verbatim quotation. Strongest pull-quote candidates from available primary sources:

### Candidate A — Fuchi 1992 retrospective on the exaggerated image

Fuchi's 1992 retrospective (pp.3-4) distinguished the sensational worldwide image from the actual project goals. The chapter paraphrases his distinction but does not quote him verbatim. A pull-quote could land after the paragraph beginning "By 1992, Fuchi was explicit about the gap between image and project" in the "## The Hype Narrows" section.

Candidate sentence (from Fuchi 1992 p.3, paraphrase awaiting OCR verification):
> "The 1981 conference generated sensational news all over the world and created an exaggerated image of the FGCS project."

**Status: PROPOSED**, contingent on verbatim verification. Rationale: Fuchi's self-correction is the chapter's central historiographical move — distinguishing the threat story from the research program. A verbatim primary-source sentence makes that move explicit rather than paraphrased, and the source is Green. Insertion anchor: "## The Hype Narrows," after the opening paragraph ("By 1992, Fuchi was explicit..."). Annotation should name the rhetorical stakes: this is the project director, not a foreign critic, distinguishing the public fantasy from what ICOT actually built.

### Candidate B — OTA 1983 "competitive onslaught" framing

OTA 1983 (p.206) characterized Japan's announced objectives as a "competitive onslaught directed at the U.S. computer industry." The chapter already attributes this framing to OTA. A pull-quote could land in "## The Threat Lands Abroad."

**Status: SKIPPED** in favour of Candidate A. Cap is 1. The Fuchi retrospective serves the chapter's central corrective argument (threat-as-perception vs. research-reality) more directly than the OTA threat framing, which is already well-represented in the surrounding prose. Repeating the OTA alarm as a callout would amplify the threat story without adding new historiographical work.

### Candidate C — Feigenbaum & McCorduck *The Fifth Generation* (1983)

This book was a major amplifier of Western alarm and is on the candidate primary-source list. However, the current contract does not include it as a Green anchor. Its framing would require adding a new source before prose could carry it.

**Status: SKIPPED** — source not in current Green anchor set; adding it requires a separate source verification step outside this proposal's scope.

### Candidate D — ICOT Final Evaluation Workshop framing (Uchida/Fuchi, p.4)

The preface describes the project as combining "highly parallel processing and knowledge information processing using logic programming." Clean and compact, but this is institutional self-description rather than a quote-worthy evaluative sentence.

**Status: SKIPPED** — descriptive rather than evaluative; the prose already integrates this framing without needing a pull-quote to do new work.

## Element 10 — Plain-reading asides (0–3 per chapter)

Ch23 is narrative-institutional for most of its length. Survey of potentially dense paragraphs:

### Candidate E — Prolog/logic-programming bridge paragraph ("## The Technical Bet")

The paragraph beginning "Furukawa's structure is useful: knowledge information processing sat above logic programming..." explains a three-layer stack (knowledge processing → logic programming → parallel hardware/VLSI) and uses "logic programming" and "kernel language" in a technical sense. However, the prose immediately and clearly explains the structure in plain English ("Logic programming was the hinge. If problems could be expressed as logical relations..."). No separate aside needed.

**Status: SKIPPED** — the prose does its own plain-reading work; an aside would only repeat it.

### Candidate F — GHC/KL1 concurrent logic-programming paragraph ("## Machines For Inference")

The paragraph mentioning GHC, KL1, Multi-PSI, PIM, PIMOS, Kappa, MGTP, and HELIC-II is a survey of acronyms. It could confuse a general reader who does not know what "concurrent logic programming" means architecturally, or how GHC relates to KL1.

**Status: PROPOSED.** Rationale: the acronym stack — GHC → KL1 → Multi-PSI/PIM — represents a genuine conceptual progression (concurrent logic language research → integrating kernel language → parallel inference hardware) that the prose names but does not fully unpack. An aside can crystallize the lineage in 2 sentences without touching the prose. Insertion anchor: after the paragraph "GHC and KL1 continued that direction..." in "## Machines For Inference."

Proposed aside text:

> :::tip[Plain reading]
> GHC (Guarded Horn Clauses) extended Prolog with concurrency primitives so that multiple logical deductions could proceed in parallel. KL1 refined GHC into an integrating system language for the final stage — not just a research exercise but the one language in which FGCS intended to write everything from operating systems to applications. Multi-PSI and the PIM prototypes were the hardware platforms built to run KL1 at scale.
> :::

### Candidate G — PIM/MIPS architecture sentence ("## Machines For Inference")

The brief mention of PSI-II reaching "around 330–400 KLIPS" (kilo logical inferences per second) and PSI-III using PIM/m CPU technologies is in the claim matrix but does not appear prominently in the prose. No dense architectural passage warrants a plain-reading aside.

**Status: SKIPPED** — the KLIPS/PIM architecture is not developed to the depth that would make an aside necessary; the prose stays descriptive.

## Summary verdict

- Element 8: **SKIP** (universal).
- Element 9: **1 PROPOSED** (Candidate A — Fuchi 1992 retrospective on exaggerated image, contingent on verbatim verification); **3 SKIPPED** (B, C, D).
- Element 10: **1 PROPOSED** (Candidate F — GHC/KL1/Multi-PSI conceptual lineage aside); **2 SKIPPED** (E, G).

**Total: 2 PROPOSED, 5 SKIPPED.**

---

Author asks Codex to:

1. **Verify Candidate A verbatim** against Fuchi 1992 pp.3-4 in the Bitsavers-hosted *Fifth Generation Computer Systems 1992, Volume 1* PDF (<https://www.bitsavers.org/pdf/icot/Fifth_Generation_Computer_Systems_1992_Volume_1.pdf>). Confirm the exact sentence about the 1981 conference generating a "sensational" or "exaggerated" image; APPROVE if quote-worthy and verbatim-verifiable, REJECT if only paraphrase or already too close to the surrounding prose.
2. **Verify Candidate F prose accuracy** — confirm that GHC preceded KL1 in the project lineage and that the aside's one-sentence summary of GHC (concurrency primitives in Prolog) is technically defensible against Furukawa TR-228 pp.2-3. APPROVE / REJECT / REVISE with correction.
3. **Confirm or reject the SKIPs on B, C, D, E, G** — in particular, did the author miss any genuinely quote-worthy verbatim sentence in the OTA 1983 or NRC 2005 sources that would serve the chapter's hinge better than Candidate A?
