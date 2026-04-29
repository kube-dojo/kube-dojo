# Scene Sketches: Chapter 44 — The Latent Space

## Scene 1: The Old Idea of Context

- **Evidence layer:** Harris says distribution is built from environments/co-occurrents; LSA later turns term-document associations into a lower-dimensional latent semantic factor space; Bengio brings learned distributed vectors into neural language modeling.
- **Anchors:** `sources.md` S1 pp.146-147; S2 p.391; S3 pp.1137, 1139; S7 pp.1, 5-6.
- **Prose shape:** Start with a corrective: 2013 is not where context became meaning. The scene should move from "words occur with other words" to "those patterns can become coordinates." Keep it concrete: occurrence environments, term-document matrices, learned feature vectors.
- **Avoid:** claiming Harris or LSA anticipated Word2Vec specifically.

## Scene 2: The Bottleneck

- **Evidence layer:** Bengio's neural probabilistic language model attacks the curse of dimensionality by learning word feature vectors, but the architecture still costs serious compute.
- **Anchors:** `sources.md` S3 pp.1137, 1141-1142, 1148-1149, 1152-1153.
- **Prose shape:** The writer can explain the 100,000-word vocabulary example and then show the price of making it neural: mapping C, softmax probabilities, and AP News training that took about three weeks on 40 CPUs. This is the chapter's pressure-building scene.
- **Avoid:** turning Bengio into a failed precursor. The model was important; Word2Vec simplified a real success, not a dead end.

## Scene 3: The Google Simplification

- **Evidence layer:** Word2Vec reframes the problem with simple log-linear architectures. CBOW predicts a word from its context; Skip-gram predicts context from a word. The papers measure architecture, training words, vector dimensions, and runtime.
- **Anchors:** `sources.md` S4 pp.1, 3-8; S7 pp.10-15.
- **Prose shape:** Treat the model diagram as the scene: context words flow into a projection; the center word predicts its neighbors; the hidden layer disappears. Then widen to infrastructure: Google News 6B tokens, one-CPU tables, and DistBelief replicas.
- **Avoid:** "standard CPUs/GPUs" phrasing. The anchor is CPU and DistBelief, not GPU.

## Scene 4: Offsets in the Space

- **Evidence layer:** Mikolov, Yih, and Zweig test whether syntactic and semantic relations become vector offsets. King-Man+Woman near Queen is one example inside a broader analogy-evaluation program.
- **Anchors:** `sources.md` S5 pp.746-750; S4 pp.5-10; S7 pp.17-18.
- **Prose shape:** Make the famous arithmetic feel empirical. Explain how the offset method works, name the test sets, mention the almost-40% syntactic result and later semantic-syntactic question counts, then add caveats. The scene's drama is the measurable regularity, not a private discovery.
- **Avoid:** saying the vector lands "exactly" on Queen or that relationships are perfectly mirrored.

## Scene 5: Making It Usable, Then Hitting The Boundary

- **Evidence layer:** The NIPS 2013 paper turns the idea into a more usable toolkit: negative sampling, subsampling, and phrase vectors. The secondary synthesis marks word2vec as static embeddings, one fixed vector per word.
- **Anchors:** `sources.md` S6 pp.1-5; S7 pp.10-11, 12-15; S3 p.1151.
- **Prose shape:** Finish with the engineering details that made embeddings practical: avoid full softmax, throw away some high-frequency words, promote phrases to tokens, train at very high throughput. Then close honestly: one word still has one point, so context-sensitive meaning belongs to the next chapter.
- **Avoid:** making GloVe, FastText, BERT, or transformers into a second chapter inside this one.
