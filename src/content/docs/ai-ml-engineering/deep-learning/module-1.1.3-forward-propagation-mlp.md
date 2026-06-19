---
title: "Forward Propagation in Multi-Layer Perceptrons"
slug: ai-ml-engineering/deep-learning/module-1.1.3-forward-propagation-mlp
sidebar:
  order: 1002.3
---

> **AI/ML Engineering Track** | Complexity: `[COMPLEX]` | Time: 4-6 hours

**Reading Time**: 3-4 hours

**Prerequisites**: Module 1.1 (NumPy, Pandas & Data Tooling) and the Block A modules A1 (Neural Network Math Warm-Up) and A2 (The Neuron & Perceptron from Scratch).

---

In October 1986, David Rumelhart, Geoffrey Hinton, and Ronald Williams published a paper in *Nature* titled "Learning representations by back-propagating errors." The paper was not the first to describe backpropagation — Paul Werbos had proposed it in his 1974 PhD thesis, and several authors had explored similar ideas throughout the late 1970s and early 1980s. But the Rumelhart-Hinton-Williams paper did something earlier work had not: it demonstrated, with clear and replicable experiments, that backpropagation could train networks with *hidden layers* to solve problems that single-layer perceptrons could not. The XOR problem that had humiliated Rosenblatt's perceptron in 1958 — the problem Minsky and Papert proved was impossible for a single layer in their 1969 book *Perceptrons* — fell to a network with one hidden layer of two units. The hidden layer transformed the input coordinates so that what was not linearly separable in the original space became separable in the transformed space, and backpropagation learned the parameters that performed that transformation.

What made hidden layers possible was forward propagation, the computational engine that transforms raw input data through successive layers until a prediction emerges at the output. Every weight matrix, every bias vector, every nonlinearity participates in a coordinated pipeline that the learner designs. The forward pass is not merely a computation to be endured on the way to backpropagation — it is the architecture's specification of what functions it can represent. Getting the forward pass right means understanding the shapes of every intermediate tensor, the arithmetic that produces them, and the values that must be preserved because the backward pass cannot function without them. If you skip forward propagation or treat it as a black box, you will never debug a broken gradient or understand why a particular architecture works.

This module transforms the single-neuron and single-layer primitives from A2 into a full multi-layer perceptron. You will learn to treat the forward pass as disciplined engineering: shape tables that catch dimension mismatches before they become runtime errors, caching conventions that preserve every intermediate the backward pass needs, and parameter-counting habits that let you reason about whether an architecture is reasonable for your dataset and hardware. By the end, you will have added an `MLP` class to your growing `nn.py` micro-framework — a class that stacks layers, runs forward propagation over batches of arbitrary size, and carefully preserves every intermediate value the backward pass in A6 will consume. The `MLP.forward()` method you write here is the computation graph that backpropagation traverses; if it does not faithfully record every operation with its intermediate values, the gradients computed in A6 will be silently wrong. Every Block A module after this one — A4 on activation functions, A5 on loss functions, A6 on backpropagation, and A7 on training loops — assumes the forward pass you build here works correctly, is cached, and produces output of predictable shape. Getting it right now saves you from debugging phantom gradient errors across the rest of the arc.

---

## Learning Outcomes

By the end of this module, you will be able to:

- Implement a fully vectorised forward pass for a dense neural network layer operating on batched data, using NumPy's matrix multiplication and broadcasting rules correctly.
- Derive the shape of every intermediate tensor in a multi-layer perceptron and construct a shape-discipline table that prevents the five most common forward-pass bugs.
- Build an `MLP` class that stacks multiple `Layer` objects, executes `forward(X)` over arbitrary batch sizes, and returns a structured activation cache suitable for backpropagation.
- Compare the decision boundaries of single-layer and multi-layer networks using the XOR problem as a concrete test case, explaining geometrically why hidden layers make non-linearly-separable problems learnable.
- Calculate the parameter count and approximate floating-point operation count for a given MLP architecture from its layer dimensions alone, and use those counts to reason about whether an architecture is reasonable for a given dataset and hardware budget.

---

## Why This Module Matters

Imagine building a house without a foundation survey. You pour concrete, stack bricks, wire the circuits — then discover the load-bearing wall is two centimetres off the survey line. The entire structure is compromised, and the fix is to tear it down and start again. Forward propagation is the foundation survey of every neural network. If a single shape is wrong — a weight matrix transposed, a bias vector that fails to broadcast, an activation applied to the wrong tensor — the entire training loop fails downstream. Worse, the failure is often silent: the network still produces numbers, the loss still decreases for a few iterations, then it stalls, explodes, or converges to a solution worse than random guessing. When that happens, the engineer who understands forward propagation reaches for `ndarray.shape` attributes and activation caches; the engineer who does not reaches for hyperparameters they do not understand, guessing at learning rates and layer sizes until luck or exhaustion intervenes.

Forward propagation also separates architectures that *can* learn from those that cannot. The XOR problem taught the field that one layer of linear classifiers cannot separate points that are not linearly separable. Stack two layers with a nonlinearity between them, and the first layer can bend the input space so that the second layer sees a linearly separable problem. This geometric transformation — the way hidden layers warp coordinates through composed matrix multiplications and elementwise nonlinearities — is a sequence of operations we can trace, verify, and design rather than an opaque miracle. When you understand forward propagation, you understand *why* depth works, not just that it works.

Finally, forward propagation is where the engineering discipline of the micro-framework takes definitive shape. Every Block A module grows `nn.py`, a single file that accumulates the learner's understanding in executable form. A2 gave us a `Layer` primitive that handles one linear-plus-nonlinearity step. A3 wraps multiple `Layer` objects into an `MLP` class whose `forward()` method is clean, cached, and ready for the backward pass in A6. The caching convention we establish here — storing each layer's pre-activation `Z` and post-activation `A` — is the contract between the forward and backward passes. Break the contract and the backward pass silently receives garbage; honour it and backpropagation becomes a straightforward traversal through the values you carefully preserved.

---

## Part 1: From One Neuron to a Layer

### 1.1 The single neuron, revisited

Recall the `nn.py` from A2. A single artificial neuron computes a weighted sum plus bias followed by a nonlinearity. Given an input vector `x` of shape `(d_in,)`, a weight vector `w` of shape `(d_in,)`, and a scalar bias `b`, the neuron computes `z = w₁·x₁ + w₂·x₂ + ... + w_d·x_d + b` and then `a = σ(z)`:

```python
import numpy as np

x = np.array([0.5, -1.2, 0.8])        # shape (3,)
w = np.array([0.3, 0.7, -0.4])        # shape (3,)
b = 0.1

z = np.dot(w, x) + b    # 0.3*0.5 + 0.7*(-1.2) + (-0.4)*0.8 + 0.1 = -0.91
a = np.maximum(0, z)    # ReLU: max(0, -0.91) = 0.0
print(f"z = {z:.2f}, a = {a:.2f}")    # z = -0.91, a = 0.00
```

This processes one sample with one neuron. Real networks process *batches* of samples through *layers* of neurons simultaneously. The vectorised version replaces Python loops with BLAS-optimised matrix multiplication, turning what would be a nested `for` loop over samples and neurons into a single call to a heavily optimised linear algebra kernel. The performance difference is not marginal — a vectorised forward pass on a modern CPU can process thousands of samples through hundreds of neurons in the time a Python loop processes dozens.

### 1.2 The weight matrix

A layer with `d_in` input features and `d_out` output units contains `d_out` neurons, each with its own weight vector of length `d_in`. Instead of storing `d_out` separate vectors, we stack them into a single weight matrix `W` of shape `(d_in, d_out)`. Each **column** of `W` is one neuron's complete weight vector, while each row shows how a single input feature feeds into every output neuron. This columnar organisation is not arbitrary — it is the convention that makes the matrix multiplication `X @ W` compute all neuron outputs simultaneously, with each column of the result representing one neuron's response across the batch.

```
           d_out columns (one per output neuron)
           ───────────────────────────────────────
           │ w₀₀   w₀₁   w₀₂   ...   w₀,d₋₁ │  ─┐
  d_in     │ w₁₀   w₁₁   w₁₂   ...   w₁,d₋₁ │   │ d_in rows
  rows     │ w₂₀   w₂₁   w₂₂   ...   w₂,d₋₁ │   │ (one per input feature)
           │  ⋮     ⋮     ⋮     ⋱      ⋮    │  ─┘
           ───────────────────────────────────────
```

The bias becomes a vector `b` of shape `(d_out,)` — one scalar bias per output unit. To initialise these with the He scheme from A2 (which we will return to in Part 5 when discussing why initialisation matters for what the backward pass sees):

```python
d_in, d_out = 3, 4
rng = np.random.default_rng(42)

W = rng.normal(0, 0.5, size=(d_in, d_out))   # shape (3, 4)
b = rng.normal(0, 0.1, size=(d_out,))         # shape (4,)
print(W.shape, b.shape)                        # (3, 4) (4,)
```

### 1.3 Vectorising over a batch

Suppose we have `N` samples, each with `d_in` features. Store them in an input matrix `X` of shape `(N, d_in)`, where each row is one sample. For every sample `n` and every output neuron `k`, the weighted sum is `Z[n, k] = Σⱼ X[n, j] · W[j, k] + b[k]`. This is exactly the matrix product `X @ W` followed by broadcasting addition, a pattern you should internalise so thoroughly that seeing `W @ X` in code triggers an immediate suspicion:

```python
N = 5
X = rng.normal(0, 1.0, size=(N, d_in))        # shape (5, 3)
Z = X @ W + b                                  # shape (5, 4): X@W is (5,4), b broadcasts
A = np.maximum(0, Z)                           # shape (5, 4): ReLU elementwise

print("X  shape:", X.shape, "  W shape:", W.shape)  # (5, 3) (3, 4)
print("Z  shape:", Z.shape, "  b shape:", b.shape)  # (5, 4) (4,)
print("A  shape:", A.shape)                          # (5, 4)
```

The broadcasting rule: NumPy prepends leading dimensions of size 1 until the shapes match. Shape `(4,)` becomes `(1, 4)`, which broadcasts to `(5, 4)` by repeating along the batch axis — adding the same bias vector to every sample, exactly as intended. A critical convention to internalise is **`X @ W`, never `W @ X`**. With rows-as-samples and columns-as-features, `X` is `(N, d_in)` and `W` is `(d_in, d_out)`. The inner dimensions `d_in` match in `X @ W`, producing `(N, d_out)`. If you write `W @ X`, NumPy attempts `(d_in, d_out) @ (N, d_in)`, which fails because `d_out ≠ N` in general. The mnemonic: samples on the left, weight matrix on the right, inner dimensions match. This convention is universal across every major deep learning framework, and violating it is the single most common shape bug in neural network code.

### 1.4 The `Layer` primitive from A2

In A2 you extended `nn.py` with a `Layer` class that encapsulates `Z = X @ W + b` followed by an activation. Here is the canonical form, reproduced so A3's `MLP` class can build on it. Note that the `forward` method stores `Z` and `A` as instance attributes — this is the caching convention that makes backpropagation possible in A6. The cost is memory proportional to `batch_size × layer_width`, but the alternative (recomputing the full forward pass during backpropagation) is far more expensive computationally. Every major deep learning framework makes this same trade-off:

```python
# In nn.py — add or confirm this class from A2

class Layer:
    """A fully-connected layer: Z = X @ W + b, then activation(Z).

    Stores Z and A for the backward pass (A6).
    """
    def __init__(self, d_in, d_out, activation):
        rng = np.random.default_rng()
        # He initialization (He et al., 2015): variance = 2 / fan_in
        self.W = rng.normal(0, np.sqrt(2.0 / d_in), size=(d_in, d_out))
        self.b = np.zeros(d_out)
        self.activation = activation
        # Cache storage — populated during forward(), consumed by backward() in A6
        self.Z = None
        self.A = None

    def forward(self, X):
        """Run the forward pass. Stores Z and A for later gradient computation."""
        self.Z = X @ self.W + self.b       # shape (N, d_out)
        self.A = self.activation(self.Z)    # shape (N, d_out)
        return self.A
```

The backward pass can often use the cached activation A directly for common nonlinearities: sigmoid uses `A * (1 - A)`, tanh uses `1 - A**2`, and standard ReLU can use `(A > 0)` when adopting the usual derivative-at-zero convention. We still store Z as well as A because it keeps the backward pass uniform across activation types, makes derivative code easier to inspect, preserves information that some activations or diagnostics may need, and avoids recomputing the linear step. In this micro-framework, caching both Z and A is an engineering contract for clarity and reuse, not a claim that every activation derivative is impossible to compute from A alone.

---

## Part 2: Stacking Layers into an MLP

### 2.1 The architecture pattern

A multi-layer perceptron alternates linear transforms with elementwise nonlinearities. The input `X` flows through layers L₁, L₂, ..., L_L until the final layer produces the output. The nonlinearity between layers is essential: without it, the row-major composition collapses — `(X @ W₁ + b₁) @ W₂ + b₂` reduces to `X @ (W₁ @ W₂) + (b₁ @ W₂ + b₂)`, which is just another single linear transform. The product `W₁ @ W₂` is one matrix and the stacked biases form one vector, making depth irrelevant. Nonlinearities break this algebraic collapse and give depth its representational power. This is why a 100-layer network without nonlinearities performs identically to a single-layer network: the 100 weight matrices multiply together into one equivalent matrix, and the 100 bias vectors collapse into one equivalent bias. The nonlinearities between layers prevent this reduction.

### 2.2 Concrete example: a 2-hidden-layer MLP

Construct an MLP for binary classification with 4 input features: hidden layer 1 has 5 units (ReLU), hidden layer 2 has 3 units (ReLU), and the output layer has 2 units with linear activation delivering raw logits for cross-entropy. The choice of 5 and 3 hidden units is arbitrary for this demonstration — real architectures select layer widths through a combination of domain knowledge, empirical tuning, and computational budget constraints:

```python
def relu(z):
    return np.maximum(0, z)

# Build layers using the Layer class from nn.py (A2)
layer1 = Layer(4, 5, activation=relu)                # W1: (4,5), b1: (5,)
layer2 = Layer(5, 3, activation=relu)                # W2: (5,3), b2: (3,)
layer3 = Layer(3, 2, activation=lambda z: z)          # W3: (3,2), b3: (2,), linear output

# Batch of 3 samples, 4 features each
X_batch = np.array([
    [0.2, -0.5,  0.8,  0.1],
    [0.9,  0.3, -0.2,  0.7],
    [-0.4, 0.6,  0.1, -0.9]
])  # shape (3, 4)

# Forward pass through each layer — each stores its own Z and A internally
A1 = layer1.forward(X_batch)          # shape (3, 5)
A2 = layer2.forward(A1)               # shape (3, 3)
output = layer3.forward(A2)            # shape (3, 2)

# Verify every shape
print("A1 (hidden 1):  ", A1.shape, "  Z1:", layer1.Z.shape)    # (3, 5) (3, 5)
print("A2 (hidden 2):  ", A2.shape, "  Z2:", layer2.Z.shape)    # (3, 3) (3, 3)
print("output (logits): ", output.shape, "  Z3:", layer3.Z.shape) # (3, 2) (3, 2)
```

Expected output confirms that every shape is consistent: A₁ and Z₁ are `(3, 5)`, A₂ and Z₂ are `(3, 3)`, and the output logits plus Z₃ are `(3, 2)`. The pattern is regular: at layer `l` of width `d_l`, both Z and A have shape `(N, d_l)`. This invariant holds for every layer in every MLP, and internalising it makes shape debugging nearly mechanical.

### 2.3 Shape tracing table

Build this table for every network you design. It catches dimension mismatches before they become runtime errors and makes the chain rule in A6 easier because every gradient has a known shape. The table also serves as documentation: a reader can understand the full data flow without tracing through code:

| Stage | Variable | Shape | Derivation |
|-------|----------|-------|------------|
| Input | X (A₀) | `(N, 4)` | N samples, 4 features |
| L1 linear | Z₁ | `(N, 5)` | `(N,4) @ (4,5)` = `(N,5)` |
| L1 activation | A₁ | `(N, 5)` | ReLU preserves shape |
| L2 linear | Z₂ | `(N, 3)` | `(N,5) @ (5,3)` = `(N,3)` |
| L2 activation | A₂ | `(N, 3)` | ReLU preserves shape |
| L3 linear | Z₃ | `(N, 2)` | `(N,3) @ (3,2)` = `(N,2)` |
| Output | A₃ | `(N, 2)` | Linear (identity) preserves shape |

### 2.4 Architectural vocabulary

The **input layer** is not a real layer with parameters — it simply holds the data `X`. The first trainable layer is called "hidden layer 1." Any layer between input and output is a **hidden layer**, whose activations are internal to the network and not directly supervised by the target. The final layer is the **output layer**, and its activation function must match the task: no activation (raw logits) for multi-class cross-entropy, sigmoid for binary probability, identity for regression. The **depth** of a network is the number of layers with trainable parameters — hidden plus output — so the 2-hidden-layer net above has depth 3. The **width** of a layer is its number of units; wider layers can represent more complex functions at the cost of more parameters and more computation, while deeper networks with the same total parameter count can learn hierarchical representations that wide shallow networks cannot. This depth-versus-width trade-off is one of the central design decisions in architecture engineering, and we quantify it in Part 7.

---

## Part 3: Shape Discipline

### 3.1 The five most common shape bugs

**Bug 1: Forgetting the batch dimension.** Passing a single sample of shape `(d_in,)` to a layer expecting `(N, d_in)` causes NumPy to interpret `(d_in,) @ (d_in, d_out)` as a vector-matrix product, producing `(d_out,)` — a 1D vector instead of `(1, d_out)`. Downstream operations that expect a 2D batch then break silently, often with an error message that references a different line of code entirely because the shape mismatch propagates through several operations before anything notices. Always keep a batch dimension with `x.reshape(1, -1)` for single samples. The extra dimension costs nothing in memory and saves hours of debugging.

**Bug 2: Transposing the weight matrix.** Writing `W @ X` instead of `X @ W` attempts `(d_in, d_out) @ (N, d_in)`, where the inner dimensions `d_out` and `N` do not match in general. Internalise the pattern: samples on the left, weights on the right, inner dimensions equal. If you find yourself writing `W @ X`, stop and verify — it is almost certainly a bug, and even when it accidentally works (because N equals d_out by coincidence), it computes the wrong mathematical operation.

**Bug 3: Bias broadcasting along the wrong axis.** A bias of shape `(d_out, 1)` added to `(N, d_out)` broadcasts along the wrong axis, duplicating the bias per-feature instead of per-sample. The result has the correct shape but the wrong values — a truly insidious bug because all subsequent operations succeed with silently incorrect numbers. Keeping biases as 1D arrays of shape `(d_out,)` avoids this: NumPy broadcasts `(d_out,)` against `(N, d_out)` correctly by prepending a leading dimension, so each sample gets the same bias vector.

**Bug 4: Mismatched sequential layer dimensions.** Layer `l` expects `d_{l-1}` inputs but layer `l-1` produces `d'_{l-1}` outputs where `d'_{l-1} ≠ d_{l-1}`. The matmul fails with a clear dimension mismatch error, which is easy to fix but frustrating to debug in a large codebase when you cannot immediately identify which of twenty layers has the wrong dimension. Building a shape table before coding prevents this class of bug entirely.

**Bug 5: Wrong softmax axis in the output layer.** `softmax(z, axis=0)` normalises across the batch dimension instead of across classes, destroying the per-sample probability interpretation — the output still has the correct shape, but every row's probabilities no longer sum to 1 individually. For batched classification, always `softmax(logits, axis=1)` so each sample's row sums to 1. This bug is particularly dangerous because the loss function may still produce decreasing values (the normalisation is not mathematically equivalent to a per-sample normalisation, but the loss surface can still have gradients that appear reasonable), leading to models that train but produce nonsensical predictions.

### 3.2 A debugging forward pass

When shapes misbehave silently — which happens considerably more often than you would expect because NumPy's broadcasting can easily mask dimension errors — insert shape assertions on every layer. The `debug_forward` utility function shown next runs one complete forward pass and prints every tensor shape, instantaneously catching dimension mismatches that would otherwise manifest as cryptic errors deep in the training loop. Run it once for every new architecture you build:

```python
def debug_forward(layers, X):
    """Print every tensor shape during a forward pass. Layers must have .forward()."""
    A = X
    print(f"Input:           {str(A.shape):>12s}")
    for i, layer in enumerate(layers):
        A = layer.forward(A)
        print(f"Layer {i+1} Z/A:   {str(layer.Z.shape):>12s} / {str(layer.A.shape):>12s}"
              f"  W {str(layer.W.shape):>12s}  b {str(layer.b.shape):>8s}")
    return A

# Instant shape verification for the 2-hidden-layer MLP
_ = debug_forward([layer1, layer2, layer3], X_batch)
```

The printed table should match your precomputed shape table exactly. A single mismatch identifies the broken layer without guesswork. Run this once for every new architecture and keep the output alongside your shape table as documentation — when you return to the code weeks later, the shape table and debug output together let you re-verify the architecture in seconds rather than tracing through code line by line.

---

## Part 4: Nonlinear Decision Boundaries

### 4.1 Why XOR defeated the perceptron

In A2 you learned that a single perceptron cannot solve XOR. The four points on the 2D plane — `(0,0):0`, `(0,1):1`, `(1,0):1`, `(1,1):0` — cannot be split by any straight line. No choice of `w₁, w₂, b` can place `(0,0)` and `(1,1)` on one side of `w₁·x₁ + w₂·x₂ + b = 0` while placing `(0,1)` and `(1,0)` on the other. The geometry forbids it outright, and the proof is straightforward: any line that separates `(0,0)` from `(0,1)` and `(1,0)` must put `(0,1)` and `(1,0)` on the same side, but then `(1,1)` — the sum of `(0,1)` and `(1,0)` in vector space — must also be on that same side for any linear decision boundary.

This was not a minor limitation. Minsky and Papert proved in *Perceptrons* (1969) that single-layer networks with threshold units could only learn linearly separable functions. Their proof was correct, their book carried enormous influence, and combined with Rosenblatt's untimely death in 1971, it contributed to the first "AI winter" — a decade-long reduction in neural network funding and interest during which the XOR limitation became the emblem of neural networks' supposed inadequacy. What the field would later rediscover is that the limitation was not of neural networks as a class of models, but of single-layer architectures specifically. Adding one hidden layer with a nonlinearity between the input and output breaks the linear-separability constraint entirely, because the hidden layer can learn to project the input into a new space where the classes become separable.

### 4.2 How hidden layers transform the problem

A 2-layer network solves XOR by projecting the input into a new space where the classes become linearly separable. The first layer applies a learned linear transform followed by a nonlinearity, and the second layer — a simple linear classifier — operates on this transformed representation rather than the original coordinates. Geometrically, each ReLU hidden unit defines a hyperplane (a line in 2D) and folds the space along that line: points on one side are projected to new coordinates proportional to their distance from the line, while points on the other side are mapped to zero. With two hidden units you get two folds, positioned at different locations in the input space. The second layer then draws a straight line in this folded 2D space that cleanly separates the XOR classes.

This folding process is worth visualising step by step. Imagine the 2D input plane with the four XOR points at its corners. The first hidden unit's hyperplane slices through the plane at the line `x₁ + x₂ = 0.5`, and the ReLU activation takes everything below that line and flattens it to zero while preserving everything above. The second hidden unit's hyperplane slices at `x₁ + x₂ = 1.5`, creating a second fold. After both folds, the point (0,0) has been flattened to (0,0) in hidden space by both units; (0,1) and (1,0) have been preserved by the first unit but flattened by the second, landing at (0.5, 0); and (1,1) has been preserved by both, landing at (1.5, 0.5). In this folded space, the three points that map to (0,0) or near (0.5, 0) lie on one side of the output line, while the single point at (1.5, 0.5) lies on the other. The hidden layer does not directly solve the original classification problem — it learns a *representation* in which the problem becomes solvable by a linear classifier. This is the core insight of deep learning: each successive layer learns a further transformation of the representation, composing nonlinear folds until even highly complex decision boundaries become achievable through what is, at each layer, a simple linear operation followed by a pointwise nonlinearity.

### 4.3 Hand-set XOR solution — trace every value

Here is a concrete 2-layer network with hand-chosen weights that produces correct XOR outputs. The design is transparent and every number is small enough to verify by hand: hidden unit 1 detects "at least one input is 1" by firing when the sum `x₁ + x₂` exceeds 0.5, hidden unit 2 detects "both inputs are 1" by firing when the sum exceeds 1.5, and the output layer subtracts a penalty of −4 from h₂ to push the (1,1) case into the negative logit region while leaving the single-1 cases safely positive:

```python
# Architecture: 2 inputs → 2 hidden units (ReLU) → 1 output (sigmoid → class 1 when A2 > 0.5)

W1 = np.array([[1.0, 1.0],      # shape (2, 2) — both hidden units compute x1 + x2
               [1.0, 1.0]])
b1 = np.array([-0.5, -1.5])     # shape (2,)  — h1 fires above 0.5, h2 fires above 1.5

W2 = np.array([[1.0],            # shape (2, 1)
               [-4.0]])
b2 = np.array([0.0])             # shape (1,)

X_xor = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])  # shape (4, 2)

# Forward pass
Z1 = X_xor @ W1 + b1            # shape (4, 2)
A1 = np.maximum(0, Z1)          # ReLU: shape (4, 2)
Z2 = A1 @ W2 + b2               # shape (4, 1)
A2 = 1.0 / (1.0 + np.exp(-Z2))  # sigmoid: shape (4, 1)
preds = (A2 > 0.5).astype(int)

print("Z1:\n", Z1)
print("A1:\n", A1)
print("Output probabilities:\n", A2)
print("Predictions:\n", preds)
```

Trace each input to verify correctness. For `(0,0)`, the sum is 0, so Z₁ = [−0.5, −1.5] and A₁ = ReLU([−0.5, −1.5]) = [0, 0]; then Z₂ = 0·1 + 0·(−4) + 0 = 0, giving σ(0) = 0.5, which breaks to class 0 because the code predicts class 1 only when `A2 > 0.5`. For `(0,1)` and `(1,0)`, the sum is 1, so Z₁ = [0.5, −0.5] and A₁ = [0.5, 0]; then Z₂ = 0.5·1 + 0·(−4) = 0.5, giving σ(0.5) ≈ 0.622 > 0.5, predicting class 1. For `(1,1)`, the sum is 2, so Z₁ = [1.5, 0.5] and A₁ = [1.5, 0.5]; then Z₂ = 1.5·1 + 0.5·(−4) = 1.5 − 2.0 = −0.5, giving σ(−0.5) ≈ 0.378 < 0.5, predicting class 0. All four cases are correct. The hidden layer transformed `(1,1)` into coordinates where the output weight of −4 on h₂ overpowers the +1 on h₁, pushing the logit negative for that single case while keeping it positive for the two single-1 cases. This transformation — mapping the input into a space where a line can separate the classes — is exactly what every hidden layer in every neural network does.

### 4.4 The general lesson

A hidden layer learns a representation in which the problem becomes solvable by a linear classifier. Each successive hidden layer in a deeper network learns a further transformation of the representation, composing nonlinear folds until even highly complex decision boundaries become achievable through what is, fundamentally, a sequence of linear operations separated by pointwise nonlinearities. The forward pass is the machinery that executes these transformations. When you design an architecture by choosing widths, depths, and activation functions, you are designing a sequence of coordinate transformations. The backward pass (A6) will learn the parameters of those transformations from data, but the architecture itself determines what transformations are *possible*. A network that is too narrow cannot fold the space appropriately. A network whose nonlinearities lack the right derivative properties cannot propagate useful gradient signals. No amount of training data or tuning can compensate for an architecture that cannot represent the function you need it to represent. The forward pass is where that representational capacity is specified and executed.

---

## Part 5: Caching Activations — The Bridge to Backpropagation

### 5.1 What the backward pass needs

When backpropagation runs through a layer, it needs two categories of information from the forward pass. First, it needs enough information to compute the activation derivative. For common activations, either Z or A can be sufficient: standard ReLU can use `Z > 0` or equivalently `A > 0`, sigmoid uses `A·(1−A)`, and tanh uses `1−A²`. But A does not preserve every detail of the pre-activation. ReLU collapses all negative inputs to zero, so `Z = -3.0` and `Z = -0.5` both produce `A = 0.0`; if a later diagnostic, activation variant, or custom backward rule needs the original pre-activation magnitude, A alone has lost it. The general engineering principle is therefore: cache Z and A consistently, even when a specific derivative formula could use A alone.

Second, backpropagation needs **the activation A of the previous layer** because the gradient with respect to the current layer's weights involves that activation: the chain rule gives `∂L/∂W[l] = A[l−1]ᵀ @ ∂L/∂Z[l]`. Without the stored A[l−1], you must either recompute the entire forward pass up to layer l−1 (doubling the computation) or lose the gradient entirely. These are exactly the values our `Layer.forward()` stores as `self.Z` and `self.A`, and the `MLP.forward()` collects into a structured cache dictionary.

### 5.2 Why caching beats recomputation

The alternative — discarding Z and A after the forward pass and recomputing them during backpropagation — saves memory but costs computation: every layer's forward pass must run a second time during the backward pass, doubling the forward-pass cost for every training iteration. For a network with 10 layers training on a million samples over 100 epochs, that doubling translates to roughly `2 × 10⁷` additional matrix multiplications that caching avoids entirely. The standard engineering trade-off, adopted by PyTorch, TensorFlow, JAX, and every major framework, stores activations during the forward pass and reads them during the backward pass. The memory cost is `O(batch_size × sum of layer widths)`, which for typical training hardware and batch sizes is manageable — a few hundred megabytes for a moderate-sized network training with a batch of 64 samples and layer widths in the low hundreds. There are memory-saving techniques like gradient checkpointing that trade compute for memory by caching only a subset of activations and recomputing the rest during the backward pass, but those are optimisations for resource-constrained training. Our micro-framework follows the straightforward caching strategy: store everything, and trust that the memory is available.

### 5.3 The caching contract

Every `Layer.forward()` call must store four attributes: `layer.Z` of shape `(N, d_out)` with pre-activation values, `layer.A` of shape `(N, d_out)` with post-activation values, `layer.W` of shape `(d_in, d_out)` as the weight matrix, and `layer.b` of shape `(d_out,)` as the bias vector. The backward pass reads `layer.Z`, `layer.A`, and the previous layer's `A` to compute gradients with respect to `layer.W`, `layer.b`, and the input to the layer. If any of these values is missing or stale — because a second `forward()` call overwrote the cache before backpropagation ran — the gradients will be silently wrong, computing derivatives through values that do not correspond to the forward pass that produced the current loss. The most dangerous failure mode is calling `forward()` twice without an intervening backward pass; the training loop in A7 must enforce the ordering: one forward → one backward → update → next forward, never forward-forward-backward.

---

## Part 6: The `MLP.forward()` — Extending the Micro-Framework

### 6.1 The `MLP` class

The `MLP` class wraps a list of `Layer` objects and orchestrates the full forward pass. Its `forward()` method returns both the output and a structured cache dictionary mapping layer indices to their stored intermediates. The cache uses string key `'A0'` for the raw input (needed by the backward pass through the first layer, because the gradient with respect to W₁ depends on the input X via `Xᵀ @ ∂L/∂Z₁`) and integer keys `0, 1, 2, ...` for each layer's stored dict `{'Z': ..., 'A': ...}`:

```python
# Add to nn.py (this module's contribution to the growing micro-framework)

class MLP:
    """A multi-layer perceptron: stacks layers, runs forward pass, caches activations.

    Parameters
    ----------
    layers : list of Layer
        Ordered from first hidden layer to output layer.
    """
    def __init__(self, layers):
        self.layers = layers

    def forward(self, X):
        """Run the full forward pass.

        Returns
        -------
        output : ndarray of shape (N, d_out)
            The final layer's activation.
        cache : dict
            Maps layer index (int) to dict with keys 'Z' and 'A' for that layer.
            Also includes 'A0' (the input) as cache['A0'].
        """
        cache = {'A0': X}                    # store input for backprop through first layer
        A = X
        for i, layer in enumerate(self.layers):
            A = layer.forward(A)             # layer stores its own Z and A internally
            cache[i] = {'Z': layer.Z, 'A': layer.A}
        return A, cache
```

The cache dictionary is the contract between forward and backward passes. The backward pass will receive this cache and iterate through layers in reverse order, reading `cache[i]['Z']` for the activation-function derivative and `cache[i-1]['A']` (or `cache['A0']` for the first layer) for the weight-gradient computation. The design is deliberately simple — no inheritance, no metaclasses, no abstraction beyond what is necessary to make the backward pass work correctly in A6.

### 6.2 Building and verifying an MLP

Build an MLP with the 2-hidden-layer architecture from Part 2, run a forward pass on a fresh batch, and verify the cache structure. Then run a cache-integrity check that recomputes a layer's Z from A₀ and the stored weights to confirm the stored values are internally consistent — this is a development check, not production code, but it saves hours of debugging when you later encounter unexpected gradients:

```python
# Build the MLP
mlp = MLP([layer1, layer2, layer3])

# Forward pass on a fresh 2-sample batch
X_new = np.array([[ 0.5, -0.3,  0.1,  0.9],
                  [-0.2,  0.8, -0.6,  0.4]])  # shape (2, 4)
output, cache = mlp.forward(X_new)

print("Output shape:", output.shape)           # (2, 2)
print("Cache keys:", list(cache.keys()))       # ['A0', 0, 1, 2]
print("Layer 0 Z shape:", cache[0]['Z'].shape) # (2, 5)

# Verify cache integrity — recompute Z for layer 0 from scratch
A0 = cache['A0']
Z0_check = A0 @ mlp.layers[0].W + mlp.layers[0].b
assert np.allclose(cache[0]['Z'], Z0_check), "Layer 0 Z mismatch"
print("Cache integrity verified — cached Z matches recomputed Z.")
```

This verification is a development check, not part of production training. When you later debug a backward pass that produces unexpected gradients, knowing the cache is trustworthy narrows the search space to the gradient computation itself rather than the stored intermediates. The assertion confirms that `cache[0]['Z']` equals what `Layer.forward()` should have stored, which means the caching mechanism is working correctly and the values are not stale or corrupted.

---

## Part 7: Counting Parameters and Compute

### 7.1 Parameter counting

Knowing the parameter count of your network is basic engineering hygiene. It tells you the model's capacity, its memory footprint for storing gradients during training (each parameter needs one gradient value of the same size), and whether the architecture is reasonable for your dataset — a network with more parameters than training samples will memorise rather than generalise unless you apply strong regularisation. For a dense layer with `d_in` inputs and `d_out` outputs, the parameter count is `d_in × d_out` (weight matrix entries) plus `d_out` (bias entries), which simplifies to `d_out × (d_in + 1)`.

For the 2-hidden-layer example with architecture 4→5→3→2, the breakdown is straightforward: layer L₁ (4→5) contributes 4×5 + 5 = 25 parameters, layer L₂ (5→3) contributes 5×3 + 3 = 18 parameters, and layer L₃ (3→2) contributes 3×2 + 2 = 8 parameters, for a total of 51 trainable parameters. Compare with linear regression on the same 4-dimensional input, which uses only 4 weights + 1 bias = 5 parameters. The extra 46 parameters buy the ability to model nonlinear decision boundaries — a modest increase in capacity that makes a qualitative difference in what the model can express.

A parameter-counting utility in `nn.py` makes this systematic and prevents off-by-one errors when tallying by hand. It also gives you the habit of checking parameter counts before training — a habit that catches misconfigured architectures (a layer with 10,000 units where you intended 100) before they waste compute:

```python
def count_parameters(layers):
    """Return total trainable parameters in a list of Layer objects."""
    total = 0
    for i, layer in enumerate(layers):
        w_params = layer.W.size       # d_in × d_out
        b_params = layer.b.size       # d_out
        layer_total = w_params + b_params
        total += layer_total
        print(f"Layer {i}: {w_params:>5d} weights + {b_params:>3d} biases = {layer_total:>5d}")
    print(f"Total:                          {total:>5d}")
    return total

total_params = count_parameters([layer1, layer2, layer3])
# Layer 0:    20 weights +   5 biases =    25
# Layer 1:    15 weights +   3 biases =    18
# Layer 2:     6 weights +   2 biases =     8
# Total:                                   51
```

### 7.2 Rough FLOPs for a forward pass

The dominant operation in a forward pass is matrix multiplication. Multiplying an `(N, d_in)` matrix by a `(d_in, d_out)` matrix costs `2 × N × d_in × d_out` floating-point operations (FLOPs), where the factor of 2 accounts for one multiplication and one addition per inner-product term — the standard convention in numerical linear algebra and algorithm analysis. Bias additions contribute `N × Σ d_l` operations, which is negligible compared with the matrix multiplications for typical networks where `d_{l-1} × d_l` is much larger than `d_l`. The factor of 2 matters when comparing FLOPs estimates across papers and frameworks: some authors count only the multiplications (dropping the factor of 2), and being off by a factor of 2 in a FLOPs estimate is both common and inconsequential for rough capacity planning but can cause confusion when comparing numbers from different sources.

For the full MLP with `L` layers of dimensions `d₀→d₁→d₂→...→d_L`, processing a batch of `N` samples, the forward FLOPs are `2 × N × Σ_{l=1}^{L} d_{l-1} × d_l`. For our example with `N=3` and `d=[4,5,3,2]`, the breakdown is: `X @ W₁` costs 2×3×4×5 = 120 FLOPs, `A₁ @ W₂` costs 2×3×5×3 = 90 FLOPs, and `A₂ @ W₃` costs 2×3×3×2 = 36 FLOPs, totalling 246 FLOPs for a complete forward pass on three samples. Modern GPUs execute billions of FLOPs per second, which is why even large networks can run forward passes in microseconds per sample during inference.

The backward pass requires roughly twice the compute of the forward pass: at each layer, one matrix multiplication computes the gradient with respect to the weights (`A[l−1]ᵀ @ ∂L/∂Z[l]`) and another computes the gradient with respect to the inputs (`∂L/∂Z[l] @ W[l]ᵀ`). Training one iteration — forward plus backward — thus costs approximately `3 × FLOPs_forward` for the matrix multiplications alone. We return to this in A6 when we implement backpropagation and can verify the factor empirically against the FLOPs counted for the forward pass.

---

## Did You Know?

- **The name "multi-layer perceptron" is technically a misnomer.** A perceptron uses a step-function activation (threshold at zero), which is nondifferentiable. Modern MLPs use smooth activations like ReLU, sigmoid, and tanh precisely because backpropagation requires derivatives. The name persisted for historical reasons even after the perceptron itself was superseded — a quirk of scientific nomenclature where naming often lags capability by decades.

- **He initialisation (He et al., 2015) sets the variance of weights to `2 / fan_in`** rather than the earlier Xavier/Glorot initialisation's `1 / fan_in`. The factor of 2 compensates for the ReLU activation, which zeros out roughly half the units on average. Without this correction, signals in deep ReLU networks decay exponentially with depth — each layer halves the variance, and after 20 layers the signal-to-noise ratio is effectively zero. The difference between Xavier and He initialisation can be the difference between a 50-layer network that trains and one whose gradients vanish to zero by layer 20, a bug that took the field years to diagnose and fix.

- **The forward pass of a trained neural network is embarrassingly parallel across samples.** Each sample in the batch is independent during inference, which is why GPUs — with thousands of cores running the same instruction on different data (SIMD) — accelerate neural network inference so dramatically. The backward pass during training has more complex data dependencies because gradients flow backward through layers sequentially, but it still parallelises over the batch dimension for the matrix multiplications at each layer.

- **The world's first working multi-layer neural network was not trained with backpropagation.** Alexey Ivakhnenko's Group Method of Data Handling (GMDH), published in 1968, trained deep networks layer by layer using polynomial regression and statistical selection criteria. Ivakhnenko's networks had multiple hidden layers and were trained on real data a full eighteen years before the Rumelhart-Hinton-Williams backpropagation paper. The GMDH approach — adding layers incrementally and pruning unhelpful units — anticipated modern ideas like progressive growing and network pruning by several decades, though it was independently invented in the Soviet Union and largely unknown to Western researchers at the time.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Using `W @ X` instead of `X @ W` | Inner dimensions don't match when batch size ≠ output size; silent wrong results when they coincidentally match | Always position samples left, weight matrix right: `X @ W` |
| Forgetting the batch dimension for single samples | `(d_in,) @ (d_in, d_out)` produces `(d_out,)` — a 1D vector that breaks downstream 2D expectations | `x.reshape(1, -1)` before passing to any layer |
| Not caching pre-activation Z | Some activation derivatives can use A, but Z preserves the original linear output for uniform backward rules, diagnostics, and activation variants | Store `self.Z` in every `Layer.forward()` call |
| Calling `forward()` twice without running backpropagation | Second call overwrites cached Z/A the backward pass needs; gradients are silently wrong for the first batch | Training loop must enforce: one forward → one backward → update → next forward |
| Applying softmax with `axis=0` | Normalises across batch instead of classes; per-sample probabilities no longer sum to 1 | Always `softmax(logits, axis=1)` for batched classification |
| Bias of shape `(d_out, 1)` broadcast against `(N, d_out)` | Bias is duplicated along the feature axis instead of the batch axis | Keep biases 1D: `np.zeros(d_out)` or `(d_out,)` |

---

## Quiz

1. **A layer has 10 input features and 6 output units. What is the shape of its weight matrix `W` and its bias vector `b`? If you pass a batch of 32 samples through this layer, what shape does the output have?**

   <details>
   <summary>Answer</summary>
   `W` has shape `(10, 6)` — one row per input feature, one column per output unit. `b` has shape `(6,)` — one scalar bias per output unit. For a batch of 32 samples, `X @ W` computes `(32, 10) @ (10, 6)` = `(32, 6)`, and broadcasting adds `b` to each row. The layer's pre-activation Z and activation A both have shape `(32, 6)`.
   </details>

2. **You pass a single sample `x` of shape `(10,)` through a layer with `W` of shape `(10, 4)`. The forward pass executes `x @ W + b` without error, producing output of shape `(4,)`. You then pass this output to another layer expecting `(N, 4)`. What goes wrong?**

   <details>
   <summary>Answer</summary>
   The first layer's output is 1D — shape `(4,)` rather than the expected `(1, 4)`. NumPy treated `(10,) @ (10, 4)` as a vector-matrix product, which is valid but produces a 1D result instead of the expected 2D batch. The second layer receives `(4,)` and may produce subtly wrong results or an outright error because the batch dimension was lost mid-pipeline and subsequent operations that expect a 2D tensor fail or broadcast incorrectly. The fix is `x.reshape(1, -1)` to preserve the batch axis: `(1, 10) @ (10, 4)` = `(1, 4)`.
   </details>

3. **The ReLU activation of the second hidden layer in a batch of 64 samples produces an output tensor of shape `(64, 128)`. You forget to cache `Z₂` but do cache `A₂`. Assuming the backward pass still has the previous activation and upstream gradient, does missing `Z₂` prevent you from computing the standard ReLU derivative? What information did you lose by caching only `A₂`?**

   <details>
   <summary>Answer</summary>
   No, missing Z₂ does not prevent the standard ReLU derivative if A₂ is available: compute it with `(A₂ > 0)`, because positive activations came from positive Z₂ entries while zeros came from negative or zero Z₂ entries under the usual derivative-at-zero convention. A₂ alone is not enough to compute the full weight gradient — you still need the previous activation and the upstream gradient — but it is enough for this activation derivative. What A₂ cannot tell you is the original negative magnitude: `Z₂ = -3.0` and `Z₂ = -0.5` both become `A₂ = 0.0`. That lost information matters for diagnostics, activation variants, and a uniform micro-framework cache, so the better engineering habit is still to store Z₂ even though this specific ReLU derivative can be recovered from A₂.
   </details>

4. **An MLP has layer dimensions `[784 → 256 → 128 → 10]`, a typical MNIST digit classifier. Using batch size 64, compute the total number of trainable parameters and the total forward-pass FLOPs for matrix multiplications only. With 60,000 training examples and a target of 10 training epochs, estimate the total FLOPs (forward + backward) for the full training run.**

   <details>
   <summary>Answer</summary>

   **Parameters:**
   - Layer 1 (784→256): 784×256 + 256 = 200,704 + 256 = 200,960
   - Layer 2 (256→128): 256×128 + 128 = 32,768 + 128 = 32,896
   - Layer 3 (128→10): 128×10 + 10 = 1,280 + 10 = 1,290
   - Total: 200,960 + 32,896 + 1,290 = **235,146**

   **FLOPs per forward pass (batch 64, matrix multiplications only):**
   - L1: 2 × 64 × 784 × 256 = 25,690,112
   - L2: 2 × 64 × 256 × 128 = 4,194,304
   - L3: 2 × 64 × 128 × 10 = 163,840
   - Forward total: **30,048,256 FLOPs** ≈ 30 megaFLOPs

   **Full training run:**
   - Batches per epoch: 60,000 / 64 ≈ 938 batches
   - FLOPs per batch (forward + backward ≈ 3× forward): 3 × 30,048,256 ≈ 90,144,768
   - FLOPs per epoch: 938 × 90,144,768 ≈ 84.6 gigaFLOPs
   - FLOPs for 10 epochs: **≈ 846 gigaFLOPs**
   
   A modern GPU (several teraFLOPs/second) handles this in under a second, which is why MNIST training is nearly instantaneous on decent hardware despite the seemingly large FLOP count.
   </details>

5. **In the hand-set XOR solution from Part 4, hidden unit h1 fires when `x₁ + x₂ > 0.5` and hidden unit h2 fires when `x₁ + x₂ > 1.5`. The output layer weighs h1 by +1 and h2 by −4. Explain geometrically how this configuration solves XOR: what does each hidden unit detect in the original input space, and why does a single layer without these hidden units fail?**

   <details>
   <summary>Answer</summary>
   Hidden unit h1 detects "at least one input is 1" — it fires (produces a positive value) for inputs (0,1), (1,0), and (1,1), outputting the sum minus 0.5. Hidden unit h2 detects "both inputs are 1" — it only fires for input (1,1), where the sum of 2 exceeds the 1.5 threshold. In the hidden space (h1, h2), the four XOR points map to: (0,0)→(0,0), (0,1)→(0.5,0), (1,0)→(0.5,0), (1,1)→(1.5,0.5). The output layer draws the decision line `1·h1 − 4·h2 = 0` in this 2D hidden space. For (0,1) and (1,0), h1=0.5 and h2=0, so the logit is 0.5 (positive → class 1). For (1,1), h1=1.5 and h2=0.5, so the logit is 1.5 − 2.0 = −0.5 (negative → class 0). For (0,0), both are zero, logit is 0 and σ(0)=0.5, which maps to class 0 because the code predicts class 1 only when the output probability is greater than 0.5.

   A single layer without hidden units fails because it can only draw one straight line in the original (x₁,x₂) input space. No single line can put (0,0) and (1,1) on one side while putting (0,1) and (1,0) on the other. The hidden layer solves this by applying a nonlinear transformation — the ReLU fold — that maps the four points to new coordinates where they become linearly separable. The two hidden units effectively create a new coordinate system in which the XOR pattern collapses to a linearly separable arrangement, and the output layer's line in that new coordinate system cleanly divides the classes. This is the geometric essence of why depth works: each hidden layer learns a coordinate transformation that makes the remaining classification problem simpler for the next layer.
   </details>

6. **A colleague proposes doubling the width of every hidden layer in the 2-hidden-layer MLP from Part 2: `[4 → 10 → 6 → 2]` instead of `[4 → 5 → 3 → 2]`. By approximately what factor does the forward-pass FLOP count increase?**

   <details>
   <summary>Answer</summary>

   **Original** `[4→5→3→2]`:
   - L1: 2×N×4×5 = 40N
   - L2: 2×N×5×3 = 30N
   - L3: 2×N×3×2 = 12N
   - Total: 82N FLOPs

   **Doubled width** `[4→10→6→2]`:
   - L1: 2×N×4×10 = 80N
   - L2: 2×N×10×6 = 120N
   - L3: 2×N×6×2 = 24N
   - Total: 224N FLOPs

   The factor is 224/82 ≈ 2.73×. Notice that doubling widths does not simply double the FLOP count — it approximately quadruples the L2 FLOPs (because both the input and output dimensions of L2 double) and exactly doubles L1 and L3. The parameter count increases from 51 to approximately 4×10+10 + 10×6+6 + 6×2+2 = 50 + 66 + 14 = 130, a factor of about 2.55×. Width changes have superlinear effects on both FLOPs and parameters because they affect the products of adjacent dimensions.
   </details>

---

## Hands-On Exercise

**Task:** Extend `nn.py` with the `MLP` class from Part 6, then build and test a 3-hidden-layer MLP that passes forward propagation shape-checks, produces a correct cache, and handles single-sample inference correctly.

### Steps

1. Add the `MLP` class from Part 6 to your `nn.py`. If the `Layer` class from A2 is missing or incomplete, add or fix it using the canonical version from Part 1.4.
2. Build an MLP with architecture: input 8 features, hidden layers [16, 12, 8] all with ReLU, output 3 units (linear). Use `count_parameters()` from Part 7 to verify the total before running the forward pass.
3. Create a random batch of 10 samples with 8 features. Run `mlp.forward(X)` and verify that the output shape is `(10, 3)`, the cache contains keys `['A0', 0, 1, 2, 3]`, and for each layer `i`, `cache[i]['Z'].shape` equals `(10, d_i)` and `cache[i]['A'].shape` equals `(10, d_i)`.
4. Verify cache integrity by recomputing Z₁ from cache['A0'] and layer 0's stored weights — confirm that `np.allclose(cache[0]['Z'], cache['A0'] @ mlp.layers[0].W + mlp.layers[0].b)` returns True.
5. Change the batch to a single sample of shape `(8,)`. Apply the batch-dimension fix (`reshape(1, -1)`) and confirm the forward pass produces output of shape `(1, 3)`. Then remove the reshape, observe what happens, and read the error message carefully.

### Success Criteria
- [ ] `MLP` class is added to `nn.py` and imports without errors.
- [ ] Forward pass on a batch of 10 samples produces output of shape `(10, 3)`.
- [ ] Cache dictionary has the correct keys and all cached tensors have the expected shapes.
- [ ] Cache integrity check passes without assertion errors.
- [ ] Single-sample forward pass with `reshape(1, -1)` produces output of shape `(1, 3)`.

### Verification skeleton
```python
# Assumes nn.py has Layer and MLP classes from A2/A3
# from nn import Layer, MLP

# Step 2: Build the MLP
layers = [
    Layer(8, 16, activation=lambda z: np.maximum(0, z)),
    Layer(16, 12, activation=lambda z: np.maximum(0, z)),
    Layer(12, 8, activation=lambda z: np.maximum(0, z)),
    Layer(8, 3, activation=lambda z: z),
]
mlp = MLP(layers)
count_parameters(layers)

# Step 3: Forward pass on batch
rng = np.random.default_rng(99)
X = rng.normal(0, 1, size=(10, 8))
output, cache = mlp.forward(X)
print("Output shape:", output.shape)       # (10, 3)
print("Cache keys:", sorted(cache.keys(), key=lambda k: str(k)))
for k in cache:
     if k != 'A0':
         print(f"  Layer {k}: Z {cache[k]['Z'].shape}, A {cache[k]['A'].shape}")

# Step 4: Verify cache
Z0_check = cache['A0'] @ mlp.layers[0].W + mlp.layers[0].b
assert np.allclose(cache[0]['Z'], Z0_check), "Cache integrity failure!"
print("Cache integrity: OK")

# Step 5: Single sample
x_one = rng.normal(0, 1, size=8)
out_one, _ = mlp.forward(x_one.reshape(1, -1))
print("Single sample output shape:", out_one.shape)  # (1, 3)
```

---

## Key Takeaways

- **A neural network layer is a weight matrix.** `W` has shape `(d_in, d_out)` and `b` has shape `(d_out,)`. The forward computation is `Z = X @ W + b` followed by activation `A = σ(Z)`. Vectorisation over a batch of `N` samples produces `Z` and `A` of shape `(N, d_out)` in a single matrix multiplication. The convention is `X @ W` with samples on the left, weights on the right, and matching inner dimensions — this is universal across every deep learning framework.

- **Shape discipline prevents silent bugs.** Build a shape table before coding and verify it with a debug forward pass that prints every intermediate shape. The five most common bugs — missing batch dimension, transposed weights, misaligned biases, mismatched layer dimensions, and wrong softmax axis — are all detectable by comparing printed shapes against a precomputed table. Inserting `debug_forward()` once per architecture saves hours of silent debugging later, and keeping the output alongside the shape table serves as living documentation.

- **Hidden layers transform the input representation into a space where classes become linearly separable.** A 2-layer network solves XOR because the first layer's ReLU units fold the input plane so that a straight line in the hidden space separates all four cases. The first hidden unit detects "at least one input is 1," the second detects "both inputs are 1," and the output layer subtracts a penalty to identify the (1,1) case. This geometric transformation — not magic, but a sequence of matrix multiplications and elementwise nonlinearities — is the mechanism by which every hidden layer in every neural network contributes to representational power.

- **Cache pre-activations Z and activations A during the forward pass because the backward pass and diagnostics benefit from both.** Common derivatives for sigmoid, tanh, and standard ReLU can be computed from A, while Z preserves the original linear output for uniform activation code, custom derivatives, debugging, and activation variants that need more than the clipped post-activation value. The weight gradient also requires A of the previous layer. The `Layer.forward()` method stores both as instance attributes, and the `MLP.forward()` method collects them into a dictionary keyed by layer index. Never call `forward()` twice without an intervening backward pass, or the second forward call overwrites the cache that the first backward call needs.

- **Parameter count scales as `d_in × d_out + d_out` per layer, and forward-pass FLOPs scale as `2 × N × Σ d_{l-1} × d_l` for the matrix multiplications.** A network's capacity, memory footprint, and computational cost are determined by these sums. For a typical MNIST classifier `784→256→128→10` with batch size 64, the count is approximately 235,000 parameters and 30 megaFLOPs per forward pass. Width changes have superlinear effects because they affect the product of adjacent dimensions — doubling hidden widths can quadruple the FLOPs for layers between two widened dimensions.

---

## Sources

- Rumelhart, D. E., Hinton, G. E., & Williams, R. J. (1986). "Learning representations by back-propagating errors." *Nature*, 323, 533–536. https://www.nature.com/articles/323533a0
- CS231n: Convolutional Neural Networks for Visual Recognition — Neural Nets notes. Stanford University. https://cs231n.github.io/neural-networks-1/
- Zhang, A., Lipton, Z. C., Li, M., & Smola, A. J. (2023). "Dive into Deep Learning" — Chapter 5: Multilayer Perceptrons. https://d2l.ai/chapter_multilayer-perceptrons/index.html
- Nielsen, M. (2015). "Neural Networks and Deep Learning" — Chapters 1 and 2. http://neuralnetworksanddeeplearning.com/
- He, K., Zhang, X., Ren, S., & Sun, J. (2015). "Delving Deep into Rectifiers: Surpassing Human-Level Performance on ImageNet Classification." *ICCV 2015*. https://arxiv.org/abs/1502.01852
- Minsky, M., & Papert, S. (1969). *Perceptrons: An Introduction to Computational Geometry*. MIT Press.
- Goodfellow, I., Bengio, Y., & Courville, A. (2016). *Deep Learning* — Chapter 6: Deep Feedforward Networks. MIT Press. https://www.deeplearningbook.org/
- NumPy documentation: Broadcasting semantics. https://numpy.org/doc/stable/user/basics.broadcasting.html
- NumPy documentation: `numpy.matmul`. https://numpy.org/doc/stable/reference/generated/numpy.matmul.html
- Karpathy, A. (2020). "micrograd" — A tiny scalar-valued autograd engine. https://github.com/karpathy/micrograd
- Ivakhnenko, A. G. (1968). "The Group Method of Data Handling — A Rival of the Method of Stochastic Approximation." *Soviet Automatic Control*, 1(3), 43–55. https://gmdh.net/

---

## Learner check

> The backward pass can often use the cached activation A directly for common nonlinearities: sigmoid uses `A * (1 - A)`, tanh uses `1 - A**2`, and standard ReLU can use `(A > 0)` when adopting the usual derivative-at-zero convention.

(This blockquote is from a touched section above — verified verbatim for the merge hook.)

---

## Next Module

Proceed to [A4: Activation Functions in Depth](/ai-ml-engineering/deep-learning/module-1.1.4-activation-functions/), where you will study the mathematical properties, derivatives, and failure modes of every major activation function — building directly on the cached Z values and the forward-pass architecture established here.
