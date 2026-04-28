# Brief: Chapter 64 - The Edge Compute Bottleneck

## Thesis

AI did not simply move from the cloud to the phone. The edge became a second
frontier with different physics: battery, heat, DRAM, flash bandwidth, privacy,
offline use, app latency, model updates, and silicon specialization. This
chapter should explain the bottleneck that appears when product teams want
frontier-like experiences on personal devices: the model must be small enough,
quantized enough, specialized enough, and scheduled carefully enough to run
without turning the phone into a hand warmer or routing every request back to a
datacenter.

## Boundary Contract

- IN SCOPE: mobile-efficient neural networks as precursor; Apple Neural Engine
  and on-device Face ID/ML; Qualcomm/Android phone NPUs; Gemini Nano and AICore;
  Apple Intelligence's 3B on-device model and Private Cloud Compute fallback;
  MobileLLM/sub-billion model design; LLM-in-flash and memory hierarchy; privacy,
  offline use, latency, battery, DRAM, and flash trade-offs.
- OUT OF SCOPE: general inference-serving economics (Ch63), open-weights
  governance (Ch65), benchmark politics (Ch66), data/copyright fights (Ch68),
  power-grid/datacenter construction (Ch70/72), and export controls/chip
  geopolitics (Ch71).
- Transition from Ch63: Ch63 explains serving economics in datacenter systems;
  Ch64 explains why putting inference on a personal device changes the resource
  envelope.
- Transition to Ch65/70/72: edge constraints help explain why open weights,
  power, and datacenter build-out remain central rather than disappearing.

## Required Scenes

1. **The Phone Learns To See:** MobileNets and the A11 Neural Engine show the
   pre-LLM edge pattern: redesign networks and add specialized silicon because
   generic cloud-scale models do not fit mobile latency and power budgets.
2. **Privacy Becomes A Compute Argument:** Face ID and later Gemini Nano/Apple
   Intelligence make "on-device" a product claim: local processing can reduce
   server calls, network dependence, and data movement.
3. **The Small Model Is Not A Toy:** Gemini Nano, MobileLLM, and Apple
   AFM-on-device show that edge language models are deliberately smaller,
   specialized, quantized, and task-scoped.
4. **The Bottleneck Is Memory:** LLM-in-a-flash and Apple AFM details make DRAM,
   flash, KV cache, and quantization visible as the real edge constraints.
5. **The Cloud Comes Back:** Apple Private Cloud Compute and Pixel Video Boost
   show the honest limit: some tasks still route to server-side models when local
   compute is insufficient.
6. **Edge AI Becomes A Design Discipline:** Close on the new product
   architecture: decide what runs on device, what runs in private/cloud compute,
   and what should not run at all.

## Prose Capacity Plan

Target range: 4,000-5,000 words.

- 450-600 words: bridge from Ch63 serving economics to edge constraints; define
  battery, thermal, DRAM, flash, privacy, offline, and latency pressures.
- 650-750 words: MobileNets and A11 Neural Engine as the pre-generative edge
  pattern: efficient architectures plus dedicated silicon.
- 750-900 words: Gemini Nano / Android AICore, MobileLLM, and Qualcomm
  Snapdragon as Android edge-AI product and hardware framing.
- 850-1,000 words: Apple Intelligence / AFM-on-device as a modern edge model:
  ~3B parameters, GQA, pruning/distillation, quantization, LoRA adapters, ANE.
- 650-800 words: Memory bottleneck scene: LLM in a flash, DRAM vs flash, model
  larger than available memory, windowing/bundling, KV-cache budget.
- 450-650 words: the cloud fallback: Private Cloud Compute and Pixel Video Boost
  as evidence that edge AI is a routing discipline, not a full cloud replacement.
- 250-300 words: close and handoff to Ch65/70/72.

## Guardrails

- Do not claim on-device AI is always more private; say it can reduce server
  calls and data movement when the feature actually runs locally.
- Do not treat vendor product-brief TOPS/token claims as independent benchmarks.
- Do not make Apple the only protagonist; Android/Qualcomm and research papers
  must carry part of the chapter.
- Do not import Ch63's serving-engine details except as a short transition.
- Do not import Ch70/72 energy/datacenter material beyond the cloud-fallback
  handoff.
- Do not imply all AI features on a phone run locally. The sources explicitly
  show hybrid routing.
