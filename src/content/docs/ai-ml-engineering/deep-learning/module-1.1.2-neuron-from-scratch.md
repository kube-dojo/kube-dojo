---
title: "The Neuron & Perceptron from Scratch"
slug: ai-ml-engineering/deep-learning/module-1.1.2-neuron-from-scratch
sidebar:
  order: 1002.2
---

In 1943, Warren McCulloch and Walter Pitts published a small mathematical model with an outsized afterlife: a simplified neuron that fired when enough binary inputs were active. In 1958, Frank Rosenblatt described the perceptron, a trainable threshold unit that could adjust its weights from examples. Those systems were not modern deep learning, and they were not realistic models of a biological brain, but they gave engineers a precise question that still matters: what can a tiny learnable computation do, and where does it fail?

This module answers that question by extending the `nn.py` scratch file you started in A1. We will build a single artificial neuron, train it with the perceptron learning rule, watch it solve AND and OR, and then deliberately run it into the XOR wall. That wall is not a historical footnote; it is the cleanest reason to care about hidden layers, depth, and forward propagation in A3.

## Learning Outcomes

- Implement a single artificial neuron in NumPy, then connect each shape in the weighted-sum calculation to the equivalent scalar arithmetic by hand.
- Derive and debug the perceptron learning rule, including how positive and negative errors move both the weights and the bias.
- Train one perceptron on AND and OR, inspect the converged parameters, and compare those successes with the geometry of linear separability.
- Demonstrate why XOR cannot be solved by one perceptron, using an algebraic contradiction and a deterministic training trace that keeps making mistakes.
- Construct a hand-set two-layer XOR forward pass, then extend the Block A `nn.py` micro-framework with reusable `Neuron` and `Layer` primitives for A3.

## Why This Module Matters

A neural network is easier to understand when you stop treating it as a mysterious object and start treating it as a small program repeated many times. A single neuron is only a weighted sum, a bias, and an activation function. If you can compute `z = w dot x + b` by hand, you can understand the raw material from which larger networks are built. The hard part is not the formula itself; the hard part is learning how that formula behaves when the weights change.

The perceptron is the smallest useful training loop in neural networks. It does not use backpropagation, differentiable activations, loss curves, or optimizers, yet it already contains the basic learning pattern: predict, compare with a target, update parameters, and try again. The rule is local enough to inspect line by line, which makes it a good bridge between ordinary NumPy arrays and the multi-layer forward passes that follow later in Block A.

The limitation is just as important as the success. A single perceptron can learn some Boolean functions because it draws one straight decision boundary through input space. AND and OR are separable by one line, so the algorithm can find workable weights. XOR requires two separated positive regions, so one line cannot solve it no matter how long you train. That failure is the first honest motivation for depth: hidden units can carve the space into intermediate features that a final unit can separate.

This is also the first module where "from scratch" starts to mean more than retyping formulas. You will see the same idea three ways: arithmetic, geometry, and executable code. The arithmetic tells you what each parameter update does to one example. The geometry tells you whether a one-boundary classifier has any chance of representing the labels. The code tells you whether your implementation respects those two stories. When all three views agree, debugging becomes much less mysterious.

Treat the perceptron as a small lab instrument for your own understanding. It is limited enough that every moving part fits on one screen, but complete enough to expose the habits used in larger networks: keep shapes explicit, separate linear scores from activations, print intermediate values, and verify claims against data. Those habits are the real carry-over into A3 and the rest of Block A.

## Part 1: The Artificial Neuron

The artificial neuron in this module is a deliberately small computational object. It receives an input vector `x`, stores a weight vector `w` with the same length, stores one scalar bias `b`, computes a scalar score `z = w dot x + b`, and then passes that score through an activation function. When the activation is a step function, the neuron outputs `1` for scores at or above zero and `0` for scores below zero.

You can think of the weights as knobs for evidence. A positive weight says that a large input value should push the score upward, a negative weight says that a large input value should push the score downward, and a near-zero weight says that the feature barely matters. The bias is the neuron's default position before the features speak. A negative bias makes firing harder, while a positive bias makes firing easier.

Here is the shape picture for one neuron with three inputs. The arrays are short enough that we can see every multiplication, but the same pattern works for hundreds or thousands of inputs because NumPy performs the same dot product over longer vectors.

```text
inputs x      weights w
---------     ---------
x0 =  0.6 --> w0 =  0.8 --\
x1 = -1.2 --> w1 = -0.5 ----> z = w0*x0 + w1*x1 + w2*x2 + b
x2 =  0.3 --> w2 =  0.1 --/        = 0.91
                                      |
                                      v
                              step(z) = 1
```

The arithmetic in the diagram is `0.8*0.6 + (-0.5)*(-1.2) + 0.1*0.3 - 0.2 = 0.91`. Notice that the negative input and negative weight multiply into positive evidence, because a feature can be meaningful by being absent or below a baseline. The step function then collapses the score to a binary decision.

```python
import numpy as np

x = np.array([0.6, -1.2, 0.3])       # shape: (3,)
w = np.array([0.8, -0.5, 0.1])       # shape: (3,)
b = -0.2                             # scalar

z = float(np.dot(w, x) + b)
a = 1 if z >= 0.0 else 0

print(f"weighted sum z = {z:.2f}")
print(f"step activation = {a}")
```

```text
weighted sum z = 0.91
step activation = 1
```

The first habit to build is shape discipline. A single example has shape `(n_features,)`, the weights have shape `(n_features,)`, and the dot product returns one scalar. A batch of examples has shape `(n_examples, n_features)`, and multiplying that batch by the same weight vector returns one score per example. This is why A1 spent time on NumPy notation: the code becomes short only when the shapes are correct.

```python
import numpy as np

X = np.array(
    [
        [0.6, -1.2, 0.3],
        [1.0, 0.0, -0.4],
        [-0.2, 0.5, 0.8],
    ],
    dtype=float,
)                                      # shape: (3 examples, 3 features)
w = np.array([0.8, -0.5, 0.1])         # shape: (3 features,)
b = -0.2

scores = X @ w + b                     # shape: (3 examples,)
predictions = (scores >= 0.0).astype(int)

print(np.round(scores, 2).tolist())
print(predictions.tolist())
```

```text
[0.91, 0.56, -0.53]
[1, 1, 0]
```

For Block A, keep the neuron plain. We are not adding tensors, autograd, modules, optimizers, devices, or a package layout yet. The goal is a growing `nn.py` file where each concept is visible. A neuron is the first reusable object worth adding because future layers will just be collections of these score-and-activate computations.

There is one subtle design choice hiding in that plainness: the activation function is outside the linear score. The score `z` can be any real number, which means it can carry information about confidence, margin, or distance from a boundary. The activation turns that score into the output used by the next step. In this module, the step activation throws away nearly all of that information because the perceptron only needs a hard class label. In later modules, smoother activations keep more signal so that gradients can tell us how a small weight change would affect an output.

When you debug a neuron, separate those two stages. If the score is wrong, inspect the input features, the weight order, the bias, and the dot product. If the score is right but the decision is surprising, inspect the activation threshold or activation function. This habit prevents a common beginner mistake: changing weights to fix what is really an activation convention. In a step perceptron, the convention for `z == 0` matters because the boundary itself has to be assigned to one class.

The batch example also previews the most important performance idea in neural-network code. A Python loop over examples is easy to read, but `X @ w + b` asks NumPy to run the repeated multiply-add work in optimized native code. We still use a loop in the perceptron trainer because the classic rule updates after each example. For pure forward computation, though, the batch expression is both clearer and faster, and that is the version we will generalize in A3.

## Part 2: The Historical Framing Without the Mythology

McCulloch and Pitts did not invent a modern trainable network in 1943. Their model was closer to logical threshold computation: inputs were active or inactive, connections were excitatory or inhibitory, and the cell fired when the combined condition was satisfied. That abstraction mattered because it connected nervous-system language to Boolean reasoning. It suggested that simple threshold units could represent logic, memory, and computation at a time when digital computing itself was still taking shape.

Rosenblatt's perceptron added the learning question. Instead of only asking whether a fixed threshold circuit could compute a function, the perceptron asked whether a machine could adjust its own weights from examples. The 1958 paper described a probabilistic model for information storage and recognition, and the algorithmic core was simple enough to write in a few lines: make a prediction, compare it with the desired output, and update the weights when the prediction is wrong.

The sober version of the story is more useful than the dramatic one. Early perceptrons were interesting because they could learn linearly separable patterns, not because they solved intelligence. Minsky and Papert's 1969 book, Perceptrons, became famous for showing limitations of single-layer perceptron systems, including problems related to parity and connectedness. The book did not single-handedly create every funding decision that followed, but it became a major marker in the cooling of enthusiasm for shallow connectionist models.

That history sets up a good engineering lesson. A simple model can be both powerful inside its assumptions and useless outside them. The perceptron is not "wrong" because it fails on XOR. It fails because XOR asks for a decision surface the model class cannot represent. The right response is not to train harder; the right response is to change the representation by adding hidden units.

The historical arc is also a warning about naming. A "neuron" in this module is a mathematical primitive, not a claim that we have captured the biology of a real cell. The abstraction is valuable because it gives us a composable computation, not because it is anatomically complete. Keeping that distinction clear helps you read older neural-network papers with the right level of respect: they often used biological language, but the engineering object we inherit is the weighted threshold unit.

There is a second warning in the 1960s story. A negative result can be productive when it names the exact boundary of a model. The XOR limitation is not a vague complaint that perceptrons are too small. It is a precise statement about linear decision boundaries. That precision gives us an implementation path: show the impossible case, introduce a hidden representation, and make the impossible case possible without pretending that more epochs would have solved it.

## Part 3: The Perceptron Learning Rule

A perceptron with a step activation predicts `y_hat = 1` when `w dot x + b >= 0` and predicts `0` otherwise. For a labeled example `(x, y)`, where `y` is either `0` or `1`, the prediction error can be written as `error = y - y_hat`. That error has only three possibilities: `0` when the prediction is correct, `1` when the perceptron predicted `0` but should have predicted `1`, and `-1` when it predicted `1` but should have predicted `0`.

The update rule is the classic perceptron correction:

```text
w <- w + eta * (y - y_hat) * x
b <- b + eta * (y - y_hat)
```

The symbol `eta` is the learning rate, a small positive number that controls the size of each correction. There is no calculus hidden in this rule. If the target is `1` and the prediction is `0`, the error is positive, so the update adds some of the current input vector to the weights and raises the bias. That makes the same example more likely to produce a nonnegative score next time. If the target is `0` and the prediction is `1`, the error is negative, so the update subtracts some of the current input vector and lowers the bias.

Work through one concrete correction. Suppose `x = [1, 1]`, `y = 1`, `w = [0.0, 0.0]`, `b = -0.2`, and `eta = 0.2`. The current score is `z = 0*1 + 0*1 - 0.2 = -0.2`, so `y_hat = 0`. The error is `1 - 0 = 1`, so the new weights are `[0.0, 0.0] + 0.2*1*[1, 1] = [0.2, 0.2]`, and the new bias is `-0.2 + 0.2*1 = 0.0`. The next score for the same input is `0.2 + 0.2 + 0.0 = 0.4`, which now fires.

Here is a complete trainer for two-input Boolean datasets. It starts from zero weights, loops through the four examples in a fixed order, records the mistakes after each epoch, and stops early when an entire epoch makes no corrections. We use the same `step` convention throughout: a score of exactly zero predicts `1`, which is why the first pass from zero weights immediately corrects examples whose target is `0`.

```python
import numpy as np


def step(z):
    """Return 1 where z is nonnegative and 0 elsewhere."""
    return (z >= 0.0).astype(int)


def predict(X, w, b):
    """Predict a batch of examples with shape (n_examples, n_features)."""
    return step(X @ w + b)


def train_perceptron(X, y, lr=0.2, epochs=20):
    """Train a binary perceptron and keep a small history for inspection."""
    w = np.zeros(X.shape[1], dtype=float)
    b = 0.0
    history = []

    for epoch in range(1, epochs + 1):
        mistakes = 0

        for xi, target in zip(X, y):
            raw = float(xi @ w + b)
            pred = int(raw >= 0.0)
            error = int(target - pred)

            if error != 0:
                w += lr * error * xi
                b += lr * error
                mistakes += 1

        history.append(
            {
                "epoch": epoch,
                "weights": w.copy(),
                "bias": b,
                "mistakes": mistakes,
                "predictions": predict(X, w, b).tolist(),
            }
        )

        if mistakes == 0:
            break

    return w, b, history


X_bool = np.array(
    [
        [0.0, 0.0],
        [0.0, 1.0],
        [1.0, 0.0],
        [1.0, 1.0],
    ]
)

y_and = np.array([0, 0, 0, 1])
y_or = np.array([0, 1, 1, 1])

for name, labels in [("AND", y_and), ("OR", y_or)]:
    w, b, history = train_perceptron(X_bool, labels)
    print(f"\n{name}")
    for row in history:
        weights = np.round(row["weights"], 2).tolist()
        bias = round(row["bias"], 2)
        print(
            row["epoch"],
            weights,
            bias,
            row["mistakes"],
            row["predictions"],
        )
    print("final:", np.round(w, 2).tolist(), round(b, 2))
```

```text
AND
1 [0.2, 0.2] 0.0 2 [1, 1, 1, 1]
2 [0.4, 0.2] -0.2 3 [0, 1, 1, 1]
3 [0.4, 0.2] -0.4 3 [0, 0, 0, 1]
4 [0.4, 0.2] -0.4 0 [0, 0, 0, 1]
final: [0.4, 0.2] -0.4

OR
1 [0.0, 0.2] 0.0 2 [1, 1, 1, 1]
2 [0.2, 0.2] 0.0 2 [1, 1, 1, 1]
3 [0.2, 0.2] -0.2 1 [0, 1, 1, 1]
4 [0.2, 0.2] -0.2 0 [0, 1, 1, 1]
final: [0.2, 0.2] -0.2
```

The trainer is intentionally unsophisticated. It uses a fixed order, no shuffling, no mini-batches, no differentiable loss, and no gradient object. That is useful because the behavior is transparent. When the model is wrong, the row that caused the error directly changes the parameters. When the model completes an epoch with zero mistakes, every row is on the correct side of the boundary.

The converged weights are not unique. If you change the learning rate, example order, initial weights, or step convention at exactly zero, you may get a different valid separator. The important property is not the exact numbers; it is the existence of weights and a bias that classify all four rows correctly. That existence question is called linear separability, and it is the line between perceptron success and perceptron failure.

The learning rate changes how large each correction is, but for these tiny Boolean gates it does not change the main story. A smaller learning rate may need more updates before the printed numbers look separated, while a larger learning rate may jump to a separator in fewer passes. The perceptron convergence theorem says that, for linearly separable data and a fixed positive learning rate, repeated corrections eventually find some separator. It does not say the separator will be the prettiest one, the largest-margin one, or the same one a different ordering would find.

The bias update deserves special attention because it is easy to forget. Without a bias, the boundary `w dot x = 0` must pass through the origin. That is an unnecessary restriction for most datasets, including tiny truth tables. Updating the bias with the same signed error as the weights lets the boundary shift. You can read this geometrically as moving the line, and you can read it operationally as changing the neuron's default tendency to fire before feature evidence is added.

There is also a practical debugging rule here: print mistakes per epoch, not just final accuracy. A final prediction vector tells you whether the model worked, but the mistake count tells you whether learning has stabilized. For AND and OR, the count falls to zero, which is the signal to stop. For XOR, the count stays nonzero, and the trace becomes evidence that the training loop is correcting forever instead of converging.

## Part 4: Linear Separability and Decision Boundaries

For two input features, the perceptron's score equation is `z = w1*x1 + w2*x2 + b`. The decision boundary is the set of points where the score is exactly zero: `w1*x1 + w2*x2 + b = 0`. Points with positive scores are predicted as `1`, and points with negative scores are predicted as `0`. In two dimensions, that boundary is a line.

Use the final AND parameters from the trace: `w = [0.4, 0.2]` and `b = -0.4`. The boundary is `0.4*x1 + 0.2*x2 - 0.4 = 0`, which can be rearranged as `x2 = 2 - 2*x1`. The point `(1, 1)` gives score `0.2`, so it is positive. The point `(1, 0)` gives score `0.0`, which our convention treats as positive if evaluated alone, but the final predictions from the training loop were correct because the exact stored bias is `-0.4000000000000001`, a floating-point value just below `-0.4`. That tiny detail is a useful reminder: print rounded values for humans, but use the actual arrays for verification.

To avoid relying on rounded display, inspect the scores directly. The following snippet computes the final scores for AND and OR using the learned parameters from the deterministic training run. The values show how each truth-table row lands on one side of the learned boundary.

```python
import numpy as np

X_bool = np.array(
    [
        [0.0, 0.0],
        [0.0, 1.0],
        [1.0, 0.0],
        [1.0, 1.0],
    ]
)

and_w = np.array([0.4, 0.2])
and_b = -0.4000000000000001
or_w = np.array([0.2, 0.2])
or_b = -0.2

for name, w, b in [("AND", and_w, and_b), ("OR", or_w, or_b)]:
    scores = X_bool @ w + b
    predictions = (scores >= 0.0).astype(int)
    print(name)
    for x, score, pred in zip(X_bool.astype(int), scores, predictions):
        print(x.tolist(), round(float(score), 3), int(pred))
```

```text
AND
[0, 0] -0.4 0
[0, 1] -0.2 0
[1, 0] -0.0 0
[1, 1] 0.2 1
OR
[0, 0] -0.2 0
[0, 1] 0.0 1
[1, 0] 0.0 1
[1, 1] 0.2 1
```

The geometry is easiest to see as four corners of a square. For AND, only the top-right corner is positive, so a diagonal-ish line can leave that corner on one side and the other three corners on the other side. For OR, only the bottom-left corner is negative, so a different line can isolate that one corner. The perceptron is a straight-edge classifier; if one straight edge can divide the labels, it can learn the task.

```text
AND labels                 OR labels

x2                         x2
1   0 -------- 1           1   1 -------- 1
    |          |               |          |
    |          |               |          |
0   0 -------- 0           0   0 -------- 1
    0          1  x1           0          1  x1

One line can isolate       One line can isolate
the top-right 1.           the bottom-left 0.
```

Linear separability is not about the training algorithm being clever. It is about the model class having enough shape to represent the labeling. If no line can separate the labels, the perceptron rule has nowhere to converge. It can keep responding to the most recent mistake, but fixing one corner will break another corner because the single boundary is the wrong shape.

This distinction between algorithm and representation is one of the most useful habits in machine learning. When a model fails, ask whether the optimizer is unable to find good parameters or whether good parameters do not exist inside the model class. The perceptron on XOR is the second case. No amount of patience, logging, or hyperparameter tuning can create a single line that separates alternating corners. You need a different representation before the optimizer has anything useful to find.

For a real dataset, you rarely get a perfect truth-table square. You get noisy points, correlated features, and labels that may be wrong. The same concept still helps. A linear model asks whether one hyperplane can do the job well enough. If the answer is no, you can engineer features, add interactions, use kernels, or build a multi-layer network that learns intermediate features. XOR is the classroom-sized version of that broader engineering choice.

The perceptron also shows why plotting low-dimensional problems is more than decoration. A plot or ASCII diagram can reveal that a task is impossible for a model before you spend time tuning code. When features become high dimensional, you cannot draw the boundary as a line on a square, but the equation is still a hyperplane. The same mental model scales: positive examples need to land on one side, negative examples on the other, and the model only has one flat cut.

## Part 5: The XOR Wall

XOR returns `1` when exactly one input is active and returns `0` when both inputs match. The truth table is `[0, 1, 1, 0]` for inputs `[[0,0], [0,1], [1,0], [1,1]]`. The positive examples are the top-left and bottom-right corners of the square, while the negative examples are the bottom-left and top-right corners. A single straight line cannot put those alternating corners on opposite sides.

There is also a short algebraic proof. For XOR, we need `(0,0)` to be negative, so `b < 0`. We need `(1,0)` to be positive, so `w1 + b >= 0`, which means `w1 >= -b`. We need `(0,1)` to be positive, so `w2 + b >= 0`, which means `w2 >= -b`. Adding those two inequalities gives `w1 + w2 >= -2b`. Since `b < 0`, this implies `w1 + w2 + b >= -b > 0`, so `(1,1)` must be positive. XOR requires `(1,1)` to be negative. Contradiction.

That argument is stronger than a failed training run because it does not depend on the learning rate, initial weights, or epoch count. The perceptron cannot solve XOR because no valid parameters exist. Still, it is useful to see the training loop stall, because that is what failure looks like in practice: the code runs, the weights change, and the final predictions stay wrong.

```python
import numpy as np


def step(z):
    return (z >= 0.0).astype(int)


def predict(X, w, b):
    return step(X @ w + b)


def train_perceptron(X, y, lr=0.2, epochs=20):
    w = np.zeros(X.shape[1], dtype=float)
    b = 0.0
    history = []

    for epoch in range(1, epochs + 1):
        mistakes = 0
        for xi, target in zip(X, y):
            pred = int((xi @ w + b) >= 0.0)
            error = int(target - pred)
            if error != 0:
                w += lr * error * xi
                b += lr * error
                mistakes += 1

        history.append((epoch, w.copy(), b, mistakes, predict(X, w, b).tolist()))
        if mistakes == 0:
            break

    return w, b, history


X_bool = np.array(
    [
        [0.0, 0.0],
        [0.0, 1.0],
        [1.0, 0.0],
        [1.0, 1.0],
    ]
)
y_xor = np.array([0, 1, 1, 0])

w, b, history = train_perceptron(X_bool, y_xor)

for epoch, weights, bias, mistakes, predictions in history[:6]:
    print(epoch, np.round(weights, 2).tolist(), round(bias, 2), mistakes, predictions)

print("last:", history[-1][0], np.round(w, 2).tolist(), round(b, 2), history[-1][3], history[-1][4])
```

```text
1 [-0.2, 0.0] -0.2 3 [0, 0, 0, 0]
2 [-0.2, 0.0] 0.0 3 [1, 1, 0, 0]
3 [-0.2, 0.0] 0.0 4 [1, 1, 0, 0]
4 [-0.2, 0.0] 0.0 4 [1, 1, 0, 0]
5 [-0.2, 0.0] 0.0 4 [1, 1, 0, 0]
6 [-0.2, 0.0] 0.0 4 [1, 1, 0, 0]
last: 20 [-0.2, 0.0] 0.0 4 [1, 1, 0, 0]
```

Do not interpret this as "perceptrons are bad." Interpret it as "one linear boundary is a specific tool." The algorithm is doing exactly what it promised: every time it sees a wrong example, it moves the boundary to help that example. XOR is arranged so that any move helping one positive corner fights another requirement. The correction loop becomes a cycle because the representation cannot express the function.

This is why the XOR story is still worth teaching. It turns depth from an aesthetic preference into a representational necessity. A hidden layer can create new features such as "input one OR input two" and "input one AND input two." Once those features exist, the output neuron does not need to separate the original checkerboard pattern directly. It can separate a transformed space.

The algebraic proof is worth keeping in your notebook because it prevents a misleading interpretation of the training output. A stalled trace can always be blamed on an implementation bug unless you know the target is impossible for the model. The contradiction shows that the failure is structural. If your code cannot learn XOR with one perceptron, that is the expected result. If your code cannot learn AND or OR, that points back to your update rule, bias handling, data order, or activation convention.

There is a second lesson about labels. XOR depends on an interaction between features: the meaning of `x1` changes depending on `x2`. When `x2` is zero, `x1 = 1` should produce a positive label. When `x2` is one, `x1 = 1` should produce a negative label. A single weighted sum assigns one global coefficient to `x1`, so it cannot make that coefficient conditional on another input. Hidden units are one way to create those conditional features.

This is the first glimpse of why feature learning matters. In traditional linear modeling, an engineer might manually add an interaction feature such as `x1*x2` so that the model can represent XOR-like behavior. A neural network learns or constructs intermediate activations instead. The hand-set XOR network below is not learning those features yet, but it demonstrates the representational move that learning will later automate.

## Part 6: Why Depth Fixes XOR

A two-layer network solves XOR by using hidden neurons to create intermediate decisions. One hidden unit can compute OR, another hidden unit can compute AND, and the output unit can compute `OR AND NOT AND`. In ordinary Boolean language, XOR is true when at least one input is active but not both. In perceptron language, the hidden layer turns two raw inputs into two features, then the output perceptron separates those features with one line.

The following hand-set network uses the same step activation as before. Hidden neuron `h_or` uses weights `[1, 1]` and bias `-0.5`, so it fires for `[0,1]`, `[1,0]`, and `[1,1]`. Hidden neuron `h_and` uses weights `[1, 1]` and bias `-1.5`, so it fires only for `[1,1]`. The output neuron uses weights `[1, -2]` and bias `-0.5`, so it accepts OR when AND is off and rejects the case where both are active.

```python
import numpy as np


def step(z):
    return (z >= 0.0).astype(int)


X_bool = np.array(
    [
        [0.0, 0.0],
        [0.0, 1.0],
        [1.0, 0.0],
        [1.0, 1.0],
    ]
)

# Columns are hidden neurons: h_or and h_and.
W_hidden = np.array(
    [
        [1.0, 1.0],
        [1.0, 1.0],
    ]
)                                      # shape: (2 inputs, 2 hidden units)
b_hidden = np.array([-0.5, -1.5])      # shape: (2 hidden units,)

H = step(X_bool @ W_hidden + b_hidden) # shape: (4 examples, 2 hidden units)

W_out = np.array([1.0, -2.0])          # shape: (2 hidden units,)
b_out = -0.5
y_hat = step(H @ W_out + b_out)        # shape: (4 examples,)

print("hidden features [OR, AND]:")
print(H)
print("xor predictions:")
print(y_hat.tolist())
```

```text
hidden features [OR, AND]:
[[0 0]
 [1 0]
 [1 0]
 [1 1]]
xor predictions:
[0, 1, 1, 0]
```

The key idea is not that these particular weights are magical. The key idea is feature construction. In the original `(x1, x2)` space, XOR alternates around the square and defeats one boundary. In the hidden `(h_or, h_and)` space, the examples become `[0,0]`, `[1,0]`, `[1,0]`, and `[1,1]`. The desired labels are `0`, `1`, `1`, and `0`, so one output neuron can reject `[0,0]`, accept `[1,0]`, and reject `[1,1]`.

```text
Raw input space                  Hidden feature space

(0,1)=1     (1,1)=0              [1,0]=1     [1,1]=0
   +-----------+                    +-----------+
   |           |                    |           |
   |  crossed  |  one line          |  output   |  one line
   |  labels   |  cannot work       |  line can |  can work
   |           |                    |  work     |
   +-----------+                    +-----------+
(0,0)=0     (1,0)=1              [0,0]=0
```

In A3, forward propagation will generalize this computation. Instead of hand-writing one OR neuron and one AND neuron, we will represent a layer as a matrix of weights and a vector of biases. Instead of manually naming each hidden feature, we will compute a hidden activation matrix for a batch. The mechanics are still `X @ W + b`, followed by an activation. Depth is not a different kind of arithmetic; it is the repeated composition of this same arithmetic.

The hidden-layer example also explains why "more neurons" is not merely "more parameters." Each hidden neuron creates a new coordinate system for the next layer. In the raw input space, the output neuron sees `x1` and `x2`; in the hidden space, it sees features like "at least one input is active" and "both inputs are active." The output decision becomes simple only after the first layer changes the questions being asked.

That does not mean every hidden layer is automatically useful. Poorly chosen weights can create useless features, redundant features, or saturated features that throw away too much information. The hand-set weights work because we designed them with the truth table in mind. Later training algorithms will search for useful features from data, which is harder than evaluating a forward pass. For now, the important point is that the forward pass has enough expressive structure to represent XOR.

You should also notice that the two-layer network still uses linear pieces. The hidden layer computes linear scores and thresholds them. The output layer computes a linear score over hidden activations and thresholds it. The extra power comes from composition with nonlinearity. If we stacked only linear transformations without activations, the whole stack would collapse into one linear transformation, and the XOR limitation would remain.

## Part 7: Extending `nn.py` With Neurons and Layers

Now add a small reusable primitive to your growing `nn.py`. The class below keeps the implementation deliberately plain: a neuron owns one weight vector, one bias, and one activation name. It can run on a single example or a batch because NumPy broadcasting handles the bias and the dot product handles the last dimension. The `perceptron_update` method is only for binary step neurons, because the classic update assumes a hard prediction.

```python
import numpy as np


def step(z):
    """Binary step activation: 1 for z >= 0, else 0."""
    return (np.asarray(z) >= 0.0).astype(int)


def sigmoid(z):
    """Sigmoid activation for later modules that need smooth outputs."""
    z = np.asarray(z, dtype=float)
    return 1.0 / (1.0 + np.exp(-z))


class Neuron:
    """One weighted-sum unit with a selectable activation."""

    def __init__(self, n_inputs, activation="step", weights=None, bias=0.0, rng=None):
        self.activation = activation
        if weights is None:
            rng = np.random.default_rng(0) if rng is None else rng
            self.w = rng.normal(loc=0.0, scale=0.1, size=n_inputs)
        else:
            self.w = np.asarray(weights, dtype=float)
        self.b = float(bias)

    def linear(self, x):
        x = np.asarray(x, dtype=float)
        return x @ self.w + self.b

    def forward(self, x):
        z = self.linear(x)
        if self.activation == "step":
            return step(z)
        if self.activation == "sigmoid":
            return sigmoid(z)
        if self.activation == "identity":
            return z
        raise ValueError(f"unknown activation: {self.activation}")

    def predict_one(self, x):
        return int(self.forward(np.asarray(x, dtype=float)))

    def perceptron_update(self, x, target, lr=0.2):
        if self.activation != "step":
            raise ValueError("perceptron_update requires step activation")

        x = np.asarray(x, dtype=float)
        pred = self.predict_one(x)
        error = int(target - pred)
        if error != 0:
            self.w += lr * error * x
            self.b += lr * error
        return error


class Layer:
    """A small collection of neurons evaluated side by side."""

    def __init__(self, neurons):
        self.neurons = list(neurons)

    def forward(self, x):
        outputs = [neuron.forward(x) for neuron in self.neurons]
        return np.stack(outputs, axis=-1)


if __name__ == "__main__":
    X_bool = np.array(
        [
            [0.0, 0.0],
            [0.0, 1.0],
            [1.0, 0.0],
            [1.0, 1.0],
        ]
    )
    y_and = np.array([0, 0, 0, 1])

    neuron = Neuron(2, activation="step", weights=np.zeros(2), bias=0.0)
    for _ in range(4):
        for xi, target in zip(X_bool, y_and):
            neuron.perceptron_update(xi, target)

    print(np.round(neuron.w, 2).tolist(), round(neuron.b, 2))
    print(neuron.forward(X_bool).tolist())

    xor_hidden = Layer(
        [
            Neuron(2, activation="step", weights=[1.0, 1.0], bias=-0.5),
            Neuron(2, activation="step", weights=[1.0, 1.0], bias=-1.5),
        ]
    )
    print(xor_hidden.forward(X_bool).tolist())
```

```text
[0.4, 0.2] -0.4
[0, 0, 0, 1]
[[0, 0], [1, 0], [1, 0], [1, 1]]
```

This `Layer` is intentionally a list of neurons rather than a fully vectorized matrix object. That makes the concept visible: a layer is several neurons reading the same input and producing several outputs. In A3, we will make this more efficient by storing all layer weights in one matrix, but the mental model will stay the same. A matrix layer is just a compact way to evaluate many neurons together.

Keep this code in your scratch `nn.py` and resist the urge to overbuild it. The goal of Block A is not to recreate a production framework on day two. The goal is to understand the smallest pieces so well that the later abstractions feel earned. When you later see a layer with shape `(n_inputs, n_outputs)`, you should be able to point at each column and say, "that is one neuron."

There are a few intentional limitations in this micro-framework. The `Layer` class stores a Python list of neurons, so it is conceptually clear but not the fastest possible representation. The `Neuron` class stores activations by name, which is simple but not as flexible as passing activation objects. The perceptron update lives on the neuron, which is fine for this module but will not be the final shape once losses, gradients, and optimizers arrive. These are good limitations because they keep the code aligned with what you can currently explain.

The interface still creates a useful contract for A3. A learner can call `forward` on a neuron or a layer and receive an output with predictable shape. A single example produces one output per neuron, while a batch produces one column per neuron. Once that contract is stable, later modules can replace the list implementation with matrix-backed layers without changing the conceptual API. This is how small teaching frameworks should evolve: start with clarity, then vectorize when the repeated pattern is obvious.

One final habit: keep tiny verification scripts next to your scratch code. If you add a class and only inspect it through a long notebook, bugs become hard to localize. If you can run AND, OR, and the hand-set XOR forward pass in a few assertions, you have a fast signal that the primitive still behaves. That signal matters because A3 will stack these primitives, and stacked code magnifies small shape mistakes.

## Part 8: Debugging the Perceptron Like an Engineer

When a perceptron behaves strangely, debug it in layers of evidence. Start with the raw score for one example, not with the whole training loop. Compute `w dot x + b` by hand for the first row, then compare it with NumPy. If those disagree, the problem is shape order, dtype conversion, or a transposed array. If the score agrees but the class differs from your expectation, the problem is the activation convention, especially the treatment of exactly zero.

Next, inspect one update. Save the old weights, the old bias, the prediction, the error, and the new parameters after a single example. A positive error should add `eta*x` to the weights and add `eta` to the bias. A negative error should subtract `eta*x` from the weights and subtract `eta` from the bias. If a target of zero increases the score for the same example, the sign is reversed. If the weights change but the bias does not, the boundary can rotate but not shift correctly.

After the single update works, inspect the epoch trace. For a separable Boolean gate, the mistake count should eventually reach zero. It does not need to decrease every epoch, because online updates can temporarily hurt examples that appeared earlier in the same pass. What matters is the eventual zero-mistake epoch. If the mistake count never reaches zero on AND or OR, use the trace to find the first row whose correction is surprising. Do not change the learning rate until the sign and bias behavior are correct.

For XOR, invert the expectation. A zero-mistake epoch would be suspicious because it would contradict the separability proof for one perceptron. In that case, check whether the labels are actually XOR, whether a hidden layer accidentally entered the code, or whether the prediction function is reading stale parameters. This is an important mindset shift: sometimes a passing result is the bug, because the mathematical contract says the model should fail.

Shape logging should be boring and explicit. Write comments such as `X: (4, 2)`, `w: (2,)`, `scores: (4,)`, and `H: (4, 2)` beside the arrays while you are learning. Those comments may feel slow, but they train your eye to read neural-network code. Most beginner mistakes in from-scratch NumPy networks are not deep mathematical failures; they are shape mismatches that accidentally broadcast, flatten, or transpose data in a way the author did not intend.

Finally, keep the boundary interpretation close to the code. A weight update is not just a mutation of two numbers; it moves a line. If the model predicts positive too often, a negative correction lowers the bias and subtracts feature values, pushing the current example toward the negative side. If the model misses a positive example, a positive correction raises the score for that example. Thinking this way makes the update rule feel less like memorized syntax and more like geometry you can reason about.

## Did You Know?

- McCulloch and Pitts used threshold logic to connect simplified neural activity with formal computation, which is why early neural-network history sits close to logic and automata theory.
- The perceptron convergence theorem applies when the data is linearly separable and the learning rate is positive, but it does not promise a useful separator when no separator exists.
- XOR is a parity function on two bits, and parity-style problems are a recurring test of whether a model can represent interactions rather than independent feature effects.
- Stacking linear transformations without nonlinear activations still produces one linear transformation, so depth becomes expressive only when nonlinear steps change the representation between layers.

## Common Mistakes

| Mistake | Problem | Better Approach |
|---|---|---|
| Treating `w dot x + b` as a mysterious neural operation | It hides the fact that the neuron is just a weighted sum plus a threshold, which makes debugging harder. | Write one numeric example by hand, then check that NumPy returns the same score and activation. |
| Forgetting to update the bias | The boundary can rotate through the origin but cannot shift freely, so simple Boolean datasets may fail unnecessarily. | Update `b` with `eta * error` every time the weights are updated. |
| Assuming a failed XOR run needs more epochs | More training cannot fix a model class that cannot represent the target function. | Prove separability or non-separability first, then choose a model with enough representation power. |
| Rounding weights too early when inspecting boundaries | Rounded values can make a score appear exactly zero even when the stored floating-point value is slightly negative or positive. | Use rounded output for display, but verify predictions with the actual arrays in memory. |
| Mixing row and column conventions without checking shapes | A transposed weight matrix can silently produce wrong scores or shape errors once batches enter the code. | Write shape comments beside each array and prefer `X @ w + b` for batch scores in this module. |
| Vectorizing before the scalar rule is understood | A compact matrix expression can hide a wrong sign or missing bias update until later modules become harder to debug. | First verify one hand-worked example and one online correction, then use batch operations for forward computation. |

## Quiz

<details>
<summary>1. Why does the perceptron update add `eta * x` to the weights when the target is `1` but the prediction is `0`?</summary>

The current score was too low for that example, so adding a positive multiple of the input raises `w dot x + b` for the same row on the next pass. The bias update raises the default score as well, which shifts the boundary toward classifying that row as positive. If the example appears again with the same parameters, its score should be larger than before, which is the local correction the perceptron rule is designed to make.

</details>

<details>
<summary>2. What does the equation `w1*x1 + w2*x2 + b = 0` represent in a two-input perceptron?</summary>

It represents the decision boundary where the perceptron is exactly undecided before the step convention is applied. Points on one side have positive scores and become class `1`, while points on the other side have negative scores and become class `0`. In two dimensions that boundary is a line, so the perceptron can only solve labelings that one line can separate cleanly.

</details>

<details>
<summary>3. Why can a single perceptron learn AND and OR but not XOR?</summary>

AND and OR each have labels that can be separated by one line in the square formed by the four binary inputs. XOR places positive labels on opposite corners and negative labels on the other opposite corners, so any single line that helps one positive corner conflicts with another required label. The algebraic contradiction makes this precise: satisfying the two positive single-input corners forces the double-input corner to be positive too, which XOR forbids.

</details>

<details>
<summary>4. What role do hidden units play in the hand-set two-layer XOR network?</summary>

The hidden units transform the raw inputs into intermediate features such as OR and AND. Once those features exist, the output neuron does not need to separate the original checkerboard; it only needs to accept the OR-on, AND-off case and reject the others. This is the representational move behind depth: a later layer can solve a simpler problem because an earlier layer changed the coordinate system.

</details>

<details>
<summary>5. Why is the `Layer` class in this module implemented as a list of `Neuron` objects even though matrix multiplication would be faster?</summary>

The list version makes the concept explicit: a layer is several neurons evaluated side by side on the same input. Later modules can vectorize the implementation after the learner has a concrete mental model for what each column of a weight matrix represents. A teaching micro-framework should make the repeated structure visible before compressing that structure into a more efficient representation.

</details>

<details>
<summary>6. If your AND perceptron never reaches a zero-mistake epoch, what should you inspect before changing the learning rate?</summary>

Inspect one raw score, one prediction, and one update by hand. Confirm that `error = target - prediction`, that a positive error adds `eta*x` and raises the bias, and that a negative error subtracts `eta*x` and lowers the bias. Also check the convention for scores exactly equal to zero. Learning rate tuning is only meaningful after the sign, bias, and shape behavior are correct.

</details>

## Hands-On Exercise

Extend your local `nn.py` with the `Neuron` and `Layer` code from Part 7, then add one short script named `perceptron_checks.py` that imports those primitives and verifies three behaviors. First, train a step neuron on AND until it predicts `[0, 0, 0, 1]`. Second, train a separate step neuron on OR until it predicts `[0, 1, 1, 1]`. Third, build the hand-set two-layer XOR network and verify that it predicts `[0, 1, 1, 0]` without training.

Your script does not need to become a formal test suite yet, but it should fail loudly if any behavior is wrong. Use `assert` statements with clear messages, print the learned weights for AND and OR, and keep the hidden XOR weights hand-set so you can separate "learning a single boundary" from "forward propagating through two layers." If an assertion fails, inspect shapes before changing math.

**Success criteria:**

- [ ] The AND check prints learned parameters and asserts the exact prediction vector `[0, 0, 0, 1]` without changing the target labels.
- [ ] The OR check trains a separate neuron and asserts the exact prediction vector `[0, 1, 1, 1]` without reusing AND weights.
- [ ] The XOR check uses a two-layer hand-set forward pass and asserts `[0, 1, 1, 0]` without calling `perceptron_update` on XOR labels.

```python
import numpy as np

from nn import Layer, Neuron


X = np.array(
    [
        [0.0, 0.0],
        [0.0, 1.0],
        [1.0, 0.0],
        [1.0, 1.0],
    ]
)


def train_gate(labels, epochs=8):
    neuron = Neuron(2, activation="step", weights=np.zeros(2), bias=0.0)
    for _ in range(epochs):
        for xi, target in zip(X, labels):
            neuron.perceptron_update(xi, target)
    return neuron


and_neuron = train_gate(np.array([0, 0, 0, 1]))
or_neuron = train_gate(np.array([0, 1, 1, 1]))

and_pred = and_neuron.forward(X).tolist()
or_pred = or_neuron.forward(X).tolist()

assert and_pred == [0, 0, 0, 1], f"AND failed: {and_pred}"
assert or_pred == [0, 1, 1, 1], f"OR failed: {or_pred}"

xor_hidden = Layer(
    [
        Neuron(2, activation="step", weights=[1.0, 1.0], bias=-0.5),
        Neuron(2, activation="step", weights=[1.0, 1.0], bias=-1.5),
    ]
)
xor_output = Neuron(2, activation="step", weights=[1.0, -2.0], bias=-0.5)

H = xor_hidden.forward(X)
xor_pred = xor_output.forward(H).tolist()
assert xor_pred == [0, 1, 1, 0], f"XOR failed: {xor_pred}"

print("AND weights:", np.round(and_neuron.w, 2).tolist(), round(and_neuron.b, 2))
print("OR weights:", np.round(or_neuron.w, 2).tolist(), round(or_neuron.b, 2))
print("XOR hidden features:", H.tolist())
print("all checks passed")
```

```text
AND weights: [0.4, 0.2] -0.4
OR weights: [0.2, 0.2] -0.2
XOR hidden features: [[0, 0], [1, 0], [1, 0], [1, 1]]
all checks passed
```

## Learner check

> | 1.1.2 | [The Neuron & Perceptron from Scratch](/ai-ml-engineering/deep-learning/module-1.1.2-neuron-from-scratch/) |

## Key Takeaways

- A neuron computes `z = w dot x + b` and then applies an activation, so the first debugging question is always whether the shapes and score arithmetic are correct.
- The perceptron learning rule updates only when a prediction is wrong, using `w <- w + eta * error * x` and `b <- b + eta * error`.
- AND and OR are learnable by one perceptron because their labels can be separated by one straight decision boundary in the two-input square.
- XOR is not learnable by one perceptron because the required labels create a contradiction for any single boundary, not because the training loop is too short.
- A two-layer network solves XOR by constructing hidden features first, which previews the forward-propagation machinery that A3 will make systematic.

## Sources

- Warren S. McCulloch and Walter Pitts, "A Logical Calculus of the Ideas Immanent in Nervous Activity": https://doi.org/10.1007/BF02478259
- Frank Rosenblatt, "The Perceptron: A Probabilistic Model for Information Storage and Organization in the Brain": https://pubmed.ncbi.nlm.nih.gov/13602029/
- Marvin Minsky and Seymour Papert, "Perceptrons: An Introduction to Computational Geometry": https://papers.baulab.info/papers/Minsky-1969.pdf
- Stanford CS231n, "Neural Networks Part 1: Setting up the Architecture": https://cs231n.github.io/neural-networks-1/
- Dive into Deep Learning, "Multilayer Perceptrons": https://d2l.ai/chapter_multilayer-perceptrons/index.html
- NumPy documentation for `numpy.dot`: https://numpy.org/doc/stable/reference/generated/numpy.dot.html
- NumPy documentation for `numpy.matmul`: https://numpy.org/doc/stable/reference/generated/numpy.matmul.html
- Ian Goodfellow, Yoshua Bengio, and Aaron Courville, "Deep Learning" chapter on deep feedforward networks: https://www.deeplearningbook.org/contents/mlp.html
- Michael Nielsen, "Neural Networks and Deep Learning" chapter 1: http://neuralnetworksanddeeplearning.com/chap1.html
- scikit-learn documentation, perceptron notes in linear models: https://scikit-learn.org/stable/modules/linear_model.html#perceptron
- Cornell CS4780 lecture notes on the perceptron: https://www.cs.cornell.edu/courses/cs4780/2018fa/lectures/lecturenote03.html
- Andrej Karpathy, `micrograd`: https://github.com/karpathy/micrograd

## Next Module

**[A3 — Forward Propagation in MLPs](/ai-ml-engineering/deep-learning/module-1.1.3-forward-propagation-mlp/)** turns the hand-set two-layer XOR example into the general forward-propagation pattern for multi-layer perceptrons. The important preparation from this module is the contract that a neuron or layer receives an input array, computes `linear = input @ weights + bias`, applies an activation, and returns an output whose shape the next layer can consume.
