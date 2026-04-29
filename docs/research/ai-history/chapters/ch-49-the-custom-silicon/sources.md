# Sources: Chapter 49 - The Custom Silicon

## Verification Key

- **Green**: claim has a verified page, section, figure/table, DOI, or stable official-web anchor.
- **Yellow**: source exists but the specific claim is not page-located, is interpretive, or needs stronger confirmation.
- **Red**: do not draft the claim.

## Primary Sources

| ID | Source | Use | Verification |
|---|---|---|---|
| P1 | Norman P. Jouppi, Cliff Young, Nishant Patil, David Patterson, et al., "In-Datacenter Performance Analysis of a Tensor Processing Unit," ISCA 2017 / arXiv:1704.04760. DOI: https://doi.org/10.48550/arXiv.1704.04760 and ACM DOI: https://doi.org/10.1145/3079856.3080246 | Main anchor for TPU v1 origin, architecture, deployment, workload suite, performance, and latency. | Green. Verified via arXiv PDF page anchors: p.1 abstract/introduction; p.2 origin and Table 1; p.3 architecture; p.4 systolic execution/software stack; p.7-p.8 latency/performance; p.12 discussion; p.13-p.14 related work. |
| P2 | Norm Jouppi, "Google supercharges machine learning tasks with TPU custom chip," Google Cloud Blog, May 19, 2016. URL: https://cloud.google.com/blog/products/ai-machine-learning/google-supercharges-machine-learning-tasks-with-custom-chip | Public announcement; Google services using TPUs; custom ASIC/TensorFlow framing; datacenter packaging. | Green for section/date anchors on the official Google Cloud page. |
| P3 | Kaz Sato and Cliff Young, "An in-depth look at Google's first Tensor Processing Unit (TPU)," Google Cloud Blog, May 12, 2017. URL: https://cloud.google.com/blog/products/ai-machine-learning/an-in-depth-look-at-googles-first-tensor-processing-unit-tpu | Pedagogical explanation of TPU v1, systolic arrays, quantization, block diagram, and performance. | Green for official page sections "The road to TPUs," "Prediction with neural networks," "Quantization in neural networks," "The heart of the TPU: A systolic array," and "Minimal and deterministic design." |
| P4 | Jeff Dean and Urs Hoelzle, "Build and train machine learning models on our new Google Cloud TPUs," Google Cloud Blog, May 18, 2017. URL: https://cloud.google.com/blog/topics/inside-google-cloud/google-cloud-offer-tpus-machine-learning | Closing hinge: Cloud TPU, second-generation TPU, training plus inference, TPU pods, TensorFlow Research Cloud. | Green for official page sections "Introducing Cloud TPUs" and "Introducing the TensorFlow Research Cloud." |

## Secondary / Context Sources

| ID | Source | Use | Verification |
|---|---|---|---|
| S1 | John L. Hennessy and David A. Patterson, "A New Golden Age for Computer Architecture," *Communications of the ACM* 62(2), 2019, pp. 48-60. DOI: https://doi.org/10.1145/3282307 | Context for domain-specific architectures and TPU v1 as an example of the post-Dennard/Moore architectural turn. | Green for CACM HTML sections "Domain-specific architectures," "Domain-Specific Languages," "Example DSA TPU v1," and "Summary." |
| S2 | Nicole Hemsoth Prickett, "First In-Depth Look at Google's TPU Architecture," *The Next Platform*, April 5, 2017. URL: https://www.nextplatform.com/2017/04/05/first-depth-look-googles-tpu-architecture/ | Interview context for Jouppi's role and the fast chip-design sprint. | Yellow for scene color unless quoting exactly from the article. Prefer P3 where Google republishes the relevant Jouppi quotation. |
| S3 | Hennessy and Patterson, *Computer Architecture: A Quantitative Approach*, 6th ed., Elsevier, 2017/2018. | Broader architecture background; not needed for load-bearing claims if P1 and S1 suffice. | Yellow until page anchors are extracted from the edition actually used. |

## Scene-Level Claim Table

| ID | Claim | Scene | Primary Anchor | Independent Confirmation | Status | Notes |
|---|---|---|---|---|---|---|
| C1 | Deep neural networks produced major service-quality gains, including a reported 30% word-error-rate reduction in speech recognition and image-recognition improvements. | 1 | P1, p.1 introduction | P3 "Prediction with neural networks" context | **Green** | Use as setup only; do not expand into a speech-recognition chapter. |
| C2 | Neural-network work splits into training/development and inference/production; TPU v1 targeted inference, while training remained floating-point-heavy. | 1 | P1, p.1 introduction | P4 opening section contrasts first TPU inference with later Cloud TPU training | **Green** | This is the core boundary against overstating TPU v1. |
| C3 | Quantization turns floating-point values into narrow integers, often 8-bit, which can be good enough for inference and cheaper in area/energy. | 1, 3 | P1, p.1 introduction | P3 "Quantization in neural networks" | **Green** | Keep accuracy claims cautious: "often" and "for these uses." |
| C4 | Google discussed GPUs, FPGAs, or custom ASICs for datacenter deployment as early as 2006, but initially found too few special-hardware applications to justify them. | 1 | P1, p.2, Section 2 | P3 "The road to TPUs" | **Green** | Useful for showing the decision was not automatic. |
| C5 | In 2013, a projection in which people used voice search for three minutes per day with DNN speech recognition would have required Google datacenters to double under conventional CPUs. | 1 | P1, p.2, Section 2 | P3 "The road to TPUs"; S2 opening summary | **Green** | This is the strongest scene opener. Do not add dollar figures. |
| C6 | Google started a high-priority custom ASIC project for inference, bought off-the-shelf GPUs for training, set a 10x cost-performance goal over GPUs, and designed/verified/built/deployed the TPU in 15 months. | 1, 2 | P1, p.2, Section 2 | P3 "The road to TPUs" | **Green** | The "15 months" applies to design-through-deployment as stated by the paper. |
| C7 | TPU v1 was deployed in Google datacenters since 2015 and accelerates neural-network inference. | 2 | P1, p.1 abstract | P2 announcement says TPUs had been running in Google datacenters for more than a year | **Green** | "Since 2015" comes from the 2017 paper, not the 2016 announcement. |
| C8 | TPU v1 was designed as a coprocessor on the PCIe I/O bus that could plug into existing servers rather than be tightly integrated with a CPU. | 2 | P1, p.2, Section 2 | P3 "The road to TPUs" | **Green** | Supports the rack/card scene. |
| C9 | The TPU Matrix Multiply Unit contains 256x256 MACs that perform 8-bit multiply-adds on signed or unsigned integers. | 3 | P1, p.3, Section 2 | P3 "The heart of the TPU: A systolic array" | **Green** | Equivalent to 65,536 MACs. |
| C10 | The TPU includes 24 MiB Unified Buffer, 4 MiB accumulators, and 8 GiB off-chip Weight Memory for inference weights. | 3 | P1, p.3, Section 2 | P3 "TPU Block Diagram" section | **Green** | Reconcile with abstract's 28 MiB by explaining the split. |
| C11 | TPU v1 has about a dozen CISC-style instructions; the key operations are host-memory reads/writes, weight reads, MatrixMultiply/Convolve, and Activate. | 3 | P1, p.3, Section 2 | P3 "RISC, CISC and the TPU instruction set" | **Green** | Good for explaining "programmable but narrow." |
| C12 | Systolic execution reduces Unified Buffer reads/writes: data and weights flow through the 256-cell dimension as diagonal wavefronts. | 3 | P1, p.4, Section 2 | P3 "The heart of the TPU: A systolic array" | **Green** | Do not overstate as no memory access at all; it reduces repeated access. |
| C13 | TPU software had to stay compatible with CPU/GPU stacks; TensorFlow portions were compiled into APIs that could run on GPUs or TPUs. | 2, 3 | P1, p.4, Section 2 | P2 says TPU was tailored for TensorFlow; P3 software-stack section | **Green** | Supports software/hardware co-design. |
| C14 | The TPU paper's six benchmark applications represented 95% of Google's NN inference workload in datacenters. | 4 | P1, p.2, Table 1 | P1 abstract repeats 95% workload framing | **Green** | Avoid universalizing beyond Google's suite. |
| C15 | The six benchmark apps included MLPs, LSTMs, and CNNs; the paper identifies examples including RankBrain, Google Neural Machine Translation subset, Inception, and AlphaGo. | 4 | P1, p.2, Table 1 caption | P2 Google service examples | **Green** | The table does not map every anonymized benchmark name to an app. |
| C16 | The comparison used a server-class Intel Haswell CPU and Nvidia K80 GPU, contemporaries deployed in the same datacenters. | 4 | P1, p.1 abstract | P3 performance discussion | **Green** | Specify "contemporary" and "same datacenters." |
| C17 | Across the paper's workload suite, TPU v1 was about 15x-30x faster than the contemporary CPU/GPU baselines, with TOPS/Watt about 30x-80x higher. | 4 | P1, p.1 abstract; p.2 highlights | P3 opening and performance sections | **Green** | Keep as paper-reported average/weighted result. |
| C18 | Inference applications often emphasize response time over throughput because many are user-facing. | 4 | P1, p.2 highlights; p.8 response-time discussion | P3 "Minimal and deterministic design" | **Green** | Helps explain why GPU peak throughput was not decisive. |
| C19 | For the MLP0 benchmark, the longest allowable 99th-percentile latency was 7 ms; TPU delivered 225,000 IPS at 7.0 ms in Table 4. | 4 | P1, p.8, Table 4 | P3 "Minimal and deterministic design" | **Green** | Do not identify MLP0 with a named product; the paper does not. |
| C20 | TPU v1 deliberately omitted features common in CPUs/GPUs - caches, branch prediction, out-of-order execution, multiprocessing, speculative prefetching, address coalescing, multithreading, context switching - because they help average cases more than 99th-percentile latency. | 4 | P1, p.8 | P3 "Minimal and deterministic design" | **Green** | Strong line for the minimalism scene; paraphrase rather than overquote. |
| C21 | Four of the six applications were memory-bandwidth limited on TPU; the paper's hypothetical TPU with K80-like GDDR5 memory would substantially improve results. | 4 | P1, p.2 highlights; p.12 Section 7 | P3 performance discussion | **Green** | Shows limits and avoids boosterism. |
| C22 | TPU v1 work began after Google saw the need for custom accelerators; the public 2016 announcement calls TPU a custom ASIC built for machine learning and tailored for TensorFlow. | 2 | P2, Google Cloud 2016 announcement section | P1 p.2 | **Green** | Anchor is official Google web section, not a page number. |
| C23 | By the May 2016 announcement, Google said more than 100 teams were using machine learning internally, including Street View, Inbox Smart Reply, and voice search. | 2 | P2, Google Cloud 2016 announcement section | P1 p.1 lists speech/vision/language/search applications | **Green** | This is ML usage at Google, not TPU usage for every team. |
| C24 | Google said the TPU board fit into a hard-disk-drive slot in datacenter racks and that first tested silicon ran applications at speed in datacenters within 22 days. | 2 | P2, Google Cloud 2016 announcement section | P3 "The road to TPUs" | **Green** | Useful concrete infrastructure detail. |
| C25 | Google said TPUs powered RankBrain, Street View, and AlphaGo by the 2016 announcement. | 2 | P2, Google Cloud 2016 announcement section | P1 Table 1 caption includes RankBrain and AlphaGo examples | **Green** | Do not imply these were the only services. |
| C26 | Google's May 2017 Cloud TPU announcement says second-generation TPUs were coming to Google Cloud and could accelerate both training and inference. | 5 | P4, opening / Cloud TPU announcement section | P4 later sections; P1 v1 inference boundary | **Green** | Closing hinge only; do not turn Ch49 into a TPU v2 chapter. |
| C27 | Google said a second-generation TPU device delivered up to 180 teraflops, and a TPU pod contained 64 second-generation TPUs with up to 11.5 petaflops. | 5 | P4, Cloud TPU announcement section | Contemporary secondary reporting can confirm if needed | **Green** | Use as announcement claim, not independent benchmark. |
| C28 | Google announced Cloud TPUs via Google Compute Engine and said users could mix hardware options including Skylake CPUs and Nvidia GPUs. | 5 | P4, "Introducing Cloud TPUs" section | P4 same section | **Green** | Reinforces coexistence, not replacement. |
| C29 | Google announced 1,000 Cloud TPUs for qualified ML researchers via TensorFlow Research Cloud. | 5 | P4, "Introducing the TensorFlow Research Cloud" section | Google program pages if needed | **Green** | Closing platform/access detail. |
| C30 | Hennessy and Patterson use TPU v1 as an example of a domain-specific architecture and identify DSAs as a response to slowing general-purpose performance gains. | 5 | S1, "Domain-specific architectures" and "Example DSA TPU v1" sections | P1 architecture details | **Green** | Secondary/context, but anchored. |
| Y1 | Exact capital cost, power cost, or dollar value that Google avoided by not doubling datacenters. | 1 | None located | P1 says doubling would be "very expensive" | Yellow | Do not invent dollar amounts. |
| Y2 | Exact TPU v1 fleet size, number of chips deployed, or percent of Google services served by TPUs. | 2 | None located | P2/P3 say deployed in datacenters and used by many services | Yellow | Google did not disclose a board count in the sources above. |
| Y3 | The complete internal staffing story behind the 15-month project. | 2 | S2 interview color; P3 republishes one Jouppi quote | P1 technical paper | Yellow | Use only the verified Jouppi quote if needed; no invented team scenes. |
| Y4 | TPU v1 directly caused an industry-wide custom AI silicon race. | 5 | None page-located here | Later AWS/Microsoft/Nvidia sources would be needed | Yellow | Frame only as a forward pointer unless sourced in a later chapter. |
| Y5 | MLP0's product identity or the specific Google service behind each anonymized benchmark. | 4 | P1 anonymizes most benchmark names | Table 1 caption names examples but not every mapping | Yellow | Keep benchmark labels as in paper. |
| R1 | Google "broke Nvidia's monopoly" with TPU v1. | 4, 5 | Contradicted/narrowed by P1 and P4 | P1 says GPUs bought for training; P4 offers Nvidia GPUs alongside Cloud TPU | Red | Do not draft. Overbroad and misleading. |
| R2 | Any private dialogue, panic meeting, or exact emotional reaction inside Google when the voice-search projection arrived. | 1 | None | None | Red | The scene can be dramatic through the projection itself, not invented dialogue. |

## Page Anchor Worklist

### Done

- P1 arXiv PDF: p.1 abstract/introduction; p.2 Section 2 and Table 1; p.3 architecture; p.4 systolic execution/software stack; p.7-p.8 latency and Table 4; p.12 memory-bandwidth discussion; p.13-p.14 related work and FPGA comparison.
- P2 Google Cloud 2016 TPU announcement: official date, custom ASIC/TensorFlow, datacenter deployment, hard-disk-slot board, 22-day first-silicon deployment, RankBrain/Street View/AlphaGo examples.
- P3 Google Cloud 2017 in-depth TPU explainer: road to TPUs, quantization, instruction set, systolic-array explanation, performance, deterministic/minimal design.
- P4 Google Cloud 2017 Cloud TPU announcement: second-generation TPUs, training plus inference, 64-TPU pods, Google Compute Engine access, TensorFlow Research Cloud.
- S1 Hennessy & Patterson 2019 CACM: domain-specific architectures, domain-specific languages, Example DSA TPU v1, summary.

### Still Useful But Not Required

- Physical/e-book page anchors for Hennessy and Patterson, *Computer Architecture: A Quantitative Approach*, 6th ed., if a prose writer wants deeper computer-architecture background.
- Full transcript or video anchor for the 2016 Google I/O TPU announcement if the chapter needs event staging beyond the blog page.
- Oral-history or interview material from Jouppi, Young, Patterson, Dean, or Hoelzle if the editor wants more human scene material.

## Conflict Notes

- The paper reports both an aggregate 28 MiB software-managed on-chip memory figure and the more detailed 24 MiB Unified Buffer plus 4 MiB accumulators. Explain the split.
- The paper's 15x-30x / 30x-80x result is bounded to the six-production-workload suite and the paper's baselines; do not turn it into a universal law.
- Google public posts are corporate primary sources. They are strong anchors for what Google announced and claimed, but benchmark interpretation should lean on the peer-reviewed ISCA paper.
