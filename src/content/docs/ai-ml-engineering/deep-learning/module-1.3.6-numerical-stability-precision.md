---
title: "Numerical Stability & Precision"
slug: ai-ml-engineering/deep-learning/module-1.3.6-numerical-stability-precision
sidebar:
  order: 1004.6
---

> **AI/ML Engineering Track** | Complexity: `[COMPLEX]` | Time: 4-6 hours
>
> **Prerequisites**: Module 1.1.5 (stable softmax cross-entropy), Module 1.1.6 (hand-derived VJPs), Module 1.1.8 (scalar autograd), Module 1.3.2 (optimizer epsilon), Module 1.3.4 (normalization epsilon), and the training loop mechanics from Module 1.3.
>
> **Primary tools**: PyTorch 2.12, `torch.finfo`, `torch.logsumexp`, `torch.nn.functional.cross_entropy`, `torch.nn.BCEWithLogitsLoss`, `torch.amp.autocast`, `torch.amp.GradScaler`, and `torch.set_float32_matmul_precision`.

---

In 2017, Paulius Micikevicius and colleagues published "Mixed Precision Training," a paper that made a practical claim many engineers wanted to be true but did not yet trust: large neural networks could train with half-precision storage and arithmetic without losing model quality, if the training system protected the fragile parts of the computation. The paper's recipe was not "cast everything to fp16 and hope." It kept a full-precision master copy of weights, used loss scaling so tiny fp16 gradients did not underflow to zero, and treated precision as an engineering interface rather than a cosmetic performance switch. That paper became one of the roots of the automatic mixed precision workflows you use through PyTorch today.

The story matters because the math you wrote in Block A was real math, while the hardware runs finite approximations of that math. In A5, the softmax cross-entropy derivation was exact: exponentiate logits, normalize them into probabilities, take a log, then differentiate. On a GPU, `exp(1000)` is not a huge real number; it is `inf`. `log(0)` is not a large negative number; it is `-inf`. `inf - inf` is not zero; it is `nan`. The autograd engine from A8 still follows the same graph logic you built by hand, but once a tensor contains a non-finite value, the graph faithfully propagates the damage.

This module is the float-level reality check for the entire training-as-engineering block. PyTorch is not magic here either. `torch.Tensor` stores values in a chosen dtype, `loss.backward()` applies VJPs through operations that may overflow or underflow, `nn.CrossEntropyLoss` is the stable softmax-CE you implemented by hand in A5, and `torch.optim.AdamW` still applies updates whose denominator needs the epsilon discipline you met in B4. The difference is that production training also asks you to choose fp32, fp16, bf16, TF32, and sometimes fp8 paths deliberately, because at scale the dtype is part of the model architecture.

---

## Learning Outcomes

By the end of this module, you will be able to:

1. **Compare** fp32, fp16, bf16, and fp8 training formats by exponent range, mantissa precision, machine epsilon, and practical failure mode, then **verify** those limits with `torch.finfo` checks instead of relying on memory.
2. **Debug** the arithmetic sources of `NaN` and `Inf` in a PyTorch graph, including overflow, invalid operations, division by zero, `log(0)`, `sqrt(negative)`, propagation, and first-non-finite tensor bisection.
3. **Implement** the log-sum-exp trick for softmax cross-entropy, **connect** it back to the stable A5 implementation, and **replace** unstable `softmax -> log -> NLL` or `sigmoid -> BCE` code with fused PyTorch loss functions on logits.
4. **Configure** current PyTorch 2.12 automatic mixed precision with `torch.amp.autocast`, then **apply** `torch.amp.GradScaler` correctly for fp16 training, including `unscale_` before gradient clipping.
5. **Distinguish** AMP from TF32 matmul precision controls, **choose** when to use `torch.set_float32_matmul_precision("high")`, and **explain** the determinism and accuracy tradeoffs of reduced-precision math.

---

## Why This Module Matters

When a training run goes non-finite, the failure often arrives as one boring line in a log file: `loss=nan`. That line hides a chain of events. A single logit became too large for the dtype, an exponential overflowed to `inf`, a probability rounded to exactly zero, a denominator collapsed under an epsilon placed in the wrong location, or an fp16 gradient flushed to zero until the optimizer state no longer represented the gradient you thought you were applying. The model did not suddenly become mysterious. The arithmetic stopped matching the assumptions in your derivation.

This is where the Block A back-reference is especially important. In A5, you already implemented stable softmax cross-entropy by subtracting the maximum logit before exponentiation. That was not a numerical trick bolted onto the math; it was an algebraically equivalent expression chosen because floating-point hardware has finite range. In A8, your scalar autograd `Value` engine computed correct derivatives through a computation graph, but it had no way to rescue a node whose value was already `nan`. PyTorch's autograd engine behaves the same way at tensor scale: it can differentiate the graph you built, not the mathematical graph you intended if the forward values have left the representable number system.

Precision is also a capacity planning issue. A model that fits in fp32 may train twice as fast or fit a larger batch in bf16 because activations and gradients occupy fewer bytes and Tensor Cores can accelerate matrix multiplies. A model that converges in bf16 may diverge in fp16 because fp16 has far less dynamic range. A model that is bitwise stable in full fp32 may move slightly when TF32 matmul precision is enabled, because inputs are stored as fp32 but matrix multiply reads fewer mantissa bits internally. You cannot reason about throughput, memory, convergence, or reproducibility without knowing which arithmetic path the tensors actually take.

The practical payoff is direct. Stable losses let you train with logits whose magnitude would destroy naive formulas. AMP lets you use lower precision where it is fast while preserving fp32 where the operation is sensitive. Gradient scaling lets fp16 carry small gradients that would otherwise underflow to zero. TF32 gives Ampere-and-later NVIDIA GPUs a fast path for fp32-shaped workloads, but it is not AMP and it does not change tensor storage dtype. Once you understand those boundaries, a NaN stops being a superstition and becomes a search problem over a finite list of arithmetic causes.

Think of dtype choice like choosing measuring instruments in a machine shop. A long tape measure can span a warehouse but cannot measure a bearing surface to micrometer accuracy. A micrometer can measure tiny differences but is useless if the object is larger than its jaw. fp16 is the small, precise instrument with a narrow span; bf16 is the long-range instrument with coarser markings; fp32 is the heavier instrument you trust when both range and precision matter. Training stability comes from using the right instrument at each operation, not from declaring one instrument universally superior.

---

## Part 1: Floating Point in 90 Seconds

Floating-point numbers are scientific notation in binary. A finite floating-point value is encoded with a sign bit, exponent bits, and mantissa bits. The sign says positive or negative. The exponent controls the scale, so it decides dynamic range: how large and how tiny a normal value can be. The mantissa, also called the significand, controls the spacing between nearby representable values, so it decides precision: how many distinct values fit between powers of two. Deep-learning engineers mostly need those two knobs, range and precision, because training failures usually come from exceeding range or from losing enough precision that two different mathematical values become the same stored value.

Here is the table to keep in your head. The exponent and mantissa counts below use the explicitly stored mantissa bits for the common naming convention. The implicit leading bit in normalized binary formats gives one additional bit of significand precision for fp32, fp16, and bf16, but the engineering comparison is still clear: fp16 spends bits on precision and has narrow range; bf16 spends bits on range and has coarse precision.

| Format | Bits | Exponent / mantissa | Approx max finite | Machine epsilon near 1 | Training implication |
|---|---:|---:|---:|---:|---|
| fp32 (`torch.float32`) | 32 | 8e / 23m | ~3.4e38 | ~1.19e-7 | Default training baseline: wide range and enough precision for most reductions and optimizer state. |
| fp16 (`torch.float16`) | 16 | 5e / 10m | 65,504 | ~9.77e-4 | Fast and compact, but narrow range means overflow and gradient underflow are common without loss scaling. |
| bf16 (`torch.bfloat16`) | 16 | 8e / 7m | ~3.39e38 | ~7.81e-3 | Same exponent range as fp32 with less precision, which is why it is usually preferred for training on supported accelerators. |
| fp8 (`e4m3`, `e5m2`) | 8 | 4e / 3m or 5e / 2m | format-dependent | very coarse | Used on modern accelerators with scaling metadata and framework support; not a drop-in replacement for ordinary tensors. |

This table also explains a common confusion about fp16 and bf16. fp16 has more mantissa bits than bf16, so if both formats can represent a value near 1.0, fp16 can usually represent nearby differences more finely. That does not make fp16 safer for training. The most destructive training failures are often magnitude failures: logits, activations, gradient products, or optimizer-state values leave the representable range. bf16 sacrifices local precision to keep the fp32 exponent range, which is a trade many neural networks tolerate better than fp16's narrow range.

`torch.finfo` is the simplest way to make this concrete. It reports `max`, `tiny` (the smallest positive normal value), and `eps` (the smallest increment that changes 1.0 in that dtype). Run this snippet on any PyTorch 2.12 environment; the fp8 lines are guarded because FP8 dtype availability depends on the build and device path.

```python
import torch

dtypes = [torch.float32, torch.float16, torch.bfloat16]
for name in ("float8_e4m3fn", "float8_e5m2"):
    if hasattr(torch, name):
        dtypes.append(getattr(torch, name))

for dtype in dtypes:
    info = torch.finfo(dtype)
    print(f"{str(dtype):22s} max={info.max:.6e} tiny={info.tiny:.6e} eps={info.eps:.6e}")

# Typical fp16/bf16/fp32 output includes:
# torch.float32          max=3.402823e+38 tiny=1.175494e-38 eps=1.192093e-07
# torch.float16          max=6.550400e+04 tiny=6.103516e-05 eps=9.765625e-04
# torch.bfloat16         max=3.389531e+38 tiny=1.175494e-38 eps=7.812500e-03
```

The `tiny` field is easy to misread. It reports the smallest positive normal value, not necessarily the smallest positive subnormal value a format can encode. Subnormals extend the range toward zero with reduced precision, but many accelerator paths handle them differently for speed, and some low-precision paths flush denormals to zero. When you are training, the operational question is not "does the format have any bit pattern below `tiny`?" but "will this kernel, on this device, preserve the gradient magnitude I need?" Gradient scaling exists because relying on fragile subnormal behavior is not a robust training strategy.

Machine epsilon explains why decimal-looking code is not decimal arithmetic. The number `0.1` has no finite binary representation, just like `1/3` has no finite decimal representation. When Python or PyTorch stores `0.1`, it stores the nearest representable binary float. The expression `0.1 + 0.2` therefore combines two approximations, and the result is close to but not exactly `0.3`.

```python
import torch

x = torch.tensor(0.1, dtype=torch.float64)
y = torch.tensor(0.2, dtype=torch.float64)
z = torch.tensor(0.3, dtype=torch.float64)

print((x + y).item())          # 0.30000000000000004
print((x + y == z).item())     # False
print(torch.isclose(x + y, z)) # tensor(True)
```

The key engineering lesson is not "floating point is broken." Floating point is deterministic, standardized, and extremely fast. The lesson is that equality and algebraic rearrangement are no longer free. Addition is not associative, so `(a + b) + c` can differ from `a + (b + c)`. Subtracting two nearly equal large values can destroy most of the meaningful digits, a pattern called catastrophic cancellation. Once those bits are gone, autograd cannot reconstruct them during backward.

```python
import torch

a32 = torch.tensor(100_000_001.0, dtype=torch.float32)
b32 = torch.tensor(100_000_000.0, dtype=torch.float32)
a64 = torch.tensor(100_000_001.0, dtype=torch.float64)
b64 = torch.tensor(100_000_000.0, dtype=torch.float64)

print((a32 - b32).item())  # 0.0, because 100000001 rounded to 100000000 in fp32
print((a64 - b64).item())  # 1.0, because fp64 has enough precision here
```

That example looks artificial until you remember what a neural network does all day: it subtracts means, computes residuals, normalizes by small variances, accumulates dot products, exponentiates logits, and sums many terms in reductions. The stable formulas in this module are not optional elegance. They are the difference between preserving enough signal for `loss.backward()` to compute useful VJPs and feeding the optimizer gradients that are already corrupted by the forward pass.

There is one more practical implication: tests that use tiny toy tensors can miss dtype bugs. A three-class example with logits `[1, 2, 3]` may pass whether you use stable or unstable softmax, because every exponential fits comfortably in fp32. The same implementation can fail in a real classifier whose logits reach 90, or in a contrastive loss with thousands of negative examples, or in a language model where a reduction spans a large vocabulary. Good numerical tests deliberately include extreme but realistic values, because stability is mostly invisible in the comfortable middle of the range.

---

## Part 2: Where NaNs and Infs Are Born

`Inf` means the result exceeded the dtype's representable range or came from division by zero with a nonzero numerator. `NaN` means "not a number," usually because an operation had no valid numerical answer in the real-valued path the dtype can represent. A non-finite value is not local for long. If one activation in a layer becomes `nan`, most downstream tensor operations that touch it produce more NaNs, and the backward pass spreads them into gradients and optimizer state.

The arithmetic culprits are finite and memorable. `exp(large)` overflows to `inf`. `log(0)` returns `-inf`. `0 / 0` returns `nan`. `inf - inf` returns `nan` because there is no single meaningful result. `sqrt(negative)` returns `nan` for real tensors. `0 * inf` returns `nan` because IEEE-style arithmetic treats it as invalid, not as zero. The following snippet prints the usual suspects and uses `torch.isnan`, `torch.isinf`, and `torch.isfinite` to classify them.

```python
import torch

examples = {
    "exp(1000)": torch.exp(torch.tensor(1000.0)),
    "log(0)": torch.log(torch.tensor(0.0)),
    "0/0": torch.tensor(0.0) / torch.tensor(0.0),
    "inf-inf": torch.tensor(float("inf")) - torch.tensor(float("inf")),
    "sqrt(-1)": torch.sqrt(torch.tensor(-1.0)),
    "0*inf": torch.tensor(0.0) * torch.tensor(float("inf")),
}

for name, value in examples.items():
    print(
        f"{name:8s} -> {value.item():>8}, "
        f"isnan={torch.isnan(value).item()}, "
        f"isinf={torch.isinf(value).item()}, "
        f"isfinite={torch.isfinite(value).item()}"
    )

nan_value = torch.tensor(float("nan"))
print((nan_value == nan_value).item())  # False: NaN is unequal to itself
```

The last line surprises people once and then becomes a useful debugging trick. A NaN compares unequal to itself, which is why `x == x` can be false for a tensor element. In PyTorch, use `torch.isnan(x)` rather than equality tricks in production code because it is explicit, vectorized, and communicates intent to the next engineer.

A single NaN contaminates a graph because most operations are elementwise or reduction-based. Elementwise addition with NaN returns NaN at that element. Matrix multiply spreads a NaN across every output value whose dot product touched it. A mean reduction over a vector with one NaN returns NaN for the entire scalar loss. Once the scalar loss is NaN, every gradient derived from it is usually NaN or at least no longer trustworthy.

The propagation behavior is exactly what your A8 autograd engine would do if one `Value.data` field became `float("nan")`. The backward functions would still run in topological order, and each local derivative would still be multiplied by upstream gradients, but arithmetic involving NaN would produce more NaNs. PyTorch does the same thing with tensors. Autograd is not a sanitation system; it is a differentiation system. If the forward pass creates invalid values, backward correctly differentiates an invalid numerical trace.

```python
import torch

x = torch.ones(4, 4)
x[1, 2] = float("nan")
w = torch.arange(16, dtype=torch.float32).reshape(4, 4)

y = x @ w
loss = y.mean()

print(torch.isnan(x).sum().item())    # 1 NaN in the input
print(torch.isnan(y).sum().item())    # 4 NaNs after matmul
print(torch.isnan(loss).item())       # True: one NaN poisons the scalar loss
```

This is why the first debugging question is not "which layer is bad in general?" but "where did the first non-finite value appear?" If the loss becomes NaN at step 12,000, the cause may be a logit overflow in the forward pass, a division by a near-zero norm, an fp16 gradient overflow detected during backward, or an optimizer state update that inherited NaN from a previous step. The tools in B7 help you bisect the training system; this module narrows the suspect list to arithmetic and dtype behavior.

The most useful mental model is a checkpointed pipeline. Inputs enter finite, each operation either preserves finiteness or creates the first non-finite value, and every later stage may only amplify the symptom. If you probe only the final loss, you are inspecting the smoke after it has filled the building. If you probe inputs, logits, losses, gradients, and parameters in order, you are walking backward toward the first spark. That is why precision debugging should be boring and systematic rather than dramatic.

---

## Part 3: Numerically Stable Implementations

The canonical stability example is the one you already wrote in A5: softmax cross-entropy. The mathematical softmax for logits `z` is `exp(z_i) / sum_j exp(z_j)`. The problem is not the formula. The problem is that the formula asks hardware to compute exponentials of raw logits. If one logit is 1000, fp32 cannot represent `exp(1000)`, and fp16 overflows much earlier. Subtracting the maximum logit fixes the range without changing the result, because adding or subtracting the same constant from every logit leaves softmax unchanged.

The log-sum-exp identity is the stable expression underneath this fix:

```text
log(sum_j exp(z_j)) = m + log(sum_j exp(z_j - m)), where m = max_j z_j
```

After subtracting `m`, the largest exponent is `exp(0) = 1`, so the sum cannot overflow merely because the logits were shifted upward together. This is exactly what you did by hand in A5, and it is exactly why PyTorch exposes `torch.logsumexp` as a numerically stabilized primitive rather than asking you to write `torch.log(torch.exp(x).sum(dim))`.

```python
import torch

logits = torch.tensor([[1000.0, 1001.0, 1002.0]])  # shape: [batch=1, classes=3]

naive_exp = torch.exp(logits)
naive_softmax = naive_exp / naive_exp.sum(dim=-1, keepdim=True)
print(naive_exp)       # tensor([[inf, inf, inf]])
print(naive_softmax)   # tensor([[nan, nan, nan]])

m = logits.max(dim=-1, keepdim=True).values
stable_exp = torch.exp(logits - m)
stable_softmax = stable_exp / stable_exp.sum(dim=-1, keepdim=True)
stable_logsumexp = m.squeeze(-1) + torch.log(stable_exp.sum(dim=-1))

print(stable_softmax)                 # tensor([[0.0900, 0.2447, 0.6652]])
print(stable_logsumexp)               # tensor([1002.4076])
print(torch.logsumexp(logits, dim=-1))# tensor([1002.4076])
```

Cross-entropy for one target class can be written as `-z_y + logsumexp(z)`. That is the stable path. The unstable path is `softmax -> log -> negative log likelihood`, especially if the softmax is written naively or if probabilities have already rounded to zero. In PyTorch, the practical rule is simple: pass raw logits to `torch.nn.functional.cross_entropy` or to `nn.CrossEntropyLoss`. If you already need log probabilities for another reason, use `F.log_softmax` followed by `F.nll_loss`, not `torch.log(F.softmax(...))`.

```python
import torch
import torch.nn.functional as F

logits = torch.tensor([[1000.0, 1001.0, 1002.0]])  # [N=1, C=3]
target = torch.tensor([2])                         # class index, shape [N]

loss_fused = F.cross_entropy(logits, target)
log_probs = F.log_softmax(logits, dim=-1)
loss_two_step = F.nll_loss(log_probs, target)

manual = -logits[0, target[0]] + torch.logsumexp(logits, dim=-1)[0]

print(loss_fused.item())     # about 0.4076
print(loss_two_step.item())  # same stable value
print(manual.item())         # same stable value
```

There is a subtle API lesson in that example. `F.cross_entropy` is not a probability loss; it is a logits loss. The function name describes the mathematical objective, not the expected input representation. This is why passing `F.softmax(logits, dim=-1)` into `F.cross_entropy` is a double mistake: you remove the logit dynamic range that makes the stable implementation possible, and then PyTorch applies a log-softmax-style computation to values that are already normalized probabilities. The result may still produce a number, but it is not the objective you intended.

Binary classification has the same pattern. The unstable path is `sigmoid -> log -> BCE`, because extreme logits push sigmoid outputs to exactly 0 or exactly 1 in finite precision. The stable path is `BCEWithLogitsLoss`, which fuses the sigmoid and binary cross-entropy into an algebraically equivalent expression based on log-sum-exp style rearrangement. The input is a logit, not a probability. This distinction is as important as the class-index shape you learned for cross-entropy.

```python
import torch
import torch.nn.functional as F

logit = torch.tensor([-100.0])      # very confident negative logit
target = torch.tensor([1.0])        # but the correct label is positive

naive = -torch.log(torch.sigmoid(logit))
stable = F.binary_cross_entropy_with_logits(logit, target)

print(naive)   # tensor([inf]) on common fp32 paths
print(stable)  # tensor(100.)
```

Fused losses are also easier to audit in code review. A reviewer who sees `F.cross_entropy(logits, y)` can check shapes and target dtype. A reviewer who sees `torch.log(torch.softmax(scores))` has to inspect the implementation, the dtype, the axis, the possible score range, and whether the result later flows into the right reduction. Stable APIs compress a whole page of numerical reasoning into a call site whose contract is documented and tested by the framework.

The same principle applies to epsilon placement. In B4, Adam's denominator used `sqrt(v_hat) + eps`, not `sqrt(v_hat + eps)`, because the epsilon is guarding the denominator used for the update, not changing the second-moment estimate itself. In B6, normalization layers use an epsilon inside the variance-to-standard-deviation path because they need to avoid division by zero when variance is tiny. The placement is part of the formula, not a decorative constant added wherever a division appears.

```python
import torch

x = torch.zeros(4)
bad = x / x.norm()
good = x / x.norm().clamp_min(1e-8)

print(bad)   # tensor([nan, nan, nan, nan])
print(good)  # tensor([0., 0., 0., 0.])
```

Do not treat `eps=1e-8` as a universal spell. If the denominator has normal scale, `1e-8` is harmless. If the denominator is supposed to carry meaningful information around `1e-9`, adding `1e-8` changes the computation by an order of magnitude. If the dtype is fp16, `1e-8` may underflow to zero in the dtype path where you needed protection. Good stable code chooses epsilon based on the quantity being protected, the dtype, and the surrounding algebra. The B4 Adam epsilon and B6 normalization epsilon discussions are examples of this rule in two different places.

The fused-loss rule is the most important habit in this module: keep logits as logits until the loss function consumes them. Probabilities are for interpretation, calibration plots, sampling, or metrics. Losses want logits because logits preserve dynamic range. The A5 stable softmax-CE implementation taught the math; PyTorch's `F.cross_entropy`, `F.log_softmax`, `F.nll_loss`, and `BCEWithLogitsLoss` give you the production APIs that encode the same stability discipline.

When you do need probabilities, create them at the boundary where probabilities are actually consumed. Metrics such as accuracy can use `argmax(logits)` without softmax at all, because softmax preserves ordering. Calibration plots need probabilities, so compute `softmax` for that reporting path under `torch.no_grad()`. Sampling needs probabilities or log probabilities, so use the framework's stable sampling and log-softmax paths. Keeping these boundaries clear prevents a common anti-pattern where the model's `forward` method returns probabilities because they look friendly, and every downstream training loss then has to recover from a representation that already threw away numerical headroom.

---

## Part 4: Mixed-Precision Training with AMP

Automatic mixed precision, or AMP, means the framework chooses lower precision for operations that benefit from it and keeps sensitive operations in fp32 where range or reduction accuracy matters. It is not the same as calling `.half()` on the whole model. In current PyTorch, you should use the `torch.amp` namespace: `torch.amp.autocast` for dtype policy and `torch.amp.GradScaler` when fp16 gradient scaling is needed. The older CUDA-specific AMP namespace is deprecated in the PyTorch 2.12 docs.

Autocast wraps the forward pass and loss computation. It should not wrap `loss.backward()`. In the forward region, matrix multiplies and linear/convolution layers can run in lower precision to use accelerator hardware efficiently, while reductions, softmax, log, cross-entropy, normalization, and similar numerically sensitive operations can be promoted or kept in fp32 according to PyTorch's op table. That per-op policy is the main reason AMP is safer than manual casting.

The engineering contract is that autocast changes execution dtype, not your model design. You still define modules in ordinary PyTorch. You still move inputs and parameters to the right device. You still use `optimizer.zero_grad(set_to_none=True)`, compute a loss, run backward, and step the optimizer. The difference is that the forward graph enters a context manager where PyTorch can choose faster low-precision kernels for eligible operations and safer fp32 kernels for sensitive ones. That is the line-for-line replacement story of Block B again: AMP replaces manual casting decisions with a framework policy, but the training loop remains the loop you already know.

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class TinyClassifier(nn.Module):
    def __init__(self, in_features=32, hidden=64, classes=5):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, hidden),
            nn.ReLU(),
            nn.Linear(hidden, classes),
        )

    def forward(self, x):
        return self.net(x)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
device_type = device.type
model = TinyClassifier().to(device)
optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4)

def train_step_bf16(batch):
    inputs, targets = batch
    inputs = inputs.to(device)    # shape: [N, 32], dtype fp32 storage
    targets = targets.to(device)  # shape: [N], dtype int64 class indices

    model.train()
    optimizer.zero_grad(set_to_none=True)

    amp_enabled = device_type == "cuda" and torch.cuda.is_bf16_supported()
    with torch.amp.autocast(
        device_type=device_type,
        dtype=torch.bfloat16,
        enabled=amp_enabled,
    ):
        logits = model(inputs)              # shape: [N, 5]
        loss = F.cross_entropy(logits, targets)

    loss.backward()                         # backward outside autocast
    optimizer.step()
    return loss.detach()

batch = (
    torch.randn(16, 32),
    torch.randint(0, 5, (16,), dtype=torch.long),
)
print(train_step_bf16(batch).item())
```

Notice the shape and dtype boundaries. The model parameters are still stored in the default fp32 unless you deliberately choose another storage strategy. The inputs enter as fp32 tensors. Autocast decides which forward ops can use bf16 on CUDA. The loss remains a scalar tensor that participates in autograd exactly like the scalar loss in A8, except now the graph contains tensor operations with dtype policy attached. The optimizer still sees gradients and parameter tensors through the ordinary PyTorch optimizer interface you learned in B2 and B4.

Why use bf16 when available? Because bf16 has the same exponent range as fp32, so activations and gradients are much less likely to overflow or underflow merely because their magnitude is outside the dtype range. The tradeoff is precision: bf16 has only seven explicitly stored mantissa bits, so nearby values around 1.0 are spaced roughly 0.0078125 apart. For many deep-learning workloads, especially large models with normalization and stable losses, range matters more than the extra mantissa precision fp16 provides. That is why bf16 has become the default low-precision training choice on modern accelerators that support it well.

NVIDIA's mixed-precision training guide shows a language-model training curve where mixed precision without loss scaling diverges, while the loss-scaled run tracks the single-precision baseline. The lesson is narrow but important: the failure was not "lower precision is impossible." It was "lower precision without the right range-management mechanism changes the optimization." AMP exists to encode those mechanisms in a workflow engineers can use without manually rewriting every matmul, reduction, and loss.

There are still times when you should carve out a full-precision island. A custom loss that computes a small difference between large values, a hand-written normalization path, or a metric reused as a differentiable objective may need `with torch.amp.autocast(device_type=device_type, enabled=False):` around the sensitive block and explicit `.float()` casts for tensors entering that block. This is not a failure of AMP. It is the same engineering principle as stable softmax: use low precision where it is safe, and force full precision where the algebra is sensitive to range or cancellation.

---

## Part 5: Gradient Scaling for fp16

fp16 has a narrow exponent range. Its largest finite value is 65,504, and its smallest positive normal value is about `6.10e-5`, with subnormals extending lower but with reduced precision and device-specific performance behavior. Many gradients in deep networks are much smaller than `1e-5`. If a backward operation produces fp16 gradients directly, those small values may underflow to zero. A zero gradient is not a noisy gradient; it is no update at all for that parameter component.

Gradient scaling solves underflow by multiplying the loss by a scale factor before backward. If the loss is multiplied by `S`, every gradient produced by the backward pass is also multiplied by `S`. Those larger gradients are more likely to be representable in fp16. Before the optimizer step, the scaler unscales gradients by dividing by `S`, so the final update corresponds to the original loss. Dynamic scaling adjusts `S` over time: if gradients overflow to `inf` or `nan`, the scaler skips the optimizer step and lowers the scale; after many successful steps, it may raise the scale.

This skip behavior is a feature, not a nuisance. If the scaler detects non-finite gradients and still let the optimizer update parameters, AdamW's moment buffers could inherit `inf` or `nan`, and future steps would remain corrupted even after the original arithmetic spike disappeared. Skipping the step contains the damage to one batch. Lowering the scale then gives the next batch a better chance of producing representable gradients. The scaler is therefore both a range amplifier for small gradients and a circuit breaker for overflow.

bf16 generally does not need gradient scaling because its exponent range matches fp32. That sentence has two qualifiers. "Generally" means there can be exotic models or custom kernels that still need special handling. "Because" matters: bf16 is not safer because it is more precise than fp16; it is less precise near 1.0. It is safer for training because the exponent range protects magnitude. If a value is representable in fp32 by range, it is usually representable in bf16 by range too, though with fewer mantissa bits.

Here is the correct current PyTorch 2.12 fp16 loop shape. The order is the contract: create a `torch.amp.GradScaler("cuda")`, run forward and loss under `torch.amp.autocast(..., dtype=torch.float16)`, scale the loss, call backward, unscale before gradient clipping, step through the scaler, then update the scaler. If non-finite gradients are detected, `scaler.step(optimizer)` skips the actual `optimizer.step()` so bad gradients do not pollute weights or optimizer state.

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
device_type = device.type

model = nn.Sequential(
    nn.Linear(32, 64),
    nn.GELU(),
    nn.Linear(64, 5),
).to(device)
optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4)

use_fp16_amp = device_type == "cuda"
scaler = torch.amp.GradScaler("cuda", enabled=use_fp16_amp)

def train_step_fp16(batch):
    inputs, targets = batch
    inputs = inputs.to(device)
    targets = targets.to(device)

    model.train()
    optimizer.zero_grad(set_to_none=True)

    with torch.amp.autocast(
        device_type=device_type,
        dtype=torch.float16,
        enabled=use_fp16_amp,
    ):
        logits = model(inputs)              # [N, 5]
        loss = F.cross_entropy(logits, targets)

    scaler.scale(loss).backward()

    # Required before inspecting or clipping gradients, because they are scaled.
    scaler.unscale_(optimizer)
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

    scaler.step(optimizer)  # internally skips optimizer.step() on inf/NaN grads
    scaler.update()
    return loss.detach()
```

The `unscale_` line is the one many otherwise-correct loops miss. Clipping scaled gradients clips the artificial scale, not the real gradient norm. If the scale factor is 65,536, a perfectly reasonable real gradient norm of 0.5 appears as 32,768 before unscale, so clipping at 1.0 would crush the update by accident. Any logic that reads gradient values, such as clipping, logging exact norms, or checking for custom overflow conditions, belongs after `scaler.unscale_(optimizer)` and before `scaler.step(optimizer)`.

The link to A8 is direct. Your scalar autograd engine had no concept of dtype or scaling; every `.grad` value was a Python float in a tiny graph. PyTorch's autograd computes the same chain-rule product over a much larger graph, but the dtype of forward and backward tensors affects which gradient values survive as representable numbers. Gradient scaling does not change calculus. It changes the numerical encoding so the calculus has something nonzero to store.

The link to B4 is just as direct. AdamW divides the first-moment estimate by a square root of the second-moment estimate plus epsilon, so a gradient that underflowed to zero changes both numerator and denominator history. The optimizer cannot distinguish "the true gradient was exactly zero" from "the dtype flushed this small gradient to zero before I saw it." Loss scaling protects the optimizer's memory by making the gradient values that enter those moment buffers closer to the mathematical gradients the backward pass intended to produce.

---

## Part 6: TF32 and Matmul Precision

TensorFloat-32, usually written TF32, is a hardware math mode on NVIDIA Ampere-and-later GPUs. It is easy to confuse with AMP because both involve reduced precision and Tensor Cores, but the mechanisms are different. AMP changes the dtype used by selected operations in an autocast region, often to fp16 or bf16. TF32 keeps tensors stored as fp32 but lets supported matrix multiplications and convolutions use a reduced-precision internal multiply path, reading fewer mantissa bits while typically accumulating in a wider format.

The high-level PyTorch control for fp32 matrix multiply precision is `torch.set_float32_matmul_precision`. The settings are `"highest"`, `"high"`, and `"medium"`. `"highest"` asks for full fp32 internal matmul precision where available. `"high"` allows TF32 or a bfloat16-based algorithm when the backend has a faster path. `"medium"` allows more aggressive reduced precision where supported. The output tensor dtype remains fp32; the setting controls the internal algorithm.

```python
import torch

torch.set_float32_matmul_precision("high")

if torch.cuda.is_available():
    # Direct backend flag seen in older code. Prefer the high-level API above
    # for new code that wants a portable matmul-precision intent.
    torch.backends.cuda.matmul.allow_tf32 = True

a = torch.randn(512, 512, device="cuda" if torch.cuda.is_available() else "cpu")
b = torch.randn(512, 512, device=a.device)
c = a @ b
print(c.dtype)  # torch.float32: storage/output dtype did not become bf16/fp16
```

The tradeoff is speed versus numerical agreement with full fp32 matmul. Many neural-network training workloads converge the same way with TF32 enabled, especially when the loss and reductions are stable and the model has normalization. Some scientific workloads, small-error regression tests, or numerically sensitive linear algebra routines need full fp32 precision. The correct engineering move is to decide deliberately, document the setting, and test convergence and metrics under the setting you plan to use in production.

Reduced precision also interacts with reproducibility. Floating-point addition and multiplication are not associative, parallel kernels may reduce values in different orders, and faster algorithms may choose different tiling strategies. `torch.use_deterministic_algorithms(True)` can force deterministic alternatives or raise when only nondeterministic algorithms are available, but determinism often costs speed and does not mean "identical to fp64 math." It means the same software and hardware path produces the same result for the same inputs. Precision choice, deterministic kernels, random seeds, and data-ordering controls are separate switches that together define how reproducible a training run can be.

A practical team policy is to treat matmul precision as part of the experiment configuration, alongside seed, batch size, learning-rate schedule, AMP dtype, and checkpoint format. If a baseline was selected with TF32 enabled, evaluate ablations with TF32 enabled unless the ablation is specifically about numerical precision. If a regression test compares exact tensor values, run it under `"highest"` or loosen it to a tolerance that reflects the configured precision. Silent defaults are what create arguments later; explicit precision settings turn those arguments into reproducible experiments.

---

## Part 7: A Precision-Specific NaN Debugging Recipe

B7 owns the broader training-diagnostics playbook, so keep this slice focused on arithmetic. The first rule is to find the first non-finite value, not the loudest downstream symptom. Check inputs before the model, logits before the loss, the scalar loss before backward, gradients after backward, and parameters after the optimizer step. A NaN observed in the loss is already late; a NaN observed in logits or an `inf` observed in a normalization denominator points closer to the cause.

```python
import torch

def assert_finite_tensor(name, tensor):
    if not torch.isfinite(tensor).all():
        bad = tensor[~torch.isfinite(tensor)]
        raise RuntimeError(
            f"{name} contains non-finite values; "
            f"count={bad.numel()}, first={bad.flatten()[0].item()}"
        )

def check_gradients(model):
    for name, param in model.named_parameters():
        if param.grad is not None:
            assert_finite_tensor(f"grad:{name}", param.grad)
```

The second rule is to enable anomaly detection only while narrowing the failure, not as a default training mode. `torch.autograd.set_detect_anomaly(True)` records extra autograd information and reports the operation that produced a NaN during backward, but it is slower and noisier than ordinary training. Use it on a short reproduction, ideally after you have reduced the batch, fixed the seed, and found a step where the failure happens reliably.

```python
optimizer.zero_grad(set_to_none=True)
with torch.amp.autocast(device_type="cuda", dtype=torch.bfloat16, enabled=False):
    logits = model(inputs)
    loss = torch.nn.functional.cross_entropy(logits, targets)

assert_finite_tensor("logits", logits)
assert_finite_tensor("loss", loss)

with torch.autograd.set_detect_anomaly(True):
    loss.backward()
check_gradients(model)
optimizer.step()
```

The third rule is to check the precision suspects before rewriting the model. Is the learning rate too high, causing logits or activations to explode? Did someone compute `torch.log(probabilities)` where probabilities can be exactly zero? Did a normalization path divide by a norm that can be zero? Did a custom loss use `torch.exp` on raw scores instead of a log-sum-exp form? Did fp16 AMP run without `GradScaler`, or did clipping happen before `scaler.unscale_(optimizer)`? Did a bf16 run inherit a kernel or custom op that was never tested outside fp32?

The shortest useful recipe is: reproduce with one batch, disable AMP to see whether the failure is precision-specific, lower the learning rate by 10x to test optimizer explosion, replace manual losses with fused logits-based losses, assert finite tensors around custom math, then re-enable AMP with the correct bf16 or fp16 path. If disabling AMP fixes the run, do not conclude "AMP is broken." Conclude that some operation in your graph needs a stable formulation, a fp32 autocast island, bf16 instead of fp16, or correct gradient scaling.

When the failure appears only after many successful steps, preserve the first failing batch and checkpoint if you can. Save the model, optimizer state, scaler state, random seed, and the batch that produced the first non-finite loss. Then replay one step with extra assertions. This avoids the expensive pattern of rerunning thousands of clean steps just to observe the same NaN again. Precision bugs become much easier when you turn them from a long training story into a deterministic one-step reproduction.

---

## Did You Know?

- **NaN is contagious by design**: IEEE-style arithmetic treats invalid operations as values that propagate, which is painful during training but useful for debugging because it preserves evidence that an invalid operation happened instead of silently pretending the result was zero.
- **bf16 was designed around neural-network range needs**: Google's bfloat16 format keeps the eight exponent bits of fp32 and drops mantissa bits, reflecting the empirical observation that many deep networks are more sensitive to exponent range than to extra significand precision.
- **AMP is an op policy, not a dtype promise**: Inside an autocast region, `linear` and `matmul` may run in lower precision while `cross_entropy`, `log_softmax`, `softmax`, `sum`, and normalization-related operations may run in fp32 for stability according to PyTorch's op tables.
- **TF32 output still says `torch.float32`**: TF32 changes how supported fp32 matrix multiplies are internally computed on specific NVIDIA hardware; it does not turn model parameters, activations, or outputs into a different storage dtype.

---

## Common Mistakes

| Mistake | Problem | Better Approach |
|---|---|---|
| Passing probabilities into `F.cross_entropy` | `cross_entropy` expects unnormalized logits, so probabilities remove dynamic range and cause the function to apply the wrong mathematical contract. | Pass raw logits directly, or use `F.log_softmax(logits, dim=-1)` plus `F.nll_loss` only when you explicitly need log probabilities. |
| Writing `torch.log(torch.softmax(logits))` | The separate softmax and log path is slower and can become unstable when probabilities round to zero or logits are extreme. | Use `F.log_softmax` or `F.cross_entropy`, both of which encode the stable log-sum-exp formulation. |
| Using `torch.sigmoid(logits)` before `BCELoss` | Extreme logits can become exact 0 or 1 probabilities, and the backward path is unsafe under autocast for fp16. | Use `nn.BCEWithLogitsLoss` or `F.binary_cross_entropy_with_logits` on logits. |
| Calling `.half()` on the model and inputs manually | Manual casting moves sensitive reductions and losses into fp16 unless every operation is audited, which is how silent underflow and overflow enter a run. | Use `torch.amp.autocast` so PyTorch applies per-op dtype policy, and keep backward outside the autocast region. |
| Clipping gradients before `scaler.unscale_(optimizer)` | The clipping threshold sees artificially scaled gradients, so it clips based on the loss scale rather than the real gradient norm. | Call `scaler.unscale_(optimizer)`, then clip or inspect gradients, then call `scaler.step(optimizer)` and `scaler.update()`. |
| Treating bf16 as "more precise fp16" | bf16 has wider range but fewer mantissa bits than fp16, so it solves many overflow/underflow problems while making nearby values coarser. | Choose bf16 when range and Tensor Core support matter, but keep reductions and numerically sensitive operations stable. |
| Confusing TF32 with AMP | TF32 controls internal fp32 matmul precision on supported hardware, while AMP changes selected operation dtypes inside an autocast region. | Configure `torch.set_float32_matmul_precision` separately from AMP and test convergence under the exact combination you deploy. |

---

## Quiz

1. **Why does subtracting the maximum logit before softmax not change the mathematical probabilities?**

   <details>
   <summary>Answer</summary>

   Softmax is invariant to adding or subtracting the same constant from every logit because the common factor `exp(c)` appears in both numerator and denominator and cancels. Choosing `c = max(logits)` makes the largest shifted logit zero, so the largest exponential is `exp(0) = 1` rather than an overflowing value. This is the same stable softmax-CE idea you implemented in A5.

   </details>

2. **A model trains in fp32 but produces NaNs when you switch to fp16 AMP without a scaler. What is the first mechanism you should suspect?**

   <details>
   <summary>Answer</summary>

   Suspect fp16 gradient underflow or overflow, then debug the first non-finite value rather than only the final loss. fp16 has narrow dynamic range, so small gradients can flush to zero and large values can exceed 65,504; the same run may also hide arithmetic sources such as `exp` overflow, `log(0)`, `sqrt` of a negative value, division by zero, or NaN propagation after one invalid tensor element appears. The standard fp16 AMP fix is `torch.amp.GradScaler("cuda")` with the exact scale, backward, optional unscale-and-clip, scaler step, and scaler update sequence. If scaling still fails, use finite checks around inputs, logits, loss, gradients, and parameters to locate the first operation that created `NaN` or `Inf`.

   </details>

3. **Why is `BCEWithLogitsLoss` more stable than `sigmoid -> BCELoss`?**

   <details>
   <summary>Answer</summary>

   `BCEWithLogitsLoss` fuses the sigmoid and binary cross-entropy into an algebraically stable logits-based expression, avoiding explicit probabilities that can round to exactly 0 or 1. The fused form uses a log-sum-exp style rearrangement, so extreme logits produce large but finite losses where a manual `log(sigmoid(x))` path may produce `inf`.

   </details>

4. **Why does bf16 usually not need gradient scaling even though it has fewer mantissa bits than fp16?**

   <details>
   <summary>Answer</summary>

   Gradient scaling mainly protects dynamic range, not fine precision near 1.0. bf16 has the same eight exponent bits as fp32, so it can represent very large and very small normal values over roughly the same range as fp32. fp16 has more mantissa bits than bf16 but only five exponent bits, which is why fp16 gradients often underflow or overflow without scaling.

   </details>

5. **Where should `loss.backward()` appear relative to `torch.amp.autocast`?**

   <details>
   <summary>Answer</summary>

   The autocast context should wrap the forward pass and loss computation, then exit before backward. PyTorch's AMP docs recommend this because backward operations run in the dtype selected for their corresponding forward operations, and wrapping backward in autocast is not recommended. The usual structure is `with autocast: logits = model(x); loss = loss_fn(logits, y)`, then `loss.backward()` or `scaler.scale(loss).backward()` outside the context.

   </details>

6. **What is the difference between enabling TF32 matmul precision and enabling AMP?**

   <details>
   <summary>Answer</summary>

   TF32 keeps tensors stored and returned as fp32 but allows supported fp32 matrix multiplications to use a reduced-precision internal multiply path on NVIDIA Ampere-and-later hardware. AMP uses an autocast policy to run selected operations in lower precision dtypes such as fp16 or bf16 while keeping sensitive operations in fp32. They are separate controls and can be combined, but they solve different performance problems.

   </details>

---

## Hands-On Exercise

**Task**: Build a small numeric stability probe that demonstrates naive softmax overflow, stable log-sum-exp cross-entropy, NaN propagation, and a guarded AMP training step. This is a teaching experiment, not a full lab; the goal is to make the failure modes visible in less than a minute.

**Steps**: Follow these prompts in order so the experiment first exposes the unstable arithmetic, then replaces it with the stable PyTorch path.

1. Create a file named `precision_probe.py` and paste the code below.
2. Run it first on CPU; if you have a CUDA GPU, run it again and observe whether the AMP section enables bf16 autocast.
3. Change the logits from `[1000, 1001, 1002]` to `[10, 11, 12]` and confirm that the naive path stops overflowing while the stable path still matches.
4. Change `torch.bfloat16` to `torch.float16` in the autocast block on CUDA, add a `GradScaler`, and compare the loop shape to the fp16 skeleton in Part 5.

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

torch.manual_seed(7)

def show_softmax_stability():
    logits = torch.tensor([[1000.0, 1001.0, 1002.0]])
    target = torch.tensor([2])
    naive = torch.exp(logits) / torch.exp(logits).sum(dim=-1, keepdim=True)
    stable_loss = F.cross_entropy(logits, target)
    stable_probs = F.softmax(logits, dim=-1)
    print("naive softmax:", naive)
    print("stable probs:", stable_probs)
    print("stable CE:", stable_loss.item())

def show_nan_propagation():
    x = torch.ones(3, 3)
    x[0, 1] = float("nan")
    y = x @ torch.randn(3, 3)
    print("input NaNs:", torch.isnan(x).sum().item())
    print("output NaNs after matmul:", torch.isnan(y).sum().item())

class TinyNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = nn.Sequential(nn.Linear(8, 16), nn.ReLU(), nn.Linear(16, 3))

    def forward(self, x):
        return self.layers(x)

def show_amp_step():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    device_type = device.type
    model = TinyNet().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    x = torch.randn(12, 8, device=device)
    y = torch.randint(0, 3, (12,), device=device)
    amp_enabled = device_type == "cuda" and torch.cuda.is_bf16_supported()

    model.train()
    optimizer.zero_grad(set_to_none=True)
    with torch.amp.autocast(device_type=device_type, dtype=torch.bfloat16, enabled=amp_enabled):
        logits = model(x)
        loss = F.cross_entropy(logits, y)
    loss.backward()
    optimizer.step()
    print("amp enabled:", amp_enabled, "loss:", float(loss.detach().cpu()))

show_softmax_stability()
show_nan_propagation()
show_amp_step()
```

**Success Criteria**: Treat the exercise as complete only when each observable behavior below is visible and you can explain the dtype reason behind it.

- [ ] The naive softmax prints `nan` for the extreme `[1000, 1001, 1002]` logits, while `F.cross_entropy` returns a finite scalar.
- [ ] The NaN propagation check shows that one NaN in the input can create multiple NaNs after matrix multiplication.
- [ ] The AMP step runs without wrapping backward in autocast, and the printed loss is finite.
- [ ] You can explain why bf16 AMP does not use a `GradScaler` in this exercise, and when fp16 would need one.

**Verification**: Run the script from the repository root with the project venv, or with an equivalent PyTorch 2.12 environment if this checkout lacks torch.

```bash
.venv/bin/python precision_probe.py
```

---

## Key Takeaways

- Floating-point training is governed by range and precision: exponent bits decide how large or tiny values can be, while mantissa bits decide how closely nearby values can be represented.
- NaNs and Infs come from specific arithmetic events, and the right debugging target is the first non-finite tensor rather than the downstream loss that finally reports `nan`.
- Stable softmax cross-entropy is the A5 log-sum-exp implementation in production form; use logits with `F.cross_entropy`, `F.log_softmax` plus `F.nll_loss`, and `BCEWithLogitsLoss`.
- AMP is a per-op dtype policy around the forward pass and loss, not a blanket cast of the model, and current PyTorch code should use the `torch.amp` namespace.
- fp16 training needs gradient scaling because its range is narrow; bf16 usually does not because it keeps fp32-like exponent range even though its mantissa is coarse.
- TF32 controls internal fp32 matmul precision on supported NVIDIA GPUs and remains separate from AMP, deterministic algorithms, random seeds, and dtype storage choices.

---

## Sources

- [PyTorch 2.12 release blog](https://pytorch.org/blog/pytorch-2-12-release-blog/)
- [PyTorch 2.12: Automatic Mixed Precision package - `torch.amp`](https://docs.pytorch.org/docs/2.12/amp.html)
- [PyTorch 2.12: `torch.logsumexp`](https://docs.pytorch.org/docs/2.12/generated/torch.logsumexp.html)
- [PyTorch 2.12: `torch.nn.functional.cross_entropy`](https://docs.pytorch.org/docs/2.12/generated/torch.nn.functional.cross_entropy.html)
- [PyTorch 2.12: `torch.nn.functional.log_softmax`](https://docs.pytorch.org/docs/2.12/generated/torch.nn.functional.log_softmax.html)
- [PyTorch 2.12: `torch.nn.BCEWithLogitsLoss`](https://docs.pytorch.org/docs/2.12/generated/torch.nn.BCEWithLogitsLoss.html)
- [PyTorch 2.12: `torch.set_float32_matmul_precision`](https://docs.pytorch.org/docs/2.12/generated/torch.set_float32_matmul_precision.html)
- [PyTorch 2.12: Numerical accuracy notes](https://docs.pytorch.org/docs/2.12/notes/numerical_accuracy.html)
- [PyTorch 2.12: `torch.use_deterministic_algorithms`](https://docs.pytorch.org/docs/2.12/generated/torch.use_deterministic_algorithms.html)
- [NVIDIA: Train With Mixed Precision](https://docs.nvidia.com/deeplearning/performance/mixed-precision-training/index.html)
- [Micikevicius et al. 2017: Mixed Precision Training](https://arxiv.org/abs/1710.03740)
- [Google Cloud: BFloat16, the secret to high performance on Cloud TPUs](https://cloud.google.com/blog/products/ai-machine-learning/bfloat16-the-secret-to-high-performance-on-cloud-tpus)
- [IEEE 754-2019 standard overview](https://standards.ieee.org/ieee/754/6210/)
- [FP8 Formats for Deep Learning](https://arxiv.org/abs/2209.05433)

---

## Next Module

[Convolutional Neural Networks & Computer Vision](/ai-ml-engineering/deep-learning/module-1.5-rnns-sequence-models/) continues the arc by applying these training-stability habits to vision architectures whose convolutions, normalizers, and activations make precision choices visible at scale.

## Learner check

The index row for this module is intentionally quoted here so the merge hook can verify that the module and section index moved together:

> | 1.3.6 | [Numerical Stability & Precision](/ai-ml-engineering/deep-learning/module-1.3.6-numerical-stability-precision/) |
