# Sources: Chapter 64 - The Edge Compute Bottleneck

## Research Status

Contract is `capacity_plan_anchored` as of 2026-04-28. Sources below were
verified from arXiv PDFs, official Apple/Google/Android pages, and a Qualcomm
product brief using web access plus local `curl` + `pdftotext`. Claude must
still source-review the anchors and Gemini must gap/capacity audit the prose
range before drafting.

## Primary Source Spine

| Source | Use | Verification |
|---|---|---|
| Andrew G. Howard et al., "MobileNets: Efficient Convolutional Neural Networks for Mobile Vision Applications," arXiv:1704.04861. PDF: https://arxiv.org/pdf/1704.04861 | Pre-generative edge pattern: architectures deliberately designed for mobile latency/size constraints. | Green: PDF downloaded 2026-04-28. Abstract/page 1 says MobileNets are efficient models for mobile and embedded vision applications and use hyperparameters to trade latency and accuracy. Pages 2-4 explain depthwise separable convolutions and width/resolution multipliers. |
| Apple, "The future is here: iPhone X," September 12, 2017. URL: https://www.apple.com/newsroom/2017/09/the-future-is-here-iphone-x/ | Neural Engine/on-device ML precursor; Face ID privacy. | Green: official Apple page opened 2026-04-28. Lines 81-83 say Face ID processing is done on-device and not in the cloud. Lines 162-167 introduce A11 Bionic and say the neural engine performs up to 600 billion operations per second for real-time processing and enables Face ID/Animoji. |
| Qualcomm, "Snapdragon 8 Gen 3 Mobile Platform Product Brief," 2023. PDF: https://www.qualcomm.com/content/dam/qcomm-martech/dm-assets/images/company/news-media/media-center/press-kits/snapdragon-summit-2023/documents/Snapdragon8Gen3_%20ProductBrief.pdf | Android phone NPU/product-brief claims: multimodal generative AI, 10B parameters, tokens/sec, NPU perf/watt. | Green/Yellow: product brief downloaded 2026-04-28. Page 1 says the AI Engine supports multimodal generative AI models including LLM/LVM/ASR up to 10B parameters solely on-device, LLMs up to 20 tokens/sec based on 7B Llama 2, 98% faster Hexagon NPU, and 40% performance/watt improvement. Use as vendor product framing, not independent benchmark. |
| Google, "Pixel 8 Pro ... now running Gemini Nano," December 6, 2023. URL: https://blog.google/products-and-platforms/devices/pixel/pixel-feature-drop-december-2023/ | Gemini Nano on Pixel 8 Pro; on-device/offline/privacy claims; cloud fallback for video. | Green: official Google page opened 2026-04-28. Lines 278-286 say Gemini Nano is Google's most efficient model for on-device tasks and runs on Pixel 8 Pro for Recorder Summarize and Smart Reply. Lines 279 and 286 say it helps keep sensitive data on phone and can work without network. Lines 296-297 say Video Boost uploads videos to the cloud for computational photography processing. |
| Android Developers, "Gemini Nano," documentation. URL: https://developer.android.com/ai/gemini-nano | AICore system service; developer-facing on-device architecture and constraints. | Green: official Android docs opened 2026-04-28. Lines 375-379 say Gemini Nano delivers generative AI without network/cloud, low cost/privacy safeguards, runs in AICore, and uses device hardware. Lines 390-396 say AICore manages model updates/safety/hardware accelerators and that inference speed depends on device hardware. |
| Android Developers Blog, "Gemini Nano is now available on Android via experimental access," October 2024. URL: https://android-developers.googleblog.com/2024/10/gemini-nano-experimental-access-available-on-android.html | On-device benefits and limits: smaller/less generalized than cloud models; app integration/storage challenge. | Green: official Android blog opened 2026-04-28. Lines 34-39 say Gemini Nano is the most efficient model for on-device tasks, processes prompts without server calls, and is smaller/less generalized than cloud equivalents. Lines 47-48 describe Nano 2 as nearly twice Nano 1's size. Lines 89-90 say integrating generative models into mobile apps is challenging due to computational resources and storage. |
| Apple Machine Learning Research, "Introducing Apple's On-Device and Server Foundation Models," June 10, 2024. URL: https://machinelearning.apple.com/research/introducing-apple-foundation-models | Apple Intelligence split between ~3B on-device model and server model via Private Cloud Compute. | Green: official Apple ML page opened 2026-04-28. Lines 17-20 announce Apple Intelligence and state Apple details a ~3B on-device language model and a larger server-based model available with Private Cloud Compute. |
| Apple, "Apple extends its privacy leadership..." June 10, 2024. URL: https://www.apple.com/newsroom/2024/06/apple-extends-its-privacy-leadership-with-new-updates-across-its-platforms/ | On-device vs Private Cloud Compute routing; larger-than-pocket model boundary. | Green: official Apple Newsroom page opened 2026-04-28. Lines 58-60 say on-device processing is a cornerstone, but larger-than-pocket models route to Private Cloud Compute; requests are analyzed for whether they can be processed on device. |
| Apple, "Apple Intelligence Foundation Language Models," arXiv:2407.21075. PDF: https://arxiv.org/pdf/2407.21075 | AFM-on-device technical details: ~3B, GQA, pruning/distillation, quantization, power/latency, LoRA adapters. | Green: PDF downloaded 2026-04-28. Abstract/page 1 says Apple built a ~3B on-device model and larger server model. Lines/pages around architecture say GQA reduces KV-cache footprint; AFM-on-device is distilled/pruned from larger models; deployment sections discuss latency/power, note compression to about 3.5 bits per weight without significant quality loss, and state Apple uses 3.7 bpw in production. |
| Keivan Alizadeh et al., "LLM in a flash: Efficient Large Language Model Inference with Limited Memory," arXiv:2312.11514. PDF: https://arxiv.org/pdf/2312.11514 | DRAM/flash bottleneck and model-larger-than-memory edge inference. | Green: PDF downloaded 2026-04-28. Abstract/page 1 says the method runs LLMs exceeding available DRAM by storing parameters in flash and loading them on demand, enabling models up to twice DRAM size with 4-5x CPU and 20-25x GPU speedups versus naive loading. Pages 2-3 explain bandwidth/energy constraints and flash/DRAM hierarchy. |
| Zechun Liu et al., "MobileLLM: Optimizing Sub-billion Parameter Language Models for On-Device Use Cases," ICML 2024 / arXiv:2402.14905. PDF: https://arxiv.org/pdf/2402.14905 | Small-model design for on-device tasks: sub-billion scale, deep/thin, GQA, API calling. | Green: PDF downloaded 2026-04-28. Abstract/page 1 says the paper focuses on LLMs under 1B parameters for mobile deployment, with deep/thin architecture, embedding sharing, and GQA. Pages around Tables 5-7 evaluate chat/API calling and W8A8 compatibility. |

## Scene-Level Claim Table

| Claim | Scene | Primary Anchor | Independent Confirmation | Status | Notes |
|---|---|---|---|---|---|
| Efficient mobile AI predates LLMs: MobileNets were explicitly designed for mobile/embedded vision, trading accuracy against latency and size. | Phone Learns To See | MobileNets p.1 | MobileNets architecture sections | Green | Use as precursor, not modern generative endpoint. |
| MobileNets use depthwise separable convolutions and width/resolution multipliers to reduce computation and tune models to device constraints. | Phone Learns To See | MobileNets pp.2-4 | N/A | Green | Good explanatory layer. |
| iPhone X's Face ID processed facial information on-device rather than in the cloud. | Privacy Compute Argument | Apple iPhone X lines 81-83 | A11 Neural Engine lines 162-167 | Green | Early privacy/edge scene. |
| A11 Neural Engine was a dual-core ML accelerator claiming up to 600B operations/sec for real-time processing. | Phone Learns To See | Apple iPhone X lines 162-167 | N/A | Green | Vendor claim; do not compare directly to modern TOPS. |
| Snapdragon 8 Gen 3 product brief claimed on-device multimodal generative AI support up to 10B parameters and up to 20 tokens/sec for 7B Llama 2. | Android Edge Product Claim | Qualcomm product brief p.1 | N/A | Yellow | Vendor product brief only; do not treat as independent benchmark. |
| Google introduced Gemini Nano as its most efficient model for on-device tasks, running on Pixel 8 Pro. | Small Model Not Toy | Google Pixel lines 278-280 | Android docs lines 375-379 | Green | Product-era anchor. |
| Gemini Nano on Pixel 8 Pro powered Recorder Summarize and Smart Reply, with offline/privacy benefits. | Privacy Compute Argument | Google Pixel lines 279, 286-289 | Android docs lines 394-396 | Green | Good concrete user-facing scene. |
| Google Pixel Video Boost uploaded videos to the cloud for processing, showing that not all phone AI features were local. | Cloud Comes Back | Google Pixel lines 296-297 | Apple PCC lines 58-60 | Green | Important no-overclaim guardrail. |
| Android AICore is a system service for Gemini Nano that manages model updates, safety, and access to hardware accelerators. | Small Model Not Toy | Android docs lines 390-396 | Android blog lines 89-90 | Green | Infrastructure layer. |
| Android docs say on-device generative AI removes server calls, but inference speed depends on device hardware. | Privacy Compute Argument | Android docs lines 394-396 | Android blog lines 38-39 | Green | Balanced claim. |
| Android blog says on-device models are significantly smaller and less generalized than cloud equivalents. | Small Model Not Toy | Android blog lines 38-39 | MobileLLM p.1 | Green | Key capacity caveat. |
| Apple Intelligence includes a ~3B on-device language model and a larger server model via Private Cloud Compute. | Small Model Not Toy / Cloud Comes Back | Apple ML lines 17-20 | Apple AFM paper p.1 | Green | Core Apple split. |
| Apple says it analyzes whether requests can be processed on device and routes larger-than-pocket needs to PCC. | Cloud Comes Back | Apple Newsroom lines 58-60 | Apple ML lines 17-20 | Green | Hybrid routing, not all-local. |
| AFM-on-device uses GQA to reduce KV-cache memory footprint. | Bottleneck Is Memory | Apple AFM paper architecture section | Ch63 KV-cache context | Green | Technical bridge from Ch63. |
| Apple reports AFM-on-device was pruned/distilled from larger models and compressed aggressively: about 3.5 bits per weight is the paper's quality-loss threshold, while 3.7 bpw is the production deployment choice. | Small Model Not Toy | Apple AFM paper training/deployment sections | Apple ML overview | Green | Avoid claiming 3.5 bpw as the shipped configuration. |
| LLM-in-a-flash runs models exceeding available DRAM by storing parameters in flash and loading them on demand. | Bottleneck Is Memory | LLM-in-a-flash p.1 | Apple AFM quantization/memory sections | Green | Strong edge bottleneck anchor. |
| LLM-in-a-flash reports models up to twice DRAM size and 4-5x CPU / 20-25x GPU speedups versus naive loading. | Bottleneck Is Memory | LLM-in-a-flash p.1 | Tables/results sections | Green | Paper-specific result. |
| MobileLLM argues sub-billion models are practical for mobile deployment and can handle common on-device chat/API-calling use cases. | Small Model Not Toy | MobileLLM p.1 and Tables 5-7 | Android blog smaller-model caveat | Green | Keep under-1B scope source-bound. |
| Edge AI is a routing and design problem, not a simple migration from cloud to phone. | Close | Synthesizes Apple PCC, Pixel Video Boost, AICore, LLM-in-flash | N/A | Green | Synthesis from sourced pieces. |

## Conflict Notes

- Qualcomm numbers are product-brief claims, not independent benchmark results.
- Apple/Google privacy claims are first-party product statements. Use them as
  product architecture claims, not legal proof that all data handling is perfect.
- Do not claim Gemini Nano or AFM-on-device equals frontier cloud models. The
  Android blog explicitly says on-device models are smaller and less generalized.
- Do not imply a single phone can run arbitrary frontier LLMs. LLM-in-flash is a
  research method for limited memory, not proof that all large models are
  practical on phones.

## Anchor Worklist For Prose

- Use MobileNets p.1/pp.2-4 to establish mobile efficiency as an old design
  discipline.
- Use Apple iPhone X lines 81-83 and 162-167 for Neural Engine/on-device privacy
  precursor.
- Use Google Pixel lines 278-289 and Android docs lines 375-396 for Gemini Nano.
- Use Apple ML lines 17-20, Apple Newsroom lines 58-60, and AFM paper deployment
  sections for Apple Intelligence hybrid routing and on-device model details.
- Use LLM-in-a-flash p.1 and MobileLLM p.1/Tables 5-7 for memory and small-model
  design.
