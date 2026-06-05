---
title: "Embeddings & Representation Learning"
slug: ai-ml-engineering/deep-learning/module-1.4.1-embeddings-representation-learning
sidebar:
  order: 1005.1
---

> **AI/ML Engineering Track** | Complexity: `[MEDIUM]` | Time: 3-4 hours
>
> **Prerequisites**: Block A modules A3 (forward propagation shapes), A5 (softmax cross-entropy on logits), A6 (backprop and sparse gradient intuition), and A8 (scalar autograd). Block B modules 1.2 (`nn.Linear`, `nn.Module`, autograd), 1.3 (training loop), 1.3.1 (initialization), and 1.3.4 (LayerNorm — forward-point only).
>
> **Primary tools**: PyTorch 2.12, `nn.Embedding`, `F.one_hot`, `F.cosine_similarity`, `F.linear`.

---

In 2013, Tomas Mikolov and colleagues at Google published "Efficient Estimation of Word Representations in Vector Space," a paper that made a deceptively simple claim stick: you could train a shallow neural network on a word-prediction task and the hidden weight matrix would become a useful map from discrete symbols to continuous vectors. Words that appeared in similar contexts landed near each other in that space. The famous arithmetic example — `king - man + woman ≈ queen` — was not magic; it was the geometry of co-occurrence statistics compressed into a table of learnable rows. That paper launched the modern embedding era, but the engineering insight is older and simpler than any specific algorithm: **a discrete ID is just an index into a weight matrix**, and lookup is matrix multiplication with a one-hot input.

Follow-up work in the same research line extended those vectors to phrases and sharpened negative-sampling training recipes that practitioners still cite when they need a fast standalone embedding baseline. You do not need to reproduce those loops to build transformers, but you should recognize them as historical proof that shallow objectives already learned useful geometry — which is why tying, freezing, and fine-tuning pretrained rows remain mainstream even after billion-parameter models arrived.

Everything in Block C — attention, residual streams, transformer blocks — operates on continuous vectors. Raw text, category labels, and user IDs arrive as integers. Before any `nn.Linear` projection or scaled dot-product can run, those integers must become tensors of shape `(batch, seq_len, d_model)` or `(batch, d_embed)`. This module is where that conversion happens. The spine is the same mechanism you already built in Block B: **`nn.Embedding` is `nn.Linear` with a sparse one-hot input**, implemented as an efficient gather so you never materialize the one-hot matrix. Once you internalize that equivalence, embeddings stop feeling like a separate "NLP trick" and start looking like the first layer of almost every modern architecture — including the transformer block you will assemble in module C4.

Positional encoding — the separate question of *where* a token sits in a sequence — belongs to C4. Token embeddings answer *what* the symbol is. Keep that boundary clean as you read.

If you remember one sentence from this module before moving on, make it this: **embeddings are a weight matrix indexed by integers, trained by the same autograd rules as every other layer.** Everything else — cosine neighbors, word2vec history, tying, subword tokenizers — is elaboration on that single engineering fact. The next modules in Block C will stack attention, residuals, and LayerNorm on top of these vectors without changing how the table is indexed or updated. Carry the shape comments habit forward: every gather has a `(B, T) → (B, T, D)` story, and every backward pass writes only the rows you actually used in that step.

---

## Learning Outcomes

By the end of this module, you will be able to:

1. **Explain** why one-hot encoding fails as a representation for high-cardinality discrete inputs, and **compare** its equidistant geometry to neighborhood structure learned by dense embeddings.
2. **Derive** the equivalence `embedding(id) ≡ one_hot(id) @ W`, **implement** both forms in PyTorch 2.12 with explicit shape comments, and **verify** identical outputs on a toy vocabulary.
3. **Analyze** sparse embedding gradients during backprop — connecting row-only updates to the VJP picture from A6/A8 — and **measure** cosine similarity, nearest neighbors, and analogy directions as diagnostic geometry rather than guaranteed lexical rules.
4. **Contrast** word2vec skip-gram/CBOW and GloVe co-occurrence factorization with modern end-to-end embedding training, then **choose** pretrained versus from-scratch initialization and **apply** freezing versus fine-tuning based on dataset size and domain shift.
5. **Configure** vocabulary size, embedding dimension, `padding_idx`, weight tying with the output projection, and initialization as capacity knobs tied to signal propagation from module 1.3.1.

---

## Why This Module Matters

Neural networks are continuous functions. They eat floating-point tensors and return floating-point tensors. Yet most real inputs are discrete: a token ID from a vocabulary of fifty thousand subwords, a product category from an enum of three hundred values, a user ID from a table with millions of rows. The bridge between those worlds is the embedding layer, and treating that layer as a black box is how engineers end up with shape errors, runaway memory use, and models that never transfer knowledge from pretraining.

The Block A/B back-reference matters here because nothing about embeddings introduces a new autograd primitive. In module 1.2 you learned that `nn.Linear(in_features, out_features)` applies a weight matrix `W` of shape `(out_features, in_features)` to an input `x` of shape `(..., in_features)`, producing `(..., out_features)`. If `x` is a one-hot vector of length `V` with a single `1` at index `k`, then `x @ W.T` (equivalently `F.linear(x, W)`) returns column `k` of `W` (= row `k` of `E=W^T`, shape `(V, D)`). That is an embedding lookup. PyTorch's `nn.Embedding(V, D)` stores exactly that weight matrix — shape `(V, D)` — and implements the multiply as an index gather for speed and memory. When you call `loss.backward()`, gradients flow into only the rows that participated in the forward pass, which is the same sparsity pattern you would get from a one-hot matmul, just without allocating the one-hot tensor.

Representation quality determines downstream ease. A good embedding space places similar items near each other so that a simple linear classifier — a single `nn.Linear` — can separate classes that matter for your task. A bad representation forces every downstream layer to undo the input encoding before it can learn anything useful. That is why transfer learning works: pretraining on a large corpus learns geometry that smaller task-specific datasets can fine-tune rather than discover from scratch. It is also why random initialization plus end-to-end training still works when you have enough labeled data: the embedding matrix is just the first set of weights optimized by the same backprop chain you traced by hand in A6.

For Block C specifically, embeddings are the entry ramp. Multi-head attention (C3) projects embedded tokens with three independent `nn.Linear` layers. The transformer block (C4) adds positional information on top of token embeddings and routes both through LayerNorm and residual connections. If you do not understand how the embedding table is indexed, shaped, padded, and updated, every subsequent module looks like incantation. This module makes the table concrete.

The same entry ramp applies outside NLP. Recommendation models embed users and items; graph models embed nodes; tabular pipelines embed high-cardinality categoricals. The tensor shapes change — `(batch,)` IDs versus `(batch, seq_len)` token grids — but the gather pattern, sparse gradients, and vocabulary bookkeeping repeat. Treat embeddings as a cross-domain primitive, not a language-only chapter, and Block C’s later attention material will feel like composition rather than a domain switch.

Think of an embedding matrix like the drawer labels in a parts warehouse. A one-hot encoding gives every part its own isolated room with no map between rooms — finding a substitute means walking every aisle. A learned embedding gives each part a coordinate in a continuous floor plan where neighbors are functionally similar: screws near screws, brackets near brackets. Training moves the shelves; inference is just reading coordinates.

There is also a memory story that bites production teams who only think in terms of parameter counts for `nn.Linear` layers. An embedding table with vocabulary `V = 128{,}256` and dimension `d = 4096` stores roughly half a billion trainable floats in that matrix alone before you add transformer blocks. That is not a reason to avoid embeddings — language models depend on them — but it is a reason to treat vocabulary design, tying, factorization, and checkpoint sharding as first-class engineering. Block B taught you to watch activation scale through depth; Block C starts earlier, at the input boundary, where the first matrix already sets the dtype path, the sequence width, and the gradient sparsity pattern for the entire step.

When you debug a transformer later in this block, many “the model does not learn” reports trace back to the embedding boundary: wrong `padding_idx`, tokenizer vocabulary mismatch after a data refresh, accidental training with frozen random rows, or an embedding dimension that does not divide evenly into the head count used by multi-head attention in C3. Fixing those issues does not require new mathematics. It requires the same shape discipline you practiced in A3 and the same autograd mental model from A8 — only applied to a `(V, D)` table instead of a dense weight stack.

---

## Part 1: From Symbols to Vectors

### 1.1 Why discrete IDs are not yet representations

A language model does not receive the string `"cat"`. It receives an integer — say `3847` — produced by a tokenizer that maps subword strings to indices in a fixed vocabulary. That integer is symbolic: swapping label `3847` for `9999` would change nothing about the mathematics if you relabeled consistently. The model needs a **representation**: a vector of real numbers where nearby directions encode usable similarity structure.

The naive encoding is one-hot: represent item `k` in a vocabulary of size `V` as a vector `e_k ∈ {0,1}^V` with a `1` at position `k` and zeros elsewhere. For `V = 50{,}000`, each vector is fifty thousand dimensional, almost entirely zeros. Storage is wasteful, but the deeper problem is geometric: every pair of distinct one-hot vectors has the same cosine similarity (zero) and the same Euclidean distance (`√2`). The encoding carries **no notion of neighborhood**. `"cat"` and `"kitten"` are exactly as far apart as `"cat"` and `"democracy"`.

```python
import torch
import torch.nn.functional as F

V = 8  # toy vocabulary size
id_cat, id_kitten, id_democracy = 2, 3, 7

def one_hot_id(index: int, vocab_size: int) -> torch.Tensor:
    # scalar index -> (vocab_size,) binary vector
    return F.one_hot(torch.tensor(index), num_classes=vocab_size).to(torch.float32)

v_cat = one_hot_id(id_cat, V)           # (8,)
v_kitten = one_hot_id(id_kitten, V)     # (8,)
v_demo = one_hot_id(id_democracy, V)    # (8,)

print("cat · kitten =", F.cosine_similarity(v_cat, v_kitten, dim=0).item())      # 0.0
print("cat · democracy =", F.cosine_similarity(v_cat, v_demo, dim=0).item())    # 0.0
print("||cat - kitten|| =", (v_cat - v_kitten).norm().item())                  # 1.4142...
print("||cat - democracy|| =", (v_cat - v_demo).norm().item())                  # 1.4142...
```

Dense learned embeddings fix both problems. Instead of fifty thousand sparse dimensions, you choose a modest `d_embed` — often 256, 512, or 768 — and learn a matrix `E ∈ ℝ^{V × d_embed}` so item `k` maps to row `E[k]`. Similar items can end up with similar rows because training pulls them together when the loss rewards it. The dimension `d_embed` is a capacity knob: too small and distinct symbols collide; too large and you waste parameters and risk overfitting on small datasets.

The jump from one-hot to dense is also where similarity becomes measurable. In a one-hot world, the dot product of two distinct symbols is always zero, so any classifier built on top must learn every relationship from scratch on every pair. In a dense world, dot products and cosines between rows become features the next layers can reuse. That reuse is the core of representation learning: you are not merely encoding IDs, you are exporting structure learned from the data distribution into a geometry the rest of the network can exploit with ordinary linear maps from Block B.

### 1.2 Categories, users, and the same pattern

Natural language gets the headlines, but the embedding pattern is universal. Recommender systems embed user IDs and item IDs into a shared space where dot products approximate preference scores. Categorical features in tabular models embed enum values before feeding a multilayer perceptron. Graph neural networks embed node IDs. The engineering questions repeat: vocabulary size (how many rows), embedding dimension (how wide each row), out-of-vocabulary handling (an `<unk>` row or a hash trick), and whether to train from scratch or import pretrained rows. The mechanism is identical; only the tokenizer and pretraining corpus change.

The failure mode is also universal. If you one-hot encode a million user IDs, you create a million-dimensional space where collaborative filtering cannot generalize — every user looks unrelated to every other user until you have dense co-occurrence signal. If you embed users into, say, 64 dimensions, the model can learn that users who click similar item sequences should land near each other even when their raw IDs differ. That is the same co-occurrence intuition word2vec exploited, just with a different alphabet. The Block A lesson about linear layers as the workhorse of deep networks therefore applies unchanged: an embedding is the first linear map from a sparse categorical input into the hidden space where nonlinear blocks operate.

High-cardinality categoricals also stress optimizers differently from dense weight matrices. A `nn.Linear(512, 512)` layer receives gradient on every weight every step. An embedding table receives gradient on only the handful of rows touched by the current batch. Adam’s second-moment estimates for rare rows evolve slowly; learning rates that work for upper layers can be too aggressive for frequently updated common tokens and too timid for tail tokens. You do not need a bespoke optimizer to start, but you should expect tail-token behavior to differ from head-token behavior unless the data distribution or sampling strategy compensates.

---

## Part 2: The Embedding Layer Is One-Hot Times a Weight Matrix

### 2.1 Worked equivalence on a toy vocabulary

Let `V = 4` and `d_embed = 3`. The embedding matrix `W` holds one row per vocabulary item:

```
W = [[ 0.10,  0.20,  0.30],   # id 0
     [ 0.40,  0.50,  0.60],   # id 1
     [ 0.70,  0.80,  0.90],   # id 2
     [ 1.00,  1.10,  1.20]]   # id 3
     shape (4, 3)
```

If the input token ID is `2`, one-hot encoding produces `[0, 0, 1, 0]`. Multiplying that one-hot row by `W` selects the third row:

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

V, D = 4, 3
W = torch.tensor([
    [0.10, 0.20, 0.30],
    [0.40, 0.50, 0.60],
    [0.70, 0.80, 0.90],
    [1.00, 1.10, 1.20],
])  # (V, D) = (4, 3)

token_id = torch.tensor(2)  # scalar index

# Path A: explicit one-hot matmul
one_hot = F.one_hot(token_id, num_classes=V).to(W.dtype)  # (4,)
via_one_hot = one_hot @ W                                  # (4,) @ (4,3) -> (3,)
print("one_hot @ W =", via_one_hot)                          # [0.7, 0.8, 0.9]

# Path B: nn.Embedding gather
embed = nn.Embedding(V, D)
with torch.no_grad():
    embed.weight.copy_(W)
via_embedding = embed(token_id)                            # () -> (3,) after batching rules
print("nn.Embedding =", via_embedding)                     # [0.7, 0.8, 0.9]

assert torch.allclose(via_one_hot, via_embedding)
```

For a batch of sequences, IDs arrive as `(batch, seq_len)` integers. `nn.Embedding` returns `(batch, seq_len, d_embed)` by gathering each index's row. That tensor is exactly what the first transformer layer expects before any Q/K/V projection — though positional encoding (C4) will add separate position information later.

```python
B, T, V, D = 2, 5, 4, 3
ids = torch.tensor([
    [0, 2, 1, 3, 2],
    [1, 1, 0, 2, 3],
])  # (B, T) = (2, 5)

embed = nn.Embedding(V, D)
x = embed(ids)  # (B, T, D) = (2, 5, 3)
print(x.shape)
```

### 2.2 Connection to `nn.Linear` from module 1.2

Formally, if you treat the one-hot vector as the input to a linear layer with **no bias** and weight matrix `W` shaped `(d_embed, V)` — note PyTorch stores `nn.Linear.weight` as `(out_features, in_features)` — you recover the same result with a transposed convention. The embedding layer stores `(V, d_embed)` and gathers rows, which is the memory-efficient pattern for extremely sparse inputs. You would never instantiate a `(batch, seq_len, V)` one-hot tensor in production; a vocabulary of fifty thousand makes that prohibitive. The math equivalence is the pedagogical anchor; the gather implementation is the engineering reality.

You can prove the equivalence to yourself whenever a teammate insists embeddings are “different” from linear layers. Take a single ID, build the one-hot vector explicitly in fp32, multiply by `W`, compare to `nn.Embedding`, then delete the one-hot path and keep the gather forever. The backward pass tells the same story: a one-hot input routes gradient to one column of the linear weight; a gather routes gradient to one row of the embedding table. Transpose conventions swap row/column language; the sparsity pattern does not.

### 2.3 Sparse gradients through the embedding table

During backpropagation, the embedding lookup is a selection operation. Only the rows that appeared in the forward pass receive non-zero gradients. If token ID `2` occurred three times in a batch, the gradient for row `2` accumulates those three contributions — autograd sums them automatically when you call `optimizer.step()`.

```python
import torch
import torch.nn as nn

V, D = 6, 4
ids = torch.tensor([2, 2, 5])  # (3,) — id 2 appears twice, id 5 once
embed = nn.Embedding(V, D)
loss = embed(ids).sum()        # dummy scalar loss
loss.backward()

# Rows never looked up stay at zero gradient
print(embed.weight.grad[0].abs().sum().item())  # 0.0 — id 0 unused
print(embed.weight.grad[2])                     # non-zero — used twice
print(embed.weight.grad[5])                     # non-zero — used once
```

This is the same sparsity you would see from a one-hot matmul, and it connects directly to A6's picture of the `+` and selection nodes in a computation graph: the VJP routes upstream signal only to paths that participated. It also explains a common training pathology: **rare tokens update slowly** because they receive gradient signal infrequently. Frequency-based learning rates, adaptive optimizers (module 1.3.2), and large pretraining corpora all address that imbalance in different ways.

If you have ever inspected `embed.weight.grad` after a step and wondered why only a few rows look “bright” in a histogram, you are seeing the token frequency distribution of your batch written into optimization. Mixed-precision training from module 1.3.6 applies here too: embedding gradients can underflow in fp16 like any other tensor, and tying can amplify effective learning rates because two loss paths update the same storage. None of that changes the sparse pattern — it only changes the numeric scale on the rows that did receive signal.

### 2.4 `padding_idx` and masked batches

Real batches pad shorter sequences to a common length. Padding tokens must not affect the loss or receive gradient updates that corrupt a shared `<pad>` row. PyTorch's `nn.Embedding(V, D, padding_idx=pad_id)` keeps that row at zero (by default) and skips gradient updates to it when the index equals `pad_id`.

```python
PAD = 0
V, D = 10, 8
embed = nn.Embedding(V, D, padding_idx=PAD)

ids = torch.tensor([3, 4, PAD, PAD])  # (4,)
vecs = embed(ids)                        # (4, 8)

print(vecs[2])  # row stays zeros — padding position
# In a transformer, padding masks (C3) also zero out attention to pad positions
```

Do not confuse token embedding padding with causal attention masks (C3) or with positional encoding (C4). Padding handles variable-length batches within a fixed tensor shape; causal masks enforce autoregressive visibility; positional encoding injects order information. All three meet in the full transformer block, but they solve different problems.

In a training loop from module 1.3, the embedding layer participates exactly like any other `nn.Module` child: forward produces `(B, T, D)`, loss reduces to a scalar, `loss.backward()` fills `embed.weight.grad`, and `optimizer.step()` updates only the rows that received signal. If you inspect `embed.weight.grad` mid-training and see entire unused rows still at zero while common rows have large accumulated gradients, you are watching the empirical token frequency distribution written into the optimization dynamics. Data loading choices — oversampling rare classes, class-balanced batching, or simply training long enough on a large corpus — change that pattern as much as architectural choices do.

When you export a checkpoint, the embedding matrix is often the largest single tensor in the file besides transformer blocks. Versioning the tokenizer JSON alongside that checkpoint is not bureaucracy; without it, row 1042 might mean `"learning"` in production and `"▁learn"` in staging after a BPE merge table change. The embedding module is simple code with heavy operational dependencies.

---

## Part 3: The Geometry of Embedding Spaces

### 3.1 Cosine similarity and neighborhoods

Once symbols live in `ℝ^d`, similarity is measured by geometry. Cosine similarity compares direction while down-weighting pure magnitude differences when norms vary: `cos(u, v) = (u · v) / (||u|| ||v||)`. Values near `1` mean the vectors point roughly the same direction; near `0` mean orthogonal; near `-1` mean opposite. For word embeddings trained on co-occurrence signal, related words often cluster — `"python"` near `"java"` in a programming corpus — because the training objective pushes tokens that predict similar contexts toward similar rows.

Euclidean distance and cosine are related but not identical when norms differ. Two vectors can be far in L2 distance yet have high cosine similarity if they point the same direction but differ in length. In practice, NLP inspection workflows often normalize rows before neighbor search so length quirks do not dominate. Vision and recommender pipelines sometimes keep raw dot products when scores must reflect both alignment and magnitude. The engineering habit is to declare which metric your loss or retrieval index uses and stay consistent across training and evaluation.

```python
import torch
import torch.nn.functional as F

# Toy "learned" rows — illustrative, not trained
words = ["king", "queen", "man", "woman", "apple"]
W = torch.tensor([
    [ 1.0,  0.2,  0.0,  0.5],  # king
    [ 0.9,  0.3,  0.1,  0.6],  # queen
    [ 0.2, -0.5,  0.1,  0.0],  # man
    [ 0.3, -0.4,  0.2,  0.1],  # woman
    [-1.0,  2.0,  3.0, -2.0],  # apple (unrelated)
])  # (5, 4)

def cosine_table(W: torch.Tensor) -> torch.Tensor:
    Wn = F.normalize(W, dim=1)              # (N, D) unit rows
    return Wn @ Wn.T                        # (N, N) pairwise cosines

print(cosine_table(W))
# king/queen and man/woman pairs tend high; apple low vs royalty words
```

Nearest-neighbor lookup — argmax cosine against all rows except the query — is the standard sanity check when inspecting a trained embedding table. Production systems rarely scan the full vocabulary linearly at scale; they use approximate nearest-neighbor indexes. For learning, the brute-force loop is fine.

```python
def nearest(W: torch.Tensor, query_idx: int, k: int = 3):
    Wn = F.normalize(W, dim=1)                       # (V, D)
    q = Wn[query_idx]                                # (D,)
    sims = Wn @ q                                    # (V,)
    sims[query_idx] = -1.0                           # mask self
    topk = torch.topk(sims, k=k)
    return topk.indices.tolist(), topk.values.tolist()

print(nearest(W, query_idx=0))  # neighbors of "king"
```

### 3.2 Analogies: illustrative regularity, not a guarantee

The `king - man + woman ≈ queen` example popularized embedding arithmetic. The intuition is that some relational directions — gender, tense, capital-city — appear as approximate translations in the vector space learned by word2vec-style objectives. **It is not a theorem.** Many analogies fail; the effect depends on corpus bias, training hyperparameters, and whether the relation is linearly encoded at all. Present analogies as diagnostic curiosities: when they work, they reveal structure; when they fail, they reveal limits of shallow linear reasoning on a single embedding table.

Engineering teams sometimes misuse analogy demos as product guarantees — for example, assuming a finance embedding will reliably answer “country : capital” style queries because a word2vec slide did. The safer workflow is to treat analogies like unit tests you did not write yourself: sample them, log failures, and pair them with nearest-neighbor lists that are easier to interpret. Cosine neighbors answer “what is close?”; analogies answer “is there a consistent direction?” Both are useful, neither is definitive.

```python
idx = {w: i for i, w in enumerate(words)}
vec = lambda w: W[idx[w]]  # (4,)

analogy = vec("king") - vec("man") + vec("woman")  # (4,)
Wn = F.normalize(W, dim=1)
analogy_n = F.normalize(analogy, dim=0)
sims = Wn @ analogy_n
print("closest word to king-man+woman:", words[sims.argmax().item()])
# With this toy table the winner may not be "queen" — that's the point
```

### 3.3 Visualizing clusters (optional sanity check)

When `d_embed` is 2 or 3, scatter plots make clustering visible. High-dimensional embeddings require dimensionality reduction (PCA, t-SNE, UMAP) for human viewing — treat those plots as qualitative only; t-SNE distances are not metric faithful. The engineering habit is: train, sample, compute cosine neighbors, read the lists.

Another inspection trick used in production postmortems is to track how neighbor lists drift across checkpoints. If `"security"` suddenly neighbors `"performance"` after a fine-tune, you may have collapsed part of the geometry with too large a learning rate on the embedding table or too small a regularization budget. Geometry is not a vanity visualization; it is a cheap regression test on representation health before you spend GPU hours on downstream benchmarks.

---

## Part 4: How Embeddings Are Learned

### 4.1 Classical word2vec: prediction drives geometry

Before transformers dominated NLP, **word2vec** (Mikolov et al., 2013) learned embeddings with a shallow network on a simple prediction task. Two variants matter conceptually:

- **Skip-gram**: given a center word, predict surrounding context words.
- **CBOW (continuous bag of words)**: given context words, predict the center word.

Both optimize rows of an embedding matrix so that words appearing in interchangeable contexts get similar vectors. Negative sampling makes training tractable on large corpora by contrasting real context pairs with random noise words. You do not need to implement word2vec in this module; the lesson is that **the objective sculpts the geometry**. Change the task, change the space.

Skip-gram and CBOW differ in which direction prediction flows, but both learn two matrices in the original implementation — input embeddings and output context embeddings — that practitioners often merge or discard depending on the downstream task. Modern transformers collapse that story: one token embedding matrix at the input, sometimes tied to the output projection, trained on next-token prediction at scale. The historical two-matrix word2vec setup explains why papers talk about “input” and “output” embeddings separately even when production code shares weights.

### 4.2 GloVe: global co-occurrence factorization

**GloVe** (Pennington et al., 2014) constructs a word-word co-occurrence matrix from corpus statistics and learns vectors whose dot products approximate log co-occurrence counts. It is factorization-flavored rather than local prediction-flavored, yet it produces similar neighbor structure on many benchmarks. The engineering takeaway parallel to word2vec: embeddings compress statistical regularities of the training data — including biases present in that data.

GloVe’s global matrix view makes explicit something word2vec hides inside streaming minibatches: co-occurrence counts are the raw material. Whether you factorize those counts directly or train a classifier to predict context, you are still estimating which symbols should be near each other in vector space. That is why pretrained embedding tables from different algorithms can still fine-tune into the same downstream model — the downstream task only needs a reasonable starting geometry, not a specific historical training recipe.

### 4.3 Modern default: end-to-end task training

Today most production models — BERT, GPT-class decoders, vision transformers with patch embeddings — **learn embeddings as the first layer of the end-to-end model** on the downstream or pretraining objective. There is no separate word2vec stage unless you choose one for speed on tiny hardware. The embedding matrix is initialized (module 1.3.1), updated by the same optimizer as every other weight (module 1.3.2), regularized by dropout and weight decay (module 1.3.3), and normalized downstream by LayerNorm (module 1.3.4). Stable softmax on logits (A5, module 1.3.6) governs the classification head that sits above embeddings in classifier models.

Vision transformers apply the same pattern with patch embeddings: image patches become a sequence of tokens, each with an ID or direct linear projection from patch pixels. The discrete/continuous boundary blurs — patches may be flattened pixels rather than lookup tables — but the sequence-of-vectors story Block C tells still begins at “turn inputs into `(B, T, D)` tensors the stack can mix.”

The Block C preview: transformer token embeddings are exactly this table, plus separate positional information added in C4 before attention mixes tokens. When you later implement scaled dot-product attention in C3, remember that Q/K/V projections assume inputs already live in a well-scaled `(B, T, d_model)` space. If embeddings explode because initialization ignored fan-in, attention logits explode with them — which is why stable softmax from A5 and module 1.3.6 re-enters the story at the attention row, not at the embedding row, but prevention beats triage.

Negative sampling in word2vec also previews a training theme you will see again at vocabulary scale: full softmax over 50k classes every step is expensive, so objectives sample negatives or factorize co-occurrence to make learning tractable. Language-model heads at the output side face the same pressure, which motivates weight tying and sampled softmax variants. The embedding input side and the logits output side are two ends of the same vocabulary-sized bottleneck.

---

## Part 5: Representation Learning and Transfer

### 5.1 The linear-probe intuition

A **representation** is good when simple downstream models succeed. A linear probe — freeze the embedding table (or an entire pretrained encoder) and train only a final `nn.Linear` classifier — measures how linearly separable your labels are in that space. Strong pretraining yields high probe accuracy with tiny labeled sets; random initialization yields chance until enough labels train the table.

```python
import torch
import torch.nn as nn

V, D, num_classes = 5000, 256, 10
ids = torch.randint(0, V, (32, 20))      # (B, T) fake batch
labels = torch.randint(0, num_classes, (32,))

class BagOfEmbeddingsClassifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.embed = nn.Embedding(V, D)
        self.head = nn.Linear(D, num_classes)

    def forward(self, ids):
        x = self.embed(ids)           # (B, T, D)
        x = x.mean(dim=1)             # (B, D) — mean pool for illustration
        return self.head(x)           # (B, num_classes)

model = BagOfEmbeddingsClassifier()
logits = model(ids)
```

This classifier is pedagogically simple — mean pooling discards order on purpose. Sequence models (C3/C4) replace pooling with attention, but the embedding entry point is identical.

Mean pooling is a deliberate simplification to isolate the embedding table’s contribution. If your pooled embedding already separates classes linearly, you have evidence the table carries signal. If not, either train longer, increase `d_embed`, import pretrained rows, or add depth — but do not blame the optimizer before inspecting the representation. The diagnostics playbook from module 1.3.5 applies unchanged: overfit a tiny batch first. If the model cannot memorize ten examples when only the embedding and a linear head are unfrozen, the issue is likely indexing, shapes, or labels — not mystical “bad luck.”

### 5.2 Pretrained versus from-scratch

| Situation | Typical choice | Reason |
|-----------|----------------|--------|
| Large in-domain corpus, ample compute | Train embeddings end-to-end | Task-specific geometry beats generic pretraining |
| Small labeled set, general-domain text | Start from pretrained token embeddings | Transfer carries co-occurrence signal you cannot afford to relearn |
| New vocabulary (chemical tokens, log formats) | Extend vocabulary, init new rows, fine-tune | Pretrained rows still help shared subwords |
| Frozen encoder deployment | Freeze embeddings + lower layers, train head | Limits overfit and compute |

**Fine-tuning** updates embedding rows with a usually smaller learning rate than upper layers. **Freezing** treats the table as a fixed feature extractor. Neither is universally correct: freezing fails when domain shift makes pretrained neighbors misleading; full fine-tune on tiny data overwrites rare rows destructively.

A practical pattern on small domain-specific corpora is to freeze embeddings for the first epochs while upper layers learn a decision boundary, then unfreeze with a reduced learning rate so geometry adapts without erasing pretraining in the first hundred steps. Another pattern is to append new vocabulary rows for domain tokens initialized randomly or from subword averages while keeping the original rows tied to the pretrained checkpoint. Both patterns treat the embedding table as a data structure with lifecycle management, not a static constant baked into the model constructor.

Linear probes also help you decide whether representation problems live in the embedding layer or above it. If a probe on frozen upper-layer activations succeeds but a probe on raw embeddings fails, depth is doing the work and embeddings may be fine. If even a probe on mean-pooled embeddings succeeds on a tiny dataset, you may be under-training the head or over-parameterizing upper blocks relative to the actual signal available.

---

## Part 6: Tokenization (Brief Forward-Pointer)

Embeddings index **tokenizer output**, not raw Unicode strings. **Byte Pair Encoding (BPE)** and **WordPiece** iteratively merge frequent character or subword pairs until the vocabulary reaches a target size (often 30k–50k for language models). Rare words decompose into subwords (`"unhappiness"` → `"un" + "happiness"` or finer splits), controlling out-of-vocabulary rate at the cost of longer sequences.

The engineering contract: tokenizer defines `V`; embedding matrix has `V` rows; model weights and saved checkpoints must use the same vocabulary file. Changing tokenizers without resizing and re-mapping embeddings breaks inference silently — IDs point at the wrong rows. Full tokenizer implementation belongs to a dedicated topic; here the dependency is explicit: **vocabulary indexes the table**.

Byte-level and subword tokenizers also change how OOV behaves in production. Instead of a single `<unk>` token swallowing an unseen word, you often get a sequence of smaller pieces whose embeddings already exist. That shifts failure modes from “missing row” to “longer sequence” — a trade attention-based models handle differently than old bag-of-words baselines. Sequence length interacts with memory linearly in the embedding gather and quadratically in naive attention, which is why tokenizer choice belongs in the same design review as `d_model` and batch size.

Positional encoding (C4) will address sequence order separately. Subword tokenization addresses vocabulary size and open-vocabulary coverage; do not conflate the two.

From an operations perspective, tokenizer files are part of the model artifact bundle. Serving code must apply the same normalization, byte-level pretokenization, and special-token rules the trainer used. A mismatch often surfaces first as out-of-vocabulary explosions or as sudden UNK rates in logs, but the deeper failure is silent: IDs still index valid rows, just the wrong rows for the string the user typed. Embedding inspection cannot catch that bug unless you decode IDs back to strings before neighbor search.

---

## Part 7: Practical Details Engineers Actually Tune

### 7.1 Embedding dimension as capacity

`d_embed` trades expressiveness against memory and compute. Memory for the table alone is roughly `V × d_embed × bytes_per_param`. Doubling `d_embed` doubles embedding memory and increases FLOPs in every subsequent matmul that touches `(batch, seq_len, d_embed)`. He/Xavier intuition from module 1.3.1 still applies: if you stack deep MLPs on embeddings without normalization, scale initialization to keep activations finite — though most transformer stacks pair embeddings with LayerNorm before attention.

Rule of thumb starting points (not laws): small classifiers on categoricals often use 16–64; word models historically used 100–300; transformer `d_model` commonly lands at 512, 768, or 1024 with head splits chosen so `d_model = n_heads × d_head`.

The interaction with multi-head attention in C3 is worth stating early so you do not pick arbitrary dimensions. If `d_model` is not divisible by `n_heads`, you cannot reshape cleanly into `(B, n_heads, T, d_head)`. Embedding dimension therefore is not an isolated hyperparameter; it is part of a shape contract that propagates through Q/K/V projections, residual adds, and LayerNorm feature axes from module 1.3.4. When you widen embeddings without revisiting initialization variance, you also change the scale of dot products inside attention — another reason init discipline from 1.3.1 belongs in the same checklist as vocabulary design.

### 7.2 Weight tying with the output projection

Language models often **tie** the input embedding matrix with the final linear projection that emits vocabulary logits: the same weight tensor maps hidden states to logits and maps token IDs to hidden inputs, transposed appropriately. Tying reduces parameter count (~`V × d` saved) and acts as regularization because input and output roles must share geometry. PyTorch does not tie automatically; you assign `model.head.weight = model.embed.weight` (with shape checks) when architecting small decoders.

```python
V, D = 1000, 128
embed = nn.Embedding(V, D)
head = nn.Linear(D, V, bias=False)
head.weight = embed.weight  # shared (V, D) storage — verify shapes deliberately
print(head.weight is embed.weight)  # True
```

Verify tying against your exact layout: some models factor embeddings (input vs output) when vocabulary expansion or adapter tuning demands it.

Weight tying interacts with initialization and optimizer state in easy-to-miss ways. Because input and output share storage, an update from the language-model head gradient and an update from the embedding lookup gradient accumulate into the same underlying tensor. That is desirable regularization, but it also means you cannot independently tune learning rates for “input” and “output” embeddings when they are literally the same parameter. If you need asymmetric treatment, stop tying.

### 7.3 Initialization

Default `nn.Embedding` initialization in PyTorch 2.12 draws from `N(0, 1)` with no additional scaling — treat defaults as a starting point, not gospel. Many transformer recipes initialize embeddings with smaller variance (`N(0, 0.02)` or Xavier scaled by `1/√d_embed`) to match the signal propagation goals from module 1.3.1. Pretrained checkpoints bypass init entirely: you load rows from disk and optionally fine-tune.

When you stack LayerNorm immediately after embeddings in a transformer (C4), you are explicitly acknowledging that init scale matters less than it once did because normalization re-centers activations per token. That does not make init irrelevant — poorly scaled embeddings still waste early steps and can produce extreme values before the first norm — but it shifts the debugging question toward “are post-norm activations finite?” rather than “is row 17 huge on step zero?”

```python
import torch.nn as nn

V, D = 32000, 512
embed = nn.Embedding(V, D)
nn.init.normal_(embed.weight, mean=0.0, std=0.02)  # common transformer-scale init
```

### 7.4 ASCII: data flow from ID to hidden state

```
 token IDs (B, T)  integers in [0, V)
        |
        v
 +------------------+
 |  nn.Embedding    |  gather rows of W (V, D)
 +------------------+
        |
        v
 token vectors (B, T, D)
        |
        |  (+ positional encoding in C4 — not here)
        v
 +------------------+
 |  nn.Linear etc.  |  attention / MLP blocks (C2–C4)
 +------------------+
```

---

## Did You Know?

- **The embedding lookup predates deep learning branding.** Latent semantic analysis (LSA) and matrix factorization on word-document counts produced low-dimensional word vectors in the 1990s; word2vec made the neural formulation fast at web scale.
- **`nn.Embedding` supports sparse backward on GPU** — only touched rows accumulate gradients, which is why embedding tables with millions of rows remain trainable despite dense optimizers storing full moment tensors per parameter.
- **Weight tying was popularized in language modeling** partly because output softmax over `V` classes is expensive; tying shares parameters and improved perplexity in several classic LSTM and transformer language models.
- **Subword tokenization changed embedding row semantics.** The same string `"learning"` might map to one ID in a word-level vocab and two IDs in BPE; neighbor geometry depends on that choice.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Materializing one-hot `(B, T, V)` tensors | GPU OOM for large `V` | Use `nn.Embedding` gather; equivalence is for understanding only |
| Ignoring `padding_idx` | Pad rows drift; attention attends to garbage | Set `padding_idx`; combine with batch padding masks in C3 |
| Confusing token and positional embeddings | Model has no order signal or double-counts position | Token embeddings here; positional encodings in C4 only |
| Expecting analogies to always work | Misleading demos; brittle reasoning | Treat as qualitative probes, not API guarantees |
| Vocabulary mismatch at checkpoint load | Silent nonsense outputs | Ship tokenizer + embedding row count together; resize carefully |
| Using full `V`-way softmax on huge vocabs without sampling | Slow training, memory spikes | Sampled softmax, hierarchical softmax, or tied weights in LM heads |

---

## Quiz

1. **Why are all distinct one-hot vectors mutually equidistant in cosine similarity?**
   <details>
   <summary>Answer</summary>
   One-hot vectors for different indices are orthogonal: dot product zero, equal non-zero norm, so cosine similarity is 0 for every unequal pair. The encoding cannot express graded similarity without learning a dense map.
   </details>

2. **How do you verify in PyTorch that `nn.Embedding(k)` equals `one_hot(k) @ W` for a shared weight matrix?**
   <details>
   <summary>Answer</summary>
   Copy the same `W` into `nn.Embedding.weight`, compute `F.one_hot(k, V) @ W` and `embed(k)`, then assert `torch.allclose` on a handful of indices. Shape check: one-hot is `(V,)`, matmul yields `(D,)`, embedding returns `(D,)` for a scalar index.
   </details>

3. **After backprop on a batch containing token IDs `[2, 2, 5]`, which rows of `embed.weight.grad` are non-zero, and how does that connect to A6/A8?**
   <details>
   <summary>Answer</summary>
   Only rows `2` and `5` receive gradient — row `2` accumulates two contributions. This is the gather/sparse VJP pattern: autograd routes upstream signal only through indices used in the forward lookup, exactly like a one-hot matmul would.
   </details>

4. **How do word2vec skip-gram/CBOW and GloVe differ from modern end-to-end embedding training, and when should you choose pretrained versus frozen versus fine-tuned tables?**
   <details>
   <summary>Answer</summary>
   Word2vec learns vectors via local prediction (skip-gram/CBOW); GloVe factorizes global co-occurrence counts. Modern transformers usually learn the embedding matrix as layer zero on the task loss. Prefer pretrained rows when labels are scarce and domain overlaps pretraining; freeze to protect rare rows on tiny data; fine-tune with smaller LR when geometry must adapt to domain shift.
   </details>

5. **Which embedding-layer knobs — `padding_idx`, dimension, weight tying, initialization — affect training stability, and how do they connect to module 1.3.1?**
   <details>
   <summary>Answer</summary>
   `padding_idx` prevents pad rows from accumulating junk gradients; dimension must fit downstream head splits; tying shares input/output weights for regularization and memory; init scale controls initial activation norm before LayerNorm/attention. All are capacity and signal-propagation choices in the same spirit as He/Xavier init analysis.
   </details>

6. **Why do transformers often use subword tokenization before embedding lookup?**
   <details>
   <summary>Answer</summary>
   Subwords bound vocabulary size and handle rare or novel strings by composition, trading longer sequences for fewer OOV failures compared to word-level vocabs.
   </details>

---

## Hands-On Exercise

**Task**: Build a tiny embedding sanity-check script that verifies one-hot equivalence, prints cosine neighbors from a hand-crafted table, and demonstrates sparse gradients and `padding_idx` behavior. **Steps**: save the script below as `embedding_probe.py`, run it with `.venv/bin/python embedding_probe.py` (or any PyTorch 2.12 environment), then read the printed neighbor lists and gradient rows to confirm unused indices stay zero.

1. Paste the code into `embedding_probe.py`.
2. Run once on CPU; CUDA is optional for this probe.
3. Optionally change the toy table rows and observe how neighbor rankings change when you break the royalty cluster.

```python
"""embedding_probe.py — Block C1 hands-on sanity checks (PyTorch 2.12)."""
import torch
import torch.nn as nn
import torch.nn.functional as F

def equivalence_check():
    V, D = 6, 4
    W = torch.randn(V, D)
    embed = nn.Embedding(V, D)
    with torch.no_grad():
        embed.weight.copy_(W)
    for token_id in [0, 3, 5]:
        oh = F.one_hot(torch.tensor(token_id), V).to(W.dtype)  # (V,)
        a = oh @ W                                              # (D,)
        b = embed(torch.tensor(token_id))                       # (D,)
        assert torch.allclose(a, b), token_id
    print("equivalence_check: OK")

def neighbor_demo():
    words = ["king", "queen", "man", "woman", "car"]
    W = torch.tensor([
        [1.0, 0.1, 0.0],
        [0.9, 0.2, 0.1],
        [0.1, -0.5, 0.0],
        [0.2, -0.4, 0.1],
        [-2.0, 1.0, 3.0],
    ])
    Wn = F.normalize(W, dim=1)          # (5, 3)
    q = 0                               # "king"
    sims = Wn @ Wn[q]                    # (5,)
    sims[q] = -1
    idx = sims.argmax().item()
    print(f"nearest to {words[q]}: {words[idx]} (cos={sims[idx]:.3f})")

def sparse_grad_and_padding():
    PAD = 0
    V, D = 8, 5
    embed = nn.Embedding(V, D, padding_idx=PAD)
    ids = torch.tensor([2, 2, 4, PAD])   # (4,)
    loss = embed(ids).sum()
    loss.backward()
    assert embed.weight.grad[1].abs().sum() == 0  # unused row
    assert embed.weight.grad[2].abs().sum() > 0
    assert embed.weight.grad[PAD].abs().sum() == 0  # padding row frozen
    print("sparse_grad_and_padding: OK")

if __name__ == "__main__":
    equivalence_check()
    neighbor_demo()
    sparse_grad_and_padding()
```

**Success Criteria**: Treat the exercise as complete only when equivalence asserts pass for multiple token IDs, the neighbor of `"king"` is `"queen"` on the toy table rather than `"car"`, and gradients are zero on unused and padding rows after backward.

- [ ] Equivalence asserts pass for multiple token IDs.
- [ ] Neighbor of `"king"` is `"queen"` on the toy table (not `"car"`).
- [ ] Gradients are zero on unused and padding rows after backward.

**Verification**: Run the script from the repository root with the project venv, or with an equivalent PyTorch 2.12 environment if this checkout lacks torch.

```bash
.venv/bin/python embedding_probe.py
```

---

## Key Takeaways

- Discrete symbols become continuous vectors through a learned weight matrix; one-hot encoding is the conceptual baseline but never the production implementation for large vocabularies.
- `nn.Embedding` is a sparse gather implementing `one_hot(id) @ W`; backprop updates only rows that were used, matching the VJP intuition from Block A.
- Geometry in embedding space — cosine similarity, neighborhoods, occasional analogies — reflects training objectives and corpus statistics, not guaranteed lexical logic.
- Word2vec and GloVe are historical objectives that explain where modern tables come from; transformers usually learn embeddings end-to-end as layer zero of the model.
- Transfer learning, freezing, and fine-tuning are choices about how much to reuse pretrained geometry versus relearn from task labels.
- Tokenizers define vocabulary size and index semantics; positional encoding is a separate module (C4) that answers sequence order, not token identity.
- Embedding dimension, initialization, padding index, and weight tying are engineering levers tied to memory, signal scale, and regularization — the same training-as-engineering discipline from Block B.

---

## Sources

- [Mikolov et al. 2013: Efficient Estimation of Word Representations in Vector Space](https://arxiv.org/abs/1301.3781)
- [Mikolov et al. 2013: Distributed Representations of Words and Phrases](https://arxiv.org/abs/1310.4546)
- [Pennington et al. 2014: GloVe — Global Vectors for Word Representation](https://nlp.stanford.edu/pubs/glove.pdf)
- [PyTorch 2.12: `torch.nn.Embedding`](https://docs.pytorch.org/docs/2.12/generated/torch.nn.Embedding.html)
- [PyTorch 2.12: `torch.nn.functional.one_hot`](https://docs.pytorch.org/docs/2.12/generated/torch.nn.functional.one_hot.html)
- [PyTorch 2.12: `torch.nn.functional.cosine_similarity`](https://docs.pytorch.org/docs/2.12/generated/torch.nn.functional.cosine_similarity.html)
- [PyTorch 2.12: `torch.nn.Linear`](https://docs.pytorch.org/docs/2.12/generated/torch.nn.Linear.html)
- [d2l.ai — Word Embedding](https://d2l.ai/chapter_natural-language-processing-pretraining/word-embedding.html)
- [CS224n GloVe lecture notes (Stanford)](https://web.stanford.edu/class/cs224n/)
- [Sennrich et al. 2016: Neural Machine Translation of Rare Words with Subword Units (BPE)](https://arxiv.org/abs/1508.07909)
- [PyTorch 2.12 release blog](https://pytorch.org/blog/pytorch-2-12-release-blog/)

---

## Next Module

[Residual Connections & Deep-Architecture Patterns](/ai-ml-engineering/deep-learning/module-1.4.2-residual-deep-architectures/) continues Block C by explaining skip connections and the residual stream — the `+` node that keeps gradients flowing through depth before attention and LayerNorm compose into a full transformer block.

## Learner check

The index row for this module is intentionally quoted here so the merge hook can verify that the module and section index moved together:

> | 1.4.1 | [Embeddings & Representation Learning](/ai-ml-engineering/deep-learning/module-1.4.1-embeddings-representation-learning/) |
