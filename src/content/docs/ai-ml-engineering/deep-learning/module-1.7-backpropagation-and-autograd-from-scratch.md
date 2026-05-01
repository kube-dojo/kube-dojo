---
title: "Backpropagation and Autograd from Scratch"
slug: ai-ml-engineering/deep-learning/module-1.7-backpropagation-and-autograd-from-scratch
sidebar:
  order: 1008
---
> **AI/ML Engineering Track** | Complexity: `[COMPLEX]` | Time: 8-10 hours

# Backpropagation and Autograd from Scratch

**Reading Time**: 6-7 hours

**Prerequisites**: Python, NumPy basics, matrix multiplication, basic derivatives, and prior neural network training experience.

---

## Learning Outcomes

By the end of this module, you will be able to evaluate how gradients move through computational graphs, debug broken gradient flows, and justify why reverse-mode automatic differentiation is the default method for neural network training.

You will be able to implement a scalar autograd engine from scratch, including operation recording, topological ordering, local derivative rules, and gradient accumulation across reused graph nodes.

You will be able to compare manual backpropagation, numerical gradient checking, and framework-provided autograd, then choose the right debugging technique when a model produces NaNs, dead activations, or unstable updates.

You will be able to design small experiments that expose vanishing gradients, exploding gradients, missing `zero_grad()` calls, unsafe in-place tensor changes, and incorrect custom layer derivatives.

You will be able to build a practical workflow for validating custom neural network code before it reaches a long training run where failures become expensive.

---

## Why This Module Matters

A machine learning engineer joins a team that has just moved a successful prototype into a larger training job. The prototype trained on one GPU with a small dataset, but the production model now runs for hours before the loss turns into `nan`. The logs show nothing obvious. The data loader passes smoke tests, the model architecture looks plausible, and the training loop came from an older project that everyone assumes is reliable.

She opens the debugger and finds a familiar line: `loss.backward()`. That one call hides the mechanism that decides whether every parameter moves in a useful direction or drifts into numerical failure. When gradients are correct, the optimizer has a signal. When gradients are wrong, missing, accumulated accidentally, or corrupted by an in-place operation, the model can look alive while learning nothing.

Backpropagation is the working engineer's explanation for what happens inside `loss.backward()`. Automatic differentiation is the system that records enough history during the forward pass to compute those gradients later. A practitioner who treats autograd as magic can train models, but they struggle when a custom loss, custom layer, or memory optimization breaks the assumptions that made the magic work.

This module teaches backpropagation from the ground up. It starts with the chain rule, turns that rule into a computational graph, implements a small autograd engine, and then applies the same reasoning to real debugging situations. The goal is not to replace PyTorch or TensorFlow. The goal is to make their behavior legible enough that you can diagnose failures instead of guessing.

---

## 1. The Core Question: Which Parameter Caused the Loss?

Training a neural network is not mainly about computing a prediction. The forward pass gives a prediction and a loss, but learning begins only when the system can answer a harder question: if this parameter changes slightly, how does the loss change? That sensitivity is the gradient, and the optimizer uses it as the local instruction for the next update.

Consider a tiny model that predicts one number from one input. The model computes `prediction = x * w + b`, then compares the prediction with a target using squared error. If the loss is high, both `w` and `b` may have contributed, but they did not necessarily contribute equally. Backpropagation assigns each parameter its share of responsibility by tracing how the loss depends on every earlier value.

```ascii
+---------+     +---------+     +---------+     +---------+
| input x | --> | x * w   | --> | + bias  | --> | loss    |
+---------+     +---------+     +---------+     +---------+
      |               |               |               |
      |               v               v               v
      |          parameter w     parameter b      scalar L
      |
      +---- gradients flow backward from L to earlier values ----+
```

The diagram shows the important asymmetry. Values move forward from inputs to loss, while gradients move backward from loss to inputs and parameters. The backward pass is not a second model. It is the chain rule applied to the exact operations that happened during the forward pass.

A common beginner mistake is to ask, "What is the gradient of the model?" A more useful question is, "What is the gradient of this scalar loss with respect to each value that influenced it?" Gradients are always relative to an output. In training, that output is usually a scalar loss because one scalar can summarize whether the prediction was good enough for the current batch.

**Pause and predict:** If `x = 2`, `w = 3`, `b = 1`, and `loss = (x * w + b) ** 2`, which parameter do you expect to have a larger gradient magnitude, `w` or `b`? Make a prediction before reading the worked example, and explain it using the path each parameter takes into the loss.

The answer is `w`, because changing `w` is amplified by the input `x`. The bias contributes directly to the pre-activation, while the weight contribution is multiplied by `x` before it reaches the same pre-activation. Backpropagation turns that intuition into exact arithmetic.

---

## 2. The Chain Rule as a Local Contract

The chain rule says that when one value affects another through intermediate steps, the total effect is the product of the local effects along the path. This is why backpropagation can be modular. Each operation only needs to know its own derivative, and the graph traversal composes those derivatives into gradients for earlier values.

For a single-variable expression, the rule is compact. If `y = f(g(x))`, then `dy/dx = dy/dg * dg/dx`. The outer function tells us how `y` changes when `g` changes, and the inner function tells us how `g` changes when `x` changes. Multiplying them gives the sensitivity of the final output to the original input.

```python
# Runnable scalar check for y = (2x + 1)^3 at x = 1.
x = 1.0
g = 2 * x + 1
y = g ** 3
dy_dx = 3 * g ** 2 * 2

epsilon = 1e-6
y_plus = (2 * (x + epsilon) + 1) ** 3
y_minus = (2 * (x - epsilon) + 1) ** 3
numerical = (y_plus - y_minus) / (2 * epsilon)

print(y)
print(dy_dx)
print(numerical)
```

This example is small, but it contains the entire shape of backpropagation. The forward pass computed `g` and then `y`. The backward pass starts from `dy/dy = 1`, computes `dy/dg`, and then computes `dy/dx`. It travels through the same operations in reverse order because each earlier derivative needs the gradient that arrived from later operations.

The multi-path version matters even more in real models. If one value is reused in two places, its gradient is the sum of the gradient contributions from both paths. This is why autograd engines accumulate gradients with `+=` instead of assigning with `=` inside local backward functions.

```python
# A value x contributes through two paths: y = x*x + x.
x = 3.0

# Analytic derivative: dy/dx = 2x + 1.
analytic = 2 * x + 1

epsilon = 1e-6
y_plus = (x + epsilon) * (x + epsilon) + (x + epsilon)
y_minus = (x - epsilon) * (x - epsilon) + (x - epsilon)
numerical = (y_plus - y_minus) / (2 * epsilon)

print(analytic)
print(numerical)
```

When `x` is reused, the graph has multiple outgoing paths from the same node. During the backward pass, each downstream operation sends its contribution back to `x`. If the engine overwrites `x.grad` instead of accumulating into it, the final gradient silently loses part of the graph.

**Stop and think:** In the expression `y = x * x + x`, why is the gradient not just `2x`? Identify the two paths from `x` to `y`, and name the contribution from each path before moving on.

---

## 3. Computational Graphs Record the Evidence

A computational graph is a record of how values were produced. Each node stores a value, each operation creates a new node, and edges point back to the parent nodes needed to compute local derivatives. Autograd works because the forward pass leaves behind enough evidence for the backward pass to reconstruct the chain rule.

For the expression `L = (x * w + b) ** 2`, the graph has two parameters, one input, two intermediate values, and one scalar loss. The important detail is not the drawing itself. The important detail is that every operation knows both its parents and the local derivative rule needed to send gradients back to those parents.

```ascii
             +------------+
             |  x = 2.0   |
             +------------+
                    \
                     \
                      v
                  +--------+        +------------+
                  |   *    | <----- |  w = 3.0   |
                  +--------+        +------------+
                      |
                      v
             +----------------+
             | z1 = x * w = 6 |
             +----------------+
                      |
                      v
                  +--------+        +------------+
                  |   +    | <----- |  b = 1.0   |
                  +--------+        +------------+
                      |
                      v
             +----------------+
             | z2 = z1+b = 7 |
             +----------------+
                      |
                      v
                  +--------+
                  |  **2   |
                  +--------+
                      |
                      v
             +----------------+
             |   L = 49.0     |
             +----------------+
```

The forward pass is ordinary computation. It computes `z1`, then `z2`, then `L`. The backward pass begins by setting `L.grad = 1.0`, because `dL/dL` is one. Each operation then receives the gradient of the final loss with respect to its output and distributes it to its inputs using its local derivative.

```python
x, w, b = 2.0, 3.0, 1.0

z1 = x * w
z2 = z1 + b
L = z2 ** 2

dL_dL = 1.0
dL_dz2 = dL_dL * 2 * z2
dL_dz1 = dL_dz2 * 1.0
dL_db = dL_dz2 * 1.0
dL_dx = dL_dz1 * w
dL_dw = dL_dz1 * x

print(L)
print(dL_dx, dL_dw, dL_db)
```

A senior-level mental model is to treat every operation as a small adapter. The square operation knows how to transform an incoming gradient using `2 * z2`. The addition operation copies the incoming gradient to both inputs. The multiplication operation sends `incoming * other_input` to each side. Complex networks are large compositions of these small adapters.

There is a subtle but critical constraint: the graph must be processed in reverse topological order. A node should run its backward function only after all later nodes that depend on it have already contributed their gradients. Otherwise, a reused intermediate may be processed before all of its downstream gradient contributions have arrived.

---

## 4. Building a Scalar Autograd Engine

A minimal autograd engine needs four capabilities. It must store the numeric value, store the current gradient, remember the parent nodes that produced the value, and attach a backward function for the operation that created the value. This small design is enough to reproduce the core idea behind framework autograd.

```python
import math


class Value:
    """A scalar value that records a computation graph for reverse-mode autodiff."""

    def __init__(self, data, _children=(), _op=""):
        self.data = float(data)
        self.grad = 0.0
        self._prev = set(_children)
        self._op = _op
        self._backward = lambda: None

    def __repr__(self):
        return f"Value(data={self.data}, grad={self.grad})"

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

    def __pow__(self, power):
        if not isinstance(power, (int, float)):
            raise TypeError("power must be int or float")
        out = Value(self.data ** power, (self,), f"**{power}")

        def _backward():
            self.grad += out.grad * power * self.data ** (power - 1)

        out._backward = _backward
        return out

    def __neg__(self):
        return self * -1.0

    def __sub__(self, other):
        return self + (-other)

    def __rsub__(self, other):
        return Value(other) + (-self)

    def __truediv__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        return self * (other ** -1.0)

    def __rtruediv__(self, other):
        return Value(other) * (self ** -1.0)

    def __radd__(self, other):
        return self + other

    def __rmul__(self, other):
        return self * other

    def tanh(self):
        t = math.tanh(self.data)
        out = Value(t, (self,), "tanh")

        def _backward():
            self.grad += out.grad * (1.0 - t * t)

        out._backward = _backward
        return out

    def relu(self):
        out = Value(max(0.0, self.data), (self,), "relu")

        def _backward():
            self.grad += out.grad * (1.0 if self.data > 0.0 else 0.0)

        out._backward = _backward
        return out

    def exp(self):
        out = Value(math.exp(self.data), (self,), "exp")

        def _backward():
            self.grad += out.grad * out.data

        out._backward = _backward
        return out

    def log(self):
        if self.data <= 0.0:
            raise ValueError("log is only defined for positive scalar values")
        out = Value(math.log(self.data), (self,), "log")

        def _backward():
            self.grad += out.grad * (1.0 / self.data)

        out._backward = _backward
        return out

    def sigmoid(self):
        s = 1.0 / (1.0 + math.exp(-self.data))
        out = Value(s, (self,), "sigmoid")

        def _backward():
            self.grad += out.grad * s * (1.0 - s)

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

The engine deliberately uses scalar values because scalar code makes the graph mechanics visible. PyTorch generalizes the same idea to tensors, broadcasting rules, GPU kernels, memory reuse, and many optimized operations. The conceptual contract is still recognizable: each differentiable operation creates an output that can send gradients back to the inputs used to produce it.

Test the engine on the earlier expression. The result should match the hand-computed gradients exactly because this graph contains only simple polynomial operations. If it does not match, the bug is likely in the local derivative for multiplication, power, or gradient accumulation.

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

Now test a reused value. This case is important because it catches engines that assign gradients instead of accumulating them. The derivative of `x * x + x` at `x = 3` is `7`, and the two appearances of `x` must both contribute.

```python
x = Value(3.0)
y = x * x + x
y.backward()

print(y.data)
print(x.grad)
```

**Pause and predict:** Before running the next example, decide whether `a.grad` should include one contribution, two contributions, or three contributions. Then run the code and trace which operations sent gradients back to `a`.

```python
a = Value(2.0)
b = a + a
c = b * a
c.backward()

print(c.data)
print(a.grad)
```

The expression is `c = (a + a) * a`, which is equivalent to `2a^2`. The derivative is `4a`, so at `a = 2`, the gradient is `8`. The graph-based explanation is more useful than the algebraic simplification because real neural networks cannot always be simplified by inspection.

---

## 5. From Scalar Autograd to Neural Network Backpropagation

A neural network layer is a structured collection of scalar operations. A linear layer computes weighted sums, an activation applies a nonlinear function, and a loss compares predictions with targets. Backpropagation through a layer is still just local derivatives and incoming gradients, but the notation shifts from scalars to vectors and matrices.

For a layer `y = activation(Wx + b)`, the forward pass has two stages. First, the linear transformation creates `z = Wx + b`. Second, the activation creates `y = activation(z)`. The backward pass reverses that sequence: it moves through the activation first, then through the matrix multiplication and addition.

```ascii
Forward:
+---------+     +-----------+     +--------------+     +---------+
| input x | --> | z = Wx+b  | --> | activation y | --> | loss L  |
+---------+     +-----------+     +--------------+     +---------+
                    |   |                                      |
                    |   +---- parameter b                      |
                    +-------- parameter W                      |

Backward:
+---------+     +-----------+     +--------------+     +---------+
| dL/dx   | <-- | dL/dz     | <-- | dL/dy        | <-- | dL/dL=1 |
+---------+     +-----------+     +--------------+     +---------+
                    |   |
                    |   +---- dL/db
                    +-------- dL/dW
```

The matrix formulas are compact, but each formula corresponds to the same local rule used in the scalar engine. The bias gradient is the incoming pre-activation gradient, summed across a batch. The weight gradient is the outer product of the incoming gradient and the previous activation. The input gradient is needed only because earlier layers depend on the layer input.

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
prediction = W2 @ a1 + b2
loss = 0.5 * (prediction - target) ** 2

dL_dprediction = prediction - target
dL_dW2 = dL_dprediction @ a1.T
dL_db2 = dL_dprediction
dL_da1 = W2.T @ dL_dprediction
dL_dz1 = dL_da1 * (z1 > 0.0)
dL_dW1 = dL_dz1 @ x.T
dL_db1 = dL_dz1
dL_dx = W1.T @ dL_dz1

print("prediction:", prediction.item())
print("loss:", loss.item())
print("dL_dW2 shape:", dL_dW2.shape)
print("dL_dW1 shape:", dL_dW1.shape)
print("dL_dx shape:", dL_dx.shape)
```

This manual implementation is useful because it exposes the dimensions. Many backpropagation bugs are shape bugs that happen to broadcast into a plausible but wrong result. A senior engineer checks whether gradients have the expected shape and whether batch dimensions are being summed intentionally.

**Stop and think:** If `dL_dW2` is computed as `a1 @ dL_dprediction.T` instead of `dL_dprediction @ a1.T`, what shape do you get, and why would that be wrong for `W2`? Answer by comparing the gradient shape to the parameter shape, not by relying on a library error message.

---

## 6. Gradient Checking: Trust but Verify

Gradient checking compares the gradient from backpropagation with a numerical estimate from finite differences. It is too slow for normal training, but it is one of the most valuable tools when implementing a custom operation, a custom loss, or a manual backward pass. It gives you an independent signal that does not rely on the same derivative code you are trying to test.

The central approximation is simple. Nudge one parameter slightly upward, nudge it slightly downward, measure the loss difference, and divide by the size of the total nudge. A centered difference is usually more accurate than a one-sided difference because some approximation error cancels out.

```python
import numpy as np


def gradient_check(param, loss_and_grad_fn, epsilon=1e-5):
    loss, analytic_grad = loss_and_grad_fn(param)
    numerical_grad = np.zeros_like(param)

    iterator = np.nditer(param, flags=["multi_index"], op_flags=["readwrite"])
    while not iterator.finished:
        index = iterator.multi_index
        original = param[index]

        param[index] = original + epsilon
        loss_plus, _ = loss_and_grad_fn(param)

        param[index] = original - epsilon
        loss_minus, _ = loss_and_grad_fn(param)

        param[index] = original
        numerical_grad[index] = (loss_plus - loss_minus) / (2.0 * epsilon)
        iterator.iternext()

    numerator = np.abs(analytic_grad - numerical_grad)
    denominator = np.abs(analytic_grad) + np.abs(numerical_grad) + 1e-8
    relative_error = np.max(numerator / denominator)

    return loss, relative_error, analytic_grad, numerical_grad


def square_loss_and_grad(W):
    loss = np.sum(W ** 2)
    grad = 2.0 * W
    return loss, grad


W = np.random.randn(3, 4)
loss, error, analytic, numerical = gradient_check(W, square_loss_and_grad)

print("loss:", loss)
print("relative error:", error)
```

A good gradient check uses a small deterministic input, not a full production model. Random dropout, data augmentation, nondeterministic kernels, and batch normalization state can make finite differences noisy. Freeze those sources of randomness or test a smaller pure function before testing the full training loop.

Gradient checking also has numerical limits. If `epsilon` is too large, the approximation is coarse. If it is too small, floating-point rounding dominates. Values around `1e-4` to `1e-6` are often practical for double precision, but the right value depends on the function scale and dtype.

A useful workflow is to gradient-check new math before optimizing it. First write a clear version, validate it with finite differences, then vectorize it or move it into a custom autograd function. If a later optimization changes behavior, the gradient check becomes a regression test.

---

## 7. Common Gradient Failures in Real Training

Gradient failures often look similar from the outside: loss stops improving, becomes unstable, or turns into `nan`. The fastest debugging path is to separate graph correctness, numeric stability, optimizer behavior, and data issues. Each category has different evidence and different fixes.

Vanishing gradients happen when gradients shrink as they move backward through many layers. Sigmoid and tanh activations can saturate, which means their derivatives become very small for large positive or negative inputs. Multiplying many small derivatives can make early layers learn slowly or not at all.

Exploding gradients are the opposite failure. Gradients grow as they move through the graph, causing parameter updates that are too large. Recurrent networks, very deep networks, poor initialization, and high learning rates can all contribute. Gradient clipping does not fix bad modeling choices by itself, but it can prevent a single step from destroying training.

NaN gradients usually indicate numerical invalid operations or overflow. Common causes include `log(0)`, division by very small values, square roots of negative values, unchecked exponentials, and learning rates that push parameters into unstable regions. The first NaN is the useful one; later NaNs usually spread everywhere.

```python
import torch


def inspect_batch(model, batch, loss_fn):
    x, y = batch

    if torch.isnan(x).any() or torch.isinf(x).any():
        raise ValueError("input contains NaN or Inf")

    model.train()
    output = model(x)

    if torch.isnan(output).any() or torch.isinf(output).any():
        raise ValueError("model output contains NaN or Inf")

    loss = loss_fn(output, y)

    if torch.isnan(loss) or torch.isinf(loss):
        raise ValueError("loss is NaN or Inf before backward")

    model.zero_grad(set_to_none=True)
    loss.backward()

    for name, param in model.named_parameters():
        if param.grad is None:
            print(f"{name}: no gradient")
            continue
        grad = param.grad.detach()
        print(
            f"{name}: norm={grad.norm().item():.3e}, "
            f"min={grad.min().item():.3e}, max={grad.max().item():.3e}"
        )
        if torch.isnan(grad).any() or torch.isinf(grad).any():
            raise ValueError(f"{name} gradient contains NaN or Inf")

    return loss.item()
```

Hooks can help locate the first parameter where a bad gradient appears. They are especially useful in large models where printing every tensor would create too much output. The goal is not to leave hooks in production training forever; the goal is to narrow the failure to a small set of operations.

```python
import torch


def attach_gradient_nan_hooks(model):
    handles = []

    def make_hook(name):
        def hook(grad):
            if torch.isnan(grad).any() or torch.isinf(grad).any():
                print(f"bad gradient detected at {name}")
                print(f"min={grad.min().item()}, max={grad.max().item()}")
            return grad

        return hook

    for name, param in model.named_parameters():
        if param.requires_grad:
            handles.append(param.register_hook(make_hook(name)))

    return handles
```

**Pause and predict:** A model trains normally for several batches, then loss becomes `nan` immediately after a batch with unusually large input values. Which hypothesis should you test first: missing `zero_grad()`, exploding gradients, incorrect labels, or dead ReLUs? State what measurement would confirm or reject your hypothesis.

The strongest first hypothesis is exploding gradients or numeric overflow triggered by the large inputs. You would confirm it by logging activation ranges, loss value before backward, and gradient norms for the failing batch. Missing `zero_grad()` can also cause growth over time, but the tight correlation with an outlier batch points toward scale sensitivity.

---

## Did You Know?

**Did You Know?** Reverse-mode automatic differentiation and backpropagation describe closely related ideas from different communities: one emphasizes a general derivative-computation method, while the other emphasizes its use in training neural networks.

**Did You Know?** A dynamic autograd system, such as PyTorch eager execution, builds the computation graph as normal Python code runs, which makes debugging and control flow easier than in older static-graph workflows.

**Did You Know?** Gradient checkpointing reduces activation memory by recomputing parts of the forward pass during backward, trading extra compute for the ability to train larger models.

**Did You Know?** Numerical gradient checking is usually a development-time tool, not a training-time tool, because checking every parameter with finite differences requires many additional forward passes.

---

## Common Mistakes

| Mistake | Why It Breaks Learning | Better Practice |
|---|---|---|
| Using in-place tensor operations on values needed for backward, such as `a += b` on an activation reused later | Autograd may need the original value to compute a local derivative, and changing it can corrupt the saved graph state or raise a versioning error | Prefer out-of-place operations during model development, and use in-place variants only when you understand what backward needs |
| Forgetting to call `optimizer.zero_grad()` or `model.zero_grad()` before each backward pass | Frameworks accumulate gradients by default, so each step accidentally includes old batches and update magnitudes drift upward | Clear gradients once per optimization step, usually immediately before the forward or backward pass |
| Calling `.backward()` twice on the same graph without `retain_graph=True` when a multi-loss workflow needs it | Most frameworks free graph intermediates after backward to save memory, so the second backward cannot reuse the released values | Combine losses before one backward when possible, or explicitly retain the graph when repeated backward is truly required |
| Treating `param.grad is None` and `param.grad == 0` as the same symptom | `None` often means the parameter was not connected to the loss, while zero can mean it was connected but the local derivative was zero | Inspect graph connectivity, `requires_grad`, frozen parameters, and activation states separately |
| Debugging NaNs only after the optimizer step | The optimizer may spread one bad gradient across many parameters, hiding the operation that first produced the invalid value | Check inputs, outputs, loss, and gradients before calling `optimizer.step()` |
| Using sigmoid or tanh everywhere in a deep feedforward network without monitoring saturation | Saturated activations have small derivatives, so early layers can receive gradients too small to drive useful learning | Start with ReLU-family activations and inspect activation and gradient distributions |
| Trusting a custom backward implementation because the forward output looks correct | Forward correctness does not prove derivative correctness, and wrong gradients can still reduce loss briefly by accident | Add finite-difference gradient checks on small deterministic inputs |
| Clipping gradients as the only response to exploding loss | Clipping limits update size but does not identify the root cause, such as poor initialization, invalid loss math, or an excessive learning rate | Use clipping as a guardrail while also checking scale, initialization, loss formulation, and optimizer settings |

---

## Quiz

**Q1: Your team adds a custom loss for a ranking model. The forward values match a NumPy reference implementation, but training gets worse after a few hundred steps. How would you validate whether the backward computation is the problem?**

<details>
<summary>Answer</summary>

Build a small deterministic test case and compare the analytic gradients with finite-difference numerical gradients. Use fixed inputs, disable randomness, and check a few representative parameters or inputs rather than the full production model. If the relative error is large, inspect the local derivative rules inside the custom loss before changing optimizer settings.
</details>

**Q2: A colleague reports that a model's validation loss suddenly becomes `nan` after one batch with much larger feature magnitudes than usual. What should you check before changing the architecture?**

<details>
<summary>Answer</summary>

First check whether the forward pass already produced extreme or invalid values, then check the loss before backward and gradient norms before the optimizer step. Large features can trigger overflow, invalid logarithms, or exploding gradients. If gradient norms spike only on that batch, normalization, clipping, loss stabilization, or learning-rate changes are more targeted than an architecture rewrite.
</details>

**Q3: You inspect a model and find that several early-layer parameters have `grad=None`, while later layers have normal gradient values. What does this suggest, and how should you investigate?**

<details>
<summary>Answer</summary>

`grad=None` suggests those parameters were not connected to the scalar loss used for backward, were frozen with `requires_grad=False`, or were bypassed by control flow. Trace the forward path from inputs to loss, confirm the parameters are used, check `requires_grad`, and verify that tensors were not detached or converted through NumPy before reaching the loss.
</details>

**Q4: During a refactor, someone replaces `hidden = hidden + residual` with `hidden += residual` to save memory. Training now fails with an autograd versioning error. What is the likely cause?**

<details>
<summary>Answer</summary>

The in-place update changed a tensor whose original value was still needed for a later backward calculation. Autograd tracks tensor versions so it can detect when saved values have been modified. Revert to the out-of-place expression or restructure the computation so the in-place operation does not modify any value required by backward.
</details>

**Q5: A deep MLP using sigmoid activations trains very slowly. Gradient norm logs show tiny gradients in the earliest layers and larger gradients near the output. Which mechanism explains this pattern, and what would you try first?**

<details>
<summary>Answer</summary>

This is consistent with vanishing gradients. Sigmoid derivatives become small when activations saturate, and multiplying many small derivatives makes early-layer gradients shrink. A practical first change is to use ReLU-family activations with appropriate initialization, then compare activation distributions and gradient norms again.
</details>

**Q6: You implement a scalar autograd engine and test `y = x * x + x` at `x = 3`. Your engine returns `x.grad = 6` instead of `7`. Which bug is most likely?**

<details>
<summary>Answer</summary>

The engine is probably overwriting a gradient contribution instead of accumulating all contributions. In `x * x + x`, `x` reaches `y` through multiple paths, so its gradient is the sum of `2x` from the multiplication path and `1` from the addition path. Local backward functions should use `+=` when adding to parent gradients.
</details>

**Q7: Your team computes two losses from the same forward pass and calls `loss_a.backward()` followed by `loss_b.backward()`. The second call fails because the graph was freed. What design would you recommend?**

<details>
<summary>Answer</summary>

If both losses should train the same forward pass, combine them into one scalar, such as `total_loss = loss_a + weight * loss_b`, and call `total_loss.backward()` once. If there is a specific reason to run separate backward passes on the same graph, use `retain_graph=True` on the first call, but recognize that retaining graphs increases memory use.
</details>

---

## Hands-On Exercise: Build and Debug Backpropagation

In this exercise you will implement a scalar autograd engine, validate it against finite differences, and use gradient diagnostics to debug a small PyTorch training loop. The point is not speed. The point is to connect the arithmetic you can inspect with the framework behavior you use in real projects.

### Step 1: Create a local autograd file

Create a file named `autograd_lab.py` and paste the `Value` class from this module into it. Keep the implementation scalar and readable. Do not add tensor support yet, because tensor broadcasting would hide the graph mechanics you are trying to inspect.

- [ ] The file defines a `Value` class with `data`, `grad`, `_prev`, `_op`, and `_backward` fields.
- [ ] Addition, multiplication, power, `tanh`, `relu`, `log`, and `sigmoid` all return new `Value` objects.
- [ ] Each local backward function accumulates into parent gradients with `+=`.
- [ ] The `backward()` method builds a topological order and processes it in reverse.

### Step 2: Verify the worked example

Add a test function for `loss = (x * w + b) ** 2` with `x = 2`, `w = 3`, and `b = 1`. Run the function and compare the output to the hand calculation in the module.

- [ ] `loss.data` is `49.0`.
- [ ] `x.grad` is `42.0`.
- [ ] `w.grad` is `28.0`.
- [ ] `b.grad` is `14.0`.
- [ ] You can explain why `w.grad` is smaller than `x.grad` in this specific numeric setup.

### Step 3: Test gradient accumulation

Add a second test for `y = x * x + x` at `x = 3`. This test catches the most common bug in small autograd engines: replacing a gradient instead of accumulating multiple graph paths.

- [ ] `y.data` is `12.0`.
- [ ] `x.grad` is `7.0`.
- [ ] Changing `+=` to `=` in one backward function causes this test to fail.
- [ ] Your notes identify both paths from `x` to `y`.

### Step 4: Add finite-difference gradient checking

Write a small finite-difference function for scalar `Value` expressions. Use it to check the derivative of `f(x) = log(sigmoid(x))` at a few input values where the log is valid and numerically stable.

- [ ] The numerical gradient and autograd gradient are close for at least three input values.
- [ ] The test uses a centered difference, not a one-sided difference.
- [ ] You reset gradients or rebuild the graph for each checked input.
- [ ] You record one case where choosing an `epsilon` that is too large or too small makes the check worse.

### Step 5: Debug a broken PyTorch loop

Use the following intentionally flawed training loop. Your job is to make the failure observable before you fix it, then apply targeted fixes rather than rewriting everything blindly.

```python
import torch
import torch.nn as nn


def broken_training():
    model = nn.Sequential(
        nn.Linear(10, 64),
        nn.Sigmoid(),
        nn.Linear(64, 64),
        nn.Sigmoid(),
        nn.Linear(64, 1),
    )

    optimizer = torch.optim.SGD(model.parameters(), lr=8.0)

    for step in range(80):
        x = torch.randn(32, 10) * (10 if step == 25 else 1)
        y = torch.randn(32, 1)

        output = model(x)
        loss = torch.log(output).mean()

        loss.backward()
        optimizer.step()

        if step % 10 == 0:
            print(step, loss.item())


broken_training()
```

- [ ] You add a deterministic seed so the failure can be reproduced.
- [ ] You print or assert input range, output range, loss validity, and gradient norms before `optimizer.step()`.
- [ ] You replace the invalid loss with a suitable supervised loss such as mean squared error.
- [ ] You call `optimizer.zero_grad()` once per step before backward.
- [ ] You reduce the learning rate to a value that does not immediately destabilize training.
- [ ] You can explain whether sigmoid saturation is still a concern after the other fixes.

### Step 6: Compare gradient clipping by value and by norm

Implement two clipping helpers and run them on a small model after backward. One helper should clamp each gradient component independently. The other should scale all gradients together so their global norm does not exceed a threshold.

- [ ] Value clipping limits each component to the configured range.
- [ ] Norm clipping preserves gradient direction while reducing the global magnitude.
- [ ] You print the total gradient norm before and after norm clipping.
- [ ] You explain why clipping can prevent a bad update but does not prove the model is correctly specified.

### Step 7: Write the postmortem

Write a short postmortem for the broken loop. Treat it like a professional debugging note, not a diary. Name the symptoms, the measurements that narrowed the cause, the fixes applied, and one guardrail you would keep in the training code.

- [ ] The postmortem distinguishes between the first invalid value and later propagated NaNs.
- [ ] The postmortem names at least one graph correctness issue and one numerical stability issue.
- [ ] The postmortem includes a minimal regression test or diagnostic you would keep.
- [ ] The postmortem avoids vague conclusions such as "PyTorch was unstable."

---

## Next Module

Next: **Phase 7: Advanced Generative AI**. You will use the gradient and autograd mental models from this module when studying fine-tuning, parameter-efficient adaptation, reinforcement learning from human feedback, diffusion models, multimodal systems, and efficient inference.

---

_Last updated: 2025-11-27_

_Status: Complete_

## Sources

- [Seppo Linnainmaa](https://en.wikipedia.org/wiki/Seppo_Linnainmaa) — Background on Linnainmaa's early work and its connection to reverse-mode automatic differentiation.
- [AlexNet](https://en.wikipedia.org/wiki/AlexNet) — Overview of AlexNet and its 2012 ImageNet win using GPU-based training.
- [Training Deep Nets with Sublinear Memory Cost](https://arxiv.org/abs/1604.06174) — Canonical reference for gradient checkpointing and the memory-versus-compute tradeoff.
- [Automatic Differentiation in Machine Learning: a Survey](https://arxiv.org/abs/1502.05767) — Authoritative overview of autodiff methods, including reverse mode and backpropagation.
