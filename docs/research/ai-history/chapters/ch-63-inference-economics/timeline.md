# Timeline: Chapter 63 - Inference Economics

- **2022-05:** FlashAttention reframes attention speed around GPU memory
  hierarchy, arguing that wall-clock performance depends on IO between HBM and
  SRAM as much as asymptotic FLOPs.
- **2022-07:** Orca appears at OSDI, identifying autoregressive Transformer
  generation as a serving-systems problem and proposing iteration-level
  scheduling plus selective batching.
- **2022-11:** SmoothQuant shows a post-training path to W8A8 LLM inference,
  linking quantization directly to serving memory and speed.
- **2022-11 / 2023-02:** Speculative decoding and speculative sampling show how
  a draft model can reduce target-model serial decoding passes while preserving
  the target distribution under a rejection/verification scheme.
- **2023-03:** FlexGen demonstrates that, for throughput-oriented workloads,
  LLM inference can trade latency for higher throughput by coordinating GPU,
  CPU, and disk memory plus compression.
- **2023-09 / 2023-10:** vLLM/PagedAttention makes KV-cache memory management a
  first-class serving primitive, borrowing virtual-memory paging ideas to reduce
  fragmentation and increase throughput.
- **2024:** DistServe formalizes the next serving split: prefill and decode have
  different latency metrics, resource preferences, and interference patterns, so
  they can be scheduled on different GPU pools.
