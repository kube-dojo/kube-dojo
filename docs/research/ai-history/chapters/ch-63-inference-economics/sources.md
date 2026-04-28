# Sources: Chapter 63 - Inference Economics

## Research Status

Contract is `capacity_plan_anchored` as of 2026-04-28. Sources below were
verified from arXiv and USENIX PDFs using local `curl` + `pdftotext`. The
chapter still needs Claude source-fidelity review and Gemini gap/capacity audit
before prose drafting. Gemini's first gap audit requested a tighter 3,400-4,500
word natural cap to prevent the cost-lever scene from becoming a catalog.

## Primary Source Spine

| Source | Use | Verification |
|---|---|---|
| Gyeong-In Yu et al., "Orca: A Distributed Serving System for Transformer-Based Generative Models," OSDI 2022. PDF: https://www.usenix.org/system/files/osdi22-yu.pdf | Autoregressive serving, iteration-level scheduling, selective batching, latency/throughput trade-off. | Green: PDF downloaded 2026-04-28. Abstract/page 1 says generation requires multiple model iterations, existing request-level batching blocks finished and newly arrived requests, Orca proposes iteration-level scheduling and selective batching, and evaluation on GPT-3 175B shows 36.9x throughput improvement at same latency versus FasterTransformer. |
| Tri Dao et al., "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness," arXiv:2205.14135. PDF: https://arxiv.org/pdf/2205.14135 | Memory hierarchy: attention speed depends on HBM/SRAM reads and writes, not only FLOPs. | Green: PDF downloaded 2026-04-28. Abstract/page 1 says Transformers are slow and memory-hungry on long sequences; FlashAttention is IO-aware, reduces reads/writes between HBM and SRAM, and gets wall-clock speedups. Page 2/Figure 1 says it avoids reading/writing the large N x N attention matrix to HBM and reports 7.6x attention-computation speedup on GPT-2. |
| Guangxuan Xiao et al., "SmoothQuant: Accurate and Efficient Post-Training Quantization for Large Language Models," arXiv:2211.10438. PDF: https://arxiv.org/pdf/2211.10438 | Quantization as inference cost lever; activation outliers; W8A8 serving. | Green: PDF downloaded 2026-04-28. Abstract/page 1 says quantization reduces memory and accelerates inference; SmoothQuant enables W8A8 quantization by migrating activation outlier difficulty to weights, with up to 1.56x speedup and 2x memory reduction. Introduction/page 1 says GPT-3 175B needs at least 350GB memory in FP16. |
| Ying Sheng et al., "FlexGen: High-Throughput Generative Inference of Large Language Models with a Single GPU," arXiv:2303.06865. PDF: https://arxiv.org/pdf/2303.06865 | Offload and memory-tier economics for latency-insensitive/high-throughput inference. | Green: PDF downloaded 2026-04-28. Abstract/page 1 defines high-throughput generation with limited GPU memory, aggregates GPU/CPU/disk memory, and claims 100x higher maximum throughput for OPT-175B on a single T4 with compression/offloading. Introduction/page 2 gives concrete memory hierarchy and batch/latency trade-offs. |
| Woosuk Kwon et al., "Efficient Memory Management for Large Language Model Serving with PagedAttention," SOSP 2023 / arXiv:2309.06180. PDF: https://arxiv.org/pdf/2309.06180 | KV cache as serving bottleneck; PagedAttention/vLLM; fragmentation and throughput. | Green: PDF downloaded 2026-04-28. Abstract/page 1 says KV cache memory is huge, dynamic, and wasted by fragmentation/duplication; PagedAttention uses virtual-memory-inspired paging; vLLM achieves near-zero KV cache waste and 2-4x throughput improvement at same latency versus FasterTransformer/Orca. Page 1 says an LLM request can be 10x more expensive than a traditional keyword query, but use as Yellow framing because it cites an external estimate. |
| Yaniv Leviathan, Matan Kalman, Yossi Matias, "Fast Inference from Transformers via Speculative Decoding," ICML 2023 / arXiv:2211.17192. PDF: https://arxiv.org/pdf/2211.17192 | Speculative decoding: fewer target-model serial passes without changing output distribution. | Green: PDF downloaded 2026-04-28. Abstract/page 1 says decoding K tokens normally takes K serial model runs; speculative decoding uses a faster model to draft several tokens and the target model to verify them concurrently without changing distribution, reporting 2x-3x latency improvement. |
| Charlie Chen et al., "Accelerating Large Language Model Decoding with Speculative Sampling," arXiv:2302.01318. PDF: https://arxiv.org/pdf/2302.01318 | Independent speculative-sampling confirmation and limitations: draft acceptance, latency, decoding method. | Green: PDF downloaded 2026-04-28. Abstract/page 1 says speculative sampling uses a faster draft model and modified rejection sampling to preserve target distribution; Chinchilla 70B benchmarks show 2-2.5x decoding speedup. Later sections note speedup plateaus/regresses with larger draft length depending on acceptance and overhead. |
| Yinmin Zhong et al., "DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving," OSDI 2024. PDF: https://www.usenix.org/system/files/osdi24-zhong-yinmin.pdf | Prefill/decode split, TTFT/TPOT, phase interference, per-GPU goodput. | Green: PDF downloaded 2026-04-28. Abstract/page 1 says existing systems colocate/batch prefill and decoding, causing interference and resource coupling; DistServe assigns phases to different GPUs and can serve up to 7.4x more requests or meet 12.6x tighter SLOs. Pages 1-3 define TTFT/TPOT and explain prefill as compute-bound and decoding as constrained by memory/I/O. |

## Scene-Level Claim Table

| Claim | Scene | Primary Anchor | Independent Confirmation | Status | Notes |
|---|---|---|---|---|---|
| Autoregressive generation runs a model repeatedly, one or a few tokens at a time, making inference a recurring product cost. | Meter Starts Running | Orca p.1 | vLLM p.1; DistServe pp.1-2 | Green | Use to define why inference differs from one-shot classification. |
| Traditional request-level batching is poorly matched to variable-length generation because finished requests and new arrivals wait for the batch. | Batching Meets Autoregression | Orca p.1 | vLLM background | Green | Core latency scene. |
| Orca proposes iteration-level scheduling and selective batching for generative Transformer serving. | Batching Meets Autoregression | Orca p.1 and pp.2-5 | vLLM cites Orca as prior state of art | Green | Avoid diving into implementation minutiae. |
| Orca reports 36.9x throughput improvement at the same latency against FasterTransformer for GPT-3-scale serving. | Batching Meets Autoregression | Orca p.1 | Orca intro p.2 | Green | Treat as paper evaluation, not universal production result. |
| FlashAttention identifies attention as memory/IO-bound and reduces HBM/SRAM reads and writes. | Memory Wall | FlashAttention p.1 | FlashAttention Fig. 1/page 2 | Green | Use to explain memory hierarchy, not only training. |
| FlashAttention avoids materializing the full N x N attention matrix in HBM and reports 7.6x attention-computation speedup on GPT-2. | Memory Wall | FlashAttention Fig. 1/page 2 | Algorithm section pp.4-5 | Green | Good concrete anchor. |
| In LLM serving, model weights are mostly static but KV cache grows dynamically per request and can consume close to 30% of A100 memory in the vLLM example. | KV Cache Becomes The Bill | vLLM p.1/Fig. 1 | vLLM Section 3 | Green | Do not generalize 30% to all systems. |
| Inefficient KV cache management limits batch size and throughput. | KV Cache Becomes The Bill | vLLM pp.1-3 | DistServe decoding memory discussion | Green | Central economic mechanism. |
| PagedAttention borrows OS paging to store KV cache in non-contiguous blocks and reduce fragmentation. | KV Cache Becomes The Bill | vLLM pp.1-2 | Figure 2 | Green | Strong explanatory analogy. |
| vLLM reports 2-4x serving-throughput improvement at same latency versus FasterTransformer/Orca. | KV Cache Becomes The Bill | vLLM abstract/p.2 | Evaluation sections | Green | Paper evaluation only. |
| SmoothQuant treats quantization as both memory reduction and inference acceleration, enabling W8A8 quantization for LLM matrix multiplications. | Compression/Offload/Speculation | SmoothQuant p.1 | SmoothQuant prelims | Green | Explain activation outliers carefully. |
| SmoothQuant reports up to 1.56x speedup and 2x memory reduction with negligible accuracy loss. | Compression/Offload/Speculation | SmoothQuant p.1 | Results sections | Green | Paper-specific result. |
| FlexGen shows latency-insensitive, batched inference can trade latency for throughput by offloading across GPU, CPU, and disk memory. | Compression/Offload/Speculation | FlexGen pp.1-3 | Figure 1 | Green | Boundary: not real-time chat default. |
| FlexGen reports OPT-175B on a single 16GB T4 with high-throughput/offload trade-offs and up to 100x higher maximum throughput versus offloading baselines under its setup. | Compression/Offload/Speculation | FlexGen pp.1-3 | Evaluation setup | Green | Keep as constrained benchmark. |
| Speculative decoding uses a small/draft model to propose tokens and a larger target model to verify them, preserving the target distribution. | Compression/Offload/Speculation | Speculative Decoding p.1 | Speculative Sampling p.1 | Green | Do not imply quality shortcuts. |
| Speculative decoding/sampling reports roughly 2x-3x or 2-2.5x speedups in evaluated setups, with acceptance/overhead limits. | Compression/Offload/Speculation | Speculative Decoding p.1; Speculative Sampling pp.1, 7-8 | Both papers | Green | Include plateau/regression caveat. |
| DistServe frames serving around TTFT for prefill and TPOT for decoding. | Prefill And Decode Split | DistServe pp.1-2 | DistServe Section 2 | Green | Useful definitions for readers. |
| DistServe argues colocating prefill and decoding creates interference and resource coupling. | Prefill And Decode Split | DistServe p.1 and Section 2.3 | Figures 1-2 | Green | Main architecture shift. |
| DistServe describes prefill as often compute-bound and decoding as constrained by similar I/O per step despite one-token processing. | Prefill And Decode Split | DistServe pp.2-3 | DistServe Section 3 | Green | Avoid absolute phrasing; "often" and setup-specific. |
| DistServe reports up to 7.4x more requests or 12.6x tighter SLOs versus state-of-art baselines. | Prefill And Decode Split | DistServe p.1 | Evaluation sections | Green | Paper evaluation only. |
| vLLM cites an estimate that an LLM request can be 10x more expensive than a traditional keyword query. | Meter Starts Running | vLLM p.1 | External estimate cited by paper, not independently fetched here | Yellow | Use only as source-attributed framing, not as a measured claim of this chapter. |

## Conflict Notes

- Do not quote current cloud/API prices as if they are stable historical facts.
- Do not convert paper benchmark speedups into production guarantees.
- Distinguish latency-sensitive chat from throughput-oriented batch/offline
  inference; FlexGen is mainly the latter.
- Distinguish prefill (prompt processing, TTFT) from decode (sequential output,
  TPOT). This is the chapter's cleanest explanatory axis.
- Keep energy and physical power-grid consequences as handoffs to Ch70/72.

## Anchor Worklist For Prose

- Use Orca p.1 for the "ordinary batching breaks on generation" scene.
- Use FlashAttention pp.1-2 to explain IO-aware attention and HBM/SRAM.
- Use vLLM pp.1-3 for KV cache, fragmentation, PagedAttention, and 2-4x
  throughput claims.
- Use SmoothQuant p.1 and FlexGen pp.1-3 for compression/offload cost levers.
- Use speculative decoding/sampling p.1 plus later caveat sections for the
  "draft and verify" scene.
- Use DistServe pp.1-3 for TTFT/TPOT, prefill/decode interference, and goodput.
