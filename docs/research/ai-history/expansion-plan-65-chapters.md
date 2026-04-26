# Expansion Plan: From 10 to 65 Chapters

This document outlines the roadmap for expanding the AI History book from the initial 10-chapter "light" MVP into a full-scale, 65-chapter definitive historical work, matching the pacing, density, and breadth of *Chip War*.

The 65 chapters are structured into 7 parts to maintain a cohesive narrative arc, explicitly focusing on the infrastructural, hardware, data constraints, and the open-source distribution layer that shaped every era of Artificial Intelligence.

---

## Part 1: The Analog Dream & The Digital Blank Slate (1940s-1950s)
*Focus: The transition from vacuum tubes and biology to von Neumann architectures and magnetic core memory.*

1. **The Dream Before the Machine:** Cybernetics and the physical limits of analog hardware.
2. **The Ballistics Bottleneck:** The ENIAC, human computers, and the limits of physical cables.
3. **The Stored Program:** John von Neumann, the EDVAC, and the birth of software.
4. **The Memory Miracle:** The transition from fragile Williams tubes to stable magnetic core memory.
5. **The Summer AI Named Itself:** The Dartmouth Conference and the IBM 704.
6. **The Logic Theorist:** Newell, Simon, and the RAND JOHNNIAC infrastructure.
7. **The Cold War Blank Check:** ONR, early ARPA, and the military funding of symbolic logic.
8. **SAGE:** The first continental-scale command-and-control computer infrastructure.
9. **The 5-Ton Brain:** Frank Rosenblatt, the Mark I Perceptron, and custom hardware.
10. **The Perceptron's Fall:** Minsky, Papert, and the computational intractability of multi-layer networks on 1960s mainframes.

## Part 2: The Symbolic Era, Specialized Hardware & European Defunding (1960s-1980s)
*Focus: The attempt to scale symbolic AI, the Lighthill Report, and expensive, custom workstations.*

11. **The List Processor:** McCarthy, LISP, and memory allocation abstractions.
12. **Project MAC:** The Time-Sharing revolution and interactive computing.
13. **The Lighthill Devastation:** The 1973 Lighthill Report, the defunding of massive mainframes in the UK, and the collapse of European AI infrastructure.
14. **ARPANET:** Networking the researchers and the birth of digital collaboration.
15. **The Silicon Dawn:** The Intel 4004 and the birth of the microprocessor.
16. **Rules, Experts, and the Knowledge Bottleneck:** The introduction of Expert Systems.
17. **The Rule-Based Fortune:** XCON/R1 and the commercialization of AI at DEC.
18. **The LISP Machine Bubble:** Symbolics, LMI, and the attempt to build custom AI hardware.
19. **The Japanese Threat:** The Fifth Generation Computer Systems project and massive parallel processing goals.
20. **Moore's Law Strikes:** The fall of the LISP machine to general-purpose Unix workstations and PCs.

## Part 3: The Statistical Underground & The Rise of Data (1980s-2000s)
*Focus: The quiet shift to probabilities, enabled by the internet and search engine corpora.*

21. **The Second AI Winter:** When hand-coded rules broke under maintenance complexity.
22. **The Statistical Underground:** Fred Jelinek, IBM, and the Hidden Markov Model.
23. **The DARPA SUR Program:** The shift from theoretical elegance to empirical metrics.
24. **The Accidental Corpus:** The World Wide Web and the digitization of human text.
25. **Indexing the Mind:** Google, PageRank, and the realization of internet-scale data infrastructure.
26. **The Multicore Wall:** CPU clock speeds plateau, forcing the industry toward parallelism.
27. **The Human API:** Amazon Mechanical Turk and the abstraction of human labor.
28. **The Vision Wall:** PASCAL VOC and the limitations of small datasets.
29. **Data Becomes Infrastructure:** Fei-Fei Li, WordNet, and the creation of ImageNet.
30. **Distributing the Compute:** Hadoop, MapReduce, and the cluster revolution.

## Part 4: The GPU Coup & The Deep Learning Revolution (2000s-2010s)
*Focus: The repurposing of graphics cards for massive parallel matrix multiplication.*

31. **The Utility Era:** AWS, EC2, and the birth of rented cloud infrastructure.
32. **The Graphics Hack:** The early, painful days of General-Purpose GPU (GPGPU) computing.
33. **CUDA:** Nvidia's genius abstraction that turned gaming PCs into supercomputers.
34. **The GTX 580 Sweatshop:** Krizhevsky, Sutskever, and the physical engineering of AlexNet.
35. **The ImageNet Smash:** The 2012 ILSVRC competition that broke the computer vision establishment.
36. **The Talent War:** Google, Facebook, and Baidu begin hoarding researchers and GPUs.
37. **DeepMind and the Distributed Cluster:** Scaling reinforcement learning across data centers.
38. **AlphaGo:** The hardware muscle behind the defeat of Lee Sedol.
39. **The Recurrent Bottleneck:** LSTMs, Sequence-to-Sequence, and the limits of un-parallelizable RNNs.
40. **The Custom Silicon:** Google's TPU and the move away from generalized GPUs.

## Part 5: The Era of Extreme Scale, Open Source & LLMs (2018-2022)
*Focus: Scaling laws, the Transformer, and the democratization of AI through open source.*

41. **Attention, Scale, and the Language Turn:** The Transformer aligns perfectly with matrix-math hardware.
42. **The Open Source Distribution Layer:** GitHub, early collaborative weights, and breaking the corporate lab monopoly.
43. **The Open Source Scaling Race:** BERT and bidirectional transformers.
44. **GPT-2:** Unsupervised learning and the dawn of few-shot capabilities.
45. **The Hub of Weights:** Hugging Face emerges as the central infrastructure for hosting and distributing models.
46. **The Scaling Laws:** OpenAI formalizes the mathematical relationship between compute, data, and loss.
47. **The Megacluster:** The massive Microsoft Azure supercomputer built for OpenAI.
48. **The API Moat:** GPT-3 and the transition from open-source models to gated cloud infrastructure.
49. **The Alignment Problem:** The realization that raw autocomplete is not a usable product.
50. **The Human Feedback Loop:** RLHF (InstructGPT) as the necessary behavioral infrastructure.

## Part 6: The Product Shock & The Edge Compute Frontier (2022-2023)
*Focus: Consumer adoption and the engineering required to run AI everywhere.*

51. **The Product Shock:** The launch of ChatGPT and the fastest consumer adoption in history.
52. **The Physics of Scale:** Megatron-LM and the engineering of tensor/pipeline parallelism.
53. **Inference Economics:** vLLM, PagedAttention, and the software required to serve models cheaply.
54. **The Edge Compute Bottleneck:** The shift from massive datacenters to mobile constraints.
55. **The Neural Engine:** Apple's dedicated NPU and the silicon engineering to run AI on battery power.
56. **The OS of AI:** Kubernetes, Ray, and orchestrating unreliable hardware at scale to democratize access.
57. **The Geopolitical Bottleneck:** TSMC, Taiwan, and the extreme difficulty of 3nm silicon fabrication.

## Part 7: The New Industrial Stack & The Physical Limits (2024-Present)
*Focus: AI transitions from computer science to geopolitics and heavy industry.*

58. **The Monopoly:** Nvidia's H100, the Blackwell architecture, and the moat of CUDA.
59. **Sovereign AI:** Nations begin building their own domestic GPU clusters.
60. **The Open Weights Rebellion:** Meta's Llama series, Mistral, and the push against closed APIs via Hugging Face.
61. **The Data Exhaustion Limit:** The looming crisis of running out of high-quality human text.
62. **The Energy Grid Collision:** AI scaling laws meet the physical limits of global power transmission.
63. **The Nuclear Pivot:** Tech giants explicitly invest in nuclear reactors to power massive data centers.
64. **The Chip War:** US export controls, ASML EUV machines, and denying infrastructure to rivals.
65. **The Infinite Datacenter:** Planning for the 100,000 GPU cluster and the future of industrial AI.