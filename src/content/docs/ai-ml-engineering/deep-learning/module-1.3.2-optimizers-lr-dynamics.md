---
title: "Optimizers & Learning-Rate Dynamics"
slug: ai-ml-engineering/deep-learning/module-1.3.2-optimizers-lr-dynamics
sidebar:
  order: 1004.2
---

> **AI/ML Engineering Track** | Complexity: `[COMPLEX]` | Time: 4-6 hours
>
> **Prerequisites**: Module 1.1.7 (Tiny NumPy NN Lab — wrote SGD by hand), Module 1.1.8 (Scalar Autograd — built a Value engine), Module 1.3 (Training Neural Networks — PyTorch training loop mechanics), Module 1.3.1 (Weight Initialization — parameter values at t=0).
>
> **Primary tools**: PyTorch 2.12, `torch.optim`, `torch.optim.lr_scheduler`, NumPy.

---

Hypothetical scenario: you inherit a training script that ran for 72 hours on eight GPUs. The loss curve looks like an EKG — sharp drops alternating with long, almost-flat plateaus. The final validation accuracy is 68.3%, two points worse than a smaller model trained with a budget a tenth the size. The author shrugs: "I tried a few learning rates. SGD just does that sometimes." You open the file and find `torch.optim.SGD(model.parameters(), lr=0.01)` — no momentum, no schedule, no thought about the loss landscape the optimizer is trying to navigate. The training did not fail because deep learning is hard; it failed because the optimizer was handed a pair of boots and asked to climb ice.

The manual update rule you wrote in Module 1.1.7 — `layer.W -= lr * layer.dW` — is the ancestor of every modern optimizer. That single line of code is correct, complete, and mathematically sound. It is also, in a great many practical settings, too slow to converge, too sensitive to its hyperparameter, or outright incapable of reaching a good minimum. The 70 years of optimization research that separate Rosenblatt's perceptron from today's large-scale training are not about inventing fundamentally different mathematics; they are about engineering the update step so that scarce gradient information moves parameters as efficiently as possible.

This module builds the complete modern optimizer stack on top of the one-line update you already understand. Every PyTorch optimizer you will meet — SGD, Momentum, Nesterov, AdaGrad, RMSProp, Adam, AdamW — is a direct refinement of `W -= lr * dW`. The refinements address three problems: direction (which way should I move?), step size (how far?), and schedule (when should I change those decisions?). When you finish this module, you will read `torch.optim.AdamW(model.parameters(), lr=3e-4)` and see inside it a chain of design choices, each solving a problem you can diagnose from a loss curve.

---

## Learning Outcomes

By the end of this module, you will be able to:

1. **Diagnose** SGD convergence failures — zig-zagging in ravines, stalling on plateaus, and diverging from noisy gradients — from loss-curve and gradient-norm evidence alone.
2. **Implement** momentum and Nesterov accelerated gradient in both raw NumPy and PyTorch, and explain why the "heavy ball" mechanism damps oscillation while preserving consistent gradient direction.
3. **Derive** the Adam update rule from its parent methods (momentum + RMSProp + bias correction), computing one complete step by hand with a toy parameter vector to verify understanding.
4. **Explain** why weight decay and L2 regularization are not equivalent under Adam, and configure `torch.optim.AdamW` correctly because of that distinction.
5. **Design** a learning-rate schedule — including warmup, cosine annealing, and step decay — that matches a given training budget and batch size, then **execute** a learning-rate range test to select a well-motivated LR for a new problem rather than guessing `3e-4`.

---

## Why This Module Matters

A practitioner who can design a model architecture but cannot diagnose an optimizer is like a driver who can plan a route but cannot read the fuel gauge. The optimizer controls the only mechanism by which your model actually changes. Hyperparameter search — grid, random, Bayesian — can find decent settings if you have unlimited compute budget, but it cannot explain why one setting worked and another did not. When training diverges at step 53,201, or when a carefully constructed schedule produces worse results than no schedule at all, understanding the optimizer's internal state is the difference between a five-minute fix and a multi-day rerun.

The optimizer is also the site where many assumptions about the loss landscape become visible. Gradient descent assumes a locally quadratic bowl; real loss surfaces contain ravines, saddle points, cliffs, and regions where the Hessian's condition number exceeds 1,000. Momentum, adaptive step sizes, and schedules are all responses to violations of the simple-bowl assumption. Each response comes with its own failure modes. Adam can overshoot when its second-moment estimate lags behind a suddenly steep gradient. Cosine annealing can produce a loss spike at the restart boundary if the warmup is too short. SGD with momentum still requires you to pick the momentum coefficient β, and the wrong choice can turn the optimizer into an undamped oscillator that bounces across the loss surface without settling.

The learning rate is often called the single most important hyperparameter in deep learning. That statement is approximately true — but it obscures the deeper truth that the learning rate is not one number. It is a number that interacts with batch size, gradient noise, optimizer state, normalization layers, and weight initialization to produce an effective step size the practitioner never directly sets. This module teaches you to think about that effective step size, so you can see past the `lr=` argument to the dynamics it actually controls.

---

## Part 1: SGD, the Loss Landscape, and Why It Goes Wrong

### 1.1 The Update Rule You Already Know

In Module 1.1.7 you implemented the core training loop for a tiny NumPy neural network. After computing gradients via your hand-written backpropagation, you updated every parameter with a single line:

```python
layer.W -= lr * layer.dW
layer.b -= lr * layer.db
```

This is stochastic gradient descent in its purest form. For a parameter vector θ, given a mini-batch estimate of the gradient g_t at step t, the update is:

```
θ_{t+1} = θ_t - η · g_t
```

where η is the learning rate. The PyTorch equivalent is:

```python
import torch
import torch.optim as optim

model = torch.nn.Linear(10, 2)
optimizer = optim.SGD(model.parameters(), lr=0.01)

# Inside the training loop:
optimizer.zero_grad()
loss.backward()
optimizer.step()
```

The `.step()` call executes exactly `θ -= η · g` for every registered parameter. The one-line manual update from A7 and this three-step PyTorch pattern are identical in effect. The difference is that PyTorch handles parameter traversal, gradient accumulation, device movement, and state management — but the mathematics has not changed.

### 1.2 The Geometry That Breaks SGD

Pure SGD is correct, but correct does not mean fast. To understand why, we need to look at the loss surface itself.

Imagine a narrow valley running diagonally across a plane. The valley floor slopes gently toward a minimum at the far end, but the walls on either side are steep. If you stand anywhere in this valley and compute the gradient, it points almost straight into the wall — perpendicular to the direction you actually want to travel. SGD responds by stepping down the steep wall, overshooting the valley floor because the gradient was large, landing on the opposite wall, and repeating. The result is a zig-zag path that makes progress toward the minimum only through the small diagonal component of each step.

This is the **ravine problem**. It is not a pathological edge case; it arises whenever the Hessian (the matrix of second derivatives) has eigenvalues that differ substantially in magnitude — a condition called **ill-conditioning**. The condition number κ = λ_max / λ_min quantifies this. When κ ≫ 1, the loss surface is shaped like a long, narrow trench, and the gradient at any point is dominated by the steepest direction, regardless of where the minimum actually lies.

```ascii
   Steep wall
      /\
     /  \
    /    \
   /  o-> \       o = starting point
  /   |    \      -> = gradient direction (into wall)
 /    v     \     ... = SGD path (zig-zag toward minimum)
/............*_____\___ Valley floor
              * = minimum
```

The zig-zag behavior has a concrete cost. If the condition number is 100, each step moves you roughly 100 units sideways for every 1 unit of forward progress. At a fixed learning rate, convergence takes O(κ) iterations instead of the O(1) you would get in a perfectly spherical bowl. Worse, the learning rate is bounded by the steepest direction: set it too high, and the steps into the wall overshoot so badly that training diverges. Set it low enough to avoid divergence, and forward progress along the valley floor becomes glacial.

A second failure mode is the **plateau problem**. When the surface has very low curvature in every direction — a flat region where the gradient is near zero — SGD takes tiny steps and can appear to stop entirely. The optimizer has no memory of how it arrived at the plateau, so it cannot use past momentum to coast through.

A third is **noisy gradients**. Mini-batch SGD estimates the true gradient from a subset of the data, so every g_t contains sampling noise. Near a sharp minimum, that noise can kick the parameters out of the basin entirely. Near a saddle point — where one direction curves up, another curves down — the noise can actually help by pushing the optimizer off the flat ridge, but it can also destabilize convergence in the final stages of training.

All three failure modes — ravines, plateaus, and noise — are addressed by the two families of improvements we will study: momentum (which adds a velocity term) and adaptivity (which gives each parameter its own learning rate).

---

## Part 2: Momentum and Nesterov Accelerated Gradient

### 2.1 The Heavy-Ball Intuition

Physical momentum smooths motion. Push a heavy ball across a bumpy surface, and it resists sudden changes in direction — it rolls past small divots and averages out high-frequency jitter while continuing in the general direction of the slope. Polyak's 1964 momentum method borrows exactly this idea for optimization.

Instead of using the raw gradient to update parameters, momentum maintains a **velocity vector** v_t that accumulates gradients over time, damped by a coefficient μ (typically 0.9):

```
v_t = μ · v_{t-1} + g_t
θ_{t+1} = θ_t - η · v_t
```

In the ravine scenario, the gradient alternates sign across the steep direction on every step: positive on one wall, negative on the other. The velocity sum v_t adds those opposite-sign contributions, so they partially cancel. Along the valley floor, the gradient consistently points the same way, so those contributions accumulate. The result: the zig-zag is damped, and forward progress accelerates.

Work through one dimension of a ravine numerically. Suppose the gradient alternates between +10 and -9 in the steep direction while contributing +0.1 consistently along the valley. With μ = 0.9, η = 0.01, and starting from rest:

| Step | Raw gradient g_t | v_t (μ=0.9) | Update η·v_t |
|------|-------------------|--------------|---------------|
| 1    | +10               | 10.0         | 0.100         |
| 2    | -9                | 0.0          | 0.000         |
| 3    | +10               | 10.0         | 0.100         |
| 4    | -9                | 0.0          | 0.000         |

In the steep direction, the velocity cancels completely every other step. Pure SGD would have oscillated between +0.10 and -0.09 each step, never settling. Now contrast the valley-direction contribution, assuming a consistent gradient of +0.1:

| Step | Cumulative v_t (valley) | Cumulative displacement (η·Σv₁..t) |
|------|--------------------------|-------------------------------------|
| 1    | 0.10                     | 0.001                               |
| 2    | 0.19                     | 0.003                               |
| 3    | 0.27                     | 0.006                               |
| 4    | 0.34                     | 0.009                               |
| 10   | 0.65                     | 0.041                               |

The accumulative effect means the optimizer accelerates along consistent gradient directions — exactly the behavior that pushes it through plateaus and along ravine floors. The cost: momentum introduces one new hyperparameter, μ (PyTorch calls it `momentum`). Values of 0.9, 0.99, and 0.999 are common starting points.

In PyTorch, enabling momentum requires only the `momentum` argument on the SGD optimizer — the velocity buffer is created, maintained, and applied automatically. This single flag activates the entire heavy-ball mechanism:

```python
optimizer = optim.SGD(model.parameters(), lr=0.01, momentum=0.9)
```

That is the entire API change. The optimizer now maintains a velocity buffer for every parameter, updates it on each `.step()` call, and uses it to compute the actual parameter update. You can inspect the buffer:

```python
optimizer.step()
# After step, the velocity is in the optimizer state dict:
state = optimizer.state_dict()
for param_id, param_state in state['state'].items():
    if 'momentum_buffer' in param_state:
        print(param_state['momentum_buffer'].shape)
```

### 2.2 Nesterov Accelerated Gradient: Look Before You Leap

Standard momentum computes the gradient at the current position, then adds the velocity to decide where to go. Nesterov's insight, from his 1983 work on accelerated gradient methods, was to compute the gradient at the position you *would* reach after applying the velocity, rather than at the current position. In physical terms: look where the momentum is carrying you, then correct. In equations:

```
v_t = μ · v_{t-1} + g(θ_{t-1} − η·μ·v_{t-1})
θ_t = θ_{t-1} − η · v_t
```

The difference is the gradient argument: it is evaluated at the look-ahead position `θ − η·μ·v` (one momentum step ahead in the descent direction) instead of at the current `θ`. This correction term allows Nesterov to react faster when the velocity is carrying it toward a region where the gradient changes rapidly — it "sees the curve coming" and begins decelerating before the overshoot.

For convex optimization, Nesterov's method has a provably better convergence rate (O(1/t²) vs. O(1/t) for standard momentum). For non-convex deep-learning loss surfaces, the practical benefit is subtler: Nesterov often reduces the oscillation amplitude around sharp minima and can produce modestly better final performance, particularly when training with high momentum values (μ ≥ 0.9) and a decaying learning rate.

PyTorch exposes Nesterov as a flag on the SGD optimizer:

```python
optimizer = optim.SGD(model.parameters(), lr=0.01, momentum=0.9, nesterov=True)
```

PyTorch uses an algebraically-equivalent *reformulation* that avoids the second forward pass; note that PyTorch's momentum/Nesterov convention differs subtly from the classical Sutskever formulation, so do not expect bit-identical trajectories to a textbook implementation — see the PyTorch `torch.optim.SGD` docs. The reformulation maps directly onto the corrected textbook rule above: with `nesterov=True`, PyTorch still accumulates velocity with the current gradient but applies the update using a look-ahead correction baked into the step. The modest benefit shows up most clearly when μ is high (≥ 0.9) and the learning rate is decaying — settings where standard momentum tends to overshoot sharp curvature near a minimum.

A small worked check with a single scalar parameter confirms the behavior difference. The code below tracks two copies of the same scalar parameter, one updated with standard momentum and the other with Nesterov, under identical gradients from a simple quadratic loss:

```python
import torch

# Standard momentum baseline
p_m = torch.tensor([0.0], requires_grad=True)
opt_m = torch.optim.SGD([p_m], lr=0.1, momentum=0.9, nesterov=False)

# Nesterov
p_n = torch.tensor([0.0], requires_grad=True)
opt_n = torch.optim.SGD([p_n], lr=0.1, momentum=0.9, nesterov=True)

# Simulate a few steps with a simple quadratic loss: loss = (p - 3)^2
for step in range(5):
    for name, p, opt in [('momentum', p_m, opt_m), ('nesterov', p_n, opt_n)]:
        opt.zero_grad()
        loss = (p - 3.0) ** 2   # minimum at p=3
        loss.backward()
        opt.step()
    print(f"step {step}: momentum p={p_m.item():.4f}, nesterov p={p_n.item():.4f}")

# Both converge to 3.0; Nesterov typically overshoots less on the initial approach
```

### 2.3 What Momentum Cannot Fix

Momentum helps with ravines and plateaus by adding a directional memory. It does not help with the fact that every parameter shares the same global learning rate. In a deep network, different layers operate at different scales: the first convolutional layer may need tiny updates to avoid wrecking learned edge detectors, while the final classifier head may need large updates because its weights were just randomly initialized. A single η forces a compromise that satisfies neither. This is the problem that adaptive methods solve.

---

## Part 3: Adaptive Methods — One Learning Rate Per Parameter

### 3.1 AdaGrad: The First Adaptive Optimizer

AdaGrad (Duchi, Hazan & Singer, 2011) introduced the idea that each parameter should have its own effective learning rate, and that rate should be informed by the history of gradients seen for that parameter. The rule is elegantly simple:

```
r_t = r_{t-1} + g_t²          (accumulate squared gradients)
θ_{t+1} = θ_t - (η / (√(r_t) + ε)) · g_t
```

where r_t is the sum of squared gradients for that parameter across all time, ε is a tiny constant (1e-8 or so) for numerical stability, and the division and square root are applied element-wise. PyTorch places ε outside the square root — the same convention used in Adam's update below. The effect: parameters that consistently receive large gradients (like the steep walls of a ravine) get their effective learning rate scaled down by 1/√(Σg²). Parameters that receive small, infrequent gradients (like those on a plateau) keep a relatively larger learning rate.

This is a genuine breakthrough for sparse features and problems where different dimensions have vastly different gradient magnitudes. In natural language processing, for instance, rare words get few gradient updates; AdaGrad gives them larger steps when they do appear, allowing them to be learned despite their sparsity.

The fatal flaw: the denominator r_t is a sum over the entire training history, so it grows monotonically and without bound. As training proceeds, the effective learning rate `η / √(r_t)` decays to zero for every parameter. The model eventually stops learning, even if it has not converged. For convex problems this is actually a feature — the vanishing rate guarantees convergence. For non-convex deep learning over many epochs, it is a showstopper.

### 3.2 RMSProp: A Moving Average Fixes the Decay

RMSProp (Tieleman & Hinton, 2012, from Hinton's Coursera lecture) replaces the cumulative sum with an exponentially weighted moving average (EMA) of squared gradients:

```
r_t = β₂ · r_{t-1} + (1 - β₂) · g_t²
θ_{t+1} = θ_t - (η / (√(r_t) + ε)) · g_t
```

where the smoothing constant (PyTorch calls it `alpha`) is typically 0.9–0.99, with a default of 0.99 — distinct from Adam's β₂ = 0.999. Because the EMA forgets old gradient magnitudes at a rate controlled by this decay, the effective learning rate no longer decays to zero. It adapts to the *recent* gradient magnitudes, which is exactly what non-stationary deep-learning optimization needs.

RMSProp is still in active use, particularly in reinforcement learning where its simpler second-moment tracking (no bias correction, no first moment) works well with the high-variance gradients typical of policy-gradient methods. PyTorch includes it directly:

```python
optimizer = optim.RMSprop(model.parameters(), lr=0.01, alpha=0.99)
# alpha is the EMA coefficient (β₂ in our notation)
```

Much of the benefit of adaptive methods is already captured by RMSProp. It handles per-parameter scaling and does not suffer from the monotonic decay of AdaGrad. What it lacks — and what Adam adds — is momentum.

### 3.3 Adam: Momentum + RMSProp + Bias Correction

Adam (Kingma & Ba, 2015, "Adam: A Method for Stochastic Optimization") combines the two ideas: the momentum velocity (using an EMA of past gradients) and the RMSProp adaptive scaling (using an EMA of squared gradients). The algorithm maintains two buffers for each parameter:

```
m_t = β₁ · m_{t-1} + (1 - β₁) · g_t        (first moment estimate — momentum)
v_t = β₂ · v_{t-1} + (1 - β₂) · g_t²       (second moment estimate — adaptive scaling)
```

The algorithm's default hyperparameters are set to values that Kingma and Ba found robust across a wide variety of tasks: β₁ = 0.9 controls the first-moment decay (how much past gradients influence the current momentum direction), β₂ = 0.999 controls the second-moment decay (how quickly the adaptive scaling responds to changing gradient magnitudes), and ε = 1e-8 prevents division by zero in the parameter update.

At t = 0, both m₀ and v₀ are initialized to zero. This introduces a problem: in the first few steps, m_t and v_t are biased toward zero because the EMA starts from zero and has not yet accumulated enough signal. For example, at step 1:

```
m₁ = β₁·0 + (1-β₁)·g₁ = (1-β₁)·g₁
```

If β₁ = 0.9, then m₁ = 0.1·g₁ — the estimate is an order of magnitude too small. Adam corrects this with a **bias correction** term:

```
m̂_t = m_t / (1 - β₁ᵗ)
v̂_t = v_t / (1 - β₂ᵗ)
```

This division exactly cancels the initialization bias. At t=1, 1-β₁ᵗ = 0.1, so m̂₁ = (0.1·g₁) / 0.1 = g₁ — the unbiased estimate. As t grows, β₁ᵗ → 0 fairly quickly (0.9²⁰ ≈ 0.12, so the correction is negligible after ~20 steps), so the bias correction matters most in the very early phase of training.

The final parameter update is:

```
θ_{t+1} = θ_t - η · m̂_t / (√v̂_t + ε)
```

This is the full Adam update. Let us compute one step by hand for a single parameter to make it concrete.

**Worked example — one Adam step by hand.** Suppose θ₀ = 0.5, and the first three gradients are g₁ = 0.3, g₂ = -0.1, g₃ = 0.2. Use η = 0.01, β₁ = 0.9, β₂ = 0.999, ε = 1e-8.

**Step 1 (t=1, g₁=0.3):** m₁ = 0.9·0 + 0.1·0.3 = 0.03; v₁ = 0.999·0 + 0.001·(0.3)² = 0.00009; m̂₁ = 0.03 / (1 - 0.9¹) = 0.3; v̂₁ = 0.00009 / (1 - 0.999¹) = 0.09; θ₁ = 0.5 - 0.01 · 0.3 / (√0.09 + 1e-8) = 0.5 - 0.01 = **0.49**.

**Step 2 (t=2, g₂=-0.1):** m₂ = 0.9·0.03 + 0.1·(-0.1) = 0.017; v₂ = 0.999·0.00009 + 0.001·(0.01) = 0.00009991; m̂₂ = 0.017 / (1 - 0.9²) ≈ 0.08947; v̂₂ = 0.00009991 / (1 - 0.999²) ≈ 0.04998; θ₂ = 0.49 - 0.01 · 0.08947 / (√0.04998 + ε) ≈ 0.49 - 0.00400 = **0.4860**.

**Step 3 (t=3, g₃=0.2):** m₃ = 0.9·0.017 + 0.1·0.2 = 0.0353; v₃ = 0.999·0.00009991 + 0.001·(0.04) = 0.00013981; m̂₃ = 0.0353 / (1 - 0.9³) ≈ 0.1303; v̂₃ = 0.00013981 / (1 - 0.999³) ≈ 0.04665; θ₃ = 0.4860 - 0.01 · 0.1303 / (√0.04665 + ε) ≈ 0.4860 - 0.00603 = **0.4800**.

The bias-correction divisors (1 - β₁ᵗ) and (1 - β₂ᵗ) are **smallest** in the first few steps — at t=1 they equal 0.1 and 0.001 — so the correction factors 1/(1−βᵗ) are **largest** then, and m̂ and v̂ are much larger than the raw m and v early on. The effective step size is amplified until the EMA buffers have accumulated enough history. By step 3, m̂₃ ≈ 3.7× m₃ and v̂₃ ≈ 334× v₃; after ~20 steps the first-moment correction fades, but the second-moment correction (β₂ = 0.999) persists for hundreds of steps. This is why warmup matters: it keeps η small while those early, correction-amplified updates would otherwise dominate.

Notice how the effective step size is determined by the ratio m̂ / (√v̂ + ε) — not by η alone. When the gradient is consistently large, v̂ grows and scales the step down. When gradients oscillate, m̂ (the smoothed value) is small even while v̂ remains large, producing a very small step. This automatic per-parameter scaling is why Adam often works out of the box at its default learning rate of 1e-3 (or 3e-4, the popular convention) across a wide range of architectures.

In PyTorch, Adam is instantiated with exactly the defaults described above — the only argument you normally provide beyond the parameters is the learning rate:

```python
optimizer = optim.Adam(model.parameters(), lr=3e-4, betas=(0.9, 0.999), eps=1e-8)
```

The `betas` tuple is (β₁, β₂). You rarely need to change these from their defaults. The `eps` value is increased in some mixed-precision settings (e.g., to 1e-7 or higher) to avoid division-by-zero when the second-moment estimate underflows in float16.

```python
# Verify the buffers
optimizer.step()
state = optimizer.state_dict()
for param_id, s in state['state'].items():
    print('exp_avg (m_t) shape:', s['exp_avg'].shape)
    print('exp_avg_sq (v_t) shape:', s['exp_avg_sq'].shape)
```

The `exp_avg` buffer holds m_t; `exp_avg_sq` holds v_t. Both are tensors the same shape as the parameter and consume memory proportional to the model size — Adam stores two additional copies of every trainable parameter. For large models, this memory overhead is substantial (~3× the parameter memory, counting parameters + m + v), and it is one reason projects like Adafactor (which factorizes the second moment) exist.

---

## Part 4: AdamW and the Weight-Decay Subtlety

### 4.1 The Equivalence That Isn't

In classical optimization, L2 regularization adds a penalty term λ‖θ‖² to the loss:

```
L_reg(θ) = L(θ) + (λ/2) ‖θ‖²
```

The gradient of the penalty is λθ, so the SGD update becomes:

```
θ_{t+1} = θ_t - η·(g_t + λθ_t) = (1 - ηλ)·θ_t - η·g_t
```

This is L2 regularization implemented as weight decay: the parameter shrinks by a factor of (1-ηλ) before the gradient update. In plain SGD, L2 regularization and weight decay are exactly equivalent after a simple reparameterization.

Under Adam, they are not. When the L2 penalty gradient λθ is folded into g_t, it passes through the Adam machinery — specifically, it is divided by √v̂_t. A parameter that has a large second-moment estimate v̂_t will have its weight-decay contribution scaled down, making the regularization *adaptive*. A parameter with small v̂_t gets relatively stronger regularization. This is almost certainly not what you intended: regularization strength should be uniform across parameters, not coupled to gradient magnitude history.

The correct approach is **decoupled weight decay** (Loshchilov & Hutter, 2019). Instead of adding λθ to the gradient before the Adam update, apply the decay directly to the parameter, **decoupled from** (i.e., not routed through) the adaptive `m̂/√v̂` update:

```
θ_{t+1} = θ_t - η · m̂_t / (√v̂_t + ε) - η·λ·θ_t
```

The regularization term η·λ·θ_t is subtracted directly from the parameter, outside the adaptive scaling machinery. This is what `torch.optim.AdamW` does — and the distinction is not cosmetic. The Loshchilov & Hutter paper demonstrated that decoupled weight decay consistently outperforms L2 regularization under Adam across CIFAR-10 and ImageNet, often by margins of 1-2% absolute accuracy:

```python
optimizer = optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.01)
```

The `weight_decay` argument to AdamW is the λ above — a direct multiplicative decay applied to the parameter, decoupled from the gradient scaling. In `torch.optim.Adam`, the same `weight_decay` argument implements the old-style L2 penalty (added to the gradient before the adaptive update), which is why the two optimizers produce different trajectories for the same `weight_decay` value.

A practical rule: if your model uses Adam and you want regularization, use AdamW with `weight_decay=0.01` (or 0.1 for some vision models). Do not fall back to Adam and assume the `weight_decay` argument means the same thing.

```python
# These two produce DIFFERENT training dynamics:
opt_adam   = optim.Adam(   model.parameters(), lr=3e-4, weight_decay=0.01)
opt_adamw  = optim.AdamW(  model.parameters(), lr=3e-4, weight_decay=0.01)
# Prefer AdamW for any model where you want weight decay.
```

The distinction generalizes: any optimizer that uses adaptive per-parameter scaling (Adam, RMSProp, AdaGrad, Adamax, Nadam) should decouple weight decay from the gradient preprocessing. PyTorch provides `AdamW` as the primary implementation; `SGD` does not need this distinction because it has no adaptive scaling.

---

## Part 5: Learning-Rate Schedules

### 5.1 Why a Constant Learning Rate Is Rarely Optimal

Early in training, the loss surface is unexplored territory — the optimizer needs to move quickly to escape random-initialization basins and find a good region. Late in training, the optimizer is navigating fine structure near a minimum — large steps would bounce it out. A constant learning rate cannot be both aggressive enough early and gentle enough late.

Schedules address this by varying η over time. The simplest is **step decay**: multiply η by a factor γ every S epochs:

```python
scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=30, gamma=0.1)
# Decays the LR by 10× (multiplies by γ=0.1) every 30 epochs:
# epoch 0-29: η = 0.1
# epoch 30-59: η = 0.01
# epoch 60-89: η = 0.001
```

Multistep decay provides finer control by letting you specify exact epoch boundaries where the learning rate drops. This is especially useful when you have prior knowledge about the loss landscape — for example, when training ResNet on ImageNet, the canonical schedule drops the LR at epochs 30, 60, and 90:

```python
scheduler = optim.lr_scheduler.MultiStepLR(
    optimizer, milestones=[60, 120, 160], gamma=0.2
)
```

These schedules work well when you know roughly how many epochs the problem needs, but they introduce two new hyperparameters (step size and decay factor) and create abrupt transitions that can temporarily destabilize training.

### 5.2 Cosine Annealing

Cosine annealing (Loshchilov & Hutter, 2017, "SGDR: Stochastic Gradient Descent with Warm Restarts") replaces the step-function decay with a smooth cosine curve:

```
η_t = η_min + 0.5 · (η_max - η_min) · (1 + cos(π · t / T))
```

Starting at η_max, the learning rate follows a half-cosine down to η_min over T steps. The transition is smooth, so there is no moment where the optimizer suddenly receives much smaller updates. Cosine annealing has become a standard for vision models trained with SGD and for many transformer training recipes.

```python
scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=200, eta_min=0)
# η follows a half-cosine from initial LR to 0 over 200 epochs.
```

The warm-restart variant (CosineAnnealingWarmRestarts) divides training into multiple cosine cycles, resetting η to η_max at the start of each cycle. The period T_mult typically doubles each cycle so later cycles are longer:

```python
scheduler = optim.lr_scheduler.CosineAnnealingWarmRestarts(
    optimizer, T_0=50, T_mult=2, eta_min=1e-6
)
# Cycle 1: 50 epochs, cycle 2: 100 epochs, cycle 3: 200 epochs
```

### 5.3 Warmup: Why the First Few Steps Need Kid Gloves

The earliest steps of training have a problem that the optimizer's internal state makes worse. At initialization, the Adam buffers m₀ and v₀ are zero. The bias correction fixes the scale, but it cannot fix the quality: the early second-moment estimate v̂_t is computed from very few gradient samples and is therefore a noisy, unreliable divisor. Dividing by a noisy estimate can produce wild parameter updates in the first few hundred steps that push the model into a bad region from which it never fully recovers.

Warmup addresses this by starting the learning rate at (or near) zero and linearly increasing it to the target value over a small number of steps (typically a few hundred to a few thousand). By the time the LR reaches full strength, the Adam buffers have accumulated enough signal to produce stable estimates.

```python
def warmup_lambda(step):
    warmup_steps = 1000
    if step < warmup_steps:
        return step / warmup_steps
    return 1.0  # constant LR after warmup

warmup_scheduler = optim.lr_scheduler.LambdaLR(optimizer, lr_lambda=warmup_lambda)
```

For a warmup followed by cosine decay — the standard recipe for transformer training since Vaswani et al. (2017) — PyTorch's `SequentialLR` composes the two schedules cleanly. The `milestones` argument specifies the step at which the active scheduler switches:

```python
warmup = optim.lr_scheduler.LinearLR(
    optimizer, start_factor=0.01, total_iters=1000
)
cosine = optim.lr_scheduler.CosineAnnealingLR(
    optimizer, T_max=10000, eta_min=1e-6
)
scheduler = optim.lr_scheduler.SequentialLR(
    optimizer, schedulers=[warmup, cosine], milestones=[1000]
)
```

After step 1000, the active scheduler switches from warmup to cosine automatically. This pattern — warmup then cosine — is the de facto standard for transformer training (Vaswani et al., 2017; GPT variants; ViT) and appears in almost every large-scale training recipe published since 2018.

### 5.4 When to Call scheduler.step()

When to call `scheduler.step()` is a source of persistent training bugs, and the distinction between epoch-level and step-level scheduling is not something PyTorch enforces — it trusts you to get it right. The convention is straightforward but unforgiving:

- **Epoch-level schedules** (StepLR, MultiStepLR, CosineAnnealingLR): call `scheduler.step()` once per epoch, AFTER `optimizer.step()`.
- **Step-level schedules** (LambdaLR with a step function, warmup): call `scheduler.step()` once per optimizer step (i.e., once per batch), AFTER `optimizer.step()`.

Calling `scheduler.step()` before `optimizer.step()` gives you the LR for the *previous* step, which is usually not what you want. Calling it at the wrong frequency can silently produce a very different schedule than intended. The safe pattern:

```python
for epoch in range(num_epochs):
    for batch in dataloader:
        optimizer.zero_grad()
        loss = model(batch).mean()
        loss.backward()
        optimizer.step()
        # Step-level scheduler goes here (warmup, per-step LambdaLR)
        if per_step_scheduler:
            per_step_scheduler.step()
    # Epoch-level scheduler goes here (StepLR, CosineAnnealingLR)
    epoch_scheduler.step()
```

The per-step vs per-epoch distinction is the most common scheduler bug in production code. The runnable contrast below uses the same toy optimizer but two schedulers with identical `T_max=10` — one stepped every batch, one stepped every epoch over 2 epochs × 5 batches. The per-step scheduler completes its full cosine in 10 optimizer steps (LR 1.0 → eta_min). The per-epoch scheduler uses the SAME `T_max=10` but is called only twice (once per epoch boundary), so it advances just 2/10 of the cosine — the LR barely drops (≈1.0 → ≈0.976) and never approaches `eta_min`. Sizing `T_max` for per-step calls while stepping per epoch is exactly the bug:

```python
import torch
import torch.optim as optim

def demo_scheduler_placement():
    # Per-step: T_max counts optimizer steps
    opt_step = optim.SGD([torch.nn.Parameter(torch.tensor(1.0))], lr=1.0)
    sched_step = optim.lr_scheduler.CosineAnnealingLR(opt_step, T_max=10, eta_min=0.0)
    lrs_per_step = []
    for epoch in range(2):
        for batch in range(5):
            opt_step.step()          # dummy optimizer step
            sched_step.step()        # AFTER optimizer.step(), once per batch
            lrs_per_step.append(opt_step.param_groups[0]['lr'])

    # Per-epoch: T_max counts epoch boundaries
    opt_epoch = optim.SGD([torch.nn.Parameter(torch.tensor(1.0))], lr=1.0)
    sched_epoch = optim.lr_scheduler.CosineAnnealingLR(opt_epoch, T_max=10, eta_min=0.0)
    lrs_per_epoch = []
    for epoch in range(2):
        for batch in range(5):
            opt_epoch.step()
            lrs_per_epoch.append(opt_epoch.param_groups[0]['lr'])
        sched_epoch.step()           # AFTER all batches in the epoch

    print("per-step LRs:", [round(x, 3) for x in lrs_per_step])
    # Cosine drops across all 10 steps: 1.0 → ... → 0.0
    print("per-epoch LRs:", [round(x, 3) for x in lrs_per_epoch])
    # LR stays 1.0 for epoch 0, then drops once at epoch 1 boundary

demo_scheduler_placement()
```

Match `T_max` to the unit you actually step on. Warmup schedulers composed via `SequentialLR` are almost always per-step; `StepLR` and `CosineAnnealingLR` in vision recipes are almost always per-epoch. Mixing them in one training loop without tracking which scheduler fires where is how you end up with warmup ending at step 1,000 but cosine annealing finishing at step 200.

---

## Part 6: The Learning-Rate Finder

### 6.1 The Range Test

In 2015 (updated 2017), Leslie Smith proposed a simple empirical method: instead of guessing a learning rate, run one epoch where the LR increases exponentially from a very small value (e.g., 1e-7) to a very large value (e.g., 10), and plot the loss. The loss typically does three things:

1. **Flat or slowly decreasing** at very low LRs — the optimizer is barely moving.
2. **Steeply decreasing** as the LR enters the productive range — this is where you want to train.
3. **Diverging** (sharp increase) when the LR exceeds what the loss landscape can tolerate — the optimizer is overstepping.

The "just before divergence" point gives you an upper bound. Smith recommends picking an LR one order of magnitude below that point, or roughly at the point where the loss is decreasing fastest (the steepest negative slope). For cyclical learning rates, the upper and lower bounds of the cycle bracket this region.

A minimal but functionally complete implementation of the LR range test in PyTorch is shown below. The key design choice is the exponential LR multiplier: each step increases the LR by a constant factor so that the sweep covers several orders of magnitude smoothly. The early-stopping guard (loss exceeding 4× the recent average) prevents wasting time on diverged training after the LR has exceeded the usable range:

```python
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

def lr_find(model, train_loader, criterion, device, start_lr=1e-7, end_lr=10, num_steps=200):
    """Run one epoch with exponentially increasing LR, collect loss values."""
    model.train()
    lr_mult = (end_lr / start_lr) ** (1 / num_steps)
    lr = start_lr
    optimizer = optim.SGD(model.parameters(), lr=lr)

    lrs, losses = [], []
    data_iter = iter(train_loader)

    for step in range(num_steps):
        try:
            batch = next(data_iter)
        except StopIteration:
            data_iter = iter(train_loader)
            batch = next(data_iter)

        inputs, targets = batch
        inputs, targets = inputs.to(device), targets.to(device)

        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()

        lrs.append(lr)
        losses.append(loss.item())

        lr *= lr_mult
        for pg in optimizer.param_groups:
            pg['lr'] = lr

        # Stop if loss explodes
        if step > 5 and loss.item() > 4 * np.mean(losses[-5:-1]):
            break

    return lrs, losses

# After running: plot losses vs lrs on a log scale.
# Pick LR at the steepest descending point, or ~1/10 of the divergence point.
```

The range test is cheap — one epoch of training — and gives you an evidence-based starting LR for any new dataset, architecture, or optimizer. It does not replace tuning, but it prevents the most expensive failure mode: discovering after a full run that the learning rate was off by a factor of 10 or 100.

### 6.2 Order-of-Magnitude Defaults

When the range test is impractical (e.g., hyperparameter search over many configurations), these defaults serve as reasonable starting points, backed by the literature:

| Optimizer | Typical LR range | Notes |
|-----------|-----------------|-------|
| SGD (no momentum) | 1e-2 to 1e-1 | Requires a schedule; sensitive to batch size |
| SGD + momentum (0.9) | 1e-2 to 1e-1 | Cosine schedule typical; still common for vision |
| Adam | 1e-4 to 1e-3 | Default 1e-3 from paper; 3e-4 is the popular convention |
| AdamW | 1e-4 to 3e-3 | Often higher than Adam because weight decay is decoupled |
| RMSProp | 1e-3 to 1e-2 | Common in RL; alpha=0.99 |

These are starting points, not laws. The correct LR for your problem depends on batch size (larger batches → often higher LR, the "linear scaling rule"), model depth, normalization layers (BatchNorm and LayerNorm reduce LR sensitivity), and dataset difficulty. The range test remains your best tool for narrowing the search.

---

## Part 7: Choosing an Optimizer in Practice

### 7.1 A Decision Framework, Not a Table

The optimizer question is too often answered by habit: "I always use AdamW" or "SGD generalizes better, so I use SGD." Both statements capture real patterns, but both are incomplete. The right optimizer depends on at least four factors:

**1. How much hyperparameter tuning budget do you have?** Adam and AdamW are more robust to the learning-rate choice — they work reasonably well at their defaults across a wide range of problems. SGD with momentum requires careful LR tuning (the range test helps) and almost always needs a schedule. If you are exploring a new architecture or dataset and want quick signal, start with AdamW. If you are squeezing the last half-percent of accuracy on a well-understood benchmark (e.g., ImageNet classification), the tuning investment in SGD + momentum + cosine may pay off.

**2. Does your problem have sparse gradients?** Embedding layers, particularly in NLP and recommendation systems, produce very sparse gradient updates — most rows of an embedding matrix get zero gradient on any given batch. Adam handles this well because its per-parameter scaling gives infrequently updated parameters larger effective step sizes. AdaGrad was originally motivated by this very use case. If your model has large embedding tables, Adam or a dedicated sparse optimizer (e.g., Adagrad, FTRL) is a better default than SGD.

**3. What is your memory budget?** SGD stores one buffer per parameter (the velocity if momentum is used). Adam stores two. For a 7B-parameter model in float32, each full-size buffer is 7×10⁹ × 4 bytes = 28 GB, so **Adam (params + m + v) ≈ 28 × 3 = 84 GB** versus **SGD-with-momentum (params + velocity) ≈ 28 × 2 = 56 GB**. For very large models, this gap dictates whether training fits in GPU memory at all. Techniques like 8-bit Adam (bitsandbytes), Adafactor (which factorizes v_t), or plain SGD become necessary purely for memory reasons.

**4. The generalization-gap debate.** A persistent empirical finding, most thoroughly documented by Wilson et al. (2017, "The Marginal Value of Adaptive Gradient Methods in Machine Learning"), is that adaptive methods sometimes produce models that generalize slightly worse than well-tuned SGD with momentum — on the order of 1-3% absolute accuracy on image classification benchmarks. The hypothesized mechanism: adaptive methods find "sharper" minima (higher curvature), which are more sensitive to data perturbations than the "flatter" minima SGD tends to find. The effect is real but its magnitude varies substantially across architectures and tasks. In practice, the generalization gap is often closed by strong data augmentation, longer training, and modern regularization (dropout, weight decay, stochastic depth), so that AdamW and SGD converge to similar final performance on many modern benchmarks when both are well-tuned.

### 7.2 Practical Defaults

For new projects in 2025-2026, a reasonable default stack is:

```
AdamW, lr=3e-4, weight_decay=0.01, betas=(0.9, 0.999)
 + CosineAnnealingLR with warmup (1-5% of total steps)
 + Gradient clipping at 1.0 (module B6)
```

This combination handles most architectures — transformers, MLPs, CNNs — with minimal per-problem tuning. Exceptions: (a) very large vision models where SGD + momentum + cosine still holds state-of-the-art claims, (b) RL where RMSProp or specialized optimizers (PPO defaults) dominate, (c) memory-constrained settings requiring 8-bit or factorized optimizers.

A complete PyTorch snippet that instantiates this recommended stack and runs a training loop is shown below. Note the use of `set_to_none=True` on `zero_grad()` — this is slightly more memory-efficient than zeroing the gradient tensor in place, and it avoids a class of subtle bugs where zero-valued gradient tensors are accidentally included in gradient-norm calculations:

```python
import torch
import torch.optim as optim

model = ...  # your nn.Module
# compute_loss(model, batch) and batch come from your training setup

optimizer = optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.01,
                         betas=(0.9, 0.999), eps=1e-8)

warmup_steps = 500
total_steps = 10000

scheduler1 = optim.lr_scheduler.LinearLR(
    optimizer, start_factor=0.01, total_iters=warmup_steps
)
scheduler2 = optim.lr_scheduler.CosineAnnealingLR(
    optimizer, T_max=total_steps - warmup_steps, eta_min=1e-6
)
scheduler = optim.lr_scheduler.SequentialLR(
    optimizer, schedulers=[scheduler1, scheduler2], milestones=[warmup_steps]
)

# Training loop (per-step scheduler.step() — matches warmup + cosine T_max in steps)
for step in range(total_steps):
    batch = next_batch()  # your data iterator
    optimizer.zero_grad(set_to_none=True)
    loss = compute_loss(model, batch)
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    optimizer.step()
    scheduler.step()
```

The `set_to_none=True` argument on `zero_grad()` sets `.grad` fields to `None` instead of zeroing the tensor. This is slightly more memory-efficient (the gradient buffer is freed) and can avoid a class of subtle bugs where zero-valued gradient tensors are accidentally included in gradient-norm calculations.

---

## Did You Know?

- **Where "Adam" comes from.** Kingma & Ba derived the name from **ada**ptive **m**oment estimation — the optimizer tracks the first moment (mean) and second moment (uncentered variance) of the gradients.

- **Sutskever's 2013 paper on momentum** (the one that popularized Nesterov momentum for deep learning) reports that without momentum, a deep autoencoder failed to train at all on MNIST under the same architecture and learning rate. The addition of momentum made the difference between zero signal and successful convergence.

- **The linear scaling rule** (Goyal et al., 2017, "Accurate, Large Minibatch SGD: Training ImageNet in 1 Hour") states that when you multiply the batch size by k, you should also multiply the learning rate by k. This holds because one large-batch update with learning rate k·η approximates the *net effect* of k consecutive small-batch SGD steps at learning rate η, **under the assumption that the gradient changes little across those k steps** — which is why the rule needs warmup early in training (when that assumption is weakest) and breaks down past batch sizes of ~8K on ImageNet.

- **Adam's ε parameter has caused real production incidents.** With float16 mixed precision, the default ε = 1e-8 can underflow the second-moment estimate v̂ to zero, causing division-by-zero in the update. PyTorch's automatic mixed precision handles this, but custom AMP implementations have produced NaN-in-weight incidents that took teams days to diagnose. Raising ε to 1e-7 or 1e-5 in fp16 regimes is a cheap insurance policy.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Calling `scheduler.step()` before `optimizer.step()` | The LR for step t is based on step t-1's schedule state; the first epoch runs at the wrong LR | Always call `scheduler.step()` after `optimizer.step()` |
| Using `Adam.weight_decay` as if it were decoupled | The weight decay is passed through the adaptive scaling, making regularization strength parameter-dependent | Use `AdamW` for decoupled weight decay |
| Forgetting to zero the momentum buffer when restarting training from a checkpoint | The optimizer state dict carries velocity, but if you change the LR or model, stale momentum can push parameters in wrong directions | If changing hyperparameters mid-training, reinitialize the optimizer or manually zero the momentum buffers |
| Setting `lr=0.1` with Adam because it works for SGD | Adam's effective step size is roughly η / √v̂, which is much larger than η alone for parameters with small gradients; 0.1 with Adam typically diverges | Start at 1e-3 or 3e-4 for Adam; use the LR finder |
| Using cosine annealing with `T_max` equal to total steps but calling `scheduler.step()` every epoch | The cosine curve completes in `T_max` scheduler calls; if `T_max` is sized for total steps but you call `scheduler.step()` once per epoch, after `num_epochs` calls it has advanced only `num_epochs/T_max` of the way — the schedule never finishes, so the LR stays near its initial value and barely anneals | Match the scheduler call frequency to T_max: set T_max = num_epochs for epoch-level calls, or T_max = total_steps for step-level calls |
| Forgetting that `optimizer.step()` uses the gradients accumulated in `.grad`, not the loss itself | If you call `.backward()` twice without `zero_grad()` in between, the second backward's gradients are added to the first — the effective batch size has changed | One `zero_grad()` per step; if accumulating gradients intentionally, call `optimizer.step()` only after the last backward in the accumulation cycle |

---

## Quiz

1. **Why does pure SGD zig-zag in ravines instead of moving directly toward the minimum?**

   <details>
   <summary>Answer</summary>
   In an ill-conditioned loss surface (large condition number κ), the gradient is dominated by the direction of steepest curvature. In a narrow valley, the gradient points almost perpendicular to the valley floor — into the steep wall. SGD follows that gradient, overshoots, lands on the opposite wall, and repeats. The forward progress along the valley floor is only the small diagonal component of each step. The effective convergence rate degrades from O(1) to O(κ).
   </details>

2. **Adam's bias correction divides m_t by (1 - β₁ᵗ) and v_t by (1 - β₂ᵗ). Why are these corrections necessary, and roughly how many steps does it take for them to become negligible at β₁=0.9 and β₂=0.999?**

   <details>
   <summary>Answer</summary>
   Both m₀ and v₀ are initialized to zero. The EMA update m_t = β₁·m_{t-1} + (1-β₁)·g_t therefore produces estimates biased toward zero in early steps — at t=1, m₁ = 0.1·g₁ rather than g₁. Dividing by (1-β₁ᵗ) exactly cancels this initialization bias. For β₁=0.9: after ~20 steps, 0.9²⁰ ≈ 0.12, so the divisor (1-0.12)=0.88 and the correction is modest. After ~50 steps the correction is negligible. For β₂=0.999: 0.999¹⁰⁰⁰≈0.368, so it takes roughly 1,000-2,000 steps before the bias correction on v_t becomes small. The second-moment correction matters much longer, which is one reason warmup helps — it prevents large effective step sizes while v̂_t is still unreliable.
   </details>

3. **Explain why `Adam.weight_decay` and `AdamW.weight_decay` produce different parameter trajectories even when all other hyperparameters are identical.**

   <details>
   <summary>Answer</summary>
   In `Adam`, weight decay is implemented as L2 regularization: the penalty gradient λθ is added to g_t and then divided by √v̂_t (the adaptive scaling). This means parameters with larger second-moment estimates receive weaker regularization, and vice versa. In `AdamW`, weight decay is decoupled: the term η·λ·θ is subtracted from the parameter AFTER the adaptive Adam update, so all parameters receive uniform regularization independent of their gradient history. The practical effect is that AdamW provides more consistent regularization, which typically leads to better generalization, especially for models where different layers have very different gradient magnitudes (e.g., transformers with large embedding tables).
   </details>

4. **You train a model with AdamW, warmup for 1,000 steps, then switch to cosine annealing. The loss drops quickly during warmup, then rises sharply at step 1,001 and never fully recovers. What is the most likely cause?**

   <details>
   <summary>Answer</summary>
   The most likely cause is that the `SequentialLR` transition between warmup and cosine did not preserve the learning-rate value at the boundary. If warmup ends at η=1e-3 but the cosine scheduler was initialized with a different starting LR (or `eta_max`), the LR jumps discontinuously at step 1,001. The abrupt change can destabilize training, especially if the jump is upward. The fix is to ensure `CosineAnnealingLR` starts from the same LR where warmup ends. With `LinearLR(start_factor=0.01)` and initial LR=3e-4, warmup ends at 3e-4; if cosine's initial LR was set to the optimizer's default before warmup (3e-4), the transition is smooth. Alternatively, use `LambdaLR` with a custom function that smoothly transitions.
   </details>

5. **What does an LR range-test loss plot look like when the initial LR is already in the productive range, and what does it look like when the initial LR is too low?**

   <details>
   <summary>Answer</summary>
   When the initial LR is already productive, the loss decreases immediately from the first few steps — there is no flat region at the left of the plot. When the initial LR is too low, the loss remains flat or decreases extremely slowly for many steps (the left side of the U-shaped curve) before finally entering the productive range. The optimal LR to pick is near the steepest point of the descending curve, which usually lies an order of magnitude or two below the divergence point. If you never see a steep descent (the loss decreases gradually over the entire range), the upper bound of the test may not be high enough; extend `end_lr` upward. If the loss diverges almost immediately, the lower bound `start_lr` should be decreased.
   </details>

6. **You are training a large model with AdamW on 8 GPUs using DistributedDataParallel. Each GPU processes a batch of 32 samples. Should you adjust the learning rate relative to a single-GPU baseline with batch size 32, and if so, by how much?**

   <details>
   <summary>Answer</summary>
   The effective global batch size is 8 × 32 = 256. By the linear scaling rule (Goyal et al., 2017), you should multiply the learning rate by the batch-size ratio: η_256 ≈ 8 × η_32. So if the well-tuned single-GPU LR is 3e-4, the 8-GPU training should start around 2.4e-3. In practice, the linear scaling rule holds well up to batch sizes of a few thousand for ImageNet-scale problems, but for very large batch sizes (>8K) the rule breaks down because gradient noise reduction saturates. Note that the linear scaling rule was originally demonstrated for SGD + momentum; under Adam/AdamW the relationship is similar but the effective scaling may differ slightly because the adaptive normalization already adjusts per-parameter step sizes. The range test remains the most reliable method for determining the correct LR at any batch size.
   </details>

---

## Hands-On Exercise

**Task**: Run the learning-rate range test on a small CNN (or MLP) with the Fashion-MNIST dataset, then compare the loss curves produced by SGD, SGD with momentum, and Adam at the LR suggested by the range test.

Follow these numbered steps to complete the exercise, which walks you through infrastructure setup, the LR range test, comparative training, and analysis of the resulting loss curves:

1. Set up a minimal training pipeline: a 3-layer CNN or 2-hidden-layer MLP, `CrossEntropyLoss`, and the Fashion-MNIST data loader (available via `torchvision.datasets.FashionMNIST`).

2. Implement the LR range test (as shown in Part 6) with `torch.optim.SGD(model.parameters(), lr=1e-7)`, sweeping up to `lr=1.0` over 200 steps. Plot the loss against LR on a log scale. Identify: the LR at which loss decreases fastest, and the LR at which loss begins diverging.

3. Train three short runs (5 epochs each) at the chosen LR:
   - `optim.SGD(model.parameters(), lr=chosen_lr)`
   - `optim.SGD(model.parameters(), lr=chosen_lr, momentum=0.9)`
   - `optim.Adam(model.parameters(), lr=chosen_lr / 10)` (because Adam's effective step size is larger — the factor of 10 is a heuristic; the range test on Adam separately is more precise)

4. Record the final training loss for each run and plot the loss curves on the same axes.

When you have completed the training runs, verify each of the following observable outcomes. If any criterion fails, the most likely culprit is the learning-rate choice — rerun the range test and verify you selected the LR at the steepest point of descent, not the divergence point:

- [ ] The range-test plot shows the characteristic three-region shape (flat → steep descent → divergence).
- [ ] SGD with momentum converges faster (lower loss at a given epoch) than plain SGD at the same LR.
- [ ] Adam achieves competitive or better loss than momentum SGD within 5 epochs, without manual LR tuning beyond the /10 heuristic.

After training, use the following verification code to compare final losses. The expected ordering (sgdm < sgd, adam competitive with sgdm) confirms that both momentum and adaptivity improve over plain SGD on a real problem, validating the theoretical arguments of Parts 2 and 3:
```python
# After training, compare final losses
print(f"SGD final loss: {sgd_losses[-1]:.4f}")
print(f"SGD+momentum final loss: {sgdm_losses[-1]:.4f}")
print(f"Adam final loss: {adam_losses[-1]:.4f}")
# Expect: sgdm_losses[-1] < sgd_losses[-1], and adam_losses[-1] roughly competitive
```

---

## Key Takeaways

1. `torch.optim.SGD(lr=0.01)` is the exact equivalent of the `W -= lr * dW` loop you wrote by hand in Module 1.1.7. Its simplicity makes its failure modes — ravines, plateaus, noise sensitivity — directly visible.
2. Momentum (μ ≈ 0.9) adds a velocity term that damps oscillation across steep directions and accelerates movement along consistent gradient directions. Nesterov momentum evaluates the gradient at the look-ahead position `θ − η·μ·v` (one descent step ahead), often reducing overshoot when μ is high and the LR is decaying.
3. Adam combines momentum (first moment EMA) with per-parameter adaptive scaling (second moment EMA) plus bias correction for the zero-initialization of both buffers. It is the default optimizer for most deep-learning work because it tolerates a wide range of learning rates.
4. Weight decay and L2 regularization are not equivalent under adaptive optimizers. Use `AdamW` to apply weight decay outside the gradient-scaling machinery.
5. Learning-rate schedules — step decay, cosine annealing, warmup — are not optional polish. Warmup is functionally necessary for stable Adam training at scale, and cosine annealing often provides a free 0.5-2% improvement in final accuracy over constant LR.
6. The LR range test costs one epoch and gives you an evidence-based learning rate for any new problem. Combined with the optimizer defaults in this module, it eliminates most of the guesswork from optimizer configuration.

---

## Sources

- Kingma, D. P., & Ba, J. (2015). Adam: A Method for Stochastic Optimization. *arXiv:1412.6980*. https://arxiv.org/abs/1412.6980
- Loshchilov, I., & Hutter, F. (2019). Decoupled Weight Decay Regularization. *arXiv:1711.05101*. https://arxiv.org/abs/1711.05101
- Smith, L. N. (2017). Cyclical Learning Rates for Training Neural Networks. *arXiv:1506.01186*. https://arxiv.org/abs/1506.01186
- Loshchilov, I., & Hutter, F. (2017). SGDR: Stochastic Gradient Descent with Warm Restarts. *arXiv:1608.03983*. https://arxiv.org/abs/1608.03983
- Duchi, J., Hazan, E., & Singer, Y. (2011). Adaptive Subgradient Methods for Online Learning and Stochastic Optimization. *Journal of Machine Learning Research, 12*, 2121-2159. https://jmlr.org/papers/v12/duchi11a.html
- Sutskever, I., Martens, J., Dahl, G., & Hinton, G. (2013). On the Importance of Initialization and Momentum in Deep Learning. *ICML 2013*. https://proceedings.mlr.press/v28/sutskever13.html
- Wilson, A. C., Roelofs, R., Stern, M., Srebro, N., & Recht, B. (2017). The Marginal Value of Adaptive Gradient Methods in Machine Learning. *NeurIPS 2017*. https://arxiv.org/abs/1705.08292
- Goyal, P., et al. (2017). Accurate, Large Minibatch SGD: Training ImageNet in 1 Hour. *arXiv:1706.02677*. https://arxiv.org/abs/1706.02677
- PyTorch `torch.optim` documentation. https://pytorch.org/docs/stable/optim.html
- PyTorch learning rate scheduler documentation. https://pytorch.org/docs/stable/optim.html#how-to-adjust-learning-rate
- Zhang, A., Lipton, Z. C., Li, M., & Smola, A. J. (2023). *Dive into Deep Learning*, Chapter 12: Optimization Algorithms. https://d2l.ai/chapter_optimization/

---

## Next Module

Continue to [Training Deep Networks: Normalization, Regularization & Optimization](/ai-ml-engineering/deep-learning/module-1.4-cnns-computer-vision/) — the practical training-stability toolkit that builds directly on optimizer and learning-rate choices.

---

## Learner check

> | 1.3 | [Training Neural Networks](/ai-ml-engineering/deep-learning/module-1.3-training-neural-networks/) |
