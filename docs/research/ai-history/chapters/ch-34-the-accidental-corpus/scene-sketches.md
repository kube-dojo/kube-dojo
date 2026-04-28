# Scene Sketches: Chapter 34 — The Accidental Corpus

Five scenes mapped 1:1 to the Prose Capacity Plan layers in `brief.md`. Each scene lists what is dramatically present, what is anchored, what must not be drafted without further research, and which sources.md entries it depends on.

---

## Scene 1: The Data Famine — what "large corpus" still meant in the early 1990s

**Setting.** Early 1990s, just before web-scale data was available. The empirical revival in NLP is underway — Church 2011 dates its inflection point to 1988 — and SIGDAT founds its Workshop on Very Large Corpora in 1993. Researchers are explicitly arguing that the data ceiling matters.

**Anchored beats.**
- The Brown Corpus is *the* baseline: 1,014,312 words from 1961, 500 samples of ~2,000 words each, distributed via tape and later CD-ROM. (Brown Corpus Manual §1; sources.md row "The Brown Corpus comprises 1,014,312 words…".)
- Church & Mercer's 1993 framing — quoted by Church 2011 p.4 — describes the one-million-word Brown Corpus as having been "considered large" only ten years earlier. (sources.md row "In the early 1990s, the one-million-word Brown Corpus was still cited…".)
- The empirical revival was motivated not by abundance but by *pragmatism*: the field was emerging from the second AI Winter (1987-93), and incremental, deliverable approaches gained traction precisely because grand promises had failed. (sources.md row "The first AI Winter spanned 1974-80…".)
- The data ceiling was a binding constraint: statistical methods were viable in principle but starved of training material in practice. (Church 2011 LiLT pp.1-3 pendulum discussion.)

**What this scene must NOT do.**
- Do not assert that statistical NLP did not exist before 1989. Church 2011's pendulum places empiricism as already-revived in the early 1990s.
- Do not invent a specific researcher's frustrated quote about not having enough data. Church and Norvig (in Halevy 2009) gesture at the felt scarcity, but specific frustrated-researcher dialogue is not anchored.
- Do not cite a Jelinek "every time I fire a linguist" quote. The quote is widely repeated but its provenance is not anchored in the sources gathered for this chapter; treat as Red until separately verified.

**Source dependencies.** Brown Corpus Manual; Halevy/Norvig/Pereira 2009 p.8; Church 2011 LiLT pp.1, 3, 4; Spärck Jones 2005 J05-1001 abstract.

**Word budget.** 600-900 words.

---

## Scene 2: The CERN Memo — March 1989

**Setting.** CERN, March 1989. Berners-Lee, working in the DD division, drafts an internal information-management proposal. The document is short (a few pages of prose plus diagrams). The system has no name yet — internally Berners-Lee uses "Mesh." The proposal will not be funded as a Web project until 1990.

**Anchored beats.**
- The proposal's stated motive is institutional, not technological: "This proposal concerns the management of general information about accelerators and experiments at CERN." (Berners-Lee 1989 §"Overview".)
- The actual problem named: "the high turnover of people. When two years is a typical length of stay, information is constantly being lost." (Berners-Lee 1989 §"Losing Information at CERN".)
- The system is called "Mesh" in 1989; Berners-Lee renames it "World Wide Web" while writing the code in 1990. The renaming note is itself part of the HTMLized version's prefatory header. (Berners-Lee 1989 prefatory header.)
- The proposal's CERN Requirements list — Remote access; Heterogeneity (VM/CMS, Macintosh, VAX/VMS, Unix); Non-Centralisation; Access to existing data; Private links; Bells and Whistles (ASCII text on 24x80 screens "is in the short term sufficient, and essential") — is explicitly engineered for *information management*, not for AI. (Berners-Lee 1989 §"CERN Requirements".)
- The proposal does not mention AI, machine learning, training data, or corpora. (sources.md row "Tim Berners-Lee's March 1989 proposal…does not mention AI, machine learning, or training data.")

**What this scene must NOT do.**
- Do not present Berners-Lee as having predicted the web's role as an AI corpus. The 1989 document is silent on AI; later interviews are out of scope.
- Do not romanticise CERN's "open culture" as the cause. The actual motive is more prosaic: physicists leave, knowledge gets lost, somebody needs a system.
- Do not extrapolate to NCSA Mosaic, Netscape, or the dot-com boom. Those are real but out of this chapter's scope.

**Source dependencies.** Berners-Lee 1989 (w3.org HTMLization).

**Word budget.** 600-900 words.

---

## Scene 3: Mining the Wild — Resnik 1999 and the first formal proof

**Setting.** Late 1990s. The Web has gone mainstream; AltaVista is the dominant search engine. Resnik, at the University of Maryland, writes STRAND with DoD/DARPA funding (not Microsoft or Google money). The question: can the open Web be mined for parallel translation pairs without a librarian?

**Anchored beats.**
- The pre-Web parallel-text resources were "subject to such limitations as licensing restrictions, usage fees, restricted domains or genres, and dated text (such as 1980's Canadian politics)" — the Hansard problem. (Resnik 1999 §1 p.527.)
- The STRAND pipeline: AltaVista candidate generation → structural diff alignment → character-n-gram language identification. (Resnik 1999 §2 p.528 Figure 1.)
- The structural-alignment trick: reduce both pages to linear sequences of HTML markup tokens with chunk-length numerical features; align using diff. The chunk-length linear correlation is the load-bearing observation. (Resnik 1999 §2 p.528-529.)
- Formal evaluation methodology: two independent native-speaker judges working in parallel; Cohen's κ for inter-judge agreement; precision/recall computed against the *intersection* of judge agreement to surface only the most reliable examples. (Resnik 1999 §3-4 pp.530-531.)
- Numerical results, in order: English-Spanish 92.1% precision / 47.3% recall; English-French initial 79.5% / 70.3%; English-French stricter 100% / 64.1% with 2,491 documents (~1.5M words/language). (Resnik 1999 §4 pp.531-533.)
- Resnik's conclusion: the work "places acquisition of parallel text from the Web on solid empirical footing." (Resnik 1999 §5 p.533.)

**What this scene must NOT do.**
- Do not generalize STRAND to all NLP tasks. STRAND works because parallel HTML pages exist on the Web with structural similarity — a property of bilingual organisation choices, not of all annotation problems.
- Do not credit Resnik with inventing web mining. Earlier work existed; STRAND's contribution is the formal evaluation and the language-identification filter.
- Do not skip the DoD/DARPA funding footnote. The institutional pattern (Microsoft, Google in later scenes; DoD here) matters for the chapter's "industry vs. academy" conflict note.

**Source dependencies.** Resnik 1999 (ACL P99-1068).

**Word budget.** 800-1,100 words.

---

## Scene 4: The Log-Linear Surprise — Banko & Brill 2001

**Setting.** Microsoft Research, Redmond, around 2000-2001. Banko and Brill are working on grammar-checking technology. The empirical revival is fully underway. Specialized learners are being benchmarked against each other on small fixed datasets. Banko and Brill ask a different question.

**Anchored beats.**
- Pragmatic motivation: "Given a fixed amount of time, we considered what would be the most effective way to focus our efforts in order to attain the greatest performance improvement." Options: better algorithms, new techniques, more sophisticated features, *or* simply more data. (Banko & Brill 2001 §3 PDF p.1.)
- Test problem: confusion-set disambiguation. Concrete examples: `{principle, principal}`, `{then, than}`, `{to, two, too}`, `{weather, whether}`. Why this problem: labels are surface-apparent — the answer is in the source text — so labeled training data is essentially free. (Banko & Brill 2001 §2 PDF p.1.)
- Training corpus construction: 1 billion words from "news articles, scientific abstracts, government transcripts, literature and other varied forms of prose"; probabilistic sampling weighted by source size to avoid concatenation bias. Test set: 1 million words of Wall Street Journal text, held out from training. Cutoff points: 10⁶, 10⁷, 10⁸, 10⁹ words. (Banko & Brill 2001 §3 PDF p.1.)
- Four learners: winnow (Roth's implementation, acknowledged in fn.1), perceptron (Roth's implementation), naive Bayes, memory-based. Standard feature set: word window plus collocations with words and parts-of-speech. The memory-based learner used only the word before and word after as features. (Banko & Brill 2001 §3 PDF p.1.)
- Result: Figure 1 learning curves are "log-linear even out to one billion words"; "none of the learners tested is close to asymptoting in performance at the training corpus size commonly employed by the field." (Banko & Brill 2001 §3 PDF p.2.)
- The chapter's load-bearing claim — at 10⁹ words, all four learners reach test accuracies that exceed the *best* learner's accuracy at 10⁶ words — is read off Figure 1. The exact numerical gaps are visible in the figure (≈0.96-0.97 at 10⁹ vs ≈0.85-0.88 at 10⁶). (Banko & Brill 2001 §3 Figure 1 PDF p.2.)
- Cost note (Figure 2): the size of learned representations grows roughly linearly with training corpus size — at 10⁹ words, both winnow and memory-based learners hold ~10⁵-10⁶ representation entries. "For some applications, this is not necessarily a concern. But for others, where space comes at a premium, obtaining the gains that come with a billion words of training data may not be viable without an effort made to compress information." (Banko & Brill 2001 §3 Figure 2 PDF p.2.)
- §4 voting: above ~10⁶ words "little is gained by voting, and indeed on the largest training sets voting actually hurts accuracy." (Banko & Brill 2001 §4 PDF p.3.)
- §5 active learning and weakly supervised learning experiments: at 10⁹ supervised, accuracy on `{then, than}` is 0.9878 and on `{among, between}` is 0.9021; the unsupervised methods plateau and then decline as more data is added. The chapter must note this — unsupervised learning on the same corpus did *not* match supervised performance. (Banko & Brill 2001 §5.2 Table 3 PDF p.6.)
- Conclusion: "a logical next step for the research community would be to direct efforts towards increasing the size of annotated training collections, while deemphasizing the focus on comparing different learning techniques trained only on small training corpora." (Banko & Brill 2001 §6 PDF p.7.)

**What this scene must NOT do.**
- Do not flatten Banko-Brill's conclusion into "more data beats better algorithms." Their actual claim is narrower and more specific.
- Do not skip §5. The unsupervised plateau-and-decline result is the part that complicates the heroic reading; the chapter must include it.
- Do not invent quotes from Banko or Brill about "scaling laws." The paper's language is specific: "log-linear" and "no learner asymptotes." Use the paper's words.

**Source dependencies.** Banko & Brill 2001 (ACL P01-1005).

**Word budget.** 900-1,200 words.

---

## Scene 5: The Doctrine Articulated — 2006-2011

**Setting.** Google research, 2006-2009. Halevy, Norvig, and Pereira write a short essay for *IEEE Intelligent Systems* that crystallises a lesson the field has been absorbing through Banko-Brill, Brants-Franz, and dozens of similar results. Church responds two years later in LiLT.

**Anchored beats.**
- The Web 1T 5-Gram release as institutional moment: September 19, 2006; Brants and Franz at Google, distributed through LDC; 1.024 trillion tokens; ~95 billion sentences; 1.18 billion 5-grams. The corpus is released *to academic researchers*, not kept proprietary. (LDC LDC2006T13 catalog page.)
- Brants et al. 2007 distributed-LM scale: 2 trillion tokens, 300 billion n-grams, single-pass decoding, Stupid Backoff smoothing approaching Kneser-Ney quality as data grows. The paper documents the operational substrate — not just a benchmark, but a system used in production-style MT. (Brants et al. 2007 abstract p.858.)
- Halevy/Norvig/Pereira 2009 "Unreasonable Effectiveness of Data" core argument:
  - The Brown Corpus had a million words; the new corpus is a million times larger. (p.8.)
  - First lesson: "use available large-scale data rather than hoping for annotated data that isn't available." (p.8.)
  - Doctrine: "But invariably, simple models and a lot of data trump more elaborate models based on less data." (p.9.)
  - Caveat 1 (the Hays-Efros example): "With a corpus of thousands of photos, the results were poor. But once they accumulated millions of photos, the same algorithm performed quite well." Threshold of sufficient data, not magic. (p.9.)
  - Caveat 2 (rare events): "throwing away rare events is almost always a bad idea, because much Web data consists of individually rare but collectively frequent events." (p.9.)
  - Caveat 3 (semantic interpretation remains hard): the Semantic Web vs. semantic interpretation discussion is the meat of the article's middle (pp.10-11) and qualifies the doctrine substantially.
  - Close: "follow the data. Choose a representation that can use unsupervised learning on unlabeled data, which is so much more plentiful than labeled data." (p.12.)
- Church 2011's caveat: the empirical revival has succeeded so completely that the field risks forgetting the rationalist critiques — Pierce-Chomsky-Minsky positions are no longer in popular textbooks; "PCM's arguments were controversial at the time and remain so because they caused a number of severe funding winters." (Church 2011 LiLT pp.5-6.)
- Church's pendulum oscillation: 1950s Empiricism (Shannon, Skinner, Firth, Harris) → 1970s Rationalism (Chomsky, Minsky) → 1990s Empiricism (IBM Speech Group, AT&T Bell Labs) → 2010s "A Return to Rationalism?" (Church 2011 LiLT p.3.)

**What this scene must NOT do.**
- Do not draft the Halevy article as triumphalism. The article itself is careful, with multiple caveats; the chapter should preserve them.
- Do not draft the Church paper as a reactionary backlash. Church is one of the people who *started* the empirical revival; the paper is partly autobiographical reflection on what the movement cost.
- Do not forward-ref deep learning, transformers, or large language models. Those are subsequent chapters; this chapter ends in 2011 with the doctrine articulated and immediately questioned.

**Source dependencies.** LDC LDC2006T13; Brants et al. 2007 (D07-1090); Halevy/Norvig/Pereira 2009; Church 2011 LiLT.

**Word budget.** 800-1,100 words.

---

## Total budget cross-check

Layer budgets sum to 3,700-5,200 words, matching the Prose Capacity Plan total in `brief.md`. Word Count Discipline label: `4k-7k stretch`. If layers begin running short on anchored material, cap the chapter at the lower-bound length rather than padding.
