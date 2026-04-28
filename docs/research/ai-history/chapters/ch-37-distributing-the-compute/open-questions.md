# Open Questions: Chapter 37 — Distributing the Compute

What remains Yellow or Red, and what archival access would help. Each question lists: the gap, the chapter scene it would strengthen, the source most likely to close it, and the access barrier.

## Yellow gaps (one source, primary anchor pending)

### Q1. Exact months of NDFS and MapReduce-in-Nutch development

**Gap.** Bonaci 2015 (Cutting-endorsed timeline) gives "2004: Cutting and Cafarella implement NDFS based on GFS spec; 2005: MapReduce integrated into Nutch (July)." Datanami's reproduction of Bonaci adds: *"It took them better part of 2004."* The exact start month of NDFS and the exact MapReduce-port commit have not been verified against a primary source.

**Scene affected.** Scene 3 (Layer 3, the open-source port) — currently the chapter's thinnest layer.

**Likely closing source.** The Apache Nutch SVN history (now Git history at `https://gitbox.apache.org/repos/asf/nutch.git` or the SVN archive). Searching for the first NDFS-related commit and the first MapReduce-related commit would give specific dates.

**Access barrier.** Tractable. Apache projects expose their full history publicly. The work is non-trivial because Nutch was active for many other reasons in 2004–2005 and the relevant commits have to be filtered out.

### Q2. The 5,000 LOC HDFS / 6,000 LOC MapReduce factoring claim

**Gap.** Wikipedia's *Apache Hadoop* History section reports "about 5,000 lines of code for HDFS and about 6,000 lines of code for MapReduce" as the size of the code factored out of Nutch in early 2006. The footnote chain points to Cutting/Cafarella/Lorica's O'Reilly Media piece *"The next 10 years of Apache Hadoop"* (31 March 2016), which is paywalled and not yet verified. No other secondary source Claude checked carries the exact figure.

**Scene affected.** Scene 3 (Layer 3) and Scene 4 (Layer 4 ledger of the split).

**Likely closing source.** The O'Reilly piece itself; alternatively, the JIRA ticket(s) corresponding to the actual code move (HADOOP-1 through HADOOP-100), or the initial 0.1.0 tarball line counts.

**Access barrier.** Paywall (O'Reilly) or moderate work (computing line counts on the 0.1.0 tarball, which itself is missing from the public archive index).

### Q3. Cutting's specific Yahoo start date in January 2006

**Gap.** Bonaci 2015 says "Cutting joins Yahoo (January)." Vance 2009 NYT says "Yahoo hired Mr. Cutting and set to work" but does not give a date. The JIRA INFRA-700 ticket dated 28 January 2006 implies Cutting was already a Yahoo employee by then (the Lucene PMC vote and the resource request he was making would have been coordinated with his new employer), but the specific Yahoo start date is not anchored.

**Scene affected.** Scene 4 (Layer 4) — the chapter currently uses "January 2006" without a more specific date.

**Likely closing source.** A LinkedIn / résumé-level source (not authoritative); Cutting's own talks; Tom White's *Hadoop: The Definitive Guide* foreword.

**Access barrier.** Mostly paywalled (LinkedIn) or non-authoritative.

### Q4. Hadoop 0.1.0 release date

**Gap.** Wikipedia says April 2006. The Apache release archive at `https://archive.apache.org/dist/hadoop/core/` does not include a 0.1.0 tarball; the earliest version present is 0.10.1 (2007-01-11). The mass timestamp on the 0.10.x–0.16.x folders (2008-01-22) suggests an archive migration that may have pruned earlier releases.

**Scene affected.** Scene 4 (Layer 4) closes by gesturing at Hadoop's first release; the chapter currently does not state a specific 0.1.0 date.

**Likely closing source.** The Apache Lucene mailing list archives circa April 2006 (the Hadoop mailing lists were under Lucene's PMC at the time, per the JIRA ticket). The release announcement email would carry the date.

**Access barrier.** Tractable. `mail-archives.apache.org` is open.

### Q5. Yahoo's specific Hadoop investment scale

**Gap.** Vance 2009 NYT says *"Yahoo is estimated to have spent tens of millions of dollars developing Hadoop"* — but the source of the estimate is not given in the article. No other verified primary source gives a specific Yahoo-Hadoop investment figure.

**Scene affected.** Scene 4 (Layer 4) and Scene 5 (Layer 5 close).

**Likely closing source.** Yahoo's own engineering blog circa 2007–2009; the Owen O'Malley / Eric Baldeschwieler interviews; Hortonworks-era retrospectives.

**Access barrier.** Tractable for narrative anchoring (engineering blogs are open); load-bearing anchoring would require a Yahoo internal source which is unlikely to be available.

### Q6. The exact division of labor between Cutting and Cafarella

**Gap.** Wikipedia and Bonaci consistently name Cutting and Cafarella as Hadoop's co-founders. The specific work each did on Nutch, NDFS, and MapReduce is not anchored.

**Scene affected.** Scenes 1, 3, and 4. The chapter currently uses "Cutting and Cafarella" jointly to avoid overclaiming.

**Likely closing source.** Cafarella's Computer History Museum oral history (if it exists); a Cafarella-authored retrospective; Tom White's foreword (which would mention Cafarella's role from Cutting's first-person perspective).

**Access barrier.** Moderate. CHM oral histories are open when they exist.

### Q7. Levy 2011 *In the Plex* — what specifically does it say about Hadoop?

**Gap.** The legacy Gemini-drafted Ch37 cited Levy 2011 as a secondary source for the Hadoop origin story. Claude did not access the book. Specific page anchors are unverified.

**Scene affected.** Scene 4 (Layer 4) — Levy's reporting on Yahoo's Google-rivalry context could enrich the chapter's framing.

**Likely closing source.** The book itself; alternatively, Levy's own *Wired* / *Backchannel* articles.

**Access barrier.** Paywall.

## Red gaps (no anchor; do not draft from)

### Q8. What did Cutting actually feel/think when he read the Google papers?

**Gap.** Bonaci 2015 reports *"When they read the paper they were astonished. It contained blueprints for solving the very same problems they were struggling with."* This is Bonaci's framing, not a Cutting quote. No verified primary source quotes Cutting on his first reading of GFS or MapReduce.

**Scene affected.** Scene 2 (Layer 2). The chapter is OK without this — Layer 2 is anchored on what the papers said, not on Cutting's reaction.

**Likely closing source.** A Cutting interview from 2005–2010 where he discusses reading the Google papers. Tom White's foreword is the most likely venue.

**Access barrier.** Paywall (Tom White).

### Q9. Was the Lucene PMC vote that the JIRA ticket references documented anywhere?

**Gap.** The JIRA INFRA-700 body says *"The Lucene PMC has voted to split part of Nutch into a new sub-project named Hadoop."* The vote itself — the message thread, the voters, the date the vote concluded — is not anchored.

**Scene affected.** Scene 4 (Layer 4). The JIRA ticket alone is sufficient to anchor the announcement; the underlying vote would be additional texture.

**Likely closing source.** The Apache Lucene developer mailing list archive (`lucene-dev@apache.org`) circa late January 2006.

**Access barrier.** Tractable. `mail-archives.apache.org` is open.

### Q10. Was MapReduce *really* explicitly designed with ML in mind?

**Gap.** The MapReduce paper's Section 6 list of uses includes "large-scale machine learning problems." This is the load-bearing anchor for the chapter's "ML-as-inheritance" argument. But: was ML on the design list when the system was built in early 2003, or did it accrue as a use case by the time of the OSDI 2004 writeup? The paper does not say.

**Scene affected.** Scene 5 (Layer 5 close). The chapter's argumentative load — that the ML era *inherited* this substrate rather than commissioning it — depends on ML having been a *post-hoc* fit, not a design goal. The current framing ("ML appears in the 2004 list of uses *alongside* web search") is honest under either reading, but a primary anchor on Google's MapReduce design intent c. 2002–2003 would strengthen the framing.

**Likely closing source.** A Dean or Ghemawat retrospective interview; the MapReduce internal design documents (not public).

**Access barrier.** Hard. Google's internal design documents are not public; retrospective interviews exist but few are anchored at length.

## What would make the chapter Layer-3-ready (the thinnest layer)

If only one archival access could be obtained before drafting, the highest-value target is **Tom White's *Hadoop: The Definitive Guide* foreword by Doug Cutting (1st edition, 2009)**. Cutting's first-person account of the NDFS-then-MapReduce port and the naming origin would close Q1, Q3, Q6, and Q8 in a single document. Without it, Layer 3 (Scene 3) should be compressed to 400–500 words and the budget reallocated to Layers 2 and 4.

## What would push the chapter from `3k-5k likely` to `4k-7k stretch`

The closing target. Three things would unlock the higher range:

1. The Tom White foreword (above) — strengthens Layer 3, gives Layer 4 first-person texture.
2. Apache Nutch SVN log circa 2004–2005 — anchors Q1's exact months for NDFS and the MapReduce port.
3. A primary anchor for Yahoo's Hadoop investment scale (Q5) — would let Layer 4 say something specific about the Yahoo bet rather than gesturing at "tens of millions" via Vance.

Without these, draft to the lower bound (~3,700 words) and accept that the chapter's natural length is shorter than the part-level target.
