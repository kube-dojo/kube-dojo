# Open Questions: Chapter 46 - The Recurrent Bottleneck

## Yellow Claims to Resolve

- **Hochreiter 1991 thesis pages.** The 1997 LSTM paper cites and summarizes Hochreiter's thesis pp. 19-21, but the thesis itself was not retrieved. A scan would let prose cite the original diagnosis directly rather than through the 1997 retrospective summary.
- **Bengio 1994 interior evidence.** The abstract and bibliographic page anchor the headline claim, but full PDF extraction would support a richer Scene 1 with experiments and exact wording.
- **Gers 2000 interior evidence.** The abstract anchors the forget gate and continual-stream weakness. Full article pages would strengthen Scene 3 with the benchmark design and exact failure mode.
- **LSTM-era dominance.** Current Green claims support specific tasks: speech recognition, machine translation, language modeling/sequence transduction in Vaswani et al.'s framing. A broad "LSTMs dominated sequence data" sentence remains too wide.
- **Original LSTM hardware.** The 1997 paper gives algorithmic complexity and experiments, but the contract does not yet anchor the machines used to run them.

## Red Claims to Exclude Unless Sourced

- Specific GPU-utilization anecdotes such as "20% utilization."
- Internal Google motivations for replacing LSTMs with Transformers.
- GNMT deployment traffic, latency, production volume, or user-scale claims beyond what Wu et al. state.

## Useful Archival or Source Access

- IEEE full text for Bengio, Simard & Frasconi 1994.
- MIT Press full PDF for Gers, Schmidhuber & Cummins 2000.
- Hochreiter's 1991 diploma thesis scan.
- NVIDIA/cuDNN papers or engineering posts on recurrent kernels, sequence-length limits, and model parallelism.
- Contemporary talks or engineering notes from the GNMT/Transformer teams if the prose phase wants a richer transition from Ch46 to Ch50.

## Prose Readiness Judgment

The contract is ready for a cautious draft at **3,650-5,050 words**. It should not attempt a 6,000-word chapter unless the systems/hardware gaps above are filled. The strongest scenes are Scene 2, Scene 4, and Scene 5. Scene 1 is solid but should stay compact without full Bengio PDF pages. Scene 3 is important as a correction but should not sprawl until the full Gers 2000 paper is extracted.
