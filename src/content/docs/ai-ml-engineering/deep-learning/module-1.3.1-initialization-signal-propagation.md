---
title: "Initialization & Signal Propagation"
slug: ai-ml-engineering/deep-learning/module-1.3.1-initialization-signal-propagation
sidebar:
  order: 1004.1
---

> **AI/ML Engineering Track** | Complexity: `[COMPLEX]` | Time: 4-5 hours
>
> **Prerequisites**: Block A modules A3 (Forward Propagation), A6 (Backprop by Hand), A7 (Tiny NumPy NN Lab), and A8 (Scalar Autograd). PyTorch fundamentals from module 1.2 are helpful but not strictly required.
>
> **Primary tools**: PyTorch 2.12, NumPy for cross-checks.

---

In 2010, Xavier Glorot and Yoshua Bengio published a paper at AISTATS titled "Understanding the difficulty of training deep feedforward neural networks." The paper opened with a puzzle that had frustrated practitioners for years: deep networks with more than a handful of hidden layers often failed to train at all, while shallow networks with the same total parameter count sometimes worked fine. The failure was not a bug in the optimizer or the loss function — it was a signal problem. Activations at the deepest layers were either vanishing toward zero or exploding toward infinity before the first gradient step completed, and the gradients flowing backward were distorted by the same compounding effect. Glorot and Bengio showed that the root cause was weight initialization: drawing weights from a distribution with unit variance, which seemed reasonable, actually multiplied activation variance by the fan-in at every layer. A ten-layer network with 512 units per layer could amplify variance by a factor of 512 ten times over — a number so large that floating-point arithmetic itself became the bottleneck.

Their fix was not a new optimizer or a new activation function. It was a scaling rule: initialize each weight from a distribution whose variance depends on the layer's fan-in and fan-out so that signals — both activations forward and gradients backward — remain near unit variance across depth. Five years later, Kaiming He and colleagues refined the rule for ReLU networks, adding a factor of two that accounts for ReLU zeroing half the activations on average. Those two papers — Glorot & Bengio (2010) and He et al. (2015) — are the engineering foundation beneath every modern deep network's first training step. In Block A you built forward propagation (A3), derived backward-pass VJPs by hand (A6), and trained a tiny MLP with manually chosen weight scales (A7). This module shows why that scale mattered, derives the variance rules from first principles, and maps them directly onto PyTorch's `nn.init` API so that `torch.Tensor` and `nn.Linear` feel like the same objects you already engineered in NumPy — just with the initialization discipline built in.

---

## Learning Outcomes

By the end of this module, you will be able to measure activation and gradient scale in deep PyTorch stacks, derive the variance propagation formulas that explain those measurements, and apply Xavier and He initialization correctly in production training code.

- **Implement** layer-wise activation and gradient standard-deviation probes in PyTorch 2.12 that make vanishing and exploding signals visible in a deep network before any optimizer step runs.
- **Derive** the forward-pass variance propagation formula `Var(out) = n_in · Var(W) · Var(in)` for a linear layer under zero-mean independence assumptions, and explain why preserving unit variance requires `Var(W) = 1/n_in`.
- **Compare** Xavier/Glorot and He/Kaiming initialization schemes, including their uniform and normal parameterizations, and select the appropriate scheme for tanh versus ReLU-family activations; **evaluate** when orthogonal initialization, LSUV, or normalization layers (forward-point to module B6) supplement or replace variance-scaled random init.
- **Apply** PyTorch initialization idioms — `nn.init.kaiming_normal_`, `nn.init.xavier_uniform_`, the `nonlinearity` and `gain` arguments, and the `model.apply(init_fn)` pattern — to debug training failures by inspecting weight statistics, layer-wise activation norms, and early gradient magnitudes rather than guessing at learning rates.

---

## Why This Module Matters

Training a deep network is a chain of multiplications. Every layer takes an input vector, multiplies it by a weight matrix, adds a bias, and passes the result through a nonlinearity. If the weights are too small, each multiplication shrinks the signal; after twenty or fifty layers the activations are indistinguishable from zero, the nonlinearities sit in their linear region or at saturation, and the gradients that backpropagation sends upstream are equally tiny. The optimizer receives gradient vectors full of numerical noise and cannot move the weights meaningfully — training appears to "not work" even though the code runs without errors. If the weights are too large, the opposite happens: activations explode layer by layer, floating-point values overflow to `inf` or `nan`, and the loss becomes undefined before you finish the first epoch.

This is not a hypothetical edge case. It is the default outcome when you stack many layers and initialize weights from `N(0, 1)` without scaling. The NumPy `Layer` class you built in A3 used He-style scaling (`std = sqrt(2/fan_in)`) almost incidentally — this module explains *why* that choice was necessary and what happens when you omit it. The backward-pass VJPs you derived in A6 propagate gradient variance through weight matrices transposed relative to the forward pass; a weight scale that preserves forward variance does not automatically preserve backward variance, which is why Xavier initialization compromises between fan-in and fan-out while He initialization targets the forward pass for ReLU nets where backward variance is less fragile.

PyTorch's `nn.Linear` and `nn.Conv2d` layers ship with sensible defaults (Kaiming uniform for linear layers in PyTorch 2.12), but defaults are not guarantees. Transfer learning, custom architectures, RNNs, and transformer blocks all require you to choose or override initialization deliberately. Normalization layers (module B6) reduce sensitivity to initialization but do not eliminate the need for it — a network with batch normalization still benefits from reasonable starting weights, and many architectures (especially RNNs and early transformer variants) train without normalization at all. Optimizers and learning-rate schedules (module B4) cannot fix a network whose signal is already dead on arrival. Initialization is the first engineering decision in every training run, and it is the one decision that costs nothing at runtime yet determines whether everything downstream is possible.

The engineering mindset here mirrors what you practiced in A6 when you finite-difference checked analytic gradients: treat a claim as untrusted until you measure it. Initialization theory gives you a formula; a ten-line PyTorch probe tells you whether that formula matches your actual architecture, activation choice, and layer widths. When someone reports that a fifty-layer MLP "will not learn," the first diagnostic is not "try Adam with lr=3e-4" — it is "print activation std at layer 25." If that number is `1e-9` or `1e6`, no optimizer rescues the run. This module gives you both the formula and the probe so you can classify the failure in minutes instead of burning GPU cycles on random hyperparameter sweeps.

There is also a subtle interaction between initialization and batch size that practitioners rediscover painfully. Gradient variance scales inversely with batch size when the loss is averaged over samples, as you saw when the `1/N` factor in A6's mean-loss gradient had to match the optimizer step. Initialization sets the *activation* scale before batching enters the picture, but if activations are already near zero, dividing gradients by a large batch makes them even smaller relative to weight magnitudes. Conversely, if activations are huge, a small batch produces noisy but enormous gradient spikes. Healthy initialization puts you in the regime where batch-size and learning-rate tuning in B4 actually matter — it widens the basin of trainable hyperparameters rather than replacing those hyperparameters entirely.

---

## Part 1: Making the Problem Visible

Before deriving formulas, run an experiment that prints numbers you can trust. The goal is to watch activation standard deviation at every layer of a deep stack and see it drift away from 1.0 — the healthy baseline for unit-variance inputs.

### 1.1 A deep linear stack with `N(0, 1)` weights

Consider a depth-`L` network of linear layers with no bias, each mapping `n` inputs to `n` outputs. Initialize every weight matrix with independent `N(0, 1)` entries. Feed in a batch of inputs where each feature has approximately unit variance:

```python
import torch

def probe_forward_stds(depth: int, n: int, init_std: float, activation=None):
    """Print activation std after each layer of a deep stack.

    Args:
        depth: number of weight layers
        n: fan-in / fan-out (square layers)
        init_std: standard deviation of weight initialization
        activation: optional callable (e.g., torch.tanh); None = linear only
    """
    torch.manual_seed(0)
    x = torch.randn(256, n)  # batch=256, features ~ N(0,1)
    print(f"input  std = {x.std():.4f}")

    for layer_idx in range(depth):
        W = torch.randn(n, n) * init_std  # shape (n, n), N(0, init_std^2)
        x = x @ W                         # (256, n) @ (n, n) -> (256, n)
        if activation is not None:
            x = activation(x)
        print(f"layer {layer_idx + 1:2d} std = {x.std():.4f}")

    return x

print("=== Linear only, N(0,1) weights, depth=10, n=512 ===")
probe_forward_stds(depth=10, n=512, init_std=1.0, activation=None)
```

On a typical run, the input std is near 1.0, layer 1 std jumps to roughly 22–23 (because `sqrt(512) ≈ 22.6`), layer 2 std exceeds 500, and by layer 10 the values are astronomical or overflow to `inf`. Each linear layer multiplies variance by approximately `n_in · Var(W) = 512 · 1 = 512`, so the standard deviation scales by `sqrt(512) ≈ 22.6` per layer. Over ten layers that is `22.6^10`, far beyond float32 range. This is **activation explosion**, and it happens before any training step — purely from initialization and forward propagation.

Compare with a small init: `init_std=0.01`. Now each layer shrinks variance by roughly `512 × 0.01² = 0.0512`, so std shrinks by about `sqrt(0.0512) ≈ 0.23` per layer. After ten layers the activations are near zero — **activation vanishing**.

### 1.2 The same stack with `tanh`

Nonlinearities change the picture but do not eliminate the problem, because saturation and vanishing gradients replace raw variance explosion as the primary failure mode when activations are poorly scaled. Run the same probe with `tanh` inserted after each linear map:

```python
print("\n=== tanh activations, N(0,1) weights, depth=50, n=256 ===")
probe_forward_stds(depth=50, n=256, init_std=1.0, activation=torch.tanh)
```

With large pre-activations, `tanh` saturates toward ±1, so activation std may appear stable near 0.7–0.8 in deeper layers — but this stability is deceptive. The saturated tanh outputs carry almost no usable gradient: `d tanh(z)/dz = 1 - tanh²(z) ≈ 0` when `|z|` is large. The forward signal looks fine while the backward signal is dead. This is the classic **vanishing gradient** problem that plagued deep tanh networks before ReLU and before proper initialization.

### 1.3 Probing gradient magnitudes

Forward std alone does not tell the whole story. Measure gradient std at each layer during a backward pass:

```python
import torch.nn as nn

class DeepLinearTanh(nn.Module):
    def __init__(self, depth, n, init_std):
        super().__init__()
        self.layers = nn.ModuleList([
            nn.Linear(n, n, bias=False) for _ in range(depth)
        ])
        for layer in self.layers:
            nn.init.normal_(layer.weight, mean=0.0, std=init_std)

    def forward(self, x):
        for layer in self.layers:
            x = torch.tanh(layer(x))
        return x

def probe_gradient_stds(depth=20, n=256, init_std=1.0):
    torch.manual_seed(1)
    model = DeepLinearTanh(depth, n, init_std)
    x = torch.randn(64, n, requires_grad=False)
    y = model(x).sum()  # scalar loss
    y.backward()

    print(f"init_std={init_std}, depth={depth}, n={n}")
    for i, layer in enumerate(model.layers):
        gstd = layer.weight.grad.std().item()
        print(f"  layer {i + 1:2d} weight grad std = {gstd:.6e}")

print("=== Gradient probe: bad init ===")
probe_gradient_stds(depth=20, n=256, init_std=1.0)
```

With `init_std=1.0`, gradient std typically **decreases** from the output layer toward the input — early layers receive tiny gradients and barely learn. With `init_std=0.01`, gradients may explode toward the input. The backward pass applies the same weight matrices transposed (exactly the VJP `dL_dX = dL_dY @ W.T` from A6), so variance preservation requires a *different* scaling constraint on `Var(W)` — one that involves fan-out rather than fan-in. Parts 2 and 3 derive both constraints and show how Xavier and He schemes reconcile them.

The asymmetry between forward and backward variance is easy to miss because both directions use the same weight tensor. In the forward pass each output neuron aggregates `n_in` inputs; in the backward pass each input neuron receives gradient contributions from `n_out` outputs. A square layer with `n_in = n_out = 512` makes both constraints identical, which is why early experiments on symmetric architectures masked the problem. Modern networks are rarely square: a projection from 2048 to 512 has very different fan-in and fan-out, and a compromise formula like Xavier's becomes necessary rather than optional. When you read PyTorch's `mode='fan_in'` versus `mode='fan_out'` in `kaiming_*`, you are choosing which direction gets priority — most feed-forward ReLU nets prioritize forward activations because dead activations are harder to recover from than slightly noisy gradients.

### 1.4 Connecting to Block A

In A3 you computed `Z = X @ W + b` and cached `Z` and `A` for backprop. In A7 you initialized `W` with `rng.normal(0, np.sqrt(2.0 / d_in), size=(d_in, d_out))` — He scaling for ReLU. The experiment above is the same computation in PyTorch: `nn.Linear` stores `W` with shape `(out_features, in_features)` and computes `x @ W.T + b`. The variance story is identical; only the weight layout differs from your NumPy convention where `W` was `(d_in, d_out)`. When reading PyTorch docs, always check whether a formula uses fan-in (columns of the weight matrix in the `(out, in)` layout) or fan-out (rows).

The connection to A8's scalar autograd is equally direct. When micrograd-style `Value` objects propagated local derivatives through a tiny graph, each `+` and `*` node had a backward rule that preserved the scale of the upstream gradient relative to the local partial derivative. A deep network with badly scaled weights is a graph where those local partial derivatives are uniformly too large or too small — `loss.backward()` still runs the correct VJP algebra from A6, but the numeric values flowing through the graph are unusable. Initialization is therefore the step that puts the computational graph in a numerically healthy regime before autograd executes. PyTorch does not rescale your weights for you; it faithfully differentiates whatever values you provide.

### 1.5 Intuition: why depth multiplies the problem

Shallow networks forgive bad init because there are few multiplication steps between input and output. A three-layer MLP with width 128 has at most three opportunities to amplify or shrink variance. A fifty-layer network compounds the per-layer factor fifty times — multiplicatively in variance, which means exponentially in standard deviation for linear stacks. This is the same compounding intuition you saw when XOR required only one hidden layer but deeper architectures in modern vision need dozens. Depth buys representational power at the cost of demanding disciplined signal engineering at every layer boundary. Initialization is how you pay that cost up front rather than discovering it through failed training runs.

---

## Part 2: Variance Propagation Mathematics

We now derive the scaling rule that the experiment demonstrated empirically. The derivation assumes independent, zero-mean weights and inputs — approximations that hold well at initialization before correlations develop during training.

### 2.1 One linear layer

Consider a single linear output unit (one row of the weight matrix) computing `y = sum_{j=1}^{n_in} w_j x_j`. Assume `E[w_j] = E[x_j] = 0` and that all `w_j` and `x_j` are mutually independent. The variance of the sum of independent products is `Var(y) = sum_j Var(w_j x_j) = sum_j Var(w_j) Var(x_j) = n_in * Var(W) * Var(x)`, where the last step uses identical variances across inputs and weights. In plain language: **output variance equals fan-in times weight variance times input variance**. If you want `Var(y) = Var(x)` — keeping the signal at unit scale — you need `Var(W) = 1/n_in`. For a weight matrix where each of the `n_in × n_out` entries is drawn independently from the same distribution, set `std(W) = 1 / sqrt(n_in)`. This is the **forward-pass preservation rule**.

The derivation is an approximation, not a law of nature. Once training begins, weights and activations become correlated: certain neurons co-activate, others compete, and the independence assumption breaks. That is acceptable because initialization only needs to produce a reasonable starting point for the first few hundred steps — not to predict activation statistics at epoch fifty. What the formula captures is the *multiplicative* nature of depth. Each layer applies the same scaling logic, so errors compound exponentially in the number of layers unless each layer's scale is carefully chosen. A network with five layers and unit-variance mistakes loses roughly five factors of scale; a network with fifty layers loses fifty. That is why shallow networks trained fine with naive init in the 1990s while deeper networks did not: depth turned a small per-layer error into a catastrophic global failure.

In A3 notation with `Y = X @ W + b` where `X:(N, d_in)` and `W:(d_in, d_out)`, each output neuron sums over `d_in` products, so `n_in = d_in`. PyTorch's `nn.Linear(d_in, d_out)` stores weight with shape `(d_out, d_in)`, so fan-in is `weight.shape[1]`. When you inspect a checkpoint's `state_dict`, always read fan-in from the second dimension of `*.weight` tensors — confusing it with fan-out is one of the most common initialization bugs in ported code.

### 2.2 Backward-pass variance

During backpropagation, the gradient with respect to the layer input is (from A6) `dL/dX = (dL/dY) @ W.T`. Each row of `dL/dX` is a sum over `n_out` products of upstream gradients and weights. By the same independence argument, `Var(dL/dx_j) = n_out * Var(W) * Var(dL/dy_j)`. To preserve gradient variance backward requires `Var(W) = 1 / n_out`. Forward and backward cannot both be satisfied exactly with a single random matrix unless `n_in = n_out`. Real networks have rectangular layers, so initialization schemes **compromise** between the two constraints. When you derived `dL_dX = G @ W.T` in A6, you were computing exactly the operation whose variance scales with fan-out; that is why a weight scale that looks perfect in a forward-only probe can still produce dying gradients in the earliest layers during backprop.

### 2.3 Effect of activations

Nonlinearities modify variance in activation-dependent ways, as summarized in the table below. The factor of one-half for ReLU is critical: even if the linear pre-activation has unit variance, the ReLU output has half the variance because roughly half the entries are zeroed. He initialization compensates with a factor of 2 in the weight variance (Part 4). Tanh and sigmoid introduce a different failure mode — not variance explosion but **saturation**, where outputs cluster near plus or minus one and local derivatives approach zero, starving the backward pass regardless of how carefully you scaled the weights.

### 2.4 Worked numeric example

| Activation | Effect on forward variance | Gradient concern |
|---|---|---|
| Identity (linear) | Preserves variance exactly under the linear rule | Same as forward |
| `tanh` / sigmoid | Saturates: large inputs produce outputs near plus or minus one, variance bounded | Gradients vanish when saturated |
| ReLU | Zeros negative half: `Var(out)` is about half of `Var(pre_activation)` | Gradient is 0 or 1 — no shrinkage, but dead neurons |

Suppose `n_in = 256`, inputs have `Var(x) = 1`, and weights are `N(0, 1)`. Then `Var(y) = 256`, so `std(y)` is about 16, and to target `std(y)` near 1 you need `Var(W) = 1/256`, giving `std(W) = 1/16 = 0.0625`. The following PyTorch snippet verifies this single-layer relationship before you trust it in a deep stack:

```python
n = 256
x = torch.randn(10000, n)  # large batch for stable std estimate
W_bad = torch.randn(n, n)           # std = 1.0
W_good = torch.randn(n, n) / (n ** 0.5)  # std = 1/sqrt(n)

y_bad = x @ W_bad
y_good = x @ W_good

print(f"std(x)      = {x.std():.4f}")       # ~1.0
print(f"std(y_bad)  = {y_bad.std():.4f}")    # ~16
print(f"std(y_good) = {y_good.std():.4f}")    # ~1.0
```

This single-layer check is the building block for deep stacks: if each layer preserves variance, a 50-layer network maintains stable activations throughout. Run it whenever you port a formula from a paper into PyTorch — a transposed weight layout or a mistaken fan-in dimension silently turns a correct equation into an incorrect scale, and this three-line probe catches that mistake before you build fifty layers on top of it.

---

## Part 3: Xavier / Glorot Initialization

Xavier Glorot and Yoshua Bengio (2010) proposed initializing weights to balance forward and backward variance for symmetric activations like `tanh` and sigmoid, where the activation's derivative is largest near zero and gradients flow best when pre-activations stay in that region.

### 3.1 The compromise formula

Xavier initialization sets `Var(W) = 2 / (n_in + n_out)`. The factor of 2 accounts for the uniform distribution variant described below. For layers where `n_in` is approximately equal to `n_out`, this is close to both `1/n_in` and `1/n_out` simultaneously. The scheme keeps pre-activations in the linear region of `tanh` where gradients are near 1, avoiding both saturation and vanishing. When layer widths differ substantially — for example a bottleneck layer mapping 2048 units to 64 — the compromise lands closer to one constraint than the other, which is still far better than ignoring the mismatch entirely.

### 3.2 Uniform and normal parameterizations

PyTorch provides both forms via `nn.init.xavier_uniform_` and `nn.init.xavier_normal_`:

| Distribution | Parameterization | PyTorch call |
|---|---|---|
| Uniform | `W ~ U(-a, a)` where `a = sqrt(6 / (n_in + n_out))` | `nn.init.xavier_uniform_(tensor, gain=1.0)` |
| Normal | `W ~ N(0, 2 / (n_in + n_out))` | `nn.init.xavier_normal_(tensor, gain=1.0)` |

The uniform bound `a` is chosen so that for uniform `U(-a,a)`, variance equals `a²/3`. Setting `a = sqrt(6/(n_in+n_out))` gives `Var(W) = 2/(n_in+n_out)`. The normal form uses `std = sqrt(2/(n_in+n_out))` directly. Both distributions are equally valid; uniform init was common in early TensorFlow examples while normal init is more common in PyTorch codebases today. The variance target is identical — only the tail behavior differs, which matters slightly for regularization but rarely changes training outcomes for large matrices where the central limit theorem applies across thousands of weight entries.

```python
import torch.nn as nn

layer = nn.Linear(512, 512, bias=True)
nn.init.xavier_uniform_(layer.weight)
nn.init.zeros_(layer.bias)  # bias convention: start at 0

print("weight std:", layer.weight.std().item())
print("expected:  ", (2.0 / (512 + 512)) ** 0.5)
```

The `gain` argument scales the effective variance for activations that amplify or shrink signals. PyTorch's `nn.init.calculate_gain(nonlinearity)` returns recommended gains — for example `tanh` uses gain approximately 5/3 and ReLU uses `sqrt(2)`. When a paper specifies init for linear activations but your network uses ReLU, pass the matching `nonlinearity` string so PyTorch adjusts the gain automatically rather than applying a mismatched scale that would leave activations systematically far too large or far too small at the very first training step.

### 3.3 When to use Xavier

Use Xavier (Glorot) initialization when your hidden activations are **symmetric and saturating** — `tanh`, logistic sigmoid, or linear output layers in encoder-decoder architectures. It remains the standard for LSTM and GRU gates in many implementations, though LSTM-specific schemes exist. For ReLU-family activations, Xavier leaves activations slightly too small on average because it does not account for ReLU halving variance; use He initialization instead (Part 4).

Historically, Xavier initialization unlocked training for deeper tanh networks in the early 2010s, contributing directly to the resurgence of deep learning after the long "AI winter" period when multilayer perceptrons were considered too fragile to stack. Before Glorot and Bengio's analysis, practitioners often used ad-hoc scales like `1/sqrt(n)` without understanding the forward-backward tradeoff, and hyperparameter search over init scale was common. The paper replaced guesswork with a single line you could compute from layer dimensions. When you encounter legacy code or academic reproductions that mention "Glorot uniform," they refer to the same scheme as "Xavier uniform" in PyTorch — the naming split is purely historical, not mathematical.

---

## Part 4: He / Kaiming Initialization for ReLU Networks

Kaiming He, Xiangyu Zhang, Shaoqing Ren, and Jian Sun (2015) analyzed variance propagation through ReLU layers and showed that Xavier's compromise is suboptimal when half the activations are zeroed at every layer.

### 4.1 Deriving the factor of 2

For a pre-activation `z` with zero mean and unit variance, ReLU output is `a = max(0, z)`. Because ReLU zeros the negative half of the distribution, `Var(a) = 0.5 * Var(z)`, so the linear part must produce pre-activation variance 2 rather than 1 to maintain unit output variance after ReLU. Since `Var(pre) = n_in * Var(W) * Var(x_in)`, preserving unit output variance after ReLU requires `n_in * Var(W) * Var(x_in) = 2 * Var(x_in)`, which simplifies to `Var(W) = 2 / n_in`. Equivalently, `std(W) = sqrt(2 / n_in)`. This is the **He (Kaiming) initialization** — the default philosophy for modern convolutional and transformer feed-forward blocks using ReLU, GELU, or similar non-saturating activations. Compare to your A7 NumPy code: `W = rng.normal(0, np.sqrt(2.0 / d_in), ...)`. That line was He initialization. PyTorch's `nn.init.kaiming_normal_` computes the same scale.

### 4.2 Uniform and normal forms

| Distribution | Parameterization | PyTorch call |
|---|---|---|
| Normal | `W ~ N(0, 2/n_in)` with `mode='fan_in'` | `nn.init.kaiming_normal_(w, mode='fan_in', nonlinearity='relu')` |
| Uniform | `W ~ U(-a, a)` where `a = sqrt(6/n_in)` | `nn.init.kaiming_uniform_(w, mode='fan_in', nonlinearity='relu')` |

The `mode` argument selects whether fan-in (`'fan_in'`), fan-out (`'fan_out'`), or the average (`'fan_avg'`) appears in the denominator. Default for `'fan_in'` matches the derivation above. For convolutions, fan-in includes kernel size: `n_in = in_channels × kernel_h × kernel_w`.

```python
conv = nn.Conv2d(64, 128, kernel_size=3, padding=1)
nn.init.kaiming_normal_(conv.weight, mode='fan_in', nonlinearity='relu')
fan_in = 64 * 3 * 3
expected_std = (2.0 / fan_in) ** 0.5
print(f"conv weight std: {conv.weight.std():.5f}, expected: {expected_std:.5f}")
```

For `LeakyReLU` with negative slope `a`, PyTorch's `calculate_gain('leaky_relu', param=a)` adjusts the variance factor because fewer activations are zeroed.

### 4.3 When to use He

Use He (Kaiming) initialization for any network whose hidden layers use **ReLU, LeakyReLU, PReLU, or GELU** (GELU is often close enough that He init works well in practice). ResNet, VGG, and most vision backbones rely on this scheme. PyTorch 2.12 applies Kaiming uniform with `a=sqrt(5)` as the default for `nn.Linear` — slightly different from pure He for ReLU but within the same design family.

The ResNet paper (He et al., 2016) demonstrated that with proper initialization and residual connections, networks with 100+ layers could train on ImageNet — a result that would have been unthinkable with `N(0,1)` init. Residual shortcuts provide an additional path for gradients to flow, but they do not remove the need for reasonable weight scales in the convolutional blocks themselves. When you initialize a modern vision transformer's MLP sublayers, you are still applying the same fan-in variance logic, even though the architecture looks nothing like a 2012 AlexNet. The activation changed from ReLU to GELU; the init philosophy remained variance preservation adapted to the nonlinearity.

---

## Part 5: Orthogonal Initialization and Other Schemes

Variance-scaled random initialization is the default tool, but several alternatives address specific architectural needs when independence-based variance formulas are insufficient or when the same weight matrix is applied repeatedly across time or depth in ways that amplify small scaling errors.

### 5.1 Orthogonal initialization

An orthogonal matrix `Q` satisfies `Q Q^\top = I`. Initialized as a random orthogonal matrix via SVD of a Gaussian draw, weights preserve vector norms exactly: `||Qx|| = ||x||` when `Q` is square. This prevents both explosion and vanishing across depth for linear maps and helps recurrent networks maintain hidden state magnitude over many time steps (forward-point to RNN modules in section 1.5).

```python
nn.init.orthogonal_(layer.weight, gain=1.0)
```

Orthogonal init is common for RNN hidden-to-hidden weights where the same matrix is applied repeatedly across time steps, compounding variance errors that feed-forward networks experience only across depth. It is less common for standard CNN or transformer feed-forward layers where Kaiming init is simpler and performs equally well. PyTorch implements orthogonal initialization via `nn.init.orthogonal_(tensor, gain=1.0)`, which performs an SVD on a random Gaussian matrix and returns an orthogonal factor. The optional `gain` scales the singular values uniformly, letting you combine norm preservation with a desired output amplitude when the downstream nonlinearity expects a specific input scale.

### 5.2 Layer-Sequential Unit-Variance (LSUV)

LSUV (Mishkin & Matas, 2016) initializes with orthogonal matrices, then iteratively rescales each layer's weights so that empirical output variance on a sample batch equals 1. It is more expensive than closed-form rules but adapts to exotic activations or architectures where analytical variance formulas are messy. Use LSUV when standard rules fail and you have compute budget for a data-dependent init pass. The method bridges random init and normalization: it uses real data to calibrate scales layer by layer, which can rescue architectures where neither Xavier nor He assumptions hold cleanly, such as networks with custom activations or unusual connectivity patterns.

### 5.3 Bias initialization

Bias vectors are almost always initialized to **zero**. Non-zero bias shifts the pre-activation distribution away from the origin, which matters for ReLU (shifting how many units start active) and batch normalization (which expects zero-centered inputs at init in some formulations). Output-layer biases sometimes receive special treatment — for example, initializing a binary classification bias to `-log((1-π)/π)` where π is the prior positive rate — but hidden-layer biases stay at zero unless you have a specific reason.

### 5.4 Normalization layers change the game — but do not remove init

Batch normalization (module B6), layer normalization, and RMSNorm re-center and re-scale activations during training, dramatically reducing sensitivity to initialization scale. ResNet trains with BN partly because it can tolerate a wider range of initial weight scales. However:

- Normalization does not help if the very first forward pass produces `nan` before BN statistics are computed.
- Many architectures (RNNs without BN, early transformers, reinforcement-learning heads) still depend on good init.
- Even with BN, better initialization leads to faster convergence and more stable early training curves.

Treat normalization as a complement to initialization, not a replacement. Batch normalization (module B6) will re-scale activations during training, but the first forward pass still runs on uninitialized statistics, and layers without normalization remain sensitive to weight scale throughout training.

### 5.5 Residual connections and init scale

Residual networks add a skip connection `y = F(x) + x` that gives gradients a direct highway past the stacked layers. This architectural choice reduces effective depth for gradient flow but does not change the forward activation scale in the residual branch `F(x)`. If `F(x)` has exploding variance, the sum `F(x) + x` is dominated by `F(x)` and the skip connection stops helping. ResNet-style training therefore combines He initialization in convolutional blocks with careful scaling of the final batch-norm gamma in each residual branch (often initialized to zero in the last BN of a block so early training behaves like an identity). You do not need to master residual init patterns in this module, but you should recognize that architecture and initialization co-evolve — neither alone explains why modern deep nets train.

---

## Part 6: PyTorch Initialization in Practice

PyTorch centralizes initialization in `torch.nn.init`. Every `nn.Module` with learnable parameters exposes `.weight` and `.bias` tensors you can initialize after construction or via a recursive apply function.

### 6.1 Inspecting defaults

When you construct `nn.Linear(256, 256)` without custom init, PyTorch calls `reset_parameters()` which uses Kaiming uniform scaling derived from the fan-in and the LeakyReLU parameter `a=sqrt(5)` in the default implementation:

```python
import math
import torch.nn as nn

layer = nn.Linear(256, 256)
w = layer.weight
print("default weight shape:", w.shape)          # (256, 256) = (out, in)
print("default weight std:  ", w.std().item())
# PyTorch default nn.Linear uses kaiming_uniform_(a=sqrt(5)) -> gain=sqrt(1/3),
# so the uniform bound is 1/sqrt(fan_in). (sqrt(6/fan_in) would be the ReLU/gain=sqrt(2) bound.)
fan_in = w.shape[1]
bound = 1.0 / math.sqrt(fan_in)
print("approx Kaiming uniform bound:", bound)
```

Always inspect rather than assume. Third-party modules, copied code, and `load_state_dict` from checkpoints may leave weights in arbitrary states. When you wrap a pretrained backbone and add a new classification head, the backbone weights come from someone else's init and training, while your head needs explicit init — leaving the head at PyTorch defaults is fine, but leaving it at whatever random state existed after a partial `load_state_dict` is not.

### 6.5 Convolutional layers and fan-in

For `nn.Conv2d(in_channels, out_channels, kernel_size=k)`, fan-in is `in_channels * k * k` (times kernel height and width for non-square kernels). Each output pixel is a sum over all input channels and kernel positions, so the variance formula uses the full receptive field size, not just channel count:

```python
conv = nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3)
fan_in = 3 * 7 * 7  # 147
he_std = (2.0 / fan_in) ** 0.5
nn.init.kaiming_normal_(conv.weight, mode='fan_in', nonlinearity='relu')
print(f"conv fan_in={fan_in}, he_std={he_std:.4f}, actual std={conv.weight.std():.4f}")
```

The same `model.apply(init_fn)` pattern handles both Linear and Conv2d by checking `isinstance`. For depthwise-separable convolutions, fan-in per group differs from standard conv — always compute fan-in from the actual weight tensor shape rather than memorizing a formula for one conv type.

### 6.2 The `model.apply(init_fn)` pattern

The idiomatic way to initialize an entire model is a recursive `apply` function that pattern-matches module types and assigns the correct scheme to each, rather than hand-initializing tensors after construction:

```python
def init_weights(m):
    if isinstance(m, nn.Linear):
        nn.init.kaiming_normal_(m.weight, mode='fan_in', nonlinearity='relu')
        if m.bias is not None:
            nn.init.zeros_(m.bias)
    elif isinstance(m, nn.Conv2d):
        nn.init.kaiming_normal_(m.weight, mode='fan_in', nonlinearity='relu')
        if m.bias is not None:
            nn.init.zeros_(m.bias)

model = nn.Sequential(
    nn.Linear(784, 256),
    nn.ReLU(),
    nn.Linear(256, 128),
    nn.ReLU(),
    nn.Linear(128, 10),
)

model.apply(init_weights)

# Verify
for name, param in model.named_parameters():
    if 'weight' in name:
        print(f"{name:30s} std={param.std():.5f}")
```

This pattern mirrors what you did manually in A7 — loop over layers, set scale per layer width — but delegates the variance math to `nn.init`.

### 6.3 Mapping Block A concepts to PyTorch

| Block A (NumPy) | PyTorch 2.12 | Notes |
|---|---|---|
| `W = rng.normal(0, sqrt(2/d_in), (d_in, d_out))` | `nn.init.kaiming_normal_(m.weight, mode='fan_in', nonlinearity='relu')` | Weight layout transposed: PyTorch stores `(out, in)` |
| Manual `W -= lr * dW` | `optimizer.step()` after `loss.backward()` | A8 autograd maps to `torch.autograd` |
| `Layer.forward` caching `Z`, `A` | `nn.Module` forward + autograd graph | Same VJPs, automated |
| He scale in A3 Part 5 preview | Default `nn.Linear` reset | Same formula, built in |

When porting NumPy init code, remember to transpose the shape convention or use PyTorch's fan-in based on `weight.shape[1]`.

### 6.4 Custom initialization for specific layers

Sometimes one layer needs different treatment — most commonly the output classification head, which may use Xavier scaling while hidden ReLU layers use He init:

```python
class MLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.hidden = nn.Linear(512, 512)
        self.output = nn.Linear(512, 10)

    def forward(self, x):
        x = torch.relu(self.hidden(x))
        return self.output(x)

def init_mlp(m):
    if isinstance(m, nn.Linear):
        if m.out_features == 10:  # output head
            nn.init.xavier_uniform_(m.weight, gain=1.0)
        else:
            nn.init.kaiming_normal_(m.weight, nonlinearity='relu')
        if m.bias is not None:          # zero ALL biases (hidden + output); safe if bias=False
            nn.init.zeros_(m.bias)

mlp = MLP()
mlp.apply(init_mlp)
```

Output layers with softmax plus cross-entropy (A5) often train fine with smaller Xavier-scaled weights because the loss gradient `p - y` is already well-scaled at the head. The hidden layers are where He init matters most. When you fine-tune a pretrained backbone, you typically leave backbone weights untouched and initialize only the new head — the same principle applies: match init scheme to activation and layer role, not a one-size-fits-all default across the entire module tree.

### 6.6 Transfer learning and partial initialization

Loading a pretrained checkpoint is not initialization in the random sense, but it interacts with init discipline. When you replace the final layer of a pretrained ResNet with a new ten-class head, PyTorch creates fresh `nn.Linear` weights with default Kaiming init while the backbone retains trained values. If you accidentally call `model.apply(init_weights)` after loading, you overwrite the pretrained backbone with random weights — a common bug in transfer-learning scripts. The safe pattern is: load checkpoint, then initialize only parameters that were not loaded (detect by missing keys or by module name prefix). Initialization thinking applies whenever weights first enter the training loop, whether from a random generator or from disk.

---

## Part 7: Closing the Loop — Verifying Stable Propagation

Return to the Part 1 experiment and re-run with He initialization. The activation std should remain near 1.0 across all 50 layers:

```python
def probe_forward_stds_he(depth: int, n: int, activation=torch.tanh):
    """Deep stack with He-scaled weights: std(W) = sqrt(2/n)."""
    torch.manual_seed(0)
    x = torch.randn(256, n)
    print(f"input  std = {x.std():.4f}")

    he_std = (2.0 / n) ** 0.5
    for layer_idx in range(depth):
        W = torch.randn(n, n) * he_std
        x = x @ W
        if activation is not None:
            x = activation(x)
        print(f"layer {layer_idx + 1:2d} std = {x.std():.4f}")

print("=== tanh + He init, depth=50, n=256 ===")
probe_forward_stds_he(depth=50, n=256, activation=torch.tanh)
```

For `tanh`, He init (designed for ReLU) is not the theoretically optimal choice — Xavier is — but it keeps pre-activations modest and avoids saturation far better than `N(0,1)`. For a ReLU stack, He init is the correct match:

```python
print("\n=== ReLU + He init, depth=50, n=256 ===")
probe_forward_stds_he(depth=50, n=256, activation=torch.relu)
```

Layer-wise std values should cluster between 0.8 and 1.2 throughout depth. Re-run the gradient probe from Part 1.3 with `init_std=(2/n)**0.5`:

```python
print("\n=== Gradient probe: He init ===")
probe_gradient_stds(depth=20, n=256, init_std=(2.0 / 256) ** 0.5)
```

Gradient std across layers should be same order of magnitude — not decaying by ten orders from output to input. This empirical closure confirms the math: correct initialization is a variance engineering problem you can measure before spending GPU hours on a doomed training run.

When training a real model, add lightweight logging on the first batch so you capture activation scale before the optimizer has changed any weights:

```python
def log_activation_stats(model, x, tag=""):
    with torch.no_grad():
        activations = []
        h = x
        for module in model:
            h = module(h)
            if isinstance(h, torch.Tensor):
                activations.append(h.std().item())
    print(f"{tag} activation stds:", [f"{s:.3f}" for s in activations[:5]], "...")
```

If stds drift outside `[0.1, 10]` in the first forward pass, fix initialization before tuning the learning rate (module B4). If stds look healthy but loss still diverges, look next at normalization (B6) or optimizer settings — but init is always the first check.

### 7.1 Building a reusable init diagnostic

Production training code often wraps the probe into a hook or callback that runs once on the first batch:

```python
@torch.no_grad()
def activation_stats(model, x):
    # Forward hooks capture each layer's real output during one actual forward pass,
    # so this works regardless of branching, residuals, or functional (torch.relu) activations.
    stats, handles = [], []
    def hook(module, inp, out):
        stats.append((module.__class__.__name__, out.std().item()))
    for m in model.modules():
        if isinstance(m, (nn.Linear, nn.Conv2d)):
            handles.append(m.register_forward_hook(hook))
    try:
        model(x)
    finally:
        for h in handles:
            h.remove()
    return stats
```

Call this before `optimizer.step()` on step zero. Log the stats to your experiment tracker. When a run fails at epoch 3, you can compare its step-zero stats against a known-good baseline and immediately know whether initialization drift (from a code change, a partial checkpoint reload, or a mistaken `reset_parameters` call) caused the regression. This is cheaper than re-running full training with five learning rates hoping one works.

### 7.2 Forward pointers: normalization and optimizers

This module stops at initialization because signal scale at step zero is a prerequisite for everything that follows, not because the other training-engineering tools are unimportant. Module B6 (normalization) attacks a related but distinct problem: even with good init, internal covariate shift during training can destabilize activations as weights update. Batch norm and layer norm re-standardize activations on the fly, reducing sensitivity to init scale — but they introduce their own engineering concerns (batch-size dependence, train/eval mode toggles, running-statistics lag). Module B4 (optimizers) determines how gradient information is accumulated and scaled over time; AdamW and learning-rate warmup can rescue some mildly bad inits but cannot reconstruct a signal that has already vanished to machine epsilon. The recommended diagnostic order when training fails is therefore: check init stats first, then normalization behavior, then optimizer and learning-rate schedule — the same order as the Block B module sequence.

---

## Did You Know?

- **The name "Xavier"** comes from Xavier Glorot's first name — the scheme is also called **Glorot initialization** after the first author. Papers and frameworks use both names interchangeably; PyTorch prefers `xavier_*` in API names.
- **He initialization was first published on arXiv** in February 2015 as "Delving Deep into Rectifiers" (arXiv:1502.01852) and helped enable training of 100+ layer ResNets that won ImageNet 2015. The same team later formalized the PReLU activation in the same paper.
- **PyTorch's default Linear init is not exactly pure He** — it uses Kaiming uniform with `a=sqrt(5)` derived from the LeakyReLU parameterization in the original `reset_parameters` design. For strict ReLU networks, explicitly calling `kaiming_normal_(..., nonlinearity='relu')` is clearer and matches the textbook formula.
- **Orthogonal initialization connects to linear algebra**, not probability: the set of orthogonal matrices has measure zero in the space of all matrices, but the SVD-based sampling algorithm produces a uniform distribution over the orthogonal group — a rare case where "random" also means "structure-preserving."

---

## Common Mistakes

| Mistake | Problem | Solution |
|---|---|---|
| Using `N(0, 1)` weights in deep networks | Activations explode or vanish exponentially with depth; training never starts | Scale by `1/sqrt(fan_in)` at minimum; use He or Xavier formulas |
| Applying Xavier init to ReLU hidden layers | Ignores ReLU halving variance; activations shrink layer by layer | Use `nn.init.kaiming_normal_(..., nonlinearity='relu')` for ReLU stacks |
| Applying He init to `tanh` / sigmoid stacks | Pre-activations may be larger than Xavier targets; more saturation risk | Use `nn.init.xavier_uniform_` or `xavier_normal_` for symmetric activations |
| Confusing NumPy `(d_in, d_out)` with PyTorch `(out, in)` layout | Correct formula applied to wrong dimension; init still wrong | Always use `weight.shape[1]` as fan-in for PyTorch `nn.Linear` |
| Initializing biases to large random values | Shifts ReLU activation fraction; batch norm running stats start biased | Initialize all hidden biases to zero unless you have a domain-specific reason |
| Assuming `nn.Linear` defaults save you after `load_state_dict` partial load | Missing or mismatched keys leave some layers randomly initialized | After any partial load, verify `named_parameters()` std values explicitly |
| Tuning learning rate when loss is `nan` on batch 1 | Optimizer cannot fix overflow that happened in forward pass | Probe activation std first; fix init or add normalization (B6) |

---

## Quiz

1. **Why does `Var(out) = n_in · Var(W) · Var(in)` require independence assumptions, and what breaks first during training?**

   <details>
   <summary>Answer</summary>

   The formula treats each product `w_j x_j` as independent with zero mean so that cross-terms vanish in `Var(Σ w_j x_j)`. During training, weights and activations become correlated because the network learns structure — the formula describes initialization, not late training. What breaks first is usually saturation: even with correct init variance, updates can push activations into tanh/sigmoid flat regions where gradients vanish regardless of the independence assumption.

   </details>

2. **A linear layer has `n_in=1024`, `n_out=256`. What is the Xavier normal std and the He normal std (fan-in mode)?**

   <details>
   <summary>Answer</summary>

   Xavier: `std = sqrt(2 / (n_in + n_out)) = sqrt(2 / 1280) ≈ 0.0395`.
   He (fan-in): `std = sqrt(2 / n_in) = sqrt(2 / 1024) ≈ 0.0442`.
   He allows slightly larger weights because ReLU will halve the forward variance afterward. For this rectangular layer, Xavier sits between the forward-only (`1/1024`) and backward-only (`1/256`) targets.

   </details>

3. **You stack 40 ReLU layers with He init and batch normalization after each layer. Activation std is stable but loss is flat. Is initialization the problem?**

   <details>
   <summary>Answer</summary>

   Probably not. Batch normalization (B6) actively re-scales activations, so stable std confirms init and BN are doing their jobs. A flat loss with healthy activations points to optimizer dynamics (B4), learning rate, label issues, or a model capacity / task mismatch. Initialization was necessary but not sufficient — proceed to optimizer and data debugging.

   </details>

4. **How does `loss.backward()` in PyTorch relate to the hand-derived VJPs in A6?**

   <details>
   <summary>Answer</summary>

   `loss.backward()` traverses the autograd graph in reverse topological order, applying the same VJP rules you derived: dense layers use `dL_dW = X.T @ G`, `dL_dX = G @ W.T`; ReLU multiplies by `(Z > 0)`. The scalar autograd engine in A8 records operations during forward; PyTorch's `torch.autograd` does the same at tensor scale. Initialization determines whether the numeric values flowing through those VJPs are well-scaled or dominated by rounding error.

   </details>

5. **When would orthogonal initialization be preferred over He or Xavier?**

   <details>
   <summary>Answer</summary>

   Orthogonal init preserves norms exactly and is preferred for recurrent hidden-to-hidden weights applied across many time steps, where variance errors compound multiplicatively at each timestep. It is also useful in very deep linear or near-linear pathways (some normalizing-flow components). For standard feed-forward ReLU CNNs, He init is simpler and equally effective.

   </details>

6. **What printed output confirms that He initialization fixed the Part 1 explosion experiment?**

   <details>
   <summary>Answer</summary>

   Layer-wise activation std values that stay roughly in `[0.5, 1.5]` across all 50 layers (instead of growing by 10× per layer or decaying toward 0), and gradient std values that do not drop by more than 1–2 orders of magnitude from the last layer to the first. The absolute numbers depend on batch size and seed, but stability across depth is the signature of correct init.

   </details>

---

## Hands-On Exercise

**Task**: Build a diagnostic script that compares three initialization strategies on the same deep MLP architecture and reports whether signal propagation is healthy. Follow the steps below to construct the model, apply each init scheme, probe forward activation standard deviation at several depths, run a backward pass to inspect gradient scale, and record which strategies show exploding, vanishing, or stable statistics. The starter skeleton below provides the class structure; you fill in the comparison loop and interpret the printed numbers against the variance rules derived in Part 2.

```python
import torch
import torch.nn as nn

class DeepMLP(nn.Module):
    def __init__(self, depth=30, width=256, n_classes=10):
        super().__init__()
        layers = []
        for _ in range(depth):
            layers += [nn.Linear(width, width), nn.ReLU()]
        layers.append(nn.Linear(width, n_classes))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)

def apply_init(model, scheme: str):
    for m in model.modules():
        if isinstance(m, nn.Linear):
            if scheme == "bad":
                nn.init.normal_(m.weight, 0.0, 1.0)
            elif scheme == "xavier":
                nn.init.xavier_normal_(m.weight)
            elif scheme == "he":
                nn.init.kaiming_normal_(m.weight, nonlinearity='relu')
            if m.bias is not None:
                nn.init.zeros_(m.bias)

def probe_model(model, x, layer_indices=(0, 18, 38, 58)):
    """Probe std after selected Sequential indices (Linear+ReLU pairs)."""
    activations = []
    h = x
    for i, module in enumerate(model.net):
        h = module(h)
        if i in layer_indices:
            activations.append((i, h.std().item()))
    return activations

# Run for scheme in ["bad", "xavier", "he"] and compare
```

Your success criteria:

- [ ] Bad init shows std changing by more than 10x between layer 1 and layer 30 in either direction.
- [ ] He init keeps hidden-layer std within roughly `[0.3, 3.0]` across depth.
- [ ] Gradient std for He init does not differ by more than 100x between first and last hidden layer.
- [ ] You can explain in one sentence why He outperforms Xavier for this ReLU MLP.

Verification requires no external dataset — random input suffices because initialization quality is a property of the untrained network's forward and backward pass geometry, not of the data distribution.

---

## Key Takeaways

- Deep networks multiply variance at every layer: for a linear map, `Var(out) = n_in · Var(W) · Var(in)` under zero-mean independence; preserving unit signal requires `Var(W) = 1/n_in`.
- Backward-pass gradient variance imposes a complementary constraint `Var(W) = 1/n_out`; Xavier initialization compromises with `Var(W) = 2/(n_in + n_out)` for tanh/sigmoid, while He initialization uses `Var(W) = 2/n_in` to account for ReLU halving variance.
- PyTorch 2.12 exposes these rules through `nn.init.xavier_*`, `nn.init.kaiming_*`, and `nn.init.orthogonal_*`; the `model.apply(init_fn)` pattern initializes entire architectures consistently.
- Always verify initialization empirically — print layer-wise activation and gradient std on the first forward-backward pass before tuning optimizers (B4) or adding normalization (B6).
- Block A's manual weight scaling in A3/A7 was He initialization in disguise; PyTorch automates the same math that you previously wrote as `sqrt(2/d_in)`.

---

## Sources

- Glorot, X., & Bengio, Y. (2010). Understanding the difficulty of training deep feedforward neural networks. *AISTATS*. http://proceedings.mlr.press/v9/glorot10a.html
- He, K., Zhang, X., Ren, S., & Sun, J. (2015). Delving Deep into Rectifiers: Surpassing Human-Level Performance on ImageNet Classification. *arXiv:1502.01852*. https://arxiv.org/abs/1502.01852
- PyTorch 2.12 documentation: `torch.nn.init`. https://pytorch.org/docs/stable/nn.init.html
- PyTorch 2.12 documentation: `torch.nn.Linear` (default `reset_parameters`). https://pytorch.org/docs/stable/generated/torch.nn.Linear.html
- Dive into Deep Learning — Numerical Stability and Initialization: https://d2l.ai/chapter_multilayer-perceptrons/numerical-stability-and-init.html
- Stanford CS231n — Weight Initialization: https://cs231n.github.io/neural-networks-2/#init
- Goodfellow, I., Bengio, Y., & Courville, A. (2016). *Deep Learning*, §6.5–6.6. https://www.deeplearningbook.org/contents/mlp.html
- Mishkin, D., & Matas, J. (2016). All you need is a good init. *ICLR*. https://arxiv.org/abs/1511.07289
- Karpathy, A. (2022). "A Recipe for Training Neural Networks." http://karpathy.github.io/2019/04/25/recipe/
- Paszke, A., et al. (2019). PyTorch: An Imperative Style, High-Performance Deep Learning Library. *NeurIPS*. https://arxiv.org/abs/1912.01703

---

## Learner check

> | 1.3.1 | [Initialization & Signal Propagation](/ai-ml-engineering/deep-learning/module-1.3.1-initialization-signal-propagation/) |

---

## Next Module

Continue to [Optimizers & Learning-Rate Dynamics](/ai-ml-engineering/deep-learning/module-1.3.2-optimizers-lr-dynamics/) — where initialization meets the update rule, and you will learn why even perfectly scaled weights need momentum, adaptive learning rates, and warmup schedules to converge efficiently.
