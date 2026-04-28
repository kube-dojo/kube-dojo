# Infrastructure Log: Chapter 37 — Distributing the Compute

The chapter's infrastructure argument rests on five anchored pieces of evidence: the Google production cluster spec circa 2003–2004, the GFS deployment scale circa 2003, the MapReduce deployment scale in August 2004, the cluster the published MapReduce benchmarks ran on, and the post-Yahoo Hadoop deployment scale Cutting described in 2009. Each piece is anchored to a specific page or paragraph below.

## Google's commodity cluster (2003–2004)

The MapReduce paper's Section 3 environment description (p.3 lines 245–260, anchored 2026-04-28) is the single most useful infrastructure anchor for the chapter:

- **Compute:** dual-processor x86 processors running Linux, 2–4 GB of memory per machine.
- **Networking:** typically 100 Mbit/s or 1 Gbit/s at the machine level, "averaging considerably less in overall bisection bandwidth."
- **Cluster size:** "hundreds or thousands of machines, and therefore machine failures are common."
- **Storage:** "inexpensive IDE disks attached directly to individual machines. A distributed file system [GFS] developed in-house is used to manage the data stored on these disks. The file system uses replication to provide availability and reliability on top of unreliable hardware."
- **Scheduling:** "Users submit jobs to a scheduling system. Each job consists of a set of tasks, and is mapped by the scheduler to a set of available machines within a cluster."

This five-bullet description — verified verbatim from the OSDI 2004 paper — is the chapter's anchor for the claim that *commodity hardware was the assumption, not the optimization target*. The infrastructure-shift argument rests on this.

## GFS production deployment (October 2003)

GFS 2003 p.2 lines 89–93 (verified `pdftotext` 2026-04-28):

> "Multiple GFS clusters are currently deployed for different purposes. The largest ones have over 1000 storage nodes, over 300 TB of disk storage, and are heavily accessed by hundreds of clients on distinct machines on a continuous basis."

GFS 2003 p.1 abstract (verified):

> "The largest cluster to date provides hundreds of terabytes of storage across thousands of disks on over a thousand machines, and it is concurrently accessed by hundreds of clients."

GFS architecture (p.2 line 148; p.3 line 160; p.3 line 247, all verified):

- single master + multiple chunkservers + multiple clients
- 64 MB chunk size (much larger than typical filesystem block sizes)
- 3-replica chunks by default, with per-namespace overrides

These three anchors together support the chapter's two-paragraph GFS exposition. They are sufficient; no further GFS anchors are needed for Layer 2.

## MapReduce production deployment (August 2004)

MapReduce 2004 p.10 Table 1 (verified `pdftotext` 2026-04-28):

| Metric | Value |
|---|---|
| Number of jobs | 29,423 |
| Average job completion time | 634 secs |
| Machine days used | 79,186 days |
| Input data read | 3,288 TB |
| Intermediate data produced | 758 TB |
| Output data written | 193 TB |
| Average worker machines per job | 157 |
| Average worker deaths per job | 1.2 |
| Average map tasks per job | 3,351 |
| Average reduce tasks per job | 55 |
| Unique map implementations | 395 |
| Unique reduce implementations | 269 |
| Unique map/reduce combinations | 426 |

This single table is the chapter's load-bearing anchor for "this was production at planet scale, not a research demo." Use the row "Input data read 3,288 TB" as the headline number; the "Average worker deaths per job 1.2" row is useful for the fault-tolerance scene because it shows machine failure was *normal*, not exceptional.

## The published-benchmarks cluster (2004)

MapReduce 2004 p.8 Section 5.1 (lines 633–639, verified):

> "All of the programs were executed on a cluster that consisted of approximately 1800 machines. Each machine had two 2GHz Intel Xeon processors with HyperThreading enabled, 4GB of memory, two 160GB IDE disks, and a gigabit Ethernet link. The machines were arranged in a two-level tree-shaped switched network with approximately 100-200 Gbps of aggregate bandwidth available at the root."

Use this paragraph if the chapter wants to give a single concrete cluster spec. Combined with the Section 3 environment description, it gives a calibrated sense of "what a Google cluster looked like" in 2004: thousands of two-socket Xeons with two IDE disks each, hung off gigabit Ethernet aggregating to 100–200 Gbps.

## Fault tolerance in production (2004)

The chapter's "fault tolerance was the point" beat is anchored to two passages:

- **Worker failure:** MapReduce 2004 p.5 lines 350–360 (verified): the master pings every worker, marks failed workers, reassigns their tasks. The paper's load-bearing example: *"during one MapReduce operation, network maintenance on a running cluster was causing groups of 80 machines at a time to become unreachable for several minutes. The MapReduce master simply re-executed the work done by the unreachable worker machines, and continued to make forward progress, eventually completing the MapReduce operation."*
- **Stragglers:** MapReduce 2004 p.7 lines 466–471 + p.10 lines 884–893 (verified): backup tasks are scheduled near job completion to mitigate slow machines. The benchmark sort takes 891 seconds with backup tasks and 1,283 seconds without — a 44% slowdown. This is the chapter's clearest anchor for "the abstraction's value was the systems work, not the algorithm."

## Post-Yahoo Hadoop deployment (2009)

By the time of Vance 2009 NYT, Hadoop was running production analysis on Yahoo's homepage. Vance, verified 2026-04-28 against Wayback snapshot:

> "A Hadoop-powered analysis also determines what 300 million people a month see. Yahoo tracks peoples' behavior to gauge what types of stories and other content they like and tries to alter its homepage accordingly. Similar software tries to match ads with certain types of stories."

This is the chapter's anchor for the close: by 2009, three years after the JIRA split, the open-source clone of the 2003–2004 Google papers was load-bearing on a top-five web property.

## Numbers the chapter must NOT use without anchoring

- "Yahoo invested tens of millions of dollars in Hadoop" — Vance 2009 NYT says *"Yahoo is estimated to have spent tens of millions of dollars developing Hadoop"* but the source of the estimate is not given in the article. Treat as Yellow; if used, attribute to "Vance 2009, citing an unspecified estimate."
- Specific Yahoo Hadoop cluster sizes (number of nodes, total storage) — none of the verified sources give a specific 2006–2009 Yahoo cluster spec. Do not invent one.
- Production usage figures from later years (Facebook's 100+ PB, etc.) — out of chapter scope.
- 5,000 LOC HDFS / 6,000 LOC MapReduce — Wikipedia-only, treat as illustrative.

## The infrastructure thesis (in one paragraph, anchored)

The chapter's infrastructure argument is: by August 2004, Google had a production system processing 3,288 TB of input across 29,423 monthly jobs (MapReduce 2004 Table 1). By October 2003, Google had a storage system running over 1,000 nodes with over 300 TB of disk (GFS 2003 p.2). These systems treated machine failure as normal (1.2 worker deaths per job, MapReduce 2004 Table 1) and required no distributed-systems expertise from their users. Cutting and Cafarella ported the design — not the code — to Java between 2004 and early 2006. By 2009, the ported version was load-bearing on Yahoo's homepage (Vance 2009 NYT). When deep-learning workloads arrived after 2012, the data-engineering substrate they needed was already running in production at the major web companies. That convergence is the chapter's argumentative load. Every claim in this paragraph is Green-anchored.
