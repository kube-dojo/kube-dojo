# Scene Sketches: Chapter 46 - The Recurrent Bottleneck

## Scene 1: The Gradient Fades or Blows Up

**Layer:** Prose Capacity Plan layer 1.

The chapter opens with a recurrent network as a promise: unlike a fixed-window feedforward model, it can carry a hidden state forward through a sequence. That promise immediately turns into a training problem. When the learner tries to send credit backward through time, the signal must pass through repeated recurrent transformations. Hochreiter & Schmidhuber's 1997 paper summarizes the result in blunt terms: with BPTT or RTRL, error signals flowing backward in time tend either to blow up or vanish. Bengio, Simard, and Frasconi independently frame the same obstacle as learning long-term dependencies with gradient descent.

The prose should make the math intuitive: a signal multiplied again and again either shrinks into nothing, grows out of control, or becomes dominated by short-range distractions. Keep equations sparse. The point is not to teach BPTT from scratch; the point is to show why a beautiful sequence idea became a practical bottleneck.

**Anchors:** `sources.md` G1-G2.

## Scene 2: The Constant Error Carousel

**Layer:** Prose Capacity Plan layer 2.

The answer in 1997 is not "use more data" or "use bigger GPUs." It is architectural. LSTM introduces a special memory cell whose internal state has a protected path for error flow. The constant error carousel is the central image: a self-connected, linear memory path, with gates controlling when information enters and when it affects the rest of the network.

Write this as a technical invention with historical stakes. LSTM was designed to make long time lags trainable. The paper's abstract claims more than 1000 discrete time steps on artificial tasks, and the body explains why the memory cell needs input and output gates: without them, the same weights are asked both to store a signal and to ignore later distractions, both to expose memory and to prevent irrelevant memory from disturbing output.

Avoid the common simplification that "LSTM has input, output, and forget gates" unless the next scene immediately corrects it. In this scene, original LSTM has input/output access protection and the constant error carousel.

**Anchors:** `sources.md` G3-G6.

## Scene 3: Learning to Forget

**Layer:** Prose Capacity Plan layer 3.

The 1997 memory path is powerful, but perfect memory is not always what a stream needs. Gers, Schmidhuber, and Cummins identify the weakness in continual input streams: if sequences are not explicitly segmented and reset, the internal state can grow indefinitely and break down. Their remedy is the adaptive forget gate, which lets a cell learn when to reset itself and release internal resources.

This scene is partly a correction of later folklore. The modern LSTM family that appears in textbooks and systems papers usually includes a forget gate, but the gate arrived as a follow-up. Use Goodfellow et al. to show how the mature field understood gated RNNs: create paths through time where derivatives neither vanish nor explode, then make the time scale of integration dynamic.

**Anchors:** `sources.md` G6-G7.

## Scene 4: The LSTM Workhorse

**Layer:** Prose Capacity Plan layer 4.

Now move from architecture to infrastructure. LSTM is no longer a paper solution to artificial long-lag tasks. Graves, Mohamed, and Hinton use deep LSTM RNNs in speech recognition. Sutskever, Vinyals, and Le use multilayer LSTMs to map sequences to sequences: one LSTM reads the input one timestep at a time into a vector, another decodes the output, and reversing the source sentence makes optimization easier by shortening early dependencies.

The 2014 paper gives the chapter's strongest machine-room detail. A single-GPU implementation runs too slowly for their purposes, so they use eight GPUs: four for LSTM layers, four for the softmax. That buys a speedup and still leaves a ten-day training run. GNMT in 2016 extends the pattern: deep LSTM encoder and decoder stacks, attention, residual connections, model parallelism, data parallelism, low-precision inference, and wordpieces.

The narrative stance should be admiring but unsentimental. These systems work. They also reveal how much engineering is being spent to keep recurrence moving.

**Anchors:** `sources.md` G8-G14 and G20.

## Scene 5: The Sequential Wall

**Layer:** Prose Capacity Plan layer 5.

The final scene names the bottleneck in the language of "Attention Is All You Need." Recurrent, LSTM, and GRU models are firmly established for sequence modeling and transduction; then Vaswani et al. state the cost. Recurrent models compute along symbol positions. The hidden state at one position depends on the previous hidden state, so computation inside a training example cannot be parallelized across the sequence.

Use Table 1 as the technical hinge: recurrent layers require O(n) sequential operations; self-attention requires O(1). Mention the 8-P100 training schedule only as a forward signal, then stop. The chapter closes by separating the two bottlenecks: LSTM had solved the old vanishing-gradient bottleneck well enough to power major systems, but the recurrent time axis became the next constraint.

Forward pointer: see Ch50 for the Transformer answer.

**Anchors:** `sources.md` G15-G19.
