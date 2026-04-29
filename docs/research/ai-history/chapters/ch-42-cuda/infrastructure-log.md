# Infrastructure Log: Chapter 42 - CUDA

## Scene 1 - Pre-CUDA GPGPU

- **Hardware:** Commodity programmable graphics processors; Stanford/Buck context includes GeForce cards and broader programmable graphics hardware. Anchors: Stanford abstract lines 9-12; New Yorker lines 95-116.
- **Software surface:** Shaders, textures, graphics APIs, and graphics-pipeline constraints. The sources support the conclusion that general computation was possible but awkward. Anchors: Stanford abstract lines 10-12; ACM Queue lines 63-68; Wired lines 141-145.
- **Constraint:** Programmers had to think in graphics terms, not ordinary CPU-style data structures and loops. Anchor: Tom's Hardware lines 476-478.

## Scene 2 - Brook

- **Hardware:** Earlier-generation programmable GPUs, including DX9-class hardware in Buck's retrospective. Anchor: Tom's Hardware lines 471-478.
- **Programming model:** Streams, kernels, reductions, compiler/runtime, and data-parallel C extensions. Anchors: HGPU lines 73-75; Stanford abstract lines 10-12.
- **Measured examples:** SAXPY, SGEMV, image segmentation, FFT, and ray tracing; Brook implementations are reported as comparable to hand-written GPU code and up to seven times faster than CPU counterparts. Anchor: HGPU lines 74-75.
- **Constraint:** Brook was fitted to the limits of earlier graphics hardware; CUDA later relaxed some memory-model constraints. Anchor: Tom's Hardware lines 491-493.

## Scene 3 - G80/Tesla Hardware

- **Hardware:** NVIDIA GeForce 8800 GTX/GTS, G80/Tesla architecture, unified shader design, 128 stream processors at 1.35 GHz in the GTX. Anchors: NVIDIA technical brief p.8 lines 120-133; p.26 lines 512-514.
- **Architecture:** Unified stream processors could handle vertex, pixel, geometry, or physics workloads and were described as effectively general-purpose floating-point processors. Anchor: NVIDIA technical brief p.31 lines 601-616.
- **CUDA support:** GeForce 8800 GPUs included CUDA built-in technology, a standard C language interface, cooperative GPU threads, and a CPU-complementing architecture. Anchor: NVIDIA technical brief p.19 lines 324-337.
- **Tooling:** NVIDIA described an industry-standard C compiler, math libraries, dedicated driver, hardware debugging, profiler, and lower-level assembly access. Anchor: NVIDIA technical brief p.21 lines 376-384.

## Scene 4 - CUDA Programming Model

- **Execution model:** Host CPU calls kernels; kernels execute across grids of thread blocks; thread blocks contain concurrent threads. Anchor: ACM Queue lines 20-24.
- **Memory model:** Per-thread local memory, per-block shared memory, and global memory; on Tesla, shared memory is low-latency on-chip RAM and global memory resides in graphics-board DRAM. Anchor: ACM Queue lines 42-55.
- **Synchronization:** Threads within a block can use barrier synchronization and shared memory; blocks must remain independent. Anchors: ACM Queue lines 35-40 and 56-62.
- **Performance lever:** Shared memory can be used as a software-managed cache; ACM Queue reports about 20 percent improvement in one sparse-matrix example. Anchor: ACM Queue lines 95-104.

## Scene 5 - Early Platform Consequences

- **Availability:** CUDA was announced with GeForce 8800 and future Quadro support; SDK access was through NVIDIA's registered developer program. Anchors: CGW lines 45-48; Game Developer lines 163-166.
- **Hardware scope:** ACM Queue describes Tesla/CUDA support across GeForce 8800, Quadro, Tesla, and future/mainstream NVIDIA GPUs. Anchor: ACM Queue lines 141-145.
- **Early applications:** MRI reconstruction, molecular dynamics, and n-body simulation were reported as early CUDA application examples with large speedups. Anchor: ACM Queue lines 71-74.
- **Adoption signal:** ACM Queue reported tens of thousands of CUDA developers in 2008 and framed CUDA as democratizing parallel programming. Anchor: ACM Queue lines 115-119.
- **Boundary:** Later reporting says CUDA initially targeted an uncertain scientific/supercomputing market and that AI was not the central early application. Anchor: New Yorker lines 119-124.
