# Brief: Chapter 28 - The Second AI Winter

## Thesis

The second AI winter was not a single failure of intelligence or a simple moral tale about hype. It was a systems failure: rule-based expert systems worked in narrow domains, but the infrastructure around them could not absorb the cost of knowledge acquisition, rule maintenance, brittle control, specialized Lisp-machine hardware, and government programs that had promised machine intelligence before the underlying concepts and compute could scale. The winter arrived when organizations stopped treating demonstrations as proof of durable infrastructure.

## Scope

- IN SCOPE: expert-system maintenance burden; knowledge-acquisition bottleneck; XCON as both success and warning; collapse of confidence in specialized AI hardware and shells; DARPA Strategic Computing retreat from machine intelligence toward high-performance computing; Japanese FGCS as expectation trigger and international pressure; continuity into statistical/probabilistic methods.
- OUT OF SCOPE: first AI winter and Lighthill in detail; full Lisp-machine business history unless used as hardware-economics context; SVM/statistical speech/RL details reserved for Ch29-Ch31; broad claims that all expert systems failed.

## Boundary Contract

This chapter must preserve two truths at once. Expert systems delivered real value in constrained settings, including XCON-like configuration and defense technology-transfer tools. Yet the boom was brittle because rule bases were expensive to build, hard to maintain, and often tied to specialized tools and hardware. Do not write "symbolic AI was useless." Write that symbolic systems were useful where the domain, rule maintenance, and operational workflow stayed bounded.

## Scenes Outline

1. **The Successful Warning Sign:** Open with XCON: a celebrated expert system that configured DEC computers but grew into thousands of rules and a formidable maintenance task.
2. **The Knowledge Acquisition Bottleneck:** Explain why extracting informal human expertise into production rules became the bottleneck even when shells and tools improved.
3. **The Demonstration Trap:** Use DARPA Strategic Computing and the ALV/AI program reviews to show the gap between demonstrations, benchmarks, transition, and durable systems.
4. **The Fifth Generation Shadow:** Japan's FGCS program raised international expectations around knowledge processing, logic programming, and parallel inference; by the early 1990s, its final results were more research-platform than world-changing product.
5. **Hardware Loses Its Moat:** Symbolics gives the concrete business scene: specialized AI hardware was pressured by cheaper general workstations while losses and layoffs made the market correction visible.
6. **Winter as Reallocation:** The winter did not end computing progress; it redirected money and prestige toward architectures, high-performance computing, benchmarks, and statistical methods.

## 4k-6k Prose Capacity Plan

- 600-900 words: define the winter as convergence, not collapse from one cause.
- 900-1,200 words: XCON and expert-system maintenance, including 6,200 rules, 20,000 parts, annual rule churn, and intelligibility/control problems.
- 700-1,000 words: knowledge-acquisition bottleneck and why domain experts' tacit heuristics resisted easy encoding.
- 800-1,100 words: DARPA Strategic Computing, Schwartz's 1987-1990 cuts, the "no new ideas" critique, shift toward architectures/HPC, and congressional demand for products.
- 500-800 words: FGCS as international expectation amplifier and final-results nuance.
- 300-600 words: hardware economics via Symbolics layoffs/losses and Sun/Apollo workstation competition.
- 500-800 words: conclusion/handoff to Ch29-Ch31: margin methods, statistical speech recognition, and RL roots grow as alternatives to brittle rule maintenance.

Stretch path to 6k: add hardware economics only through the Symbolics anchor and, if needed, one additional business-press source. Do not stretch with generic "AI hype cycle" commentary.

## Citation Bar

- Minimum primary/near-primary sources before prose: Neumann 1988 on XCON maintenance; NASA/JSC 1987 or Atkinson 1990 on knowledge acquisition; Roland and Shiman 2002 on DARPA Strategic Computing; ICOT FGCS 1992 proceedings for the Japanese program's stated goals/final context.
- Minimum secondary/context sources: Hendler 2008 or equivalent for the later "perfect storm" framing; one source for Lisp-machine market collapse if that scene is included.
- Current status: enough anchored source material for a 4,000-5,500 word chapter.
