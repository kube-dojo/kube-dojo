---
title: "Backprop by Hand for Dense Nets"
slug: ai-ml-engineering/deep-learning/module-1.1.6-backprop-by-hand-dense-nets
sidebar:
  order: 1002.6
---

> **AI/ML Engineering Track** | Complexity: `[COMPLEX]` | Time: 6-8 hours

Hypothetical scenario: You have a tiny NumPy MLP that runs forward perfectly. The logits have shape `(4, 2)`, the softmax probabilities sum to one along `axis=1`, and the loss looks reasonable. You add a few lines of "backprop" copied from memory, run one training step, and the loss rises. You lower the learning rate, try a different seed, and inspect the activations, but the network still behaves like a broken instrument. The bug is not mysterious. One transpose is on the wrong side of a matrix multiply, so the weight gradient is not the derivative of the loss that produced the forward pass.

That is why this module is deliberately slow and exact. In A3 you built the forward pass for dense layers with the convention `Z = X @ W + b`, where `X:(N,d_in)`, `W:(d_in,d_out)`, `b:(d_out,)`, and each row is one sample. In A4 you gave activation functions a `forward()` and `backward(grad_output)` interface. A5, when present, starts the backward pass from the fused softmax-cross-entropy result: the per-sample logit gradient is `p - y`, and the mean-loss version is `(p - y) / N`. A6 stitches those pieces together until your `nn.py` micro-framework can compute every parameter gradient, verify those gradients with finite differences, and take one SGD step that makes a tiny loss go down.

The payoff is not only a working exercise. Backpropagation is reverse-mode automatic differentiation before the automation arrives. A8 will build the graph engine that records operations for you; this module makes you do the recordkeeping by hand once, so the engine later feels inevitable instead of magical. We will never materialize the full Jacobian of a dense layer because doing so would waste memory and obscure the computation. Each operation will instead receive an upstream gradient and return a vector-Jacobian product: the exact gradient signal needed by the previous operation, plus gradients for any parameters owned by the operation.

## Learning Outcomes

By the end of this module, you will be able to:

- **Derive** dense-layer gradients for `Y = X @ W + b` and verify that `dL_dW`, `dL_db`, and `dL_dX` have the exact shapes required by the A3 convention.
- **Implement** activation backward passes as elementwise vector-Jacobian products that multiply the upstream gradient by a local derivative cached during the forward pass.
- **Trace** a multi-layer perceptron backward from `dL_dlogits` through output, hidden activations, dense layers, and finally back to the input.
- **Compare** analytic gradients against centered finite-difference gradients and **debug** common backpropagation failures, including missing transposes, missing bias sums, stale caches, and loss-scaling mismatches.
- **Extend** the cumulative `nn.py` micro-framework with `Layer.backward()`, `MLP.backward()`, and a minimal SGD update without introducing the graph engine reserved for A8.

## Why This Module Matters

Backpropagation is often introduced as a special neural-network algorithm, but its core idea is the ordinary chain rule applied with disciplined bookkeeping. The forward pass builds a sequence of intermediate values: inputs become pre-activations, pre-activations become activations, activations become logits, and logits become a scalar loss. The backward pass walks the same sequence in reverse. At each step, it asks one local question: "Given `dL/doutput`, how does this operation transform that into `dL/dinput`, and if the operation owns parameters, how does it fill `dL/dparams`?" That local question is enough to train deep networks because the chain rule composes all local answers into the global gradient.

Dense networks are the right place to learn this because the shapes are visible. A convolutional layer hides parameter sharing inside sliding windows, attention hides it inside batched matrix products, and PyTorch hides the whole derivative path behind `loss.backward()`. A dense layer has nowhere to hide: `X @ W + b` either lines up or it does not. If `X` is `(N,d_in)` and `W` is `(d_in,d_out)`, then the upstream gradient from later layers must be `(N,d_out)`, the weight gradient must be `(d_in,d_out)`, the bias gradient must be `(d_out,)`, and the gradient sent to the previous layer must be `(N,d_in)`. Those four shapes are the backbone of this module.

The second reason to learn backprop by hand is that gradient bugs are uniquely cruel. A wrong forward pass often crashes with a shape error. A wrong backward pass often returns arrays with plausible shapes and quietly optimizes the wrong function. You might see loss decrease for a few batches, flatten unexpectedly, explode after an update, or fail only for batch sizes greater than one. Finite-difference gradient checking is the antidote: treat the analytic gradient as an engineering claim, perturb every parameter, measure the loss change directly, and compare. When the relative error is below about `1e-5` in float64, you have strong evidence that the backward pass matches the forward computation.

This is also the moment when the cumulative micro-framework becomes a real learning system. A1 gave you finite differences, A2 gave you neurons and perceptron intuition, A3 made the forward pass and cache explicit, A4 made activations interchangeable, and A5 defined the loss gradient that enters the network from the right-hand side. A6 is the hinge: after this module, `nn.py` has enough machinery to move weights in response to a loss. The result will still be tiny compared with PyTorch, but it will contain the same conceptual pieces: parameters, cached intermediates, local backward rules, and an optimizer step.

There is a practical debugging payoff too. Production training failures are often reported as metrics, not as neat math problems. You see loss spikes, dead activations, gradients full of zeros, or model quality that changes when batch size changes. Those symptoms map back to local derivative rules. A missing bias sum produces batch-size-dependent updates. A stale cache differentiates a forward pass that no longer exists. A double `1/N` makes the learning rate seem too small by a factor that changes when you resize batches. When you understand the hand calculation, those operational symptoms become searchable, testable hypotheses instead of vague suspicion.

Backpropagation also teaches a useful engineering humility: a neural network is not trained by "making the bad output smaller" in a vague way. It is trained by measuring how the scalar loss changes with respect to each stored parameter, then moving those parameters a small distance against that measured slope. Every optimizer you will meet later, from momentum to AdamW, starts from those same gradients. If the gradients are wrong, the optimizer is polishing a broken signal. If the gradients are correct, even plain SGD becomes a trustworthy baseline you can reason about before adding more machinery.

## Part 1: The Chain Rule, Scaled Up

Start with the scalar chain rule because it carries the entire idea. Suppose a scalar input `x` flows through two functions: `u = f(x)` and `L = g(u)`. A tiny change in `x` changes `u` by `du/dx`; that changed `u` changes `L` by `dL/du`. The combined sensitivity is their product: `dL/dx = dL/du * du/dx`. If `f(x) = 3x + 2`, `g(u) = u^2`, and `x = 4`, then `u = 14`, `dL/du = 2u = 28`, `du/dx = 3`, and `dL/dx = 84`. The backward pass stores no mystery there; it simply multiplies the upstream gradient `28` by the local derivative `3`.

The vector version keeps the same idea but replaces single slopes with a Jacobian. Let `x` be a vector and let `y = f(x)` be another vector. The Jacobian `J = dy/dx` contains every partial derivative `J[i,j] = dy_i/dx_j`. If a scalar loss `L` depends on `y`, the gradient with respect to `x` is `dL/dx = dL/dy @ J` when gradients are written as row vectors, or `J.T @ dL/dy` when written as column vectors. In NumPy code for this track, we do not usually build either notation explicitly. We keep the gradient array shaped like the value it differentiates, and each operation implements the multiply that sends the gradient backward.

The matrix version adds batching and parameters. A dense layer computes many scalar equations at once: `Y[n,k] = sum_j X[n,j] * W[j,k] + b[k]`. The loss depends on all `Y[n,k]` entries, so the upstream gradient `G = dL_dY` also has one entry per `Y[n,k]`. Backpropagation asks how each entry in `X`, `W`, and `b` influences the scalar loss through all those outputs. The chain rule answers by summing over every path from that entry to the loss. For weights and biases, those paths run across the batch dimension; for input activations, they run across output units in the same sample.

The phrase "reverse topological order" is a precise way to say "walk backward through dependencies." In the forward pass, `Z1` must be computed before `A1`, `A1` before `Z2`, and `Z2` before the loss. The backward pass obeys the reverse dependency order because the gradient with respect to `A1` is not known until the later layer has converted `dL_dZ2` through its dense VJP. If you attempt to compute an early-layer gradient before the later-layer upstream gradient exists, you are missing one factor in the chain rule. This is why `for layer in reversed(self.layers)` is not a coding trick; it is the dependency graph written as a loop.

The shape invariant is equally important: a gradient with respect to a value has the same shape as that value. If `A1` is `(N,d1)`, then `dL_dA1` is `(N,d1)`. If `W2` is `(d1,d2)`, then `dL_dW2` is `(d1,d2)`. This invariant makes it possible to debug the backward pass locally. You never need to ask whether `dL_dW` should have a batch dimension, because `W` has no batch dimension. You never need to ask whether `dL_dX` should be transposed, because the previous layer expects an upstream gradient shaped exactly like its output activation.

Here is a scalar-to-vector numeric check that uses the finite-difference habit from A1. The function is small enough to inspect, but it already follows the pattern we will use for whole networks: compute an analytic gradient, compute a numerical gradient from symmetric perturbations, and compare them.

```python
import numpy as np

def finite_difference_grad(f, x, eps=1e-6):
    """Return numerical gradient of scalar f at array x."""
    x = np.array(x, dtype=np.float64, copy=True)
    grad = np.zeros_like(x)
    for idx in np.ndindex(x.shape):
        old_value = x[idx]
        x[idx] = old_value + eps
        plus = f(x)
        x[idx] = old_value - eps
        minus = f(x)
        x[idx] = old_value
        grad[idx] = (plus - minus) / (2.0 * eps)
    return grad

def f(x):
    u = 3.0 * x + 2.0
    return np.sum(u**2)

x = np.array([4.0, -1.0, 0.5])
u = 3.0 * x + 2.0
analytic = 2.0 * u * 3.0
numeric = finite_difference_grad(f, x)

print("analytic:", analytic)
print("numeric: ", numeric)
print("max abs diff:", np.max(np.abs(analytic - numeric)))
```

The output should show agreement to floating-point precision. This small example is the whole story in miniature: the loss gradient arrives at `u` as `2u`; the local derivative of `u = 3x + 2` is `3`; the product is the gradient for `x`. A neural network is simply a larger directed acyclic computation with arrays instead of scalars, and with matrix multiplies whose local derivative is easier to implement as a vector-Jacobian product than as a giant Jacobian.

## Part 2: Vector-Jacobian Products

A vector-Jacobian product, usually shortened to VJP, is the central engineering abstraction behind reverse-mode autodiff. If an operation computes `y = f(x)` and the later network has already produced an upstream gradient `dL_dy`, the operation does not need to expose its full Jacobian `dy/dx`. It only needs to compute `dL_dx`, the product of the upstream gradient with the local Jacobian. This is memory-efficient because the full Jacobian of a dense layer can be enormous, while the VJP has exactly the same shape as the input activation.

For a layer `Y = X @ W + b` with `X:(N,d_in)` and `Y:(N,d_out)`, the Jacobian of `Y` with respect to `X` would connect every output element to every input element. Written naively, that object has shape `(N,d_out,N,d_in)`. Most of its entries are zero because sample `n` does not depend on sample `m`, but even storing the zeroes would be wasteful. With `N=128`, `d_in=1024`, and `d_out=4096`, the dense Jacobian shape would contain more than 68 billion entries. The VJP `dL_dX = dL_dY @ W.T` contains only `128 * 1024` entries and is exactly what the previous layer needs.

The same logic applies to activations. A ReLU activation maps `Z` to `A` element by element, so its Jacobian is diagonal if flattened. You could build that diagonal matrix, multiply it by the upstream gradient, and discard it immediately. Or you can observe that the VJP is just elementwise multiplication by the local derivative: `dL_dZ = dL_dA * (Z > 0)`. The second version is what every framework implements. A8 will automate the bookkeeping, but it will still rely on local backward rules that look like these VJPs.

The backward pass can be pictured as a reverse walk through the values cached in A3:

```text
forward:
X -> [dense: X @ W1 + b1] -> Z1 -> [activation] -> A1
  -> [dense: A1 @ W2 + b2] -> Z2 -> [activation/output] -> logits -> loss

backward:
dL/dlogits -> output backward -> dL/dA1, dL/dW2, dL/db2
            -> activation backward -> dL/dZ1
            -> dense backward      -> dL/dX,  dL/dW1, dL/db1
```

Notice the phrase "cached in A3." The backward pass cannot derive `dL_dW1` from `dL_dZ1` alone; it needs the layer input `X`. It cannot derive a ReLU mask safely after the fact if the original pre-activation `Z1` was overwritten. That is why the forward-pass cache is not optional engineering decoration. It is the set of values that makes each VJP well-defined for the specific loss value currently being differentiated.

VJPs also explain why reverse mode is the right default for neural-network training. A model can have thousands, millions, or billions of parameters, but the training objective for one mini-batch is normally one scalar loss. Reverse mode starts from that scalar and computes all parameter gradients in one backward sweep. Forward finite differences would ask the opposite question, perturbing one parameter at a time and paying for a fresh loss evaluation for each coordinate. That method is useful for checking a tiny network because it is simple and independent, but it is not how you train.

Think of each operation as having a small backward contract. A dense layer promises to consume `dL_dY` and return `dL_dX` while filling `dL_dW` and `dL_db`. A ReLU promises to consume `dL_dA` and return `dL_dZ`. A loss promises to consume logits and labels during forward, then produce the first upstream gradient during backward. Once every operation keeps its contract, the network-level backward pass becomes ordinary plumbing. The difficulty is not inventing a new algorithm for every architecture; it is making sure each local contract is mathematically correct.

## Part 3: Backprop Through One Dense Layer

Now derive the dense-layer formulas using the exact A3 convention. The forward computation is `Y = X @ W + b`, where `X:(N,d_in)`, `W:(d_in,d_out)`, `b:(d_out,)`, and `Y:(N,d_out)`. Assume the later network gives us `G = dL_dY` with shape `(N,d_out)`. We need gradients for `W`, `b`, and `X`. The three formulas are:

```python
dL_dW = X.T @ G              # (d_in,N) @ (N,d_out) -> (d_in,d_out)
dL_db = np.sum(G, axis=0)    # sum over N samples -> (d_out,)
dL_dX = G @ W.T              # (N,d_out) @ (d_out,d_in) -> (N,d_in)
```

These transposes are not aesthetic choices; they are forced by the scalar equation. For a single weight `W[j,k]`, only outputs in column `k` depend on it, and the derivative of `Y[n,k]` with respect to `W[j,k]` is `X[n,j]`. The chain rule therefore gives `dL/dW[j,k] = sum_n dL/dY[n,k] * X[n,j]`. That is exactly the `(j,k)` entry of `X.T @ G`: row `j` of `X.T` holds feature `j` across the batch, and column `k` of `G` holds the upstream gradient for output unit `k` across the batch.

The bias sum appears because `b[k]` is shared by every sample in the batch. In the forward pass, NumPy broadcasts the same bias vector onto every row of `X @ W`. Therefore `Y[0,k]`, `Y[1,k]`, and all other sample rows depend on the same scalar `b[k]` with local derivative `1`. The chain rule accumulates all those paths: `dL/db[k] = sum_n dL/dY[n,k]`. If you forget the sum and keep a `(N,d_out)` bias gradient, you have computed the gradient of a different model, one with a separate bias for every sample.

For the input gradient, fix one input entry `X[n,j]`. It influences every output unit `k` in the same sample row through weight `W[j,k]`, so `dL/dX[n,j] = sum_k dL/dY[n,k] * W[j,k]`. That is the `(n,j)` entry of `G @ W.T`. The transpose belongs on `W` because the upstream gradient rows are indexed by output unit, while the previous layer expects feature-indexed gradients.

Another way to remember the formulas is to name the axes before multiplying. `X` has axes `(sample, input_feature)`, while `G` has axes `(sample, output_unit)`. The weight gradient needs axes `(input_feature, output_unit)`, so the shared `sample` axis must be reduced away; `X.T @ G` does exactly that. The input gradient needs axes `(sample, input_feature)`, so the shared `output_unit` axis must be reduced away; `G @ W.T` does exactly that. Bias has only the `output_unit` axis, so the `sample` axis is the one that disappears through summation.

This axis naming habit prevents a surprisingly common false fix. When `X.T @ G` fails because some upstream shape is wrong, students sometimes try `G.T @ X` because it returns a matrix with related dimensions. That computes `(d_out,d_in)`, the transpose of the desired weight gradient, and it may sneak through if the next line also transposes something. The right response to a failing gradient matmul is not to move transposes around until NumPy accepts the expression. The right response is to write the target shape next to the parameter and reduce the axis that should disappear.

Run this numeric example and inspect both values and shapes:

```python
import numpy as np

X = np.array([[1.0,  2.0, -1.0],
              [0.0, -3.0,  4.0]])         # (N=2, d_in=3)
W = np.array([[ 0.2, -0.1],
              [ 0.5,  0.3],
              [-0.4,  0.7]])              # (d_in=3, d_out=2)
b = np.array([0.1, -0.2])                  # (d_out=2,)
G = np.array([[0.6, -0.4],
              [0.2,  0.5]])               # dL_dY, shape (N=2, d_out=2)

Y = X @ W + b                              # (2, 2)
dL_dW = X.T @ G                            # (3, 2)
dL_db = np.sum(G, axis=0)                  # (2,)
dL_dX = G @ W.T                            # (2, 3)

print("Y:\n", Y)
print("dL_dW:\n", dL_dW)
print("dL_db:", dL_db)
print("dL_dX:\n", dL_dX)
```

Expected values are `Y = [[1.7, -0.4], [-3.0, 1.7]]`, `dL_dW = [[0.6, -0.4], [0.6, -2.3], [0.2, 2.4]]`, `dL_db = [0.8, 0.1]`, and `dL_dX = [[0.16, 0.18, -0.52], [-0.01, 0.25, 0.27]]`. The most important thing to notice is that every gradient has the same shape as the thing it differentiates. `dL_dW` can be subtracted from `W` during SGD, `dL_db` can be subtracted from `b`, and `dL_dX` can be handed to the previous layer because it has the same shape as `X`.

If you want a quick mental check for a dense layer, test the degenerate case `N = 1`. Then `X.T @ G` becomes an outer product between one input row and one upstream gradient row, which is exactly what the scalar rule says: every weight receives input value times output error. As the batch grows, the matrix multiply simply sums those outer products across rows. That is why batch training is not a different derivative; it is the same derivative accumulated over several independent samples before the optimizer step.

## Part 4: Backprop Through an Activation

An activation function in A4 is an elementwise operation wrapped in an object with `forward()` and `backward(grad_output)`. During the forward pass, it caches whatever it needs: ReLU caches its input `Z`, tanh can cache its output `A`, and sigmoid can cache its output because the derivative is `A * (1 - A)`. During the backward pass, it receives `dL_dA`, multiplies by the local derivative, and returns `dL_dZ`. In notation, the rule is `dL/dZ = dL/dA ⊙ a'(Z)`, where `⊙` means elementwise multiplication.

Here is a worked ReLU example. The pre-activation `Z` has three entries, the forward activation `A` zeros out the negative entry, and the local derivative is zero for the negative value and one for the positive values. The upstream gradient on the negative value disappears because changing a negative ReLU pre-activation slightly still leaves the activation at zero.

```python
import numpy as np

Z = np.array([[-2.0, 0.5, 3.0]])       # cached pre-activation, shape (1, 3)
A = np.maximum(0.0, Z)                 # [[0.0, 0.5, 3.0]]
dL_dA = np.array([[0.1, -0.2, 0.4]])   # upstream gradient, shape (1, 3)

local_grad = (Z > 0.0).astype(float)   # [[0.0, 1.0, 1.0]]
dL_dZ = dL_dA * local_grad             # [[0.0, -0.2, 0.4]]

print("A:", A)
print("local_grad:", local_grad)
print("dL_dZ:", dL_dZ)
```

For tanh, the same elementwise pattern in code is:

```python
dL_dZ = dL_dA * (1.0 - A**2)   # tanh backward, where A = tanh(Z)
```

The same pattern applies to tanh: `dL_dZ = dL_dA * (1 - A**2)` when `A = tanh(Z)`. It applies to sigmoid: `dL_dZ = dL_dA * A * (1 - A)`. It applies to GELU and SiLU too, although their local derivatives have longer formulas. The interface keeps the layer code simple because `Layer.backward()` does not need to know which activation it owns; it calls `self.activation.backward(dL_dy)` and receives `dL_dz` with the same shape.

One subtle bug from A4 becomes important here: do not blindly apply the derivative at `A` when the derivative formula is defined in terms of `Z`. For ReLU, `A > 0` happens to match `Z > 0` except at the conventional zero point. For tanh, `1 - A**2` is valid because `A = tanh(Z)` and the derivative can be expressed using the output. For Leaky ReLU, GELU, and SiLU, the safest habit is to cache the pre-activation `Z` or the specific intermediate values the class needs. The backward pass should consume the cache from the exact forward call that produced the current loss, not recompute from a mutated or overwritten value.

The activation backward pass never changes the batch or feature shape. This is a useful local assertion: after `dL_dz = activation.backward(dL_dy)`, `dL_dz.shape` should equal `layer.Z.shape`, and it should also equal `dL_dy.shape` because elementwise activations preserve shape. If an activation backward method returns a reduced vector or a scalar, it has accidentally mixed reduction logic into a pointwise operation. Reductions belong to losses, metrics, or explicit pooling layers, not to ReLU, tanh, or sigmoid hidden activations.

The local derivative can still change the meaning of the gradient dramatically. A saturated sigmoid with output near zero or one multiplies the upstream gradient by a tiny number, so earlier layers barely move. A dead ReLU multiplies by zero for every sample where the pre-activation is negative. A tanh hidden unit near zero passes gradients more freely than one near its flat tails. Backpropagation does not merely transport error signals; it filters them through the local geometry of every operation in the forward pass.

## Part 5: The Full MLP Backward Pass

A full MLP backward pass alternates activation backward and dense backward as it walks from the output layer to the input. The loss object supplies the first gradient, `dL_dlogits`. If the A5 loss is a fused softmax-cross-entropy over one sample, the derivative with respect to logits is `p - y`. If the scalar loss is the mean over a batch of `N` samples, the gradient passed into the MLP is `(p - y) / N`. This scaling is not optional: finite differences of the mean loss will only match analytic gradients that include the same `1/N`.

For a three-layer network with dimensions `d0 -> d1 -> d2 -> d3`, the forward pass is:

```text
A0 = X
Z1 = A0 @ W1 + b1
A1 = activation1(Z1)
Z2 = A1 @ W2 + b2
A2 = activation2(Z2)
Z3 = A2 @ W3 + b3
logits = A3 = identity(Z3)
loss = softmax_cross_entropy(logits, y)
```

The backward pass reverses that order. Start from `dL_dA3 = dL_dlogits`. For the output identity activation, `dL_dZ3 = dL_dA3`. Then compute `dL_dW3 = A2.T @ dL_dZ3`, `dL_db3 = sum(dL_dZ3, axis=0)`, and `dL_dA2 = dL_dZ3 @ W3.T`. Feed `dL_dA2` through activation2 backward to get `dL_dZ2`, compute the second layer's parameter gradients, and continue until the first layer returns `dL_dA0`, the gradient with respect to the input batch.

The loop structure is short because every layer owns the same local rule:

```python
class Layer:
    def backward(self, dL_dy):
        dL_dz = self.activation.backward(dL_dy)  # same shape as self.Z
        self.dW = self.X.T @ dL_dz               # same shape as self.W
        self.db = np.sum(dL_dz, axis=0)          # same shape as self.b
        dL_dX = dL_dz @ self.W.T                 # same shape as self.X
        return dL_dX

class MLP:
    def backward(self, dL_dlogits):
        grad = dL_dlogits
        for layer in reversed(self.layers):
            grad = layer.backward(grad)
        return grad
```

The important design choice is that `Layer.forward()` must cache `self.X` as well as `self.Z` and `self.A`. A3 cached `Z` and `A` to prepare for backpropagation; A6 adds the layer input because the weight gradient needs the previous activation. For layer 1, that input is the raw `X`. For layer 2, it is `A1`. For layer 3, it is `A2`. Without that cache, `X.T @ dL_dz` has no `X` to multiply, and recomputing it risks using parameters that have already changed.

The cache lifecycle is therefore part of the API. A correct training iteration is forward, loss, backward, update. Running a second forward before backward overwrites `self.X`, `self.Z`, and activation caches, so the backward pass differentiates the second batch while the loss may have been computed on the first. Updating weights before all layers have used them creates a different problem: the upstream gradient for an earlier layer may be computed with a later layer's old values, while the parameter gradient for that later layer has already mutated the model. The simple rule is strict because the math is strict.

It is also worth separating output heads from hidden activations. Hidden layers use activations like ReLU or tanh to shape representations. The output layer for multiclass classification usually returns raw logits with `Identity()`, and the fused softmax-cross-entropy loss handles both probability normalization and the stable gradient. If you apply softmax inside the `Layer` and then apply a separate cross-entropy backward naively, you either need to derive the softmax Jacobian explicitly or risk double-normalizing. A5's fused result is popular because it gives a stable and compact starting gradient for A6: `p - y`, with the batch reduction scale applied consistently.

## Part 6: Gradient Checking the Whole Network

Gradient checking compares the backward pass to the definition of a derivative. Pick a scalar loss function, perturb one parameter by `+eps`, measure the loss, perturb it by `-eps`, measure again, and estimate the slope with `(loss_plus - loss_minus) / (2*eps)`. Repeat for every entry of every weight matrix and bias vector. Then compare those numerical slopes to the analytic gradients in `layer.dW` and `layer.db`.

Use float64 and a small network because gradient checking is slow. It performs two forward passes per parameter, so it is a debugging tool, not a training algorithm. Also avoid nondifferentiable points when possible. ReLU is fine in real training, but if a pre-activation lands extremely close to zero, finite differences can cross the kink and report a large relative error even when your implementation follows the standard subgradient convention. The check below uses tanh hidden activations to keep the loss smooth.

The relative-error denominator matters because some true gradients are tiny. Comparing only absolute difference can make a `1e-9` disagreement look excellent even when both gradients are near `1e-12`, and comparing only percentage difference can explode when the correct gradient is essentially zero. The common compromise is `abs(numeric - analytic) / max(1e-8, abs(numeric) + abs(analytic))`. This treats small gradients carefully without letting division by an almost-zero denominator dominate the report.

When a gradient check fails, isolate before rewriting. First check that the forward loss is deterministic for the same parameters. Then check one layer with a tiny input and a hand-chosen upstream gradient, as in Part 3. Then check one parameter entry from the failing layer manually by printing `loss_plus`, `loss_minus`, numeric slope, and analytic value. A single bad bias entry usually points to a reduction bug, while many bad entries in one weight matrix point to a transpose or stale-cache bug. Broad failure across all layers often means the first gradient from the loss has the wrong scale.

```python
import numpy as np

class Activation:
    def forward(self, x):
        raise NotImplementedError

    def backward(self, grad_output):
        raise NotImplementedError

class Tanh(Activation):
    def forward(self, x):
        self.output = np.tanh(x)
        return self.output

    def backward(self, grad_output):
        return grad_output * (1.0 - self.output**2)

class Identity(Activation):
    def forward(self, x):
        return x

    def backward(self, grad_output):
        return grad_output

class Layer:
    def __init__(self, d_in, d_out, activation, rng):
        self.W = rng.normal(0.0, np.sqrt(2.0 / d_in), size=(d_in, d_out))
        self.b = np.zeros(d_out, dtype=np.float64)
        self.activation = activation
        self.X = None
        self.Z = None
        self.A = None
        self.dW = np.zeros_like(self.W)
        self.db = np.zeros_like(self.b)

    def forward(self, X):
        self.X = X
        self.Z = X @ self.W + self.b
        self.A = self.activation.forward(self.Z)
        return self.A

    def backward(self, dL_dy):
        dL_dz = self.activation.backward(dL_dy)
        self.dW = self.X.T @ dL_dz
        self.db = np.sum(dL_dz, axis=0)
        return dL_dz @ self.W.T

class MLP:
    def __init__(self, layers):
        self.layers = layers

    def forward(self, X):
        A = X
        for layer in self.layers:
            A = layer.forward(A)
        return A

    def backward(self, dL_dlogits):
        grad = dL_dlogits
        for layer in reversed(self.layers):
            grad = layer.backward(grad)
        return grad

class SoftmaxCrossEntropy:
    def forward(self, logits, y_onehot):
        shifted = logits - logits.max(axis=1, keepdims=True)
        exp = np.exp(shifted)
        self.probs = exp / exp.sum(axis=1, keepdims=True)
        self.y_onehot = y_onehot
        N = logits.shape[0]
        return -np.sum(y_onehot * np.log(self.probs + 1e-12)) / N

    def backward(self):
        N = self.y_onehot.shape[0]
        return (self.probs - self.y_onehot) / N

def loss_and_backward(model, loss_fn, X, y_onehot):
    logits = model.forward(X)
    loss = loss_fn.forward(logits, y_onehot)
    dL_dlogits = loss_fn.backward()
    model.backward(dL_dlogits)
    return loss

def loss_only(model, loss_fn, X, y_onehot):
    return loss_fn.forward(model.forward(X), y_onehot)

def check_all_params(model, loss_fn, X, y_onehot, eps=1e-6):
    loss_and_backward(model, loss_fn, X, y_onehot)
    max_rel_error = 0.0
    worst = None

    for layer_i, layer in enumerate(model.layers):
        for param_name, grad_name in (("W", "dW"), ("b", "db")):
            param = getattr(layer, param_name)
            analytic_grad = getattr(layer, grad_name)

            for idx in np.ndindex(param.shape):
                old_value = param[idx]
                param[idx] = old_value + eps
                loss_plus = loss_only(model, loss_fn, X, y_onehot)
                param[idx] = old_value - eps
                loss_minus = loss_only(model, loss_fn, X, y_onehot)
                param[idx] = old_value

                numeric_grad = (loss_plus - loss_minus) / (2.0 * eps)
                denom = max(1e-8, abs(numeric_grad) + abs(analytic_grad[idx]))
                rel_error = abs(numeric_grad - analytic_grad[idx]) / denom

                if rel_error > max_rel_error:
                    max_rel_error = rel_error
                    worst = (layer_i, param_name, idx, numeric_grad, analytic_grad[idx])

    return max_rel_error, worst

rng = np.random.default_rng(7)
X = rng.normal(size=(5, 3))              # (N=5, d_in=3)
y_idx = np.array([0, 1, 2, 1, 0])
y_onehot = np.eye(3)[y_idx]              # (N=5, classes=3)

model = MLP([
    Layer(3, 4, Tanh(), rng),
    Layer(4, 5, Tanh(), rng),
    Layer(5, 3, Identity(), rng),
])
loss_fn = SoftmaxCrossEntropy()

max_rel_error, worst = check_all_params(model, loss_fn, X, y_onehot)
print("max relative error:", max_rel_error)
print("worst entry:", worst)
```

On the tested run for this module, the maximum relative error was approximately `2.03e-07`, with the worst entry in the first weight matrix. That is comfortably below the `1e-5` threshold normally expected for float64 gradient checks on smooth functions. If you see `1e-2`, `1e-1`, or a value near `1`, do not tune the learning rate. The gradient checker is telling you that the backward computation does not match the forward computation.

Do not skip this proof because the formulas look familiar. Most backpropagation bugs come from code that "obviously" matches the formula until a shape convention changes. Textbooks that use column vectors often write a single-sample layer as `z = W @ x + b`, where `W:(d_out,d_in)`. This track uses batched row samples and `X @ W + b`, so the same math appears with transposes in different places. Gradient checking protects the code you actually wrote, not the formula you intended to write.

Gradient checking is also a contract between the loss definition and the backward scale. In this module, the loss function returns a batch mean, so `SoftmaxCrossEntropy.backward()` divides by `N`. If you remove that division, the analytic gradients will be exactly `N` times too large compared with finite differences of the mean loss. If you change the scalar loss to a sum and leave the division in place, the analytic gradients will be too small. This is why good training code treats loss reduction as an explicit choice rather than a hidden convention.

When you inspect a failed check, keep the worst-entry report. A worst entry in `layer 0, W, (2, 2)` points your attention to one column of the first layer's weight gradient. A worst entry in `layer 2, b, (1,)` points your attention to a bias reduction in the output layer. The exact coordinate is not guaranteed to name the only bug, but it gives you a reproducible starting point. Debugging backpropagation is faster when you can rerun the same failing coordinate after each fix instead of staring at a single global error number.

Finally, remember what gradient checking cannot prove. It proves local agreement between the current forward computation and the current backward rules near one parameter setting. It does not prove that the architecture is expressive enough, that the optimizer will converge, or that the data labels are correct. Those questions belong to later training and evaluation modules. Here the check has one job: prevent you from building A7 on top of a backward pass that is mathematically disconnected from the loss.

## Part 7: Extend the Micro-Framework

Now fold the local rules into the cumulative `nn.py` file. `Tanh` and the other activations from A4 are already part of that framework; Part 7 adds the dense-layer and MLP scaffolding so the network built in Part 8 has every class it references. This code deliberately stays simple. It does not create graph nodes, store arbitrary operation tapes, or overload arithmetic operators because A8 owns the autograd engine. Here, a network is just a list of layers, and each layer knows how to differentiate its own dense transform plus activation.

```python
# In nn.py, extending the A3/A4 micro-framework.
import numpy as np

class ReLU(Activation):
    def forward(self, x):
        self.inputs = x
        return np.maximum(0.0, x)

    def backward(self, grad_output):
        return grad_output * (self.inputs > 0.0)

class Identity(Activation):
    def forward(self, x):
        return x

    def backward(self, grad_output):
        return grad_output

class Layer:
    """Dense layer: Z = X @ W + b, then activation(Z)."""
    def __init__(self, d_in, d_out, activation, rng=None):
        self.rng = np.random.default_rng() if rng is None else rng
        self.W = self.rng.normal(0.0, np.sqrt(2.0 / d_in), size=(d_in, d_out))
        self.b = np.zeros(d_out)
        self.activation = activation
        self.X = None
        self.Z = None
        self.A = None
        self.dW = np.zeros_like(self.W)
        self.db = np.zeros_like(self.b)

    def forward(self, X):
        self.X = X
        self.Z = X @ self.W + self.b
        self.A = self.activation.forward(self.Z)
        return self.A

    def backward(self, dL_dy):
        dL_dz = self.activation.backward(dL_dy)
        self.dW = self.X.T @ dL_dz
        self.db = np.sum(dL_dz, axis=0)
        return dL_dz @ self.W.T

    def step(self, lr):
        self.W -= lr * self.dW
        self.b -= lr * self.db

class MLP:
    def __init__(self, layers):
        self.layers = layers

    def forward(self, X):
        A = X
        for layer in self.layers:
            A = layer.forward(A)
        return A

    def backward(self, dL_dlogits):
        grad = dL_dlogits
        for layer in reversed(self.layers):
            grad = layer.backward(grad)
        return grad

    def step(self, lr):
        for layer in self.layers:
            layer.step(lr)
```

The update rule is minimal SGD: `parameter -= learning_rate * gradient`. There is no momentum, Adam, weight decay, gradient clipping, or batching utility yet. That restraint matters pedagogically because A7 is the training lab where optimization loops, epochs, shuffling, metrics, and learning-rate choices become the main subject. A6 only needs to prove that the gradients are correct and can move parameters in a descent direction.

Parameter ownership stays local. `Layer` owns `W`, `b`, `dW`, and `db`, so `Layer.step()` updates those arrays. `MLP` owns the ordered layer list, so `MLP.step()` delegates to each layer. This is intentionally less abstract than a production framework's parameter registry, but it teaches the same invariant: each trainable array must have one matching gradient array, and the optimizer should update exactly those arrays. If you later add batch normalization or embeddings, the same question applies: which object owns the parameter, and where is its gradient stored?

The code also avoids in-place activation mutation. It is tempting to implement ReLU with `x[x < 0] = 0` because it is short, but that mutates the cached pre-activation if `x` is a shared array. A mutated `Z` can make the backward mask wrong and can corrupt any debugging print that tries to compare pre- and post-activation values. Use `np.maximum(0.0, x)` for the forward result and keep the cached input intact unless you have deliberately designed an in-place memory policy and its backward consequences.

## Part 8: One SGD Step That Decreases Loss

The final proof is a tiny training step. We will use XOR because it is familiar from A3, but we will not run a full multi-epoch lab here. The goal is narrower: run forward, compute mean softmax-cross-entropy, backpropagate, update parameters once, and show that the loss decreases for this deterministic setup.

```python
# Assumes MLP, Layer, Identity, and Tanh are defined in your cumulative nn.py (A2–A6).
import numpy as np

class SoftmaxCrossEntropy:
    def forward(self, logits, y_onehot):
        shifted = logits - logits.max(axis=1, keepdims=True)
        exp = np.exp(shifted)
        self.probs = exp / exp.sum(axis=1, keepdims=True)
        self.y_onehot = y_onehot
        N = logits.shape[0]
        return -np.sum(y_onehot * np.log(self.probs + 1e-12)) / N

    def backward(self):
        N = self.y_onehot.shape[0]
        return (self.probs - self.y_onehot) / N

def loss_and_backward(model, loss_fn, X, y_onehot):
    logits = model.forward(X)
    loss = loss_fn.forward(logits, y_onehot)
    model.backward(loss_fn.backward())
    return loss

def loss_only(model, loss_fn, X, y_onehot):
    return loss_fn.forward(model.forward(X), y_onehot)

rng = np.random.default_rng(11)
X_xor = np.array([[0.0, 0.0],
                  [0.0, 1.0],
                  [1.0, 0.0],
                  [1.0, 1.0]], dtype=np.float64)
y_idx = np.array([0, 1, 1, 0])
y_onehot = np.eye(2)[y_idx]

model = MLP([
    Layer(2, 4, Tanh(), rng),
    Layer(4, 2, Identity(), rng),
])
loss_fn = SoftmaxCrossEntropy()

before = loss_and_backward(model, loss_fn, X_xor, y_onehot)
model.step(lr=0.3)
after = loss_only(model, loss_fn, X_xor, y_onehot)

print(f"loss before: {before:.6f}")
print(f"loss after:  {after:.6f}")
```

The tested output is `loss before: 0.836447` and `loss after: 0.771041`. One step decreasing the loss does not prove the model is fully trained, and it does not prove the learning rate will work for long. It proves something narrower and more important for A6: the gradients point in a descent direction for the scalar loss you just computed. A7 will build the training loop that repeats this process over epochs, tracks accuracy, and handles the practical decisions that turn a single correct step into a trained model.

A one-step loss decrease is weaker than a gradient check but still useful. The gradient check says the derivatives match the scalar loss locally. The SGD step says those derivatives are wired into the model update in the correct direction. If the gradient check passes but the one-step loss rises for a modest learning rate, inspect the update sign first. `p -= lr * grad` descends; `p += lr * grad` ascends. If the sign is correct, lower the learning rate and verify that the loss decreases for a sufficiently small step, because even a correct gradient can overshoot when the step is too large.

Keep the boundary between A6 and A7 clear. A6 does not promise that XOR converges, that hidden units separate the four points, or that the learning rate schedule is robust. Those are training-loop questions. A6 promises that when the loss object returns `dL_dlogits`, the MLP can propagate that gradient through every dense layer, fill every parameter gradient, prove those gradients numerically, and apply an update. That is the keystone: everything later depends on trusting this backward pass.

## Did You Know?

- **Reverse-mode autodiff is efficient because neural networks usually have many parameters but one scalar loss.** A single reverse pass computes gradients for all parameters with cost on the same order as a few forward passes, while finite differences would need two loss evaluations per parameter.
- **Backpropagation predates the current deep learning boom.** Rumelhart, Hinton, and Williams popularized its use for learning internal representations in 1986, while earlier work by Paul Werbos described related reverse differentiation ideas before modern GPUs made large networks practical.
- **The bias gradient is a reduction, not a broadcast.** Forward propagation broadcasts `b` across the batch; backward propagation performs the adjoint operation by summing the upstream gradient across that same batch axis.
- **Gradient checking is intentionally slow.** It is a microscope for debugging small models, not an optimizer, because it scales with the number of parameters rather than with the number of layers.

## Common Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| Transposing the wrong matrix | `dW` has the wrong shape, or worse, the shape happens to fit but the gradient check fails badly | For `Y = X @ W + b`, use `X.T @ dL_dY` for `dW` and `dL_dY @ W.T` for `dX` |
| Forgetting the batch-sum for `b` | `db` has shape `(N,d_out)` or updates bias as if every sample had a private bias | Use `np.sum(dL_dY, axis=0)` so `db` has shape `(d_out,)` |
| Mixing summed and averaged losses | Analytic gradients differ from finite differences by a factor near `N`, or learning rate sensitivity changes with batch size | If the scalar loss is a batch mean, pass `(p - y) / N`; if it is a batch sum, pass `p - y` |
| Overwriting cached activations in place | Backward uses values from a later forward pass, and gradient checks become seed-dependent or batch-order-dependent | Enforce one forward, one backward, one update; avoid in-place mutation of cached `X`, `Z`, or `A` |
| Applying an activation derivative at `A` instead of `Z` | ReLU may appear to work, but GELU, SiLU, or Leaky ReLU gradients are wrong | Cache the pre-activation or the exact intermediate values required by the activation's own backward rule |
| Updating parameters before every layer has backpropagated | Earlier layers receive gradients computed with a mix of old and new weights | Finish the full backward pass first, then call `model.step(lr)` once |
| Trusting shape success as proof of correctness | Loss moves unpredictably even though every matrix multiply runs | Run a central finite-difference check over every parameter before trusting the implementation |

## Quiz

1. **For `Y = X @ W + b`, with `X:(32,10)`, `W:(10,4)`, `b:(4,)`, and upstream gradient `G:(32,4)`, what are the shapes of `dL_dW`, `dL_db`, and `dL_dX`?**

   <details>
   <summary>Answer</summary>
   `dL_dW = X.T @ G` has shape `(10,32) @ (32,4) = (10,4)`, matching `W`. `dL_db = np.sum(G, axis=0)` has shape `(4,)`, matching `b`. `dL_dX = G @ W.T` has shape `(32,4) @ (4,10) = (32,10)`, matching `X`.
   </details>

2. **Why do we sum the bias gradient across the batch dimension instead of averaging automatically inside `Layer.backward()`?**

   <details>
   <summary>Answer</summary>
   The layer backward rule should reflect the upstream gradient it receives. If the loss object has already averaged the batch loss, then `dL_dY` already contains the `1/N` scale, and summing over the batch produces the correct mean-loss bias gradient. If the loss object represents a summed batch loss, then no `1/N` is present, and summing produces the correct summed-loss bias gradient. Averaging inside the layer would silently impose a loss reduction choice that belongs to the loss function.
   </details>

3. **A ReLU activation receives `dL_dA = [[2.0, -3.0, 1.0]]` and cached `Z = [[-1.0, 0.0, 4.0]]`. Using the convention that ReLU's derivative at zero is zero, what is `dL_dZ`?**

   <details>
   <summary>Answer</summary>
   The local derivative mask is `[[0.0, 0.0, 1.0]]` because only the positive pre-activation passes gradient. Elementwise multiplication gives `dL_dZ = [[0.0, -0.0, 1.0]]`, usually written as `[[0.0, 0.0, 1.0]]`.
   </details>

4. **Your gradient check reports a maximum relative error of `0.5`, and the worst parameter is a bias entry. The analytic `db` has shape `(d_out,)`, but every value is about one-fourth of the numerical gradient for a batch of four samples. What is the most likely bug?**

   <details>
   <summary>Answer</summary>
   The most likely bug is a reduction mismatch: the analytic path divided by `N` one extra time or the numerical loss is a sum while the analytic gradient is a mean. Because the factor matches the batch size, inspect where `1/N` is applied. The loss reduction and `dL_dlogits` scaling must agree; `Layer.backward()` should only sum the upstream bias gradient across the batch axis.
   </details>

5. **Why does reverse-mode backpropagation avoid materializing the full Jacobian for a dense layer?**

   <details>
   <summary>Answer</summary>
   The full Jacobian of a batched dense layer is huge and mostly unnecessary. The previous layer only needs `dL_dX`, not every partial derivative stored separately, and the optimizer only needs gradients shaped like `W` and `b`. The VJP formulas `X.T @ G`, `sum(G, axis=0)`, and `G @ W.T` compute exactly those arrays with ordinary matrix operations.
   </details>

6. **Debug this common backpropagation failure: a full-network gradient check fails only when batch size is greater than one, the loss sometimes rises after SGD, and the error is concentrated in `db`. Which missing bias sum or loss-scaling mismatch should you investigate first, and why?**

   <details>
   <summary>Answer</summary>
   Investigate the bias reduction first. Bias is broadcast across samples in the forward pass, so its backward rule must sum the upstream gradient over `axis=0`. If the implementation keeps a per-sample bias gradient, averages in the wrong place, or sums over `axis=1`, the bug may not appear for `N=1` but will show up immediately when several samples share the same bias parameter.
   </details>

7. **Trace the order of backward calls for a network `X -> Layer1(ReLU) -> Layer2(Tanh) -> Layer3(Identity logits) -> SoftmaxCrossEntropy`. What gradient enters `Layer3`, and what gradient should `Layer1.backward()` return?**

   <details>
   <summary>Answer</summary>
   The loss supplies the first upstream gradient: for a mean softmax-cross-entropy batch, `dL_dlogits = (p - y) / N`. `Layer3.backward()` consumes that gradient, fills `dW3` and `db3`, and returns `dL_dA2`. `Layer2.backward()` converts that through tanh and its dense transform, returning `dL_dA1`. `Layer1.backward()` converts that through ReLU and the first dense transform, fills `dW1` and `db1`, and returns `dL_dX`, a gradient with the same shape as the original input batch `X`.
   </details>

## Hands-On Exercise

**Task:** Add `backward(dL_dy)` and `step(lr)` to your local `Layer` class, add `backward(dL_dlogits)` and `step(lr)` to `MLP`, and run a finite-difference gradient check on a two-layer network before taking one SGD step.

### Steps

1. Start from the A3/A4 `nn.py` file and add `self.X`, `self.dW`, and `self.db` to `Layer`.
2. Implement `Layer.backward()` with `self.activation.backward(dL_dy)`, `self.X.T @ dL_dz`, `np.sum(dL_dz, axis=0)`, and `dL_dz @ self.W.T`.
3. Implement `MLP.backward()` by iterating through `reversed(self.layers)` and threading the gradient returned by each layer.
4. Copy the gradient-checking function from Part 6 and verify a tiny `3 -> 4 -> 3` tanh network against mean softmax-cross-entropy.
5. Build the XOR network from Part 8 and confirm one update lowers the printed loss for the provided seed and learning rate.

### Success Criteria

- [ ] Every `dW` has the same shape as its layer's `W`, and every `db` has the same shape as its layer's `b`.
- [ ] The whole-network gradient check reports maximum relative error below `1e-5` in float64.
- [ ] One SGD step decreases the XOR toy loss for the provided deterministic setup.
- [ ] No code builds an autograd graph, `Value` object, tape, or overloaded arithmetic engine; that belongs to A8.

### Verification

```python
# After running the Part 6 checker:
assert max_rel_error < 1e-5

# After running the Part 8 training step:
assert after < before
```

## Key Takeaways

- Backpropagation is the chain rule applied in reverse topological order, using cached forward values so every local operation can compute its VJP.
- For the A3 dense-layer convention `Y = X @ W + b`, the only correct gradient shapes are `dL_dW:(d_in,d_out)`, `dL_db:(d_out,)`, and `dL_dX:(N,d_in)`.
- Activation backward passes are elementwise VJPs: multiply the upstream gradient by the local derivative from the cached pre-activation or cached activation output.
- The loss reduction controls gradient scale. If the scalar loss is averaged over the batch, the first gradient entering the MLP must include `1/N`.
- A finite-difference gradient check over all parameters is the proof that your analytic backward pass matches your forward pass before A7 turns it into a training loop.

## Sources

- Stanford CS231n, "Backpropagation, Intuitions" and vectorized gradient discussion: https://cs231n.github.io/optimization-2/
- Andrej Karpathy, "Yes you should understand backprop": https://karpathy.medium.com/yes-you-should-understand-backprop-e2f06eab496b
- Dive into Deep Learning, "Forward Propagation, Backward Propagation, and Computational Graphs": https://d2l.ai/chapter_multilayer-perceptrons/backprop.html
- Goodfellow, Bengio, and Courville, *Deep Learning*, Chapter 6.5 "Back-Propagation and Other Differentiation Algorithms": https://www.deeplearningbook.org/contents/mlp.html
- Michael Nielsen, *Neural Networks and Deep Learning*, Chapter 2 "How the backpropagation algorithm works": http://neuralnetworksanddeeplearning.com/chap2.html
- Rumelhart, Hinton, and Williams, "Learning representations by back-propagating errors": https://www.nature.com/articles/323533a0
- NumPy documentation, `numpy.matmul`: https://numpy.org/doc/stable/reference/generated/numpy.matmul.html
- NumPy documentation, broadcasting rules: https://numpy.org/doc/stable/user/basics.broadcasting.html
- NumPy documentation, `numpy.sum`: https://numpy.org/doc/stable/reference/generated/numpy.sum.html
- PyTorch documentation, "Automatic Differentiation with torch.autograd": https://pytorch.org/tutorials/beginner/basics/autogradqs_tutorial.html
- TensorFlow documentation, "Introduction to gradients and automatic differentiation": https://www.tensorflow.org/guide/autodiff

## Learner check

> | 1.1.6 | [Backprop by Hand for Dense Nets](/ai-ml-engineering/deep-learning/module-1.1.6-backprop-by-hand-dense-nets/) |

## Next Module

Continue toward A7 through the [Deep Learning section index](/ai-ml-engineering/deep-learning/), where the next Block A module turns this single verified backward pass into a full training loop with SGD.
