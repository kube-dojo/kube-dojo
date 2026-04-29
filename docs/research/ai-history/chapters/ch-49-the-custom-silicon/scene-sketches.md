# Scene Sketches: Chapter 49 - The Custom Silicon

## Scene 1: The Projection That Changed the Hardware Question

- **Action:** Start with the 2013 projection, not a boardroom invention scene. If users spoke to voice search for three minutes per day and Google served the DNN speech-recognition workload on conventional CPUs, datacenter capacity would have to double.
- **Technical turn:** Explain why this is an inference problem: trained models are now embedded in user-facing products, and every request has latency and cost consequences.
- **Human scale:** Jouppi and the TPU team can enter through the decision to build a high-priority custom inference ASIC, but do not invent their meeting or emotions.
- **Anchors:** sources.md C2-C6.
- **Drafting warning:** No dollar cost, no exact datacenter count, no private dialogue.

## Scene 2: A Card Built for Existing Racks

- **Action:** The chip becomes infrastructure. TPU v1 is deployed internally by 2015 and revealed publicly in 2016 as a custom ASIC tailored for TensorFlow.
- **Concrete image:** A TPU board that can fit into existing rack/server conventions is stronger than generic "AI hardware" language. Tie this to the PCIe coprocessor design and the hard-disk-slot packaging.
- **Product evidence:** RankBrain, Street View, and AlphaGo are acceptable as examples because Google's 2016 announcement names them. Keep AlphaGo to one sentence unless Ch48 already handled the game.
- **Anchors:** sources.md C7-C8, C13, C22-C25.
- **Drafting warning:** Do not imply that every Google ML team used TPU or that TPU replaced all CPUs/GPUs.

## Scene 3: The Systolic Heart

- **Action:** Slow down for the chapter's technical explanation. Neural-network inference keeps doing multiply-add work; quantization makes 8-bit operations useful; a 256x256 matrix unit turns that pattern into hardware.
- **Pedagogical move:** Use the systolic "wavefront" image, but keep it anchored: data arrives from different directions, weights from the top, activations/data from the left, and computations move through the array.
- **Architecture contrast:** CPUs/GPU generality costs area and power; TPU v1 trades generality for dense, repeated matrix operations plus deterministic latency.
- **Anchors:** sources.md C3, C9-C13, C20.
- **Drafting warning:** Do not say there is no memory access; say systolic execution reduces repeated Unified Buffer reads/writes.

## Scene 4: The Benchmark Is a Business Argument

- **Action:** Treat the 2017 paper as an argument about datacenter service economics. It is not just "92 TOPS"; it is six production inference workloads, response-time limits, host overhead, and performance per watt.
- **Comparison:** Haswell CPU and Nvidia K80 GPU are the baselines. Use the reported 15x-30x speed and 30x-80x TOPS/Watt envelope, bounded to the paper's workload suite.
- **Latency beat:** The MLP0 7 ms table is the scene's hinge: a GPU's peak throughput matters less if response-time limits force smaller batches and lower utilization.
- **Honesty beat:** Include the memory-bandwidth limits and hypothetical GDDR5 variant so the scene does not read as corporate victory copy.
- **Anchors:** sources.md C14-C21.
- **Drafting warning:** Do not identify anonymized benchmarks with products. Do not universalize the benchmark numbers.

## Scene 5: From Internal ASIC to Cloud Primitive

- **Action:** Close with the May 2017 Cloud TPU announcement: the internal inference accelerator becomes a cloud-facing product line, now with training plus inference and TPU pods.
- **Transition:** The point is not to catalog every TPU generation. The point is that TPU v1 taught Google that AI hardware could be vertically designed from model math through compiler/runtime through datacenter deployment.
- **Architecture frame:** Hennessy and Patterson's "domain-specific architectures" framing lets the chapter zoom out responsibly: TPU v1 is one example of a broader post-Dennard/Moore return to specialized architectures.
- **Forward pointer:** One sentence may point to later custom-silicon competition and foundation-model infrastructure, but details belong elsewhere.
- **Anchors:** sources.md C26-C30 plus Yellow Y4 for what not to overclaim.
- **Drafting warning:** Do not say TPUs made GPUs obsolete; P4 explicitly presents Cloud TPUs beside CPUs and Nvidia GPUs.
