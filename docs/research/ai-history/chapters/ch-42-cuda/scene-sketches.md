# Scene Sketches: Chapter 42 - CUDA

## Scene 1: The Awkward Power Under the Graphics Card

Open with the gap between hardware capability and programmability. Commodity GPUs were already fast enough to tempt scientists and graphics researchers, but the programmer still had to enter through the graphics door: shaders, textures, pipeline stages, and awkward mappings. Buck and Hanrahan's Stanford abstract supplies the clean historical sentence: if GPUs were to become powerful processing resources, the abstraction had to be right. Wired's November 2006 Supercomputing report adds the wider atmosphere: researchers comparing GPUs and CPUs, Folding@Home trying GPU clients, and developers still forced to "trick" the GPU into non-graphics work.

Evidence anchors: `sources.md` G1, G16, G17. Prose layer: 650-900 words.

## Scene 2: Brook Tries to Make a GPU Look Like a Processor

Move from atmosphere to mechanism. Brook extended C with data-parallel constructs, presented streams and kernels as the programmer's mental model, and used a compiler/runtime to hide or virtualize graphics-hardware details. Buck's 2009 interview gives the prose its human voice: he says there was no good framework for thinking about GPUs as compute devices and that, before Brook-style abstraction, GPU porting could require deep graphics expertise. The scene should explain Brook without turning into a language manual: one paragraph on streams/kernels, one on what the compiler/runtime hid, one on why it still reflected the limits of DX9-era hardware.

Evidence anchors: `sources.md` G2, G3, G4, G14. Prose layer: 700-950 words.

## Scene 3: The Hardware Is Rebuilt While the Abstraction Becomes a Product

Tie Buck's move to NVIDIA to G80's multi-year design arc. The GeForce 8800 technical brief says the architecture work began in summer 2002 and targeted not just graphics performance but high-end floating-point computation and pipeline changes. The chapter can then show why unified stream processors mattered: the same processor pool could be allocated to vertices, pixels, geometry, or physics, and NVIDIA described those processors as effectively general-purpose floating-point processors. CUDA enters here as the software name attached to this hardware change: a standard C language interface, GPU threads that could cooperate, and tooling around a dedicated compute driver and compiler.

Evidence anchors: `sources.md` G5, G6, G7, G8, G9, G16, G19. Prose layer: 850-1,150 words.

## Scene 4: CUDA's Contract With the Programmer

This is the densest technical scene. Explain CUDA by following a programmer's unit of thought: write a C-like kernel, launch it over a grid, divide the grid into blocks, let threads in a block cooperate through shared memory and barriers, and move data between host and device memory. The important narrative point is not syntax for its own sake; it is that CUDA made parallelism explicit while letting hardware handle thread creation, scheduling, and processor-count scaling. The scene must also include restrictions: independent thread blocks, no direct within-grid block communication, explicit host-device copies, and performance sensitivity around shared memory and divergent control flow.

Evidence anchors: `sources.md` G10, G11, G12, G13, G14. Prose layer: 900-1,250 words.

## Scene 5: A Platform Appears Before Its Most Famous Use

Close with the launch and early platform consequences. Contemporary trade coverage presents CUDA as a GPU-computing architecture and C-compiler environment available with GeForce 8800 and future Quadro products. ACM Queue's 2008 article gives the early application texture: MRI reconstruction, molecular dynamics, n-body simulation, sparse matrix-vector multiplication, and tens of thousands of developers. Then stop before Ch43. Later New Yorker reporting is useful here precisely because it warns against hindsight: NVIDIA was pushing into an uncertain scientific/supercomputing market, not obviously building an AI empire in 2006. The last beat should be infrastructure, not triumphal prophecy: CUDA made a proprietary parallel-computing surface that future AI researchers could use.

Evidence anchors: `sources.md` G15, G16, G18, G19, G20. Prose layer: 700-1,050 words.
