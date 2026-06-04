---
title: "Neural Network Math Warm-Up"
slug: ai-ml-engineering/deep-learning/module-1.1.1-nn-math-warmup
sidebar:
  order: 1002.1
---

> **AI/ML Engineering Track** | Complexity: `[MEDIUM]` | Time: 5–6 hours | **Prerequisites:** [NumPy, Pandas & Data Tooling for ML](/ai-ml-engineering/deep-learning/module-1.1-numpy-pandas-data-tooling/)

When Andrej Karpathy taught Stanford’s CS231n course, the idea at the heart of a neural network was almost insultingly simple: a matrix multiply, a bias vector, and a squashing function. Students who had only used high-level frameworks expected magic; what they got was linear algebra with a nonlinearity sprinkled on top. That honesty is why the “from scratch” track in this curriculum exists. Before PyTorch autograd hides the chain rule behind `loss.backward()`, you need the same fluency Karpathy assumed: shapes that line up, broadcasting that does what you intend, and gradients you can sanity-check with a few lines of NumPy.

This module is the first step in **Block A — Foundations from scratch**. Every later module in the block extends a single file you keep on disk, `nn.py`, the way Karpathy’s [micrograd](https://github.com/karpathy/micrograd) and [makemore](https://github.com/karpathy/makemore) courses grow one tiny engine across lessons. By the end of Block A you will train a small network in pure NumPy that **you** assembled piece by piece. Here we only lay the mathematical pavement: tensors, broadcasting, matrix multiplication, finite-difference gradients, the chain rule, and the gradient vector as the compass for learning.

You might wonder why a cloud-native curriculum spends thousands of words on NumPy before Kubernetes manifests for GPUs. The reason is operational: the engineers who keep training clusters healthy are the same people who must read loss curves, inspect tensor shapes in logs, and decide whether a NaN came from data or from a wrong reduction axis. Math warm-up is not academic detour; it is the debugging interface for the hardware you will schedule later in the MLOps modules.

---

## Learning Outcomes

By the end of this module, you will be able to implement batched linear transforms with explicit shape comments, debug broadcasting and matmul errors by reading NumPy’s alignment rules, derive numerical gradients with centered finite differences, apply the chain rule to composed functions with numeric confirmation, and explain why optimization steps move opposite the gradient toward later gradient-descent modules.

- **Implement** batched linear transforms `Y = X @ W + b` in NumPy with explicit shape comments and dtype choices appropriate for neural network training.
- **Debug** broadcasting and matmul shape errors by reading NumPy’s alignment rules instead of guessing with `reshape` until something runs.
- **Derive** numerical gradients with centered finite differences and use them as a fallback verifier before trusting symbolic derivatives.
- **Apply** the chain rule to composed scalar functions and confirm symbolic and numerical results agree on a worked example.
- **Explain** why optimization steps move opposite the gradient, setting up gradient descent in the next modules of the from-scratch arc.

---

## Why This Module Matters

Neural networks are not a separate branch of mathematics; they are a disciplined way of chaining cheap, repeated operations—mostly matrix multiplies and element-wise nonlinearities—so that a loss function can be minimized. When a training job blows up, the failure is almost never “the neural net spirit was weak.” It is a tensor with shape `(batch, features)` treated as `(features, batch)`, a bias broadcast across the wrong axis, or a gradient with the wrong sign. Frameworks surface these mistakes as cryptic `RuntimeError` messages; engineers who understand the underlying layout fix them in minutes.

If you completed [NumPy, Pandas & Data Tooling](/ai-ml-engineering/deep-learning/module-1.1-numpy-pandas-data-tooling/), you already know arrays, dtypes, and vectorization. This module narrows the lens to the **idioms deep learning reuses everywhere**: samples along axis 0, features along axis 1, parameters stored as matrices that map feature dimension to hidden dimension, and gradients shaped like the parameters they update. PyTorch appears later in the track; Block A stays NumPy-first so nothing autodiffs away the learning.

The habits you build here—comment the shapes, check a gradient numerically, treat the chain rule as bookkeeping—are the same habits that make Module 1.7’s autograd-from-scratch exercise feel inevitable rather than magical. You are not “warming up” for a trivia quiz; you are installing the mental compiler the rest of the from-scratch arc will call on every week.

Engineering teams sometimes onboard practitioners who can tune Hugging Face pipelines but cannot explain why a loss tensor has shape `()` while logits have shape `(batch, classes)`. That gap shows up during incident response: the on-call engineer needs five minutes to notice a softmax applied along axis 1 instead of axis 0. This module is insurance against becoming that blind spot on your team. You will still use frameworks for production scale; you will also be able to open a NumPy REPL and reproduce the failing slice of math.

---

## Part 1: Tensors as NumPy Arrays

In machine learning literature, **tensor** is a fancy word for an array with a defined shape and dtype. NumPy gives you scalars (0-D), vectors (1-D), matrices (2-D), and batches (3-D and up) without changing libraries. A single floating-point weight is `np.array(0.5)` with shape `()`; a mini-batch of 32 RGB images might be `(32, 3, 224, 224)` in convolutional models. For fully connected layers—the focus of Block A—think in terms of **2-D batches**: rows are independent examples, columns are features. When a paper writes \(X \in \mathbb{R}^{n \times d}\), that is exactly your `X` array: `n` rows, `d` columns. Transposing swaps the meaning of those axes, which is why we nag you to write shapes in comments before you `@`.

The jump from spreadsheets to NumPy is mostly about naming axes consistently. Excel hides batching inside implicit ranges; NumPy forces you to materialize the batch dimension as the first index so vectorization can see all samples at once. Once that click happens, reading PyTorch `Tensor` documentation later is straightforward because the same convention survives: leading dimension is batch unless the API explicitly says otherwise for weights. Weight matrices are not batched the same way activations are; `W` has shape `(d_in, d_out)` without a batch axis because parameters are shared across examples.

```python
import numpy as np

# Scalar, vector, matrix, batch-of-vectors
scalar = np.array(3.0)                 # shape ()
vector = np.array([1.0, 2.0, 3.0])       # shape (3,)
matrix = np.array([[1., 2.], [3., 4.]])  # shape (2, 2)
batch = np.random.randn(8, 4)            # shape (8, 4)  -> 8 samples, 4 features each
```

**Axis conventions** matter because NumPy reductions and broadcasts refer to axis indices. For a batch matrix `X` with shape `(n, d)`, `X.mean(axis=0)` averages over samples and returns one mean per feature; `X.mean(axis=1)` averages within each sample across features. Neural code almost always keeps **axis 0 as batch** so `X[i]` is the `i`-th example. Libraries like PyTorch default to the same layout for tabular and MLP data, which is why transposing without documenting it is a recurring source of silent bugs.

**dtype** chooses memory and numerical behavior. `float64` is the NumPy default; many neural nets run in `float32` because it halves memory bandwidth and matches GPU tensor cores. You can cast explicitly: `X = X.astype(np.float32)`. For this module’s tiny examples, either dtype is fine; for training loops you will standardize on `float32` unless you have a numerical reason not to. Integer dtypes appear for labels (`int64` class indices) but never for learnable weights.

```python
rng = np.random.default_rng(0)
X = rng.standard_normal((5, 3), dtype=np.float32)  # 5 samples, 3 features
W = rng.standard_normal((3, 2), dtype=np.float32)  # maps 3 -> 2
print(X.shape, W.shape, X.dtype)
```

**Worked shape check:** If `X` is `(5, 3)` and `W` is `(3, 2)`, then `X @ W` is `(5, 2)`. Each row of `X` is a dot product with each column of `W`. Comment shapes in every block you write for Block A; future-you will treat `(d_out, d_in)` versus `(d_in, d_out)` transposes as the prime suspect when loss goes flat.

**Memory layout intuition:** NumPy stores `float32` matrices in row-major order (C contiguous): row 0’s entries sit next to each other in RAM, then row 1, and so on. BLAS libraries exploit that layout when multiplying batches. You rarely manipulate strides directly in Block A, but you will see `order='C'` in interoperability guides when passing arrays to other runtimes. Contiguity matters when a stray `.T` returns a view with awkward strides and a subsequent `reshape` copies silently.

**Labels versus features:** Supervised learning separates `X` (inputs) from `y` (targets). For classification, `y` might be shape `(batch,)` integer class ids; for regression, `(batch, 1)` floats. Never concatenate labels into `X` “for convenience” before a train/test split—that recreates the leakage patterns you fixed in the scikit-learn track. Keep a mental picture of two arrays walking side by side through the pipeline with identical batch dimension.

**Random seeds:** `np.random.default_rng(seed)` makes notebooks reproducible. Neural training has stochasticity from data shuffling and dropout later; for this module’s deterministic arrays, fixing the seed lets you diff outputs after refactors. Document the seed in exercises so a classmate can reproduce your numeric gradient check byte-for-byte.

**Views versus copies:** Slicing `X[0:10]` often returns a view sharing memory with `X`; assigning into the slice mutates the parent. Reshaping with `-1` can return a view when strides allow it. When a tutorial says “clone before modifying,” it is protecting you from poisoning cached activations during backprop experiments. Use `X.copy()` when you intentionally perturb a batch for finite differences while keeping the original intact.

**Inspecting arrays in the REPL:** `X.shape`, `X.dtype`, `X.strides`, and `np.isfortran(X)` are quick diagnostics when interoperating with C extensions. Most Block A code stays C-contiguous float32 batches; if a foreign library returns Fortran-ordered arrays, `np.ascontiguousarray` avoids silent performance cliffs. You will not need strides daily, but knowing they exist explains occasional “why is this transpose slow?” questions on forums.

---

## Part 2: Broadcasting — Rules and Failure Modes

Broadcasting lets NumPy apply element-wise operations between arrays of different shapes without manual tiling. The rules, stated in [NumPy’s broadcasting documentation](https://numpy.org/doc/stable/user/basics.broadcasting.html), are easy to internalize if you always align shapes on the right: compare the last dimension first, then move left. Two trailing dimensions are compatible when each pair is equal, or when one side is `1`, or when one array is missing that axis entirely (NumPy treats missing leading axes as length 1). If any pair disagrees without a `1` to stretch, NumPy raises `ValueError: operands could not be broadcast together` instead of guessing.

Think of broadcasting as stretching singleton axes just long enough for element-wise operations to line up, never as a substitute for matrix multiply. Students who confuse `A * B` with `A @ B` often had broadcasting accidentally succeed on a lucky shape once, reinforcing the wrong mental model. When you mean linear layer math, type `@` explicitly and say “matmul” aloud while coding.

```python
a = np.array([[1.], [2.], [3.]])   # shape (3, 1)
b = np.array([10., 20.])           # shape (2,)
# (3,1) + (2,) -> (3,2): b is stretched down each column
print(a + b)
```

**Bias addition** is the pattern you will live in. If activations `H` have shape `(batch, out_features)` and bias `b` has shape `(out_features,)`, then `H + b` broadcasts `b` across rows:

```python
batch, out = 4, 3
H = np.ones((batch, out))
b = np.array([0.1, 0.2, 0.3])
print((H + b).shape)  # (4, 3)
```

**Classic bug:** bias must broadcast along the **feature** axis (last axis). Shape `(out_features,)` or `(1, out_features)` adds correctly to `(batch, out_features)`. Shape `(out_features, 1)` does **not** broadcast to `(batch, out_features)` in general—NumPy aligns trailing dims first, so `(out, 1)` versus `(batch, out)` compares `1` against `out` on the last axis (compatible: the `1` stretches across the features) and then `out` against `batch` on the first axis (compatible only when they are equal). So the add "succeeds" only in the degenerate case `batch == out_features`, and even then it spreads a single value per row across all features instead of one bias per feature. Transposing `H` to `(out, batch)` without noticing is a separate way to turn a harmless bias add into garbage. When you see a broadcast error, print `arr.shape` for **every** operand; do not chain `.reshape(-1)` until the error disappears.

```python
# Intentional mismatch: bias length 7 vs feature dimension 5
X = np.ones((8, 5))
b_wrong = np.ones((7,))
try:
    X + b_wrong
except ValueError as e:
    print("caught:", e)  # operands could not be broadcast together ... (8, 5) (7,)
```

**Reading the error:** NumPy’s message ends with the two shapes it could not reconcile. Train yourself to map those tuples back to batch/feature language. That single skill prevents hours of debugging distributed training jobs where only one rank had a transposed weight shard.

**Expanding dimensions explicitly:** When you need outer-product style behavior, `np.newaxis` (or `None`) documents intent better than mysterious reshapes. If `u` has shape `(3,)` and `v` has shape `(4,)`, then `u[:, None] * v[None, :]` yields a `(3, 4)` grid of pairwise products. That pattern appears in attention score construction later; broadcasting is not only about adding biases. Practicing small grids now prevents you from treating every rank-2 tensor as “probably a batch of vectors” when it is actually a matrix of pairwise interactions.

**Normalization broadcasts:** Layer normalization subtracts means and divides by standard deviations per feature or per sample depending on design. Those operations are element-wise after statistics are computed with `keepdims=True`, which leaves length-1 axes that broadcast back to the original shape. When you implement normalization from scratch in later modules, you will use `mean = X.mean(axis=..., keepdims=True)` precisely so subtraction does not accidentally collapse the batch dimension you still need for the next matmul.

---

## Part 3: Dot Products, `matmul`, and the Dense Layer Primitive

The **dot product** measures how aligned two vectors are: `np.dot(u, v) == sum(u_i * v_i)`. Geometrically, if vectors are long and point in similar directions, the dot product is large; orthogonal vectors yield zero. A fully connected layer computes many dot products at once by stacking weights as a matrix.

For one sample row vector `x` with shape `(d_in,)` and weight matrix `W` with shape `(d_in, d_out)`, the linear output is `x @ W` with shape `(d_out,)`. For a batch `X` with shape `(batch, d_in)`, right-multiplying by `W` applies the same weight matrix to every sample:

```python
batch, d_in, d_out = 6, 4, 2
rng = np.random.default_rng(1)
X = rng.standard_normal((batch, d_in))
W = rng.standard_normal((d_in, d_out))
b = rng.standard_normal((d_out,))
Y = X @ W + b
assert Y.shape == (batch, d_out)
print(Y[0])  # first sample's two outputs
```

**`@` versus `np.dot` versus `*`:** The star operator is element-wise multiplication and requires broadcast-compatible shapes. `np.dot` and `@` generalize to stacks, but for 2-D batch work prefer `@` (Python 3.5+) because it reads as matrix multiply. With batches `(b, m, k) @ (b, k, n)` you get `(b, m, n)`; without the batch dimension NumPy follows linear algebra rules you already use in spreadsheets.

**Geometric meaning of a layer:** Each column of `W` is a template over input features. The dot product between `x` and that column measures how strongly the sample activates that template. Adding bias shifts the activation threshold per template. Nonlinearities applied element-wise afterward (ReLU, sigmoid) are separate; the linear block is always this affine map.

```python
# Tiny numeric forward pass by hand
x = np.array([1.0, -2.0, 0.5])
W = np.array([[0.2, 1.0],
              [0.0, -0.5],
              [1.0, 1.0]])
b = np.array([0.1, -0.1])
y = x @ W + b
print("manual:", y)
print("einsum equivalent:", np.einsum('i,ij->j', x, W) + b)
```

Keep a cheat sheet on your desk: **samples × features @ features × outputs → samples × outputs**. Every Block A module that builds layers will reuse that string.

**Batching as a design choice:** Frameworks could loop over samples with a Python `for` and call a single-sample multiply each time. They do not, because looping in Python destroys throughput. Vectorization turns the inner loop into one BLAS call that uses SIMD instructions on your CPU (and later, tensor cores on a GPU). When you read performance guides that say “increase batch size until memory is full,” they are really saying “give the matmul a taller `batch` dimension so the hardware spends less time idle.” That is why `(32, 784) @ (784, 128)` is the canonical picture for an MNIST hidden layer: 32 simultaneous dot products, not one dot product executed thirty-two times with extra Python overhead.

**Parameter layout:** Some textbooks draw \(W\) with shape `(d_out, d_in)` and use `W @ x`. NumPy code in this track keeps weights as `(d_in, d_out)` so `X @ W` matches the batch-on-top layout. Neither convention is “wrong,” but mixing them inside one repository is. Pick one, document it in `nn.py`, and grep for transposes when loss stops decreasing.

**Einsum as readable documentation:** The `np.einsum` API can express the same multiply with explicit indices: `np.einsum('bi,io->bo', X, W)` reads as “batch×in times in×out gives batch×out.” You do not need einsum day-to-day, but when a paper uses Einstein summation notation, translating it literally into einsum strings is faster than guessing reshape tricks. Many attention implementations in research code are thin wrappers around einsum for that reason.

**Timing intuition:** A `(1024, 4096) @ (4096, 4096)` multiply dominates transformer FLOPs. You will not implement custom CUDA in Block A, yet you should know why batching and dtype choices matter for cluster schedulers: halving precision roughly halves memory traffic on hardware that supports it, which changes how many pods fit on a node. The math warm-up connects to FinOps and capacity planning, not only to notebooks.

---

## Part 4: Derivatives Without the Calculus Wall

A **derivative** answers a local what-if question: if I nudge the input a tiny amount, how much does the output change? For a function `f(x)`, the slope at `x` is the limit of rise over run as the step goes to zero. You do not need symbolic calculus fluency to work with neural nets—you need intuition plus a numerical safety net.

Define a small `epsilon`, often `1e-5` for float64 and `1e-3` to `1e-4` for float32. The **centered finite difference** approximates the derivative at `x` with the formula “upper f minus lower f, divided by twice epsilon,” which is the symmetric slope between two nearby samples. Written in code you will use `(f(x+eps) - f(x-eps)) / (2*eps)`; written on paper the same idea is \(f'(x) \approx (f(x+\varepsilon)-f(x-\varepsilon))/(2\varepsilon)\). Centering matters because asymmetric steps bias the estimate when curvature is noticeable.

```python
def numerical_grad(f, x, eps=1e-5):
    """f: array -> scalar float; grad same shape as x."""
    x = np.array(x, dtype=float, copy=True)  # copy so finite-diff perturbations never mutate the caller's array
    grad = np.zeros_like(x)
    it = np.nditer(x, flags=['multi_index'], op_flags=['readwrite'])
    while not it.finished:
        idx = it.multi_index
        old = x[idx]
        x[idx] = old + eps
        f_plus = float(f(x))
        x[idx] = old - eps
        f_minus = float(f(x))
        x[idx] = old
        grad[idx] = (f_plus - f_minus) / (2 * eps)
        it.iternext()
    return grad

def f_square(x):
    return (x ** 2).sum()

x0 = np.array([1.0, -2.0, 3.0])
g_num = numerical_grad(f_square, x0)
g_ana = 2 * x0
print("numerical:", g_num)
print("analytic :", g_ana)
print("max abs err:", np.max(np.abs(g_num - g_ana)))
```

For `f(x) = sum(x**2)`, the analytic gradient is `2x`. Agreement within `1e-4` is typical with `eps=1e-5`; if error is huge, your `f` is not smooth enough, `eps` is wrong for your dtype, or `f` mutates global state between calls.

**Slope as rise over run:** If moving from `x=2` to `x=2.001` changes `f` from `4` to about `4.004`, the slope is roughly `0.004 / 0.001 = 4`, matching `2x` at `x=2`. Neural training later asks how each **parameter** nudges the **loss**; finite differences on a scalar loss with respect to every weight become expensive, which is why backpropagation (Modules A6–A7) computes all partial derivatives in one backward pass. Until then, numerical checks on **small** parameter vectors are gold.

**Connecting partial derivatives to matrices:** Suppose loss \(L\) depends on all entries of `W`. The partial derivative \(\partial L / \partial W_{ij}\) asks how \(L\) changes when only coordinate \((i,j)\) moves. The collection of those values forms a matrix the same shape as `W`, which is exactly what `grad_W` must be for a gradient-descent update. When you later derive backprop for `Y = X @ W`, you will recognize `dL/dW = X.T @ (dL/dY)` as “each weight’s sensitivity is a sum over batch examples of input feature times upstream gradient.” Finite checking one entry of `W` in a toy network is how you prove that formula before you trust it in production code.

**Differentiability caveats:** ReLU is not differentiable at zero, yet every framework trains with it. In practice engineers use a convention at \(z=0\) (often treat derivative as 0) because measure-zero kinks rarely harm optimization. For this module’s smooth examples—polynomials, squares, sigmoids—finite differences and calculus agree. When you add ReLU in Module A2, you will still finite-check on points where \(z \neq 0\).

**Sigmoid and tanh previews:** Classification neurons often use \(\sigma(z) = 1/(1+e^{-z})\). The derivative satisfies \(\sigma'(z) = \sigma(z)(1-\sigma(z))\), which is largest near \(z=0\) and tiny when saturated near 0 or 1. That saturation drives vanishing gradients in deep sigmoid nets, one historical reason ReLU gained popularity. You do not need to memorize every activation derivative today, but you should practice deriving one by hand and confirming with `numerical_grad` on a scalar `z`. The pattern “symbolic local rule times upstream gradient” is identical for every activation you will add to `nn.py`.

**Loss scaling:** Multiplying loss by a constant scales all gradients by the same constant, which is why learning rates interact with loss definitions. If you switch from `mean` to `sum` over the same `(batch, d_out)` tensor, gradients grow by a factor of `batch * d_out` unless you retune the learning rate. Document whether your loss uses `mean` or `sum` reduction; mixing conventions across copied code snippets is a classic silent bug when teams merge notebooks into libraries.

---

## Part 5: The Chain Rule by Example

Real networks compose functions: normalize data, affine transform, ReLU, another affine transform, loss. If `y = f(g(x))`, the chain rule says \(\frac{dy}{dx} = \frac{dy}{dg}\cdot\frac{dg}{dx}\). Each step only needs its local derivative multiplied by whatever gradient arrived from above.

**Worked scalar composition:** Let `g(x) = 2x + 1` and `f(g) = g**3` so `y = (2x+1)^3`. Symbolically, `dy/dg = 3*g**2` and `dg/dx = 2`, so `dy/dx = 6*g**2`. At `x=1`, `g=3` and the derivative is `54`. That number is not magic; it is the product of how sensitive the cube is to its inner input and how sensitive the inner affine map is to `x`. Every backprop edge in a deep net is a variant of that multiply, with different local factors stored in the graph.

```python
x = 1.0
g = 2 * x + 1
y = g ** 3
# dy/dg = 3*g**2, dg/dx = 2  -> dy/dx = 3*g**2*2
dy_dx_symbolic = 3 * g ** 2 * 2

def F(vec):
    x = vec[0]
    return (2 * x + 1) ** 3

g_num = numerical_grad(F, np.array([x]))[0]
print("y =", y)
print("symbolic dy/dx:", dy_dx_symbolic)
print("numeric  dy/dx:", g_num)
```

Run the cell: symbolic and numeric values should match within tolerance. That agreement is the contract backpropagation must satisfy on every edge in the graph.

**Multi-path intuition:** If `x` feeds two branches that merge by addition, gradients from each branch **add** at `x`. This is why frameworks accumulate `.grad` with `+=` when a tensor is reused. You will implement that policy manually before you trust PyTorch to do it.

**Vector-valued intermediate:** Real networks rarely end at a scalar until the loss. If `h = g(x)` is vector-valued and `L = f(h)` is scalar, each component of `h` receives \(\partial L / \partial h_i\) from the loss, then backprop into `x` uses the Jacobian of `g`. You do not need full Jacobian machinery today; you need the habit of asking “what is the upstream gradient at this node?” before multiplying by the local derivative. Module A6 will name those upstream gradients `grad_out` in code.

**Worked vector stage:** Let `x = np.array([1.0, 2.0])`, `h = A @ x` with `A = np.array([[1., 0.], [0., 2.]])`, and `L = h.sum()`. Then \(\partial L / \partial h = [1, 1]\) and \(\partial L / \partial x = A.T @ [1, 1] = [1, 2]\). Numeric check:

```python
A = np.array([[1., 0.], [0., 2.]])
def L_of_x(vec):
    h = A @ vec
    return h.sum()
x = np.array([1., 2.])
print(numerical_grad(L_of_x, x))  # should be close to [1., 2.]
```

This is the same pattern as a two-neuron layer without activation: matrix multiply followed by a loss that aggregates outputs.

**Composition stack exercise (pen and paper):** Write `y = log(1 + exp(x))` (softplus) and identify the outer `log` and inner `1+exp(x)` pieces. The chain rule multiplies `1/(1+exp(x))` by `exp(x)`. Run the scalar numeric check in NumPy when you want confirmation. Softplus appears in stable loss formulations; seeing it here demystifies later “log-sum-exp trick” blog posts.

**Backprop depth preview:** A three-layer MLP without activations is just repeated matmuls—still linear. Activations between matmuls break linearity and make each layer’s local Jacobian depend on the current forward values. That is why forward caches exist: backward needs the `z` values before ReLU to know which units were active. You are building the vocabulary to read those implementations without surprise.

---

## Part 6: Gradients, Vectors, and the Direction of Learning

When \(f\) depends on many variables \(\mathbf{x} = (x_1,\dots,x_n)\), the **gradient** \(\nabla f\) collects all partial derivatives into a vector pointing uphill on the loss surface. Steepest **ascent** follows \(+\nabla f\); **descent** follows \(-\nabla f\). Training minimizes loss, so parameter updates in the next modules will look like `param -= learning_rate * grad`.

```python
# Simple 2D bowl: f(x,y) = x^2 + 3*y^2
def f(xy):
    x, y = xy
    return x**2 + 3*y**2

pt = np.array([2.0, 1.0])
g = numerical_grad(f, pt)
print("point", pt, "loss", f(pt))
print("gradient (uphill)", g)
print("one descent step -0.1 * g ->", pt - 0.1 * g, "loss", f(pt - 0.1 * g))
```

At `(2, 1)`, the gradient `(4, 6)` points uphill; stepping opposite reduces the value. Learning rate controls step size; too large steps overshoot, too small steps crawl. Block A will tune that knob once you have a full network and a real loss.

**Jacobian size reality:** For vector-valued functions, the full Jacobian can be enormous. Backpropagation is clever bookkeeping that never materializes that matrix explicitly. Understanding gradients as vectors of partial derivatives explains what autograd stores without requiring you to allocate a gigabyte dense Jacobian for a transformer. The scalar finite-difference loops in this module are intentionally tiny so you respect the cost of numerical checking at scale.

**Stationary points:** Where gradient is zero, first-order updates stop. Not every stationary point is a global minimum; saddle points abound in high dimensions. Later modules discuss momentum and adaptive optimizers that help escape saddles and flat regions. The sign and direction lessons here still apply: if gradient is near zero because of saturation, changing learning rate alone may not help—you may need a different activation or normalization.

**Preview:** Module A2 builds a single neuron; Modules A6–A7 implement backprop and training loops. The sign convention you just verified—move opposite the gradient of the quantity you minimize—is non-negotiable. If loss increases after an update, check whether you added the gradient instead of subtracting it, or whether the loss is defined with the wrong sign.

**Contour intuition without heavy plots:** Imagine walking on a bowl-shaped surface above the `(x, y)` plane. The gradient points toward the steepest uphill direction; following it would climb out of the bowl. Descent walks downhill toward the bottom. Real networks have millions of dimensions, so you cannot sketch the surface, but local linear approximations still hold: near a point, first-order Taylor expansion says the loss changes approximately by `grad · delta`. That is why small learning rates work: you stay inside the neighborhood where linear approximation is meaningful. When linear approximation breaks, you see loss spikes and need smaller steps or better conditioning.

**Interaction with data scale:** Features with wildly different units produce ill-conditioned bowls: one weight direction is steep, another flat. Practitioners standardize inputs (zero mean, unit variance) partly so gradients are not dominated by a single large-magnitude column of `X`. You already practiced scaling in the machine-learning track; here you see the calculus reason it matters for neural nets specifically, because every layer multiplies by those columns again and again.

---

## Part 7: Seeding `nn.py` — Your Growing Micro-Framework

Create a file next to your exercises named `nn.py`. Every Block A module appends to it. Today you only need a numerical gradient helper; later modules add neurons, layers, losses, and optimizers.

```python
# nn.py — Block A cumulative framework (starter from Module 1.1.1)
import numpy as np

def numerical_grad(f, x, eps=1e-5):
    """Centered finite-difference gradient; f must return a scalar loss."""
    x = np.array(x, dtype=float, copy=True)  # copy so finite-diff perturbations never mutate the caller's array
    grad = np.zeros_like(x)
    it = np.nditer(x, flags=['multi_index'], op_flags=['readwrite'])
    while not it.finished:
        idx = it.multi_index
        old = x[idx]
        x[idx] = old + eps
        f_plus = float(f(x))
        x[idx] = old - eps
        f_minus = float(f(x))
        x[idx] = old
        grad[idx] = (f_plus - f_minus) / (2 * eps)
        it.iternext()
    return grad
```

Keep the API boring on purpose. Karpathy’s teaching stacks work because each lecture mutates the same small codebase. When Module 1.1.2 introduces a `Neuron` class, you will import it from this file and test forward passes with the broadcasting rules from Part 2.

**Forward look:** [The Neuron & Perceptron from Scratch](/ai-ml-engineering/deep-learning/module-1.1.2-neuron-from-scratch/) implements `z = w·x + b` with a nonlinearity and shows why XOR needs hidden units. Re-read your `nn.py` before starting that module; you should recognize every line as either array plumbing or a gradient check you already trust.

**Testing discipline:** Add a `if __name__ == "__main__":` block at the bottom of `nn.py` that runs shape asserts and one gradient check when executed as a script. That pattern becomes your micro test suite until you introduce pytest in later engineering modules. Failing fast on import is preferable to discovering shape bugs ten epochs into a night-long training job.

**Version control:** Commit `nn.py` after each Block A module. Diffing week-over-week shows how your abstractions grow—from scalar finite differences to neurons to full MLPs. That history is also excellent interview material: you can walk an interviewer through a real file you built rather than reciting memorized backprop slides.

**Collaboration tip:** When pairing, one person reads shapes aloud while the other types `@`. It sounds silly and prevents the majority of silent shape bugs. If you disagree, print `X.shape`, `W.shape`, and the proposed output shape on paper before running the cell.

---

## Did You Know?

- **Broadcasting predates the NumPy name:** Numeric, NumPy’s predecessor, already implemented broadcasting via zero strides; see the [NumPy internals note on broadcasting](https://numpy.org/devdocs/dev/internals.code-explanations.html#broadcasting).
- **Finite differences scale poorly but never lie:** A full neural net with millions of parameters cannot be gradient-checked parameter-by-parameter in production, but checking **one layer** or **a few synthesized weights** catches sign and transpose bugs before week-long training runs.
- **The `@` operator was added in Python 3.5** specifically to make matrix multiplication readable; before that, tutorials mixed `np.dot` calls that confused batched stacks.
- **CS231n’s first assignment** is still largely linear algebra fluency; teams interview for framework knowledge, but the course assumes you can implement a vectorized loss gradient by hand.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Transposing `W` silently | `X @ W` becomes `(batch, d_in)` or crashes | Write `(d_in, d_out)` on paper; assert shapes after multiply |
| Using `*` instead of `@` | Element-wise product with wrong broadcast | Use `@` for linear layers; reserve `*` for activations like `relu(z) * mask` |
| Bias shape `(batch, 1)` on wrong axis | Adds per-sample constants across features | Keep bias length `d_out` for shape `(batch, d_out)` |
| `float64` data with `float32` weights | Upcast surprises and slower loops | Cast once at the pipeline boundary |
| `eps` too small for float32 | Numerical gradient noise dominates | Try `1e-3` for float32 checks; tighten only if stable |
| Stepping **with** the gradient on a loss | Loss increases every iteration | Minimize loss: update parameters opposite \(\nabla L\) |
| Skipping finite checks on custom ops | Wrong local derivative poisons all earlier layers | Compare analytic local deriv to `numerical_grad` on scalars |
| Treating gradient shape as free | `grad` must match parameter shape for updates | `assert grad.shape == param.shape` in `nn.py` tests |

---

## Quiz

1. **You have `X` with shape `(32, 10)` and `W` with shape `(10, 4)`. What is the shape of `X @ W + b` if `b` has shape `(4,)`?**
   <details>
   <summary>Answer</summary>
   The product `X @ W` has shape `(32, 4)`. Adding `b` broadcasts across the batch dimension, yielding `(32, 4)`. If `b` were shape `(32, 1)`, you would be adding a per-row scalar across four features—usually wrong for a standard dense layer bias.
   </details>

2. **Why do we prefer centered differences `(f(x+ε)-f(x-ε))/(2ε)` over forward differences `(f(x+ε)-f(x))/ε`?**
   <details>
   <summary>Answer</summary>
   Centered formulas cancel first-order bias terms in the Taylor expansion, giving \(O(\varepsilon^2)\) error instead of \(O(\varepsilon)\) for smooth functions. That means you can pick a moderate `ε` without systematically over- or under-estimating the slope.
   </details>

3. **For `y = (2x+1)^3` at `x=1`, what is `dy/dx` using the chain rule?**
   <details>
   <summary>Answer</summary>
   Here `g=3`, `dy/dg=3g^2=27`, `dg/dx=2`, so `dy/dx=54`. A quick numeric check with `ε=1e-5` should match within ~1e-4.
   </details>

4. **A student writes `relu(z) = z * (z > 0)` using `*` between two vectors. Is that correct?**
   <details>
   <summary>Answer</summary>
   Yes for element-wise ReLU when `z` is an ndarray: `*` is element-wise multiplication and `(z > 0)` broadcasts a boolean mask converted to 0/1. They must not use `@`, which would interpret the operation as a dot product.
   </details>

5. **Gradient of `f(x,y)=x^2+y^2` at `(3, 4)` points which direction for ascent?**
   <details>
   <summary>Answer</summary>
   Partial derivatives are `(2x, 2y) = (6, 8)`, pointing uphill. Descent would move in direction `(-6, -8)` scaled by a learning rate.
   </details>

6. **You finite-check a layer and see error `1e-2` with `eps=1e-8` in float32. What should you try first?**
   <details>
   <summary>Answer</summary>
   Increase `eps` toward `1e-3` or `1e-4`. Tiny `eps` with float32 rounding often dominates the difference quotient; also verify `f` is deterministic and returns a true scalar loss.
   </details>

---

## Hands-On Exercise

Extend your starter `nn.py` so it implements a batched affine layer and a half-mean-squared-error loss, then verify that a manual partial derivative of the loss with respect to one weight matches the centered finite difference from Part 4. Start by implementing `affine(X, W, b)` that returns `X @ W + b` and asserts `X.shape[1] == W.shape[0]` and `b.shape == (W.shape[1],)`. Choose concrete dimensions such as batch four, three input features, and two outputs so you can print intermediate arrays without flooding the terminal.

Define `loss_half_mse(y, target)` to return `0.5 * np.mean((y - target)**2)`, which is a scalar loss. Because `mean` divides by `batch * d_out`, the loss gradient w.r.t. predictions is \(\partial L / \partial Y = (Y - \text{target}) / (batch \cdot d_{out})\) (element-wise, same shape as `Y`). For affine `Y = X @ W + b`, \(\partial L / \partial W_{0,0} = \sum_k X_{k,0}\, (\partial L / \partial Y)_{k,0}\). Compare that closed form to `numerical_grad` on a scalar wrapper that perturbs only `W[0,0]` while holding other weights fixed. They should agree within `1e-3` for float32 or tighter for float64.

- [ ] **Implement:** `affine` passes `assert Y.shape == (batch, d_out)` with `Y = X @ W + b` and dtype you document
- [ ] **Derive:** centered finite difference on `W` matches manual `dL/dW` from backprop preview at least for one element
- [ ] **Apply chain rule:** scalar composition `(2x+1)**3` numeric derivative matches `3*g**2*2` at your chosen `x`
- [ ] **Explain gradient descent:** one sentence states why we step opposite the gradient when minimizing loss
- [ ] **Debug:** you recorded one broadcasting mistake and how printed shapes exposed it

Run verification from your exercise directory with `.venv/bin/python -c "import nn; import numpy as np; X=np.ones((4,3)); W=np.ones((3,2)); b=np.zeros(2); Y=nn.affine(X,W,b); assert Y.shape==(4,2)"` so CI-style smoke checks pass before you move to Module 1.1.2.

---

## Bridging to Module 1.1.2 and the Rest of Block A

Module 1.1.2 introduces the **neuron** as a reusable function: compute affine scores, apply a nonlinearity, compare to labels. Every line in that module should cite shapes you learned here. The perceptron learning rule is a special case of gradient descent on a step activation; you will see the historical algorithm first, then recognize it as a constrained optimizer in modern language. XOR failure is not a party trick; it is the reason hidden layers exist, and your matmul skills explain how hidden units mix features before the final dot product.

When you later read PyTorch documentation for `nn.Linear`, mentally expand it to `X @ W + b` with stored `W.T` if needed. Frameworks sometimes store parameters transposed for BLAS efficiency; that is an implementation detail, not a change to the math story. Your job is to map their storage layout back to the shapes you comment in `nn.py`.

Block A deliberately delays PyTorch so you cannot hide a wrong gradient behind autograd. That discipline feels slow for a week, then pays off when a custom loss in production misbehaves and you are the person who finite-checks the new term before restarting a thousand-GPU job. Treat every future module’s code addition to `nn.py` as a contract: forward shapes documented, backward paths testable, numerical spot checks mandatory for anything you derived by hand.

**Study loop recommendation:** Read one Part, close the markdown, and recreate its code cells from memory in a blank notebook. If you cannot, re-read and type again. Spaced repetition beats skimming thousand-word modules. Pair with the 3Blue1Brown calculus series linked in Sources when a inequality step feels unmotivated; visualization and finite differences reinforce each other.

**Notebook hygiene:** Keep one notebook per module for experiments, but treat `nn.py` as the canonical library. Notebooks are for exploration; duplicated logic in notebook cells drifts from the library and breaks the cumulative arc. When something works in a notebook, paste it into `nn.py`, add a `__main__` check, and delete the duplicate cell.

---

## Key Takeaways

NumPy arrays **are** the tensors of Block A: batch on axis 0, features on axis 1, `float32` for speed, explicit dtypes when mixing integers and floats. Broadcasting implements bias and mask operations only when trailing dimensions align; shape errors are documentation you should read, not annoyances to silence with `reshape(-1)`. Matrix multiply `@` is the dense layer; dot products are its rows. Finite differences turn “trust me, the derivative is \(2x\)” into evidence you can rerun after every custom activation. The chain rule is multiplication along paths and addition at forks. Gradients point uphill; training walks downhill. Your `nn.py` file is the spine of the from-scratch arc—keep it under version control and grow it module by module.

Carry a one-line mantra into Module 1.1.2: **forward is matmul plus nonlinearity; learning is chained local derivatives with a minus sign.** If either half of that sentence feels fuzzy, reopen the matching Part in this module and re-run the numeric cells until the numbers match your expectations. Fluency here is measured by fewer surprises later, not by speed-reading length.

When you feel tempted to skip the numeric cells because “you get the idea,” run them anyway. The idea is cheap; the muscle memory of seeing `54` match `54.0000001` is what keeps you calm when a production loss looks fine but gradients are `nan` because someone multiplied by `*` instead of `@`. That calm is worth the extra ten minutes per Part.

Share your `nn.py` with a peer and ask them to break one shape on purpose; fix it together using only printed `shape` tuples and broadcasting rules from Part 2. Teaching another person is the fastest way to discover which sentences in this module you understood versus which you only recognized while reading. That social check closes the loop before Module 1.1.2 adds neurons on top of your helpers.

Finally, write a five-line “shape diary” for your affine exercise: list `X`, `W`, `b`, `Y`, and `dL/dW` shapes in order. Pin it above your monitor. Every time a future module introduces a new tensor, extend the diary until the habit is automatic and you stop losing afternoons to transposes. Thirty seconds of diary maintenance beats thirty minutes of printf debugging in a cluster job you already submitted. Treat that trade as part of your definition of done for every Block A exercise.

---

## Sources

- [NumPy Quickstart](https://numpy.org/doc/stable/user/quickstart.html) — array creation, shapes, and beginner operations.
- [NumPy Broadcasting](https://numpy.org/doc/stable/user/basics.broadcasting.html) — official broadcasting rules referenced in Part 2.
- [numpy.matmul](https://numpy.org/doc/stable/reference/generated/numpy.matmul.html) — `@` behavior for batched stacks.
- [numpy.dot](https://numpy.org/doc/stable/reference/generated/numpy.dot.html) — dot product generalizations and when they differ from `@`.
- [CS231n: Neural Networks Part 1](https://cs231n.github.io/neural-networks-1/) — neuron as dot product plus bias, activation functions.
- [d2l.ai: Preliminaries — ndarray](https://d2l.ai/chapter_preliminaries/ndarray.html) — tensor viewpoint aligned with deep learning notation.
- [d2l.ai: Preliminaries — calculus](https://d2l.ai/chapter_preliminaries/calculus.html) — derivatives and chain rule intuition.
- [Karpathy: Neural Networks: Zero to Hero (YouTube series)](https://www.youtube.com/playlist?list=PLAqhIrjkxbuWIhTZ1GT45hdvvisJBPKyA) — micrograd/makemore pedagogy for cumulative `nn.py`.
- [micrograd repository](https://github.com/karpathy/micrograd) — minimal autograd engine inspiration for Block A.
- [3Blue1Brown: Essence of calculus](https://www.3blue1brown.com/topics/calculus) — visual intuition for derivatives and chain rule (companion to finite differences).
- [Karpathy: Yes you should understand backprop](https://karpathy.medium.com/yes-you-should-understand-backprop-e2f06eab496b) — why manual gradients still matter for practitioners.

---

## Learner check

> Neural Network Math Warm-Up — Block A entry module; NumPy tensors, broadcasting, matmul, finite-difference gradients, chain rule, starter `nn.py`; precedes The Neuron & Perceptron from Scratch.

---

## Next Module

Continue the from-scratch arc with **[Module 1.1.2: The Neuron & Perceptron from Scratch](/ai-ml-engineering/deep-learning/module-1.1.2-neuron-from-scratch/)**, where you implement `z = w·x + b`, train AND/OR, and meet the XOR limitation that motivates hidden layers.
