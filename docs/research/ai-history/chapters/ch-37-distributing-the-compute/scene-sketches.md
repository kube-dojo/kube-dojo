# Scene Sketches: Chapter 37 — Distributing the Compute

Five scenes, mapped 1:1 to the Prose Capacity Plan layers in `brief.md`. Each scene lists: action (what happens), actors, anchored sources, and the prose density target. No dialogue or motive is invented; reconstruction is permitted only where multiple primary sources converge.

---

## Scene 1 — The Four-Machine Ceiling (2002–2003)

**Layer:** 1 (700–900 words)

**Action.** Doug Cutting and Mike Cafarella are running the open-source Apache Nutch web crawler. The single-machine deployment indexes about 100 web pages per second and tops out around 100 million pages. They expand to four machines. The web in 2003 has on the order of a billion individual pages. Even four-fold parallelism is not enough, and the engineering cost of going further — disk failure handling, node coordination, restartability across nodes, network partition tolerance — is the wall that stops them. The wall is not algorithmic; it is the absence of a reliable distributed-systems substrate.

**Actors.** Cutting, Cafarella; the Apache Nutch project as an institutional context.

**Anchored sources for the scene's load-bearing claims.**

- Bonaci 2015 timeline (verified by Claude `WebFetch` 2026-04-28): Lucene starts 1997; Nutch ~2002; Cafarella as University of Washington graduate student; the four-machine ceiling.
- Datanami 2015 reproduction with Cutting's "well told and accurate" endorsement: *"Faced with this scalability limit, Cutting and Carafella expanded Nutch to run across four machines. Expanding it beyond that would create too much complexity."*
- Vance 2009 NYT: anchors the broader fact that Cutting "started Hadoop … to make his Apache Nutch search-engine project scale" — i.e., the wall existed and Hadoop was the response to it.

**What the scene must NOT contain.**

- Specific dialogue between Cutting and Cafarella.
- Invented technical details about exactly which disk failed first, which network cable lost packets, etc.
- The number 100 million pages is repeated by Datanami; the precise number is Yellow. Use "about 100 million pages" rather than a precise figure.

**Prose density target.** Compact. Layer 1 sets up Layer 2; the chapter's argumentative load is the convergence between Cutting's wall and Google's already-built solution, not a Cutting-as-protagonist arc.

---

## Scene 2 — The Specifications (October 2003 – December 2004)

**Layer:** 2 (1,000–1,300 words). The densest, anchor-richest scene in the chapter.

**Action.** Two papers come out of Google in fourteen months. SOSP '03 in October 2003 publishes *The Google File System* by Ghemawat, Gobioff, and Leung; OSDI '04 in December 2004 publishes *MapReduce: Simplified Data Processing on Large Clusters* by Dean and Ghemawat. The papers describe systems already running at production scale. They are not architectural sketches; they are documentation of a system Google has been running internally since at least February 2003 (MapReduce's first version) and October 2003 (GFS at the scale described in SOSP '03). The scene unpacks what each paper actually said and why an open-source engineer reading them in 2003–2004 would have recognized them as a manual.

**Actors.** Dean, Ghemawat (and Gobioff, Leung for GFS); the Google production cluster as an actor in its own right (the place where these systems were already running). Cutting and Cafarella as readers.

**Anchored sources, ordered by where they fit in the scene.**

*GFS — what it said.*
- GFS 2003 p.1 lines 39–49: "component failures are the norm rather than the exception."
- GFS 2003 p.1 abstract + p.2 lines 89–93: deployment scale (over 1,000 storage nodes; over 300 TB of disk; hundreds of clients; thousands of disks).
- GFS 2003 p.2 line 148: single master + chunkservers + clients architecture.
- GFS 2003 p.3 line 247: 64 MB chunks.
- GFS 2003 p.3 line 160: default 3-replica chunks.

*MapReduce — what it added.*
- MapReduce 2004 p.1 abstract: "MapReduce is a programming model and an associated implementation… The run-time system takes care of the details of partitioning the input data, scheduling the program's execution across a set of machines, handling machine failures, and managing the required inter-machine communication."
- MapReduce 2004 p.3 lines 245–260: cluster spec (dual-processor x86 Linux, 2–4 GB RAM, 100 Mb/s–1 Gb/s networking, IDE disks via GFS, "hundreds or thousands of machines").
- MapReduce 2004 p.4 Section 3.3: "must tolerate machine failures gracefully."
- MapReduce 2004 p.5 lines 350–360: the 80-machines-unreachable example.
- MapReduce 2004 p.7 lines 466–471: backup tasks; 44% slowdown without them.
- MapReduce 2004 p.10 Table 1: August 2004 production stats (29,423 jobs / 3,288 TB read / 758 TB intermediate / 193 TB output / 1.2 worker deaths/job).

**The chapter's argumentative beat in this scene.** The papers worked as specifications because Google did three things deliberately: (i) treated commodity hardware as the assumption rather than the optimization target (GFS p.1 introduction); (ii) made fault tolerance transparent to the user (MapReduce p.4–p.5); (iii) restricted the programming model so parallelism was automatic (MapReduce p.1 abstract). Each of these is anchored.

**What the scene must NOT contain.**

- Invented Cutting-reading-the-paper atmospherics.
- Claims about Google's internal politics, who wrote which section, or how Dean and Ghemawat actually collaborated.
- The "60% of all Google production systems run on MapReduce" type claims that appear in later retrospectives — none of those are anchored in the OSDI 2004 paper.

**Prose density target.** This scene carries Layer 2's 1,000–1,300 words. The August 2004 Table 1 numbers and the Section 3 cluster spec should be presented as concrete, verifiable claims — quote the paper directly when in doubt.

---

## Scene 3 — The Open-Source Port (2004–2005)

**Layer:** 3 (600–800 words). The thinnest layer evidence-wise.

**Action.** Cutting and Cafarella treat the GFS paper as a specification. Over the course of 2004 they reimplement it in Java as the Nutch Distributed File System (NDFS), inside the Apache Nutch source tree. In 2005 — Bonaci's timeline says July 2005 — they port MapReduce on top of NDFS. The work happens as a subproject of Nutch, not yet as a separate Apache project. The result is a working but Nutch-integrated copy of the GFS+MapReduce stack, written in Java instead of C++, running on commodity hardware just like Google's.

**Actors.** Cutting, Cafarella; the Apache Nutch project; the Apache Software Foundation's release machinery as an institutional substrate.

**Anchored sources.**

- Bonaci 2015 timeline (Yellow on exact months; Green on the broad sequence): "2004: Cutting and Cafarella implement NDFS based on GFS spec; 2005: MapReduce integrated into Nutch (July)."
- Datanami 2015 / Woodie reproduction: *"They used the paper as the specification and started implementing it in Java. It took them better part of 2004… After it was finished they named it Nutch Distributed File System (NDFS)."* — reproduced with Cutting's stated endorsement of the Bonaci article.
- MapReduce 2004 p.11 lines 1009–1027 (the indexing rewrite anchor): the abstraction's payoff — one phase dropping from 3,800 to 700 LOC — gives the scene a concrete shape for what "the abstraction was the point" means in production code.

**What the scene must NOT contain.**

- The 5,000-LOC HDFS / 6,000-LOC MapReduce factoring number as a load-bearing claim. It is Yellow; if used, frame it as "Wikipedia editors have estimated…"
- A specific claim about *who* wrote which Java class. The division of labor between Cutting and Cafarella is Yellow.
- Invented dialogue about Cutting and Cafarella's reaction to the Google papers.

**Prose density target.** Compressed. This is the scene where the chapter is most exposed to padding pressure; if the verified evidence runs out before 600 words, cap the scene and reallocate to Scenes 2 or 4.

---

## Scene 4 — The Yellow Elephant (January–February 2006)

**Layer:** 4 (800–1,100 words). The chapter's narrative anchor.

**Action.** In January 2006 Doug Cutting joins Yahoo. On 28 January 2006 at 05:01 UTC he opens Apache JIRA INFRA-700, "new mailing lists request: hadoop." The body reads: *"The Lucene PMC has voted to split part of Nutch into a new sub-project named Hadoop."* The request is fulfilled at 05:37 UTC the same day. The name "Hadoop" comes from Cutting's two-year-old son's word for a stuffed yellow elephant — Cutting himself is on the record about this in the 2009 Vance NYT article and the 2013 Morris CNBC article. The toy is later "banished to a sock drawer," in Vance's phrasing; Morris's reporting eight years later confirms it lives in Cutting's sock drawer to this day. By April 2006 (Wikipedia's claim, Yellow) Hadoop 0.1.0 is released. Within six months of Cutting's Yahoo hire, Cutting tells Vance, "Hadoop was a critical part of Yahoo." Within a year or two, "supercritical."

**Actors.** Cutting; Cutting's son (named only as "Cutting's son, then 2"); the Lucene PMC; Yahoo; the Apache Software Foundation infrastructure team (the "Done." reply at 05:37 UTC).

**Anchored sources.**

- Apache JIRA INFRA-700, Wayback snapshot 2016-03-07: created 28/Jan/06 05:01 UTC by `cutting`; body *"The Lucene PMC has voted to split part of Nutch into a new sub-project named Hadoop."*; "Done." at 05:37 UTC.
- Vance 2009 NYT, Wayback snapshot 2012-06-30: *"…to create his own version of the technology, called Hadoop. (The name came from his son's plush toy elephant, which has since been banished to a sock drawer.)"* + the Cutting "supercritical" quote.
- Morris 2013 CNBC, Wayback snapshot 2015-11-12: *"Cutting's son, then 2, was just beginning to talk and called his beloved stuffed yellow elephant 'Hadoop' (with the stress on the first syllable)."* + Cutting's naming-criteria quote.
- Bonaci 2015 timeline: Cutting joins Yahoo January 2006; Hadoop split February 2006 (which the chapter reconciles against the JIRA's 28 January date).

**The chapter's beat in this scene.** The scene is the chapter's narrative anchor and should be allowed to be human. The toddler-named-elephant detail is well-sourced, charming, and not load-bearing — it is the texture that lets the chapter argue infrastructure history without sounding like a trade press release. The load-bearing beat is the JIRA timestamp: Hadoop became Hadoop on 28 January 2006 at 05:01 UTC, with a 36-minute infra-team turnaround.

**What the scene must NOT contain.**

- Invented dialogue between Cutting and his son.
- Claims about Yahoo's specific dollar investment without anchor (Vance's "estimated to have spent tens of millions" is Yellow; if used, attribute the estimate to Vance, not to Yahoo).
- Embellishment of the toy-elephant story beyond what Vance and Morris report.

**Prose density target.** Spend the budget. This scene is what the chapter is *for* in narrative terms; the previous scenes earn the right to tell it.

---

## Scene 5 — The Substrate the AI Era Inherited (2006–2012, briefly)

**Layer:** 5 (600–900 words). Honest close.

**Action.** Hadoop spreads. By 2007 Twitter, Facebook, and LinkedIn are experimenting with it; Cassandra (Facebook), Hive (Facebook), Kafka (LinkedIn), and Storm (Twitter) come out of those experiments. Cloudera launches in 2008; Hortonworks spins out of Yahoo in 2011. By 2009 Hadoop is determining what 300 million people see on Yahoo's homepage. By 2012 — the year ImageNet/AlexNet triggers the deep-learning surge — the open-source descendants of two 2003–2004 Google papers are running in production at every major web company. The chapter's argumentative close: the deep-learning revolution did not have to invent its data infrastructure. It inherited a substrate that web search had already built and paid for. The MapReduce paper itself, in its 2004 conclusions section, names "machine learning" as one of the system's intended uses — not because it was designed for ML, but because, like web indexing and ad ranking and Google Zeitgeist, ML was a workload that already fit the abstraction.

**Actors.** The Hadoop community as a collective; Yahoo as the institutional anchor; the broader web industry as the inheritor; the deep-learning community after 2012 as the eventual beneficiary (referenced once at most).

**Anchored sources.**

- Vance 2009 NYT: Hadoop on Yahoo's homepage in 2009; Cloudera launched 2008.
- MapReduce 2004 p.12 Section 8: *"MapReduce is used for the generation of data for Google's production web search service, for sorting, for data mining, for machine learning, and many other systems."*
- MapReduce 2004 p.10 Section 6 *Experience* bullet list: ML alongside Zeitgeist, news clustering, ad placement, geographic extraction.
- Datanami 2015 / Bonaci 2015 timeline: Cloudera 2008; Hortonworks 2011; YARN 2012.

**The chapter's beat in this scene.** Honesty over output. The chapter does NOT claim Hadoop caused the 2012 deep-learning surge. It claims the data substrate the surge needed was already in production. Frame the close around the JIRA timestamp from Scene 4: 28 January 2006, 05:01 UTC. Six years later, deep learning would arrive at a planet that already had this stack. The chapter ends there.

**What the scene must NOT contain.**

- Hindsight victory laps about big data, the cloud era, or AI's "inevitability."
- Forward-references to Spark, TensorFlow, PyTorch, Kubernetes, or any other system that belongs to later chapters.
- A claim that Hadoop was *necessary* for the deep-learning surge. It is sufficient to argue that the surge inherited a fitting substrate.

**Prose density target.** Brisk. The chapter's argument is already made; this scene seals it and exits.
