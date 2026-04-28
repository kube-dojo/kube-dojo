# People: Chapter 63 - Inference Economics

## Research And Systems Actors

- **Gyeong-In Yu, Joo Seong Jeong, Geon-Woo Kim, Soojeong Kim, Byung-Gon Chun /
  Orca team:** Use as the serving-systems inflection for generative Transformers:
  iteration-level scheduling and selective batching.
- **Tri Dao et al. / FlashAttention team:** Use as the memory-hierarchy anchor.
  The chapter should emphasize the IO-aware idea rather than author biography.
- **Guangxuan Xiao et al. / SmoothQuant team:** Use for quantization as an
  inference-serving technique, especially activation outliers and W8A8
  deployment.
- **Ying Sheng et al. / FlexGen team:** Use for offload and throughput-oriented
  inference under limited GPU memory.
- **Woosuk Kwon et al. / vLLM and PagedAttention team:** Use for KV-cache memory
  management, virtual-memory analogy, and open serving engine impact.
- **Yaniv Leviathan, Matan Kalman, Yossi Matias; Charlie Chen et al.:** Use for
  speculative decoding/sampling, draft-target verification, and latency
  reduction with distribution preservation.
- **Yinmin Zhong et al. / DistServe team:** Use for prefill/decode
  disaggregation and SLO/goodput framing.

## Institutional Actors

- Systems research groups at Berkeley, Stanford, Seoul National University,
  FriendliAI, MIT, NVIDIA, Google, DeepMind, and related labs appear through the
  papers. Mention institutions only when they clarify the systems lineage.
- Cloud AI providers are part of the product context, but the chapter should not
  speculate about private cost structures.

## Guardrail

Do not turn this into a founder or lab rivalry chapter. The protagonist is the
serving stack: schedulers, memory managers, quantizers, offload planners,
speculative decoders, and SLO-driven routers.
