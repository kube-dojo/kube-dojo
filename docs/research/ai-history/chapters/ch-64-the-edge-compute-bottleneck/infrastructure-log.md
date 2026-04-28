# Infrastructure Log: Chapter 64 - The Edge Compute Bottleneck

## Systems To Track In Prose

- **Mobile-efficient architectures:** Depthwise separable convolutions,
  width/resolution multipliers, and later sub-billion LLM design all show that
  edge AI begins by changing the model, not merely shrinking hardware.
- **Dedicated phone accelerators:** Apple Neural Engine, Qualcomm Hexagon NPU,
  Google Tensor/AICore, and Apple ANE are specialized local execution surfaces.
- **On-device model services:** AICore and Apple Intelligence route application
  features through system-managed models rather than making every app ship its
  own runtime and weights.
- **Quantization and adapters:** Apple AFM-on-device uses aggressive
  quantization and parameter-efficient adapters; MobileLLM studies W8A8
  compatibility for small models.
- **KV cache and memory:** GQA, quantization, and DRAM budgeting make Ch63's
  inference-economics concepts visible on the device.
- **Flash as overflow:** LLM-in-a-flash treats storage as a slower backing layer
  when DRAM cannot hold the model.
- **Hybrid routing:** Pixel Video Boost and Apple Private Cloud Compute are the
  practical admission that some features exceed local device capacity.

## Metrics And Claims To Keep Source-Bound

- A11 Neural Engine: up to 600B operations/sec, Apple 2017 claim.
- Snapdragon 8 Gen 3: up to 10B-parameter on-device generative models and up to
  20 tokens/sec for 7B Llama 2, Qualcomm product-brief claim only.
- Apple AFM-on-device: ~3B parameters; GQA reduces KV cache; compressible to
  about 3.5 bits per weight without significant quality loss, with 3.7 bpw used
  in production in the paper's deployment discussion.
- LLM-in-a-flash: models up to 2x DRAM size; 4-5x CPU and 20-25x GPU speedups
  versus naive loading in the paper setup.
- MobileLLM: 125M/350M models; deep/thin architecture, embedding sharing, GQA,
  and API-calling/chat evaluations.

## Boundary

- Ch64 owns the device envelope. Ch63 owns datacenter serving engines; Ch70/72
  own grid and datacenter build-out; Ch71 owns export controls and chip
  geopolitics.
- Keep privacy claims technical and source-bound. The chapter can explain why
  local processing is marketed as privacy-preserving, but should not become a
  legal/privacy-policy audit.
