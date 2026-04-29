# Infrastructure Log: Chapter 44 — The Latent Space

## Scene 1: Distribution Before Neural Scale

- Harris 1954 is conceptual infrastructure: distributional analysis depends on occurrence environments, not compute claims. Anchor: `sources.md` S1, p.146.
- LSA's infrastructure is matrix infrastructure: a term-document matrix reduced by singular-value decomposition into about 100 orthogonal factors. Anchor: `sources.md` S2, p.391.

## Scene 2: Bengio's Neural Language Model Cost

- Bengio et al. use a vocabulary mapping `C` from each word to a real vector and learn it jointly with the probability function. Anchor: `sources.md` S3, pp.1141-1142.
- The curse-of-dimensionality setup uses a vocabulary of 100,000 and 10-word sequences to illustrate roughly `10^50` possible combinations. Anchor: `sources.md` S3, p.1137.
- AP News experiments ran only 5 epochs and took about 3 weeks using 40 CPUs. Anchor: `sources.md` S3, pp.1148-1149.
- The conclusion says the approach shifts difficulty toward computation but avoids exponential scaling in computation and memory with conditioning variables. Anchor: `sources.md` S3, pp.1152-1153.

## Scene 3: Word2Vec Efficiency And Google-Scale Training

- "Efficient Estimation" defines model complexity as a function of epochs, training words, and architecture-specific cost; it is explicitly trying to maximize accuracy while minimizing computational complexity. Anchor: `sources.md` S4, pp.2-3.
- CBOW removes the non-linear hidden layer and averages/project context words; Skip-gram predicts surrounding words from a current word. Anchor: `sources.md` S4, pp.3-4.
- Google News experiment: about 6B tokens and a vocabulary restricted to 1M most frequent words. Anchor: `sources.md` S4, p.6.
- One-CPU table: 300-dimensional CBOW on 783M words in about 1 day; 300-dimensional Skip-gram on 783M words in about 3 days; one-epoch Skip-gram on 1.6B words in about 2 days. Anchor: `sources.md` S4, p.7.
- DistBelief setup: 50 to 100 replicas, mini-batch asynchronous gradient descent, Adagrad, shared data-center machines; Table 6 reports models over 6B words with training time in days x CPU cores. Anchor: `sources.md` S4, p.8.

## Scene 4: Evaluation Infrastructure

- "Linguistic Regularities" uses RNN vectors trained on 320M words of Broadcast News with an 82k vocabulary. Anchor: `sources.md` S5, p.749.
- Its syntactic analogy dataset has 8,000 questions. Anchor: `sources.md` S5, pp.747-748.
- Its semantic evaluation uses SemEval-2012 Task 2 with 69 test relations. Anchor: `sources.md` S5, p.748.
- "Efficient Estimation" expands evaluation to 8,869 semantic and 10,675 syntactic questions. Anchor: `sources.md` S4, p.6.

## Scene 5: Optimization Tricks

- Full softmax in Skip-gram is impractical because cost is proportional to vocabulary size, often `10^5` to `10^7` terms. Anchor: `sources.md` S6, pp.2-3.
- Negative sampling reframes training as distinguishing target words from noise samples. Anchor: `sources.md` S6, pp.3-4.
- Frequent-word subsampling addresses words like "in", "the", and "a"; the paper reports several-times training-speed improvement and better vector accuracy. Anchor: `sources.md` S6, pp.4-5.
- Phrase handling replaces frequent multiword phrases with unique tokens and reports 72% on a phrase analogy dataset. Anchor: `sources.md` S6, p.5.
- Optimized single-machine implementation claim: more than 100B words in one day. Anchor: `sources.md` S6, p.1.

## Explicit Non-Claims

- No GPU infrastructure claim is anchored. Keep GPU references out.
- Do not identify exact Google News corpus composition beyond the paper's "Google News corpus" language.
- Do not state exact public word2vec release dates until the code archive is extracted.
