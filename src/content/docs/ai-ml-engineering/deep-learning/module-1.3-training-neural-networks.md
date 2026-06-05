---
title: "The Training Loop: From One Step to a Reproducible Run"
slug: ai-ml-engineering/deep-learning/module-1.3-training-neural-networks
sidebar:
  order: 1004
---

Hypothetical scenario: A model retraining job finishes without an exception, writes a checkpoint, and sends a neat metrics summary to the team channel. The training loss went down, so the run looks healthy at first glance. The next morning, validation accuracy is worse than the baseline, the resumed run uses a different learning rate than the interrupted run, and nobody can reproduce the "good" curve from yesterday because the random split changed. Nothing in that story requires a new derivative formula. It is a training-loop failure: the loop did not clearly separate training from validation, did not save enough state to resume, and did not make the experiment repeatable enough to debug.

This module treats the training loop as an engineering object, not as boilerplate around the model. In Block A you wrote the NumPy loop yourself: mini-batches entered, logits came out, stable softmax cross-entropy produced a scalar, backprop filled gradients, and `W -= lr * dW` updated parameters. In B1 you crossed the bridge to PyTorch primitives: `torch.Tensor`, `torch.autograd`, `nn.Linear`, `nn.CrossEntropyLoss`, `DataLoader`, and `torch.optim.SGD`. B2 now asks the practical question: how do those primitives become a run you can trust, stop, resume, compare, and explain?

## Learning Outcomes

By the end of this module, you will be able to:

- Implement the canonical PyTorch training step in the correct order, then map each line back to the A7 manual NumPy update and B1's tensor, autograd, module, loss, and optimizer primitives.
- Debug train/validation loop boundaries by verifying `.train()` mode during parameter updates, `.eval()` mode during validation, and `with torch.no_grad():` around evaluation-only forward passes.
- Design checkpoint dictionaries that restore model parameters, optimizer state, scheduler state, epoch counters, and best validation metrics rather than only reloading weights.
- Compare reproducibility controls, including Python, NumPy, PyTorch, `DataLoader` worker seeding, and deterministic-algorithm settings, while explaining why bit-identical results across hardware are not guaranteed.
- Implement metric logging, overfit-one-batch sanity checks, gradient accumulation, and early-stopping hooks, then evaluate whether the resulting script can be interrupted, resumed, validated, and audited with enough evidence to explain a failed or successful run.

## Why This Module Matters

The shortest PyTorch training loop is easy to memorize and easy to get subtly wrong. A single missing `optimizer.zero_grad(set_to_none=True)` changes the effective gradient from "this batch" to "this batch plus whatever came before." A single missing `model.eval()` makes validation depend on stochastic dropout masks and batch-normalization batch statistics. A checkpoint that saves only `model.state_dict()` can restart inference, but it cannot faithfully resume training because momentum buffers, adaptive optimizer moments, scheduler counters, and best-metric history are missing. The code still runs, which is why these bugs are more dangerous than syntax errors.

The loop is also where the Block A mental model becomes operational. `loss.backward()` is the same reverse graph walk your A8 scalar `Value.backward()` performed, except the nodes are tensor operations and PyTorch owns the vector-Jacobian products. `nn.CrossEntropyLoss` is the stable softmax cross-entropy from A5, except the API takes logits and integer class labels instead of an explicit one-hot target matrix. `torch.optim.SGD.step()` is the A7 line `W -= lr * dW`, except the optimizer discovers registered parameters from the `nn.Module` tree and applies the update consistently. PyTorch replaces your hand-written code line-for-line; it does not remove the need to know which line owns which responsibility.

Think of the training loop like a flight checklist. The engine design matters, but crews still use a fixed sequence because order prevents silent state mistakes. In a training step, the checklist is `zero_grad -> forward -> loss -> backward -> step`. In an epoch, the checklist is `train loop -> validation loop -> metrics -> checkpoint -> scheduler/early-stop decision`, with the exact scheduler placement depending on the scheduler type. In a reproducible run, the checklist starts before the first batch with seeds, dataset split policy, device choice, and run metadata. You are not adding ceremony for its own sake; you are making the run inspectable.

This module deliberately avoids re-teaching autograd and `nn.Module`. B1 already covered the bridge, and Block A already made the math visible. Here the emphasis is training discipline: what happens to gradients between steps, what happens to mode-dependent modules between train and validation, what state is needed to continue a run, what numbers should be logged, and what small sanity check should happen before a long job consumes real compute. Optimizer internals belong to B4, initialization to B3, regularization to B5, normalization to B6, detailed diagnostics to B7, and precision to B8. B2 owns the loop that holds all of them together.

## Part 1: The Canonical Training Step

The smallest trustworthy PyTorch training step has five operations in a strict order. First, clear gradients from the previous step. Second, run the model forward on the current mini-batch. Third, compute a scalar loss from model outputs and targets. Fourth, ask autograd to backpropagate through the computation graph. Fifth, ask the optimizer to update the parameters using the gradients that were just computed. This sequence is short, but every line has stateful consequences.

```text
A7 NumPy loop                           B2 PyTorch training step
--------------------------------------------------------------------------------
dW, db = 0 for this batch            -> optimizer.zero_grad(set_to_none=True)
logits = layer.forward(xb)           -> logits = model(inputs)
loss = stable_softmax_ce(logits, y)  -> loss = loss_fn(logits, targets)
backward cached VJPs through layers  -> loss.backward()
W -= lr * dW; b -= lr * db           -> optimizer.step()
```

The order matters because PyTorch gradients accumulate by default. Accumulation is useful for gradient accumulation, multi-loss objectives, and some distributed training patterns, but it is wrong for ordinary one-batch-one-step training unless you reset at the start of each step. The current PyTorch optimizer API defaults `zero_grad` to `set_to_none=True`, which sets `.grad` fields to `None` instead of allocating zero tensors. That saves memory and lets you detect parameters that received no gradient, but it also means manual gradient inspection must handle `None` explicitly.

```python
import torch
from torch import nn

w = nn.Parameter(torch.tensor([[0.5]]))  # shape: [1, 1]
optimizer = torch.optim.SGD([w], lr=0.1)
loss_fn = nn.MSELoss()

x = torch.tensor([[2.0]])      # shape: [batch=1, features=1]
target = torch.tensor([[0.0]]) # shape: [batch=1, outputs=1]

optimizer.zero_grad(set_to_none=True)
prediction = x @ w             # 2.0 * 0.5 = 1.0
loss = loss_fn(prediction, target)
loss.backward()

print(f"loss before step: {loss.item():.1f}")
print(f"gradient dloss/dw: {w.grad.item():.1f}")

optimizer.step()
print(f"w after step: {w.item():.1f}")
```

The expected output is `loss before step: 1.0`, `gradient dloss/dw: 4.0`, and `w after step: 0.1`. The derivative is the same calculation you would do by hand: `loss = (2w - 0)^2`, so `dloss/dw = 2 * (2w) * 2 = 4` when `w = 0.5`. The SGD update is the A7 update rule with a registered parameter: `w = 0.5 - 0.1 * 4 = 0.1`. PyTorch did not invent a new rule; it recorded the operations and applied the chain rule you already implemented.

A model-agnostic training step only needs to make batch movement and return values explicit. Notice that the function sets training mode before the forward pass, moves both inputs and targets to the same device as the model, clears gradients before building the graph, and returns detached Python numbers rather than live tensors. Returning live tensors from logging code can accidentally keep graphs alive and increase memory across an epoch.

```python
def train_step(model, batch, loss_fn, optimizer, device):
    model.train()

    inputs, targets = batch
    inputs = inputs.to(device)
    targets = targets.to(device)

    optimizer.zero_grad(set_to_none=True)
    logits = model(inputs)
    loss = loss_fn(logits, targets)
    loss.backward()
    optimizer.step()

    batch_size = inputs.shape[0]
    return loss.detach().item(), batch_size
```

The graph lifecycle is worth making concrete. The forward pass creates a dynamic graph because model parameters require gradients. The scalar loss points to the output of that graph. `loss.backward()` walks the graph backward, accumulates gradients into leaf parameters, and normally frees intermediate buffers that are no longer needed. `optimizer.step()` reads parameter `.grad` fields and mutates parameter values. If you call `backward()` twice on the same graph without retaining it, PyTorch complains because the temporary buffers were already released; if you retain every graph for logging, memory grows because you told the runtime not to clean up.

```text
inputs + parameters
        |
        v
   model forward  ---- dynamic graph records tensor ops
        |
        v
   scalar loss    ---- one number that still points to the graph
        |
        v
   backward()     ---- parameter.grad fields receive accumulated gradients
        |
        v
   optimizer.step ---- parameters are mutated, graph is no longer needed
```

The common beginner reversal is to call `optimizer.step()` before `loss.backward()`. That step uses old gradients, `None` gradients, or gradients from a previous batch, depending on what happened earlier. Another common reversal is to call `zero_grad` after `backward()` and before `step()`, which erases exactly the gradients the optimizer was supposed to use. Some PyTorch tutorials clear gradients after `step()` so the next iteration starts clean; this module uses the equally valid and more checklist-friendly pattern of clearing before the forward pass. The invariant is the same: each optimizer step must consume exactly the gradients intended for that step.

`nn.CrossEntropyLoss` deserves one boundary reminder because it is the loss most learners use first. It expects raw logits shaped `[batch, classes]` and class-index targets shaped `[batch]` with integer dtype. Do not apply `softmax` before passing logits to this loss. In A5 you wrote stable softmax cross-entropy manually to understand the math; in PyTorch the loss combines the stable log-softmax and negative-log-likelihood pieces internally, so passing probabilities instead of logits weakens numerical stability and changes gradient behavior.

The step also defines where it is safe to observe state. Before `backward()`, parameter gradients should usually be `None` because they were cleared and the current graph has not propagated anything yet. After `backward()`, gradients should be finite for parameters that participated in the loss; parameters with `None` gradients may be frozen, unused, detached, or behind a branch that did not execute. After `optimizer.step()`, parameter values should change if the learning rate is nonzero and the gradients are nonzero. These three checkpoints are the first debugging probes for a model that "runs but does not learn," and they are much cheaper than launching another full experiment.

In A7 you could inspect `dW` arrays directly because every layer stored its own backward result. PyTorch centralizes that evidence in the `.grad` field of each leaf parameter. That is why a practical training-step smoke test often prints a small table of parameter names, gradient norms, and update norms for one batch. You do not need that table in every production run, but you should know how to produce it when loss is flat. If all gradient norms are zero or `None`, the problem is upstream of the optimizer. If gradients are finite and parameters still do not move, the problem is usually optimizer configuration, frozen parameters, or a learning rate of zero.

## Part 2: The Full Loop: Epochs, Batches, and Validation

A real training run wraps the training step in two loops: epochs over the dataset and mini-batches inside each epoch. The training `DataLoader` usually shuffles examples because mini-batch SGD relies on different stochastic estimates of the full-dataset gradient. The validation `DataLoader` usually does not need shuffling because validation is a measurement pass, not an optimization pass. A separate validation loop is not optional. If the same loop both updates parameters and reports "validation" metrics, you are measuring training behavior under a misleading name.

The complete skeleton below uses a synthetic classification problem so the code is runnable without downloading data. It is intentionally model-agnostic: replace `TinyClassifier` and the dataset with your own module and loaders, and the loop contract stays the same. The model itself is not the lesson; the lesson is the shape of the run. Inputs are `[batch, features]`, logits are `[batch, classes]`, and targets are `[batch]`, exactly the CrossEntropyLoss contract from B1 and A5.

```python
import random
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset, random_split


class TinyClassifier(nn.Module):
    def __init__(self, in_features=8, hidden=32, num_classes=3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, hidden),
            nn.ReLU(),
            nn.Linear(hidden, num_classes),
        )

    def forward(self, x):
        return self.net(x)


def make_synthetic_dataset(n=900, in_features=8, num_classes=3, seed=123):
    generator = torch.Generator().manual_seed(seed)
    x = torch.randn(n, in_features, generator=generator)
    teacher = torch.randn(in_features, num_classes, generator=generator)
    logits = x @ teacher
    y = logits.argmax(dim=1)
    return TensorDataset(x, y)


def make_loaders(batch_size=64, seed=123):
    dataset = make_synthetic_dataset(seed=seed)
    split_generator = torch.Generator().manual_seed(seed)
    train_ds, val_ds = random_split(dataset, [720, 180], generator=split_generator)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True,
                              generator=torch.Generator().manual_seed(seed))
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)
    return train_loader, val_loader


def accuracy_from_logits(logits, targets):
    predictions = logits.argmax(dim=1)
    return (predictions == targets).sum().item()


def train_one_epoch(model, loader, loss_fn, optimizer, device):
    model.train()
    total_loss = 0.0
    total_correct = 0
    total_examples = 0

    for inputs, targets in loader:
        inputs = inputs.to(device)
        targets = targets.to(device)

        optimizer.zero_grad(set_to_none=True)
        logits = model(inputs)
        loss = loss_fn(logits, targets)
        loss.backward()
        optimizer.step()

        batch_size = inputs.shape[0]
        total_loss += loss.detach().item() * batch_size
        total_correct += accuracy_from_logits(logits.detach(), targets)
        total_examples += batch_size

    return {
        "loss": total_loss / total_examples,
        "accuracy": total_correct / total_examples,
    }


@torch.no_grad()
def evaluate(model, loader, loss_fn, device):
    model.eval()
    total_loss = 0.0
    total_correct = 0
    total_examples = 0

    for inputs, targets in loader:
        inputs = inputs.to(device)
        targets = targets.to(device)

        logits = model(inputs)
        loss = loss_fn(logits, targets)

        batch_size = inputs.shape[0]
        total_loss += loss.item() * batch_size
        total_correct += accuracy_from_logits(logits, targets)
        total_examples += batch_size

    return {
        "loss": total_loss / total_examples,
        "accuracy": total_correct / total_examples,
    }


def fit(epochs=5, seed=123):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    train_loader, val_loader = make_loaders(seed=seed)

    model = TinyClassifier().to(device)
    loss_fn = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.2)

    history = []
    for epoch in range(1, epochs + 1):
        train_metrics = train_one_epoch(model, train_loader, loss_fn, optimizer, device)
        val_metrics = evaluate(model, val_loader, loss_fn, device)

        row = {
            "epoch": epoch,
            "train_loss": train_metrics["loss"],
            "train_acc": train_metrics["accuracy"],
            "val_loss": val_metrics["loss"],
            "val_acc": val_metrics["accuracy"],
        }
        history.append(row)
        print(
            f"epoch={epoch:02d} "
            f"train_loss={row['train_loss']:.4f} train_acc={row['train_acc']:.3f} "
            f"val_loss={row['val_loss']:.4f} val_acc={row['val_acc']:.3f}"
        )

    return model, history


if __name__ == "__main__":
    fit()
```

The separation between `train_one_epoch` and `evaluate` is more than style. The training function mutates model parameters and therefore must build a graph, call `backward()`, and call `optimizer.step()`. The evaluation function measures the current model and therefore must not build a backward graph or mutate parameters. The `@torch.no_grad()` decorator is equivalent to wrapping the function body in `with torch.no_grad():`; it disables gradient recording for inference-style code and reduces memory use because PyTorch does not keep backward buffers.

The metric aggregation multiplies each batch loss by `batch_size` before averaging. That small detail matters whenever the last batch is smaller than the others. If you simply average per-batch losses, a final batch of 17 examples receives the same weight as a full batch of 64 examples. The difference may be small, but it is avoidable, and careful aggregation makes metrics easier to compare across batch sizes. Accuracy is counted as correct examples divided by total examples for the same reason.

Validation is not the test set. The validation split is used repeatedly during development to choose checkpoints, tune early-stopping behavior, and decide whether the training run is improving. The test set should remain untouched until the model-selection process is finished. This module focuses on the train/validation loop because the test protocol depends on project policy, but the engineering rule is stable: do not update parameters on validation examples, and do not make repeated design decisions from the final test set.

Scheduler placement depends on the scheduler. Some schedulers, such as `StepLR`, are commonly stepped once per epoch after the optimizer has completed that epoch. Others, such as `OneCycleLR`, are stepped every optimizer update. `ReduceLROnPlateau` is stepped after validation because it needs the validation metric. B4 will teach learning-rate dynamics in detail; for B2, the important habit is to state when the scheduler moves and to save its state so a resumed run does not repeat or skip scheduler history.

The epoch boundary is also the right place to make run-level decisions because it is the first moment when training evidence and validation evidence are both available for the same model state. If you save a checkpoint before validation, the checkpoint does not correspond to the validation metric you are about to report. If you update a scheduler from validation loss before writing the checkpoint, the saved scheduler state represents the next epoch rather than the state that produced the metric. Either policy can be valid when documented, but hidden ordering makes resumes confusing. A clean loop chooses an order and makes the checkpoint represent that order.

For small local experiments, printing one formatted line per epoch is enough. For longer jobs, write structured records such as JSON Lines, TensorBoard events, or another metrics format your platform can ingest. The record should include epoch or step, train loss, validation loss, task metric, learning rate, checkpoint path, and whether the checkpoint became the new best. That small schema turns the loop into evidence. When a run fails, you can ask whether validation degraded before the learning-rate change, whether the best checkpoint was written, and whether the resumed run continued from the expected epoch.

## Part 3: `.train()` and `.eval()` Mode Discipline

`model.train()` and `model.eval()` toggle the module's `training` flag recursively through child modules. They do not mean "compute gradients" and "do not compute gradients." Gradient recording is controlled by autograd context, such as normal execution, `with torch.no_grad():`, or inference-specific contexts. The mode toggle affects modules whose forward behavior changes between training and evaluation. The two most important examples are dropout and batch normalization, which B5 and B6 teach in depth. In B2, the key point is the mode bug: validation can be wrong even when gradients are disabled if the module remains in training mode.

Dropout randomly zeroes activations during training and becomes an identity operation during evaluation. Batch normalization uses batch statistics during training and running statistics during evaluation when running statistics are tracked. Those behaviors are exactly why the validation loop calls both `model.eval()` and `torch.no_grad()`. The first line changes layer behavior; the second line changes graph recording. They solve different problems and both belong in evaluation code.

```python
import torch
from torch import nn

torch.manual_seed(7)
dropout = nn.Dropout(p=0.5)
x = torch.ones(12)

dropout.train()
train_a = dropout(x)
train_b = dropout(x)

dropout.eval()
eval_a = dropout(x)
eval_b = dropout(x)

print("training outputs differ:", not torch.equal(train_a, train_b))
print("evaluation outputs equal:", torch.equal(eval_a, eval_b))
print("evaluation is identity:", torch.equal(eval_a, x))
```

The exact training outputs depend on the random mask, but the pattern is stable: training mode samples masks, evaluation mode does not. If you forget `model.eval()` before validation, the validation metric becomes a noisy measurement of training-time behavior. If you forget `model.train()` after validation, the next epoch may train with dropout disabled and batch normalization frozen in evaluation behavior. Both mistakes can produce plausible metrics for a while, which is why the mode calls should be part of named functions rather than scattered across notebook cells.

| Concern | `model.train()` / `model.eval()` | `with torch.no_grad():` |
|---|---|---|
| Primary job | Switch mode-dependent module behavior | Disable recording of backward graph |
| Affects dropout | Yes, active in train and identity in eval | No, dropout follows module mode |
| Affects BatchNorm | Yes, batch stats in train and running stats in eval | No, statistics behavior follows module mode |
| Affects gradient computation | Not directly | Yes, operations stop tracking gradients |
| Belongs in training loop | `model.train()` before train batches | Usually no, because training needs gradients |
| Belongs in validation loop | `model.eval()` before validation batches | Yes, because validation does not call backward |

The order inside validation is simple: set eval mode, enter no-grad, run forward passes, aggregate metrics, and leave the function. You do not need to set the model back to training mode at the end of `evaluate` if the next call to `train_one_epoch` always begins with `model.train()`. That style makes each function locally responsible for its required mode and avoids hidden dependence on what the previous function happened to do.

One subtle point is that `model.eval()` changes behavior only for modules that implement mode-specific logic. A plain `nn.Linear` layer returns the same values in train and eval mode. That is why a mode bug may remain invisible in a small MLP and appear later when you add dropout in B5 or batch normalization in B6. Build the habit before the architecture needs it. It costs one line and prevents a class of failures that are painful to diagnose after a long run.

## Part 4: Checkpointing and Resuming

A checkpoint is not just a file with weights. It is a snapshot of the training state needed to continue the run with the same optimization trajectory. For inference, saving `model.state_dict()` is enough because you only need learned parameters and persistent buffers. For training, PyTorch's saving-and-loading guidance is explicit that a general checkpoint should save more than the model state: optimizer state matters because optimizers keep internal buffers and hyperparameter state while training. If you use a scheduler, its counter matters too. If you track "best validation loss," that metric matters because early stopping and best-checkpoint selection depend on it.

The minimal training checkpoint for this module contains five fields: model state, optimizer state, scheduler state or `None`, epoch, and best metric. The scheduler is optional because not every run has one, but the key should still exist so load code has a stable shape. This pattern also leaves room for run metadata such as a seed, git SHA, dataset version, or hyperparameters, but avoid stuffing large datasets or arbitrary Python objects into the checkpoint. The file should restore training state, not become a hidden experiment database.

```python
from pathlib import Path
import torch


def save_checkpoint(path, model, optimizer, scheduler, epoch, best_metric):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "scheduler_state_dict": scheduler.state_dict() if scheduler is not None else None,
            "epoch": epoch,
            "best_metric": float(best_metric),
        },
        path,
    )


def load_checkpoint(path, model, optimizer, scheduler, device):
    checkpoint = torch.load(path, map_location=device, weights_only=True)

    model.load_state_dict(checkpoint["model_state_dict"])
    optimizer.load_state_dict(checkpoint["optimizer_state_dict"])

    scheduler_state = checkpoint.get("scheduler_state_dict")
    if scheduler is not None and scheduler_state is not None:
        scheduler.load_state_dict(scheduler_state)

    start_epoch = int(checkpoint["epoch"]) + 1
    best_metric = float(checkpoint["best_metric"])
    return start_epoch, best_metric
```

The load order assumes you have already reconstructed the model, moved it to the target device, constructed the optimizer from the model parameters, and constructed the scheduler from the optimizer. Construct the scheduler from the optimizer BEFORE loading any state, then load the saved `state_dict`s in order — model, optimizer, scheduler — and resume at `epoch + 1`. Most schedulers (e.g. `StepLR`) do not change the optimizer's learning rate at construction time; a few (e.g. `OneCycleLR`) set the initial LR when created, which is the specific case where construction order versus state-load order matters. Loading in the model → optimizer → scheduler order is the safe sequence in all cases.

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = TinyClassifier().to(device)
optimizer = torch.optim.SGD(model.parameters(), lr=0.2)
scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)
train_loader, val_loader = make_loaders(seed=123)
loss_fn = nn.CrossEntropyLoss()

save_checkpoint(
    "checkpoints/best.pt",
    model=model,
    optimizer=optimizer,
    scheduler=scheduler,
    epoch=0,
    best_metric=float("inf"),
)

start_epoch, best_val_loss = load_checkpoint(
    "checkpoints/best.pt",
    model=model,
    optimizer=optimizer,
    scheduler=scheduler,
    device=device,
)

print(start_epoch, best_val_loss)
```

The common bug is saving the best model weights but not the optimizer or scheduler state, then calling that a resume checkpoint. That is a valid inference checkpoint and a weak training checkpoint. With SGD momentum, the optimizer's velocity buffers affect the next update. With Adam or AdamW, first and second moment estimates shape every update. With schedulers, the current learning rate may depend on how many steps or epochs have already happened. Reloading weights while resetting those states creates a new run that starts from old weights but follows a different trajectory.

Best-checkpoint handling is a separate decision from periodic checkpointing. Periodic checkpoints answer "can I resume after interruption?" Best checkpoints answer "which model should I deploy or evaluate after training?" A robust run often writes both: a latest checkpoint every epoch or every fixed number of steps, and a best checkpoint only when validation improves. For small teaching runs a single best checkpoint is enough to learn the mechanism, but production jobs should choose a policy that matches failure risk and storage constraints.

If exact stochastic replay matters, checkpointing gets more complicated because random-number-generator states and sampler positions matter. This module does not require an exact mid-epoch replay mechanism, and many production teams accept epoch-boundary resumes because they are simpler and reliable enough. Be honest about that boundary. A checkpoint that restores model, optimizer, scheduler, epoch, and best metric can resume training correctly at an epoch boundary. It does not guarantee bit-identical continuation of every augmentation, shuffle, and kernel choice unless you also control and restore those sources of randomness.

Checkpoint files should be treated as write-once artifacts for a particular run state. If a process can be interrupted while writing, prefer writing to a temporary path and then renaming it into place so readers do not see a half-written file. If storage is remote, understand whether the rename operation is atomic for that storage backend before relying on it for failure recovery. This module stays local and uses `torch.save` directly, but the habit scales: checkpointing is part of the failure model of a training system, not a decorative line at the end of an epoch.

The checkpoint should also be load-tested early. A run that saves checkpoints for six hours and only discovers a load error after interruption did not really have checkpointing. During development, save a checkpoint after a tiny epoch, create a fresh model, optimizer, and scheduler, load it, and run one more training step. That test catches mismatched model definitions, missing scheduler state, bad device mapping, and accidental dependence on in-memory variables. It is the checkpoint equivalent of overfitting one batch: prove the recovery path before you need it.

## Part 5: Reproducibility Without False Promises

Reproducibility starts before training. Set Python's `random` seed if your dataset, split code, or transforms use it. Set NumPy's seed if preprocessing or dataset code uses NumPy randomness. Set PyTorch's seed because model initialization, tensor sampling, dropout masks, and PyTorch samplers may use it. If you use a `DataLoader` with worker processes, seed the worker libraries and pass a `torch.Generator` so shuffling and worker base seeds are controlled. These steps do not make every run identical across all machines, but they remove avoidable randomness from the script.

```python
import random
import numpy as np
import torch


def seed_everything(seed, deterministic=False):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    torch.use_deterministic_algorithms(deterministic)
    if deterministic and torch.backends.cudnn.is_available():
        torch.backends.cudnn.benchmark = False
```

PyTorch's reproducibility documentation is careful: completely reproducible results are not guaranteed across releases, commits, platforms, or even CPU versus GPU execution when the same seeds are used. That caveat is not legal fine print; it is a numerical reality. Floating-point reductions can happen in different orders, backend libraries can select different kernels, and deterministic alternatives may not exist for every operation. `torch.use_deterministic_algorithms(True)` asks PyTorch to use deterministic algorithms when available and to raise an error when only nondeterministic implementations are available, but PyTorch also notes that deterministic operations often run slower.

The tradeoff is a policy decision. During debugging, deterministic algorithms can save hours because two runs with the same seed differ less, making regressions easier to isolate. During high-throughput training, strict determinism can reduce performance or block useful operations. A pragmatic workflow is to keep a deterministic debug mode for small reproductions, record seeds and versions for every serious run, and use multiple seeds for conclusions that depend on model quality rather than on debugging a specific failure.

`DataLoader` worker seeding is the place where many "I set the seed" claims fail. Worker processes may call NumPy or Python randomness inside dataset code or transforms. PyTorch documents the pattern: derive a worker seed from `torch.initial_seed()`, use it to seed NumPy and Python in that worker, and pass a seeded `torch.Generator` to the loader. The generator controls random sampling and the worker base seed; the worker function aligns other libraries with that seed.

```python
def seed_worker(worker_id):
    worker_seed = torch.initial_seed() % 2**32
    np.random.seed(worker_seed)
    random.seed(worker_seed)


generator = torch.Generator()
generator.manual_seed(123)

train_loader = DataLoader(
    make_synthetic_dataset(seed=123),
    batch_size=64,
    shuffle=True,
    num_workers=2,
    worker_init_fn=seed_worker,
    generator=generator,
)
```

Reproducibility also includes what you write down. A useful run record includes the seed, PyTorch version, device type, dataset version or split seed, model hyperparameters, optimizer settings, scheduler settings, and checkpoint path. If the run is part of a larger platform workflow, record the container image or environment lockfile and the git commit as well. KubeDojo will eventually connect this to platform-level training workflows, but the local habit starts here: a metric curve without run context is a story you cannot verify later.

One more practical boundary: validation reproducibility depends on validation data order only if your metric aggregation is order-sensitive or your validation code has hidden state. For ordinary loss and accuracy, validation shuffling is unnecessary. Leaving it off makes metric traces easier to compare and removes one source of accidental variance. Training shuffling remains useful because the mini-batch sequence influences optimization, which is exactly why it should be seeded and recorded.

Reproducibility is strongest when the dataset split is an artifact rather than an accident. A split created by `random_split(..., generator=seeded_generator)` is reproducible as long as the dataset order is stable, but a later dataset refresh can still change which examples land in validation. For serious experiments, record the dataset version and either persist the split indices or make the split rule deterministic from stable example identifiers. The seed answers "how did the random process run"; the data version answers "what did the random process run on." You need both to compare runs honestly.

Do not confuse deterministic debugging with scientific confidence. A single deterministic seed can make a bug reproducible, but it can also hide the fact that a training recipe is fragile across seeds. Once the loop is correct, important claims about model quality should be checked across a small seed sweep when compute allows. That sweep belongs above the single-run loop, but the loop must expose the seed and write metrics consistently so the sweep can aggregate results without guessing which run produced which checkpoint.

## Part 6: Metrics, Sanity Checks, Accumulation, and Stopping

The training loop should report at least a training loss, a validation loss, and one task metric that a human can understand. For classification, accuracy is often a first metric, even when it is not sufficient for imbalanced datasets. For regression, mean absolute error may be more interpretable than mean squared error. The important engineering habit is to log both the objective the optimizer sees and a metric that reflects the task. A decreasing training loss with a flat validation metric is not automatically a bug, but it is evidence that needs interpretation.

Logging should detach values from the graph. Use `loss.item()` for scalar losses and count metrics from detached logits or no-grad validation outputs. If you store `loss` tensors directly in a list during training, each tensor may keep references to the graph that produced it, and memory can grow across the epoch. This is the same graph-lifetime issue from Part 1, now expressed through logging. Python numbers, detached tensors, and no-grad validation outputs are safer metric artifacts than live graph-connected tensors.

Before a long run, overfit one batch. This sanity check is old practical wisdom, popularized in modern neural-network debugging guides such as Karpathy's training recipe and echoed in CS231n: if a sufficiently expressive model cannot memorize a tiny batch with regularization disabled, the full training job is not worth starting. The failure usually points to a data/label mismatch, wrong loss contract, missing gradient, frozen parameter, impossible learning rate, or mode bug. B7 will turn this into a full diagnostic playbook; B2 uses it as the first smoke test for the loop.

```python
def overfit_one_batch(model, loader, loss_fn, optimizer, device, steps=200):
    model.train()
    inputs, targets = next(iter(loader))
    inputs = inputs.to(device)
    targets = targets.to(device)

    losses = []
    for _ in range(steps):
        optimizer.zero_grad(set_to_none=True)
        logits = model(inputs)
        loss = loss_fn(logits, targets)
        loss.backward()
        optimizer.step()
        losses.append(loss.detach().item())

    return losses
```

Read this function as a contract test, not as a regular training method. It intentionally reuses the same batch for many updates because the question is whether gradients, labels, loss, and optimizer updates can cooperate on the easiest possible task. If your model includes dropout or heavy data augmentation, disable those influences for the check or use a model variant without them. If the one-batch loss cannot drop sharply, do not proceed to a full dataset and hope the problem disappears.

Gradient accumulation is another loop mechanism that belongs here because it changes when `optimizer.step()` happens. Suppose GPU memory fits a micro-batch of 32 examples, but you want the gradient signal of an effective batch of 128 examples. You can run four forward/backward passes, divide each loss by four, accumulate gradients, then step once. Dividing by the accumulation count preserves the gradient scale you would get from a mean loss over the larger batch. Without that division, the effective gradient is four times larger, which also changes the effective learning rate. B4 will discuss learning-rate scaling; B2 gives you the loop pattern.

```python
def train_one_epoch_with_accumulation(
    model,
    loader,
    loss_fn,
    optimizer,
    device,
    accumulation_steps=4,
):
    model.train()
    optimizer.zero_grad(set_to_none=True)

    total_loss = 0.0
    total_examples = 0

    for batch_idx, (inputs, targets) in enumerate(loader):
        inputs = inputs.to(device)
        targets = targets.to(device)

        logits = model(inputs)
        loss = loss_fn(logits, targets) / accumulation_steps
        loss.backward()

        if (batch_idx + 1) % accumulation_steps == 0:
            optimizer.step()
            optimizer.zero_grad(set_to_none=True)

        batch_size = inputs.shape[0]
        total_loss += loss.detach().item() * accumulation_steps * batch_size
        total_examples += batch_size

    if len(loader) % accumulation_steps != 0:
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)

    return {"loss": total_loss / total_examples}
```

The leftover step at the end handles loaders whose length is not divisible by `accumulation_steps`, but it is slightly under-scaled because those leftover gradients were divided as if a full accumulation group existed. For production code, prefer `drop_last=True` when exact accumulation groups matter, or scale the last group by its actual size with a slightly more complex loop. That nuance is a perfect example of training engineering: a simple pattern is correct under stated assumptions, and those assumptions should be visible.

Early stopping is a validation-driven loop hook. It watches a validation metric, counts how many consecutive checks have failed to improve by at least `min_delta`, and stops when that count reaches `patience`. B5 will cover the regularization interpretation; here the point is mechanism and checkpoint discipline. If you stop because validation stopped improving, restore the best checkpoint rather than leaving the model at the final, possibly worse epoch.

```python
class EarlyStopping:
    def __init__(self, patience=3, min_delta=0.0):
        self.patience = patience
        self.min_delta = min_delta
        self.best = float("inf")
        self.bad_epochs = 0

    def step(self, metric):
        improved = metric < self.best - self.min_delta
        if improved:
            self.best = metric
            self.bad_epochs = 0
            return False, True

        self.bad_epochs += 1
        should_stop = self.bad_epochs >= self.patience
        return should_stop, False
```

The hook returns two booleans because the loop has two separate jobs: save the best checkpoint when validation improves, and stop when patience is exhausted. In a real loop, the validation block would call `stopper.step(val_loss)`, save a best checkpoint on improvement, break on stop, and then load the best checkpoint before final evaluation. That design avoids a quiet mismatch between the reported best metric and the in-memory model left after training.

```python
stopper = EarlyStopping(patience=2, min_delta=1e-4)
best_path = "checkpoints/best.pt"

for epoch in range(start_epoch, 20):
    train_metrics = train_one_epoch(model, train_loader, loss_fn, optimizer, device)
    val_metrics = evaluate(model, val_loader, loss_fn, device)
    scheduler.step()

    should_stop, improved = stopper.step(val_metrics["loss"])
    if improved:
        save_checkpoint(best_path, model, optimizer, scheduler, epoch, stopper.best)

    print(epoch, train_metrics, val_metrics, "best_val_loss", stopper.best)

    if should_stop:
        print(f"early stopping at epoch {epoch}")
        break

load_checkpoint(best_path, model, optimizer, scheduler, device)
model.eval()
```

This snippet assumes an epoch-stepped scheduler such as `StepLR`; a metric-driven scheduler such as `ReduceLROnPlateau` would receive the validation loss instead, and a per-step scheduler would move inside the batch loop. The important point is not one universal scheduler location. The important point is that the training loop names the location, saves the scheduler state, and makes the stop/restore decision from validation evidence rather than from training loss alone.

The loop mechanisms in this part are intentionally modest, but together they create an engineering runbook. Metrics tell you whether training and validation are moving together or separating. The overfit-one-batch check tells you whether the model can learn at all under idealized conditions. Gradient accumulation tells you how to trade memory pressure for a larger effective batch without changing gradient scale by accident. Early stopping tells you when the validation evidence says to stop spending compute and which checkpoint should represent the run. None of these mechanisms replaces understanding the model, but each one narrows the search space when training does something surprising.

## Did You Know?

- PyTorch 2.12 was announced by the PyTorch Foundation on May 13, 2026, and the current docs for this module's APIs are the 2.12 documentation set. That matters because API details move over time; for example, the modern mixed-precision documentation points users toward `torch.amp.autocast("cuda", ...)` instead of the deprecated `torch.cuda.amp.autocast(...)` form.
- PyTorch's `zero_grad(set_to_none=True)` behavior is not merely cosmetic. Gradients set to `None` can reduce memory use and make it clear which parameters did not receive gradients, but optimizers can treat `None` differently from a zero tensor, so manual gradient code must be written with that distinction in mind.
- `model.eval()` and `torch.no_grad()` are easy to confuse because both appear in validation code, but they control different systems. Evaluation mode changes layer behavior for modules such as dropout and BatchNorm, while no-grad changes autograd recording and memory use during forward passes.
- Full reproducibility is an engineering target, not a single function call. PyTorch documents that results are not guaranteed to be reproducible across releases, platforms, or CPU/GPU executions, even with identical seeds, so serious run records should include seeds, versions, device details, and dataset split policy.

## Common Mistakes

| Mistake | Problem | Better approach |
|---|---|---|
| Calling `optimizer.step()` before `loss.backward()` | The optimizer updates with stale, missing, or previous-batch gradients instead of the current batch's gradients. | Keep the step checklist fixed: zero gradients, forward, loss, backward, optimizer step. |
| Forgetting `optimizer.zero_grad(set_to_none=True)` | Gradients accumulate across batches and silently change the effective update direction and magnitude. | Clear gradients once per intended optimizer update, usually before the forward pass. |
| Validating without `model.eval()` | Dropout and BatchNorm behave as if the model is still training, so validation becomes noisy or biased. | Make `evaluate()` call `model.eval()` internally every time it runs. |
| Validating without `torch.no_grad()` | PyTorch records graphs that will never be backpropagated, wasting memory and sometimes keeping tensors alive through logging. | Wrap validation in `with torch.no_grad():` or use `@torch.no_grad()` on the evaluation function. |
| Saving only `model.state_dict()` for resume | The model weights reload, but optimizer buffers, scheduler counters, epoch, and best metric reset or disappear. | Save a checkpoint dictionary with model, optimizer, scheduler, epoch, and best validation metric. |
| Averaging per-batch losses equally | A small final batch receives the same weight as a full batch, making epoch loss slightly wrong. | Multiply each batch loss by batch size, sum, and divide by total examples. |
| Accumulating gradients without dividing the loss | The gradient is scaled by the number of micro-batches, which changes the effective learning rate. | Divide loss by `accumulation_steps` before `backward()` when using mean-reduced losses. |
| Reporting training loss as model quality | Training loss can improve while validation quality degrades, especially once a model memorizes training data. | Track train loss, validation loss, and at least one task metric, then choose best checkpoints from validation evidence. |

## Quiz

1. **Why does the canonical step clear gradients before the forward pass in this module?**

   <details>
   <summary>Answer</summary>

   PyTorch accumulates gradients into parameter `.grad` fields. Clearing gradients before the forward pass makes the invariant obvious: the next `backward()` call should produce exactly the gradients for the current intended update. Clearing after `optimizer.step()` can also work if done consistently, but clearing between `backward()` and `step()` erases the gradients the optimizer needs.

   </details>

2. **What is the difference between `model.eval()` and `with torch.no_grad():` during validation?**

   <details>
   <summary>Answer</summary>

   `model.eval()` recursively changes the module's training flag, which affects mode-dependent layers such as dropout and BatchNorm. `torch.no_grad()` disables gradient recording, which reduces memory use and prevents construction of a backward graph during evaluation. Validation usually needs both because correct layer behavior and disabled graph recording are separate concerns.

   </details>

3. **Why is a checkpoint with only `model.state_dict()` insufficient for resuming training?**

   <details>
   <summary>Answer</summary>

   Model weights are only one part of training state. Optimizers keep momentum or adaptive moment buffers, schedulers keep counters and learning-rate history, and the loop needs the current epoch and best validation metric to make correct stop/save decisions. Loading only weights starts from the same parameters but not from the same optimization trajectory.

   </details>

4. **A validation loop reports lower loss every epoch, but it never calls `torch.no_grad()`. Is the metric necessarily wrong?**

   <details>
   <summary>Answer</summary>

   The numeric metric may still be correct if the model is in evaluation mode and no accidental mutation occurs, but the loop is wasteful and risky because PyTorch records graphs that are never used for backward. The memory overhead can hide until larger batches or longer validation runs. Correct validation uses no-grad because evaluation is a measurement pass, not a gradient-building pass.

   </details>

5. **Why divide the loss by `accumulation_steps` during gradient accumulation?**

   <details>
   <summary>Answer</summary>

   Most PyTorch losses default to a mean over the mini-batch. If four micro-batches are backpropagated and each mean loss is used directly, the accumulated gradient is roughly four times the gradient of one effective large batch. Dividing each micro-batch loss by four preserves the gradient scale and avoids accidentally changing the effective learning rate.

   </details>

6. **What does the overfit-one-batch sanity check prove, and what does it not prove?**

   <details>
   <summary>Answer</summary>

   It proves that the model, data, labels, loss, gradients, and optimizer can cooperate on an intentionally easy memorization task. It does not prove that the model generalizes, that the validation split is clean, or that hyperparameters are optimal. Passing the check is a gate before serious training; failing it is strong evidence of a loop, data, or contract bug.

   </details>

7. **Which reproducibility controls belong in a serious PyTorch training run, and why is a seed alone not enough?**

   <details>
   <summary>Answer</summary>

   A serious run should record or set Python, NumPy, and PyTorch seeds, use a seeded `torch.Generator` for reproducible sampling, seed `DataLoader` workers when they call Python or NumPy randomness, record the dataset version or split indices, and document whether deterministic algorithms were enabled. A seed alone is not enough because dataset order, worker libraries, backend kernels, hardware, PyTorch versions, and nondeterministic operations can still change the observed result.

   </details>

## Hands-On Exercise

Take the synthetic training skeleton from Part 2 and turn it into a small experiment you can repeat. First run it as written for five epochs and record the final train and validation metrics. Then add a `StepLR` scheduler with `step_size=2` and `gamma=0.5`, save a checkpoint whenever validation loss improves, and reload the best checkpoint after training. Finally, run the same script twice with the same seed and confirm that the printed metrics are close enough for your local hardware and PyTorch build.

For the mode-discipline check, temporarily remove `model.eval()` from `evaluate()` and add `nn.Dropout(p=0.4)` after the ReLU in `TinyClassifier`. Run validation twice in a row without a training step between the two calls. If validation metrics differ noticeably, you have demonstrated why evaluation mode belongs inside the evaluation function. Restore `model.eval()` afterward and confirm that repeated validation is stable for the same model state.

For the checkpoint check, train for two epochs, save a latest checkpoint, create a fresh model/optimizer/scheduler trio, load the checkpoint, and continue training from the returned `start_epoch`. Print the learning rate before and after resume so you can see whether scheduler state survived. If the resumed run restarts the learning-rate schedule at the beginning, your checkpoint is missing scheduler state or loading it in the wrong place.

Success criteria:

- [ ] The training script has separate `train_one_epoch` and `evaluate` functions, and each function owns its required module mode internally.
- [ ] The checkpoint dictionary contains `model_state_dict`, `optimizer_state_dict`, `scheduler_state_dict`, `epoch`, and `best_metric`.
- [ ] Repeated validation on the same model state does not change because dropout is disabled by evaluation mode and gradients are not recorded.
- [ ] The best checkpoint is restored after early stopping or after the final epoch, so the in-memory model matches the best validation metric you report.
- [ ] The run record includes the seed, PyTorch version, device type, dataset split policy, final metrics, and path to the best checkpoint.

## Key Takeaways

The PyTorch training step is the A7 NumPy update loop with better engineering around the same responsibilities. `zero_grad(set_to_none=True)` clears previous gradients, the forward pass builds the graph, the loss produces a scalar objective, `loss.backward()` runs the A8-style reverse graph walk at tensor scale, and `optimizer.step()` performs the parameter update that used to be `W -= lr * dW`.

The full training loop must separate mutation from measurement. Training mode plus gradient recording belongs in the train loop. Evaluation mode plus no-grad belongs in the validation loop. Checkpoints must save enough state to resume optimization, not merely enough weights to run inference. Reproducibility requires seeding multiple libraries, controlling `DataLoader` workers, recording run context, and being honest about hardware and backend limits.

The loop is also your first diagnostic surface. Log train loss, validation loss, and a task metric; overfit one batch before launching a long run; use gradient accumulation only when the loss scaling and step timing are explicit; and restore the best checkpoint when early stopping chooses a validation winner. Later Block B modules will tune initialization, optimizers, regularization, normalization, diagnostics, and precision, but every one of those tools enters through this loop.

## Learner check

The index row for this rescope is intentionally mirrored here so the module and section index stay tied together:

> | 1.3 | [The Training Loop: From One Step to a Reproducible Run](/ai-ml-engineering/deep-learning/module-1.3-training-neural-networks/) |

## Sources

- PyTorch Foundation, "PyTorch 2.12 Release Blog" - https://pytorch.org/blog/pytorch-2-12-release-blog/
- PyTorch Tutorials, "Training with PyTorch" - https://docs.pytorch.org/tutorials/beginner/introyt/trainingyt.html
- PyTorch Tutorials, "Saving and Loading Models" - https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html
- PyTorch 2.12 documentation, `torch.optim.Optimizer.zero_grad` - https://docs.pytorch.org/docs/2.12/generated/torch.optim.Optimizer.zero_grad.html
- PyTorch 2.12 documentation, `torch.nn.Module.eval` and module mode behavior - https://docs.pytorch.org/docs/2.12/generated/torch.nn.Module.html
- PyTorch 2.12 documentation, `torch.no_grad` - https://docs.pytorch.org/docs/2.12/generated/torch.no_grad.html
- PyTorch 2.12 documentation, reproducibility notes and `DataLoader` worker seeding - https://docs.pytorch.org/docs/2.12/notes/randomness.html
- PyTorch 2.12 documentation, `torch.use_deterministic_algorithms` - https://docs.pytorch.org/docs/2.12/generated/torch.use_deterministic_algorithms.html
- PyTorch 2.12 documentation, automatic mixed precision deprecation notes for `torch.cuda.amp` - https://docs.pytorch.org/docs/2.12/amp.html
- Dive into Deep Learning, "Generalization in Deep Learning" - https://d2l.ai/chapter_multilayer-perceptrons/generalization-deep.html
- Andrej Karpathy, "A Recipe for Training Neural Networks" - https://karpathy.github.io/2019/04/25/recipe/
- Stanford CS231n, "Neural Networks Part 3: Learning and Evaluation" - https://cs231n.github.io/neural-networks-3/

## Next Module

Next: [Initialization & Signal Propagation](/ai-ml-engineering/deep-learning/module-1.3.1-initialization-signal-propagation/).
