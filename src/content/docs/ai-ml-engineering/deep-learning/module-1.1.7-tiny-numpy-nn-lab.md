---
title: "Tiny NumPy NN Lab: XOR to Fashion-MNIST"
slug: ai-ml-engineering/deep-learning/module-1.1.7-tiny-numpy-nn-lab
sidebar:
  order: 1002.7
---

> **AI/ML Engineering Track** | Complexity: `[COMPLEX]` | Time: 5–7 hours
>
> **Reading Time**: 3–4 hours | **Exercise**: 1–2 hours
>
> **Prerequisites**: Modules 1.1.1 (Math Warm-Up), 1.1.2 (Neuron & Perceptron from Scratch),
> 1.1.3 (Forward Propagation in MLPs), 1.1.4 (Activation Functions), 1.1.5 (Loss Functions &
> Output Heads), and 1.1.6 (Backpropagation by Hand for Dense Nets). You need the `nn.py`
> micro-framework built cumulatively through those modules.

---

In Block A so far you have built every component of a neural network by hand: the neuron, the
forward pass through stacked layers, the activation functions and their derivatives, the loss
that measures distance from the target, and the backward pass that computes gradients through
the chain rule. Each module gave you a piece of machinery. None of them, on its own, could learn.

This module assembles every Block A component into a working training loop. You will watch a
hand-built network converge on three datasets of rising difficulty — XOR (the four-point
problem that defeated the perceptron in A2), two interleaving half-moons, and a real
Fashion-MNIST image classifier — using only NumPy and the classes already growing in your
`nn.py`. By the end you will have a complete from-scratch trainer: forward, loss, backward,
parameter update, repeated over mini-batches across epochs, with loss curves that tell a story.
This is the capstone of Block A: you built the engine across six prior modules, and here you
turn the key — watching loss fall on real data with code you wrote yourself.

---

## Learning Outcomes

By the end of this module, you will be able to demonstrate each of the following in a working
NumPy trainer you can explain line by line:

- Implement the canonical training loop in pure NumPy — forward, loss, backward, SGD step over
  mini-batches and epochs, with correct gradient accumulation and parameter update ordering.
- Train small MLPs on XOR, two-moons, and Fashion-MNIST — including NumPy data generation,
  standard loading and preprocessing, train/validation splits, and honest accuracy reporting.
- Diagnose common training failures: NaN loss from high learning rates, overfitting visible in
  train/validation gaps, incorrect initial loss, and inability to overfit a single batch.
- Apply learning-rate and batch-size sensitivity through controlled experiments, connecting
  observed loss curves to underlying SGD dynamics.
- Wrap the training loop into a reusable `train()` helper in `nn.py`, closing Block A with a
  complete from-scratch trainer and a clear forward-reference to PyTorch in Block B.

---

## Why This Module Matters

Every prior Block A module was a static computation. You called `forward()` and received a
tensor. You called `backward()` and received gradients. Neither call changed the model. That
changes here. The training loop is the computation that turns static gradients into a model
that improves. It is also where more things can go wrong than in the forward and backward
passes combined: wrong update order, stale cached activations, gradient contributions from the
wrong batch, learning rates that produce NaN instead of progress, and loss curves that look
plausible but correspond to a model that has silently diverged.

This module also closes the loop that opened in A2. The perceptron could not solve XOR because
the data is not linearly separable. You proved that algebraically, traced the geometry, and
watched a training run cycle through mistakes forever without converging. Now you will build an
MLP with a hidden layer, train it with backpropagation and SGD, and watch the loss fall to
zero. That convergence is not magic — it is forward propagation through a hidden nonlinearity
followed by gradient descent on a differentiable loss. The pieces are the same pieces you built
across A2 through A6, connected into a loop that actually learns.

The three-dataset progression (XOR → two-moons → Fashion-MNIST) is deliberate. XOR gives you a
toy problem small enough to verify by hand — four points, a tiny network, convergence in
seconds. Two-moons adds noise, sample variation, and the need for a train/validation split, but
remains small enough to inspect visually. Fashion-MNIST forces you to confront real-world
concerns: data loading pipelines, normalisation decisions, batch-size tradeoffs, and accuracy
curves that plateau rather than converge to zero. Each dataset teaches a different debugging
muscle.

Finally, this module is where you stop being a consumer of deep-learning frameworks and start
being their peer. When you later call `model.fit()` in PyTorch or Keras, you will know what
that single line is doing: shuffling indices, slicing batches, running `forward()`, computing
the loss, running `backward()`, accumulating gradients, stepping with SGD, and repeating across
epochs. The abstraction is valuable, but only if you know what it abstracts. After this module,
you will.

---

## Part 1: The Training Loop, Named

### 1.1 The canonical cycle

Every supervised neural-network training loop — whether you write it in NumPy today or call
`optimizer.step()` in PyTorch tomorrow — repeats the same four steps, regardless of framework,
architecture, or dataset. The names and ordering are not stylistic choices; they are the minimum
sequence required for stochastic gradient descent to actually move parameters toward lower loss:

```text
for each epoch:
    shuffle the training data
    for each mini-batch:
        (1) FORWARD:  compute predictions and loss
        (2) BACKWARD: compute gradients via backpropagation
        (3) UPDATE:   apply gradients to parameters (SGD step)
    (4) REPORT:     log epoch-level metrics (loss, accuracy)
```

The names are standard. An **epoch** is one complete pass through the training set. A
**mini-batch** is a subset of the training data processed in one forward/backward/update cycle;
its size, the **batch size**, is a hyperparameter that trades gradient-noise against per-step
computation. An **iteration** is one mini-batch worth of the cycle. For a dataset of 60,000
samples and batch size 64, one epoch contains ⌈60000/64⌉ = 938 iterations.

The shuffle before each epoch prevents the model from learning spurious patterns in the
ordering of the data — a real problem when, for example, all class-0 examples precede all
class-1 examples in a classification dataset. Without shuffling, the model learns to predict
class 0 for the first half of each epoch and class 1 for the second half, a pattern it must
then unlearn when deployment data arrives in random order.

### 1.2 The loop skeleton in NumPy

Here is the skeleton that every trainer in this module shares. Study the structure before we
add the network-specific details, because every deviation from this ordering is a potential
bug:

```python
import numpy as np

def train_loop(model, X_train, y_train, loss_fn, epochs, batch_size, lr, rng=None):
    """Mini-batch SGD loop for an MLP model (see Part 8)."""
    if rng is None:
        rng = np.random.default_rng()
    N = X_train.shape[0]
    history = {'loss': [], 'acc': []}

    for epoch in range(epochs):
        # Shuffle indices each epoch — destroy ordering artifacts
        idx = rng.permutation(N)

        epoch_loss = 0.0
        epoch_correct = 0

        for start in range(0, N, batch_size):
            batch_idx = idx[start:start + batch_size]
            Xb, yb = X_train[batch_idx], y_train[batch_idx]

            # (1) FORWARD
            logits = model.forward(Xb)              # MLP.forward — no cache returned
            loss, dlogits = loss_fn(logits, yb)

            # (2) BACKWARD
            model.backward(dlogits)                 # MLP.backward — single arg, self-cached

            # (3) UPDATE
            for param, grad in model.parameters():  # in-place SGD via parameters() generator
                param -= lr * grad

            epoch_loss += loss * len(batch_idx)
            if logits.shape[1] == 1:
                preds = (sigmoid(logits) > 0.5).astype(int).ravel()
                targets = yb.ravel().astype(int)
                epoch_correct += (preds == targets).sum()
            else:
                epoch_correct += (logits.argmax(axis=1) == yb.argmax(axis=1)).sum()

        history['loss'].append(epoch_loss / N)
        history['acc'].append(epoch_correct / N)
        print(f"Epoch {epoch+1:3d}  loss: {history['loss'][-1]:.4f}  "
              f"acc: {history['acc'][-1]:.3f}")

    return history
```

Read this skeleton against what you built in A6. The `model.backward(dlogits)` call is the
hand-derived chain rule you coded layer by layer; each `Layer` caches its own activations in
`forward()` so backward needs only the upstream gradient. The update loop walks
`model.parameters()` — plain SGD with no momentum or Adam yet. Nothing here is new mathematics
— it is the same `dW` and `db` tensors your `Layer.backward()` populated, now applied on every
mini-batch instead of a single toy example. When you run this loop, watch the printed loss:
epoch 1 should be near `ln(K)` for `K` classes (Part 7.2), then trend downward if forward,
backward, and update are wired correctly.

Three implementation details deserve explicit attention because they are the most common silent
bugs in student trainers. First, the loss is multiplied by `len(batch_idx)` before accumulating
so that the epoch average weights each sample equally even when the final batch is smaller than
`batch_size`. Second, accuracy must match the output head: for single-logit binary problems
use `(sigmoid(logits) > 0.5)`; for one-hot multiclass use `.argmax(axis=1)` on both logits and
targets (integer labels can be compared directly). Third, the parameter update
(`param -= lr * grad`) must happen *after* the backward pass for all layers, because
later-layer gradient computations depend on earlier-layer weights. Updating weights
mid-backpropagation is a classic bug that produces silently wrong gradients — the model still
trains, but slower and to a worse final loss, which makes the bug hard to spot without the
ordering discipline from A6.

### 1.3 The softmax cross-entropy block

Since A5 and A6 provide the loss and backward derivations, we need only the NumPy functions
that those modules produce. The softmax with log-sum-exp stabilisation and the
cross-entropy loss with its combined backward pass (which returns `p - y`) are:

```python
def softmax_cross_entropy(logits, y_onehot):
    """Stable softmax + cross-entropy. Returns (loss, dlogits)."""
    N = logits.shape[0]
    # Stabilise: subtract max per row to avoid exp overflow
    shifted = logits - logits.max(axis=1, keepdims=True)
    exp_vals = np.exp(shifted)
    probs = exp_vals / exp_vals.sum(axis=1, keepdims=True)
    # Cross-entropy: −Σ y·log(p)
    eps = 1e-12
    loss = -np.sum(y_onehot * np.log(probs + eps)) / N
    # Combined gradient: p − y  (this is the key result from A5/A6)
    dlogits = (probs - y_onehot) / N
    return loss, dlogits
```

The gradient `dlogits = (probs − y_onehot) / N` is the most elegant result in
classification backpropagation — the combined derivative you derived in A5 and implemented in
A6. When the prediction is confident and correct (`probs[k] ≈ 1` for the true class), the
gradient is near zero for all logits, so SGD takes only a small step. When the prediction is
confident and wrong, the gradient is large and corrective, pushing logits toward the true label.
The division by `N` (the batch size) makes the loss an average rather than a sum, which keeps
gradient magnitudes stable when you change batch size later in Part 5. If you ever doubt this
block, re-run the finite-difference check from A4 on a single batch: numerical gradients and
`(probs - y_onehot) / N` should agree within floating-point tolerance.

### 1.4 The `Layer` with backward

The `Layer` class from A2/A3 holds `W`, `b`, `Z`, and `A`. For the training loop we extend
it with a `backward(dA)` method that computes gradients with respect to `W`, `b`, and the
input to the layer. The backward pass through the activation function is included, so `dA`
arriving from the layer above is the gradient with respect to the *post-activation* output
`A`. The layer first computes `dZ = dA * activation_derivative(Z)`, then computes `dW`, `db`,
and `dX` (the gradient to pass to the previous layer):

```python
# Activation functions and their derivatives — add to nn.py if not already present

def relu(z):
    return np.maximum(0, z)

def relu_deriv(z):
    return (z > 0).astype(float)

def sigmoid(z):
    z_clipped = np.clip(z, -500, 500)
    return 1.0 / (1.0 + np.exp(-z_clipped))

def sigmoid_deriv(z):
    s = sigmoid(z)
    return s * (1.0 - s)

# ---------------------------------------------------------------------------
# Layer class — accumulates A2 (forward) + A6 (backward) functionality

class Layer:
    """Fully-connected layer: Z = X @ W + b, A = activation(Z).
    Stores Z, A, dW, db for the training loop.
    """
    def __init__(self, d_in, d_out, activation_fn, activation_deriv, rng=None):
        if rng is None:
            rng = np.random.default_rng()
        self.W = rng.normal(0, np.sqrt(2.0 / d_in), size=(d_in, d_out))
        self.b = np.zeros(d_out)
        self.activation_fn = activation_fn
        self.activation_deriv = activation_deriv
        # Forward cache
        self.Z = None
        self.A = None
        # Gradient accumulators — populated by backward()
        self.dW = None
        self.db = None
        # Cache the input to this layer (X or A from prev layer)
        self.X_in = None

    def forward(self, X):
        self.X_in = X                     # store for dW computation
        self.Z = X @ self.W + self.b
        self.A = self.activation_fn(self.Z)
        return self.A

    def backward(self, dA):
        """Receive grad w.r.t. output A. Compute dW, db, and return dX."""
        dZ = dA * self.activation_deriv(self.Z)   # chain through activation
        self.dW = self.X_in.T @ dZ                 # (d_in, N) @ (N, d_out) → (d_in, d_out)
        self.db = dZ.sum(axis=0)                   # sum over batch → (d_out,)
        dX = dZ @ self.W.T                         # pass back to previous layer
        return dX
```

The backward pass through the activation — multiplying `dA` by `activation_deriv(self.Z)` —
is where the gradient can vanish (if the derivative is near zero, as in saturated sigmoid or
dead ReLU) or explode (if the derivative is large and compounding across many layers). This
is the mechanical reason behind the activation-function design principles covered in A4. Notice
how `self.X_in` is cached in `forward()` purely for the `dW = X_in.T @ dZ` multiply — the same
pattern PyTorch hides inside `autograd`. When you train XOR below, print `layer.dW.max()` after
the first backward: non-zero values confirm the chain rule is reaching every weight, not dying
at a saturated activation.

---

## Part 2: Dataset 1 — Closing the XOR Loop

### 2.1 The problem, revisited

In A2 you proved that a single perceptron cannot solve XOR. The four points on the 2D plane —
`(0,0):0`, `(0,1):1`, `(1,0):1`, `(1,1):0` — cannot be split by any straight line. You
watched the perceptron training loop cycle through mistakes forever because the model class
could not represent the target function. More epochs, a different learning rate, or different
initial weights could not fix a representational limitation.

Now we close that loop. A 2-layer MLP with one hidden layer of 4 ReLU units — architecture
`2 → 4 → 1` — *can* solve XOR. The hidden layer projects the four input points into a
4-dimensional space where the classes become linearly separable, and the output layer draws a
hyperplane in that transformed space.

### 2.2 Building and training the XOR MLP

The network below is small enough to train in under a second on any laptop, which makes it the
fastest end-to-end check that your A2–A6 pieces still compose correctly. We use binary
cross-entropy loss (sigmoid output) rather than softmax-CE because XOR is a binary problem with
labels in `{0, 1}`: the sigmoid produces a single probability per sample, and the binary
cross-entropy gradient is `a − y` (where `a` is the sigmoid output) — the same `(prediction −
target)` shape as softmax-CE, just in one dimension. The hidden layer uses ReLU (A4) and He-style
init `sqrt(2/d_in)` (A3); the output layer stays linear because the sigmoid lives inside the
loss, mirroring how softmax pairs with cross-entropy in the multi-class trainers later:

```python
import numpy as np

# ---------------------------------------------------------------------------
# Binary cross-entropy with sigmoid output
def binary_cross_entropy(logits, y):
    """BCE loss for binary classification. y is shape (N, 1) with values 0 or 1."""
    N = logits.shape[0]
    probs = sigmoid(logits)
    eps = 1e-12
    loss = -np.sum(y * np.log(probs + eps) + (1 - y) * np.log(1 - probs + eps)) / N
    dlogits = (probs - y) / N
    return loss, dlogits

# ---------------------------------------------------------------------------
# XOR dataset — the same four points from A2
X_xor = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=float)  # (4, 2)
y_xor = np.array([[0], [1], [1], [0]], dtype=float)               # (4, 1)

# Architecture: 2 → 4 → 1  (one hidden layer, binary output)
rng = np.random.default_rng(42)
layers = [
    Layer(2, 4, relu, relu_deriv, rng=rng),
    Layer(4, 1, lambda z: z, lambda z: np.ones_like(z), rng=rng),  # linear → sigmoid in loss
]

# Training configuration
epochs = 2000
lr = 0.5
N = X_xor.shape[0]
batch_size = 4  # full-batch on 4 samples

for epoch in range(epochs):
    idx = rng.permutation(N)
    Xb, yb = X_xor[idx], y_xor[idx]

    # Forward
    A = Xb
    for layer in layers:
        A = layer.forward(A)
    logits = A
    loss, dlogits = binary_cross_entropy(logits, yb)

    # Backward
    dA = dlogits
    for layer in reversed(layers):
        dA = layer.backward(dA)

    # SGD update
    for layer in layers:
        layer.W -= lr * layer.dW
        layer.b -= lr * layer.db

    if epoch % 400 == 0 or epoch == epochs - 1:
        preds = (sigmoid(logits) > 0.5).astype(int)
        acc = (preds == yb).mean()
        print(f"Epoch {epoch+1:4d}  loss: {loss:.6f}  acc: {acc:.2f}")
```

When you run the XOR trainer, compare every stage to the skeleton from §1.2: shuffle (trivial
on four points), forward through both layers, BCE loss, backward in reverse layer order, then
SGD. With `rng = np.random.default_rng(42)` for both weight init and shuffling, the printed
trace should match the following — the shape (high initial loss, rising accuracy, loss
approaching zero) confirms the loop is learning rather than merely running:

```text
Epoch    1  loss: 0.724909  acc: 0.75
Epoch  401  loss: 0.018664  acc: 1.00
Epoch  801  loss: 0.006498  acc: 1.00
Epoch 1201  loss: 0.003798  acc: 1.00
Epoch 1601  loss: 0.002657  acc: 1.00
Epoch 2000  loss: 0.002027  acc: 1.00
```

The loss starts near `−ln(0.5) ≈ 0.693` (the entropy of a fair coin) and falls toward zero
as the network learns to assign high probability to the correct class for each of the four
points. The accuracy reaching 1.00 against all four training points confirms what A2 proved
was impossible for a single perceptron: the hidden layer has learned a representation in
which XOR is linearly separable. The loop that opened in A2 — "why do we need depth?" — is
now closed with an executable answer.

### 2.3 What the hidden layer learned

After convergence, inspect what the hidden layer actually learned — this closes the conceptual
loop from A3 (hidden units as feature detectors) with numbers you can print. Forward through
the hidden layer only and compare the four rows: class-0 and class-1 points should land on
opposite sides of some hyperplane in the 4D hidden space, which is exactly the representation
argument you could only draw schematically before:

```python
# Forward through hidden layer only
A_hidden = relu(X_xor @ layers[0].W + layers[0].b)
print("Hidden representation:\n", A_hidden)
```

The four input points, which in the original `(x₁, x₂)` space form a checkerboard pattern,
are now mapped to four points in 4D where a single hyperplane (the output layer's weight
vector) cleanly separates class 0 from class 1. The specific coordinates depend on the random
initialisation, but the property is invariant: the hidden representation makes the problem
linearly solvable.

---

## Part 3: Dataset 2 — The Two-Moons Generator

### 3.1 Generating two interleaving half-moons in pure NumPy

The two-moons dataset — two crescent-shaped clusters that interleave without overlapping —
is a classic test for nonlinear classification. Unlike XOR's four discrete points, two-moons
has continuous variation and noise, which makes it a better test of generalisation. We
generate it from first principles in NumPy so you can see every sampling step rather than
treating the dataset as a black-box import. The geometry is two semicircles in the plane with
additive noise — nonlinearly separable like XOR, but with hundreds of points and stochastic
jitter, which forces you to care about generalisation instead of memorising four coordinates:

```python
def make_two_moons(n_samples=200, noise=0.1, rng=None):
    """Generate two interleaving half-moons in pure NumPy.

    Returns X of shape (2*n_samples, 2) and y of shape (2*n_samples,).
    Class 0 is the upper unit half-circle at the origin; class 1 is an inverted
    half-circle shifted right and down so the crescents interleave.
    """
    if rng is None:
        rng = np.random.default_rng()

    # Moon 0: upper unit half-circle at the origin (unshifted)
    theta0 = rng.uniform(0, np.pi, n_samples)
    x0 = np.column_stack([np.cos(theta0), np.sin(theta0)])
    x0 += rng.normal(0, noise, size=(n_samples, 2))
    y0 = np.zeros(n_samples, dtype=int)

    # Moon 1: inverted half-circle shifted right by 1.0, centered near y≈0.5
    theta1 = rng.uniform(0, np.pi, n_samples)
    x1 = np.column_stack([1.0 - np.cos(theta1), 0.5 - np.sin(theta1)])
    x1 += rng.normal(0, noise, size=(n_samples, 2))
    y1 = np.ones(n_samples, dtype=int)

    X = np.vstack([x0, x1])
    y = np.hstack([y0, y1])

    # Shuffle to mix the classes
    perm = rng.permutation(2 * n_samples)
    return X[perm], y[perm]
```

The generator samples `n_samples` points uniformly along a half-circle for each moon, adds
Gaussian noise with standard deviation `noise`, and combines them into a single array. Moon 0
is the upper unit half-circle at the origin (unshifted); moon 1 is an inverted half-circle
shifted right by 1.0 and down (centered near y≈0.5), so the two crescents interleave. The
result is two curved clusters that cannot be separated by any straight line — a 2D problem
that, like XOR, requires a hidden layer.

> **Convenience note**: scikit-learn provides `sklearn.datasets.make_moons(n_samples, noise)`
> for a similar two-moons dataset, but it is not a literal drop-in replacement: sklearn's
> `n_samples` is the *total* point count (pass `n_samples=2*N` to match this generator's
> `N`-per-moon), and the precise geometry and noise will differ slightly. The pure-NumPy
> generator above is provided so you can run every line of this module without any imports
> beyond NumPy.

### 3.2 Training and evaluating on two-moons

The training script below extends the XOR pattern in three ways that matter for real projects:
softmax-CE on two classes, a deeper `2 → 16 → 16 → 2` MLP, and an explicit train/validation
split so you log both `train_loss` and `val_loss` every epoch. Read it as the same §1.2 loop
with extra bookkeeping — the forward/backward/update core is unchanged, which is the point:
once the cycle is correct on XOR, scaling to curved boundaries is mostly data plumbing:

```python
# Generate dataset
rng = np.random.default_rng(42)
X, y = make_two_moons(n_samples=300, noise=0.15, rng=rng)

# Train/validation split — 80/20
N = X.shape[0]
n_train = int(0.8 * N)
idx = rng.permutation(N)
X_train, y_train = X[idx[:n_train]], y[idx[:n_train]]
X_val, y_val = X[idx[n_train:]], y[idx[n_train:]]

# One-hot encode labels for softmax-CE
y_train_oh = np.eye(2)[y_train]
y_val_oh = np.eye(2)[y_val]

# Architecture: 2 → 16 → 16 → 2
layers = [
    Layer(2, 16, relu, relu_deriv, rng=rng),
    Layer(16, 16, relu, relu_deriv, rng=rng),
    Layer(16, 2, lambda z: z, lambda z: np.ones_like(z), rng=rng),
]

lr = 0.05
batch_size = 32
epochs = 300
N_train = X_train.shape[0]

train_losses, val_losses, train_accs, val_accs = [], [], [], []

for epoch in range(epochs):
    # --- Training ---
    idx = rng.permutation(N_train)
    epoch_loss, epoch_correct = 0.0, 0

    for start in range(0, N_train, batch_size):
        batch_idx = idx[start:start + batch_size]
        Xb, yb = X_train[batch_idx], y_train_oh[batch_idx]

        # Forward
        A = Xb
        for layer in layers:
            A = layer.forward(A)
        loss, dlogits = softmax_cross_entropy(A, yb)

        # Backward
        dA = dlogits
        for layer in reversed(layers):
            dA = layer.backward(dA)

        # Update
        for layer in layers:
            layer.W -= lr * layer.dW
            layer.b -= lr * layer.db

        epoch_loss += loss * len(batch_idx)
        epoch_correct += (A.argmax(axis=1) == yb.argmax(axis=1)).sum()

    train_losses.append(epoch_loss / N_train)
    train_accs.append(epoch_correct / N_train)

    # --- Validation (no gradient) ---
    A_val = X_val
    for layer in layers:
        A_val = layer.forward(A_val)
    v_loss, _ = softmax_cross_entropy(A_val, y_val_oh)
    val_losses.append(v_loss)
    val_acc = (A_val.argmax(axis=1) == y_val.argmax(axis=1)).mean()
    val_accs.append(val_acc)

    if epoch % 60 == 0 or epoch == epochs - 1:
        print(f"Epoch {epoch+1:3d}  train_loss: {train_losses[-1]:.4f}  "
              f"train_acc: {train_accs[-1]:.3f}  "
              f"val_loss: {val_losses[-1]:.4f}  val_acc: {val_accs[-1]:.3f}")
```

The key addition from the XOR example is the **validation loop** — we run the forward pass on
held-out data after each epoch but *do not call backward or update*, so the validation data
never influences the model's parameters. This gives us an honest estimate of generalisation
performance. The decision boundary of a well-trained two-moons classifier is a curved line
that snakes between the two crescent-shaped clusters — the hidden layer has warped the input
coordinates so that the final linear classifier can draw a clean separation in the transformed
space.

### 3.3 The train/validation split

The validation set serves a specific purpose that the training loss alone cannot serve. The
training loss always decreases (or at least trends downward) because SGD directly optimises
it. The validation loss is the honest signal: if it stops decreasing while the training loss
continues to fall, the model is memorising noise in the training set rather than learning
general patterns. For two-moons with 300 samples and noise 0.15, a 2×16×16×2 MLP should
achieve >95% accuracy on both train and validation sets, with the gap between them staying
below a few percentage points.

---

## Part 4: Dataset 3 — Fashion-MNIST MLP

### 4.1 The dataset and loading strategy

Fashion-MNIST (Xiao et al., arXiv:1708.07747) is a drop-in replacement for the original MNIST
digits: 28×28 grayscale images of 10 clothing categories (t-shirt, trouser, pullover, dress,
coat, sandal, shirt, sneaker, bag, ankle boot). It is harder than digit MNIST — a plain MLP
achieves ~85–89% test accuracy instead of ~97–98% — which makes it a more honest benchmark
for a from-scratch classifier.

Fashion-MNIST is where Block A meets a dataset large enough that batching, normalisation, and
patience actually matter. We load through Keras's built-in helper (or `torchvision` if you
prefer PyTorch-style tooling) only for I/O — the IDX byte format is a distraction from the
training loop itself. Once arrays are in memory, every subsequent step uses your `Layer` class,
your softmax-CE, and your SGD update; the framework import never participates in forward or
backward. That separation is deliberate: in Block B you will replace Keras loading with
`torchvision.datasets.FashionMNIST` while keeping the same normalise-flatten-one-hot recipe:

```python
# Data loading — requires: pip install tensorflow  (or keras directly)
# If you do not have Keras, you can download the raw IDX files from
# https://github.com/zalandoresearch/fashion-mnist and parse them with
# numpy.frombuffer — but the Keras loader is the standard route.

from keras.datasets import fashion_mnist

(X_train_full, y_train_full), (X_test, y_test) = fashion_mnist.load_data()

# Normalise to [0, 1] and flatten 28×28 → 784
X_train_full = X_train_full.astype(float) / 255.0
X_test = X_test.astype(float) / 255.0
X_train_full = X_train_full.reshape(-1, 784)
X_test = X_test.reshape(-1, 784)

# One-hot encode labels (0–9 → 10-dimensional vectors)
y_train_full_oh = np.eye(10)[y_train_full]
y_test_oh = np.eye(10)[y_test]

# Hold out 10,000 training samples for validation
X_train, X_val = X_train_full[:-10000], X_train_full[-10000:]
y_train_oh, y_val_oh = y_train_full_oh[:-10000], y_train_full_oh[-10000:]

print(f"Train: {X_train.shape[0]}, Val: {X_val.shape[0]}, Test: {X_test.shape[0]}")
# Output: Train: 50000, Val: 10000, Test: 10000
```

The normalisation to `[0, 1]` is essential. Raw pixel values are integers 0–255; feeding those
directly into a network with He-initialised weights produces pre-activations in the hundreds,
which saturate ReLU outputs and can push the logit matmul toward overflow and NaN loss.
Normalising to `[0, 1]` keeps activations and gradients in a numerically stable
regime.

### 4.2 Architecture and training

A plain MLP with one hidden layer of 256 ReLU units is the baseline. The input is
784-dimensional (flattened 28×28 pixels), and the output is 10-dimensional with softmax-CE.
This architecture has `784×256 + 256 + 256×10 + 10 = 203,530` parameters — modest by modern
standards but sufficient for ~85% test accuracy on Fashion-MNIST when training is configured
honestly. The loop below is intentionally verbose (no `train()` helper yet) so you can map
each line to §1.2: inner loop over batches, validation forward-only pass, history dict for
plotting later. Expect epoch 1 accuracy near 10% (random guessing among ten classes) and loss
near `ln(10) ≈ 2.30`; if those sanity checks fail, fix preprocessing before burning twenty
epochs on a broken pipeline:

```python
# Architecture: 784 → 256 → 10
rng = np.random.default_rng(42)
layers = [
    Layer(784, 256, relu, relu_deriv, rng=rng),
    Layer(256, 10, lambda z: z, lambda z: np.ones_like(z), rng=rng),
]

lr = 0.05
batch_size = 64
epochs = 20
N_train = X_train.shape[0]
history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': []}

for epoch in range(epochs):
    # --- Training ---
    idx = rng.permutation(N_train)
    epoch_loss, epoch_correct = 0.0, 0

    for start in range(0, N_train, batch_size):
        batch_idx = idx[start:start + batch_size]
        Xb, yb = X_train[batch_idx], y_train_oh[batch_idx]

        A = Xb
        for layer in layers:
            A = layer.forward(A)
        loss, dlogits = softmax_cross_entropy(A, yb)

        dA = dlogits
        for layer in reversed(layers):
            dA = layer.backward(dA)

        for layer in layers:
            layer.W -= lr * layer.dW
            layer.b -= lr * layer.db

        epoch_loss += loss * len(batch_idx)
        epoch_correct += (A.argmax(axis=1) == yb.argmax(axis=1)).sum()

    history['train_loss'].append(epoch_loss / N_train)
    history['train_acc'].append(epoch_correct / N_train)

    # --- Validation ---
    A_val = X_val
    for layer in layers:
        A_val = layer.forward(A_val)
    v_loss, _ = softmax_cross_entropy(A_val, y_val_oh)
    history['val_loss'].append(v_loss)
    history['val_acc'].append((A_val.argmax(axis=1) == y_val_oh.argmax(axis=1)).mean())

    print(f"Epoch {epoch+1:2d}  "
          f"train_loss: {history['train_loss'][-1]:.4f}  "
          f"train_acc: {history['train_acc'][-1]:.3f}  "
          f"val_loss: {history['val_loss'][-1]:.4f}  "
          f"val_acc: {history['val_acc'][-1]:.3f}")

# --- Final test evaluation ---
A_test = X_test
for layer in layers:
    A_test = layer.forward(A_test)
test_loss, _ = softmax_cross_entropy(A_test, y_test_oh)
test_acc = (A_test.argmax(axis=1) == y_test_oh.argmax(axis=1)).mean()
print(f"\nTest loss: {test_loss:.4f}  Test accuracy: {test_acc:.4f}")
```

Expected output after 20 epochs: training accuracy ~88–90%, validation accuracy ~85–87%, test
accuracy ~85–87%. The test accuracy being slightly below training accuracy is normal — it
reflects the gap between the distribution the model was optimised on and the held-out
distribution. An MLP cannot exploit the spatial structure of images the way a CNN can, so
~87% test accuracy is near the ceiling for a plain 784→256→10 MLP without data augmentation,
dropout, or batch normalisation. A CNN (which we build in Block D) pushes this past 93%.
State honestly: this is what a plain MLP achieves; if your numbers are substantially lower
(<80%), check your normalisation, initialisation, and learning rate.

While the epoch loop runs, compare three signals together rather than chasing accuracy alone.
Initial loss near `ln(10)` confirms preprocessing; falling training loss confirms forward and
backward; validation accuracy within a few points of training accuracy confirms you are not
grossly overfitting on 50,000 samples. If training accuracy climbs while validation accuracy
stalls below 80%, revisit Part 6.2 before adding layers or epochs — more capacity rarely fixes
a data or normalisation bug. CS231n's training notes (see Sources) describe this babysitting
mindset: watch curves, intervene early, and treat every divergence as a hypothesis about
numerics or hyperparameters rather than mere random bad luck.

### 4.3 What the model actually learns

The weights of the first layer have shape `(784, 256)`. Each of the 256 columns is a
784-dimensional vector that, when reshaped to 28×28, forms a pattern the neuron responds to.
Early in training these patterns are random noise. By epoch 20, many of them have organised
into coarse templates: one neuron might respond to trouser-like vertical structures, another
to t-shirt-like horizontal shoulders, another to bag-like rectangular outlines. These are not
clean Gabor filters — an MLP lacks the translation-invariance inductive bias of a CNN — but
they are recognisably clothing-shaped templates that the second layer combines into
class-level decisions.

---

## Part 5: Hyperparameters That Matter Here

### 5.1 Learning rate — the master dial

The learning rate is the single most important hyperparameter in this micro-framework, and
the effects of getting it wrong are dramatic. Too high a learning rate causes the loss to
explode to NaN within a few iterations — the gradient steps overshoot minima, the weights
grow large, and the pre-activation matmul `Z = X @ W + b` overflows to `inf` (or `NaN`);
those poisoned logits break even the max-subtracted softmax (`inf − inf = NaN`).
Too low a learning rate causes convergence to crawl, with the loss decreasing by fractions
of a percent per epoch and the model never reaching acceptable accuracy within a reasonable
training budget.

The fastest way to internalise learning-rate sensitivity is a controlled sweep on XOR: same
seed, same architecture, only `lr` changes. Run the experiment below and treat the printed
`any_NaN` column as a hard failure signal — not a hyperparameter to tune around, but evidence
the numerical pipeline has left the stable regime from A4's activation clipping and A5's log-sum-exp
stabilisation:

```python
def train_xor_with_lr(lr, epochs=1000):
    rng = np.random.default_rng(42)
    layers = [
        Layer(2, 4, relu, relu_deriv, rng=rng),
        Layer(4, 1, lambda z: z, lambda z: np.ones_like(z), rng=rng),
    ]
    X_xor = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=float)
    y_xor = np.array([[0], [1], [1], [0]], dtype=float)
    losses = []
    for epoch in range(epochs):
        idx = rng.permutation(4)
        Xb, yb = X_xor[idx], y_xor[idx]
        A = Xb
        for layer in layers:
            A = layer.forward(A)
        loss, dlogits = binary_cross_entropy(A, yb)
        dA = dlogits
        for layer in reversed(layers):
            dA = layer.backward(dA)
        for layer in layers:
            layer.W -= lr * layer.dW
            layer.b -= lr * layer.db
        losses.append(loss)
    return losses

import pprint
for lr in [0.001, 0.01, 0.1, 1.0, 10.0]:
    losses = train_xor_with_lr(lr)
    # Report final loss and whether NaN appeared
    has_nan = any(np.isnan(l) for l in losses)
    final = losses[-1]
    print(f"lr={lr:6.3f}  final_loss={final:.6f}  any_NaN={has_nan}  "
          f"losses={[f'{l:.4f}' for l in losses[:4]]}...")
```

Across random seeds you should see a consistent pattern: at `lr=0.001` loss decreases slowly and
may not reach ~0 within 1000 epochs; at `lr=0.01` and `lr=0.1` convergence is steady to fast;
at `lr=1.0` training may still succeed but oscillates; at `lr=10.0` NaN appears within the
first few epochs as logits explode through the sigmoid and BCE path. That bracketing experiment
is the same sensitivity analysis you will repeat at Fashion-MNIST scale in the Hands-On Exercise.

The safe range for this micro-framework on normalised data is roughly `0.001 ≤ lr ≤ 1.0`.
Within that range, higher values train faster but risk instability; lower values are safer
but slower. The standard starting point for SGD on an MLP is `lr=0.01` to `0.1`.

### 5.2 Batch size — noise versus speed

Batch size is the other dial you will sweep in the Hands-On Exercise: it controls the
trade-off between gradient noise (stochasticity that can help escape shallow minima) and
per-step wall-clock (how many forward/backward passes fit in one epoch). The table summarises
the extremes; practical training lives in the mini-batch column:

| Batch size | Gradient noise | Steps per epoch | Wall-clock per epoch |
|------------|---------------|-----------------|---------------------|
| 1 (pure SGD) | High | N | Slow (N matmul calls) |
| 32–128 (mini-batch) | Moderate | N/batch_size | Moderate |
| N (full-batch) | Zero | 1 | Fastest per epoch |

Smaller batches produce noisier gradient estimates, which can help escape shallow local minima
but also make the loss curve more jagged. Larger batches produce smoother gradients but may
converge to sharper minima that generalise worse — a phenomenon studied extensively in the
deep-learning optimisation literature (Keskar et al., 2017). For the datasets in this module,
`batch_size=32` or `64` is a sensible default. Full-batch training on Fashion-MNIST
(50,000 samples) requires the entire dataset in memory for one forward pass, which is fine for
a 784→256→10 MLP but teaches a habit that does not scale to larger models.

### 5.3 Hidden width and depth

For XOR, 2 hidden units suffice — the hand-set solution in A3 used exactly two. Four hidden
units give the optimiser more paths to a solution. For two-moons, 8–16 hidden units in one or
two layers capture the curved boundary. For Fashion-MNIST, 256 hidden units in one layer
represents a sweet spot: fewer than 128 units underfit (accuracy < 82%), while more than 512
units increase training time without meaningful accuracy gains for a plain MLP.

Adding a second hidden layer to the Fashion-MNIST architecture (`784 → 256 → 128 → 10`) can
squeeze out another percentage point of accuracy at the cost of roughly double the training
time, because the extra layer can compose features hierarchically. The cost in additional
parameters is `256×128 + 128 = 32,896` — roughly 16% more than the single-hidden-layer
baseline.

---

## Part 6: Reading the Curves

### 6.1 What a healthy loss curve looks like

Loss curves are the primary telemetry you have before confusion matrices or test accuracy —
learn to read their shape as carefully as you read code. A healthy training loss curve for an
MLP on Fashion-MNIST typically shows three phases: rapid initial drop, slower refinement, then
a plateau near the model's capacity ceiling:

```text
loss
 │
 │ ╲          Phase 1: steep descent (model learns obvious patterns)
 │  ╲
 │   ╲
 │    ╲___    Phase 2: deceleration (model refines)
 │        ╲
 │         ╲__  Phase 3: plateau (model near capacity)
 │
 └────────────────── epoch
```

Phase 1 typically lasts the first few epochs. The loss drops sharply as the weights move from
random initialisation toward a region that captures coarse structure — for Fashion-MNIST, this
means learning that some pixel patterns consistently correlate with trousers versus bags.
Phase 2 is longer and less dramatic; the loss decreases more slowly as the model refines
finer distinctions (shirt versus t-shirt). Phase 3 is the plateau, where the loss bounces
around a floor determined by the irreducible noise in the data and the representational
capacity of the architecture.

### 6.2 The train/validation gap

Plot the training and validation loss on the same axes. A healthy training run shows both
curves decreasing together with a small gap between them — the validation loss is slightly
higher because the model was not directly optimised on the validation data, but both curves
share the same downward trend:

```text
loss
 │
 │  train ╲___                     train loss (lower, decreases smoothly)
 │           ╲___
 │  val  ╲      ╲___               validation loss (slightly higher, may bounce)
 │        ╲         ╲___
 │
 └─────────────────────── epoch
```

When the training loss continues to decrease but the validation loss *stops decreasing and
starts increasing* — the gap between them widens — the model is **overfitting**. It has
memorised noise and quirks in the training data that do not generalise to the validation set.
On two-moons with high noise and a small training set, this can happen within tens of epochs.
On Fashion-MNIST with 50,000 training samples, a plain MLP tends to plateau rather than
dramatically overfit, but the gap is still visible.

### 6.3 Deliberate overfitting — a diagnostic tool

Overfitting is easier to understand when you cause it intentionally rather than discovering it
accidentally on a production training run. Take the Fashion-MNIST training set, reduce it to
500 samples, and train for 100 epochs with the same 784→256→10 architecture you used in Part 4.
The training accuracy will approach 100% because the model has enough capacity to memorise 500
labeled images, while validation accuracy plateaus around 70–75% — a gap of twenty-five or more
percentage points that widens every epoch after the first ten. Training loss approaches zero
while validation loss hovers near 0.8–1.0, the textbook signature of a model that has stopped
learning generalisable structure and started fitting noise.

This is the scenario where **early stopping** matters. If you had stopped training at the
epoch where the validation loss was minimised (typically epoch 10–20 in this tiny-data
scenario), you would have a model that generalises about as well as the one at epoch 100, but
with less wasted computation. Early stopping is a regularisation technique that we implement
properly in Block B (PyTorch), where you have a framework that tracks validation metrics and
checkpoints the best model automatically.

---

## Part 7: Sanity Checks and Debugging

### 7.1 Overfit a single batch

The single most useful diagnostic before any long Fashion-MNIST run answers one question: can
your implementation memorise a tiny slice of data? Take 64 random training examples, train on
them exclusively for a few hundred epochs, and verify that loss drops toward zero and accuracy
approaches 100%. If this fails — loss plateaus high or accuracy stays near random guessing —
your network, loss, backward, or update has a bug that no amount of full-dataset training will
fix. This single-batch overfit test is Outcome 3 in practice: it isolates code errors from
data-scale or hyperparameter issues before you burn GPU-less hours on 50,000 images:

```python
# Sanity: overfit a single batch
X_small = X_train[:64]
y_small_oh = y_train_oh[:64]

layers = [
    Layer(784, 256, relu, relu_deriv),
    Layer(256, 10, lambda z: z, lambda z: np.ones_like(z)),
]

for epoch in range(200):
    A = X_small
    for layer in layers:
        A = layer.forward(A)
    loss, dlogits = softmax_cross_entropy(A, y_small_oh)
    dA = dlogits
    for layer in reversed(layers):
        dA = layer.backward(dA)
    for layer in layers:
        layer.W -= 0.01 * layer.dW
        layer.b -= 0.01 * layer.db
    if epoch % 40 == 0:
        acc = (A.argmax(axis=1) == y_small_oh.argmax(axis=1)).mean()
        print(f"Sanity epoch {epoch:3d}  loss: {loss:.4f}  acc: {acc:.3f}")
```

If this reaches accuracy > 0.95 within 200 epochs, the pipeline is correct and you can scale
to the full dataset with confidence. If it does not, check: (a) is the loss function
computing the correct gradient? (b) are the activation derivatives correct (verify with
finite differences as in A4)? (c) are the parameter updates subtracting `lr * grad` (not
adding)? (d) are you normalising the input data?

### 7.2 The initial loss check

Before training, compute the loss on the full training set with randomly initialised weights.
For a balanced `K`-class classification problem with softmax-CE, the expected initial loss is
`ln(K)`. For Fashion-MNIST with 10 roughly balanced classes, the initial loss should be
approximately `ln(10) ≈ 2.302`. If your initial loss is 0.0, you are computing the loss on
predictions that have already collapsed to a single class (likely due to an activation bug).
If it is 15.0, your logits are enormous (missing normalisation or weight initialisation is
too large). If it is NaN, your pre-activations or logits have overflowed.

Make the initial-loss check a habit before every new architecture or dataset — it costs one
forward pass and catches normalisation bugs, wrong output dimension, and softmax blow-ups
before you schedule a long training run:

```python
# Initial loss check
A_init = X_train
for layer in layers:
    A_init = layer.forward(A_init)
init_loss, _ = softmax_cross_entropy(A_init, y_train_oh)
print(f"Initial loss: {init_loss:.4f}  (expected ~{np.log(10):.4f} for 10 classes)")
```

### 7.3 What NaN loss means

When loss prints as `nan`, stop the epoch loop immediately — continuing only propagates NaN
weights and wastes time. In this micro-framework, three causes cover the vast majority of
cases, listed below in order of how often they appear in student submissions:

1. **Learning rate too high.** The gradient step pushes weights large, which pushes the
   pre-activation matmul `Z = X @ W + b` into the hundreds or thousands until `Z` overflows
   to `inf` (or `NaN`). Those `inf` logits then poison even the max-subtracted softmax from
   Part 1.3 (`inf − inf = NaN`). The stable softmax prevents overflow *inside* the softmax;
   it does not save you once the logits themselves are `inf`. Fix: reduce `lr` by a factor
   of 10 and retry.

2. **Missing input normalisation.** Raw pixel values of 0–255 combined with He-initialised
   weights of `N(0, sqrt(2/784)) ≈ N(0, 0.05)` produce pre-activations of order
   `255 * sqrt(784) * 0.05 ≈ 70`. While this may not overflow immediately, it pushes the
   softmax into a regime where small floating-point errors in exp can compound. Normalising
   to `[0, 1]` is the universal fix.

3. **Division by zero in cross-entropy.** If a softmax probability is exactly zero (possible
   with extreme logits), `log(0) = −inf`. The `eps = 1e-12` floor in the cross-entropy code
   prevents this, but if you omitted the floor, NaN is the result.

A NaN in the loss column is not a subtle tuning problem — it is a hard numerical failure
that tells you to stop, check the three causes above, and restart with a safer configuration.
Do not train through NaN on the assumption that it will self-correct; NaN gradients produce
NaN weights, and the run is unrecoverable.

---

## Part 8: Finalising the Micro-Framework

### 8.1 A reusable `train()` helper

After working through three datasets and a hyperparameter experiment, the training loop has
become a pattern you recognise — the same four beats whether the batch contains four XOR
points, 32 two-moon samples, or 64 Fashion-MNIST images. It is time to wrap that pattern into
a reusable function so that `nn.py` is a genuine micro-framework, not a collection of fragments
copied from Part 1 through Part 4. The refactor should change behaviour only by removing
copy-paste errors: run XOR and Fashion-MNIST once with the helper and confirm loss curves match
your earlier verbose scripts epoch for epoch.

```python
# Add to nn.py — the final Block A contribution

class MLP:
    """Multi-layer perceptron: stacks Layer objects, runs forward and backward."""
    def __init__(self, layers):
        self.layers = layers

    def forward(self, X):
        A = X
        for layer in self.layers:
            A = layer.forward(A)
        return A

    def backward(self, dA):
        for layer in reversed(self.layers):
            dA = layer.backward(dA)

    def parameters(self):
        """Generator yielding (param, grad) pairs for the update step."""
        for layer in self.layers:
            yield layer.W, layer.dW
            yield layer.b, layer.db


def _batch_correct(logits, yb):
    """Count correct predictions for single-logit binary or one-hot multiclass."""
    if logits.shape[1] == 1:
        preds = (sigmoid(logits) > 0.5).astype(int).ravel()
        targets = yb.ravel().astype(int)
        return (preds == targets).sum()
    return (logits.argmax(axis=1) == yb.argmax(axis=1)).sum()


def train(model, X_train, y_train_oh, X_val, y_val_oh,
          loss_fn, epochs, batch_size, lr, rng=None, verbose=True):
    """Train an MLP model with mini-batch SGD.

    Parameters
    ----------
    model : MLP
        Model with layers that have .forward() and .backward().
    X_train, y_train_oh : ndarray
        Training data and labels (one-hot for multiclass; shape (N, 1) for binary BCE).
    X_val, y_val_oh : ndarray
        Validation data and labels. Pass None for both to skip validation.
    loss_fn : callable
        Function (logits, y) -> (loss, dlogits). Use softmax_cross_entropy or
        binary_cross_entropy.
    epochs, batch_size, lr : standard hyperparameters.
    rng : numpy.random.Generator or None
        Seeded generator for shuffling and reproducible runs.
    verbose : bool
        Print progress every epoch.

    Returns
    -------
    history : dict with keys 'train_loss', 'train_acc', 'val_loss', 'val_acc'.
    """
    if rng is None:
        rng = np.random.default_rng()
    N = X_train.shape[0]
    history = {'train_loss': [], 'train_acc': [],
               'val_loss': [], 'val_acc': []}

    for epoch in range(epochs):
        # Shuffle
        idx = rng.permutation(N)
        epoch_loss, epoch_correct = 0.0, 0

        for start in range(0, N, batch_size):
            batch_idx = idx[start:start + batch_size]
            Xb, yb = X_train[batch_idx], y_train_oh[batch_idx]

            logits = model.forward(Xb)
            loss, dlogits = loss_fn(logits, yb)
            model.backward(dlogits)

            for param, grad in model.parameters():
                param -= lr * grad

            epoch_loss += loss * len(batch_idx)
            epoch_correct += _batch_correct(logits, yb)

        history['train_loss'].append(epoch_loss / N)
        history['train_acc'].append(epoch_correct / N)

        if X_val is not None:
            val_logits = model.forward(X_val)
            v_loss, _ = loss_fn(val_logits, y_val_oh)
            history['val_loss'].append(v_loss)
            if val_logits.shape[1] == 1:
                val_preds = (sigmoid(val_logits) > 0.5).astype(int).ravel()
                val_targets = y_val_oh.ravel().astype(int)
                history['val_acc'].append((val_preds == val_targets).mean())
            else:
                history['val_acc'].append(
                    (val_logits.argmax(axis=1) == y_val_oh.argmax(axis=1)).mean()
                )
        else:
            history['val_loss'].append(float('nan'))
            history['val_acc'].append(float('nan'))

        if verbose:
            msg = (f"Epoch {epoch+1:3d}  "
                   f"train_loss: {history['train_loss'][-1]:.4f}  "
                   f"train_acc: {history['train_acc'][-1]:.3f}")
            if X_val is not None:
                msg += (f"  val_loss: {history['val_loss'][-1]:.4f}  "
                        f"val_acc: {history['val_acc'][-1]:.3f}")
            print(msg)

    return history
```

The `MLP` class wraps the layers list and provides `forward()` (sequential), `backward()`
(reverse-sequential), and `parameters()` (generator for the update loop). The `train()`
function is the training loop from Parts 1–4, parameterised: shuffle, mini-batch slice,
forward, `loss_fn`, backward, SGD step, epoch metrics, optional validation. Passing
`loss_fn=softmax_cross_entropy` or `binary_cross_entropy` keeps the helper dataset-agnostic;
`_batch_correct()` handles accuracy for both single-logit binary (sigmoid threshold) and
one-hot multiclass (argmax). Pass a seeded `rng` for reproducible shuffles and weight init.
Together with `Layer`, activations, and losses, this is a complete from-scratch deep-learning
framework in under 200 lines of NumPy — every line traceable to A2–A6.

### 8.2 Using the final framework

With `train()` in `nn.py`, the Fashion-MNIST script from Part 4 collapses to configuration plus
a call — the same decomposition PyTorch encourages when you separate `model`, `criterion`, and
`optimizer`. Compare the eleven lines below to the fifty-line explicit loop and verify they
produce matching accuracy curves:

```python
rng = np.random.default_rng(42)
model = MLP([
    Layer(784, 256, relu, relu_deriv, rng=rng),
    Layer(256, 10, lambda z: z, lambda z: np.ones_like(z), rng=rng),
])

history = train(
    model, X_train, y_train_oh, X_val, y_val_oh,
    loss_fn=softmax_cross_entropy,
    epochs=20, batch_size=64, lr=0.05, rng=rng,
)

# Evaluate on test set
test_logits = model.forward(X_test)
test_loss, _ = softmax_cross_entropy(test_logits, y_test_oh)
test_acc = (test_logits.argmax(axis=1) == y_test_oh.argmax(axis=1)).mean()
print(f"Test accuracy: {test_acc:.4f}")
```

That is eleven lines of code that do what took 50 lines in Part 4. The framework is not
PyTorch — it lacks automatic differentiation, GPU support, optimisers beyond SGD,
regularisation, and a hundred other features — but it encapsulates exactly what the learner
needs to understand *before* those abstractions arrive. Every line of the framework was
written by the learner across Block A, and every line has a known purpose.

### 8.3 Block A close and Block B forward-reference

Block A is now complete. You have built a neural network from individual neurons through
forward propagation, activation functions, loss functions, backpropagation, and a training
loop. You have trained it on XOR, two-moons, and Fashion-MNIST. You have debugged NaN loss,
inspected training curves, and wrapped the result into a reusable `train()` function.

In Block B, you will pick up PyTorch and discover that `model.forward(X)`, `loss.backward()`,
and `optimizer.step()` are direct analogues of the three lines you just wrote by hand — the
same decomposition documented in the [PyTorch basics tutorial](https://pytorch.org/tutorials/beginner/basics/intro.html).
The PyTorch versions add automatic differentiation (no more hand-writing `backward()` methods),
GPU acceleration (no more waiting for NumPy to multiply on CPU), a library of optimisers
(SGD, Adam, RMSProp), and a `DataLoader` that shuffles and batches for you. But the underlying
computation — forward through stacked layers, loss measurement, gradient computation via the
chain rule, parameter update — is identical to what you built here. When your Fashion-MNIST run
plateaus near 87%, that honesty is a feature: you now know the ceiling of a plain MLP before
Block D's convolutions exploit spatial structure. Block B will feel like getting a power tool
after building a house with hand tools: the work is the same shape, but suddenly much faster.

---

## Did You Know?

- **The name "epoch" comes from astronomy**, where it meant a fixed point in time from which
  measurements are taken. In machine learning, an epoch is one complete cycle through the
  training data — a full orbit that returns the model to having seen every example once. The
  number of epochs is how many orbits the optimiser takes through the data.

- **Fashion-MNIST was created specifically because original MNIST had become too easy.**
  By 2017, plain MLPs achieved >97% accuracy, CNNs reached >99.5%, and the dataset no longer
  distinguished between good and bad architectures. Fashion-MNIST, at ~87% MLP and ~93% CNN,
  restored the dataset's value as a meaningful benchmark (Xiao et al., 2017).

- **The softmax-CE gradient `p − y` is sometimes called the "beautiful gradient."**
  The cancellation of the softmax derivative with the cross-entropy derivative eliminates
  terms that would otherwise make the backward pass through softmax numerically unstable.
  This is not a coincidence — the softmax and cross-entropy are a matched pair designed for
  exactly this cancellation, which is why every deep-learning textbook treats them
  together rather than separately.

- **SGD with a fixed learning rate converges for convex problems but has no such guarantee
  for neural networks.** The loss landscape of even a small MLP is non-convex with many local
  minima, saddle points, and flat regions. That SGD still finds good solutions is an empirical
  fact that took the field years to trust and even longer to partially explain. It works in
  practice; the theory of *why* it works is still an active research area.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Updating weights mid-backpropagation | Later layers use stale weights from earlier layers, producing silently wrong gradients | Accumulate all gradients first (backward pass), then update all weights |
| Forgetting to normalise pixel data | Raw values 0–255 cause enormous pre-activations, logit overflow, and NaN loss | Divide by 255.0 before training; verify initial loss ≈ ln(num_classes) |
| Computing accuracy on softmax probabilities instead of one-hot | `(probs > 0.5)` on 10-class softmax produces a 10-boolean vector, not a class index | Use `logits.argmax(axis=1)` compared against integer labels or one-hot argmax |
| Using training accuracy as the only metric | Overfitting is invisible if you never evaluate on held-out data | Maintain a validation set; compute val_loss and val_acc every epoch |
| Assuming more epochs always helps | After the validation loss plateaus, further training wastes computation and may hurt generalisation | Monitor the val_loss curve; stop when it stops decreasing |
| Not shuffling between epochs | The model learns to exploit the fixed order, memorising sequence rather than class patterns | `rng.permutation(N)` at the start of every epoch |
| Using `eps=0` in cross-entropy | `log(0) = −inf`, which produces NaN in the loss and kills the run | Floor probabilities at `1e-12` before taking the log |

---

## Quiz

1. **The training loop has four stages per mini-batch: forward, loss, backward, update. Why must the backward pass for all layers complete before any layer's weights are updated?**

   <details>
   <summary>Answer</summary>
   The gradient flowing to earlier layers, `dX[l] = dZ[l] @ W[l].T`, depends on the later layers' weight matrices `W[l]`, which must remain their *original* (pre-update) values throughout the entire backward pass. The chain rule assumes the same computational graph in both directions — the weights that produced the forward activations the loss was computed on. Therefore all parameter gradients must be computed (full backward) before any weight is updated; updating any layer mid-backward makes the gradients inconsistent with that forward graph. This bug can survive many training runs without detection because the gradients still point roughly in the right direction — they are just slightly wrong, which manifests as slower convergence or a higher final loss rather than an obvious crash.
   </details>

2. **You train a Fashion-MNIST MLP and observe these curves: train_loss decreases from 2.3 to 0.15, train_acc increases from 0.10 to 0.96, val_loss decreases from 2.3 to 0.60 then increases to 0.75, val_acc plateaus at 0.78. What is happening, and what should you do?**

   <details>
   <summary>Answer</summary>
   The model is overfitting. The training accuracy of 0.96 and training loss of 0.15 show the model has essentially memorised the training set. The validation loss increasing from 0.60 to 0.75 (while training loss still decreases) is the classic signature: the model is learning patterns that exist only in the training data and do not generalise. To fix this: (a) apply early stopping — checkpoint the model at the epoch where val_loss was minimised (~0.60); (b) add regularisation (weight decay or dropout, covered in Block B); (c) reduce model capacity (fewer hidden units); or (d) increase training data size. For a plain MLP on Fashion-MNIST with 50k training samples, overfitting this severe suggests the model has too many parameters relative to the data — check that you are using the full 50k training set and that your architecture is not wider than ~512 hidden units.
   </details>

3. **What is the expected value of the softmax cross-entropy loss at initialisation for a perfectly balanced 10-class classification problem, and why?**

   <details>
   <summary>Answer</summary>
   At random initialisation with small weights, the logits are approximately zero-mean with small variance. The softmax of near-zero logits produces approximately uniform probabilities: `p[k] ≈ 1/10 = 0.1` for each class `k`. The cross-entropy for a correct label is `−log(0.1) = log(10) ≈ 2.3026`. Since each sample's loss is approximately `−log(1/K) = log(K)`, the average loss over the dataset is also `log(K)`. For 10 balanced classes, the expected initial loss is therefore `ln(10) ≈ 2.3026`. If your initial loss is substantially different, something is wrong — 0.0 means the loss is being computed on collapsed predictions, NaN means numerical overflow, and values far from `ln(K)` suggest a bug in the softmax, the normalisation, or the weight initialisation.
   </details>

4. **You change the learning rate from 0.01 to 1.0 and the loss immediately becomes NaN on the next iteration. What sequence of numerical events caused this?**

   <details>
   <summary>Answer</summary>
   The sequence: (1) The gradient step `W -= 1.0 * dW` is 100× larger than before, pushing weight magnitudes up sharply. (2) The next forward pass computes `Z = X @ W + b` with these enlarged weights, producing pre-activation values in the hundreds or thousands until `Z` overflows to `inf` (or `NaN`). (3) Those `inf` logits poison even the max-subtracted softmax from Part 1.3: `exp(inf − inf) = NaN`, so the loss becomes `NaN`. The stable softmax prevents overflow *inside* the softmax on finite logits; it does not save you once the logits themselves are `inf`. (4) Subsequent gradient computations on `inf` or `NaN` values propagate NaN through the entire parameter set, and the run is unrecoverable. The fix is reducing the learning rate by a factor of 10 and restarting from fresh initialisation.
   </details>

5. **In a controlled learning-rate and batch-size sensitivity experiment on Fashion-MNIST, what should you observe in training and validation loss when either hyperparameter is poorly chosen?**

   <details>
   <summary>Answer</summary>
   A learning rate that is too high produces NaN loss or wild oscillation within the first few epochs — the same logits-overflow sequence as the XOR sweep in Part 5.1. A learning rate that is too low yields a flat validation curve: loss decreases glacially and accuracy may stay near random guessing after ten epochs. Batch size changes the noise in each gradient step: very small batches (e.g., 8) create jagged loss curves but can generalise well; very large batches smooth the curve but may converge to sharper minima with worse validation accuracy (Keskar et al., 2017). A well-tuned pair shows training and validation loss decreasing together with a small gap; a poorly tuned pair shows divergence, plateau, or NaN. The Hands-On Exercise step 2 is exactly this controlled experiment — record validation accuracy at each learning rate and identify the failure threshold.
   </details>

6. **The two-moons generator samples points along half-circles with Gaussian noise. Why is this a stronger test of your MLP than XOR alone?**

   <details>
   <summary>Answer</summary>
   XOR has only four fixed points with no noise — you can memorise coordinates without learning a general decision boundary. Two-moons adds continuous variation along curved manifolds plus stochastic jitter, so the model must learn a nonlinear boundary that generalises to held-out points, not just four corners of the unit square. The train/validation split makes overfitting visible: a model that memorises training noise will show rising validation loss while training loss falls. Architecturally, both problems need a hidden layer, but two-moons teaches the debugging habits — splits, curves, batch training — that Fashion-MNIST demands at scale.
   </details>

7. **After loading Fashion-MNIST, the module divides pixel values by 255.0 before training. What breaks if you skip normalisation?**

   <details>
   <summary>Answer</summary>
   Raw pixels in `[0, 255]` produce pre-activations orders of magnitude larger than He-initialised weights expect: `Z = X @ W + b` scales with input magnitude, so pre-activations and logits can overflow to `inf`, poisoning even the max-subtracted softmax (`inf − inf = NaN`). Initial loss will be far from `ln(10) ≈ 2.30`, often in the tens or NaN immediately. Dividing by 255 maps inputs to `[0, 1]`, keeping activations and gradients in the stable regime your A4 clipping and A5 log-sum-exp tricks were designed for. This is the same preprocessing recipe PyTorch tutorials apply before `model.forward()` on image tensors.
   </details>

8. **What does the reusable `train()` helper in Part 8 consolidate compared to the raw loop in Part 1?**

   <details>
   <summary>Answer</summary>
   `train()` packages the canonical cycle — shuffle, mini-batch iteration, forward, `loss_fn`, backward, SGD update, epoch loss/accuracy aggregation, optional validation forward pass — into one callable with a `history` dict return value. The `MLP` wrapper adds sequential `forward()`/`backward()` and a `parameters()` generator so the update step does not hard-code layer lists. You pass `loss_fn=softmax_cross_entropy` or `binary_cross_entropy`, making the same helper work for two-moons, Fashion-MNIST, and XOR (with appropriate output heads); `_batch_correct()` uses sigmoid thresholding for single-logit binary and argmax for multiclass. Pass a seeded `rng` for reproducible runs. Nothing new is learned mathematically; the abstraction removes copy-paste bugs when you run hyperparameter sweeps in the Hands-On Exercise and mirrors how Block B separates `model`, `criterion`, and `optimizer.step()`.
   </details>

---

## Hands-On Exercise

Extend the Fashion-MNIST lab in three targeted ways to deepen your understanding of the
training pipeline, using the reusable `train()` helper from Part 8 for every experiment rather
than duplicating the raw loop from Part 1.

1. **Add a second hidden layer.** Replace the `784 → 256 → 10` architecture with
   `784 → 256 → 128 → 10`. Train for 20 epochs with the same hyperparameters (`lr=0.05`,
   `batch_size=64`). Compare test accuracy with the single-hidden-layer baseline and note
   whether the extra depth buys a meaningful gain on Fashion-MNIST.

2. **Run a learning-rate sensitivity sweep at scale.** Train the single-hidden-layer
   `784 → 256 → 10` architecture for 10 epochs each at `lr ∈ {0.01, 0.05, 0.1, 0.5, 1.0}`.
   Record final validation accuracy for each rate, identify the best value, and note the
   threshold where training becomes unstable (NaN loss or accuracy below random guessing).

3. **Plot a confusion matrix on the test set.** After training your best model, compute
   predicted classes and build a 10×10 confusion matrix (`np.zeros((10, 10), dtype=int)` plus
   a loop, or `np.histogram2d`). Identify the two most-confused class pairs (often shirt vs.
   t-shirt) and explain in one sentence why a flat MLP lacks spatial priors to separate them.

Before the full-dataset runs, confirm your pipeline can **overfit a single batch** from Part 7.1
to near-zero loss — if that sanity check fails, fix backward or update bugs before scaling up.

Track progress with these checkboxes:

- [ ] Two-hidden-layer `784 → 256 → 128 → 10` model trains without NaN and matches or beats the single-layer test accuracy.
- [ ] Learning-rate sensitivity sweep at `lr ∈ {0.01, 0.05, 0.1, 0.5, 1.0}` identifies a clear optimum and a failure threshold on validation accuracy.
- [ ] Confusion matrix covers all 10,000 test samples and names the most-confused class pair with a plausible explanation.
- [ ] Every experiment uses the reusable `train()` helper from Part 8 rather than the raw Part 1 loop.

After implementing the exercise, verify numerically:

```python
# After implementing the exercise, verify:
assert model.layers[0].W.shape[0] == 784
assert model.layers[-1].W.shape[1] == 10
assert test_acc > 0.80, f"Test accuracy {test_acc:.3f} is below 80% — check normalisation and lr"
assert confusion_matrix.sum() == len(y_test), "Confusion matrix must cover all test samples"
```

---

## Key Takeaways

- The training loop — forward, loss, backward, update, repeated over mini-batches and epochs — is the same pattern in every deep-learning framework. Understanding it in NumPy makes every framework call thereafter transparent rather than magical.

- XOR is solvable by an MLP with one hidden layer because the hidden layer transforms the input into a representation where the classes become linearly separable. You proved it could not be solved without that hidden layer in A2; you proved it can be solved with one in this module. That closed loop is the single most important demonstration of why depth matters.

- The two-moons dataset demonstrates generalisation: a curved decision boundary learned from noisy samples, evaluated on held-out validation data. The train/validation split is the learner's first honest signal of overfitting.

- Fashion-MNIST shows that a from-scratch MLP can reach ~85% test accuracy on a real image classification task. The accuracy ceiling for a plain MLP without convolutions is real and honest — Block D will push past it with CNNs.

- Learning rate is the master hyperparameter. Too high → NaN. Too low → glacial progress. The safe range is empirically discoverable in minutes with a small sweep.

- The `train()` function you wrote wraps the entire Block A arc into a reusable interface. It is not PyTorch, but it contains exactly the same computation that PyTorch orchestrates with automatic differentiation. When you encounter `model.forward()`, `loss.backward()`, and `optimizer.step()` in Block B, you will know what each call is doing — because you wrote the NumPy version yourself.

---

## Sources

- Xiao, H., Rasul, K., & Vollgraf, R. (2017). "Fashion-MNIST: a Novel Image Dataset for Benchmarking Machine Learning Algorithms." arXiv:1708.07747. https://arxiv.org/abs/1708.07747
- Zhang, A., Lipton, Z. C., Li, M., & Smola, A. J. (2023). "Dive into Deep Learning" — MLP implementation from scratch. https://d2l.ai/chapter_multilayer-perceptrons/mlp-scratch.html
- Zhang et al. (2023). "Dive into Deep Learning" — MLP implementation with frameworks. https://d2l.ai/chapter_multilayer-perceptrons/mlp-implementation.html
- Zhang et al. (2023). "Dive into Deep Learning" — Image classification dataset loading. https://d2l.ai/chapter_linear-classification/image-classification-dataset.html
- Karpathy, A. (2020). "micrograd" — A tiny scalar-valued autograd engine. https://github.com/karpathy/micrograd
- Karpathy, A. (2022). "makemore" — A character-level language model. https://github.com/karpathy/makemore
- Stanford CS231n: Neural Networks Part 1 (architecture and activations). https://cs231n.github.io/neural-networks-1/
- Stanford CS231n: Neural Networks Part 3 (training and babysitting). https://cs231n.github.io/neural-networks-3/
- PyTorch Tutorials: Learn the Basics (Block B forward-reference for `forward` / `backward` / `step`). https://pytorch.org/tutorials/beginner/basics/intro.html
- Goodfellow, I., Bengio, Y., & Courville, A. (2016). *Deep Learning*, Chapter 8: Optimization for Training Deep Models. MIT Press. https://www.deeplearningbook.org/
- Keskar, N. S., et al. (2017). "On Large-Batch Training for Deep Learning: Generalization Gap and Sharp Minima." ICLR 2017. https://arxiv.org/abs/1609.04836
- He, K., Zhang, X., Ren, S., & Sun, J. (2015). "Delving Deep into Rectifiers: Surpassing Human-Level Performance on ImageNet Classification." ICCV 2015. https://arxiv.org/abs/1502.01852

---

## Learner check

> The training loop is forward → loss → backward → SGD step repeated over shuffled mini-batches across epochs; watch the loss curve for overfitting (train falls, val rises) and NaN (lr too high or missing normalisation) — see [Tiny NumPy NN Lab](/ai-ml-engineering/deep-learning/module-1.1.7-tiny-numpy-nn-lab/).

---

## Next Module

Block A is complete. Proceed to [Block B: PyTorch Fundamentals](/ai-ml-engineering/deep-learning/module-1.2-pytorch-fundamentals/), where you will rebuild the same training loop using automatic differentiation, GPU acceleration, and the optimiser library — and discover that the underlying computation is exactly what you built here.
