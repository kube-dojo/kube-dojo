---
title: "Residual Connections & Deep-Architecture Patterns"
slug: ai-ml-engineering/deep-learning/module-1.4.2-residual-deep-architectures
sidebar:
  order: 1005.2
---

> **AI/ML Engineering Track** | Complexity: `[COMPLEX]` | Time: 4-5 hours
>
> **Prerequisites**: Block A modules A6 (Backprop by Hand), A8 (Scalar Autograd). Block B modules 1.3.1 (Initialization & Signal Propagation) and 1.3.4 (Normalization Layers). PyTorch fundamentals from module 1.2.
>
> **Primary tools**: PyTorch 2.12.

---

At Microsoft Research Asia in 2015, Kaiming He and his colleagues ran an experiment that should not have happened. They trained a 56-layer convolutional network on CIFAR-10 alongside a shallower 20-layer version of the same architecture, expecting depth to improve accuracy as it always had. Instead, the 56-layer network performed worse on both training and test sets. This was not overfitting. Overfitting would have meant better training error and worse test error — but here the deeper network could not even fit its training data. Adding more layers, the defining trick of deep learning since AlexNet, had made the network strictly less capable. They called it the degradation problem, and it revealed something uncomfortable: stacking layers under standard initialization and BatchNorm did not guarantee trainability. The signal and its gradients were fine — BatchNorm had fixed vanishing and exploding activations years earlier — but the *optimization landscape* itself was collapsing. The deeper network's loss surface had become so ill-conditioned that gradient descent could not find a good minimum in any reasonable time.

Their solution was a structural intervention, not an optimizer tweak. Instead of asking each layer to learn the full input-to-output mapping, they asked it to learn a *residual* — the difference between the input and the desired output. The layer's output became `x + F(x)`, where `x` is the input and `F(x)` is the residual function. The identity shortcut `x` passes through untouched. A block initialized to near-zero residuals (with careful weight scaling or batch normalization) starts life behaving almost like an identity function, so adding more blocks cannot make the network worse than a shallower version. From this starting point, gradient descent gradually lifts the residual branches away from zero to learn the target function. The architecture they built around this idea, ResNet, won the ImageNet Large Scale Visual Recognition Challenge that year with residual networks up to 152 layers deep — roughly eight times deeper than VGG-19 — and its winning ensemble dropped the top-5 classification error to 3.57%, down from the previous year's ~6.7%.

Residual connections are now universal. Every modern transformer block — including the one you will build in module 1.4.4 — wraps its attention and feed-forward sub-layers in residual additions. The insight that unlocked 152-layer vision models in 2015 is the same insight that lets thousand-layer language models train without gradient collapse. This module derives that insight from the backpropagation rules you already mastered in Block A, connects it to the initialization and normalization tools you built in Block B, and establishes a mental model — the residual stream — that will carry you directly into transformer architecture.

---

## Learning Outcomes

By the end of this module, you will be able to implement residual blocks in PyTorch 2.12 with correct shortcut handling, derive the gradient-flow guarantee that makes deep residual networks trainable, and explain how the residual-stream model generalizes from ResNets to transformer architectures.

- **Implement** residual blocks with identity and projection shortcuts in PyTorch 2.12, including correct dimension-matching and the pre-activation design pattern, with tensor shapes verified at every step.
- **Derive** the backpropagation gradient through a residual connection `y = x + F(x)` from the chain rule and the autograd `+` distributes-gradient rule you built in A6/A8, and explain why the identity path guarantees at least one undiminished gradient route to every layer.
- **Diagnose** deep-network training failures by measuring gradient norms at the first layer in plain versus residual stacks, connecting the measurements to the degradation problem observed in He et al. (2015).
- **Design** a pre-norm residual block (the transformer standard) using `nn.LayerNorm` and `nn.Linear` from modules 1.3.4 and 1.2, and articulate why pre-normalisation interacts favourably with the residual stream.
- **Evaluate** architectural tradeoffs between depth-scaling and width-scaling in residual networks, **explain** how zero-initialised residual branches (ReZero) and Fixup-style scaling produce near-identity initialisation that replaces the need for BatchNorm, and **distinguish** residual connections from gated highway networks and DenseNet concatenative skips.

---

## Why This Module Matters

Deep learning spent nearly a decade fighting the vanishing gradient. The fix was BatchNorm, better initialisations, and ReLU activations — each of which you worked through in Block B. The degradation problem was different. After all those fixes were in place, signal magnitude was healthy. Gradients were not vanishing numerically. Yet optimisation still failed in deep networks. The loss surface itself was the culprit. Gradient descent, even with momentum and Adam, could not consistently navigate the high-dimensional, non-convex landscape of a fifty-layer network that had no structural scaffolding to guide it. The residual connection is that scaffolding. It turns the optimisation problem from "learn the function" into "learn the perturbation around the identity," and in doing so it reshapes the loss surface so that gradient descent can succeed where it previously wandered or stalled.

This module sits at the architectural pivot of the entire neural-networks curriculum. In Block A you built backpropagation by hand and traced gradients through scalar computation graphs. In Block B you trained multi-layer perceptrons with PyTorch, tuned initialisation for signal health, and added normalisation layers to stabilise activations. This module takes those primitives and assembles them into the first genuinely deep architectural pattern. The residual block is not a new layer type. It is a *connection pattern* — a way of wiring together `nn.Linear`, `nn.ReLU`, and `nn.LayerNorm` that you already know — such that a network of depth 100 trains as reliably as a network of depth 10. The architecture discipline you learn here (pre-norm placement, correct shortcut handling, the gradient-highway guarantee) is what makes transformer training possible at scale.

There is also a subtler reason this module matters. The residual stream — the view of a deep residual network as a running sum that every block reads from and writes to via addition — is the single most important mental model for understanding transformer internals. When you reach the transformer block in module 1.4.4 and see `x = x + MHA(LayerNorm(x))` followed by `x = x + MLP(LayerNorm(x))`, you will recognise it immediately: two residual blocks in sequence, each reading from and writing to the same running sum. The residual stream model explains why attention heads can specialise independently, why transformer depth can exceed 100 layers, and why certain interpretability techniques (like patching activations at a specific layer and watching them propagate) work at all. Mastering residual connections here means the transformer block in C4 is a composition exercise, not a foreign architecture.

---

## Part 1: The Degradation Problem — When Deeper Hurts

The intuition that deeper networks are more expressive is correct in theory. A network with more layers can represent more complex functions. The universal approximation theorem guarantees that a single hidden layer can approximate any continuous function on a compact set, but it says nothing about how many neurons are required or how the optimisation behaves. In practice, depth consistently outperformed width throughout the 2010s. AlexNet (8 layers, 2012), VGG (19 layers, 2014), and GoogLeNet (22 layers, 2014) all improved on their shallower predecessors. The trend was clear: add layers, get better accuracy.

He et al. broke that trend in a controlled experiment. They took two convolutional networks with identical architecture families — one with 20 weight layers and one with 56 — trained both on CIFAR-10 with BatchNorm, ReLU, and a standard SGD schedule, and plotted training error. The 20-layer network converged smoothly to a low training error. The 56-layer network started higher and stayed higher throughout training. The gap was not small: at convergence, the deeper network had roughly 2% higher training error. Test error tracked training error with a similar gap, ruling out overfitting. The deeper network had more parameters and more representational capacity, but it learned a worse solution. Adding more layers — the most reliable lever in the deep-learning toolkit — had backfired.

This is the degradation problem, and it is distinct from the vanishing-gradient problem you studied in module 1.3.1. In the vanishing-gradient regime, activations and gradients decay exponentially with depth, so early layers receive no useful signal. BatchNorm, He initialisation, and ReLU collectively fix that: they keep activation variances near 1.0 and gradient variances near 1.0 across many layers. The degradation problem occurs even when signal magnitudes are healthy throughout. The issue is that the loss surface of a deep plain network — one where each layer's output is `F(x)` rather than `x + F(x)` — is poorly conditioned. Gradient descent follows a path that leads to a suboptimal basin, and the basin the optimiser finds in the 56-layer network is worse than the basin it finds in the 20-layer network.

He et al.'s insight was not that a 56-layer network is fundamentally worse than a 20-layer network. A 56-layer network with the 20-layer solution embedded in its first 20 layers and identity mappings in the remaining 36 — an exact copy — would achieve the same training error as the 20-layer network. The problem is that gradient descent cannot discover this solution. Plain layers are not incentivised to learn near-identity mappings. A `nn.Linear → ReLU → nn.Linear` block with zero-mean weight initialisation (He normal) maps a roughly normalised input to a transformed output that is not close to the input. Stacking fifty such blocks compounds the deviation. The optimisation must simultaneously discover both the correct transformations and the condition that most blocks should do very little — a needle-in-a-haystack problem in parameter space.

The residual connection solves this by making identity the default. When the residual branch `F(x)` is initialised to produce small outputs — either by design (zero-initialising the last layer of each residual block) or by the natural behaviour of BatchNorm followed by random weights — the block output `x + F(x)` is approximately `x`. Stacking fifty such blocks produces approximately the identity function. The network starts near a good solution and gradient descent gradually lifts each residual branch away from zero to learn the necessary deviations. The optimisation landscape is fundamentally reshaped: the loss surface near the identity function is far better conditioned than the loss surface of an equivalent plain network with no identity shortcut.

---

## Part 2: The Residual Block

A residual block wraps a sub-network `F(x)` inside an additive shortcut. The block's forward computation is:

```
y = x + F(x)
```

where `F(x)` is typically two or three weighted layers separated by nonlinearities, and `x` is the block's input. The block output `y` has the same shape as `x` because addition requires shape agreement. When the shapes differ — for example when a block changes the number of channels in a convolutional network or the feature dimension in a fully-connected network — the shortcut must project `x` to the correct shape. A projection shortcut uses a learned linear transformation:

```
y = W_proj @ x + F(x)
```

where `W_proj` is a weight matrix (an `nn.Linear` layer) that matches dimensions. The projection is only needed when the input and output shapes differ; for same-shape blocks, the identity shortcut is the correct and most common choice.

Here is the simplest residual block in PyTorch, using the `nn.Linear` layers you already know from module 1.2:

```python
import torch
import torch.nn as nn

class ResidualBlock(nn.Module):
    """A residual block with an identity shortcut.

    The block learns F(x) such that y = x + F(x).
    When the block starts near identity (F(x) ≈ 0), the gradient
    highway through the `+` node carries the upstream gradient
    to earlier layers undiminished.
    """
    def __init__(self, dim: int, expansion: int = 1, dropout: float = 0.0):
        super().__init__()
        hidden_dim = dim * expansion
        self.net = nn.Sequential(
            nn.Linear(dim, hidden_dim),   # (dim, hidden_dim)
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, dim),   # (hidden_dim, dim)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (N, dim)
        return x + self.net(x)  # (N, dim) + (N, dim) -> (N, dim)
```

When `expansion=1`, the hidden dimension equals the input dimension — a bottleneck-free block. When `expansion > 1`, the block expands to a wider hidden layer then contracts back, trading more parameters for more representational capacity per block while keeping the residual addition at the original dimension.

When the input and output dimensions differ — for example when transitioning between stages of a deep network — a projection shortcut is required:

```python
class ResidualBlockWithProjection(nn.Module):
    """A residual block with a learned projection shortcut.

    Used when in_dim != out_dim (dimension change between stages).
    The projection is a learned linear map — not an identity.
    """
    def __init__(self, in_dim: int, out_dim: int, expansion: int = 4):
        super().__init__()
        hidden_dim = out_dim * expansion
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),    # (in_dim, hidden_dim)
            nn.ReLU(),
            nn.Linear(hidden_dim, out_dim),   # (hidden_dim, out_dim)
        )
        # Projection shortcut: learn a linear map so shapes match
        self.proj = nn.Linear(in_dim, out_dim)  # (in_dim, out_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (N, in_dim)
        return self.proj(x) + self.net(x)  # (N, out_dim) + (N, out_dim) -> (N, out_dim)
```

### Pre-activation versus post-activation design

The original ResNet paper placed BatchNorm and ReLU *after* the weight layers, with the addition performed before the final ReLU. The pre-activation design (He et al., 2016) moved BatchNorm and ReLU *before* each weight layer, creating a cleaner gradient path where the identity shortcut flows through the entire block without passing through any nonlinearity. In pre-activation form, the forward pass is:

```
y = x + W2 · ReLU(BN(W1 · ReLU(BN(x))))
```

The pre-activation variant consistently trains better on very deep networks (>200 layers) because the gradient path through the identity shortcut is completely unobstructed — no ReLU and no BatchNorm sit on the shortcut itself. For fully-connected networks and transformer blocks (where LayerNorm replaces BatchNorm), the pre-norm design — placing LayerNorm before the sub-layer, then adding the residual — achieves the same effect. You will see this exact pattern when we reach the transformer block: `x = x + MHA(LayerNorm(x))` is a pre-norm residual block where the sub-layer is multi-head attention.

---

## Part 3: The Gradient Highway — Why Residuals Work

The residual connection's power is easiest to see through its backpropagation behaviour. In module A6 you derived backpropagation by hand for a computation graph of scalar operations. In module A8 you built a scalar autograd engine where the `+` node's backward rule distributes the upstream gradient to both operands unchanged. The residual connection exploits that exact rule.

Consider a single residual block whose forward computation is `y = x + F(x)`. The scalar loss `L` depends on `y`, and we want the gradient with respect to the input `x`:

```
∂L/∂x = ∂L/∂y · ∂y/∂x
       = ∂L/∂y · ∂/∂x (x + F(x))
       = ∂L/∂y · (1 + ∂F/∂x)
       = ∂L/∂y + ∂L/∂y · ∂F/∂x
```

The first term, `∂L/∂y`, is the upstream gradient *passed through the identity path unchanged*. The second term, `∂L/∂y · ∂F/∂x`, is the upstream gradient modified by the residual branch's local derivatives. Even if the residual branch produces near-zero local gradients (because its weights happen to be small or its activations are in flat regions), the identity path delivers the full upstream gradient to earlier layers without attenuation. Across `L` residual blocks, the gradient at the input includes the term `∂L/∂y_L` from the final block *directly*, plus contributions from every intermediate residual branch. No multiplication chain of near-zero factors can extinguish the signal.

This is fundamentally different from a plain stack where each layer's output is `h_l = F_l(h_{l-1})`. In a plain stack, the gradient at layer `l` is:

```
∂L/∂h_l = ∂L/∂h_L · ∏_{k=l+1}^{L} ∂F_k/∂h_{k-1}
```

If any factor `∂F_k/∂h_{k-1}` has eigenvalues less than 1 — which is common when weights are initialised to small values and nonlinearities compress their inputs — the product shrinks exponentially with depth. This is the vanishing-gradient problem, and it persists even with BatchNorm because BatchNorm normalises activations but does not guarantee that the Jacobian of a nonlinear transformation has eigenvalues near 1. The residual connection sidesteps the product: the additive identity term `1` ensures a depth-independent gradient path through the identity shortcut.

### Demonstrating the gradient highway numerically

The following experiment creates a plain deep stack and a residual deep stack with identical layer counts, feeds the same input through both, backpropagates from a scalar loss, and measures the gradient norm reaching the input. The residual stack preserves gradient magnitude; the plain stack loses it rapidly with depth.

```python
import torch
import torch.nn as nn

def measure_first_layer_grad(depth: int, dim: int, use_residual: bool):
    """Compare gradient norm at layer 1 for plain vs residual stacks.

    Returns the L2 norm of the gradient at the input tensor (`x.grad`), which the gradient must
    reach through the full depth.
    """
    torch.manual_seed(42)
    if use_residual:
        layers = nn.ModuleList([
            ResidualBlock(dim) for _ in range(depth)  # defined above
        ])
    else:
        layers = nn.ModuleList([
            nn.Sequential(
                nn.Linear(dim, dim),  # (dim, dim)
                nn.ReLU(),
                nn.Linear(dim, dim),  # (dim, dim)
            ) for _ in range(depth)
        ])

    x = torch.randn(32, dim)        # (32, dim)
    x.requires_grad_(True)

    # Forward pass
    h = x
    for layer in layers:
        h = layer(h)                # (32, dim)

    loss = h.sum()                  # scalar
    loss.backward()

    grad_norm = x.grad.norm().item()
    return grad_norm


dim = 128
print(f"{'Depth':>6}  {'Plain':>10}  {'Residual':>10}")
print("-" * 30)
for depth in [5, 10, 20, 50]:
    plain_g = measure_first_layer_grad(depth, dim, use_residual=False)
    res_g   = measure_first_layer_grad(depth, dim, use_residual=True)
    print(f"{depth:>6}  {plain_g:>10.4f}  {res_g:>10.4f}")
```

The plain stack's input-tensor gradient shrinks to near-zero by depth 50, while the residual stack's gradient reaching the input remains within an order of magnitude of its depth-5 value. This is the gradient highway in action: each `+` node copies the upstream gradient to both the residual branch and the identity path, and the identity path connects directly back to the input across the full depth.

### Connecting to the autograd you built

In module A8 you implemented a scalar autograd engine where the `Add` node's backward function distributes the upstream gradient `g` to both operands:

```python
# From your micrograd-style autograd (A8)
class Add:
    def backward(self, g):
        self.a.grad += g   # gradient to left operand
        self.b.grad += g   # gradient to right operand
```

In the residual connection `y = x + F(x)`, the autograd `Add` node receives the upstream gradient `∂L/∂y` and distributes it to both `x` and `F(x)` **in full and unchanged**. The `x` operand receives `∂L/∂y` directly — this is the identity path. The `F(x)` operand also receives `∂L/∂y`, and from there backpropagation continues through the residual branch's `nn.Linear` layers. Even if every `nn.Linear` in the residual branch has tiny weights, the `Add` node's distribution rule guarantees that `∂L/∂y` reaches the earlier blocks. The residual connection does not amplify or reshape the gradient. It guarantees that the gradient is *present* at every depth — a property that a plain multiplicative chain cannot provide.

---

## Part 4: The Residual Stream — An Additive Read/Write Bus

Consider a deep residual network as a running sum. Every block takes the current sum, reads it, computes a residual contribution, and writes that contribution back by addition. The state after block `l` is:

```
h_{l} = h_{l-1} + F_l(h_{l-1})
      = x + Σ_{k=1}^{l} F_k(h_{k-1})
```

The output after `L` blocks is the original input `x` plus the sum of all residual contributions. This is the residual stream: a shared additive bus that runs the full depth of the network. Every block has read access to the stream (it receives `h_{l-1}` as input) and write access (it adds its output `F_l(h_{l-1})` to the stream). No block can overwrite or erase what previous blocks have written — it can only add.

### Walking through the stream over a few blocks

To make this concrete, trace the stream state through three residual blocks processing an input vector `x` of dimension 64. After block 1, the stream holds `h_1 = x + F_1(x)` — the original input plus whatever transformation the first block deemed useful. Block 2 receives `h_1` and adds its own contribution: `h_2 = h_1 + F_2(h_1) = x + F_1(x) + F_2(h_1)`. Block 3 receives `h_2` and writes `F_3(h_2)`, producing `h_3 = x + F_1(x) + F_2(h_1) + F_3(h_2)`. The original input `x` is still present in full at block 3. The contribution from block 1 is still present. Nothing has been overwritten. If block 2 decided that `F_1(x)` encoded a useful feature — say, the presence of an edge at a particular orientation — that feature remains available to block 3 and every subsequent block. In a plain network, block 3 receives only `F_2(F_1(x))`; the raw output of `F_1` is gone, replaced by `F_2`'s transformation of it. Information must survive every intermediate bottleneck.

This cumulative, append-only property has a direct analogue in how transformer blocks operate. In module 1.4.4, you will build a transformer block whose core computation is two residual additions in sequence: `x = x + MHA(LayerNorm(x))` followed by `x = x + FFN(LayerNorm(x))`. The stream `x` begins as a token embedding and accumulates contributions from every attention head at every layer plus every feed-forward sub-layer. A head at layer 12 can attend to information written into the stream by a head at layer 3 because that information was added, not replaced. An interpretability researcher studying a trained transformer can patch a single activation value at layer 5 — replacing it with a counterfactual value — and observe that value propagate unchanged through the remaining 20 layers except where later heads explicitly modify it. This is how mechanistic interpretability studies attribute transformer behaviour to specific circuits: the residual stream makes information traceable across depth.

### Why the stream stays healthy

The residual stream's health depends on the scale of the contributions. If a block's `F_l(h)` consistently produces outputs with large magnitude relative to the stream, the stream grows without bound across depth. After fifty blocks, the accumulated magnitude may be an order of magnitude larger than the input, downstream nonlinearities saturate, and gradients become unstable. Two design choices prevent this. First, normalisation — LayerNorm in transformers, BatchNorm in ResNets — placed on the residual branch constrains the sub-layer's output scale. Second, near-identity initialisation (Part 5) ensures that the residual contributions start small, giving gradient descent time to discover useful transformations before the stream magnitude grows large. The pre-norm transformer pattern `x + F(Norm(x))` is particularly effective here: LayerNorm normalises the input to unit variance, bounding the sub-layer's output magnitude regardless of depth, and the identity shortcut carries a clean gradient path alongside the normalised branch.

This view is not merely a notational convenience. It explains several phenomena that are otherwise puzzling:

**Why very deep residual networks don't suffer from representational collapse.** In a plain deep network, the representation at layer 50 may have lost information present at layer 5 because each transformation can discard information (weights can produce near-zero outputs, ReLU can zero out negative activations). In a residual stream, information added at layer 5 remains in the stream at layer 50 unless a later block explicitly subtracts it. Subtraction is possible — a block could add a negative contribution — but it requires learning to do so, and gradient descent under standard initialisation does not default to cancellation.

**Why attention heads in transformers can specialise.** In the transformer block (module 1.4.4), the residual stream after the multi-head attention sub-layer contains the original token embedding plus attention outputs from all heads and all previous layers, plus feed-forward contributions. An attention head at layer 20 can attend to information added by any previous layer because that information is still present in the stream. The stream acts as a shared communication channel where every sub-layer can read the full history and write new information without disrupting what previous sub-layers contributed.

**Why pre-norm transformers train more stably than post-norm.** LayerNorm placed *before* the sub-layer (pre-norm) constrains the input to the sub-layer to unit norm, bounding the sub-layer's output scale and keeping residual contributions moderate. LayerNorm placed *after* the addition (post-norm, the original transformer design) normalises the updated stream, which can mask growing magnitudes during the forward pass but does not constrain the sub-layer's output, leading to gradient instability at scale.

The pre-norm residual block (transformer-style) in PyTorch:

```python
class PreNormResidualBlock(nn.Module):
    """Pre-norm residual block — the transformer standard.

    The normalisation is applied to the input *before* the sub-layer,
    and the residual connection bypasses both. This is the pattern
    you will see in module 1.4.4's transformer block.
    """
    def __init__(self, dim: int, sublayer: nn.Module, dropout: float = 0.1):
        super().__init__()
        self.norm = nn.LayerNorm(dim)         # (dim,)
        self.sublayer = sublayer
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (N, dim) — the current state of the residual stream
        return x + self.dropout(self.sublayer(self.norm(x)))
        #        (N, dim) + (N, dim) -> (N, dim)
```

The gradient path through this block is clean. The upstream gradient flows through the `+` node to both `x` (the identity path) and the dropout-sublayer-norm path. The normalisation sits on the sub-layer branch only, not on the identity shortcut. LayerNorm's backward pass scales the incoming gradient by the inverse of the input's standard deviation, which can amplify or attenuate the gradient locally, but the identity path carries the gradient through unscaled.

---

## Part 5: Initialisation and Scale for Residual Nets

A residual network is easiest to train when it starts near the identity function. If every block produces near-zero output at initialisation, the full network approximates `y ≈ x`, and gradient descent can gradually increase the magnitude of each block's contribution as needed. This principle — start from identity, learn perturbations — is the deep reason residual networks train so reliably. When the network begins at the identity function, the deeper version's initial loss equals the shallower version's, and gradient descent has a well-conditioned starting point from which to gradually activate each block's representational capacity. The signal-propagation analysis you learned in module 1.3.1 applies directly here: at initialisation, the residual stream's variance should remain near 1.0 across all blocks, and the residual branch's contribution should be small enough that adding fifty of them does not cause the stream to diverge.

### Zero-initialised residual branches (ReZero)

The simplest approach to guaranteed near-identity initialisation is to multiply each residual branch's output by a learned scalar `α` that starts at zero:

```
y = x + α · F(x),   α = 0 at initialisation
```

At `α = 0`, the block is exactly the identity function, regardless of `F(x)`'s weights. Gradient descent adjusts `α` upward as training proceeds. The gradient with respect to `α` is `∂L/∂y · F(x)`, which is non-zero even at `α = 0` as long as `F(x)` is non-zero, so the parameter can learn. ReZero (Bachlechner et al., 2020) demonstrated that this alone enables training residual networks of arbitrary depth without BatchNorm — the learned scalar `α` acts as a per-block learnable gate on the residual contribution. The tradeoff: `α` is a per-block scalar bottleneck; it controls the overall magnitude of the residual contribution but cannot shape which dimensions of `F(x)` are amplified, only by how much overall. For architectures where the residual branch produces multi-dimensional outputs, a single scalar gate cannot selectively amplify useful feature dimensions while suppressing noise.

### Zero-initialising the last layer of each residual block

A subtler technique, used in Fixup initialisation (Zhang et al., 2019), initialises the last weight layer of each residual branch to zero and scales intermediate layers so that the residual branch contributes exactly zero at the start of training. Unlike ReZero, this requires no additional parameters — it uses the existing weight matrices. When the last `nn.Linear` of the residual branch has all-zero weights, `F(x) = 0` regardless of the earlier layers' computations. As training proceeds, the last layer's weights move away from zero and the branch begins contributing. Fixup also scales the initialisation of other layers within the branch to maintain healthy signal propagation once the branch activates.

The signal-propagation reasoning behind Fixup connects directly to module 1.3.1. At initialisation, the residual branch outputs zero, so the residual stream's variance is exactly the input variance — perfect signal health across arbitrary depth. When training begins and the last layer's weights move away from their zero initialisation, the intermediate layer scaling (typically `1/√(depth)` for the second-to-last layer and careful multiplicative factors for earlier layers) keeps the branch's output variance bounded and prevents the stream from diverging. Fixup achieves what BatchNorm does for signal normalisation without the compute overhead or batch-dependence of normalisation layers, making it valuable in settings where BatchNorm is impractical — recurrent networks, small-batch training, and reinforcement learning.

### Demonstrating initialisation sensitivity

A small numeric experiment makes the initialisation principle concrete. Below, we compare two residual stacks of depth 30: one with standard He-initialised `nn.Linear` layers in the residual branch, and one where the last `nn.Linear` of each branch is zero-initialised. Both receive the same random input, and we measure the output's deviation from the input — a healthy near-identity initialisation should produce small deviation.

```python
import torch
import torch.nn as nn

def output_deviation(depth, dim, zero_init_last):
    """Measure ||h_depth - x|| after forward pass through a residual stack."""
    torch.manual_seed(0)
    blocks = []
    for _ in range(depth):
        net = nn.Sequential(
            nn.Linear(dim, dim),   # (dim, dim) — He init
            nn.ReLU(),
            nn.Linear(dim, dim),   # (dim, dim)
        )
        if zero_init_last:
            nn.init.zeros_(net[-1].weight)
            nn.init.zeros_(net[-1].bias)
        blocks.append(net)

    x = torch.randn(1, dim)         # (1, dim)
    h = x
    with torch.no_grad():
        for net in blocks:
            h = h + net(h)          # (1, dim) + (1, dim)

    return (h - x).norm().item()    # deviation from identity

dim = 128
print(f"Depth 30, standard He init:  deviation = {output_deviation(30, dim, zero_init_last=False):.4f}")
print(f"Depth 30, zero-init last:    deviation = {output_deviation(30, dim, zero_init_last=True):.4f}")
```

The zero-initialised stack produces exactly zero deviation — the network is the identity function at the start of training, regardless of depth. The standard He-initialised stack produces a measurable deviation that grows with depth, pushing the network away from identity before training even begins.

### The interaction with LayerNorm

In pre-norm transformer blocks, LayerNorm normalises the sub-layer's input to zero mean and unit variance. If the sub-layer's weight matrices are initialised with small variance (He or Xavier scaling), the sub-layer's output `F(LayerNorm(x))` is naturally small relative to `x`, because the layer-normalised input has bounded scale and the weights are small. This is why pre-norm transformers train stably at depth without explicit zero-initialisation tricks: the combination of LayerNorm and standard weight scaling already produces near-identity behaviour at initialisation. Post-norm transformers lack this property because normalisation happens after the addition, so the sub-layer's output scale is unconstrained during the forward pass.

### BatchNorm and residual initialisation

In the original ResNet, BatchNorm follows each convolutional layer. A BatchNorm layer with zero mean and unit variance output, followed by zero-mean weights, produces a residual branch whose expected output is zero. The variance is not strictly zero — BatchNorm's learned scale `γ` defaults to 1, and ReLU introduces positive bias — but the magnitude is small relative to the identity path in early training. This is sufficient for ResNets up to roughly 200 layers. Beyond that, pre-activation design (Part 2) and Fixup-style initialisation become necessary to maintain the near-identity property at extreme depth.

---

## Part 6: Depth versus Width

Every neural network architect faces a fundamental question: should we add more layers (depth) or make each layer larger (width)? The residual connection changes the answer by making depth a safe, reliable scaling axis — but the tradeoffs between depth and width remain real and must be understood on their own terms.

### The case for depth

Each additional layer introduces a new nonlinear transformation. In a residual network, depth adds another term to the running sum: a deeper residual network has more terms in `x + Σ F_k(h_{k-1})`. Each term can model a different aspect of the target function, and because terms are additive, the network can learn to specialise different blocks to different sub-problems. A block early in the network might learn to extract low-level features (edges, textures), a middle block might compose those into mid-level patterns (shapes, parts), and a late block might assemble them into task-specific representations. This is why ResNet-152 (152 layers, ~60M parameters) outperformed wider but shallower architectures with the same parameter count: depth provides more nonlinear stages, each of which can refine the representation incrementally. The residual connection makes depth safe in practice — the identity shortcut guarantees the deeper network is at least as expressive as the shallower one, and because identity is the default, gradient descent can fall back to it when extra layers have nothing to add, so added depth no longer degrades training error the way it does in plain stacks. The new layers can learn the identity function if they have nothing useful to contribute, and gradient descent can discover this solution because identity is the default.

### The case for width

Increasing the hidden dimension of each block's residual branch (the `expansion` parameter in Part 2) increases the block's capacity to model complex transformations *at that stage*. A wider block can learn more complex residuals per depth unit — a block with a 4096-dimensional hidden layer can represent far more varied transformations of its input than a block with a 256-dimensional hidden layer. This matters when the target function demands rich per-stage computation: tasks with high-dimensional outputs, multi-modal inputs, or complex per-token transformations benefit from width. The tradeoff is quadratic: an `nn.Linear(dim, hidden_dim)` layer has `dim × hidden_dim` parameters, so doubling the hidden dimension quadruples the parameter count (for the two `nn.Linear` layers in a residual block). Compute cost scales similarly. A single wide residual block can consume as many parameters and FLOPs as many narrow ones.

### The empirical tradeoff

For a fixed parameter budget, depth generally outperforms width on tasks with hierarchical structure — image classification, language modelling, any domain where the target function decomposes naturally into successive transformations. The residual connection is what makes depth viable: without it, the benefits of depth are capped by optimisation difficulty at around 20-30 layers. With residual connections, depth scaling continues to improve performance well past 1000 layers (as demonstrated by the pre-activation ResNet-1001 training successfully on CIFAR in He et al., 2016).

For a fixed compute budget (FLOPs), the picture is more nuanced. Wider layers parallelise better on GPUs — a wide shallow network saturates the GPU's compute units more effectively than a narrow deep one, because each layer's matrix multiply has larger dimensions in the inner loop. Modern transformer designs (such as Llama and GPT variants) use hidden dimensions of 4096-8192 with 32-80 layers, balancing depth (for representational power) with width (for hardware efficiency). The residual stream model clarifies why this balance works: depth gives you more additive terms in the stream (more opportunities to refine), while width gives each term more expressive power. Both dimensions are subject to diminishing returns — a 200-layer network with 16-dimensional hidden layers cannot learn much because each residual contribution has too little capacity to matter, and a 2-layer network with 65536-dimensional hidden layers wastes parameters on a representation that is never transformed through successive stages.

A concrete example: a ResNet-50 with bottleneck blocks (expansion factor 4, hidden dimension 256) has roughly 25M parameters and achieves 76% top-1 accuracy on ImageNet. Doubling the width (hidden dimension 512) while keeping depth at 50 yields ~97M parameters and ~78% accuracy — a 2% gain for 4× the parameters. Doubling the depth to ResNet-101 (101 layers, same width) yields ~44M parameters and ~77.4% accuracy — a 1.4% gain for 1.8× the parameters. Depth gives more accuracy per parameter because each new layer adds a new nonlinear stage, while widening an existing layer only increases the capacity of an existing stage. This relationship holds broadly across vision and language tasks: when parameter efficiency matters, prefer depth; when hardware utilisation matters, add enough width to saturate the GPU.

The simplest rule, valid for most learning problems you will encounter: use residual connections, start with a depth that is at least 10-20 blocks, make each block wide enough that the parameter count fits your compute budget, and scale depth before width when you have headroom. The residual connection is what makes depth a safe scaling axis — without it, depth is dangerous.

---

## Part 7: Other Skip Patterns

Residual connections are the dominant skip pattern in modern architectures, but they are not the only one. Two predecessors — highway networks and DenseNet — introduced ideas that shaped the residual design and remain relevant in specialised contexts. Understanding what these alternatives do differently clarifies what makes the simple residual connection so effective and when a different skip pattern might be the better tool.

### Highway networks (Srivastava et al., 2015)

Published months before ResNet, highway networks use a gated residual connection:

```
y = T(x) · H(x) + (1 − T(x)) · x
```

where `T(x) = σ(W_T · x + b_T)` is a transform gate (a sigmoid output between 0 and 1) and `H(x)` is the candidate transformation. When `T(x) ≈ 1`, the block behaves like a plain transformation layer — the input is fully transformed, no shortcut. When `T(x) ≈ 0`, the block passes the input through unchanged — an identity highway. The gate is learned, so the network decides per-example and per-dimension how much to transform versus pass through. A highway block can selectively route some dimensions of its input through the transformation while letting others pass unchanged, giving the network fine-grained control over which information is modified and which is preserved.

Highway networks demonstrated that very deep networks (up to 100 layers) could be trained before ResNet was published, but the learned gating adds parameters — `W_T` and `b_T` for every block — and the `(1 − T(x))` gate mechanism introduces a more complex gradient path than a simple additive shortcut. When `T(x)` is near 0.5, the gradient through the gate is divided between the transform path and the carry path, which can slow learning compared to a residual connection's fixed identity shortcut, which passes the full upstream gradient through unchanged. In practice, the learned gate rarely outperforms the fixed identity shortcut of ResNet for visual tasks, though gating resurfaces in modern architectures in more specialised roles: mixture-of-experts routers use learned gating to select which expert sub-networks process each token, and gated linear units (GLU) in LLMs apply learned sigmoid gates to control information flow through feed-forward layers. Highway networks are the appropriate tool when you need the network to learn *when* to transform rather than just *what* to transform — a distinction that matters in sequence modelling where some time steps require no computation, or in multi-task architectures where different tasks need different numbers of transformations.

### DenseNet (Huang et al., 2017)

DenseNet replaces residual addition with concatenation. Every layer receives the feature maps of *all* preceding layers as input:

```
h_l = Concat(x, h_1, h_2, ..., h_{l-1})
```

Each layer writes new feature maps that are concatenated to the running collection, and every downstream layer can read from any earlier layer's output directly. This is maximal feature reuse: a layer at depth 50 has direct access to the raw input, the first layer's features, and everything in between. Each layer typically adds a small number of new feature maps (a *growth rate* `k`, often 12 or 32), keeping the total parameter count low despite the growing input.

DenseNet achieves competitive accuracy with far fewer parameters than ResNet because features are reused rather than recomputed — a DenseNet-121 (121 layers, growth rate 32) has roughly 8M parameters and matches the accuracy of a ResNet-50 with 25M parameters on ImageNet. The parameter efficiency comes from the concatenation design: earlier features are available directly, so later layers do not need to re-learn them. The cost is memory: the concatenated tensor grows linearly with depth (size `k × l` for layer `l`), and the memory footprint of storing all intermediate feature maps during training is substantially larger than ResNet's fixed-size residual stream. During backpropagation, every layer must have its inputs available in memory — DenseNet must store the growing concatenation at every depth, while ResNet stores a fixed-dimension tensor at every block. For a network of depth 100 with growth rate 32, the concatenation at the final layer contains `100 × 32 = 3200` channels, and every preceding concatenation must also be stored. DenseNet is most useful in memory-rich, parameter-constrained settings — edge deployment, small-model regimes — while ResNet's additive stream dominates in large-scale training where memory efficiency matters more than parameter efficiency.

### When to use which pattern

The residual connection is the default: it works, it scales, and it costs nothing beyond a single addition per block. Highway gating is useful when the network benefits from learning *per-example routing* — deciding which sub-networks to engage for each input, as in mixture-of-experts models and conditional computation. DenseNet concatenation is useful when *parameter budget* is the binding constraint and memory is plentiful — small models for mobile or embedded deployment, where the 3–4× parameter efficiency of DenseNet over ResNet at equal accuracy directly translates to smaller on-device binaries. Both highway gating and DenseNet concatenation introduce complexity — gating adds learned parameters and a more complex gradient path, concatenation forces the input dimension to grow with depth. The residual connection `y = x + F(x)` remains the simplest, most reliable skip pattern, and it is the substrate on which both alternatives can be understood as variations.

Both patterns — gated highways for learned routing and DenseNet for aggressive feature reuse — remain active research tools. But the simple additive residual connection `y = x + F(x)`, with its clean gradient highway and minimal parameter overhead, is the pattern that scaled deep learning to its current frontier.

---

## Did You Know?

- The ResNet paper (He et al., 2015) won the Best Paper Award at CVPR 2016 and is among the most-cited papers in all of science, with well over 200,000 citations as of 2025 — yet the idea that endured is the residual connection itself, not the specific ResNet architecture, which is why you find `x + F(x)` in every modern transformer.
- The residual-stream view is sometimes called the "additive bus" or "accumulation register" model. In mechanistic interpretability research, it is the substrate on which transformer circuits are analysed: researchers trace how information written into the stream by one attention head at layer 3 is read by a different head at layer 18.
- The pre-activation ResNet design (He et al., 2016) successfully trained a **1001-layer** network on CIFAR-10 and achieved better accuracy than the 152-layer version — the only architecture at the time where depth beyond 200 layers continued to improve performance rather than degrade it.
- BatchNorm and ResNet were published within months of each other in 2015. Together with He initialisation (also 2015), they formed a triad — normalisation, residual connections, and scaled initialisation — that eliminated the depth barrier that had constrained neural networks since the 1990s. Every modern deep architecture rests on these three techniques.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---|---|---|
| **Forgetting the projection shortcut** | When `in_dim ≠ out_dim`, the identity `+` fails with a shape mismatch. PyTorch raises `RuntimeError: The size of tensor a (N, in_dim) must match the size of tensor b (N, out_dim)`. | Add a learned `nn.Linear(in_dim, out_dim)` as the projection shortcut. Use `nn.Identity()` when dimensions match. |
| **Placing BatchNorm/LayerNorm on the identity shortcut** | Normalisation on the shortcut breaks the gradient highway. The identity path is no longer `1 · ∂L/∂y` — it passes through a normalisation layer's backward computation, which scales the gradient by the inverse standard deviation and can amplify noise in deep networks. | Normalisation belongs on the residual branch only. In pre-norm: `x + F(Norm(x))`. In post-norm: `Norm(x + F(x))`. Never `Norm(x) + F(x)`. |
| **Initialising residual branches with large weights** | If `F(x)` produces outputs with magnitude comparable to or larger than `x`, the residual stream diverges over depth. By block 50, the stream magnitude may be 10× the input magnitude, saturating activations and causing gradient explosion. | Use zero-initialised last layers, ReZero, or Fixup scaling. Or rely on BatchNorm/LayerNorm on the residual branch to constrain output magnitude. |
| **Expecting plain deep networks to match residual performance with better hyperparameters** | The degradation problem is structural, not a hyperparameter issue. No learning-rate schedule, optimiser choice, or initialisation scheme fixes a plain 50-layer network to match a residual 50-layer network on CIFAR-10 — the loss landscape is fundamentally worse. | Use residual connections from the start. The cost of a single `+` operation per block is negligible relative to the matrix multiplications. |
| **Treating the residual connection as an optional trick** | In architectures where the residual stream is the core organisational principle (transformers, modern CNNs), removing residuals does not "simplify" the architecture — it makes it untrainable beyond a handful of layers. | Residual connections are load-bearing structure, not decoration. Design with the residual stream model from the start. |
| **Using `+=` in-place on a tensor that needs its computation graph** | `x += F(x)` modifies `x` in-place, breaking the autograd graph that connects `x` to earlier layers. The gradient can no longer flow backward through `x`'s history because the tensor's storage was overwritten. PyTorch may raise `RuntimeError: a leaf Variable that requires grad is being used in an in-place operation` or silently produce incorrect gradients. | Always use `x = x + F(x)` (out-of-place addition) in forward methods. The `+` operator creates a new tensor, preserving the computation graph. The overhead is negligible — a single tensor allocation per block. |

---

## Quiz

1. **A 56-layer plain network achieves 4% higher training error than a 20-layer version of the same architecture, and test error is correspondingly worse. Which of the following is the correct diagnosis?**
   <details>
   <summary>Answer</summary>
   This is the degradation problem — an optimisation failure, not overfitting. Overfitting would produce lower training error but higher test error. The deeper network cannot even fit its training data because the loss surface of a deep plain network is poorly conditioned compared to a shallower one. The residual connection fixes this by making identity the default behaviour, reshaping the loss surface so gradient descent finds a good minimum.
   </details>

2. **Derive the gradient ∂L/∂x through a residual connection y = x + F(x) and explain which term guarantees that gradients reach early layers without vanishing.**
   <details>
   <summary>Answer</summary>
   ∂L/∂x = ∂L/∂y · (1 + ∂F/∂x) = ∂L/∂y + ∂L/∂y · ∂F/∂x. The first term, ∂L/∂y, is the upstream gradient passed through the identity path unchanged. Even if ∂F/∂x is near-zero (because the residual branch has tiny weights or saturated activations), the full upstream gradient reaches x via the identity path. In a plain stack y = F(x), the gradient is ∂L/∂y · ∂F/∂x — if ∂F/∂x is small, the gradient vanishes. The additive `1` in the residual derivative is the gradient highway.
   </details>

3. **A pre-norm residual block computes y = x + F(LayerNorm(x)). Why is this preferred over y = LayerNorm(x + F(x)) for very deep transformer training?**
   <details>
   <summary>Answer</summary>
   In pre-norm, LayerNorm constrains the input to the sub-layer F, bounding F's output scale and keeping residual contributions moderate. The identity shortcut carries the gradient through without passing through LayerNorm's backward computation. In post-norm, the sub-layer's output is unconstrained — F(x) can have arbitrarily large magnitude — and LayerNorm after the addition normalises the result, which can mask growing magnitudes during forward pass but does not prevent gradient instability. Pre-norm is empirically more stable at depth (50+ layers) and is now standard in Llama, GPT, and most modern transformer designs.
   </details>

4. **You are designing a residual block where in_dim=128 and out_dim=256. The block contains two Linear layers. What must the shortcut do, and what happens if you omit it?**
   <details>
   <summary>Answer</summary>
   The shortcut must project the input from 128 to 256 dimensions using a learned `nn.Linear(128, 256)`. If omitted, the addition `x + F(x)` fails with a shape mismatch because `x` has shape `(N, 128)` and `F(x)` has shape `(N, 256)`. PyTorch raises a runtime error. A simple `nn.Identity()` shortcut only works when `in_dim == out_dim`.
   </details>

5. **In the residual-stream model, the output after L blocks is h_L = x + Σ F_k(h_{k-1}). What does this representation tell us about how information flows through a deep residual network compared to a plain deep network?**
   <details>
   <summary>Answer</summary>
   In the residual-stream model, every block's contribution is additive and persistent. Information written into the stream at block 5 is still present at block 50 unless a later block explicitly subtracts it out. In a plain network, each layer's output replaces the previous one — information from early layers must be encoded in a way that survives every subsequent nonlinear transformation. The additive property is why transformer attention heads can read information from any earlier layer and why patching an activation at an intermediate layer propagates cleanly forward. The stream is a cumulative, append-only data structure.
   </details>

6. **Why does zero-initialising the last layer of each residual branch produce near-identity behaviour at the start of training, and why is this useful?**
   <details>
   <summary>Answer</summary>
   When the last `nn.Linear` in the residual branch has all-zero weights, the branch output `F(x)` is exactly 0 regardless of earlier layers, so `y = x + 0 = x` — the block is exactly the identity function. As training proceeds and the last layer's weights move away from zero, the branch begins contributing. This is useful because it guarantees the deeper network starts at the same performance as a shallower one (since the extra blocks do nothing at first) and gradient descent can gradually activate residual branches as needed, rather than having to simultaneously discover both the correct function and the right amount of contribution from each block.
   </details>

---

## Hands-On Exercise

**Task:** Train a 50-layer MLP on a synthetic regression task and compare plain versus residual stacks by measuring both final loss and first-layer gradient norm throughout training. Follow these numbered steps in sequence, verifying your output at each stage:

1. Create a synthetic dataset: 1000 samples of `x ∈ R^{64} ~ N(0, 1)`, with target `y = sin(||x||₂) + ε` where ε is small Gaussian noise. This is a simple nonlinear function of a scalar summary — easy enough that a shallow network can learn it, but deep enough in architecture that the degradation problem is observable in a plain stack.

2. Build a `DeepMLP` class that stacks `depth` blocks, with a flag `use_residual` that switches between `nn.Sequential(Linear, ReLU, Linear)` blocks and `ResidualBlock`s. Both variants have the same number of `nn.Linear` layers.

3. Train both variants (plain and residual) for 200 epochs with Adam, learning rate 1e-3, MSE loss. Record the loss after every epoch and the gradient norm at the first layer after the final epoch.

4. Plot the loss curves. The plain stack should converge more slowly and to a higher final loss than the residual stack, despite having the same parameter count. Print the first-layer gradient norm for both — the residual stack's should be larger. The starter code block below provides the complete dataset, model classes, and comparison harness; your task is to fill in the training loop where indicated and run the comparison.

```python
import torch
import torch.nn as nn
import math

# ---- Dataset ----
torch.manual_seed(0)
N, dim = 1000, 64
x = torch.randn(N, dim)                          # (N, dim)
target = torch.sin(x.norm(dim=1, keepdim=True))  # (N, 1)
target += 0.05 * torch.randn(N, 1)               # noise

# ---- Your ResidualBlock (from Part 2) ----
class ResidualBlock(nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dim, dim),   # (dim, dim)
            nn.ReLU(),
            nn.Linear(dim, dim),   # (dim, dim)
        )

    def forward(self, x):
        return x + self.net(x)     # (N, dim) + (N, dim)

# ---- Deep MLP ----
class DeepMLP(nn.Module):
    def __init__(self, depth, dim, use_residual):
        super().__init__()
        self.input_proj = nn.Linear(dim, dim)    # (dim, dim)
        if use_residual:
            self.blocks = nn.ModuleList([ResidualBlock(dim) for _ in range(depth)])
        else:
            self.blocks = nn.ModuleList([
                nn.Sequential(nn.Linear(dim, dim), nn.ReLU(), nn.Linear(dim, dim))
                for _ in range(depth)
            ])
        self.head = nn.Linear(dim, 1)            # (dim, 1)

    def forward(self, x):
        h = self.input_proj(x)                   # (N, dim)
        for block in self.blocks:
            h = block(h)                         # (N, dim)
        return self.head(h)                      # (N, 1)

# ---- Training loop (fill in) ----
def train(model, x, target, epochs=200, lr=1e-3):
    optim = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()
    losses = []
    for epoch in range(epochs):
        # YOUR CODE: forward, loss, backward, optim step
        pass
    return losses

# ---- Compare ----
depth = 50
plain = DeepMLP(depth, dim, use_residual=False)
resid = DeepMLP(depth, dim, use_residual=True)

losses_plain = train(plain, x, target)
losses_resid = train(resid, x, target)

print(f"Final loss — plain: {losses_plain[-1]:.4f}, residual: {losses_resid[-1]:.4f}")
```

**Success criteria:** Run `python exercise_residual.py` and verify that:

- [ ] Loss curves printed or plotted: residual final loss should be lower than plain final loss.
- [ ] Plain stack's loss curve may plateau early or diverge; residual stack's loss decreases steadily.
- [ ] Output the first-layer gradient norm for both models after the final training step.

```bash
python exercise_residual.py
```

---

## Key Takeaways

1. **The degradation problem is an optimisation failure, not a signal problem.** A 56-layer plain network underperforms a 20-layer version on training error even with BatchNorm and ReLU — the loss surface is poorly conditioned, and gradient descent cannot find a good minimum.

2. **A residual connection `y = x + F(x)` provides a gradient highway.** The derivative `∂L/∂x = ∂L/∂y + ∂L/∂y · ∂F/∂x` guarantees at least one undiminished gradient path from the loss to every layer, regardless of `F`'s local derivatives. This is the autograd `+` distributes-gradient rule from Block A in architectural form.

3. **The residual-stream model views a deep residual network as an additive read/write bus.** Each block reads the current sum and writes its contribution by addition — no block can erase previous contributions. This is the unifying mental model for understanding information flow in ResNets and transformers.

4. **Pre-norm placement (`x + F(Norm(x))`) produces cleaner gradient highways than post-norm (`Norm(x + F(x))`).** In pre-norm, the identity shortcut carries the gradient without passing through any normalisation layer. In post-norm, the gradient path goes through LayerNorm's backward computation, which can scale or destabilise the signal.

5. **Near-identity initialisation is the key to deep residual training.** Zero-initialised last layers, ReZero, Fixup scaling, and the combination of LayerNorm with standard weight initialisation all produce residual branches that start near zero, so the network begins at the identity function and learns perturbations gradually.

6. **Residual connections are load-bearing structure.** They are not decoration or an optional trick. Every modern deep architecture — from ResNet-152 to Llama-4 — depends on residual connections as the primary mechanism for depth scaling. The `+` in `x + F(x)` is the most architecturally important operation in modern deep learning.

---

## Sources

- He, K., Zhang, X., Ren, S., & Sun, J. (2016). Deep Residual Learning for Image Recognition. *CVPR 2016*. https://arxiv.org/abs/1512.03385 — The original ResNet paper. Section 4.1 demonstrates the degradation problem; Section 3 describes the residual block.
- He, K., Zhang, X., Ren, S., & Sun, J. (2016). Identity Mappings in Deep Residual Networks. *ECCV 2016*. https://arxiv.org/abs/1603.05027 — Pre-activation residual blocks and the 1001-layer ResNet.
- Srivastava, R. K., Greff, K., & Schmidhuber, J. (2015). Highway Networks. https://arxiv.org/abs/1505.00387 — The gated precursor to ResNet.
- Huang, G., Liu, Z., van der Maaten, L., & Weinberger, K. Q. (2017). Densely Connected Convolutional Networks. *CVPR 2017*. https://arxiv.org/abs/1608.06993 — DenseNet concatenative skip connections.
- Bachlechner, T., Majumder, B. P., Mao, H. H., Cottrell, G. W., & McAuley, J. (2020). ReZero is All You Need: Fast Convergence at Large Depth. https://arxiv.org/abs/2003.04887 — Zero-initialised α scaling on residual branches.
- Zhang, H., Dauphin, Y. N., & Ma, T. (2019). Fixup Initialization: Residual Learning Without Normalization. *ICLR 2019*. https://arxiv.org/abs/1901.09321 — Fixup initialisation for training deep residual networks without BatchNorm.
- Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, Ł., & Polosukhin, I. (2017). Attention Is All You Need. https://arxiv.org/abs/1706.03762 — The original transformer paper; residual connections in Section 3.1.
- PyTorch documentation — `nn.Linear`, `nn.LayerNorm`, `nn.Module`. https://pytorch.org/docs/stable/
- d2l.ai — Dive into Deep Learning, Chapter 8: Modern Convolutional Neural Networks (ResNet). https://d2l.ai/chapter_convolutional-modern/resnet.html
- CS231n: Convolutional Neural Networks for Visual Recognition — Lecture 9: CNN Architectures. https://cs231n.github.io/convolutional-networks/
- The Annotated Transformer — Harvard NLP. https://nlp.seas.harvard.edu/annotated-transformer/ — Residual connections in encoder/decoder blocks.
- Lilian Weng — The Transformer Family. https://lilianweng.github.io/posts/2023-01-27-the-transformer-family-v2/ — Pre-norm vs post-norm discussion.

---

## Next Module

Continue to [Attention from Scratch](/ai-ml-engineering/deep-learning/module-1.4.3-attention-from-scratch/), where the residual-stream model you built here becomes the backbone of the transformer block.

---

## Learner check

> | 1.4.2 | [Residual Connections & Deep-Architecture Patterns](/ai-ml-engineering/deep-learning/module-1.4.2-residual-deep-architectures/) |
