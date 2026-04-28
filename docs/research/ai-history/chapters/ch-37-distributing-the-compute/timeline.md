# Timeline: Chapter 37 — Distributing the Compute

All dates verified against primary or endorsed-secondary sources listed in `sources.md`. Where a date is Yellow (sourced only secondarily), it is flagged inline.

## Pre-history (1997–2002)

- **1997.** Doug Cutting begins writing Lucene as a personal text-search project. *(Bonaci 2015 timeline; Yellow — secondary.)*
- **2000.** Cutting open-sources Lucene under SourceForge. *(Bonaci 2015; Yellow.)*
- **2001.** Lucene moves to the Apache Software Foundation. *(Bonaci 2015; Yellow.)*
- **End of 2001.** Cutting and Mike Cafarella, then a University of Washington graduate student, begin Apache Nutch as an open-source web crawler. *(Bonaci 2015 + Datanami 2015 / Woodie's summary of Bonaci, with Cutting's stated endorsement of the Bonaci article. Yellow on the exact start month; Green on the broad fact.)*

## Google's distributed-systems papers (2003–2004)

- **October 19–22, 2003.** SOSP '03 in Bolton Landing, NY. Ghemawat, Gobioff, and Leung publish *The Google File System*. The paper describes single-master / multi-chunkserver architecture, 64 MB chunks, default 3-replica chunks, and "the largest [GFS clusters] have over 1000 storage nodes, over 300 TB of disk storage." *(GFS 2003 p.1 footer; p.2 lines 89–93. Green.)*
- **February 2003 (internal).** First version of Google's MapReduce library written. *(MapReduce 2004 p.10 lines 905–909: "We wrote the first version of the MapReduce library in February of 2003." Green.)*
- **August 2003 (internal).** Significant MapReduce enhancements added at Google: locality optimization and dynamic load balancing of task execution. *(MapReduce 2004 p.10 line 906. Green.)*
- **August 2004 (internal).** Google runs 29,423 MapReduce jobs in a single month, reading 3,288 TB of input, producing 758 TB of intermediate data, and writing 193 TB of output. *(MapReduce 2004 p.10 Table 1. Green.)*
- **Late September 2004 (internal).** Almost 900 separate MapReduce program instances are checked into Google's source tree, up from 0 in early 2003. *(MapReduce 2004 p.10 Figure 4 description. Green.)*
- **December 2004.** OSDI '04 in San Francisco. Dean and Ghemawat publish *MapReduce: Simplified Data Processing on Large Clusters*. The paper's Section 6 list of intended uses includes "large-scale machine learning problems" alongside web indexing, news clustering, and ad-related extraction. *(MapReduce 2004 p.1 footer "To appear in OSDI 2004"; p.10 Section 6 Experience bullet list. Green.)*

## The open-source port (2004–2006)

- **2004 (course of the year).** Cutting and Cafarella reimplement the GFS specification in Java as the Nutch Distributed File System (NDFS). *(Bonaci 2015; Datanami 2015 reproduction with Cutting's endorsement: "It took them better part of 2004…" Yellow on exact months; Green on the fact.)*
- **July 2005.** MapReduce is integrated into Nutch on top of NDFS. *(Bonaci 2015 timeline. Yellow on the specific month — primary anchor in the Apache Nutch SVN log not yet pulled.)*

## The Hadoop split (January 2006)

- **January 2006 (no specific date verified).** Doug Cutting joins Yahoo. *(Bonaci 2015 timeline; Vance 2009 NYT confirms the Yahoo hire frames Hadoop's adoption arc. Green on the year-month; Yellow on the specific date.)*
- **28 January 2006, 05:01 UTC.** Doug Cutting opens Apache JIRA INFRA-700, "new mailing lists request: hadoop." Body: *"The Lucene PMC has voted to split part of Nutch into a new sub-project named Hadoop."* The request is fulfilled at 05:37 UTC the same day. *(Apache JIRA INFRA-700, Wayback snapshot 2016-03-07. Green.)*
- **March 2006.** Owen O'Malley becomes the first non-Cutting committer to the Hadoop project. *(Wikipedia History citing Cutting's 2006-03-30 mailing list announcement. Yellow — Wayback verification not yet attempted.)*
- **April 2006 (claimed).** Hadoop 0.1.0 is released. *(Wikipedia History; Yellow — the public Apache archive index Claude verified does not list a 0.1.0 tarball, only 0.10.1 from 2007-01-11 onward. The 0.1.0 → April 2006 claim is directionally consistent with the JIRA ticket but not directly verified against a tarball.)*

## Yahoo's adoption and the surrounding ecosystem (2006–2009)

- **Within six months of Cutting's Yahoo hire (mid-2006).** Hadoop becomes "a critical part of Yahoo." *(Vance 2009 NYT, direct quote from Cutting: "Within six months, Hadoop was a critical part of Yahoo and within a year or two it became supercritical." Green.)*
- **11 January 2007.** Hadoop 0.10.1 tarball published on the Apache release archive. *(Apache release archive directory listing, verified by Claude `curl` 2026-04-28. Green.)*
- **2008.** Cloudera founded by Christophe Bisciglia (ex-Google), Amr Awadallah (ex-Yahoo), Jeff Hammerbacher (ex-Facebook), and Mike Olson. Vance 2009 reports the founding announcement. *(Vance 2009 NYT. Green for the founders and the broad date; Yellow on the specific founding-month detail.)*
- **17 March 2009.** Ashlee Vance, "Hadoop, a Free Software Program, Finds Uses Beyond Search," published in *The New York Times*. Reports that Hadoop is determining what 300 million people a month see on Yahoo's homepage and matching ads to stories. *(Vance 2009 NYT, Wayback snapshot. Green.)*

## Beyond the chapter's scope (referenced only as forward pointers)

- **2008 onward.** Hadoop spreads to Twitter, Facebook, LinkedIn; Cassandra, Hive, Kafka, Storm emerge from these companies as Hadoop-ecosystem contributions. *(Vance 2009 NYT page 2 + Datanami 2015. Out of chapter scope — single-paragraph forward pointer only.)*
- **2011.** Yahoo spins out Hortonworks. *(Datanami 2015. Out of chapter scope.)*
- **2012.** YARN separates resource management from MapReduce. *(Datanami 2015. Out of chapter scope.)*
