# Gap Analysis: Chapter 22 - The Lisp Machine Bubble

## Current Verdict

`REVIEW_REQUESTED`

The chapter has enough anchored evidence for a 4,000-5,000 word draft if it
stays focused on the infrastructure story: time-sharing pain, special hardware
as a rational answer, all-Lisp environment, commercialization, Common Lisp
portability, and stock-hardware pressure. It does not yet have enough verified
business evidence for exact market-size, revenue, sales, bankruptcy, or
failure-cause claims.

Word Count Discipline label: `4k-5k confirmed; 5k-5.6k requires business-source unlocks`

## Green Scenes

- **Time-sharing wall:** AIM-444 and Gabriel/Steele support response time,
  swapping, address-space limits, MACSYMA/LUNAR pressure, and why a special
  machine seemed rational.
- **Personal computing for AI:** AIM-444 and the Lisp Machine Manual support one
  processor/memory per user, shared resources, and service to the interactive
  programmer.
- **CONS to CADR:** AIM-444 and AIM-528 support prototype status, CADR
  terminology, writable microcode, stack support, virtual memory, and 24-bit
  virtual addressing.
- **All-Lisp environment:** AIM-444, the manual, and Symbolics 3600 support I/O,
  editor, compiler/debugger culture, display/mouse interaction, Zetalisp, and
  system software written in Lisp.
- **Commercialization bridge:** Gabriel/Steele and Symbolics 3600 support MIT
  commercialization, LMI/Symbolics emergence, CADR clones, LM-2, and 3600.
- **3600 product pitch:** Symbolics 3600 supports product specifications,
  development environment, networking, graphics, tags, and application
  ambitions.
- **Common Lisp portability:** Gabriel/Steele supports ARPA's community meeting,
  divergent Lisp communities, LMI/Symbolics participation, portable-standard
  boundaries, and criticism of Lisp-machine assumptions.
- **Stock-hardware pressure:** Gabriel/Steele supports the claim that later
  general-purpose hardware and stock Lisp implementations competed effectively.

## Yellow / Thin Areas

- **Market economics:** No parsed independent source yet for revenue, sales,
  headcount, financing, layoffs, IPO, or bankruptcy. Keep the bubble argument
  technical/economic rather than numerical.
- **Failure causes:** Dan Weinreb's archived account is identified but not
  parsed. It may unlock a richer postmortem, but it must remain participant
  memory and should not displace the anchored infrastructure argument.
- **Company conflict:** Stallman's account is identified but not parsed and is
  partisan. Use only if a balanced conflict scene is necessary.
- **Competitor map:** TI Explorer, Xerox Lisp machines, and other competitors
  are not covered by current core anchors. Mention only briefly unless a source
  is added.
- **Financial metaphor:** "Bubble" is supported as a narrative/economic frame,
  but not as an exact quantified market bubble unless business sources are
  added.

## Red / Excluded Claims

- "Symbolics failed because of exactly one cause."
- "Lisp machines were useless or technically silly."
- "The 3600 application list proves broad market adoption."
- "Common Lisp killed Lisp machines."
- "Stock hardware instantly made Lisp machines obsolete."
- "LMI/Symbolics conflict can be narrated from Stallman alone."
- Exact revenue, sales, headcount, bankruptcy, or market-share claims without a
  parsed source.

## Word Count Readiness

Natural supported range: 4,000-5,000 words.

Path to 4,000 without bloat:

- Open with a time-sharing scene tied to actual Lisp workloads.
- Explain personal processors and memory as a deliberate inversion of
  time-sharing priorities.
- Use CONS/CADR hardware details only where they explain Lisp performance and
  interactivity.
- Make the editor, mouse, display, debugger, and all-Lisp system the human
  center of the chapter.
- Treat Symbolics 3600 as a mature product scene with vendor-source caveats.
- Use Common Lisp as the portability turn, not as a language-specification
  detour.
- Close on timing and economics: special hardware had to keep outrunning stock
  hardware.

Path to 5,000-5,600 without bloat:

- Parse an independent business history of Symbolics/LMI.
- Parse Dan Weinreb's account and add it as a clearly labeled participant
  postmortem.
- Add a verified competitor source on TI Explorer/Xerox if broader market
  context becomes necessary.

## Reviewer Questions

1. Are OCR-derived page anchors from the MIT and Symbolics scans acceptable for
   Green source status if direct quotations are later checked against page
   images?
2. Is the Symbolics vendor summary correctly bounded as product-spec evidence,
   not market-success evidence?
3. Does the chapter need an independent business source before drafting, or can
   it draft at 4,000-5,000 words while excluding exact financial claims?
4. Should Dan Weinreb's participant postmortem be parsed now as a stretch
   unlock, or saved for revision if the first draft feels under-supported?
