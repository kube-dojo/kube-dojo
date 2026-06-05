---
citations_verified: true
title: "Computational Graphs & Scalar Autograd"
slug: ai-ml-engineering/deep-learning/module-1.1.8-computational-graphs-scalar-autograd
sidebar:
  order: 1002.8
---

> **AI/ML Engineering Track** | Complexity: `[COMPLEX]` | Time: 6-8 hours

In [A6: Backprop by Hand for Dense Nets](/ai-ml-engineering/deep-learning/module-1.1.6-backprop-by-hand-dense-nets/) you derived every gradient for a tiny MLP yourself. You wrote `dL_dW = X.T @ G`, summed bias gradients across the batch, and walked layers in reverse topological order. That work was slow, exact, and indispensable: it proved you understand the vector-Jacobian products (VJPs) that make training possible. This module is the payoff — the eighth and final installment of Block A. You will build the **engine** that performs those same local derivative rules automatically for **any** scalar computation, which is the conceptual leap that makes `torch.autograd` feel inevitable instead of magical.

We stay in **scalar** land on purpose because tensors, broadcasting, and GPU kernels hide the bookkeeping that frameworks must still perform underneath every `loss.backward()` call. Karpathy's [micrograd](https://github.com/karpathy/micrograd) shows the entire idea in roughly 100 lines of Python; we extend that pattern with the vocabulary from A6 (VJPs, reverse topological order, gradient accumulation) and connect it to production autograd. We will **not** re-derive matrix backprop here — that remains A6's job, and duplicating it would blur the line between "derive the layer formulas" and "automate the graph walk." A8 generalizes A6's hand-written gradients into a reusable graph engine so you never manually chain another scalar expression again, while still knowing what the engine is doing when it chains millions of them on a GPU.

## Learning Outcomes

After completing this module, you will be able to:

- **Draw** computational graphs for concrete expressions, explain DAG forward evaluation with cached intermediates, and trace reverse-mode VJPs node by node.
- **Implement** a micrograd-style `Value` class with operator overloading, per-node `_backward` closures, topological `backward()`, and `+=` accumulation for reused values.
- **Verify** that the engine reproduces hand-derived gradients from [A6](/ai-ml-engineering/deep-learning/module-1.1.6-backprop-by-hand-dense-nets/) on a two-input neuron with squared-error loss.
- **Contrast** reverse-mode and forward-mode automatic differentiation, and justify why reverse mode is the default when one scalar loss depends on many parameters.
- **Explain** how `torch.autograd` scales the same graph contract to tensors, including memory retention, in-place hazards, and `zero_grad()` semantics.

## Why This Module Matters

Every time you call `loss.backward()` in PyTorch, a runtime has already recorded a computation graph during the forward pass. That graph is not a metaphor or a pedagogical cartoon; it is a concrete data structure with nodes for values, edges for dependencies, cached outputs for local derivative rules, and a schedule for walking backward. When training fails with NaNs, `grad is None`, or versioning errors after an in-place update, the fix lives in that graph story rather than in vague suspicion about the optimizer or learning rate. Engineers who treat `backward()` as a black box can still ship models until the first custom head, fused loss, or memory optimization breaks an assumption they did not know they were making.

A6 made you the human autograd engine for dense layers. You multiplied upstream gradients by local Jacobians (VJPs), summed over batch axes, and checked every formula with finite differences. A8 automates the bookkeeping while keeping the math visible. The local rules do not change: addition copies the upstream gradient to both inputs; multiplication sends `upstream * other_operand` to each side; ReLU gates the upstream gradient when the pre-activation was non-positive. The engine's job is to call those rules in the right order and **accumulate** when one value feeds multiple operations.

This is also the bridge to Block B. [PyTorch Fundamentals](/ai-ml-engineering/deep-learning/module-1.2-pytorch-fundamentals/) assumes you already know what `requires_grad`, `backward()`, and `zero_grad()` mean at the graph level. After A8, they mean: build the DAG on the forward pass, seed the loss gradient, reverse-walk with VJPs, then free or retain the graph depending on memory policy. The tensors are bigger; the contract is the same.

> **Hypothetical scenario: The custom loss that passed forward checks**
>
> Imagine a team ships a ranking loss whose forward values match a NumPy reference on every batch in staging. After two days of GPU training, validation AUC flatlines while the loss curve looks healthy. A senior engineer traces the graph and finds the backward kernel for one normalization term used post-softmax probabilities instead of the pre-softmax logits the forward pass cached. Forward smoke tests never compared gradients. A one-hour finite-difference check on a five-sample batch would have caught the bug before the cluster job started. The lesson matches what you will practice in the hands-on lab: autograd is a contract on **both** directions, and correct forward numbers are necessary but not sufficient for learning.

> **The Tape Recorder Analogy**
>
> Imagine each arithmetic operation leaves a short voice memo: "I multiplied these two parents to produce this child." Forward pass is playing the program left to right while the recorder captures every step. Backward pass rewinds the tape from the loss backward, and each memo tells you how to split the blame among parents. Reverse-mode autodiff is that rewind button — one pass from one scalar output to all inputs.

---

## What You Will Build

By the end of this module you will have a self-contained `Value` class and `autograd_lab.py` test harness that together demonstrate the full pipeline: forward build, reverse walk, gradient accumulation, agreement with A6 hand math, and optional finite-difference auditing. The scope is intentionally narrower than a framework — no tensor types, no optimizer classes, no DataLoader — because those pieces arrive in Block B with PyTorch while the graph contract stays constant. What you are building is the **tape** itself: the data structure textbooks draw as boxes and arrows, now executable Python you can breakpoint.

---

## Part 1: Every Numeric Program Is a Graph

A **computational graph** is a DAG whose nodes are values and whose edges are dependencies created by primitive operations. The forward pass evaluates nodes in **topological order**: every parent is computed before its children, which is the same dependency discipline you enforced manually when A6 insisted that `Layer2.backward()` cannot run before `dL_dZ2` exists. Each intermediate node **caches** its output because backward needs both the cached value and the operation type to apply the correct local VJP, mirroring how A3 cached `Z` and `A` so activation backward could multiply by the ReLU mask that was true during the specific forward call that produced the loss.

Consider a concrete expression from a tiny loss fragment such as `L = (a * b + c) * relu(d)`, which mixes arithmetic, addition, and a ReLU gate in one scalar objective. We will use the numeric instance `a = 2`, `b = 3`, `c = 1`, and `d = 1.5` so every forward and backward value can be checked by hand without a calculator habit you cannot audit.

```text
L = (a * b + c) * relu(d)
```

```text
Forward evaluation (topological order):

  n1 = a * b     --> 6.0
  n2 = n1 + c    --> 7.0
  n3 = relu(d)   --> 1.5        (d > 0, pass through)
  L  = n2 * n3   --> 10.5

Graph (edges point from parents to children):

       a=2.0 ----\
                  * --> n1=6.0 --\
       b=3.0 ----/                + --> n2=7.0 --\
                                  c=1.0 ---------/                * --> L=10.5
       d=1.5 --> relu --> n3=1.5 ------------------------------/
```

Three ideas matter for everything that follows, and each one has direct engineering consequences when you move from pencil-and-paper graphs to framework code. The graph is built **during** forward evaluation, which means you cannot reconstruct reliable gradients from final numbers alone after the fact; you need the structure, the operation labels, and the cached intermediates at each op so the backward kernel knows which local derivative rule to apply. PyTorch records this tape automatically when tensors have `requires_grad=True`, and our `Value` class records it when you use overloaded operators instead of raw floats. The graph must also be a **DAG** because cycles would make topological ordering impossible — there would be no valid sequence in which every parent is ready before its children during forward, nor a reverse sequence during backward where every consumer finishes before its producer. Real models with loops handle this by unrolling a fixed number of steps or by checkpointing segments, but the differentiable slice for one `backward()` call must still be acyclic. Finally, shared subgraphs are normal rather than exceptional: if `a` appeared in two multiplications, backward must **sum** both gradient paths into `a.grad`, which is why local backward functions use `+=` instead of assignment, and why forgetting that accumulation produces gradients that look plausible on simple graphs but fail on reused activations in production architectures.

Frameworks name the cached intermediates differently — PyTorch calls them saved variables on `grad_fn`, micrograd stores them on `_prev` — but the engineering invariant is identical. If you overwrite a saved pre-activation with an in-place ReLU before backward runs, you have destroyed evidence the chain rule needs, exactly as if you erased part of the tape recording. That is why debugging autograd failures starts with drawing the graph for a **small** failing batch, not with randomly lowering the learning rate.

Before you read the reverse walk in Part 2, sketch the backward messages on paper for the graph above: `n2` feeds only the final multiply, while `a` reaches `L` through a single path via `n1`. How many distinct paths from `d` to `L` exist, and what numeric value do you expect for `d.grad` when `d = 1.5`? Write your prediction, then compare with the engine trace in Part 4.

---

## Part 2: Reverse-Mode Autodiff

**Reverse-mode** automatic differentiation starts at a scalar output (here, the loss `L`) with seed gradient `dL/dL = 1`, then walks the graph in **reverse topological order**. At each node, the engine applies that node's **local VJP**: given `dL/d(child)`, compute contributions to `dL/d(parent)` using the same local derivative rules you derived by hand in A6.

Walking the graph from the loss downward, the final multiply `L = n2 * n3` sends `dL/dn2 = dL/dL * n3 = 1.5` and `dL/dn3 = dL/dL * n2 = 7.0` using the multiplication VJP. The addition `n2 = n1 + c` copies the upstream `1.5` to both parents so `dL/dn1 = 1.5` and `dL/dc = 1.5`. The product `n1 = a * b` contributes `dL/da = 1.5 * b = 4.5` and `dL/db = 1.5 * a = 3.0`. The ReLU node `n3 = relu(d)` with `d = 1.5 > 0` passes the full upstream `7.0` to `d`. These are exactly the VJPs from A6, expressed on scalars instead of batched matrices.

```text
dL/dn2 = 1.5,  dL/dn3 = 7.0
dL/dn1 = 1.5,  dL/dc  = 1.5
dL/da  = 4.5,  dL/db  = 3.0
dL/dd  = 7.0
```

A dense layer's `dL_dW = X.T @ G` is the batched outer-product version of "multiply upstream gradient by the other operand and sum over shared axes."

### Reverse mode vs forward mode

| Mode | Seed | Cost for 1 scalar loss, `P` parameters | Typical use |
|------|------|----------------------------------------|-------------|
| **Forward** | One variable at a time | `O(P)` forward passes | Few inputs, many outputs |
| **Reverse** | One scalar output | `O(1)` backward pass over graph | Many parameters, one loss |

Training minimizes one scalar loss over millions of weights. Reverse mode computes **all** parameter gradients in one backward sweep — the reason backpropagation won. Forward-mode AD (or coordinate-wise finite differences) would re-run the forward graph once per parameter. Fine for gradient **checking** a tiny net in A6; unusable at production scale.

[Baydin et al.'s autodiff survey](https://arxiv.org/abs/1502.05767) makes the community lineage explicit: reverse mode is the same structural idea as backpropagation, stated in the language of automatic differentiation rather than neural networks. [Wikipedia's automatic differentiation overview](https://en.wikipedia.org/wiki/Automatic_differentiation) gives a compact history including Linnainmaa's 1970 reverse-mode formulation — the same decade neural networks were being invented, though the communities merged only later.

### Forward mode in one paragraph

Forward mode seeds each input dimension with unit directional derivatives and propagates Jacobian-vector products forward alongside values. If you have three inputs and one output, you need three forward sweeps to recover the full gradient row. That is excellent when outputs are high-dimensional and inputs are few — inverse problems, sensitivity analysis of a handful of hyperparameters — but backwards for neural nets where inputs are images with millions of pixels yet the loss is one scalar. Keep forward mode in your debugging toolkit as finite differences with structure; do not use it to train ResNet-50.

A graph with 50,000 parameter nodes and one scalar loss node is the standard training shape, so pause and articulate why PyTorch calls `loss.backward()` once instead of running 50,000 forward-mode passes. Your answer should mention seed direction (loss versus parameters), the cost of repeated forward sweeps, and how shared subgraphs let one reverse walk accumulate contributions into every parent parameter.

---

## Part 2b: The Chain Rule as a Local Contract

Before we implement code, lock in the modular view that makes both A6 and A8 work. When `y = f(g(x))`, the sensitivity of the final output to `x` is the product of the local sensitivities along the path: `dy/dx = (dy/dg) * (dg/dx)`. Backpropagation never asks a node to know the entire network; it only asks for the **local** derivative of this node's output with respect to each parent, multiplied by the upstream gradient already arriving at this node's output.

```python
# Runnable scalar check: y = (2*x + 1)^3 at x = 1
x = 1.0
g = 2 * x + 1
y = g ** 3
dy_dx = 3 * g ** 2 * 2

eps = 1e-6
y_plus = (2 * (x + eps) + 1) ** 3
y_minus = (2 * (x - eps) + 1) ** 3
numerical = (y_plus - y_minus) / (2 * eps)

print(y, dy_dx, numerical)
```

The backward story mirrors the forward story in reverse: start from `dy/dy = 1`, compute `dy/dg = 3g^2`, then `dg/dx = 2`, multiply to get `dy/dx = 6g^2 = 54` at `x = 1` (`g = 3`). Each step is a VJP. The multi-path version is where engines earn their keep. For `y = x*x + x`, the derivative is `2x + 1` because `x` reaches `y` through the square **and** through the addition. An engine that only keeps the last message overwrites one path. A human deriving by hand sums paths explicitly; autograd sums them inside `+=`.

```python
# Multi-path check: y = x*x + x at x = 3
x = 3.0
analytic = 2 * x + 1
eps = 1e-6
y_plus = (x + eps) * (x + eps) + (x + eps)
y_minus = (x - eps) * (x - eps) + (x - eps)
numerical = (y_plus - y_minus) / (2 * eps)
print(analytic, numerical)  # 7.0, ~7.0
```

Treat every primitive op as a tiny adapter with a known local rule. Addition copies upstream gradient to each parent. Multiplication sends `upstream * other_parent_value` to each side. Power rules use the cached base. ReLU multiplies upstream by zero or one depending on the **cached** pre-activation sign. Complex networks are long compositions of these adapters; the graph is the wiring diagram that schedules them.

The exercise below is worth doing once with pen before you trust code. Pick any small expression with three ops, label each forward value, then propagate `dL/dL = 1` backward one node at a time writing the local factor you multiply at each step. If your hand trace disagrees with the engine later, the disagreement is almost always a local rule typo, not a misunderstanding of the whole network. That discipline is what A6 drilled on matrix multiply transposes; A8 drills it on graph scheduling so both skills reinforce each other.

---

## Part 3: The Scalar `Value` Class

We implement a micrograd-style engine in pure Python so every graph edge is visible in a debugger. Each `Value` stores the fields below, and together they are sufficient to train small scalar networks without NumPy matrix helpers.

| Field | Role |
|-------|------|
| `data` | Numeric result of the forward op |
| `grad` | Accumulated `dL/d(data)` |
| `_prev` | Parent nodes in the graph |
| `_op` | Label for debugging (`+`, `*`, `relu`, …) |
| `_backward` | Closure applying the local VJP |

Operator overloading builds the graph **during** forward evaluation, which is the same trick PyTorch uses when you write `z = x @ w + b` with tensors. Each op performs three duties in one call: it computes the child value for the forward result, it links parents in `_prev` so the topological sort can find dependencies, and it defines `_backward` that will later add into parent `.grad` using `+=`. Constants like `2.0` are wrapped in `Value(2.0)` when needed so every edge in the graph is between `Value` nodes; literals on the right-hand side hit `__rmul__` and `__radd__` paths that keep the graph connected.

Read the implementation once with the multiplication rule in mind. When `out = self * other`, the local derivatives are `dout/dself = other.data` and `dout/dother = self.data`. During backward, the upstream `out.grad` is multiplied by those local factors and accumulated into parents. Division is implemented as multiplication by a negative power so we do not duplicate quotient-rule logic. Subtraction reuses addition and negation. This minimal surface area is deliberate — every new op you add to a framework is another local rule you must prove correct against finite differences.

```python
import math


class Value:
    """Scalar value with reverse-mode autodiff (micrograd-style)."""

    def __init__(self, data, _children=(), _op=""):
        self.data = float(data)
        self.grad = 0.0
        self._prev = set(_children)
        self._op = _op
        self._backward = lambda: None

    def __repr__(self):
        return f"Value(data={self.data:.4f}, grad={self.grad:.4f})"

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
            self.grad += out.grad * power * (self.data ** (power - 1))

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
        out = Value(math.log(self.data), (self,), "log")

        def _backward():
            self.grad += out.grad / self.data   # d/dx log(x) = 1/x

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

### Why `+=` is non-negotiable

If a value is reused, it receives gradient contributions along **every** path from the loss. Consider `y = x * x + x` at `x = 3`:

- Path through `x * x`: contributes `2x = 6`
- Path through `+ x`: contributes `1`
- Total: `7`

An engine that assigns `self.grad = ...` in `_backward` keeps only the last path. That bug is silent and deadly — the forward loss looks fine while optimization follows wrong slopes.

```python
x = Value(3.0)
y = x * x + x
y.backward()
print(x.grad)  # 7.0
```

Worse case: `c = (a + a) * a` at `a = 2` gives `c = 8`, derivative `4a = 8`. Here `a` appears in **three** op edges: two addition edges each forwarding the multiply's upstream gradient, plus the multiply edge scaling by the other factor `b = 2a = 4`. Trace those three contributions on paper before running the code, because this expression is the smallest example where assignment-based engines fail while accumulation-based engines succeed.

```python
a = Value(2.0)
b = a + a      # a used twice in addition
c = b * a      # a used again in multiplication
c.backward()
print(a.grad)  # 8.0
```

If you extend the engine later with `log`, `sigmoid`, or `softmax`, each new method follows the same template: compute forward `data`, stash parents, define `_backward` with `+=`. The [micrograd repository](https://github.com/karpathy/micrograd) includes additional ops you can port as stretch goals; verify each with finite differences before using it in a toy trainer.

---

## Part 4: `backward()` End to End

The `backward()` method performs three coordinated steps that mirror what every framework must do before calling into C++ or CUDA kernels. It first builds a topological sort from the output node via depth-first search over `_prev`, then seeds the output gradient with `self.grad = 1.0` because the derivative of a scalar loss with respect to itself is one, and finally iterates in reverse calling each node's `_backward` only after all downstream consumers have finished contributing to `out.grad`. Processing in that order guarantees that when a node's `_backward` runs, `out.grad` already holds the full upstream `dL/d(out)` including every downstream path, which is the scalar version of waiting until `dL_dY` is fully known before computing `dL_dW` in A6.

Run the Part 1 example in code and compare the printed gradients with the hand trace from Part 2:

```python
a = Value(2.0)
b = Value(3.0)
c = Value(1.0)
d = Value(1.5)

n1 = a * b
n2 = n1 + c
n3 = d.relu()
L = n2 * n3
L.backward()

print("L:", L)
print("a:", a)   # grad 4.5
print("b:", b)   # grad 3.0
print("c:", c)   # grad 1.5
print("d:", d)   # grad 7.0
```

Hand calculation in Part 2 matches to floating-point agreement. If any gradient disagrees, inspect the local rule for that op before blaming the topological sort — sort bugs usually show up as partially zero gradients on reused nodes, not as uniform scale errors.

The topological sort itself deserves a slow read because it is the scheduling heart of the engine. Depth-first search from the loss node visits each parent before appending the current node to `topo`, which yields an order where every parent appears before its children. Reversing that list ensures that when we call `_backward` on a node, every downstream consumer has already added its contribution into `out.grad`. This is the same dependency discipline as A6's `for layer in reversed(self.layers)`, but applied automatically to an arbitrary expression graph rather than a hand-wired list of layers. If you ever implement autograd on a new platform, get this ordering right before you optimize kernels — wrong order produces gradients that are silently too small, not loudly NaN.

Karpathy's [spelled-out backpropagation lecture](https://www.youtube.com/watch?v=VMj-3S1tku0) walks this same graph with pen and paper; micrograd is the code companion. [CS231n backprop notes](https://cs231n.github.io/optimization-2/) use the same "local gradient times upstream gradient" picture at tensor scale. Watching the lecture while stepping through your own `Value` implementation is time well spent: pause when the instructor labels local derivatives on the graph and write the matching `_backward` before seeing the answer.

---

## Part 5: Proof — The Engine Matches A6

A6 derived gradients for a dense layer `Y = X @ W + b` with upstream `G = dL/dY`. For a **single sample** (`N = 1`), that collapses to scalar equations:

```text
z = w1*x1 + w2*x2 + b
a = relu(z)
loss = 0.5 * (a - target)^2
```

Take the numeric instance A6-style with one row and two features: `x1 = 1.0`, `x2 = 2.0`, `w1 = 0.5`, `w2 = 0.3`, `b = 0.1`, and `target = 1.0`. Forward gives `z = 1.2`, `a = relu(1.2) = 1.2`, and `loss = 0.5 * (1.2 - 1.0)^2 = 0.02`. Hand backward using the same VJPs as A6 Parts 3–4 yields `dL/da = 0.2`, `dL/dz = 0.2` with ReLU active, `dL/dw1 = 0.2`, `dL/dw2 = 0.4`, `dL/db = 0.2`, `dL/dx1 = 0.1`, and `dL/dx2 = 0.06`.

```text
forward: z=1.2, a=1.2, loss=0.02
backward: dw1=0.2, dw2=0.4, db=0.2, dx1=0.1, dx2=0.06
```

For the full matrix story — batching, transposes, `X.T @ G`, and why the bias gradient sums across the batch axis — see [A6](/ai-ml-engineering/deep-learning/module-1.1.6-backprop-by-hand-dense-nets/). Here we only need agreement on the scalars, because a single-sample dense layer **is** a two-input neuron with extra notation. The psychological benefit of this test is large: when the engine prints `w1.grad == 0.2`, you are not comparing against a mysterious library — you are comparing against a derivative you could still derive on paper during an interview or a whiteboard review. That parity is what makes later trust in `torch.autograd` rational rather than faith-based.

```python
x1 = Value(1.0)
x2 = Value(2.0)
w1 = Value(0.5)
w2 = Value(0.3)
b = Value(0.1)
target = Value(1.0)

z = w1 * x1 + w2 * x2 + b
a = z.relu()
loss = (a - target) ** 2 * Value(0.5)
loss.backward()

hand = {
    "w1": 0.2, "w2": 0.4, "b": 0.2,
    "x1": 0.1, "x2": 0.06,
}
for name, var in [("w1", w1), ("w2", w2), ("b", b), ("x1", x1), ("x2", x2)]:
    assert abs(var.grad - hand[name]) < 1e-9, (name, var.grad, hand[name])
print("All A6 hand gradients matched.")
print(loss)
```

That assertion is the pedagogical punchline: **the engine got what you derived by hand.** Stack many such ops and you have a trainable network without new math — only more graph nodes. A6 did the calculus once per layer type; A8 records layer types automatically.

### Scalar SGD step on the same neuron

The same graph supports a parameter update without new derivative rules. After `loss.backward()`, subtract a small learning rate times each parameter gradient — the scalar version of A6's `W -= lr * dW`:

```python
lr = 0.1
for p in (w1, w2, b):
    p.data -= lr * p.grad
    p.grad = 0.0  # manual zero_grad between toy steps

# Rebuild graph for second forward (fresh Value nodes)
w1b = Value(w1.data)
w2b = Value(w2.data)
bb = Value(b.data)
x1b, x2b = Value(1.0), Value(2.0)
target = Value(1.0)
z2 = w1b * x1b + w2b * x2b + bb
a2 = z2.relu()
loss2 = (a2 - target) ** 2 * Value(0.5)
print("loss before step: 0.02, loss after step:", loss2.data)
```

On the tested numbers, the second loss drops below `0.02`, confirming gradients point downhill. This is weaker than A6's full-matrix gradient check but stronger as a narrative: the **same engine** that matched your VJPs also moves parameters correctly. For matrix layers and batching, read A6; for automation, keep adding ops to `Value`. Store those parameter values between toy steps if you want a repeatable demo, because rebuilding fresh `Value` nodes each time is the safe way to avoid accidentally differentiating an old graph while inspecting a new forward pass.

---

## Part 6: From Scalar Engine to `torch.autograd`

Real frameworks implement the **same** reverse-mode contract on **tensors**. PyTorch wraps each differentiable op in an `autograd.Function` whose `backward` receives `grad_output` and returns `grad_input` tensors — tensor VJPs.generalizing the scalar closures above.

| Scalar A8 | Tensor PyTorch |
|-----------|----------------|
| `Value.data` | `tensor` data |
| `Value.grad` | `tensor.grad` |
| `_prev` edges | `grad_fn.next_functions` |
| `_backward()` | `Function.backward` |
| `loss.backward()` | `torch.autograd.backward` |

The dense-layer VJPs from A6 (`X.T @ G`, `G @ W.T`, `sum` over batch) are what PyTorch executes inside `AddmmBackward` and friends, fused and parallelized. [PyTorch autograd docs](https://pytorch.org/docs/stable/autograd.html) describe the user-facing API; the implementation still builds a DAG during forward and frees or retains it after backward.

[d2l.ai's automatic differentiation chapter](https://d2l.ai/chapter_preliminaries/autograd.html) shows the same bridge from a small `autograd` package to neural network training. Block B's [PyTorch Fundamentals](/ai-ml-engineering/deep-learning/module-1.2-pytorch-fundamentals/) module assumes this mental model: tensors are containers; autograd is the tape.

We deliberately do **not** rebuild tensor autograd in A8. Scalar code keeps the graph legible. Your `nn.py` from Block A can stay NumPy for forward/backward by hand, **or** you can wrap scalar `Value` ops for toy experiments — but production training moves to PyTorch because matrix kernels and GPU memory matter.

The tensor bridge is not a different algorithm; it is the same reverse-mode walk with richer local VJPs. When you later read PyTorch source or custom `autograd.Function` examples, you are looking at handwritten `_backward` closures attached to tensor ops — exactly the pattern you implemented on `Value`, except the data field is a strided GPU buffer and the VJP may call cuBLAS. Memory retention is also the same trade: PyTorch holds saved tensors until backward unless you opt out, which is why inference runs under `torch.no_grad()` and why training large vision models can OOM during backward even when forward fit comfortably.

Consider a PyTorch line you will write in Block B that mirrors the Part 5 neuron:

```python
import torch

x = torch.tensor([1.0, 2.0], requires_grad=True)
w = torch.tensor([0.5, 0.3], requires_grad=True)
b = torch.tensor(0.1, requires_grad=True)
z = (x * w).sum() + b
a = torch.relu(z)
loss = 0.5 * (a - 1.0) ** 2
loss.backward()
print(w.grad, b.grad)
```

The graph structure mirrors our `Value` example: `MulBackward`, `SumBackward`, `AddBackward`, `ReluBackward`, `PowBackward`. `w.grad` should match the engine within dtype tolerance. The difference is that `*` between tensors used broadcasting reduction where our scalar code used explicit `w1*x1 + w2*x2`. The [PyTorch `Tensor.backward` documentation](https://pytorch.org/docs/stable/generated/torch.Tensor.backward.html) documents `retain_graph` and `create_graph` flags that correspond directly to whether you free the tape after one reverse walk or keep building higher-order graphs.

Before you open Block B, articulate what changes when you replace scalar `*` with `torch.matmul` in a linear layer: the parent/child graph structure and reverse topological order stay the same, but each node's local VJP becomes a matrix multiply implementing the same outer-product pattern as `X.T @ G` in A6, and the cached value becomes a tensor view subject to in-place versioning rules from Part 7.

---

## Part 7: Limits and Gotchas

Autograd is reliable only when the graph contract is respected, and the failures below appear constantly in production code even on teams that understand the forward pass well. Treat this section as a compact field guide: each symptom maps to a graph invariant you can test in a minimal repro before touching model architecture.

### Memory: the graph is retained

Every intermediate cached for backward consumes memory. PyTorch frees the graph after `backward()` unless `retain_graph=True`. Long sequences or high-resolution activations can exhaust GPU memory **during backward**, not forward. [Gradient checkpointing](https://arxiv.org/abs/1604.06174) trades extra forward recomputation for lower activation memory — the same graph idea with a different memory schedule.

### In-place ops break the tape

If you mutate a tensor that backward still needs — `x += y` on an activation saved for ReLU — autograd may raise a versioning error or silently corrupt gradients. Prefer out-of-place ops while learning; use in-place only when you know what the backward kernel reads. The scalar engine makes the same requirement visible: if you could mutate `Value.data` between forward and backward, the ReLU gate would read the wrong sign. Immutability of cached forward values is not a performance quirk; it is part of the mathematical definition of differentiating the forward function you actually evaluated.

### `detach()`, `no_grad()`, and `requires_grad=False`

`detach()` removes a subtree from the graph: downstream ops run forward, but no gradient flows back through the detached edge. `torch.no_grad()` disables graph construction entirely — essential for evaluation and metric logging where you must not waste memory retaining activations you will never differentiate. Frozen parameters set `requires_grad=False` so they never receive `.grad`, which is how transfer learning keeps a pretrained backbone fixed while training a small head. In `Value` terms, detaching is like breaking `_prev` links so `_backward` never reaches chosen parents; the forward number still flows, but the chain rule stops at the cut.

### Accumulation and `zero_grad()`

Frameworks **accumulate** gradients into `.grad` across backward calls, mirroring our `+=`. Call `optimizer.zero_grad()` (or `set_to_none=True` for speed) once per step. Forgetting this is the same bug class as overwriting instead of accumulating inside `_backward`, except the stale values come from the **previous** batch.

### Second `backward()` without `retain_graph`

Calling `loss.backward()` twice on the same graph usually fails after the first call frees intermediates. Combine losses when possible: `total = loss_a + loss_b; total.backward()`. The [PyTorch tutorial on zeroing gradients](https://raw.githubusercontent.com/pytorch/tutorials/main/recipes_source/recipes/zeroing_out_gradients.py) states explicitly that `.grad` fields accumulate by default across backward calls — the framework-level version of our `+=` inside `_backward`, applied across optimizer steps instead of across graph paths.

Gradient checkpointing from [Chen et al.](https://arxiv.org/abs/1604.06174) does not change the math; it changes **when** forward values are available. Segments of the graph are recomputed during backward instead of stored wholesale, trading extra compute for lower activation memory. When you profile a large model and see backward allocating more than forward, you are looking at this retained graph cost in the wild.

| Symptom | Likely graph cause | First check |
|---------|-------------------|-------------|
| `grad is None` | Parameter not connected to loss | Trace forward path, `requires_grad` |
| Version counter error | In-place on saved tensor | Find `+=` on activations |
| OOM on backward | Graph too large | Batch size, checkpointing, `retain_graph` |
| Gradients grow each step | Missing `zero_grad()` | Optimizer loop order |

---

## Part 8: Finite Differences as an Independent Auditor

Your autograd engine is code, and code can be wrong while still returning well-formed floats. A6 already used finite-difference gradient checking on matrix parameters; the same habit applies to `Value` graphs before you trust them on a larger scalar MLP. The idea is independent of the engine: perturb one scalar parameter by a tiny `epsilon`, measure how the loss changes, and compare that slope to `param.grad` reported by `backward()`. Centered differences `(f(x+eps) - f(x-eps)) / (2*eps)` cancel some approximation error and are the default choice in debugging notebooks.

```python
def scalar_grad_check(make_loss, param, eps=1e-6):
    """Check one Value parameter against centered finite differences."""
    loss = make_loss()
    loss.backward()
    analytic = param.grad

    old = param.data
    param.data = old + eps
    plus = make_loss().data
    param.data = old - eps
    minus = make_loss().data
    param.data = old
    numeric = (plus - minus) / (2 * eps)

    return analytic, numeric, abs(analytic - numeric) / max(1e-8, abs(analytic) + abs(numeric))
```

Use this function sparingly and deliberately. Each check rebuilds the graph, so wrap `make_loss` in a factory that constructs fresh `Value` nodes every call. Reset `param.grad` to zero between checks if you reuse nodes. For the Part 5 neuron, checking `w1` should report relative error near machine epsilon for float64 semantics implemented in Python floats. If you see `1e-2` or larger, the bug is in a local rule or in graph order — not in the learning rate.

Finite differences also teach the **definition** of the gradient your engine automates. When A6 checked `dL_dW` against perturbations of one matrix entry, it was measuring the same sensitivity the chain rule computes analytically. When your scalar engine passes those checks on every op, you have evidence that each `_backward` closure matches the limit definition on a neighborhood of the test point. That evidence is local — it does not prove global convexity or convergence — but it is the right bar for releasing a custom autograd op inside a company codebase.

The workflow we recommend mirrors how framework teams land new operators. First implement the forward pass and a readable backward pass in Python. Second, gradient-check against centered differences on deterministic tiny inputs with randomness disabled. Third, compare against a reference implementation on a handful of shapes. Fourth, only then port to optimized kernels. Skipping step two is how ranking losses pass forward QA and fail silently in training, as in the hypothetical scenario at the top of this module. Your `autograd_lab.py` from the hands-on section should include at least one finite-difference test so the habit survives after the exercise ends.

When you present this engine to a teammate, lead with the graph picture, not the class definition. Draw the expression, label forward values, walk one backward message, then show that `backward()` is only automation for the walk you already did on paper. That presentation order prevents the common misconception that autograd is a separate algorithm from backpropagation. It is the same chain rule with a scheduling layer — the layer A8 implements, PyTorch scales, and A6 convinced you is worth trusting only after you have derived it once by hand.

Finally, remember the relationship between A6, A8, and PyTorch. A6 proves you can differentiate a dense layer by hand. A8 proves a graph walker can apply those same local rules without hand-deriving each expression. PyTorch proves the walker can run on tensors at scale. Finite differences are the red thread that ties all three: an independent measurement that does not care which layer of abstraction you are testing. When `param.grad` disagrees with the numeric slope, draw the graph, label the local derivatives on paper, and fix the `_backward` before touching hyperparameters.

As a capstone habit, keep a single page in your lab notebook with three columns: forward expression, local VJP rule, and finite-difference spot check. Fill one row each time you add an op to `Value` or a custom `autograd.Function` in PyTorch later. That table becomes the personal reference you will wish you had the first time a fused loss misbehaves in production — and it is the same reference A6 started when it made you write `dL_dW = X.T @ G` instead of trusting a transpose guess.

---

## Did You Know?

- **[Reverse-mode AD and backpropagation are the same structural idea](https://arxiv.org/abs/1502.05767)** expressed in different communities — automatic differentiation papers versus neural network training literature.
- **[micrograd is under 150 lines](https://github.com/karpathy/micrograd)** yet implements everything needed to train a small MLP, because the heavy lifting is local VJPs, not graph magic.
- **[PyTorch builds the graph dynamically](https://pytorch.org/docs/stable/notes/autograd.html)** as Python executes the forward pass, which is why control flow and varying sequence lengths are first-class — unlike older static-graph frameworks.
- **Gradient accumulation in the engine (`+=`) and gradient accumulation across micro-batches in training** share a name because both sum contributions before an optimizer step, even though one happens inside a single backward graph walk and the other happens across multiple forward passes before `optimizer.step()`.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Using `=` instead of `+=` in `_backward` | Drops gradient paths when a value is reused | Always accumulate into parent `.grad` |
| Running `_backward` before all downstream nodes finish | Incomplete upstream gradient on shared nodes | Strict reverse topological order |
| Re-deriving matrix backprop inside A8 | Duplicates A6, confuses engine vs layer math | Link to A6; keep A8 scalar |
| Expecting autograd without building the graph | Calling backward on constants or detached tensors | Ensure ops involve `Value`/`tensor` with grad enabled |
| Ignoring `relu(0)` convention | Hand and engine disagree at exactly zero | Document subgradient `0` at zero; match PyTorch |
| Training without `zero_grad()` | Stale gradients from prior steps | Clear grads each optimizer step |
| In-place tensor updates on cached activations | Corrupts backward or raises version errors | Out-of-place until you know the kernel contract |

---

## Quiz

1. **In your scalar autograd engine, why must `backward()` process nodes in reverse topological order rather than an arbitrary reverse list of operations?**

<details>
<summary>Answer</summary>

Each node's `_backward` distributes `out.grad` to parents. That `out.grad` must already include contributions from **all** nodes that consume `out`. Reverse topological order ensures every consumer runs before the producer's backward closure. Running early would partial-sum upstream gradients and under-estimate parent gradients, especially on shared nodes.
</details>

2. **For expression `y = x * x + x`, your engine returns `x.grad = 6` at `x = 3`. What implementation bug does that indicate?**

<details>
<summary>Answer</summary>

The analytic gradient is `2x + 1 = 7`. A result of `6` means one path contributed (`2x`) but the `+ x` path's unit contribution was dropped — classic **assignment instead of accumulation** or an addition backward that never ran. Fix local `_backward` to use `+=` and verify both edges from `x` are in the graph.
</details>

3. **A model has one million parameters and one scalar cross-entropy loss. Why is reverse-mode automatic differentiation preferred over forward-mode AD for training?**

<details>
<summary>Answer</summary>

Reverse mode seeds the single loss and computes all parameter gradients in one backward traversal — cost proportional to graph size, not parameter count times graph size. Forward mode would need on the order of one forward pass per parameter for the same scalar loss. Training needs all parameter gradients each step, so reverse mode wins.
</details>

4. **You call `loss.backward()` successfully, then call it again on the same PyTorch graph without `retain_graph=True` and get an error. Why?**

<details>
<summary>Answer</summary>

PyTorch frees intermediate buffers and graph nodes after backward to save memory. The second backward needs cached forward values that were released. Combine losses for one backward, or pass `retain_graph=True` when multiple backward passes are intentional — accepting higher memory use.
</details>

5. **A `Value` graph computes `c = (a + a) * a` with `a = 2`. What is `a.grad` after `c.backward()`, and how many distinct graph edges contribute?**

<details>
<summary>Answer</summary>

`c = 2a * a = 2a^2`, so `dc/da = 4a = 8` at `a = 2`. Three edges touch `a`: two from the additions inside `a + a`, each contributing `out.grad` from the multiply's upstream, and one from the multiply's `other` slot. Accumulation sums them into `8.0`. If you get `4.0` or `6.0`, trace which `_backward` used `=` instead of `+=`.
</details>

6. **In the `Value.relu()` implementation, why does `_backward` read the cached forward pre-activation in `self.data` instead of recomputing ReLU inputs from parent nodes at backward time?**

<details>
<summary>Answer</summary>

The ReLU gate depends on whether the pre-activation was positive at **forward time**. Recomputing from parents after intermediate mutations could use stale or in-place-altered values. Caching matches PyTorch's saved-tensor contract and prevents silent wrong masks when inputs change between forward and backward.
</details>

7. **Contrast forward-mode and reverse-mode automatic differentiation: when is forward mode preferable for Jacobian shapes, and why does reverse mode remain the default when one scalar loss depends on millions of parameters?**

<details>
<summary>Answer</summary>

Contrast forward-mode and reverse-mode automatic differentiation by seed direction: forward-mode is preferable when there are few inputs and many scalar outputs, because it propagates directional derivatives cheaply. Reverse-mode remains the default for neural network training because one scalar loss depends on millions of parameters and one reverse pass reaches all of them — the justify case from the learning outcomes. The [Baydin et al. survey](https://arxiv.org/abs/1502.05767) discusses this complexity tradeoff formally.
</details>

8. **When you implement tensor autograd later, a dense layer backward needs `X.T @ G`. Which scalar multiplication and accumulation pattern from this module is it generalizing?**

<details>
<summary>Answer</summary>

Each weight connects one input feature to one output unit. The scalar multiplication rule sends `upstream * input_value` to the weight parent; summing across batch rows is the matrix multiply `X.T @ G`. See [A6](/ai-ml-engineering/deep-learning/module-1.1.6-backprop-by-hand-dense-nets/) for the full batched derivation — A8 automates the scheduling, not the formula.
</details>

---

## Hands-On Exercise: Build, Match, and Stress the Engine

**Task:** Implement or copy the `Value` class from Part 3, verify the Part 1 graph and Part 5 A6-matching neuron, stress-test gradient accumulation on reused nodes, inject a deliberate `+=` versus `=` bug, and optionally spot-check one compound op with centered finite differences.

### Step 1: Create `autograd_lab.py`

Create a local file named `autograd_lab.py` and paste the complete `Value` class from Part 3, including `backward()` and every operator used in the tests below.

- [ ] `data`, `grad`, `_prev`, `_op`, `_backward` present
- [ ] `__add__`, `__mul__`, `__pow__`, `__neg__`, `__sub__`, `__truediv__` work
- [ ] `tanh`, `relu`, `exp` implemented
- [ ] `backward()` builds topo order and seeds `grad = 1.0` on the loss

### Step 2: Verify the Part 1 graph

Using `a=2, b=3, c=1, d=1.5`, build the Part 1 graph in code and assert that every gradient matches the hand-derived values from Part 2 within `1e-9`.

- [ ] `L.data == 10.5`
- [ ] `a.grad == 4.5`, `b.grad == 3.0`, `c.grad == 1.5`, `d.grad == 7.0`

### Step 3: A6 agreement test

Run the Part 5 two-input neuron with squared-error loss and assert that all six parameter and input gradients match the A6 hand derivation within `1e-9`.

- [ ] `loss.data == 0.02`
- [ ] `w1.grad == 0.2`, `w2.grad == 0.4`, `b.grad == 0.2`

### Step 4: Reuse stress test

Implement and assert the reuse stress tests `y = x * x + x` at `x=3` and `c = (a + a) * a` at `a=2` from Part 3, confirming accumulation not assignment.

- [ ] `x.grad == 7.0` at `x = 3`
- [ ] `a.grad == 8.0` at `a = 2`

### Step 5: Deliberate bug injection

Change one `+=` to `=` inside `__mul__._backward`, re-run the Step 4 reuse tests, confirm at least one assertion fails, and document which graph path was dropped.

- [ ] You can explain the failure in terms of graph paths, not just "wrong number"

### Step 6: Optional finite-difference spot check

For `f(x) = log(x.exp())` at `x = 1.5`, compare the engine gradient to a centered finite-difference estimate with `eps = 1e-6` and confirm relative error stays below `1e-5`. Because `log(exp(x)) = x`, the engine gradient should be approximately `1.0` and the finite-difference check confirms it.

Document one failing and one passing assertion in a short comment at the top of `autograd_lab.py` so future you remembers which graph path the accumulation bug broke when `+=` became `=`. That comment is cheap insurance against reintroducing the same silent bug when you port activations or losses from `nn.py` into `Value` ops. Run all checks from the repository root or your lab directory with the command below.

```bash
python autograd_lab.py
```

---

## Learner check

> An engine that assigns `self.grad = ...` in `_backward` keeps only the last path.

Confirm you understand why gradient accumulation via `+=` is required when a value participates in multiple graph paths.

---

## Next Module

Block A ends here. You began with NumPy habits and finite differences in A1, built neurons and forward passes through A3 and A4, derived losses and hand backprop in A5 and A6, and now close the arc with an autograd engine that would have automated every scalar chain rule you wrote by hand during those modules. The cumulative `nn.py` file remains valuable as a NumPy teaching artifact, but production work in Block B assumes PyTorch's tensor graph is the system of record for gradients.

Next: **[PyTorch Fundamentals](/ai-ml-engineering/deep-learning/module-1.2-pytorch-fundamentals/)** — the same computational-graph contract, now on tensors with `torch.autograd`, GPU execution, and the training loops you will use for real models. When you type `loss.backward()` there, picture the topological walk you implemented in this module — only now the nodes are CUDA kernels and the VJPs are matrix multiplies you derived in A6.

---

## Sources

- [micrograd (Karpathy)](https://github.com/karpathy/micrograd) — Minimal scalar autograd engine that inspired the `Value` design in this module.
- [The spelled-out intro to neural networks and backpropagation](https://www.youtube.com/watch?v=VMj-3S1tku0) — Graph-level backpropagation walkthrough paired with micrograd.
- [CS231n: Backpropagation, intuitions](https://cs231n.github.io/optimization-2/) — Local gradient × upstream gradient at each graph node.
- [PyTorch autograd documentation](https://pytorch.org/docs/stable/autograd.html) — Production tensor autograd API and semantics.
- [PyTorch autograd mechanics (notes)](https://pytorch.org/docs/stable/notes/autograd.html) — Dynamic graph construction and saved-variable behavior.
- [torch.Tensor.backward](https://pytorch.org/docs/stable/generated/torch.Tensor.backward.html) — `retain_graph`, `create_graph`, and gradient kwargs.
- [Automatic Differentiation in Machine Learning: a Survey (Baydin et al.)](https://arxiv.org/abs/1502.05767) — Forward vs reverse mode and complexity discussion.
- [Automatic differentiation (Wikipedia)](https://en.wikipedia.org/wiki/Automatic_differentiation) — Historical context for reverse mode.
- [d2l.ai: Automatic differentiation](https://d2l.ai/chapter_preliminaries/autograd.html) — Bridge from toy autograd to deep learning frameworks.
- [Training Deep Nets with Sublinear Memory Cost](https://arxiv.org/abs/1604.06174) — Gradient checkpointing tradeoff referenced in Part 7.
- [PyTorch tutorial: zeroing out gradients](https://raw.githubusercontent.com/pytorch/tutorials/main/recipes_source/recipes/zeroing_out_gradients.py) — Accumulation semantics across optimizer steps.
