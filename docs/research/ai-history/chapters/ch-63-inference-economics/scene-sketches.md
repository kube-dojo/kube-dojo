# Scene Sketches: Chapter 63 - Inference Economics

## Scene 1: The Meter Starts Running

- **Action:** Open with the product shift. Training is a capital shock, but
  inference is a meter: every user request creates work that must be scheduled,
  cached, batched, and billed against scarce accelerators.
- **Evidence Layer:** Orca p.1; vLLM p.1; DistServe pp.1-2.
- **Narrative Job:** Give non-specialist readers the basic variables: throughput,
  latency, TTFT, TPOT, batch size, utilization, and goodput.
- **Guardrail:** Do not use unsourced operating-cost rumors or live API prices.

## Scene 2: Batching Meets Autoregression

- **Action:** Show why a generative model is unlike an image classifier. It does
  not simply process a request once; it loops. Orca's fixed-batch critique makes
  the product pain concrete: finished requests wait, new requests wait, and
  variable output length makes simple batching inefficient.
- **Evidence Layer:** Orca abstract/page 1; Orca intro/background pp.1-3.
- **Narrative Job:** Explain iteration-level scheduling and selective batching
  in plain terms.
- **Guardrail:** Do not imply Orca is the current production winner; use it as a
  historical systems inflection.

## Scene 3: The Memory Wall Moves Into Serving

- **Action:** Pivot from scheduling to hardware. FlashAttention gives a clean
  demonstration that attention performance depends on moving data through GPU
  memory hierarchy, not merely on inventing a lower-FLOP formula.
- **Evidence Layer:** FlashAttention pp.1-2, Figure 1, algorithm discussion.
- **Narrative Job:** Make HBM/SRAM intuitive: the expensive part is often moving
  the attention data, not just multiplying it.
- **Guardrail:** FlashAttention was also important for training, but here its job
  is to explain serving/long-context economics.

## Scene 4: The KV Cache Becomes The Bill

- **Action:** Introduce the KV cache as the hidden object users never see. It is
  per-request memory that grows as the conversation grows. vLLM/PagedAttention
  makes this visible through fragmentation, virtual-memory pages, and throughput
  gains.
- **Evidence Layer:** vLLM pp.1-3, Figures 1-3.
- **Narrative Job:** Translate "context window" into a cost story: more
  concurrent users and longer histories compete for GPU memory.
- **Guardrail:** Do not generalize vLLM's 13B/A100 memory split to every model.

## Scene 5: Compression, Offload, And Speculation

- **Action:** Compare three families of economic tricks. SmoothQuant reduces
  bytes and uses cheaper integer arithmetic. FlexGen moves tensors through GPU,
  CPU, and disk for throughput-oriented work. Speculative decoding pays for a
  small draft model to avoid some expensive serial target-model passes.
- **Evidence Layer:** SmoothQuant p.1; FlexGen pp.1-3; speculative decoding p.1;
  speculative sampling pp.1 and 7-8.
- **Narrative Job:** Show that "make inference cheaper" is not one technique; it
  is a portfolio of trade-offs.
- **Guardrail:** Keep FlexGen separated from low-latency chat; keep speculative
  speedups tied to acceptance/overhead.

## Scene 6: Prefill And Decode Split Apart

- **Action:** DistServe names the mature serving split. Prompt processing and
  output-token generation have different latency measures and different hardware
  preferences, so colocating them can create interference.
- **Evidence Layer:** DistServe pp.1-3.
- **Narrative Job:** Make TTFT and TPOT the chapter's final conceptual tool.
  This sets up why inference becomes infrastructure planning.
- **Guardrail:** Do not claim disaggregation is always best; the source frames it
  around goodput and SLOs.

## Scene 7: Economics Becomes Architecture

- **Action:** Close by reframing the AI lab. A product lab is now a serving
  operator: schedulers, caches, memory managers, quantizers, routers, and SLOs
  become part of the model's public behavior.
- **Evidence Layer:** Synthesize only from the cited serving papers.
- **Narrative Job:** Handoff to Ch64, Ch70, and Ch72: once inference dominates
  the product bill, edge constraints, power, and datacenters become narrative
  centerpieces.
- **Guardrail:** No new source-free claims about total industry spending.
