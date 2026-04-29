# Open Questions: Chapter 49 - The Custom Silicon

## Yellow Claims To Resolve

- **Y1 - avoided cost:** The sources verify that a CPU-only voice-search DNN projection would require doubling datacenters and would be "very expensive," but they do not provide a dollar figure or power budget. Useful archival target: Google infrastructure talks or interviews that quantify the avoided capex/opex.
- **Y2 - fleet size:** No source here gives the number of TPU v1 boards/chips deployed, rack count, regional spread, or share of Google inference served by TPUs. Do not imply a deployment scale beyond "deployed in datacenters" and named service examples.
- **Y3 - staffing/internal process:** The 15-month timeline is anchored, and the Jouppi quote about the hectic sprint is available through Google's 2017 explainer / The Next Platform. A fuller human scene would require interviews or oral histories.
- **Y4 - industry race:** The contract does not yet anchor AWS Trainium/Inferentia, Microsoft Brainwave, Nvidia Tensor Cores, Cerebras, Graphcore, or other post-TPU competitive responses. Keep this to a forward pointer or leave it for later chapters.
- **Y5 - benchmark identity:** The TPU paper names benchmark classes and gives some examples, but it does not fully map anonymized workloads like MLP0 to specific products. Keep paper labels unless a primary source maps them.

## Red Claims Not To Draft

- **R1 - "broke Nvidia's monopoly":** Overbroad and contradicted by the sources. TPU v1 targeted inference, Google still bought GPUs for training, and Cloud TPU was offered alongside Nvidia GPUs.
- **R2 - invented crisis-room narrative:** The datacenter-doubling projection is dramatic enough. Do not create unverified dialogue, emotional reactions, or meeting choreography.

## Archival / Source Targets That Would Help

- Full Google I/O 2016 TPU announcement transcript/video with timestamps, if the prose needs event staging.
- Oral history or long-form interview with Norm Jouppi, Cliff Young, David Patterson, Jeff Dean, or Urs Hoelzle about the TPU project.
- Internal or public Google infrastructure talk that quantifies datacenter cost/power avoided by TPU v1.
- Edition-specific page anchors for Hennessy and Patterson, *Computer Architecture: A Quantitative Approach*, 6th ed., if the prose wants textbook-grade background on domain-specific architectures.
- Independent reporting on TPU v1 deployment scale, if available without relying on speculation.

## Current Prose Readiness Judgment

The chapter is ready for a `3k-5k likely` draft from anchored sources. It is not ready for a 6k-7k narrative because the available evidence is strongest on technical artifacts and benchmark interpretation, not on internal human scenes or broad market response.
