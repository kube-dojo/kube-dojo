# Infrastructure Log: Chapter 63 - Inference Economics

## Systems To Track In Prose

- **Autoregressive decode loop:** A generated output is a sequence of repeated
  model invocations, not one model call. This creates token-by-token latency and
  per-token cost.
- **Request-level vs iteration-level scheduling:** Orca's core insight is that
  a fixed batch is wrong for variable-length generation. The scheduler needs to
  admit new requests and release finished ones at iteration granularity.
- **Selective batching:** Some Transformer operations can be batched cleanly
  while attention over variable-length histories needs special handling.
- **GPU memory hierarchy:** FlashAttention gives the reader the hardware reason
  that attention and long contexts are constrained by memory traffic between HBM
  and SRAM.
- **KV cache lifecycle:** KV cache is per-request state. It grows during
  decoding, fragments memory, determines possible batch size, and can be shared
  or paged depending on the serving engine.
- **PagedAttention/vLLM:** Treat KV cache blocks like virtual-memory pages,
  reducing reserved/internal/external fragmentation and allowing higher serving
  throughput.
- **Quantization:** SmoothQuant shows the inference-specific problem of
  activation outliers and the economic appeal of W8A8 matrix multiplication.
- **Offload:** FlexGen adds CPU and disk memory to the serving design space when
  throughput matters more than low latency.
- **Speculation:** Draft/target decoding tries to turn several serial target
  model calls into one verification pass, but speedup depends on draft quality,
  acceptance rate, and overhead.
- **Prefill/decode disaggregation:** DistServe separates prompt processing from
  token generation and optimizes for TTFT and TPOT separately.

## Metrics And Claims To Keep Source-Bound

- Orca: 36.9x throughput improvement at same latency versus FasterTransformer
  under its GPT-3 175B evaluation.
- FlashAttention: 7.6x attention-computation speedup on GPT-2 in Figure 1; exact
  attention with fewer HBM accesses.
- SmoothQuant: up to 1.56x speedup and 2x memory reduction; W8A8 quantization.
- FlexGen: up to 100x maximum throughput for OPT-175B under its single-T4,
  offloading/compression setup.
- vLLM: 2-4x serving-throughput improvement at same latency; KV cache near-zero
  waste claim.
- Speculative decoding/sampling: 2x-3x and 2-2.5x speedups in the cited setups,
  with distribution-preservation caveats.
- DistServe: up to 7.4x more requests or 12.6x tighter SLOs; TTFT/TPOT framing.

## Boundary

- Ch63 owns serving economics and architecture. Ch64 owns edge deployment
  constraints; Ch70 owns energy-grid collision; Ch72 owns datacenter scale-out.
- Ch66 owns public benchmarks and evaluation politics. Ch63 may cite paper
  evaluation numbers only as engineering evidence for serving trade-offs.
- Ch68 owns data provenance and labor. Do not smuggle copyright into this
  chapter through API pricing or product economics.
