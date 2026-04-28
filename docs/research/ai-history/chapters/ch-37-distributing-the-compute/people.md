# People: Chapter 37 — Distributing the Compute

Each entry: verified facts, anchored to the source. Speculation, biographical color, or motive that is not on the record stays out.

## Primary actors

### Jeffrey Dean (Google)

- Co-author of *MapReduce: Simplified Data Processing on Large Clusters*, OSDI 2004, with Sanjay Ghemawat. *(MapReduce 2004 p.1 byline. Green.)*
- Affiliated with Google at the time of writing (`jeff@google.com`). *(MapReduce 2004 p.1 byline. Green.)*
- Co-author of "Web search for a planet: The Google cluster architecture," *IEEE Micro* 23(2), April 2003, with Luiz Barroso and Urs Hölzle — cited as reference [4] in the MapReduce paper. *(MapReduce 2004 references list, p.12 line 1135. Green for the citation; the paper itself was not pulled by Claude in this pass.)*
- Anything beyond Dean's authorship of these two papers and the cluster-architecture predecessor stays Yellow until biographical sources are anchored. The chapter does not need biographical color about Dean to make its argument.

### Sanjay Ghemawat (Google)

- Co-author of *MapReduce* (2004) with Dean. *(MapReduce 2004 p.1 byline. Green.)*
- Lead author of *The Google File System*, SOSP 2003, with Howard Gobioff and Shun-Tak Leung. *(GFS 2003 p.1 byline. Green.)*
- Affiliated with Google (`sanjay@google.com` for MapReduce; `{sanjay,hgobioff,shuntak}@google.com` for GFS). *(MapReduce 2004 p.1 byline; GFS 2003 p.1 footnote. Green.)*

### Howard Gobioff and Shun-Tak Leung (Google)

- Co-authors of *The Google File System*, SOSP 2003, with Ghemawat. *(GFS 2003 p.1 byline. Green.)*
- Acknowledged in the MapReduce paper for "their work in developing GFS." *(MapReduce 2004 p.12 acknowledgements. Green.)*
- The chapter mentions GFS as a system, not the careers of Gobioff or Leung; biographical color about either is out of scope.

### Doug Cutting

- At the time of the Hadoop split, Cutting was working as a software consultant before joining Yahoo. *(Vance 2009 NYT: "Doug Cutting, who had been working as a software consultant…" Green.)*
- Joined Yahoo in January 2006. *(Bonaci 2015 timeline; Vance 2009 NYT corroborates the Yahoo employment in 2006. Green for the year-month; Yellow on the specific date.)*
- Reporter on Apache JIRA INFRA-700, dated 28 January 2006 05:01 UTC, requesting the new Hadoop mailing lists on behalf of the Lucene PMC. *(Apache JIRA INFRA-700, Wayback snapshot. Green.)*
- Original author of Lucene (1997, per Bonaci 2015 timeline) and co-creator (with Cafarella) of Apache Nutch (~2002, Bonaci 2015 timeline). *(Bonaci 2015. Yellow on the exact dates; Green on the broad fact.)*
- Father of the toddler who named the stuffed yellow elephant "Hadoop." *(Vance 2009 NYT: "his son's plush toy elephant"; Morris 2013 CNBC: "Cutting's son, then 2…" Green.)*
- On the record about his criteria for software names: short, easy to spell and pronounce, meaningless, and not used elsewhere. *(Morris 2013 CNBC. Green.)*
- On the record about Yahoo's Hadoop adoption arc: "Within six months, Hadoop was a critical part of Yahoo and within a year or two it became supercritical." *(Vance 2009 NYT. Green.)*

### Mike Cafarella

- Doug Cutting's collaborator on Apache Nutch and the GFS/MapReduce reimplementation. *(Wikipedia History; Bonaci 2015. Yellow as a load-bearing biographical claim until a primary Cafarella interview is anchored; Green on the fact of co-authorship.)*
- University of Washington graduate student at the time of the Nutch / NDFS work. *(Bonaci 2015 timeline; Datanami 2015 summary. Yellow.)*
- The chapter must not split the Nutch / NDFS / MapReduce-port labor between Cutting and Cafarella in any specific way until a primary source is anchored. Default phrasing: "Cutting and Cafarella" jointly.

## Secondary actors (referenced briefly)

### Owen O'Malley

- Wikipedia History reports O'Malley as "the first committer to add to the Hadoop project" in March 2006, citing Cutting's 2006-03-30 mailing-list announcement. *(Wikipedia History; Yellow.)*
- The chapter mentions O'Malley in passing in Layer 4 only if Wayback verification of the Apache mailing list announcement is achieved. Otherwise omitted.

### Dhruba Borthakur

- Wikipedia History notes Borthakur authored "the first design document for the Hadoop Distributed File System" in 2007. *(Wikipedia History footnote 24. Yellow.)*
- Out of the chapter's primary scope; mentioned only as a forward pointer if the close (Layer 5) needs to gesture at HDFS-as-a-system maturing post-2006.

### Ashlee Vance (journalist) and Chris Morris (journalist)

- Vance, *The New York Times* tech reporter, author of the 17 March 2009 article that anchors the toy-elephant origin and Cutting's "supercritical" quote. *(Vance 2009 NYT byline. Green.)*
- Morris, *CNBC.com* contributor, author of the 28 May 2013 article that anchors the toddler-aged-2 detail and Cutting's naming-criteria quote. *(Morris 2013 CNBC byline. Green.)*
- Cited in the chapter only as the venue for Cutting's first-person material.

### Marko Bonaci (author of *History of Hadoop*)

- Author of the *Medium* "History of Hadoop" timeline (11 April 2015) used to anchor the dates of Lucene 1997, Nutch 2002, NDFS 2004, MapReduce-in-Nutch 2005, Hadoop split 2006. *(Bonaci 2015. Endorsed-secondary: Datanami 2015 reports Cutting called the article "well told and accurate." Green on the timeline endorsement; Yellow for any specific narrative claim Cutting did not directly verify.)*

## Out of chapter scope (mentioned only by name)

The MapReduce paper's Acknowledgements (p.12) name Josh Levenberg, Mohit Aron, Howard Gobioff, Markus Gutschke, David Kramer, Shun-Tak Leung, Josh Redstone, Percy Liang, Olcan Sercinoglu, Mike Burrows, Wilson Hsieh, Sharon Perl, Rob Pike, Debby Wallach, and Eric Brewer (OSDI shepherd) as contributors and reviewers. *(MapReduce 2004 p.12 lines 1141–1153. Green.)* These names are anchored as a citation but do not appear in the chapter prose; they are documented here so a future reviewer can see Claude noted them.
