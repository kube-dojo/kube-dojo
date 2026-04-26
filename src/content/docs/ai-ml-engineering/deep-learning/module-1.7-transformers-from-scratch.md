---
title: "Transformers from Scratch"
slug: ai-ml-engineering/deep-learning/module-1.7-backpropagation-and-autograd-from-scratch
sidebar:
  order: 1008
---
> **AI/ML Engineering Track** | Complexity: `[COMPLEX]` | Time: 8-10 hours

# Backpropagation and Autograd from Scratch

**Reading Time**: 6-7 hours  
**Prerequisites**: Python, NumPy basics, derivatives, matrix multiplication, and prior neural-network training modules

---

## Learning Outcomes

By the end of this module, you will be able to:

- **Trace and debug** gradient flow through scalar and vector computation graphs, including branches where gradients must be accumulated rather than overwritten.
- **Implement and validate** a small reverse-mode automatic differentiation engine that supports arithmetic operations, nonlinearities, and topological backpropagation.
- **Compare and justify** reverse-mode autodiff, forward-mode autodiff, and finite-difference gradient checking for practical neural-network workloads.
- **Diagnose and fix** vanishing gradients, exploding gradients, dead activations, stale accumulated gradients, and numerical instability in training loops.
- **Design and evaluate** a gradient-debugging workflow that moves from one-batch overfitting to gradient statistics, gradient checking, and targeted remediation.

---

## Why This Module Matters

A team ships a model that performed well in a notebook, but the production training job quietly stops learning after a refactor. The loss value still prints every epoch, the GPU stays busy, and no exception is raised, yet the validation curve is flat. One engineer suspects the optimizer. Another blames the data pipeline. A third starts changing model depth, learning rates, and batch sizes without knowing whether any parameter is receiving a useful gradient.

The senior engineer asks for one small experiment: overfit a single batch, print gradient norms by layer, and check the custom loss with finite differences. Within minutes, the team finds the cause. A tensor was detached inside a helper function, so the graph ended before the custom scoring layer. The optimizer was stepping, but the most important weights never received gradient signal.

That failure is why backpropagation and autograd are not merely mathematical background. They are operational tools. Anyone can call `loss.backward()`, but engineers who understand what it does can inspect broken training loops, write custom layers safely, validate new losses, and explain why a model is or is not learning. This module keeps the historical frontmatter title for platform compatibility, but the actual topic is the mechanism underneath deep learning: backpropagation through computational graphs and the autograd systems that automate it.

---

## From Loss to Learning Signal

Training a neural network is not just running a model many times. It is an optimization loop that uses the loss to decide how each parameter should move. If the loss is high, the optimizer does not know which weight caused the problem by looking at the final number alone. It needs a derivative for each trainable parameter, and that derivative answers a precise question: if this parameter changes slightly, how does the loss change?

For a small model, you could derive every derivative by hand. For a modern model, that approach collapses immediately because the computation contains millions or billions of parameters and many repeated operations. Backpropagation solves the scaling problem by applying the chain rule systematically from the output backward through the graph. Autograd systems, such as PyTorch autograd, make the process programmable by recording operations during the forward pass and replaying their derivative rules during the backward pass.

A single training step has four distinct phases. The forward pass computes predictions and loss. The backward pass computes gradients. The optimizer updates parameters using those gradients. The next iteration starts only after old gradients have been cleared, because most frameworks accumulate gradients by default. Many real bugs come from mixing these phases, especially forgetting to clear gradients or accidentally breaking the computation graph before the loss.

```
Input batch
    |
    v
+------------------+
| Forward pass     |
| predictions      |
| loss             |
+------------------+
    |
    v
+------------------+
| Backward pass    |
| gradients        |
| dLoss/dParam     |
+------------------+
    |
    v
+------------------+
| Optimizer step   |
| updated weights  |
+------------------+
    |
    v
Clear gradients before the next accumulation window
```

**Pause and predict:** If a model calls `optimizer.step()` but a parameter has `param.grad is None`, will that parameter update? Before reading on, decide whether the optimizer can infer a missing gradient from the loss value alone. The answer is no: optimizers consume stored gradient tensors, and a missing gradient usually means the parameter was not connected to the loss or was deliberately excluded from the graph.

The simplest useful mental model is "local derivative times upstream gradient." Each operation knows only its local derivative. Multiplication knows how its output changes with respect to each input. Addition knows that both inputs receive the same upstream signal. A square knows that its derivative is twice the input. Backpropagation composes those local facts into a global derivative from the loss to every earlier value.

---

## Chain Rule on a Computation Graph

The chain rule is the foundation of backpropagation because neural networks are nested functions. A parameter affects a pre-activation, the pre-activation affects an activation, the activation affects the next layer, and eventually all those effects reach the loss. The derivative of the loss with respect to the parameter is the product of the derivative along each step in that path, with sums where multiple paths join.

Consider the scalar expression `L = (x * w + b) ** 2`. This expression is small enough to solve by hand, but it contains the same structural pieces as a neural network: multiplication, addition, nonlinearity, and a scalar loss. The forward pass computes intermediate values. The backward pass starts from `dL/dL = 1` and walks backward through the same intermediate values.

```python
x = 2.0
w = 3.0
b = 1.0

z1 = x * w
z2 = z1 + b
loss = z2 ** 2

print(z1, z2, loss)
```

At these values, `z1 = 6`, `z2 = 7`, and `loss = 49`. The derivative of the square with respect to `z2` is `2 * z2`, so the upstream gradient reaching `z2` is `14`. Addition passes that gradient unchanged to both inputs. Multiplication sends `upstream * other_input` to each side, so `dL/dx = 14 * w = 42` and `dL/dw = 14 * x = 28`.

```text
                 upstream gradient starts here
                              |
                              v
    x=2        w=3         z1=6        b=1        z2=7        L=49
     \          /            |          /           |           |
      \        /             |         /            |           |
       [ multiply ] -------->[ add    ] ---------->[ square    ]
       local: dz1/dx=w       local: dz2/dz1=1      local: dL/dz2=2*z2
       local: dz1/dw=x       local: dz2/db=1
```

When a value feeds multiple downstream operations, gradients must be accumulated. This is not a minor implementation detail. If a variable contributes to the loss through two different paths, the total derivative is the sum of path contributions. A correct autograd engine uses `+=` during local backward rules because each child operation may add another piece of the final derivative.

**Stop and think:** Suppose `y = x * x + x`. How many paths connect `x` to `y`, and what goes wrong if an autograd engine assigns `x.grad = ...` instead of adding with `x.grad += ...`? There are three contributions: one from the left side of the multiplication, one from the right side, and one from the addition. Overwriting keeps only the most recent contribution and silently produces the wrong derivative.

The same accumulation rule appears in deep networks. A shared embedding table, residual branch, tied output projection, or reused tensor can receive gradient through multiple routes. The graph may look larger, but the rule remains the same: each operation contributes its local derivative multiplied by the upstream gradient, and a node sums all contributions that arrive from its consumers.

---

## Reverse-Mode Autograd by Hand

Automatic differentiation is different from symbolic differentiation and numerical differentiation. Symbolic differentiation manipulates formulas, which can become enormous. Numerical differentiation perturbs inputs and estimates slopes, which is simple but slow and approximate. Autograd evaluates the original program while recording a graph of primitive operations, then applies exact local derivative rules to that recorded graph.

Reverse-mode autograd is especially useful for neural networks because training usually maps many parameters to one scalar loss. A model may have millions of inputs to the objective and only one output loss. Reverse mode computes all parameter gradients with one backward traversal after one forward pass. Forward mode is useful in other settings, but for "many parameters, one loss," reverse mode is the practical winner.

| Method | How it works | Best fit | Main trade-off |
|---|---|---|---|
| Symbolic differentiation | Rewrites formulas into derivative formulas | Small closed-form math | Can create huge expressions |
| Finite differences | Perturbs inputs and estimates slopes numerically | Checking tiny examples | Slow and approximate |
| Forward-mode autodiff | Pushes derivative information forward with values | Few inputs, many outputs | Expensive for many parameters |
| Reverse-mode autodiff | Pulls gradients backward from outputs | Many inputs, scalar loss | Must store or recompute graph context |

A computation graph must be processed in reverse topological order. "Topological" means children appear before the node that depends on them during the forward construction. During backward execution, the order reverses so every node receives its full upstream gradient before it distributes contributions to its parents. Without this ordering, a parent may backpropagate too early and miss a contribution from another downstream branch.

```python
class Value:
    """Scalar value with enough history to support reverse-mode autodiff."""

    def __init__(self, data, _children=(), _op=""):
        self.data = float(data)
        self.grad = 0.0
        self._prev = set(_children)
        self._op = _op
        self._backward = lambda: None

    def __repr__(self):
        return f"Value(data={self.data:.6f}, grad={self.grad:.6f})"

    def __add__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data + other.data, (self, other), "+")

        def _backward():
            self.grad += out.grad
            other.grad += out.grad

        out._backward = _backward
        return out

    def __mul__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data * other.data, (self, other), "*")

        def _backward():
            self.grad += out.grad * other.data
            other.grad += out.grad * self.data

        out._backward = _backward
        return out

    def __pow__(self, exponent):
        if not isinstance(exponent, (int, float)):
            raise TypeError("only numeric powers are supported")
        out = Value(self.data ** exponent, (self,), f"**{exponent}")

        def _backward():
            self.grad += out.grad * exponent * (self.data ** (exponent - 1))

        out._backward = _backward
        return out

    def __neg__(self):
        return self * -1

    def __sub__(self, other):
        return self + (-other)

    def __radd__(self, other):
        return self + other

    def __rmul__(self, other):
        return self * other

    def tanh(self):
        import math

        t = math.tanh(self.data)
        out = Value(t, (self,), "tanh")

        def _backward():
            self.grad += out.grad * (1 - t * t)

        out._backward = _backward
        return out

    def relu(self):
        out = Value(max(0.0, self.data), (self,), "relu")

        def _backward():
            self.grad += out.grad * (1.0 if self.data > 0 else 0.0)

        out._backward = _backward
        return out

    def backward(self):
        topo = []
        visited = set()

        def build_topo(node):
            if node not in visited:
                visited.add(node)
                for child in node._prev:
                    build_topo(child)
                topo.append(node)

        build_topo(self)
        self.grad = 1.0

        for node in reversed(topo):
            node._backward()
```

This class is intentionally small, but it captures the essential design. Each operation creates a new `Value`, stores references to the input values, and installs a closure that knows how to pass the output gradient into the inputs. The `backward()` method builds a topological order from the final loss and then executes the closures backward. The closures are local derivative rules; the traversal composes them into full derivatives.

```python
x = Value(2.0)
w = Value(3.0)
b = Value(1.0)

loss = (x * w + b) ** 2
loss.backward()

print(loss)
print(x)
print(w)
print(b)
```

A correct run prints gradients matching the hand calculation: `x.grad` is `42`, `w.grad` is `28`, and `b.grad` is `14`. If those values do not match, the bug is likely in one of three places: a local derivative rule, missing gradient accumulation, or backward traversal order. This is a practical debugging pattern for custom autograd code because small scalar examples are easier to reason about than full tensor models.

**Pause and predict:** In the `__mul__` backward rule, why does `self.grad` receive `out.grad * other.data` instead of `out.grad * self.data`? Test the expression `x * w` at `x = 2` and `w = 3` mentally. If `x` wiggles, the output changes by `w` times that wiggle, so the derivative with respect to `x` is the other input.

---

## Worked Example: A Tiny Neural Network

A neural network layer combines a linear transformation with a nonlinearity. The forward formula is usually written as `a = activation(Wx + b)`. During backpropagation, the loss gradient first passes through the activation, then through the affine transform, and finally reaches the weights, bias, and previous layer activation. The order matters because each derivative is evaluated at the forward-pass values.

The following NumPy example implements a two-layer network for one training example. It is not meant to be a high-performance trainer. It is meant to expose the shapes and gradient formulas so you can inspect each intermediate tensor. Once you understand this version, framework autograd becomes less mysterious because it automates the same sequence of local derivative applications.

```python
import numpy as np

np.random.seed(42)

W1 = np.random.randn(3, 2) * 0.1
b1 = np.zeros((3, 1))
W2 = np.random.randn(1, 3) * 0.1
b2 = np.zeros((1, 1))

x = np.array([[1.0], [2.0]])
target = np.array([[1.0]])

z1 = W1 @ x + b1
a1 = np.maximum(0.0, z1)
z2 = W2 @ a1 + b2
pred = z2
loss = 0.5 * (pred - target) ** 2

dL_dpred = pred - target
dL_dz2 = dL_dpred

dL_dW2 = dL_dz2 @ a1.T
dL_db2 = dL_dz2
dL_da1 = W2.T @ dL_dz2

dL_dz1 = dL_da1 * (z1 > 0.0)
dL_dW1 = dL_dz1 @ x.T
dL_db1 = dL_dz1
dL_dx = W1.T @ dL_dz1

print("loss:", float(loss))
print("dL_dW2 shape:", dL_dW2.shape)
print("dL_dW1 shape:", dL_dW1.shape)
print("dL_dx shape:", dL_dx.shape)
```

The weight-gradient shapes reveal the structure. `dL_dW2` has the same shape as `W2`, and `dL_dW1` has the same shape as `W1`. That is not coincidence; optimizers update each parameter with a gradient tensor of matching shape. When a gradient has the wrong shape, a transpose, reduction, or broadcasting operation was probably placed incorrectly in the backward derivation.

```
                 backward direction
                       <--------
+---------+     +------------+     +------+     +------------+     +------+
| input x | --> | z1 = W1x+b | --> | ReLU | --> | z2 = W2a+b | --> | loss |
+---------+     +------------+     +------+     +------------+     +------+
      |                |              |                |               |
      |                |              |                |               |
      v                v              v                v               v
   dL/dx           dL/dW1,dL/db1   ReLU mask       dL/dW2,dL/db2    dL/dL=1
```

**Stop and think:** If every element of `z1` is negative for every training example, what happens to `dL_dW1` through ReLU? The ReLU mask becomes zero, so gradients into that hidden unit vanish. This is the dead ReLU problem: the unit outputs zero and receives no gradient through the standard ReLU derivative.

The worked example also shows why cached forward values are necessary. The ReLU backward pass needs to know which `z1` elements were positive. The matrix multiplication backward pass needs the input activation to compute the weight gradient. Autograd engines store enough context during the forward pass to evaluate backward rules later, which is why training uses more memory than inference.

---

## Gradient Checking and Trustworthy Custom Code

Gradient checking is the engineering practice of comparing an analytical gradient from backpropagation with a numerical finite-difference estimate. It is too slow for normal training, but it is excellent for validating a custom layer, custom loss, or small autograd engine. The key is to check a tiny deterministic example where you can tolerate many forward passes.

Finite differences estimate a derivative by evaluating the function on both sides of the current value. The centered version is more accurate than a one-sided difference for the same small epsilon. If the analytical and numerical gradients disagree by a large relative error, the backward implementation is wrong or the function is numerically unstable near the test point.

```python
import numpy as np


def gradient_check(param, loss_and_grad, epsilon=1e-5):
    loss, analytical_grad = loss_and_grad(param)
    numerical_grad = np.zeros_like(param)

    iterator = np.nditer(param, flags=["multi_index"], op_flags=["readwrite"])
    while not iterator.finished:
        idx = iterator.multi_index
        original = param[idx]

        param[idx] = original + epsilon
        loss_plus, _ = loss_and_grad(param)

        param[idx] = original - epsilon
        loss_minus, _ = loss_and_grad(param)

        param[idx] = original
        numerical_grad[idx] = (loss_plus - loss_minus) / (2 * epsilon)
        iterator.iternext()

    numerator = np.abs(analytical_grad - numerical_grad)
    denominator = np.abs(analytical_grad) + np.abs(numerical_grad) + 1e-8
    relative_error = np.max(numerator / denominator)

    return relative_error, analytical_grad, numerical_grad


def squared_loss(W):
    loss = np.sum(W ** 2)
    grad = 2 * W
    return loss, grad


np.random.seed(7)
W = np.random.randn(3, 4)
error, analytical, numerical = gradient_check(W, squared_loss)

print("relative error:", error)
```

A useful gradient check isolates the operation being tested. If you check an entire large network, many unrelated operations can hide the bug. Start with one operation, one parameter tensor, and a deterministic seed. Once the local derivative passes, integrate it into a slightly larger computation and check again. This staged approach mirrors how senior engineers debug production training: narrow the suspected surface before adding complexity.

There are cases where gradient checking can mislead you. ReLU is not differentiable exactly at zero, so finite differences near zero may disagree with the framework's chosen subgradient. Very small epsilons can amplify floating-point noise, while very large epsilons stop approximating the local slope. Stochastic layers, dropout, random data augmentation, and nondeterministic kernels must be controlled or disabled before comparison.

**Pause and predict:** If you run gradient checking with dropout enabled, should you trust a mismatch between analytical and numerical gradients? You should not trust it until the randomness is removed, because the two finite-difference evaluations may be measuring different functions. Gradient checking assumes that only the perturbed parameter changes.

---

## Debugging Gradient Pathologies

Most gradient failures fall into a small set of patterns. The symptoms may appear as flat loss, exploding loss, `NaN` values, unstable validation, or layers that never learn. The productive response is not to randomly change hyperparameters. The productive response is to form a diagnosis from gradient statistics, forward-value ranges, and controlled experiments.

| Pattern | Typical symptom | Likely mechanism | First checks |
|---|---|---|---|
| Vanishing gradients | Early layers learn slowly or not at all | Repeated derivatives smaller than one shrink signal | Activation choice, initialization, residual paths |
| Exploding gradients | Loss jumps or becomes `NaN` | Repeated derivatives or large weights amplify signal | Gradient norms, learning rate, clipping |
| Dead ReLU units | Some channels output zero forever | Negative pre-activations make ReLU derivative zero | Bias initialization, activation stats |
| Detached graph | A parameter has `grad is None` | Tensor left the graph through detach, conversion, or no-grad context | Graph-breaking helpers, logging conversions |
| Stale accumulation | Updates grow unexpectedly over steps | Gradients were not cleared before the next backward pass | `optimizer.zero_grad()` placement |
| Unstable loss math | `NaN` or `inf` appears in loss | `log(0)`, division by zero, overflow, invalid targets | Input ranges, epsilons, stable losses |

A vanishing-gradient diagnosis should be grounded in layer-wise gradient norms, not just training disappointment. If earlier layers have gradients many orders of magnitude smaller than later layers, the signal is fading as it travels backward. Common interventions include ReLU-family activations, residual connections, normalization, and initialization schemes matched to the activation. The best fix depends on the model architecture and the evidence you collect.

Exploding gradients often show up as a sudden transition from plausible values to enormous values, then `NaN`. Gradient clipping can keep a training run alive, but clipping should not be used to hide a fundamentally unstable setup. Check the learning rate, loss scaling, input normalization, recurrent depth, and initialization. If clipping is still appropriate, prefer logging the unclipped norm so you know whether clipping is occasional protection or constant emergency braking.

```python
import torch


def summarize_gradients(model):
    rows = []
    for name, param in model.named_parameters():
        if param.grad is None:
            rows.append((name, "missing", None, None))
            continue

        grad = param.grad.detach()
        rows.append(
            (
                name,
                "present",
                float(grad.norm()),
                bool(torch.isfinite(grad).all()),
            )
        )
    return rows


def print_gradient_report(model):
    for name, status, norm, finite in summarize_gradients(model):
        if status == "missing":
            print(f"{name}: grad missing")
        else:
            print(f"{name}: norm={norm:.3e}, finite={finite}")
```

A detached graph is subtler because it may not throw an exception. Converting tensors through `.item()`, `.numpy()`, or a Python float inside the loss path can remove gradient history. Using `torch.no_grad()` around code that participates in loss computation has the same effect. The model may still run, but key parameters receive no gradient. When in doubt, inspect `requires_grad`, `grad_fn`, and whether expected parameters have non-`None` gradients after backward.

**Stop and think:** Your model trains when using PyTorch's built-in `MSELoss`, but stops learning when a custom loss helper is introduced. The helper returns `torch.tensor(loss_value)` after calling `.item()` internally. What broke? The helper created a fresh tensor from a Python number, so the returned loss is no longer connected to the model outputs. Backward has no path to the parameters.

A disciplined debugging workflow starts with one batch. If the model cannot overfit a single tiny batch, the problem is usually in the model, loss, optimizer, or gradients rather than generalization. Then inspect forward ranges, loss validity, gradient presence, gradient norms, and optimizer updates. Only after those checks pass should you tune regularization or architecture.

```python
import torch
import torch.nn as nn


def debug_one_batch(model, batch, loss_fn, optimizer):
    x, y = batch

    optimizer.zero_grad(set_to_none=True)
    output = model(x)
    loss = loss_fn(output, y)

    print("output finite:", bool(torch.isfinite(output).all()))
    print("loss:", float(loss.detach()))
    print("loss finite:", bool(torch.isfinite(loss)))

    loss.backward()
    print_gradient_report(model)

    before = {
        name: param.detach().clone()
        for name, param in model.named_parameters()
        if param.requires_grad
    }

    optimizer.step()

    for name, param in model.named_parameters():
        if name in before:
            delta = (param.detach() - before[name]).norm()
            print(f"{name}: update norm={float(delta):.3e}")
```

This function checks a full training step rather than a single isolated property. It verifies finite outputs, finite loss, gradient presence, gradient finiteness, and actual parameter movement. That sequence catches many false assumptions. A parameter may have a valid gradient but no update if it is not registered with the optimizer. A loss may be finite before backward but produce invalid gradients if the backward formula has an unstable denominator.

---

## Building Better Mental Models

Autograd is easiest to reason about when you separate values, operations, and storage. Values flow forward. Gradients flow backward. Operations define local derivative rules. Storage choices determine whether the backward pass has the information it needs. In frameworks, a tensor can have data, a gradient field, and graph metadata, but those roles should not be conflated.

The following table maps beginner questions to senior-level interpretations. The goal is not to memorize framework internals. The goal is to know which layer of the system you are debugging when training misbehaves.

| Beginner observation | Senior interpretation | Practical next step |
|---|---|---|
| "The loss is not going down." | The update direction may be wrong, missing, too small, or too large. | Inspect one-batch overfit and gradient norms. |
| "`grad` is `None`." | The parameter is disconnected, frozen, unused, or not included in the loss path. | Check `requires_grad`, graph breaks, and optimizer parameter groups. |
| "`grad` is zero." | The path exists, but local derivatives or data made the contribution zero. | Check activation masks, saturation, and loss reduction. |
| "Loss becomes `NaN`." | Some forward or backward computation produced invalid floating-point values. | Add finite checks around inputs, outputs, loss, and gradients. |
| "Gradient check fails." | A local derivative rule, nondeterminism, or numerical setting is suspect. | Disable randomness and test smaller deterministic cases. |
| "Training works only with tiny learning rate." | Gradients or curvature may be poorly scaled. | Normalize inputs, check initialization, consider clipping or adaptive optimizers. |

A senior workflow also distinguishes diagnosis from mitigation. Gradient clipping mitigates exploding gradients, but it does not explain why they exploded. Batch normalization can improve flow, but it can also hide bad initialization or input scaling. A smaller learning rate may stabilize training, but it may leave a detached branch unnoticed. The correct intervention is the one that matches the evidence.

**Pause and predict:** If two parameters have identical values but one is not passed to the optimizer, will their gradients still be computed? Gradients can be computed for both if they are connected to the loss and require gradients. The optimizer step is separate; only parameters in its parameter groups are updated.

---

## Did You Know?

1. Reverse-mode automatic differentiation was described before modern deep learning became practical, but neural networks made its value visible because they commonly optimize one scalar loss over many parameters.

2. PyTorch builds dynamic computation graphs during normal Python execution, which is why control flow such as `if` statements and loops can participate naturally in differentiable programs.

3. Gradient checkpointing reduces activation memory by discarding selected forward intermediates and recomputing them during backward, trading extra compute for lower memory pressure.

4. Finite-difference gradient checks are often more useful for small custom operations than for full models because they isolate one derivative rule and avoid unrelated numerical noise.

---

## Common Mistakes

| Mistake | Why it hurts | How to correct it |
|---|---|---|
| Treating the inherited title as the topic | The platform title may say "Transformers," but this module teaches backpropagation and autograd. | Follow the H1, outcomes, exercises, and slug; use transformer content in the appropriate attention module. |
| Forgetting `optimizer.zero_grad()` | Gradients accumulate across steps, so updates reflect old batches as well as the current one. | Clear gradients before each backward pass unless intentionally accumulating over microbatches. |
| Overwriting gradients in a custom engine | Shared values and branched graphs lose contributions from earlier backward paths. | Use `+=` in local backward functions and test expressions with reused variables. |
| Calling `.item()` inside the loss path | The value becomes a Python number and loses graph history. | Keep computations as tensors until after backward, using `.item()` only for logging. |
| Trusting a gradient check with randomness enabled | Numerical estimates compare different sampled functions rather than one deterministic function. | Disable dropout, fix seeds, and run the checked function in deterministic mode where possible. |
| Clipping gradients without logging norms | Training may appear stable while every step is being heavily clipped. | Log unclipped global norms and investigate persistent explosions. |
| Debugging only on full training runs | Many gradient bugs are hidden by data variation, schedulers, and long feedback loops. | First verify that the model can overfit one small batch. |
| Assuming `grad is None` and zero gradient mean the same thing | Missing gradients indicate no graph path or no request for gradient; zero gradients indicate a path with zero contribution. | Inspect graph connectivity separately from activation saturation and local derivatives. |

---

## Quiz

**Q1.** Your team replaces a built-in loss with a helper that computes a tensor loss, calls `.item()` for logging, and returns `torch.tensor(logged_value, requires_grad=True)`. Training continues without an exception, but all model parameters have `grad is None` after backward. What should you inspect and how should you fix the helper?

<details>
<summary>Answer</summary>

Inspect whether the returned loss is connected to the model output through `grad_fn`. The helper broke the graph by converting the loss to a Python number with `.item()` and then creating a new leaf tensor. Keep the loss as a tensor for return, and use `.detach().item()` only for logging outside the differentiable path.
</details>

**Q2.** A custom scalar autograd engine passes the simple test `L = x * w`, but fails for `L = x * x + x`. The reported gradient for `x` is too small and changes when operation order changes. Which implementation detail is most likely wrong?

<details>
<summary>Answer</summary>

The backward rules are probably overwriting `x.grad` instead of accumulating into it. In `x * x + x`, the same value contributes through multiple paths, so the total derivative is the sum of all path contributions. Local backward functions should use `+=`, and tests should include reused variables and branched graphs.
</details>

**Q3.** You add a deep stack of sigmoid layers to a model. The last layer has visible gradients, but early layers show gradient norms near zero and the one-batch overfit test fails. Which mechanism explains the failure, and what changes would you evaluate first?

<details>
<summary>Answer</summary>

The likely mechanism is vanishing gradients caused by repeatedly multiplying derivatives whose magnitudes are less than one, especially when sigmoid activations saturate. Evaluate ReLU-family activations, better initialization, normalization, residual connections, and simpler depth. Use layer-wise gradient norms to confirm that early-layer signal improves.
</details>

**Q4.** A recurrent model's loss becomes `NaN` after several hundred updates. Gradient norms grow sharply shortly before the failure, and lowering the learning rate delays but does not eliminate the problem. What debugging and mitigation sequence is justified?

<details>
<summary>Answer</summary>

First add finite checks for inputs, outputs, loss, and gradients to locate the first invalid value. Log unclipped global gradient norms to confirm explosion, then evaluate learning rate, initialization, sequence length, and normalization. Gradient clipping is a reasonable mitigation, but it should be paired with norm logging so persistent instability remains visible.
</details>

**Q5.** Your custom CUDA operation produces plausible training curves, but a small deterministic gradient check fails only when inputs are exactly near zero. The operation includes a ReLU-like kink. How should you interpret the failure?

<details>
<summary>Answer</summary>

A mismatch near a nondifferentiable point may not indicate a bug because finite differences sample both sides of the kink while the framework chooses a particular subgradient. Test points away from the kink, verify the documented subgradient convention, and compare against a reference implementation. If failures persist away from nondifferentiable points, investigate the backward rule.
</details>

**Q6.** A model has valid nonzero gradients after backward, but several parameters do not change after `optimizer.step()`. What should you check before changing the architecture?

<details>
<summary>Answer</summary>

Check whether those parameters are included in the optimizer's parameter groups and whether their learning rate is nonzero. Gradient computation and optimizer updates are separate phases. A parameter can be connected to the loss and still not update if it was omitted from the optimizer or placed in a frozen group.
</details>

**Q7.** During a memory optimization, an engineer wraps part of the forward pass in `torch.no_grad()` because it saves GPU memory. The model still runs, but the affected block stops learning. How would you explain the regression and propose a safer alternative?

<details>
<summary>Answer</summary>

`torch.no_grad()` prevents autograd from recording operations, so the loss has no backward path through that block. The block's parameters therefore receive missing gradients or incomplete gradients. For memory reduction during training, evaluate gradient checkpointing instead, which discards selected activations and recomputes them during backward while preserving differentiability.
</details>

---

## Hands-On Exercise

In this lab, you will build and validate a small autograd system, then use the same reasoning to debug a PyTorch training loop. Work in a new file such as `autograd_lab.py` or a notebook cell, but keep each step runnable independently. The goal is not to produce a production framework; the goal is to make `loss.backward()` explainable and debuggable.

### Part 1: Implement scalar reverse-mode autodiff

Start from the `Value` class in this module and add `log()` and `sigmoid()` operations. Use local backward functions that accumulate gradients. Include checks that compare your gradients with known analytical derivatives.

```python
def test_log_and_sigmoid(Value):
    x = Value(2.0)
    y = x.log()
    y.backward()
    print("log data:", y.data)
    print("log grad:", x.grad)

    z = Value(0.0)
    s = z.sigmoid()
    s.backward()
    print("sigmoid data:", s.data)
    print("sigmoid grad:", z.grad)
```

Success criteria:

- [ ] `log(2)` prints approximately `0.693` and its gradient prints approximately `0.5`.
- [ ] `sigmoid(0)` prints approximately `0.5` and its gradient prints approximately `0.25`.
- [ ] Every local backward rule uses gradient accumulation rather than replacement.
- [ ] A reused-variable test such as `y = x * x + x` produces the expected derivative.

### Part 2: Validate gradients with finite differences

Write a small finite-difference checker for scalar functions built from your `Value` class. Test at several input values away from nondifferentiable points. Compare the analytical gradient from `backward()` with the centered finite-difference estimate.

```python
def finite_difference(fn, x, epsilon=1e-5):
    return (fn(x + epsilon) - fn(x - epsilon)) / (2 * epsilon)


def check_scalar(Value, raw_x):
    x = Value(raw_x)
    y = (x * x + x.sigmoid()) * 0.5
    y.backward()

    numerical = finite_difference(
        lambda v: (v * v + 1.0 / (1.0 + __import__("math").exp(-v))) * 0.5,
        raw_x,
    )

    print("analytical:", x.grad)
    print("numerical:", numerical)
    print("absolute error:", abs(x.grad - numerical))
```

Success criteria:

- [ ] The analytical and numerical gradients are close for several deterministic inputs.
- [ ] You can explain why finite differences become less reliable at nondifferentiable points.
- [ ] You can identify whether a mismatch comes from a local derivative rule or graph traversal order.

### Part 3: Debug a broken PyTorch training loop

Create a small PyTorch model and intentionally break it by detaching the loss path or omitting `zero_grad()`. Then repair it using the diagnostic workflow from this module. Your final version should print finite loss values, present gradients, and nonzero update norms.

```python
import torch
import torch.nn as nn


def make_model():
    return nn.Sequential(
        nn.Linear(10, 32),
        nn.ReLU(),
        nn.Linear(32, 1),
    )


def train_one_step(model, optimizer, x, y):
    optimizer.zero_grad(set_to_none=True)
    pred = model(x)
    loss = nn.functional.mse_loss(pred, y)
    loss.backward()
    optimizer.step()
    return float(loss.detach())
```

Success criteria:

- [ ] You can reproduce a broken case where at least one expected parameter has `grad is None` or stale accumulated gradients.
- [ ] You add diagnostic prints for finite outputs, finite loss, gradient presence, gradient norm, and update norm.
- [ ] You fix the broken case without weakening the loss or skipping the backward pass.
- [ ] You verify that the model can reduce loss on one small fixed batch over repeated steps.

### Part 4: Evaluate a mitigation decision

Modify the model or inputs so gradients become unusually large, then compare training with and without gradient clipping. Record the unclipped norm before applying clipping. Decide whether clipping is an occasional guardrail or a constant intervention in your experiment.

Success criteria:

- [ ] You compute and print the global gradient norm before clipping.
- [ ] You apply norm clipping only after measuring the original norm.
- [ ] You explain whether clipping addresses the root cause or only mitigates the symptom.
- [ ] You propose one non-clipping change, such as input normalization or learning-rate reduction, and test its effect.

---

## Next Module

Next: [Advanced Generative AI Overview](/ai-ml-engineering/generative-ai/)

---

## Sources

- [Seppo Linnainmaa](https://en.wikipedia.org/wiki/Seppo_Linnainmaa) — Background on Linnainmaa's early work and its connection to reverse-mode automatic differentiation.
- [AlexNet](https://en.wikipedia.org/wiki/AlexNet) — Overview of AlexNet and its 2012 ImageNet win using GPU-based training.
- [karpathy/micrograd](https://github.com/karpathy/micrograd) — A compact educational reverse-mode autodiff engine that matches the module's scalar autograd walkthrough.
- [Automatic Differentiation in Machine Learning: a Survey](https://arxiv.org/abs/1502.05767) — Authoritative overview of autodiff methods, including reverse mode and backpropagation.
