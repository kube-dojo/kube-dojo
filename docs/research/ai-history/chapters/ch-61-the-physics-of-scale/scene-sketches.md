# Scene Sketches: Chapter 61
# Scene Sketches: Chapter 61 - The Physics of Scale

## Scene 1: The Model Does Not Fit
- **Action:** Inventory the memory objects in a training step: parameters, gradients, optimizer states, activations, temporary buffers, and fragmented memory.
- **Evidence Anchor:** ZeRO pp.1-3.
- **Guardrail:** Do not reduce the problem to "buy more GPUs."

## Scene 2: The Pipeline
- **Action:** Layers are partitioned across accelerators; mini-batches are cut into micro-batches; devices fill and drain like a pipeline.
- **Evidence Anchor:** GPipe Section 2; Megatron 2021 pipeline-bubble discussion.
- **Guardrail:** Include idle/bubble overhead so the scene is not magic scaling.

## Scene 3: The Tensor Split
- **Action:** Transformer matrix multiplications are split inside layers; all-reduces stitch the distributed partial results back together.
- **Evidence Anchor:** Megatron-LM 2019 Section 3.
- **Guardrail:** Explain tensor parallelism separately from pipeline parallelism.

## Scene 4: The Optimizer Trap
- **Action:** Data parallelism replicates model states; ZeRO partitions optimizer states, gradients, and parameters across workers.
- **Evidence Anchor:** ZeRO Figure 1 and pp.2-4.
- **Guardrail:** Do not claim ZeRO eliminated the need for model parallelism in all cases.

## Scene 5: Three-Dimensional Parallelism
- **Action:** Pipeline, tensor, and data parallelism are composed; topology decides which parallelism belongs inside a node and which crosses nodes.
- **Evidence Anchor:** Megatron-LM 2021 p.1 and Sections 2-3.
- **Guardrail:** Keep topology/communication central.

## Scene 6: The Compute Budget
- **Action:** PaLM shows thousands-of-chip training; Chinchilla shows the parameter count is not the only scale dial.
- **Evidence Anchor:** PaLM Section 4; Chinchilla p.1/Section 3.
- **Guardrail:** Route deeper data-limit, energy, chip, and inference-cost analysis to later chapters.
