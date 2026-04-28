# Open Questions: Chapter 34 — The Accidental Corpus

What's still Yellow or Red after the 2026-04-28 anchor pass, and what archival access would help.

## Q1. Provenance of the Jelinek "fire a linguist" quote (Red)

Multiple secondary sources attribute to Frederick Jelinek (IBM Speech Group, later JHU) the line "Every time I fire a linguist, the performance of the speech recognizer goes up" or variants. The quote is widely repeated, but its primary source is unclear — sometimes attributed to a 1985 NLP workshop, sometimes to internal IBM memos, sometimes to a 1988 conference talk. **Status: Red. Do not draft.** The chapter does not need this quote; the empirical revival can be told without it.

What would unlock it: a primary source attributable to Jelinek directly (paper, recorded talk, letter, or first-person witness statement). Until then, treat as folklore.

## Q2. Brown Corpus original 1967 page anchors (Yellow → Green)

The Manual (Wayback `20080309235836`) provides the corpus-size and structure anchors. The original 1967 *Computational Analysis of Present-Day American English* (Brown University Press) is the canonical citation and the form Halevy 2009 references, but I have not opened the physical book; specific page anchors for the introduction and methodology are not yet extracted. **Status: Yellow.**

What would unlock it: physical or scanned access to the 1967 Brown University Press volume. Likely available through Brown University Library or HathiTrust. Not on the chapter's critical path because the Manual provides the anchors needed.

## Q3. Hall, Jurafsky, and Manning 2008 ACL Anthology empirical-shift analysis (Yellow)

Church 2011 pp.1-2 cites Hall et al. 2008 for the dating of the empirical inflection point to 1988. The Hall et al. paper is referenced but I have not fetched the original. **Status: Yellow.** The chapter could cite Church 2011 alone for this beat without further research, but a direct Hall-et-al. citation would strengthen Scene 1.

What would unlock it: ACL Anthology lookup for Hall, Jurafsky, Manning 2008. Tractable.

## Q4. Church & Mercer 1993 special issue introduction (Yellow → Green if needed)

Church 2011 p.4 quotes from Church & Mercer 1993, the introduction to the *Computational Linguistics* special issue on "Using Large Corpora." The quote is anchored via Church 2011 (transitively Green for the chapter's purposes), but a direct anchor in Church & Mercer 1993 would be cleaner. **Status: Yellow.** ACL Anthology likely has the special issue.

What would unlock it: lookup of CL vol.19 no.1 (March 1993) special-issue introduction. Tractable.

## Q5. Resnik's preliminary 1998 STRAND paper (Yellow)

Resnik 1999 references Resnik 1998 for the original STRAND results. The 1998 paper is at AMTA-98 (Association for Machine Translation in the Americas) and is referenced via `http://umiacs.umd.edu/~resnik/amta98/`. **Status: Yellow.** The chapter does not strictly need it; Resnik 1999 supersedes the preliminary work for the chapter's purposes.

What would unlock it: AMTA archive lookup. Not on the critical path.

## Q6. Brown et al. 1990 IBM statistical-MT paper (Yellow)

Resnik 1999 §1 p.527 cites "Brown et al., 1990" as the canonical statistical-MT reference. This is presumably Brown, Cocke, Della Pietra et al., "A Statistical Approach to Machine Translation," *Computational Linguistics*. Anchored as a *reference* in Resnik 1999, but I have not fetched the IBM paper itself. **Status: Yellow.** Useful as background but not load-bearing for Ch34's argument; the deeper IBM-MT story belongs to Ch32 or earlier.

What would unlock it: ACL Anthology lookup. Tractable; not on critical path.

## Q7. Berners-Lee's later commentary on the Web's relationship to AI (Yellow)

The 1989 proposal is silent on AI. Berners-Lee's later writings (e.g., *Weaving the Web*, 1999; W3C Semantic Web essays from 1998 onward) discuss the Web's information role at length. Halevy 2009 actually references Berners-Lee, Hendler, and Lassila's "The Semantic Web" *Scientific American* article (May 17, 2001) as ref [11]. **Status: Yellow.** The chapter does not need this — the boundary contract is that the *1989 document* is silent on AI, which is verified — but a footnote could reference Berners-Lee's later thinking on data.

What would unlock it: fetch of *Scientific American* article (paywalled but archived). Not on critical path.

## Q8. The exact production status of Brants et al. 2007's MT system (Yellow)

The 2007 EMNLP-CoNLL paper describes the distributed-LM infrastructure as serving 2 trillion tokens to a translation system. The paper does not explicitly say whether this was *Google Translate's* production stack or a research evaluation system. Secondary commentary widely treats this as Google Translate's substrate, but the paper itself does not make that claim. **Status: Yellow.** The chapter should describe the system carefully — "operational" and "production-style" rather than asserting it was Google Translate.

What would unlock it: a separately authored paper or talk by Och or Dean explicitly tying the LM infrastructure to Google Translate's launch. Not on critical path.

## Q9. The "industry vs. academy" institutional pattern (Yellow as critical interpretation)

Banko & Brill at Microsoft, Halevy/Norvig/Pereira at Google, Brants et al. at Google, Resnik at Maryland with DoD funding. The pattern is real and observable. Whether to draw a structural conclusion — that web-scale empiricism was constituted as a corporate research program with privileged data access — is interpretive. Church 2011 raises the concern indirectly. **Status: Yellow as interpretation.** The chapter can note the pattern factually without needing to commit to a structural argument.

What would unlock a stronger claim: a critical-history secondary source (e.g., a STS / sociology-of-AI paper) explicitly making this argument with primary evidence. Not anchored yet.

## Q10. The "Mesh"→"World Wide Web" rename — exact date and primary documentation (Yellow)

The prefatory header on the HTMLized 1989 proposal is itself written by Berners-Lee at a later date (the rename note presupposes "1990" had already happened). The chapter should treat this as Berners-Lee's later self-reportage, not as a 1989 primary document. **Status: Yellow as an attribution refinement.**

What would unlock it: a 1990 primary source (commit log, code header, internal CERN memo) confirming the rename date. Not on critical path; the chapter's load-bearing claim is just that the system *was* renamed at some point in 1990.

## Q11. Earlier web-mining work that pre-dates Resnik 1999 (Yellow)

Resnik's 1998 preliminary work was not the first to use the web as a data source. Earlier work by Diekema et al. (TREC-7, 1998) and Gey et al. (TREC-7, 1998) is referenced in Resnik 1999 §1 p.527. The chapter can choose to credit Resnik 1999 with the *formal evaluation* contribution rather than with first use of the web. **Status: Yellow.** Useful context.

What would unlock a fuller version: TREC-7 Proceedings (Voorhees and Harman 1998). Tractable via NIST TREC archive.

## Q12. The chapter's relationship to Ch32 (DARPA SUR / speech recognition) (Yellow as cross-chapter handoff)

Speech recognition's earlier statistical turn — Jelinek-era IBM, ARPA SUR program, the late-1980s/early-1990s sphinx work — is the empirical-revival counterpart in *speech*. Ch32 covers it. Ch34 references it as background but does not draft it. **Status: Yellow as cross-chapter coordination.** Confirm with the editor that Ch32's framing aligns with Ch34's pendulum-mid-swing claim.

What would unlock cleaner alignment: a quick read of Ch32's brief.md when it exists. Currently Ch32 is one of the unfilled chapter directories.

## What is *not* an open question

- The 1,014,312-word figure for the Brown Corpus. **Green via Manual §1.**
- That Berners-Lee's 1989 proposal does not mention AI. **Green via direct text grep.**
- The 1-billion-word Banko-Brill corpus and its log-linear curves. **Green via Banko-Brill 2001 §3 PDF p.2.**
- The trillion-token Web 1T 5-Gram release. **Green via LDC LDC2006T13 catalog.**
- The Halevy "trump" sentence. **Green via Halevy 2009 p.9.**

## Summary

The chapter is well-anchored on its load-bearing claims. The open questions are mostly *additive* — extra primary sources that would deepen specific paragraphs but are not required to draft. The two genuinely Red items (Q1 Jelinek quote; deep Berners-Lee commentary on AI) should not be drafted; the chapter does not need them.
