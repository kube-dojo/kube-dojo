# Sources: Chapter 10

## Annotated Bibliography

### Primary
- [x] **"vLLM: Easy, Fast, and Cheap LLM Serving with PagedAttention" (Kwon et al., SOSP 2023)**
  - Verification: Green. The primary paper documenting the infrastructural software breakthrough that made massive LLM inference economically viable. Anchors Scene 2.
- [x] **"Megatron-LM: Training Multi-Billion Parameter Language Models Using Model Parallelism" (Shoeybi et al., Nvidia, 2019)**
  - Verification: Green. Primary document showing the complex orchestration (tensor and pipeline parallelism) required to train across massive GPU clusters. Anchors Scene 1.

### Secondary
- [x] **"Chip War: The Fight for the World's Most Critical Technology" (Chris Miller, 2022)**
  - Verification: Green. Provides the macroeconomic and geopolitical context of the TSMC/Nvidia supply chain that constrains modern AI. Anchors Scene 3.
- [x] **"The AI data shortage" (Epoch AI research reports, 2022-2023)**
  - Verification: Green. Verified secondary research projecting the exhaustion of high-quality internet data, highlighting the incoming infrastructural limit. Anchors Scene 3.
- [x] **"Microsoft and nuclear power for AI datacenters" (Wall Street Journal/Bloomberg, 2023-2024)**
  - Verification: Green. Journalistic accounts of the physical energy limits constraining the new industrial stack. Anchors Scene 3.

## Conflict Notes
- **Software vs. Hardware bottlenecks:** This chapter synthesizes both. While the media focuses on Nvidia's stock price, this chapter will ensure equal weight is given to the orchestration software (Kubernetes, vLLM) that actually makes the raw hardware usable.