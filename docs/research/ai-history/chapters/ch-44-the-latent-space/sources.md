# Sources: Chapter 44 — The Latent Space

## Verification Key

- **Green**: claim has a verified page, section, DOI+page, or stable identifier anchor.
- **Yellow**: source exists and is relevant, but the specific claim is not yet page-located or needs stronger independent confirmation.
- **Red**: do not draft; no verifiable anchor yet or the legacy claim is misleading.

## Anchor Index

| ID | Source | Anchors verified for this contract |
|---|---|---|
| S1 | Zellig S. Harris, "Distributional Structure," *WORD* 10:2-3 (1954), pp. 146-162. DOI: `10.1080/00437956.1954.11659520`. Open scan: `https://www.its.caltech.edu/~matilde/ZelligHarrisDistributionalStructure1954.pdf` | **Green** for distributional description without meaning/history intrusion and definition of distribution/environment on p.146; distributional statements covering language material and networks of relative occurrence on p.147. Verified via web PDF text extraction, 2026-04-29. |
| S2 | Scott Deerwester, Susan T. Dumais, George W. Furnas, Thomas K. Landauer, Richard Harshman, "Indexing by Latent Semantic Analysis," *JASIS* 41:6 (1990), pp. 391-407. DOI: `10.1002/(SICI)1097-4571(199009)41:6<391::AID-ASI1>3.0.CO;2-9`. | **Green** for abstract-level claim on p.391 that LSA used singular-value decomposition of a term-document matrix into about 100 orthogonal factors and represented documents/queries as factor-weight vectors. Verified from open bibliographic/abstract mirrors; full publisher PDF is access-limited. |
| S3 | Yoshua Bengio, Rejean Ducharme, Pascal Vincent, Christian Jauvin, "A Neural Probabilistic Language Model," *JMLR* 3 (2003), pp. 1137-1155. URL: `https://www.jmlr.org/papers/volume3/bengio03a/bengio03a.pdf` | **Green** for curse of dimensionality and 100,000-word/10-word example on p.1137; distributed word feature vector recipe on p.1139; mapping C and neural model on pp.1141-1142; AP News training took about 3 weeks on 40 CPUs and perplexity results on pp.1148-1149; conclusion that distributed representations fight the curse and computation/memory scale linearly, not exponentially, on pp.1152-1153. Verified via web PDF text extraction, 2026-04-29. |
| S4 | Tomas Mikolov, Kai Chen, Greg Corrado, Jeffrey Dean, "Efficient Estimation of Word Representations in Vector Space," arXiv:1301.3781v3 (2013). URL: `https://arxiv.org/pdf/1301.3781` | **Green** for two model architectures and less-than-a-day / 1.6B-word abstract claim on p.1; atomic word-index problem on p.1; CBOW and Skip-gram definitions on pp.3-4; Figure 1 architecture caption on p.4; analogy task and vector arithmetic method on pp.5-6; Google News 6B-token/1M-vocabulary experiment on p.6; architecture comparison and training-time tables on pp.7-8; DistBelief 50-100 replicas and Table 6 on p.8; examples of learned relationships and conclusion on pp.9-10. Verified via web PDF text extraction, 2026-04-29. |
| S5 | Tomas Mikolov, Wen-tau Yih, Geoffrey Zweig, "Linguistic Regularities in Continuous Space Word Representations," NAACL-HLT 2013, pp. 746-751. ACL Anthology ID `N13-1090`. URL: `https://aclanthology.org/N13-1090.pdf` | **Green** for King-Man+Woman near Queen and "almost 40%" syntactic analogy result on p.746; distributed representations vs discrete n-grams on p.746; RNN vectors trained on 320M words and 82k vocabulary on p.749; vector offset method on pp.748-749; SemEval result outperforming previous system on pp.749-750; conclusion on p.750. Verified via web PDF text extraction, 2026-04-29. |
| S6 | Tomas Mikolov, Ilya Sutskever, Kai Chen, Greg Corrado, Jeffrey Dean, "Distributed Representations of Words and Phrases and their Compositionality," *NIPS 2013*. URL: `https://proceedings.neurips.cc/paper_files/paper/2013/file/9aa42b31882ec039965f3c4923ce901b-Paper.pdf` | **Green** for Skip-gram efficiency and optimized single-machine implementation training on more than 100B words/day on p.1; extensions via subsampling, negative sampling, and phrase vectors on pp.1-2; Skip-gram objective and full-softmax cost proportional to vocabulary size on pp.2-3; negative sampling objective on pp.3-4; subsampling rationale and formula on pp.4-5; phrase analogy examples and 72% phrase dataset result on p.5. Verified via web PDF text extraction, 2026-04-29. |
| S7 | Daniel Jurafsky and James H. Martin, *Speech and Language Processing*, 3rd ed. draft, Chapter 5 "Embeddings," August 24, 2025. URL: `https://stanford.edu/~jurafsky/slp3/5.pdf` | **Green** as secondary synthesis for distributional hypothesis on p.1; vector semantics and embeddings as points in multidimensional space on pp.5-6; sparse vector scale and cosine on pp.7-9; word2vec/SGNS explanation and static embedding caveat on pp.10-15; semantic properties and analogy caveats on pp.17-18; historical notes on p.22; references on pp.25-27. Verified via web PDF text extraction, 2026-04-29. |

## Primary And Secondary Sources

| Source | Type | Use | Verification |
|---|---|---|---|
| Harris 1954, "Distributional Structure" | Primary intellectual lineage | Establishes that language can be described in terms of relative occurrence/distribution before neural embeddings. | **Green** via S1, pp.146-147. |
| Deerwester et al. 1990, "Indexing by Latent Semantic Analysis" | Primary technical precursor | Shows the term "latent semantic" tradition and SVD factor-space representation before neural word embeddings. | **Green** for abstract/page-level claims via S2, p.391; Yellow for deeper experimental details until full pages are extracted. |
| Bengio et al. 2003, "A Neural Probabilistic Language Model" | Primary technical precursor | Anchors the neural distributed-word-vector model and its computational cost. | **Green** via S3, pp.1137, 1139, 1141-1142, 1148-1149, 1152-1153. |
| Mikolov et al. 2013, "Efficient Estimation..." | Primary Word2Vec paper | Anchors CBOW, Skip-gram, analogy benchmark, Google-scale training, and DistBelief/single-machine comparisons. | **Green** via S4, pp.1, 3-10. |
| Mikolov, Yih, Zweig 2013, "Linguistic Regularities..." | Primary analogy paper | Anchors vector offsets, King-Man+Woman near Queen, syntactic and semantic regularity evaluation. | **Green** via S5, pp.746-750. |
| Mikolov et al. 2013, "Distributed Representations..." | Primary optimization/extension paper | Anchors negative sampling, subsampling, phrase vectors, and efficiency claims. | **Green** via S6, pp.1-5. |
| Jurafsky and Martin 2025, Chapter 5 "Embeddings" | Secondary textbook synthesis | Confirms the lineage, terminology, static embedding caveat, and analogy limits. | **Green** via S7, pp.1, 5-18, 22. |

## Scene-Level Claim Table

| Claim | Scene | Primary Anchor | Independent Confirmation | Status | Notes |
|---|---|---|---|---|---|
| Harris defined a distributional account of language in terms of occurrence of parts relative to other parts and stated that this description could proceed without history or meaning. | 1 | S1, p.146 | S7, p.1 | **Green** | Use as lineage, not as a claim that Harris predicted neural embeddings. |
| Harris defined the distribution of an element as the sum of its environments/co-occurrents. | 1 | S1, p.146 | S7, p.1 | **Green** | Supports the "context as evidence" opening. |
| LSA used SVD on a term-document matrix to produce a lower-dimensional latent semantic factor space for retrieval. | 1 | S2, p.391 abstract | S7, references/history pp.22, 25 | **Green** | Green only at abstract level; do not over-narrate experiments. |
| Bengio et al. framed language modeling as a curse-of-dimensionality problem, giving the example of 10 words from a 100,000-word vocabulary implying roughly 10^50 possible sequences. | 2 | S3, p.1137 | S7, pp.10, 22 | **Green** | Strong technical setup. |
| Bengio et al. proposed learning a distributed word feature vector for each vocabulary word while learning the probability function over word sequences. | 2 | S3, p.1139 | S4, pp.1-2 | **Green** | Anchor the move from discrete symbols to learned vectors. |
| Bengio et al.'s model used a mapping C from each vocabulary item to a real vector and represented C as a free-parameter matrix. | 2 | S3, pp.1141-1142 | S7, pp.10-12 | **Green** | Infrastructure-level anchor for lookup-table embeddings. |
| Bengio et al. reported AP News training of only 5 epochs taking approximately three weeks using 40 CPUs. | 2 | S3, p.1148 | S4, pp.2-3 | **Green** | Use to explain why computational simplification mattered. |
| Bengio et al. concluded that the model shifted the difficulty to more computation while keeping computation and memory scaling linear rather than exponential with conditioning variables. | 2 | S3, pp.1152-1153 | S4, pp.2-3 | **Green** | Good bridge into Word2Vec's efficiency story. |
| Mikolov et al. said many NLP systems treated words as atomic vocabulary indices with no similarity between words. | 3 | S4, p.1 | S7, pp.1, 5 | **Green** | Use as the chapter's "one-hot/index" critique. |
| "Efficient Estimation" introduced two architectures for continuous vector representations, CBOW and Skip-gram. | 3 | S4, pp.1, 3-4 | S7, pp.10-12 | **Green** | Title-level Word2Vec anchor. |
| CBOW predicts the current word from surrounding context, while Skip-gram predicts surrounding words from the current word. | 3 | S4, pp.3-4, Figure 1 p.4 | S7, pp.10-12 | **Green** | Phrase this as model objective, not cognition. |
| The paper's complexity comparison says the new log-linear models removed the non-linear hidden layer to reduce computational complexity and train on more data. | 3 | S4, p.3 | S7, p.22 | **Green** | Key design tradeoff. |
| The "Efficient Estimation" experiments used a Google News corpus of about 6B tokens and a restricted vocabulary of 1M most frequent words. | 3 | S4, p.6 | S6, pp.4-5 | **Green** | Infrastructure anchor. |
| In one-CPU experiments, Table 5 reported 300-dimensional CBOW on 783M words in about 1 day and 300-dimensional Skip-gram on 783M words in about 3 days. | 3 | S4, p.7 | S6, p.1 | **Green** | Avoid "standard CPUs/GPUs"; GPU is not anchored. |
| In DistBelief experiments, Mikolov et al. used 50 to 100 replicas and reported CBOW/Skip-gram models over 6B words with training times measured in days x CPU cores. | 3 | S4, p.8 | S4, p.3 | **Green** | Good infrastructure detail, but "data center machines shared with production tasks" should be phrased carefully. |
| "Linguistic Regularities" reported that King-Man+Woman produced a vector very close to Queen and that syntactic analogy questions were answered almost 40% correctly. | 4 | S5, p.746 | S7, pp.17-18 | **Green** | This is the safer anchor for the famous example. |
| The vector offset method assumes relationships are present as offsets so word pairs sharing a relation have a roughly constant vector offset. | 4 | S5, pp.748-749 | S7, pp.17-18 | **Green** | Do not say "perfectly mirrors." |
| The syntactic analogy test set in "Linguistic Regularities" had 8,000 questions; the semantic test used SemEval-2012 Task 2 with 69 test relations. | 4 | S5, pp.747-748 | S7, pp.17-18 | **Green** | Useful to make the scene empirical rather than magical. |
| The RNN vectors in "Linguistic Regularities" were trained on 320M words of Broadcast News with an 82k vocabulary. | 4 | S5, p.749 | S4, p.7 | **Green** | Keeps the analogy scene historically before full Word2Vec scale. |
| "Efficient Estimation" built a broader semantic-syntactic test set with 8,869 semantic and 10,675 syntactic questions. | 4 | S4, p.6 | S7, pp.17-18 | **Green** | Pair with Table 1 examples on S4 pp.5-6. |
| "Efficient Estimation" Table 8 included examples like Paris-France+Italy=Rome and other relation families, but the paper noted room for improvement. | 4 | S4, pp.9-10 | S7, pp.17-18 | **Green** | Corrects "exactly lands on Queen" tone. |
| The NIPS 2013 paper introduced extensions improving vector quality and speed: frequent-word subsampling, negative sampling, and phrase vectors. | 5 | S6, pp.1-2 | S7, pp.10-15 | **Green** | The strongest optimization layer. |
| The NIPS 2013 paper explained that full softmax cost is proportional to vocabulary size, often 10^5 to 10^7 terms. | 5 | S6, pp.2-3 | S7, pp.10-15 | **Green** | Useful for infrastructure explanation. |
| Negative sampling replaced each Skip-gram objective term with a binary discrimination objective using k noise samples. | 5 | S6, pp.3-4 | S7, pp.12-15 | **Green** | Phrase at accessible level. |
| Subsampling frequent words was presented as a way to counter imbalance from extremely common words and produced several-times speed improvements plus better accuracy. | 5 | S6, pp.4-5 | S7, pp.12-15 | **Green** | Anchor the "the/a/in" infrastructure trick. |
| The NIPS paper reported an optimized single-machine implementation could train on more than 100B words in one day. | 5 | S6, p.1 | S4, pp.7-8 | **Green** | Strong but source-specific; do not generalize to all implementations. |
| The NIPS paper treated phrases as individual tokens and reported 72% accuracy on a phrase analogy dataset. | 5 | S6, p.5 | S7, pp.10-15 | **Green** | Useful for "limits of one word = one point" close. |
| Jurafsky and Martin characterize word2vec embeddings as static embeddings: one fixed embedding per word in the vocabulary, unlike later contextual embeddings. | 5 | S7, pp.10-11 | S3, p.1151 on single point/polysemy | **Green** | Boundary with Ch45/transformers. |
| The exact date and packaging history of the public word2vec code release is July 2013. | 5 | Google Code archive not extracted in this session | Wikipedia/common secondary memory | Yellow | Needs archive page or commit/release anchor before Green. |
| The Google News corpus composition behind the 6B-token training set is fully specified in the 2013 papers. | 3 | S4, p.6 says "Google News corpus"; composition not specified | None | Yellow | Do not describe corpus sources beyond "Google News corpus." |
| Word2Vec became the default embedding baseline across NLP within months of publication. | 5 | None page-located | S7 textbook synthesis implies importance; citation history not extracted | Yellow | Needs citation/adoption evidence if a prose scene wants uptake. |
| GloVe, FastText, and later contextual embeddings are the direct successors in a neat linear sequence. | 5 | S7, pp.15, 10-11 | Primary papers not extracted here | Yellow | The lineage is useful but too simplified; use as sparse pointers only. |
| The "King-Man+Woman=Queen" result was discovered in a particular Google lab moment. | 4 | None | None | Red | No lab scene, no dialogue, no eureka moment. |
| Word2Vec "perfectly mirrors" semantic and syntactic relationships. | 4 | Contradicted by S4 p.10 and S7 pp.17-18 caveats | None | Red | Replace with "often exposes useful regularities; accuracy has limits." |
| Word2Vec training depended on GPUs. | 3, 5 | None in extracted papers; papers emphasize CPUs, DistBelief, and single-machine implementations | None | Red | Do not mention GPUs unless a later anchor is found. |

## Page Anchor Worklist

### Done

- Harris 1954: pp.146-147 via open Caltech PDF.
- Bengio et al. 2003: pp.1137, 1139, 1141-1142, 1148-1149, 1152-1153 via JMLR PDF.
- Mikolov et al. 2013 "Efficient Estimation": pp.1, 3-10 via arXiv PDF.
- Mikolov, Yih, Zweig 2013 "Linguistic Regularities": pp.746-750 via ACL Anthology PDF.
- Mikolov et al. 2013 NIPS: pp.1-5 via NeurIPS PDF.
- Jurafsky and Martin 2025: Chapter 5 pp.1, 5-18, 22, 25 via Stanford PDF.

### Still useful

- Full-page extraction for Deerwester et al. 1990 beyond the abstract/p.391.
- Public word2vec code archive/release anchors.
- Physical or library access to citation/adoption history if the prose wants a strong "field uptake" paragraph.

## Conflict Notes

- "Word2Vec invented vector semantics" is false. Harris, LSA, and Bengio give a longer lineage. The chapter should say Word2Vec made dense learned word vectors cheap, measurable, and widely usable.
- "Semantic arithmetic is magic" is false. The primary papers frame it as vector-offset evaluation with measurable but limited accuracy.
- "Latent space" is a chapter title metaphor. Use technically grounded phrases: vector space, continuous representation, embedding space, distributed representation, and static embedding.
