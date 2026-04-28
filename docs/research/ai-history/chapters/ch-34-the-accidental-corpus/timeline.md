# Timeline: Chapter 34 — The Accidental Corpus

Dates are tied to verified primary anchors in `sources.md`. Items with `(SECONDARY)` are derived from anchored secondary sources; items with `(BACKGROUND)` are listed for context but are out of this chapter's scope.

## Pre-history

- **1961:** Source publication year for all 500 samples in the Brown Corpus. (Brown Corpus Manual §1.)
- **February 1963:** Conference at Brown University to determine the Brown Corpus's category structure and per-category sample counts. (Brown Corpus Manual §1.)
- **1967:** Henry Kučera and W. Nelson Francis publish *Computational Analysis of Present-Day American English* (Brown University Press), the first major analytic work on the corpus. (Halevy/Norvig/Pereira 2009 reference list, ref [3]; Brown Corpus Manual §1.)
- **July 1979:** Brown Corpus Manual revised and amplified by Francis & Kučera at Brown University. The Wayback-archived version is this revision. ICAME News No. 2 (Bergen, March 1979) lists 57 published works using or referring to the Corpus by that date. (Brown Corpus Manual front matter.)

## The data famine and the empirical revival

- **1987-1993:** The "second AI Winter" period of reduced funding and confidence in symbolic-AI approaches. (Church 2011 LiLT pp.4-5, citing the Wikipedia AI-winter list as a contemporary summary.)
- **1988:** The empirical inflection point in the ACL Anthology, dated by Hall, Jurafsky, and Manning (2008) and cited by Church 2011 pp.1-2 as starting with Brown et al. 1988 and Church 1988. (Church 2011 LiLT pp.1-2.)
- **1990:** Brown, Cocke, Della Pietra et al. publish "A Statistical Approach to Machine Translation" in *Computational Linguistics* — the IBM team's foundational statistical-MT paper. (BACKGROUND; cited by Resnik 1999 §1 p.527 as the canonical citation for statistical-MT methods relying on large bilingual text.)
- **1993:** SIGDAT founded as the ACL special interest group on linguistic data and corpus-based approaches. The first Workshop on Very Large Corpora is held in 1993; this later evolves into the EMNLP conferences. (Church 2011 LiLT p.1.)
- **Early 1990s:** Church & Mercer (in their 1993 introduction to the *Computational Linguistics* special issue on Using Large Corpora) describe the one-million-word Brown Corpus as having been "considered large" only "ten years ago" — i.e., as recently as the early 1980s. (Church 2011 LiLT p.4 block-quote of Church & Mercer 1993.)

## The accidental cause

- **1980:** Berners-Lee writes Enquire at CERN, an early personal hypertext system for tracking software, people, and modules in the Proton Synchrotron control system. (Berners-Lee 1989 §"Personal Experience with Hypertext.")
- **March 1989:** Berners-Lee writes "Information Management: A Proposal" at CERN. The document's stated purpose is managing information about CERN's accelerators and experiments; the system is internally called "Mesh" at this point. The proposal does not mention AI, machine learning, or training data. (Berners-Lee 1989 prefatory header and §"Overview.")
- **1990:** Berners-Lee implements the system; renames "Mesh" to "World Wide Web" while writing the code. (Berners-Lee 1989 prefatory header note.)
- **May 1990:** Proposal redistributed unchanged apart from the date addition. (Berners-Lee 1989 prefatory header.)

## Mining the wild

- **June 1997:** Babel survey estimates 63,000 primarily non-English Web servers across 14 languages. (Resnik 1999 §1 p.527.)
- **1998:** Resnik publishes the preliminary STRAND results (referenced in Resnik 1999 as Resnik 1998). (Resnik 1999 §1 p.527.)
- **November 1998:** Resnik runs scaled-up STRAND with date-range AltaVista queries; generates 16,763 candidate page pairs over an 18-fold productivity increase, ultimately yielding 3,376 GOOD English-French pairs after filtering. (Resnik 1999 §4 p.532.)
- **1999:** Resnik publishes "Mining the Web for Bilingual Text" at ACL 1999 (P99-1068), formally reporting STRAND with language identification at 100% precision / 64.1% recall under a stricter language-ID criterion, yielding 2,491 English-French document pairs (~1.5 million words per language). (Resnik 1999 abstract p.527; §4 p.533.)

## The log-linear surprise

- **2001:** Banko and Brill at Microsoft Research publish "Scaling to Very Very Large Corpora for Natural Language Disambiguation" at ACL 2001 (P01-1005), reporting log-linear learning curves out to one billion words on confusion-set disambiguation; the worst learner trained on a billion words outperforms the best learner trained on a million. (Banko & Brill 2001 §3 Figure 1.)

## The doctrine articulated

- **September 19, 2006:** Linguistic Data Consortium releases Web 1T 5-Gram Version 1 (LDC2006T13), authored by Thorsten Brants and Alex Franz, contributed by Google Inc. — 1,024,908,267,229 tokens, ~95 billion sentences, 13.6 million unigrams, ~1.18 billion 5-grams. (LDC LDC2006T13 catalog page.)
- **June 2007:** Brants, Popat, Xu, Och, and Dean publish "Large Language Models in Machine Translation" at EMNLP-CoNLL 2007 in Prague (D07-1090), describing distributed-LM infrastructure trained on up to 2 trillion tokens with up to 300 billion n-grams, and introducing "Stupid Backoff" smoothing. (Brants et al. 2007 abstract p.858.)
- **March/April 2009:** Halevy, Norvig, and Pereira publish "The Unreasonable Effectiveness of Data" in *IEEE Intelligent Systems* vol.24 no.2, pp.8-12, articulating the "follow the data" / "simple models and a lot of data trump more elaborate models based on less data" doctrine. (Halevy/Norvig/Pereira 2009 pp.8-12.)
- **October 2011:** Church publishes "A Pendulum Swung Too Far" in *Linguistic Issues in Language Technology* vol.6 issue 5, framing the empirical revival's success as a pendulum mid-swing whose dominance risked marginalising rationalist methods. (Church 2011 LiLT pp.1-3.)

## After this chapter (forward-pointers, sparse)

- **Late 2000s:** The new bottleneck is no longer text data but the compute and infrastructure to actually do anything with it — see Ch37 for how Google's data infrastructure (GFS, MapReduce, Bigtable) made trillion-token LMs operationally tractable in the first place.
- **2009-2012:** ImageNet and the rise of large vision corpora (Ch39, Ch43); Mechanical Turk and human annotation at scale (Ch38) — out of scope here.
