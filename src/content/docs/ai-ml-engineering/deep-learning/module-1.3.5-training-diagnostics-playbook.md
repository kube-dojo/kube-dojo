---
title: "Training-Diagnostics Playbook"
slug: ai-ml-engineering/deep-learning/module-1.3.5-training-diagnostics-playbook
sidebar:
  order: 1004.5
---

> **AI/ML Engineering Track** | Complexity: `[COMPLEX]` | Time: 4-5 hours
>
> **Prerequisites**: Module 1.3 (The Training Loop), Modules 1.3.1–1.3.4 (initialization, optimizers, regularization, normalization), and Block A modules A5 (Loss Functions) and A7 (Tiny NumPy NN Lab — the hand-written training loop you will map onto PyTorch diagnostics).
>
> **Primary tools**: PyTorch 2.12, TensorBoard `SummaryWriter`, optional `torchinfo`.

---

In April 2019, Andrej Karpathy published a blog post titled "A Recipe for Training Neural Networks" that distilled years of practical debugging into a disciplined sequence: start small, overfit one batch, verify the loss at initialization, then scale up. The post was not a new algorithm or architecture — it was a **process**. Karpathy argued that most "my model won't train" reports are not mysteries requiring a novel optimizer; they are engineering failures that a cheap checklist would have caught in the first hour. That checklist became one of the most cited practitioner documents in deep learning because it respects a uncomfortable truth: when training fails, the bug is usually in the data pipeline, the loss contract, or a mode toggle — not in the number of hidden units. Modules B3 through B6 gave you the **tools** (initialization, optimizers, regularization, normalization). This module gives you the **playbook**: symptom → hypothesis → instrument → fix. Every PyTorch primitive here maps onto something you already built by hand in Block A — `loss.backward()` is still the autograd engine from A8, `nn.CrossEntropyLoss` is still the stable softmax-CE from A5, and the overfit-one-batch test is the same contract you ran in A7 before trusting a full Fashion-MNIST epoch.

---

## Learning Outcomes

By the end of this module, you will be able to:

1. **Implement** Karpathy's sanity gauntlet — expected initial loss, overfit-a-single-batch, and input-independent baseline — and **interpret** each failure mode as a data bug, loss mismatch, or frozen-parameter problem rather than a hyperparameter problem.
2. **Compare** canonical train/validation loss-curve shapes (healthy convergence, underfitting, overfitting, LR-too-high, LR-too-low, noisy data, warmup) and **localize** the likely cause from curve geometry alone before touching architecture.
3. **Instrument** global and per-layer gradient norms and per-layer activation statistics using post-`backward()` reads and forward hooks, **apply** Karpathy's grad-to-param update ratio heuristic, and **select** between `clip_grad_norm_` and `clip_grad_value_` when explosions or dead ReLUs appear.
4. **Debug** data-pipeline failures — transform mismatch, missing `.train()`/`.eval()` toggles, label leakage, broken `Dataset.__getitem__`, class imbalance — by eyeballing denormalized batches before blaming the model.
5. **Run** a learning-rate range test (Smith 2017) as a diagnostic instrument, **assemble** a consolidated decision tree and metrics-logging loop with TensorBoard and `torch.autograd.set_detect_anomaly(True)`, and **decide** when the optimizer versus the data pipeline is the more likely culprit (forward-pointing NaN arithmetic to Module 1.3.6).

---

## Why This Module Matters

Training a neural network is an experiment. Like any experiment, it produces signals — scalar losses, gradient norms, activation histograms, learning rates — and your job as an engineer is to read those signals with the same discipline a reliability engineer brings to an incident postmortem. The difference between a practitioner who debugs training in an afternoon and one who burns a week of GPU time on random hyperparameter sweeps is rarely raw mathematical talent. It is **process**: knowing which cheap check eliminates which class of bug, in what order, before you escalate to expensive interventions.

Block B has been teaching you that PyTorch is not magic. `torch.Tensor` is the NumPy array you manipulated in A1–A3. `loss.backward()` is the scalar autograd engine from A8 and the hand-derived VJPs from A6 — the engine does exactly what you did by hand, on every node in the graph. `nn.Linear` is the `Layer` class from A3/A7. `torch.optim.SGD` is the manual `W -= lr * dW` loop from A7. When training breaks, the diagnostic playbook asks you to **verify that mapping** before you assume PyTorch introduced a black box. If a random model's initial cross-entropy is not near `ln(num_classes)`, something is wrong with labels, logits shape, or loss reduction — not with AdamW's beta parameters. If you cannot overfit a single batch of eight examples after two hundred steps with regularization disabled, no amount of cosine annealing on the full dataset will save you.

The modules immediately preceding this one each addressed a **fix** for a specific failure class. Module 1.3.1 (initialization) fixes signal scale at step zero. Module 1.3.2 (optimizers and learning rate) fixes how gradient information is accumulated and scaled over time. Module 1.3.3 (regularization) fixes the train/validation gap when the model memorizes. Module 1.3.4 (normalization) fixes internal activation drift and the train/eval statistics switch. This module does not re-teach those fixes — it teaches you **when to reach for them** by reading symptoms first. A flat validation loss with falling training loss implicates regularization (B5), not initialization (B3). A loss that spikes to NaN on step fifty implicates learning rate (B4) or numerical precision (B8), not dropout. A model that trains beautifully on the training set but collapses in deployment implicates `.eval()` mode and normalization statistics (B6), not the optimizer choice.

The centerpiece deliverable is a **diagnostic decision tree** you can keep open during every training run: a symptom maps to a first instrument, that instrument narrows the hypothesis space, and the fix references the module that owns it. Treat this playbook the way you treat a runbook for a production service — not as material to memorize once, but as a checklist you execute until the habits become automatic.

There is a cultural trap in machine learning teams that this module is designed to break. When a run fails, the social default is often to propose a new architecture, switch from AdamW to Lion, or double the parameter count — interventions that feel productive because they change code on screen. Diagnostic discipline inverts that instinct: you change nothing until a measurement falsifies a hypothesis. The expected-init-loss check takes thirty seconds; the overfit-one-batch test takes two minutes on a laptop CPU; visualizing one batch takes one minute. Together they eliminate whole categories of bugs that would otherwise consume a multi-GPU day. The engineer who runs the gauntlet first is not being cautious — they are being fast, because false starts are the slowest possible training strategy.

The back-reference thread to Block A is not decorative. When you verify that initial cross-entropy equals `log(C)`, you are checking the same softmax head contract you proved in A5. When you overfit one batch, you are rerunning the memorization experiment from A7 with PyTorch replacing your hand-written `W -= lr * dW` loop — if PyTorch cannot memorize eight images, the bug is in how you wired `loss.backward()`, not in PyTorch's autograd implementation. When you inspect gradient norms, you are measuring the same signal whose VJPs you derived layer by layer in A6. Block B did not replace that understanding; it industrialized it. Diagnostics are how you prove the industrial machinery still matches the math you own.

---

## Part 1: The Diagnostic Mindset and the Sanity Gauntlet

Before you touch TensorBoard, before you sweep learning rates, before you redesign the architecture — run three checks that cost minutes and eliminate the majority of training failures. Karpathy's recipe and CS231n's "babysitting the learning process" notes converge on the same principle: **prove the pipeline can learn the easiest possible task** before you ask it to learn the hard one.

### 1.1 Expected loss at initialization

A freshly initialized classifier with `C` balanced classes and a correct cross-entropy head should produce logits that are roughly symmetric around zero. After softmax, each class receives probability near `1/C`, and the per-example loss is:

\[
\mathcal{L} = -\log\left(\frac{1}{C}\right) = \log(C)
\]

For natural-log cross-entropy (PyTorch's default in `nn.CrossEntropyLoss`), ten classes give expected loss `ln(10) ≈ 2.3026`. This is the same stable softmax-CE you implemented in A5 — if your hand-derived code predicted `log(C)` at init, PyTorch should agree to within Monte Carlo noise on a single batch.

```python
import math
import torch
import torch.nn as nn

num_classes = 10
expected = math.log(num_classes)
print(f"Expected initial CE (balanced, random logits): {expected:.4f}")  # 2.3026

model = nn.Sequential(
    nn.Flatten(),
    nn.Linear(28 * 28, 256),
    nn.ReLU(),
    nn.Linear(256, num_classes),
)
loss_fn = nn.CrossEntropyLoss()

# One random batch — labels 0..9 uniformly
torch.manual_seed(0)
x = torch.randn(64, 1, 28, 28)
y = torch.randint(0, num_classes, (64,))

model.eval()  # no dropout/BN train quirks for this check
with torch.no_grad():
    logits = model(x)  # shape (64, 10)
    loss = loss_fn(logits, y)
print(f"Observed initial loss: {loss.item():.4f}")
```

If observed loss is **far below** `log(C)`, suspect label smoothing baked into the loss, a bug that makes labels easier than random guessing, or logits that are not raw scores (accidental softmax before CE). If observed loss is **far above** `log(C)`, suspect wrong `num_classes`, integer labels outside `[0, C-1]`, a regression loss applied to classification targets, or accidental double-softmax. If loss is NaN on batch one, skip straight to Part 7's anomaly detection — Module 1.3.6 covers why float arithmetic produces NaNs at the operation level. The numeric anchor is worth memorizing: for Fashion-MNIST (`C=10`), expect roughly `2.30`; for CIFAR-100, roughly `4.61`. When your logged value is `0.4` at step zero, you are not looking at a "good" model — you are looking at a mis-specified head or leaked labels.

### 1.2 Overfit a single batch

The overfit-one-batch test is a **contract test** for your entire training loop, not a training strategy. Take one micro-batch (eight to sixty-four examples), disable dropout and heavy augmentation, use a model with enough capacity to memorize, and run two hundred optimizer steps on **the same batch**. A correct stack should drive loss toward zero (or near-zero for noisy labels).

```python
def overfit_one_batch(model, loader, loss_fn, optimizer, device, steps=200):
    model.train()
    # Disable regularization influences for the smoke test
    for module in model.modules():
        if isinstance(module, (nn.Dropout, nn.BatchNorm1d, nn.BatchNorm2d)):
            module.eval()  # BN uses running stats; Dropout off

    inputs, targets = next(iter(loader))
    inputs, targets = inputs.to(device), targets.to(device)

    losses = []
    for step in range(steps):
        optimizer.zero_grad(set_to_none=True)
        logits = model(inputs)
        loss = loss_fn(logits, targets)
        loss.backward()
        optimizer.step()
        losses.append(loss.item())
        if step % 50 == 0:
            print(f"step {step:3d}  loss = {loss.item():.6f}")
    return losses
```

Module 1.3 introduced this pattern as the first smoke test for the loop; here is how to **read** the outcome. If loss stays flat near `log(C)`, you have a bug: frozen parameters (`requires_grad=False`), wrong loss (MSE on class indices), detached tensors, backward not reaching weights, labels misaligned with inputs, or learning rate effectively zero. If loss decreases but plateaus high, the model may be under-capacity **for this test only** — try a wider MLP — or regularization is still active. If loss reaches near zero, your loop, loss, labels, and backward path are **proven**; failures on the full dataset are generalization or tuning problems (B4, B5), not plumbing bugs. Disable weight decay in the optimizer for this test if your default AdamW couples L2 with the step — a non-zero weight decay can prevent exact memorization even when the loop is correct, which is good for production training but confusing for a memorization smoke test.

This is the same lesson as A7's XOR and single-batch checks before Fashion-MNIST: if you cannot memorize eight pixels, do not launch a twelve-hour run.

### 1.3 Input-independent baseline

Zero the inputs (or replace them with constant noise) and run a forward pass. Loss should **worsen** compared to real data — the model should not achieve low loss when inputs carry no information. If loss stays low with zeroed inputs, the model may be ignoring features (bug in forward path, collapsed batch norm, or label leakage where targets are derivable without inputs).

```python
def input_independence_check(model, inputs, targets, loss_fn):
    model.eval()
    with torch.no_grad():
        real_loss = loss_fn(model(inputs), targets).item()
        zeroed = torch.zeros_like(inputs)
        null_loss = loss_fn(model(zeroed), targets).item()
    print(f"real inputs loss: {real_loss:.4f}")
    print(f"zeroed inputs loss: {null_loss:.4f}")
    assert null_loss > real_loss, "Model may not be using inputs — investigate pipeline"
```

Together, these three checks form the **sanity gauntlet**. Run them in order on every new dataset and architecture combo. They take less time than writing the Slack message asking for help.

### 1.4 Ordering and escalation discipline

Karpathy's recipe is explicitly sequential for a reason: each check falsifies a different failure class. Expected init loss falsifies label and loss-contract bugs before you spend steps optimizing. Overfit-one-batch falsifies backward and optimizer wiring before you touch the full dataset. Input independence falsifies leakage and ignored-feature paths before you debate model capacity. Skipping straight to learning-rate search when init loss is wrong is like tuning Kubernetes HPA before confirming the pod starts — you may find a number that moves metrics while the underlying system remains broken.

Document gauntlet results in your experiment log the same way Module 1.3 taught you to log seeds and checkpoint paths. When a run fails at epoch twenty, your future self should see: "init loss 2.31, overfit-one-batch final 0.003, input check passed" and know to skip Part 1 entirely. When those lines are missing, every debugging session resets to zero. The playbook is as much about **what to record** as what to execute.

### 1.5 Mapping gauntlet failures to fixes (without re-teaching B3–B6)

When init loss is wrong, fixes live in label encoding, output head width, and loss choice — not in Kaiming init (B3). When overfit fails, fixes live in `requires_grad`, detached tensors, accidental `torch.no_grad()` around forward, label tensor dtype, and frozen batch norm in train mode — not in weight decay (B5). When input independence fails, fixes live in feature engineering and dataset code — not in AdamW betas (B4). This mapping is the spine of the decision tree in Part 7: instruments first, module-specific fixes second.

---

## Part 2: Reading Loss Curves

Once the gauntlet passes, you scale up — and the train/validation loss curves become your primary telemetry. Each canonical shape implicates a different failure class. You do not need a PhD in visualization; you need pattern recognition tied to hypotheses. The curves are not decorative plots for slide decks — they are the time series you would chart for any other engineering system whose health you care about. A spike at step four hundred is an incident; treat it like one.

Loss curves integrate every upstream subsystem: the dataloader, augmentations, model mode, loss reduction, optimizer step, and regularization strength all leave fingerprints. That is why curve reading comes **after** the gauntlet but **before** architecture changes. When validation diverges, the curve tells you whether divergence started at epoch one (data or eval-mode bug) or epoch thirty (overfitting). When both curves flatline, the curve tells you whether flatline began immediately (LR or capacity) or after warmup ended (schedule cliff). Keeping a small library of annotated curve screenshots from your own past projects — with root cause written in the caption — builds diagnostic intuition faster than reading textbooks alone.

### 2.1 Healthy convergence

Both training and validation loss decrease together, with validation trailing training by a modest and stable gap rather than diverging. Task metrics such as accuracy or F1 should improve in sync with loss rather than contradict it — if loss falls while accuracy is flat, verify that you are computing metrics on the same head and label space as the loss. This shape is the baseline every other diagnosis compares against; when you cannot reach it after the sanity gauntlet passes, the problem is hyperparameter or capacity tuning, not a hidden backward bug.

```
loss
  |\
  | \___  val (slightly above)
  |  \___
  |   \__ train
  +-----------> epoch
```

### 2.2 Underfitting

Both curves remain high and flat after many epochs, indicating the model or optimization setup cannot fit even the training distribution. The model may lack capacity, the learning rate may be too low (see Module 1.3.2), regularization may be too aggressive (see Module 1.3.3), or the task may be mis-specified relative to the labels you provided. Confirm with the overfit-one-batch test first: if that also fails, return to Part 1 because the issue is not underfitting in the generalization sense but a broken pipeline.

```
loss
  |~~~~~~~~  val
  |~~~~~~~~  train
  +-----------> epoch
```

### 2.3 Overfitting

Training loss continues downward while validation loss rises after an initial drop, which is the classic signature that Module 1.3.3 treats with dropout, weight decay, early stopping, and data augmentation — not with a lower learning rate alone. The diagnostic nuance is timing: late-epoch divergence often implicates memorization of noise, while divergence from epoch one implicates train/eval mismatch or validation set contamination rather than classical overfitting.

```
loss
  |     /  val
  |    /
  |\__/
  | \____ train
  +-----------> epoch
```

### 2.4 Learning rate too high

Loss spikes, oscillates wildly, or diverges to NaN within the first few hundred steps, often accompanied by exploding gradient norms from Part 3. Fix by reducing learning rate (Module 1.3.2), adding warmup, or clipping gradients — not by changing initialization unless step-zero activations were already pathological in Module 1.3.1 probes. Spikes that coincide with batch-norm layers entering train mode on tiny batches can mimic LR instability; check batch size against normalization requirements from Module 1.3.4 before declaring LR guilty.

```
loss
  |    *
  |   * *
  |  *   *___ NaN
  +-----------> step
```

### 2.5 Learning rate too low

Loss decreases glacially and training would need impractical epoch counts to reach acceptable error, while curves otherwise look healthy but compressed horizontally. An LR range test from Part 6 resolves this faster than blind doubling because it shows whether any decade of learning rates produces meaningful descent. If even aggressive LR cannot help until the overfit-one-batch test passes, the bottleneck is not LR magnitude.

```
loss
  |\
  | \________________  (barely moves)
  +-----------> epoch
```

### 2.6 Noisy or unshuffled data

Training loss shows a sawtooth pattern epoch to epoch because consecutive batches are correlated — sorted by class, filename, or collection timestamp — which makes each epoch's gradient steps chase the same structure repeatedly. Always shuffle training loaders with a reproducible seed when debugging, and for IterableDataset pipelines verify shard ordering across workers. The curve looks like instability but the root cause is dataloading, not optimizer stochasticity.

### 2.7 Warmup and "flat then drop"

Many schedules such as linear warmup or batch-norm burn-in produce a flat loss region followed by a sharp drop once effective learning rate or normalization statistics stabilize. Distinguish this expected shape from underfitting by plotting learning rate on the same axis and checking whether the drop aligns with warmup ending. Module 1.3.2 implemented warmup; this module teaches you to recognize its fingerprint so you do not rip out a working schedule thinking the model lacks capacity.

When logging, always plot **both** train and validation on the same axes, use the same loss reduction (mean per example), and log at the same frequency. Comparing a summed train loss to a mean validation loss has sent many engineers on false bug hunts.

### 2.8 How to read curves under regularization and augmentation

Module 1.3.3 introduced dropout, weight decay, and augmentation as tools that intentionally widen the train/validation gap during healthy training — the model sees harder training inputs than validation inputs by design. A modest gap is therefore not automatically overfitting. The diagnostic question is whether validation loss is **improving then degrading** (classic overfit) versus **stable but above train** (expected regularization effect). Plot a smoothed validation curve (exponential moving average over checkpoints) when batch-level noise dominates; raw step-level validation can look like random walk even when learning progresses.

Learning-rate warmup produces a characteristic flat region at the start of training that is easy to misread as underfitting. If your schedule ramps LR over the first thousand steps, compare loss against the **effective learning rate** on the same chart. When the flat region ends exactly when warmup ends and loss then drops sharply, the curve shape confirms schedule behavior rather than capacity limits. Module 1.3.2 covered warmup mechanics; here the skill is **not** reaching for more hidden units when the optimizer has not yet reached its target step size.

Multi-task and multi-loss setups add another curve-reading skill: log each loss component separately. A headline loss can decrease because an easy auxiliary task dominates while the primary task stagnates. When your model has reconstruction plus classification heads, or detection plus segmentation branches, treat each component as its own diagnostic channel before interpreting the weighted sum.

---

## Part 3: Gradient Diagnostics

Gradients are the feedback signal your optimizer consumes through the same autograd path you traced by hand in A6 and industrialized in A8. When training misbehaves, measuring gradient scale often localizes the failure faster than staring at loss alone because loss is a scalar summary that hides which layers are starving or exploding. Treat gradient norms as you would treat latency percentiles in a service mesh: the aggregate number matters, but the layer-wise breakdown tells you where to open the trace.

### 3.1 Global gradient norm as a probe

After `loss.backward()`, every parameter with a gradient contributes to a single global norm. PyTorch exposes this through `torch.nn.utils.clip_grad_norm_`, which **returns the total norm of all gradients as a 0-D `Tensor` computed before any clipping is applied** (call `.item()` for a Python float). If you pass `max_norm=float("inf")` (clips nothing), the return value is a pure probe:

```python
import torch.nn.utils as nn_utils

optimizer.zero_grad(set_to_none=True)
loss.backward()

total_norm = nn_utils.clip_grad_norm_(model.parameters(), max_norm=float("inf"))
print(f"global grad norm (pre-clip): {total_norm:.4e}")
optimizer.step()
```

Typical healthy norms vary by architecture and loss scale, but **watch the trend**: norms that grow exponentially step-over-step signal explosion; norms that shrink below `1e-7` everywhere signal vanishing. Compare against a known-good run on the same model — absolute numbers matter less than sudden regime changes.

When you actually need clipping, `clip_grad_norm_` scales all gradients so the global norm does not exceed `max_norm`, preserving direction. `clip_grad_value_` clamps each element independently and can distort direction — use norm clipping for RNNs and deep stacks unless you have a specific reason otherwise.

### 3.2 Per-layer gradient norms

Global norms hide layer-wise pathology: early layers may vanish while the head explodes. Capture per-layer norms after backward:

```python
def per_layer_grad_norms(model):
    stats = []
    for name, param in model.named_parameters():
        if param.grad is not None:
            stats.append((name, param.grad.norm().item()))
    return stats

loss.backward()
for name, gnorm in per_layer_grad_norms(model):
    print(f"{name:40s} grad_norm = {gnorm:.4e}")
```

Ratios matter: if the first layer's grad norm is `1e-10` and the last layer's is `1e2`, backprop signal is not reaching the bottom — revisit initialization (B3) and activation choices before raising learning rate.

### 3.3 Grad-to-param update ratio

Karpathy's heuristic: a healthy step has `lr * ||grad|| / ||param||` on the order of **`1e-3`** for many vision models with SGD-like optimizers. Adam adapts per-parameter, so interpret this as a sanity order-of-magnitude, not a law.

```python
def update_ratio_probe(model, lr):
    ratios = []
    for name, param in model.named_parameters():
        if param.grad is None:
            continue
        gnorm = param.grad.norm().item()
        pnorm = param.data.norm().item()
        if pnorm > 0:
            ratio = lr * gnorm / pnorm
            ratios.append((name, ratio))
    return ratios

loss.backward()
for name, r in update_ratio_probe(model, lr=1e-3):
    if "weight" in name:
        print(f"{name}: lr*||g||/||w|| = {r:.2e}")
```

If ratios are `1e-8`, learning is frozen — raise LR or fix vanishing grads. If ratios are `1e+1`, expect instability — lower LR or clip.

### 3.4 Backward hooks for persistent monitoring

For long runs, register backward hooks once:

```python
grad_history = {}

def make_grad_hook(name):
    def hook(grad):
        grad_history[name] = grad.norm().item()
        return grad
    return hook

handles = []
for name, param in model.named_parameters():
    if param.requires_grad:
        handles.append(param.register_hook(make_grad_hook(name)))
# ... training loop ...
# grad_history[name] available after backward
```

Remove hooks when done to avoid memory leaks. Forward hooks for activations are covered in Part 4 and Module 1.3.1.

### 3.5 Connecting gradient probes to Block A backprop intuition

When per-layer gradient norms decay exponentially from output to input, you are observing in numbers the same compounding effect you analyzed symbolically in A6: each layer multiplies upstream gradients by local Jacobians. A dead ReLU layer contributes zero rows to that product for units stuck at zero — which is why activation diagnostics in Part 4 belong in the same debugging session as gradient norms. PyTorch's autograd engine computes the same chain rule you derived; the probes tell you whether the computed values are numerically usable. If the last layer receives gradients of order one but the first convolution receives `1e-12`, no optimizer hyperparameter rescues representation learning in early layers — fix signal propagation (B3, B6) before opening a learning-rate sweep ticket.

Exploding gradients often appear suddenly mid-training rather than at step zero because activations drift as weights move — even with good initialization, a few unlucky batches combined with a slightly high learning rate can push activations into a regime where Jacobians grow. Logging global grad norm every step creates a time series you can align with batch content, data augmentation randomness, and LR schedule events. When explosion correlates with LR warmup ending, the fix is schedule and peak LR (B4), not architecture. When explosion appears from step one, return to Part 1.

---

## Part 4: Activation and Dead-Unit Diagnostics

Gradients depend on activations through the chain rule. Dead units — ReLU channels stuck at zero, saturated sigmoids — silently shrink effective capacity.

### 4.1 Reusing `activation_stats` from Module 1.3.1

Module 1.3.1 defined forward hooks that capture per-layer mean, standard deviation, and fraction of zeros. Extend that pattern for diagnostics:

```python
import torch
import torch.nn as nn

@torch.no_grad()
def activation_stats(model, x):
    records = []
    handles = []

    def hook(module, inp, out):
        t = out.detach()
        records.append({
            "layer": module.__class__.__name__,
            "mean": t.mean().item(),
            "std": t.std().item(),
            "pct_zero": (t == 0).float().mean().item() * 100.0,
        })

    for m in model.modules():
        if isinstance(m, (nn.Linear, nn.Conv2d)):
            handles.append(m.register_forward_hook(hook))

    model(x)
    for h in handles:
        h.remove()
    return records

# Example: batch (32, 1, 28, 28)
x = torch.randn(32, 1, 28, 28)
model.train()
stats = activation_stats(model, x)
for row in stats[:5]:
    print(row)
```

**Healthy ReLU stack after He init (B3):** per-layer `std` roughly in `[0.5, 2.0]`, `pct_zero` between 40% and 60% (ReLU zeros roughly half of symmetric inputs). **Pathological:** `pct_zero` approaching 100% in mid-network layers → dead ReLUs; `std` exploding layer-by-layer → fix init before tuning LR; `std` collapsing toward zero → vanishing signal.

### 4.2 Saturated sigmoids and tanh

For legacy or RNN stacks, check whether activations cluster at ±1 (tanh) or 0/1 (sigmoid). Saturation kills gradient flow — the same saturation problem you saw when probing `tanh` in Module 1.3.1. Normalization (B6) and Xavier init reduce saturation risk; the diagnostic is still forward-pass histograms, not guesswork.

### 4.3 Train vs eval activation drift

BatchNorm and Dropout change activations between modes. If you diagnose activations in `eval()` but train in `train()`, you are comparing different distributions. Module 1.3.4 emphasized that forgetting `.eval()` at inference destroys accuracy silently — the same toggle affects your diagnostic readings during development.

### 4.4 Histogram intuition without a plotting library

You do not need matplotlib to diagnose activation pathology during a quick terminal session. The `pct_zero` statistic from `activation_stats` approximates what a histogram would show for ReLU: near 100% zeros means almost all mass sits at a single bin. For tanh stacks, add `pct_saturated = (out.abs() > 0.99).float().mean()` in your hook — values above 30–40% saturation in mid-layers warrant Xavier init review (B3) or layer norm (B6). Compare step-zero stats against epoch-five stats on the same fixed batch; drift without normalization layers implicates the optimizer moving weights into a bad activation regime, while drift with batch norm often implicates too-small batch sizes (B6 small-batch failure mode).

Residual connections change interpretation: a ResNet block's output is `x + F(x)`, so downstream layers see a sum of identity and transformed paths. Activation std may look healthy even when `F(x)` is tiny because the identity path dominates — probe **both** the block output and intermediate `F(x)` when blocks use pre-norm (B6). This is advanced but appears often enough in vision and transformer stacks that the playbook mentions it so you do not misread healthy-looking block outputs while the residual branch has died.

---

## Part 5: The Data Is Usually the Bug

When the sanity gauntlet fails or curves look inexplicable, verify the data pipeline before blaming the model. This rule is so reliable across teams and architectures that experienced practitioners reflexively visualize a batch before they open a terminal to tweak learning rate. The model is the component you are trying to train; the dataloader is the component that decides what "training" even means, and silent bugs there propagate through every metric you trust.

### 5.1 Eyeball a batch

Denormalize images, print labels, and confirm shapes:

```python
def inspect_batch(inputs, targets, mean=(0.1307,), std=(0.3081,)):
    # Fashion-MNIST normalization — adjust for your dataset
    img = inputs[0].cpu() * std[0] + mean[0]
    print(f"input shape: {inputs.shape}")   # e.g. (64, 1, 28, 28)
    print(f"label[0]: {targets[0].item()}")
    print(f"value range after denorm: [{img.min():.3f}, {img.max():.3f}]")
```

Mis-normalized inputs (wrong mean/std constants copied from ImageNet onto medical X-rays) produce models that "train" but generalize terribly — the bug is visible the moment you visualize pixels.

### 5.2 Train/eval transform mismatch

A classic failure: random crops and flips in training, but validation forgets to resize to the same spatial size, or validation applies a different normalization. Training loss improves; validation loss is noise. Diff your `train_transform` and `val_transform` line by line.

### 5.3 `.train()` and `.eval()` toggles

Before validation, call `model.eval()`. Before training, call `model.train()`. BatchNorm uses batch statistics in train mode and running statistics in eval mode (Module 1.3.4). Dropout is active only in train mode (Module 1.3.3). Validating in train mode inflates loss variance and corrupts BN running stats; inferencing in train mode randomizes outputs.

```python
model.train()
train_one_epoch(...)

model.eval()
with torch.no_grad():
    validate(...)
```

### 5.4 Shuffling, leakage, and broken `__getitem__`

- **No shuffle:** sorted datasets produce biased batch statistics and misleading epoch curves (Part 2.6).
- **Label leakage:** features that encode the target (patient ID in metadata concatenated to inputs, future timestamps in time-series windows) make training loss plummet while deployment fails. The input-independence check (Part 1.3) helps catch gross leakage.
- **Broken `Dataset.__getitem__`:** off-by-one labels, `(C,H,W)` returned as `(H,W,C)` without permute, stale cache returning wrong pairs. Write a unit test that loads index `i` twice and asserts identical tensors.

### 5.5 Class imbalance

Cross-entropy on imbalanced data can look "healthy" while minority classes never learn. Log **per-class accuracy**, not just aggregate loss. Weighted sampling or loss weighting (B5) are fixes — but diagnosis comes from the metric breakdown, not from the headline loss.

### 5.6 Reproducible batch inspection as a unit test

Encode batch inspection into a pytest that runs once in CI for your dataset class. Load indices `[0, len//2, -1]`, assert tensor shapes, dtype, value ranges after transform, and that labels fall in `[0, num_classes-1]`. When a colleague refactors `__getitem__` and accidentally returns `(image, image)` instead of `(image, label)`, the test fails before any GPU hour is spent. This pattern mirrors how production services test API contracts — the dataloader is an API between storage and model.

Distributed training adds a subtle data bug: each rank must see a different shard with correct overlap rules. If every rank trains on identical batches, effective batch size is wrong and batch norm statistics are nonsense. Diagnosing distributed issues starts with logging `rank`, `batch_idx`, and a hash of `inputs.sum()` on rank zero — not with changing the optimizer.

### 5.7 When the model "works" in notebooks but fails in scripts

Notebook globals hide bugs: a `model` left in `eval()` from yesterday's inference cell poisons today's training cell; a `transform` defined in one cell differs from the script's import path; `%matplotlib inline` makes you visualize the wrong tensor slice. When notebook and script diverge, diff the **exact** `Dataset`, `DataLoader`, and mode toggles line by line. The playbook treats scriptable, logged training as the source of truth and notebooks as exploratory — not because notebooks are bad, but because they skip the reproducibility contracts Module 1.3 established.

---

## Part 6: LR Finding and Schedules as Diagnostics

Module 1.3.2 taught optimizers and the LR range test as a **tuning** tool. Here we treat it as a **diagnostic**: the shape of the loss-versus-LR curve tells you whether your baseline LR is in the wrong decade.

### 6.1 LR range test (Smith 2017)

Sweep learning rate exponentially from `1e-7` to `10` over ~200 steps; plot loss vs LR on a log axis. The loss falls sharply in a "good" band, then diverges. Choose an LR near the steepest descent point, typically **one decade below** the divergence cliff.

```python
import torch
import torch.optim as optim

def lr_range_test(model, loader, loss_fn, device, start_lr=1e-7, end_lr=10, num_steps=200):
    model.train()
    optimizer = optim.SGD(model.parameters(), lr=start_lr)
    lr_mult = (end_lr / start_lr) ** (1 / num_steps)

    lrs, losses = [], []
    data_iter = iter(loader)
    lr = start_lr

    for step in range(num_steps):
        try:
            inputs, targets = next(data_iter)
        except StopIteration:
            data_iter = iter(loader)
            inputs, targets = next(data_iter)

        inputs, targets = inputs.to(device), targets.to(device)

        optimizer.param_groups[0]["lr"] = lr
        optimizer.zero_grad(set_to_none=True)
        logits = model(inputs)
        loss = loss_fn(logits, targets)
        loss.backward()
        optimizer.step()

        lrs.append(lr)
        losses.append(loss.item())
        lr *= lr_mult

        if step > 10 and loss.item() > 4 * min(losses[-10:]):
            print(f"Early stop at step {step}: loss diverging")
            break

    return lrs, losses
```

If the curve never enters a descending region, suspect **underfitting/architecture** or **data bugs** (return to Part 1 and Part 5) before blaming "LR too low." If descent starts at unusually high LR, your init and normalization may be unusually well-scaled (B3, B6).

### 6.2 Reading schedules as diagnostics

Apply a schedule only after a baseline constant-LR run proves the stack learns. When adding warmup:

- **Flat loss during warmup then drop:** expected if warmup starts from near-zero LR (Part 2.7).
- **Flat loss after warmup ends:** LR may still be too low, or regularization dominates (B5).
- **Spike exactly when warmup ends:** target LR is too high — reduce peak LR or lengthen warmup (B4).

Cosine annealing that never improves validation metrics over a plain constant LR is a sign the **bottleneck is not LR shape** — revisit data and capacity.

### 6.3 Optimizer vs data: decision heuristic

If **lr_find** shows a wide good band but full-dataset training fails while overfit-one-batch passes, suspect **data augmentation too strong**, **train/val mismatch**, or **regularization** — not the optimizer family. If lr_find fails immediately but overfit-one-batch also fails, suspect **implementation bugs** first. If overfit passes but lr_find diverges at moderate LR, suspect **init/activation pathology** (Parts 3–4, B3) before switching from AdamW to SGD.

### 6.4 Schedules as controlled experiments

Treat every schedule change as an A/B experiment with one variable. If you add cosine annealing and validation improves, you still do not know whether cosine helped or whether the implicit LR reduction fixed a too-high constant LR. The diagnostic discipline is: establish a constant-LR baseline that passes the sanity gauntlet and shows monotonic-ish train improvement; then add the schedule and compare **validation AUC at equal wall-clock**, not just final epoch. Module 1.3.2 listed schedule implementations; this module asks you to interpret their **effect on curves** rather than adopting them by default because a blog post used cosine.

One-cycle schedules (Smith's cyclical LR family) can mask data bugs temporarily by sweeping through productive LR regions every cycle — loss drops each cycle then rises when LR peaks. If you see rhythmic loss oscillation aligned with cycle period, confirm with lr_find whether the baseline constant LR sits in a viable band before attributing oscillation to overfitting or batch noise.

---

## Part 7: Instrumentation, Tooling, and the Decision Tree

Professional training runs are **observable**. You should be able to answer, from logs alone: what was the loss, the LR, the grad norm, and the validation metric at step *t*?

### 7.1 Minimal metrics loop

```python
import torch.nn.utils as nn_utils
from torch.utils.tensorboard import SummaryWriter

writer = SummaryWriter(log_dir="runs/diagnostic-demo")
global_step = 0

for epoch in range(num_epochs):
    model.train()
    for inputs, targets in train_loader:
        inputs, targets = inputs.to(device), targets.to(device)
        optimizer.zero_grad(set_to_none=True)
        logits = model(inputs)
        loss = loss_fn(logits, targets)
        loss.backward()

        grad_norm = nn_utils.clip_grad_norm_(model.parameters(), max_norm=float("inf"))  # probe: measures norm, clips nothing
        optimizer.step()

        writer.add_scalar("train/loss", loss.item(), global_step)
        writer.add_scalar("train/grad_norm", grad_norm.item(), global_step)
        writer.add_scalar("train/lr", optimizer.param_groups[0]["lr"], global_step)
        global_step += 1

    model.eval()
    with torch.no_grad():
        val_loss = 0.0
        for inputs, targets in val_loader:
            inputs, targets = inputs.to(device), targets.to(device)
            val_loss += loss_fn(model(inputs), targets).item() * inputs.size(0)
        val_loss /= len(val_loader.dataset)
    writer.add_scalar("val/loss", val_loss, epoch)

writer.close()
# tensorboard --logdir runs/
```

Weights & Biases (`wandb.log`) follows the same pattern — describe in prose, do not require an account for this module. This loop **measures** grad norm with `max_norm=float("inf")` (clips nothing); set a finite `max_norm` only when you intend to clip. Logging the pre-clip return value lets you see explosions that clipping would otherwise hide.

### 7.2 Model shape sanity with `torchinfo`

Before debugging training, confirm parameter counts and output shapes:

```python
from torchinfo import summary

summary(model, input_size=(64, 1, 28, 28), col_names=("output_size", "num_params"))
```

A logits layer with output size `(batch, 9)` for ten classes is a one-line typo that wastes days.

### 7.3 NaN tracing with `set_detect_anomaly`

When loss becomes NaN, enable anomaly detection to pinpoint the backward op:

```python
torch.autograd.set_detect_anomaly(True)
# next backward() raises with forward stack trace
```

This is slow — use on one failing batch, not for full training. Module 1.3.6 explains **why** operations produce NaNs at the float level; this flag tells you **where**.

### 7.4 Consolidated diagnostic decision tree

| Symptom | First instrument | Likely cause | Fix module / action |
|---------|------------------|--------------|---------------------|
| Loss NaN step 1–100 | Expected init loss + `set_detect_anomaly` | Bad loss contract, overflow, LR too high | Part 1.1; B4; B8 |
| Cannot overfit one batch | Overfit test + per-layer grad norms | Frozen params, label bug, wrong loss | Part 1.2; Part 5 |
| Loss OK with zeroed inputs | Input-independence check | Leakage or ignored features | Part 5.4 |
| Train ↓ val ↑ | Train/val curve shape | Overfitting | B5 regularization |
| Both curves flat high | Curve shape + overfit test | Underfitting / LR too low | B4; capacity |
| Loss spikes mid-run | Global grad norm trend | LR too high / explosion | B4; `clip_grad_norm_` |
| Grad norm → 0 in early layers | Per-layer grad norms + activation_stats | Vanishing signal | B3 init; B6 norm |
| 100% ReLU zeros mid-net | activation_stats `pct_zero` | Dead units | B3 init; lower LR; B6 |
| Val metrics random | Inspect batch + `.eval()` toggle | Transform mismatch; BN in train mode | Part 5; B6 |
| Sawtooth epoch loss | Loader shuffle audit | Unshuffled data | Part 5.4 |
| Slow but stable descent | LR range test | LR too low | B4 |
| Divergence only at high LR in sweep | LR range test plot | LR too high at current setting | B4 |

ASCII flow for quick reference:

```
Training looks wrong
        |
        v
  Run sanity gauntlet (Part 1)
        |
   fails -----> fix data/loss/loop (Part 5) --> retry
        |
     passes
        |
        v
  Read train vs val curves (Part 2)
        |
        +-- val rises --> B5 regularization
        +-- both flat --> lr_find (Part 6) + capacity
        +-- spikes/NaN --> grad norms (Part 3) + B4
        |
        v
  Still stuck? activation_stats (Part 4) + log everything (Part 7)
```

### 7.5 Building a personal diagnostic checklist file

Copy the decision tree into a `TRAINING_DEBUG.md` beside your experiment config. Before each run, check boxes: gauntlet passed, train and val logged with same reduction, grad norm logged, `model.eval()` on validation confirmed in code review. After each failed run, append one line: symptom, instrument, root cause. Over months this file becomes more valuable than any hyperparameter spreadsheet because it captures **your** codebase's recurring bugs — the transform that breaks every time someone copies ImageNet constants, the forgotten `eval()` in the validation helper, the DataLoader worker seed issue that only appears on multi-GPU. The playbook is generic; your checklist makes it specific.

Module 1.3.6 will explain numerical stability — mixed precision, loss scaling, and why `softmax` plus `log` produces NaNs at the bit level. When `set_detect_anomaly` points at a particular backward op, read B8 for the float-level why; when loss goes NaN without a clear op trace, return to this playbook's ordering: gauntlet, curves, grads, activations, data, LR, then precision.

---

## Did You Know?

- **Karpathy's recipe** explicitly recommends starting with a tiny subset (e.g., 10 examples) before the full overfit-one-batch test — the subset confirms labels visually; the one-batch test confirms gradients.
- **`clip_grad_norm_` returns a 0-D `Tensor`** holding the total norm (call `.item()` for a Python float) **before** clipping; monitoring that return value is officially supported usage, not a side effect — see PyTorch docs for `torch.nn.utils.clip_grad_norm_`.
- **Expected initial CE** assumes roughly zero-mean logits; if your final layer bias is initialized to large positive values for one class, initial loss deviates from `log(C)` even when code is correct — another reason to log init loss, not assume it.
- **CS231n's "babysitting" notes** predate Karpathy's post but agree on the same hierarchy: get the loss going down on a small dataset before scaling — independent convergence of practical wisdom across institutions.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Skipping overfit-one-batch before long runs | Wastes GPU on unfixable pipeline bugs | Part 1.2 on every new project |
| Comparing init loss to `log(C)` without checking label range | False alarm or missed off-by-one labels | Verify `targets.min()`, `targets.max()`, `num_classes` |
| Using `clip_grad_norm_` return value after aggressive clip without logging pre-clip norm | Explosions hidden by clipping | Log return value; temporarily set high `max_norm` to probe |
| Diagnosing activations in wrong mode | BN/Dropout distort readings | Match `train()`/`eval()` to the phase you are debugging |
| Tuning LR when gauntlet fails | Optimizer cannot fix wrong labels | Fix Part 1/5 first |
| Logging train sum vs val mean | Apparent divergence is a math artifact | Same reduction for both curves |
| Running `set_detect_anomaly(True)` for full epochs | 10–100× slowdown | One failing batch only |
| Ignoring per-class metrics on imbalanced data | Headline loss hides failure on minorities | Confusion matrix / per-class accuracy |

---

## Quiz

1. **Why should initial cross-entropy loss be near `ln(C)` for a balanced C-class classifier with random logits?**

   <details>
   <summary>Answer</summary>

   Random roughly symmetric logits produce softmax probabilities near `1/C` for each class. Cross-entropy per example is `-log(1/C) = log(C)`. Deviations implicate wrong `num_classes`, mis-specified loss, label smoothing, or logits that are not raw scores. This is the same math you implemented in A5's stable softmax-CE.

   </details>

2. **When you compare train and validation loss curves, what shape indicates overfitting versus underfitting?**

   <details>
   <summary>Answer</summary>

   **Overfitting:** training loss continues to fall while validation loss rises after an initial decrease — the signature Module 1.3.3 addresses with regularization. **Underfitting:** both curves stay high and flat — capacity, learning rate, or excessive regularization. Healthy convergence shows both decreasing with a modest stable gap. LR-too-high shows spikes or NaN; LR-too-low shows painfully slow descent.

   </details>

3. **What does the overfit-one-batch test prove, and what does it not prove?**

   <details>
   <summary>Answer</summary>

   It proves the training loop, backward pass, optimizer update, loss function, and label-input alignment can drive loss to near zero on a tiny memorizable set — the same contract test from Module 1.3 and A7. It does **not** prove generalization, correct augmentation, or that hyperparameters are optimal for the full dataset.

   </details>

4. **What does `torch.nn.utils.clip_grad_norm_(params, max_norm)` return, and why does that matter for diagnostics?**

   <details>
   <summary>Answer</summary>

   It returns the total norm of all gradients **before** any clipping is applied (a 0-D `Tensor`; call `.item()` for a Python float). You can call it with `max_norm=float("inf")` to measure global gradient scale without altering updates, or log the pre-clip norm while using clipping as a fix for explosions. Per-layer activation statistics from forward hooks complement this probe when dead ReLUs block gradient flow to early layers.

   </details>

5. **Train loss falls while validation loss rises. What is the most likely diagnosis and first fix?**

   <details>
   <summary>Answer</summary>

   Overfitting: the model memorizes training noise. First fixes are regularization tools from Module 1.3.3 — dropout, weight decay, early stopping, data augmentation — not a higher learning rate or deeper network.

   </details>

6. **Why must you call `model.eval()` before validation when BatchNorm is present?**

   <details>
   <summary>Answer</summary>

   BatchNorm uses mini-batch statistics in train mode and frozen running mean/variance in eval mode (Module 1.3.4). Validating in train mode adds noise and corrupts running stats; inference in train mode yields stochastic wrong outputs.

   </details>

7. **How do you interpret an LR range test where loss never decreases before diverging?**

   <details>
   <summary>Answer</summary>

   The problem is unlikely to be "LR slightly too high." Return to sanity gauntlet and data inspection — label bugs, frozen parameters, or insufficient model capacity often prevent any LR from helping. Only after overfit-one-batch passes should lr_find guide LR selection (Module 1.3.2).

   </details>

8. **How do you run a learning-rate range test as a diagnostic instrument, and when do you assemble TensorBoard logging with the consolidated decision tree?**

   <details>
   <summary>Answer</summary>

   **Run** the range test by sweeping learning rate exponentially while logging loss (Smith 2017 / Module 1.3.2) — the steepest descent region locates a viable LR band before full training. **Assemble** observability by logging train/val loss, grad norm, and LR each step via TensorBoard `SummaryWriter`, then map symptoms through the Part 7 decision tree. Use `torch.autograd.set_detect_anomaly(True)` on a single failing batch when NaNs appear; Module 1.3.6 explains float-level causes. When lr_find fails but the gauntlet passes, suspect the data pipeline over the optimizer.

   </details>

---

## Hands-On Exercise

Build a miniature diagnostic report for a deliberately buggy training setup, then fix it using the playbook. Train a small MLP on Fashion-MNIST (or synthetic data) with PyTorch 2.12, and introduce **one** bug at a time: (a) learning rate `1.0`, (b) training loader **without** shuffling (sorted, correlated batches), (c) forget `model.eval()` during validation, (d) freeze the first linear layer's weights.

Follow these steps in order. First, run the sanity gauntlet from Part 1: print expected versus observed init loss, run overfit-one-batch for 200 steps, and run the input-independence check — interpret each result before changing hyperparameters. Second, train for five epochs while logging train and validation loss plus global grad norm using the Part 7.1 loop to TensorBoard or a CSV so you can compare canonical curve shapes from Part 2. Third, for each injected bug, fill one row of the Part 7.4 decision tree with symptom, instrument, diagnosis, and fix, citing the Block B module that owns the fix. Fourth, remove the bug and confirm curves return to healthy convergence shape, noting which instrument detected each bug fastest.

You succeed when documented init loss sits within 0.2 of `ln(10)` for ten-class CE in the bug-free baseline, overfit-one-batch reaches loss below 0.1 with regularization disabled, each injected bug is identified using at most two playbook instruments, and the decision tree table contains four completed rows. Before closing the exercise, confirm every deliverable in the list below passes — all four items must be satisfied before you claim the playbook exercise complete.

- [ ] Documented init loss within 0.2 of `ln(10)` for 10-class CE when bug-free
- [ ] Overfit-one-batch reaches loss `< 0.1` when bug-free and regularization disabled
- [ ] Identified each injected bug using at most two instruments from the playbook
- [ ] Decision tree table completed with four rows (one per bug)

Confirm programmatically with the assertions below after restoring the bug-free baseline.

```python
import math
assert abs(initial_loss - math.log(10)) < 0.2
assert overfit_final_loss < 0.1
print("Diagnostic exercise checks passed.")
```

---

## Key Takeaways

- Run the **sanity gauntlet** (expected init loss, overfit one batch, input-independence) before scaling experiments — most failures are pipeline bugs, not architecture limits.
- **Loss-curve shape** localizes underfitting, overfitting, LR mismatch, and data ordering problems; always plot train and validation with the same reduction.
- **Gradient norms** — global and per-layer — plus Karpathy's `lr * ||g|| / ||param||` heuristic reveal vanishing and exploding signal before loss goes NaN; `clip_grad_norm_`'s return value is your pre-clip probe.
- **Activation stats** via forward hooks catch dead ReLUs and drift; connect fixes to initialization (B3) and normalization (B6), not random LR sweeps.
- **Verify data** (visualize batches, diff transforms, shuffle, `.train()`/`.eval()`) before blaming the optimizer — the data is usually the bug.
- **LR range tests and schedules** are diagnostic instruments: interpret their failure modes with the decision tree, and forward NaN arithmetic questions to Module 1.3.6.

---

## Sources

- Karpathy, A. (2019). *A Recipe for Training Neural Networks*. https://karpathy.github.io/2019/04/25/recipe/
- Smith, L. N. (2017). *Cyclical Learning Rates for Training Neural Networks*. https://arxiv.org/abs/1506.01186
- Stanford CS231n. *Neural Networks Part 2: Setting up the data and the model*. https://cs231n.github.io/neural-networks-2/
- PyTorch 2.12 documentation: `torch.nn.utils.clip_grad_norm_`. https://pytorch.org/docs/stable/generated/torch.nn.utils.clip_grad_norm_.html
- PyTorch 2.12 documentation: `torch.nn.utils.clip_grad_value_`. https://pytorch.org/docs/stable/generated/torch.nn.utils.clip_grad_value_.html
- PyTorch 2.12 documentation: `torch.autograd.set_detect_anomaly`. https://pytorch.org/docs/stable/generated/torch.autograd.set_detect_anomaly.html
- PyTorch 2.12 documentation: TensorBoard `SummaryWriter`. https://pytorch.org/docs/stable/tensorboard.html
- PyTorch 2.12 documentation: Forward and backward hooks. https://pytorch.org/docs/stable/notes/autograd.html#backward-hooks
- `torchinfo` documentation. https://github.com/TylerYep/torchinfo
- Weights & Biases documentation: Logging metrics. https://docs.wandb.ai/guides/track

---

## Next Module

Continue to [Numerical Stability & Precision](/ai-ml-engineering/deep-learning/module-1.3.6-numerical-stability-precision/) — where NaNs, mixed precision, and float-level arithmetic explain failures that this playbook helps you localize but does not fully derive.

---

## Learner check

> | 1.3.5 | [Training-Diagnostics Playbook](/ai-ml-engineering/deep-learning/module-1.3.5-training-diagnostics-playbook/) |
