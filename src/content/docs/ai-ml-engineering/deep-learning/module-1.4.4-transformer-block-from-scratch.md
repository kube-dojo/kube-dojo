---
title: "The Transformer Block from Scratch"
slug: ai-ml-engineering/deep-learning/module-1.4.4-transformer-block-from-scratch
sidebar:
  order: 1005.4
---

> **AI/ML Engineering Track** | Complexity: `[COMPLEX]` | Time: 4-5 hours
>
> **Prerequisites**: Embeddings and representation learning (1.4.1), residual streams (1.4.2), attention from scratch (1.4.3), LayerNorm/RMSNorm (1.3.4), initialization and signal propagation (1.3.1), and numerical stability (1.3.6).
>
> **Primary tools**: PyTorch 2.12, `nn.Embedding`, `nn.MultiheadAttention`, `nn.LayerNorm`, `nn.GELU`, `nn.TransformerEncoderLayer`.

On June 12, 2017, the first version of "Attention Is All You Need" was submitted to arXiv. The paper is remembered for replacing recurrence with attention, but the engineering object that made the idea reusable was not attention alone. It was the repeatable block around attention: token vectors receive position information, attention mixes information across positions, a feed-forward network transforms each position independently, and residual connections keep the running representation trainable through depth. Once you see that pattern, a transformer block stops looking like a new kind of neural network and starts looking like a careful composition of the primitives you already built in Blocks A, B, and the first three modules of Block C.

The boundary for this capstone matters. Module 1.4.3 already owned the internals of scaled dot-product attention: Q/K/V projections, the `1 / sqrt(d_k)` scale, causal and padding masks, and multi-head reshaping. This module treats multi-head attention as a component you can call. The new work is the assembly discipline around it: where positions enter, why the feed-forward network is position-wise, where LayerNorm sits, how the residual stream runs through many blocks, and how the from-scratch block maps to PyTorch's production reference layer.

## Learning Outcomes

- **Implement** sinusoidal and learned positional encodings with shape-correct PyTorch code, then **explain** why attention needs explicit order information before it can distinguish reordered sequences.
- **Assemble** a pre-norm transformer block using `x = x + sublayer(LN(x))`, `nn.MultiheadAttention(batch_first=True)`, a position-wise `Linear -> GELU -> Linear` feed-forward network, dropout, and residual additions.
- **Compare** sinusoidal, learned, rotary, and linear-bias position strategies at the level needed for this block, while reserving RoPE and ALiBi mechanics for the later modern-transformers module.
- **Debug** block-level shape, mask, normalization, and residual-stream failures by tracing tensors through `(B, T, d_model)` comments rather than guessing from the final loss curve.
- **Map** your from-scratch implementation to `nn.TransformerEncoderLayer(norm_first=True, batch_first=True)` and **estimate** the parameter count contributed by attention, feed-forward layers, norms, and embeddings.

## Why This Module Matters

Attention is a powerful information router, but it is not a complete architecture by itself. A bare self-attention layer can let token 17 read token 4, but it does not know the absolute or relative position of either token unless you inject that information. It can mix information across positions, but after the mix every position still needs a nonlinear transformation that expands and recompresses features. It can be stacked, but only if gradients have a clean residual path through the stack. The transformer block is the answer to those assembly problems.

This is where the Block C spine pays off. In module 1.4.1, embeddings turned token IDs into `(B, T, d_model)` vectors. In module 1.4.2, residual streams showed how `x + F(x)` creates a running representation and a gradient highway. In module 1.4.3, attention gave each position a way to read other positions. From Block B, `nn.Linear`, `nn.Module`, `LayerNorm`, initialization, dropout, and numerical stability are already familiar tools. C4 does not add a mysterious new primitive. It shows the exact wiring pattern that turns those pieces into a trainable modern block.

Think of the residual stream as a shared whiteboard that passes from block to block. Attention reads the whiteboard and writes cross-position information onto it. The feed-forward network reads the updated whiteboard at each position and writes feature transformations back onto the same stream. LayerNorm prepares a clean view for each writer, while the residual addition preserves the old content and adds the new contribution. A transformer stack is many writers making controlled updates to one running state.

Hypothetical scenario: a small language model trains for hours and the loss moves, but generated text treats "service A calls service B" and "service B calls service A" as nearly interchangeable. The attention code is correct, the masks are correct, and the embedding table updates. The bug is that position information was accidentally removed during a refactor. Self-attention without positions is permutation-equivariant: if you reorder the input tokens, the outputs reorder in the same way, with no built-in sense that one order should mean something different. Positional encoding is not decorative metadata. It is the part that makes word order visible to a block that otherwise compares sets of vectors.

This module also matters because the exact norm placement affects trainability. The original transformer used post-norm structure, `LN(x + sublayer(x))`. Many modern deep transformer implementations use pre-norm structure, `x + sublayer(LN(x))`, because the residual stream remains an unobstructed path across depth and the sublayer receives normalized input. PyTorch exposes that choice directly through `norm_first=True` in `nn.TransformerEncoderLayer`. If you can assemble both formulas by hand, the production flag becomes obvious rather than magical.

## Part 1: Why a Block Is More Than Attention

Attention mixes information across positions. That is its job. Given a sequence tensor `x` shaped `(B, T, d_model)`, self-attention lets every position read from other positions and returns another tensor shaped `(B, T, d_model)`. The shape preservation is important: it means attention can be placed inside a residual block without changing the width of the residual stream. What attention does not do is apply a rich nonlinear transformation independently to each position after the mix. That role belongs to the position-wise feed-forward network.

The classic transformer block alternates two sublayers. First, multi-head self-attention performs communication across the sequence. Second, a feed-forward network applies the same small MLP to each token position independently. Alternating these two roles gives the architecture its strength. Attention says "which other positions should this position read from?" The feed-forward network says "now that the position has new context, how should its feature vector be transformed?" Residual connections wrap both steps so the block writes additions to a running stream rather than replacing the entire representation at once.

The pre-norm version you will implement can be written compactly as two residual writes to the same stream:

```text
x = x + MultiHeadAttention(LayerNorm(x))
x = x + FeedForward(LayerNorm(x))
```

That two-line formula is the core of this module. The first line uses attention from 1.4.3 as a component. The second line uses a position-wise MLP made from `nn.Linear`, `nn.GELU`, and another `nn.Linear`. The LayerNorm calls are the normalization layers from 1.3.4, and the additions are the residual stream from 1.4.2. If you remove any one part, the block changes character: without attention it cannot communicate across positions, without the feed-forward network it has limited nonlinear feature transformation, without positions it cannot know order, and without residuals it becomes hard to stack deeply.

Here is the division of labor as a compact table that you can use as a debugging map while building the block:

| Component | Input shape | Output shape | Main job |
|---|---:|---:|---|
| Token embedding | `(B, T)` | `(B, T, d_model)` | Convert IDs into vectors learned by backpropagation. |
| Positional encoding | `(B, T, d_model)` | `(B, T, d_model)` | Add order information without changing width. |
| Multi-head attention | `(B, T, d_model)` | `(B, T, d_model)` | Mix information across sequence positions. |
| Feed-forward network | `(B, T, d_model)` | `(B, T, d_model)` | Transform each position's features independently. |
| Residual stream | `(B, T, d_model)` | `(B, T, d_model)` | Carry old state plus controlled updates through depth. |

The table is also a shape contract. Every sublayer must return `(B, T, d_model)` so it can be added back to `x`. Most transformer implementation bugs violate this contract somewhere: a head dimension is not concatenated correctly, a feed-forward layer returns `d_ff` instead of projecting back to `d_model`, or a mask has a shape that broadcasts over the wrong axis. The habit from Block A and B still applies: write the shape before you trust the code.

The same flow is easier to remember as a residual-stream diagram. Read the vertical line as the running state, and read each side branch as a module that computes an update before addition:

```text
token_ids (B, T)
    |
    v
embedding + position                         -> x0 (B, T, d_model)
    |
    +-- LayerNorm -> MultiHeadAttention -----+
    |                                        |
    +<-------------- add attention update ---+ -> x1 (B, T, d_model)
    |
    +-- LayerNorm -> Linear -> GELU -> Linear+
    |                                        |
    +<--------------------- add FFN update --+ -> x2 (B, T, d_model)
```

Do not read that diagram as two independent networks. The attention branch and the FFN branch both read the current residual stream and both write back to it. That is why interpretability discussions often talk about "the residual stream" as a shared state rather than describing each layer as a closed box. Attention heads may add information about other positions, while FFN neurons may add nonlinear feature refinements at the current position, but both additions accumulate in the same vector space. This is also why width consistency matters so much: the stream is only a stream if every writer agrees on its dimensionality.

The word "block" is useful because the pattern repeats. A single attention call can route context once, but a stack of blocks lets the model iteratively refine representations. Early blocks may resolve local syntax or nearby dependencies; later blocks can use those refined states to reason about longer-range relationships. You should be careful not to overinterpret any fixed layer-by-layer story, because learned models specialize in messy ways, but the architectural possibility comes from the repetition: communicate across positions, transform per position, preserve the stream, repeat.

## Part 2: Positional Encoding Adds Order

Self-attention by itself is permutation-equivariant. If two sequences contain the same token embeddings in a different order, the same attention operation will process the same set of vectors and produce correspondingly reordered outputs. That property is mathematically clean, but language, time series, logs, traces, and source code all depend on order. "Dog bites man" and "man bites dog" contain the same token identities with different structure. The transformer block needs a way to add position information to the token vectors before attention sees them.

The original transformer used sinusoidal positional encoding. For position `pos` and feature-pair index `i`, the paper defines this pair of equations:

```text
PE(pos, 2i)     = sin(pos / 10000^(2i / d_model))
PE(pos, 2i + 1) = cos(pos / 10000^(2i / d_model))
```

The even dimensions use sine waves and the odd dimensions use cosine waves. The denominator changes by frequency: early dimensions vary quickly across positions, while later dimensions vary slowly. The result is a fixed table of shape `(max_len, d_model)` where each row is a deterministic code for one position. You add that row to the token embedding at the same position, so the representation carries both token identity and location in the same `d_model`-wide vector.

The frequency ladder is the main idea worth slowing down for. If every feature dimension used the same sine wave, two positions separated by the wave period would look identical along that feature. By spreading frequencies across dimensions, the encoding gives the model several clocks at once: fast clocks distinguish nearby positions, while slow clocks remain useful over longer spans. The model is not handed a symbolic integer position. It is handed a vector whose components vary predictably with position, and the attention and FFN weights can learn linear combinations of those components.

For a tiny `d_model = 8`, the first pair uses the fastest frequency because the exponent is `0 / 8`, so the denominator is `1`. The next pair uses `2 / 8`, then `4 / 8`, then `6 / 8`, which progressively slows the wave. Position 0 always has sine entries of 0 and cosine entries of 1. Position 1 has a large change in the first pair and a smaller change in later pairs. The important verification is the exponent: the code must step by even feature indices, not by pair numbers alone.

The implementation below makes the shape and dtype behavior explicit. The positional table is not a trainable parameter, so it should be registered as a buffer. A buffer moves with the module across devices and appears in module state, but it does not receive gradients from `loss.backward()`. That distinction connects directly to Block B's `nn.Module` model: parameters are optimized, buffers are state.

```python
import math

import torch
import torch.nn as nn


class SinusoidalPositionalEncoding(nn.Module):
    """Fixed sinusoidal positions added to token embeddings."""

    def __init__(self, d_model: int, max_len: int = 4096, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(dropout)

        # pe: (max_len, d_model), one row per position and one column per feature.
        pe = torch.zeros(max_len, d_model, dtype=torch.float32)

        # position: (max_len, 1), column vector [0, 1, 2, ...].
        position = torch.arange(max_len, dtype=torch.float32).unsqueeze(1)

        # div_term: (ceil(d_model / 2),), frequencies for even feature columns.
        div_term = torch.exp(
            torch.arange(0, d_model, 2, dtype=torch.float32)
            * (-math.log(10000.0) / d_model)
        )

        # position * div_term: (max_len, 1) * (ceil(d_model / 2),) -> (max_len, ceil(d_model / 2)).
        pe[:, 0::2] = torch.sin(position * div_term)  # even columns: (max_len, ceil(d_model / 2))

        # Odd columns can be one shorter when d_model is odd, so slice div_term to the destination width.
        odd_width = pe[:, 1::2].shape[1]
        pe[:, 1::2] = torch.cos(position * div_term[:odd_width])  # odd columns: (max_len, floor(d_model / 2))

        # pe: (1, max_len, d_model), broadcastable across batch B.
        self.register_buffer("pe", pe.unsqueeze(0))

    def forward(self, token_embeddings: torch.Tensor) -> torch.Tensor:
        # token_embeddings: (B, T, d_model)
        B, T, d_model = token_embeddings.shape
        if T > self.pe.size(1):
            raise ValueError(f"sequence length {T} exceeds max_len {self.pe.size(1)}")
        if d_model != self.pe.size(2):
            raise ValueError(f"input width {d_model} does not match positional width {self.pe.size(2)}")

        # positions: (1, T, d_model), converted to the same dtype as token embeddings.
        positions = self.pe[:, :T, :].to(dtype=token_embeddings.dtype)

        # token_embeddings + positions: (B, T, d_model) + (1, T, d_model) -> (B, T, d_model).
        return self.dropout(token_embeddings + positions)
```

The exponent is easy to get subtly wrong. The term `torch.arange(0, d_model, 2)` represents the even feature indices `2i`, so multiplying it by `-log(10000) / d_model` implements `10000^(-2i / d_model)`. The code multiplies positions by that inverse denominator, which is equivalent to `pos / 10000^(2i / d_model)`. Using `i / d_model` instead of `2i / d_model` doubles the frequency spacing and changes the intended table.

You can inspect the first positions without plotting, which is often enough to catch a transposed table or wrong exponent:

```python
torch.set_printoptions(precision=4, sci_mode=False)

d_model = 8
pos = SinusoidalPositionalEncoding(d_model=d_model, max_len=4, dropout=0.0)

# encoded_positions: (1, max_len=4, d_model=8)
encoded_positions = pos.pe
print(encoded_positions[0, 0])  # (d_model,), position 0 is [0, 1, 0, 1, ...].
print(encoded_positions[0, 1])  # (d_model,), position 1 has several frequencies.
print(encoded_positions.shape)  # torch.Size([1, 4, 8])
```

The sinusoidal choice has one elegant property: relative offsets can be represented by linear transformations of the encoding. Sine and cosine obey angle-addition identities, so the encoding at `pos + k` is a fixed linear function of the encoding at `pos` for any fixed offset `k`. You do not need to derive those identities to use the block, but they explain why the original paper expected the model to learn relative-position behavior from a fixed absolute table.

There is also a practical extrapolation story. A sinusoidal table can be generated for positions longer than those seen during training, as long as the model's learned weights handle the new range. That does not guarantee reliable long-context behavior, because training distribution still matters, but it is different from a learned table with a hard maximum row count. The fixed table gives the architecture a deterministic position code; the learned weights decide how to use it.

Buffers deserve one more practical note. If you store the table as a plain Python attribute, it may stay on CPU when the rest of the model moves to CUDA or another accelerator. If you store it as a parameter, the optimizer will try to update it and the checkpoint will imply that it is trainable. `register_buffer` is the middle path: the tensor follows the module's device and dtype movement, but it is not returned by `model.parameters()`. That distinction prevents subtle device mismatches when a training loop calls `model.to(device)` and then feeds GPU token batches through the encoder.

## Part 3: Learned Positions and Modern Pointers

Many influential transformer models use learned positional embeddings instead of fixed sinusoidal rows. The implementation is simpler: create `nn.Embedding(max_len, d_model)`, build a position ID tensor `0..T-1`, look up position rows, and add them to token embeddings. Gradients flow into the position table just as they flow into the token embedding table from module 1.4.1. The block sees the same final shape, `(B, T, d_model)`.

```python
class LearnedPositionalEncoding(nn.Module):
    """Learned absolute positions added to token embeddings."""

    def __init__(self, d_model: int, max_len: int = 4096, dropout: float = 0.1):
        super().__init__()
        self.position_embedding = nn.Embedding(max_len, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, token_embeddings: torch.Tensor) -> torch.Tensor:
        # token_embeddings: (B, T, d_model)
        B, T, d_model = token_embeddings.shape
        if T > self.position_embedding.num_embeddings:
            raise ValueError(f"sequence length {T} exceeds learned max_len")

        # position_ids: (T,), one integer position per sequence slot.
        position_ids = torch.arange(T, device=token_embeddings.device)

        # position_ids expanded: (B, T), so each batch item receives the same absolute positions.
        position_ids = position_ids.unsqueeze(0).expand(B, T)

        # positions: (B, T, d_model), learned rows from the position table.
        positions = self.position_embedding(position_ids)

        # token_embeddings + positions: (B, T, d_model) + (B, T, d_model) -> (B, T, d_model).
        return self.dropout(token_embeddings + positions)
```

The tradeoff is capacity versus extrapolation. Learned absolute positions are easy for a model to adapt to the training distribution. If position 12 often behaves differently from position 512, the table can store that difference directly. The cost is that the table has a fixed size, and rows beyond the trained range have no learned meaning unless you extend or interpolate them. Sinusoidal positions avoid trainable rows and can be generated at arbitrary lengths, but the model has less freedom to invent its own absolute position geometry.

Learned absolute positions are especially natural when the context window is a product constraint rather than an open-ended mathematical promise. If a model is trained, validated, and deployed with a fixed maximum sequence length, then a learned table can specialize to that window and the simplicity is attractive. BERT-style encoders and GPT-style decoders made this pattern familiar: token rows and position rows are both embedding tables, and their sum becomes the initial residual stream. The risk appears when the deployment context changes. Extending the table from 512 to 4096 rows is not the same as teaching the model to use positions 513 through 4095 reliably.

Modern production models often move beyond both simple absolute choices. Rotary positional embeddings, or RoPE, rotate query and key features so relative offsets affect attention scores directly. ALiBi adds linear biases to attention logits so farther keys receive distance-dependent penalties. Those mechanisms belong to module 1.10, where the focus is modern transformer variants. For C4, the important point is narrower: every transformer block needs some order signal, and the simplest two are fixed sinusoidal rows and learned absolute rows added before the first block.

A useful rule of thumb is to choose the position mechanism that matches the learning problem. If you are teaching the original transformer or building a small encoder for controlled experiments, sinusoidal encoding is transparent and parameter-free. If you are training a BERT-like encoder or a GPT-style decoder with a known context window, learned absolute embeddings are straightforward and common. If you are designing long-context systems, you should investigate relative, rotary, or bias-based methods rather than assuming an absolute table will extrapolate safely.

The addition point is the same either way, so this smoke test works for the block no matter which absolute position strategy you choose:

```python
vocab_size = 1000
B, T, d_model = 2, 6, 32

token_ids = torch.randint(0, vocab_size, (B, T))  # (B, T)
token_embedding = nn.Embedding(vocab_size, d_model)  # weights: (vocab_size, d_model)
positional_encoding = SinusoidalPositionalEncoding(d_model=d_model, max_len=128, dropout=0.0)

# token_vectors: (B, T, d_model)
token_vectors = token_embedding(token_ids) * math.sqrt(d_model)

# x: (B, T, d_model), token identity plus positional information.
x = positional_encoding(token_vectors)
print(x.shape)  # torch.Size([2, 6, 32])
```

The multiplication by `sqrt(d_model)` follows the original transformer implementation pattern: token embeddings are scaled before fixed positions are added so their magnitude is not too small relative to the positional signal at initialization. Learned systems vary in initialization and scaling details, but the shape contract does not change. Positions are added before the stack, not concatenated to double the width, because concatenation would change `d_model` and break the residual additions unless every later layer were redesigned.

A useful debugging check is to temporarily zero out token embeddings or position embeddings and observe what changes. If you zero token embeddings and keep positions, the model only sees where slots are, not what symbols occupy them. If you zero positions and keep token embeddings, the model sees the bag of token identities but loses order before attention. Neither ablation should be your production model, but both are quick ways to prove that the two signals enter through the addition you intended.

## Part 4: The Position-Wise Feed-Forward Network

After attention mixes information across positions, the block needs a nonlinear transformation that operates on each position's feature vector. The position-wise feed-forward network is that transformation. It is an MLP applied independently and identically at every sequence position:

```text
FFN(x) = Linear(d_model, d_ff) -> GELU -> Linear(d_ff, d_model)
```

The word "position-wise" means there is no communication between token positions inside this sublayer. If `x` has shape `(B, T, d_model)`, PyTorch's `nn.Linear` applies to the last dimension and preserves the leading batch and sequence dimensions. The first linear expands each position from `d_model` to `d_ff`; the second projects it back to `d_model` so the residual addition can happen. The conventional expansion is `d_ff = 4 * d_model`, though smaller and larger ratios appear in different model families.

```python
class PositionWiseFeedForward(nn.Module):
    """Transformer feed-forward sublayer applied independently per position."""

    def __init__(self, d_model: int, d_ff: int | None = None, dropout: float = 0.1):
        super().__init__()
        d_ff = d_ff or 4 * d_model
        self.net = nn.Sequential(
            nn.Linear(d_model, d_ff),   # (B, T, d_model) -> (B, T, d_ff)
            nn.GELU(),                  # (B, T, d_ff) -> (B, T, d_ff)
            nn.Dropout(dropout),        # (B, T, d_ff) -> (B, T, d_ff)
            nn.Linear(d_ff, d_model),   # (B, T, d_ff) -> (B, T, d_model)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, T, d_model)
        return self.net(x)  # (B, T, d_model)
```

The FFN often holds more parameters than attention. With biases ignored for a simple estimate, multi-head self-attention uses four `d_model x d_model` matrices: Q, K, V, and output projection, for about `4 * d_model^2` weights. The feed-forward network uses `d_model x d_ff` plus `d_ff x d_model`, for `2 * d_model * d_ff`. If `d_ff = 4 * d_model`, that is about `8 * d_model^2`, roughly twice the attention projection count. Attention gets the architectural spotlight because it routes information across positions, but the FFN is a major capacity store.

That parameter split explains why many model variants experiment with FFN design. Some replace the simple GELU MLP with gated variants such as SwiGLU, some change the expansion ratio, and some use mixtures of experts so only part of a large FFN activates for each token. Those are advanced variations, but the baseline lesson remains stable: the FFN is where each position's context-enriched vector gets a private nonlinear transformation. Attention asks other positions for information; the FFN decides how to process the answer at this position.

GELU is the common activation in many transformer families because it gates values smoothly instead of hard-thresholding like ReLU. You studied the activation zoo in module 1.1.4, so connect the intuition directly: ReLU says negative values become exactly zero; GELU weights values by a smooth Gaussian cumulative shape, letting small negative inputs pass with reduced magnitude. The practical lesson is not that GELU is always superior. It is that transformer FFNs are ordinary MLPs, and their activation choice follows the same signal, gradient, and nonlinearity tradeoffs you already learned.

A quick shape check makes the position-wise independence visible because PyTorch preserves the leading batch and sequence axes:

```python
B, T, d_model, d_ff = 2, 5, 16, 64
ffn = PositionWiseFeedForward(d_model=d_model, d_ff=d_ff, dropout=0.0)

x = torch.randn(B, T, d_model)  # (B, T, d_model)
y = ffn(x)                      # (B, T, d_model)

print(x.shape)  # torch.Size([2, 5, 16])
print(y.shape)  # torch.Size([2, 5, 16])
```

No attention mask appears in the FFN because the FFN does not look across positions. Padding still matters for the loss and for attention, but the same MLP can safely run on every padded slot as long as you ignore padded outputs downstream. That separation of concerns is part of the transformer's clean design: attention handles communication and masking; the FFN handles per-position feature computation.

The independence is sometimes misunderstood as "the FFN is unimportant for sequence modeling." That is backwards. The FFN does not communicate across positions, but it transforms the information that attention just gathered. A token's vector after attention may contain evidence from several other positions; the FFN can then turn that evidence into features useful for the next block. Communication and computation alternate. If you remove the FFN, the model can still mix values, but it loses a large nonlinear workspace where many learned features are formed.

## Part 5: Pre-Norm, Post-Norm, and the Residual Stream

There are two common ways to place normalization around transformer sublayers. The original paper used this post-norm formula, where normalization follows the residual addition:

```text
x = LayerNorm(x + sublayer(x))
```

Many modern deep transformer stacks use this pre-norm formula, where normalization prepares the sublayer input before the update is added:

```text
x = x + sublayer(LayerNorm(x))
```

Both preserve the `(B, T, d_model)` residual stream, but they expose different gradient paths. In post-norm, the residual addition is immediately passed through LayerNorm before the next block. In pre-norm, the residual stream itself remains the direct object being added through depth, while LayerNorm prepares the sublayer input. That means the identity path from module 1.4.2 is cleaner: the stream can pass from one block to the next through additions without being transformed on the shortcut itself.

The LayerNorm paper introduced normalization across features within a sample, which fits sequence models because it does not depend on large batch statistics. The transformer architecture then used LayerNorm to stabilize sublayer inputs and outputs. Later analysis of norm placement showed why pre-norm transformers often train more stably at depth: placing normalization inside the residual branch improves gradient behavior at initialization. The full story is mathematical, but the implementation lesson is simple enough to carry: for deep stacks, prefer pre-norm unless you have a specific reason to reproduce an original post-norm baseline.

RMSNorm is a related modern choice. Instead of subtracting the mean and dividing by standard deviation as LayerNorm does, RMSNorm scales by root mean square and usually omits mean-centering. You covered that distinction in module 1.3.4. This module uses `nn.LayerNorm` because PyTorch's reference transformer layer exposes it directly and because it is the clearest teaching path. When you read modern model code that swaps in RMSNorm, the residual formula remains recognizable: normalize the stream, run the sublayer, add the result back.

The dropout placement also matters. In the reference pattern, dropout is applied to the sublayer output before the residual addition during training. That makes the residual stream robust to missing residual updates, while the identity path remains present. You should not apply dropout to the shortcut itself unless you are intentionally experimenting with stochastic depth or a related depth-regularization method. The ordinary transformer block keeps the shortcut reliable.

Here is the pre-norm skeleton without attention internals, written as pseudocode so the residual-stream dataflow is the only thing in focus:

```text
# x: (B, T, d_model), the residual stream entering this block.
# normed_for_attention: (B, T, d_model), normalized view for the attention sublayer.
normed_for_attention = ln1(x)

# attention_update: (B, T, d_model), cross-position update from MHA.
attention_update = self_attention(normed_for_attention)

# x: (B, T, d_model), residual stream after attention write.
x = x + dropout(attention_update)

# normed_for_ffn: (B, T, d_model), normalized view for the feed-forward sublayer.
normed_for_ffn = ln2(x)

# ffn_update: (B, T, d_model), per-position nonlinear update.
ffn_update = feed_forward(normed_for_ffn)

# x: (B, T, d_model), residual stream after FFN write.
x = x + dropout(ffn_update)
```

That skeleton is the residual-stream mental model in code. Every sublayer reads a normalized view of the stream and writes an update back through addition. The stream width never changes inside the block. If a sublayer returns the wrong width, addition fails immediately. If it returns the right width but was computed from the wrong axes, the model may run but learn the wrong structure. Shape comments prevent both errors.

The final normalization after a stack is a related but separate choice. In many pre-norm stacks, each block normalizes the input to its sublayers, but the output of the final residual addition is not automatically normalized for the task head. A final `nn.LayerNorm(d_model)` gives the classifier, language-model head, or downstream pooling operation a well-scaled view of the completed stream. That final norm does not replace the two norms inside each block; it prepares the stack output after all residual writes have accumulated.

When you compare post-norm and pre-norm diagrams, resist the urge to call one universally correct. Post-norm was part of the original architecture and can work well with the right depth, learning-rate schedule, and warmup. Pre-norm is favored for many deeper stacks because it is forgiving and keeps the identity path clearer. The practical skill is to recognize which formula a codebase implements. A misplaced LayerNorm can make two models with the same parameter count behave very differently during optimization.

## Part 6: Assemble a TransformerBlock

Now we can build the block. To respect the boundary with module 1.4.3, this implementation uses `nn.MultiheadAttention` as the attention component rather than re-deriving Q/K/V and scaled dot-product attention. We still make the mask semantics explicit because PyTorch's `nn.MultiheadAttention` uses `True` to mean "blocked" for boolean masks, while `F.scaled_dot_product_attention` uses `True` to mean "allowed" in its boolean attention mask. Naming the mask `blocked_mask` avoids the common inversion bug.

```python
class TransformerBlock(nn.Module):
    """Pre-norm transformer encoder-style block."""

    def __init__(
        self,
        d_model: int,
        num_heads: int,
        d_ff: int | None = None,
        dropout: float = 0.1,
    ):
        super().__init__()
        if d_model % num_heads != 0:
            raise ValueError("d_model must be divisible by num_heads")

        self.ln1 = nn.LayerNorm(d_model)
        self.self_attn = nn.MultiheadAttention(
            embed_dim=d_model,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True,
        )
        self.dropout1 = nn.Dropout(dropout)

        self.ln2 = nn.LayerNorm(d_model)
        self.ffn = PositionWiseFeedForward(d_model=d_model, d_ff=d_ff, dropout=dropout)
        self.dropout2 = nn.Dropout(dropout)

    def forward(
        self,
        x: torch.Tensor,
        blocked_attn_mask: torch.Tensor | None = None,
        key_padding_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        # x: (B, T, d_model)
        # blocked_attn_mask: optional (T, T), True means this query-key pair is blocked.
        # key_padding_mask: optional (B, T), True means this key position is padding and ignored.

        # normed: (B, T, d_model), normalized view for attention.
        normed = self.ln1(x)

        # attn_out: (B, T, d_model), attention update computed from normed stream.
        attn_out, _ = self.self_attn(
            query=normed,                   # (B, T, d_model)
            key=normed,                     # (B, T, d_model)
            value=normed,                   # (B, T, d_model)
            attn_mask=blocked_attn_mask,    # (T, T) or None
            key_padding_mask=key_padding_mask,  # (B, T) or None
            need_weights=False,
        )

        # x: (B, T, d_model), residual stream after attention update.
        x = x + self.dropout1(attn_out)

        # normed: (B, T, d_model), normalized view for position-wise FFN.
        normed = self.ln2(x)

        # ffn_out: (B, T, d_model), per-position nonlinear update.
        ffn_out = self.ffn(normed)

        # x: (B, T, d_model), residual stream after FFN update.
        x = x + self.dropout2(ffn_out)
        return x
```

Walk through the forward pass once without thinking about attention internals. `ln1` normalizes the current stream, but the residual branch still adds back to the original `x`, not to a detached copy or a replaced tensor. `self_attn` receives the same normalized tensor as query, key, and value because this is self-attention. The attention output is dropped out during training and added to the stream. Then `ln2` normalizes the updated stream, the FFN computes a per-position update, and the second dropout-plus-add produces the block output. That sequence is exactly `x = x + MHA(LN(x)); x = x + FFN(LN(x))`.

The `need_weights=False` argument is intentional in production-style code. It tells `nn.MultiheadAttention` that you do not need the attention matrix returned for inspection, which allows optimized scaled-dot-product attention paths where available. When teaching attention internals in 1.4.3, returning weights was useful because it let you inspect row sums and masks. In a block assembly module, returning weights from every layer can waste memory and distract from the residual path. You can turn weights back on for debugging, but do it deliberately.

The same class works for bidirectional encoder-style attention and decoder-style causal attention. The block structure is unchanged; only the mask differs. For an encoder, you usually omit the causal mask so every real token can read every other real token. For a decoder language model, you block future keys by passing an upper-triangular boolean mask:

```python
def make_causal_blocked_mask(seq_len: int, device: torch.device | None = None) -> torch.Tensor:
    # mask: (T, T), True above the diagonal means "future key is blocked".
    return torch.ones(seq_len, seq_len, dtype=torch.bool, device=device).triu(diagonal=1)


B, T, d_model, num_heads = 2, 6, 32, 4
block = TransformerBlock(d_model=d_model, num_heads=num_heads, dropout=0.0)

x = torch.randn(B, T, d_model)  # (B, T, d_model)
causal_mask = make_causal_blocked_mask(T, x.device)  # (T, T)

y_encoder = block(x)                                  # (B, T, d_model), bidirectional.
y_decoder_like = block(x, blocked_attn_mask=causal_mask)  # (B, T, d_model), causal.

print(y_encoder.shape)      # torch.Size([2, 6, 32])
print(y_decoder_like.shape) # torch.Size([2, 6, 32])
```

Notice what did not appear: no Q/K/V derivation, no attention score matrix derivation, and no head splitting code. You already built those in 1.4.3. The lesson here is assembly correctness. The attention component must return a residual update with the same stream width; the FFN must project back to the same stream width; LayerNorm must normalize the feature dimension; masks must match PyTorch's boolean semantics.

The padding mask belongs at the attention call because padding positions should not be used as keys. If `tokens` has shape `(B, T)` and `pad_id = 0`, then `tokens.eq(0)` has shape `(B, T)` and `True` marks keys to ignore in `nn.MultiheadAttention`. You still usually mask the loss at padded query positions, because the block may compute outputs for padding slots even if they are not allowed to serve as keys.

A reliable block debugging routine is to test one concern at a time. First, run without masks and confirm `(B, T, d_model)` enters and leaves the block unchanged. Second, add a causal mask and confirm the output shape is still unchanged. Third, add a padding mask and confirm the mask uses `True` for ignored keys in `nn.MultiheadAttention`. Fourth, switch the module to `.eval()` and confirm dropout no longer changes repeated outputs for the same input. These checks are small, but they catch the most expensive class of transformer bugs before you start interpreting a training curve.

## Part 7: Stack Blocks and Match PyTorch's Production Layer

A transformer encoder stack starts with token IDs, embeds them, adds positions, runs `N` blocks, applies a final normalization, and optionally projects to logits. The residual stream is the same tensor shape through every block: `(B, T, d_model)`. Stacking is therefore just a `ModuleList` loop, not a new mathematical primitive.

```python
class TinyTransformerEncoder(nn.Module):
    """Small transformer encoder assembled from the block above."""

    def __init__(
        self,
        vocab_size: int,
        d_model: int = 64,
        num_heads: int = 4,
        num_layers: int = 2,
        d_ff: int | None = None,
        max_len: int = 256,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.d_model = d_model
        self.token_embedding = nn.Embedding(vocab_size, d_model)
        self.position = SinusoidalPositionalEncoding(d_model=d_model, max_len=max_len, dropout=dropout)
        self.blocks = nn.ModuleList(
            [
                TransformerBlock(
                    d_model=d_model,
                    num_heads=num_heads,
                    d_ff=d_ff,
                    dropout=dropout,
                )
                for _ in range(num_layers)
            ]
        )
        self.final_norm = nn.LayerNorm(d_model)
        self.output_head = nn.Linear(d_model, vocab_size)

    def forward(
        self,
        token_ids: torch.Tensor,
        key_padding_mask: torch.Tensor | None = None,
        causal: bool = False,
    ) -> torch.Tensor:
        # token_ids: (B, T), integer token IDs.
        B, T = token_ids.shape

        # x: (B, T, d_model), token lookup scaled before positions are added.
        x = self.token_embedding(token_ids) * math.sqrt(self.d_model)

        # x: (B, T, d_model), token identity plus position information.
        x = self.position(x)

        # blocked_mask: (T, T) or None, True means future keys are blocked.
        blocked_mask = make_causal_blocked_mask(T, token_ids.device) if causal else None

        # x: (B, T, d_model), residual stream preserved through every block.
        for block in self.blocks:
            x = block(
                x,
                blocked_attn_mask=blocked_mask,
                key_padding_mask=key_padding_mask,
            )

        # x: (B, T, d_model), final normalized residual stream.
        x = self.final_norm(x)

        # logits: (B, T, vocab_size), one distribution per position.
        logits = self.output_head(x)
        return logits
```

Run a tiny forward pass to verify the shape path before you attach a loss function or optimizer:

```python
torch.manual_seed(7)

B, T, vocab_size = 2, 6, 37
model = TinyTransformerEncoder(
    vocab_size=vocab_size,
    d_model=32,
    num_heads=4,
    num_layers=2,
    d_ff=128,
    max_len=32,
    dropout=0.0,
)

token_ids = torch.randint(1, vocab_size, (B, T))  # (B, T), avoid pad_id=0 for this smoke test.
logits = model(token_ids, causal=False)           # (B, T, vocab_size)

print(token_ids.shape)  # torch.Size([2, 6])
print(logits.shape)     # torch.Size([2, 6, 37])
```

For the tiny configuration above, the parameter count is small enough to reason about. Each attention block has roughly `4 * d_model * d_model` projection weights plus biases, so with `d_model = 32` that is about `4096` weights before biases. The FFN has `32 * 128 + 128 * 32 = 8192` weights before biases, so it is about twice the attention projection count. Two LayerNorm layers add `4 * d_model` learned scalars per block because each norm has a weight and bias. The embedding table and output head each add `vocab_size * d_model` scale. For large vocabularies, embeddings dominate small models; for large widths, FFNs dominate the per-block count.

That estimate also explains why changing `d_ff` is a serious capacity decision. Increasing `num_heads` while keeping `d_model` fixed changes how the attention width is split, but it does not by itself multiply the projection matrix sizes. Increasing `d_ff` directly expands the two FFN matrices. Increasing `d_model` affects almost everything: attention projections, FFN matrices, LayerNorm vectors, embeddings, and output heads all grow. When you debug memory usage, distinguish these knobs rather than saying "the transformer got bigger" as one undifferentiated cause.

PyTorch's reference layer expresses the same structure with a production API. Set `batch_first=True` so tensors are `(B, T, d_model)`, and set `norm_first=True` for the pre-norm formula you implemented. The reference layer also lets you choose `activation="gelu"` and `dim_feedforward=d_ff`.

```python
d_model, num_heads, d_ff = 32, 4, 128

encoder_layer = nn.TransformerEncoderLayer(
    d_model=d_model,
    nhead=num_heads,
    dim_feedforward=d_ff,
    dropout=0.0,
    activation="gelu",
    batch_first=True,
    norm_first=True,
)

encoder = nn.TransformerEncoder(
    encoder_layer=encoder_layer,
    num_layers=2,
    norm=nn.LayerNorm(d_model),
)

x = torch.randn(B, T, d_model)              # (B, T, d_model)
blocked_mask = make_causal_blocked_mask(T)  # (T, T), True means blocked for this API path.

encoded = encoder(x, mask=blocked_mask)     # (B, T, d_model)
print(encoded.shape)                        # torch.Size([2, 6, 32])
```

The reference layer is not a replacement for understanding your own block. It is a compact, tested implementation of the same encoder-layer pattern, with fast paths and framework integration. Once you know the from-scratch structure, the constructor arguments become readable: `d_model` is residual-stream width, `nhead` splits attention into heads, `dim_feedforward` is `d_ff`, `batch_first` chooses `(B, T, D)` layout, and `norm_first` toggles pre-norm versus post-norm placement.

The production equivalent is also a good reminder that an encoder block and a decoder-only block are close relatives, not unrelated architectures. The encoder layer is usually bidirectional because no causal mask is supplied. A decoder-only language model supplies a causal mask so each position predicts from previous positions only. Encoder-decoder transformers add cross-attention blocks where queries come from the decoder stream and keys/values come from the encoder output. Those variations change masks and sublayer sources, but the residual-stream discipline remains the same.

## Did You Know?

- **The original transformer used fixed sinusoidal positions and post-norm residual sublayers.** Many later stacks changed one or both choices, but the core block shape stayed recognizably the same.
- **`nn.MultiheadAttention` and `F.scaled_dot_product_attention` use opposite boolean-mask meanings in important places.** In the module above, `blocked_attn_mask=True` means "do not attend" because that matches `nn.MultiheadAttention`.
- **The FFN can hold more parameters than attention inside a block.** With the conventional `d_ff = 4 * d_model`, the two FFN matrices have about twice the projection weights of Q, K, V, and output attention matrices.
- **Pre-norm changes training behavior without changing tensor shapes.** The block still returns `(B, T, d_model)`, but the residual stream has a cleaner identity path through depth.

## Common Mistakes

| Mistake | Problem | Solution |
|---|---|---|
| Re-teaching Q/K/V inside this block | It blurs the module boundary and hides the actual C4 lesson, which is block assembly. | Treat multi-head attention as the 1.4.3 component and focus on positions, FFN, norms, residuals, and stacking. |
| Forgetting positional information | Attention without positions cannot distinguish reordered inputs except through accidental data artifacts. | Add sinusoidal or learned positions to token embeddings before the first block. |
| Concatenating positions instead of adding them | Concatenation changes the stream width and breaks residual additions unless every downstream layer is redesigned. | Keep token and position vectors at `d_model` and add them elementwise. |
| Letting the FFN return `d_ff` | The residual addition requires the FFN update to match `(B, T, d_model)`. | Use `Linear(d_model, d_ff) -> GELU -> Linear(d_ff, d_model)`. |
| Mixing pre-norm and post-norm accidentally | `LN(x + sublayer(x))` and `x + sublayer(LN(x))` train differently and should not be swapped silently. | Choose the formula deliberately; use `norm_first=True` when matching the pre-norm implementation. |
| Inverting PyTorch mask semantics | A mask that means "allowed" in one attention function may mean "blocked" in another, causing future leakage or overmasking. | Name masks by meaning, such as `blocked_attn_mask`, and verify the target API's boolean convention. |
| Applying dropout to the shortcut path | Dropping the identity stream weakens the residual highway that makes deep stacks trainable. | Apply dropout to sublayer outputs before addition, leaving the shortcut itself intact. |

## Quiz

1. **Why is attention alone not enough to make a full transformer block?**

   <details>
   <summary>Answer</summary>
   Attention mixes information across positions, but it does not inject position information, does not provide the position-wise nonlinear MLP transformation, and does not by itself define a stable deep residual stack. The full block adds positions before attention, wraps attention and FFN updates in residual connections, and uses normalization so many blocks can be stacked.
   </details>

2. **What shape should a sinusoidal positional encoding have before it is added to token embeddings shaped `(B, T, d_model)`?**

   <details>
   <summary>Answer</summary>
   A convenient registered buffer shape is `(1, max_len, d_model)`. During the forward pass, slice it to `(1, T, d_model)` and add it to `(B, T, d_model)`. Broadcasting copies the same position rows across the batch dimension while preserving token-specific embeddings.
   </details>

3. **Why does the sinusoidal formula use `2i / d_model` in the exponent denominator?**

   <details>
   <summary>Answer</summary>
   The even feature index is `2i`, so each sine/cosine pair receives a frequency determined by that even index relative to the model width. In code, `torch.arange(0, d_model, 2) * (-log(10000) / d_model)` implements the inverse denominator `10000^(-2i / d_model)`.
   </details>

4. **What is the difference between learned absolute positions and sinusoidal positions?**

   <details>
   <summary>Answer</summary>
   Learned absolute positions are trainable rows in an `nn.Embedding(max_len, d_model)` table, so gradients update position vectors for the trained context window. Sinusoidal positions are deterministic buffers, not parameters, and can be generated for arbitrary positions, though extrapolation quality still depends on the model's learned behavior.
   </details>

5. **Why does the FFN usually expand to `d_ff` and then contract back to `d_model`?**

   <details>
   <summary>Answer</summary>
   The expansion gives each position a wider nonlinear workspace, while the contraction restores the residual-stream width required for addition. If the FFN returned `d_ff`, the block could not add the update back to `x` without a projection to `d_model`.
   </details>

6. **How does pre-norm differ from post-norm in one line of code?**

   <details>
   <summary>Answer</summary>
   Post-norm is `x = LN(x + sublayer(x))`, while pre-norm is `x = x + sublayer(LN(x))`. Pre-norm normalizes the sublayer input but keeps the residual stream itself on a cleaner additive path through depth.
   </details>

7. **Which PyTorch flags make `nn.TransformerEncoderLayer` match the block layout used in this module?**

   <details>
   <summary>Answer</summary>
   Use `batch_first=True` so inputs and outputs are `(B, T, d_model)`, and use `norm_first=True` so LayerNorm happens before attention and feed-forward operations. Set `activation="gelu"` and `dim_feedforward=d_ff` when you want the FFN to mirror the module's `Linear -> GELU -> Linear` design.
   </details>

8. **A block returns `(B, T, d_model)` but training leaks future-token information. What should you inspect first?**

   <details>
   <summary>Answer</summary>
   Inspect the causal mask semantics before blaming the FFN or LayerNorm. In the `nn.MultiheadAttention` path used here, a boolean attention mask uses `True` for blocked query-key pairs, so the upper triangle should be `True` for decoder-style causal attention. Also verify that padding masks use shape `(B, T)` and mark ignored key positions with `True`.
   </details>

## Hands-On Exercise

Build a tiny pre-norm transformer encoder and compare its output shape with PyTorch's reference encoder layer. The goal is not to train a language model; it is to verify that you can carry the residual stream through positions, attention, FFN, stacking, and final projection without a shape mismatch. Treat this as the same kind of smoke test you used in Block B: one controlled forward pass before a full training loop.

**Task**: Copy the classes from this module into one Python file, then run the smoke test below with PyTorch 2.12.

```python
import torch
import torch.nn as nn

torch.manual_seed(11)

B, T, vocab_size = 3, 7, 50
d_model, num_heads, d_ff, num_layers = 32, 4, 128, 2

model = TinyTransformerEncoder(
    vocab_size=vocab_size,
    d_model=d_model,
    num_heads=num_heads,
    num_layers=num_layers,
    d_ff=d_ff,
    max_len=64,
    dropout=0.0,
)

token_ids = torch.randint(1, vocab_size, (B, T))  # (B, T)
logits = model(token_ids, causal=True)            # (B, T, vocab_size)

print("token_ids:", token_ids.shape)  # torch.Size([3, 7])
print("logits:", logits.shape)        # torch.Size([3, 7, 50])

encoder_layer = nn.TransformerEncoderLayer(
    d_model=d_model,
    nhead=num_heads,
    dim_feedforward=d_ff,
    dropout=0.0,
    activation="gelu",
    batch_first=True,
    norm_first=True,
)

x = torch.randn(B, T, d_model)              # (B, T, d_model)
blocked_mask = make_causal_blocked_mask(T)  # (T, T)
encoded = encoder_layer(x, src_mask=blocked_mask)  # (B, T, d_model)

print("encoded:", encoded.shape)  # torch.Size([3, 7, 32])
```

Before running the file, read each printed shape and predict it from the constructor values. If you cannot explain a shape, stop and trace the stream before adding a loss.

### Success Criteria

- [ ] The custom model prints logits with shape `(3, 7, 50)`, proving the stack returns one vocabulary distribution per batch item and position.
- [ ] The PyTorch reference layer prints encoded states with shape `(3, 7, 32)`, proving `batch_first=True` kept the `(B, T, d_model)` layout.
- [ ] Setting `causal=False` in `TinyTransformerEncoder` still returns the same output shape, which confirms that encoder-style and decoder-style blocks differ by mask behavior, not by residual-stream width.
- [ ] Changing `d_model` to a value not divisible by `num_heads` raises the explicit `ValueError`, which catches a common multi-head shape bug before attention runs.

### Verification

```bash
.venv/bin/python transformer_block_smoke.py
```

If your local virtual environment does not have PyTorch installed, read the printed shapes in the exercise as the expected behavior and run the code in an environment with PyTorch 2.12 available. The repository verifier checks prose and structure, but architecture code still deserves a real smoke test when the dependency is present.

## Key Takeaways

A transformer block is an assembly pattern, not a magic primitive. Start with `(B, T, d_model)` token embeddings, add position information, let attention mix across positions, let the FFN transform each position independently, and wrap both sublayers in pre-norm residual additions. The residual stream remains the same shape through every block, which is why stacking is straightforward and why shape discipline catches so many errors early.

Sinusoidal and learned absolute positions both solve the same immediate problem: self-attention needs order information. Sinusoidal positions are fixed buffers with frequency structure; learned positions are trainable embedding rows with a fixed maximum length. RoPE and ALiBi refine the idea by making position affect attention more directly, but they build on the same core need for order.

Pre-norm structure, `x = x + sublayer(LN(x))`, is the default mental model to carry forward. It connects the residual-gradient highway from 1.4.2 to the normalization behavior from 1.3.4 and maps directly to PyTorch's `norm_first=True` flag. When you read a production transformer implementation, identify the residual stream first; the rest of the block becomes a sequence of controlled writes to that stream.

## Learner check

The deep-learning index places this module before the existing CNN destination row, so the learner sees the transformer-block capstone before leaving Block C:

> | 1.3.6 | [Numerical Stability & Precision](/ai-ml-engineering/deep-learning/module-1.3.6-numerical-stability-precision/) |
> | 1.4.4 | [The Transformer Block from Scratch](/ai-ml-engineering/deep-learning/module-1.4.4-transformer-block-from-scratch/) |
> | 1.5 | [Convolutional Neural Networks & Computer Vision](/ai-ml-engineering/deep-learning/module-1.5-cnns-computer-vision/) |

## Sources

- ["Attention Is All You Need" - Vaswani et al.](https://arxiv.org/abs/1706.03762)
- [PyTorch 2.12 `nn.MultiheadAttention` documentation](https://docs.pytorch.org/docs/2.12/generated/torch.nn.MultiheadAttention.html)
- [PyTorch 2.12 `nn.TransformerEncoderLayer` documentation](https://docs.pytorch.org/docs/2.12/generated/torch.nn.TransformerEncoderLayer.html)
- [PyTorch 2.12 `nn.TransformerEncoder` documentation](https://docs.pytorch.org/docs/2.12/generated/torch.nn.TransformerEncoder.html)
- [PyTorch 2.12 `nn.Embedding` documentation](https://docs.pytorch.org/docs/2.12/generated/torch.nn.Embedding.html)
- [PyTorch 2.12 `nn.LayerNorm` documentation](https://docs.pytorch.org/docs/2.12/generated/torch.nn.LayerNorm.html)
- [PyTorch 2.12 `nn.GELU` documentation](https://docs.pytorch.org/docs/2.12/generated/torch.nn.GELU.html)
- [PyTorch 2.12 `scaled_dot_product_attention` documentation](https://docs.pytorch.org/docs/2.12/generated/torch.nn.functional.scaled_dot_product_attention.html)
- [The Annotated Transformer - Harvard NLP](https://nlp.seas.harvard.edu/annotated-transformer/)
- [Dive into Deep Learning: The Transformer Architecture](https://d2l.ai/chapter_attention-mechanisms-and-transformers/transformer.html)
- ["On Layer Normalization in the Transformer Architecture" - Xiong et al.](https://arxiv.org/abs/2002.04745)
- ["Layer Normalization" - Ba, Kiros, and Hinton](https://arxiv.org/abs/1607.06450)
- ["Gaussian Error Linear Units (GELUs)" - Hendrycks and Gimpel](https://arxiv.org/abs/1606.08415)
- ["BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding" - Devlin et al.](https://arxiv.org/abs/1810.04805)
- ["RoFormer: Enhanced Transformer with Rotary Position Embedding" - Su et al.](https://arxiv.org/abs/2104.09864)
- ["Train Short, Test Long: Attention with Linear Biases Enables Input Length Extrapolation" - Press et al.](https://arxiv.org/abs/2108.12409)

## Next Module

Continue to [Convolutional Neural Networks & Computer Vision](/ai-ml-engineering/deep-learning/module-1.5-cnns-computer-vision/) to shift from sequence blocks into visual feature extractors.
