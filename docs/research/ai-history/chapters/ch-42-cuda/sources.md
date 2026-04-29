# Sources: Chapter 42 - CUDA

## Verification Key

- **Green**: claim has a verified source anchor: page, section, DOI, stable URL, or line-located web/PDF extraction.
- **Yellow**: source exists, but the exact claim is interpretive, date-conflicted, or not yet pinned to a strong primary anchor.
- **Red**: do not draft as fact yet.

Note: local shell `curl` could not resolve external hosts in this sandbox, so PDF extraction was verified through browser-extracted opened PDF/HTML line anchors rather than local `pdftotext`. Do not upgrade any unlisted claim to Green without a fresh anchor check.

## Primary and Near-Primary Sources

| Source | Use | Verification |
|---|---|---|
| Ian Buck and Pat Hanrahan, "Data Parallel Computation on Graphics Hardware," Stanford CS tech report page. URL: https://hci.stanford.edu/cstr/abstracts/2003-03.html | Pre-CUDA GPGPU and Brook abstraction setup. | **Green** for abstract claims at lines 9-12: researchers using graphics hardware for CPU work; need for correct abstraction; stream processor model; Brook implementation. |
| Ian Buck et al., "Brook for GPUs: Stream Computing on Graphics Hardware," ACM SIGGRAPH 2004 / TOG 23(3), pp. 777-786. DOI: 10.1145/1186562.1015800. HGPU mirror: https://hgpu.org/?p=1137 | Brook's C extension, compiler/runtime, abstraction of graphics hardware, and benchmark examples. | **Green** for bibliographic anchor and abstract at HGPU lines 48-75, including DOI, pages 777-786, and the Brook abstract. |
| NVIDIA, *NVIDIA GeForce 8800 GPU Architecture Technical Brief*, TB-02787-001_v1.0, November 8, 2006. URL: https://www.nvidia.com/content/PDF/Geforce_8800/GeForce_8800_GPU_Architecture_Technical_Brief.pdf | G80/GeForce 8800 architecture, CUDA built-in technology, unified shaders, stream processors, C compiler/tooling. | **Green** for p.8 lines 120-133; p.19 lines 324-337; p.21 lines 376-384; p.26 lines 496-514; p.31 lines 601-616; p.32-33 lines 621-656. |
| John Nickolls, Ian Buck, Michael Garland, Kevin Skadron, "Scalable Parallel Programming with CUDA," *ACM Queue* 6(2), April 28, 2008. URL: https://queue.acm.org/detail.cfm?id=1365500 | CUDA programming model, examples, restrictions, early application experience, Tesla sidebar. | **Green** for opening and "The CUDA Paradigm" lines 15-24; kernel/block details lines 27-40; memory/restrictions lines 42-68; application examples lines 71-74; shared memory lines 95-104; adoption/democratization lines 115-119; Tesla sidebar lines 141-162. |
| "Nvidia Introduces CUDA Architecture for Computing on GPUs," *Computer Graphics World*, November 16, 2006. URL: https://www.cgw.com/Press-Center/News/2006/Nvidia-Introduces-CUDA-Architecture-for-Computin.aspx | Contemporaneous launch coverage quoting NVIDIA's CUDA announcement. | **Green** for dated announcement and claims at lines 38-48: CUDA architecture, first GPU C-compiler development environment claim, GeForce 8800 availability, SDK availability. |
| "Product: Nvidia Announces Cuda GPU Architecture," *Game Developer*, November 8, 2006. URL: https://www.gamedeveloper.com/game-platforms/product-nvidia-announces-cuda-gpu-architecture | Launch-week date cross-check and GeForce 8800 availability. | **Green** for article date and NVIDIA-statement summary at lines 150-166. |
| NVIDIA Developer, "CUDA Zone - Library of Resources." URL: https://developer.nvidia.com/cuda-zone?wptouch_preview_theme=enabled | NVIDIA's current capsule history of Brook and CUDA. | **Green** for NVIDIA's own historical summary at lines 49-51; use cautiously because it is retrospective corporate copy. |
| NVIDIA Blog author page for Ian Buck. URL: https://blogs.nvidia.com/blog/author/ian-buck/ | Buck bio, NVIDIA employment, Brook and CUDA role. | **Green** for official bio at lines 5-8; note possible conflict with Buck's 2009 interview on exact start year. |
| Alan Dang, "Exclusive Interview: Nvidia's Ian Buck Talks GPGPU," *Tom's Hardware*, September 3, 2009. URL: https://www.tomshardware.com/reviews/ian-buck-nvidia%2C2393.html | First-person retrospective from Buck on Stanford, Brook, and starting CUDA. | **Green** for interview context lines 408-419 and Buck statements at lines 467-493. |

## Secondary Sources

| Source | Use | Verification |
|---|---|---|
| Branden Hookway, *Interface* (MIT Press, 2014). | Possible theoretical framing of interfaces and abstraction. | Yellow. Not accessed in this contract; do not use for specific CUDA facts without page anchors. |
| Stephen Witt, "How Jensen Huang's Nvidia Is Powering the A.I. Revolution," *The New Yorker*, November 27, 2023. URL: https://www.newyorker.com/magazine/2023/12/04/how-jensen-huangs-nvidia-is-powering-the-ai-revolution | Later-reported business context: GeForce origins, Buck's 8K rig, Huang's supercomputing bet, early CUDA market uncertainty. | **Green** for anchored secondary claims at lines 95-124; use sparingly and mark retrospective interpretation. |
| "Supercomputing's Next Revolution," *Wired*, November 9, 2006. URL: https://www.wired.com/2006/11/supercomputings-next-revolution/ | Contemporaneous HPC/GPGPU context and CUDA announcement context. | **Green** for Supercomputing 2006 context and CUDA-accessibility framing at lines 80-89 and programming-difficulty context at lines 141-145. |
| "New Nvidia computing architecture taps GPU, speeds data-intensive processing," *Military & Aerospace Electronics*, November 13, 2006. URL: https://www.militaryaerospace.com/computers/article/16722514/new-nvidia-computing-architecture-taps-gpu-speeds-data-intensive-processing | Contemporaneous reprint/coverage of NVIDIA CUDA announcement. | **Green** for article date and launch claims at lines 67-87. |
| AnandTech, "NVIDIA's GeForce 8800 (G80): GPUs Re-architected for DirectX 10," November 8, 2006. | Hardware-review context and CUDA reception. | Yellow. Search result found relevant section, but direct open redirected to forums in this environment; do not use as Green until accessible. |
| PC Perspective, "NVIDIA GeForce 8800 GTX Review - DX10 and Unified Architecture," November 8, 2006. | Launch-day reviewer context for G80 and CUDA. | Yellow. Search snippets show relevant sections, but this contract does not rely on it for Green claims. |

## Green Claim Table

| ID | Claim | Scene | Anchor | Independent Confirmation | Status | Notes |
|---|---|---|---|---|---|---|
| G1 | Before CUDA, researchers were already looking to graphics hardware for work previously done on CPUs, and Buck/Hanrahan argued that the right abstraction was necessary. | 1 | Buck/Hanrahan Stanford abstract, lines 9-12. | Wired 2006 lines 80-89; New Yorker 2023 lines 111-116. | **Green** | Phrase as pre-existing GPGPU work, not NVIDIA invention. |
| G2 | Brook for GPUs was a 2004 SIGGRAPH/TOG paper, pp. 777-786, DOI 10.1145/1186562.1015800, presenting a system for general-purpose computation on programmable graphics hardware. | 2 | HGPU bibliographic and abstract lines 48-75. | ACM Queue reference list line 125. | **Green** | HGPU is a mirror/index; DOI and page range are stable anchors. |
| G3 | Brook extended C with data-parallel constructs and used a compiler/runtime to abstract and virtualize aspects of graphics hardware. | 2 | HGPU abstract lines 73-75. | Stanford abstract lines 10-12; Tom's Hardware lines 476-478. | **Green** | Strongest bridge claim. |
| G4 | Buck later described Brook as an attempt to abstract "graphics-isms" into general programming concepts and said GPU porting previously required deep graphics expertise. | 2 | Tom's Hardware interview lines 476-478. | Brook abstract lines 73-75. | **Green** | First-person retrospective; do not invent exact lab scene. |
| G5 | Buck said he joined NVIDIA to start CUDA and that the initial CUDA effort was him and one other engineer. | 3 | Tom's Hardware lines 487-488. | NVIDIA bio lines 5-8 confirms Buck/CUDA role but gives a 2004 date. | **Green** | Date conflict with Y1; use "by 2005" for CUDA start. |
| G6 | NVIDIA's GeForce 8800 technical brief presents the 8800 GTX as the first fully unified architecture-based DirectX 10-compatible GPU and describes 128 stream processors at 1.35 GHz. | 3 | NVIDIA technical brief p.8, lines 120-133. | Game Developer lines 163-165; CGW lines 45-46. | **Green** | This is NVIDIA's technical characterization. |
| G7 | All GeForce 8800 GPUs included CUDA built-in technology, with a standard C language interface and GPU threads able to communicate/cooperate. | 3 | NVIDIA technical brief p.19, lines 324-337. | CGW lines 45-47. | **Green** | Use "included" for GeForce 8800, not all GPUs forever. |
| G8 | GeForce 8800 architecture design began in summer 2002 and targeted higher performance, image quality, GPU physics/high-end floating-point computation, and DirectX 10 pipeline features. | 3 | NVIDIA technical brief p.26, lines 496-514. | NVIDIA technical brief p.22, lines 406-420. | **Green** | Useful for showing CUDA rode a multi-year hardware redesign. |
| G9 | GeForce 8800 unified stream processors could process vertices, pixels, geometry, or physics and were described as effectively general-purpose floating-point processors. | 3 | NVIDIA technical brief p.31, lines 601-616. | Technical brief p.32-33, lines 621-656. | **Green** | Do not overstate as CPU-equivalent. |
| G10 | CUDA provides abstractions of thread-group hierarchy, shared memories, and barrier synchronization, with kernels executing across parallel threads. | 4 | ACM Queue lines 18-24. | NVIDIA technical brief p.19 lines 327-337. | **Green** | Core programming-model anchor. |
| G11 | CUDA kernels are launched with grid/block dimensions; thread blocks can exceed processor count and virtualize processing elements. | 4 | ACM Queue lines 27-40. | ACM Queue Tesla sidebar lines 146-150. | **Green** | Good explanatory material for prose. |
| G12 | CUDA exposes local, shared, and global memory spaces; shared memory maps to low-latency on-chip RAM on Tesla GPUs while global memory resides in board DRAM. | 4 | ACM Queue lines 42-55. | ACM Queue Tesla sidebar lines 159-160. | **Green** | Avoid turning into a full tutorial. |
| G13 | CUDA's restrictions included independent thread blocks, no direct communication between blocks in the same kernel grid, and explicit host-device data copies for CPU/GPU memory systems. | 4 | ACM Queue lines 56-62. | ACM Queue lines 39-40 and 49-50. | **Green** | Important honesty layer: CUDA was powerful but constrained. |
| G14 | CUDA differed from streaming languages by offering flexible thread creation, thread blocks, shared/global memory, and explicit synchronization; Brook fit earlier-generation GPUs. | 2, 4 | ACM Queue lines 63-68. | Tom's Hardware lines 491-493. | **Green** | Strong comparison between Brook and CUDA. |
| G15 | Early CUDA application examples included MRI reconstruction, molecular dynamics, and n-body simulation, with large reported speedups on Tesla-architecture GPUs. | 5 | ACM Queue lines 71-74. | Wired 2006 lines 80-89 and 129-145 for wider GPGPU context. | **Green** | Use as reported examples, not universal performance guarantee. |
| G16 | NVIDIA announced CUDA as a GPU computing architecture and GPU C-compiler development environment during the GeForce 8800 launch period. | 3, 5 | CGW lines 38-48; Game Developer lines 150-166; Military & Aerospace lines 67-87. | NVIDIA technical brief p.19-21. | **Green** | Use "announced during launch week" to handle article-date spread. |
| G17 | NVIDIA's current CUDA Zone says Brook was unveiled in 2003, Buck later joined NVIDIA, and led CUDA's 2006 launch. | 2, 3 | NVIDIA CUDA Zone lines 49-51. | NVIDIA Buck bio lines 5-8. | **Green** | Retrospective corporate summary; use for bio/history, not priority disputes. |
| G18 | ACM Queue reported in 2008 that CUDA had tens of thousands of developers and called it a democratization of parallel programming. | 5 | ACM Queue lines 115-119. | NVIDIA CUDA Zone lines 9-12 for later broader application ecosystem. | **Green** | "Tens of thousands" is 2008 source claim. |
| G19 | Tesla architecture extended the GPU beyond graphics and supported GeForce 8800, Quadro, Tesla, and mainstream GeForce GPUs with CUDA C programmability. | 3, 5 | ACM Queue sidebar lines 141-145. | NVIDIA technical brief p.19 lines 324-337. | **Green** | Useful for infrastructure-platform thesis. |
| G20 | Later reporting says Huang marketed GPUs to the supercomputing community in 2006, but early CUDA targeted an obscure academic/scientific market rather than AI. | 5 | New Yorker lines 116-124. | Wired 2006 lines 80-89; ACM Queue app examples lines 71-74. | **Green** | Secondary, retrospective; cite as later reporting, not contemporaneous fact. |

## Yellow Claim Table

| ID | Claim | Scene | Anchor | Status | Reason |
|---|---|---|---|---|---|
| Y1 | Buck joined NVIDIA in 2004 vs 2005. | 3 | NVIDIA bio lines 5-8 says 2004; Tom's Hardware lines 487-488 says 2005 for starting CUDA. | Yellow | Conflict likely comes from employment date vs CUDA project start. Do not flatten. |
| Y2 | The public CUDA SDK became available on a specific day in February 2007. | 5 | CGW line 48 says SDK was available to registered developers; ACM Queue line 16 says NVIDIA released CUDA in 2007. | Yellow | Exact SDK release date not anchored here. |
| Y3 | Jensen Huang personally noticed researchers buying gaming cards for science and made that observation the trigger for CUDA. | 1, 5 | New Yorker lines 119-121 gives later Chiu story; no contemporaneous decision record. | Yellow | Good narrative possibility, but too motive-heavy for Green. |
| Y4 | CUDA created an immediate economic moat for NVIDIA. | 5 | Later interpretation; early sources show NVIDIA-only support but not lock-in economics. | Yellow | Use "vendor-controlled platform" Green; keep "moat" as interpretation. |
| Y5 | CUDA "obsoleted" streaming languages. | 4, 5 | CGW line 46 reports NVIDIA's claim; Military & Aerospace line 85 repeats "said to obsolete." | Yellow | Green only as NVIDIA's marketing claim, not as historical judgment. |
| Y6 | Hookway's *Interface* provides a strong conceptual frame for CUDA as interface history. | 1-5 | Bibliographic source only. | Yellow | Needs page anchors before prose relies on it. |

## Red Claim Table

| ID | Claim | Scene | Status | Reason |
|---|---|---|---|---|
| R1 | NVIDIA "bet the company" on CUDA in 2006. | 5 | Red | New Yorker lines 119-124 support a costly unpopular push, but "bet the company" is too strong for CUDA 2006 and is better reserved for later AI strategy if anchored. |
| R2 | CUDA was designed in 2006 primarily for deep learning. | 5 | Red | Sources point to scientific, technical, graphics, product design, data analysis, and HPC targets. AI outcome is Ch43. |
| R3 | CUDA was the first general-purpose GPU programming system. | 1-2 | Red | Brook and earlier GPGPU systems predate CUDA. Only NVIDIA's "first GPU C-compiler development environment" claim is anchored as a launch claim. |

## Page Anchor Worklist

- Pull local PDF text for the Brook paper from ACM/author-hosted copy if shell network is available in a later session. Current Green status rests on DOI/page metadata plus abstract lines from HGPU.
- Locate CUDA Programming Guide 1.0 or 1.1 PDF and anchor exact SDK/toolkit language at page level.
- Locate NVIDIA's original November 8, 2006 press release in NVIDIA's own archive, if still available.
- If the chapter wants stronger business narrative, find NVIDIA FY2007/FY2008 annual report language about CUDA, Tesla, developer programs, or GPU computing.
