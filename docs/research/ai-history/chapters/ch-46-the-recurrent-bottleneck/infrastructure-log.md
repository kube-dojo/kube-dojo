# Infrastructure Log: Chapter 46 - The Recurrent Bottleneck

## Scene 1 - Training Through Time

- **Computing shape:** Backpropagation through time unfolds a recurrent network across sequence positions. The same recurrent weights are reused, and the error signal travels backward across time steps.
- **Constraint:** Hochreiter & Schmidhuber 1997 summarize the problem as exponentially sensitive error flow: signals can vanish or blow up over long time lags. This is a training-infrastructure problem as much as a mathematical one because long sequences require storing and traversing many intermediate states.
- **Anchor:** `sources.md` G1-G2.

## Scene 2 - LSTM Memory Cells

- **Computing shape:** LSTM introduces special units with self-connected internal state, input/output gates, and constant error flow through the memory cell path.
- **Constraint solved:** The 1997 paper claims LSTM can bridge artificial minimal time lags beyond 1000 steps and has per-time-step/per-weight O(1) complexity.
- **Constraint remaining:** LSTM still updates through time. It makes long dependencies learnable; it does not make the sequence axis parallel.
- **Anchor:** `sources.md` G3-G5.

## Scene 3 - Forget Gates

- **Computing shape:** Continual streams without explicit resets can let internal states grow indefinitely. The adaptive forget gate gives the cell a learned reset/release mechanism.
- **Constraint solved:** Better behavior on continual prediction tasks where sequence boundaries are not externally marked.
- **Boundary:** This is a 2000 extension, not a feature of the original 1997 LSTM.
- **Anchor:** `sources.md` G6-G7.

## Scene 4 - Deep LSTM Systems

- **Speech:** Graves, Mohamed, and Hinton use deep LSTM RNNs for TIMIT phoneme recognition, reporting 17.7% test error.
- **Translation, 2014:** Sutskever, Vinyals, and Le train four-layer LSTM encoder/decoder models. Their implementation uses an 8-GPU machine: four LSTM layers on four GPUs and softmax split across four more, reaching about 6,300 words/sec with minibatch 128 and training for about ten days.
- **GNMT, 2016:** Wu et al. use 8 encoder and 8 decoder LSTM layers with residual connections, attention, wordpieces, low-precision inference, data parallelism, and model parallelism. One model replica is partitioned 8 ways across GPUs.
- **Constraint visible:** The systems improve throughput by stacking, batching, partitioning, and narrowing dependencies. They do not remove the recurrent time-step dependency.
- **Anchor:** `sources.md` G8-G14 and G20.

## Scene 5 - The Sequential Wall

- **Computing shape:** Vaswani et al. write that recurrent models factor computation along symbol positions; the hidden state at one position depends on the previous hidden state and the current input.
- **Constraint:** This "inherently sequential nature" prevents parallelization within training examples. Table 1 lists recurrent layers as requiring O(n) sequential operations, while self-attention requires O(1).
- **Hardware comparison:** The Transformer paper reports one 8-P100 machine, 12 hours for base and 3.5 days for big. Use only as a contrast showing why the parallelism critique mattered; Ch50 owns the architecture and results.
- **Anchor:** `sources.md` G15-G19.

## Red-Line Infrastructure Claims

- No specific GPU-utilization percentage is anchored.
- No exact production traffic, latency, or deployment volume for GNMT is anchored.
- No exact hardware for the original 1997 LSTM experiments is anchored.
