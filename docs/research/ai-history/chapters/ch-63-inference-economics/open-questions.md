# Open Questions: Chapter 63 - Inference Economics

## Resolved For This Contract

- **Use live API pricing?** No. It changes too often and would require dated,
  provider-specific caveats. This chapter can explain the economics structurally
  from serving-system papers without relying on unstable price tables.
- **Include product-cost rumors?** No. Unsourced claims about ChatGPT daily cost
  are excluded. vLLM's "10x traditional keyword query" estimate is retained only
  as Yellow source-attributed framing.
- **Include energy and datacenter scale?** Only as handoff. Ch70/72 own power
  and datacenter arguments.
- **Include benchmark politics?** No. Paper speedups are allowed as local
  engineering evidence; public benchmark warfare belongs to Ch66.
- **Use DistServe?** Yes. It provides a clean late-era architecture frame:
  prefill/decode disaggregation, TTFT/TPOT, SLOs, and goodput.

## Still Needed Before Prose Drafting

- Claude source-fidelity review of page anchors and paper-specific claims.
- Gemini gap/capacity audit of the 4,600-5,400 word plan, especially whether the
  cost-levers scene should be capped below 950 words to avoid becoming a catalog.
- Optional: add a dated official provider pricing page only if the reviewer wants
  a short product-price sidebar. Default is to avoid it.
