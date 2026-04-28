# Infrastructure Log: Chapter 34 — The Accidental Corpus

This file records the computing infrastructure each scene relied on, with citations to anchored sources. The chapter's argument is partly infrastructural — what changed between 1989 and 2009 was the *substrate*, not the algorithms — so this log matters.

## Scene 1: The Data Famine

- **Brown Corpus (1961 source texts; original publication 1967; revised Manual 1979).** 1,014,312 words across 500 samples of 2,000+ words each, drawn from edited American English prose published in the United States in 1961. Distribution medium at original release: magnetic tape; later distributions included CD-ROM and digital download via the LDC and ICAME. Tagged versions (1979) added part-of-speech annotations. (Brown Corpus Manual §1 Contents and §6 Basic Technical Information; verified via Wayback snapshot `20080309235836`.)

- **Selection categories (1963 conference at Brown University).** The corpus was structured into Press: Reportage / Editorial / Reviews; Religion; Skills and Hobbies; Popular Lore; Belles-Lettres; Miscellaneous; Learned; Fiction (General, Mystery & Detective, Science, Adventure & Western, Romance & Love Story, Humor) — assignments balanced by proportional 1961 publication amounts. (Brown Corpus Manual §1.)

- **Compute substrate for early statistical NLP (early 1990s).** Mainframes and Unix workstations; corpus sizes constrained by storage and parsing speed, not by network bandwidth. Church 2011 p.4 quotes Church & Mercer 1993 noting that "many locations have samples of text running into the hundreds of millions or even billions of words" — but accessible-to-individual-experiments scale was still typically millions. (Church 2011 LiLT p.4 block-quote of Church & Mercer 1993.)

## Scene 2: The CERN Memo

- **CERN's information environment in 1989.** Multiple incompatible systems (VM/CMS, Macintosh, VAX/VMS, Unix), with information distributed across institutional silos and no unifying linkage layer. The proposal explicitly lists "Heterogeneity" as one of CERN's clear practical requirements: "Access is required to the same data from different types of system." (Berners-Lee 1989 §"CERN Requirements.")

- **Berners-Lee's Enquire (1980).** Personal predecessor to the Web proposal. Ran on a multi-user system, allowed many people to access the same data, lacked graphical hyperlinks. Used to track "people, groups, experiments, software modules and hardware devices." (Berners-Lee 1989 §"Personal Experience with Hypertext.")

- **What the proposal did *not* anticipate.** No mention of full-text indexing, search engines, web crawlers, training corpora, or machine learning. The "Bells and Whistles" requirement explicitly limits ambitions: "Storage of ASCII text, and display on 24x80 screens, is in the short term sufficient, and essential. Addition of graphics would be an optional extra with very much less penetration for the moment." (Berners-Lee 1989 §"CERN Requirements.")

## Scene 3: Mining the Wild

- **AltaVista (Resnik 1999, June 1997 Babel survey baseline).** Web search engine used by STRAND for candidate-page generation. Resnik's pipeline relied on AltaVista's index size and on its "Advanced Search" date-range feature (which he exploited to break the 1,000-hit-per-query limit by issuing per-day mutually exclusive queries). (Resnik 1999 §2 p.528 and §4 p.532.)

- **STRAND structural-alignment substrate.** Documents reduced to a linear sequence of HTML markup tokens (`[BEGIN:TITLE]`, `[Chunk: 24]`, `[END:TITLE]`) with chunk-length numerical features. Alignment performed by a "standard, widely available dynamic programming algorithm" — Resnik footnote 1 p.528: "Known to many programmers as `diff`." (Resnik 1999 §2 p.528.)

- **Language-identification corpus.** Character 5-gram models for language identification trained on 100k characters per language from the European Corpus Initiative (ECI), available from the Linguistic Data Consortium (LDC). (Resnik 1999 §3 p.530.)

- **Babel survey (June 1997) infrastructure baseline.** "On the order of 63,000 primarily non-English Web servers, ranging over 14 languages." (Resnik 1999 §1 p.527 citing the Babel survey at `http://www.isoc.org/`.) The chapter should cite this as the *contemporary* sense of how many non-English servers existed when Resnik began his work — not as a current figure.

## Scene 4: The Log-Linear Surprise

- **Banko-Brill 1-billion-word training corpus.** Composition: news articles, scientific abstracts, government transcripts, literature, and other varied forms of prose. Construction method: probabilistic sampling of sentences from different sources weighted by source size, to avoid training biases from concatenation order. Test set held out: 1 million words of Wall Street Journal text (no WSJ in training corpus). Training cutoff points: 10⁶, 10⁷, 10⁸, 10⁹ words. (Banko & Brill 2001 §3 PDF p.1; Tables 1 and 3.)

- **Banko-Brill compute scale.** The paper reports running four learners (winnow, perceptron, naive Bayes, memory-based) at six logarithmic cutoff points across ten confusion sets. Figure 2 shows the "size of learned representations" (memory cost) growing roughly linearly with training corpus size — by 10⁹ words the winnow representation is ~10⁵-10⁶ entries and the memory-based learner ~10⁵-10⁶. The paper notes that "for some applications, this is not necessarily a concern. But for others, where space comes at a premium, obtaining the gains that come with a billion words of training data may not be viable without an effort made to compress information." (Banko & Brill 2001 §3 Figure 2 PDF p.2.)

## Scene 5: The Doctrine Articulated

- **LDC Web 1T 5-Gram Version 1 (LDC2006T13, released September 19, 2006).** Source: text taken from publicly accessible Web pages; encoding auto-detected and normalized to UTF-8; tokenization similar to Penn Treebank Wall Street Journal tokenization with hyphenation, slashed-numbers, URL/email exceptions. Distribution: 24 GB compressed gzip text files. Counts: 1,024,908,267,229 tokens; 95,119,665,584 sentences; 13,588,391 unigrams; 314,843,401 bigrams; 977,069,902 trigrams; 1,313,818,354 fourgrams; 1,176,470,663 fivegrams. (LDC LDC2006T13 catalog page.)

- **Brants et al. 2007 distributed-LM infrastructure.** Trained on up to 2 trillion tokens, producing language models with up to 300 billion n-grams. The architecture serves smoothed probabilities (not raw counts), enabling exactly one worker contact per n-gram for simple smoothing techniques like Stupid Backoff — in contrast to suffix-array approaches that store one sub-corpus per worker and require contacting all workers for each n-gram request. (Brants et al. 2007 §1 p.858; §"Both approaches differ from ours" comparison paragraph p.858.)

- **What the chapter does *not* dwell on (forward-pointer to Ch37).** The trillion-token LM was operationally tractable because of GFS (Google File System), MapReduce, and Bigtable — Google's internal data infrastructure — which made the per-worker storage and the parallel n-gram extraction possible. Ch37 covers that substrate. Ch34 only notes that the doctrine of "follow the data" presupposes infrastructure not every researcher had.

## Scope contrast

| Substrate | Scene | Approximate size | Distribution |
|---|---|---|---|
| Brown Corpus | 1 | 1,014,312 words | Magnetic tape, later CD-ROM and LDC download |
| Birmingham/COBUILD (referenced in Church 2011 p.4 as a 1980s alternative) | 1 | ~hundreds of millions of words | Academic distribution |
| Resnik 1999 STRAND output (English-French parallel pairs) | 3 | 2,491 documents, ~1.5M words/language | Research output |
| Banko-Brill 2001 1-billion-word corpus | 4 | 10⁹ words | Microsoft-internal; not publicly released |
| Web 1T 5-Gram (LDC2006T13) | 5 | 1.02 trillion tokens | LDC member download (academic) |
| Brants et al. 2007 internal Google LM | 5 | 2 trillion tokens, 300B n-grams | Google-internal |
| Halevy 2009 framing scale | 5 | "a million times larger" than Brown | Doctrinal |

The vertical jump from millions (Scene 1) to trillions (Scene 5) over twenty years is the chapter's infrastructural spine.
