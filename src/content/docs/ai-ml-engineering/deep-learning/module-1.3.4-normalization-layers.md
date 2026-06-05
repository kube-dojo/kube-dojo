---
title: "Normalization Layers"
slug: ai-ml-engineering/deep-learning/module-1.3.4-normalization-layers
sidebar:
  order: 1004.4
---

> **AI/ML Engineering Track** | Complexity: `[COMPLEX]` | Time: 4-5 hours
>
> **Prerequisites**: Module 1.3.1 (Weight Initialization — understanding activation and gradient variance across depth), Module 1.3.2 (Optimizers & LR Dynamics — how effective step size interacts with gradient scale), and Module 1.1.7 (Tiny NumPy NN Lab — you hand-wrote the training loop where activation statistics went unmonitored).
>
> **Primary tools**: PyTorch 2.12, `torch.nn.BatchNorm1d/2d`, `torch.nn.LayerNorm`, `torch.nn.RMSNorm`, `torch.nn.GroupNorm`.

---

In early 2015, Sergey Ioffe and Christian Szegedy posted a paper to arXiv titled "Batch Normalization: Accelerating Deep Network Training by Reducing Internal Covariate Shift." The paper was short — nine pages — and the core idea was startlingly simple: after every layer, re-standardize the activations to zero mean and unit variance using the statistics of the current mini-batch, then let the network learn an affine transformation (scale γ and shift β) on top of the normalized values. The authors reported that adding batch normalization to a then-standard Inception network allowed them to train the model 14 times faster, reach higher accuracy, and eliminate the need for dropout in many configurations. Within two years, BatchNorm was a default architectural component — not an optional trick or a hyperparameter to tune, but a layer you included in every convolutional block as routinely as a ReLU.

The story behind BatchNorm's invention speaks to a pain every practitioner has felt. Deep networks were finicky. Before BatchNorm, training a deep convolutional network meant weeks of tuning learning rates, monitoring gradient norms, and hoping the initialization was good enough to survive the first thousand steps. The problem was not that the theory was wrong — backpropagation had been known for decades, and the SGD update rule was correct — but that the interaction between weight updates and activation statistics was poorly understood. Every training step changed the weights, every weight change shifted the activation distribution at the next layer, and the downstream layers had to continuously re-adapt to a moving target. The deeper the network, the more layers there were to compound the drift, and the harder training became. BatchNorm's elegance was that it attacked the problem not at the optimizer or the architecture but at the activation itself: don't let the distribution drift in the first place.

Ioffe and Szegedy's hypothesis — that this drift, which they called "internal covariate shift," was the root cause of training instability — turned out to be partially wrong, and understanding why is essential to understanding what normalization layers actually do. Santurkar et al. (2018) designed an elegant experiment to test the internal-covariate-shift hypothesis directly. They trained networks with BatchNorm but injected explicit, time-varying noise (a random per-step shift and scale) after each BN layer, deliberately reintroducing — even amplifying — covariate shift throughout training. These "noisy-BN" networks trained essentially as well as standard BN networks, despite having large, unstable activation distributions. If internal covariate shift reduction were the mechanism by which BatchNorm accelerated training, this deliberate amplification of covariate shift should have harmed performance. It did not. The result is a knockout: BatchNorm helps training through a different mechanism entirely.

What Santurkar and colleagues found is that BatchNorm smooths the loss landscape. More precisely, the gradient of the loss with respect to the parameters has a smaller Lipschitz constant in BatchNorm-trained networks — the gradient changes less abruptly as you move through parameter space. A smoother landscape means that (a) the gradient at your current position is a better predictor of the gradient a step ahead, so larger learning rates are safer; (b) the loss is less sensitive to small parameter perturbations, improving generalization; and (c) the optimizer is less likely to get stuck in sharp minima that correspond to poor generalization performance on unseen data. The practical takeaway is important enough to restate: normalization layers do not work by keeping input distributions fixed. They work by reparameterizing the optimization problem in a way that makes gradient descent more effective. This is a more nuanced claim than the original paper's framing, and it explains a puzzle the original theory could not resolve — namely, why normalization helps even in shallow three-layer networks where internal covariate shift is negligible.

The normalization family has grown well beyond BatchNorm. Layer Normalization (Ba et al., 2016) normalizes across features per sample, making it batch-independent and the natural choice for recurrent networks and Transformers where batch composition and sequence length are variable. RMSNorm (Zhang & Sennrich, 2019) drops the mean-centering step from LayerNorm entirely, normalizing by root-mean-square only — the cheaper operation that modern LLMs like LLaMA and Mistral now use at every attention and feed-forward sub-layer. Group Normalization (Wu & He, 2018) divides channels into groups and normalizes within each group, providing batch-independent normalization for vision tasks where GPU memory constraints force batch sizes of 2 or 4 — object detection on high-resolution images, medical image segmentation, video understanding. InstanceNorm, the extreme case of GroupNorm with one group per channel, is the normalizer at the heart of neural style transfer.

In Module 1.3.1 you learned that weight initialization sets the *starting* activation scale so that the network is trainable at step zero. Normalization layers are the mechanism that *maintains* trainable activation scale as training proceeds. Where initialization is the first engineering decision — applied once, at network creation — normalization is the ongoing decision, re-applied every forward pass, and its correct configuration determines whether the optimizer's carefully chosen hyperparameters remain valid throughout training. Misconfiguring normalization — using batch statistics in evaluation mode, normalizing over the wrong axis, forgetting the mode toggle — produces silent correctness bugs that degrade deployed accuracy by 1-5% without ever raising an error, raising a NaN, or crashing the process. This module teaches you the exact computation inside every normalization layer, the train-vs-eval behavior that distinguishes them, and how to choose one for a given architecture.

---

## Learning Outcomes

By the end of this module, you will be able to:

1. **Implement** BatchNorm's forward pass — including the running-mean update rule `running = (1−momentum)·running + momentum·batch_stat` and the train-vs-eval statistics switch — in both raw PyTorch tensor operations and the `nn.BatchNorm` API, and **verify** that a normalized feature channel has mean ≈ 0 and std ≈ 1.

2. **Derive** the normalized axes for BatchNorm (batch + spatial), LayerNorm (feature), RMSNorm (feature, no mean subtraction), and GroupNorm (grouped channels), and **predict** which normalizers are batch-dependent versus batch-independent from their normalization axes alone.

3. **Diagnose** the small-batch BatchNorm failure mode — noisy μ and σ estimates producing inaccurate training-time normalization and drift between training and inference statistics — and **select** GroupNorm or LayerNorm as the appropriate replacement when batch sizes fall below 8.

4. **Compare** the empirical effect of BatchNorm against Santurkar et al.'s loss-smoothing hypothesis and **select** the appropriate normalizer for a given architecture: BatchNorm for large-batch vision CNNs, LayerNorm for Transformers and sequence models, RMSNorm for modern LLMs, GroupNorm for small-batch vision, and InstanceNorm for style transfer.

5. **Place** a normalization layer correctly in a residual block — pre-norm vs post-norm — and **explain** why pre-norm training is more stable at initialization, permitting deeper networks to train without specialized warmup schedules.

---

## Why This Module Matters

Consider a fifty-layer convolutional network trained with perfectly tuned He initialization (Module 1.3.1), AdamW (Module 1.3.2), and a well-chosen cosine learning-rate schedule. Step zero: every activation has standard deviation near 1.0, gradients flow cleanly, the optimizer's adaptive buffers see well-scaled signals. Now take one optimizer step. The weights change. The activation distribution at layer 25 shifts — not dramatically, but the mean might drift from 0.02 to 0.07, the standard deviation from 1.0 to 1.3. Another hundred steps: the shift compounds. By step 1,000, the optimizer is receiving gradients whose scale, direction, and conditioning are all different from what the initialization promised. The loss landscape your learning-rate schedule was designed around has deformed.

This drift is not a bug. It is a mathematical inevitability of updating weights in a composition of nonlinear functions. Every weight matrix in every layer participates in a forward computation that multiplies its input by the weight values; when those values change, the output distribution changes, and lower layers experience the cumulative effect of all upstream changes. The only question is how you respond to the drift. Without normalization, you respond by lowering the learning rate — giving the optimizer smaller, more cautious steps to avoid the worst consequences of a shifting landscape, paying for stability with wall-clock time and sometimes with final accuracy because the optimizer cannot explore the parameter space aggressively enough. With normalization, you respond by re-standardizing activations at every layer, keeping the signal in roughly the same range throughout training so that the optimizer's carefully chosen hyperparameters remain valid from step 1 to step 100,000.

The back-reference thread from this module to the Block A from-scratch material is direct and concrete. In Module 1.1.6 you derived backpropagation VJPs by hand: `dL/dx = dL/dy · W^T`, and you traced how gradient magnitude compounds across layers exactly like activation magnitude compounds in the forward pass. In Module 1.1.7 you trained a tiny three-layer MLP and updated weights with the manual rule `W -= lr * dW` — a training loop that implicitly relied on activations staying roughly unit-scale through a shallow network where drift was negligible because there were only two weight matrices to compound errors through. In Module 1.1.8 you built a scalar autograd engine (the `Value` class) that computed gradients through arbitrary computation graphs by traversing backward through every operation, including element-wise transforms. Normalization layers are the engineering solution to the problem you didn't have at depth 3 but that becomes dominant at depth 30 and 50 and 100: the multiplication of many layers amplifying small distribution shifts into large, training-destabilizing changes. When you call `loss.backward()` in PyTorch and the autograd engine traces through a normalization layer, it computes exactly the VJP of the normalization operation `y = (x − μ)/σ · γ + β` — the same kind of VJP you derived by hand in A6, node by node, but now applied to a multi-input operation where the statistics μ and σ are themselves functions of the batch. The engine is doing what you did on paper, and if you understand the VJP structure you can predict how gradient flow through a normalization layer differs from gradient flow through a bare linear layer.

The train-vs-eval behavior of BatchNorm is the single most common source of silent accuracy bugs in production deep learning. A model trained with `model.train()` and deployed with `model.eval()` uses different statistics — in training, the per-batch mean and variance; in evaluation, the frozen running-mean and running-variance buffers accumulated during training. If you forget the mode toggle, or if your inference framework (ONNX, TensorRT, CoreML, a handwritten C++ inference loop) doesn't faithfully reproduce the PyTorch BatchNorm eval-mode computation, the deployed model normalizes with the wrong statistics. The outputs look reasonable — no NaN, no crash, no obviously wrong prediction — but systematically differ from the training-time behavior, degrading accuracy by 1-5% in production. This bug survives basic smoke tests, passes unit tests that compare single-sample outputs across frameworks, and only surfaces when someone computes aggregate metrics over a real test set and notices the degradation. This module teaches you not just the "what" but the "how to verify" — the ten-line probe you can run before deploying any model to confirm that your normalization layers are using the statistics you think they are using.

There is also a subtler reason this module matters: normalization layers are not optional polish or a hyperparameter to try if training is unstable. They are architectural decisions that interact with every other component of the training pipeline. The choice of BatchNorm versus LayerNorm determines whether your model's predictions depend on batch composition. The choice of pre-norm versus post-norm placement in residual blocks determines whether your hundred-layer Transformer can train without a 10,000-step warmup schedule. The `momentum` parameter in BatchNorm — a number whose default value of 0.1 is rarely changed — determines how many batches of history inform the running statistics and therefore how long you must train before the running statistics stabilize. A practitioner who treats normalization as a black-box layer that "just works" will eventually encounter a regime — small batch size, variable-length sequences, distributed training across unevenly loaded GPUs — where the black box stops working and the training loss curve becomes inexplicable. This module gives you the mental model to open the box and fix it.

---

## Part 1: Why Normalize — Activation Statistics Drift, Measured

Before introducing any normalization layer, run the experiment that forces you to see the problem. The goal is to measure activation statistics in a deep network, take one training step, and observe that even with perfect He initialization the activation distribution shifts measurably. The shift is small after one step — but training involves thousands of steps, and the small per-step drift compounds.

### 1.1 Drift after one update

The experiment is straightforward: build a depth-30 MLP with He initialization (the best practice from Module 1.3.1), pass a batch of random inputs through it, record the per-layer activation standard deviations, then run one SGD step with a dummy loss and measure again. The numbers you see depend on the random seed and the specific architecture, but the pattern is consistent: deeper layers drift more because they accumulate the effect of weight changes in all preceding layers.

```python
import torch
import torch.nn as nn

torch.manual_seed(42)
depth, width = 30, 256
batch = 128

# Build a deep ReLU MLP with He init
layers = []
for i in range(depth):
    lin = nn.Linear(width, width)
    nn.init.kaiming_normal_(lin.weight, nonlinearity='relu')
    nn.init.zeros_(lin.bias)
    layers.append(lin)
    layers.append(nn.ReLU())

model = nn.Sequential(*layers)
model.train()

x = torch.randn(batch, width)

# Measure activation stds (no autograd needed)
with torch.no_grad():
    h = x
    pre_update_stds = []
    for name, module in model.named_children():
        h = module(h)
        if isinstance(module, nn.ReLU):
            pre_update_stds.append(h.std().item())
    print(f"Before training — layer 1 std: {pre_update_stds[0]:.3f}, "
          f"layer 15 std: {pre_update_stds[14]:.3f}, "
          f"layer 30 std: {pre_update_stds[-1]:.3f}")

# One real training step: a FRESH forward WITH autograd, then backward
optimizer = torch.optim.SGD(model.parameters(), lr=1e-4)
optimizer.zero_grad(set_to_none=True)
out = model(x)                 # fresh forward, grad enabled
loss = out.mean()              # bounded dummy objective for demonstration
loss.backward()
optimizer.step()

# Record activation stds AFTER one update, same input
with torch.no_grad():
    h = x
    post_update_stds = []
    for name, module in model.named_children():
        h = module(h)
        if isinstance(module, nn.ReLU):
            post_update_stds.append(h.std().item())
    print(f"After 1 SGD step  — layer 1 std: {post_update_stds[0]:.3f}, "
          f"layer 15 std: {post_update_stds[14]:.3f}, "
          f"layer 30 std: {post_update_stds[-1]:.3f}")
```

Even with He initialization, the standard deviation at the deepest layers shifts after a single SGD step — with seed 42 and the code above, layer 15 moves from 0.757 to 0.755 and layer 30 from 1.292 to 1.279, though the exact before/after pair depends on the random seed and the specific pattern of weight updates. The direction of the shift is not the point; what matters is that it happens at all, and that it compounds. With a bounded mean loss and a learning rate of 1e-4 the one-step shift is modest, but training for 10,000 steps at this learning rate means 10,000 opportunities for the distribution to drift further, and the optimizer must navigate a loss surface whose geometry changes as the weight values change.

### 1.2 The original hypothesis (and why it's incomplete)

Ioffe and Szegedy (2015) framed the problem they were solving as "internal covariate shift": the distribution of each layer's inputs changes during training because the parameters of all preceding layers change. Their proposed fix — re-standardize layer inputs to zero mean and unit variance, then let the network learn an affine transformation on top — made intuitive sense. A layer trained to expect inputs with mean zero and variance one would not need to waste capacity adapting to shifting input statistics. The normalization decoupled the layers: each layer could assume stable input statistics regardless of what the preceding layers were doing.

This framing is elegant and was widely cited for years. It is also, as Santurkar et al. demonstrated, not the mechanism by which BatchNorm actually helps. The Santurkar experiment was devilishly simple: they trained networks with BatchNorm but injected explicit, time-varying noise (a random per-step shift and scale) after each BN layer, deliberately reintroducing — even amplifying — covariate shift throughout training. These "noisy-BN" networks trained essentially as well as standard BN networks, despite having large, unstable activation distributions. If internal covariate shift reduction were the mechanism, this deliberate amplification of covariate shift should harm performance. It did not.

The mechanism Santurkar identified is loss-landscape smoothing. BatchNorm reparameterizes the optimization so that the loss function L(θ) has a smaller Lipschitz constant with respect to the weights θ — meaning that ‖∇L(θ₁) − ∇L(θ₂)‖ ≤ C · ‖θ₁ − θ₂‖ with a smaller constant C. A smaller Lipschitz constant means the gradient is a more reliable direction signal: the first-order Taylor approximation ∇L(θ)·Δθ is accurate over larger steps Δθ, so you can increase the learning rate without risking the instability that occurs when you step past the radius where the linear approximation holds. Empirically, networks with BatchNorm tolerate learning rates 5× to 30× higher than networks without it, directly because the smoother landscape makes gradient descent's local-linearity assumption valid over longer distances.

The practical insight is worth internalizing: normalization layers are not primarily about fixing activation distributions. They are about making the optimization problem numerically better-conditioned. This is why normalization helps even in shallow networks (where internal covariate shift is minimal), why it helps with optimizers like Adam that already adapt per-parameter step sizes, and why the specific form of normalization matters less than you might think — LayerNorm, RMSNorm, and GroupNorm all provide loss-landscape smoothing through different axes, and the differences between them are more about batch-dependence and computational cost than about fundamentally different mechanisms.

### 1.3 The back-reference: why init alone is not enough

Module 1.3.1 taught you that initialization sets `Var(W) = 2/n_in` (He) or `Var(W) = 2/(n_in + n_out)` (Xavier) so that the activation standard deviation stays near 1.0 *at step zero*. That analysis assumed the weights are random and independent — an assumption that holds exactly before the first gradient step and becomes increasingly wrong as training proceeds. Once training begins, weights within the same layer become correlated with each other, weights across layers become correlated through the gradient signal, and the simple variance-propagation formula `Var(out) = n_in · Var(W) · Var(in)` derived under the independence assumption no longer accurately predicts the activation scale.

You can initialize perfectly and still watch activation statistics drift by step 1,000. The initialization fixes the problem at t=0; normalization fixes it at every t > 0. Normalization layers can be thought of as "continuous re-initialization" — after every layer, after every batch, they pull activations back toward zero mean and unit variance regardless of what the preceding weights are doing. This redundancy with initialization is not wasteful. It is the engineering principle of defense in depth: initialization gives you a good starting point, and normalization keeps you there throughout training. The combination of good initialization and normalization is more robust than either alone because each addresses a different time scale of the drift problem — static vs dynamic, step zero vs all steps.

---

## Part 2: Batch Normalization

### 2.1 The exact computation

For a mini-batch of size `m`, consider a single feature channel. Let the values of that feature across the batch be `x₁, x₂, ..., xₘ`. For `BatchNorm1d`, these are the `m` values of one feature across the batch. For `BatchNorm2d`, these are the `m × H × W` activations of one channel — the normalization pools over batch and spatial dimensions together. BatchNorm computes four quantities in sequence:

```
μ_B = (1/m) · Σ x_i                       ← batch mean
σ²_B = (1/m) · Σ (x_i − μ_B)²            ← batch variance (biased estimator)
x̂_i = (x_i − μ_B) / √(σ²_B + ε)          ← normalize
y_i = γ · x̂_i + β                          ← scale and shift
```

The learnable parameters γ (gamma, scale) and β (beta, shift) are one pair per feature channel. The constant ε is small — PyTorch defaults to `1e-5` — and exists solely to prevent division by zero when the batch variance is exactly zero (which can happen when a feature is constant across the batch, e.g., for dead ReLU units that output zero for every sample). The affine transformation by γ and β is not optional: without it, every layer's output would be forced to exactly zero mean and unit variance, stripping the network of the ability to represent transformations that change the scale or shift the mean. The learnable affine parameters restore the representational capacity that the normalization step removes, and the network learns, per channel, the optimal scale and shift for the downstream computation.

### 2.2 The PyTorch equivalent, built by hand

To make every step of the operation concrete, here is a manual implementation that produces identical results to `nn.BatchNorm1d` (up to floating-point precision). The key detail is the `dim=0` argument on `.mean()` and `.var()`: normalizing over the batch dimension means every feature channel gets its own μ and σ² computed from the batch samples alone, and no information crosses between feature channels during normalization.

```python
import torch
import torch.nn as nn

torch.manual_seed(0)
batch, features = 32, 16
x = torch.randn(batch, features)  # (32, 16)

# Manual BatchNorm1d — step by step
eps = 1e-5
mu = x.mean(dim=0, keepdim=True)         # (1, 16) — mean over batch dimension
var = x.var(dim=0, unbiased=False, keepdim=True)  # (1, 16) — biased variance
x_hat = (x - mu) / torch.sqrt(var + eps) # (32, 16)

gamma = nn.Parameter(torch.ones(features))
beta  = nn.Parameter(torch.zeros(features))
y_manual = gamma * x_hat + beta           # (32, 16)

# PyTorch built-in — configure to always use batch stats for comparison
bn = nn.BatchNorm1d(features, eps=eps, affine=True,
                    momentum=None, track_running_stats=False)
# momentum=None + track_running_stats=False: always batch stats, no buffers
bn.weight.data.copy_(gamma)
bn.bias.data.copy_(beta)

y_pytorch = bn(x)

print(f"Max difference: {(y_manual - y_pytorch).abs().max().item():.2e}")
# Expected: ~1e-7 or smaller

# Verify normalization: each feature should have ~0 mean, ~1 std
# (before the affine transform, with γ=1 and β=0, these are exact)
print(f"Feature 0 mean: {y_manual[:, 0].mean().item():.4f}")
print(f"Feature 0 std:  {y_manual[:, 0].std(unbiased=False).item():.4f}")
# With initial γ=1, β=0: mean ≈ 0.0, std ≈ 1.0
```

For `BatchNorm2d`, the normalization pools over three dimensions — batch, height, and width — for each channel independently. The effective sample size for the statistics is `N × H × W` per channel. With batch=32 and spatial size 28×28, that is 25,088 values per channel, giving very stable estimates of μ and σ² even if the per-channel distribution is non-Gaussian. This is why BatchNorm works so well at large batch sizes: the statistics are computed from tens of thousands of values and the sampling error is negligible.

### 2.3 Train vs eval: the statistics switch

The single most important behavioral detail in BatchNorm — and the source of more silent production bugs than any other normalization feature — is that it behaves differently in `.train()` and `.eval()` modes. The difference is not cosmetic; it is a fundamental design choice about which statistics to use for normalization.

In **training mode** (`.train()`), BatchNorm computes μ_B and σ²_B from the current mini-batch, normalizes using those batch statistics, and simultaneously updates two persistent buffers — `running_mean` and `running_var` — using an exponential moving average:

```
running_mean = (1 − momentum) · running_mean + momentum · μ_B
running_var  = (1 − momentum) · running_var  + momentum · σ²_B,unbiased
```

The σ²_B written into `running_var` is the **unbiased** batch variance (divide by m−1), not the biased estimator used for normalization.

PyTorch's default `momentum=0.1` means each batch contributes 10% to the running estimate, and the effective memory of the running average — the number of batches it takes for a given batch's contribution to decay below 1% — is roughly `ln(0.01) / ln(1 − momentum)` ≈ 44 batches. After training, the running buffers approximate the population statistics of the training data distribution, weighted toward more recent batches.

In **evaluation mode** (`.eval()`), BatchNorm uses the frozen `running_mean` and `running_var` — no batch statistics are computed, and the running buffers are not updated. The `momentum` parameter is irrelevant. The output for a given input is deterministic (independent of other samples in the batch) and approximates what the model would produce if the batch statistics were averaged over the entire training set.

The **biased** variance estimator `σ²_B = Σ(x−μ)²/m` (dividing by m) is used to **normalize** the current batch, but the value written into the `running_var` buffer is the **unbiased** estimator `Σ(x−μ)²/(m−1)` — PyTorch applies Bessel's correction to the stored running variance, equivalent to `torch.var(unbiased=True)`, while normalization uses `torch.var(unbiased=False)`. (Ref: PyTorch `nn.BatchNorm1d` docs.) PyTorch's convention for the running-average update is `running = (1−momentum)·running + momentum·batch`. Other frameworks — notably TensorFlow and Keras — historically used the reverse convention `running = momentum·running + (1−momentum)·batch`, which means a PyTorch `momentum=0.1` corresponds to a TensorFlow `momentum=0.9`. When porting models between frameworks, this convention difference is a reliable source of subtle accuracy mismatches that are difficult to trace because both numbers look reasonable in isolation.

### 2.4 The running-buffer probe

The best way to trust that the buffers are doing what you expect is to print them, update them, and print again. The following probe shows the running statistics initialized to their defaults (mean=0, var=1), updated by two batches from different distributions, and then frozen during evaluation:

```python
import torch
import torch.nn as nn

torch.manual_seed(42)
bn = nn.BatchNorm1d(4, momentum=0.1, track_running_stats=True)
bn.train()

# Before any forward pass, running_mean is initialized to 0, running_var to 1
print(f"Initial running_mean: {bn.running_mean}")
print(f"Initial running_var:  {bn.running_var}")

x1 = torch.randn(8, 4)  # batch=8, features=4 — standard normal distribution
_ = bn(x1)
print(f"\nAfter batch 1 — running_mean: {bn.running_mean}")
# Each entry is 0.1 * batch_mean + 0.9 * 0 = 0.1 * batch_mean
# Since x1 is N(0,1), batch_mean ≈ 0, so running_mean stays near 0

x2 = torch.randn(8, 4) * 2 + 5  # deliberately shifted: mean ≈ 5, std ≈ 2
_ = bn(x2)
print(f"After batch 2 — running_mean: {bn.running_mean}")
# Now: 0.1 * batch2_mean + 0.9 * (0.1 * batch1_mean)
# ≈ 0.1 * 5.0 + 0.9 * 0.0 ≈ 0.5 for each feature

# Switch to eval — the running buffers are frozen
bn.eval()
x3 = torch.randn(8, 4)
y3 = bn(x3)
print(f"\nEval mode — norm uses running stats, not batch stats")
print(f"running_mean: {bn.running_mean}")
print(f"batch3 mean:   {x3.mean(dim=0)}")
# These will differ; y3 uses running_mean, not batch3's mean

# Verify: in eval mode, repeated forward passes with same input are identical
y3_again = bn(x3)
print(f"Eval output stable: {(y3 - y3_again).abs().max().item():.2e}")
# Expected: 0.0 — running buffers don't change during eval
```

The probe reveals an important detail about the running-statistics lifecycle: the running buffers are updated during `.train()` forward passes only — not during `.backward()` and not during `.eval()`. If your training loop calls `.backward()` without a preceding `.forward()` (unusual but possible in custom training setups), the running statistics will not be updated for that step, and the accumulated population estimates will be biased.

### 2.5 The small-batch problem

BatchNorm's defining characteristic — normalizing using batch statistics — is also its Achilles' heel. When the batch size is small, the batch statistics μ_B and σ²_B are noisy estimators of the population statistics. A batch of 2 samples produces a mean estimate whose variance is σ²/2 (where σ² is the true population variance), and a variance estimate that is even noisier. The noise has two distinct consequences, both harmful at very small batch sizes.

First, **training instability**: each forward pass normalizes with a different, inaccurate μ/σ pair. The noise injected into the activations by these fluctuating statistics depends on the specific samples in the batch, not on any learnable parameter, and the gradient signal is therefore corrupted by normalization noise that the optimizer cannot reduce by updating weights. At batch size 8 or above, this noise is modest and can even act as a beneficial regularizer — Ioffe and Szegedy observed that BatchNorm allowed them to remove dropout from their networks, because the stochasticity in the batch statistics provided enough regularization. At batch size 2 or 4, the noise is large enough to dominate the gradient signal, and training loss becomes erratic or diverges.

Second, **train-inference mismatch**: the running statistics stored during training are a moving average of noisy batch estimates. With batch size 2, even after 100,000 updates, the running mean has not converged to the true population mean — its variance is reduced by the momentum averaging (effective window ~44 batches) but not eliminated because each batch estimate is itself extremely noisy. When you switch to eval mode and use these unconverged running statistics for inference, the normalization is systematically wrong, and the model's predictions on the same input differ from what they would have been with accurate population statistics.

The practical rule of thumb: BatchNorm needs a batch size of at least 16 for reliable statistics. At batch size 8, the performance degradation is often measurable but small (0.5-1% accuracy). At batch size 4, the degradation is significant. At batch size 2, BatchNorm is essentially broken — use GroupNorm for vision or LayerNorm for sequences. The coupling effect is also worth noting: because BatchNorm normalizes using batch statistics, the prediction for sample `i` depends on which other samples happen to be in the same batch. This dependence is why `SyncBatchNorm` exists — in distributed training, each GPU computes its own batch statistics from its local batch, and without synchronization, the effective batch for statistics is the per-GPU batch, not the global batch.

---

## Part 3: Layer Normalization

### 3.1 Normalize over features, not over the batch

Layer Normalization (Ba et al., 2016) takes the opposite approach from BatchNorm: instead of normalizing each feature across the batch, it normalizes across features for each individual sample. For an input vector `x ∈ R^H` (a single sample with H features), the computation is structurally identical to BatchNorm but with the reduction axis reversed:

```
μ = (1/H) · Σ_{j=1}^{H} x_j              ← per-sample mean (over features)
σ² = (1/H) · Σ_{j=1}^{H} (x_j − μ)²      ← per-sample variance
x̂_j = (x_j − μ) / √(σ² + ε)              ← normalize
y_j = γ_j · x̂_j + β_j                       ← scale and shift (per-feature γ, β)
```

The critical difference from BatchNorm: the statistics μ and σ² are computed from the features of a *single sample*. There is no batch dependence, no concept of population versus batch statistics, no running buffer to maintain, and — most importantly for deployment — no difference in behavior between `model.train()` and `model.eval()`. A LayerNorm layer produces identical outputs in both modes, given the same input, regardless of batch size or batch composition. The mode independence eliminates an entire class of production bugs that BatchNorm introduces.

The learnable parameters γ and β are per-feature (one pair for each of the H features), giving the network the ability to rescale and shift each feature dimension independently after normalization. This is the same affine mechanism as BatchNorm; the difference is only in which axis the normalization is applied to.

### 3.2 Shape conventions in PyTorch

`nn.LayerNorm(normalized_shape)` normalizes over the last `len(normalized_shape)` dimensions of the input. The most common patterns in practice:

```python
# Input shape (batch, features) — standard for MLPs
ln = nn.LayerNorm(256)           # normalized_shape = 256 (a single int)
x = torch.randn(32, 256)
y = ln(x)                        # normalizes over dim=-1 (the 256 features)

# Input shape (batch, seq_len, d_model) — standard for Transformers
ln = nn.LayerNorm(512)           # normalized_shape = 512
x = torch.randn(32, 100, 512)   # batch=32, seq_len=100, d_model=512
y = ln(x)                        # normalizes over the last dim (512) per token
# Each of the 32*100 = 3200 tokens is normalized independently

# Input shape (batch, C, H, W) — LayerNorm in vision (less common)
ln = nn.LayerNorm([64, 32, 32]) # normalized_shape is a list of 3 dims
x = torch.randn(8, 64, 32, 32)
y = ln(x)                        # normalizes over dims [-3, -2, -1] → C*H*W
# Each sample's (64, 32, 32) tensor is normalized as one 65,536-element vector
```

### 3.3 Why Transformers use LayerNorm

The Transformer architecture, introduced by Vaswani et al. (2017), processes variable-length sequences of tokens. Each token position is represented by a `d_model`-dimensional vector, and the self-attention and feed-forward operations are applied independently to each token position — the model is position-wise in its computation except for the attention mechanism, which mixes information across positions. Using BatchNorm in a Transformer would create several problems simultaneously.

The most immediate problem is padding. Sequences in a batch rarely have the same length; shorter sequences are padded with a special padding token to match the length of the longest sequence. If BatchNorm were applied, the padding tokens' features would contribute to μ_B and σ²_B, distorting the statistics for real tokens. A sequence with 10 real tokens and 90 padding tokens would be normalized using statistics dominated by the padding distribution, which is not representative of the real data.

The second problem is batch dependence. A Transformer processes variable-length sequences, and the batch composition can change dramatically from step to step — one batch might contain short sentences averaging 15 tokens, while the next contains long paragraphs averaging 200 tokens. BatchNorm's running statistics, updated at each step, would need to track statistics across this heterogeneous population, and the statistics for a given feature would represent an average over all sequence lengths, which may not be meaningful.

LayerNorm solves both problems by normalizing per token, per feature dimension. Each token is normalized using only its own feature values — no cross-token interaction, no cross-batch dependence. A padding token is normalized using its own features and remains a padding token; it does not affect the normalization of real tokens. The batch composition and sequence length are irrelevant to the normalization computation. And because there is no train/eval distinction, the inference behavior is deterministic given the input regardless of batch size — including batch size 1, which is common in online serving.

### 3.4 Manual verification

You can verify the computation by replicating LayerNorm manually and comparing with the PyTorch implementation. The key is to normalize over `dim=-1` (the last dimension) and use the biased variance estimator:

```python
import torch
import torch.nn as nn

torch.manual_seed(0)
batch, features = 4, 8
x = torch.randn(batch, features)

# Manual LayerNorm — normalize over the last dimension
eps = 1e-5
mu = x.mean(dim=-1, keepdim=True)              # (4, 1) — per-sample mean
var = x.var(dim=-1, unbiased=False, keepdim=True)  # (4, 1) — biased variance
x_hat = (x - mu) / torch.sqrt(var + eps)       # (4, 8)

ln = nn.LayerNorm(features, eps=eps)
y_pytorch = ln(x)

print(f"Max difference: {(x_hat - y_pytorch).abs().max().item():.2e}")
# Before learnable affine, ln(x) ≈ x_hat — difference ~1e-7

# Verify per-sample statistics: each row should have ~0 mean, ~1 std
print(f"Row 0 mean: {x_hat[0].mean().item():.4f}")
print(f"Row 0 std:  {x_hat[0].std(unbiased=False).item():.4f}")
# Without affine transform, these are exactly 0.0 and 1.0

# Train vs eval: LayerNorm is mode-independent
ln.eval()
y_eval = ln(x)
ln.train()
y_train = ln(x)
print(f"Train vs eval diff: {(y_train - y_eval).abs().max().item():.2e}")
# Always 0.0 — LayerNorm has no mode-dependent behavior
```

The train/eval equivalence is the property that makes LayerNorm the safe default for any architecture where batch dependence is undesirable. It eliminates the need for running-statistics management, mode-toggle discipline, and population-statistic convergence checks that BatchNorm requires.

---

## Part 4: RMSNorm — Drop the Mean, Keep the Scale

### 4.1 The formula

RMSNorm (Zhang & Sennrich, 2019) simplifies LayerNorm by removing the mean-centering step. For an input vector `x ∈ R^H`, the computation reduces to two operations: compute the root-mean-square of the features, and divide each feature by that value.

```
RMS(x) = √( (1/H) · Σ_{j=1}^{H} x_j² + ε )
x̂_j = x_j / RMS(x)
y_j = γ_j · x̂_j
```

There is no bias term β, no mean subtraction, and only a learnable gain parameter γ (one per feature). The normalization preserves the sign of every feature and the relative magnitudes between features, while constraining the root-mean-square of the feature vector to approximately 1 (before the learned gain). This is a more minimal operation than LayerNorm: instead of forcing the distribution to zero mean and unit variance, it forces only the scale (RMS) to unity and leaves the mean whatever it naturally is.

The absence of the bias term β follows from a deeper design choice. Zhang & Sennrich (2019) argue that LayerNorm's **re-centering** (mean subtraction) is dispensable — the **re-scaling** invariance is what matters for optimization — so RMSNorm drops mean-centering and the bias term, reporting **7%–64% per-layer runtime reductions** while matching LayerNorm accuracy. Mean-centering ensures that the normalized features are centered at zero, which symmetrizes the distribution around the origin and may help with activation functions like GELU that behave differently in negative and positive regimes. But the experimental evidence from large-scale language modeling suggests that this symmetry is not necessary — the RMS-constraint alone is sufficient to keep the optimization well-conditioned, and the saved computation (one fewer reduction per normalization) more than justifies the simplification at the scale of billion-parameter models trained on trillion-token corpora.

### 4.2 Why modern LLMs prefer RMSNorm

The computational saving from omitting mean subtraction is modest but real: LayerNorm requires two reduction operations per normalization (sum for mean, sum of squares for variance), while RMSNorm requires only one (sum of squares for RMS). In a large Transformer, normalization is applied after every attention block and every feed-forward block — for an 80-layer model, that is 160 normalization operations per token per forward pass. Dropping half the reduction operations saves roughly 10-15% of the normalization compute, which at the scale of a trillion-token pretraining run translates to non-trivial wall-clock savings measured in GPU-hours.

Empirically, RMSNorm performs comparably to LayerNorm on language modeling benchmarks. The LLaMA family (Touvron et al., 2023), Mistral (Jiang et al., 2023), and many subsequent open-weight LLMs use RMSNorm as their primary normalization layer, applied before the attention and feed-forward sub-layers in a pre-norm configuration. The success of these models at scales from 7B to 405B parameters demonstrates that the mean-centering step — the step that LayerNorm adds beyond RMSNorm — is not necessary for effective training at scale. The normalization landscape has effectively bifurcated: RMSNorm for large language models, LayerNorm for the original Transformer and most non-LLM sequence architectures.

The architectural pattern is a literal swap: where a standard Transformer has `nn.LayerNorm(d_model)`, an RMSNorm-based architecture has `nn.RMSNorm(d_model)`. The interface is **nearly** identical — both take `normalized_shape` and `eps` — though in PyTorch 2.12 `nn.RMSNorm` has no `bias`, its `eps` defaults to `None`, and `nn.LayerNorm` exposes `elementwise_affine=True, bias=True`. The position in the network is the same (pre-norm, before the sub-layer).

### 4.3 PyTorch code

`nn.RMSNorm` is available in PyTorch 2.12 as a stable API:

```python
import torch
import torch.nn as nn

batch, seq_len, d_model = 2, 16, 512
x = torch.randn(batch, seq_len, d_model)

rms = nn.RMSNorm(d_model, eps=1e-5)
rms.eval()  # RMSNorm is mode-independent (like LayerNorm)
y = rms(x)  # (2, 16, 512) — normalized over last dim per token

# Manual verification
eps = 1e-5
rms_manual = torch.sqrt((x ** 2).mean(dim=-1, keepdim=True) + eps)
x_hat_manual = x / rms_manual
print(f"Max diff (manual vs PyTorch): {(x_hat_manual - y).abs().max().item():.2e}")
# ~1e-7 — identical up to floating-point precision before learned gain

# Per-token RMS after normalization (before gain, γ=1)
rms_per_token = torch.sqrt((y ** 2).mean(dim=-1))
print(f"RMS per token (first 3 tokens): {rms_per_token[0, :3]}")
# Each element ≈ 1.0 — the RMS constraint is satisfied
```

---

## Part 5: Group Normalization

### 5.1 Batch-independent normalization for vision

Group Normalization (Wu & He, 2018) was designed to solve a specific, practical problem: modern vision tasks — object detection, instance segmentation, video understanding, high-resolution medical imaging — require large input resolutions that force small per-GPU batch sizes, often 2 or 4. BatchNorm degrades badly at these batch sizes, as discussed in Section 2.5. LayerNorm, applied over all channels and spatial dimensions, is too aggressive for vision: normalizing all 64 or 128 or 256 channels of a feature map as a single distribution washes out the channel-wise structure that the convolutional filters have learned. GroupNorm steers a middle course.

Instead of normalizing over the batch (like BN) or over all channels (like LN), GroupNorm divides the C channels into G groups of C/G channels each and normalizes within each group independently. For a single sample with shape `(C, H, W)`, each group computes its mean and variance over the `(C/G) × H × W` values belonging to that group and normalizes those values. The normalization is per-sample (no batch dependence) and per-group (not per-channel, not all-channel), giving GroupNorm two advantages:

The first advantage is **batch-size independence**: the statistics are computed from a single sample's features, so batch size 2 produces exactly the same per-sample normalization quality as batch size 256. There is no running buffer, no train/eval distinction, and no population-statistic convergence to worry about. The second advantage is **channel-group expressivity**: because normalization happens within groups and not across all channels, different groups of channels can have different means and variances. A feature map where channels 0-15 represent edge detectors and channels 48-63 represent color blobs will have those two groups normalized independently, preserving their distinct statistical properties.

### 5.2 The API

`nn.GroupNorm(num_groups, num_channels)` requires that `num_channels` is divisible by `num_groups`. The standard pattern is to choose `num_groups` as a small divisor of the channel count — typically 32 for networks with 64+ channels, or 8-16 for shallower networks.

```python
import torch
import torch.nn as nn

# 64 channels, 4 groups → each group normalizes 16 channels
gn = nn.GroupNorm(num_groups=4, num_channels=64)

x = torch.randn(8, 64, 32, 32)  # (N, C, H, W) — batch of 8
y = gn(x)                         # (8, 64, 32, 32) — same shape

# Special cases that illustrate the design space:
# num_groups=1 → equivalent to LayerNorm over (C, H, W) per sample
# num_groups=num_channels → InstanceNorm (one group per channel)
```

The special cases are instructive. At `num_groups=1`, GroupNorm normalizes all channels as a single group — this is functionally equivalent to applying LayerNorm over the `(C, H, W)` dimensions per sample. At `num_groups=C` (one group per channel), GroupNorm normalizes each channel independently over its `H × W` spatial dimensions — this is InstanceNorm, the normalization used in neural style transfer to separate content (spatial structure) from style (channel-wise mean and variance).

### 5.3 When to use GroupNorm

The paper's experimental results are decisive. On ImageNet classification with a ResNet-50, GroupNorm with batch size 2 achieves 75.9% top-1 accuracy, only 0.5% below BatchNorm at batch size 256 (76.4%). At batch size 2, BatchNorm's error rises to 34.7% (≈65.3% top-1 accuracy) while GroupNorm holds at 24.1% error (≈75.9% accuracy) — a 10.6 error-point gap that GroupNorm closes almost entirely. On object detection and segmentation tasks where batch sizes are forced small by high-resolution inputs, GroupNorm consistently matches or exceeds BatchNorm's accuracy without any batch-size dependence.

InstanceNorm — the extreme case of GroupNorm with one group per channel — is the normalizer at the heart of neural style transfer. The original style transfer literature (Ulyanov et al., 2016; Huang & Belongie, 2017) showed that normalizing each feature map independently removes the "style" information (encoded in the per-channel mean and variance) while preserving the "content" information (encoded in the spatial activation pattern). This property is specific to InstanceNorm and does not generalize to other normalizers: BatchNorm and LayerNorm both mix information across channels in ways that blend style and content.

---

## Part 6: Choosing and Placing Normalization

### 6.1 The decision table

Choosing a normalization layer is not a hyperparameter search problem. The choice follows directly from the architecture type and the constraints on batch size and sequence format. The following table summarizes the practical decision rules that cover the vast majority of cases encountered in production deep learning.

| Normalizer | Normalizes over | Batch-dependent? | Best for | Avoid when |
|---|---|---|---|---|
| **BatchNorm** | `(N, H, W)` per channel | Yes — train/eval split, running buffers | Vision CNNs, batch ≥ 16 | Batch < 8; recurrent nets; variable-length sequences |
| **LayerNorm** | Feature dim per sample | No — identical train/eval | Transformers, NLP, RNNs | Vision CNNs (degrades vs BN on large-batch ImageNet) |
| **RMSNorm** | Feature dim per sample | No — identical train/eval | Modern LLMs (LLaMA, Mistral) | Tasks where mean-centering is critical (rare; few known cases) |
| **GroupNorm** | Grouped channels per sample | No — identical train/eval | Small-batch vision, detection, segmentation | Large-batch ImageNet (BN still marginally better at batch 256+) |
| **InstanceNorm** | `(H, W)` per channel, per sample | No — identical train/eval | Style transfer, image generation | Classification, detection (destroys channel correlations useful for semantics) |

For vision CNNs trained with batch size 256 on ImageNet-scale datasets, BatchNorm remains the best-tested choice. Its batch statistics are highly accurate at this batch size, its regularizing side effect from batch-statistic noise is beneficial, and decades of empirical tuning have validated its hyperparameters. For Transformers and sequence models, LayerNorm (or RMSNorm for large-scale LLM training) is the standard — batch dependence is a liability for variable-length sequences, and per-token normalization respects the independence of sequence positions. For vision tasks with batch size constrained to 8 or below, GroupNorm replaces BatchNorm with minimal accuracy loss. For style transfer, InstanceNorm is the only normalizer that provides the style-content separation the task requires.

### 6.2 Pre-norm vs post-norm in residual blocks

A residual block computes `output = F(x) + x`, where `F` is a sub-network — a stack of convolutions, a self-attention block followed by a feed-forward network, or any composition of learnable transformations. The normalization layer can be placed either before `F` (pre-norm) or after the addition (post-norm), and the choice has dramatic consequences for training stability as depth increases.

**Pre-norm**: normalize before the sub-network, then add the residual. `output = F(LN(x)) + x`. In this configuration, the residual path `x` passes through to the output unchanged — the identity connection is clean, and gradients can flow backward through this path without attenuation or transformation. Only the sub-network input is normalized. This is the standard in modern Transformers from GPT-2 onward and in all large language models.

**Post-norm**: normalize after the addition. `output = LN(F(x) + x)`. This was the original Transformer design (Vaswani et al., 2017). Both the residual path and the sub-network output pass through the normalization layer, which constrains the scale of the combined signal.

The stability difference between the two configurations is large and well-documented. In post-norm, the residual signal is normalized, which means the effective contribution of the identity path is scaled down along with the sub-network output. At initialization, when `F(x)` is small (weights are small, the sub-network output is near zero), the residual connection should dominate and provide a near-identity function — but post-norm scales that identity down, potentially amplifying the untrained sub-network's random output relative to the stable identity path. Pre-norm avoids this by normalizing only the sub-network input; the identity path `+ x` is never normalized, so its contribution is always at full scale. This is why pre-norm Transformers can train reliably without the careful learning-rate warmup that the original post-norm Transformer required, and why scaling Transformers to hundreds of layers became feasible only after the field adopted pre-norm.

The trade-off is not one-sided. Some evidence suggests that post-norm can achieve slightly better final accuracy when training succeeds — because the normalization at the output of the residual block constrains the signal at the point where it feeds into the next block, providing tighter control over activation scale throughout the network. But this accuracy advantage is conditional on the network surviving the early training steps, which at depth 50 or 100 is far from guaranteed with post-norm. The practical rule: use pre-norm for any residual architecture deeper than ~12 layers, and consider post-norm only for shallow residual networks where stability is not the bottleneck.

This topic receives full architectural treatment in Module C4 (the Transformer architecture), where the attention mechanism, residual streams, and normalization placement are analyzed as a system with explicit gradient-flow analysis. For this module, the key takeaway is that normalization placement is an architectural decision, not a hyperparameter, and the choice between pre-norm and post-norm determines whether your deep network can train at all without specialized warmup schedules.

### 6.3 Normalization as a regularizer

BatchNorm's use of per-batch statistics has a side effect that its inventors recognized immediately: it injects noise into the activations. Every mini-batch has slightly different μ and σ, and the normalized activations for a given sample differ depending on which other samples happen to be in the same batch. This stochasticity acts as a mild regularizer — the network cannot rely on precise activation values because those values shift slightly from batch to batch, so it must learn representations that are robust to small perturbations.

Ioffe and Szegedy observed that this regularizing effect was strong enough to replace dropout in many configurations. Dropout randomly zeros activations during training to prevent co-adaptation of features; BatchNorm's batch-statistic noise provides a different form of stochasticity that achieves a similar regularizing goal. Networks trained with BatchNorm often achieve their best generalization without dropout, and adding dropout on top of BatchNorm can sometimes harm performance by introducing too much noise.

This regularizing side effect is specific to batch-dependent normalizers. LayerNorm, RMSNorm, and GroupNorm are deterministic per sample — given the same input, they always produce the same output, regardless of batch composition. They provide no regularization from normalization noise. If you replace BatchNorm with GroupNorm in a vision model, you may need to add or increase dropout to compensate for the loss of the BatchNorm noise regularizer.

The interaction with BatchNorm's regularization also connects to Module 1.3.2's discussion of batch size and gradient noise. The stochasticity in BatchNorm's statistics is correlated with the stochasticity in the gradient estimates: both depend on which samples happen to be in the current batch. When you increase batch size, both sources of noise decrease together, which is part of why the linear scaling rule for learning rate (Goyal et al., 2017) works — larger batches produce less noisy gradients and less noisy normalization, both of which permit larger learning rates.

---

## Did You Know?

- **BatchNorm was preceded by "whitening" approaches.** Earlier work attempted to whiten activations — zero mean, unit variance, *and* decorrelated — before each layer. The problem with whitening is that it requires computing the full covariance matrix and its inverse square root, an O(d³) operation for d-dimensional features that is expensive to compute and nontrivial to backpropagate through because the eigendecomposition or Cholesky factorization is not a simple element-wise operation. Ioffe and Szegedy's key insight was that per-dimension normalization — mean and variance only, no decorrelation — is sufficient, because the subsequent learned linear transform (the weight matrix of the next layer, plus the learned γ and β of the normalization itself) can handle the necessary rotation. This reduced the cost from O(d³) to O(d) and made normalization cheap enough to insert at every layer of every network, which is why BatchNorm succeeded where whitening failed.

- **The "frozen BatchNorm" trick** is a common fine-tuning practice. When adapting a pretrained vision model to a new task with a small dataset (fewer than a few thousand samples), it is often better to freeze the BatchNorm running statistics — set the layer to eval mode and do not update the running buffers — and only update the affine parameters γ and β, or even freeze those as well and only train the task-specific head. The reasoning: the running statistics computed from the large source dataset (e.g., ImageNet with 1.2 million images) are high-quality population estimates. Overwriting them with noisy statistics from a small target dataset produces worse normalization and degrades the model's ability to leverage its pretrained features.

- **`SyncBatchNorm`** converts BatchNorm to use global statistics across all GPUs in a distributed training run. In standard `DistributedDataParallel`, each GPU normalizes using only its own per-GPU batch. With 8 GPUs each processing 32 samples, each GPU's BatchNorm sees only 32 samples for its statistics — and if memory constraints force per-GPU batch size to 4, each GPU sees only 4 samples. `SyncBatchNorm` (`torch.nn.SyncBatchNorm`) communicates μ and σ² across GPUs so the effective batch for statistics is the global batch size (256 in the first example, 32 in the second). The communication overhead is modest — two all-reduce operations per normalization layer — and the benefit is that your BatchNorm statistics are as accurate as if you had trained on a single GPU with the global batch size.

- **Weight Standardization** (Qiao et al., 2019) takes the dual approach: instead of normalizing activations, standardize the *weights* of each layer to zero mean and unit variance. The idea is that if the weights are constrained to zero mean and unit variance, the output of a convolution has more stable statistics even without activation normalization. Combined with GroupNorm (which handles the residual activation drift), Weight Standardization eliminated BatchNorm from vision training entirely on ImageNet, achieving competitive accuracy (75.9% with ResNet-50 at batch size 256) without any batch-dependent statistics. The approach has not seen widespread adoption — BatchNorm remains simpler and more battle-tested — but it demonstrates that the normalization axis (activations vs weights, features vs batch) is a design choice, not a mathematical necessity.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Forgetting `model.eval()` before inference | BatchNorm continues to use per-batch statistics and update running buffers during inference, producing outputs that depend on batch composition and silently degrade over time | Switch the module to evaluation mode with `model.eval()` before inference — this is what flips BN/Dropout to their eval behavior; optionally also wrap the forward in `with torch.inference_mode():` for speed. `torch.inference_mode()` ALONE does not change the module's train/eval state, so BN/Dropout stay in training behavior without the eval-mode call. Verify with `assert not model.training` |
| Applying BatchNorm to a batch size of 1 or 2 | The batch statistics are extremely noisy — the variance estimate from 2 samples has ~50% relative error; running estimates converge poorly; training and inference drift apart systematically | Use GroupNorm for vision tasks, LayerNorm for sequences when batch ≤ 8 |
| Using BatchNorm in Transformers or RNNs | Padded positions contribute to μ and σ, distorting statistics for real tokens; batch composition affects per-sample predictions | Use LayerNorm or RMSNorm — per-token, per-feature normalization respects sequence independence |
| Confusing `momentum` conventions between frameworks | PyTorch: `running = (1−m)·running + m·batch`; TensorFlow/Keras (historical): `running = m·running + (1−m)·batch` | When porting models, set PyTorch `momentum = 1.0 − TF_momentum`; verify by printing `running_mean` after a few batches |
| Applying weight decay to γ and β of normalization layers | Weight decay penalizes large γ values, which reduces the effective learning rate for early layers and can prevent the network from learning useful feature scales | Exclude normalization parameters from weight decay: `no_decay = [p for n, p in model.named_parameters() if 'norm' in n or 'bias' in n]` |
| Normalizing after ReLU instead of before | ReLU zeros negative activations, shifting the mean of surviving values upward; normalizing after ReLU produces a non-zero mean that BatchNorm then re-centers, wasting the learnable β parameter's capacity | Place normalization *before* the activation function (conv → BN → ReLU), the standard ordering in ResNet and most modern CNNs |
| Using BatchNorm's unbiased variance estimator when replicating the computation | `torch.var(unbiased=False)` is used for **normalization**, but the `running_var` buffer stores `torch.var(unbiased=True)`; the default `torch.var()` (unbiased) matches the buffer, not the normalization step | Always pass `unbiased=False` when replicating BatchNorm's *normalization* variance computation; the discrepancy is invisible at batch=256 but matters at batch=4 |

---

## Quiz

1. **BatchNorm uses batch statistics in train mode and running statistics in eval mode. If you deploy a model with `model.train()` instead of `model.eval()`, what two problems occur, and why might they go undetected in a brief smoke test?**

   <details>
   <summary>Answer</summary>
   First, the model uses per-batch μ and σ instead of the frozen running estimates, so the prediction for a given input depends on which other inputs happen to be in the same inference batch — outputs are non-deterministic and vary with batch composition. Second, the forward pass continues to update the running buffers via `running = (1−momentum)·running + momentum·batch_stat`, gradually overwriting the carefully accumulated training-set population statistics with the inference data distribution. The bug often passes brief smoke tests because (a) if the inference batch happens to be large and well-distributed, the per-batch stats approximate the population stats well, and (b) the model still produces outputs in a reasonable range — the degradation is statistical (1-5% accuracy drop) rather than catastrophic. It surfaces only when someone computes aggregate metrics over a properly distributed test set.
   </details>

2. **A 50-layer ResNet is pretrained with BatchNorm and batch size 256 on ImageNet. You need to fine-tune it on a medical imaging dataset where GPU memory limits you to batch size 4. What will happen if you leave BatchNorm in train mode during fine-tuning, and what is the correct fix?**

   <details>
   <summary>Answer</summary>
   With batch size 4, the per-batch μ and σ estimates are extremely noisy. Each forward pass normalizes with a different, inaccurate μ/σ pair — the fluctuations inject uninformative noise into the activations, and gradients computed from those noisy activations are themselves corrupted. Training loss shows high variance between steps. Simultaneously, the running-mean update `running = 0.9·running + 0.1·batch_stat` accumulates the noisy batch estimates, and the running buffers drift away from the true ImageNet population statistics toward a noisy estimate of the small medical dataset's statistics. The correct fix has two options. Option A: freeze the BatchNorm layers in eval mode (use pretrained ImageNet running statistics) and only train the affine parameters γ and β — or simply freeze all BatchNorm parameters and train only the final classifier. Option B: replace BatchNorm with GroupNorm before fine-tuning (`nn.GroupNorm(num_groups=32, num_channels=C)`), which provides batch-independent normalization and trains stably at any batch size. Option A is simpler; Option B is better if the domain shift is large enough that the ImageNet statistics are substantially wrong for the medical images.
   </details>

3. **Explain why the learnable parameters γ and β are essential to BatchNorm. What would happen if you normalized to zero mean and unit variance without them?**

   <details>
   <summary>Answer</summary>
   Without γ and β, every layer's output is constrained to exactly zero mean and unit variance for every feature channel. A ReLU following such a normalization layer receives activations where roughly half the values are negative and zeroed out, and the surviving half have a mean shifted upward from zero. The network cannot represent transformations that require a different scale or mean — a sigmoid activation expecting inputs in [−1, 1] always receives unit-variance inputs regardless of what is optimal for the task; a layer that needs to amplify one feature and suppress another cannot do so because the normalization fixes the scale. The learnable γ and β restore full representational capacity: γ lets the network learn, per channel, the optimal scale (amplify important features, attenuate noise), and β lets it learn the optimal shift (bias the normalized distribution toward positive or negative values as the downstream computation requires). The normalization provides stable optimization; the affine parameters provide expressive power.
   </details>

4. **Layer Normalization computes μ = (1/H)·Σ x_j per sample. If H = 1 (a single feature), what is the output of LayerNorm, and why is this a degenerate case?**

   <details>
   <summary>Answer</summary>
   With H = 1, the single feature value x_1 is also the mean: μ = x_1. The variance is σ² = (x_1 − x_1)² / 1 = 0. The normalized value is x̂_1 = (x_1 − x_1) / √(0 + ε) = 0. For any input, the normalized output is identically 0, and the final output after the affine transform is y = γ · 0 + β = β — a constant independent of the input. LayerNorm requires at least 2 features to compute a meaningful variance and produce a non-degenerate normalization. This degenerate case is avoided in practice because LayerNorm is always applied over at least dozens of features — d_model ≥ 64 in Transformers, H × W ≫ 1 in vision LayerNorm.
   </details>

5. **You replace BatchNorm with GroupNorm in a CNN and observe that validation accuracy drops 1.5% at batch size 256, the same batch size where BatchNorm has always excelled. Is GroupNorm a worse normalizer?**

   <details>
   <summary>Answer</summary>
   GroupNorm is not worse in any absolute sense; the comparison at batch size 256 is BatchNorm's home turf. At this batch size, BatchNorm's statistics are estimated from N × H × W values — for a 256×28×28 feature map that is over 200,000 samples per channel, producing extremely accurate μ and σ. Additionally, the small residual noise from batch statistics acts as a beneficial regularizer that GroupNorm, being deterministic per sample, cannot provide. The 1.5% gap is the cost of giving up both accurate large-sample statistics and batch-noise regularization. The fair comparison is at batch size 2 or 4, where BatchNorm's statistics are noisy and GroupNorm's batch-independence becomes an advantage — in that regime GroupNorm outperforms BatchNorm by 2-4%, which is exactly the regime GroupNorm was designed for. The normalizer choice depends on the operational constraint (batch size), not on an abstract ranking of "better" versus "worse."
   </details>

6. **Santurkar et al. (2018) showed that BatchNorm smooths the loss landscape. What does "smoothing" mean precisely, and why does it allow higher learning rates?**

   <details>
   <summary>Answer</summary>
   Smoothing means the loss function L(θ) has a smaller Lipschitz constant with respect to the weights θ — formally, there exists a constant C such that ‖∇L(θ₁) − ∇L(θ₂)‖ ≤ C · ‖θ₁ − θ₂‖ for all θ₁, θ₂ in the relevant region of parameter space. A smaller C means the gradient does not change abruptly as you move through weight space. The practical consequence: the first-order Taylor approximation ∇L(θ_t)·Δθ — which gradient descent uses to decide its step direction and magnitude — is accurate over larger steps Δθ. If the gradient changes slowly, taking a larger step in the current gradient direction remains a good move; if the gradient changes rapidly (large Lipschitz constant), a large step lands you in a region where the gradient points somewhere else entirely and the update is counterproductive. This is why BatchNorm-trained networks tolerate learning rates 5× to 30× higher than un-normalized networks: the smoother landscape makes gradient descent's local-linearity assumption valid over longer distances. The Santurkar experiments validated this by measuring the effective β-smoothness of the loss along the optimization trajectory and showing it is consistently smaller with BatchNorm.
   </details>

---

## Hands-On Exercise

**Task**: Build a small CNN with and without BatchNorm, train both on Fashion-MNIST, and measure (a) training speed (loss after N steps), (b) sensitivity to learning rate, and (c) the value of the running mean buffer after training.

1. Set up a minimal CNN: `Conv2d(1, 16, 3) → ReLU → Conv2d(16, 32, 3) → ReLU → AdaptiveAvgPool2d(4) → Flatten → Linear(512, 10)`. Train for 5 epochs on Fashion-MNIST with `torch.optim.SGD`, lr=0.01, batch=64. Record the final training loss and the activation mean/std at the output of the first Conv2d (before ReLU).

2. Insert BatchNorm after each Conv2d (before ReLU, so: `Conv2d → BatchNorm2d → ReLU`). Re-train with identical hyperparameters. Record: the final training loss, the activation mean/std at the output of the first BatchNorm (should be ∼0, ∼1), and the running-mean buffer of the first BatchNorm layer after training.

3. Repeat the BatchNorm experiment with lr=0.1 (10× higher). Record whether training diverges. Compare with the no-BN network at lr=0.1 — it should diverge or produce much higher loss.

4. Switch to batch size 4 and compare BatchNorm vs GroupNorm. Replace `BatchNorm2d(16)` with `GroupNorm(num_groups=4, num_channels=16)` and `BatchNorm2d(32)` with `GroupNorm(num_groups=8, num_channels=32)`. Train both for 5 epochs at lr=0.01 and record final training loss.

```python
# Verification scaffold — run after completing the four experiments above
import torch
import torch.nn as nn

# After training the BatchNorm model:
bn_layer = model_with_bn[1]  # first BatchNorm2d, after first Conv2d
print(f"BatchNorm running mean (first 8 of {bn_layer.num_features} channels):")
print(bn_layer.running_mean[:8])
print(f"BatchNorm running var  (first 8):")
print(bn_layer.running_var[:8])

# The running mean should be meaningfully non-zero — the data has structure
# that the running statistics have captured.

# At batch_size=4, GroupNorm should train to a lower loss than BatchNorm:
print(f"BN final train loss (bs=4):  {bn_bs4_loss:.4f}")
print(f"GN final train loss (bs=4):  {gn_bs4_loss:.4f}")
# Expected: gn_bs4_loss < bn_bs4_loss (GroupNorm handles small batches better)
```

Success criteria:

- [ ] The BN model at lr=0.01 reaches lower training loss than the no-BN model after 5 epochs.
- [ ] The no-BN model diverges or trains poorly at lr=0.1; the BN model does not.
- [ ] The running-mean buffer after training is meaningfully non-zero (it learned population statistics from the data).
- [ ] At batch size 4, GroupNorm achieves lower final training loss than BatchNorm.

---

## Key Takeaways

Normalization layers re-standardize activations during training so that deep networks remain trainable despite weight updates shifting activation distributions across layers. They address the *dynamic* problem of distribution drift that initialization solves statically at step zero. Without normalization, activation statistics compound across depth — a small shift at layer 3 becomes a large shift at layer 30 — and the optimizer must continuously re-adapt to a moving target.

BatchNorm normalizes over the batch and spatial dimensions per channel, computing per-batch μ and σ² and maintaining running-mean and running-variance buffers via `running = (1−momentum)·running + momentum·batch_stat`. The train-vs-eval statistics switch — batch statistics in `.train()`, frozen running buffers in `.eval()` — must be explicitly managed: forgetting `model.eval()` before inference produces silent accuracy degradation that passes basic smoke tests. The running-buffer update uses PyTorch's `(1−momentum)` convention, which differs from TensorFlow's historical convention, making the `momentum` value a portability trap.

LayerNorm normalizes over the feature dimension per sample, is batch-independent, and has identical train and eval behavior. This makes it the natural choice for Transformers and sequence models where batch composition and sequence length vary, and where the per-token independence of normalization is essential for correct handling of padding and variable-length inputs. RMSNorm simplifies LayerNorm further by dropping the mean-centering step and the bias term, normalizing by root-mean-square only — the cheaper operation that modern LLMs use at every sub-layer.

GroupNorm normalizes within groups of channels per sample, providing batch-independent normalization for vision tasks where GPU memory constraints force small batch sizes. InstanceNorm (GroupNorm with one group per channel) is the normalizer for style transfer, where per-channel normalization separates content from style. The choice of normalizer follows directly from the architecture type and batch-size constraint, not from hyperparameter search.

Santurkar et al. (2018) demonstrated that BatchNorm's primary mechanism is smoothing the loss landscape — reducing the gradient's Lipschitz constant — rather than reducing internal covariate shift. This explains why normalization helps even in shallow networks where covariate shift is negligible, and why BatchNorm-trained networks tolerate learning rates 5× to 30× higher than un-normalized networks.

Normalization placement in residual blocks — pre-norm versus post-norm — is an architectural decision with stability consequences. Pre-norm (normalize before the sub-layer, then add the residual) preserves a clean identity path for gradient flow and is the standard for deep Transformers. Post-norm was the original design but requires careful warmup schedules to survive early training at depth.

---

## Sources

- Ioffe, S., & Szegedy, C. (2015). Batch Normalization: Accelerating Deep Network Training by Reducing Internal Covariate Shift. *ICML 2015*. arXiv:1502.03167. https://arxiv.org/abs/1502.03167
- Ba, J. L., Kiros, J. R., & Hinton, G. E. (2016). Layer Normalization. *arXiv:1607.06450*. https://arxiv.org/abs/1607.06450
- Zhang, B., & Sennrich, R. (2019). Root Mean Square Layer Normalization. *NeurIPS 2019*. arXiv:1910.07467. https://arxiv.org/abs/1910.07467
- Wu, Y., & He, K. (2018). Group Normalization. *ECCV 2018*. arXiv:1803.08494. https://arxiv.org/abs/1803.08494
- Santurkar, S., Tsipras, D., Ilyas, A., & Madry, A. (2018). How Does Batch Normalization Help Optimization? *NeurIPS 2018*. arXiv:1805.11604. https://arxiv.org/abs/1805.11604
- Ulyanov, D., Vedaldi, A., & Lempitsky, V. (2016). Instance Normalization: The Missing Ingredient for Fast Stylization. *arXiv:1607.08022*. https://arxiv.org/abs/1607.08022
- Qiao, S., Wang, H., Liu, C., Shen, W., & Yuille, A. (2019). Micro-Batch Training with Batch-Channel Normalization and Weight Standardization. *arXiv:1903.10520*. https://arxiv.org/abs/1903.10520
- Touvron, H., et al. (2023). LLaMA: Open and Efficient Foundation Language Models. *arXiv:2302.13971*. https://arxiv.org/abs/2302.13971
- Jiang, A. Q., et al. (2023). Mistral 7B. *arXiv:2310.06825*. https://arxiv.org/abs/2310.06825
- Huang, X., & Belongie, S. (2017). Arbitrary Style Transfer in Real-Time with Adaptive Instance Normalization. *ICCV 2017*. arXiv:1703.06868. https://arxiv.org/abs/1703.06868
- Goyal, P., et al. (2017). Accurate, Large Minibatch SGD: Training ImageNet in 1 Hour. *arXiv:1706.02677*. https://arxiv.org/abs/1706.02677
- Vaswani, A., et al. (2017). Attention Is All You Need. *NeurIPS 2017*. https://arxiv.org/abs/1706.03762
- PyTorch 2.12 documentation: `torch.nn.BatchNorm1d`. https://pytorch.org/docs/stable/generated/torch.nn.BatchNorm1d.html
- PyTorch 2.12 documentation: `torch.nn.LayerNorm`. https://pytorch.org/docs/stable/generated/torch.nn.LayerNorm.html
- PyTorch 2.12 documentation: `torch.nn.RMSNorm`. https://pytorch.org/docs/stable/generated/torch.nn.RMSNorm.html
- PyTorch 2.12 documentation: `torch.nn.GroupNorm`. https://pytorch.org/docs/stable/generated/torch.nn.GroupNorm.html
- Dive into Deep Learning — Batch Normalization: https://d2l.ai/chapter_convolutional-modern/batch-norm.html
- Stanford CS231n — Training Neural Networks, Part 2 (Normalization): https://cs231n.github.io/neural-networks-2/

---

## Next Module

Continue to [Training-Diagnostics Playbook](/ai-ml-engineering/deep-learning/module-1.3.5-training-diagnostics-playbook/) — where the initialization, optimizer, regularization, and normalization machinery from Modules 1.3.1–1.3.4 becomes a systematic process for reading loss curves, gradient norms, and activation statistics to localize why a training run is failing.

## Learner check

> | 1.3.4 | [Normalization Layers](/ai-ml-engineering/deep-learning/module-1.3.4-normalization-layers/) |
