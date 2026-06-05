---
title: "Loss Functions & Output Heads"
slug: ai-ml-engineering/deep-learning/module-1.1.5-loss-functions-output-heads
sidebar:
  order: 1002.5
---

Stanford's [CS231n notes on linear classification](https://cs231n.github.io/linear-classify/) emphasize a result that still surprises practitioners the first time they derive it: the gradient of softmax plus cross-entropy with respect to the logits is nothing more than **predicted probabilities minus true labels** — not a Jacobian stuffed with exponentials, not a nest of chain-rule terms that fills three chalkboards, just `p − y`. That cancellation is not a party trick for an exam; it is the reason every production framework fuses the output activation with the loss into one numerically stable kernel. Module A4 taught you which squashing functions belong at hidden layers versus the output head; this module teaches the scalar objective those heads serve and, critically, the **exact** upstream gradient `∂L/∂z` that Module A6 will propagate backward through your cached `Z` tensors.

You have already built forward propagation: batched `X @ W + b`, ReLU hidden units, linear logits at the output, and an `Activation` interface in `nn.py`. Training still lacks a compass. Until this module, your MLP could transform features beautifully and still have no principled way to compare its outputs with labels or to compute the first gradient that A6 will recurse through the cache. That missing piece is not an implementation detail you can postpone — every framework, from this NumPy file to PyTorch distributed jobs on a GPU cluster, spends the majority of its training cycles evaluating a loss and its derivatives. The engineering question is never whether you need a loss, but whether you have chosen the right one for the label semantics and implemented its boundary gradient without off-by-one reduction bugs.

Think of the loss as the contract between the world and your parameters: the world supplies targets, the network supplies predictions or logits, and the loss supplies both a scalar score for monitoring and a gradient vector for improvement. When teams debate whether a model is learning, they watch the scalar; when they debug whether a model is learning correctly, they inspect the gradient at the output, then finite-check one layer backward. This module trains both habits consistently. You will not merely memorize formulas — you will implement them, run the A1 finite-difference ritual on each, and see the printed max absolute error that turns calculus into evidence. A loss function maps predictions and targets to a single number you minimize, and its gradient with respect to the network's final pre-activations is the seed of backpropagation. Get that seed wrong by one sign, one missing `1/n`, or one unstable `exp`, and every weight update in the MLP you constructed in A3 is garbage downstream — often silently, because the loss still decreases for a few steps before NaNs appear. This module's job is to make those gradients inevitable: derive them by hand, implement them in NumPy, and verify each one with the finite-difference checker from A1 before A6 asks you to trust them across an entire graph. Every formula in the parts below is a load-bearing beam for the backpropagation scaffold ahead.

---

## Learning Outcomes

By the end of this module, you will be able to:

- **Explain** what a loss function measures, why training minimizes a scalar objective, and how `∂L/∂z` at the output logits seeds the backward pass that A6 implements through your MLP cache.
- **Derive** gradients for MSE, MAE, and Huber regression losses and for fused sigmoid+BCE and softmax+cross-entropy, including the step-by-step cancellation to `∂L/∂z = p − y`.
- **Implement** numerically stable softmax, log-sum-exp, and BCE-from-logits in NumPy, contrasting naive overflow with the max-subtraction fix in a worked example.
- **Compare** task types to output heads, losses, and output-layer gradients, and describe calibration (ECE, temperature scaling) plus class-imbalance tools (weighted CE, focal loss).
- **Extend** `nn.py` with a `Loss` interface implementing MSE, BCE-with-logits, and softmax-CE-with-logits, verifying each `backward` with `numerical_grad` from A1.

---

## Why This Module Matters

Forward propagation answers "what does the network predict right now?" The loss answers "how wrong is that prediction, and in which direction should every parameter move to become less wrong?" Without a correct loss gradient at the output boundary, backpropagation has nothing to propagate. The chain rule multiplies local derivatives along the path from the loss to each weight; the loss supplies the first factor in that product. If you implement binary cross-entropy on probabilities `p = σ(z)` as two separate steps — sigmoid forward, then BCE on `p` — you can still get the right math, but you are far more likely to divide by `p` when `p` is numerically zero and to pay an extra memory pass. Fusing head and loss is standard because the combined gradient is simpler and stabler than either piece alone.

Regression and classification demand different output heads. A linear head with unbounded outputs pairs with squared error for real-valued targets. A sigmoid head squashes one logit into a probability for binary labels. A softmax head turns a vector of logits into a categorical distribution. Module A4 already warned you not to put softmax in hidden layers; here you learn why softmax at the output is paired exclusively with cross-entropy, and why the derivative of that pair is the elegant `p − y` vector you will reuse in every classifier you train. Engineering teams debugging production models still check this boundary first: does the loss use mean or sum reduction? Are logits passed into `BCEWithLogitsLoss` or probabilities into plain BCE? Mixing conventions between a notebook and a serving binary is a classic source of calibrated-looking metrics in training that collapse in deployment.

Numerical stability is not an optional appendix. The naive formula `p_k = exp(z_k) / Σ_j exp(z_j)` overflows when any logit exceeds roughly 700 in float64 — and far sooner in float32. The log-sum-exp trick and the max-subtraction identity are the difference between a softmax layer that runs on MNIST and one that returns `inf` on the second mini-batch of noisy features. You will see both the failure and the fix in runnable NumPy, because A7's training lab will call softmax-cross-entropy on every epoch. Finally, class imbalance and miscalibration sit at the boundary between loss design and production monitoring: weighted cross-entropy and focal loss adjust how much rare classes contribute to the gradient, while temperature scaling adjusts logits after training so predicted probabilities match empirical frequencies. You need the baseline losses first; these refinements are the knobs practitioners reach for when the baseline under-trains minority classes or overstates confidence.

---

## Part 1: What a Loss Function Is

A supervised learning loop has three visible objects at each step: inputs `X`, targets `y`, and predictions `ŷ` (or logits `z` before the output head). A loss function `L(ŷ, y)` — or `L(z, y)` when the head is fused into the loss — maps those tensors to a scalar that measures dis-agreement, and training adjusts parameters to minimize that scalar. The gradient `∇_θ L` tells you how to nudge each weight and bias; gradient descent in A7 moves opposite that gradient with a learning rate that scales the step size. Without a differentiable loss, there is no principled direction for improvement — you would be tweaking millions of parameters blindly.

At the output boundary, backpropagation starts with `∂L/∂z` (gradient w.r.t. logits) or `∂L/∂ŷ` (gradient w.r.t. post-activation predictions). That vector has the same shape as the network's final layer output: `(batch, d_out)` for vector outputs, `(batch,)` for scalar regression per sample when `d_out = 1`. Module A6 will multiply this upstream gradient by the local Jacobian of each layer going backward, applying the chain rule layer by layer until it reaches `W` and `b` in every `Layer`. The loss is therefore not a separate cosmetic metric reported to TensorBoard — it is the training signal encoded as calculus, and its derivative at the output is the initial condition for the entire backward recursion.

```python
import numpy as np

# Toy: single sample, one output dimension (regression)
z = np.array([2.5])          # logit = prediction (identity head)
y = np.array([1.0])          # target
y_hat = z                    # linear head: ŷ = z

L = np.mean((y_hat - y) ** 2)   # scalar MSE
dL_dy_hat = (2.0 / y_hat.size) * (y_hat - y)  # shape (1,) — seed for backprop
print("loss:", L, "  dL/dŷ:", dL_dy_hat)
```

Reduction semantics deserve explicit attention because they are the silent partner of every learning rate you will tune in A7. This track uses mean reduction unless stated otherwise, which means you divide loss sums by the number of elements that contributed to the average. Mean reduction keeps gradient magnitude stable when you double the batch size; sum reduction would double the gradients as well and force you to halve the learning rate to compensate. PyTorch defaults to `reduction='mean'` for `MSELoss` and `CrossEntropyLoss`, and when you implement `nn.py` losses you should document the same choice and divide `∂L/∂z` by the number of averaged elements so finite-difference checks from A1 agree with your analytical backward pass.

Denote the final pre-activation logits `z`. An output head is the activation applied at the output only: identity for regression, sigmoid for binary probability, softmax for multiclass probabilities. You may fuse the head into the loss implementation (BCE-with-logits, softmax-CE-with-logits) while still reasoning about the head separately when you sketch architectures on a whiteboard. Module A4's rule still holds: ReLU and GELU belong in hidden layers where they preserve gradient flow; the head at the end matches the task and the loss, not the other way around. When you read framework documentation that mentions "logits," it almost always means the values **before** the output squashing — the same `Z` tensor your final `Layer` cached in A3.

> **Hypothetical scenario: The double-sigmoid deployment**
>
> A fraud-detection team shipped a model that applied sigmoid in the network and again wrapped outputs with `BCELoss` expecting probabilities. Training loss looked healthy in notebooks because the notebook matched the mistake. In production, the serving container applied **yet another** sigmoid on top of already-squashed scores. Precision-recall collapsed on live traffic: every score clustered between 0.52 and 0.61, so the ops dashboard threshold at 0.8 never fired. Rollback took an afternoon; root cause took three days because nobody checked whether `BCEWithLogitsLoss` was the right API. The lesson: name whether your tensor is logits or probabilities, fuse head and loss in training code, and make the serving graph a literal copy of the last training forward pass.

The shape contract at this boundary mirrors forward propagation discipline from A3. If your MLP ends with `output` of shape `(N, K)` for `K` classes, then `y` as integer labels has shape `(N,)` and `∂L/∂z` must return shape `(N, K)`. If you instead store one-hot targets, `y` matches `(N, K)`. A common bug is reducing the loss over classes when labels are integer — the backward pass still needs a full `(N, K)` gradient row per sample. Print shapes once when you wire the loss in A7; it is cheaper than interpreting a flat loss curve.

---

## Part 2: Regression Losses

Regression targets are real numbers — price, temperature, latency in milliseconds — and the model must emit unconstrained reals rather than probabilities. The output head is therefore linear (identity): `ŷ = z`, and the loss compares `ŷ` and `y` directly without any squashing function that would cap dynamic range. This pairing is the simplest head-loss combination in the block, yet it already encodes modeling assumptions: squared error implies you believe residuals are roughly symmetric around zero, while absolute or Huber losses encode skepticism about outlier behavior.

### 2.1 Mean squared error (MSE)

For `n` elements (batch × output dims), mean squared error averages squared residuals: $L_{\text{MSE}} = \frac{1}{n} \sum_{i=1}^{n} (\hat{y}_i - y_i)^2$. Differentiating with respect to one prediction gives $\frac{\partial L_{\text{MSE}}}{\partial \hat{y}_i} = \frac{2}{n}(\hat{y}_i - y_i)$, which is the gradient you will feed into backprop when the output head is linear. With an identity head, `∂L/∂z = ∂L/∂ŷ` because the local Jacobian of the identity map is one. MSE penalizes large errors quadratically, which means a single mislabeled or corrupted target can dominate the gradient for an entire mini-batch and pull weights toward fitting that one point. That sensitivity is desirable when residuals are roughly Gaussian and outliers are genuinely rare; it is harmful when labels are heavy-tailed, as in revenue forecasting or latency prediction where a one-hour spike should not rewrite the entire representation. Teams sometimes switch to Huber after they notice training loss jitter caused by a handful of extreme labels in otherwise clean pipelines.

```python
def mse_forward(y_hat, y):
    n = y.size
    return float(np.mean((y_hat - y) ** 2))

def mse_backward(y_hat, y):
    n = y.size
    return (2.0 / n) * (y_hat - y)   # same shape as y_hat
```

### 2.2 Mean absolute error (MAE)

Mean absolute error uses $L_{\text{MAE}} = \frac{1}{n} \sum_{i=1}^{n} |\hat{y}_i - y_i|$, which grows linearly with residual magnitude instead of quadratically. For `ŷ_i ≠ y_i`, the derivative is `∂L/∂ŷ_i = (1/n) · sign(ŷ_i − y_i)`. At `ŷ_i = y_i` the absolute value is non-differentiable; implementations typically assign subgradient zero at that point, which is a modeling convention rather than a physical law. MAE treats outliers linearly rather than quadratically, which makes it robust but also flat near the optimum: when you are already close to the correct prediction, MAE gradients do not shrink toward zero as aggressively as MSE gradients do, and optimization can feel sluggish unless you pair MAE with adaptive learning rates or switch to Huber for the best of both worlds.

### 2.3 Huber loss (smooth L1)

Huber blends MSE near zero and MAE far away. With threshold `δ > 0` and residual `r = ŷ − y`, the loss is quadratic inside the band (`L = \frac{1}{2n} r^2` when $|r| \le \delta$) and linear outside (`L = \frac{1}{n}(\delta |r| - \frac{\delta^2}{2})$ when $|r| > \delta$). The derivative w.r.t. `ŷ` follows the same split: $\frac{1}{n} r$ inside the band and $\frac{\delta}{n}\,\mathrm{sign}(r)$ outside, which caps how aggressively a single outlier can push the gradient while preserving smoothness at the hand-off. Smooth-L1 is the name PyTorch uses for Huber with a specific `δ`. Practitioners often start with MSE because it is the maximum-likelihood loss under Gaussian noise assumptions, then move to Huber when validation error is clearly driven by a thin tail of extreme examples. Computer-vision detection heads used Smooth L1 for bounding-box offsets for years because pixel-level outliers from mis-annotations should not dominate the entire feature map update. Robotics teams use the same logic for torque residuals where occasional sensor spikes are real measurements you do not want to ignore entirely, but also do not want to dominate the Jacobian.

Choosing a regression loss is therefore a statement about your noise model and operational tolerance, not a hyperparameter you should copy blindly from a tutorial notebook. If mislabeled outliers are common, robust losses help; if outliers are rare and physically meaningful, MSE may be the honest likelihood. Document the choice in experiment logs the same way you document learning rate — future you will need to know which gradient shape the optimizer saw.

| Loss | Outlier sensitivity | Smoothness | Typical use |
|------|---------------------|------------|-------------|
| MSE | High (quadratic) | Smooth everywhere | Default regression, Gaussian noise |
| MAE | Low (linear) | Non-smooth at 0 | Heavy tails, median-like fit |
| Huber | Tunable via `δ` | Smooth (C¹) | Robust regression with stable gradients |

---

## Part 3: Binary Classification — Sigmoid and BCE

Binary labels `y ∈ {0, 1}` use one output logit `z` (shape `(batch, 1)` or `(batch,)`). The sigmoid head maps to probability $p = \sigma(z) = 1/(1 + e^{-z})$, and binary cross-entropy (BCE) measures dis-agreement: $L_{\text{BCE}} = -\frac{1}{n}\sum_i [ y_i \log p_i + (1 - y_i)\log(1 - p_i) ]$. This pairing is the default for single-label Bernoulli outcomes because it penalizes confident wrong predictions harshly while rewarding calibrated improvements near the decision boundary.

### 3.1 Separate derivatives (before fusion)

Before fusion, apply the chain rule on one sample (dropping the `1/n` mean factor momentarily). The loss derivative w.r.t. probability is $\frac{\partial L}{\partial p} = -y/p + (1-y)/(1-p) = (p-y)/(p(1-p))$, the sigmoid derivative is $\partial p/\partial z = p(1-p)$, and multiplying yields $\partial L/\partial z = \frac{p-y}{p(1-p)} \cdot p(1-p) = p - y$. The `p(1−p)` terms cancel completely, which is one of the few places in deep learning where the algebra gets simpler rather than more ornate as you add layers of composition. This is why frameworks implement `BCEWithLogitsLoss`: the forward pass can compute a stable scalar loss from `z` directly using `log1p` identities, while the backward pass hands back `p − y` without ever dividing by a probability near zero. If you separate the steps, you must store `p` for the backward through sigmoid **and** evaluate `log p` when `p` is tiny; fused code avoids both the extra memory and the division hazard. When you inspect PyTorch autograd graphs, you will often see a single fused kernel at the end of classifiers — that is not micro-optimization alone, it is numerical hygiene.

From an information-theory viewpoint, BCE is the cross-entropy between the Bernoulli distribution implied by your model and the empirical label distribution. Minimizing BCE is equivalent to maximizing log-likelihood of the labels under the model's predicted Bernoulli parameters. That connection matters when you compare losses across papers: authors may write "negative log-likelihood" while code says `BCEWithLogitsLoss`, and both mean the same training signal if reductions match.

### 3.2 Step-by-step algebra for one sample

Start from $L = -[y \log \sigma(z) + (1-y)\log(1-\sigma(z))]$ with $\sigma = \sigma(z)$. The first derivative expands to $\frac{\partial L}{\partial z} = -\sigma'(z)\big(y/\sigma - (1-y)/(1-\sigma)\big)$. Substitute $\sigma'(z) = \sigma(1-\sigma)$ and distribute: $-\sigma(1-\sigma)\cdot(y/\sigma - (1-y)/(1-\sigma)) = -y(1-\sigma) + (1-y)\sigma$, which simplifies term by term to $-y + y\sigma + \sigma - y\sigma = \sigma - y = p - y$. With mean reduction over `n` elements, `∂L/∂z = (p − y) / n`. Run the scalar check from A1 on a single logit when you implement `BCEWithLogitsLoss.backward`: choose `z = 0.7`, `y = 1`, compute `p = σ(z) ≈ 0.668`, analytical gradient `(p−y)/1 ≈ −0.332`, and confirm `numerical_grad` matches within `1e-5`. That one-number test catches sign flips and forgotten mean factors faster than staring at a training curve.

Binary classification with multiple logits per sample (multi-label) applies the same per-entry `p − y` gradient independently across output dimensions because each label is a separate Bernoulli draw. Do not apply softmax across those dimensions unless labels are mutually exclusive within the group — spam-versus-not-spam and urgent-versus-not-urgent on the same email are independent events and want independent sigmoids, not a softmax that forces probabilities to sum to one.

```python
def sigmoid(z):
    z = np.clip(z, -500, 500)
    return 1.0 / (1.0 + np.exp(-z))

def bce_with_logits_backward(z, y):
    p = sigmoid(z)
    n = z.size
    return (p - y) / n   # shape matches z
```

---

## Part 4: Multi-Class — Softmax and Cross-Entropy

Multi-class classification uses a vector of logits `z ∈ ℝ^K` per sample and a one-hot target `y` (or integer class index for the stable implementation). The softmax head turns logits into a categorical distribution: $p_k = e^{z_k} / \sum_j e^{z_j}$. Categorical cross-entropy for one-hot `y` averages per-sample sums $L_{\text{CE}} = -\frac{1}{n_{\text{batch}}}\sum_{\text{samples}} \sum_k y_k \log p_k$, which collapses to $L = -\frac{1}{n_{\text{batch}}} \log p_c$ when class $c$ is the sole positive label. This is THE gradient A6 depends on: for each sample, the vector `∂L/∂z` equals `p − y`. The result looks deceptively like linear regression on probabilities, but it is the endpoint of a Jacobian calculation where off-diagonal softmax coupling cancels against the structure of cross-entropy. When you implement backprop by hand in A6, you will not re-derive this matrix every time — you will call `SoftmaxCEWithLogitsLoss.backward` and trust the vector shape `(N, K)` as the incoming gradient to the final linear layer.

Multi-class single-label problems are exactly where softmax belongs. The normalization forces competition among logits so that raising one class probability lowers others, which matches the generative story "exactly one correct category." If your labels can co-occur (tags on a document), softmax is the wrong head; independent sigmoids with BCE per tag are the standard fix. Getting this modeling choice wrong is worse than picking a suboptimal learning rate because the loss itself encodes an incorrect factorization of the label distribution.

### 4.1 Softmax Jacobian

Let $p = \text{softmax}(z)$. The Jacobian entries are $\frac{\partial p_i}{\partial z_j} = p_i(\delta_{ij} - p_j)$ where $\delta_{ij}$ is the Kronecker delta. Intuition: increasing `z_j` raises `p_j` directly through the exponent in the numerator, but also renormalizes every probability because the shared denominator grows. That coupling is why naive "derivative of log softmax" derivations look intimidating on paper yet collapse to `p − y` when paired with cross-entropy. The Jacobian is not sparse, but the loss gradient contracts it into a simple residual vector.

You can sanity-check the Jacobian on a three-class toy with `z = [0, 1, 2]`. Compute `p` with stable softmax, then finite-difference each `z_j` while holding others fixed to see rows of `∂p/∂z`. You should observe that rows sum to zero because softmax outputs sum to one — probability mass is conserved, so any local change reallocates rather than creates mass. That zero-sum structure is what ultimately produces the clean CE gradient.

### 4.2 Cross-entropy gradient (one-hot)

For a single sample, $L = -\sum_k y_k \log p_k$. With one-hot $y_c = 1$, the chain rule gives $\frac{\partial L}{\partial z_j} = -\frac{1}{p_c}\frac{\partial p_c}{\partial z_j}$ after all other $y_k$ terms vanish. Substitute the Jacobian entry $\partial p_c/\partial z_j = p_c(\delta_{cj} - p_j)$ to obtain $\frac{\partial L}{\partial z_j} = -(\delta_{cj} - p_j) = p_j - y_j$. Vector form for one-hot `y`: **`∂L/∂z = p − y`**. With mean reduction over a batch of `N` samples, divide each sample's vector by `N`.

```python
def softmax(z):
    z_shift = z - np.max(z, axis=-1, keepdims=True)  # stability — Part 5
    exp_z = np.exp(z_shift)
    return exp_z / np.sum(exp_z, axis=-1, keepdims=True)

def softmax_ce_backward(z, y_onehot):
    p = softmax(z)
    N = z.shape[0]
    return (p - y_onehot) / N
```

Integer-label APIs (like PyTorch `CrossEntropyLoss`) fuse softmax and CE without materializing one-hot `y`; the gradient w.r.t. logits is still `p − y_onehot` conceptually, with the true class index receiving the `-1` contribution in that sparse picture. Our `nn.py` implementation accepts integer `y` of shape `(N,)` for convenience and expands to one-hot internally during `backward`, which keeps the learner-facing API small while preserving the same mathematics you derived on paper.

Label smoothing is a common regularizer that replaces strict one-hot targets with `y' = (1−ε) y + ε/K`. The gradient becomes `p − y'` rather than `p − y`, softening overconfidence during training. You will not implement smoothing in this module, but you should recognize it as a direct edit to the `y` side of the `p − y` formula rather than a change to softmax itself.

---

## Part 5: Numerical Stability

### 5.1 Softmax overflow — naive vs stable

If `z = [1000, 1001, 1002]`, naive `exp(z)` overflows to `inf` in floating point, yet the softmax result should still be a valid probability vector because the largest exponent dominates after normalization. The max-subtraction trick uses the identity `softmax(z) = softmax(z − c)` for any constant `c`; choosing `c = max(z)` pulls every exponent into a non-positive range before exponentiation, which eliminates overflow while leaving the normalized output unchanged:

```python
import numpy as np

z = np.array([[1000., 1001., 1002.]])

# Naive — overflows. NumPy returns inf/nan with only a warning by default,
# so promote overflow to an error to make the failure explicit.
try:
    with np.errstate(over="raise", invalid="raise"):
        p_naive = np.exp(z) / np.exp(z).sum(axis=-1, keepdims=True)
    print("naive:", p_naive)
except FloatingPointError:
    print("naive: overflow")

# Stable
z_max = np.max(z, axis=-1, keepdims=True)
p_stable = np.exp(z - z_max) / np.exp(z - z_max).sum(axis=-1, keepdims=True)
print("stable:", p_stable)   # [0.090, 0.245, 0.665] — valid distribution
```

### 5.2 Log-sum-exp

Computing `log Σ_k exp(z_k)` appears in log-softmax and in stable CE. The log-sum-exp identity rewrites the sum as $\log\sum_k e^{z_k} = \max(z) + \log\sum_k e^{z_k - \max(z)}$, which prevents overflow by factoring out the largest exponent before exponentiating the rest. The same idea underlies log-softmax implementations that compute `log p_k = z_k − logsumexp(z)` without ever materializing tiny probabilities that would underflow when logged.

```python
def logsumexp(z, axis=-1):
    z_max = np.max(z, axis=axis, keepdims=True)
    return z_max + np.log(np.sum(np.exp(z - z_max), axis=axis, keepdims=True))
```

Log-softmax: `log p_k = z_k − logsumexp(z)`.

### 5.3 Stable BCE from logits

Stable classification training keeps two failure modes in mind at once: overflow in softmax exponentials and underflow in logarithms of probabilities that rounded to zero. Directly evaluating `log σ(z)` and `log(1−σ(z))` can lose precision for large `|z|` because both logs sit on steep tails where floating-point spacing between representable numbers widens. A standard stable form uses `log1p` and `max`:

```python
def bce_with_logits_forward(z, y):
    # per-element stable BCE (Goodfellow et al., Ch. 6; CS231n softmax notes)
    max_z = np.maximum(0.0, z)
    loss = max_z - z * y + np.log1p(np.exp(-np.abs(z)))
    return float(np.mean(loss))
```

Clip extreme logits only for `exp` in sigmoid when implementing separate steps; fused losses avoid computing `log p` from a tiny `p` directly. The clipping bounds (`±500` is common) are far from arbitrary — they are chosen so `exp` stays within floating-point range while changing `σ(z)` by less than machine epsilon relative to exactly saturated values. When you debug NaNs, search for `log(p)` applied outside fused kernels first; that is where underflow usually enters.

Training in float32 makes stability matter earlier than float64 classroom derivations suggest. A logits vector with values around `80` can already push `exp` toward overflow in fp32 accumulations inside reduction kernels. Mixed-precision training stacks (outside Block A) keep master weights in fp32 partly because loss computations are sensitive pinch points. Even here in pure NumPy, cast consciously: it is fine to keep `nn.py` in float64 for learning, but comment where a production port would insert fp32-safe kernels.

---

## Part 6: Output Heads — Summary Table

| Task | Output head | Loss | `∂L/∂z` (per element / vector, before batch mean) |
|------|-------------|------|---------------------------------------------------|
| Regression (real targets) | Linear (identity) | MSE | `(2/n)(z − y)` |
| Regression (robust) | Linear | Huber / smooth-L1 | piecewise — see Part 2.3 |
| Binary classification | Sigmoid `p=σ(z)` | BCE (fused) | `(p − y) / n` |
| Multi-class (mutually exclusive) | Softmax `p=softmax(z)` | Categorical CE (fused) | `(p − y) / N` per sample |

Hidden layers from A4 use ReLU, GELU, or SiLU — not sigmoid or softmax — because hidden units need non-saturating gradients, not normalized probabilities. The output head is chosen after the last hidden representation has done its feature work; the loss is chosen to match that head rather than the convenience of whichever API your framework imports first. When you sketch an MLP on paper, draw the head and loss as a boxed pair at the right edge of the diagram so you do not accidentally insert a softmax between two ReLU blocks "because classification."

Module A7's training loop will wire `MLP.forward()` into `Loss.forward()`, then `Loss.backward()` into backpropagation from A6, then an optimizer step on weights. The table above is the cheat sheet you should memorize before writing that loop: if the task column does not match your dataset labels, fix the modeling story before tuning learning rate. Engineers who inherit mis-specified heads spend weeks tuning optimizers for a problem the loss cannot represent.

---

## Part 7: Calibration

Calibration sits at the intersection of loss design and deployment policy, and it is easy to confuse with raw accuracy. A classifier can achieve low cross-entropy while producing **miscalibrated** probabilities: it might output `0.9` for positive predictions that are only correct 70% of the time. **Calibration** means predicted probabilities align with empirical accuracy — when the model says 80%, roughly 80% of those predictions should be correct.

**Reliability diagrams** bin predictions by confidence and plot accuracy vs. mean confidence per bin. **Expected calibration error (ECE)** summarizes bin-wise gaps (Guo et al., 2017). Deep networks trained with cross-entropy are often **over-confident** (sharp softmax peaks) even when accuracy is high.

**Temperature scaling** is a post-hoc fix: divide logits by a scalar `T > 0` before softmax at inference (or fit `T` on a held-out set). `T > 1` softens probabilities (less peaky); `T < 1` sharpens them. Only the logits scale; weights are unchanged.

```python
def softmax_with_temperature(z, T=1.0):
    return softmax(z / T)

# Illustration: sharp logits → over-confident
z = np.array([[5.0, 1.0, 0.5]])
p_cold = softmax(z)
p_warm = softmax_with_temperature(z, T=3.0)
print("T=1:", np.round(p_cold, 3))   # e.g. [0.971, 0.018, 0.011] — very peaky
print("T=3:", np.round(p_warm, 3))   # e.g. [0.673, 0.177, 0.150] — softer
```

Temperature scaling does not fix all calibration issues: class imbalance, covariate shift, and genuinely ambiguous examples need different tools. It is nonetheless the baseline post-training knob practitioners try first because it is one scalar fit on a validation set and often improves expected calibration error without retraining. Monitoring calibration in production — reliability diagrams sliced by cohort — is how teams discover that a model trained with the losses in this module still becomes over-confident when the live population drifts from the training distribution.

Expected calibration error approximates the weighted average absolute gap between bin confidence and bin accuracy. You do not need to implement ECE in `nn.py` for Block A, but you should know it exists when stakeholders ask whether "70% confidence" means anything operational. A model can be accurate yet miscalibrated, which matters for threshold policies in fraud, medicine, and capacity planning where decisions use probability cuts, not argmax labels.

---

## Part 8: Class Imbalance — Weighted CE and Focal Loss

When positives are rare, the gradient is dominated by easy negatives. **Class-weighted cross-entropy** multiplies each class's contribution by a weight `w_k`:

\[
L = -\frac{1}{n}\sum_i \sum_k w_k \, y_{ik} \log p_{ik}
\]

Set larger `w_k` for rare classes so their errors move parameters more aggressively. Weights can be inverse frequency or tuned on validation data.

**Focal loss** (Lin et al., 2017) down-weights easy examples:

\[
L_{\text{focal}} = -\frac{1}{n}\sum_i (1 - p_{t,i})^{\gamma} \log p_{t,i}
\]

where `p_t` is the model's probability assigned to the true class and `γ ≥ 0` is a focusing parameter. When `p_t → 1` (easy example), `(1−p_t)^γ → 0` shrinks the loss and gradient; hard misclassified examples retain strong signal. Class imbalance appears in fraud detection, medical screening, rare-fault prediction on fleets, and any tabular dataset where the positive label is scarce. The baseline softmax-plus-CE gradient still points in a sensible direction, but the magnitude on majority-class rows dominates mini-batch statistics, so the model learns to look accurate while ignoring minority recall. Weighted CE reweights the per-class channels in the sum; focal loss reweights entire examples based on how easy they are. Both are levers on the same `p − y` picture — they change how loudly each coordinate speaks during the backward pass, not the fundamental multiclass calculus.

When `γ = 0`, focal loss recovers ordinary cross-entropy. Larger `γ` focuses training on hard examples the model still misclassifies confidently. Focal loss became popular in dense object detection where background tiles vastly outnumber objects; for tabular or text classifiers with mild imbalance, weighted CE is often enough and is easier to explain to stakeholders. If you try focal loss, log the effective gradient magnitudes on easy negatives before and after — you should see them shrink when `γ` is doing its job.

Weighted CE modifies the target side of the story by scaling each class channel; focal loss modifies how much each **example** contributes based on difficulty. They can be combined in research code, but you should master the unfocused baselines in this module first so you can tell whether a deployment issue is modeling, data, or optimization. Class weights are frequently set to inverse frequency; that is a heuristic, not a theorem, and extreme weights can destabilize training if the learning rate is not adjusted.

---

## Part 9: Extending `nn.py` — The `Loss` Interface

Mirror the `Activation` interface from A4: each loss exposes `forward(logits, y) → scalar` and `backward(logits, y) → ∂L/∂logits` with the same shape as `logits`. Add the following to your cumulative `nn.py` (after `numerical_grad`, `Layer`, `MLP`, and `Activation` classes).

```python
# nn.py — Loss primitives (Module A5)
import numpy as np

class Loss:
    """Maps (logits, targets) → scalar loss; backward returns ∂L/∂logits."""
    def forward(self, logits, y):
        raise NotImplementedError

    def backward(self, logits, y):
        raise NotImplementedError


def _stable_softmax(z):
    z = np.asarray(z, dtype=float)
    z_shift = z - np.max(z, axis=-1, keepdims=True)
    exp_z = np.exp(z_shift)
    return exp_z / np.sum(exp_z, axis=-1, keepdims=True)


class MSELoss(Loss):
    """Regression: identity head, mean squared error."""
    def forward(self, logits, y):
        logits = np.asarray(logits, dtype=float)
        y = np.asarray(y, dtype=float)
        return float(np.mean((logits - y) ** 2))

    def backward(self, logits, y):
        logits = np.asarray(logits, dtype=float)
        y = np.asarray(y, dtype=float)
        n = logits.size
        return (2.0 / n) * (logits - y)


class BCEWithLogitsLoss(Loss):
    """Binary classification: fused sigmoid + BCE, stable forward."""
    def forward(self, logits, y):
        logits = np.asarray(logits, dtype=float)
        y = np.asarray(y, dtype=float)
        max_z = np.maximum(0.0, logits)
        loss = max_z - logits * y + np.log1p(np.exp(-np.abs(logits)))
        return float(np.mean(loss))

    def backward(self, logits, y):
        logits = np.asarray(logits, dtype=float)
        y = np.asarray(y, dtype=float)
        z = np.clip(logits, -500, 500)
        p = 1.0 / (1.0 + np.exp(-z))
        n = logits.size
        return (p - y) / n


class SoftmaxCEWithLogitsLoss(Loss):
    """Multi-class: fused softmax + CE; y may be integer labels (N,) or one-hot (N,K)."""
    def forward(self, logits, y):
        logits = np.asarray(logits, dtype=float)
        y = np.asarray(y)
        if y.ndim == 1:
            y_oh = np.zeros_like(logits)
            y_oh[np.arange(logits.shape[0]), y.astype(int)] = 1.0
            y = y_oh
        # stable log-softmax via log-sum-exp (Part 5.2) — consistent with the (p − y) backward,
        # no arbitrary clipping
        z_max = np.max(logits, axis=-1, keepdims=True)
        log_sum_exp = z_max + np.log(np.sum(np.exp(logits - z_max), axis=-1, keepdims=True))
        log_p = logits - log_sum_exp
        per_sample = -np.sum(y * log_p, axis=-1)
        return float(np.mean(per_sample))

    def backward(self, logits, y):
        logits = np.asarray(logits, dtype=float)
        y = np.asarray(y)
        if y.ndim == 1:
            y_oh = np.zeros_like(logits)
            y_oh[np.arange(logits.shape[0]), y.astype(int)] = 1.0
            y = y_oh.astype(float)
        else:
            y = y.astype(float)
        p = _stable_softmax(logits)
        N = logits.shape[0]
        return (p - y) / N


def check_loss_grad(loss_cls, logits, y, name, eps=1e-5):
    """Finite-difference check for any Loss subclass."""
    loss_obj = loss_cls()

    def scalar_loss(flat):
        shaped = flat.reshape(logits.shape)
        return loss_obj.forward(shaped, y)

    ana = loss_obj.backward(logits, y)
    num = numerical_grad(scalar_loss, logits.ravel(), eps=eps).reshape(logits.shape)
    err = float(np.max(np.abs(ana - num)))
    status = "PASS" if err < 1e-4 else "FAIL"
    print(f"[{status}] {name:22s} max abs error: {err:.6e}")
    return err < 1e-4


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    ok = True
    ok &= check_loss_grad(MSELoss, rng.standard_normal((4, 2)), rng.standard_normal((4, 2)), "MSELoss")
    ok &= check_loss_grad(BCEWithLogitsLoss, rng.standard_normal((6, 1)), rng.integers(0, 2, (6, 1)), "BCEWithLogitsLoss")
    ok &= check_loss_grad(SoftmaxCEWithLogitsLoss, rng.standard_normal((5, 3)), rng.integers(0, 3, 5), "SoftmaxCEWithLogitsLoss")
    assert ok, "loss gradient check failed"
    print("All loss gradient checks passed.")
```

Running the `__main__` block should print three `PASS` lines with max absolute error near `1e-11` for float64 test tensors — the same order of magnitude you saw for activations in A4. `SoftmaxCEWithLogitsLoss.forward` uses the same log-sum-exp identity from Part 5.2 rather than clipping probabilities before `log`, so forward and backward stay aligned under widely separated logits. This is the contract A6 expects: `Loss.backward` returns the exact seed for backprop through the final linear layer. Keep the `check_loss_grad` helper beside `numerical_grad` in `nn.py`; you will reuse the pattern whenever you add a custom loss term in later engineering modules.

Mirror the `Activation` interface style from A4: store whatever forward needs for backward, but prefer recomputing cheap quantities like `p = softmax(z)` in `backward` rather than caching large tensors unless profiling proves you need the cache. Loss objects are stateless aside from reduction hyperparameters in this teaching framework; production frameworks sometimes fuse loss+backward into one kernel call for speed. Your educational version stays readable first.

---

## Part 10: Bridging to A6, A7, and PyTorch Later

Module A6 will take `grad_out = loss.backward(logits, y)` and propagate it through the final `Layer` using the weight matrix transpose and activation local derivatives from A4. The only new calculus in A6 is applying the chain rule through `Z = A_prev @ W + b`; the loss seed you derived here is the boundary condition that makes that recursion terminate at the correct value. If `grad_out` has the wrong shape or sign, every `grad_W` in the network will be wrong even when the forward cache is perfect.

Module A7 will wrap forward, loss, backward, and weight updates into a training loop on a toy dataset. You will finally see loss curves descend when the pieces align. Before that moment, treat each component as a separately tested module: forward shapes from A3, activations from A4, losses from A5, backprop from A6. The discipline feels slower than importing `torch.nn`, but when a loss looks flat you will know which finite-difference check to run.

When you later read PyTorch, map `torch.nn.CrossEntropyLoss` to `SoftmaxCEWithLogitsLoss` here, `torch.nn.BCEWithLogitsLoss` to our binary class, and `torch.nn.MSELoss` to `MSELoss`. The naming is intentionally parallel. Autograd will hide the `p − y` algebra, but you should still recognize it in debugging hooks when you print `loss.grad_fn` metadata on toy graphs.

Study habits that pay off in the next two modules: keep a single notebook cell that forward-passes a toy MLP, evaluates each loss, prints `loss.backward` shapes, and finite-checks one coordinate whenever you change reduction or dtype. Re-derive `p − y` on paper once per week until it feels automatic. When you explain your choices to teammates, lead with the Part 6 table row for your task — head, loss, gradient — before discussing optimizers or learning rates. That ordering prevents the common meeting failure mode where infrastructure tuning masks a mis-specified output layer.

The cumulative `nn.py` file should now contain `numerical_grad` from A1, `Layer` and `MLP` from A2–A3, `Activation` subclasses from A4, and `Loss` subclasses from this module. Resist splitting into multiple files until Block A ends; the pedagogical point is that a few hundred lines of NumPy can express the entire training boundary without hiding derivatives inside a compiled extension. You are one backward pass away from closing the loop.

---

## Did You Know?

- **Cross-entropy predates deep learning in information theory:** Shannon entropy and KL divergence motivate CE as "how many nats of surprise" your predicted distribution assigns to the true label (Goodfellow, Bengio & Courville, *Deep Learning*, Ch. 6).
- **The `p − y` gradient is why softmax + CE is universal:** CS231n and d2l.ai both emphasize the fused form; separate softmax then `log p` costs more and divides by small probabilities.
- **Huber loss appeared in robust statistics long before neural nets:** Peter J. Huber's 1964 work on M-estimators motivates the same smooth-L1 piecewise used in Fast R-CNN bounding-box regression.
- **Temperature scaling won the ImageNet calibration benchmark** in Guo et al. (2017) with a single scalar `T` — often beating far more complex post-hoc methods on held-out data.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| BCE on probabilities with logits already passed through sigmoid | Saturated `p` near 0/1 → `log p` blows up; gradients vanish or NaN | Use `BCEWithLogitsLoss` on raw logits; backward uses `p−y` stably |
| Softmax before `log` in separate steps | Numerical underflow in `log p_k` | Fuse softmax+CE; use log-sum-exp / max subtraction |
| Mean vs sum reduction mismatch | Changing batch size changes gradient scale; learning rate "stops working" | Pick mean or sum; divide `∂L/∂z` consistently; document in `nn.py` |
| Applying MSE to classification outputs | Unbounded logits penalized quadratically — not a valid probability model | Use BCE (binary) or softmax+CE (multiclass) |
| Sigmoid on multi-class outputs | Outputs do not sum to 1; mutually exclusive classes mis-modeled | One softmax over `K` logits |
| Ignoring class imbalance only via accuracy | Model predicts majority class always; loss looks "okay" | Weighted CE or focal loss; monitor per-class recall |
| Evaluating calibration on training set | Over-confident metrics look fine on data the model memorized | Reliability diagrams on held-out data; temperature fit on validation |

---

## Quiz

1. **Why does fusing sigmoid and BCE simplify `∂L/∂z`?**
   <details>
   <summary>Answer</summary>
   BCE contributes a factor `1/(p(1−p))` w.r.t. `p`, while sigmoid's derivative is `p(1−p)`. Multiplying them cancels the denominator, leaving `p − y`. You avoid dividing by near-zero `p` and save a backward pass through an explicitly stored probability.
   </details>

2. **For one-hot `y` and `p = softmax(z)`, what is `∂L/∂z`?**
   <details>
   <summary>Answer</summary>
   `p − y` (vector). The softmax Jacobian and the `1/p_k` term from cross-entropy cancel the off-diagonal coupling, leaving a remarkably sparse-looking gradient that is actually the full vector difference.
   </details>

3. **When should you prefer Huber loss over MSE?**
   <details>
   <summary>Answer</summary>
   When outliers dominate MSE gradients but you still want smooth optimization near zero — Huber behaves like MSE for small residuals and like MAE for large ones, controlled by `δ`.
   </details>

4. **What does temperature scaling change, and what does it leave fixed?**
   <details>
   <summary>Answer</summary>
   It divides logits by `T` before softmax at inference (or evaluation), softening (`T>1`) or sharpening (`T<1`) probabilities. Trained weights are unchanged; only the calibration of reported probabilities improves if `T` is fit on validation data.
   </details>

5. **What is the max-subtraction trick for softmax?**
   <details>
   <summary>Answer</summary>
   `softmax(z) = softmax(z − max(z))`. Subtracting the max logit prevents `exp(z_k)` from overflowing without changing the result mathematically, because the same factor `exp(−max)` appears in numerator and denominator.
   </details>

6. **How does focal loss change learning on easy examples?**
   <details>
   <summary>Answer</summary>
   The factor `(1 − p_t)^γ` shrinks the loss and gradient when the true class probability `p_t` is already high, letting hard misclassified examples dominate updates.
   </details>

7. **Walk through the fused BCE gradient: why does `∂L/∂p` times `∂p/∂z` simplify to `p − y`?**
   <details>
   <summary>Answer</summary>
   `∂L/∂p = (p−y)/(p(1−p))` and `∂p/∂z = p(1−p)` for sigmoid. Multiplying cancels `p(1−p)`, leaving `p−y`. This is the algebraic reason fused `BCEWithLogitsLoss` backward does not divide by probabilities.
   </details>

8. **What is expected calibration error measuring, and how does temperature scaling help?**
   <details>
   <summary>Answer</summary>
   ECE summarizes how far predicted confidences diverge from empirical accuracies across probability bins. Temperature scaling divides logits by a fitted `T` before softmax at evaluation time, softening over-confident peaks so stated probabilities better match observed hit rates on held-out data.
   </details>

---

## Hands-On Exercise

**Task:** Add `MSELoss`, `BCEWithLogitsLoss`, and `SoftmaxCEWithLogitsLoss` to your `nn.py` using the `Loss` interface in Part 9. Run the `check_loss_grad` harness for each class and confirm `PASS` with max absolute error below `1e-4`.

**Steps:**
1. Copy the Part 9 code into your cumulative `nn.py` below the `Activation` classes from A4.
2. Run `.venv/bin/python nn.py` from your exercise directory and capture the three `PASS` lines.
3. Demonstrate softmax instability: evaluate naive `exp` softmax on `z = [[1000, 1001, 1002]]` and compare to `_stable_softmax` — record that only the stable version returns a valid probability vector.
4. For a binary toy with `z = np.array([[0.0], [2.0]])` and `y = np.array([[1.0], [0.0]])`, compute `BCEWithLogitsLoss().backward(z, y)` by hand (`p−y`, mean-reduced) and match the code output.
5. From the Part 6 table, write one sentence each for a regression, binary, and multiclass project you care about naming the correct head, loss, and `∂L/∂z` pattern.
6. Run the Part 7 temperature demo on `z = [[5.0, 1.0, 0.5]]` with `T=1` and `T=3`; note how softmax peaks soften and relate that to calibration intuition.

**Success criteria:**
- [ ] All three loss classes implement `forward` → scalar and `backward` → same shape as `logits`
- [ ] Finite-difference checks pass for MSE, BCE-with-logits, and softmax-CE-with-logits
- [ ] You can state the fused binary and multiclass `∂L/∂z` formulas without looking (`p−y`)
- [ ] Stable softmax demo shows overflow or `inf` for naive code and finite probabilities for stable code
- [ ] Part 6 task→head→loss mapping completed for three hypothetical projects (regression, binary, multiclass)
- [ ] Temperature scaling demo run; you can explain in one paragraph when weighted CE or focal loss would replace plain CE

---

## Key Takeaways

- A loss maps predictions and targets to a **scalar** training objective; `∂L/∂z` at the logits is the **seed gradient** for backpropagation in A6.
- Regression uses a **linear head** with MSE (or Huber for robustness); classification uses **sigmoid+BCE** (binary) or **softmax+CE** (multiclass), fused for stability.
- The fused gradients **`p − y`** (binary and one-hot multiclass) are not shortcuts — they are exact consequences of the chain rule that cancel awkward terms.
- **Numerical stability** (max-subtraction, log-sum-exp, `log1p` BCE) is required for real training, not an advanced topic.
- **Calibration** and **class imbalance** (weighted CE, focal loss) adjust probability interpretation and gradient emphasis after you master the baseline losses.
- Your `nn.py` `Loss` interface completes the output boundary: forward cache from A3/A4, loss backward here, full backprop next in A6, training loop in A7.

---

## Sources

- [CS231n: Linear Classification — softmax and cross-entropy](https://cs231n.github.io/linear-classify/) — softmax scores, cross-entropy loss, gradient intuition.
- [CS231n: Neural Networks Part 1](https://cs231n.github.io/neural-networks-1/) — activation and output layers in MLP context.
- [d2l.ai: Softmax regression](https://d2l.ai/chapter_linear-classification/softmax-regression.html) — softmax, CE, stable implementation patterns.
- [d2l.ai: Loss functions](https://d2l.ai/chapter_multilayer-perceptrons/loss-functions.html) — regression and classification losses.
- [Goodfellow, Bengio & Courville — Ch. 6: Deep Feedforward Networks](https://www.deeplearningbook.org/contents/mlp.html) — cross-entropy and output units.
- [Lin et al. (2017) — Focal Loss for Dense Object Detection](https://arxiv.org/abs/1708.02002) — focal loss definition and motivation.
- [Guo et al. (2017) — On Calibration of Modern Neural Networks](https://arxiv.org/abs/1706.04599) — reliability diagrams, ECE, temperature scaling.
- [NumPy: `numpy.log1p`](https://numpy.org/doc/stable/reference/generated/numpy.log1p.html) — stable logarithm near zero.
- [Karpathy: micrograd](https://github.com/karpathy/micrograd) — cumulative micro-framework pedagogy mirrored in Block A `nn.py`.
- [Karpathy: Yes you should understand backprop](https://karpathy.medium.com/yes-you-should-understand-backprop-e2f06eab496b) — why manual loss gradients still matter for practitioners.
- [Nielsen: Neural Networks and Deep Learning — Ch. 3](http://neuralnetworksanddeeplearning.com/chap3.html) — cross-entropy motivation and softmax intuition.

---

## Learner check

> Loss Functions & Output Heads — Block A module A5; fused sigmoid+BCE and softmax+CE gradients collapse to `p − y`; stable log-sum-exp; `Loss` interface in `nn.py`; precedes Backprop by Hand (A6).

---

## Next Module

Continue the from-scratch arc with **[Backprop by Hand for Dense Nets](/ai-ml-engineering/deep-learning/module-1.1.6-backprop-by-hand-dense-nets/)** — it consumes the `∂L/∂logits` you derived here and propagates it through the `MLP` cache (A3) using the matrix chain rule.
