---
title: "Attention from Scratch"
slug: ai-ml-engineering/deep-learning/module-1.4.3-attention-from-scratch
sidebar:
  order: 1005.3
---

> **AI/ML Engineering Track** | Complexity: `[COMPLEX]` | Time: 4-5 Hours

On June 12, 2017, the first version of ["Attention Is All You Need"](https://arxiv.org/abs/1706.03762) was submitted to arXiv. The paper's headline idea sounded almost too simple: sequence models did not have to process tokens one after another with recurrence, and they did not have to slide convolution windows across text. A model could compare every token with every other token directly, turn those comparisons into soft weights, and mix information through matrix multiplication. That mechanism became scaled dot-product attention, and it is the part of the transformer that most often feels mysterious until you write every shape by hand.

This module treats attention as a composition of primitives you already built in Blocks A and B. The query, key, and value projections are ordinary `nn.Linear` layers. The score matrix is a batched matmul. The scale by `sqrt(d_k)` is the same variance-control instinct you used in initialization. The probability distribution is the numerically stable softmax from the loss and precision modules, applied over the key dimension. Multi-head attention does not copy the whole model into several parallel worlds; it splits `d_model` into smaller head dimensions, runs the same operation in parallel subspaces, concatenates the result, and applies one more linear projection.

## Learning Outcomes

- Implement scaled dot-product attention from first principles with shape comments for every matmul, transpose, mask, softmax, and value mix.
- Derive why the `1 / sqrt(d_k)` scale keeps attention logits in a healthier range for softmax gradients.
- Debug causal and padding masks by reasoning about allowed key positions, `float("-inf")` logits, and all-masked-row failures.
- Compare self-attention and cross-attention by identifying where queries, keys, and values come from in each case.
- Implement multi-head attention by splitting `d_model` into `num_heads * d_head`, not by duplicating the full representation per head.

## Why This Module Matters

Attention is the first Block C primitive where a small shape error can silently produce a model that trains, returns tensors of plausible size, and learns the wrong dependency pattern. If you apply softmax over the query dimension instead of the key dimension, each column rather than each row sums to one, so every key distributes itself across queries instead of every query choosing keys. If you mask after softmax, forbidden tokens still influenced the denominator. If you reshape heads without transposing, positions and heads are interleaved incorrectly. These bugs are hard to see from loss curves alone because the model may still have enough parameters to compensate badly.

The payoff is that attention becomes much less magical once you own the tensor algebra. In Block A, you built softmax and backprop by hand; in Block B, you moved that intuition into `nn.Linear`, autograd, initialization, and normalization. Attention combines those ingredients into a parallel lookup table. Each token asks a learned question, compares that question with learned keys from candidate tokens, normalizes the comparison scores, and takes a weighted average of learned values. The full transformer block in the next module will add LayerNorm, residual connections, and an MLP around this mechanism, but the central information-routing step lives here.

Operationally, attention also explains why modern model engineering cares so much about sequence length. The attention matrix for one head is `T x T`, so doubling the context length roughly quadruples the score matrix. Production kernels such as PyTorch's [`scaled_dot_product_attention`](https://docs.pytorch.org/docs/2.12/generated/torch.nn.functional.scaled_dot_product_attention.html) can fuse and tile the work, and FlashAttention-style algorithms reduce memory traffic, but the logical dependency pattern remains pairwise. You need to understand the simple version before optimized versions feel like engineering improvements rather than new mathematics.

## Part 1: From Sequence Bottlenecks to Soft Lookup

An RNN processes a sequence by repeatedly updating a hidden state, which means token `t` depends on token `t - 1`, which depends on token `t - 2`, and so on. That architecture has useful inductive bias, but it also creates a long computational path between distant tokens. If a sentence says "the data pipeline that the team rebuilt after three outages finally stabilized," the word "stabilized" may depend on "pipeline" even though many tokens sit between them. A recurrent model can learn that relationship, but the information has to survive many repeated transformations, and the GPU cannot evaluate all time steps independently because later states wait for earlier states.

Attention changes the shape of the computation. Instead of passing a single summary state through the sequence, it lets each position compare itself with all source positions in one matrix multiplication. For a batch with `B` examples, `T` tokens, and model width `d_model`, the input tensor has shape `(B, T, d_model)`. A self-attention layer produces three learned projections of that input: queries, keys, and values. The projections are ordinary linear layers, so this is the same building block as the PyTorch bridge module, just used three times with separate weights.

Think of attention as a soft dictionary lookup. A dictionary lookup has a query, matched keys, and returned values. A hard lookup asks for exactly one key and receives exactly one value. Attention asks a fuzzy question, scores every key, turns the scores into probabilities, and returns a weighted average of values. A token representing "it" might assign high weight to "animal" and low weight to "street" because its query vector matches the key vector for the entity that can be tired. The output is not a symbolic pointer; it is a continuous mixture that the rest of the network can refine.

The projections separate three jobs that would otherwise interfere with one another. The query says what this position is looking for. The key says how this source position should be found. The value says what content should be passed downstream if the source position is selected. It is tempting to ask why we do not compare queries directly with values. The reason is specialization: a vector optimized for matching does not have to be the same vector optimized for carrying useful content after the match.

```text
Input embeddings x:          (B, T, d_model)
Query projection q = x W_q:  (B, T, d_k)
Key projection   k = x W_k:  (B, T, d_k)
Value projection v = x W_v:  (B, T, d_v)

For self-attention, q, k, and v come from the same x.
For cross-attention, q comes from one sequence and k/v come from another.
```

The important mental move is to stop picturing attention as a special neural-network layer with hidden rules. It is a routing operation made from matrix multiplication and softmax. The trainable parameters live in the projection matrices and the output projection used after multi-head attention. The softmax and masking steps have no learned parameters, but they decide where activation and gradient signal can flow, so they deserve the same care you gave cross-entropy and numerical precision in earlier modules.

## Part 2: Scaled Dot-Product Attention by Hand

Scaled dot-product attention starts with three tensors. In the self-attention case they usually share the same sequence length, but the more general form allows `T_q` query positions and `T_k` key/value positions. The query and key depth must match because the dot product compares them, while the value depth can differ because values are what we mix into the output. With batch dimensions included, the core formula is `Attention(Q, K, V) = softmax((Q K^T) / sqrt(d_k)) V`.

Walk the shapes slowly. `q` has shape `(B, T_q, d_k)`. `k.transpose(-2, -1)` has shape `(B, d_k, T_k)`. Their batched matmul produces scores with shape `(B, T_q, T_k)`, where each row corresponds to one query position and each column corresponds to one key position. Dividing by `sqrt(d_k)` scales the logits without changing the shape. Softmax must run over `dim=-1`, the key dimension, so every query row forms a probability distribution over keys. The final matmul multiplies `(B, T_q, T_k)` weights by `(B, T_k, d_v)` values, producing `(B, T_q, d_v)`.

```python
import math
from typing import Optional

import torch
import torch.nn.functional as F


def scaled_dot_product_attention(
    q: torch.Tensor,
    k: torch.Tensor,
    v: torch.Tensor,
    attention_mask: Optional[torch.Tensor] = None,
) -> tuple[torch.Tensor, torch.Tensor]:
    """
    Teaching implementation of scaled dot-product attention.

    Shapes:
        q: (..., T_q, d_k)
        k: (..., T_k, d_k)
        v: (..., T_k, d_v)
        attention_mask: bool tensor broadcastable to (..., T_q, T_k)
                        True means this key position is allowed.

    Returns:
        output: (..., T_q, d_v)
        attention_weights: (..., T_q, T_k)
    """
    if q.size(-1) != k.size(-1):
        raise ValueError("q and k must have the same d_k")
    if k.size(-2) != v.size(-2):
        raise ValueError("k and v must have the same T_k")

    d_k = q.size(-1)

    # q: (..., T_q, d_k)
    # k.transpose(-2, -1): (..., d_k, T_k)
    # scores: (..., T_q, T_k)
    scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(d_k)

    if attention_mask is not None:
        # attention_mask: broadcastable to scores (..., T_q, T_k)
        # expanded_mask: exactly scores.shape, True means "allowed".
        expanded_mask = torch.broadcast_to(
            attention_mask.to(device=scores.device, dtype=torch.bool),
            scores.shape,
        )
        if not expanded_mask.any(dim=-1).all():
            raise ValueError("attention_mask leaves at least one query with no valid keys")

        # Mask BEFORE softmax so forbidden keys receive exactly zero probability.
        # scores remains (..., T_q, T_k), with disallowed logits set to -inf.
        scores = scores.masked_fill(~expanded_mask, float("-inf"))

    # Softmax over the LAST dimension: keys, not queries.
    # attention_weights: (..., T_q, T_k), rows sum to 1 over T_k.
    attention_weights = F.softmax(scores, dim=-1)

    # attention_weights: (..., T_q, T_k)
    # v: (..., T_k, d_v)
    # output: (..., T_q, d_v)
    output = torch.matmul(attention_weights, v)
    return output, attention_weights
```

The mask convention in this teaching function is intentionally aligned with `F.scaled_dot_product_attention`: boolean `True` means the key is allowed to participate. The guard against all-masked rows is not decorative. A row of all `-inf` logits has no valid probability distribution, so softmax would produce `NaN`. In a language model causal mask, every row can at least attend to itself. In a padding mask, you must ensure every active query has at least one real key, or handle fully padded examples before calling attention.

Here is a tiny concrete example with `B = 1`, `T = 3`, `d_k = 4`, and `d_v = 2`. The numbers are deliberately small enough to inspect. The third query matches the third key most strongly because its raw dot product is `2`, while the first two key comparisons are `1`. After scaling by `sqrt(4) = 2`, the softmax stays smooth rather than collapsing to a hard maximum.

```python
import torch

torch.set_printoptions(precision=4, sci_mode=False)

q = torch.tensor([[
    [1.0, 0.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 1.0],
    [1.0, 1.0, 0.0, 0.0],
]])  # (B=1, T_q=3, d_k=4)

k = torch.tensor([[
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 0.0, 0.0],
    [1.0, 1.0, 0.0, 0.0],
]])  # (B=1, T_k=3, d_k=4)

v = torch.tensor([[
    [10.0, 0.0],
    [0.0, 10.0],
    [5.0, 5.0],
]])  # (B=1, T_k=3, d_v=2)

output, weights = scaled_dot_product_attention(q, k, v)
print(weights)
print(output)

# Expected weights, rounded:
# tensor([[[0.3837, 0.2327, 0.3837],
#          [0.2327, 0.3837, 0.3837],
#          [0.2741, 0.2741, 0.4519]]])
#
# Expected output, rounded:
# tensor([[[5.7548, 4.2452],
#          [4.2452, 5.7548],
#          [5.0000, 5.0000]]])
```

The third output becomes `[5.0, 5.0]` because its weights are symmetric on the first two values and higher on the balanced third value. That result is a good reminder that attention does not return the winning value alone. It returns a convex mixture of value vectors. The row sums are one because softmax normalized over keys; if you accidentally use `dim=-2`, the columns would sum to one, and the meaning of the whole operation would change.

The scale factor is not an arbitrary historical constant. Suppose entries of a query vector and a key vector are roughly independent with mean zero and variance one. Their dot product is a sum of `d_k` products. Each product has roughly unit variance, so the variance of the sum grows roughly like `d_k`. When `d_k = 64`, unscaled dot products have standard deviation near `8`, which often pushes softmax into very peaked distributions. Peaked softmax outputs are not always bad, but if they appear too early and too often, gradients through the losing positions become tiny.

```python
import math
import torch

torch.manual_seed(0)
B, T, d_k = 4096, 1, 64
q = torch.randn(B, T, d_k)  # (B, T, d_k), approximately unit variance
k = torch.randn(B, T, d_k)  # (B, T, d_k), approximately unit variance

# dots: (B, T), one dot product per sample and position
dots = (q * k).sum(dim=-1)
scaled_dots = dots / math.sqrt(d_k)

print(dots.var(unbiased=False))        # around 64
print(scaled_dots.var(unbiased=False)) # around 1
```

This is the same instinct as Xavier or He initialization from the signal-propagation module. You are not trying to make every activation small forever; you are trying to keep the distribution in a range where nonlinearities still transmit useful gradients. Softmax is a nonlinearity too. If the largest logit is far above the others, the distribution becomes almost one-hot, and the derivative for many alternatives approaches zero.

## Part 3: Masks, Causality, and Padding

Masks are how attention represents structural rules without changing tensor sizes. A decoder language model must not let position `i` look at future positions `j > i`, because during generation those future tokens are not known. A batched text model must not let real tokens attend to padding tokens, because padding exists only to make examples share a rectangular tensor shape. In both cases, the correct operation is to set forbidden logits to `float("-inf")` before softmax. After stable softmax subtracts the row maximum and exponentiates, those `-inf` entries become exactly zero probability.

Use an "allowed" mask when writing from-scratch attention: `True` means the key is visible to the query. A causal allowed mask is lower triangular. For `T = 4`, query row `0` can see only key `0`; row `1` can see keys `0` and `1`; row `3` can see all four keys. The shape `(1, 1, T, T)` broadcasts over batch and heads in multi-head attention, while the same logical mask can also be squeezed to `(T, T)` for APIs that accept a two-dimensional mask.

```python
import torch


def make_causal_allowed_mask(seq_len: int, device: torch.device | None = None) -> torch.Tensor:
    # base: (T, T), True at and below the diagonal.
    base = torch.ones(seq_len, seq_len, dtype=torch.bool, device=device).tril()

    # returned mask: (1, 1, T, T), broadcastable to (B, H, T, T).
    return base.unsqueeze(0).unsqueeze(0)


allowed = make_causal_allowed_mask(seq_len=4)
print(allowed[0, 0].to(torch.int))

# tensor([[1, 0, 0, 0],
#         [1, 1, 0, 0],
#         [1, 1, 1, 0],
#         [1, 1, 1, 1]], dtype=torch.int32)
```

A padding mask has a different shape because it usually depends on the batch. If token id `0` is padding, `token_ids.ne(0)` gives `(B, T)` booleans where real tokens are `True`. For attention, those booleans describe key positions, so they should broadcast over query positions and heads. The shape `(B, 1, 1, T)` works with a score tensor `(B, H, T_q, T_k)`: it says every query in an example may attend only to that example's real keys.

```python
import torch


def make_padding_allowed_mask(token_ids: torch.Tensor, pad_id: int = 0) -> torch.Tensor:
    # token_ids: (B, T_k)
    key_is_real = token_ids.ne(pad_id)  # (B, T_k), True for non-padding keys.

    # returned mask: (B, 1, 1, T_k), broadcastable to (B, H, T_q, T_k).
    return key_is_real.unsqueeze(1).unsqueeze(2)


token_ids = torch.tensor([
    [12, 91, 33, 0, 0],
    [44, 17, 29, 81, 5],
])  # (B=2, T=5)

padding_allowed = make_padding_allowed_mask(token_ids, pad_id=0)
print(padding_allowed.shape)  # torch.Size([2, 1, 1, 5])
```

Causal and padding masks combine with logical `and` because a key must satisfy both rules to be visible. This is also where the all-masked-row trap appears. If an entire example is padding, its padding mask contains no valid keys. If you combine that with a causal mask and send it through `masked_fill(..., -inf)`, every query row in that example is invalid. Production training loops normally avoid such batches or remove all-padding examples before the attention call.

```python
B, T = token_ids.shape

causal_allowed = make_causal_allowed_mask(T, device=token_ids.device)     # (1, 1, T, T)
padding_allowed = make_padding_allowed_mask(token_ids, pad_id=0)          # (B, 1, 1, T)
combined_allowed = causal_allowed & padding_allowed                       # (B, 1, T, T)

q = torch.randn(B, 2, T, 8)  # (B, H=2, T_q=T, d_head=8)
k = torch.randn(B, 2, T, 8)  # (B, H=2, T_k=T, d_head=8)
v = torch.randn(B, 2, T, 8)  # (B, H=2, T_k=T, d_v=8)

context, weights = scaled_dot_product_attention(q, k, v, combined_allowed)
print(context.shape)  # torch.Size([2, 2, 5, 8])
print(weights.shape)  # torch.Size([2, 2, 5, 5])
```

Mask semantics are one of the few places where PyTorch APIs intentionally differ. In `F.scaled_dot_product_attention`, a boolean `attn_mask` uses `True` for allowed positions. In `nn.MultiheadAttention`, the documented binary `key_padding_mask` and `attn_mask` use `True` for positions to ignore or block. That is not a mathematical difference in attention; it is an API convention difference. When moving between the from-scratch function, `F.scaled_dot_product_attention`, and `nn.MultiheadAttention`, name masks by their meaning, such as `allowed_mask` or `blocked_mask`, instead of passing around a variable named only `mask`.

## Part 4: Self-Attention, Cross-Attention, and Attention Maps

Self-attention and cross-attention use the same formula. The only difference is where `q`, `k`, and `v` come from. In self-attention, one sequence supplies all three, so every position inside that sequence can read information from the same sequence. In encoder-decoder cross-attention, the decoder state supplies queries, while the encoder output supplies keys and values. The decoder asks, "which source positions matter for this target position?" and then mixes source values into the target representation.

| Mechanism | Query source | Key/value source | Typical use | Score shape |
|---|---|---|---|---|
| Self-attention | Current sequence `x` | Current sequence `x` | Encoder layers, decoder layers with causal mask | `(B, T, T)` |
| Cross-attention | Decoder or target states | Encoder or source states | Translation, retrieval-augmented decoders, multimodal fusion | `(B, T_target, T_source)` |

```text
Self-attention:

    x tokens ---------------> W_q ---- q
       |--------------------> W_k ---- k
       |--------------------> W_v ---- v
    q scores against k, then weights mix v from the same sequence.

Cross-attention:

    target states ----------> W_q ---- q
    source states ----------> W_k ---- k
       |--------------------> W_v ---- v
    target queries score source keys, then weights mix source values.
```

Attention weights form a matrix that learners naturally want to visualize. For a self-attention sequence of length `T`, one head produces a `(T, T)` matrix. Row `i` shows which key positions query position `i` attended to. In a decoder with a causal mask, the upper triangle should be zero because future keys are forbidden. In an encoder without a causal mask, the matrix can be dense because every token can use evidence from both left and right context.

These maps are useful debugging tools, but they are not perfect explanations. A high attention weight means the value vector at that position contributed strongly to this head's output for that query. It does not prove that the token was causally responsible for the final prediction, because later layers, residual streams, MLPs, normalization, and other heads can transform or override the contribution. The ["Attention is not Explanation"](https://arxiv.org/abs/1902.10186) line of work is a healthy warning: inspect attention maps, but validate explanations with interventions, gradients, ablations, or task-specific probes when faithfulness matters.

The most practical use of attention maps while implementing from scratch is shape and mask validation. If the mask is causal, no head should show nonzero probability above the diagonal. If padding positions exist, columns for padded keys should be zero for every query. If all rows look nearly identical at initialization, that may be normal for a tiny random model, but after training on a structured task you should expect heads to specialize. Debug the invariants first; interpret the learned patterns second.

When an attention map looks surprising, prefer controlled experiments over storytelling. Change one token, remove one source position, or freeze a mask and compare the model output before assigning semantic meaning to a bright cell in the matrix. The map is a record of one routing step, not a transcript of model reasoning. That modest interpretation keeps the visualization useful without turning it into an explanation it cannot support by itself.

## Part 5: Multi-Head Attention from Scratch

Multi-head attention repeats scaled dot-product attention across several smaller representation subspaces. The phrase "several heads" can create a dangerous myth: the model does not duplicate the full `d_model` for every head. Instead, it chooses a number of heads `H`, requires `d_model % H == 0`, and sets `d_head = d_model // H`. Each projection still maps `(B, T, d_model)` to `(B, T, d_model)`, but that last dimension is then viewed as `(H, d_head)` and transposed so attention can run as `(B, H, T, d_head)`.

Why split? One head might learn a short-range syntactic pattern, another might learn entity references, and another might track delimiter or position-like structure. Those descriptions are not guaranteed labels, but the architecture gives different heads independent projection parameters and independent softmax distributions. After all heads produce context vectors, the implementation concatenates them back to `(B, T, d_model)` and applies an output projection. That final projection lets the model recombine head outputs instead of merely stacking them.

```python
import math
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F


class MultiHeadAttention(nn.Module):
    """
    From-scratch multi-head self-attention for teaching.

    Mask convention:
        attention_mask is boolean and broadcastable to (B, H, T, T).
        True means the key position is allowed.
    """

    def __init__(self, d_model: int, num_heads: int, dropout: float = 0.0) -> None:
        super().__init__()
        if d_model % num_heads != 0:
            raise ValueError("d_model must be divisible by num_heads")

        self.d_model = d_model
        self.num_heads = num_heads
        self.d_head = d_model // num_heads
        self.dropout = dropout

        # Each projection maps (B, T, d_model) -> (B, T, d_model).
        self.q_proj = nn.Linear(d_model, d_model, bias=False)
        self.k_proj = nn.Linear(d_model, d_model, bias=False)
        self.v_proj = nn.Linear(d_model, d_model, bias=False)
        self.out_proj = nn.Linear(d_model, d_model, bias=False)

    def _split_heads(self, x: torch.Tensor) -> torch.Tensor:
        B, T, _ = x.shape

        # x: (B, T, d_model)
        # view: (B, T, num_heads, d_head), splitting d_model into heads.
        x = x.view(B, T, self.num_heads, self.d_head)

        # transpose: (B, num_heads, T, d_head), so heads are a batch-like axis.
        x = x.transpose(1, 2)
        return x

    def _merge_heads(self, x: torch.Tensor) -> torch.Tensor:
        B, H, T, d_head = x.shape
        if H != self.num_heads or d_head != self.d_head:
            raise ValueError("unexpected head shape")

        # x: (B, num_heads, T, d_head)
        # transpose: (B, T, num_heads, d_head)
        x = x.transpose(1, 2)

        # contiguous before view because transpose changes memory strides.
        # view: (B, T, d_model), concatenating heads back into the model width.
        x = x.contiguous().view(B, T, self.d_model)
        return x

    def forward(
        self,
        x: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        B, T, _ = x.shape

        # x: (B, T, d_model)
        q = self.q_proj(x)  # (B, T, d_model)
        k = self.k_proj(x)  # (B, T, d_model)
        v = self.v_proj(x)  # (B, T, d_model)

        q = self._split_heads(q)  # (B, H, T, d_head)
        k = self._split_heads(k)  # (B, H, T, d_head)
        v = self._split_heads(v)  # (B, H, T, d_head)

        # q: (B, H, T, d_head)
        # k.transpose(-2, -1): (B, H, d_head, T)
        # scores: (B, H, T, T)
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.d_head)

        if attention_mask is not None:
            mask = attention_mask.to(device=scores.device, dtype=torch.bool)
            if mask.dim() == 2:
                # (T, T) -> (1, 1, T, T), broadcast over batch and heads.
                mask = mask.unsqueeze(0).unsqueeze(0)
            elif mask.dim() == 3:
                # (B, T, T) -> (B, 1, T, T), broadcast over heads.
                mask = mask.unsqueeze(1)
            elif mask.dim() != 4:
                raise ValueError("attention_mask must have 2, 3, or 4 dimensions")

            # mask: broadcastable to (B, H, T, T)
            mask = torch.broadcast_to(mask, scores.shape)
            if not mask.any(dim=-1).all():
                raise ValueError("attention_mask leaves at least one query with no valid keys")

            # scores: (B, H, T, T), forbidden logits become -inf before softmax.
            scores = scores.masked_fill(~mask, float("-inf"))

        # weights: (B, H, T, T), softmax over keys for each query in each head.
        weights = F.softmax(scores, dim=-1)
        weights = F.dropout(weights, p=self.dropout, training=self.training)

        # weights: (B, H, T, T)
        # v: (B, H, T, d_head)
        # context: (B, H, T, d_head)
        context = torch.matmul(weights, v)

        # context: (B, H, T, d_head) -> (B, T, d_model)
        merged = self._merge_heads(context)

        # output: (B, T, d_model)
        output = self.out_proj(merged)
        return output, weights


torch.manual_seed(7)
B, T, d_model, num_heads = 2, 5, 32, 4
x = torch.randn(B, T, d_model)                  # (B, T, d_model)
causal_mask = torch.ones(T, T, dtype=torch.bool).tril()  # (T, T)

mha = MultiHeadAttention(d_model=d_model, num_heads=num_heads, dropout=0.0)
output, weights = mha(x, attention_mask=causal_mask)

print(output.shape)  # torch.Size([2, 5, 32])
print(weights.shape) # torch.Size([2, 4, 5, 5])
print(weights[0, 0].triu(diagonal=1).abs().sum()) # tensor(0.)
```

The `contiguous()` call before `view` is not cargo cult. `transpose` returns a view with different strides, so the tensor's logical order no longer matches the contiguous memory layout that `view` expects. You can also use `reshape`, which may copy when needed, but calling `contiguous().view(...)` makes the memory transition explicit for learners. The conceptual operation is concatenate heads in the last dimension, and the code must preserve the order `(B, T, H, d_head)` before flattening `H * d_head` back into `d_model`.

This implementation projects all heads at once, which is how efficient transformer code is usually written. You could create separate `nn.Linear(d_model, d_head)` layers per head and loop over them, but that would be slower and would obscure that the operation is one large matrix multiplication followed by a reshape. The projection weight for `q_proj`, for example, has shape `(d_model, d_model)` in PyTorch's linear-layer convention. Viewing its output as heads partitions the output features; it does not multiply the parameter count by `num_heads` compared with one full-width projection per Q, K, or V.

## Part 6: Production Equivalents and Complexity

The from-scratch implementation is for understanding, not for production throughput. Standard attention needs to materialize or logically compute scores with shape `(B, H, T_q, T_k)`. For self-attention where `T_q = T_k = T`, that is `B * H * T * T` logits before values are mixed. The matmul work is roughly `O(B * H * T^2 * d_head)`, which is the same as `O(B * T^2 * d_model)` after substituting `H * d_head = d_model`. The quadratic term in `T` is why long context length is expensive even when model width stays fixed.

PyTorch's [`F.scaled_dot_product_attention`](https://docs.pytorch.org/docs/2.12/generated/torch.nn.functional.scaled_dot_product_attention.html) computes the same mathematical operation while selecting optimized implementations when possible. The PyTorch 2.12 documentation describes supported implementations including FlashAttention-2, memory-efficient attention, and a C++ implementation matching the formulation. On CUDA, the function may choose a fused kernel based on inputs; on other backends it can fall back to the PyTorch implementation. The important API habit is to pass `dropout_p=0.0` when you do not want dropout, because the function applies dropout according to that argument.

```python
import torch
import torch.nn.functional as F

B, H, T, d_head = 2, 4, 5, 8
q = torch.randn(B, H, T, d_head)  # (B, H, T_q, d_head)
k = torch.randn(B, H, T, d_head)  # (B, H, T_k, d_head)
v = torch.randn(B, H, T, d_head)  # (B, H, T_k, d_head)

# allowed_mask: (1, 1, T, T), True means allowed for F.scaled_dot_product_attention.
allowed_mask = torch.ones(T, T, dtype=torch.bool).tril().unsqueeze(0).unsqueeze(0)

# sdpa_output: (B, H, T_q, d_head)
sdpa_output = F.scaled_dot_product_attention(
    q,
    k,
    v,
    attn_mask=allowed_mask,
    dropout_p=0.0,
    is_causal=False,
)

print(sdpa_output.shape)  # torch.Size([2, 4, 5, 8])
```

You will often see `is_causal=True` instead of an explicit causal mask. That is fine when the only structural rule is causal visibility, and it lets the implementation choose efficient paths. If you also need padding behavior, read the API carefully and make the mask semantics explicit. For the teaching implementation and `F.scaled_dot_product_attention`, boolean `True` means a position participates in attention. That aligns with the "allowed mask" naming used above.

The higher-level module [`nn.MultiheadAttention`](https://docs.pytorch.org/docs/2.12/generated/torch.nn.MultiheadAttention.html) packages the projections, head split, attention, concatenation, and output projection. Set `batch_first=True` for the `(B, T, d_model)` convention used throughout this track. The 2.12 docs state that `embed_dim` is split across `num_heads`, so each head has dimension `embed_dim // num_heads`; that sentence is the official version of the "split, do not duplicate" rule.

```python
import torch
import torch.nn as nn

B, T, d_model, num_heads = 2, 5, 32, 4
x = torch.randn(B, T, d_model)  # (B, T, d_model)

mha = nn.MultiheadAttention(
    embed_dim=d_model,
    num_heads=num_heads,
    dropout=0.0,
    batch_first=True,
)

# nn.MultiheadAttention binary attn_mask uses True for blocked positions.
# blocked_future: (T, T), True above diagonal blocks future keys.
blocked_future = torch.ones(T, T, dtype=torch.bool).triu(diagonal=1)

# output: (B, T, d_model)
# attn_weights: (B, num_heads, T, T) because average_attn_weights=False.
output, attn_weights = mha(
    x,
    x,
    x,
    attn_mask=blocked_future,
    need_weights=True,
    average_attn_weights=False,
)

print(output.shape)       # torch.Size([2, 5, 32])
print(attn_weights.shape) # torch.Size([2, 4, 5, 5])
```

The two production APIs are not obsolete shortcuts around learning the math. They are the same function wrapped in engineering choices: parameter packaging, mask conventions, kernel selection, dropout placement, inference fast paths, and return-shape options. When a model diverges or attends to padding, you debug those choices by returning to the from-scratch shape story: scores are `(query positions, key positions)`, masks alter scores before softmax, softmax normalizes over keys, and values are mixed after the probabilities are valid.

FlashAttention, introduced in ["FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness"](https://arxiv.org/abs/2205.14135), is a performance breakthrough precisely because it keeps the attention function exact while changing how memory is used. Rather than treating the `T x T` score matrix as a naive materialized object, it tiles computation to reduce high-bandwidth-memory traffic. That distinction matters pedagogically: optimized kernels can change speed, memory use, and floating-point rounding details, but they do not change the logical contract you implemented above.

## Part 7: Debugging Attention Like an Engineer

Attention bugs usually hide in the gap between a correct output shape and a correct computation. A tensor can return `(B, T, d_model)` at the end of the layer even if the softmax axis is wrong, the mask convention is inverted, or the heads were flattened in the wrong order. The discipline is to test intermediate invariants, not only final shapes. In the from-scratch version, the most valuable checks are simple: scores should have key positions on the last dimension, attention rows should sum to one before dropout, forbidden key columns should have zero probability after softmax, and the merged head tensor should preserve the original `B, T` ordering.

Start debugging by naming dimensions rather than relying on intuition. In a small notebook or script, set `B = 2`, `H = 3`, `T = 5`, and `d_head = 4`, then print every intermediate shape. If the score tensor is not `(2, 3, 5, 5)`, stop before looking at loss. If a causal mask has shape `(5, 5)` and broadcasts to `(2, 3, 5, 5)`, verify that the same upper-triangular positions are blocked for every batch item and head. If a padding mask has shape `(2, 1, 1, 5)`, verify that it blocks columns, not rows, because padding describes keys that should not be read.

The next check is probability direction. Row sums over keys should be one, so `weights.sum(dim=-1)` should produce a tensor of ones with shape `(B, H, T_q)`. Column sums do not have to be one. This distinction feels small, but it is the difference between "each query chooses source positions" and "each source position distributes itself across destination positions." When learners transpose scores accidentally, the output still has a legal shape because matrix multiplication is permissive across the last two dimensions. The row-sum check catches that class of bug much earlier than a training curve.

Mask checks should use both positive and negative assertions. A positive assertion says every valid row has at least one allowed key before softmax. A negative assertion says every blocked position has exactly zero probability after softmax. For causal attention, `weights.triu(diagonal=1).sum()` should be zero for each head if the weight matrix is two-dimensional, or the equivalent indexed upper triangle should be zero for batched tensors. For padding, columns corresponding to pad tokens should be zero for all query rows. These checks are cheap enough to keep in unit tests around custom attention code.

Numerical checks matter because attention combines large dot products with exponentials. PyTorch's `F.softmax` is implemented with numerical stability in mind, but it cannot rescue a logically invalid row of all `-inf` logits. The stable-softmax habit from the numerical precision module still applies: subtracting a row maximum prevents overflow for finite logits, while using `-inf` for masks guarantees forbidden logits contribute zero after exponentiation. If the row has no finite maximum because every key is masked, the problem is not a softmax implementation detail; the model has no value vector to read for that query.

Gradient debugging follows the same path. Attention is differentiable through the projections, score matmul, softmax, and value matmul for allowed positions. Masked positions do not receive probability mass, so they should not route value-gradient signal through that attention edge. That is exactly what you want for future tokens and padding tokens. If you mistakenly use a large finite negative number instead of `-inf`, it may appear to work in float32, but mixed precision can change how far from zero the forbidden probabilities really are. Using `float("-inf")` states the mathematical rule directly and lets stable softmax do the right thing.

Dropout on attention weights is another source of confusion. During training, dropout can make the post-dropout row sum differ from one because it zeros sampled probabilities and rescales the survivors. That does not mean the softmax axis is wrong. When testing the pure attention invariant, set dropout to zero or put the module in evaluation mode. When testing training behavior, assert shapes and mask zeros rather than exact row sums after dropout. This mirrors the broader training-loop habit from Block B: isolate deterministic math first, then test stochastic regularization separately.

The production APIs add one more layer of debugging: translating mask conventions. If you pass an "allowed" boolean mask into `F.scaled_dot_product_attention`, `True` means participate. If you pass a binary `attn_mask` into `nn.MultiheadAttention`, `True` means block that position. A common migration bug is to create a correct causal allowed mask with `tril()`, pass it unchanged to `nn.MultiheadAttention`, and accidentally block the past while allowing the future. The safest conversion is explicit: `blocked_mask = ~allowed_mask` after squeezing to the shape the API expects, followed by a one-line assertion that the diagonal is not blocked.

Performance debugging starts from the complexity formula rather than from hope. If memory explodes when `T` doubles, remember that the attention score area grows as `T^2`. Reducing `d_model` changes the value-projection and matmul width, but it does not remove the square score matrix. Fused kernels reduce memory traffic and can avoid materializing some intermediates, but they cannot make every pairwise dependency free. When long context is required, the engineering choices become sharper: use optimized SDPA kernels, reduce batch size, apply activation checkpointing, use architectures designed for sparse or windowed attention, or shorten the sequence before it reaches the model.

Shape tests should also cover cross-attention, because it is where many encoder-decoder bugs first appear. In self-attention, `T_q` and `T_k` are the same, so accidental assumptions go unnoticed. In cross-attention, use `T_target = 4` and `T_source = 7` in tests. The score tensor should be `(B, H, 4, 7)` and the output should be `(B, H, 4, d_head)`. A padding mask for the source should have last dimension `7`, not `4`. If a helper function only works when the query and key lengths match, it is not a general attention function yet.

Finally, tie debugging back to the decomposition spine of this track. If the output looks wrong, inspect the three linear projections as ordinary `nn.Linear` layers. If probabilities look wrong, inspect softmax and masks as the stable-softmax problem from Block A and the numerical-stability module. If gradients vanish or explode, inspect logit scale and initialization as signal propagation. If the layer trains but deeper stacks fail, the next module's residual and LayerNorm placement will matter. Attention is a modern primitive, but the debugging moves are the same old moves applied with stricter shape discipline.

There is also a useful habit around synthetic data. Before connecting attention to token embeddings, feed it tensors whose values make a known pattern obvious. One head can receive identity-like keys, another can receive values with easily recognized columns, and a causal mask can use a sequence length small enough to print on screen. If a query intended to read only the previous position produces nonzero future weights, the bug is in the mask or softmax, not in the dataset. Synthetic fixtures prevent you from explaining away a deterministic implementation error as a training-data mystery.

When comparing a from-scratch implementation with `F.scaled_dot_product_attention`, use dropout-free evaluation and tolerances rather than exact string outputs. Fused kernels can choose different accumulation paths, especially on GPU, so tiny floating-point differences are normal. The right comparison is `torch.allclose` with a reasonable tolerance for the dtype, together with the structural invariants that must hold exactly, such as zero probability for blocked positions. If `allclose` fails badly in float32 on a tiny CPU example, inspect mask polarity and scaling before suspecting PyTorch.

Another subtle error appears when learners use `.T` on tensors with more than two dimensions. For a matrix, `.T` means transpose rows and columns. For batched attention tensors, you need `transpose(-2, -1)` so only the last two dimensions swap and all batch-like dimensions remain in place. If `k` has shape `(B, H, T_k, d_head)`, then `k.transpose(-2, -1)` has shape `(B, H, d_head, T_k)`. Any operation that moves `B` or `H` by accident changes which examples or heads are being compared.

Device and dtype mismatches are less conceptual but just as disruptive. Masks created with `torch.ones(T, T)` default to CPU unless you pass a device, while model activations might live on a GPU. The examples convert masks to the score tensor's device before `masked_fill` for that reason. The mask should also be boolean when it represents allowed or blocked positions. Float masks are supported by some PyTorch APIs, but then the values are additive attention biases rather than simple visibility rules, which is a more advanced interface than this module needs.

Padding deserves special attention in loss computation as well as attention. Preventing the model from reading padding keys is only half of the job. If the task predicts a token at every position, the loss function must also ignore padded target positions, usually through an `ignore_index` or an explicit loss mask depending on the head. Otherwise, the attention layer may avoid padding correctly while the training objective still rewards the model for predicting arbitrary pad labels. Keep the data mask, attention mask, and loss mask conceptually separate even when they are derived from the same token ids.

For cross-attention, pay attention to naming in function signatures. A helper that accepts `x` and silently uses it for q, k, and v is a self-attention helper. A cross-attention helper should accept `query_states` and `memory_states` or similarly explicit names. The projections still produce q, k, and v, but their sequence lengths may differ. Good names make it harder to accidentally use target states as values when the decoder is supposed to read from the encoder memory.

Finally, avoid debugging attention only through average loss. Add small observability hooks around the layer while developing: maximum absolute score before softmax, fraction of masked logits, row-sum error before dropout, and maximum forbidden probability after softmax. These numbers do not belong in every production training loop forever, but they are powerful while writing a new implementation. Once the invariants are stable, remove noisy prints and keep focused assertions in tests.

## Did You Know?

- The original transformer paper describes multi-head attention as concatenating per-head attention results and multiplying by an output projection, which is why the final `out_proj` is part of the attention module rather than a separate transformer-block detail.
- PyTorch 2.12's `nn.MultiheadAttention` documentation explicitly says `embed_dim` is split across `num_heads`, so "more heads" at fixed `d_model` means smaller per-head dimensions rather than wider total attention activations.
- Attention weights are row-stochastic after softmax over keys: every query row sums to one unless dropout is applied to the weights during training, in which case the dropped probabilities are rescaled in the usual dropout manner.
- `Tensor.contiguous()` is not about changing mathematical values; it asks PyTorch to store a transposed view in contiguous memory so a later `view` can flatten heads back into `d_model` predictably.

## Common Mistakes

| Mistake | Why it breaks learning | Better approach |
|---|---|---|
| Applying `softmax(scores, dim=-2)` | This normalizes over queries instead of keys, so each key distributes mass across queries and the value mix no longer means "what this query reads." | Use `dim=-1` for scores shaped `(..., T_q, T_k)` and test that `weights.sum(dim=-1)` is all ones. |
| Masking after softmax | Forbidden positions still affect the denominator, and zeroing afterward leaves rows that no longer sum to one. | Use `scores.masked_fill(..., float("-inf"))` before softmax, then verify forbidden weights are zero. |
| Treating all PyTorch boolean masks the same | `F.scaled_dot_product_attention` and `nn.MultiheadAttention` use opposite boolean meanings for common mask arguments. | Name masks `allowed_mask` or `blocked_mask`, and convert at API boundaries instead of guessing. |
| Duplicating `d_model` per head | This changes the parameter and activation size, and it no longer matches transformer multi-head attention. | Split `d_model` into `num_heads * d_head`, run attention in each subspace, then concatenate back to `d_model`. |
| Calling `view` immediately after `transpose` | The logical dimensions are correct, but memory strides are not contiguous, so `view` can fail or mislead learners. | Use `x.transpose(...).contiguous().view(...)` or `reshape(...)` after explaining the memory-layout tradeoff. |
| Ignoring all-masked rows | A row of all `-inf` logits has no valid softmax distribution and can create `NaN` values that spread through the model. | Ensure every query has at least one allowed key, remove all-padding examples, or handle those rows explicitly before attention. |

## Quiz

1. **Why does scaled dot-product attention divide scores by `sqrt(d_k)` instead of by `d_k` or by a learned scalar?**
   <details>
   <summary>Answer</summary>
   If query and key entries have roughly unit variance, their dot product sums about `d_k` random terms, so its variance grows approximately with `d_k` and its standard deviation grows with `sqrt(d_k)`. Dividing by `sqrt(d_k)` brings the logit scale back toward unit variance, which keeps softmax away from unnecessary saturation. A learned scalar could adapt later, but the fixed scale gives the optimization problem a healthier starting geometry.
   </details>

2. **For scores with shape `(B, H, T_q, T_k)`, which dimension should softmax normalize and why?**
   <details>
   <summary>Answer</summary>
   Softmax should normalize `dim=-1`, the `T_k` key dimension. Each query position in each batch and head needs a probability distribution over keys, because the next operation uses those probabilities to take a weighted sum of value vectors. Normalizing over `T_q` would answer a different question: how each key spreads itself across queries.
   </details>

3. **A causal mask for a length-5 decoder sequence has zeros above the diagonal. Why not simply delete future tokens from the tensor for each position?**
   <details>
   <summary>Answer</summary>
   Deleting future tokens would give each query position a different key length, which destroys the rectangular tensor shape that makes batched GPU matmul efficient. A mask preserves the `(B, H, T, T)` score tensor while enforcing the same visibility rule. The model computes in parallel, and forbidden logits become `-inf` before softmax.
   </details>

4. **What is the difference between self-attention and cross-attention in terms of Q, K, and V?**
   <details>
   <summary>Answer</summary>
   In self-attention, queries, keys, and values are projections of the same sequence, so positions inside that sequence read from one another. In cross-attention, queries come from a target or decoder sequence, while keys and values come from a source or encoder sequence. The formula is unchanged; only the source tensors differ.
   </details>

5. **At fixed `d_model = 512`, what happens to `d_head` when `num_heads` increases from 8 to 16?**
   <details>
   <summary>Answer</summary>
   `d_head` changes from `512 / 8 = 64` to `512 / 16 = 32`. Multi-head attention splits the model width across heads. It does not give each head a separate 512-dimensional representation unless you intentionally design a nonstandard architecture with a larger total width.
   </details>

6. **How should you interpret attention maps carefully as routing weights without overstating them as faithful explanations?**
   <details>
   <summary>Answer</summary>
   They show how one head mixed value vectors at one layer, which is useful for checking masks, row sums, and obvious routing patterns. They do not prove causal responsibility for the final prediction, because later heads, MLPs, residual connections, and normalization can alter or override the signal. Faithful explanation requires stronger tests such as ablation, interventions, or gradient-based analysis.
   </details>

7. **You are implementing attention and see scores with shape `(B, H, T_q, T_k)`. Which two assertions would you add before trusting the layer?**
   <details>
   <summary>Answer</summary>
   First, after softmax with dropout disabled, assert that `weights.sum(dim=-1)` is all ones with shape `(B, H, T_q)`, because rows over keys must form distributions. Second, if a mask is present, assert that blocked key positions have zero probability after softmax. For causal self-attention, that usually means checking the upper triangle above the diagonal.
   </details>

8. **When replacing your teaching implementation with production PyTorch calls, why might the same boolean mask need to be inverted?**
   <details>
   <summary>Answer</summary>
   The teaching implementation in this module and `F.scaled_dot_product_attention` use boolean `True` to mean an attention position is allowed. `nn.MultiheadAttention` uses binary masks where `True` means a position should be ignored or blocked. The mathematical attention rule is the same, but the API convention differs, so an allowed mask often becomes `blocked_mask = ~allowed_mask` before calling `nn.MultiheadAttention`.
   </details>

## Hands-On Exercise

Create a file named `attention_shapes_check.py` and run it in an environment with PyTorch installed. The goal is not to train a language model; it is to prove that your attention implementation obeys the shape, mask, and probability invariants. Keep the assertions in place while you experiment. Most attention bugs become obvious when you check row sums, future-token weights, and output shapes for a tiny deterministic batch.

**Success Criteria:**

- [ ] Your from-scratch function returns `output.shape == (B, H, T, d_head)` and `weights.shape == (B, H, T, T)`.
- [ ] With dropout disabled, every attention row sums to one across the last dimension.
- [ ] A causal mask gives exactly zero probability to every future-token position.
- [ ] `F.scaled_dot_product_attention` matches the teaching implementation for the same `q`, `k`, `v`, mask, and `dropout_p=0.0`.

```python
import math
from typing import Optional

import torch
import torch.nn.functional as F


def scaled_dot_product_attention(
    q: torch.Tensor,
    k: torch.Tensor,
    v: torch.Tensor,
    attention_mask: Optional[torch.Tensor] = None,
) -> tuple[torch.Tensor, torch.Tensor]:
    # q: (..., T_q, d_k)
    # k: (..., T_k, d_k)
    # v: (..., T_k, d_v)
    d_k = q.size(-1)

    # scores: (..., T_q, T_k)
    scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(d_k)

    if attention_mask is not None:
        # mask: (..., T_q, T_k), broadcastable; True means allowed.
        mask = torch.broadcast_to(
            attention_mask.to(device=scores.device, dtype=torch.bool),
            scores.shape,
        )
        if not mask.any(dim=-1).all():
            raise ValueError("at least one query has no allowed keys")
        scores = scores.masked_fill(~mask, float("-inf"))

    # weights: (..., T_q, T_k), rows sum over keys.
    weights = F.softmax(scores, dim=-1)

    # output: (..., T_q, d_v)
    output = torch.matmul(weights, v)
    return output, weights


def main() -> None:
    torch.manual_seed(123)
    B, H, T, d_head = 2, 3, 6, 4

    q = torch.randn(B, H, T, d_head)  # (B, H, T_q=T, d_head)
    k = torch.randn(B, H, T, d_head)  # (B, H, T_k=T, d_head)
    v = torch.randn(B, H, T, d_head)  # (B, H, T_k=T, d_v=d_head)

    # allowed: (1, 1, T, T), causal visibility.
    allowed = torch.ones(T, T, dtype=torch.bool).tril().unsqueeze(0).unsqueeze(0)

    output, weights = scaled_dot_product_attention(q, k, v, allowed)

    assert output.shape == (B, H, T, d_head)
    assert weights.shape == (B, H, T, T)
    assert torch.allclose(weights.sum(dim=-1), torch.ones(B, H, T), atol=1e-6)
    assert weights[..., torch.triu(torch.ones(T, T, dtype=torch.bool), diagonal=1)].abs().sum() == 0

    fused = F.scaled_dot_product_attention(
        q,
        k,
        v,
        attn_mask=allowed,
        dropout_p=0.0,
        is_causal=False,
    )
    assert torch.allclose(output, fused, atol=1e-6)

    print("attention invariants passed")


if __name__ == "__main__":
    main()
```

Run it with the repository virtual environment if PyTorch is installed there:

```bash
.venv/bin/python attention_shapes_check.py
```

For an extra check, intentionally change `F.softmax(scores, dim=-1)` to `F.softmax(scores, dim=-2)` and observe which assertion fails. Then restore the correct line and change the causal mask from `tril()` to `triu()`. The exercise is meant to build a debugging reflex: every time you touch attention code, ask which axis is being normalized, which positions are visible, and whether every row has at least one valid key.

## Key Takeaways

Attention is a soft lookup table built from linear projections, a score matmul, a scale, a key-wise softmax, and a value matmul. The Q/K/V names are not decoration; they separate matching from content transport. The score tensor shape tells you almost everything: `(..., T_q, T_k)` means each query row chooses among key columns, so softmax belongs on the last dimension and masks must alter logits before normalization.

Multi-head attention splits `d_model` into smaller head dimensions, runs the same attention calculation in parallel subspaces, and concatenates the results back to `d_model`. The output projection is what lets those subspaces interact again. Production APIs preserve this function while adding fused kernels, parameter packaging, dropout behavior, and mask conventions that you must read carefully.

The next module will wrap this attention mechanism with LayerNorm, residual connections, and an MLP. That transformer block is not a new kind of magic. It is the Block B normalization and residual machinery surrounding the attention operation you just derived from scratch.

## Sources

- [Attention Is All You Need](https://arxiv.org/abs/1706.03762) - Original transformer paper defining scaled dot-product attention and multi-head attention.
- [PyTorch 2.12 Release Blog](https://pytorch.org/blog/pytorch-2-12-release-blog/) - Release note used for the current PyTorch version reference.
- [torch.nn.functional.scaled_dot_product_attention](https://docs.pytorch.org/docs/2.12/generated/torch.nn.functional.scaled_dot_product_attention.html) - Official PyTorch 2.12 API reference for fused scaled dot-product attention and mask semantics.
- [torch.nn.MultiheadAttention](https://docs.pytorch.org/docs/2.12/generated/torch.nn.MultiheadAttention.html) - Official PyTorch 2.12 API reference for packaged multi-head attention, `batch_first`, mask semantics, and head splitting.
- [torch.nn.Linear](https://docs.pytorch.org/docs/2.12/generated/torch.nn.Linear.html) - Official PyTorch reference for the projection layer used to build Q, K, V, and output projections.
- [torch.nn.functional.softmax](https://docs.pytorch.org/docs/2.12/generated/torch.nn.functional.softmax.html) - Official PyTorch reference for the softmax operation used over the key dimension.
- [torch.Tensor.masked_fill](https://docs.pytorch.org/docs/2.12/generated/torch.Tensor.masked_fill.html) - Official PyTorch reference for replacing forbidden logits with `float("-inf")` before softmax.
- [torch.Tensor.contiguous](https://docs.pytorch.org/docs/2.12/generated/torch.Tensor.contiguous.html) - Official PyTorch reference for the memory-layout step used after transposing heads.
- [The Annotated Transformer](https://nlp.seas.harvard.edu/annotated-transformer/) - Walkthrough connecting the paper formulation to readable implementation.
- [FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness](https://arxiv.org/abs/2205.14135) - Paper explaining exact attention kernels optimized around memory traffic.
- [Attention is not Explanation](https://arxiv.org/abs/1902.10186) - Paper motivating caution when interpreting attention maps as faithful explanations.

## Learner check

> | 1.4.3 | [Attention from Scratch](/ai-ml-engineering/deep-learning/module-1.4.3-attention-from-scratch/) |

## Next Module

Next: [The Transformer Block from Scratch](/ai-ml-engineering/deep-learning/module-1.4.4-transformer-block-from-scratch/)
