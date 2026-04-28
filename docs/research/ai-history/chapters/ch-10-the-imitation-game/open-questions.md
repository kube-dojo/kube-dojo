# Open Questions: Chapter 10 — The Imitation Game

Surfaced from `brief.md` *Conflict Notes* and the Yellow/Red entries in `sources.md`. Each question identifies the specific evidence needed to resolve it. Drafting cannot rely on any open-question item until its evidence is in hand.

## Resolution Required Before Drafting (Blocking)

### Q1. The 1952 BBC broadcast — direct text verification
- **Question:** What does Turing actually say in the 14 January 1952 BBC broadcast "Can Automatic Calculating Machines Be Said To Think?", and how does Jefferson actually advance his biological objections?
- **Why it matters:** Scene 5 (Aftermath) leans on this broadcast as evidence that the empirical-test framing was defended in real time against Jefferson's objections — connecting the *Mind* paper's §6.4 Argument from Consciousness rebuttal to a live exchange. Without direct text verification, the chapter can only summarise the broadcast's existence and participants, not quote anything Turing or Jefferson said.
- **Evidence needed:** Direct text of the broadcast — published in B. J. Copeland, ed., *The Essential Turing* (Oxford UP, 2004), Ch 14, pp. 487-506. Alternatively, the BBC Written Archives Centre (Caversham) holds production files for the broadcast.
- **Status:** Yellow. Multiple fetch attempts on open mirrors failed (BBC archive 404, Internet Archive viewer auth-walled, Turing Archive returned hostname-invalid). Resolvable via library access to Copeland 2004 or via correspondence with the BBC WAC.
- **Drafting impact:** Layer 5 of the Prose Capacity Plan can draft scene structure (date, participants, that Jefferson advanced biological objections and Turing defended the test framing) but cannot quote anything verbatim until resolved. If Q1 stays Yellow at draft time, Layer 5 must cap below 600 words and rely on Saygin §3-§5 reception rather than the broadcast itself for substance.

### Q2. Proudfoot 2011 — page-level anchors for the gender-structure argument
- **Question:** What is the precise structure of Proudfoot's argument that the gender-disambiguation axis was load-bearing in Turing's original Imitation Game and that subsequent commentators replaced the test with a different test by abstracting it away?
- **Why it matters:** Scene 5 introduces Proudfoot's reading as the live counterpoint to "abstracted-test" textbook treatments. Without page anchors the chapter can cite Proudfoot's overall thesis but cannot quote her or trace her argument structure step-by-step.
- **Evidence needed:** Page-level access to D. Proudfoot, "Anthropomorphism and AI: Turing's much misunderstood imitation game," *Artificial Intelligence* 175 (5-6), April 2011, pp. 950-957 (DOI 10.1016/j.artint.2011.01.006).
- **Status:** Yellow. Crossref API confirmed citation metadata. Article is paywalled at Elsevier; OpenAlex confirms no open-access mirror. Resolvable via library access.
- **Drafting impact:** Layer 5 can cite Proudfoot's thesis at the volume/page-range level; cannot quote her verbatim. Acceptable for a 500-800-word layer that presents the disagreement without picking a side.

## Resolution Required Before Drafting (Lower-Priority but Still Blocking for Quotation)

### Q3. Carpenter & Doran 1986 — exact pagination of 1947 LMS lecture passages
- **Question:** What are the exact page numbers within Carpenter & Doran 1986 (pp. 106-124) for the "fair play for the machine" passage, the 10¹⁰-bit brain estimate, and the closing paragraph on chess as a testbed?
- **Why it matters:** The seminarTEXT transcription (verified by Claude 2026-04-28) gives clean text but its own pagination 1-14 is not the standard scholarly citation. Layer 1 of the Prose Capacity Plan currently cites "seminarTEXT pp. 12-14 / Carpenter & Doran 1986, pp. 106-124"; sharper anchors would let the chapter cite the standard print form.
- **Evidence needed:** Physical or library access to B. E. Carpenter and R. W. Doran, eds., *A. M. Turing's ACE Report of 1946 and Other Papers* (MIT Press, 1986). Alternatively, Copeland 2004 Ch 9 reprints the same lecture and may have its own clean pagination.
- **Status:** Yellow. Resolvable via library access.
- **Drafting impact:** Non-blocking. The chapter can cite the seminarTEXT pages with the standard print form as the scholarly anchor; readers and reviewers can verify against either edition.

### Q4. The 1948 NPL report — Copeland 2004 Ch 10 cross-reference
- **Question:** Do Copeland 2004 Ch 10's editorial pagination and inner section labels match the NPL inner [1]-[13] pagination preserved in the Ince 1992 *Mechanical Intelligence* edition?
- **Why it matters:** Layer 1 cites NPL inner page anchors ([1]-[13]) verified via Ince 1992. If Copeland 2004's reproduction uses different page numbers or section breaks, the chapter should cite both for cross-edition robustness.
- **Evidence needed:** Physical or library access to Copeland 2004 *The Essential Turing*, Ch 10.
- **Status:** Yellow. Non-blocking — Ince 1992 anchors are already verified Green.
- **Drafting impact:** Non-blocking. The chapter can cite Ince 1992 NPL inner pagination as primary; Copeland 2004 cross-reference would just strengthen the citation chain.

## Lower-Priority Questions (Do Not Block Drafting)

### Q5. The "Mind 49" vs "Mind 59" transcription error
- **Question:** Should the chapter footnote the transcription error in the courses.cs.umbc.edu PDF that incorrectly cites "Mind 49: 433-460" instead of "Mind 59 (236): 433-460"?
- **Why it matters:** The chapter and `sources.md` already cite the correct volume number 59 (LIX). A reader who checks the umbc.edu mirror against the chapter's citation will see the discrepancy.
- **Evidence needed:** Direct comparison with any Crossref / journal-citation reference for *Mind* 1950. Saygin et al 2000 cites volume 59.
- **Status:** Resolved. The chapter cites the correct volume 59. The transcription PDF's header error does not propagate into the chapter.
- **Drafting impact:** None.

### Q6. The 1948 NPL chess experiment — what year was the "actually done" experiment?
- **Question:** Turing 1948 NPL inner p. [13] says "This is a rather idealized form of an experiment I have actually done." What year was that experiment performed?
- **Why it matters:** If the experiment was done at Bletchley Park during the war (as some secondary sources have claimed), then the operational shape of the Imitation Game predates 1948 by several years. If the experiment was done at NPL in 1947-1948, the chronology is tighter.
- **Evidence needed:** Hodges 1983 *Alan Turing: The Enigma* (specific Bletchley chapter); Bletchley Park Trust archives; Donald Michie or I. J. Good oral histories.
- **Status:** Yellow. Non-blocking — the chapter's argument runs through the *texts*, and the 1948 NPL inner p. [13] passage is the verifiable primary anchor regardless of when the underlying experiment was performed. Resolution would let the chapter make a stronger priority claim about the operational shape of the test.
- **Drafting impact:** Non-blocking. The chapter should not lean on a strong "first formulation" priority claim for the 1948 chess experiment until this is resolved (see Scene 1 beat note in `scene-sketches.md`).

### Q7. The Lovelace 1842 *Sketch* — direct verification of the "no pretensions to originate" passage
- **Question:** What is the exact wording of the Lovelace 1842 passage Turing paraphrases in §6.6 as "the Analytical Engine has no pretensions to originate anything"?
- **Why it matters:** Layer 3 (Argumentative Spine) treats the §6.6 Lady Lovelace rebuttal as load-bearing. If the chapter quotes Turing paraphrasing Lovelace, it should also be able to point at Lovelace's actual 1842 wording for context.
- **Evidence needed:** L. F. Menabrea, "Sketch of the Analytical Engine invented by Charles Babbage," translated and with notes by A. A. L. (Augusta Ada Lovelace), *Scientific Memoirs* vol. 3 (1843), pp. 666-731. Note G of Lovelace's notes is the famous passage.
- **Status:** Yellow. Lovelace 1842 *Sketch* Note G is widely available in modern reprints (e.g. P. Morrison and E. Morrison, eds., *Charles Babbage and his Calculating Engines*, Dover, 1961). Resolvable via library access or open archives.
- **Drafting impact:** Non-blocking. Turing's paraphrase in §6.6 is the verified Green anchor; Lovelace's original wording is a stretch upgrade.

### Q8. Jefferson 1949 Lister Oration — direct verification
- **Question:** What does Jefferson's 1949 Lister Oration ("The Mind of Mechanical Man," *BMJ* 1949 vol. 1 (4616), pp. 1105-1110) actually argue, and which specific objections from it does Turing rebut in *Mind* §6.4 (Argument from Consciousness)?
- **Why it matters:** Scene 3 (Argumentative Spine) and Scene 5 (Aftermath) both reference Jefferson 1949 as background. If Layer 3 leans heavily on §6.4 it should anchor Jefferson's 1949 wording independently.
- **Evidence needed:** Direct text of the BMJ article (DOI 10.1136/bmj.1.4616.1105). The BMJ journal articles from 1949 may be open-access via PubMed Central or BMJ historical archive.
- **Status:** Yellow. Resolvable via library or PMC access.
- **Drafting impact:** Non-blocking. Scene 3's Yellow flag on the §6.4 sub-page extraction would lift if both Turing's §6.4 text and Jefferson's 1949 text are anchored.

### Q9. Saygin et al 2000 §3-§5 — specific named-author claims
- **Question:** Which specific named-author claims in Saygin §3-§5 (pp. 473-513) are load-bearing for the chapter's reception narrative? (Genova 1994 on gender; Halpern on the gender substitution; Hayes 1995 on the test's status as a "behaviourist trap"; etc.)
- **Why it matters:** Scene 5's reception synthesis currently cites "the Saygin survey" at the section level. If the chapter wants to name specific subsequent commentators, those need page-level anchors in Saygin or direct anchors in the original sources.
- **Evidence needed:** Page-level extraction of the named-author rows in Saygin §3-§5.
- **Status:** Yellow. Already-fetched PDF supports this — the next session can extract specific rows if needed.
- **Drafting impact:** Non-blocking. The chapter's Scene 5 budget (500-800 words) does not require a named-author parade; it can present the survey at the section level.

## What's not a question

- The chapter does not need to resolve "Was Turing the first to propose a behavioural test for machine intelligence?" That priority claim is interesting but not load-bearing. The chapter's claim is narrower: in 1947-1952, *Turing* — through the LMS lecture, the NPL report, the *Mind* paper, and the BBC broadcast — assembled the empirical test that the rest of the AI history book treats as the protocol. Whether someone earlier (Hobbes? Pascal? Babbage? Wiener?) gestured at something similar is a footnote, not a chapter.
- The chapter does not need to resolve "Did Turing pass his own test?" The 70%/five-minute/end-of-century prediction is a frequency claim about a population of average interrogators, not a milestone declaration. Modern claims of "passing the Turing Test" (Loebner Prize results, Eugene Goostman 2014, contemporary LLMs) belong to later chapters.

## Notes on resolution sequence

The order of attempted resolution:
1. ✅ **Done (Claude 2026-04-28):** Mind 1950 paper full text (`pdftotext` extraction); 1948 NPL report (`ocrmypdf` + `pdftotext`); 1947 LMS lecture (seminarTEXT `pdftotext`); Saygin et al 2000 §2.4 + section structure (`pdftotext`); Proudfoot 2011 citation metadata (Crossref).
2. **Q3, Q4 (library or open-archive):** Carpenter & Doran 1986 + Copeland 2004 page anchors. Tractable via any major university library or Internet Archive borrow.
3. **Q1 (library or BBC archive):** 1952 BBC broadcast text via Copeland 2004 Ch 14. Same access path as Q3, Q4.
4. **Q2 (library):** Proudfoot 2011 page anchors via Elsevier/library access.
5. **Q7, Q8 (open archive or library):** Lovelace 1842 *Sketch* Note G; Jefferson 1949 Lister Oration. Both should be tractable via PubMed Central / open archives.
6. **Q6 (archival or biographical):** Hodges 1983 / Bletchley Park / oral histories for the year-of-actual-experiment question. Lowest priority.

Rows 1 are complete; rows 2-5 are tractable without physical archive trips beyond library access; row 6 is a stretch question.

The chapter has reached `capacity_plan_anchored` status: every Prose Capacity Plan layer cites at least one verified source identifier, with Layers 1-4 anchored Green and Layer 5 mixing one Green anchor (Saygin §2.4) with two Yellow anchors (Proudfoot 2011, 1952 BBC). Promotion of Layer 5 to fully Green requires Q1 + Q2 resolution.
