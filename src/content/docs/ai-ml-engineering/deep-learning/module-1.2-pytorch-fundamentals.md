---
title: "The PyTorch Bridge: From Your NumPy Engine to torch"
slug: ai-ml-engineering/deep-learning/module-1.2-pytorch-fundamentals
sidebar:
  order: 1003
---

In 2019, the PyTorch team presented the framework to the systems community as a tool built around an unusually simple promise: write ordinary Python, run tensor operations eagerly, and let automatic differentiation record the graph as the program executes. That design choice matters for you because Block A just made the same promise at a smaller scale. You wrote NumPy arrays, cached intermediate activations, hand-derived vector-Jacobian products in A6, trained a Fashion-MNIST MLP in A7, and built a scalar `Value` autograd engine in A8. PyTorch is the production version of that work: the tensors are faster, the kernels can run on GPUs, and the graph engine handles tensor VJPs, but the training story is still forward pass, loss, backward pass, parameter update.

Think of this module as a bridge rather than a reset. We will not rebuild a neuron, re-derive softmax cross-entropy, or pretend `loss.backward()` is a new mathematical idea. Instead, each PyTorch primitive will be mapped to something you already built by hand. A `torch.Tensor` is your Block A NumPy array with device placement and autograd metadata. `nn.Linear` is your A7 `Layer` with battle-tested parameter registration. `torch.optim.SGD` is the `W -= lr * dW` loop you wrote by hand. `nn.CrossEntropyLoss` is the stable softmax-CE from A5 wrapped behind an API that expects logits and integer class labels. The magic is not new math; the magic is engineering scale.

## Learning Outcomes

By the end of this module, you will be able to:

- Implement PyTorch tensor creation, shape inspection, dtype conversion, NumPy round-trips, broadcasting, indexing, and device movement while explaining how each operation maps back to the arrays and shape discipline from A1 through A3.
- Debug a small differentiable PyTorch computation by comparing finite-difference gradients to `torch.autograd`, then explain why `loss.backward()` performs the same reverse topological walk your A8 `Value.backward()` implemented.
- Construct an `nn.Module` and an equivalent `nn.Sequential` MLP, inspect registered parameters, and connect every `nn.Linear` weight and bias to the hand-rolled A7 `Layer` fields.
- Execute the canonical optimizer step sequence, `zero_grad(set_to_none=True)` -> forward -> loss -> backward -> `step()`, and relate `torch.optim.SGD` to the manual `W -= lr * dW` update loop from A7.
- Build a small `Dataset` and `DataLoader`, then translate the A7 Fashion-MNIST MLP into PyTorch using `nn.CrossEntropyLoss`, an SGD optimizer, mode toggles, and disciplined device placement.

## Why This Module Matters

Frameworks become dangerous when they make unfamiliar work look short. A learner who begins with PyTorch often sees five lines of code, trains a classifier, and concludes that deep learning is mostly API memorization. Block A deliberately denied you that shortcut. You saw that a dense layer is a matrix multiply plus a bias, that activation functions cache masks or nonlinear values, that cross-entropy should be computed from logits with numerical care, that gradients must flow in reverse order, and that parameters only improve after an explicit update step. Now that you know the machinery, PyTorch can become a force multiplier instead of a black box.

The bridge also protects you from the most common beginner failures. When `grad is None`, you will ask whether the tensor was connected to the loss instead of randomly changing the learning rate. When validation accuracy looks frozen, you will check whether gradients accumulated across batches because `zero_grad()` was missing. When a CUDA tensor meets a CPU tensor, you will recognize a device-placement bug rather than a mysterious framework failure. When `model.eval()` changes outputs, you will remember that some modules carry mode-dependent behavior. These are engineering habits, not abstract mathematical facts, and they are easier to learn when every PyTorch primitive has a Block A ancestor.

The bridge analogy is literal. On one side is your NumPy micro-framework: transparent, small, slow, and excellent for learning. On the other side is PyTorch: optimized kernels, device backends, registered modules, optimizers, data pipelines, and a tensor autograd engine. The planks across the bridge are one-to-one mappings. If a plank does not connect to something you built, we will name the missing concept and defer it to a later Block B module instead of smuggling in a new abstraction too early.

Here is the whole map before we cross it. Read it from left to right and notice how little new math appears. Most of the new vocabulary names ownership and scale: which object owns parameters, which object owns a batch, which object owns the update rule, and which device owns the memory.

```text
Block A hand-built system                   PyTorch production primitive
--------------------------------------------------------------------------------
NumPy arrays with shapes and dtypes     ->  torch.Tensor with dtype and device
Cached forward values in each Layer     ->  dynamic autograd graph nodes
A6 dense-layer VJPs                     ->  tensor backward kernels
A7 Layer(W, b, forward, backward)       ->  nn.Linear inside nn.Module
A5 stable softmax cross-entropy         ->  nn.CrossEntropyLoss on logits
Manual W -= lr * dW update              ->  torch.optim.SGD.step()
Manual shuffled index mini-batches      ->  Dataset plus DataLoader
Hand-written train/eval metric blocks   ->  B2's structured training loop
```

The right column is not superior because it hides the left column; it is superior because it preserves the left column while making the repetitive engineering reliable. PyTorch frees you from retyping the dense-layer backward formula, but it does not free you from checking that logits have shape `[batch, classes]`. It removes your hand-written softmax, but it does not remove the need to pass class-index labels. It gives you a `DataLoader`, but it does not decide whether your data should be shuffled, normalized, split, cached, or moved to a GPU. Treat the framework as a set of named replacements for work you understand, and the API surface becomes much smaller.

## Part 1: `torch.Tensor` Is the NumPy Array You Already Know

The first PyTorch object to demystify is `torch.Tensor`. In Block A, your data lived in NumPy arrays with shapes such as `(batch, features)`, `(784, 256)`, or `(batch, classes)`. A PyTorch tensor has the same core contract: it stores typed numeric data in a rectangular shape, supports vectorized operations, follows broadcasting rules, and can be indexed or reshaped without writing Python loops. The additional production concerns are dtype, device, and optional autograd metadata. Those extra fields are what let the same math run on CPU, CUDA, or Apple's MPS backend while remaining differentiable when needed.

```python
import numpy as np
import torch

# Two samples, three features, exactly like the small matrices from A1-A3.
features_np = np.array(
    [[1.0, 2.0, 3.0],
     [4.0, 5.0, 6.0]],
    dtype=np.float32,
)

features = torch.from_numpy(features_np)  # shape: [2, 3], dtype: torch.float32
bias = torch.tensor([0.1, -0.2, 0.3], dtype=torch.float32)  # shape: [3]

centered = features - features.mean(dim=0, keepdim=True)  # shape: [2, 3]
shifted = centered + bias  # broadcasting [3] across the batch dimension

print(features.shape, features.dtype)
print(shifted)
```

This code should feel almost boring after A1. The batch axis is still axis 0. `mean(dim=0, keepdim=True)` preserves a `(1, 3)` row so subtraction broadcasts across both samples. Adding `bias` with shape `[3]` uses the same broadcasting idea you practiced with NumPy. PyTorch uses `dim` where NumPy often says `axis`, but the mental model is identical: reduce or index along a named dimension, keep dimensions when you need later broadcasting to remain explicit, and inspect shapes before blaming the optimizer.

Indexing follows the same discipline. If `images` has shape `[batch, channels, height, width]`, then `images[:, 0, :, :]` selects the first channel for every sample, while `images[0]` selects one complete image and drops the batch dimension. That dimension drop is often correct for inspection and wrong for model input. A single image with shape `[1, 28, 28]` cannot feed a model expecting a batch unless you add the batch axis back with `unsqueeze(0)`, producing `[1, 1, 28, 28]`. This is the same shape reasoning you practiced in A3, now with the image convention explicit.

The most common tensor debugging move is not printing the entire tensor; it is printing a compact shape and dtype trace at the boundary between components. Before a model call, log `xb.shape`, `xb.dtype`, `xb.device`, `yb.shape`, `yb.dtype`, and `yb.device`. Before a loss call, log `logits.shape` and `yb.shape`. If those facts are correct, many scary training failures become ordinary questions about optimization. If those facts are wrong, no optimizer or initialization trick can compensate for a broken contract.

The NumPy bridge is also direct. `torch.from_numpy(array)` creates a tensor that shares memory with the NumPy array when possible, and `tensor.numpy()` returns a NumPy view for CPU tensors that do not require gradients. That shared-memory behavior is convenient but worth respecting: mutating one side can mutate the other side. For teaching experiments, it is useful because you can reuse the arrays from A7 without rewriting the data loader. For production code, explicit `.clone()` calls are often clearer when ownership matters.

```python
features_np[0, 0] = 10.0
print(features[0, 0].item())  # 10.0, because from_numpy shares CPU memory

copy_for_training = torch.from_numpy(features_np).clone()
round_trip_np = copy_for_training.numpy()
print(type(round_trip_np), round_trip_np.shape)  # <class 'numpy.ndarray'>, (2, 3)
```

Two dtype habits matter immediately. Model inputs are usually `torch.float32` unless you intentionally use mixed precision later. Class labels for `nn.CrossEntropyLoss` are integer class indices with dtype `torch.long`, not one-hot float matrices. In A5 you built softmax-CE from one-hot targets because it made the derivative `p - y` visible. In PyTorch, `nn.CrossEntropyLoss` expects raw logits of shape `[batch, classes]` and labels of shape `[batch]`, because it combines log-softmax and negative log-likelihood internally in a stable implementation.

This label change is a good example of "same math, different engineering contract." A5 used one-hot labels so the derivative could be written as a vector subtraction. PyTorch uses integer labels because the implementation can index the correct class directly and avoid storing a dense one-hot matrix for every batch. The gradient with respect to logits is still the same softmax-probability-minus-target idea; the target representation is simply more compact at the API boundary.

```python
logits = torch.randn(4, 10, dtype=torch.float32)  # shape: [batch=4, classes=10]
labels = torch.tensor([0, 3, 4, 9], dtype=torch.long)  # shape: [4]

loss_fn = torch.nn.CrossEntropyLoss()
loss = loss_fn(logits, labels)
print(loss.item())
```

Device placement is the second new field. A tensor lives on exactly one device, and operations usually require all participating tensors to live on the same device. CPU tensors cannot be added to CUDA tensors. CUDA tensors cannot feed a model whose parameters remain on CPU. The fix is not complicated; it is discipline. Pick a device, move the model once, and move every mini-batch to that device inside the training loop.

```python
def best_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


device = best_device()

features = features.to(device)
labels = labels.to(device)
print(features.device, labels.device)
```

The practical rule is simple enough to tape beside your monitor: data, labels, and model parameters must be on the same device before the forward pass. In A7, this problem did not exist because every NumPy array lived in CPU memory. PyTorch adds acceleration, but acceleration means memory ownership now matters. Later modules will discuss profiling and mixed precision; for B1, the correct habit is to choose the device explicitly and keep every tensor in a training step on it.

Do not treat `.to(device)` as a harmless decoration. It usually returns a tensor on the requested device rather than mutating the original tensor in place, so forgetting assignment leaves the old tensor where it was. The model call `model.to(device)` mutates module parameters recursively and returns the module for convenience, which is why both `model.to(device)` and `model = model.to(device)` are common. Tensors and modules therefore look similar at the call site but differ in ownership details. A disciplined batch-transfer helper avoids relying on memory of those details during a late-night debugging session.

## Part 2: Autograd Is Your A8 Engine, Scaled to Tensors

In A8, your scalar `Value` class built a computation graph during the forward pass. Each operation created a node, stored parent pointers, cached the local backward rule, and then `backward()` walked the graph in reverse topological order while accumulating gradients with `+=`. PyTorch autograd follows the same contract. The difference is that the nodes are tensor operations such as matrix multiply, addition, ReLU, indexing, and reduction, and the local VJPs are implemented in optimized C++ and backend kernels instead of handwritten Python closures.

The graph is dynamic, which means ordinary Python control flow participates naturally. If an `if` statement chooses one branch during the forward pass, autograd records the operations that actually ran, not the operations that could have run. If a loop iterates ten times for one sequence and twelve times for another, the recorded graph for each forward pass reflects that execution. This is why the 2019 PyTorch paper emphasized imperative, eager execution: the user's Python program is the graph-building language. A8 gave you the same property at scalar scale because `Value` nodes appeared only when your Python operators executed.

Leaf tensors deserve a precise definition. A leaf tensor is typically a tensor you created directly with `requires_grad=True`, such as a model parameter. Gradients are populated on leaf tensors by default because those are the values optimizers update. Intermediate tensors usually have a `grad_fn` instead of a populated `.grad`; they know how they were produced, but PyTorch does not retain their gradients unless you explicitly ask. This is why inspecting `parameter.grad` after backward is normal, while expecting every hidden activation to have `.grad` populated is a misunderstanding of the graph's memory policy.

The smallest useful example is a differentiable scalar function where you can compare finite differences from A1 with autograd from PyTorch. Use float64 here because finite differences are a numerical audit, and the extra precision makes the comparison less noisy. This is not a training recommendation; normal neural-network training usually uses float32 or a deliberate mixed-precision policy.

```python
import numpy as np
import torch

torch.manual_seed(0)

x = torch.tensor([0.25, -0.50, 1.25], dtype=torch.float64, requires_grad=True)
loss = (torch.sin(x) * x + x.pow(2)).sum()
loss.backward()

print("autograd gradient:", x.grad)

def f_numpy(v: np.ndarray) -> float:
    return float(np.sum(np.sin(v) * v + v**2))


eps = 1e-6
x_np = x.detach().numpy().copy()
finite_diff = np.zeros_like(x_np)

for i in range(x_np.size):
    plus = x_np.copy()
    minus = x_np.copy()
    plus[i] += eps
    minus[i] -= eps
    finite_diff[i] = (f_numpy(plus) - f_numpy(minus)) / (2 * eps)

print("finite difference:", finite_diff)
print("max abs error:", np.max(np.abs(finite_diff - x.grad.detach().numpy())))
```

The call to `requires_grad=True` tells PyTorch to record operations that depend on `x`. The forward expression builds a graph. The final `.sum()` turns the vector expression into one scalar loss, which is the standard reverse-mode training shape. `loss.backward()` seeds `dloss/dloss = 1` and performs the same reverse graph walk as your A8 engine. The `.grad` field on `x` then contains the accumulated gradient of that scalar loss with respect to every element of `x`.

The finite-difference comparison is slow because it perturbs one coordinate at a time and reruns the whole function for each coordinate. That slowness is exactly why reverse-mode autograd matters for training. A neural network may have millions of parameters but one scalar loss, so one reverse walk can compute all parameter gradients together. A finite-difference checker is still valuable as a microscope for a tiny custom operation, but it is not a training algorithm. You used it in A1 and A6 for trust-building; PyTorch uses analytic VJPs for actual learning.

There are two important boundary tools. `with torch.no_grad():` temporarily disables gradient tracking for operations inside the block, which is what you want during evaluation or manual parameter updates in a toy example. `.detach()` returns a tensor that shares the same data but is disconnected from the current autograd graph, which is useful for logging, NumPy conversion, or stopping gradients intentionally. Do not use either one casually inside a model's `forward()` method; they are graph surgery tools, and graph surgery changes what learning can optimize.

The difference between `no_grad()` and `detach()` is mainly about scope. `no_grad()` is a temporary mode for a block of operations: all computations inside the block avoid graph recording. `detach()` is a tensor-level boundary: one tensor leaves the graph, and future operations built from that detached tensor are disconnected from the earlier history. Logging a loss with `loss.item()` is another boundary, because it extracts a Python number that cannot carry gradients. These tools are good when intentional and disastrous when used to silence an error you did not understand.

```python
w = torch.tensor(2.0, requires_grad=True)

loss = (w - 5.0).pow(2)
loss.backward()
print("before update:", w.item(), "grad:", w.grad.item())  # grad is -6.0

with torch.no_grad():
    w -= 0.1 * w.grad

w.grad = None
print("after update:", w.item())  # 2.6
```

Gradient accumulation is the first autograd behavior that surprises learners. PyTorch adds into `.grad`; it does not overwrite it. That is the same `+=` rule you used inside A8 because a value may receive gradient contributions from several paths. Across training iterations, however, you usually want each mini-batch to compute a fresh gradient estimate. That is why optimizer steps begin with `optimizer.zero_grad(set_to_none=True)`.

```python
w = torch.tensor(2.0, requires_grad=True)

loss1 = w * w
loss1.backward()
print(w.grad.item())  # 4.0

loss2 = 3.0 * w
loss2.backward()
print(w.grad.item())  # 7.0, because 4.0 + 3.0 accumulated

w.grad = None
```

This behavior is not a bug; it is a feature that enables gradient accumulation across micro-batches when batch memory is limited. The bug is forgetting which behavior you intend. In normal B1 training, clear gradients once per optimizer step. In deliberate gradient accumulation, clear them only after several backward passes and scale the loss accordingly. B2 will turn this into a complete training-loop discipline, but the core reason already lives in your A8 graph engine.

One final autograd habit: rebuild the graph every training iteration. In PyTorch, the graph created by a forward pass is normally freed after `backward()` because saved intermediates consume memory. If you compute one loss, call `backward()`, and then try to backward through the exact same graph again, PyTorch will complain unless you asked to retain the graph. The usual training loop does not need retention. It runs a fresh forward pass for the next mini-batch, creating a fresh graph that reflects the current parameters and inputs.

## Part 3: `nn.Module` and `nn.Linear` Are Your A7 `Layer`

In A7, your `Layer` class owned a weight matrix `W`, a bias vector `b`, a forward method, cached activations, and gradient fields such as `dW` and `db`. PyTorch packages the same idea into `nn.Module`. A module owns parameters, defines `forward()`, can contain child modules, and exposes `parameters()` so optimizers can find what should be updated. `nn.Linear(in_features, out_features)` is the dense layer you wrote by hand, with weight shape `[out_features, in_features]` and bias shape `[out_features]`.

That weight orientation surprises many NumPy-first learners because A7 may have stored weights as `[in_features, out_features]` and computed `X @ W + b`. PyTorch stores `Linear.weight` as `[out_features, in_features]` and computes the equivalent affine transform internally. You should not transpose it during normal use; just know the registered parameter's shape when inspecting it. The external contract remains simple: an input batch shaped `[batch, in_features]` becomes logits or activations shaped `[batch, out_features]`.

```python
import torch
from torch import nn


class TinyMLP(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.hidden = nn.Linear(4, 8)  # input features 4 -> hidden units 8
        self.output = nn.Linear(8, 3)  # hidden units 8 -> class logits 3

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = torch.relu(self.hidden(x))
        return self.output(h)


model = TinyMLP()
xb = torch.randn(5, 4)  # shape: [batch=5, features=4]
logits = model(xb)     # shape: [5, 3]

for name, parameter in model.named_parameters():
    print(name, tuple(parameter.shape), parameter.requires_grad)
```

The output names are the first payoff: `hidden.weight`, `hidden.bias`, `output.weight`, and `output.bias` are registered automatically because they are parameters inside child modules assigned as attributes. You did that bookkeeping manually in A7 with a `parameters()` generator. PyTorch does it consistently across nested models, which is why optimizers can receive `model.parameters()` without you passing every matrix by hand.

Registration is the reason subclassing `nn.Module` correctly matters. If you store a raw tensor as `self.weight = torch.randn(...)`, PyTorch will not automatically treat it as a trainable parameter unless it is wrapped as `nn.Parameter`. If you store child layers in a plain Python list instead of `nn.ModuleList`, PyTorch may not discover their parameters recursively. The safest early habit is to use built-in modules as attributes, `nn.Sequential`, `nn.ModuleList`, or `nn.Parameter` only when you can explain why you need manual ownership.

The conceptual mapping is tight enough to put in a table:

| Block A object | PyTorch object | What changed |
|---|---|---|
| `np.ndarray` activation batch | `torch.Tensor` | Adds dtype, device, and optional autograd graph metadata |
| `Layer.W` and `Layer.b` | `nn.Linear.weight` and `nn.Linear.bias` | Registered as trainable `nn.Parameter` objects |
| `Layer.forward(X)` | `Module.forward(x)` | Called by `model(x)` so hooks and module machinery work |
| `Layer.backward(G)` | `loss.backward()` through autograd | Dense-layer VJPs are generated and scheduled by the graph engine |
| `model.parameters()` in A7 | `model.parameters()` in PyTorch | Same name, but recursive and standardized across modules |

You will also see `nn.Sequential`, which is useful for simple feed-forward stacks. It is not less real than a custom class; it is just a compact container when the forward pass is a straight chain. Use a custom `nn.Module` when you need named subparts, multiple inputs, control flow, or extra helper methods. Use `nn.Sequential` when the architecture is genuinely linear.

```python
sequential_model = nn.Sequential(
    nn.Linear(4, 8),
    nn.ReLU(),
    nn.Linear(8, 3),
)

logits = sequential_model(torch.randn(5, 4))
print(logits.shape)  # torch.Size([5, 3])
```

For the A7 Fashion-MNIST MLP, the module translation is straightforward. A7 used flattened 28 by 28 images, one hidden dense layer with 256 units, ReLU, and a 10-class output head. In PyTorch, that becomes `nn.Flatten()`, `nn.Linear(784, 256)`, `nn.ReLU()`, and `nn.Linear(256, 10)`. Notice what is absent: no explicit cache fields, no hand-written backward method, and no one-hot target matrix for cross-entropy.

```python
class FashionMLP(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Flatten(),        # [batch, 1, 28, 28] -> [batch, 784]
            nn.Linear(28 * 28, 256),
            nn.ReLU(),
            nn.Linear(256, 10),  # raw logits for 10 Fashion-MNIST classes
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


model = FashionMLP()
example_images = torch.randn(32, 1, 28, 28)
example_logits = model(example_images)
print(example_logits.shape)  # torch.Size([32, 10])
```

This is the same MLP skeleton as A7 with much less handwritten infrastructure. The dense math is still `X @ W.T + b`, the activation is still ReLU, and the output is still raw class logits. PyTorch simply owns the repetitive engineering: parameter registration, graph construction, dense-layer backward kernels, and optimizer integration.

The `state_dict()` method is another ownership payoff. It returns a mapping from parameter and buffer names to tensors, which is what checkpointing uses later. B2 will handle checkpoint discipline, but the idea begins here: once modules own parameters with stable names, saving, loading, freezing, and inspecting models becomes systematic. Your A7 micro-framework could do this only if you wrote the naming and serialization conventions yourself.

## Part 4: Optimizers Are the Manual `W -= lr * dW` Loop

The canonical PyTorch training step has a fixed order. Clear stale gradients, run the forward pass, compute a scalar loss, call backward, then update parameters. Change that order only when you can explain the reason. In A7, you updated each layer by iterating over `(param, grad)` pairs and subtracting `lr * grad`. `torch.optim.SGD` performs the same operation over registered parameters, with optional extras such as momentum left for B4.

The fixed order is a debugging tool. If loss is `nan`, inspect the forward and loss before backward. If gradients are missing, inspect the graph connection before `step()`. If parameters do not change, inspect `.grad` after backward and before the optimizer clears or steps. A training loop with the same order every time creates reliable observation points. A loop that sometimes clears gradients after forward, sometimes after step, and sometimes not at all makes every later failure harder to localize.

```python
import torch
from torch import nn

torch.manual_seed(7)

model = nn.Sequential(
    nn.Linear(4, 8),
    nn.ReLU(),
    nn.Linear(8, 3),
)

optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
loss_fn = nn.CrossEntropyLoss()

xb = torch.randn(16, 4)                         # shape: [16, 4]
yb = torch.randint(0, 3, size=(16,), dtype=torch.long)  # shape: [16]

model.train()
optimizer.zero_grad(set_to_none=True)
logits = model(xb)               # shape: [16, 3]
loss = loss_fn(logits, yb)        # scalar
loss.backward()
optimizer.step()

print(loss.item())
```

The `zero_grad(set_to_none=True)` call is current PyTorch idiom and often avoids unnecessary memory writes compared with filling existing gradient tensors with zeros. After backward, each parameter's `.grad` field contains the gradient for the current mini-batch. `optimizer.step()` reads those gradients and mutates parameters under the hood. That mutation is why you should not call `step()` before `backward()`, and why stale gradients produce a different update than the one your current batch actually requested.

It is legal to call `zero_grad()` after `step()` instead of before the next forward pass, and some codebases do. This module uses the before-forward pattern because it makes the invariant visible: at the start of each mini-batch, parameter gradients are empty. The exact placement is less important than consistency, but consistency matters more than style. When you later read unfamiliar code, identify where gradients become empty, where they become populated, and where the optimizer consumes them.

If you want to see the connection to A7 explicitly, compare SGD to a manual update on a single parameter. This toy block is not how you should train modules in real code, but it reveals the same arithmetic.

```python
weight = torch.tensor([1.0, -2.0], requires_grad=True)
loss = (weight * weight).sum()
loss.backward()

with torch.no_grad():
    manual_updated = weight - 0.1 * weight.grad

print(weight.grad)       # tensor([ 2., -4.])
print(manual_updated)    # tensor([ 0.8000, -1.6000])
```

That subtraction is all plain SGD does before you add variants. Adam, AdamW, schedulers, warmup, and learning-rate dynamics are important, but they are B4's topic. In B1, the goal is to establish that an optimizer object is a disciplined wrapper around parameter mutation after autograd has filled `.grad`.

`torch.optim.SGD` also owns optimizer state, even when plain SGD has almost none. Once momentum enters, the optimizer remembers velocity tensors for each parameter. Once AdamW enters, it remembers moving averages. That state is why optimizers are objects rather than single functions, and why checkpointing later saves both `model.state_dict()` and `optimizer.state_dict()`. For B1, remember only the basic relationship: autograd computes gradients; the optimizer decides how to use them to mutate parameters.

## Part 5: `Dataset` and `DataLoader` Replace Hand-Sliced Mini-Batches

A7 made you shuffle indices and slice arrays manually. PyTorch keeps the same mini-batch concept but standardizes the data pipeline with `Dataset` and `DataLoader`. A `Dataset` answers two questions: how many examples exist, and what is example `i`? A `DataLoader` handles batching, optional shuffling, collation, and worker processes. The training loop then receives tensors through the familiar `for xb, yb in loader:` idiom.

Separate those responsibilities carefully. The `Dataset` should represent individual examples and deterministic transforms that belong to an example. The `DataLoader` should decide how examples are grouped into mini-batches and whether their order is shuffled. The model should not know whether a batch came from an in-memory tensor, an image folder, a parquet file, or a streaming source. That separation is the reason the same training step can work with a tiny synthetic dataset in B1 and a production input pipeline later.

```python
from torch.utils.data import Dataset, DataLoader


class TensorClassificationDataset(Dataset):
    def __init__(self, x: torch.Tensor, y: torch.Tensor) -> None:
        if x.shape[0] != y.shape[0]:
            raise ValueError("features and labels must have the same first dimension")
        self.x = x
        self.y = y

    def __len__(self) -> int:
        return self.x.shape[0]

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self.x[index], self.y[index]


images = torch.rand(128, 1, 28, 28)                         # shape: [128, 1, 28, 28]
labels = torch.randint(0, 10, size=(128,), dtype=torch.long)  # shape: [128]
dataset = TensorClassificationDataset(images, labels)

loader = DataLoader(dataset, batch_size=32, shuffle=True, num_workers=0)

for xb, yb in loader:
    print(xb.shape, yb.shape)  # torch.Size([32, 1, 28, 28]), torch.Size([32])
    break
```

The `num_workers` argument controls subprocesses used for loading and preprocessing data. In notebooks, small local scripts, and teaching snippets, `num_workers=0` is the least surprising setting because all loading happens in the main process. In production training scripts, increasing it can hide input-pipeline latency behind GPU work, but only after you measure the bottleneck. The Block A equivalent was not glamorous: a shuffled index array and slices like `X[batch_idx]`. The PyTorch version is a reusable contract that scales to files, images, streaming datasets, and distributed training later.

Shuffling belongs in the training loader, not the validation loader. Training shuffling changes the order in which SGD sees examples, reducing order artifacts and giving each epoch a different sequence of mini-batches. Validation shuffling usually adds noise to debugging because metrics should be reproducible and independent of data order. This is the same reasoning as A7's train/validation split, now encoded as `shuffle=True` for training and `shuffle=False` for validation.

Batch collation is the quiet third job. When a dataset returns one image tensor and one label at a time, the `DataLoader` stacks those individual images into an `[batch, channels, height, width]` tensor and the labels into `[batch]`. That default collation works when examples have the same shape. Variable-length text or ragged sequences need a custom collate function, but that belongs in later sequence modules. For Fashion-MNIST images, the default collation is exactly what you want.

The `DataLoader` does not magically put batches on the GPU. It yields CPU tensors unless the dataset already returns tensors on another device, which is uncommon for ordinary datasets. Move each batch inside the training loop. That keeps data loading separate from device execution and avoids quietly storing an entire dataset in GPU memory.

```python
# Continues the running example: best_device(), FashionMLP, and loader are defined in earlier parts.
device = best_device()
model = FashionMLP().to(device)

for xb, yb in loader:
    xb = xb.to(device)
    yb = yb.to(device)
    logits = model(xb)
    print(logits.device, yb.device)
    break
```

This is the same separation you used in A7 between data preparation and training math. Dataset code answers "what are the examples?" Training code answers "where should this mini-batch execute?" Mixing those responsibilities is a reliable way to create memory leaks or device mismatch errors.

The data bridge can be summarized in one sentence: A7 manually selected rows from arrays, while PyTorch asks a dataset for examples and asks a loader to assemble rows into batches. Once the batch exists, the model and optimizer do not care how it was assembled. That is the abstraction worth learning, because it lets you swap synthetic tensors, Fashion-MNIST files, or a cached feature store without rewriting the training step.

## Part 6: Rebuilding the A7 Fashion-MNIST MLP in PyTorch

Now put the bridge together. A7 trained a `784 -> 256 -> 10` MLP on Fashion-MNIST using a hand-written `Layer`, stable softmax-CE, mini-batch SGD, and manual metric reporting. The PyTorch translation below uses the same shape contract and the same math, but removes most of the infrastructure you wrote for learning purposes. The example uses Fashion-MNIST-shaped tensors so the snippet runs without a network download; if you have the actual A7 arrays loaded, replace the synthetic `images` and `labels` tensors with `torch.from_numpy(X_train).reshape(-1, 1, 28, 28).float()` and `torch.from_numpy(y_train).long()`.

The important thing to preserve from A7 is not the data-loading library; it is the contract. Each input image becomes 784 float features after flattening. Each target is one of ten clothing classes. The model produces ten logits per image. The loss compares those logits against integer labels. The optimizer updates the two dense layers. Whether the tensors came from A7's NumPy arrays, `torchvision.datasets.FashionMNIST`, or the synthetic shape check below, the training step is the same. Real data makes the metric meaningful; the shape check makes the code path auditable before download or preprocessing enters the story.

For a real Fashion-MNIST run, the first sanity check from A7 still applies. With roughly balanced ten-class labels and logits near zero at initialization, cross-entropy starts near `ln(10)`, about `2.302`. You do not need the value to be exact, but a first loss around `50`, `nan`, or `0.01` should trigger a contract check before a long run. Inspect label dtype, output dimension, normalization, and whether you accidentally passed probabilities instead of logits. Framework code is shorter, but the debugging questions remain Block A questions.

```python
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset, random_split


def best_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


class FashionMLP(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Flatten(),
            nn.Linear(28 * 28, 256),
            nn.ReLU(),
            nn.Linear(256, 10),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


torch.manual_seed(42)

# Replace these two tensors with real Fashion-MNIST tensors from A7 or torchvision.
images = torch.rand(1024, 1, 28, 28)                         # shape: [N, 1, 28, 28]
labels = torch.randint(0, 10, size=(1024,), dtype=torch.long)  # shape: [N]

dataset = TensorDataset(images, labels)
train_set, val_set = random_split(
    dataset,
    lengths=[900, 124],
    generator=torch.Generator().manual_seed(42),
)

train_loader = DataLoader(train_set, batch_size=64, shuffle=True, num_workers=0)
val_loader = DataLoader(val_set, batch_size=128, shuffle=False, num_workers=0)

device = best_device()
model = FashionMLP().to(device)
loss_fn = nn.CrossEntropyLoss()
optimizer = torch.optim.SGD(model.parameters(), lr=0.1)

for epoch in range(3):
    model.train()
    train_loss = 0.0
    train_correct = 0
    train_seen = 0

    for xb, yb in train_loader:
        xb = xb.to(device)
        yb = yb.to(device)

        optimizer.zero_grad(set_to_none=True)
        logits = model(xb)
        loss = loss_fn(logits, yb)
        loss.backward()
        optimizer.step()

        batch_size = xb.shape[0]
        train_loss += loss.item() * batch_size
        train_correct += (logits.argmax(dim=1) == yb).sum().item()
        train_seen += batch_size

    model.eval()
    val_loss = 0.0
    val_correct = 0
    val_seen = 0

    with torch.no_grad():
        for xb, yb in val_loader:
            xb = xb.to(device)
            yb = yb.to(device)
            logits = model(xb)
            loss = loss_fn(logits, yb)

            batch_size = xb.shape[0]
            val_loss += loss.item() * batch_size
            val_correct += (logits.argmax(dim=1) == yb).sum().item()
            val_seen += batch_size

    print(
        f"epoch={epoch + 1} "
        f"train_loss={train_loss / train_seen:.4f} "
        f"train_acc={train_correct / train_seen:.3f} "
        f"val_loss={val_loss / val_seen:.4f} "
        f"val_acc={val_correct / val_seen:.3f}"
    )
```

The synthetic data will not produce meaningful accuracy, and that is fine for a structural check. The purpose of this snippet is to verify that the model, loss, optimizer, DataLoader, device movement, and train/eval modes fit together with correct shapes. When you swap in real Fashion-MNIST tensors, the same code becomes the A7 experiment expressed in PyTorch. Compared with the A7 from-scratch version, this is roughly 10x less code for the same training skeleton because PyTorch replaces the hand-written `Layer`, backward methods, stable softmax-CE routine, parameter generator, and update loop with standard primitives.

That 10x reduction should not be read as "ten times less understanding." It is ten times less scaffolding. In A7, the scaffolding was the point because you needed to see every moving part. In B1, the point is to keep the same moving parts while using the framework's reliable versions. The first time a model fails to learn, you should be able to expand the PyTorch line mentally: `loss.backward()` means graph walk, local VJPs, and gradient accumulation; `optimizer.step()` means parameter mutation; `DataLoader` means shuffled mini-batches; `CrossEntropyLoss` means stable log-softmax plus class-index negative log-likelihood.

The math is identical. `nn.Linear(784, 256)` computes the dense affine transform from A3 and A7. `nn.ReLU()` applies the activation from A4. `nn.CrossEntropyLoss()` consumes logits and class labels while implementing the stable softmax-CE from A5. `loss.backward()` executes the reverse-mode VJPs from A6 and A8. `torch.optim.SGD` subtracts a scaled gradient from each parameter, just like your manual A7 update. The shorter code is valuable only because you can still explain each line in Block A terms.

There is one deliberate boundary in the snippet: it does not introduce Adam, learning-rate schedules, regularization, initialization experiments, normalization layers, or mixed precision. Those topics are not optional in serious training, but they are not B1. This module's payoff is the bridge itself. Once the bridge is solid, later Block B modules can add one engineering concern at a time without forcing you to relearn the basic PyTorch object model.

## Part 7: Mode and Device Discipline

Two PyTorch habits deserve early attention because they produce confusing bugs in real training runs. First, modules have mode. `model.train()` tells modules they are in training mode; `model.eval()` tells them they are in evaluation mode. For the simple B1 MLP above, the outputs are the same either way because `Linear`, `ReLU`, and `Flatten` do not behave differently across modes. Later, dropout, batch normalization, and some other modules absolutely do behave differently. Calling the mode methods now builds the habit before the habit is expensive.

Mode is state on the module, not state on the optimizer or the data. A common mistake is to put `model.eval()` around validation and then forget to call `model.train()` when training resumes for the next epoch. Another mistake is to assume `model.eval()` makes gradients impossible. It does not. It changes module behavior; `torch.no_grad()` changes graph recording. Keeping those two ideas separate prevents subtle bugs when B5 and B6 introduce dropout and normalization.

```python
# Continues the running example: FashionMLP and device are defined in earlier parts.
model = FashionMLP().to(device)

model.train()
# Training loop: gradients enabled, optimizer.step() allowed after backward.

model.eval()
with torch.no_grad():
    # Evaluation loop: no graph tracking, no optimizer step, lower memory use.
    logits = model(torch.rand(8, 1, 28, 28, device=device))
```

Second, device placement must be consistent. The model's parameters live wherever you moved the model. Inputs and labels must move there too. Loss functions usually have no parameters, but any class weights or tensors used inside a custom loss must also be on the same device. The error message often mentions "Expected all tensors to be on the same device," and the fix is not to sprinkle `.to(device)` randomly; the fix is a clear policy.

```python
device = best_device()
model = FashionMLP().to(device)
loss_fn = nn.CrossEntropyLoss()

xb = torch.rand(16, 1, 28, 28).to(device)
yb = torch.randint(0, 10, size=(16,), dtype=torch.long).to(device)

logits = model(xb)
loss = loss_fn(logits, yb)
print(loss.device)
```

Hypothetical scenario: a team trains on a GPU instance and evaluates in a scheduled CPU job. The training script calls `model.to("cuda")` near the top, then later loads a validation batch from disk without moving it. The first evaluation step crashes with a device mismatch, and a hurried patch moves only the images, not the labels used by the weighted loss. The real fix is a single `device` variable, one model move after construction, and a batch-transfer helper used consistently in train and eval loops. The lesson is small, but the bug class is common enough that every PyTorch engineer should recognize it instantly.

Mode and device bugs often masquerade as "bad model" bugs because the code still looks like training code. A dropout model evaluated in training mode may produce noisy metrics. A batch-norm model trained with validation statistics leaking into the running estimates may look better during development than it will in deployment. A CPU tensor accidentally created inside a custom loss may work on a laptop and fail only on the GPU job. B1 cannot cover every future failure, but it can give you the habit of inspecting mode, graph tracking, and device before changing the architecture.

B2 will go deeper on training-loop structure: checkpointing, validation cadence, early stopping, metric history, and failure recovery. B1 stops at the bridge. You now know what PyTorch objects replace the pieces you wrote by hand, and you have a minimal loop whose ordering is correct.

## Did You Know?

- **PyTorch 2.12 was released on May 13, 2026.** The release blog is useful context when a module mentions current stable behavior, but most code in this bridge uses long-standing APIs that are stable across recent PyTorch versions.
- **`torch.from_numpy` usually shares CPU memory with the source array.** That makes A7-to-B1 migration convenient, but it also means mutation can cross the boundary unless you explicitly clone the tensor.
- **Karpathy's micrograd is intentionally tiny because reverse-mode autodiff is a local-contract idea.** Your A8 `Value` engine and PyTorch autograd differ in scale, not in the need to cache parents, run local VJPs, and accumulate gradients.
- **PyTorch records dynamic graphs as Python executes.** That is why ordinary control flow can participate in the forward pass, and why each training iteration builds a fresh graph for the specific batch and branch choices that actually occurred.

## Common Mistakes

| Mistake | Why it breaks | Better approach |
|---|---|---|
| Passing one-hot labels into `nn.CrossEntropyLoss` for ordinary class-index training | PyTorch's standard cross-entropy API expects logits shaped `[batch, classes]` and integer labels shaped `[batch]`, so one-hot targets change the contract. | Keep targets as `torch.long` class indices, and remember that the loss combines stable log-softmax with negative log-likelihood. |
| Forgetting `optimizer.zero_grad(set_to_none=True)` before each step | Gradients accumulate across backward calls, so stale gradients from prior mini-batches corrupt the current update. | Clear gradients once per optimizer step unless you are deliberately accumulating micro-batches with a documented scaling policy. |
| Calling `.numpy()` on a CUDA tensor or a tensor that still requires gradients | NumPy only views CPU memory, and tensors connected to autograd need an explicit graph boundary before conversion. | Use `tensor.detach().cpu().numpy()` for logging or analysis, and avoid feeding that detached result back into the differentiable path. |
| Moving the model to GPU but leaving batches on CPU | PyTorch operations require participating tensors to live on compatible devices, and mixed CPU/CUDA operations fail before training can proceed. | Create one `device`, call `model.to(device)` once, and move `xb` plus `yb` inside every train and eval loop. |
| Expecting `.eval()` to disable gradients by itself | Evaluation mode changes module behavior, but it does not turn off autograd recording for ordinary tensor operations. | Use both `model.eval()` and `with torch.no_grad():` during evaluation loops so behavior and graph tracking are both correct. |
| Mutating tensors in-place without understanding autograd's saved values | Backward kernels may need forward intermediates, and in-place changes can invalidate those saved tensors or silently change intended math. | Prefer out-of-place operations while learning, and reserve in-place mutations for code paths where you understand the autograd contract. |

## Quiz

1. **How does `torch.Tensor` extend the NumPy arrays you used in A1 through A3?**

   <details>
   <summary>Answer</summary>

   A PyTorch tensor keeps the familiar rectangular shape, dtype, broadcasting, indexing, and vectorized operation model from NumPy, but adds device placement and optional autograd metadata. Device placement lets the same operation run on CPU, CUDA, or MPS backends when supported. Autograd metadata lets PyTorch record operations during the forward pass so `loss.backward()` can compute gradients later. The core shape reasoning remains the same.

   </details>

2. **Why does `loss.backward()` feel similar to the A8 `Value.backward()` method even though PyTorch operates on tensors?**

   <details>
   <summary>Answer</summary>

   Both systems build a graph during the forward pass, seed the scalar loss with gradient one, and walk the graph in reverse topological order. Each node applies a local VJP and accumulates contributions into parent gradients. PyTorch's nodes are tensor operations implemented by optimized kernels, while A8's nodes were scalar Python objects, but the reverse-mode contract is the same.

   </details>

3. **What is the correct order of a normal PyTorch SGD training step, and which A7 operation does `optimizer.step()` replace?**

   <details>
   <summary>Answer</summary>

   The normal order is `optimizer.zero_grad(set_to_none=True)`, forward pass, scalar loss computation, `loss.backward()`, and `optimizer.step()`. The step call replaces the manual A7 loop that subtracted `lr * grad` from every trainable parameter. Clearing gradients first is essential because PyTorch accumulates into `.grad` rather than overwriting it.

   </details>

4. **A model returns logits with shape `[64, 10]`. What shape and dtype should labels have for `nn.CrossEntropyLoss`, and why should you not apply softmax first?**

   <details>
   <summary>Answer</summary>

   Labels should have shape `[64]` and dtype `torch.long`, with each value holding the integer class index. You should pass raw logits because `nn.CrossEntropyLoss` internally applies a stable log-softmax plus negative log-likelihood. Applying softmax first can reduce numerical stability and changes the API contract away from the intended logits-based loss.

   </details>

5. **What does a `DataLoader` add beyond the manual A7 mini-batch slicing loop, and what does it not do automatically?**

   <details>
   <summary>Answer</summary>

   A `DataLoader` asks the dataset for examples, batches them, optionally shuffles training order, and can use worker processes for loading. It replaces the manual shuffled-index slicing loop from A7 while preserving the same mini-batch idea. It does not automatically move tensors to the model's device, choose the right split policy, normalize inputs, or make validation metrics meaningful. Those remain explicit training-engineering decisions.

   </details>

6. **Why do we call both `model.eval()` and `with torch.no_grad():` during evaluation?**

   <details>
   <summary>Answer</summary>

   `model.eval()` changes the behavior of mode-sensitive modules such as dropout and batch normalization, while `torch.no_grad()` disables graph recording for operations inside the block. They solve different problems. Evaluation should use inference behavior and avoid building unnecessary graphs, so robust eval loops use both together.

   </details>

7. **You receive an error saying tensors are on CPU and CUDA at the same time. What should you inspect first?**

   <details>
   <summary>Answer</summary>

   Inspect the device of the model parameters, the input batch, the labels, and any tensors used inside the loss. A disciplined loop moves the model once with `model.to(device)` and moves every `xb` and `yb` to the same device inside the loop. Randomly adding `.to(device)` in one place often hides the next mismatch rather than fixing the policy.

   </details>

## Hands-On Exercise

**Task:** Translate one small Block A-style training run into PyTorch and prove that autograd, the optimizer, the DataLoader, and mode/device discipline are all wired correctly before you touch a larger dataset.

1. Create a tensor dataset with 512 synthetic Fashion-MNIST-shaped images using `torch.rand(512, 1, 28, 28)` and 512 integer labels using `torch.randint(0, 10, (512,), dtype=torch.long)`.
2. Build the `FashionMLP` class from Part 6 and print every parameter name plus shape using `model.named_parameters()`, confirming that the dense layers correspond to `784 -> 256 -> 10`.
3. Train for five epochs with `nn.CrossEntropyLoss`, `torch.optim.SGD(model.parameters(), lr=0.1)`, `optimizer.zero_grad(set_to_none=True)`, `loss.backward()`, and `optimizer.step()`.
4. Add an evaluation loop that calls `model.eval()` and wraps the forward pass in `with torch.no_grad():`, then reports validation loss and accuracy.
5. Run the same script on `cpu` and, if available, on `cuda` or `mps`; document the one helper function that keeps model, inputs, and labels on the same device.

**Success criteria:**

- [ ] The first printed batch has image shape `[batch, 1, 28, 28]`, label shape `[batch]`, and logits shape `[batch, 10]`.
- [ ] Every optimizer step follows the exact order `zero_grad` -> forward -> loss -> backward -> step.
- [ ] The evaluation loop uses both `model.eval()` and `torch.no_grad()`, with no optimizer step inside evaluation.
- [ ] No device mismatch occurs when switching from CPU to another available backend.
- [ ] You can point to the A7 line or concept replaced by `nn.Linear`, `nn.CrossEntropyLoss`, `loss.backward()`, and `torch.optim.SGD`.

**Verification:**

```python
assert next(model.parameters()).device.type == device.type  # compare type: device "mps"/"cuda" vs param "mps:0"/"cuda:0"
assert logits.shape[1] == 10
assert labels.dtype == torch.long
assert all(parameter.grad is not None for parameter in model.parameters())
```

Run those assertions immediately after a training backward pass and before `optimizer.zero_grad(set_to_none=True)` clears gradients for the next step. The final assertion should fail during evaluation under `torch.no_grad()`, which is exactly the point: evaluation should not populate gradients.

## Key Takeaways

PyTorch is the Block A system made practical. A tensor is a NumPy-style array with dtype, device, and optional graph metadata. Autograd is your A8 reverse-mode engine operating on tensor operations and optimized VJPs. `nn.Module` and `nn.Linear` are the standardized form of your A7 model and `Layer` classes. `torch.optim.SGD` is the manual parameter update wrapped in a reliable optimizer object. `Dataset` and `DataLoader` replace hand-sliced mini-batches while preserving the same batch semantics.

The most important engineering habit is ordering. Move model and batches to the same device. Enter training mode for training and evaluation mode for evaluation. Clear stale gradients, run forward, compute loss from logits and integer labels, call backward once on the scalar loss, then step the optimizer. Use `with torch.no_grad():` when evaluating. If you can explain each line in terms of A6, A7, and A8, PyTorch has stopped being magic and started being leverage.

## Learner check

> | 1.2 | [The PyTorch Bridge: From Your NumPy Engine to torch](/ai-ml-engineering/deep-learning/module-1.2-pytorch-fundamentals/) |

## Sources

- PyTorch 2.12 release blog. https://pytorch.org/blog/pytorch-2-12-release-blog/
- PyTorch tensor documentation. https://docs.pytorch.org/docs/2.12/tensors.html
- PyTorch autograd documentation. https://docs.pytorch.org/docs/2.12/autograd.html
- PyTorch autograd mechanics note. https://docs.pytorch.org/docs/2.12/notes/autograd.html
- PyTorch `torch.nn.Module` documentation. https://docs.pytorch.org/docs/2.12/generated/torch.nn.Module.html
- PyTorch `torch.nn.Linear` documentation. https://docs.pytorch.org/docs/2.12/generated/torch.nn.Linear.html
- PyTorch `torch.nn.CrossEntropyLoss` documentation. https://docs.pytorch.org/docs/2.12/generated/torch.nn.CrossEntropyLoss.html
- PyTorch `torch.optim.SGD` documentation. https://docs.pytorch.org/docs/2.12/generated/torch.optim.SGD.html
- PyTorch data loading documentation. https://docs.pytorch.org/docs/2.12/data.html
- Paszke et al., "PyTorch: An Imperative Style, High-Performance Deep Learning Library." https://papers.neurips.cc/paper_files/paper/2019/hash/bdbca288fee7f92f2bfa9f7012727740-Abstract.html
- d2l.ai automatic differentiation chapter. https://d2l.ai/chapter_preliminaries/autograd.html
- Karpathy micrograd repository. https://github.com/karpathy/micrograd

## Next Module

Continue to [The Training Loop](/ai-ml-engineering/deep-learning/module-1.3-training-neural-networks/).
